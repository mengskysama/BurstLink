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


class Remote(Protocol):

    def __init__(self, session):
        self.session = session

    def connectionMade(self):
        print 'Remote Connection Made'
        self.session.remote_conn = self
        self.session.send_to_remote()

    def dataReceived(self, data):
        self.session.send_seqcache.putin(data)
        self.session.send_to_tunnel()

    def sendData(self, data):
        #print data
        self.transport.write(data)


class RemoteFactory(ClientFactory):

    def __init__(self, session):
        self.session = session

    def startedConnecting(self, connector):
        print 'connecting remote'

    def buildProtocol(self, addr):
        return Remote(self.session)

    def clientConnectionLost(self, connector, reason):
        print 'lost remote connection'
        print self.session.sessionid
        self.session.close_session()

    def clientConnectionFailed(self, connector, reason):
        print 'Connecte remote failed:'
        self.session.close_session()

#reactor.connectTCP('127.0.0.1', 2333, RemoteFactory(2))
#reactor.connectTCP('127.0.0.1', 2334, RemoteFactory(3))
#reactor.run()

conn = 0

class Server(Protocol):

    def __init__(self, dct_session):
        self.dct_session = dct_session
        #stage 1
        #First pack head recved
        self.stage = 0
        #data of seq
        self.buf = ''
        #seq data len
        self.data_len = 0
        self.data_seq = 0
        self.session = None

    def connectionMade(self):
        print 'Local connection made'
        global conn
        conn+=1
        print 'conn' , conn

    def connectionLost(self, reason):
        print 'Local connection lost'
        global conn
        conn-=1
        print 'conn' , conn
        if self.session is None:
            return
        self.session.close_session()

    def dataReceived(self, data):
        self.buf += data
        #print 'self.stage=' + str(self.stage)
        if self.stage == 0:
            #print 'buf', self.buf
            if len(self.buf) < 4:
                return
            session_id = struct.unpack('>I', self.buf[0:4])[0]
            #print 'get sissid',session_id
            self.buf = self.buf[4:]
            if session_id not in self.dct_session:
                self.dct_session[session_id] = Session(self.dct_session, session_id)
            session = self.dct_session[session_id]
            if session.add_conn(self) is False:
                #out of SESSION_MAX_TUNNEL close this
                self.abortConnection()
                return
            self.session = session
            self.stage = 1
        if self.stage >= 1:
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
                    #23333333333333333333333333333333
                    self.buf = self.buf[:self.data_len][::-1] + self.buf[self.data_len:]
                    #recved a full seq data
                    if self.data_seq == 0 and self.stage == 1:
                        #Seq 0
                        addrtype = ord(self.buf[0])
                        if addrtype == 1:
                            dest_addr = socket.inet_ntoa(self.buf[1:5])
                            dest_port = struct.unpack('>H', self.buf[5:7])[0]
                        elif addrtype == 3:
                            addrlen = ord(self.buf[1])
                            dest_addr = self.buf[2:2 + addrlen]
                            dest_port = struct.unpack('>H', self.buf[2 + addrlen:4 + addrlen])[0]
                        elif addrtype == 4:
                            dest_addr = socket.inet_ntop(socket.AF_INET6, data[1:17])
                            dest_port = struct.unpack('>H', data[17:19])[0]
                        else:
                            print 'wtf'
                            self.abortConnection()
                            return
                        #Connect to Remote
                        print 'Connecting to %s:%s' % (dest_addr, dest_port)
                        reactor.connectTCP(dest_addr, dest_port, RemoteFactory(self.session))
                        self.buf = self.buf[self.data_len:]
                        self.data_len = 0
                        self.stage = 2
                    else:
                        self.session.recv_seqcache.put(self.data_seq, self.buf[:self.data_len])
                        #print 'red a seq '+ str(self.data_seq) + ' ' + str(len(self.buf[:self.data_len]))
                        self.buf = self.buf[self.data_len:]
                        self.data_len = 0
                        self.session.send_to_remote()
                else:
                    break

    def sendData(self, data):
        self.transport.write(data)

class ServerFactory(ServerFactory):

    def __init__(self):
        self.dct_session = {}

    def buildProtocol(self, addr):
        return Server(self.dct_session)

reactor.listenTCP(config.SERVER_PORT, ServerFactory())
reactor.run()
