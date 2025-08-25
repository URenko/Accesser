from pathlib import Path
import shutil, os, shutil, filecmp

try:
    import tomllib
except ModuleNotFoundError:
    import tomli as tomllib
import argparse
import platform
import logging

basepath = Path(__file__).parent.parent
certpath = None


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

_rules = {}

if not Path("rules").exists() or not Path("rules").is_dir():
    Path("rules").mkdir()

for custom_rules in sorted(Path("rules").glob("*.toml"), key=lambda f: f.name):
    with custom_rules.open(mode="rb") as f:
        _rules = deep_merge(_rules, tomllib.load(f))

with Path("rules.toml").open(mode="rb") as f:
    _rules = deep_merge(_rules, tomllib.load(f))

if not Path("config.toml").exists():
    shutil.copyfile(basepath / "config.toml", "config.toml")

with open("config.toml", "rb") as f:
    _config = tomllib.load(f)

config = _rules.copy()
config = deep_merge(_config, _rules)


def decide_state_path_legacy():
    if config["importca"]:
        return Path(basepath)
    return Path()


def decide_state_path_unix_like():
    if os.geteuid() == 0:
        logging.warning(
            "Running Accesser as the root user carries certain risks. Do not use it in production."
        )
        return Path("/var/lib") / "accesser"

    state_path = os.getenv("XDG_STATE_HOME", None)
    if state_path is not None:
        state_path = Path(state_path) / "accesser"
    else:
        state_path = Path.home() / ".local/state" / "accesser"
    return state_path


def decide_certpath():
    # 人为指定最优先
    if "state_dir" in config and config["state_dir"] is not None:
        return Path(config["state_dir"]) / "CERT"
    match platform.system():
        case "Linux" | "FreeBSD":
            deprecated_path = decide_state_path_legacy() / "CERT"
            # 暂仅在 *nix 上视为已废弃
            if deprecated_path.exists():
                logging.warning("deprecated path, see pull #245")
                return deprecated_path
            return decide_state_path_unix_like() / "CERT"
        case _:
            # windows,mac,android ...
            return decide_state_path_legacy() / "CERT"
    return


def parse_args():
    global certpath
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
    parser.add_argument(
        "--state-dir",
        type=str,
        help="where state file store , override notimportca",
        default=None,
    )
    args = parser.parse_args()
    if args.notsetproxy:
        config["setproxy"] = False
    if args.notimportca:
        config["importca"] = False
    if args.state_dir is not None:
        config["state_dir"] = args.state_dir
    certpath = decide_certpath()
    if not certpath.exists() or certpath.is_file():
        certpath.mkdir(parents=True)
    return
