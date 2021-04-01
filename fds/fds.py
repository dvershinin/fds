from __future__ import unicode_literals

import argparse
import ipaddress
import logging as log  # for verbose output
import os
import sys
import six

from .Countries import Countries
from .FirewallWrapper import FirewallWrapper
from .__about__ import __version__
from .config import action_config


def commandline_arg(bytestring):
    """
    Workaround fix for Python 2 input argument to be Unicode.
    See: https://stackoverflow.com/questions/22947181/dont-argparse-read-unicode-from-commandline
    """
    unicode_string = bytestring.decode(sys.getfilesystemencoding())
    return unicode_string


def is_root():
    return os.geteuid() == 0


def block_region(region):
    """
    Simply goes over all countries with the region and nukes them all
    Args:
        region ():

    Returns:

    """
    countries = Countries()
    for country in countries:
        if country.data['region'] == region:
            action_block(country.name, reload=False)


def action_block(ip_or_country_name, ipset_name=None, reload=True):
    # FD
    fw = FirewallWrapper()
    # CF
    from cds.CloudflareWrapper import CloudflareWrapper
    cw = CloudflareWrapper()
    if 'tor' == ip_or_country_name:
        return fw.block_tor(reload=reload)
    ip_or_country_name = six.text_type(ip_or_country_name)
    try:
        ip_or_country_name = ipaddress.ip_network(ip_or_country_name)
        fw.block_ip(ip_or_country_name, ipset_name=ipset_name, reload=reload)
        cw.block_ip(ip_or_country_name)
    except ValueError:
        # we know now it's not IP, so we capitalize in case user passed "country" and not "Country"
        ip_or_country_name = ip_or_country_name.capitalize()
        countries = Countries()
        regions = countries.get_continents()
        if ip_or_country_name in regions:
            block_region(ip_or_country_name)
        else:
            country = countries.get_by_name(ip_or_country_name)
            if not country:
                log.error('{} does not look like a correct IP, region, or a country name'.format(
                    ip_or_country_name))
                return False
            fw.block_country(country, reload=reload)
            cw.block_country(country)


def action_cron():
    fw = FirewallWrapper()
    fw.update_ipsets()


def action_unblock(ip_or_country_name):
    fw = FirewallWrapper()
    # CF
    from cds.CloudflareWrapper import CloudflareWrapper
    cw = CloudflareWrapper()
    ip_or_country_name = six.text_type(ip_or_country_name)
    try:
        ip_or_country_name = ipaddress.ip_network(ip_or_country_name)
        fw.unblock_ip(ip_or_country_name)
        cw.unblock_ip(ip_or_country_name)
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
    elif what == 'continents':
        countries = Countries()
        countries.print_all_continents()
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


def action_info(v):
    countries = Countries()
    country = countries.get_by_name(v)
    print(country)


def main():
    parser = argparse.ArgumentParser(description='Convenient FirewallD wrapper.',
                                     prog='fds')

    subparsers = parser.add_subparsers(help='Special action to run, e.g. block', dest="action")

    parser_cron = subparsers.add_parser('cron', help='Run fds cron tasks, e.g. updating IP sets')

    parser_config = subparsers.add_parser('config', help='Quickly configure your firewall')

    parser_block = subparsers.add_parser('block', help='Block a network, IP, or a country')
    if six.PY2:
        type = commandline_arg
    else:
        type = str
    parser_block.add_argument('value', nargs='?', default=None, help='Action value', type=type)
    parser_block.add_argument('--no-reload', '-nr', dest='reload', action='store_false',
                              default=True, help='Skip reloading FirewallD')
    parser_block.add_argument('--ipset', dest='ipset_name',
                              default=None, help='Base name for the block IP set ("networkblock", by default)')

    parser_unblock = subparsers.add_parser('unblock')
    parser_unblock.add_argument('value', nargs='?', default=None, help='Action value', type=type)

    parser_info = subparsers.add_parser('info')
    parser_info.add_argument('value', nargs='?', default=None, help='Action value', type=type)

    subparsers.add_parser('reset')

    parser_list = subparsers.add_parser('list', help='Show a listing of ...')
    list_subparsers = parser_list.add_subparsers(
        dest='what',
        help='Specify listing type',
    )

    list_blocked_subparser = list_subparsers.add_parser('blocked', help='List blocked')
    list_blocked_subparser.add_argument('kind', nargs='?', default='all',
                                        choices=['all', 'networks'],
                                        help='Kind of blocked entries to be listed')


    list_countries_subparser = list_subparsers.add_parser('countries', help='List countries')

    list_continents_subparser = list_subparsers.add_parser('continents', help='List continents')

    parser.add_argument('--verbose', dest='verbose', action='store_true')

    parser.add_argument('--version', action='version',
                        version='%(prog)s {version}'.format(version=__version__))



    args = parser.parse_args()

    if args.verbose:
        log.basicConfig(format="%(levelname)s: %(message)s", level=log.DEBUG)
        log.debug("Verbose output.")
    else:
        level = log.WARNING if args.action == 'cron' else log.INFO
        log.basicConfig(format="%(message)s", level=level)

    if args.action == 'config':
        return action_config()

    if args.action == 'info':
        return action_info(args.value)

    if args.action == 'block':
        return action_block(args.value, args.ipset_name, reload=args.reload)

    if args.action == 'cron':
        return action_cron()

    if args.action == 'unblock':
        return action_unblock(args.value)

    if args.action == 'reset':
        return action_reset()

    if args.action == 'list':
        return action_list(what=args.what)

    log.error('Unknown command {}'.format(args.action))
