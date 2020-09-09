# TODO cds set txt example.com  "value" (unique by name, suitable for dkim set script


from CloudFlare import CloudFlare
import logging as log

from CloudFlare.exceptions import CloudFlareAPIError

cf = CloudFlare()
