import socket

from utils import BROADCAST_PORT


class Broker:
    def __init__(self):
        # Create receiving socket
        self.recv_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.recv_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.recv_sock.bind(('', BROADCAST_PORT))
        # self.recv_sock.setblocking(0)


br = Broker()
while True:
    (data, addr) = br.recv_sock.recvfrom(20)
    print(data.decode('utf-8'), addr)


sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
sock.bind(('0.0.0.0', 0))
sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
sock.sendto('hello, sexy2222222'.encode('utf-8'), ('13.13.13.3', 10001))
sock.sendto('hello, sexy230'.encode('utf-8'), ('13.13.13.4', 10001))

