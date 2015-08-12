# coding: utf-8

import os
import redis
import logging
from subprocess import check_call

import reloader
from reloader.ensure import ensure_file, ensure_file_absent, ensure_dir
from reloader.config import load_config
from reloader.templates import Jinja2

config = load_config()
rds = redis.Redis(config.redis_host, config.redis_port)
template = Jinja2(reloader.__name__, template_folder=config.template_folder)

logging.basicConfig(level=logging.INFO, format='%(levelname)s - %(asctime)s: %(message)s')
logger = logging.getLogger(__name__)

backends_cache = {}

def _judge_backends_diff(old, new):
    if set(old.keys()) != set(new.keys()):
        return True
    for entrypoint in new.keys():
        old_backends = old[entrypoint]
        new_backends = new[entrypoint]
        if set(old_backends) != set(new_backends):
            return True
    return False

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

    backends = {entrypoint: list(rds.smembers(config.backends_key % (appname, entrypoint))) for entrypoint in entrypoints}
    old_backends = backends_cache.get(appname, {})

    if not _judge_backends_diff(old_backends, backends):
        return
        
    backends_cache[appname] = backends

    # ensure nginx access/error log dir
    ensure_dir(os.path.join(config.log_prefix, appname))

    # reload nginx
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
                appname=appname, backends=backends, config=config)
        server_nginx_conf = template.render_template('/server_nginx.jinja',
                appname=appname, backends=backends, config=config)
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
