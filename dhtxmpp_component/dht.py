#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
    protocol: DHT XMPP Component dht
    See the file LICENSE for copying permission.
"""

import sys
from twisted.internet import reactor
from collections import Counter
from protocol import custom_protocol
from twisted.python import log
from server import custom_server

def most_common(lst):
    data = Counter(lst)
    return data.most_common(1)[0][0]

class DHT():

    def __init__(self, bootstrapip, xmpp):
        # log to std out
        log.startLogging(sys.stdout)
        self.server = custom_server()
        self.server.protocol = custom_protocol(self, self.server)
        self.server.listen(5678)
        self.server.bootstrap([(bootstrapip, 5678)]).addCallback(self.bootstrapDone, self.server)
        self.myip = None
        self.xmpp = xmpp

    def run(self):
        reactor.run()

    def quit(self, result):
        log.msg("quit result: %s" % result)
        self.mdns.unregister_dht_with_mdns()
        reactor.stop()

    def done(self, found, server):
        log.msg("Found nodes: %s" % found)

    def get_visible_ip_callback(self, ip_list, server):
        # check that it got a result back
        # print str(server.node.long_id)
        if not len(ip_list):
            print "Could not determine my ip"
        if len(ip_list) > 0:
            self.myip = most_common(ip_list)
            print ("found my ip = %s" % str(self.myip))


    def get_visible_ip(self):
        self.server.inetVisibleIP().addCallback(self.get_visible_ip_callback, self.server)

    def bootstrapDone(self, found, server):
        if len(found) == 0:
            print "Could not connect to the bootstrap server."
            reactor.stop()
            exit(0)

    def findneighbors(self):
        return self.server.bootstrappableNeighbors()