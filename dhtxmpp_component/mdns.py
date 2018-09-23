'''
Created on Apr 6, 2017

@author: spendleton
'''

import logging
import socket
import time
import random

from zeroconf import ServiceInfo, Zeroconf, ServiceBrowser, ServiceStateChange

def get_ip():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        # doesn't even have to be reachable
        s.connect(('10.255.255.255', 1))
        IP = s.getsockname()[0]
    except:
        IP = '127.0.0.1'
    finally:
        s.close()
    return IP

class mdns_service(object):
    
    def register_dht_with_mdns(self):
        
        logging.basicConfig(level=logging.DEBUG,
                        format='%(pathname)s %(asctime)s %(levelname)s %(message)s',
                        filename='/var/log/dhtxmpp_componentd_mdns.log',
                        filemode='w')

        service_name = 'dht'
        desc = {'service': service_name, 'version': '0.0.1'}

        fqdn = socket.gethostname()
        ip_addr = get_ip()
        hostname = fqdn.split('.')[0]
        port = 5678
        logging.debug("Registering dhtxmpp in mdns for ip %s with hostname %s" % (ip_addr, hostname))
        
        self.info = ServiceInfo('_dht._tcp.local.', 
                        hostname + ' ' + service_name + '._dht._tcp.local.',
                        socket.inet_aton(ip_addr), port, 0, 0,
                        desc, hostname + '.local.')
        self.zeroconf = Zeroconf()
        self.zeroconf.register_service(self.info)

    def unregister_dht_with_mdns(self):
        logging.debug("Unregistering...")
        self.zeroconf.unregister_service(self.info)
        self.zeroconf.close()
        
    def on_service_state_change(self, zeroconf, service_type, name, state_change):
        if state_change is ServiceStateChange.Added:
            info = zeroconf.get_service_info(service_type, name)
            if info:
                logging.debug("  Zeroconf service Address: %s:%d" % (socket.inet_ntoa(info.address), info.port))
                self.service_address = socket.inet_ntoa(info.address)

    def listen_for_service(self):
        self.service_address = None
        self.zeroconf = Zeroconf()
        ServiceBrowser(self.zeroconf, "_dht._tcp.local.", handlers=[self.on_service_state_change])
        num_listen_tries = 0

        while(num_listen_tries<10):
            logging.debug("Listening for mdns dhtxmpp service...%d" % (num_listen_tries))
            num_listen_tries += 1          
            time.sleep(random.randint(3,6))
            
            if self.service_address != None:
                logging.debug("Found mdns dhtxmpp service on %s" %(str(self.service_address)))
                break
            
        return self.service_address