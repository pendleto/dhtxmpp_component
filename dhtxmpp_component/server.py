'''
Created on Sep 14, 2018

@author: spendleton
'''
from kademlia.network import Server
from dhtxmpp_component.storage import storage
from dhtxmpp_component.protocol import protocol

class server(Server):
    protocol_class = protocol
    def __init__(self):        
        Server.__init__(self, ksize=20, alpha=3, node_id=None, storage=storage())
        
    async def get(self, key):
        return await Server.get(self, key)

    async def set(self, key, value):
        return await Server.set(self, key, value)