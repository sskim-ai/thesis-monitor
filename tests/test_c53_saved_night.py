"""Audit recorded rows and broker observations without changing source evidence."""
from datetime import datetime, timedelta
import hashlib
import json
import socket
import sqlite3

import pytest

from app.jobs.probe_krx_night_futures import KRX_FUTURES_DAILY_URL
from app.services.unified_snapshot_contract import digest, encoded
from scripts.c53_inspect_saved_night import inspect
from tests.test_c52_saved_night import contents, write
from tests.test_krx_night_futures_probe import _row


@pytest.fixture(autouse=True)
def no_external(monkeypatch):
    def denied(*args, **kwargs):
        raise AssertionError('C53_DIAGNOSTIC_EXTERNAL_IO_DENIED')
    monkeypatch.setattr(socket.socket, 'connect', denied)
    monkeypatch.setattr(socket, 'getaddrinfo', denied)
    monkeypatch.setattr(sqlite3, 'connect', denied)
    monkeypatch.setattr('subprocess.Popen', denied)


def row(day, session, close, *, change=None, settlement=None):
    value = _row('KOSPI 200 선물', session, 'A016C000',
        '코스피200 F 202612' + (' 야간' if session == '야간' else ''), close, day, change)
    value.update(TDD_OPNPRC='769.90', TDD_HGPRC='769.95', TDD_LWPRC='731.35',
                 ACC_TRDVOL='44229', SETL_PRC=settlement)
    return value


def saved(root, latest, *, day_close='778.10', settlement='778.10'):
    at = datetime.fromisoformat('2026-11-25T08:10:00+09:00')
    generation = 'c52-synthetic-source'
    descriptors = []
    payloads = [latest,
        [row('20261124', '정규', day_close, settlement=settlement),
         row('20261124', '야간', '777.95', change='51.30')],
        [row('20261123', '정규', '726.65', settlement='726.65')]]
    for index, rows in enumerate(payloads):
        day = at.date() - timedelta(days=index)
        key = 'night:KOSPI200:' + day.isoformat()
        artifact = 'raw/' + key + '/source.body'
        descriptors.append(dict(logical_request_id=key, provider='krx_night_futures',
            consumer_role=key, raw_path=artifact))
        body = encoded({'OutBlock_1': rows})
        path = root / 'dispatch' / artifact
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(body)
        sha = hashlib.sha256(body).hexdigest()
        final = dict(status='PASS', raw_sha256=sha, logical_request_id=key)
        final['receipt_sha256'] = digest(final)
        write(root / 'dispatch/receipts' / key / 'final.json', final)
        stamp = (at + timedelta(seconds=index + 1)).isoformat()
        write(root / f'night/probe/receipt-{index+1:03d}.json', dict(run_id=generation,
            provider='krx_night_futures', outcome='HTTP_RESPONSE', http_status=200,
            request=dict(method='GET', route=KRX_FUTURES_DAILY_URL, params={'basDd': day.strftime('%Y%m%d')}),
            artifact=artifact, artifact_sha256=sha, requested_at=stamp, received_at=stamp,
            sealed_logical_id=key, sealed_final_receipt_sha256=final['receipt_sha256']))
    write(root / 'production-frozen-source-plan.json', dict(generation_id=generation,
        frozen_at=at.isoformat(), plan={'descriptors': descriptors}))
    return root


def test_absent_latest_row_is_distinct_from_stale_selected_pair(tmp_path):
    root = saved(tmp_path / 'source', [])
    before = contents(root)
    report = inspect(root, maturity='202612')
    assert report['status'] == 'SAVED_NIGHT_AUDIT_COMPLETE', report
    assert report['queries'][0]['raw_row_count'] == 0
    assert report['finding']['diagnosis'] == 'EXPECTED_TARGET_NIGHT_ABSENT'
    assert report['finding']['stale_fallback_selected'] is True
    assert report['current_parser']['source_date'] == '2026-11-24'
    assert report['financial_http_calls'] == report['model_calls'] == report['production_db_calls'] == 0
    assert contents(root) == before


def test_present_latest_row_selected_by_current_parser(tmp_path):
    root = saved(tmp_path / 'source', [row('20261125', '야간', '742.60', change='-35.50')])
    report = inspect(root, maturity='2026-12')
    assert report['finding']['diagnosis'] == 'EXPECTED_TARGET_SELECTED'
    assert report['finding']['stale_fallback_selected'] is False
    comparison = report['same_contract_comparisons'][0]
    assert comparison['provider_matches_day_close'] is True
    assert comparison['day_settlement'] == 778.10


def test_broker_observation_never_fills_missing_latest_provider_row(tmp_path):
    root = saved(tmp_path / 'source', [])
    reference = dict(source_kind='USER_BROKER_SCREENSHOT', broker='KIWOOM', product='KOSPI200',
        maturity='2026-12', chart_date='2026-11-24', open=769.90, high=769.95, low=731.35,
        close=742.60, volume=44229, previous_night_close=777.95, header_change_point=-35.50)
    report = inspect(root, maturity='202612', broker_reference=reference)
    comparison = report['broker_comparison']
    assert report['finding']['diagnosis'] == 'EXPECTED_TARGET_NIGHT_ABSENT'
    assert report['current_parser']['observations'][0]['night_close'] == 777.95
    assert all(not row['close_matches'] for row in comparison['saved_night_comparisons'])
    assert comparison['prior_night_change_pct'] == pytest.approx(-4.54399383)
    assert comparison['header_implied_reference_price'] == 778.10
    assert comparison['header_reference_kind'] == 'UNCONFIRMED'
    assert comparison['provider_dates_modified'] is False


def test_raw_target_filtered_for_missing_close_is_visible(tmp_path):
    root = saved(tmp_path / 'source', [row('20261125', '야간', '-')])
    report = inspect(root, maturity='202612')
    assert report['finding']['diagnosis'] == 'EXPECTED_QUERY_TARGET_ROWS_FILTERED_OR_DATE_MISMATCH'
    assert report['queries'][0]['target_rows'][0]['parser_reasons'] == ['CLOSE_NOT_NUMERIC']


def test_unexplained_provider_change_conflict_retains_raw_row_and_rejection(tmp_path):
    root = saved(tmp_path / 'source', [row('20261125', '야간', '742.60', change='-99.00')])
    report = inspect(root, maturity='202612')
    assert report['finding']['diagnosis'] == 'EXPECTED_TARGET_PRESENT_PARSER_NOT_SELECTED'
    assert report['finding']['stale_fallback_selected'] is True
    comparison = report['same_contract_comparisons'][0]
    assert comparison['provider_matches_day_close'] is False
    assert comparison['provider_matches_day_settlement'] is False
    assert report['current_parser']['product_statuses'][0]['rejection_reason'] == 'provider_change_conflict'


def test_settlement_comparison_is_separate_from_legacy_close_only_check(tmp_path):
    root = saved(tmp_path / 'source', [row('20261125', '야간', '742.60', change='-35.50')],
                 day_close='778.20', settlement='778.10')
    report = inspect(root, maturity='202612')
    comparison = report['same_contract_comparisons'][0]
    assert comparison['day_close'] == 778.20
    assert comparison['provider_matches_day_close'] is False
    assert comparison['provider_matches_day_settlement'] is True
    assert comparison['legacy_close_only_check_would_reject'] is True


def test_modified_saved_body_is_not_used(tmp_path):
    root = saved(tmp_path / 'source', [])
    (root / 'dispatch/raw/night:KOSPI200:2026-11-25/source.body').write_bytes(b'{}')
    report = inspect(root, maturity='202612')
    assert report['status'] == 'FAILED'
    assert report['failure']['stable_error_code'] == 'night_saved_body_hash_mismatch'
    assert 'current_parser' not in report
