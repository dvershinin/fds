from __future__ import unicode_literals

# from netaddr import IPAddress
import logging as log  # for verbose output

import dbus
from firewall.client import FirewallClient
from firewall.client import FirewallClientIPSetSettings

from .WebClient import WebClient


def do_maybe_already_enabled(func):
    def func_wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except dbus.exceptions.DBusException as e:
            if 'org.fedoraproject.FirewallD1.Exception' == e.get_dbus_name() \
                    and e.get_dbus_message().startswith('ALREADY_ENABLED:'):
                log.debug(e.get_dbus_message())
                return True
            else:
                # re-raise :)
                raise e

    return func_wrapper


def do_maybe_not_enabled(func):
    def func_wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except dbus.exceptions.DBusException as e:
            if 'org.fedoraproject.FirewallD1.Exception' == e.get_dbus_name() \
                    and e.get_dbus_message().startswith('NOT_ENABLED:'):
                log.debug(e.get_dbus_message())
                return True
            else:
                # re-raise :)
                raise e

    return func_wrapper


def do_maybe_invalid_ipset(func):
    def func_wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except dbus.exceptions.DBusException as e:
            if 'org.fedoraproject.FirewallD1.Exception' == e.get_dbus_name() \
                    and e.get_dbus_message().startswith('INVALID_IPSET:'):
                log.debug(e.get_dbus_message())
                return True
            else:
                # re-raise :)
                raise e

    return func_wrapper


class FirewallWrapper:
    NETWORKBLOCK_IPSET4 = 'networkblock4'
    NETWORKBLOCK_IPSET6 = 'networkblock6'
    NETWORKBLOCK_IPSET_BASE_NAME = 'networkblock'

    def __init__(self):
        self.fw = FirewallClient()
        self.config = self.fw.config()
        if not self.config:
            log.warning('FirewallD is not running attempting to start...')
            import subprocess
            subprocess.check_output(['systemctl', 'enable', '--now', 'firewalld'])
            # firewall-cmd synchronously waits for FirewallD startup
            subprocess.check_output(['firewall-cmd', '--state'])
            self.fw = FirewallClient()
            self.config = self.fw.config()

    def get_create_set(self, name, family='inet'):
        if name in self.config.getIPSetNames():
            return self.config.getIPSetByName(
                name
            )
        settings = FirewallClientIPSetSettings()
        settings.setType('hash:net')
        settings.setOptions({
            'maxelem': '1000000',
            'family': family,
            'hashsize': '4096'
        })
        return self.config.addIPSet(
            name, settings
        )

    def get_block_ipset4(self, name=None):
        if not name:
            name = FirewallWrapper.NETWORKBLOCK_IPSET_BASE_NAME
        name = name + '4'
        if name in self.config.getIPSetNames():
            return self.config.getIPSetByName(
                name
            )
        settings = FirewallClientIPSetSettings()
        settings.setType('hash:net')
        settings.setOptions({
            'maxelem': '1000000',
            'family': 'inet',
            'hashsize': '4096'
        })
        return self.config.addIPSet(
            name, settings
        )

    def get_block_ipset6(self, name=None):
        if not name:
            name = FirewallWrapper.NETWORKBLOCK_IPSET_BASE_NAME
        name = name + '6'
        if name in self.config.getIPSetNames():
            return self.config.getIPSetByName(
                name
            )
        settings = FirewallClientIPSetSettings()
        settings.setType('hash:net')
        settings.setOptions({
            'maxelem': '1000000',
            'family': 'inet6',
            'hashsize': '4096'
        })
        return self.config.addIPSet(
            name, settings
        )

    def get_block_ipset_for_ip(self, ip, name=None):
        if ip.version == 4:
            return self.get_block_ipset4(name)
        if ip.version == 6:
            return self.get_block_ipset6(name)
        return None

    @do_maybe_already_enabled
    def ensure_ipset_entries(self, ipset, entries):
        return ipset.setEntries(entries)

    @do_maybe_already_enabled
    def ensure_entry_in_ipset(self, ipset, entry):
        return ipset.addEntry(str(entry))

    @do_maybe_already_enabled
    def ensure_entry_not_in_ipset(self, ipset, entry):
        return ipset.removeEntry(str(entry))

    @do_maybe_already_enabled
    def ensure_block_ipset_in_drop_zone(self, ipset):
        # ensure that the block ipset is in drop zone:
        drop_zone = self.config.getZoneByName('drop')
        # self.config.getIPSetNames
        return drop_zone.addSource('ipset:{}'.format(
            ipset.get_property('name')
        ))

    @do_maybe_already_enabled
    def add_service(self, name, zone='public'):
        self.fw.addService(zone, name)
        self.fw.runtimeToPermanent()

    @do_maybe_already_enabled
    def block_ip(self, ip, ipset_name=None, reload=True):
        block_ipset = self.get_block_ipset_for_ip(ip, ipset_name)
        if not block_ipset:
            # TODO err: unsupported protocol
            raise Exception('Unsupported protocol')
        self.ensure_block_ipset_in_drop_zone(block_ipset)
        log.info('Adding IP address {} to block set {}'.format(ip, block_ipset.get_property('name')))
        try:
            from aggregate6 import aggregate
            entries = []
            for entry in block_ipset.getEntries():
                entries.append(str(entry))
            entries.append(str(ip))
            block_ipset.setEntries(aggregate(entries))
        except ImportError:
            block_ipset.addEntry(str(ip))
        if reload:
            log.info('Reloading FirewallD to apply permanent configuration')
            self.fw.reload()
        log.info('Breaking connection with {}'.format(ip))
        import errno
        from subprocess import CalledProcessError, check_output, STDOUT
        try:
            check_output(["/sbin/conntrack", "-D", "-s", str(ip)], stderr=STDOUT)
        except OSError as e:
            if e.errno == errno.ENOENT:
                log.warning('conntrack not found, skipping connection drop')
            else:
                raise
        except CalledProcessError:
            pass

    def get_blocked_ips4(self, name=None):
        block_ipset4 = self.get_block_ipset4(name)
        return block_ipset4.getEntries()

    def get_blocked_ips6(self, name=None):
        block_ipset6 = self.get_block_ipset6(name)
        return block_ipset6.getEntries()

    @do_maybe_not_enabled
    def remove_ipset_from_zone(self, zone, ipset_name):
        # drop_zone.removeSource('ipset:')
        zone.removeSource('ipset:{}'.format(
            ipset_name
        ))

    @do_maybe_invalid_ipset
    def clear_ipset_by_name(self, ipset_name):
        try:
            # does not work: ipset.setEntries([])
            self.fw.setEntries(ipset_name, [])
        except dbus.exceptions.DBusException:
            pass

    @do_maybe_invalid_ipset
    def destroy_ipset_by_name(self, name):
        log.info('Destroying IPSet {}'.format(name))
        # firewalld up to this commit
        # https://github.com/firewalld/firewalld/commit/f5ed30ce71755155493e78c13fd9036be8f70fc4
        # does not delete runtime ipsets, so we have to clear them :(
        # they are not removed from runtime as still reported by ipset -L
        # although they *are* removed from FirewallD
        if name not in self.fw.getIPSets():
            return

        ipset = self.config.getIPSetByName(name)
        if ipset:
            self.clear_ipset_by_name(name)
            ipset.remove()

    def get_blocked_countries(self):
        blocked_countries = []
        all_ipsets = self.fw.getIPSets()
        from .Countries import Countries
        countries = Countries()
        for ipset_name in all_ipsets:
            if ipset_name.startswith('fds-'):
                country_code = ipset_name.split('-')[1]
                if country_code in countries.names_by_code:
                    blocked_countries.append(countries.names_by_code[country_code])
        return blocked_countries

    def update_ipsets(self):
        need_reload = False
        all_ipsets = self.fw.getIPSets()
        from .Countries import Countries
        countries = Countries()
        is_tor_blocked = False
        for ipset_name in all_ipsets:
            if ipset_name.startswith('fds-tor-'):
                is_tor_blocked = True
            elif ipset_name.startswith('fds-'):
                country_code = ipset_name.split('-')[1]
                if country_code in countries.names_by_code:
                    country_name = countries.names_by_code[country_code]
                    country = countries.get_by_name(country_name)
                    self.block_country(country, reload=False)
                    need_reload = True
        if is_tor_blocked:
            self.block_tor(reload=False)
            need_reload = True
        if need_reload:
            self.fw.reload()
        return True

    def reset(self):
        drop_zone = self.config.getZoneByName('drop')

        self.remove_ipset_from_zone(drop_zone, self.NETWORKBLOCK_IPSET4)
        self.destroy_ipset_by_name(self.NETWORKBLOCK_IPSET4)

        self.remove_ipset_from_zone(drop_zone, self.NETWORKBLOCK_IPSET6)
        self.destroy_ipset_by_name(self.NETWORKBLOCK_IPSET6)

        all_ipsets = self.fw.getIPSets()
        # get any ipsets prefixed with "fds-"
        for ipset_name in all_ipsets:
            if ipset_name.startswith('fds-'):
                self.remove_ipset_from_zone(drop_zone, ipset_name)
                self.destroy_ipset_by_name(ipset_name)

        self.fw.reload()

    def block_tor(self, reload=True):
        log.info('Blocking Tor exit nodes')
        w = WebClient()
        tor4_exits = w.get_tor_exits(family=4)
        tor6_exits = w.get_tor_exits(family=6)

        tor4_ipset = self.get_create_set('fds-tor-4')
        self.ensure_ipset_entries(tor4_ipset, tor4_exits)

        tor6_ipset = self.get_create_set('fds-tor-6', family='inet6')
        self.ensure_ipset_entries(tor6_ipset, tor6_exits)

        self.ensure_block_ipset_in_drop_zone(tor4_ipset)
        self.ensure_block_ipset_in_drop_zone(tor6_ipset)
        if reload:
            log.info('Reloading FirewallD...')
            self.fw.reload()
        log.info('Done!')
        # while cron will do "sync" behavior"

    def block_country(self, country, reload=True):
        # print('address/netmask is invalid: %s' % sys.argv[1])
        # parse out as a country

        log.info('Blocking {} {}'.format(country.name, country.getFlag()))
        # print("\N{grinning face}")

        # TODO get aggregated zone file, save as cache,
        # do diff to know which stuff was changed and add/remove blocks
        # https://docs.python.org/2/library/difflib.html
        # TODO persist info on which countries were blocked (in the config file)
        # then sync zones via "fds cron"
        # TODO conditional get test on getpagespeed.com
        w = WebClient()
        country_networks = w.get_country_networks(country=country)

        ipset = self.get_create_set(country.get_set_name())
        self.ensure_ipset_entries(ipset, country_networks)

        # this is slow. setEntries is a lot faster
        # for network in tqdm(country_networks, unit='network',
        #                     desc='Adding {} networks to IPSet {}'.format(c.getNation(), c.get_set_name())):
        #     log.debug(network)
        #     fw.ensure_entry_in_ipset(ipset=ipset, entry=network)

        # TODO retry, timeout
        # this action re-adds all entries entirely
        # there should be "fds-<country.code>-<family>" ip set
        self.ensure_block_ipset_in_drop_zone(ipset)
        if reload:
            log.info('Reloading FirewallD...')
            self.fw.reload()
        log.info('Done!')
        # while cron will do "sync" behavior"

    def unblock_country(self, ip_or_country_name):
        # print('address/netmask is invalid: %s' % sys.argv[1])
        # parse out as a country
        from .Countries import Countries
        countries = Countries()
        c = countries.get_by_name(ip_or_country_name)

        if not c:
            log.error('{} does not look like a correct IP or a country name'.format(ip_or_country_name))
            return False

        drop_zone = self.config.getZoneByName('drop')

        log.info('Unblocking {} {}'.format(c.name, c.getFlag()))

        self.remove_ipset_from_zone(drop_zone, c.get_set_name())
        self.destroy_ipset_by_name(c.get_set_name())
        log.info('Reloading FirewallD...')
        self.fw.reload()
        log.info('Done!')
        # while cron will do "sync" behavior"

    def unblock_ip(self, ip_or_country_name):
        block_ipset = self.get_block_ipset_for_ip(ip_or_country_name)
        if not block_ipset:
            # TODO err: unsupported protocol
            raise Exception('Unsupported protocol')
        log.info(
            'Removing {} from block set {}'.format(
                ip_or_country_name, block_ipset.get_property('name')
            )
        )
        self.ensure_entry_not_in_ipset(block_ipset, ip_or_country_name)
        log.info('Reloading FirewallD to apply permanent configuration')
        self.fw.reload()
