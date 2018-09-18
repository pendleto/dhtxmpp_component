#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
    protocol: DHT XMPP Component dht
    See the file LICENSE for copying permission.
"""

import asyncio
from dhtxmpp_component.server import server
from collections import Counter

import logging

log = logging.getLogger('dhtxmpp_component')
log.setLevel(logging.DEBUG)
log.addHandler(logging.StreamHandler())

def most_common(lst):
    data = Counter(lst)
    return data.most_common(1)[0][0]
    
class DHT():
    
    HEARTBEAT_INTERVAL_SECS = 10
    
    def __init__(self, bootstrapip, xmpp):
        # log to std out
        self.bootstrapip = bootstrapip
        self.server = server()
        self.server.listen(5678)
        self.server.protocol.dht = self        
        self.myip = None
        self.xmpp = xmpp
        self.num_failures = None
        
    def run(self):
        self.num_neighbors = 0
        self.loop = asyncio.get_event_loop()
        self.loop.set_debug(True)
        self.loop.run_until_complete(self.bootstrap())
        self.heartbeat()
        
        try:
            self.loop.run_forever()
        except KeyboardInterrupt:
            pass
        finally:
            logging.debug("CLOSING DHT")
            self.quit()
        
    async def bootstrap(self):
        self.num_failures = None
        await self.server.bootstrap([(self.bootstrapip, 5678)])
        
    def heartbeat(self):
        logging.debug("HEARTBEAT DHT")
        asyncio.ensure_future(self._heartbeat())
        loop = asyncio.get_event_loop()
        self.refresh_loop = loop.call_later(self.HEARTBEAT_INTERVAL_SECS, self.heartbeat)

    async def _heartbeat(self):
        logging.debug("HEARTBEAT DHT START")
        data = {
            'neighbors': self.server.bootstrappableNeighbors()
        }
        if len(data['neighbors']) == 0:
            if self.num_failures == None:
                self.num_failures = 1
            else:
                self.num_failures = self.num_failures + 1  
            logging.debug("No known neighbors. Num failures=%d" %(self.num_failures))         
        else:
            self.num_failures = 0
            logging.debug(str(data))
            
        self.num_neighbors = len(data['neighbors'])
        
        logging.debug("HEARTBEAT DHT END")
        
    def quit(self):
        logging.debug("QUITTING DHT")
        self.refresh_loop.cancel()
        self.server.stop()
        self.loop.stop()
        logging.debug("QUIT DHT")

    def done(self, found, server):
        log.msg("Found nodes: %s" % found)

    async def set(self, key, value):
        # Give it some async work
        logging.debug("SETTING KEY %s ON NETWORK" % (str(key)))
        await self.server.set(key, str(value))
    
    async def get(self, key):
        logging.debug("GETTING KEY %s OFF NETWORK" % (str(key)))
        result = await self.server.get(key)
        logging.debug("GOT VALUE %s OFF NETWORK" % (str(result)))
        return result
                        
    def get_visible_ip_callback(self, ip_list, server):
        # check that it got a result back
        # print str(server.node.long_id)
        if not len(ip_list):
            logging.debug ("Could not determine my ip")
        if len(ip_list) > 0:
            self.myip = most_common(ip_list)
            logging.debug ("found my ip = %s" % str(self.myip))


    def get_visible_ip(self):
        self.server.inetVisibleIP().addCallback(self.get_visible_ip_callback, self.server)

    def findneighbors(self):
        return self.server.bootstrappableNeighbors()
    