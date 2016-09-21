import socket

sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
sock.bind(('0.0.0.0', 0))
sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
sock.sendto('hello, sexy2222222'.encode('utf-8'), ('13.13.13.3', 10001))
sock.sendto('hello, sexy230'.encode('utf-8'), ('13.13.13.4', 10001))