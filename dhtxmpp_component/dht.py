#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
    protocol: DHT XMPP Component dht
    See the file LICENSE for copying permission.
"""

import sys
import asyncio
from kademlia.network import Server
from collections import Counter
from dhtxmpp_component.protocol import custom_protocol

import logging

log = logging.getLogger('dhtxmpp_component')
log.setLevel(logging.DEBUG)
log.addHandler(logging.StreamHandler())

def most_common(lst):
    data = Counter(lst)
    return data.most_common(1)[0][0]

class dhtxmpp_server(Server):
    protocol_class = custom_protocol
    def __init__(self):
        Server.__init__(self)
    
class DHT():

    def __init__(self, bootstrapip, xmpp):
        # log to std out
        self.bootstrapip = bootstrapip
        self.server = dhtxmpp_server()
        self.server.listen(5678)
        self.server.protocol.dht = self        
        self.myip = None
        self.xmpp = xmpp

    def run(self):
        self.loop = asyncio.get_event_loop()
        self.loop.set_debug(True)
        self.loop.run_until_complete(self.server.bootstrap([(self.bootstrapip, 5678)]))
        try:
            self.loop.run_forever()
        except KeyboardInterrupt:
            pass
        finally:
            self.server.stop()
            self.loop.close()

    def quit(self, result):
        log.msg("quit result: %s" % result)
        self.mdns.unregister_dht_with_mdns()
        self.server.stop()
        self.loop.close()

    def done(self, found, server):
        log.msg("Found nodes: %s" % found)

    def set(self, key, value):
        # Create a new loop
        new_loop = asyncio.new_event_loop()
        # Give it some async work
        future = asyncio.run_coroutine_threadsafe(
            self.server.set(key, str(value)), 
            self.loop
            )
                
    def get_visible_ip_callback(self, ip_list, server):
        # check that it got a result back
        # print str(server.node.long_id)
        if not len(ip_list):
            print ("Could not determine my ip")
        if len(ip_list) > 0:
            self.myip = most_common(ip_list)
            print ("found my ip = %s" % str(self.myip))


    def get_visible_ip(self):
        self.server.inetVisibleIP().addCallback(self.get_visible_ip_callback, self.server)

    def findneighbors(self):
        return self.server.bootstrappableNeighbors()