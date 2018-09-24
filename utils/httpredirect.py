#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Accesser
# Copyright (C) 2018  URenko

# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.

# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.

# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

server_address = ('127.0.0.1', 80)

import configparser
import socket
from http.server import *
from http import HTTPStatus

config = configparser.ConfigParser()

class RedirectHandler(BaseHTTPRequestHandler):
    def handle_one_request(self):
        """Handle a single HTTP request.
        """
        try:
            self.raw_requestline = self.rfile.readline(65537)
            if len(self.raw_requestline) > 65536:
                self.requestline = ''
                self.request_version = ''
                self.command = ''
                self.send_error(HTTPStatus.REQUEST_URI_TOO_LONG)
                return
            if not self.raw_requestline:
                self.close_connection = True
                return
            if not self.parse_request():
                return
            self.do_all()
            self.wfile.flush()
        except socket.timeout as e:
            self.log_error("Request timed out: %r", e)
            self.close_connection = True
            return

    def do_all(self):
        self.send_response(HTTPStatus.MOVED_PERMANENTLY)
        redirect_to = self.headers['Host']
        if redirect_to in config['http_redirect']:
            redirect_to = config['http_redirect'][redirect_to]
            print(redirect_to)
        self.send_header('Location', 'https://'+redirect_to+self.path)
        self.end_headers()

def main():
    config.read('setting.ini')
    httpd = ThreadingHTTPServer(server_address, RedirectHandler)
    httpd.serve_forever()
