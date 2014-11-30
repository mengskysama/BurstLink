import config
import struct
from seqcache import SeqCache

#stage 0
#Seq 0 Not recved

#stage 1
#Seq 0 Has benn recved

#stage 2
#All tunnel est

#stage 3
#Session close

class Session():

    """Each socks5 tunnel is a sessin"""
    def __init__(self, dct_session, sessionid):
        self.dct_session = dct_session
        self.sessionid = sessionid
        self.tunnels_conn = []
        self.remote_stream = None
        self.remote_conn = None
        self.socks_conn = None
        self.read_from_remote_called = False
        self.send_to_remote_called = False
        self.tunnel_curr = 0
        self.recv_seqcache = SeqCache(config.SESSION_BUFF_SIZE)
        self.send_seqcache = SeqCache(config.SESSION_BUFF_SIZE)
        self.closed = 0

    def add_conn(self, conn):
        """for server"""
        if len(self.tunnels_conn) > config.SESSION_MAX_TUNNEL:
            return False
        self.tunnels_conn.append(conn)
        return True

    def send_to_socks(self):
        """for server"""
        if self.socks_conn is None:
            return
        data = self.recv_seqcache.get()
        if data is None:
            return
        print data
        self.socks_conn.sendData(data)

    def send_to_tunnel_t(self):
        if len(self.tunnels_conn) == 0:
            return
        lst = self.send_seqcache.getin()
        #print 'send_to_tunnel ', lst
        if lst is None:
            return
        for i in lst:
            #encrypt
            data_seq = struct.pack('>H', i[0])
            data_len = struct.pack('>H', len(i[1]))
            #2333333333333333333333333333333333333333333333333333333333333333333333
            self._send_to_tunnel(data_seq + data_len + i[1][::-1])
            print i[1][::-1]

    def _send_to_tunnel(self, data):
        if self.tunnel_curr >= len(self.tunnels_conn):
            return
        self.tunnels_conn[self.tunnel_curr].sendData(data)
        self.tunnel_curr = (self.tunnel_curr + 1) % len(self.tunnels_conn)

    def close_session(self):
        if self.closed == 1:
            return
        self.closed = 1
        if self.remote_conn is not None:
            self.remote_conn.transport.loseConnection()#abortConnection
        if self.socks_conn is not None:
            self.socks_conn.transport.loseConnection()
        for conn in self.tunnels_conn:
            conn.transport.loseConnection()
        self.tunnels_conn = []
        if self.sessionid in self.dct_session:
            del self.dct_session[self.sessionid]

    def send_to_remote(self):
        """for server"""
        if self.remote_stream is None:
            return
        if self.send_to_remote_called is True:
            return
        #get next seq from loacl
        data = self.recv_seqcache.get()
        if data is None:
            return
        self.send_to_remote_called = True
        self.remote_stream.write(data, self.send_to_remote_callback)
        #now we can try read a seq from tunnel
        #still read now ... bom

    def send_to_remote_callback(self):
        print 'send_to_remote_callback'
        self.send_to_remote_called = False
        self.send_to_remote()
        for conn in self.tunnels_conn:
            print 'try read read_from_tunnel'
            self.read_from_tunnel(conn)

    def read_from_remote(self):
        if self.read_from_remote_called is True:
            print 'read_from_remote but already called'
            return
        #if self.remote_stream is None:
        #    return
        if self.send_seqcache.total_len + config.SEQ_SIZE > self.send_seqcache.max_len:
            #raise Exception('read_from_remote no engouh buff')
            return
        self.read_from_remote_called = True
        print 'read_from_remote'
        self.remote_stream.read_bytes(config.SEQ_SIZE, callback=self.read_from_remote_callback, partial=True)

    def read_from_remote_callback(self, data):
        self.read_from_remote_called = False
        print 'read_from_remote_callback', len(data)
        #put to tunnel send cache
        self.send_seqcache.putin(data)
        conn = self.get_idle_tunnel()
        if conn is not None:
            self.send_to_tunnel(conn)
        #keep read
        self.read_from_remote()

    def get_idle_tunnel(self):
        for conn in self.tunnels_conn:
            if conn.send_to_tunnel_called is False:
                return conn
        return None

    def send_to_tunnel(self, conn):
        if conn.send_to_tunnel_called is True:
            return
        lst = self.send_seqcache.getin(1)
        #print 'send_to_tunnel ', lst
        if lst is None:
            return
        conn.send_to_tunnel_called = True
        for i in lst:
            #encrypt
            data_seq = struct.pack('>H', i[0])
            data_len = struct.pack('>H', len(i[1]))
            #2333333333333333333333333333333333333333333333333333333333333333333333
            conn.stream.write(data_seq + data_len + i[1][::-1], conn.send_to_tunnel_callback)

    def send_to_tunnel_callback(self, conn):
        print 'send_to_tunnel callback'
        conn.send_to_tunnel_called = False
        #keep send
        self.send_to_tunnel(conn)
        #can read some new data
        self.read_from_remote()

    def read_from_tunnel(self, conn):
        if conn.read_from_tunnel_called is True:
            return
        if self.recv_seqcache.total_len + config.SEQ_SIZE > self.recv_seqcache.max_len:
            #raise Exception('read_from_remote no engouh buff')
            return
        conn.read_from_tunnel_called = True
        if conn.data_len == 0:
            print 'read_from_tunnel head'
            conn.stream.read_bytes(4, conn.read_from_tunnel_callback, partial=False)
        else:
            print 'read_from_tunnel len', conn.data_len
            conn.stream.read_bytes(conn.data_len, conn.read_from_tunnel_callback, partial=False)

    def read_from_tunnel_callback(self, conn, data):
        conn.read_from_tunnel_called = False
        #put data into recv_seqcache
        if conn.data_len == 0:
            conn.data_seq = struct.unpack('>H', data[0:2])[0]
            conn.data_len = struct.unpack('>H', data[2:4])[0]
            print 'read_from_tunnel_callback==========', conn.data_seq, conn.data_len
        else:
            print 'read_from_tunnel_callback', str(len(data))
            #bug!!!!!!!!!!!!!!!!!!!!!!!!!!
            data = data[::-1]
            self.recv_seqcache.put(conn.data_seq, data)
            conn.data_seq = 0
            conn.data_len = 0
            #send to remote
            self.send_to_remote()
            #keep read
        self.read_from_tunnel(conn)

