#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
    protocol: DHT XMPP Component protocol
    See the file LICENSE for copying permission.
"""

from kademlia.routing import RoutingTable

class custom_routing_table(RoutingTable):
    
    def __init__(self, dht, router, ksize, node):
        self.dht = dht
        super(custom_routing_table, self).__init__(router, ksize, node)        
                
    def addContact(self, node):
        print ("adding new node %s" % (str(tuple(node))))
        super(custom_routing_table, self).addContact(node)

    def removeContact(self, node):
        super(custom_routing_table, self).removeContact(node)
        