import selectors
import warnings
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

        self.online_user_list = dict()

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
                MessageFields.USER_LIST: list(self.online_user_list.keys())
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

    def _get_user_address(self, username):
        return self.online_user_list.get(username)

    def _add_new_user(self, username, ip, port):
        if username and ip and port:
            self.online_user_list[username] = (ip, port)
        else:
            warnings.warn('one of the fields username, ip, or port is not set',
                                    username,
                                    ip,
                                    port)


br = Broker()

def amazing_func():
    while True:
        events = br.selector.select()
        for key, mask in events:
            key.data()

worker = Thread(target=amazing_func)
# It will kill the thread when the program exits
worker.setDaemon(True)
worker.start()

while True:
    pass