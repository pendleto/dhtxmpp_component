'''
Created on Sep 14, 2018

@author: spendleton
'''
import time
import logging
from kademlia.storage import ForgetfulStorage
from collections import OrderedDict

class storage(ForgetfulStorage):

    def __init__(self, ttl=3600):
        """
        By default, max age is an hour.
        """
        ForgetfulStorage.__init__(self, ttl)

    def __setitem__(self, key, value):
        
        logging.debug("ADDING %s to storage" % (value))
        
        if key in self.data:
            values = value.split("|")
            newvalues = []
            for v in values:
                found = False
                for v2 in self.data[key][1].split("|"):
                    if v == v2:
                        logging.debug("VALUE %s already found in storage...skipping" % (v))
                        found = True
                        break
                
                if found == False:
                    newvalues.append(v)  
            
            if len(newvalues) > 0: 
                newvalues.append(self.data[key][1])
                newvalue = "|".join(newvalues)
            else:
                return
            
        else:
            newvalue = value
            
        ForgetfulStorage.__setitem__(self, key, newvalue)