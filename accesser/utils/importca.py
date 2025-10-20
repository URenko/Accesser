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

import os, sys, platform
import datetime
import subprocess
import locale
from pathlib import Path

from cryptography import x509
from cryptography.hazmat.primitives import serialization, hashes
from cryptography.hazmat.primitives.serialization import pkcs12

from . import setting
from . import certmanager as cm
from .log import logger
logger = logger.getChild('importca')


def run_and_log(cmd, check=True):
    result = subprocess.run(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT, 
        text=True,
    )

    logger.debug(result.stdout)

    if check:
        result.check_returncode()

    return result


def export_ca() -> bool:
    if platform.system() == 'Windows':
        try:
            pfx_path = setting.certpath.joinpath("root.pfx")
            ps_cmd = f"""
            $pwd = ConvertTo-SecureString -String "Accesser" -AsPlainText -Force
            $cert = Get-ChildItem Cert:\\CurrentUser\\My | Where-Object {{ $_.Subject -like "CN=Accesser*" }} |
                    Sort-Object NotBefore -Descending | Select-Object -First 1
            if ($null -eq $cert) {{ exit 1 }}
            Export-PfxCertificate -Cert $cert -FilePath "{pfx_path}" -Password $pwd -Force
            """
            run_and_log(["powershell", "-NoProfile", "-Command", ps_cmd], check=True)
            logger.debug("Export succeed.")
        except subprocess.CalledProcessError:
            logger.debug("Export failed.")
            return False
        private_key, certificate, _ = pkcs12.load_key_and_certificates(pfx_path.read_bytes(), password=b'Accesser')
        setting.certpath.joinpath("root.crt").write_bytes(certificate.public_bytes(serialization.Encoding.PEM))
        setting.certpath.joinpath("root.key").write_bytes(
            private_key.private_bytes(
                encoding=serialization.Encoding.PEM,
                format=serialization.PrivateFormat.PKCS8,
                encryption_algorithm=serialization.NoEncryption(),
            )
        )
        setting.certpath.joinpath("root.pfx").write_bytes(
            serialization.pkcs12.serialize_key_and_certificates(
                b"Accesser", private_key, certificate, None, serialization.NoEncryption()
            )
        )
        return True
    else: # TODO
        return False


def import_windows_ca():
    try:
        logger.info("Importing new certificate")
        run_and_log(f'CertUtil -f -user -p "" -importPFX My "{setting.certpath.joinpath("root.pfx")}"')
    except subprocess.CalledProcessError:
        logger.error("Import Failed")
        run_and_log('CertUtil -user -delstore My Accesser')
        logger.warning('Try to manually import the certificate')


def import_mac_ca():
    ca_hash = CertUtil.ca_thumbprint.replace(':', '')

    def get_exist_ca_sha1():
        args = ['security', 'find-certificate', '-Z', '-a', '-c', 'Accesser']
        output = subprocess.check_output(args)
        for line in output.splitlines(True):
            if len(line) == 53 and line.startswith("SHA hash:"):
                sha1_hash = line[12:52]
                return sha1_hash

    exist_ca_sha1 = get_exist_ca_sha1()
    if exist_ca_sha1 == ca_hash:
        logger.info("Accesser CA exist")
        return

    import_command = 'security add-trusted-cert -d -r trustRoot -k /Library/Keychains/System.keychain {}'.format('root.crt')
    if exist_ca_sha1:
        delete_ca_command = 'security delete-certificate -Z %s' % exist_ca_sha1
        exec_command = "%s;%s" % (delete_ca_command, import_command)
    else:
        exec_command = import_command

    admin_command = """osascript -e 'do shell script "%s" with administrator privileges' """ % exec_command
    cmd = admin_command.encode('utf-8')
    logger.info("try auto import CA command:%s", cmd)
    os.system(cmd)


def is_cert_valid(cert_path: Path, key_path: Path, ensure_trusted: bool) -> int:
    cert = x509.load_pem_x509_certificate(cert_path.read_bytes())

    if (datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(days=365)) > cert.not_valid_after_utc:
        logger.warning('The root certificate has expired or will expire soon!')
        return False

    private_key = serialization.load_pem_private_key(key_path.read_bytes(), password=None)

    public_key_cert = cert.public_key()
    public_key_private = private_key.public_key()
    if public_key_cert.public_numbers() != public_key_private.public_numbers():
        logger.warning('The root certificate and private key do not match!')
        return False

    if ensure_trusted:
        if sys.platform.startswith("win"):
            cert_fingerprint = cert.fingerprint(hashes.SHA1()).hex().upper()

            ps_cmd = f"""
            $found = $false
            Get-ChildItem Cert:\\CurrentUser\\Root, Cert:\\LocalMachine\\Root | ForEach-Object {{
                if ($_.Thumbprint -eq '{cert_fingerprint}') {{ $found = $true }}
            }}
            exit ($found -eq $false)
            """
            result = subprocess.run(["powershell", "-NoProfile", "-Command", ps_cmd])
            if result.returncode != 0:
                logger.warning('The root certificate is not yet trusted by the operating system!')
                return False

    return True


def import_ca():
    cert_path = setting.certpath.joinpath("root.crt")
    key_path = setting.certpath.joinpath("root.key")

    if not (cert_path.exists() and key_path.exists()) or not is_cert_valid(cert_path, key_path, ensure_trusted=setting.config['importca']):
        if not (export_ca() and is_cert_valid(cert_path, key_path, ensure_trusted=setting.config['importca'])):
            logger.warning('Generating a new root certificate...')
            cm.create_root_ca()
            if setting.config['importca']:
                if platform.system() == 'Windows':
                    import_windows_ca()
                    return
                else:
                    logger.warning('Automatic import of root certificate root.crt is not yet supported on this platform.')
    _log_msg = f'You can GET root certificate from http://localhost:{setting.config["server"]["port"]}/CERT/root.crt'
    if not setting.config['importca']:
        _log_msg += ' and import it manually.'
    logger.warning(_log_msg)
