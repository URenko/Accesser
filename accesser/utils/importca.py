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

from OpenSSL import crypto
import os, sys
import subprocess
import locale

from . import setting
from . import certmanager as cm
from .setting import basepath
from .log import logger
logger = logger.getChild('importca')

certpath = os.path.join(basepath, 'CERT')

def logandrun(cmd):
    if hasattr(subprocess, 'STARTUPINFO'):
        si = subprocess.STARTUPINFO()
        si.dwFlags |= subprocess.STARTF_USESHOWWINDOW
    else:
        si = None
    return logger.debug(subprocess.check_output(cmd, stdin=subprocess.PIPE, stderr=subprocess.PIPE \
           , startupinfo=si, env=os.environ).decode(locale.getpreferredencoding()))

def import_windows_ca():
    try:
        logandrun('certutil -f -user -p "" -exportPFX My Accesser '+os.path.join(certpath, 'root.pfx'))
    except subprocess.CalledProcessError:
        logger.debug("Export Failed")
    if not os.path.exists(os.path.join(certpath ,"root.pfx")):
        cm.create_root_ca()
        try:
            logger.info("Importing new certificate")
            logandrun('CertUtil -f -user -p "" -importPFX My '+os.path.join(certpath, 'root.pfx'))
        except subprocess.CalledProcessError:
            logger.error("Import Failed")
            logandrun('CertUtil -user -delstore My Accesser')
            # os.remove(os.path.join(certpath ,"root.pfx"))
            # os.remove(os.path.join(certpath ,"root.crt"))
            # os.remove(os.path.join(certpath ,"root.key"))
            # sys.exit(5)
            logger.warning('Try to manually import the certificate')
    else:
        with open(os.path.join(certpath ,"root.pfx"), 'rb') as pfxfile:
            p12 = crypto.load_pkcs12(pfxfile.read())
        with open(os.path.join(certpath ,"root.crt"), "wb") as certfile:
            certfile.write(crypto.dump_certificate(crypto.FILETYPE_PEM, p12.get_certificate()))
            certfile.close()
        with open(os.path.join(certpath ,"root.key"), "wb") as pkeyfile:
            pkeyfile.write(crypto.dump_privatekey(crypto.FILETYPE_PEM, p12.get_privatekey()))
            pkeyfile.close()

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

def import_ca():
    if not(os.path.exists(os.path.join(certpath ,"root.crt")) and os.path.exists(os.path.join(certpath ,"root.key"))):
        if setting.config['importca']:
            if sys.platform.startswith('win'):
                import_windows_ca()
            else:
                cm.create_root_ca()
                logger.warning('other platform support is under development, please import root.crt manually.')
        else:
            cm.create_root_ca()