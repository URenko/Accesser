from pathlib import Path
import shutil, os, shutil, filecmp

try:
    import tomllib
except ModuleNotFoundError:
    import tomli as tomllib
import argparse

basepath = Path(__file__).parent.parent


def deep_merge(config_a: dict, config_b: dict):
    res = config_b | config_a
    for key in config_a:
        if key in config_b and type(config_a[key]) is type(config_b[key]):
            if isinstance(config_a[key], dict):
                res[key] = deep_merge(config_a[key], config_b[key])
            elif isinstance(config_a[key], list):
                for elem in config_b[key]:
                    if elem not in res[key]:
                        res[key].append(elem)
    return res


if Path("rules.toml").exists():
    if Path("rules.toml").stat().st_mtime_ns > 0:
        rules_update_case = "modified"
    else:
        if filecmp.cmp("rules.toml", basepath / "rules.toml"):
            rules_update_case = "holding"
        else:
            rules_update_case = "old"
else:
    rules_update_case = "missing"
if rules_update_case in ("old", "missing"):
    shutil.copyfile(basepath / "rules.toml", "rules.toml")
    os.utime("rules.toml", ns=(0, 0))

_config = {}

if not Path("rules").exists() or not Path("rules").is_dir():
    Path("rules").mkdir()

for custom_config in Path("rules").glob("*.toml"):
    with custom_config.open(mode="rb") as f:
        _config = deep_merge(_config, tomllib.load(f))

with Path("rules.toml").open(mode="rb") as f:
    _config = deep_merge(_config, tomllib.load(f))

if not Path("config.toml").exists():
    shutil.copyfile(basepath / "config.toml", "config.toml")

with open("config.toml", "rb") as f:
    config = tomllib.load(f)

config = deep_merge(config, _config)


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--notsetproxy",
        action="store_true",
        help="do not set system's pac proxy automatically",
    )
    parser.add_argument(
        "--notimportca",
        action="store_true",
        help="do not import certificate to system automatically",
    )
    args = parser.parse_args()
    if args.notsetproxy:
        config["setproxy"] = False
    if args.notimportca:
        config["importca"] = False
