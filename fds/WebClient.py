from __future__ import unicode_literals

import requests
from cachecontrol import CacheControl
from cachecontrol.caches import FileCache
from tqdm import tqdm
import logging as log

from .__about__ import __version__


def get_country_ipblocks_url(country):
    # we cannot use https:// reliably here because their cert has chain issues/expired!
    return 'http://www.ipdeny.com/ipblocks/data/aggregated/{}-aggregated.zone'.format(
        country.code.lower()
    )


def get_country_zone_filename(country):
    return '/var/lib/fds/{}.zone'.format(country.code.lower())


# monkey patching older requests library's response class so it can use context manager
# https://github.com/psf/requests/issues/4136
def requests_response_patched_enter(self):
    return self


def requests_response_patched_exit(self, *args):
    self.close()


if not hasattr(requests.Response, '__exit__'):
    requests.Response.__enter__ = requests_response_patched_enter
    requests.Response.__exit__ = requests_response_patched_exit


class WebClient:

    def __init__(self):
        s = requests.session()
        s.headers.update({'User-Agent': 'fds/{}'.format(__version__)})
        self.cs = CacheControl(s, cache=FileCache('/var/cache/fds'))


    def download_file(self, url, local_filename=None, display_name=None, return_type='filename'):
        contents = b''
        if local_filename is None:
            local_filename = url.split('/')[-1]
        # NOTE the stream=True parameter below
        with self.cs.get(url, stream=True) as r:
            r.raise_for_status()
            # content-length may be empty, default to 0
            file_size = int(r.headers.get('Content-Length', 0))
            bar_size = 1024
            # fetch 16 KB at a time
            chunk_size = 16384
            # how many bars are there in a chunk?
            chunk_bar_size = chunk_size / bar_size
            # bars are by KB
            num_bars = int(file_size / bar_size)

            pbar = tqdm(
                disable=None,  # disable on non-TTY
                total=num_bars,
                unit='KB',
                desc='Downloading {}'.format(local_filename if not display_name else display_name),
                leave=True  # progressbar stays
            )
            with open(local_filename, 'wb') as f:
                for chunk in r.iter_content(chunk_size=chunk_size):
                    if chunk:  # filter out keep-alive new chunks
                        f.write(chunk)
                        if return_type == 'contents':
                            contents = contents + chunk
                        # we fetch 8 KB, so we update progress by +8x
                        pbar.update(chunk_bar_size)
            pbar.set_description('Downloaded {}'.format(local_filename))
            pbar.close()

        return contents.decode("utf-8") if return_type == 'contents' else local_filename


    def get_country_networks(self, country):
        # r = self.cs.get(
        #     'https://www.ipdeny.com/ipblocks/data/aggregated/{}-aggregated.zone'.format(
        #         country.code.lower()
        #     )
        # )
        url = get_country_ipblocks_url(country)
        log.debug('Downloading {}'.format(url))
        content = self.download_file(
            url,
            display_name='{} networks list'.format(country.getNation()),
            local_filename=get_country_zone_filename(country),
            return_type='contents'
        )
        return content.splitlines()

    def get_tor_exits(self, family=4):
        url = 'https://lists.fissionrelays.net/tor/exits-ipv{}.txt'.format(family)
        log.debug('Downloading {}'.format(url))
        content = self.download_file(
            url,
            display_name='Tor IPv{} exits list'.format(family),
            local_filename='/var/lib/fds/tor-{}.zone'.format(family),
            return_type='contents'
        )
        return content.splitlines()
