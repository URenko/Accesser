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
import OpenSSL
import os, sys
import subprocess
sys.path.append(os.path.dirname(__file__))

def import_windows_ca(certfile):
    def logandrun(cmd):
        return logging.info(subprocess.run(cmd, check=True, stdout=subprocess.PIPE).stdout)
    try:
        logging.info("Deleting old certificate")
        logandrun("CertUtil -delstore Root Accesser")
        logging.info("Importing new certificate")
        logandrun("CertUtil -addstore -f Root {}".format(certfile))
    except subprocess.CalledProcessError:
        logging.error("Import Failed")

def import_mac_ca(certfile):
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

    import_command = 'security add-trusted-cert -d -r trustRoot -k /Library/Keychains/System.keychain {}'.format(certfile)
    if exist_ca_sha1:
        delete_ca_command = 'security delete-certificate -Z %s' % exist_ca_sha1
        exec_command = "%s;%s" % (delete_ca_command, import_command)
    else:
        exec_command = import_command

    admin_command = """osascript -e 'do shell script "%s" with administrator privileges' """ % exec_command
    cmd = admin_command.encode('utf-8')
    logging.info("try auto import CA command:%s", cmd)
    os.system(cmd)

def import_ca(certfile):
    if sys.platform.startswith('win'):
        import win32elevate
        if not win32elevate.areAdminRightsElevated():
            win32elevate.elevateAdminRun('"'+os.path.abspath(__file__)+'" '+certfile, reattachConsole=False)
        else:
            main(certfile)
    else:
        logging.warning('other platform support is under development, please import root.crt manually.')

def main(certfile):
    import traceback, time
    try:
        if sys.platform.startswith('win'):
            import_windows_ca(certfile)
        else:
            logging.warning('other platform support is under development, please import root.crt manually.')
    except Exception:
        traceback.print_exc()

if __name__ == '__main__':
    import configparser
    config = configparser.ConfigParser()
    config.read('setting.ini')
    loglevel = getattr(logging, config['setting']['loglevel'])
    logfile = config['setting']['logfile']
    logging.basicConfig(level=loglevel, filename=logfile,
                        format='%(asctime)s %(levelname)-8s L%(lineno)-3s %(message)s',
                        datefmt='%Y-%m-%d %H:%M:%S', filemode='a+')
    if len(sys.argv) < 2:
        logging.error("Error argument")
        sys.exit(1)
    main(sys.argv[1])