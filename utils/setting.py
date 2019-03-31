import sys
from os import path
import json

if hasattr(sys, '_MEIPASS'):
    basepath = sys._MEIPASS
else:
    basepath = '.'

with open(path.join(basepath, 'config.json.default'), 'r') as f:
    config = json.load(f)
if path.exists(path.join(basepath, 'config.json')):
    with open(path.join(basepath, 'config.json'), 'r') as f:
        config = {**config, **json.load(f)}

def set(new):
    '''set value and return whether need to restart server'''
    global config
    if 'server' in new:
        restart_server = (new['server'] != config['server'])
    else:
        restart_server = False
    config = {**config, **new}
    return restart_server

def save():
    with open(path.join(basepath, 'config.json'), 'w') as f:
        json.dump(config, f, indent=2)
