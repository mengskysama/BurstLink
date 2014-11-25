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


class Socks5Session(TCPServer):

    def __init__(self, server, io_loop=None, **kwargs):
        self.server_dct_session = server.dct_session
        self.stream = None
        self.session = None
        self.remote_stream = None
        self.send_to_remote_callback = None
        self.read_from_remote_called = False
        TCPServer.__init__(self, io_loop=io_loop, **kwargs)

    def handle_stream(self, stream, address):
        self.stream = stream
        logging.debug("Local connected %s:%s" % (address[0], address[1]))
        self.sessionid_read()

    def sessionid_read(self):
        self.stream.read_bytes(4, self.on_sessionid_read)

    def on_sessionid_read(self, data):
        session_id = struct.unpack('>I', data)[0]
        #print 'get sissid',session_id
        if session_id not in self.dct_session:
            self.dct_session[session_id] = Session(self.dct_session, session_id)
        session = self.dct_session[session_id]
        if session.add_conn(self) is False:
            #out of SESSION_MAX_TUNNEL close this
            logging.debug("session out of SESSION_MAX_TUNNEL close")
            self.stream.close()
        self.session = session
        self.seq_head_read()

    def seq_head_read(self):
        self.stream.read_bytes(4, self.on_seq_head_read)

    def on_seq_head_read(self, data):
        data_seq = struct.unpack('>H', data[0:2])[0]
        data_len = struct.unpack('>H', data[2:4])[0]
        call = self.on_seq_read
        if data_seq == 0:
            call = self.on_first_seq_read
        self.stream.read_bytes(data_len, call)

    def on_seq_read(self, data):
        pass

    def on_first_seq_read(self, data):
        addrtype = ord(self.data[0])
        if addrtype == 1:
            dest_addr = socket.inet_ntoa(self.data[1:5])
            dest_port = struct.unpack('>H', self.data[5:7])[0]
        elif addrtype == 3:
            addrlen = ord(self.data[1])
            dest_addr = self.data[2:2 + addrlen]
            dest_port = struct.unpack('>H', self.data[2 + addrlen:4 + addrlen])[0]
        elif addrtype == 4:
            dest_addr = socket.inet_ntop(socket.AF_INET6, data[1:17])
            dest_port = struct.unpack('>H', data[17:19])[0]
        else:
            print 'wtf'
            self.stream.close()
            return
        address = (dest_addr, dest_port)
        self.remote_connect(address, socket.AF_INET6 if addrtype == 4 else socket.AF_INET)

    def remote_connect(self, address, atype):
        s = socket.socket(atype, socket.SOCK_STREAM)
        self.remote_stream = IOStream(s)
        self.remote_stream.set_close_callback(self.on_remote_close)
        self.remote_stream.connect(address, self.on_remote_connect)

    def on_remote_connect(self):
        print 'remote connected!'
        self.session.remote_conn = self
        self.send_to_remote()

    def on_remote_close(self):
        print 'remote close'
        pass

    def send_to_remote(self):
        self.session.send_to_remote()

    def on_send_to_remote(self):
        self.send_to_remote()

    def read_from_remote(self):
        if self.session.read_from_remote_called is True:
            return
        if self.session.send_seqcache.total_len + config.SEQ_SIZE > self.session.send_seqcache.max_len:
            return
        self.read_from_remote_called = True
        self.stream.read_bytes(config.SEQ_SIZE, callback=self._on_read_from_remote, partial=True)

    def _on_read_from_remote(self, data):
        self.session.session.read_from_remote_called = False
        self.session.send_seqcache.putin(data)

    def send_to_tunnel(self):
        self.session.send_to_tunnel()

    def on_send_to_tunnel(self):
        





class BurstServer(object):

    def __init__(self):
        self.dct_session = {}
        self.address = '127.0.0.1'
        self.port = '56789'

    def server_forever(self):
        try:
            logging.debug("BurstServer Listening on %s:%s" % (self.address, self.port))
            server = Socks5Session(self)
            server.bind(self.port, self.address)
            server.start()
            tornado.ioloop.IOLoop.instance().start()
        except KeyboardInterrupt:
            tornado.ioloop.IOLoop.instance().stop()

s = BurstServer()
s.server_forever()