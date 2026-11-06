"""Capture storage boundary only: SQL compatibility and immutable file receipts.

This module does not issue registration, Provider or financial authority.
"""
from datetime import datetime
import json
import os
from pathlib import Path
import re

from app.services.vnext_research_store import digest, encoded, plain

CONTRACT = 'public-file-capture-archive-v1'


def find_capture(store, run_id, provider, key):
    if isinstance(store, FileCaptureArchive):
        return store.find_capture(run_id, provider, key)
    with store.connect() as c:
        return c.execute('SELECT raw_path,receipt_json FROM source_capture WHERE run_id=? AND provider=? AND request_key=?',
            (run_id, provider, key)).fetchone()


def list_captures(store, run_id, provider):
    if isinstance(store, FileCaptureArchive):
        return store.list_captures(run_id, provider)
    with store.connect() as c:
        return c.execute('SELECT raw_path,receipt_json FROM source_capture WHERE run_id=? AND provider=?',
            (run_id, provider)).fetchall()


def run_started_at(store, run_id):
    if isinstance(store, FileCaptureArchive):
        return store.run_started_at(run_id)
    with store.connect() as c:
        row=c.execute('SELECT started_at FROM research_run WHERE run_id=?',(run_id,)).fetchone()
    return row[0] if row else None


class FileCaptureArchive:
    """Default-off, single-run public source storage; no SQL or grant restoration."""
    def __init__(self, root, *, run_id, started_at, securities, code_pins, enabled=False):
        if enabled is not True:
            raise ValueError('file_capture_explicit_enable_required')
        root=plain(root)
        if (not re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9_-]{0,79}',run_id)
                or datetime.fromisoformat(started_at).utcoffset() is None
                or not securities or len({s['ticker'] for s in securities})!=len(securities)):
            raise ValueError('file_capture_run_identity_required')
        root.mkdir(mode=0o700,parents=True,exist_ok=False)
        self.path=root/'archive.json'
        self._manifest=dict(contract=CONTRACT,run_id=run_id,started_at=started_at,
            securities=securities,code_pins=code_pins,authority_issued=False)
        self._write(self.path,encoded(self._manifest))
        self._manifest_sha=digest(self.path.read_bytes())
        self.read_only=False
        (root/'captures').mkdir(mode=0o700)
        (root/'raw').mkdir(mode=0o700)

    @classmethod
    def open_read_only(cls, root, *, expected_manifest_sha256):
        obj=object.__new__(cls);root=plain(root);obj.path=root/'archive.json'
        obj._manifest=json.loads(obj._read(obj.path))
        if (obj._manifest.get('contract')!=CONTRACT
                or digest(obj._read(obj.path))!=expected_manifest_sha256):
            raise ValueError('file_capture_manifest_binding')
        obj._manifest_sha=expected_manifest_sha256;obj.read_only=True
        obj._check(obj._manifest['run_id'])
        return obj

    @property
    def manifest_sha256(self):return self._manifest_sha

    @staticmethod
    def _read(path):
        path=plain(path);s=path.stat()
        if not path.is_file() or s.st_nlink!=1 or s.st_size>32*1024**2:
            raise ValueError('file_capture_artifact_identity_or_size')
        return path.read_bytes()

    @staticmethod
    def _write(path, raw):
        path=plain(path)
        fd=os.open(path,os.O_WRONLY|os.O_CREAT|os.O_EXCL|os.O_NOFOLLOW,0o600)
        with os.fdopen(fd,'wb') as f:f.write(raw);f.flush();os.fsync(f.fileno())

    def _check(self, run_id):
        if run_id!=self._manifest['run_id'] or digest(self._read(self.path))!=self._manifest_sha:
            raise ValueError('file_capture_run_or_manifest_changed')
        for path,sha in self._manifest['code_pins'].items():
            if digest(self._read(Path(path)))!=sha:
                raise ValueError('file_capture_code_changed')

    def run_started_at(self, run_id):
        self._check(run_id);return self._manifest['started_at']

    def identities(self):
        self._check(self._manifest['run_id'])
        return json.loads(encoded(self._manifest['securities']))

    def find_capture(self, run_id, provider, key):
        self._check(run_id)
        name=digest([run_id,provider,key])
        p=self.path.parent/'captures'/name
        if not p.exists():return None
        item=json.loads(self._read(p))
        if (item['run_id']!=run_id or item['provider']!=provider or item['key']!=key
                or not re.fullmatch('[a-f0-9]{64}',item['raw_sha256'])):
            raise ValueError('file_capture_receipt_scope')
        rawpath=self.path.parent/'raw'/item['raw_sha256']
        if digest(self._read(rawpath))!=item['raw_sha256']:
            raise ValueError('file_capture_raw_changed')
        return str(rawpath),encoded(item['receipt']).decode()

    def list_captures(self, run_id, provider):
        self._check(run_id);rows=[]
        for p in sorted((self.path.parent/'captures').iterdir()):
            if not re.fullmatch('[a-f0-9]{64}',p.name):
                raise ValueError('file_capture_unexpected_artifact')
            item=json.loads(self._read(p))
            if item['provider']==provider:
                rows.append(self.find_capture(run_id,provider,item['key']))
        return rows

    def capture(self, run_id, provider, key, raw, receipt):
        self._check(run_id)
        if self.read_only or (self.path.parent/'capture-seal.json').exists():
            raise ValueError('file_capture_read_only')
        if (not isinstance(raw,bytes) or len(raw)>32*1024**2
                or provider not in {'Finnhub','KIS','Kiwoom'}
                or receipt.get('run_id')!=run_id or receipt.get('provider')!=provider
                or receipt.get('raw_sha256')!=digest(raw)
                or receipt.get('raw_birth')!='CURRENT_HTTP' or receipt.get('status')!=200
                or datetime.fromisoformat(receipt['started_at']) < datetime.fromisoformat(self._manifest['started_at'])
                or datetime.fromisoformat(receipt['captured_at']) < datetime.fromisoformat(receipt['started_at'])):
            raise ValueError('file_capture_original_receipt_required')
        old=self.find_capture(run_id,provider,key)
        if old:
            if self._read(Path(old[0]))!=raw or json.loads(old[1])!=receipt:
                raise ValueError('file_capture_replacement_denied')
            return digest(raw)
        sha=digest(raw);p=self.path.parent/'raw'/sha
        if p.exists():
            if self._read(p)!=raw:raise ValueError('file_capture_CAS_changed')
        else:self._write(p,raw)
        self._write(self.path.parent/'captures'/digest([run_id,provider,key]),
            encoded(dict(run_id=run_id,provider=provider,key=key,raw_sha256=sha,receipt=receipt)))
        return sha

    def _inventory(self):
        self._check(self._manifest['run_id'])
        return {str(p.relative_to(self.path.parent)):digest(self._read(p))
            for directory in ('captures','raw') for p in sorted((self.path.parent/directory).iterdir())}

    def seal_captures(self):
        if self.read_only:raise ValueError('file_capture_read_only')
        value=dict(contract='public-file-capture-seal-v1',manifest_sha256=self._manifest_sha,
            files=self._inventory())
        raw=encoded(value);self._write(self.path.parent/'capture-seal.json',raw)
        return digest(raw)

    @classmethod
    def open_sealed_read_only(cls,root,*,expected_manifest_sha256,expected_capture_seal_sha256):
        obj=cls.open_read_only(root,expected_manifest_sha256=expected_manifest_sha256)
        raw=obj._read(obj.path.parent/'capture-seal.json')
        seal=json.loads(raw)
        if (digest(raw)!=expected_capture_seal_sha256 or seal.get('contract')!='public-file-capture-seal-v1'
                or seal['manifest_sha256']!=expected_manifest_sha256 or seal['files']!=obj._inventory()):
            raise ValueError('file_capture_seal_or_inventory_changed')
        return obj
