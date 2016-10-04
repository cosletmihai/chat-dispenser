import selectors

from connection import Connection
from utils import BROADCAST_PORT, MESSAGE_PORT


class Broker:
    def __init__(self):
        self.writing_connection = Connection(read=False)
        self.reading_connection = Connection(read=True)
        self.broadcasting_connection = Connection(True, '', BROADCAST_PORT)
        self.selector = selectors.DefaultSelector()
        self.selector.register(self.broadcasting_connection.sock, selectors.EVENT_READ, self.reading_sel)

    def reading_sel(self, sock):
        data, addr = sock.recvfrom(1234)
        print(data, addr)
        new_data = data.decode('utf-8').split(',')
        self.writing_connection.send_message(new_data[0], addr[0], int(new_data[1]))



br = Broker()
while True:
    events = br.selector.select()
    for key, mask in events:
        key.data(key.fileobj)
