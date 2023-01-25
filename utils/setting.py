import sys
from os import path
import shutil
import tomllib
import argparse

if hasattr(sys, '_MEIPASS'):
    basepath = sys._MEIPASS
else:
    basepath = '.'

if not path.exists('config.toml'):
    shutil.copyfile(path.join(basepath, 'config.toml'), 'config.toml')
with open('config.toml', 'rb') as f:
    config = tomllib.load(f)

parser = argparse.ArgumentParser()
parser.add_argument('--cli', action='store_true', help='do not open webui automatically')
parser.add_argument('--notsetproxy', action='store_true', help='do not set system\'s pac proxy automatically')
parser.add_argument('--notimportca', action='store_true', help='do not import certificate to system automatically')
args = parser.parse_args()
if args.cli:
    config['webui'] = False
if args.notsetproxy:
    config['setproxy'] = False
if args.notimportca:
    config['importca'] = False

def set(new):
    '''set value and return whether need to restart server'''
    global config
    if 'server' in new:
        restart_server = (new['server'] != config['server'])
    else:
        restart_server = False
    config = {**config, **new}
    return restart_server
