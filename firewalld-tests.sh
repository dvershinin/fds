#!/bin/bash
set -x

systemctl start dbus
sleep 5
systemctl start firewalld
sleep 5

fds block 1.2.3.4
