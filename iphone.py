#!/usr/bin/env python3
"""Start the existing workspace behind private, owner-only Tailscale Serve."""
import argparse
from email.header import Header
import json
import shutil
import signal
import socket
import subprocess
import sys
import time
from pathlib import Path
from urllib.error import URLError
from urllib.request import Request, build_opener, ProxyHandler

from access import tailscale_url

ROOT = Path(__file__).resolve().parent


def find_tailscale(explicit=None):
    candidates = [explicit] if explicit else [
        shutil.which('tailscale'),
        '/Applications/Tailscale.app/Contents/MacOS/Tailscale',
        str(Path.home() / 'Applications/Tailscale.app/Contents/MacOS/Tailscale'),
    ]
    for candidate in candidates:
        if candidate and Path(candidate).is_file():
            return str(candidate)
    raise ValueError('Tailscale was not found. Install the Mac app from https://tailscale.com/download/mac, open it, and sign in. Then run this launcher again.')


def read_json(cli, *args):
    try:
        result = subprocess.run([cli, *args], capture_output=True, text=True, timeout=20)
    except (OSError, subprocess.TimeoutExpired) as e:
        raise ValueError('Could not contact Tailscale. Open the Tailscale app and check that it is connected.') from e
    if result.returncode:
        raise ValueError('Tailscale could not report its status. Open the Mac app, sign in, and check that a current version is installed. You can inspect it with: tailscale ' + ' '.join(args))
    try:
        return json.loads(result.stdout)
    except ValueError:
        raise ValueError('Tailscale returned an unreadable status. Update the Mac app and try again.') from None


def owner_and_url(status, https_port):
    if not isinstance(status, dict) or status.get('BackendState') != 'Running':
        raise ValueError('Tailscale is not connected. Open the Mac app, sign in, and turn it on.')
    own = status.get('Self') or {}
    login = (status.get('User') or {}).get(str(own.get('UserID')), {}).get('LoginName')
    if not login or own.get('Tags'):
        raise ValueError('This launcher needs a user-owned Mac with a Tailscale login. Tagged devices have no user identity; ask your tailnet administrator before changing that setup.')
    dns = (own.get('DNSName') or '').rstrip('.')
    url = tailscale_url(f'https://{dns}:{https_port}')
    return login, url


def port_in_use(config, port):
    """Check background and nested foreground configs without resetting anything."""
    if not isinstance(config, dict):
        return False
    tcp = config.get('TCP') or {}
    if isinstance(tcp, dict) and str(port) in tcp:
        return True
    for key in ['Web', 'AllowFunnel']:
        entries = config.get(key) or {}
        if isinstance(entries, dict) and any(str(host).endswith(':' + str(port)) and value
                                             for host, value in entries.items()):
            return True
    for value in config.values():
        if isinstance(value, dict) and port_in_use(value, port):
            return True
    return False


def stop(process, graceful=False):
    if process is not None and process.poll() is None:
        try:
            if graceful:
                process.send_signal(signal.SIGINT)
            else:
                process.terminate()
        except ProcessLookupError:
            return
        try:
            process.wait(timeout=8)
        except subprocess.TimeoutExpired:
            process.kill()
            process.wait()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--https-port', type=int, default=8443)
    parser.add_argument('--port', type=int, default=18765, help='Loopback backend port (default: 18765)')
    parser.add_argument('--data', default=str(ROOT / 'data' / 'studio.sqlite3'))
    parser.add_argument('--tailscale-bin', help='Optional path to the Tailscale CLI')
    args = parser.parse_args()
    for port in [args.port, args.https_port]:
        if not 1 <= port <= 65535:
            parser.error('Ports must be between 1 and 65535')
    if args.port == args.https_port:
        parser.error('The backend and HTTPS ports must be different')
    backend = serve = None
    def interrupted(signum, frame):
        raise KeyboardInterrupt
    previous_signals = {sig: signal.signal(sig, interrupted) for sig in [signal.SIGTERM, signal.SIGHUP]}
    try:
        cli = find_tailscale(args.tailscale_bin)
        login, url = owner_and_url(read_json(cli, 'status', '--json'), args.https_port)
        config = read_json(cli, 'serve', 'status', '--json')
        if config is not None and not isinstance(config, dict):
            raise ValueError('Unrecognized Serve configuration; nothing was changed.')
        if port_in_use(config, args.https_port):
            raise ValueError(f'Tailscale HTTPS port {args.https_port} is already configured. Nothing was changed. Choose a free port, for example: python3 iphone.py --https-port 9443')
        # Do not attach a proxy to an older unauthenticated app on an occupied port.
        probe = socket.socket()
        try:
            probe.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            probe.bind(('127.0.0.1', args.port))
        except OSError:
            raise ValueError(f'Local port {args.port} is busy. Close the other iPhone launcher, or choose a free backend port with --port.') from None
        finally:
            probe.close()
        print('Starting the existing Pattern Quarry database in owner-only Tailscale mode.', flush=True)
        backend = subprocess.Popen([sys.executable, str(ROOT / 'server.py'), '--port', str(args.port),
                                    '--data', str(args.data), '--tailscale-url', url, '--tailscale-user', login])
        # Verify the guarded backend before starting Serve; no project data is read.
        opener = build_opener(ProxyHandler({}))
        ready = False
        for _ in range(60):
            if backend.poll() is not None:
                raise ValueError('The guarded backend could not start; no Tailscale service was started.')
            req = Request(f'http://127.0.0.1:{args.port}/healthz', headers={
                'Host': url.split('://')[1], 'Tailscale-User-Login': Header(login, 'utf-8', maxlinelen=10000).encode(),
                'X-Forwarded-Proto': 'https', 'X-Forwarded-Host': url.split('://')[1]})
            try:
                with opener.open(req, timeout=.5) as response:
                    ready = json.load(response) == {'status': 'ok'}
                if ready:
                    break
            except (URLError, OSError, ValueError):
                time.sleep(.1)
        if not ready:
            raise ValueError('The backend did not become ready; no Tailscale service was started.')
        print(f'\nOn your iPhone: connect Tailscale with the SAME LOGIN, then open Safari:\n\n  {url}\n', flush=True)
        print('If Tailscale asks to enable HTTPS/Serve, follow its setup link. The URL works once Serve reports it is available.', flush=True)
        print('Keep this Terminal open and the Mac awake. Control-C stops both the app and this private Serve session.\n', flush=True)
        # Foreground Serve creates a scoped session. No --bg, Funnel, reset, or ACL changes.
        serve = subprocess.Popen([cli, 'serve', f'--https={args.https_port}', f'http://127.0.0.1:{args.port}'])
        while serve.poll() is None:
            if backend.poll() is not None:
                raise ValueError('The app stopped. Closing the private Serve session.')
            time.sleep(.3)
        if serve.returncode:
            raise ValueError('Tailscale Serve did not start or stopped with an error. Review its message above; enable HTTPS if requested, then rerun this launcher.')
        return 0
    except (ValueError, OSError) as e:
        print(f'\n{e}', file=sys.stderr, flush=True)
        return 1
    except KeyboardInterrupt:
        print('\nStopping this private iPhone session.', flush=True)
        return 0
    finally:
        for sig, handler in previous_signals.items():
            signal.signal(sig, handler)
        stop(serve, graceful=True)
        stop(backend)


if __name__ == '__main__':
    sys.exit(main())
