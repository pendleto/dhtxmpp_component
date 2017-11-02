#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
    protocol: DHT XMPP Component protocol
    See the file LICENSE for copying permission.
"""

from kademlia.protocol import KademliaProtocol
from routing import custom_routing_table

class custom_protocol(KademliaProtocol, object):
    
    def __init__(self, dht, server):
        super(custom_protocol, self).__init__(server.node, server.storage, server.ksize)
        self.router = custom_routing_table(dht, server.protocol.router, server.protocol.router.ksize, server.protocol.router.node)
        self.dht = dht 
        
    @staticmethod         
    def create_msg(from_user_key, to_user_key, msg_body):
        fullmsg = "msg:%s:%s:%s" % (from_user_key, to_user_key, msg_body)
        return fullmsg
    
    @staticmethod         
    def create_presence(user_key, status):
        presence = "prs:%s:%s" % (user_key, status)
        return presence
    
    @staticmethod         
    def crack_msg_type(msg):
        msg_list = msg.split(":")
        msg_type = msg_list[0]
        return msg_type 
    
     
    @staticmethod         
    def crack_msg(msg):
        msg_list = msg.split(':')
        from_user_key = msg_list[1]
        to_user_key = msg_list[2] 
        msg_body = ':'.join(msg_list[3:])
        return from_user_key, to_user_key, msg_body
        
    @staticmethod         
    def crack_presence(msg):
        msg_list = msg.split(":")
        user_key = msg_list[1]
        presence = msg_list[2] 
        return user_key, presence
    
    @staticmethod    
    def create_user_key(user_name, node_id):
        return user_name # + "_" + node_id
                
    def rpc_store(self, sender, nodeid, key, value):
        
        # check if value is meant for this node
        # if it is, then deliver the XMPP message
        # otherwise just store it
        value_str = str(value)
        
        print("RPC_STORE:%s\n" % str(value_str))
               
        self.dht.xmpp.parse_dht_msg(value_str)
        
        super(custom_protocol, self).rpc_store(sender, nodeid, key, value)
