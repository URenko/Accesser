import logging, logging.handlers
has_rich = True
try:
    from rich.logging import RichHandler
except ModuleNotFoundError:
    try:
        from pip._vendor.rich.logging import RichHandler
    except ModuleNotFoundError:
        has_rich = False

from . import setting

if setting.config['log']['logfile']:
    handlers = [logging.handlers.RotatingFileHandler(setting.config['log']['logfile'],
                                                     maxBytes=2**20, backupCount=1)]
else:
    handlers = [RichHandler()] if has_rich else None
logging.basicConfig(format="%(message)s" if has_rich else '%(asctime)s %(levelname)-8s %(name)s: %(message)s',
                    datefmt='%Y-%m-%d %H:%M:%S',
                    handlers=handlers)
logger = logging.getLogger('Accesser')
logger.setLevel(setting.config['log']['loglevel'].upper())
