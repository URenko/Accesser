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

HOSTS_URL1 = 'https://raw.githubusercontent.com/googlehosts/hosts/master/hosts-files/hosts'
HOSTS_URL2 = 'https://coding.net/u/scaffrey/p/hosts/git/raw/master/hosts-files/hosts'
server_address = ('127.0.0.1', 443)

import argparse
import logging
import configparser
import os, re, sys
import socket, ssl
import select
from socketserver import *

sys.path.append(os.path.dirname(__file__))
from utils import certmanager as cm
from utils import importca

from http import HTTPStatus
import urllib.error

_MAXLINE = 65536
_MAXHEADERS = 100


class ProxyHandler(StreamRequestHandler):
    raw_request = b''
    remote_ip = None
    
    def send_error(self, code, message=None, explain=None):
        #TODO
        pass
    
    def parse_host(self):
        try:
            raw_requestline = self.rfile.readline(_MAXLINE + 1)
            self.raw_request += raw_requestline
            if len(raw_requestline) > _MAXLINE:
                logging.error(HTTPStatus.REQUEST_URI_TOO_LONG)
                self.send_error(HTTPStatus.REQUEST_URI_TOO_LONG)
            if not raw_requestline:
                return False
            logging.debug(raw_requestline.strip().decode('iso-8859-1'))
            headers = []
            while True:
                raw_requestline = self.rfile.readline(_MAXLINE + 1)
                self.raw_request += raw_requestline
                if len(raw_requestline) > _MAXLINE:
                    return False
                headers.append(raw_requestline)
                if len(headers) > _MAXHEADERS:
                    return False
                if raw_requestline in (b'\r\n', b'\n', b''):
                    break
                header, value = raw_requestline.strip().split(b': ', maxsplit=1)
                if header == b'Host':
                    self.host = value.decode('iso-8859-1')
                    self.remote_ip = rhosts[self.host]
                    logging.debug('remote: {} {}'.format(self.host, self.remote_ip))
            if self.remote_ip:
                return True
            else:
                return False
        except socket.timeout as e:
            logging.error("Request timed out: {}".format(e))
            return False

    def forward(self, sock, remote):
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
                    sock.sendall(data)
        except socket.error as e:
            logging.warning('Forward: %s' % e)
        finally:
            sock.close()
            remote.close()

    def handle(self):
        if not self.parse_host():
            return
        self.remote_sock = socket.create_connection((self.remote_ip, 443))
        context = ssl.create_default_context()
        context.check_hostname = False
        self.remote_sock = context.wrap_socket(self.remote_sock)
        cert = self.remote_sock.getpeercert()
        if check_hostname:
            hostname = self.host
            if self.remote_ip in config['alert_hostname']:
                hostname = config['alert_hostname'][self.remote_ip]
            ssl.match_hostname(cert, hostname)
        self.remote_sock.sendall(self.raw_request)
        self.forward(self.request, self.remote_sock)

if __name__ == '__main__':
    print("Accesser  Copyright (C) 2018  URenko")
    parser = argparse.ArgumentParser()
    parser.add_argument('-r', '--renewca', help='renew cert', action="store_true")
    parser.add_argument('-rr', '--root', help='create root cert', action="store_true")
    args = parser.parse_args()

    config = configparser.ConfigParser()
    config.read('setting.ini')

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
    domainsupdate = False
    if not cm.match_domain('CERT/server.crt'):
        if sys.platform.startswith('win'):
            domainsupdate = True
            from utils import win32elevate
            if not win32elevate.areAdminRightsElevated():
                win32elevate.elevateAdminRun(' '.join(sys.argv), reattachConsole=False)
                sys.exit(0)
            logging.info('Updating HOSTS...')
            with open(r"C:\Windows\System32\drivers\etc\hosts") as f:
                host_content = f.read()
            with open('domains.txt') as f:
                for domain in f:
                    if not re.search(r'(\d{1,3}.\d{1,3}.\d{1,3}.\d{1,3})(?P<oth>\s+'+domain.strip()+')', host_content):
                        host_content += '\n127.0.0.1\t'+domain.strip()
                    host_content = re.sub(r'(\d{1,3}.\d{1,3}.\d{1,3}.\d{1,3})(?P<oth>\s+'+domain.strip()+')',r'127.0.0.1\g<oth>',host_content)
            with open(r"C:\Windows\System32\drivers\etc\hosts", 'w') as f:
                f.write(host_content)
            with open('setting.ini', 'w') as f:
                config.write(f)
            logging.info('Updating fin')
        else:
            logging.warning('other platform support is under development, please update HOSTS manually and then use -r to update server cert.')
    
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
    except FileNotFoundError:
        logging.error('cert not exist, please use --rr to create it')
    if int(config['setting']['http_redirect']):
        from utils import httpredirect
        import threading
        th_httpredirect = threading.Thread(target=httpredirect.main)
        th_httpredirect.daemon = True
        th_httpredirect.start()
    try:
        server = ThreadingTCPServer(server_address, ProxyHandler)
        server.socket = context.wrap_socket(server.socket, server_side=True)
        logging.info("server started at {}:{}".format(*server_address))
        server.serve_forever()
    except socket.error as e:
        logging.error(e)
    except KeyboardInterrupt:
        server.shutdown()
        sys.exit(0)