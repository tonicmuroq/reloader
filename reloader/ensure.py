# coding: utf-8

import os
import pwd
import errno

def get_uid(name):
    return pwd.getpwnam(name).pw_uid if isinstance(name, basestring) else name

def get_gid(name):
    return pwd.getpwnam(name).pw_gid if isinstance(name, basestring) else name

def ensure_file(path, owner=None, group=None, mode=0644, content=''):
    try:
        current_content = open(path).read()
    except IOError, e:
        if e.errno == errno.ENOENT:
            current_content = None
        else:
            raise

    if current_content != content:
        with open(path, 'w') as f:
            f.write(content)

    os.chmod(path, mode)
    if owner and group:
        os.chown(path, get_uid(owner), get_gid(group))

def ensure_file_absent(path):
    if os.path.lexists(path):
        os.unlink(path)

def ensure_dir(path, owner=None, group=None, mode=0755):
    try:
        os.mkdir(path, mode)
    except OSError, e:
        if e.errno != errno.EEXIST:
            raise

    if owner and group:
        os.chown(path, get_uid(owner), get_gid(group))
