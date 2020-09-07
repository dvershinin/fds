# TODO cds set txt example.com  "value" (unique by name, suitable for dkim set script


from CloudFlare import CloudFlare
import logging as log

from CloudFlare.exceptions import CloudFlareAPIError

cf = CloudFlare()

zoneDomain = 'pokerchiplounge.com'

def ensure_unique_record_for_name(hostname, )

try:
    params = {'name': zoneDomain}
    zones = cf.zones.get(params=params)[0]
    print(zones)
except CloudFlareAPIError as e:
    log.error('Bad auth - %s' % e)
    print('badauth')

    if len(zones) == 0:
        log.error('No host')
        return 'nohost'

    if len(zones) != 1:
        log.error('/zones.get - %s - api call returned %d items' % (zoneDomain, len(zones)))
        return 'notfqdn'

    zone_id = zones[0]['id']
    log.debug("Zone ID is {}".format(zone_id))

    try:
        params = {'name': hostname, 'match': 'all', 'type': ipAddressType}
        dns_records = cf.zones.dns_records.get(zone_id, params=params)
    except CloudFlareAPIError as e:
        log.error('/zones/dns_records %s - %d %s - api call failed' % (hostname, e, e))
        return '911'

    desiredRecordData = {
        'name': hostname,
        'type': ipAddressType,
        'content': ip
    }
    if ttl:
        desiredRecordData['ttl'] = ttl

    # update the record - unless it's already correct
    for dnsRecord in dns_records:
        oldIp = dnsRecord['content']
        oldIpType = dnsRecord['type']

        if ipAddressType not in ['A', 'AAAA']:
            # we only deal with A / AAAA records
            continue

        if ipAddressType != oldIpType:
            # only update the correct address type (A or AAAA)
            # we don't see this becuase of the search params above
            log.debug('IGNORED: %s %s ; wrong address family' % (hostname, oldIp))
            continue

        if ip == oldIp:
            log.info('UNCHANGED: %s == %s' % (hostname, ip))
            # nothing to do, record already matches to desired IP
            return 'nochg'

        # Yes, we need to update this record - we know it's the same address type
        dnsRecordId = dnsRecord['id']

        try:
            cf.zones.dns_records.put(zone_id, dnsRecordId, data=desiredRecordData)
        except CloudFlare.exceptions.CloudFlareAPIError as e:
            log.error('/zones.dns_records.put %s - %d %s - api call failed' % (hostname, e, e))
            return '911'
        log.info('UPDATED: %s %s -> %s' % (hostname, oldIp, ip))
        return 'good'

    # no exsiting dns record to update - so create dns record
    try:
        cf.zones.dns_records.post(zone_id, data=desiredRecordData)
        log.info('CREATED: %s %s' % (hostname, ip))
        return 'good'
    except CloudFlare.exceptions.CloudFlareAPIError as e:
        log.error('/zones.dns_records.post %s - %d %s - api call failed' % (hostname, e, e))
        return '911'
