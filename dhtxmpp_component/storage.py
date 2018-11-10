'''
Created on Sep 14, 2018

@author: spendleton
'''
import logging
import time
from itertools import takewhile
import operator
from collections import OrderedDict
from dhtxmpp_component.protocol import protocol
from kademlia.storage import IStorage

class storage(IStorage):

    def __init__(self, ttl=3600):
        """
        By default, max age is an hour.
        """
        self.msg_ttl = ttl
        self.data = OrderedDict()
        self.ttl = ttl

    def cull(self):
        logging.debug("CULLING storage START")
        for _, _ in self.iteritemsOlderThan(self.ttl):
            self.data.popitem(last=False)
        self.cull_msgs()
        logging.debug("CULLING storage COMPLETE")

    def get(self, key, default=None):
        if key in self.data:
            return self[key]
        return default

    def __getitem__(self, key):
        return self.data[key][1]

    def __iter__(self):
        return iter(self.data)

    def __repr__(self):
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
        ikeys = self.data.keys()
        ivalues = map(operator.itemgetter(1), self.data.values())
        return zip(ikeys, ivalues)
        
    def cull_msgs(self):
 
        newkeyvals = []
        for key in self.data.keys():
            value = self.data[key][1]
            msgs = protocol.crack_msg(value)
            newvalues = []
            for msg in msgs:
                t = msg.time_epoch
                expired = False
                
                if (time.time() - int(t)) > self.msg_ttl:
                    expired = True
                    logging.debug("CULLING MESSAGE: %s WITH TIME %d TTL: %d" % (str(msg), t, self.msg_ttl))

                if expired == False:
                    newvalues.append(str(msg))  
            
            if len(newvalues) > 0:
                newvalue = protocol.MSG_SEP.join(newvalues) 
                newkeyvals.append((key, newvalue))
                
         
        for kv in newkeyvals:
            key = kv[0]
            v = kv[1]
            del self.data[key]       
            self.__setitem__(key, v)
            
    def __setitem__(self, key, value):
        logging.debug("ADDING %s to storage" % (value))
        
        if key in self.data:
            values = value.split(protocol.MSG_SEP)
            newvalues = []
            for v in values:
                found = False
                for v2 in self.data[key][1].split(protocol.MSG_SEP):
                    if v == v2:
                        logging.debug("VALUE %s already found in storage...skipping" % (v))
                        found = True
                        break
                
                if found == False:
                    newvalues.append(v)  
            
            if len(newvalues) > 0: 
                newvalues.append(self.data[key][1])
                newvalue = protocol.MSG_SEP.join(newvalues)
            else:
                return
            
        else:
            newvalue = value
            
        if key in self.data:
            del self.data[key]
        self.data[key] = (time.time(), newvalue)