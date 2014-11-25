from socket import *
import time

HOST = '127.0.0.1'
PORT = 56789
BUFSIZ = 1024
ADDR = (HOST, PORT)

tcpCliSock = socket(AF_INET, SOCK_STREAM)
tcpCliSock.connect(ADDR)
tcpCliSock.send('1222')
while True:
    time.sleep(1)
    print tcpCliSock.recv(100)
tcpCliSock.close()