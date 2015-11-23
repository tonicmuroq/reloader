# coding: utf-8

import json
import logging
import requests

from reloader.config import config

logger = logging.getLogger(__name__)

__backends_cache = {}


def _backends_no_diff(old, new):
    return set(old) == set(new)


def get_balancers(appname, entrypoint):
    url = '%s/ajax/lb/%s/%s/' % (config.ainur_url, appname, entrypoint)
    if not url.startswith('http://'):
        url = 'http://' + url
    resp = requests.get(url)
    return resp.json()


def update_balancer(upstream_url, backend_name, servers):
    if not servers:
        requests.delete(upstream_url, data=json.dumps({'backend': backend_name}))
        return

    servers = ['server %s;' % b for b in servers]
    requests.put(upstream_url, data=json.dumps({'backend': backend_name, 'servers': servers}))


def service_reload_openresty(appname, backends):
    for entrypoint, servers in backends.iteritems():
        r = get_balancers(appname, entrypoint)
        if not r:
            continue

        backend_name = r['backend_name']
        old_backends = __backends_cache.get(backend_name, [])
        if _backends_no_diff(old_backends, servers):
            logger.info('No new nodes found for [%s], ignore' % appname)
            continue

        __backends_cache[backend_name] = servers

        upstream_urls = [b['lb_client']['upstream_addr'] for b in r['balancers']]
        for upstream_url in upstream_urls:
            update_balancer(upstream_url, backend_name, servers)
