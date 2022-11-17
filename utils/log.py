import logging, logging.handlers
import json

from . import setting

class JSONHandler(logging.handlers.QueueHandler):
    def prepare(self, record):
        return json.dumps({'level': record.levelname, 'content': self.format(record)})

if setting.config['log']['logfile']:
    handlers = [logging.handlers.RotatingFileHandler(setting.config['log']['logfile'],
                                                     maxBytes=2**20, backupCount=1)]
else:
    handlers = None
logging.basicConfig(format='%(asctime)s %(levelname)-8s %(name)s: %(message)s',
                    datefmt='%Y-%m-%d %H:%M:%S',
                    handlers=handlers)
logger = logging.getLogger('Accesser')
logger.setLevel(setting.config['log']['loglevel'].upper())

if setting.config['webui']:
    from tornado.queues import Queue
    logqueue = Queue()
    logger.addHandler(JSONHandler(logqueue))
