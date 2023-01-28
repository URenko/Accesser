from pathlib import Path
import shutil
import tomllib
import argparse

basepath = Path(__file__).parent.parent

if not Path('config.toml').exists():
    shutil.copyfile(basepath / 'config.toml', 'config.toml')
with open('config.toml', 'rb') as f:
    config = tomllib.load(f)

def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument('--notsetproxy', action='store_true', help='do not set system\'s pac proxy automatically')
    parser.add_argument('--notimportca', action='store_true', help='do not import certificate to system automatically')
    args = parser.parse_args()
    if args.notsetproxy:
        config['setproxy'] = False
    if args.notimportca:
        config['importca'] = False
