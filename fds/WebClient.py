import requests
from cachecontrol import CacheControl
from cachecontrol.caches import FileCache
from .__about__ import __version__


class WebClient:

    def __init__(self):
        s = requests.session()
        s.headers.update({'User-Agent': 'fds/{}'.format(__version__)})
        self.cs = CacheControl(s, cache=FileCache('.'))


    def get_country_networks(self, country):
        r = self.cs.get(
            'https://www.ipdeny.com/ipblocks/data/aggregated/{}-aggregated.zone'.format(
                country.code.lower()
            )
        )
        return r.text.splitlines()
