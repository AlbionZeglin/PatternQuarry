#!/usr/bin/env python3
import argparse
import io
import json
import os
import secrets
import zipfile
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlparse, parse_qs
from core import Store, FIELDS, canonical, markdown
from seed import seed, PROMPTS
from access import AccessPolicy

ROOT = Path(__file__).parent
TOKEN = secrets.token_urlsafe(32)

def bundle(releases):
    out = io.BytesIO()
    # Fixed zip metadata makes repeated exports byte-identical.
    with zipfile.ZipFile(out, 'w', zipfile.ZIP_DEFLATED) as z:
        def add(name, content):
            info = zipfile.ZipInfo(name, (2026, 1, 1, 0, 0, 0))
            info.compress_type = zipfile.ZIP_DEFLATED
            z.writestr(info, content)
        for r in sorted(releases, key=lambda r: r['pattern']['id']):
            add(r['pattern']['id'] + '.md', markdown(r))
            add(r['pattern']['id'] + '.json', json.dumps(r, indent=2, ensure_ascii=False))
        add('manifest.json', json.dumps({'schema_version': '1.0', 'releases': [{'id': r['id'], 'pattern': r['pattern']['id'], 'revision': r['pattern']['rev'], 'input_sha256': r['input_sha256']} for r in sorted(releases, key=lambda r: r['pattern']['id'])]}, indent=2))
        add('README.md', '# Published pattern language\n\nOnly explicitly reviewed public snapshots are included. Relative Markdown links resolve for patterns selected together. A link to an unselected pattern is a stable ID reference, not an included dependency. Claim anchors resolve to the exact public evidence revisions included in each file. Private interview history is never included.\n')
    return out.getvalue()

class Handler(BaseHTTPRequestHandler):
    def reply(self, data, code=200, content='application/json', attachment=None):
        raw = data if isinstance(data, bytes) else json.dumps(data).encode()
        self.send_response(code)
        self.send_header('Content-Type', content)
        self.send_header('Content-Length', str(len(raw)))
        self.send_header('Cache-Control', 'no-store')
        self.send_header('X-Content-Type-Options', 'nosniff')
        self.send_header('Content-Security-Policy', "default-src 'self'; script-src 'self'; style-src 'self'; connect-src 'self'; frame-ancestors 'none'; base-uri 'none'; form-action 'self'")
        if attachment:
            self.send_header('Content-Disposition', 'attachment; filename="' + attachment + '"')
        self.end_headers()
        self.wfile.write(raw)

    def allowed(self):
        return self.server.access.allows(self.headers, self.client_address[0])

    def do_GET(self):
        if not self.allowed():
            return self.reply({'error': 'Access denied. In Tailscale mode, connect through Serve using the configured Tailscale login.'}, 403)
        u = urlparse(self.path)
        q = parse_qs(u.query)
        try:
            if u.path == '/healthz':
                return self.reply({'status': 'ok'})
            if u.path == '/api/state':
                return self.reply({'items': self.server.store.all(), 'releases': self.server.store.releases(), 'fields': FIELDS, 'prompts': PROMPTS, 'token': TOKEN})
            if u.path == '/api/history':
                return self.reply(self.server.store.history(q['id'][0]))
            if u.path == '/api/export':
                ids = q.get('release', [])
                releases = [r for r in self.server.store.releases() if r['id'] in ids]
                if not releases or len(releases) != len(set(ids)):
                    raise ValueError('Select existing published releases')
                if len({r['pattern']['id'] for r in releases}) != len(releases):
                    raise ValueError('Choose only one revision per pattern for a language export')
                return self.reply(bundle(releases), content='application/zip', attachment='pattern-language.zip')
            files = {'/': ('index.html', 'text/html; charset=utf-8'), '/app.js': ('app.js', 'text/javascript; charset=utf-8'), '/style.css': ('style.css', 'text/css; charset=utf-8')}
            if u.path in files:
                name, mime = files[u.path]
                return self.reply((ROOT / 'static' / name).read_bytes(), content=mime)
            return self.reply({'error': 'Not found'}, 404)
        except (ValueError, KeyError) as e:
            self.reply({'error': str(e)}, 400)

    def do_POST(self):
        if (not self.allowed() or not self.server.access.allows_origin(self.headers)
                or self.headers.get('X-Local-Token') != TOKEN):
            return self.reply({'error': 'Invalid request or access denied; reload from the configured application URL'}, 403)
        try:
            size = int(self.headers.get('Content-Length', '0'))
            if size > 2_000_000:
                raise ValueError('Request exceeds 2 MB limit')
            data = json.loads(self.rfile.read(size))
            if self.path == '/api/save':
                result = self.server.store.save(**data)
            elif self.path == '/api/promote':
                result = self.server.store.promote(**data)
            else:
                return self.reply({'error': 'Not found'}, 404)
            self.reply(result)
        except (ValueError, KeyError, TypeError) as e:
            self.reply({'error': str(e)}, 400)

    def log_message(self, fmt, *args):
        # Deliberately no URLs/query strings or interview contents in logs.
        pass

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--port', type=int, default=8765)
    parser.add_argument('--data', default=str(ROOT / 'data' / 'studio.sqlite3'))
    parser.add_argument('--tailscale-url', help='Exact HTTPS node origin; use iphone.py for automatic setup')
    parser.add_argument('--tailscale-user', help='Exact Tailscale owner login allowed to access this workspace')
    args = parser.parse_args()
    try:
        access = AccessPolicy(args.port, args.tailscale_url, args.tailscale_user)
    except ValueError as e:
        parser.error(str(e))
    path = Path(args.data)
    path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
    store = Store(path)
    os.chmod(path, 0o600)
    seed(store)
    server = ThreadingHTTPServer(('127.0.0.1', args.port), Handler)
    server.store = store
    server.access = access
    address = access.url or f'http://localhost:{args.port}'
    print(f'Pattern Quarry → {address} (Control-C to stop)', flush=True)
    if access.url:
        print('Tailscale mode: only the configured owner identity via HTTPS Serve can access this backend.', flush=True)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        server.server_close()

if __name__ == '__main__':
    main()
