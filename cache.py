############X###XXXXXXX####XX########
#0         Min            Max        65535

###X########X###XXXXXXX####XX########
#0 Max     Min                       65535

class Cache():
    """This Cache is used to cache tunnel seq"""
    def __init__(self, max_szie = 1 * 1024 * 1024):
        self.get_seq = 0
        self.dct_seq = {}
        self.total_len = 0
        self.max_szie = max_szie

    def put(self, seq, data):
        if seq in self.dct_seq:
            Exception('seq already in cache')

        self.dct_seq = data
        self.total_len += len(data)

        if self.total_len > self.max_szie:
            Exception('cache out of max_szie')

    def next_seq(self):
        return (self.get_seq + 1) % 65535

    def get(self):
        if self.next_seq() not in self.dct_seq:
            return None
        data = ''
        while True:
            #Not use 0
            data += self.dct_seq[self.next_seq()]
            self.get_seq = self.next_seq()
            if self.next_seq() not in self.dct_seq:
                break
        self.total_len -= len(data)
        return data



