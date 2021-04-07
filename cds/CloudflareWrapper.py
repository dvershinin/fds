import os

import six
from os.path import expanduser, exists, dirname
from CloudFlare import CloudFlare
from CloudFlare.exceptions import CloudFlareAPIError
import logging as log  # for verbose output
from netaddr import IPNetwork, IPAddress
# long story short, "configparser" Python 2 backport RPM package is no good because it strips init py
try:
    # Python 3
    from configparser import ConfigParser
except ImportError:
    # Python 2
    from ConfigParser import SafeConfigParser as ConfigParser

home = expanduser("~")
# if cloudflare.cfg exists, we error on invalid credentials
# otherwise all ops are "pass" unless interactive mode and user confirmed Cloudflare use
# ~/.cloudflare/cloudflare.cfg
cf_config_filename = "{}/.cloudflare/cloudflare.cfg".format(home)


def network_for_cloudflare(network):
    """
    Cloudflare only supports bare IP, and /16 or /24 CIDR ranges
    # For bare IP, we must clean up trailing /32
    # For networks /25-31 we return array of individual addresses
    # For networks /24, as is
    # For networks /17-23, /24 subnets
    # For networks /16, as is
    # For network /1-15, /16 subnets
    E.g. 114.119.128.0/18 should be split to multiple smaller /24 networks
    E.g. http://jodies.de/ipcalc?host=114.119.128.0&mask1=18&mask2=24

    Args:
        network ():

    Returns:

    """
    network = str(network)
    network = IPNetwork(network)
    cidr = network.prefixlen
    nets = []
    if cidr == 32:
        # case to ip addr to remove /32 from presentation (for Cloudflare)
        nets.append(IPAddress(network))
    elif cidr < 32:
        if cidr >= 25:
            # 25-31
            for ip in network:
                nets.append(ip)
            pass
        elif cidr == 24:
            nets.append(network)
        elif cidr > 17:
            # 17-23
            nets = network.subnet(24, count=None, fmt=None)
        elif cidr == 16:
            nets.append(network)
        elif cidr <= 15:
            nets = network.subnet(16, count=None, fmt=None)
    return nets


def suggest_set_up():
    print(
        "Cloudflare authentication is not set or invalid. Create a token by visiting "
        "https://dash.cloudflare.com/profile/api-tokens")
    print("There, choose 'Create Custom Token' ")
    print('Type n to keep Cloudflare integration disabled, or enter token: ')
    cf_token = six.moves.input("Cloudflare token: ")
    # TODO prefer "fds" section in cloudflare.cfg
    if cf_token and 'n' != cf_token.lower():
        config = ConfigParser()
        config.read(cf_config_filename)
        if not config.has_section("CloudFlare"):
            config.add_section("CloudFlare")
        config['CloudFlare']['token'] = cf_token
        # ensure dir .cloudflare exists:
        if not exists(dirname(cf_config_filename)):
            os.makedirs(dirname(cf_config_filename))
        with open(cf_config_filename, 'w') as configfile:  # save
            config.write(configfile)
            # TODO evaluate security while creation
            os.chmod(cf_config_filename, 0o600)
    else:
        print('No token')


class CloudflareWrapper(CloudFlare):

    def __init__(self, set_up=False):
        super(CloudflareWrapper, self).__init__()

        self.use = exists(cf_config_filename)
        # The premise is that user creates fds specific token and/or ensures "Account Resources"
        # setting for it to include only account fds operates on. So we do blocks on each account
        if not self.use:
            return
        try:
            self.all_accounts = self.accounts.get()
        except CloudFlareAPIError as e:
            print("Cloudflare API error: {}".format(e))
            exit(1)


    def block_ip(self, ip, comment='fds'):
        if not self.use:
            log.info('Skipped block in Cloudflare as it was not set up. Run fds config?')
            return
        nets = network_for_cloudflare(ip)
        nets_len = len(nets)
        if nets_len > 1:
            log.info('Converted supplied network into {} entries for Cloudflare'.format(nets_len))
        for a in self.all_accounts:
            for n in nets:
                log.info('Blocking {} in Cloudflare account {}'.format(ip, a['name']))
                target = None
                if isinstance(n, IPAddress):
                    if n.version == 4:
                        target = 'ip'
                    elif n.version == 6:
                        target = 'ip6'
                elif isinstance(n, IPNetwork):
                    target = 'ip_range'
                block_data = {
                    'mode': 'block',
                    'configuration': {
                        'target': target,
                        'value': str(n),
                    },
                    'notes': comment
                }
                log.debug(block_data)
                # https://api.cloudflare.com/#account-level-firewall-access-rule-create-access-rule
                try:
                    self.accounts.firewall.access_rules.rules.post(a['id'], data=block_data)
                except CloudFlareAPIError as e:
                    if str(e) == 'firewallaccessrules.api.duplicate_of_existing':
                        pass
                    else:
                        raise e


    def set_country_access_rule(self, country, mode, comment='fds'):
        """
        TODO search existing rule in order to update vs blind insert
        https://api.cloudflare.com/#account-level-firewall-access-rule-create-access-rule
        Args:
            country ():
            mode ():
            comment ():

        Returns:

        """
        if not self.use:
            log.info('Skipped update in Cloudflare as it was not set up. Run fds config?')
            return
        for a in self.all_accounts:
            log.info('Setting access rule to {} {} in Cloudflare account {}'.format(mode, country.name, a['name']))
            rule_data = {
                'mode': mode,
                'configuration': {
                    'target': 'country',
                    'value': country.code,
                },
                'notes': comment
            }
            log.debug(rule_data)

            try:
                self.accounts.firewall.access_rules.rules.post(a['id'], data=rule_data)
            except CloudFlareAPIError as e:
                if str(e) == 'firewallaccessrules.api.duplicate_of_existing':
                    pass
                else:
                    raise e

    def block_country(self, country, comment='fds'):
        try:
            self.set_country_access_rule(country, 'block')
        except CloudFlareAPIError as e:
            if str(e) == 'firewallaccessrules.api.not_entitled.country_block':
                log.warning('Not entitled to block countries in Cloudflare. Setting Captcha challenge instead')
                self.set_country_access_rule(country, 'challenge')
            else:
                raise e

    def unblock_ip(self, ip):
        pass
