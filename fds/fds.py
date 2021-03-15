from __future__ import unicode_literals

import argparse
import ipaddress
import logging as log  # for verbose output
import os

import six

from .Countries import Countries
from .FirewallWrapper import FirewallWrapper


def is_root():
    return os.geteuid() == 0


def action_block(ip_or_country_name, reload=True):
    fw = FirewallWrapper()
    if 'tor' == ip_or_country_name:
        return fw.block_tor(reload=reload)
    ip_or_country_name = six.text_type(ip_or_country_name)
    try:
        ip_or_country_name = ipaddress.ip_network(ip_or_country_name)
        fw.block_ip(ip_or_country_name, reload=reload)
    except ValueError:
        fw.block_country(ip_or_country_name, reload=reload)


def action_unblock(ip_or_country_name):
    fw = FirewallWrapper()
    ip_or_country_name = six.text_type(ip_or_country_name)
    try:
        ip_or_country_name = ipaddress.ip_network(ip_or_country_name)
        fw.unblock_ip(ip_or_country_name)
    except ValueError:
        fw.unblock_country(ip_or_country_name)


def action_reset():
    fw = FirewallWrapper()
    fw.reset()


def action_list(what='blocked'):
    print("Listing {}".format(what))
    if what == 'countries':
        countries = Countries()
        countries.print_all()
    elif what == 'blocked':
        fw = FirewallWrapper()
        print("==================")
        print("Blocked networks / IP addresses:")
        blocked4 = fw.get_blocked_ips4()
        for entry in blocked4:
            print(entry)
        blocked6 = fw.get_blocked_ips6()
        for entry in blocked6:
            print(entry)
        print("Blocked countries:")
        for country_name in fw.get_blocked_countries():
            print(country_name)



def main():
    parser = argparse.ArgumentParser(description='Convenient FirewallD wrapper.',
                                     prog='fds')

    subparsers = parser.add_subparsers(help='Special action to run, e.g. block', dest="action")

    parser_block = subparsers.add_parser('block', help='Block a network, IP, or a country')
    parser_block.add_argument('value', nargs='?', default=None, help='Action value')
    parser_block.add_argument('--no-reload', '-nr', dest='reload', action='store_false',
                              default=True, help='Skip reloading FirewallD')

    parser_unblock = subparsers.add_parser('unblock')
    parser_unblock.add_argument('value', nargs='?', default=None, help='Action value')

    subparsers.add_parser('reset')

    parser_list = subparsers.add_parser('list', help='Show a listing of ...')
    list_subparsers = parser_list.add_subparsers(
        dest='what',
        help='Specify listing type'
    )
    list_blocked_subparser = list_subparsers.add_parser('blocked', help='List blocked')
    list_blocked_subparser.add_argument('kind', nargs='?', default='all',
                                        choices=['all', 'networks'],
                                        help='Kind of blocked entries to be listed')

    list_blocked_subparser = list_subparsers.add_parser('countries', help='List countries')
    list_blocked_subparser.add_argument('kind', nargs='?', default='all',
                                        choices=['all', 'networks'],
                                        help='Kind of blocked entries to be listed')

    parser.add_argument('--verbose', dest='verbose', action='store_true')

    args = parser.parse_args()

    if args.verbose:
        log.basicConfig(format="%(levelname)s: %(message)s", level=log.DEBUG)
        log.debug("Verbose output.")
    else:
        log.basicConfig(format="%(message)s", level=log.INFO)

    if args.action == 'block':
        return action_block(args.value, reload=args.reload)

    if args.action == 'unblock':
        return action_unblock(args.value)

    if args.action == 'reset':
        return action_reset()
    
    if args.action == 'list':
        return action_list(what=args.what)

    log.error('Unknown command {}'.format(args.action))
