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

__version__ = '0.10.0'

import os, sys
import json
import fnmatch
import random
import ssl
import asyncio
import traceback
from contextlib import closing
from urllib import request
from urllib.parse import urlsplit
from packaging.version import Version
from tld import get_tld, is_tld
import dns, dns.asyncresolver, dns.nameserver

from .utils import certmanager as cm
from .utils import importca
from .utils import setting
from .utils.setting import basepath
from .utils.log import logger
from .utils.cert_verify import match_hostname
from .utils import sysproxy


async def update_cert(server_name):
    global context, cert_store, cert_lock
    if not is_tld(server_name):
        res = get_tld(server_name, as_object=True, fix_protocol=True)
        if res.subdomain:
            server_name = res.subdomain.split('.', 1)[-1] + '.' + res.domain + '.' + res.tld
        else:
            server_name = res.domain + '.' + res.tld
    async with cert_lock:
        if not server_name in cert_store:
            cm.create_certificate(server_name)
        context.load_cert_chain(os.path.join(cm.certpath, "{}.crt".format(server_name)))
        cert_store.add(server_name)

async def send_pac(writer: asyncio.StreamWriter):
    with open('pac' if os.path.exists('pac') else os.path.join(basepath, 'pac'), 'rb') as f:
        pac = f.read().replace(b'{{port}}', str(setting.config['server']['port']).encode('iso-8859-1')).replace(b'{{host}}', setting.config['server'].get('pac_host', '127.0.0.1').encode('iso-8859-1'))
    writer.write(f'HTTP/1.1 200 OK\r\nContent-Type: application/x-ns-proxy-autoconfig\r\nContent-Length: {len(pac)}\r\n\r\n'.encode('iso-8859-1'))
    writer.write(pac)
    await writer.drain()
    writer.close()
    await writer.wait_closed()

async def send_crt(writer: asyncio.StreamWriter, path: str):
    with open(os.path.join(basepath, path.lstrip('/')), 'rb') as f:
        crt = f.read()
    writer.write(f'HTTP/1.1 200 OK\r\nContent-Type: application/x-x509-ca-cert\r\nContent-Length: {len(crt)}\r\n\r\n'.encode('iso-8859-1'))
    writer.write(crt)
    await writer.drain()
    writer.close()
    await writer.wait_closed()
    
async def http_redirect(writer: asyncio.StreamWriter, path: str):
    path = path.removeprefix('http://')
    for key in setting.config['http_redirect']:
        if path.startswith(key):
            path = setting.config['http_redirect'][key] + path[len(key):]
            break
    logger.debug('Redirect to '+path)
    writer.write(f'HTTP/1.1 301 Moved Permanently\r\nLocation: https://{path}\r\n\r\n'.encode('iso-8859-1'))
    await writer.drain()
    writer.close()
    await writer.wait_closed()

async def forward_stream(reader: asyncio.StreamReader, writer: asyncio.StreamWriter):
    while True:
        data = await reader.read(32768)
        if data == b'':
            return
        writer.write(data)
        await writer.drain()

async def handle(reader, writer):
    global context
    with closing(writer):
        raw_request = await reader.readuntil(b'\r\n\r\n')
        requestline = raw_request.decode('iso-8859-1').splitlines()[0]
        i_addr, i_port, *_ = writer.get_extra_info('peername')
        logger.debug(f"{i_addr}:{i_port} say: {requestline}")
        words = requestline.split()
        command, path = words[:2]
        match command:
            case 'CONNECT':
                host, port = path.split(':')
                remote_ip = await DNSquery(host)
                logger.debug(f'[{i_port:5}] DNS: {host} -> {remote_ip}')
            case 'GET':
                if path.startswith('/pac/'):
                    return await send_pac(writer)
                elif path.startswith('/CERT/root.'):
                    return await send_crt(writer, path)
                elif path == '/shutdown':
                    sys.exit()
                else:
                    return await http_redirect(writer, path)
            case _:
                return await http_redirect(writer, path)
        writer.write(b'HTTP/1.1 200 Connection Established\r\n\r\n')

        await update_cert(host)
        if sys.version_info[1] >= 11:
            await writer.start_tls(context)
        else:
            writer._transport = await writer._loop.start_tls(writer.transport, writer._protocol, context, server_side=True)
        server_hostname_key = next(filter(lambda h:fnmatch.fnmatchcase(host, h), setting.config['alter_hostname']), None)
        server_hostname = '' if server_hostname_key is None else setting.config['alter_hostname'][server_hostname_key]
        logger.debug(f'[{i_port:5}] {server_hostname=}')
        remote_context = ssl.create_default_context()
        remote_context.check_hostname = False
        remote_reader, remote_writer = await asyncio.open_connection(remote_ip, port, ssl=remote_context, server_hostname=server_hostname)
        cert = remote_writer.get_extra_info('peercert')
        cert_message = f"subjectAltName: {cert.get('subjectAltName', ())}, subject: {cert.get('subject', ())}"
        logger.debug(f"[{i_port:5}] {cert_message}.")
        cert_verify_key = next(filter(lambda h:fnmatch.fnmatchcase(host, h), setting.config.get('cert_verify', ())), None)
        if cert_verify_key is not None:
            cert_verify_list = setting.config['cert_verify'][cert_verify_key]
            cert_policy = False if cert_verify_list is False else True
        elif server_hostname_key is not None:
            cert_verify_list = [setting.config['alter_hostname'][server_hostname_key]]
            cert_policy = setting.config['check_hostname']
        else:
            cert_verify_list = [host]
            cert_policy = setting.config['check_hostname']
        if  cert_policy is not False and not any(match_hostname(cert, h, cert_policy) for h in cert_verify_list):
            logger.warning(f"[{i_port:5}] {cert_verify_list} don't match either of {cert_message}.")
            return
        await asyncio.gather(
            forward_stream(reader, remote_writer),
            forward_stream(remote_reader, writer)
        )
    writer.close()
    remote_writer.close()
    await remote_writer.wait_closed()
    await writer.wait_closed()

async def proxy():
    server = await asyncio.start_server(handle, setting.config['server']['address'], setting.config['server']['port'])

    print(f"Serving on {', '.join(str(sock.getsockname()) for sock in server.sockets)}")
    sysproxy.set_pac('http://localhost:'+str(setting.config['server']['port'])+'/pac/?t='+str(random.randrange(2**16)))

    try:
        async with server:
            await server.serve_forever()
    finally:
        sysproxy.set_pac(None)

async def DNSquery(domain, hosts_only=False):
    global DNSresolver
    try:
        return next(v for k,v in setting.config['hosts'].items() if k==domain or (k.startswith('.') and domain.endswith(k)))
    except StopIteration:
        if hosts_only:
            return
    if setting.config['ipv6']:
        try:
            ret = await DNSresolver.resolve(domain, 'AAAA')
        except dns.asyncresolver.NoAnswer:
            ret = await DNSresolver.resolve(domain, 'A')
    else:
        ret = await DNSresolver.resolve(domain, 'A')
    return ret[0].to_text()

def update_checker():
    for pypi_url in ['https://pypi.org/pypi/accesser/json', 'https://mirrors.cloud.tencent.com/pypi/json/accesser']:
        try:
            with request.urlopen(pypi_url) as f:
                v2 = Version(json.load(f)["info"]["version"])
                break
        except Exception:
            logger.warning(traceback.format_exc())
    else:
        with request.urlopen('https://github.com/URenko/Accesser/releases/latest') as f:
            v2 = Version(f.geturl().rsplit('/', maxsplit=1)[-1])
    v1 = Version(__version__)
    if v2 > v1:
        logger.warning("There is a new version, you can update with 'python3 -m pip install -U accesser' or download from GitHub")

async def main():
    global context, cert_store, cert_lock, DNSresolver
    print(f"Accesser v{__version__}  Copyright (C) 2018-2024  URenko")
    setting.parse_args()

    if setting.rules_update_case in ('old', 'missing'):
        logger.warning("Updated rules.toml because it is %s.", setting.rules_update_case)
    elif setting.rules_update_case == 'modified':
        logger.warning("You've already modified rules.toml, so it won't be updated automatically!")
    else:
        logger.debug("rules.toml status: %s", setting.rules_update_case)
    
    if any(_keys in setting._config for _keys in setting._rules):
        logger.warning("Some sections of config.toml overlap with rules.toml, config.toml has higher priority, but this may make rule updates ineffective.")
        
    DNSresolver = dns.asyncresolver.Resolver(configure=False)
    DNSresolver.cache = dns.resolver.LRUCache()
    for nameserver in setting.config['DNS']['nameserver']:
        if (_url := urlsplit(nameserver)).netloc == '':
            _url = urlsplit('//' + nameserver)
        address = await DNSquery(_url.hostname, hosts_only=True)
        if _url.scheme == '':
            DNSresolver.nameservers.append(dns.nameserver.Do53Nameserver(_url.hostname if address is None else address, 53 if _url.port is None else _url.port))
        elif _url.scheme == 'https':
            DNSresolver.nameservers.append(dns.nameserver.DoHNameserver(nameserver, bootstrap_address=address))
        elif _url.scheme == 'tls':
            DNSresolver.nameservers.append(dns.nameserver.DoTNameserver(_url.hostname if address is None else address, 853 if _url.port is None else _url.port, hostname=_url.hostname))
        elif _url.scheme == 'quic':
            DNSresolver.nameservers.append(dns.nameserver.DoQNameserver(_url.hostname if address is None else address, 853 if _url.port is None else _url.port, server_hostname=_url.hostname))
    
    importca.import_ca()

    context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
    cert_store = set()
    cert_lock = asyncio.Lock()
    
    await asyncio.gather(
        asyncio.to_thread(update_checker),
        proxy()
    )

def run():
    asyncio.run(main())
