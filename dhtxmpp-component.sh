#!/bin/sh

### BEGIN INIT INFO
# Provides:          dhtxmpp_componentd
# Required-Start:    $remote_fs $syslog prosody
# Required-Stop:     $remote_fs $syslog
# Default-Start:     2 3 4 5
# Default-Stop:      0 1 6
# Short-Description: DHTXMPP Component
# Description:       DHTXMPP Component
### END INIT INFO

DIR=/usr/local/bin
DAEMON=$DIR/dhtxmpp_componentd.py
DAEMON_NAME=dhtxmpp-component

# Add any command line options for your daemon here
DAEMON_OPTS="-j mesh.localhost -p dhtxmppcomponentsecret -s 127.0.0.1 -P 5347 -q"

# This next line determines what user the script runs as.
# Root generally not recommended but necessary if you are using the Raspberry Pi GPIO from Python.
DAEMON_USER=root

# The process ID of the script when it runs is stored here:
PIDFILE=/var/run/$DAEMON_NAME.pid

. /lib/lsb/init-functions

do_start () {
log_daemon_msg "Starting system $DAEMON_NAME daemon"
start-stop-daemon --start --background --pidfile $PIDFILE --make-pidfile --user $DAEMON_USER --chuid $DAEMON_USER --startas $DAEMON -- $DAEMON_OPTS
log_end_msg $?
}
do_stop () {
log_daemon_msg "Stopping system $DAEMON_NAME daemon"
start-stop-daemon --stop --pidfile $PIDFILE --retry 10
log_end_msg $?
}

case "$1" in

start|stop)
do_${1}
;;

restart|reload|force-reload)
do_stop
do_start
;;

status)
status_of_proc "$DAEMON_NAME" "$DAEMON" && exit 0 || exit $?
;;

*)
echo "Usage: /etc/init.d/$DAEMON_NAME {start|stop|restart|status}"
exit 1
;;

esac
exit 0