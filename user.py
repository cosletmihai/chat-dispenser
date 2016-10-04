import socket

from connection import Connection
from utils import BROADCAST_PORT


UDP_IP = ""
UDP_PORT = 10004


class SenderReceiver(Connection):
    def __init__(self):
        # Create broadcasting socket
        self.broad_sock = self.create_socket()
        self.broad_sock.bind(('', 0))
        self.broad_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.broad_sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        # self.broad_sock.setblocking(0)



sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
sock.bind((UDP_IP, UDP_PORT))

sr = SenderReceiver()
sr.broad_sock.sendto("lalalal".encode('utf-8'), ('<broadcast>', BROADCAST_PORT))

while True:
    data, addr = sock.recvfrom(1024) # buffer size is 1024 bytes
    print("received message: {} {}".format(data.decode('utf-8'), str(addr)))
