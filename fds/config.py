from cds.CloudflareWrapper import suggest_set_up, cf_config_filename
from .FirewallWrapper import FirewallWrapper
import logging as log


def open_web_if_webserver_running():
    fw = FirewallWrapper()
    from .utils import is_process_running, query_yes_no
    webserver_running = is_process_running('nginx')
    if webserver_running:
        zone = fw.fw.getDefaultZone()
        zone_services = fw.fw.getServices(zone)
        if 'http' not in zone_services or 'https' not in zone_services:
            open_web = query_yes_no('Webserver is running. Open up HTTP/HTTPs ports?')
            if open_web:
                fw.add_service('http')
                fw.add_service('https')
        else:
            log.info('Webserver is running and ports are already open')


def action_config():
    # if nginx runs, check/ask to ensure open web ports:
    open_web_if_webserver_running()
    # if cloudflare.cfg is missing, check/ask to ensure Cloudflare support:
    from cds.CloudflareWrapper import CloudflareWrapper
    cw = CloudflareWrapper()
    if cw.use:
        log.info('Using Cloudflare integration because {} exists'.format(cf_config_filename))
    else:
        suggest_set_up()
