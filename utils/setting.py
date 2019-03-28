import sys
from os import path
import shutil
import json

if hasattr(sys, '_MEIPASS'):
    basepath = sys._MEIPASS
else:
    basepath = '.'

if not path.exists('config.json'):
    shutil.copyfile(path.join(basepath, 'config.json.default'), 'config.json')
with open('config.json', 'r') as f:
    for key,values in json.load(f).items():
        globals()[key] = values

def save():
    with open('config.json', 'r') as f:
        config = dict()
        for key in json.load(f):
            config[key] = globals()[key]
    with open('config.json', 'w') as f:
        json.dump(config, f, indent=2)