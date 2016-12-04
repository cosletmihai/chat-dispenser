import selectors
import warnings
from collections import defaultdict
from threading import Thread

from connection import Connection
from utils import BROADCAST_PORT, MESSAGE_PORT, MessageBuilder, MessageFields, MessageId, DebugMessage


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

        self.online_user_dict = dict()
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

        message = {
            MessageFields.MESSAGE_ID: MessageId.ACKNOWLEDGE_LOG_IN,
            MessageFields.MESSAGE_CONTENT: {
                MessageFields.USER_LIST: list(self.online_user_dict.keys())
            }
        }
        message_to_send = MessageBuilder.make_sendable(message)
        self.writing_connection.send_message(message_to_send, ip, port)

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
        address = self._get_user_address(message_content.get(MessageFields.RECEIVER_USERNAME))
        if address:
            message = {
                MessageFields.MESSAGE_ID: MessageId.RECEIVE_MESSAGE,
                MessageFields.MESSAGE_CONTENT: {
                    MessageFields.SENDER_USERNAME: message_content.get(MessageFields.SENDER_USERNAME),
                    MessageFields.MESSAGE_TEXT: message_content.get(MessageFields.MESSAGE_TEXT),
                }
            }
            message_to_send = MessageBuilder.make_sendable(message)
            self.writing_connection.send_message(message_to_send, address[0], address[1])

        else:
            warnings.warn('no such user exists')


    def create_group(self, message_content):

        print('in group creation')
        group_members = message_content.get(MessageFields.GROUP_MEMBERS, [])
        group_name = message_content.get(MessageFields.GROUP_NAME)

        # Add the user that requested the creation of the group
        self.groups[group_name].add(message_content.get(MessageFields.SENDER_USERNAME))

        for group_member in group_members:
            if group_member in self.online_user_dict:
                self.groups[group_name].add(group_member)

            print(self.groups)


        # Send a message to every member of the newly created group
        for group_member in self.groups[group_name]:
            address = self._get_user_address(group_member)
            text = 'you\'re in group: {}. with members: {}'.format(group_name, str(self.groups[group_name]))
            message = {
                MessageFields.MESSAGE_ID: MessageId.RECEIVE_MESSAGE,
                MessageFields.MESSAGE_CONTENT: {
                    MessageFields.SENDER_USERNAME: 'broker',
                    MessageFields.MESSAGE_TEXT: text,
                }
            }
            message_to_send = MessageBuilder.make_sendable(message)
            self.writing_connection.send_message(message_to_send, address[0], address[1])

    def group_message(self, message_content):
        group_name = message_content.get(MessageFields.GROUP_NAME)
        sender = message_content.get(MessageFields.SENDER_USERNAME)
        text = message_content.get(MessageFields.MESSAGE_TEXT)

        if group_name in self.groups:
            for group_member in self.groups[group_name]:
                if group_member != sender:
                    address = self._get_user_address(group_member)
                    message = {
                        MessageFields.MESSAGE_ID: MessageId.GROUP_MESSAGE,
                        MessageFields.MESSAGE_CONTENT: {
                            MessageFields.SENDER_USERNAME: sender,
                            MessageFields.MESSAGE_TEXT: text,
                            MessageFields.GROUP_NAME: group_name
                        }
                    }
                    message_to_send = MessageBuilder.make_sendable(message)
                    self.writing_connection.send_message(message_to_send, address[0], address[1])
        else:
            address = self._get_user_address(sender)
            message = {
                MessageFields.MESSAGE_ID: MessageId.RECEIVE_MESSAGE,
                MessageFields.MESSAGE_CONTENT: {
                    MessageFields.SENDER_USERNAME: 'broker',
                    MessageFields.MESSAGE_TEXT: 'no such group'
                }
            }
            message_to_send = MessageBuilder.make_sendable(message)
            self.writing_connection.send_message(message_to_send, address[0], address[1])



    def get_online_users(self, message_content):
        address = self._get_user_address(message_content.get(MessageFields.SENDER_USERNAME))

        if address:
            message = {
                MessageFields.MESSAGE_ID: MessageId.ONLINE_USERS,
                MessageFields.MESSAGE_CONTENT: {
                    MessageFields.USER_LIST: list(self.online_user_dict.keys())
                }
            }
            message_to_send = MessageBuilder.make_sendable(message)
            self.writing_connection.send_message(message_to_send, address[0], address[1])
        else:
            warnings.warn('no such user exists')

    def log_out(self, message_content):
        user_to_remove = message_content.get(MessageFields.SENDER_USERNAME)
        if user_to_remove:
            self.online_user_dict.pop(user_to_remove, None)
            print("Removed: {}".format(user_to_remove))
        else:
            warnings.warn('no such user exists')

    def _get_user_address(self, username):
        return self.online_user_dict.get(username)

    def _add_new_user(self, username, ip, port):
        if username and ip and port:
            self.online_user_dict[username] = (ip, port)
        else:
            warnings.warn('one of the fields username, ip, or port is not set',
                                    username,
                                    ip,
                                    port)

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
