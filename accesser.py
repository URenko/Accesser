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

__version__ = '0.6.0'

server_address = ('127.0.0.1', 7654)

import logging
import configparser
import os, re, sys
import zlib
import socket, ssl
import select
import asyncio
import threading
from socketserver import StreamRequestHandler,ThreadingTCPServer,_SocketWriter

sys.path.append(os.path.dirname(__file__))
from utils import certmanager as cm
from utils import importca
from utils import DoH

from http import HTTPStatus
import urllib.error

_MAXLINE = 65536
PAC_HEADER = 'HTTP/1.1 200 OK\r\nContent-Length: {}\r\nContent-Type: application/x-ns-proxy-autoconfig\r\n\r\n'
REDIRECT_HEADER = 'HTTP/1.1 301 Moved Permanently\r\nLocation: https://{}\r\n\r\n'

class ProxyHandler(StreamRequestHandler):
    raw_request = b''
    remote_ip = None
    host = None
    
    def update_cert(self, server_name):
        _server_name = server_name.split('.')
        if len(_server_name) > 2:
            server_name = '.'.join(_server_name[1:])
        if not server_name in cert_store:
            cm.create_certificate(server_name)
        context.load_cert_chain("CERT/{}.crt".format(server_name))
        cert_store.add(server_name)
    
    def send_error(self, code, message=None, explain=None):
        #TODO
        pass
    
    def send_pac(self):
        with open('pac.txt') as f:
            body = f.read()
        self.wfile.write(PAC_HEADER.format(len(body)).encode('iso-8859-1'))
        self.wfile.write(body.encode())
    
    def http_redirect(self, path):
        ishttp = False
        if path.startswith('http://'):
            path = path[7:]
            ishttp = True
        for key in config['http_redirect']:
            if path.startswith(key):
                path = config['http_redirect'][key] + path[len(key):]
                break
        else:
            if not ishttp:
                return False
        logger.info('Redirect to '+path)
        self.wfile.write(REDIRECT_HEADER.format(path).encode('iso-8859-1'))
        return True
    
    def parse_host(self, forward=False):
        content_lenght = None
        try:
            raw_requestline = self.rfile.readline(_MAXLINE + 1)
            if forward:
                self.raw_request += raw_requestline
            if len(raw_requestline) > _MAXLINE:
                logger.error(HTTPStatus.REQUEST_URI_TOO_LONG)
                self.send_error(HTTPStatus.REQUEST_URI_TOO_LONG)
            if not raw_requestline:
                return False
            requestline = raw_requestline.strip().decode('iso-8859-1')
            logger.info(requestline)
            words = requestline.split()
            if len(words) == 0:
                return False
            command, path = words[:2]
            if not forward:
                if 'CONNECT' == command:
                    host, port = path.split(':')
                    if '443' == port:
                        self.host = host
                        self.remote_ip = DoH.DNSLookup(host)
                if 'GET' == command:
                    if path.startswith('/pac/'):
                        self.send_pac()
                    else:
                        self.http_redirect(path)
            elif 'POST' == command:
                    content_lenght = 0
            while True:
                raw_requestline = self.rfile.readline(_MAXLINE + 1)
                if forward:
                    self.raw_request += raw_requestline
                    if 0 == content_lenght:
                        try:
                            key,value = raw_requestline.rstrip().split(b': ', maxsplit=1)
                            if b'Content-Length' == key:
                                content_lenght = int(value)
                        except ValueError:
                            pass
                if len(raw_requestline) > _MAXLINE:
                    return False
                if raw_requestline in (b'\r\n', b'\n', b''):
                    break
            if None != content_lenght:
                self.raw_request += self.rfile.read(content_lenght)
            if not forward:
                if self.remote_ip:
                    return True
                else:
                    return False
            else:
                return not self.http_redirect(self.host+path)
        except socket.timeout as e:
            logger.error("Request timed out: {}".format(e))
            return False

    def forward(self, sock, remote, fix):
        content_encoding = None
        left_length = 0
        try:
            fdset = [sock, remote]
            while True:
                r, w, e = select.select(fdset, [], [])
                if sock in r:
                    data = sock.recv(32768)
                    if len(data) <= 0:
                        break
                    remote.sendall(data)
                if remote in r:
                    data = remote.recv(32768)
                    if len(data) <= 0:
                        break
                    if fix:
                        if None == content_encoding:
                            headers,body = data.split(b'\r\n\r\n', maxsplit=1)
                            headers = headers.decode('iso-8859-1')
                            match = re.search(r'Content-Encoding: (\S+)\r\n', headers)
                            if match:
                                content_encoding = match.group(1)
                            else:
                                content_encoding = ''
                            match = re.search(r'Content-Length: (\d+)\r\n', headers)
                            if match:
                                content_length = int(match.group(1))
                            else:
                                content_length = 0
                            left_length = content_length - len(body)
                        else:
                            left_length -= len(body)
                            if left_length <= 0:
                                content_encoding = None
                        if 'gzip' == content_encoding:
                            body = zlib.decompress(body ,15+32)
                        for old in content_fix[self.host]:
                            body = body.replace(old.encode('utf8'), content_fix[self.host][old].encode('utf8'))
                        if None != content_encoding:
                            headers = re.sub(r'Content-Encoding: (\S+)\r\n', r'', headers)
                            headers = re.sub(r'Content-Length: (\d+)\r\n', r'Content-Length: '+str(len(body))+r'\r\n', headers)
                        data = headers.encode('iso-8859-1') + b'\r\n\r\n' + body
                    sock.sendall(data)
        except socket.error as e:
            logger.debug('Forward: %s' % e)
        finally:
            sock.close()
            remote.close()

    def handle(self):
        if not self.parse_host():
            return
        self.wfile.write(b'HTTP/1.1 200 Connection Established\r\n\r\n')
        self.update_cert(self.host)
        self.request = context.wrap_socket(self.request, server_side=True)
        self.setup()
        if not self.parse_host(forward=True):
            return
        self.remote_sock = socket.create_connection((self.remote_ip, 443))
        remote_context = ssl.create_default_context()
        remote_context.check_hostname = False
        self.remote_sock = remote_context.wrap_socket(self.remote_sock)
        cert = self.remote_sock.getpeercert()
        if check_hostname:
            try:
                ssl.match_hostname(cert, self.host)
            except ssl.CertificateError as err:
                certdns = tuple(map(lambda x:x[1], cert['subjectAltName']))
                certfp = tuple(map(lambda x:x.rsplit('.', maxsplit=2)[-2:], certdns))
                if not self.host.rsplit('.', maxsplit=2)[-2:] in certfp:
                    if self.host in config['alert_hostname']:
                        if not config['alert_hostname'][self.host] in certdns:
                            raise err
                    else:
                        raise err
        self.remote_sock.sendall(self.raw_request)
        self.forward(self.request, self.remote_sock, self.host in content_fix)

if __name__ == '__main__':
    print("Accesser v{}  Copyright (C) 2018-2019  URenko".format(__version__))

    config = configparser.ConfigParser(delimiters=('=',))
    config.read('setting.ini')
    content_fix = configparser.ConfigParser(delimiters=('=',))
    content_fix.optionxform = lambda option: option
    content_fix.read('content_fix.ini')

    logging.basicConfig(filename=config['setting']['logfile'],
                        format='%(asctime)s %(levelname)-8s L%(lineno)-3s %(message)s',
                        datefmt='%Y-%m-%d %H:%M:%S', filemode='a+')
    logger = logging.getLogger(__name__)
    logger.setLevel(config['setting']['loglevel'])
    
    for domain in config['HOSTS']:
        DoH.DNScache[domain] = config['HOSTS'][domain]
    
    check_hostname = int(config['setting']['check_hostname'])
    
    if not os.path.exists('CERT'):
        os.mkdir('CERT')
    
    importca.import_ca()

    context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
    cert_store = set()
    
    try:
        server = ThreadingTCPServer(server_address, ProxyHandler)
        threading.Thread(target=lambda loop:loop.run_forever(), args=(DoH.init(logger),)).start()
        logger.info("server started at {}:{}".format(*server_address))
        if sys.platform.startswith('win'):
            os.system('sysproxy.exe pac http://{}:{}/pac/?t=%random%'.format(*server_address))
        server.serve_forever()
    except socket.error as e:
        logger.error(e)
    except KeyboardInterrupt:
        server.shutdown()
        sys.exit(0)