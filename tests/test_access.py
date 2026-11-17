from email.header import Header
from email.message import Message
import unittest

from access import AccessPolicy, tailscale_url
from iphone import owner_and_url, port_in_use


def headers(**values):
    h = Message()
    for key, value in values.items():
        h[key.replace('_', '-')] = value
    return h


class AccessTests(unittest.TestCase):
    def setUp(self):
        self.policy = AccessPolicy(18765, 'https://mac.example.ts.net:8443', 'owner@example.com')

    def proxy(self, **changes):
        values = dict(Host='mac.example.ts.net:8443', Tailscale_User_Login='owner@example.com',
                      X_Forwarded_Proto='https', X_Forwarded_Host='mac.example.ts.net:8443')
        values.update(changes)
        return headers(**values)

    def test_owner_only_including_rewritten_host(self):
        self.assertTrue(self.policy.allows(self.proxy()))
        self.assertTrue(self.policy.allows(self.proxy(Host='127.0.0.1:18765')))
        self.assertFalse(self.policy.allows(self.proxy(Tailscale_User_Login='other@example.com')))
        self.assertFalse(self.policy.allows(self.proxy(Host='127.0.0.1:18765', Tailscale_User_Login='')))
        self.assertFalse(self.policy.allows(headers(Host='localhost:18765')))
        self.assertFalse(self.policy.allows(self.proxy(), peer='100.1.2.3'))

    def test_forwarded_headers_never_expand_the_host_allowlist(self):
        self.assertFalse(self.policy.allows(self.proxy(Host='attacker.example')))
        self.assertFalse(self.policy.allows(self.proxy(X_Forwarded_Host='attacker.example')))
        self.assertFalse(self.policy.allows(self.proxy(X_Forwarded_Proto='http')))
        self.assertFalse(self.policy.allows(self.proxy(Tailscale_Funnel_Request='1')))
        duplicate = self.proxy()
        duplicate['Tailscale-User-Login'] = 'owner@example.com'
        self.assertFalse(self.policy.allows(duplicate))
        duplicate = self.proxy()
        duplicate['Host'] = 'localhost:18765'
        self.assertFalse(self.policy.allows(duplicate))

    def test_original_local_mode_and_unconfigured_proxy_rejection(self):
        policy = AccessPolicy(8765)
        self.assertTrue(policy.allows(headers(Host='localhost:8765')))
        self.assertTrue(policy.allows(headers(Host='127.0.0.1:8765')))
        self.assertFalse(policy.allows(headers(Host='mac.example.ts.net:8443')))
        self.assertFalse(policy.allows(headers(Host='localhost:8765', X_Forwarded_For='100.1.2.3')))
        self.assertFalse(policy.allows(headers(Host='localhost:8765', Tailscale_User_Login='owner@example.com')))

    def test_origin_check(self):
        self.assertTrue(self.policy.allows_origin(headers(Origin='https://mac.example.ts.net:8443')))
        self.assertTrue(self.policy.allows_origin(headers()))  # token is still required for a CLI client
        for origin in ['null', 'https://attacker.example', 'http://mac.example.ts.net:8443', 'http://localhost:18765']:
            self.assertFalse(self.policy.allows_origin(headers(Origin=origin)))
        self.assertFalse(self.policy.allows_origin(headers(Sec_Fetch_Site='cross-site')))
        duplicate = headers(Origin='https://mac.example.ts.net:8443')
        duplicate['Origin'] = 'https://mac.example.ts.net:8443'
        self.assertFalse(self.policy.allows_origin(duplicate))

    def test_url_validation_and_encoded_identity(self):
        for url in ['http://mac.example.ts.net', 'https://attacker.example', 'https://*.ts.net',
                    'https://mac.example.ts.net:0', 'https://mac.example.ts.net:65536',
                    'https://user@mac.example.ts.net', 'https://mac.example.ts.net/a',
                    'https://mac.example.ts.net?query=1', 'https://mac.example.ts.net.evil']:
            with self.subTest(url=url), self.assertRaises(ValueError):
                tailscale_url(url)
        self.assertEqual(tailscale_url('https://mac.example.ts.net:443/'), 'https://mac.example.ts.net')
        with self.assertRaises(ValueError):
            AccessPolicy(8765, 'https://mac.example.ts.net')
        policy = AccessPolicy(18765, 'https://mac.example.ts.net:8443', 'Jos\u00e9@example.com')
        h = self.proxy(Tailscale_User_Login=Header('Jos\u00e9@example.com', 'utf-8').encode())
        self.assertTrue(policy.allows(h))


class LauncherTests(unittest.TestCase):
    def test_detects_own_url_and_login_without_credentials(self):
        status = {'BackendState': 'Running', 'Self': {'DNSName': 'my-mac.example.ts.net.', 'UserID': 7},
                  'User': {'7': {'LoginName': 'owner@example.com'}}}
        self.assertEqual(owner_and_url(status, 8443), ('owner@example.com', 'https://my-mac.example.ts.net:8443'))
        status['Self']['Tags'] = ['tag:server']
        with self.assertRaisesRegex(ValueError, 'user-owned'):
            owner_and_url(status, 8443)
        with self.assertRaisesRegex(ValueError, 'not connected'):
            owner_and_url({'BackendState': 'NeedsLogin'}, 8443)

    def test_preserves_existing_serve_and_funnel_configuration(self):
        self.assertFalse(port_in_use(None, 8443))
        self.assertFalse(port_in_use({'TCP': {'443': {'HTTPS': True}}}, 8443))
        self.assertTrue(port_in_use({'TCP': {'8443': {'HTTPS': True}}}, 8443))
        self.assertTrue(port_in_use({'AllowFunnel': {'mac.example.ts.net:8443': True}}, 8443))
        self.assertTrue(port_in_use({'Web': {'mac.example.ts.net:8443': {'Handlers': {}}}}, 8443))
        self.assertTrue(port_in_use({'Foreground': {'session': {'TCP': {'8443': {'HTTPS': True}}}}}, 8443))


if __name__ == '__main__':
    unittest.main()
