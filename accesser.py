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

__version__ = '0.5.0'

HOSTS_URL1 = 'https://raw.githubusercontent.com/googlehosts/hosts/master/hosts-files/hosts'
HOSTS_URL2 = 'https://coding.net/u/scaffrey/p/hosts/git/raw/master/hosts-files/hosts'
server_address = ('127.0.0.1', 7654)

import argparse
import logging
import configparser
import os, re, sys
import zlib
import socket, ssl
import select
from socketserver import StreamRequestHandler,ThreadingTCPServer,_SocketWriter

sys.path.append(os.path.dirname(__file__))
from utils import certmanager as cm
from utils import importca

from http import HTTPStatus
import urllib.error

_MAXLINE = 65536
PAC_HEADER = 'HTTP/1.1 200 OK\r\nContent-Length: {}\r\nContent-Type: application/x-ns-proxy-autoconfig\r\n\r\n'
REDIRECT_HEADER = 'HTTP/1.1 301 Moved Permanently\r\nLocation: https://{}\r\n\r\n'

class ProxyHandler(StreamRequestHandler):
    raw_request = b''
    remote_ip = None
    host = None
    
    def send_error(self, code, message=None, explain=None):
        #TODO
        pass
    
    def send_pac(self):
        with open('pac.txt') as f:
            body = f.read()
        self.wfile.write(PAC_HEADER.format(len(body)).encode('iso-8859-1'))
        self.wfile.write(body.encode())
    
    def http_redirect(self, path):
        if path.startswith('http://'):
            path = path[7:]
        for key in config['http_redirect']:
            if path.startswith(key):
                path = config['http_redirect'][key] + path[len(key):]
                break
        else:
            return False
        logging.info('Redirect to '+path)
        self.wfile.write(REDIRECT_HEADER.format(path).encode('iso-8859-1'))
        return True
    
    def parse_host(self, forward=False):
        content_lenght = None
        try:
            raw_requestline = self.rfile.readline(_MAXLINE + 1)
            if forward:
                self.raw_request += raw_requestline
            if len(raw_requestline) > _MAXLINE:
                logging.error(HTTPStatus.REQUEST_URI_TOO_LONG)
                self.send_error(HTTPStatus.REQUEST_URI_TOO_LONG)
            if not raw_requestline:
                return False
            requestline = raw_requestline.strip().decode('iso-8859-1')
            logging.info(requestline)
            words = requestline.split()
            if len(words) == 0:
                return False
            command, path = words[:2]
            if not forward:
                if 'CONNECT' == command:
                    host, port = path.split(':')
                    if '443' == port:
                        self.host = host
                        self.remote_ip = rhosts[self.host]
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
            logging.error("Request timed out: {}".format(e))
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
            logging.debug('Forward: %s' % e)
        finally:
            sock.close()
            remote.close()

    def handle(self):
        if not self.parse_host():
            return
        self.wfile.write(b'HTTP/1.1 200 Connection Established\r\n\r\n')
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
            hostname = self.host
            if self.remote_ip in config['alert_hostname']:
                hostname = config['alert_hostname'][self.remote_ip]
            ssl.match_hostname(cert, hostname)
        self.remote_sock.sendall(self.raw_request)
        self.forward(self.request, self.remote_sock, self.host in content_fix)

if __name__ == '__main__':
    print("Accesser v{}  Copyright (C) 2018  URenko".format(__version__))
    parser = argparse.ArgumentParser()
    parser.add_argument('-r', '--renewca', help='renew cert', action="store_true")
    parser.add_argument('-rr', '--root', help='create root cert', action="store_true")
    args = parser.parse_args()

    config = configparser.ConfigParser(delimiters=('=',))
    config.read('setting.ini')
    content_fix = configparser.ConfigParser(delimiters=('=',))
    content_fix.optionxform = lambda option: option
    content_fix.read('content_fix.ini')

    loglevel = getattr(logging, config['setting']['loglevel'])
    logfile = config['setting']['logfile']
    logging.basicConfig(level=loglevel, filename=logfile,
                        format='%(asctime)s %(levelname)-8s L%(lineno)-3s %(message)s',
                        datefmt='%Y-%m-%d %H:%M:%S', filemode='a+')
    
    if not os.path.exists('hosts'):
        import urllib.request
        logging.info('hosts file not exit, downloading...')
        try:
            local_filename, headers = urllib.request.urlretrieve(HOSTS_URL1, 'hosts')
        except urllib.error.URLError as e:
            logging.warning(e)
            logging.warning('try another hosts url')
            local_filename, headers = urllib.request.urlretrieve(HOSTS_URL2, 'hosts')
        logging.info('saved to: '+local_filename)
    hosts = re.findall(r'(\d{1,3}.\d{1,3}.\d{1,3}.\d{1,3})\s+(\S+)', open('hosts').read())
    rhosts = {k:v for v,k in hosts}
    for domain in config['HOSTS']:
        rhosts[domain] = config['HOSTS'][domain]
    
    check_hostname = int(config['setting']['check_hostname'])
    domainsupdate = not cm.match_domain('CERT/server.crt')
    
    if not os.path.exists('CERT'):
        os.mkdir('CERT')
    
    if args.root:
        logging.info("Making root CA")
        cm.create_root_ca()
        importca.import_ca("CERT/root.crt")
    if args.renewca or args.root or domainsupdate:
        logging.info("Making server certificate")
        cm.create_certificate("CERT/server.crt", "CERT/server.key")

    context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
    try:
        context.load_cert_chain("CERT/server.crt", "CERT/server.key")
        cert_domains = cm.get_cert_domain("CERT/server.crt")
    except FileNotFoundError:
        logging.error('cert not exist, please use --rr to create it')
    
    try:
        server = ThreadingTCPServer(server_address, ProxyHandler)
        logging.info("server started at {}:{}".format(*server_address))
        server.serve_forever()
    except socket.error as e:
        logging.error(e)
    except KeyboardInterrupt:
        server.shutdown()
        sys.exit(0)