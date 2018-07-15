#!/bin/bash
export PATH=/usr/local/bin/:${PATH}
echo $PATH

cmd="prosodyctl restart"
eval "${cmd}" &>/dev/null &
cmd="/etc/init.d/dhtxmpp-component.sh restart"
eval "${cmd}" 
