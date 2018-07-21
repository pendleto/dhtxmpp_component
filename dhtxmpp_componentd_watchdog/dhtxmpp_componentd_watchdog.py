'''
Created on Apr 10, 2018

@author: spendleton
'''
from dhtxmpp_componentd_watchdog import ping
import time
from subprocess import Popen, PIPE
from optparse import OptionParser
import logging
from dhtxmpp_component import component

class dhtxmpp_componentd_watchdog:
    
    def start_component(self):
        try:
            process = Popen(['/usr/bin/prosodyctl', 'restart'], stdout=PIPE, stderr=PIPE)
            stdout, stderr = process.communicate()
        except:
            logging.debug("Failed to start xmpp server")
            return False
        logging.debug("Started xmpp server")
        
        try:
            process = Popen(['/etc/init.d/dhtxmpp-component.sh', 'restart'], stdout=PIPE, stderr=PIPE)
            stdout, stderr = process.communicate()
        except:
            logging.debug("Failed to start component")
            return False
        logging.debug("Started component")
        
        return True

    def _run_ping_test(self, jid, password, pingjid):
    
        try:
            xmpp = ping.PingTest(jid, password, pingjid)
            xmpp.register_plugin('xep_0030')  # Service Discovery
            xmpp.register_plugin('xep_0004')  # Data Forms
            xmpp.register_plugin('xep_0060')  # PubSub
            xmpp.register_plugin('xep_0199')  # XMPP Ping
            if xmpp.connect(reattempt=False):  
                xmpp.process(block=True)
                logging.debug("PING RETURNED %s" % (str(xmpp.success)))
                return xmpp.success
            else:
                return False
        except:
            return False
        
    def run_ping_test(self, jid, password, pingjid):
        num_tries = 0
        while num_tries < 12:
            num_tries = num_tries + 1
            if self._run_ping_test(jid, password, pingjid) == True:
                return True
            time.sleep(60)
        return False
        
        
def main():
    
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
    optp.add_option('-t', '--pingto', help='set jid to ping',
                    action='store', type='string', dest='pingjid',
                    default=None)

    # JID and password options.
    optp.add_option("-j", "--jid", dest="jid",
                    help="JID to use")
    optp.add_option("-p", "--password", dest="password",
                    help="password to use")

    opts, args = optp.parse_args()

    # Setup logging.
    # Setup logging.
    logging.basicConfig(level=logging.DEBUG,
                    format='%(pathname)s %(asctime)s %(levelname)s %(message)s',
                    filename='/var/log/dhtxmpp_componentd_watchdog.log',
                    filemode='w',
                    )
    while True: 
        watchdog = dhtxmpp_componentd_watchdog()
        if watchdog.run_ping_test(opts.jid, opts.password, opts.pingjid) == False:
            # restart XMPP server and component
            logging.debug("RESTARTING COMPONENT\n")            
            watchdog.start_component()
        else:
            logging.debug("COMPONENT WORKING\n")            
        time.sleep(120)
        
            
