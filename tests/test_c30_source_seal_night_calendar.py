"""Calendar propagation at the existing Source tail-proof boundary; synthetic I/O only."""
import asyncio
from copy import deepcopy
from datetime import datetime, timedelta
import json
import socket
import sqlite3
from types import SimpleNamespace
from zoneinfo import ZoneInfo

import httpx
import pytest
from pydantic import TypeAdapter

from app.jobs.probe_krx_night_futures import fetch_live_probe, KRX_FUTURES_DAILY_URL
from app.macro.providers.base import MacroProviderResult
from app.macro.providers.krx import materialize_night_probe
from app.services.production_source_seal import _verified_night_probe_tail
from app.services.unified_snapshot_contract import digest
from app.services.night_futures import summarize_night_futures
from tests.test_c22s_source_only import rows


@pytest.fixture(autouse=True)
def no_external(monkeypatch):
    def denied(*args, **kwargs):
        raise AssertionError('C30_TEST_NO_NETWORK_DB_OR_MODEL')
    monkeypatch.setattr(socket.socket, 'connect', denied)
    monkeypatch.setattr(socket, 'getaddrinfo', denied)
    monkeypatch.setattr(sqlite3, 'connect', denied)
    monkeypatch.setattr('subprocess.Popen', denied)


def write(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value))


def fixture(root, monkeypatch, *, mode=True):
    at = datetime.fromisoformat('2026-11-20T23:10:00+00:00')
    day = at.astimezone(ZoneInfo('Asia/Seoul')).date()
    dates = [(day - timedelta(days=i)).isoformat() for i in range(7)]
    ids = ['night:KOSPI200:' + value for value in dates]
    generation = 'synthetic-c30-tail'
    descriptors = [SimpleNamespace(logical_request_id=key, provider='krx_night_futures', subject='KOSPI200',
        market='kr', consumer_role=key, endpoint_operation='fut_bydd_trd', response_binding=None,
        raw_path=f'raw/{key}/source.body', request_json=json.dumps(dict(method='GET',
            url=KRX_FUTURES_DAILY_URL + '?basDd=' + date.replace('-', '')))) for key, date in zip(ids, dates)]
    plan = SimpleNamespace(frozen_at=at, market='us', generation_id=generation, descriptors=descriptors)
    frozen = dict(scope='SELECTED_ORIGINAL_RESEARCH_V1', selected_market='us', generation_id=generation,
        frozen_at=at.isoformat(), query_kst_date=dates[0],
        candidate=dict(night_query_dates=dates, consumer_policy=dict(us_night='ORIGINAL_CURRENT_PROBE_ONLY')))
    receipts, finals = [], {}

    def send(request):
        index = len(receipts); key = ids[index]; date = request.url.params['basDd']
        response = httpx.Response(200, json={'OutBlock_1': [] if index == 0 else [
            rows(date, '야간' if index == 1 else '정규', '101.00' if index == 1 else '100.00')]})
        artifact = descriptors[index].raw_path
        path = root / 'dispatch' / artifact; path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(response.content)
        from hashlib import sha256
        raw_sha = sha256(response.content).hexdigest()
        stamp = (at + timedelta(seconds=index + 1)).isoformat()
        finals[key] = dict(status='PASS', raw_sha256=raw_sha, receipt_sha256=f'synthetic-{index}',
            attempts=[dict(status=200, started_at=stamp, finished_at=stamp, raw_sha256=raw_sha)])
        receipts.append(dict(sealed_logical_id=key, sealed_final_receipt_sha256=f'synthetic-{index}',
            artifact=artifact, artifact_sha256=raw_sha, requested_at=stamp, received_at=stamp,
            run_id=generation, provider='krx_night_futures', outcome='HTTP_RESPONSE', http_status=200,
            request=dict(method='GET', route=KRX_FUTURES_DAILY_URL, params=dict(request.url.params))))
        return response

    probe = asyncio.run(fetch_live_probe(run_date=day, observation_time=at, api_key='synthetic',
        transport=httpx.MockTransport(send)))
    probe.live_source = True
    value = TypeAdapter(MacroProviderResult).dump_python(materialize_night_probe(probe,
        history_directory=root / 'history', night_end_dates=mode), mode='json')
    phase = dict(status='CAPTURED_NOT_QUALIFIED', value=value)
    outcome = dict(logical_results=deepcopy(finals), phases=dict(night=phase),
        completed_at=(at + timedelta(seconds=7)).isoformat())
    for index, receipt in enumerate(receipts):
        write(root / f'night/probe/receipt-{index:03d}.json', receipt)
    write(root / 'night/query.json', dict(observed_at=at.isoformat()))
    write(root / 'phase-night.json', phase)
    # Only synthetic dispatch envelopes are stubbed; retained C29 proof uses the real reader.
    monkeypatch.setattr('app.services.production_source_seal.consume_bound_result', lambda **kwargs: None)
    return frozen, outcome, plan, finals


def test_new_sealed_calendar_reaches_replay_and_exact_value(tmp_path, monkeypatch):
    args = fixture(tmp_path, monkeypatch)
    import app.services.unified_sealed_context as context
    original = context.replay_night; seen = []
    def record(**kwargs):
        result = original(**kwargs)
        seen.append((kwargs['night_end_dates'], result['value_sha256']))
        return result
    monkeypatch.setattr(context, 'replay_night', record)
    tail = _verified_night_probe_tail(tmp_path, *args)
    assert len(tail) == 4 and seen == [(True, digest(args[1]['phases']['night']['value']))]


def test_legacy_sealed_calendar_keeps_false_and_exact_value(tmp_path, monkeypatch):
    args = fixture(tmp_path, monkeypatch, mode=False)
    import app.services.unified_sealed_context as context
    original = context.replay_night; seen = []
    def record(**kwargs):
        seen.append(kwargs['night_end_dates'])
        return original(**kwargs)
    monkeypatch.setattr(context, 'replay_night', record)
    assert len(_verified_night_probe_tail(tmp_path, *args)) == 4 and seen == [False]


def test_unknown_mixed_and_value_tamper_never_close_tail(tmp_path, monkeypatch):
    frozen, outcome, plan, finals = fixture(tmp_path, monkeypatch)
    original = deepcopy(outcome['phases']['night'])
    for variant in ('unknown', 'mixed', 'value'):
        phase = deepcopy(original)
        observation = phase['value']['observations'][0]
        if variant == 'unknown':
            observation['raw_payload']['night_timeframes']['calendar_contract'] = 'UNAPPROVED'
        elif variant == 'mixed':
            other = deepcopy(observation)
            other['raw_payload']['night_timeframes']['calendar_contract'] = None
            phase['value']['observations'].append(other)
        else:
            observation['value'] += 1
        outcome['phases']['night'] = phase
        write(tmp_path / 'phase-night.json', phase)
        assert _verified_night_probe_tail(tmp_path, frozen, outcome, plan, finals) == {}


def test_terminal_proof_closes_only_four_unopened_slots(tmp_path, monkeypatch):
    args = fixture(tmp_path, monkeypatch)
    frozen, outcome, plan, finals = args
    before = deepcopy(finals)
    expected = {'night:KOSPI200:' + day for day in ('2026-11-18', '2026-11-17', '2026-11-16', '2026-11-15')}
    assert set(_verified_night_probe_tail(tmp_path, *args)) == expected
    assert len(finals) == 3 and finals == before
    write(tmp_path / 'dispatch/receipts/night:KOSPI200:2026-11-18/attempt-1.start.json', {})
    assert _verified_night_probe_tail(tmp_path, *args) == {}


def test_optional_unpublished_latest_never_exposes_fallback(tmp_path, monkeypatch):
    args = fixture(tmp_path, monkeypatch)
    value = args[1]['phases']['night']['value']
    flat = [{**row, **row['raw_payload']} for row in value['observations']]
    assert value['telemetry']['expected_reference_date'] == '2026-11-21'
    assert all(not row['reference_date_match'] for row in flat)
    assert not summarize_night_futures({'observations': flat}).items
    assert len(_verified_night_probe_tail(tmp_path, *args)) == 4


def test_kst_query_day_and_receipt_time_are_not_relabeled(tmp_path, monkeypatch):
    args = fixture(tmp_path, monkeypatch)
    frozen, outcome, plan, finals = args
    assert frozen['frozen_at'].startswith('2026-11-20') and frozen['query_kst_date'] == '2026-11-21'
    assert len(_verified_night_probe_tail(tmp_path, *args)) == 4
    path = tmp_path / 'night/probe/receipt-000.json'
    receipt = json.loads(path.read_bytes())
    receipt['received_at'] = '2026-11-22T00:00:00+00:00'
    write(path, receipt)
    assert _verified_night_probe_tail(tmp_path, *args) == {}
