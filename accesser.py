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

__version__ = '0.6.2'

import os, re, sys
import random
import zlib
import socket, ssl
import select
import asyncio
import threading
import subprocess
import webbrowser
from socketserver import StreamRequestHandler,ThreadingTCPServer,_SocketWriter
from urllib import request
from tornado.httpclient import AsyncHTTPClient
from tld import get_tld
from dns.resolver import Resolver, NoAnswer

from utils import certmanager as cm
from utils import importca
from utils import webui
from utils import setting
from utils.setting import basepath
from utils.log import logger

from http import HTTPStatus
import urllib.error

_MAXLINE = 65536

REDIRECT_HEADER = 'HTTP/1.1 301 Moved Permanently\r\nLocation: https://{}\r\n\r\n'

class ProxyHandler(StreamRequestHandler):
    raw_request = b''
    remote_ip = None
    host = None
    
    def update_cert(self, server_name):
        res = get_tld(server_name, as_object=True, fix_protocol=True)
        if res.subdomain:
            server_name = res.subdomain.split('.', 1)[-1] + '.' + res.domain + '.' + res.tld
        else:
            server_name = res.domain + '.' + res.tld
        with cert_lock:
            if not server_name in cert_store:
                cm.create_certificate(server_name)
            context.load_cert_chain(os.path.join(cm.certpath, "{}.crt".format(server_name)))
            cert_store.add(server_name)
    
    def send_error(self, code, message=None, explain=None):
        #TODO
        pass
    
    def http_redirect(self, path):
        ishttp = False
        if path.startswith('http://'):
            path = path[7:]
            ishttp = True
        for key in setting.config['http_redirect']:
            if path.startswith(key):
                path = setting.config['http_redirect'][key] + path[len(key):]
                break
        else:
            if not ishttp:
                return False
        logger.debug('Redirect to '+path)
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
            logger.debug(requestline)
            words = requestline.split()
            if len(words) == 0:
                return False
            command, path = words[:2]
            if not forward:
                if 'CONNECT' == command:
                    host, port = path.split(':')
                    if '443' == port:
                        self.host = host
                        self.remote_ip = DNSquery(host)
                if 'GET' == command:
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
                        for old in setting.config['content_fix'][self.host]:
                            body = body.replace(old.encode('utf8'), setting.config['content_fix'][self.host][old].encode('utf8'))
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
        if self.host in setting.config['alert_hostname']:
            server_hostname = setting.config['alert_hostname'][self.host]
        else:
            server_hostname = None
        try:
            self.remote_sock = socket.create_connection((self.remote_ip, 443))
        except TimeoutError:
            logger.warning('Try connect '+self.host+' with '+self.remote_ip+' timeout.')
            return
        remote_context = ssl.create_default_context()
        remote_context.check_hostname = False
        self.remote_sock = remote_context.wrap_socket(self.remote_sock, server_hostname=server_hostname)
        cert = self.remote_sock.getpeercert()
        if setting.config['check_hostname']:
            try:
                ssl.match_hostname(cert, self.host)
            except ssl.CertificateError as err:
                certdns = tuple(map(lambda x:x[1], cert['subjectAltName']))
                certfp = tuple(map(lambda x:x.rsplit('.', maxsplit=2)[-2:], certdns))
                if not self.host.rsplit('.', maxsplit=2)[-2:] in certfp:
                    if self.host in setting.config['alert_hostname']:
                        if not setting.config['alert_hostname'][self.host] in certdns:
                            logger.warning(err)
                    else:
                        logger.warning(err)
        self.remote_sock.sendall(self.raw_request)
        self.forward(self.request, self.remote_sock, self.host in setting.config['content_fix'])

class Proxy():
    def __init__(self):
        if hasattr(subprocess, 'STARTUPINFO'):
            self.si = subprocess.STARTUPINFO()
            self.si.dwFlags |= subprocess.STARTF_USESHOWWINDOW
        else:
            self.si = None
    def winrun(self, cmd):
        subprocess.check_output(cmd, stdin=subprocess.PIPE, stderr=subprocess.PIPE \
           , startupinfo=self.si, env=os.environ)
    def start(self, address, port):
        try:
            self.server = ThreadingTCPServer((address, int(port)), ProxyHandler)
            logger.info("server started at {}:{}".format(address, port))
            if setting.config['setproxy'] and sys.platform.startswith('win'):
                self.winrun(os.path.join(basepath, 'sysproxy.exe')+' pac http://localhost:'+str(setting.config['webuiport'])+'/pac/?t='+str(random.randrange(2**16)))
            self.server.serve_forever()
        except socket.error as e:
            logger.error(e)
    def shutdown(self):
        self.server.shutdown()
    def server_close(self):
        self.server.server_close()

def DNSquery(domain):
    if setting.config['ipv6']:
        try:
            return DNSresolver.query(domain, 'AAAA')[0].to_text()
        except NoAnswer:
            return DNSresolver.query(domain, 'A')[0].to_text()
    else:
        return DNSresolver.query(domain, 'A')[0].to_text()

def update_checker():
    with request.urlopen('https://github.com/URenko/Accesser/releases/latest') as f:
        v2 = f.geturl().rsplit('/', maxsplit=1)[-1][1:].split('.')
        v1 = __version__.split('.')
        if [int(v2[i]) for i in range(len(v2))] > [int(v1[i]) for i in range(len(v1))]:
            logger.warning('There is a new version, check {} for update.'.format(f.geturl()))

if __name__ == '__main__':
    print("Accesser v{}  Copyright (C) 2018-2019  URenko".format(__version__))
    
    threading.Thread(target=update_checker).start()
    
    proxy = Proxy()
    webui.init(proxy, version=__version__)
    if setting.config['webui']:
        webbrowser.open('http://localhost:{}/'.format(setting.config['webuiport']))
    
    DNSresolver = Resolver(configure=False)
    if not setting.config['DNS']['dnscrypt-proxy']:
        DNSresolver.nameservers = [setting.config['DNS']['nameserver']]
        DNSresolver.port = int(setting.config['DNS']['port'])
    else:
        # Launch dnscrypt-proxy in the `./dnscrypt`.
        # And use `127.0.0.1:53000` in default.
        DNSresolver.nameservers = ['127.0.0.1']
        DNSresolver.port = 53000
        dnscrypt_dir = os.path.join(basepath, 'dnscrypt')
        if hasattr(subprocess, 'STARTUPINFO'):
            si = subprocess.STARTUPINFO()
            si.dwFlags |= subprocess.STARTF_USESHOWWINDOW
        else:
            si = None
        subprocess.Popen([os.path.join(dnscrypt_dir, 'dnscrypt-proxy'),'-child','-logfile','dnscrypt-proxy.log'], stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE \
               , startupinfo=si, env=os.environ)
    
    importca.import_ca()

    context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
    cert_store = set()
    cert_lock = threading.Lock()
    
    threading.Thread(target=proxy.start, args=(setting.config['server']['address'],setting.config['server']['port'])).start()
    asyncio.get_event_loop().run_forever()
