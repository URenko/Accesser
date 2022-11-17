import tornado.web
from tornado import gen
import asyncio
import os
import sys
import threading
import json
import urllib.parse
import webbrowser

from . import setting
from .setting import basepath
from .log import logger, logqueue

class MainHandler(tornado.web.RequestHandler):
    def initialize(self, version):
        self.version = version
    def get(self):
        self.render('index.html', version=self.version)

class GetHandler(tornado.web.RequestHandler):
    @gen.coroutine
    def post(self):
        self.write(json.dumps(setting.config))

class SetHandler(tornado.web.RequestHandler):
    def initialize(self, proxy):
        self.proxy = proxy
    def restart_server(self):
        self.proxy.shutdown()
        self.proxy.server_close()
        threading.Thread(target=self.proxy.start, args=(setting.config['server']['address'],setting.config['server']['port'])).start()
    @gen.coroutine
    def post(self):
        try:
            require_restart = setting.set(json.loads(urllib.parse.unquote(self.request.body.decode('utf-8'))))
            setting.save()
        except json.JSONDecodeError as err:
            logger.error('JSON decode failed.')
            logger.debug(err.doc)
            self.write('-1')
            return
        if require_restart:
            self.restart_server()
            self.write('1')
            return
        self.write('0')

class LogHandler(tornado.web.RequestHandler):
    @gen.coroutine
    def post(self):
        data = yield logqueue.get()
        self.write(data)
        self.finish()

class ShutdownHandler(tornado.web.RequestHandler):
    def initialize(self, proxy):
        self.proxy = proxy
    def get(self):
        if setting.config['setproxy'] and sys.platform.startswith('win'):
            self.proxy.winrun(os.path.join(basepath, 'sysproxy.exe')+' pac ""')
        os._exit(0)

class OpenpathHandler(tornado.web.RequestHandler):
    def get(self):
        os.startfile(basepath)
        self.write('')

class PACHandler(tornado.web.RequestHandler):
    def set_default_headers(self):
        self.set_header('Content-Type', 'application/x-ns-proxy-autoconfig')
    def get(self):
        if os.path.exists('pac'):
            with open('pac') as f:
                self.write(f.read())
            return
        self.render('pac', port=setting.config['server']['port'])

class CRTHandler(tornado.web.StaticFileHandler):
    def set_headers(self):
        self.set_header('Content-Type', 'application/x-x509-ca-cert')

def make_app(proxy, version):
    return tornado.web.Application([
        (r"/", MainHandler, {'version': version}),
        (r"/set", SetHandler, {'proxy': proxy}),
        (r"/get", GetHandler),
        (r"/pac/", PACHandler),
        (r"/(CERT/root.crt)", CRTHandler, {'path': basepath}),
        (r"/shutdown", ShutdownHandler, {'proxy': proxy}),
        (r"/openpath", OpenpathHandler),
        (r"/log", LogHandler)
    ], static_path=os.path.join(basepath, 'static'),
    template_path=os.path.join(basepath, 'template'))

async def init(proxy, version):
    app = make_app(proxy, version)
    try:
        app.listen(int(setting.config['webuiport']), setting.config['server']['address'])
        webbrowser.open('http://localhost:{}/'.format(setting.config['webuiport']))
        await asyncio.Event().wait()
    except Exception as err:
        logger.error(err)