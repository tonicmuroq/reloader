# coding: utf-8

import json
import logging
import requests
from requests.adapters import HTTPAdapter
from requests.exceptions import RequestException

from reloader.config import config
from reloader.sms import send_sms

logger = logging.getLogger(__name__)

_backends_cache = {}
_session = requests.Session()
_session.mount('http://', HTTPAdapter(max_retries=10))


def _backends_no_diff(old, new):
    return set(old) == set(new)


def get_balancers(appname, entrypoint):
    url = '%s/ajax/lb/%s/%s/' % (config.ainur_url, appname, entrypoint)
    if not url.startswith('http://'):
        url = 'http://' + url
    try:
        resp = _session.get(url)
        return resp.json()
    except RequestException as e:
        send_sms('[Reloader Error] 我擦, 获取[%s:%s]后端失败, 更新失败' % (appname, entrypoint))
        logger.exception('Error when getting balancer for %s:%s' % (appname, entrypoint))
        logger.exception(e)
        return None


def update_balancer(upstream_url, backend_name, servers):
    if not servers:
        try:
            _session.delete(upstream_url, data=json.dumps({'backend': backend_name}))
        except RequestException as e:
            send_sms('[Reloader Error] 我去, 删除后端[%s]失败' % backend_name)
            logger.exception('Error when deleting backends for %s' % backend_name)
            logger.exception(e)
        return

    servers = ['server %s;' % b for b in servers]
    try:
        _session.put(upstream_url, data=json.dumps({'backend': backend_name, 'servers': servers}))
    except RequestException as e:
        send_sms('[Reloader Error] 尼玛啊, 更新后端[%s]失败' % backend_name)
        logger.exception('Error when updating backends for %s' % backend_name)
        logger.exception(e)


def service_reload_openresty(appname, backends):
    for entrypoint, servers in backends.iteritems():
        r = get_balancers(appname, entrypoint)
        if not r:
            continue

        backend_name = r['backend_name']
        old_backends = _backends_cache.get(backend_name, [])
        if _backends_no_diff(old_backends, servers):
            logger.info('No new nodes found for [%s], ignore' % appname)
            continue

        _backends_cache[backend_name] = servers

        upstream_urls = [b['lb_client']['upstream_addr'] for b in r['balancers']]
        for upstream_url in upstream_urls:
            update_balancer(upstream_url, backend_name, servers)
