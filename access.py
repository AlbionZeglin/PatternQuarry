"""Explicit local access or a loopback-only Tailscale Serve trust boundary."""
from email.header import decode_header
import re
from urllib.parse import urlsplit


def tailscale_url(value):
    """Validate an exact node origin, never a wildcard or a public hostname."""
    try:
        u = urlsplit(value)
        host = u.hostname or ''
        port = u.port if u.port is not None else 443
        labels = host.split('.')
        if (u.scheme != 'https' or not host.endswith('.ts.net')
                or len(labels) < 4 or len(host) > 253
                or not all(re.fullmatch(r'[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?', label) for label in labels)
                or u.username is not None or u.password is not None
                or u.path not in ['', '/'] or u.query or u.fragment
                or not 1 <= port <= 65535):
            raise ValueError()
    except (ValueError, TypeError):
        raise ValueError('Use an exact HTTPS Tailscale node URL, e.g. https://mac.example.ts.net:8443') from None
    return f'https://{host}' + (f':{port}' if port != 443 else '')


class AccessPolicy:
    def __init__(self, port, url=None, user=None):
        if bool(url) != bool(user):
            raise ValueError('--tailscale-url and --tailscale-user must be supplied together')
        self.url = tailscale_url(url) if url else None
        self.user = user
        self.local_hosts = {f'localhost:{port}', f'127.0.0.1:{port}'}
        self.hosts = set(self.local_hosts)
        if self.url:
            if not user.strip() or any(ord(c) < 32 for c in user):
                raise ValueError('A valid Tailscale user login is required')
            u = urlsplit(self.url)
            self.remote_hosts = {u.netloc}
            if u.port is None:
                self.remote_hosts.add(u.netloc + ':443')
            self.hosts.update(self.remote_hosts)
            self.origins = {'https://' + host for host in self.remote_hosts}
        else:
            self.origins = {'http://' + host for host in self.local_hosts}

    @staticmethod
    def single(headers, key):
        values = headers.get_all(key, [])
        return values[0] if len(values) == 1 else None

    def allows(self, headers, peer='127.0.0.1'):
        if peer != '127.0.0.1':
            return False
        host = self.single(headers, 'Host')
        if host is None or host.lower() not in self.hosts:
            return False
        if not self.url:
            # A default local server must not accidentally become a proxy backend.
            return not any(k.lower().startswith(('tailscale-', 'x-forwarded-')) or k.lower() == 'forwarded' for k in headers.keys())
        login = self.single(headers, 'Tailscale-User-Login')
        if not login or headers.get('Tailscale-Funnel-Request') is not None:
            return False
        try:
            login = ''.join(part.decode(charset or 'ascii') if isinstance(part, bytes) else part
                            for part, charset in decode_header(login))
        except (ValueError, UnicodeError, LookupError):
            return False
        # Serve injects these headers and removes client-supplied identity headers.
        # Require identity on ALL requests, even if a proxy rewrites Host to localhost.
        return (login == self.user
                and self.single(headers, 'X-Forwarded-Proto') == 'https'
                and self.single(headers, 'X-Forwarded-Host') in self.remote_hosts)

    def allows_origin(self, headers):
        origins = headers.get_all('Origin', [])
        return ((not origins or len(origins) == 1 and origins[0] in self.origins)
                and headers.get('Sec-Fetch-Site') != 'cross-site')
