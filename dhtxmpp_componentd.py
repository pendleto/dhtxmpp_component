#!/usr/bin/env python

import sys
import time
import logging
from optparse import OptionParser

from sleekxmpp.componentxmpp import ComponentXMPP
from sleekxmpp import JID, jid
from sleekxmpp.xmlstream.handler import Callback
from sleekxmpp.xmlstream.matcher import StanzaPath

from dhtxmpp_component.component import dhtxmpp_component

class dhtxmpp_componentd:
    def run(self, opts):
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


if __name__ == "__main__":    
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

    # Setup logging.
    logging.basicConfig(level=opts.loglevel,
                        format='%(levelname)-8s %(message)s')


 
    daemon = dhtxmpp_componentd()
    
    daemon.run(opts)
    sys.exit(0)
