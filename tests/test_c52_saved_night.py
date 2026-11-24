"""Saved-response diagnostics never request missing data or change original input."""
from datetime import datetime, timedelta
import hashlib
import json
import socket
import sqlite3

import pytest

from app.jobs.probe_krx_night_futures import KRX_FUTURES_DAILY_URL
from app.services.unified_snapshot_contract import digest, encoded
from scripts import c52_inspect_saved_night as diagnostic
from tests.test_krx_night_futures_probe import _row


@pytest.fixture(autouse=True)
def no_external(monkeypatch):
    def denied(*args, **kwargs):
        raise AssertionError('C52_DIAGNOSTIC_EXTERNAL_IO_DENIED')
    monkeypatch.setattr(socket.socket, 'connect', denied)
    monkeypatch.setattr(socket, 'getaddrinfo', denied)
    monkeypatch.setattr(sqlite3, 'connect', denied)
    monkeypatch.setattr('subprocess.Popen', denied)


def write(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(encoded(value))


def saved(root, *, prefix=5):
    at = datetime.fromisoformat('2026-11-24T08:10:00+09:00')
    generation = 'c46-synthetic-source'
    descriptors = []
    for index in range(7):
        day = at.date()-timedelta(days=index)
        key = 'night:KOSPI200:'+day.isoformat()
        artifact = 'raw/'+key+'/source.body'
        descriptors.append(dict(logical_request_id=key, provider='krx_night_futures',
            consumer_role=key, raw_path=artifact))
        if index >= prefix:
            continue
        rows = []
        if index in (3, 4):
            is_night = index == 3
            row = _row('KOSPI 200 선물', '야간' if is_night else '정규', 'A016C000',
                '코스피200 F 202612'+(' 야간' if is_night else ''), '101' if is_night else '100',
                day.strftime('%Y%m%d'), '1' if is_night else None)
            row.update(TDD_OPNPRC='100', TDD_HGPRC='102', TDD_LWPRC='99')
            rows.append(row)
        body = encoded({'OutBlock_1': rows})
        path = root/'dispatch'/artifact
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(body)
        sha = hashlib.sha256(body).hexdigest()
        final = dict(status='PASS', raw_sha256=sha, logical_request_id=key)
        final['receipt_sha256'] = digest(final)
        write(root/'dispatch/receipts'/key/'final.json', final)
        stamp = (at+timedelta(seconds=index+1)).isoformat()
        write(root/f'night/probe/receipt-{index+1:03d}.json', dict(run_id=generation,
            provider='krx_night_futures', outcome='HTTP_RESPONSE', http_status=200,
            request=dict(method='GET', route=KRX_FUTURES_DAILY_URL, params={'basDd':day.strftime('%Y%m%d')}),
            artifact=artifact, artifact_sha256=sha, requested_at=stamp, received_at=stamp,
            sealed_logical_id=key, sealed_final_receipt_sha256=final['receipt_sha256']))
    write(root/'production-frozen-source-plan.json', dict(generation_id=generation,
        frozen_at=at.isoformat(), plan={'descriptors':descriptors}))
    write(root/'phase-night.json', dict(status='FAILED', error_class='ValueError'))
    return root


def contents(root):
    return {str(p.relative_to(root)):p.read_bytes() for p in root.rglob('*') if p.is_file()}


def test_five_saved_responses_replay_without_rewriting_history(tmp_path):
    root = saved(tmp_path/'source')
    before = contents(root)
    result = diagnostic.inspect(root)
    assert result['status'] == 'CURRENT_CODE_REPLAY_COMPLETE', result
    assert result['recorded_response_count'] == 5
    assert result['financial_http_calls'] == result['model_calls'] == result['production_db_calls'] == 0
    assert not result['original_failure_cause_confirmed']
    assert result['original_phase'] == dict(status='FAILED', error_class='ValueError')
    replay = result['stages']['replay_current_probe']
    assert replay['recorded_responses_consumed'] == 5
    assert replay['value']['session_freshness'] == 'stale'
    rows = result['stages']['materialize_current_daily_weekly_monthly']['observations']
    assert rows[0]['value'] == 101 and rows[0]['previous_value'] == 100
    assert rows[0]['session_date'] == '2026-11-21' and rows[0]['reference_date'] == '2026-11-20'
    assert contents(root) == before


def test_missing_next_response_is_not_synthesized_or_recollected(tmp_path):
    root = saved(tmp_path/'source', prefix=4)
    result = diagnostic.inspect(root)
    assert result['status'] == 'INCOMPLETE_SAVED_CAPTURE'
    assert result['stages']['replay_current_probe'] == dict(status='RECORDED_PREFIX_EXHAUSTED',
        recorded_responses_consumed=4, unrecorded_query_date='20261120')
    assert 'materialize_current_daily_weekly_monthly' not in result['stages']


def test_modified_raw_body_is_reported_before_parsing(tmp_path):
    root = saved(tmp_path/'source')
    (root/'dispatch/raw/night:KOSPI200:2026-11-24/source.body').write_bytes(b'{}')
    result = diagnostic.inspect(root)
    assert result['status'] == 'FAILED'
    assert result['stages']['read_saved_capture']['failure']['stable_error_code'] == 'night_saved_body_hash_mismatch'
    assert 'parse_recorded_subset' not in result['stages']


@pytest.mark.parametrize('message,expected', [
    ('same_contract_weekly_constituents_unavailable', 'same_contract_weekly_constituents_unavailable'),
    ('request AUTH_KEY=secret-value https://private.example', 'ValueError'),
])
def test_failure_reports_code_location_without_arbitrary_error_text(tmp_path, monkeypatch, message, expected):
    root = saved(tmp_path/'source')
    def fail(*args, **kwargs):
        raise ValueError(message)
    monkeypatch.setattr(diagnostic, 'materialize_night_probe', fail)
    result = diagnostic.inspect(root)
    failure = result['stages']['materialize_current_daily_weekly_monthly']['failure']
    assert failure['stable_error_code'] == expected
    assert 'secret-value' not in json.dumps(result)
    assert not result['original_failure_cause_confirmed']
