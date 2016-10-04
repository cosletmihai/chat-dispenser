import selectors
from threading import Thread

from connection import Connection
from utils import BROADCAST_PORT, MESSAGE_PORT


class Broker:
    def __init__(self):
        self.writing_connection = Connection(read=False)
        self.reading_connection = Connection(read=True, ip=None, port=MESSAGE_PORT)
        self.broadcasting_connection = Connection(True, '', BROADCAST_PORT)

        self.selector = selectors.DefaultSelector()
        self.selector.register(self.broadcasting_connection.sock, selectors.EVENT_READ, self._process_login)
        self.selector.register(self.reading_connection.sock, selectors.EVENT_READ, self._process_receive)

        self.online_user_list = dict()


    def _process_login(self):
        data, addr = self.broadcasting_connection.receive_message()
        new_data = data.split(',')
        self.online_user_list[new_data[0]] = (addr[0], int(new_data[1]))
        self.writing_connection.send_message(new_data[0], addr[0], int(new_data[1]))

    def _process_receive(self):
        data, addr = self.reading_connection.receive_message()
        data_split = data.split(' ', 1)
        ip = self.online_user_list[data_split[0]][0]
        port = self.online_user_list[data_split[0]][1]
        self.writing_connection.send_message(data_split[1], ip, port)


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