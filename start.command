#!/bin/bash
set -e
cd "$(dirname "$0")"
if ! command -v python3 >/dev/null 2>&1; then
  echo 'Install Python 3.10 or newer from https://www.python.org/downloads/macos/ and try again.'
  read -r -p 'Press Return to close.'
  exit 1
fi
python3 -c 'import sys; assert sys.version_info >= (3,10), "Python 3.10 or newer is required"'
python3 server.py
