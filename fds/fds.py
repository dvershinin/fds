import argparse
import firewall.config
import ipaddress
from .FirewallWrapper import FirewallWrapper
from firewall.client import FirewallClient, \
    FirewallClientZoneSettings, \
    FirewallClientServiceSettings, \
    FirewallClientIcmpTypeSettings
from firewall.core.base import DEFAULT_ZONE_TARGET
from firewall.core.fw import Firewall

from .__about__ import __version__

def action_block(fw, ip):
    if not ipaddress.ip_address(ip):
        print('bad argument')

    fw.block(ip)

def main():
    parser = argparse.ArgumentParser(description='Convenient FirewallD wrapper.',
                                     prog='fds')
    parser.add_argument('action', nargs='?', default='block', help='Special action to run, '
                                                                   'e.g. block')

    parser.add_argument('value', nargs='?', default=None, help='Action value')

    args = parser.parse_args()

    fw = FirewallWrapper()

    if args.action == 'block':
        return action_block(fw, args.value)

    fw = FirewallClient()
    fw.checkPermanentConfig()
    Firewall.ipset
    print()
    print(fw.getZones())
