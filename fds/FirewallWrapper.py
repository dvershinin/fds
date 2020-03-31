from firewall.client import FirewallClient
from firewall.client import FirewallClientIPSetSettings

class FirewallWrapper:
    NETWORKBLOCK_IPSET4 = 'networkblock4'
    def __init__(self):
        self.fw = FirewallClient()
        self.config = self.fw.config()

    def ensure_block_ipset4(self):
        ipsets = self.config.getIPSetNames()
        if FirewallWrapper.NETWORKBLOCK_IPSET4 in ipsets:
            return True
        settings = FirewallClientIPSetSettings()
        settings.setType('hash:net')
        self.config.addIPSet(FirewallWrapper.NETWORKBLOCK_IPSET4, settings)

    def block(self, ip):
        self.ensure_block_ipset4()
        self.config.getIPSetByName(FirewallWrapper.NETWORKBLOCK_IPSET4).getEntries()
        # TODO no error if exists
        self.config.getIPSetByName(FirewallWrapper.NETWORKBLOCK_IPSET4).addEntry('1.2.3.4')
        # self.fw.addEntry
        # self.fw.addEntry(FirewallWrapper.NETWORKBLOCK_IPSET4, ip)