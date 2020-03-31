import dbus
from firewall.client import FirewallClient
from firewall.client import FirewallClientIPSetSettings
from netaddr import IPAddress
import logging as log  # for verbose output


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
        ip = IPAddress(ip)
        if ip.version == 4:
            return self.get_block_ipset4()
        if ip.version == 6:
            return self.get_block_ipset6()
        return None


    @do_maybe_already_enabled
    def ensure_block_ipset_in_drop_zone(self, ipset):
        # ensure that the block ipset is in drop zone:
        drop_zone = self.config.getZoneByName('drop')
        self.config.getIPSetNames
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
        block_ipset.addEntry(ip)
        self.fw.reload()


    @do_maybe_not_enabled
    def remove_ipset_from_zone(self, zone, ipset_name):
        # drop_zone.removeSource('ipset:')
        zone.removeSource('ipset:{}'.format(
            ipset_name
        ))


    def reset(self):
        # firewalld up to this commit https://github.com/firewalld/firewalld/commit/f5ed30ce71755155493e78c13fd9036be8f70fc4
        # does not delete runtime ipsets, so we can only clear them? :(
        try:
            self.fw.setEntries(self.NETWORKBLOCK_IPSET4, [])
        except dbus.exceptions.DBusException:
            pass
        try:
            self.fw.setEntries(self.NETWORKBLOCK_IPSET6, [])
        except dbus.exceptions.DBusException:
            pass

        block_ipset4 = self.get_block_ipset4()
        block_ipset4.setEntries([])
        block_ipset4.remove()
        block_ipset6 = self.get_block_ipset6()
        block_ipset6.remove()

        drop_zone = self.config.getZoneByName('drop')
        self.remove_ipset_from_zone(drop_zone, self.NETWORKBLOCK_IPSET4)
        self.remove_ipset_from_zone(drop_zone, self.NETWORKBLOCK_IPSET6)

        self.fw.reload()


