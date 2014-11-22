#23333

from twisted.internet import reactor
from twisted.internet.protocol import Protocol, ClientFactory, ServerFactory
from sys import stdout
import struct
import socket

from session import Session


class Remote(Protocol):

    def __init__(self, session):
        self.session = session

    def connectionMade(self):
        self.session.send_to_remote()

    def dataReceived(self, data):
        self.session.seqcache.send_seqcache.put(data)
        self.session.send_to_tunnel()

    def sendData(self, data):
        self.transport.write(data)

class RemoteFactory(ClientFactory):

    def __init__(self, session):
        self.session = session

    def startedConnecting(self, connector):
        print 'Started to connect.'

    def buildProtocol(self, addr):
        print 'Remote Connected.'
        r = Remote(self.session)
        self.session.remote_conn = r
        self.session.send_to_remote()
        return r

    def clientConnectionLost(self, connector, reason):
        print 'Lost connection.  Reason:', reason
        self.session.close_session()

    def clientConnectionFailed(self, connector, reason):
        print 'Connection failed. Reason:', reason
        self.session.close_session()

#reactor.connectTCP('127.0.0.1', 2333, RemoteFactory(2))
#reactor.connectTCP('127.0.0.1', 2334, RemoteFactory(3))
#reactor.run()



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
        self.session_id = 0

    def connectionMade(self):
        print 'connectionMade'

    def connectionLost(self, reason):
        print 'connectionLost', reason
        if self.session_id not in self.dct_session:
            return
        self.dct_session[self.session_id].close_session()

    def dataReceived(self, data):
        self.buf += data
        if self.stage == 0:
            if len(self.buf) < 4:
                return
            self.session_id = struct.unpack('>I', self.buf[0:4])[0]
            self.buf = self.buf[4:]
            if self.session_id not in self.dct_session:
                self.dct_session[self.session_id] = Session(self.session_id)
            session = self.dct_session[self.session_id]
            if session.add_conn(self) is False:
                #out of SESSION_MAX_TUNNEL close this
                self.abortConnection()
                return
            self.stage = 1
        if self.stage == 1:
            while True:
                if self.data_len == 0:
                    if len(self.buf) < 4:
                        return
                    self.data_seq = struct.unpack('>H', self.buf[0:2])[0]
                    self.data_len = struct.unpack('>H', self.buf[2:4])[0]
                    print len(self.buf)
                    print self.data_seq, self.data_len
                    self.buf = self.buf[4:]
                if len(self.buf) >= self.data_len:
                    #recved a full seq data
                    if self.data_seq == 0:
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
                        #Connect to Remote
                        print 'Connecting to %s:%s' % (dest_addr, dest_port)
                        reactor.connectTCP(dest_addr, dest_port, RemoteFactory(self.dct_session[self.session_id]))
                        self.buf = self.buf[self.data_len:]
                        self.data_len = 0
                    else:
                        self.dct_session[self.session_id].recv_seqcache.put(self.data_seq, self.buf[:self.data_len])
                        self.buf = self.buf[self.data_len:]
                        self.data_len = 0
                        self.dct_session[self.session_id].send_to_remote()
                else:
                    break

        #pass
        #reactor.connectTCP('tb.mengsky.net', 2333, RemoteFactory())
        #reactor.run()

    def sendData(self, data):
        self.transport.write(data)


class ServerFactory(ServerFactory):

    def __init__(self):
        self.dct_session = {}

    def buildProtocol(self, addr):
        return Server(self.dct_session)

reactor.listenTCP(2333, ServerFactory())
reactor.run()
