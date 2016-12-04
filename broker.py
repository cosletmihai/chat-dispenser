import selectors
import warnings
from collections import defaultdict
from threading import Thread

from connection import Connection
from utils import BROADCAST_PORT, MESSAGE_PORT, MessageBuilder, MessageFields, MessageId, DebugMessage, User


class Broker:
    def __init__(self):
        self.writing_connection = Connection(read=False)
        self.reading_connection = Connection(read=True, ip=None, port=MESSAGE_PORT)
        self.broadcasting_connection = Connection(True, '', BROADCAST_PORT)

        self.selector = selectors.DefaultSelector()
        self.selector.register(self.broadcasting_connection.socket,
                               selectors.EVENT_READ,
                               self._process_login)
        self.selector.register(self.reading_connection.socket,
                               selectors.EVENT_READ,
                               self._process_receive)

        self.users_dict = dict()
        self.unsent_messages = defaultdict(list)
        self.groups = defaultdict(set)

    def _process_login(self):
        data, addr = self.broadcasting_connection.receive_message()
        message = MessageBuilder.make_readable(data)
        DebugMessage.debug(message, addr)

        ip = addr[0]
        message_content = message.get(MessageFields.MESSAGE_CONTENT, {})
        username = message_content.get(MessageFields.SENDER_USERNAME)
        port = message_content.get(MessageFields.SENDER_PORT)
        self._add_new_user(username, ip, port)
        online_users = self.get_list()
        message = {
            MessageFields.MESSAGE_ID: MessageId.ACKNOWLEDGE_LOG_IN,
            MessageFields.MESSAGE_CONTENT: {
                MessageFields.USER_LIST: online_users
            }
        }
        message_to_send = MessageBuilder.make_sendable(message)
        self.writing_connection.send_message(message_to_send, ip, port)

        self._send_missed_messages(username)


    def _send_missed_messages(self, username):
        missed_messages = self.unsent_messages.pop(username, [])
        user = self._get_user_info(username)

        for missed_message in missed_messages:
            message = {
                MessageFields.MESSAGE_ID: MessageId.RECEIVE_MESSAGE,
                MessageFields.MESSAGE_CONTENT: {
                    MessageFields.SENDER_USERNAME: missed_message.get(MessageFields.SENDER_USERNAME),
                    MessageFields.MESSAGE_TEXT: missed_message.get(MessageFields.MESSAGE_TEXT),
                }
            }
            message_to_send = MessageBuilder.make_sendable(message)
            self.writing_connection.send_message(message_to_send, user.ip, user.port)

    def _process_receive(self):
        data, addr  = self.reading_connection.receive_message()
        message = MessageBuilder.make_readable(data)
        DebugMessage.debug(message, addr)

        message_type = message.get(MessageFields.MESSAGE_ID)
        message_content = message.get(MessageFields.MESSAGE_CONTENT, {})

        try:
            getattr(self, message_type)(message_content)
        except AttributeError:
            print(message)
            warnings.warn('oups, seems like a rogue message')

    def send_message(self, message_content):
        user = self._get_user_info(message_content.get(MessageFields.RECEIVER_USERNAME))
        if user:
            if user.is_online:
                message = {
                    MessageFields.MESSAGE_ID: MessageId.RECEIVE_MESSAGE,
                    MessageFields.MESSAGE_CONTENT: {
                        MessageFields.SENDER_USERNAME: message_content.get(MessageFields.SENDER_USERNAME),
                        MessageFields.MESSAGE_TEXT: message_content.get(MessageFields.MESSAGE_TEXT),
                    }
                }
                message_to_send = MessageBuilder.make_sendable(message)
                self.writing_connection.send_message(message_to_send, user.ip, user.port)
            else:
                text = '{} is offline. The user will receive the message when the user comes online'.format(message_content.get(MessageFields.RECEIVER_USERNAME))
                message = {
                    MessageFields.MESSAGE_ID: MessageId.RECEIVE_MESSAGE,
                    MessageFields.MESSAGE_CONTENT: {
                        MessageFields.SENDER_USERNAME: 'broker',
                        MessageFields.MESSAGE_TEXT: text
                    }
                }
                message_to_send = MessageBuilder.make_sendable(message)
                sender = self._get_user_info(message_content.get(MessageFields.SENDER_USERNAME))
                self.writing_connection.send_message(message_to_send, sender.ip, sender.port)

                self.unsent_messages[message_content.get(MessageFields.RECEIVER_USERNAME)].append({
                    MessageFields.SENDER_USERNAME: message_content.get(MessageFields.SENDER_USERNAME),
                    MessageFields.MESSAGE_TEXT: message_content.get(MessageFields.MESSAGE_TEXT)
                })
                print(self.unsent_messages)
        else:
            warnings.warn('no such user exists')

    def create_group(self, message_content):
        group_members = message_content.get(MessageFields.GROUP_MEMBERS, [])
        group_name = message_content.get(MessageFields.GROUP_NAME)

        # Add the user that requested the creation of the group
        self.groups[group_name].add(message_content.get(MessageFields.SENDER_USERNAME))

        for group_member in group_members:
            if group_member in self.users_dict:
                self.groups[group_name].add(group_member)

            print(self.groups)

        # Send a message to every member of the newly created group
        for group_member in self.groups[group_name]:
            user = self._get_user_info(group_member)
            text = 'you\'re in group: {}. with members: {}'.format(group_name, str(self.groups[group_name]))
            message = {
                MessageFields.MESSAGE_ID: MessageId.RECEIVE_MESSAGE,
                MessageFields.MESSAGE_CONTENT: {
                    MessageFields.SENDER_USERNAME: 'broker',
                    MessageFields.MESSAGE_TEXT: text,
                }
            }
            message_to_send = MessageBuilder.make_sendable(message)
            self.writing_connection.send_message(message_to_send, user.ip, user.port)

    def group_message(self, message_content):
        group_name = message_content.get(MessageFields.GROUP_NAME)
        sender = message_content.get(MessageFields.SENDER_USERNAME)
        text = message_content.get(MessageFields.MESSAGE_TEXT)

        if group_name in self.groups:
            for group_member in self.groups[group_name]:
                if group_member != sender:
                    user = self._get_user_info(group_member)
                    message = {
                        MessageFields.MESSAGE_ID: MessageId.GROUP_MESSAGE,
                        MessageFields.MESSAGE_CONTENT: {
                            MessageFields.SENDER_USERNAME: sender,
                            MessageFields.MESSAGE_TEXT: text,
                            MessageFields.GROUP_NAME: group_name
                        }
                    }
                    message_to_send = MessageBuilder.make_sendable(message)
                    self.writing_connection.send_message(message_to_send, user.ip, user.port)
        else:
            user = self._get_user_info(sender)
            message = {
                MessageFields.MESSAGE_ID: MessageId.RECEIVE_MESSAGE,
                MessageFields.MESSAGE_CONTENT: {
                    MessageFields.SENDER_USERNAME: 'broker',
                    MessageFields.MESSAGE_TEXT: 'no such group'
                }
            }
            message_to_send = MessageBuilder.make_sendable(message)
            self.writing_connection.send_message(message_to_send, user.ip, user.port)

    def get_list(self):
        # return ['{}, online: {}'.format(user, self.users_dict[user].is_online) for user in self.users_dict]
        users_list = list()
        for user in self.users_dict:
            users_list.append('{}, online: {}'.format(user, self.users_dict[user].is_online))

    def get_online_users(self, message_content):
        address = self._get_user_info(message_content.get(MessageFields.SENDER_USERNAME))
        online_users = self.get_list()
        if address:
            message = {
                MessageFields.MESSAGE_ID: MessageId.ONLINE_USERS,
                MessageFields.MESSAGE_CONTENT: {
                    MessageFields.USER_LIST: online_users
                }
            }
            message_to_send = MessageBuilder.make_sendable(message)
            self.writing_connection.send_message(message_to_send, address[0], address[1])
        else:
            warnings.warn('no such user exists')

    def _get_user_info(self, username):
        print(self.users_dict)
        print(self.users_dict.get(username))
        return self.users_dict.get(username)

    def _add_new_user(self, username, ip, port):
        if username and ip and port:
            self.users_dict[username] = User(ip, port, True)
        else:
            warnings.warn('one of the fields username, ip, or port is not set',
                          username,
                          ip,
                          port)

    def log_out(self, message_content):
        user_to_remove = message_content.get(MessageFields.SENDER_USERNAME)
        if user_to_remove:
            self.users_dict[user_to_remove] = User(None, None, False)
            print("Went offline: {}".format(user_to_remove))
        else:
            warnings.warn('no such user exists')

    def selector_function(self):
        while True:
            events = self.selector.select()
            for key, mask in events:
                key.data()


def main():
    broker = Broker()

    worker = Thread(target=broker.selector_function)
    # It will kill the thread when the program exits
    worker.setDaemon(True)
    worker.start()

    while True:
        pass


if __name__ == '__main__':
    main()
