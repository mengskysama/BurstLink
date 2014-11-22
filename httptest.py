import socket
import struct

address = ('127.0.0.1', 2334)
s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.bind(address)
s.listen(5)

ss, addr = s.accept()
print 'got connected from', addr

while True:
    s = ss.recv(512)
    if len(s) > 0:
        print s
    ss.send(s)


ss.close()
