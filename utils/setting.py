import sys
from os import path
import shutil
import json
from functools import reduce

if hasattr(sys, '_MEIPASS'):
    basepath = sys._MEIPASS
else:
    basepath = '.'

if not path.exists('config.json'):
    shutil.copyfile(path.join(basepath, 'config.json.default'), 'config.json')
with open('config.json', 'r') as f:
    for key,values in json.load(f).items():
        globals()[key] = values

keys = ["log",
        "server",
        "check_hostname",
        "DNS",
        "http_redirect",
        "alert_hostname",
        "hosts",
        "hosts_ipv6",
        "content_fix"]

def set(keys, value):
    '''set value and return whether need to restart server'''
    d = reduce(lambda d,k:d[k], keys[:-1], globals())
    if value != d[keys[-1]]:
        d[keys[-1]] = value
        if 'server' == keys[0]:
            return True
        else:
            return False

def save():
    with open('config.json', 'r') as f:
        config = dict()
        for key in keys:
            config[key] = globals()[key]
    with open('config.json', 'w') as f:
        json.dump(config, f, indent=2)

def tojson():
    return json.dumps({k:globals()[k] for k in keys})
