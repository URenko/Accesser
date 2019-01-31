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

import os
import random
import sys
import ssl
from OpenSSL import crypto

def parse_domain():
    domains = set()
    with open('domains.txt') as f:
        for domain in f:
            domain = domain.strip().split('.')
            if len(domain) == 2:
                domains.add("DNS:{}.{}".format(*domain))
            else:
                domain[0] = 'DNS:*'
                domains.add('.'.join(domain))
    return ','.join(domains).encode()

def match_domain(certfile):
    if not os.path.exists(certfile):
        return False
    cert = {'subjectAltName': get_cert_domain(certfile)}
    with open('domains.txt') as f:
        for domain in f:
            try:
                ssl.match_hostname(cert, domain.strip())
            except ssl.CertificateError:
                return False
    return True
    
def create_root_ca():
    pkey = crypto.PKey()
    pkey.generate_key(crypto.TYPE_RSA, 4096)

    cert = crypto.X509()
    cert.set_version(2)
    cert.set_serial_number(int(random.random() * sys.maxsize))
    cert.gmtime_adj_notBefore(0)
    cert.gmtime_adj_notAfter(60 * 60 * 24 * 365)

    subject = cert.get_subject()
    subject.CN = "Accesser"
    subject.O = "Accesser"

    issuer = cert.get_issuer()
    issuer.CN = "Accesser"
    issuer.O = "Accesser"

    cert.set_pubkey(pkey)
    cert.add_extensions([
        crypto.X509Extension(b"basicConstraints", True,
                             b"CA:TRUE"),
        crypto.X509Extension(b"subjectKeyIdentifier", False, b"hash",
                             subject=cert)
    ])
    cert.add_extensions([
        crypto.X509Extension(b"authorityKeyIdentifier", False, b"keyid:always",
            issuer=cert)
    ])
    cert.sign(pkey, "sha256")

    with open("CERT/root.crt", "wb") as certfile:
        certfile.write(crypto.dump_certificate(crypto.FILETYPE_PEM, cert))
        certfile.close()

    with open("CERT/root.key", "wb") as pkeyfile:
        pkeyfile.write(crypto.dump_privatekey(crypto.FILETYPE_PEM, pkey))
        pkeyfile.close()

    pfx = crypto.PKCS12Type()
    pfx.set_privatekey(pkey)
    pfx.set_certificate(cert)
    with open('CERT/root.pfx', 'wb') as pfxfile:
        pfxfile.write(pfx.export())

def create_certificate(certfile, pkeyfile):
    rootpem = open("CERT/root.crt", "rb").read()
    rootkey = open("CERT/root.key", "rb").read()
    ca_cert = crypto.load_certificate(crypto.FILETYPE_PEM, rootpem)
    ca_key = crypto.load_privatekey(crypto.FILETYPE_PEM, rootkey)

    pkey = crypto.PKey()
    pkey.generate_key(crypto.TYPE_RSA, 2048)

    cert = crypto.X509()
    cert.set_serial_number(int(random.random() * sys.maxsize))
    cert.gmtime_adj_notBefore(0)
    cert.gmtime_adj_notAfter(60 * 60 * 24 * 365)
    cert.set_version(2)

    subject = cert.get_subject()
    subject.CN = "Accesser_Proxy"
    subject.O = "Accesser"

    cert.add_extensions([crypto.X509Extension(b"subjectAltName", False, parse_domain())])

    cert.set_issuer(ca_cert.get_subject())

    cert.set_pubkey(pkey)
    cert.sign(ca_key, "sha256")


    with open(certfile, "wb") as certfile:
        certfile.write(crypto.dump_certificate(crypto.FILETYPE_PEM, cert))
        certfile.close()

    with open(pkeyfile, "wb") as pkeyfile:
        pkeyfile.write(crypto.dump_privatekey(crypto.FILETYPE_PEM, pkey))
        pkeyfile.close()

def _subjectAltNameTuple(extension):
    names = crypto._ffi.cast(
        "GENERAL_NAMES*", crypto._lib.X509V3_EXT_d2i(extension._extension)
    )

    names = crypto._ffi.gc(names, crypto._lib.GENERAL_NAMES_free)
    parts = ()
    for i in range(crypto._lib.sk_GENERAL_NAME_num(names)):
        name = crypto._lib.sk_GENERAL_NAME_value(names, i)
        try:
            label = extension._prefixes[name.type]
        except KeyError:
            pass
        else:
            value = crypto._native(
                crypto._ffi.buffer(name.d.ia5.data, name.d.ia5.length)[:])
            parts += ((label, value),)
    return parts

def get_cert_domain(certfile):
    domains = []
    with open(certfile, "rb") as f:
        cert = crypto.load_certificate(crypto.FILETYPE_PEM, f.read())
    for i in range(cert.get_extension_count()):
        extension = cert.get_extension(i)
        if b"subjectAltName" == extension.get_short_name():
            return _subjectAltNameTuple(extension)