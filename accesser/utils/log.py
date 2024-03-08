import logging, logging.handlers
try:
    from rich.logging import RichHandler
    has_rich = True
except ModuleNotFoundError:
    has_rich = False

from . import setting

is_console = not setting.config['log']['logfile']
logging.basicConfig(
    format="%(message)s" if has_rich and is_console else '%(asctime)s %(levelname)-8s %(name)s: %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S',
    handlers=[logging.handlers.RotatingFileHandler(setting.config['log']['logfile'], maxBytes=2**20, backupCount=1)] if not is_console else ([RichHandler()] if has_rich else None)
)
logger = logging.getLogger('Accesser')
logger.setLevel(setting.config['log']['loglevel'].upper())
