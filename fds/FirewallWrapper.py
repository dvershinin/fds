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


class FirewallWrapper:
    NETWORKBLOCK_IPSET4 = 'networkblock4'
    NETWORKBLOCK_IPSET6 = 'networkblock6'


    def __init__(self):
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

    def get_block_ipset4(self):
        if FirewallWrapper.NETWORKBLOCK_IPSET4 in self.config.getIPSetNames():
            return self.config.getIPSetByName(
                FirewallWrapper.NETWORKBLOCK_IPSET4
            )
        settings = FirewallClientIPSetSettings()
        settings.setType('hash:net')
        settings.setOptions({
            'maxelem': '1000000',
            'family': 'inet',
            'hashsize': '4096'
        })
        return self.config.addIPSet(
            FirewallWrapper.NETWORKBLOCK_IPSET4, settings
        )


    def get_block_ipset6(self):
        if FirewallWrapper.NETWORKBLOCK_IPSET6 in self.config.getIPSetNames():
            return self.config.getIPSetByName(
                FirewallWrapper.NETWORKBLOCK_IPSET6
            )
        settings = FirewallClientIPSetSettings()
        settings.setType('hash:net')
        settings.setOptions({
            'maxelem': '1000000',
            'family': 'inet6',
            'hashsize': '4096'
        })
        return self.config.addIPSet(
            FirewallWrapper.NETWORKBLOCK_IPSET6, settings
        )


    def get_block_ipset_for_ip(self, ip):
        if ip.version == 4:
            return self.get_block_ipset4()
        if ip.version == 6:
            return self.get_block_ipset6()
        return None

    @do_maybe_already_enabled
    def ensure_ipset_entries(self, ipset, entries):
        return ipset.setEntries(entries)

    @do_maybe_already_enabled
    def ensure_entry_in_ipset(self, ipset, entry):
        return ipset.addEntry(str(entry))


    @do_maybe_already_enabled
    def ensure_block_ipset_in_drop_zone(self, ipset):
        # ensure that the block ipset is in drop zone:
        drop_zone = self.config.getZoneByName('drop')
        # self.config.getIPSetNames
        return drop_zone.addSource('ipset:{}'.format(
            ipset.get_property('name')
        ))

    @do_maybe_already_enabled
    def block(self, ip):
        block_ipset = self.get_block_ipset_for_ip(ip)
        if not block_ipset:
            # TODO err: unsupported protocol
            raise Exception('Unsupported protocol')
        self.ensure_block_ipset_in_drop_zone(block_ipset)
        log.info('Adding IP address {} to block set {}'.format(ip, block_ipset.get_property('name')))
        block_ipset.addEntry(str(ip))
        log.info('Reloading FirewallD to apply permanent configuration')
        self.fw.reload()


    @do_maybe_already_enabled
    def block_ip(self, ip):
        block_ipset = self.get_block_ipset_for_ip(ip)
        if not block_ipset:
            # TODO err: unsupported protocol
            raise Exception('Unsupported protocol')
        self.ensure_block_ipset_in_drop_zone(block_ipset)
        log.info('Adding IP address {} to block set {}'.format(ip, block_ipset.get_property('name')))
        block_ipset.addEntry(str(ip))
        log.info('Reloading FirewallD to apply permanent configuration')
        self.fw.reload()


    @do_maybe_not_enabled
    def remove_ipset_from_zone(self, zone, ipset_name):
        # drop_zone.removeSource('ipset:')
        zone.removeSource('ipset:{}'.format(
            ipset_name
        ))

    def clear_ipset_by_name(self, ipset_name):
        try:
            # does not work: ipset.setEntries([])
            self.fw.setEntries(ipset_name, [])
        except dbus.exceptions.DBusException:
            pass

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

    def reset(self):
        drop_zone = self.config.getZoneByName('drop')

        self.remove_ipset_from_zone(drop_zone, self.NETWORKBLOCK_IPSET4)
        self.destroy_ipset_by_name(self.NETWORKBLOCK_IPSET4)

        self.remove_ipset_from_zone(drop_zone, self.NETWORKBLOCK_IPSET6)
        self.destroy_ipset_by_name(self.NETWORKBLOCK_IPSET6)

        all_ipsets = self.fw.getIPSets()
        # get any ipsets prefixed with "fds-"
        for ipset_name in all_ipsets:
            self.remove_ipset_from_zone(drop_zone, ipset_name)
            self.destroy_ipset_by_name(ipset_name)

        self.fw.reload()


    def block_country(self, ip_or_country_name):
        # print('address/netmask is invalid: %s' % sys.argv[1])
        # parse out as a country
        from .Countries import Countries
        countries = Countries()
        c = countries.getByName(ip_or_country_name)

        if not c:
            log.error('{} does not look like a correct IP or a country name'.format(ip_or_country_name))
            return False

        log.info('Blocking {} {}'.format(c.name, c.getFlag()))
        # print("\N{grinning face}")

        # TODO get aggregated zone file, save as cache,
        # do diff to know which stuff was changed and add/remove blocks
        # https://docs.python.org/2/library/difflib.html
        # TODO persist info on which countries were blocked (in the config file)
        # then sync zones via "fds cron"
        # TODO conditional get test on getpagespeed.com
        w = WebClient()
        country_networks = w.get_country_networks(country=c)

        ipset = self.get_create_set(c.get_set_name())
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
        log.info('Reloading FirewallD...')
        self.fw.reload()
        log.info('Done!')
        # while cron will do "sync" behavior"
