from __future__ import unicode_literals

import argparse
import ipaddress
import logging as log  # for verbose output
import os

import six

from .FirewallWrapper import FirewallWrapper


def is_root():
    return os.geteuid() == 0


def action_block(ip_or_country_name):
    fw = FirewallWrapper()
    ip_or_country_name = six.text_type(ip_or_country_name)
    try:
        ip_or_country_name = ipaddress.ip_address(ip_or_country_name)
        fw.block_ip(ip_or_country_name)
    except ValueError:
        fw.block_country(ip_or_country_name)


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
