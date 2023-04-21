#!/bin/bash

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

# Add your Firewalld tests here, such as adding or removing rules, zones, or services
# Example: firewall-cmd --add-service=http --zone=public --permanent
