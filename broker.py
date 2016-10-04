import selectors
from threading import Thread

from connection import Connection
from utils import BROADCAST_PORT, MESSAGE_PORT


class Broker:
    def __init__(self):
        self.writing_connection = Connection(read=False)
        self.reading_connection = Connection(read=True, ip=None, port=MESSAGE_PORT)
        print('lalal', self.reading_connection.get_reading_port())
        self.broadcasting_connection = Connection(True, '', BROADCAST_PORT)
        self.selector = selectors.DefaultSelector()
        self.selector.register(self.broadcasting_connection.sock, selectors.EVENT_READ, self.broad_reading_sel)
        self.selector.register(self.reading_connection.sock, selectors.EVENT_READ, self.reading_sel)

        self.online_user_list = dict()


    def broad_reading_sel(self, sock):
        data, addr = sock.recvfrom(1234)
        print(data, addr)
        new_data = data.decode('utf-8').split(',')
        self.online_user_list[new_data[0]] = (addr[0], int(new_data[1]))
        self.writing_connection.send_message(new_data[0], addr[0], int(new_data[1]))

    def reading_sel(self, sock):
        data, addr = sock.recvfrom(1234)
        data_split = data.decode('utf-8').split(' ', 1)
        ip = self.online_user_list[data_split[0]][0]
        port = self.online_user_list[data_split[0]][1]
        # import ipdb; ipdb.set_trace()
        self.writing_connection.send_message(data_split[1], ip, port)



br = Broker()


def amazing_func():
    while True:
        events = br.selector.select()
        for key, mask in events:
            key.data(key.fileobj)

worker = Thread(target=amazing_func)
# It will kill the thread when the program exits
worker.setDaemon(True)
worker.start()

while True:
    pass