import tornado.web
from tornado import gen
import asyncio
import os
import sys
import threading

from . import setting

class MainHandler(tornado.web.RequestHandler):
    def get(self):
        self.render('index.html')

class GetHandler(tornado.web.RequestHandler):
    @gen.coroutine
    def post(self):
        self.write(setting.tojson())

class SetHandler(tornado.web.RequestHandler):
    def initialize(self, proxy):
        self.proxy = proxy
    def restart_server(self):
        self.proxy.shutdown()
        self.proxy.server_close()
        threading.Thread(target=self.proxy.start, args=(setting.server['address'],setting.server['port'])).start()
    @gen.coroutine
    def post(self):
        require_restart = False
        for i in ('server.address', 'server.port'):
            try:
                require_restart = require_restart or setting.set(i.split('.'), self.get_argument(i))
            except tornado.web.MissingArgumentError:
                pass
        setting.save()
        if require_restart:
            self.restart_server()
            self.write('1')
            return
        self.write('0')

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

class OpenpathHandler(tornado.web.RequestHandler):
    def get(self):
        os.startfile(setting.basepath)
        self.write('')

class PACHandler(tornado.web.RequestHandler):
    def set_default_headers(self):
        self.set_header('Content-Type', 'application/x-ns-proxy-autoconfig')
    def get(self):
        self.render('pac', port=setting.server['port'])

class CRTHandler(tornado.web.StaticFileHandler):
    def set_headers(self):
        self.set_header('Content-Type', 'application/x-x509-ca-cert')

def make_app(proxy, logqueue):
    return tornado.web.Application([
        (r"/", MainHandler),
        (r"/set", SetHandler, {'proxy': proxy}),
        (r"/get", GetHandler),
        (r"/pac/", PACHandler),
        (r"/(CERT/root.crt)", CRTHandler, {'path': setting.basepath}),
        (r"/shutdown", ShutdownHandler),
        (r"/openpath", OpenpathHandler),
        (r"/log", LogHandler, {'logqueue': logqueue})
    ], static_path=os.path.join(setting.basepath, 'static'),
    template_path=os.path.join(setting.basepath, 'template'))

def init(proxy, logqueue):
    app = make_app(proxy, logqueue)
    app.listen(7654, '127.0.0.1')