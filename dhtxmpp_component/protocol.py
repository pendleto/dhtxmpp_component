#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
    protocol: DHT XMPP Component protocol
    See the file LICENSE for copying permission.
"""

from kademlia.protocol import KademliaProtocol
import time

#
#
# protoversion:timespoch:msgtype:fromuserkey:(touserkey|presence):msgbody
#

class protocol(KademliaProtocol):
    PROTOCOL_VERSION = 1
    MSG_SEP = '|'


    def __init__(self, sourceNode, storage, ksize):
        KademliaProtocol.__init__(self, sourceNode, storage, ksize)
        self._waitTimeout = 10
     
    @staticmethod         
    def crack_msg(msg):
        
        pmsglist = []
        msglist = msg.split(protocol.MSG_SEP)
        
        for m in msglist:
            pmsg = dhtxmpp_protocol_msg(m)
            pmsglist.append(pmsg)
        return pmsglist
            
    @staticmethod    
    def create_user_key(user_name):
        return user_name
             
    @staticmethod    
    def create_msg_key(user_name, msg_type):
        return user_name + "_" + str(msg_type)   
        
class dhtxmpp_protocol_msg:
    MSG_FIELD_SEP = ':'    
    msg_type_msg = "msg"
    msg_type_prs = "prs"
    
    def __init__(self, msg):
        self.to_user_key = None
        self.msg_body = None
        self.presence = None
        self.from_user_key = None
        self.msg_body = None
        self.msg_type = None
        self.protocol_version = None
        msg_list = msg.split(dhtxmpp_protocol_msg.MSG_FIELD_SEP)
        self.protocol_version = int(msg_list[0])
        self.time_epoch = float(msg_list[1]) 
        self.msg_type = msg_list[2] 
        self.from_user_key = msg_list[3] 
        if self.msg_type == dhtxmpp_protocol_msg.msg_type_msg:            
            self.to_user_key = msg_list[4] 
            self.msg_body = ':'.join(msg_list[5:]) 
        elif self.msg_type == dhtxmpp_protocol_msg.msg_type_prs:  
            self.presence = msg_list[4] 
              
    @staticmethod
    def create_presence_str(user_key, status):
        presence = dhtxmpp_protocol_msg.MSG_FIELD_SEP.join([dhtxmpp_protocol_msg.create_prologue_str(dhtxmpp_protocol_msg.msg_type_prs), user_key, status])
        return presence
                
    @staticmethod
    def create_msg_str(from_user_key, to_user_key, msg_body):
        fullmsg = dhtxmpp_protocol_msg.MSG_FIELD_SEP.join([dhtxmpp_protocol_msg.create_prologue_str(dhtxmpp_protocol_msg.msg_type_msg), from_user_key, to_user_key, msg_body])
        return fullmsg
    
    @staticmethod            
    def create_prologue_str(msg_type):
        prologue = dhtxmpp_protocol_msg.MSG_FIELD_SEP.join([str(protocol.PROTOCOL_VERSION),str(time.time()), msg_type])
        return prologue 
    
        