'''
Created on Sep 14, 2018

@author: spendleton
'''
import asyncio
from kademlia.network import Server
from dhtxmpp_component.storage import storage
from dhtxmpp_component.protocol import protocol
from kademlia.node import Node
from kademlia.crawling import NodeSpiderCrawl

class server(Server):
    protocol_class = protocol
    def __init__(self):        
        Server.__init__(self, ksize=20, alpha=3, node_id=None, storage=storage())
        
    async def get(self, key):
        return await Server.get(self, key)

    async def set(self, key, value):
        return await Server.set(self, key, value)
    
    async def _refresh_table(self):
        """
        Refresh buckets that haven't had any lookups in the last hour
        (per section 2.3 of the paper).
        """
        ds = []
        for node_id in self.protocol.getRefreshIDs():
            node = Node(node_id)
            nearest = self.protocol.router.findNeighbors(node, self.alpha)
            spider = NodeSpiderCrawl(self.protocol, node, nearest,
                                     self.ksize, self.alpha)
            ds.append(spider.find())

        # do our crawling
        await asyncio.gather(*ds)

        # now republish keys older than one hour
        for dkey, value in self.storage.iteritemsOlderThan(3600):
            await self.set_digest(dkey, str(value))