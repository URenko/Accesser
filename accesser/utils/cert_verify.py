from ssl import CertificateError, _inet_paton, _dnsname_match, _ipaddress_match

def loosely_dnsname_match(dn, hostname):
    return dn.rsplit('.', maxsplit=2)[-2:] == hostname.rsplit('.', maxsplit=2)[-2:]

def match_hostname(cert, hostname, policy):
    """based on ssl.py in python3.11
    """
    try:
        host_ip = _inet_paton(hostname)
    except ValueError:
        # Not an IP address (common case)
        host_ip = None
    dnsnames = []
    san = cert.get('subjectAltName', ())
    for key, value in san:
        if key == 'DNS':
            if host_ip is None and (_dnsname_match(value, hostname) or (policy != 'strict' and loosely_dnsname_match(value, hostname))):
                return True
            dnsnames.append(value)
        elif key == 'IP Address':
            if host_ip is not None and _ipaddress_match(value, host_ip):
                return True
            dnsnames.append(value)
    if not dnsnames:
        # The subject is only checked when there is no dNSName entry
        # in subjectAltName
        for sub in cert.get('subject', ()):
            for key, value in sub:
                # XXX according to RFC 2818, the most specific Common Name
                # must be used.
                if key == 'commonName':
                    if _dnsname_match(value, hostname) or (policy != 'strict' and loosely_dnsname_match(value, hostname)):
                        return False
                    dnsnames.append(value)
    if len(dnsnames) > 1:
        return False
    elif len(dnsnames) == 1:
        return False
    else:
        raise CertificateError("no appropriate commonName or "
            "subjectAltName fields were found")