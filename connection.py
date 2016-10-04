import socket
import warnings

from utils import BROADCAST_PORT
from utils import MESSAGE_PORT
from utils import get_local_ip


class SocketCreation:
    def _create_udp_socket(self, port=MESSAGE_PORT, is_blocking=True):
        """
        Returns a listening socket
        :param is_blocking:
        :return:
        """
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        if not is_blocking:
            sock.setblocking(False)
        return sock

    def create_reading_socket(self, ip=None, port=None):
        sock = self._create_udp_socket()
        ip = ip if ip else get_local_ip()
        port = port if port else MESSAGE_PORT
        print(ip, port)
        sock.bind((ip, port))
        return sock

    def create_writing_socket(self):
        sock = self._create_udp_socket()
        return sock


class Connection(SocketCreation):
    def __init__(self, read=True):
        self.port = MESSAGE_PORT
        self.read = read
        if read:
            self.sock = self.create_reading_socket()
        else:
            self.sock = self.create_writing_socket()

    def broadcast_message(self, message, port=BROADCAST_PORT):
        if not self.read:
            self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
            self.sock.sendto(message.encode('utf-8'), ('<broadcast>', port))
            self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 0)
        else:
            warnings.warn('this socket if for listening only')

    def send_message(self, ip, message, port=None):
        if not self.read:
            port = port if port else self.port
            self.sock.sendto(message.encode('utf-8'), (ip, port))
        else:
            warnings.warn('this socket if for listening only')

    def receive_message(self):
        if self.read:
            return self.sock.recvfrom(1000)
        else:
            warnings.warn('this socket if for writing only')