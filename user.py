import selectors
from threading import Thread

from connection import Connection


class SenderReceiver():
    def __init__(self):
        self.broker_addr = None
        self.writing_connection = Connection(read=False)
        self.reading_connection = Connection(read=True)

        self.selector = selectors.DefaultSelector()
        self.selector.register(self.reading_connection.sock, selectors.EVENT_READ, self.reading_sel)

        message = self.send_login_message()
        print(message)

    def send_login_message(self):
        self.writing_connection.broadcast_message(input('name: ') + str(self.reading_connection.get_port()))
        broker_message, addr = self.reading_connection.receive_message()
        self.broker_addr = addr
        return broker_message

    def reading_sel(self, sock):
        data, addr = sock.recvfrom(1234)
        print(data)


sr = SenderReceiver()

def amazing_func():
    while True:
        events = sr.selector.select()
        for key, mask in events:
            key.data(key.fileobj)

worker = Thread(target=amazing_func)
# It will kill the thread when the program exits
worker.setDaemon(True)
worker.start()

while True:
    print(sr.broker_addr)
    sr.writing_connection.send_message(input(), sr.broker_addr[0])