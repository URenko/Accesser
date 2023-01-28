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

from . import setting
from .setting import basepath

if setting.config['importca']:
    certpath = os.path.join(basepath, 'CERT')
else:
    certpath ='CERT'
if not os.path.exists(certpath):
    os.makedirs(certpath, exist_ok=True)

def create_root_ca():
    pkey = crypto.PKey()
    pkey.generate_key(crypto.TYPE_RSA, 4096)

    cert = crypto.X509()
    cert.set_version(2)
    cert.set_serial_number(int(random.random() * sys.maxsize))
    cert.gmtime_adj_notBefore(0)
    cert.gmtime_adj_notAfter(60 * 60 * 24 * 365 * 10)

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

    with open(os.path.join(certpath ,"root.crt"), "wb") as certfile:
        certfile.write(crypto.dump_certificate(crypto.FILETYPE_PEM, cert))
        certfile.close()

    with open(os.path.join(certpath ,"root.key"), "wb") as pkeyfile:
        pkeyfile.write(crypto.dump_privatekey(crypto.FILETYPE_PEM, pkey))
        pkeyfile.close()

    pfx = crypto.PKCS12()
    pfx.set_privatekey(pkey)
    pfx.set_certificate(cert)
    with open(os.path.join(certpath ,"root.pfx"), 'wb') as pfxfile:
        pfxfile.write(pfx.export())

pkey = crypto.PKey()
pkey.generate_key(crypto.TYPE_RSA, 2048)

def create_certificate(server_name):
    rootpem = open(os.path.join(certpath ,"root.crt"), "rb").read()
    rootkey = open(os.path.join(certpath ,"root.key"), "rb").read()
    ca_cert = crypto.load_certificate(crypto.FILETYPE_PEM, rootpem)
    ca_key = crypto.load_privatekey(crypto.FILETYPE_PEM, rootkey)

    cert = crypto.X509()
    cert.set_serial_number(int(random.random() * sys.maxsize))
    cert.gmtime_adj_notBefore(-600)
    cert.gmtime_adj_notAfter(60 * 60 * 24 * 365)
    cert.set_version(2)

    subject = cert.get_subject()
    subject.CN = "Accesser_Proxy"
    subject.O = "Accesser"

    cert.add_extensions([crypto.X509Extension(b"subjectAltName", False, ('DNS:'+server_name+',DNS:*.'+server_name).encode())])

    cert.set_issuer(ca_cert.get_subject())

    cert.set_pubkey(pkey)
    cert.sign(ca_key, "sha256")


    with open(os.path.join(certpath ,'{}.crt'.format(server_name)), "wb") as certfile:
        certfile.write(crypto.dump_certificate(crypto.FILETYPE_PEM, cert))
        certfile.write(crypto.dump_privatekey(crypto.FILETYPE_PEM, pkey))
        certfile.close()
