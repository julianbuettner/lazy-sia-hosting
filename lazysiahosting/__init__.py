from sys import exit
from time import sleep
from threading import Thread
from yaml import safe_load, scanner, parser
from .autounlock import AutoUnlock
from .autopayout import AutoPayout
from .autoprice import AutoPrice
from .autorestart import AutoRestart
from .autothrottle import AutoThrottle
from .siad import Siad


CONFIG_YAML = "config.yaml"


def _read_config() -> dict:
    yaml_errors = (
        scanner.ScannerError,
        parser.ParserError,
    )
    try:
        return safe_load(open(CONFIG_YAML).read())
    except FileNotFoundError:
        print("Could not find {}!".format(CONFIG_YAML))
        exit(1)
    except yaml_errors as e:
        print("Error parsing {}:".format(CONFIG_YAML))
        print(e)
        exit(1)


def _get_siad(config: dict) -> Siad:
    host = config.get("host", None)
    api_password = config.get("api-password", "")

    if not host:
        print("Missing config parameter 'host'")
        exit(1)

    if not api_password:
        print("Warning: no API password set")

    return Siad(host, api_password)


def get_module(config_section, auto_module, *args):
    """Get None, the module or exit(1)"""
    config_section = config_section or {}
    enabled = config_section.get("enabled", False)
    if not enabled:
        return
    try:
        return auto_module(config_section, *args)
    except ValueError as e:
        print(e)
        exit(1)


def _get_enabled_modules(config: dict, siad: Siad) -> list:
    modules_enabled = []

    # AutoUnlock
    auto_unlock = get_module(config.get("unlock"), AutoUnlock, siad)
    if auto_unlock:
        modules_enabled.append(auto_unlock)

    # AutoPrice
    auto_price = get_module(config.get("price"), AutoPrice, siad)
    if auto_price:
        modules_enabled.append(auto_price)

    # AutoRestart
    auto_restart = get_module(config.get("restart"), AutoRestart, siad)
    if auto_restart:
        modules_enabled.append(auto_restart)

    # AutoThrottle
    auto_throttle = get_module(config.get("throttle"), AutoThrottle)
    if auto_throttle:
        modules_enabled.append(auto_throttle)

    # AutoPayout
    auto_payout = get_module(config.get("payout"), AutoPayout, siad)
    if auto_payout:
        modules_enabled.append(auto_payout)

    for module in modules_enabled:
        module.print_settings()

    return modules_enabled


def main():
    config = _read_config()  # Might exit
    siad = _get_siad(config)  # Might exit

    modules_enabled = _get_enabled_modules(config, siad)  # Might exit

    print(
        "# ====\n"
        "# Modules initialized. Starting...\n"
        "# ===="
    )

    for module in modules_enabled:
        t = Thread(target=module.run)
        t.start()


    while True:
        try:
            sleep(3600)
        except KeyboardInterrupt:
            return



    