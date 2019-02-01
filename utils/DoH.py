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

import logging
import asyncio
import dns
import priority
from dohproxy import client_protocol, constants

DoH_domains = (
'mozilla.cloudflare-dns.com',
'cloudflare-dns.com',
'dns.quad9.net',
'dns9.quad9.net',
'dns10.quad9.net',
'dns.rubyfish.cn')
DoH_domain = None

class Client(client_protocol.StubServerProtocol):
    async def make_request(self, dnsq):
        async with self._lock:
            if self.client is None or self.client._conn is None:
                await self.setup_client()
            client = self.client

        headers = {'Accept': constants.DOH_MEDIA_TYPE}
        path = self.args.uri
        qid = dnsq.id
        dnsq.id = 0
        body = b''

        headers = [
            (':authority', self.args.domain),
            (':method', self.args.post and 'POST' or 'GET'),
            (':scheme', 'https'),
        ]
        if self.args.post:
            headers.append(('content-type', constants.DOH_MEDIA_TYPE))
            body = dnsq.to_wire()
        else:
            path = self._make_get_path(dnsq.to_wire())

        headers.insert(0, (':path', path))
        headers.extend([
            ('content-length', str(len(body))),
        ])
        try:
            stream_id = await self.on_start_request(client, headers, not body)
        except priority.priority.TooManyStreamsError:
            await self.setup_client()
            client = self.client
            stream_id = await self.on_start_request(client, headers, not body)
        if body:
            await self.on_send_data(client, stream_id, body)

        headers = await client.recv_response(stream_id)
        self.on_recv_response(stream_id, headers)

        resp = await client.read_stream(stream_id, -1)
        return self.on_message_received(stream_id, resp)

def build_query(args):
    dnsq = dns.message.make_query(
        qname=args.qname,
        rdtype=args.qtype,
        want_dnssec=args.dnssec,
    )
    dnsq.id = 0
    return dnsq

class Argument(object):
    qtype = 'A'
    dnssec = True
    insecure = False
    cafile = None
    remote_address = None
    port = 443
    uri = constants.DOH_URI
    post = True

DNScache = dict()
logger = logging.getLogger('DoH')
logger.setLevel(logging.INFO)
args = Argument()

async def test_DoH(args, domain):
    global DoH_domain
    try:
        await Client(args=args, logger=logger).make_request(build_query(args))
    except Exception:
        return
    if None == DoH_domain:
        DoH_domain = domain
        raise asyncio.CancelledError

async def test_DoHs():
    aws = []
    for domain in DoH_domains:
        args = Argument()
        args.qname = 'zh.wikipedia.org'
        args.domain = domain
        aws.append(test_DoH(args, domain))
    await asyncio.wait(aws, return_when=asyncio.FIRST_EXCEPTION)

def init(main_logger):
    global DoHclient,loop
    loop = asyncio.get_event_loop()
    main_logger.info('Selecting DoH server...')
    loop.run_until_complete(test_DoHs())
    main_logger.info('Auto selected DoH server: '+DoH_domain)
    args.domain = DoH_domain
    DoHclient = Client(args=args, logger=logger)
    return loop

def DNSLookup(name):
    if name in DNScache:
        return DNScache[name]
    args.qname = name
    future = asyncio.run_coroutine_threadsafe(DoHclient.make_request(build_query(args)), loop)
    dnsr = future.result()
    for i in dnsr.answer:
        for j in i.items:
            if hasattr(j, 'address'):
                DNScache[name] = j.address
                return j.address
    return None
