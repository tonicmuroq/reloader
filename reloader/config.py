# coding: utf-8

import yaml
from optparse import OptionParser
from tabulate import tabulate

class Config(dict):

    def __getattr__(self, name):
        return self.get(name, None)

_default_config = {
    'watch_key': 'eru:discovery:published',
    'entrypoints_key': 'eru:app:%s:backends',
    'backends_key': 'eru:app:entrypoint:%s:backends',
    'nginx': 'nginx',
    'upstream_dir': '/etc/nginx/up.conf.d/',
    'server_dir': '/etc/nginx/s.conf.d/',
    'redis_host': '127.0.0.1',
    'redis_port': 6379,
    'daemonize': False,
}

def load_config():
    parser = OptionParser()
    parser.add_option('-c', '--config', dest='config_path', type='str', default=None)
    parser.add_option('-w', '--watch-key', dest='watch_key', type='str', default=None)
    parser.add_option('-e', '--entrypoints-key', dest='entrypoints_key', type='str', default=None)
    parser.add_option('-b', '--backends-key', dest='backends_key', type='str', default=None)
    parser.add_option('-n', '--nginx', dest='nginx', type='str', default=None)
    parser.add_option('-u', '--upstream-dir', dest='upstream_dir', type='str', default=None)
    parser.add_option('-s', '--server-dir', dest='server_dir', type='str', default=None)
    parser.add_option('-r', '--redis-host', dest='redis_host', type='str', default=None)
    parser.add_option('-p', '--redis-port', dest='redis_port', type='int', default=None)
    parser.add_option('-d', '--daemon', dest='daemonize', action='store_true', default=None)
    options, _ = parser.parse_args()

    file_config = _default_config
    if options.config_path:
        try:
            with open(options.config_path, 'r') as f:
                file_config.update(yaml.load(f))
        except IOError as e:
            print 'Failed to open %s:\n  %s\nignored\n' % (options.config_path, e)

    for k in _default_config.keys():
        cmd_value = getattr(options, k, '')
        if cmd_value is not None:
            file_config[k] = cmd_value

    print tabulate([[k, str(v)] for k, v in file_config.iteritems()], headers=['Config Key', 'Config Value'])
    return Config(**file_config)
