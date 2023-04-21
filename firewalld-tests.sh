#!/bin/bash
set -x
# Start the Firewalld service
systemctl start firewalld
sleep 5

# Check if Firewalld is running
if systemctl is-active firewalld; then
  echo "Firewalld is active"
else
  echo "Firewalld is not active"
  exit 1
fi

fds block 1.2.3.4
