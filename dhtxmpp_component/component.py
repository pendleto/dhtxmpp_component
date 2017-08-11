#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
    dhtxmpp_component: DHT XMPP Component
    See the file LICENSE for copying permission.
"""

import sys
import logging
import getpass
import hashlib
from optparse import OptionParser

from sleekxmpp.componentxmpp import ComponentXMPP
from sleekxmpp import JID, jid
from sleekxmpp.xmlstream.handler import Callback
from sleekxmpp.xmlstream.matcher import StanzaPath

from collections import Counter

from protocol import custom_protocol
from dht import DHT
from mdns import mdns_service

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

    def __init__(self, jid, secret, server, port, bootstrapip):
        ComponentXMPP.__init__(self, jid, secret, server, port)

        # You don't need a session_start handler, but that is
        # where you would broadcast initial presence.

        # The message event is triggered whenever a message
        # stanza is received. Be aware that that includes
        # MUC messages and error messages.
        
        if bootstrapip == None:
            # Run the mdns to discover dht
            self.mdns = mdns_service()
            dht_address = self.mdns.listen_for_service()
        
            if dht_address == None:
                self.mdns.register_dht_with_mdns()
                bootstrapip = "127.0.0.1"
            else:
                bootstrapip = str(dht_address)
            
        self.dht = DHT(bootstrapip, self)
        self.add_event_handler('presence_probe', self.handle_probe)
        self.add_event_handler("message", self.message)
        self.add_event_handler("presence_available", self.presence_available)
        self.add_event_handler("presence_unavailable", self.presence_unavailable)
        self.add_event_handler('disco_info', self.disco_info)        
        self.register_handler(Callback('Disco Info', StanzaPath('iq/disco_info'), self.disco_info))
                
        self.local_jid = None
        self.local_user_key = None

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

        to_user_key = custom_protocol.create_user_key(str(to_jid.user), None)
        from_user_key = custom_protocol.create_user_key(str(from_jid.user), str(self.dht.server.node.long_id))   
        print("SENDING MSG TO KEY: %s=%s" % (str(to_user_key), str(msg_body)))
        fullmsg = custom_protocol.create_msg(from_user_key, to_user_key, msg_body)
        self.send_msg_to_dht(to_user_key, fullmsg)        
        
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
        self.local_user_key = custom_protocol.create_user_key(str(from_jid.user), str(self.dht.server.node.long_id))   
        print("got presence from: %s" % (str(from_jid)))
        self.sendPresence(pshow='available', pto=from_jid)
        # go through all items in the component roster send the presence ones to the local client
        self.send_roster()
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
        print("got unpresence from: %s" % (str(from_jid)))
        self.unpublish_jid_to_dht() 
        self.local_jid = None
        self.local_user_key = None
               
    def disco_info(self, iq):
        from_jid = JID(iq['from'])
        print("got disco_info from: %s" % (str(from_jid)))
        #component_jid = JID("mesh.localhost")
        #self.send_presence_subscription(pto=from_jid, pfrom=component_jid)     
        
                
    def on_available_jid_from_dht(self, from_jid):
        # a new jid is found on the network
        # send it to the local client
        if from_jid == None:
            print("Couldn't find JID")
            return
        print("New JID %s found on DHT" % (str(from_jid)))
        to_jid = self.local_jid
        
        # Go through the jids on our roster and send their presences to 
        # the local jid
        
        # check if this jid is already on our roster
        existing = self.client_roster.has_jid(from_jid)
        if existing == True:
            print("%s already exists in our roster" % (str(from_jid)))
            self.sendPresence(pshow='available', pto=to_jid, pfrom=from_jid)
            presence = self.make_presence(pshow='available', pfrom=from_jid)
            self.client_roster[from_jid].handle_available(presence)
            return
        

        if to_jid != None:
            print("Sending presence to %s from %s" % (str(to_jid), str(from_jid)))
            self.send_presence_subscription(pto=to_jid, pfrom=from_jid)
            #self.sendPresence(pshow='available', pto=to_jid, pfrom=mesh_jid)
            self.client_roster.add(str(from_jid))
        else:
            print ("Could not send presence because local_jid was not set") 
                                  
    def on_unavailable_jid_from_dht(self, from_jid):
        # a jid has left the network
        # send it to the local client
        if from_jid == None:
            print("Couldn't find JID")
            return
        print("JID %s left the DHT" % (str(from_jid)))
        to_jid = self.local_jid
        # check if this jid is already on our roster
        existing = self.client_roster.has_jid(from_jid)
        if existing == False:
            print("%s doesn't exist in our roster" % (str(from_jid)))
            return
    
        if to_jid != None:
            print("Sending unavailable presence to %s from %s" % (str(to_jid), str(from_jid)))
            #self.send_presence_subscription(pto=to_jid, pfrom=from_jid, ptype='unsubscribe')
            self.sendPresence(pshow='unavailable', pto=to_jid, pfrom=from_jid)
            #self.client_roster.remove(str(from_jid))
            presence = self.make_presence(pshow='unavailable', pfrom=from_jid)
            self.client_roster[from_jid].handle_unavailable(presence)
        else:
            print ("Could not send unavailable presence because local_jid was not set")   
  
    def send_roster(self):
        groups = self.client_roster.groups()
        for group in groups:
            for jid in groups[group]:
                sub = self.client_roster[jid]['subscription']
                name = self.client_roster[jid]['name']
                if self.client_roster[jid]['name']:
                    print(' %s (%s) [%s]' % (name, jid, sub))
                else:
                    print(' %s [%s]' % (jid, sub))

                connections = self.client_roster.presence(jid)
                for res, pres in connections.items():
                    show = 'available'
                    if pres['show']:
                        show = pres['show']
                    print('   - %s (%s)' % (res, show))
                    status = "available"
                    if pres['status']:
                        status = pres['status']
                    from_jid = create_jid(JID(jid).user)
                    self.sendPresence(pshow=show, pto=self.local_jid, pfrom=from_jid, pstatus=status)
                                 
    def handle_probe(self, presence):
        sender = presence['from']
        # Populate the presence reply with the agent's current status.
        self.sendPresence(pto=sender, pstatus="online", pshow="online")
        
    def run(self):
        self.dht.run();
        
    def publish_jid_to_dht(self):
        if self.local_jid != None:            
            # publish jid.user and node.id
            user_key = custom_protocol.create_user_key(self.local_jid.user, str(self.dht.server.node.long_id))
            msg = custom_protocol.create_presence(user_key, "available")
            print("SET DHT KEY: %s=%s" % (str(user_key), str(msg)))
            self.send_msg_to_dht(user_key, msg) 
        else:
            print("LOCAL JID NOT KNOWN YET. NOT PUBLISHING PRESENCE")      
            
    def unpublish_jid_to_dht(self):
        if self.local_jid != None:            
            # publish jid.user and node.id
            user_key = custom_protocol.create_user_key(self.local_jid.user, str(self.dht.server.node.long_id))
            msg = custom_protocol.create_presence(user_key, "unavailable")
            print("SET DHT KEY: %s=%s" % (str(user_key), str(msg)))
            self.send_msg_to_dht(user_key, msg) 
        else:
            print("LOCAL JID NOT KNOWN YET. NOT PUBLISHING PRESENCE")    
            
 
    def send_msg_to_dht(self, to, msg):
        key = hashlib.sha1(str(to)+str(msg)).digest()
        self.dht.server.set(key, msg)
                   
    def parse_dht_msg(self, value_str):         
        
        msg_type = custom_protocol.crack_msg_type(value_str)
        if msg_type != None:
  
            if msg_type == "msg":
                from_user_key, to_user_key, xmpp_msg = custom_protocol.crack_msg(value_str)
                
                # if this msg is destined for this node
                if (to_user_key == self.local_user_key):
                    from_jid = create_jid(from_user_key)
                    print("Sending message %s" % xmpp_msg)
                    self.send_message(mto=self.local_jid,
                                       mfrom=from_jid,
                                       mbody=xmpp_msg,
                                       mtype='chat')
                    
                
            elif msg_type == "prs":
                from_user_key, presence = custom_protocol.crack_presence(value_str)
                # if this msg is not from this node                
                if (from_user_key != self.local_user_key):
                    print ("adding new jid %s" % (str(from_user_key)))
                    jid = create_jid(from_user_key)
                    
                    if (presence=="available"):
                        self.on_available_jid_from_dht(jid)  
                    else:
                        self.on_unavailable_jid_from_dht(jid)     

if __name__ == '__main__':
    # Setup the command line arguments.
    optp = OptionParser()

    # Output verbosity options.
    optp.add_option('-q', '--quiet', help='set logging to ERROR',
                    action='store_const', dest='loglevel',
                    const=logging.ERROR, default=logging.INFO)
    optp.add_option('-d', '--debug', help='set logging to DEBUG',
                    action='store_const', dest='loglevel',
                    const=logging.DEBUG, default=logging.INFO)
    optp.add_option('-v', '--verbose', help='set logging to COMM',
                    action='store_const', dest='loglevel',
                    const=5, default=logging.INFO)

    # JID and password options.
    optp.add_option("-j", "--jid", dest="jid",
                    help="JID to use")
    optp.add_option("-p", "--password", dest="password",
                    help="password to use")
    optp.add_option("-s", "--server", dest="server",
                    help="server to connect to")
    optp.add_option("-b", "--bootstrapip", dest="bootstrapip",
                    help="bootstrap ip to connect to")
    optp.add_option("-P", "--port", dest="port",
                    help="port to connect to")

    opts, args = optp.parse_args()

    if opts.jid is None:
        opts.jid = raw_input("Component JID: ")
    if opts.password is None:
        opts.password = getpass.getpass("Password: ")
    if opts.server is None:
        opts.server = raw_input("Server: ")
    if opts.port is None:
        opts.port = int(raw_input("Port: "))
    #if opts.bootstrapip is None:
    #    opts.bootstrapip = raw_input("Bootstrap IP: ")
        
    # Setup logging.
    logging.basicConfig(level=opts.loglevel,
                        format='%(levelname)-8s %(message)s')


    # Setup the dhtxmpp_component and register plugins. Note that while plugins
    # may have interdependencies, the order in which you register them does
    # not matter.
    xmpp = dhtxmpp_component(opts.jid, opts.password, opts.server, opts.port, opts.bootstrapip)
    xmpp.registerPlugin('xep_0030') # Service Discovery
    xmpp.registerPlugin('xep_0004') # Data Forms
    xmpp.registerPlugin('xep_0060') # PubSub
    xmpp.registerPlugin('xep_0199') # XMPP Ping
    xmpp.auto_authorize = True
    xmpp.auto_subscribe = True

    # Connect to the XMPP server and start processing XMPP stanzas.
    print("Connecting to XMPP server...")
    if xmpp.connect():
        print("Connected")
        xmpp.process(block=False)
        xmpp.run()
        xmpp.disconnect()
        print("Done")
    else:
        print("Unable to connect.")

