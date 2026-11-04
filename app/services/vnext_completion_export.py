"""Typed, read-side completion export. This module cannot invoke a model/send.

Host completion, journal health and publication are separate facts. The exported
receipt is custody, not a replacement for the original research ReviewOwner.
"""
import base64
import fcntl
import json
import os
from pathlib import Path
import stat

from app.services.vnext_research_store import digest, encoded, plain

CONTRACT = 'no-send-completion-export-v1'
PREFIX = 'vnext-runtime-v1:job:'


def typed_records(rows):
    records = []
    warnings = []
    seen = set()
    for key, raw in sorted(rows):
        if not isinstance(key, str) or key in seen or not isinstance(raw, (str, bytes)):
            raise ValueError('completion_export_row_identity')
        seen.add(key)
        data = raw.encode('utf-8') if isinstance(raw, str) else raw
        row = dict(key=key, raw_base64=base64.b64encode(data).decode(), raw_sha256=digest(data))
        if key.startswith(PREFIX):
            row['kind'] = 'JOB_JSON'
            try:
                value = json.loads(data)
                if (not isinstance(value, dict) or value.get('status') != 'COMMITTED'
                        or not isinstance(value.get('request_sha256'), str) or 'result' not in value):
                    raise ValueError('invalid_job_shape')
                row['job'] = value
            except (ValueError, UnicodeError):
                row['kind'] = 'MALFORMED_JOB'
                warnings.append(dict(key=key, code='MALFORMED_JOB_PRESERVED'))
        else:
            row['kind'] = 'PLAIN_METADATA'
        records.append(row)
    return dict(contract=CONTRACT, records=records, warnings=warnings)


def completion_payload(*, host, rows, outer_exit=None):
    typed = typed_records(rows)
    jobs = {r['key']: r['job'] for r in typed['records'] if r['kind'] == 'JOB_JSON'}
    expected = PREFIX + str(host.get('attempt', '')) + '-end'
    end = jobs.get(expected)
    response = host.get('response')
    child = jobs.get(PREFIX + str(host.get('attempt', '')) + '-child')
    returned = jobs.get(PREFIX + str(host.get('attempt', '')) + '-response')
    bound = bool(end and child and returned and isinstance(child['result'], dict)
        and all(r['request_sha256'] == host.get('request_sha256') for r in (end,child,returned))
        and end['result'] == host and returned['result'] == response
        and child['result'].get('pid') == host.get('child_pid') and child['result'].get('state') == 'RUNNING')
    message = response.get('message') if isinstance(response, dict) else None
    valid_message = (isinstance(message, str) and response.get('send') is False
                     and digest(message) == response.get('message_sha256'))
    ready = bool(bound and host.get('state') == 'COMPLETED_NO_SEND'
                 and host.get('exit') == 0 and valid_message and not typed['warnings'])
    host_records = [r for r in typed['records'] if r['key'].startswith(PREFIX + str(host.get('attempt', '')) + '-')]
    receipt = dict(contract=CONTRACT, state='OUTBOX_NO_SEND_READY' if ready else 'COMPLETION_EXPORT_PARTIAL',
        host_state=host.get('state'), child_exit=host.get('exit'), outer_export_exit=outer_exit,
        model_state=response.get('model_state') if isinstance(response, dict) else None,
        host_sha256=digest(host), journal_sha256=digest(host_records), host_journal_bound=bound,
        model_reinvoked=False, original_owner_revalidated=False, delivery='NO_SEND', send=False,
        warnings=typed['warnings'], reason=None if ready else 'REQUIRES_POSTPROCESS',
        message_sha256=digest(message) if ready else None)
    return dict(receipt=receipt, typed_records=typed, publication_records=host_records, message=message if ready else None)


def publish_completion(destination, *, host, rows, outer_exit=None):
    """Atomic directory publication; killed exporters resume only these reads.

    A stable host key and lock make duplicates byte-identical. Incomplete staging
    remains recoverable and can never be mistaken for a published receipt.
    """
    payload = completion_payload(host=host, rows=rows, outer_exit=outer_exit)
    root = plain(destination)
    root.mkdir(parents=True, exist_ok=True)
    key = digest(host)
    if payload['receipt']['state'] != 'OUTBOX_NO_SEND_READY':
        key += '-partial-' + digest(payload)[:16]
    final = root / key
    lock = os.open(plain(root / (key + '.lock')), os.O_CREAT | os.O_RDWR | os.O_NOFOLLOW, 0o600)
    try:
        info = os.fstat(lock)
        if not stat.S_ISREG(info.st_mode) or info.st_nlink != 1:
            raise ValueError('completion_export_lock_alias')
        fcntl.flock(lock, fcntl.LOCK_EX)
        files = {'receipt.json': encoded(payload['receipt']), 'records.json': encoded(payload['publication_records'])}
        if payload['message'] is not None:
            files['message.txt'] = payload['message'].encode('utf-8')
        if final.exists():
            plain(final)
            if set(p.name for p in final.iterdir()) != set(files):
                raise ValueError('completion_export_conflict')
            for name, data in files.items():
                p = plain(final / name)
                if p.stat().st_nlink != 1 or p.read_bytes() != data:
                    raise ValueError('completion_export_conflict')
        else:
            stage = plain(root / (key + '.pending'))
            stage.mkdir(exist_ok=True)
            if set(p.name for p in stage.iterdir()) - set(files):
                raise ValueError('completion_export_staging_conflict')
            for name, data in files.items():
                p = plain(stage / name)
                if p.exists():
                    old = p.read_bytes()
                    if p.stat().st_nlink != 1 or not data.startswith(old):
                        raise ValueError('completion_export_staging_conflict')
                else:
                    old = b''
                fd = os.open(p, os.O_CREAT | os.O_WRONLY | os.O_APPEND | os.O_NOFOLLOW, 0o600)
                try:
                    if os.fstat(fd).st_nlink != 1:
                        raise ValueError('completion_export_staging_alias')
                    with os.fdopen(fd, 'ab', closefd=False) as stream:
                        stream.write(data[len(old):]); stream.flush(); os.fsync(fd)
                finally:
                    os.close(fd)
            dfd = os.open(stage, os.O_RDONLY)
            try: os.fsync(dfd)
            finally: os.close(dfd)
            os.rename(stage, final)
            dfd = os.open(root, os.O_RDONLY)
            try: os.fsync(dfd)
            finally: os.close(dfd)
        return dict(payload['receipt'], path=str(final), export_only=True)
    finally:
        os.close(lock)
