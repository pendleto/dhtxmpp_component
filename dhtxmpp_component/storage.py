'''
Created on Sep 14, 2018

@author: spendleton
'''
import logging
import time
from dhtxmpp_component.protocol import protocol
from kademlia.storage import ForgetfulStorage

class storage(ForgetfulStorage):

    def __init__(self, ttl=3600):
        """
        By default, max age is an hour.
        """
        self.msg_ttl = ttl
        ForgetfulStorage.__init__(self, ttl)
        
        
    def cull_msgs(self):
        logging.debug("CULLING storage START")
        ForgetfulStorage.cull(self)
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

                if expired == False:
                    newvalues.append(str(msg))  
            
            if len(newvalues) > 0:
                newvalue = protocol.MSG_SEP.join(newvalues) 
                newkeyvals.append((key, newvalue))
                
         
        for kv in newkeyvals:
            key = kv[0]
            v = kv[1]
            del self.data[key]       
            ForgetfulStorage.__setitem__(self, key, v)
        logging.debug("CULLING storage COMPLETE")
            
            
    def __setitem__(self, key, value):
        self.cull_msgs()
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
            
        ForgetfulStorage.__setitem__(self, key, newvalue)