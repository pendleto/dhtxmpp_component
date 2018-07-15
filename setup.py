#!/usr/bin/env python
from setuptools import setup, find_packages

setup(
    name="dhtxmpp_component",
    version="0.1",
    description="dhtxmpp_component is a distributed hash table XMPP component.",
    author="Stephen Pendleton",
    author_email="pendleto@movsoftware.com",
    license="MIT",
    url="http://github.com/movsoftware/dhtxmppcomponent",
    packages=find_packages(),
    requires=["sleekxmpp", "kademlia", "zeroconf", "asyncio"],
    install_requires=["sleekxmpp", "kademlia", "zeroconf", "asyncio"],
    entry_points={
        'console_scripts': ['dhtxmpp_componentd=dhtxmpp_componentd.dhtxmpp_componentd:main', 'dhtxmpp_componentd_watchdog=dhtxmpp_componentd_watchdog.dhtxmpp_componentd_watchdog:main']
        }
)