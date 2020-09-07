import os

import six
import argparse
import ipaddress
import logging as log  # for verbose output

from .FirewallWrapper import FirewallWrapper
from .WebClient import WebClient

def is_root():
    return os.geteuid() == 0


def action_block(ip):
    fw = FirewallWrapper()
    ip = six.text_type(ip)
    try:
        ip = ipaddress.ip_address(ip)
        fw.block(ip)
    except ValueError:
        # print('address/netmask is invalid: %s' % sys.argv[1])
        # parse out as a country
        from .Countries import Countries
        countries = Countries()
        c = countries.getByName(ip)



        print(c)
        print(c.getFlag())
        print("\N{grinning face}")
        print(c.code)
        # TODO get aggregated zone file, save as cache,
        # do diff to know which stuff was changed and add/remove blocks
        # https://docs.python.org/2/library/difflib.html
        # TODO persist info on which countries were blocked (in the config file)
        # then sync zones via "fds cron"
        # TODO conditional get test on getpagespeed.com
        w = WebClient()
        country_networks = w.get_country_networks(country=c)
        for network in country_networks:
            print(network)
        # TODO retry, timeout




def action_reset():
    fw = FirewallWrapper()
    fw.reset()


def main():
    parser = argparse.ArgumentParser(description='Convenient FirewallD wrapper.',
                                     prog='fds')
    parser.add_argument('action', nargs='?', default='block',
                        choices=['block', 'reset'],
                        help='Special action to run, e.g. block')
    parser.add_argument('value', nargs='?', default=None, help='Action value')
    parser.add_argument('--verbose', dest='verbose', action='store_true')

    args = parser.parse_args()

    if args.verbose:
        log.basicConfig(format="%(levelname)s: %(message)s", level=log.DEBUG)
        log.debug("Verbose output.")
    else:
        log.basicConfig(format="%(message)s", level=log.INFO)

    if args.action == 'block':
        return action_block(args.value)

    if args.action == 'reset':
        return action_reset()

    log.error('Unknown command {}'.format(args.action))
