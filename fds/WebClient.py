import requests
from cachecontrol import CacheControl
from cachecontrol.caches import FileCache
from tqdm import tqdm
import logging as log

from .__about__ import __version__


def get_country_ipblocks_url(country):
    return 'https://www.ipdeny.com/ipblocks/data/aggregated/{}-aggregated.zone'.format(
        country.code.lower()
    )


def get_country_zone_filename(country):
    return '/var/lib/fds/{}.zone'.format(country.code.lower())


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
