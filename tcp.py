from socket import *
import time
import struct

HOST = '127.0.0.1'
PORT = 23344
BUFSIZ = 1024
ADDR = (HOST, PORT)

tcpCliSock = socket(AF_INET, SOCK_STREAM)
tcpCliSock.connect(ADDR)

sessionid = struct.pack('>I', 8888888)
data_seq = struct.pack('>H', 0)

type = chr(3)
host = 'mdss.mengsky.net'
addrlen = chr(len(host))
port = struct.pack('>H', 80)
data = type + addrlen + host + port
data = data[::-1]
leng = struct.pack('>H', len(data))
tcpCliSock.send(sessionid + data_seq + leng + data)

data_seq = struct.pack('>H', 1)
data = 'GET /bg590.jpg HTTP/1.1\r\nHost: mdss.mengsky.net\r\n\r\n'
data = data_seq + struct.pack('>H', len(data)) + data
tcpCliSock.send(data)

while True:
    time.sleep(1)
    print tcpCliSock.recv(1000)

tcpCliSock.close()