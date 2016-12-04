import selectors
from threading import Thread

from connection import Connection
from utils import MessageBuilder
from utils import MessageFields
from utils import MessageId


class SenderReceiver():
    def __init__(self):
        self.broker_address = None
        self.username = None
        self.writing_connection = Connection(read=False)
        self.reading_connection = Connection(read=True)

        self.selector = selectors.DefaultSelector()
        self.selector.register(self.reading_connection.socket,
                               selectors.EVENT_READ,
                               self.reading_sel)
        self.send_login_message()

    def send_login_message(self):
        name = ''
        while not name:
            name = input('enter your username: ')

        self.username = name
        message = {
            MessageFields.MESSAGE_ID: MessageId.LOG_IN,
            MessageFields.MESSAGE_CONTENT: {
                MessageFields.SENDER_USERNAME: name,
                MessageFields.SENDER_PORT: self.reading_connection.get_port()
            }
        }
        message_to_send = MessageBuilder.make_sendable(message)

        self.writing_connection.broadcast_message(message_to_send)

        broker_message, addr = self.reading_connection.receive_message()
        received_message = MessageBuilder.make_readable(broker_message)

        received_message.get(MessageFields.MESSAGE_ID)
        message_content = received_message.get(MessageFields.MESSAGE_CONTENT)
        online_users = message_content.get(MessageFields.USER_LIST)
        print('online users: {}'.format(str(online_users)))

        self.broker_address = addr

    def reading_sel(self):
        data, _ = self.reading_connection.receive_message()
        message = MessageBuilder.make_readable(data)

        message_type = message.get(MessageFields.MESSAGE_ID)
        message_content = message.get(MessageFields.MESSAGE_CONTENT, {})

        try:
            getattr(self, message_type)(message_content)
        except AttributeError:
            pass

    def online_users(self, message_content):
        print("Online users: {}".format(message_content.get(MessageFields.USER_LIST)))

    def receive_message(self, message_content):
        from_username = message_content.get(MessageFields.SENDER_USERNAME)
        text = message_content.get(MessageFields.MESSAGE_TEXT)
        to_print = '"{}" from \x1B[3m{}\x1B[23m'.format(text, from_username)
        print(to_print)

    def group_message(self, message_content):
        from_username = message_content.get(MessageFields.SENDER_USERNAME)
        text = message_content.get(MessageFields.MESSAGE_TEXT)
        group_name = message_content.get(MessageFields.GROUP_NAME)
        to_print = '"{}" from \x1B[3m{}\x1B[23m, in {}'.format(text, from_username, group_name)
        print(to_print)

    def send_message(self):
        text_input = input()
        command_or_user = ''
        text = ''
        message_id = ''

        commands = {
            'create-group': MessageId.CREATE_GROUP,
            'online-users': MessageId.GET_ONLINE_USERS,
            'exit': MessageId.LOG_OUT
        }

        try:
            command_or_user, text = text_input.split(' ', 1)
        except ValueError:
            message_id = commands.get(text_input.strip(), None)


        if command_or_user is not '':
            if command_or_user.strip() == 'create-group':
                group_name, group_members = text.split(' ', 1)
                message = {
                    MessageFields.MESSAGE_ID: MessageId.CREATE_GROUP,
                    MessageFields.MESSAGE_CONTENT: {
                        MessageFields.SENDER_USERNAME: self.username,
                        MessageFields.GROUP_NAME: group_name,
                        MessageFields.GROUP_MEMBERS: group_members.split()
                    }
                }
            elif command_or_user.strip() == 'group':
                group_name, text = text.split(' ', 1)
                message = {
                    MessageFields.MESSAGE_ID: MessageId.GROUP_MESSAGE,
                    MessageFields.MESSAGE_CONTENT: {
                        MessageFields.SENDER_USERNAME: self.username,
                        MessageFields.GROUP_NAME: group_name,
                        MessageFields.MESSAGE_TEXT: text
                    }
                }
            else:
                message = {
                    MessageFields.MESSAGE_ID: MessageId.SEND_MESSAGE,
                    MessageFields.MESSAGE_CONTENT: {
                        MessageFields.SENDER_USERNAME: self.username,
                        MessageFields.RECEIVER_USERNAME: command_or_user.strip(),
                        MessageFields.MESSAGE_TEXT: text
                    }
                }
            self._send_message(message)

        elif message_id is not None:
            message = {
                MessageFields.MESSAGE_ID: message_id,
                MessageFields.MESSAGE_CONTENT: {
                    MessageFields.SENDER_USERNAME: self.username
                }
            }
            self._send_message(message)
        else:
            print('no such command')

    def selector_function(self):
        while True:
            events = self.selector.select()
            for key, mask in events:
                key.data()

    def _send_message(self, message):
        message_to_send = MessageBuilder.make_sendable(message)
        self.writing_connection.send_message(message_to_send, self.broker_address[0])

def main():
    user = SenderReceiver()

    worker = Thread(target=user.selector_function)
    # It will kill the thread when the program exits
    worker.setDaemon(True)
    worker.start()

    while True:
        user.send_message()


if __name__ == '__main__':
    main()
