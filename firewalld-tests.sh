#!/bin/bash
set -x

systemctl start dbus
systemctl start firewalld

sleep 5

fds block 1.2.3.4
