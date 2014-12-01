from tornado.tcpserver import TCPServer
from tornado.tcpclient import TCPClient
from tornado.iostream import IOStream
import tornado.ioloop

import socket

from session import Session
import struct
import logging

import config

logging.basicConfig(level=logging.DEBUG)


class Socks5Tunnel():

    def __init__(self, server, stream):
        self.server_dct_session = server.dct_session
        self.stream = stream
        self.session = None
        self.remote_stream = None
        self.send_to_tunnel_called = False
        self.read_from_tunnel_called = False
        self.data_seq = 0
        self.data_len = 0
        self.sessionid_read()

    def sessionid_read(self):
        self.stream.read_bytes(4, self.on_sessionid_read)

    def on_sessionid_read(self, data):
        session_id = struct.unpack('>I', data)[0]
        print 'on_sessionid_read',session_id
        #print 'get sissid',session_id
        if session_id not in self.server_dct_session:
            self.server_dct_session[session_id] = Session(self.server_dct_session, session_id)
            #self.session = self.server_dct_session[session_id]
            #self.session.add_conn(self)
            #self.seq_head_read()
        self.session = self.server_dct_session[session_id]
        self.seq_head_read()
            #self.session.read_from_tunnel(self)

    def seq_head_read(self):
        self.stream.read_bytes(4, self.on_seq_head_read, partial=False)

    def on_seq_head_read(self, data):
        self.data_seq = struct.unpack('>H', data[0:2])[0]
        self.data_len = struct.unpack('>H', data[2:4])[0]
        print 'on_seq_head_read', self.data_seq, self.data_len
        if self.data_seq == 0:
            self.stream.read_bytes(self.data_len, self.on_first_seq_read, partial=False)
            self.data_len = 0
        else:
            if self.session.add_conn(self) is False:
                #out of SESSION_MAX_TUNNEL close this
                logging.debug("session out of SESSION_MAX_TUNNEL close")
                self.stream.close()
                return
            #read from tunnel
            self.session.read_from_tunnel(self)

    def on_first_seq_read(self, data):
        data = data[::-1]
        addrtype = ord(data[0])
        if addrtype == 1:
            dest_addr = socket.inet_ntoa(data[1:5])
            dest_port = struct.unpack('>H', data[5:7])[0]
        elif addrtype == 3:
            addrlen = ord(data[1])
            dest_addr = data[2:2 + addrlen]
            dest_port = struct.unpack('>H', data[2 + addrlen:4 + addrlen])[0]
        elif addrtype == 4:
            dest_addr = socket.inet_ntop(socket.AF_INET6, data[1:17])
            dest_port = struct.unpack('>H', data[17:19])[0]
        else:
            print 'wtf'
            self.stream.close()
            return
        print 'Connecting',dest_addr,dest_port
        address = (dest_addr, dest_port)
        self.remote_connect(address, socket.AF_INET6 if addrtype == 4 else socket.AF_INET)
        if self.session.add_conn(self) is False:
            #out of SESSION_MAX_TUNNEL close this
            logging.debug("session out of SESSION_MAX_TUNNEL close")
            self.stream.close()
            return

    def remote_connect(self, address, atype):
        s = socket.socket(atype, socket.SOCK_STREAM)
        self.remote_stream = IOStream(s)
        self.remote_stream.set_close_callback(self.on_remote_close)
        self.remote_stream.connect(address, self.on_remote_connect)

    def on_remote_connect(self):
        print 'remote connected!'
        self.session.remote_stream = self.remote_stream
        #!!
        self.session.send_to_remote()
        #read from remote
        self.session.read_from_remote()
        #read from tunnel
        self.session.read_from_tunnel(self)

    def on_remote_close(self):
        self.session.remote_stream = None
        print 'remote close!'
        pass

    def send_to_tunnel_callback(self):
        self.session.send_to_tunnel_callback(self)

    def read_from_tunnel_callback(self, data):
        self.session.read_from_tunnel_callback(self, data)


class Socks5Session(TCPServer):

    def __init__(self, io_loop=None, **kwargs):
        self.dct_session = {}
        TCPServer.__init__(self, io_loop=io_loop, **kwargs)

    def handle_stream(self, stream, address):
        logging.debug("Local connected %s:%s" % (address[0], address[1]))
        Socks5Tunnel(self, stream)


class BurstServer(object):

    def __init__(self):
        self.address = '127.0.0.1'
        self.port = config.SERVER_PORT

    def server_forever(self):
        try:
            logging.debug("BurstServer Listening on %s:%s" % (self.address, self.port))
            server = Socks5Session()
            server.bind(self.port, self.address)
            server.start()
            tornado.ioloop.IOLoop.instance().start()
        except KeyboardInterrupt:
            tornado.ioloop.IOLoop.instance().stop()

s = BurstServer()
s.server_forever()