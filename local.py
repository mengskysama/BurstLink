#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# author: mengskysama
# license: GPLv3 (Read COPYING file.)
#

from twisted.internet import reactor
from twisted.internet.protocol import Protocol, ClientFactory, ServerFactory
from sys import stdout
import struct
import socket
import random
import config

import platform
if platform.system() == 'Windows':
    from twisted.internet import iocpreactor
    try:
        #http://sourceforge.net/projects/pywin32/
        iocpreactor.install()
    except:
        pass
else:
    from twisted.internet import epollreactor
    try:
        epollreactor.install()
    except:
        pass

from session import Session

conn = 0
class Server(Protocol):

    def __init__(self, session):
        self.session = session
        self.buf = ''
        self.data_len = 0

    def connectionMade(self):
        global conn
        conn+=1
        print 'conn' , conn
        print 'Server Connected'
        #session id
        self.sendData(struct.pack('>I', self.session.sessionid))
        self.session.add_conn(self)
        #Seq0
        self.session.send_to_tunnel()

    def dataReceived(self, data):
        self.buf += data
        while True:
            if self.data_len == 0:
                if len(self.buf) < 4:
                    return
                self.data_seq = struct.unpack('>H', self.buf[0:2])[0]
                self.data_len = struct.unpack('>H', self.buf[2:4])[0]
                self.buf = self.buf[4:]
            #print len(self.buf)
            #print 'seq %s  len %s' % (self.data_seq, self.data_len)
            #print 'buflen %s' % len(self.buf)
            if len(self.buf) >= self.data_len:
                #recved a full seq data
                #2333333333333333333333333333333333333
                self.session.recv_seqcache.put(self.data_seq, self.buf[:self.data_len][::-1])
                self.buf = self.buf[self.data_len:]
                self.data_len = 0
                self.session.send_to_socks()
            else:
                break

    def sendData(self, data):
        self.transport.write(data)


class ServerFactory(ClientFactory):

    def __init__(self, session):
        self.session = session

    #def startedConnecting(self, connector):
    #    print 'Started to connect.'

    def buildProtocol(self, addr):
        return Server(self.session)

    def clientConnectionLost(self, connector, reason):
        global conn
        conn-=1
        print 'conn' , conn
        print 'Lost server connection.'
        self.session.close_session()

    def clientConnectionFailed(self, connector, reason):
        print 'Connection server failed.'
        self.session.close_session()

#reactor.connectTCP('127.0.0.1', 2333, RemoteFactory(2))
#reactor.connectTCP('127.0.0.1', 2334, RemoteFactory(3))
#reactor.run()


class S5Server(Protocol):

    def __init__(self, dct_session):
        self.dct_session = dct_session
        #stage 1
        #Socks head recv
        self.stage = 0
        self.buf = ''
        #seq data len
        self.session_id = 0

    def connectionMade(self):
        print 'Socks5 connection made'

    def connectionLost(self, reason):
        print 'Socks5 connection lost'
        if self.session_id not in self.dct_session:
            return
        self.dct_session[self.session_id].close_session()

    def dataReceived(self, data):
        self.buf += data
        if self.stage == 3:
            self.dct_session[self.session_id].send_seqcache.putin(self.buf)
            self.dct_session[self.session_id].send_to_tunnel()
            self.buf = ''
            return
        if self.stage == 0:
            if len(self.buf) < 3:
                return
            #+----+----------+----------+
            #|VER | NMETHODS | METHODS  |
            #+----+----------+----------+
            #| 1　|   　1　  | 1 to 255 |
            #+----+----------+----------+
            method = ord(data[2])
            if method != 0:
                print 'S5Server Method Err'
                self.transport.abortConnection()
                return
            self.sendData('\x05\x00')
            self.buf = ''
            self.stage = 1
        elif self.stage == 1:
            if len(self.buf) < 3:
                return
            #+----+-----+-------+------+----------+----------+
            #|VER | CMD |　RSV　| ATYP | DST.ADDR  | DST.PORT |
            #+----+-----+-------+------+----------+----------+
            #| 1　| 　1 | X'00' | 　1　 | Variable |　　 2　　|
            #+----+-----+-------+------+-----------+---------+
            self.buf = self.buf[3:]
            self.stage = 2
        if self.stage == 2:
            addrtype = ord(self.buf[0])
            if addrtype == 1:
                if len(self.buf) >= 7:
                    dest_addr = socket.inet_ntoa(self.buf[1:5])
                    dest_port = struct.unpack('>H', self.buf[5:7])[0]
                    header_length = 7
                else:
                    return
            elif addrtype == 3:
                if len(self.buf) > 2:
                    addrlen = ord(self.buf[1])
                    if len(self.buf) >= 2 + addrlen:
                        dest_addr = self.buf[2:2 + addrlen]
                        dest_port = struct.unpack('>H', self.buf[2 + addrlen:4 + addrlen])[0]
                        header_length = 4 + addrlen
                    else:
                        return
                else:
                    return
            elif addrtype == 4:
                if len(self.buf) >= 19:
                    dest_addr = socket.inet_ntop(socket.AF_INET6, self.buf[1:17])
                    dest_port = struct.unpack('>H', self.buf[17:19])[0]
                    header_length = 19
                else:
                    return
            else:
                print 'S5Server Type Unkown'
                self.transport.abortConnection()
                return
            if dest_addr is None:
                print 'S5Server Recv Unkown Data'
                self.transport.abortConnection()
                return
            self.sendData('\x05\x00\x00\x01\x00\x00\x00\x00\x00\x00')
            #sock5 head done put to seq0
            #random a session id
            self.session_id = random.randint(1, 999999999)
            session = Session(self.dct_session, self.session_id)
            session.socks_conn = self
            self.dct_session[self.session_id] = session
            #connect to server
            for i in range(0, config.SESSION_MAX_TUNNEL):
                reactor.connectTCP(config.SERVER_IP, config.SERVER_PORT, ServerFactory(session))
            session.send_seqcache.dct_seq[0] = self.buf[:header_length]
            self.buf = self.buf[header_length:]
            self.stage = 3


    def sendData(self, data):
        self.transport.write(data)

class S5ServerFactory(ServerFactory):

    def __init__(self):
        self.dct_session = {}

    def buildProtocol(self, addr):
        return S5Server(self.dct_session)

reactor.listenTCP(config.LOCAL_PORT, S5ServerFactory())
reactor.run()
