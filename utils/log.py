import logging
import json

from tornado.queues import Queue

from . import setting

class JSONHandler(logging.handlers.QueueHandler):
    def prepare(self, record):
        return json.dumps({'level': record.levelname, 'content': self.format(record)})

logging.basicConfig(filename=setting.log['logfile'],
                    format='%(asctime)s %(levelname)-8s %(name)s: %(message)s',
                    datefmt='%Y-%m-%d %H:%M:%S')
logger = logging.getLogger('Accesser')
logger.setLevel(setting.log['loglevel'].upper())

logqueue = Queue()
logger.addHandler(JSONHandler(logqueue))
