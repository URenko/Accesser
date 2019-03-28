import tornado.web
from tornado import gen
import asyncio
import os
import sys

from . import setting

class MainHandler(tornado.web.RequestHandler):
    def get(self):
        self.render('index.html')

class LogHandler(tornado.web.RequestHandler):
    def initialize(self, logqueue):
        self.logqueue = logqueue
    @gen.coroutine
    def post(self):
        data = yield self.logqueue.get()
        self.write(data)
        self.finish()

class ShutdownHandler(tornado.web.RequestHandler):
    def get(self):
        if sys.platform.startswith('win'):
            os.system(os.path.join(setting.basepath, 'sysproxy.exe')+' pac ""')
        os._exit(0)

class ConfigHandler(tornado.web.RequestHandler):
    def get(self):
        os.startfile(os.path.join(setting.basepath, 'setting.ini'))
        self.write('')

class OpenpathHandler(tornado.web.RequestHandler):
    def get(self):
        os.startfile(setting.basepath)
        self.write('')

class PACHandler(tornado.web.StaticFileHandler):
    def set_headers(self):
        self.set_header('Content-Type', 'application/x-ns-proxy-autoconfig')

class CRTHandler(tornado.web.StaticFileHandler):
    def set_headers(self):
        self.set_header('Content-Type', 'application/x-x509-ca-cert')

def make_app(logqueue):
    return tornado.web.Application([
        (r"/", MainHandler),
        (r"/(pac)/", PACHandler, {'path': setting.basepath}),
        (r"/(CERT/root.crt)", CRTHandler, {'path': setting.basepath}),
        (r"/shutdown", ShutdownHandler),
        (r"/configfile", ConfigHandler),
        (r"/openpath", OpenpathHandler),
        (r"/log", LogHandler, {'logqueue': logqueue})
    ], static_path=os.path.join(setting.basepath, 'static'),
    template_path=os.path.join(setting.basepath, 'template'))

def init(logqueue):
    app = make_app(logqueue)
    app.listen(7654, '127.0.0.1')