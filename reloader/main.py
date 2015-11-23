# coding: utf-8

import redis
import logging

from reloader.nginx import service_reload_nginx
from reloader.openresty import service_reload_openresty
from reloader.config import config


logging.basicConfig(level=logging.INFO, format='%(levelname)s - %(asctime)s: %(message)s')
logger = logging.getLogger(__name__)

rds = redis.Redis(config.redis_host, config.redis_port)

reloader_function = {
    'nginx': service_reload_nginx,
    'openresty': service_reload_openresty,
}

service_reload = reloader_function[config.reloader_type]


def get_backends(appname):
    entrypoints = rds.hkeys(config.entrypoints_key % appname)
    return {entrypoint: list(rds.smembers(config.backends_key % (appname, entrypoint))) for entrypoint in entrypoints}


def watch():
    pub = rds.pubsub()
    pub.subscribe(config.watch_key)
    try:
        for data in pub.listen():
            if data['type'] != 'message':
                continue
            if data['data'] == 'stop':
                break
            logger.info('Reload Signal of [%s] published, reload' % data['data'])

            appname = data['data']
            backends = get_backends(appname)
            service_reload(appname, backends)
    except Exception as e:
        logger.exception(e)
    finally:
        pub.unsubscribe()

def main():
    try:
        watch()
    except KeyboardInterrupt:
        logger.info('Catch ctrl-c, stopped')
