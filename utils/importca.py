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
from OpenSSL import crypto
import os, sys
import subprocess
sys.path.append(os.path.dirname(__file__))
import certmanager as cm

def logandrun(cmd):
    return logging.info(subprocess.run(cmd, check=True, stdout=subprocess.PIPE).stdout)

def import_windows_ca():
    try:
        logandrun('certutil -f -user -p "" -exportPFX My Accesser CERT\\root.pfx')
    except subprocess.CalledProcessError:
        logging.debug("Export Failed")
    if not os.path.exists('CERT/root.pfx'):
        cm.create_root_ca()
        try:
            logging.info("Importing new certificate")
            logandrun('CertUtil -f -user -p "" -importPFX My CERT\\root.pfx')
        except subprocess.CalledProcessError:
            logging.error("Import Failed")
            os.remove('CERT/root.pfx')
            os.remove('CERT/root.crt')
            os.remove('CERT/root.key')
            logandrun('CertUtil -user -delstore My Accesser')
            sys.exit(5)
    else:
        with open('CERT/root.pfx', 'rb') as pfxfile:
            p12 = crypto.load_pkcs12(pfxfile.read())
        with open("CERT/root.crt", "wb") as certfile:
            certfile.write(crypto.dump_certificate(crypto.FILETYPE_PEM, p12.get_certificate()))
            certfile.close()
        with open("CERT/root.key", "wb") as pkeyfile:
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
        logging.info("Accesser CA exist")
        return

    import_command = 'security add-trusted-cert -d -r trustRoot -k /Library/Keychains/System.keychain {}'.format('root.crt')
    if exist_ca_sha1:
        delete_ca_command = 'security delete-certificate -Z %s' % exist_ca_sha1
        exec_command = "%s;%s" % (delete_ca_command, import_command)
    else:
        exec_command = import_command

    admin_command = """osascript -e 'do shell script "%s" with administrator privileges' """ % exec_command
    cmd = admin_command.encode('utf-8')
    logging.info("try auto import CA command:%s", cmd)
    os.system(cmd)

def import_ca():
    if not(os.path.exists('CERT/root.crt') and os.path.exists('CERT/root.key')):
        if sys.platform.startswith('win'):
            import_windows_ca()
        else:
            cm.create_root_ca()
            logging.warning('other platform support is under development, please import root.crt manually.')