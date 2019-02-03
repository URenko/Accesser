import tornado.web
import queue
import os
import sys

class MainHandler(tornado.web.RequestHandler):
    def get(self):
        self.render('index.html')

class LogHandler(tornado.web.RequestHandler):
    def initialize(self, logqueue):
        self.logqueue = logqueue
    def post(self):
        try:
            msg = self.logqueue.get_nowait()
        except queue.Empty:
            msg = ''
        self.write(msg)

class ShutdownHandler(tornado.web.RequestHandler):
    def get(self):
        if sys.platform.startswith('win'):
            os.system('sysproxy pac ""')
        os._exit(0)

class PACHandler(tornado.web.StaticFileHandler):
    def set_headers(self):
        self.set_header('Content-Type', 'application/x-ns-proxy-autoconfig')

def make_app(logqueue):
    return tornado.web.Application([
        (r"/", MainHandler),
        (r"/(pac)/", PACHandler, {'path': os.path.dirname(os.path.dirname(__file__))}),
        (r"/shutdown", ShutdownHandler),
        (r"/log", LogHandler, {'logqueue': logqueue})
    ], static_path=os.path.join(os.path.dirname(os.path.dirname(__file__)), 'static'),
    template_path=os.path.join(os.path.dirname(os.path.dirname(__file__)), 'template'))

def init(logqueue):
    app = make_app(logqueue)
    app.listen(7654, '127.0.0.1')