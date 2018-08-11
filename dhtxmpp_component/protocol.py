#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
    protocol: DHT XMPP Component protocol
    See the file LICENSE for copying permission.
"""

from kademlia.protocol import KademliaProtocol

class custom_protocol(KademliaProtocol):
    
    msg_type_msg = "msg"
    msg_type_prs = "prs"
    def __init__(self, sourceNode, storage, ksize):
        KademliaProtocol.__init__(self, sourceNode, storage, ksize)
        self._waitTimeout = 10
                
    @staticmethod         
    def create_msg(from_user_key, to_user_key, msg_body):
        fullmsg = "%s:%s:%s:%s" % (custom_protocol.msg_type_msg, from_user_key, to_user_key, msg_body)
        return fullmsg
    
    @staticmethod         
    def create_presence(user_key, status):
        presence = "%s:%s:%s" % (custom_protocol.msg_type_prs, user_key, status)
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
        super(custom_protocol, self).rpc_store(sender, nodeid, key, value)
