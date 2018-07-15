#!/bin/sh

python3 -m pip install dhtxmpp_component-0.1.tar.gz
python3 setup.py install
cp dhtxmpp-component.sh /etc/init.d
chmod a+x /etc/init.d/dhtxmpp-component.sh
update-rc.d dhtxmpp-component.sh defaults
cp dhtxmpp-component-watchdog.sh /etc/init.d
chmod a+x /etc/init.d/dhtxmpp-component-watchdog.sh
update-rc.d dhtxmpp-component-watchdog.sh defaults