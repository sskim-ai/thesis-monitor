"""Network-free REV9 preparation and replay; no acquisition or model route."""
import argparse
import hashlib
import json
from pathlib import Path
import socket
import zipfile

from app.services.unified_run_artifacts import durable_bytes, durable_json

REV8_SHA = 'eab400412052f9a33fbc8a2fbcff867590078eac96ff7ab4b02a984013fed6e1'


def network_guard():
    counts = {'network_attempts': 0}
    def deny(*args, **kwargs):
        counts['network_attempts'] += 1
        raise RuntimeError('REV9_OFFLINE_NETWORK_FORBIDDEN')
    socket.socket.connect = socket.socket.connect_ex = socket.getaddrinfo = deny
    return counts


def prepare(bundle, output):
    raw = bundle.read_bytes()
    if hashlib.sha256(raw).hexdigest() != REV8_SHA:
        raise ValueError('sealed_REV8_zip_identity_mismatch')
    with zipfile.ZipFile(bundle) as archive:
        manifest = json.loads(archive.read('bundle-manifest.json'))
        if len(manifest) != 3486 or set(archive.namelist()) != set(manifest) | {'bundle-manifest.json'}:
            raise ValueError('sealed_REV8_manifest_set_mismatch')
        for name, entry in manifest.items():
            path = Path(name)
            if path.is_absolute() or '..' in path.parts:
                raise ValueError('sealed_archive_path_invalid')
            data = archive.read(name)
            if hashlib.sha256(data).hexdigest() != entry['sha256'] or len(data) != entry['bytes']:
                raise ValueError('sealed_REV8_artifact_mismatch:' + name)
        for name in archive.namelist():
            durable_bytes(output / 'input' / name, archive.read(name), exclusive=True)
    durable_json(output / 'REV8-identity.json', {'zip_sha256': REV8_SHA,
        'manifest_entries_verified': len(manifest), 'missing': 0, 'hash_mismatch': 0,
        'extra': 0, 'network_calls': 0}, exclusive=True)
    print(json.dumps({'REV8_verified': len(manifest), 'network_calls': 0}), flush=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('mode', choices=['prepare'])
    parser.add_argument('--bundle', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    network_guard()
    prepare(args.bundle, args.output)


if __name__ == '__main__':
    main()
