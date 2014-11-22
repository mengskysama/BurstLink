##XXXXXXXXXXXXX######XXXXX###########
#0Seq                     RECV       65535

##XX############XXXXXXXXXXXXXXXXXXXX#
#0 RECV         Seq                  65535

import config

class SeqCache():

    """This Cache is used to cache tunnel seq"""
    def __init__(self, max_len):
        self.get_seq = 0
        self.dct_seq = {}
        self.total_len = 0
        self.max_len = max_len

    def put(self, seq, data):
        """for recv seq"""
        if seq in self.dct_seq:
            raise Exception('seq already in cache')

        self.dct_seq[seq] = data
        self.total_len += len(data)

        if self.total_len > self.max_len:
            raise Exception('cache out of max_len')

    def _next_seq(self):
        return (self.get_seq + 1) % 65535

    def get(self):
        """for recv seq"""
        if self._next_seq() not in self.dct_seq:
            return None
        data = ''
        while True:
            #Not use 0
            #233333333333333333333333333333333333333333333333333333333333333
            data += self.dct_seq[self._next_seq()][::-1]
            del self.dct_seq[self._next_seq()]
            self.get_seq = self._next_seq()
            if self._next_seq() not in self.dct_seq:
                break
        self.total_len -= len(data)
        return data

    def putin(self, data):
        """for send seq"""
        while len(data) > 0:
            if self._next_seq() in self.dct_seq:
                raise Exception('seq already in cache')
            #23333333333333333333333333333333333333333333333333333333333333
            self.dct_seq[self._next_seq()] = data[:config.SEQ_SIZE][::-1]
            self.total_len += len(self.dct_seq[self._next_seq()])
            data = data[config.SEQ_SIZE:]
            #print 'putin seq=',self._next_seq()
            self.get_seq = self._next_seq()

        if self.total_len > self.max_len:
            raise Exception('cache out of max_len')

    def getin(self):
        """for send seq"""
        data = ''
        seq = self.get_seq
        if seq not in self.dct_seq:
            return None
        lst = []
        while True:
            data = self.dct_seq[seq]
            lst.insert(0, [seq, data])
            del self.dct_seq[seq]
            seq = (seq - 1) % 65535
            if seq not in self.dct_seq:
                break
        self.total_len -= len(data)
        return lst

def testin():
    s = SeqCache(30)
    s.putin('1234')
    s.putin('123')
    s.putin('123')
    print s.getin()
    s.putin('33333333333')
    print s.getin()

def test():
    s = SeqCache(300)
    print s.get()
    s.put(1, '1.')
    s.put(2, '222222.')
    s.put(4, '44444.')
    s.put(5, '555.')
    print s.get()
    s.put(3, '333.')
    print s.get()
