#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
    dhtxmpp_component: DHT XMPP Component
    See the file LICENSE for copying permission.
"""

import sys
import logging
import asyncio

from sleekxmpp.componentxmpp import ComponentXMPP
from sleekxmpp import JID, jid
from sleekxmpp.xmlstream.handler import Callback
from sleekxmpp.xmlstream.matcher import StanzaPath

from collections import Counter

from dhtxmpp_component.protocol import protocol, dhtxmpp_protocol_msg
from dhtxmpp_component.dht import DHT
from dhtxmpp_component.mdns import mdns_service

def most_common(lst):
    data = Counter(lst)
    return data.most_common(1)[0][0]

# Python versions before 3.0 do not use UTF-8 encoding
# by default. To ensure that Unicode is handled properly
# throughout SleekXMPP, we will set the default encoding
# ourselves to UTF-8.
if sys.version_info < (3, 0):
    reload(sys)
    sys.setdefaultencoding('utf-8')
else:
    raw_input = input

def create_jid(user_key):
    j = JID()
    j.user = str(user_key)
    j.domain = "mesh.localhost"
    #j.resource = str(node_id)
    return j
            
class dhtxmpp_component(ComponentXMPP):

    """
    A XMPP component routes messages through a DHT.
    """
    HEARTBEAT_INTERVAL_SECS = 10
    def __init__(self, jid, secret, server, port, bootstrapip):
        ComponentXMPP.__init__(self, jid, secret, server, port)

        # You don't need a session_start handler, but that is
        # where you would broadcast initial presence.

        # The message event is triggered whenever a message
        # stanza is received. Be aware that that includes
        # MUC messages and error messages.
        self.bootstrapip = bootstrapip
        self.local_jid = None
        self.local_user_key = None
        self.last_msg_delivery_time_epoch = {}   
        self.last_prs_delivery_time_epoch = {} 
        
    def run(self):        
        try:
                registered_dht_with_mdns = False
                self.mdns = mdns_service()
                bootstrapip = self.bootstrapip        
                if self.bootstrapip == None:
                    # Run the mdns to discover dht
                    dht_address = self.mdns.listen_for_service()
                    logging.debug("LISTENED FOR DHT GOT ADDRESS %s" % (str(dht_address)))        
                    if dht_address == None:                
                        bootstrapip = "127.0.0.1"
                    else:
                        bootstrapip = str(dht_address)
                    if bootstrapip == "127.0.0.1":
                        registered_dht_with_mdns = True
                        self.mdns.register_dht_with_mdns()
                                   
                self.dht = DHT(bootstrapip, self)
                self.add_event_handler('presence_probe', self.handle_probe)
                self.add_event_handler("message", self.message)
                self.add_event_handler("presence_available", self.presence_available)
                self.add_event_handler("presence_unavailable", self.presence_unavailable)
                self.add_event_handler('disco_info', self.disco_info)        
                self.register_handler(Callback('Disco Info', StanzaPath('iq/disco_info'), self.disco_info))
                                
                self.heartbeat()
                self.dht.run()

                self.refresh_loop.cancel()
                
                if registered_dht_with_mdns == True:
                    self.mdns.unregister_dht_with_mdns()
                    
        except KeyboardInterrupt:
            pass
        finally:
            logging.debug("CLOSING COMPONENT")
            self.dht.quit() 
    
   
    def heartbeat(self):
        logging.debug("HEARTBEAT COMPONENT")
        asyncio.ensure_future(self._heartbeat())
        loop = asyncio.get_event_loop()
        self.refresh_loop = loop.call_later(self.HEARTBEAT_INTERVAL_SECS, self.heartbeat)

    async def _heartbeat(self):
        logging.debug("HEARTBEAT COMPONENT START")

        if self.dht.num_failures == 10:
            await self.dht.bootstrap()
            
        elif self.dht.num_failures == 0:
            
            if self.local_jid != None:
                #get all the messages
                msg_key = protocol.create_msg_key(str(self.local_jid.user), dhtxmpp_protocol_msg.msg_type_msg)
                logging.debug("GETTING MESSAGES FOR %s" % (str(msg_key)))
                msg = await self.get_msg_from_dht(msg_key)
        
                if msg != None:
                    self.parse_dht_msg(msg)
                else:
                    logging.debug("NO MESSAGES FOUND FOR %s" % (str(msg_key)))
                    
                    
                msg_key = protocol.create_msg_key("all", dhtxmpp_protocol_msg.msg_type_prs)
                logging.debug("GETTING ALL PRESENCES FOR %s" % (str(msg_key)))
                msg = await self.get_msg_from_dht(msg_key)
        
                if msg != None:
                    self.parse_dht_msg(msg)
                else:
                    logging.debug("NO PRESENCES FOUND FOR %s" % (str(msg_key)))
                    
        logging.debug("HEARTBEAT COMPONENT END")
         
    def message(self, msg):
        """
        Process incoming message stanzas. Be aware that this also
        includes MUC messages and error messages. It is usually
        a good idea to check the messages's type before processing
        or sending replies.

        Since a component may send messages from any number of JIDs,
        it is best to always include a from JID.

        Arguments:
            msg -- The received message stanza. See the documentation
                   for stanza objects and the Message stanza to see
                   how it may be used.
        """
        # The reply method will use the messages 'to' JID as the
        # outgoing reply's 'from' JID.
        to_jid = JID(msg['to'])
        from_jid = JID(msg['from'])
        # strip off the server
        msg_body = msg['body']

        to_user_key = protocol.create_user_key(str(to_jid.user))
        from_user_key = protocol.create_user_key(str(from_jid.user))   
        logging.debug("SENDING MESSAGE TO KEY: %s=%s" % (str(to_user_key), str(msg_body)))
        fullmsg = dhtxmpp_protocol_msg.create_msg_str(from_user_key, to_user_key, msg_body)
        msg_key = protocol.create_msg_key(str(to_jid.user), dhtxmpp_protocol_msg.msg_type_msg)
        self.send_msg_to_dht(msg_key, fullmsg)        
        
    def presence_available(self, presence):
        """
        Process incoming presence stanzas. 
        Arguments:
            presence -- The received message stanza.
        """
        # The reply method will use the messages 'to' JID as the
        # outgoing reply's 'from' JID.
        from_jid = JID(presence['from'])
        self.local_jid = from_jid
        self.local_user_key = protocol.create_user_key(str(from_jid.user))   
        logging.debug("got presence from: %s" % (str(from_jid)))
        self.sendPresence(pshow='available', pto=from_jid)
        # go through all items in the component roster send the presence ones to the local client
        self.send_roster()
        
        #loop = asyncio.new_event_loop()
        #asyncio.set_event_loop(loop)
        #loop.run_until_complete(self.get_roster_presence())
        
        #self.dht.server.refreshAllTable()
        self.publish_jid_to_dht()

    def presence_unavailable(self, presence):
        """
        Process incoming presence stanzas. 
        Arguments:
            presence -- The received message stanza.
        """
        # The reply method will use the messages 'to' JID as the
        # outgoing reply's 'from' JID.
        from_jid = JID(presence['from'])        
        logging.debug("got unpresence from: %s" % (str(from_jid)))
        self.unpublish_jid_to_dht() 
        self.local_jid = None
        self.local_user_key = None
               
    def disco_info(self, iq):
        from_jid = JID(iq['from'])
        logging.debug("got disco_info from: %s" % (str(from_jid)))
        #component_jid = JID("mesh.localhost")
        #self.send_presence_subscription(pto=from_jid, pfrom=component_jid)     
        
                
    def on_available_jid_from_dht(self, from_jid):
        # a new jid is found on the network
        # send it to the local client
        if from_jid == None:
            logging.debug("Couldn't find JID")
            return
        logging.debug("New JID %s found on DHT" % (str(from_jid)))
        to_jid = self.local_jid
        
        # Go through the jids on our roster and send their presences to 
        # the local jid
        
        # check if this jid is already on our roster
        existing = self.client_roster.has_jid(from_jid)
        if existing == True:
            logging.debug("%s already exists in our roster" % (str(from_jid)))
            self.sendPresence(pshow='available', pto=to_jid, pfrom=from_jid)
            presence = self.make_presence(pshow='available', pfrom=from_jid)
            self.client_roster[from_jid].handle_available(presence)
            return

        if to_jid != None:
            logging.debug("Sending presence subscription to %s from %s" % (str(to_jid), str(from_jid)))
            self.send_presence_subscription(pto=to_jid, pfrom=from_jid)
            #self.sendPresence(pshow='available', pto=to_jid, pfrom=mesh_jid)
            self.client_roster.add(str(from_jid))
        else:
            logging.debug ("Could not send presence because local_jid was not set") 
                                  
    def on_unavailable_jid_from_dht(self, from_jid):
        # a jid has left the network
        # send it to the local client
        if from_jid == None:
            logging.debug("Couldn't find JID")
            return
        logging.debug("JID %s left the DHT" % (str(from_jid)))
        to_jid = self.local_jid
        # check if this jid is already on our roster
        existing = self.client_roster.has_jid(from_jid)
        if existing == False:
            logging.debug("%s doesn't exist in our roster" % (str(from_jid)))
            return
    
        if to_jid != None:
            logging.debug("Sending unavailable presence to %s from %s" % (str(to_jid), str(from_jid)))
            self.sendPresence(pshow='unavailable', pto=to_jid, pfrom=from_jid)
            #self.client_roster.remove(str(from_jid))
            presence = self.make_presence(pshow='unavailable', pfrom=from_jid)
            self.client_roster[from_jid].handle_unavailable(presence)
        else:
            logging.debug ("Could not send unavailable presence because local_jid was not set")   
  
    async def get_roster_presence(self):
        groups = self.client_roster.groups()
        for group in groups:
            for jid in groups[group]:
                sub = self.client_roster[jid]['subscription']
                name = self.client_roster[jid]['name']
                if self.client_roster[jid]['name']:
                    logging.debug(' ROSTER %s (%s) [%s]' % (name, jid, sub))
                else:
                    logging.debug(' ROSTER %s [%s]' % (jid, sub))

                #get all the messages
                msg_key = protocol.create_msg_key(JID(jid).user, dhtxmpp_protocol_msg.msg_type_prs)
                logging.debug("GETTING PRESENCE FOR %s" % (str(msg_key)))
                msg = await self.get_msg_from_dht(msg_key)
                
                if msg != None:
                    self.parse_dht_msg(msg)
        
    def send_roster(self):
        groups = self.client_roster.groups()
        for group in groups:
            for jid in groups[group]:
                sub = self.client_roster[jid]['subscription']
                name = self.client_roster[jid]['name']
                if self.client_roster[jid]['name']:
                    logging.debug(' %s (%s) [%s]' % (name, jid, sub))
                else:
                    logging.debug(' %s [%s]' % (jid, sub))

                connections = self.client_roster.presence(jid)
                for res, pres in connections.items():
                    show = 'available'
                    if pres['show']:
                        show = pres['show']
                    logging.debug('   - %s (%s)' % (res, show))
                    status = "available"
                    if pres['status']:
                        status = pres['status']
                    from_jid = create_jid(JID(jid).user)
                    logging.debug("SENDING ROSTER PRESENCE TO %s FROM %s WITH STATUS %s" % (str(self.local_jid), str(from_jid), str(status)))
                    self.sendPresence(pshow=show, pto=self.local_jid, pfrom=from_jid, pstatus=status)
                                 
    def handle_probe(self, presence):
        sender = presence['from']
        # Populate the presence reply with the agent's current status.
        self.sendPresence(pto=sender, pstatus="online", pshow="online")
                
    def publish_jid_to_dht(self):
        if self.local_jid != None:            
            # publish jid.user and node.id
            msg_key = protocol.create_msg_key("all", dhtxmpp_protocol_msg.msg_type_prs)
            user_key = protocol.create_user_key(str(self.local_jid.user))
            msg = dhtxmpp_protocol_msg.create_presence_str(user_key, "available")
            logging.debug("SET DHT KEY: %s=%s" % (str(user_key), str(msg)))
            self.send_msg_to_dht(msg_key, msg) 
        else:
            logging.debug("LOCAL JID NOT KNOWN YET. NOT PUBLISHING PRESENCE")      
            
    def unpublish_jid_to_dht(self):
        if self.local_jid != None:            
            # publish jid.user and node.id
            msg_key = protocol.create_msg_key("all", dhtxmpp_protocol_msg.msg_type_prs)
            user_key = protocol.create_user_key(str(self.local_jid.user))
            msg = dhtxmpp_protocol_msg.create_presence_str(user_key, "unavailable")
            logging.debug("SET DHT KEY: %s=%s" % (str(user_key), str(msg)))
            self.send_msg_to_dht(msg_key, msg) 
        else:
            logging.debug("LOCAL JID NOT KNOWN YET. NOT PUBLISHING PRESENCE")    
            
 
    def send_msg_to_dht(self, to, msg):
        logging.debug("SETTING DHT MSG TO %s" % (str(to)))
        key = to #hashlib.sha1(str(to).encode('utf-8')).digest() 
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        result = loop.run_until_complete(self.dht.set(key, str(msg)))
        return result
 
    async def get_msg_from_dht(self, jid):
        logging.debug("GETTING DHT MSG FOR %s" % (str(jid)))
        key = jid #hashlib.sha1(str(jid).encode('utf-8')).digest()
        msg = await self.dht.get(key)
        return msg
                          
    def parse_dht_msg(self, value_str):         
        logging.debug("PARSING DHT XMPP MESSAGE %s" % (value_str)) 
        pmsglist = protocol.crack_msg(value_str)
        
        for pmsg in pmsglist:
            msg_type = pmsg.msg_type
            logging.debug("PARSING DHT XMPP MESSAGE TYPE %s" % (msg_type)) 
            if msg_type != None:
  
                if msg_type == dhtxmpp_protocol_msg.msg_type_msg:              
                    logging.debug("XMPP MESSAGE TYPE TO %s LOCAL %s" % (pmsg.to_user_key, self.local_user_key))               
                    # if this msg is destined for this node
                    if (pmsg.to_user_key == self.local_user_key):
                        from_jid = create_jid(pmsg.from_user_key)
                        # if last delivery time from this jid < current msg time
                        if pmsg.time_epoch > self.last_msg_delivery_time_epoch.get(from_jid, 0):
                            self.last_msg_delivery_time_epoch[from_jid] = pmsg.time_epoch
                            
                            logging.debug("Sending message %s" % pmsg.msg_body)
                            self.send_message(mto=self.local_jid,
                                       mfrom=from_jid,
                                       mbody=pmsg.msg_body,
                                       mtype='chat')
                                  
                elif msg_type == dhtxmpp_protocol_msg.msg_type_prs:    
                    # if this msg is not from this node                
                    if (pmsg.from_user_key != self.local_user_key):
                        from_jid = create_jid(pmsg.from_user_key)
                        # if last delivery time from this jid < current msg time
                        if pmsg.time_epoch > self.last_prs_delivery_time_epoch.get(from_jid, 0):
                            self.last_prs_delivery_time_epoch[from_jid] = pmsg.time_epoch
                            logging.debug ("adding new jid %s" % (str(pmsg.from_user_key)))
                                   
                            if (pmsg.presence=="available"):
                                self.on_available_jid_from_dht(from_jid)  
                            else:
                                self.on_unavailable_jid_from_dht(from_jid)     
