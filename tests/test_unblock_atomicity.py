"""Exercise partial unbans without a live firewall or Cloudflare account."""
from __future__ import unicode_literals

import importlib
import ipaddress
import sys
import types
import unittest

try:
    from unittest.mock import MagicMock, patch
except ImportError:
    from mock import MagicMock, patch


def load_firewall_modules():
    """Load the adapters, substituting only unavailable platform imports."""
    try:
        import dbus
        import firewall.client
    except ImportError:
        class DBusException(Exception):
            def __init__(self, message, name=None):
                super(DBusException, self).__init__(message)
                self.name = name

            def get_dbus_name(self):
                return self.name

            def get_dbus_message(self):
                return str(self)

        dbus = types.ModuleType('dbus')
        dbus.exceptions = types.ModuleType('dbus.exceptions')
        dbus.exceptions.DBusException = DBusException
        firewall = types.ModuleType('firewall')
        client = types.ModuleType('firewall.client')
        client.FirewallClient = object
        client.FirewallClientIPSetSettings = object
        with patch.dict(sys.modules, {'dbus': dbus, 'firewall': firewall,
                                     'firewall.client': client}):
            return (importlib.import_module('fds.FirewallWrapper'),
                    importlib.import_module('fds.fds'))
    return (importlib.import_module('fds.FirewallWrapper'),
            importlib.import_module('fds.fds'))


class FirewallCleanupTests(unittest.TestCase):
    def setUp(self):
        self.module, self.cli = load_firewall_modules()
        with patch.object(self.module.FirewallWrapper, '__init__', return_value=None):
            self.wrapper = self.module.FirewallWrapper()
        self.wrapper.fw = MagicMock()
        self.wrapper.config = MagicMock()
        self.wrapper.config.getIPSetNames.return_value = ['networkblock4']
        self.ipset = self.wrapper.config.getIPSetByName.return_value
        self.ip = ipaddress.ip_network('192.0.2.253')

    def error(self, message, name='org.fedoraproject.FirewallD1.Exception'):
        return self.module.dbus.exceptions.DBusException(message, name=name)

    def test_missing_permanent_entry_still_removes_runtime(self):
        self.ipset.removeEntry.side_effect = self.error('NOT_ENABLED: entry')
        self.assertTrue(self.wrapper.unblock_ip(self.ip))
        self.wrapper.fw.removeEntry.assert_called_once_with('networkblock4', str(self.ip))
        self.assertEqual(self.wrapper.fw.reload.call_count, 0)

    def test_missing_runtime_entry_still_removes_permanent(self):
        self.wrapper.fw.removeEntry.side_effect = self.error('NOT_ENABLED: entry')
        self.assertTrue(self.wrapper.unblock_ip(self.ip))
        self.ipset.removeEntry.assert_called_once_with(str(self.ip))

    def test_missing_ipsets_do_not_create_them(self):
        self.wrapper.config.getIPSetNames.return_value = []
        self.wrapper.fw.removeEntry.side_effect = self.error('INVALID_IPSET: networkblock4')
        self.assertTrue(self.wrapper.unblock_ip(self.ip))
        self.assertEqual(self.wrapper.config.addIPSet.call_count, 0)

    def test_permanent_failure_still_removes_runtime(self):
        self.ipset.removeEntry.side_effect = self.error('ACCESS_DENIED: denied')
        self.assertFalse(self.wrapper.unblock_ip(self.ip))
        self.wrapper.fw.removeEntry.assert_called_once_with('networkblock4', str(self.ip))

    def test_runtime_failure_still_removes_permanent(self):
        self.wrapper.fw.removeEntry.side_effect = self.error('ACCESS_DENIED: denied')
        self.assertFalse(self.wrapper.unblock_ip(self.ip))
        self.ipset.removeEntry.assert_called_once_with(str(self.ip))

    def test_other_dbus_service_not_enabled_is_failure(self):
        self.wrapper.fw.removeEntry.side_effect = self.error('NOT_ENABLED: denied', 'other.service')
        self.assertFalse(self.wrapper.unblock_ip(self.ip))

    def test_cli_reaches_cloudflare_after_firewall_failure(self):
        with patch.object(self.cli, 'FirewallWrapper') as fw, \
                patch('cds.CloudflareWrapper.CloudflareWrapper') as cf:
            fw.return_value.unblock_ip.side_effect = RuntimeError('firewall offline')
            cf.return_value.unblock_ip.return_value = True
            self.assertEqual(self.cli.action_unblock(str(self.ip)), 1)
            cf.return_value.unblock_ip.assert_called_once_with(self.ip)

    def test_cli_reaches_cloudflare_after_firewall_constructor_failure(self):
        with patch.object(self.cli, 'FirewallWrapper', side_effect=RuntimeError('offline')), \
                patch('cds.CloudflareWrapper.CloudflareWrapper') as cf:
            cf.return_value.unblock_ip.return_value = True
            self.assertEqual(self.cli.action_unblock(str(self.ip)), 1)
            cf.return_value.unblock_ip.assert_called_once_with(self.ip)

    def test_cli_exit_codes(self):
        for fw_ok, cf_ok, code in [(True, True, 0), (False, True, 1), (True, False, 1)]:
            with patch.object(self.cli, 'FirewallWrapper') as fw, \
                    patch('cds.CloudflareWrapper.CloudflareWrapper') as cf:
                fw.return_value.unblock_ip.return_value = fw_ok
                cf.return_value.unblock_ip.return_value = cf_ok
                self.assertEqual(self.cli.action_unblock(str(self.ip)), code)

    def test_ipv6_uses_ipv6_ipset(self):
        self.wrapper.config.getIPSetNames.return_value = ['networkblock6']
        ip = ipaddress.ip_network('2001:db8::1')
        self.assertTrue(self.wrapper.unblock_ip(ip))
        self.wrapper.fw.removeEntry.assert_called_once_with('networkblock6', str(ip))

    def test_missing_firewall_entry_still_cleans_cloudflare(self):
        self.ipset.removeEntry.side_effect = self.error('NOT_ENABLED: entry')
        self.wrapper.fw.removeEntry.side_effect = self.error('NOT_ENABLED: entry')
        with patch.object(self.cli, 'FirewallWrapper', return_value=self.wrapper), \
                patch('cds.CloudflareWrapper.CloudflareWrapper') as cf:
            cf.return_value.unblock_ip.return_value = True
            self.assertEqual(self.cli.action_unblock(str(self.ip)), 0)
            cf.return_value.unblock_ip.assert_called_once_with(self.ip)


class CloudflareCleanupTests(unittest.TestCase):
    def setUp(self):
        from cds.CloudflareWrapper import CloudflareWrapper
        from CloudFlare.exceptions import CloudFlareAPIError
        self.error = CloudFlareAPIError
        self.wrapper = CloudflareWrapper.__new__(CloudflareWrapper)
        self.wrapper._base = None
        self.wrapper.use = True
        self.wrapper.account_lookup_failed = False
        self.wrapper.all_accounts = [{'id': 'account', 'name': 'account'}]
        self.wrapper.accounts = MagicMock()
        self.api = self.wrapper.accounts.firewall.access_rules.rules
        self.api.get.return_value = []

    def rule(self, rule_id='rule', mode='block', value='192.0.2.253'):
        return {'id': rule_id, 'mode': mode,
                'configuration': {'target': 'ip', 'value': value},
                'scope': {'type': 'user', 'id': 'owner'}}

    def test_already_clean_is_success(self):
        self.assertTrue(self.wrapper.unblock_ip('192.0.2.253'))
        self.assertEqual(self.api.delete.call_count, 0)

    def test_user_scoped_rule_returned_by_account_is_removed(self):
        self.api.get.return_value = [self.rule()]
        self.assertTrue(self.wrapper.unblock_ip('192.0.2.253'))
        self.api.delete.assert_called_once_with('account', 'rule')

    def test_preserves_allow_challenge_and_other_addresses(self):
        self.api.get.return_value = [self.rule('allow', 'whitelist'),
                                     self.rule('challenge', 'challenge'),
                                     self.rule('other', value='192.0.2.252')]
        self.assertTrue(self.wrapper.unblock_ip('192.0.2.253'))
        self.assertEqual(self.api.delete.call_count, 0)

    def test_list_failure_is_reported(self):
        self.api.get.side_effect = self.error(10000, 'authentication error')
        self.assertFalse(self.wrapper.unblock_ip('192.0.2.253'))

    def test_delete_failure_continues_to_other_rules(self):
        self.api.get.return_value = [self.rule('first'), self.rule('second')]
        self.api.delete.side_effect = [self.error(10000, 'authentication error'), None]
        self.assertFalse(self.wrapper.unblock_ip('192.0.2.253'))
        self.assertEqual(self.api.delete.call_count, 2)

    def test_delete_race_is_success_only_after_verified_absence(self):
        self.api.get.side_effect = [[self.rule()], []]
        self.api.delete.side_effect = self.error(10009, 'gone')
        self.assertTrue(self.wrapper.unblock_ip('192.0.2.253'))
        self.assertEqual(self.api.get.call_count, 2)

    def test_pagination_collects_before_deleting(self):
        self.api.get.side_effect = [[self.rule(str(i)) for i in range(50)], [self.rule('last')]]
        self.assertTrue(self.wrapper.unblock_ip('192.0.2.253'))
        self.assertEqual(self.api.delete.call_count, 51)
        self.assertEqual(self.api.get.call_args_list[1][1]['params']['page'], 2)

    def test_failed_account_discovery_is_not_disabled_success(self):
        self.wrapper.use = False
        self.wrapper.account_lookup_failed = True
        self.assertFalse(self.wrapper.unblock_ip('192.0.2.253'))

    def test_ipv6_address_is_not_silently_skipped(self):
        self.assertTrue(self.wrapper.unblock_ip('2001:db8::1'))
        self.assertEqual(self.api.get.call_count, 1)
        self.assertEqual(self.api.get.call_args[1]['params']['configuration.target'], 'ip6')
        self.assertEqual(self.api.get.call_args[1]['params']['configuration.value'], '2001:db8::1')

    def test_ipv4_slash17_is_not_silently_skipped(self):
        from cds.CloudflareWrapper import network_for_cloudflare
        self.assertEqual(len(list(network_for_cloudflare('192.0.0.0/17'))), 128)


if __name__ == '__main__':
    unittest.main()
