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
        self.stage = 0
        self.sessionid = sessionid
        self.tunnels_conn = []
        self.remote_conn = None
        self.socks_conn = None
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

    def _send_to_tunnel(self, data):
        if self.tunnel_curr >= len(self.tunnels_conn):
            return
        self.tunnels_conn[self.tunnel_curr].sendData(data)
        self.tunnel_curr = (self.tunnel_curr + 1) % len(self.tunnels_conn)

    def send_to_tunnel(self):
        if len(self.tunnels_conn) == 0:
            return
        lst = self.send_seqcache.getin()
        if lst is None:
            return
        for i in lst:
            #encrypt
            data_seq = struct.pack('>H', i[0])
            data_len = struct.pack('>H', len(i[1]))
            #2333333333333333333333333333333333333333333333333333333333333333333333
            self._send_to_tunnel(data_seq + data_len + i[1][::-1])

    def send_to_remote(self):
        """for server"""
        if self.remote_conn is None:
            return
        data = self.recv_seqcache.get()
        if data is None:
            return
        self.remote_conn.sendData(data)

    def send_to_socks(self):
        """for server"""
        if self.socks_conn is None:
            return
        data = self.recv_seqcache.get()
        if data is None:
            return
        self.socks_conn.sendData(data)

    def close_session(self):
        if self.closed == 1:
            return
        self.closed = 1
        if self.remote_conn is not None:
            self.remote_conn.transport.abortConnection()#abortConnection
        if self.socks_conn is not None:
            self.socks_conn.transport.abortConnection()
        for conn in self.tunnels_conn:
            conn.transport.abortConnection()
        self.tunnels_conn = []
        del self.dct_session[self.sessionid]