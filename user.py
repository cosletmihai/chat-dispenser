import selectors
import warnings
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
        self.selector.register(self.reading_connection.socket, selectors.EVENT_READ, self.reading_sel)

        message = self.send_login_message()
        print(message)

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
        print(received_message.get(MessageFields.MESSAGE_ID),
              received_message.get(MessageFields.MESSAGE_CONTENT))
        self.broker_address = addr
        return broker_message

    def reading_sel(self):
        data, _ = self.reading_connection.receive_message()
        message = MessageBuilder.make_readable(data)

        message_type = message.get(MessageFields.MESSAGE_ID)
        message_content = message.get(MessageFields.MESSAGE_CONTENT, {})

        try:
            getattr(self, message_type)(message_content)
        except AttributeError:
            pass

    def receive_message(self, message_content):
        from_username = message_content.get(MessageFields.SENDER_USERNAME)
        text = message_content.get(MessageFields.MESSAGE_TEXT)
        print('"{}" from \x1B[3m{}\x1B[3m'.format(text, from_username))


sr = SenderReceiver()

def amazing_func():
    while True:
        events = sr.selector.select()
        for key, mask in events:
            key.data()

worker = Thread(target=amazing_func)
# It will kill the thread when the program exits
worker.setDaemon(True)
worker.start()

while True:
    print(sr.broker_address)
    text_input = input()
    username, text = text_input.split(' ', 1)

    message = {
        MessageFields.MESSAGE_ID: MessageId.SEND_MESSAGE,
        MessageFields.MESSAGE_CONTENT: {
            MessageFields.SENDER_USERNAME: sr.username,
            MessageFields.RECEIVER_USERNAME: username,
            MessageFields.MESSAGE_TEXT: text,
        }
    }
    message_to_send = MessageBuilder.make_sendable(message)
    sr.writing_connection.send_message(message_to_send, sr.broker_address[0])