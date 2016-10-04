import socket
import warnings

from utils import BROADCAST_PORT
from utils import MESSAGE_PORT
from utils import get_local_ip


class SocketCreation:
    def _create_udp_socket(self, is_blocking=True):
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
        ip = ip if ip or ip == '' else get_local_ip()
        port = port if port else 0
        sock.bind((ip, port))
        return sock

    def create_writing_socket(self):
        sock = self._create_udp_socket()
        return sock


class Connection(SocketCreation):
    def __init__(self, read=True, ip=None, port=None):
        self.port = MESSAGE_PORT
        self.read = read
        if read:
            self.socket = self.create_reading_socket(ip, port)
        else:
            self.socket = self.create_writing_socket()

    def broadcast_message(self, message, port=BROADCAST_PORT):
        if not self.read:
            self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
            self.socket.sendto(self._encode(message), ('<broadcast>', port))
            self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 0)
        else:
            warnings.warn('this socket if for listening only')

    def send_message(self, message, ip, port=None):
        if not self.read:
            port = port if port else self.port
            self.socket.sendto(self._encode(message), (ip, port))
        else:
            warnings.warn('this socket if for listening only')

    def receive_message(self):
        if self.read:
            message, addr = self.socket.recvfrom(1000)
            return self._decode(message), addr
        else:
            warnings.warn('this socket if for writing only')

    def get_port(self):
        return self.socket.getsockname()[1]

    def _encode(self, message):
        if not isinstance(message, bytes):
            return message.encode('utf-8')
        return message

    def _decode(self, message):
        if isinstance(message, bytes):
            return message.decode('utf-8')
        return message