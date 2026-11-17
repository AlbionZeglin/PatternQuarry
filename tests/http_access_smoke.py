"""Optional HTTP integration check; opens a temporary loopback listener."""
import http.client
import json
from pathlib import Path
import tempfile
import threading

from http.server import ThreadingHTTPServer
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from access import AccessPolicy
from core import Store
from seed import seed
from server import Handler


with tempfile.TemporaryDirectory() as temp:
    server = ThreadingHTTPServer(('127.0.0.1', 0), Handler)
    port = server.server_port
    server.store = Store(Path(temp) / 'test.sqlite3')
    seed(server.store)
    url = 'https://my-mac.example.ts.net:8443'
    host = url.split('://')[1]
    server.access = AccessPolicy(port, url, 'owner@example.com')
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    owner = {'Host': host, 'Tailscale-User-Login': 'owner@example.com',
             'X-Forwarded-Proto': 'https', 'X-Forwarded-Host': host}

    def request(path, headers=None, method='GET', data=None):
        connection = http.client.HTTPConnection('127.0.0.1', port, timeout=5)
        payload = json.dumps(data) if data is not None else None
        connection.request(method, path, body=payload, headers=headers or {})
        response = connection.getresponse()
        status, content = response.status, response.read()
        connection.close()
        return status, content

    try:
        for path in ['/', '/api/state', '/api/history?id=not-real', '/api/export', '/app.js', '/healthz']:
            assert request(path, {'Host': host})[0] == 403
            assert request(path, owner | {'Tailscale-User-Login': 'someone-else@example.com'})[0] == 403
            assert request(path, {'Host': f'localhost:{port}'})[0] == 403
        status, raw = request('/api/state', owner)
        assert status == 200
        state = json.loads(raw)
        assert any('PRIVATE-DEMO-ONLY' in str(i['body']) for i in state['items'])
        assert request('/api/state', owner | {'Host': 'attacker.example'})[0] == 403
        assert request('/api/state', owner | {'Host': f'localhost:{port}'})[0] == 200
        payload = {'kind':'project', 'project':'', 'body':{'name':'Owner HTTP test'},
                   'author':'HTTP tester', 'decision':'Authenticated integration test'}
        write_headers = owner | {'Origin': url, 'X-Local-Token': state['token'], 'Content-Type': 'application/json'}
        assert request('/api/save', write_headers | {'Origin': 'https://attacker.example'}, 'POST', payload)[0] == 403
        assert request('/api/save', owner | {'Origin':url}, 'POST', payload)[0] == 403
        status, raw = request('/api/save', write_headers, 'POST', payload)
        assert status == 200 and json.loads(raw)['body']['name'] == 'Owner HTTP test'
        release = state['releases'][0]['id']
        status, raw = request('/api/export?release=' + release, owner)
        assert status == 200 and raw[:2] == b'PK' and b'PRIVATE-DEMO-ONLY' not in raw
        # Default mode stays private/local and rejects accidental reverse proxy access.
        server.access = AccessPolicy(port)
        assert request('/api/state', {'Host':f'localhost:{port}'})[0] == 200
        assert request('/api/state', owner | {'Host':f'localhost:{port}'})[0] == 403
        print('PASS: guarded HTTP reads, writes and export; wrong/missing identity blocked; origin/token checks; original local mode')
    finally:
        server.shutdown()
        server.server_close()
        thread.join()
