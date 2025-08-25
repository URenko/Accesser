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

import os, platform
import datetime
from pathlib import Path

from cryptography import x509
from cryptography.x509.oid import NameOID
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.x509.extensions import (
    AuthorityKeyIdentifier,
    KeyUsage,
    ExtendedKeyUsage,
    SubjectKeyIdentifier,
)
from cryptography.x509.oid import ExtendedKeyUsageOID

from .log import logger
logger = logger.getChild("certmanager")
from . import setting
from .setting import basepath


def decide_state_path_legacy():
    if setting.config["importca"]:
        return Path(basepath)
    else:
        return Path()


def decide_state_path_unix_like():
    if os.geteuid() == 0:
        logger.warn("Running Accesser as the root user carries certain risks; see pull #245")
        return Path("/var/lib") / "accesser"

    state_path = os.getenv("XDG_STATE_HOME", None)
    if state_path is not None:
        state_path = Path(state_path) / "accesser"
    else:
        state_path = Path.home() / ".local/state" / "accesser"
    return state_path


def decide_certpath():
    certpath = None
    # 人为指定最优先
    #if setting.config["state_dir"]:
        #return Path(setting.config["state_dir"]) / "cert"
    match platform.system():
        case 'Linux' | 'FreeBSD':
            deprecated_path = decide_state_path_legacy() / "CERT"
            # 暂仅在 *nix 上视为已废弃
            if deprecated_path.exists():
                logger.warn("deprecated path, see pull #245")
                return deprecated_path
            certpath = decide_state_path_unix_like() / "cert"
        case _:
            # windows,mac,android ...
            certpath = decide_state_path_legacy() / "CERT"
    return certpath


certpath = decide_certpath()
if not certpath.exists():
    os.makedirs(certpath, exist_ok=True)


def create_root_ca():
    key = rsa.generate_private_key(
        public_exponent=65537,
        key_size=4096,
    )

    subject = issuer = x509.Name(
        [
            x509.NameAttribute(NameOID.ORGANIZATION_NAME, "Accesser"),
            x509.NameAttribute(NameOID.COMMON_NAME, "Accesser"),
        ]
    )
    cert = (
        x509.CertificateBuilder()
        .subject_name(subject)
        .issuer_name(issuer)
        .public_key(key.public_key())
        .serial_number(x509.random_serial_number())
        .not_valid_before(datetime.datetime.now(datetime.timezone.utc))
        .not_valid_after(
            datetime.datetime.now(datetime.timezone.utc)
            + datetime.timedelta(days=10 * 365)
        )
        .add_extension(
            x509.BasicConstraints(ca=True, path_length=None),
            critical=True,
        )
        .add_extension(
            KeyUsage(
                digital_signature=False,
                content_commitment=False,
                key_encipherment=False,
                data_encipherment=False,
                key_agreement=False,
                key_cert_sign=True,
                crl_sign=True,
                encipher_only=False,
                decipher_only=False,
            ),
            critical=True,
        )
        .add_extension(
            SubjectKeyIdentifier.from_public_key(key.public_key()),
            critical=False,
        )
        .sign(key, hashes.SHA256())
    )

    (certpath / "root.crt").write_bytes(
        cert.public_bytes(serialization.Encoding.PEM)
    )

    (certpath / "root.key").write_bytes(
        key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.PKCS8,
            encryption_algorithm=serialization.NoEncryption(),
        )
    )

    (certpath / "root.pfx").write_bytes(
        serialization.pkcs12.serialize_key_and_certificates(
            b"Accesser", key, cert, None, serialization.NoEncryption()
        )
    )


def create_certificate(server_name):
    rootpem = (certpath / "root.crt").read_bytes()
    rootkey = (certpath / "root.key").read_bytes()
    ca_cert = x509.load_pem_x509_certificate(rootpem)
    pkey = serialization.load_pem_private_key(rootkey, password=None)

    cert = (
        x509.CertificateBuilder()
        .subject_name(
            x509.Name(
                [
                    x509.NameAttribute(NameOID.ORGANIZATION_NAME, "Accesser"),
                    x509.NameAttribute(NameOID.COMMON_NAME, "Accesser_Proxy"),
                ]
            )
        )
        .issuer_name(ca_cert.subject)
        .public_key(pkey.public_key())
        .serial_number(x509.random_serial_number())
        .not_valid_before(
            datetime.datetime.now(datetime.timezone.utc)
            - datetime.timedelta(seconds=600)
        )
        .not_valid_after(
            datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(days=365)
        )
        .add_extension(
            x509.SubjectAlternativeName(
                [
                    x509.DNSName(server_name),
                    x509.DNSName("*." + server_name),
                ]
            ),
            critical=False,
        )
        .add_extension(
            KeyUsage(
                digital_signature=True,
                content_commitment=False,
                key_encipherment=False,
                data_encipherment=False,
                key_agreement=False,
                key_cert_sign=False,
                crl_sign=False,
                encipher_only=False,
                decipher_only=False,
            ),
            critical=True,
        )
        .add_extension(
            AuthorityKeyIdentifier.from_issuer_public_key(pkey.public_key()),
            critical=False,
        )
        .add_extension(
            SubjectKeyIdentifier.from_public_key(pkey.public_key()),
            critical=False,
        )
        .add_extension(
            ExtendedKeyUsage(
                usages=[
                    ExtendedKeyUsageOID.SERVER_AUTH,
                    ExtendedKeyUsageOID.CLIENT_AUTH,
                ]
            ),
            critical=True,
        )
        .sign(pkey, hashes.SHA256())
    )

    (certpath / f"{server_name}.crt").write_bytes(
        cert.public_bytes(serialization.Encoding.PEM)
        + pkey.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.PKCS8,
            encryption_algorithm=serialization.NoEncryption(),
        )
    )
