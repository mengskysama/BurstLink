# server
import socket


# client

import socket
import struct
import time

address = ('127.0.0.1', 2333)
s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.connect(address)

sessionid = struct.pack('>I', 8888888)
data_seq = struct.pack('>H', 0)
type = chr(1)
ip = socket.inet_aton('127.0.0.1')
port = struct.pack('>H', 2334)
leng = struct.pack('>H', len(ip+port+type))
s.send(sessionid + data_seq + leng + type + ip + port)


leng = struct.pack('>H', 10)

n = 1
while True:
    data_seq = struct.pack('>H', n)
    n+=1
    s.send(data_seq + leng + '0123456789')
    print s.recv(512)
    time.sleep(1)
