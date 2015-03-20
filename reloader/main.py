# coding: utf-8

import os
import redis
import logging
from subprocess import check_call

from reloader.ensure import ensure_file, ensure_file_absent
from reloader.config import load_config
from reloader.templates import template

config = load_config()
rds = redis.Redis(config.redis_host, config.redis_port)
logging.basicConfig(level=logging.INFO, format='%(levelname)s - %(asctime)s: %(message)s')
logger = logging.getLogger(__name__)

def watch():
    pub = rds.pubsub()
    pub.subscribe(config.watch_key)
    try:
        for data in pub.listen():
            if data['type'] != 'message':
                continue
            if data['data'] == 'stop':
                break
            logger.info('New node of [%s] published, reload' % data['data'])
            service_reload(data['data'])
            logger.info('Reload of [%s] done' % data['data'])
    except Exception as e:
        logger.exception(e)
    finally:
        pub.unsubscribe()

def service_reload(appname):
    entrypoints = rds.hkeys(config.entrypoints_key % appname)
    backends = {entrypoint: list(rds.smembers(config.backends_key % entrypoint)) for entrypoint in entrypoints}
    reload_nginx_config(appname, backends)
    reload_nginx()

def reload_nginx_config(appname, backends):

    def _check_backends(b):
        """check if backends is not {'entry1': [], 'entry2': []}..."""
        return any(b.values())

    up_conf = os.path.join(config.upstream_dir, '{0}.conf'.format(appname))
    server_conf = os.path.join(config.server_dir, '{0}.conf'.format(appname))
    if not _check_backends(backends):
        ensure_file_absent(up_conf)
        ensure_file_absent(server_conf)
    else:
        upstream_nginx_conf = template.render_template('/upstream_nginx.jinja',
                appname=appname, backends=backends)
        server_nginx_conf = template.render_template('/server_nginx.jinja',
                appname=appname, backends=backends)
        ensure_file(up_conf, content=upstream_nginx_conf)
        ensure_file(server_conf, content=server_nginx_conf)

def reload_nginx():
    try:
        check_call([config.nginx, '-s', 'reload'])
    except Exception as e:
        logger.exception('Reload command failed, %s' % e)

def main():
    try:
        watch()
    except KeyboardInterrupt:
        logger.info('Catch ctrl-c, stopped')
