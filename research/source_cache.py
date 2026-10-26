"""Restore deliberately evicted downloads; never silently accept changed evidence."""
import argparse
import hashlib
import io
import json
import os
from pathlib import Path
import tempfile
import urllib.request
import zipfile

ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / 'research/cache-manifest.json'


def target_path(relative):
    path = (ROOT / relative).resolve()
    if not path.is_relative_to(ROOT):
        raise ValueError('Cache path must stay inside the project')
    return path


def restore(entry, fetch=None):
    path = target_path(entry['path'])
    if path.exists():
        if hashlib.sha256(path.read_bytes()).hexdigest() != entry['sha256']:
            raise ValueError('Existing file differs; refusing to overwrite it')
        return 'already present'
    if fetch is None:
        request = urllib.request.Request(entry['url'], headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(request, timeout=60) as response:
            content = response.read()
    else:
        content = fetch(entry['url'])
    if entry['method'] == 'zip_member':
        with zipfile.ZipFile(io.BytesIO(content)) as archive:
            content = archive.read(entry['member'])
    if hashlib.sha256(content).hexdigest() != entry['sha256']:
        raise ValueError('Download differs from the recorded snapshot; re-check the live source before using it')
    path.parent.mkdir(parents=True, exist_ok=True)
    # Publish only a fully verified file; clean up partial writes after any failure.
    temporary = None
    try:
        with tempfile.NamedTemporaryFile(dir=path.parent, delete=False) as output:
            temporary = output.name
            output.write(content)
        os.replace(temporary, path)
    finally:
        if temporary and os.path.exists(temporary):
            os.unlink(temporary)
    return 'restored'


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('paths', nargs='*', help='Exact project-relative paths to restore')
    parser.add_argument('--list', action='store_true', help='List evicted paths')
    args = parser.parse_args()
    entries = json.loads(MANIFEST.read_text())['files']
    index = {entry['path']: entry for entry in entries}
    if args.list:
        for entry in entries:
            print(entry['path'])
        return 0
    if not args.paths:
        missing = sum(not target_path(entry['path']).is_file() for entry in entries)
        print(f'{missing:,} downloads absent; use --list or provide exact paths to restore.')
        return 0
    failures = 0
    for relative in args.paths:
        try:
            print(f'{relative}: {restore(index[relative])}')
        except Exception as error:
            failures += 1
            print(f'{relative}: FAILED: {error}')
    return int(bool(failures))


if __name__ == '__main__':
    raise SystemExit(main())
