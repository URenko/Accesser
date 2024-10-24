from pathlib import Path
import shutil, os, filecmp
try:
    import tomllib
except ModuleNotFoundError:
    import tomli as tomllib
import argparse

basepath = Path(__file__).parent.parent

if Path('rules.toml').exists():
    if Path('rules.toml').stat().st_mtime_ns > 0:
        rules_update_case = 'modified'
    else:
        if filecmp.cmp('rules.toml', basepath / 'rules.toml'):
            rules_update_case = 'holding'
        else:
            rules_update_case = 'old'
else:
    rules_update_case = 'missing'
if rules_update_case in ('old', 'missing'):
    shutil.copyfile(basepath / 'rules.toml', 'rules.toml')
    os.utime('rules.toml', ns=(0, 0))
with open('rules.toml', 'rb') as f:
    _rules = tomllib.load(f)
    config = _rules.copy()

if not Path('config.toml').exists():
    shutil.copyfile(basepath / 'config.toml', 'config.toml')
with open('config.toml', 'rb') as f:
    _config = tomllib.load(f)

config |= _config

def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument('--notsetproxy', action='store_true', help='do not set system\'s pac proxy automatically')
    parser.add_argument('--notimportca', action='store_true', help='do not import certificate to system automatically')
    args = parser.parse_args()
    if args.notsetproxy:
        config['setproxy'] = False
    if args.notimportca:
        config['importca'] = False
