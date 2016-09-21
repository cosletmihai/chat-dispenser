import socket


UDP_IP = ""
UDP_PORT = 10001

sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
sock.bind((UDP_IP, UDP_PORT))

# import pdb; pdb.set_trace()
while True:
    data, addr = sock.recvfrom(1024) # buffer size is 1024 bytes
    print("received message: {}".format(data.decode('utf-8')))
