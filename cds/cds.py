# TODO cds set txt example.com  "value" (unique by name, suitable for dkim set script
import argparse

import six
from CloudFlare import CloudFlare
import logging as log

from CloudFlare.exceptions import CloudFlareAPIError

cf = CloudFlare()


def commandline_arg(bytestring):
    """
    Workaround fix for Python 2 input argument to be Unicode.
    See: https://stackoverflow.com/questions/22947181/dont-argparse-read-unicode-from-commandline
    """
    unicode_string = bytestring.decode(sys.getfilesystemencoding())
    return unicode_string


def action_config():
    pass


def action_list():
    pass


def action_reset():
    pass


def action_info():
    pass


def action_cron():
    pass


def action_block():
    pass


def action_unblock():
    pass


def main():
    parser = argparse.ArgumentParser(description='Convenient Cloudflare wrapper.',
                                     prog='cds')

    subparsers = parser.add_subparsers(help='Special action to run, e.g. block', dest="action")

    parser_config = subparsers.add_parser('config', help='Quickly configure Cloudflare integration')

    parser_block = subparsers.add_parser('block', help='Block a network, IP, or a country')
    if six.PY2:
        type = commandline_arg
    else:
        type = str
    parser_block.add_argument('value', nargs='?', default=None, help='Action value', type=type)

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
