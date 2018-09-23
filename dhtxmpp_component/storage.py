'''
Created on Sep 14, 2018

@author: spendleton
'''
import time
from kademlia.storage import IStorage
from itertools import takewhile
import operator
from collections import OrderedDict

class storage(IStorage):

    def __init__(self, ttl=604800):
        """
        By default, max age is a week.
        """
        self.data = OrderedDict()
        self.ttl = ttl

    def __setitem__(self, key, value):
        if key in self.data:
            self.data[key][1].add(str(value))
        else:
            self.data[key] = (time.time(), storage_value(value))
        self.cull()

    def cull(self):
        for _, _ in self.iteritemsOlderThan(self.ttl):
            self.data.popitem(last=False)
            
        # cull items too
        for value in self.data.values():
            value[1].cull()

    def get(self, key, default=None):
        self.cull()
        if key in self.data:
            return str(self.data[key][1])
        return default

    def __getitem__(self, key):
        self.cull()
        return str(self.data[key][1])

    def __iter__(self):
        self.cull()
        return iter(self.data)

    def __repr__(self):
        self.cull()
        return repr(self.data)

    def iteritemsOlderThan(self, secondsOld):
        minBirthday = time.time() - secondsOld
        zipped = self._tripleIterable()
        matches = takewhile(lambda r: minBirthday >= r[1], zipped)
        return list(map(operator.itemgetter(0, 2), matches))
    
    def _tripleIterable(self):
        ikeys = self.data.keys()
        ibirthday = map(operator.itemgetter(0), self.data.values())
        ivalues = map(operator.itemgetter(1), self.data.values())
        return zip(ikeys, ibirthday, ivalues)
    
    def items(self):
        self.cull()
        ikeys = self.data.keys()
        ivalues = map(operator.itemgetter(1), self.data.values())
        return zip(ikeys, ivalues)
    
class storage_value:
    
    def __init__(self, value, ttl=604800):
        self.data = []
        self.add(value, ttl)      
    
    def add(self, value, ttl=604800):
        self.cull()
        self.data.append ((time.time(), ttl, str(value)))
        
    def cull(self):
        newdata = []
        for data in self.data:
            vtime = data[0]
            vttl = data[1]
            
            if vttl > (time.time() - vtime):
                newdata.append(data)
    
        self.data = newdata
        
    def __str__(self):
        values = []
        for data in self.data:
            values.append(str(data[2]))
            
        return "|".join(values)