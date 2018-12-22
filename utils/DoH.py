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
from dohproxy import client_protocol, constants, utils

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

args = utils.client_parser_base().parse_args(None)
args.domain = 'mozilla.cloudflare-dns.com'
args.qtype = 'A'
args.dnssec = True
DNScache = dict()

def init():
    global DoHclient,loop
    logger = logging.getLogger('DoH')
    logger.setLevel(logging.INFO)
    DoHclient = Client(args=args, logger=logger)
    loop = asyncio.get_event_loop()
    return loop

def DNSLookup(name):
    if name in DNScache:
        return DNScache[name]
    args.qname = name
    future = asyncio.run_coroutine_threadsafe(DoHclient.make_request(build_query(args)), loop)
    dnsr = future.result(5)
    for i in dnsr.answer:
        for j in i.items:
            if hasattr(j, 'address'):
                DNScache[name] = j.address
                return j.address
    return None
