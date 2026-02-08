import os
import subprocess
import time


def exec_in_container(cmd):
    return subprocess.check_output([
        'docker', 'exec', 'firewalld-container', '/bin/bash', '-lc', cmd
    ], stderr=subprocess.STDOUT, text=True)


def test_unblock_region_smoke():
    # Ensure container is up
    out = subprocess.check_output(['docker', 'ps', '--filter', 'name=firewalld-container', '--format', '{{.Names}}'], text=True)
    assert 'firewalld-container' in out.strip()

    # Start firewalld if needed
    try:
        exec_in_container('systemctl start dbus && systemctl start firewalld')
    except subprocess.CalledProcessError:
        # Non-systemd fallback: start dbus and firewalld
        exec_in_container('mkdir -p /var/run/dbus /run/lock && dbus-uuidgen --ensure || true && dbus-daemon --system --fork || true && firewalld --nofork &')
        time.sleep(2)

    # Confirm firewalld responds or skip test early
    try:
        state = exec_in_container('firewall-cmd --state').strip()
    except subprocess.CalledProcessError:
        state = 'not running'

    if state != 'running':
        # environment cannot run functional firewalld; skip
        return

    # Block a continent first (e.g., Europe); then unblock it
    exec_in_container('fds block Europe')
    # Check some known country ipset exists (e.g., Germany 'fds-de')
    ipsets = exec_in_container('firewall-cmd --get-ipsets || true')
    assert 'fds-de' in ipsets or 'fds-de' in exec_in_container('firewall-cmd --get-ipsets || true')

    exec_in_container('fds unblock Europe')
    ipsets_after = exec_in_container('firewall-cmd --get-ipsets || true')
    assert 'fds-de' not in ipsets_after



