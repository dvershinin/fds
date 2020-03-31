import six
import argparse
import ipaddress
import logging as log  # for verbose output

from .FirewallWrapper import FirewallWrapper


def action_block(ip):
    fw = FirewallWrapper()
    ip = six.text_type(ip)
    if not ipaddress.ip_address(ip):
        print('bad argument')

    fw.block(ip)


def action_reset():
    fw = FirewallWrapper()
    fw.reset()


def main():
    parser = argparse.ArgumentParser(description='Convenient FirewallD wrapper.',
                                     prog='fds')
    parser.add_argument('action', nargs='?', default='block', help='Special action to run, '
                                                                   'e.g. block')
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
