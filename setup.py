#!/usr/bin/env python
from setuptools import setup, find_packages
from dhtxmpp_component import version

setup(
    name="dhtxmpp_component",
    version=version,
    description="dhtxmpp_component is a distributed hash table XMPP component.",
    author="Stephen Pendleton",
    author_email="pendleto@movsoftware.com",
    license="MIT",
    url="http://github.com/movsoftware/dhtxmppcomponent",
    packages=find_packages(),
    requires=["sleekxmpp", "kademlia", "zeroconf"],
    install_requires=["sleekxmpp", "kademlia", "zeroconf"]
)