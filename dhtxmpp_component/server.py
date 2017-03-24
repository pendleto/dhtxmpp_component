#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
    protocol: DHT XMPP Component protocol
    See the file LICENSE for copying permission.
"""

from kademlia.network import Server, NodeSpiderCrawl, Node
from twisted.internet import defer

class custom_server(Server):
    
    def getAllKeyValues(self):
        ds = []
        for key, value in self.storage.iteritems():
            ds.append((key, value))
        return ds
     
    def refreshAllTable(self):
        """
        Refresh buckets 
        """
        ds = []
        for refreshid in self.protocol.getRefreshIDs():
            node = Node(refreshid)
            nearest = self.protocol.router.findNeighbors(node, self.alpha)
            spider = NodeSpiderCrawl(self.protocol, node, nearest, self.ksize, self.alpha)
            ds.append(spider.find())

        def republishKeys(_):
            ds = []
            # Republish keys
            for dkey, value in self.storage.iteritems():
                ds.append(self.set(dkey, value))
            return defer.gatherResults(ds)

        return defer.gatherResults(ds).addCallback(republishKeys)