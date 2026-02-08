#!/bin/bash
set -euo pipefail
set -x

have_systemd() {
  # True if PID 1 is systemd
  [ "$(cat /proc/1/comm 2>/dev/null || echo)" = "systemd" ]
}

start_dbus_nosystemd() {
  mkdir -p /var/run/dbus /run/lock
  if command -v dbus-uuidgen >/dev/null 2>&1; then
    dbus-uuidgen --ensure
  elif command -v systemd-machine-id-setup >/dev/null 2>&1; then
    systemd-machine-id-setup
  elif [ ! -s /etc/machine-id ]; then
    cat /proc/sys/kernel/random/uuid | tr -d '-' | head -c 32 > /etc/machine-id
  fi
  # Start system bus in background
  dbus-daemon --system --fork
}

start_firewalld_nosystemd() {
  # Start firewalld in background and wait for it to become ready
  firewalld --nofork &
  for i in {1..20}; do
    if firewall-cmd --state >/dev/null 2>&1; then
      break
    fi
    sleep 1
  done
  # Do not fail if it's not running; just print status for diagnostics
  firewall-cmd --state || echo "firewalld not running"
}

if have_systemd; then
  systemctl start dbus
  sleep 3
  systemctl start firewalld
  # Give some time for firewalld to come up
  for i in {1..20}; do
    if firewall-cmd --state >/dev/null 2>&1; then
      break
    fi
    sleep 1
  done
else
  start_dbus_nosystemd
  sleep 1
  start_firewalld_nosystemd
fi

# Simple smoke test (only if firewalld is up)
if firewall-cmd --state 2>/dev/null | grep -q running; then
  # Smoke test: block single IP
  fds block 1.2.3.4

  # Functional test: block and unblock a continent (Europe)
  # Expect an EU country's ipset (e.g., Germany) to appear then disappear
  echo "Blocking continent: Europe"
  fds block Europe
  firewall-cmd --get-ipsets | grep -q 'fds-de-4'

  echo "Unblocking continent: Europe"
  fds unblock Europe
  if firewall-cmd --get-ipsets | grep -q 'fds-de-4'; then
    echo 'Expected fds-de-4 to be removed after unblocking Europe';
    exit 1;
  fi
else
  echo "Firewalld is not running in this environment. Skipping functional firewall test."
fi

exit 0
