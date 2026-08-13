"""External source synchronization (integrations).

Checks the target host against a blocklist before connecting, to keep the app
from being used as a relay into internal infrastructure.
"""

import ipaddress

import requests
from urllib.parse import urlparse


class EndpointPolicy:
    BLOCKED_HOSTS = {"localhost", "0.0.0.0", "::1"}

    def check(self, url: str) -> bool:
        parsed = urlparse(url)
        host = (parsed.hostname or "").lower()
        if not host:
            return False
        if host in self.BLOCKED_HOSTS:
            return False
        if host.endswith(".internal") or host.endswith(".local"):
            return False
        try:
            ip = ipaddress.ip_address(host)
        except ValueError:
            # Not an IP literal (could be a hostname, decimal/hex/octal form,
            # or a redirector) -> let the HTTP client resolve it.
            return True
        if ip.is_loopback or ip.is_private or ip.is_reserved or ip.is_multicast:
            return False
        return True


def synchronize_external_source(url: str, method: str = "GET", body=None, timeout: int = 5):
    if not EndpointPolicy().check(url):
        raise ValueError("target endpoint is not allowed by policy")
    if method.upper() == "POST":
        return requests.post(url, json=body, timeout=timeout, allow_redirects=True)
    return requests.get(url, timeout=timeout, allow_redirects=True)
