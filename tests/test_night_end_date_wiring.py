"""Current end-date DWM wiring and exact historical replay; synthetic wire only."""
import asyncio
from copy import deepcopy
from datetime import date, datetime
import json
import socket

import httpx
import pytest
from pydantic import TypeAdapter

from app.jobs.probe_krx_night_futures import fetch_live_probe
from app.macro.providers.base import MacroProviderResult
from app.macro.providers.krx import KrxNightFuturesProvider, materialize_night_probe, sealed_night_end_date_history
from app.services.krx_night_history_service import persist_krx_response
from app.services.market_numeric_claim_service import numeric_catalog
from app.services.night_futures import summarize_night_futures, night_futures_context_row
from app.services.night_futures_session_mapping_service import KST, resolve_us_morning_night_reference_date
from app.services.night_futures_visibility_service import night_futures_user_facing_visibility
from app.services.official_night_market_eligibility_service import night_market_eligibility
from app.services.unified_sealed_context import replay_night
from app.services.unified_snapshot_contract import digest, encoded
from tests.test_krx_night_futures_probe import _row
from tests.test_r9_rev8_night_bridge import night


@pytest.fixture(autouse=True)
def no_external(monkeypatch):
    def denied(*args, **kwargs):
        raise AssertionError('NIGHT_TEST_EXTERNAL_IO_DENIED')
    monkeypatch.setattr(socket.socket, 'connect', denied)
    monkeypatch.setattr(socket, 'getaddrinfo', denied)


def probe_at(at, *, missing_latest=False):
    at = datetime.fromisoformat(at)
    def reply(request):
        day = request.url.params['basDd']
        rows = []
        if not (missing_latest and day == '20261121'):
            for session, close in (('정규', '100'), ('야간', '101')):
                row = _row('KOSPI 200 선물', session, 'A016C000',
                    '코스피200 F 202612' + (' 야간' if session == '야간' else ''),
                    close, day, '1' if session == '야간' else None)
                row.update(TDD_OPNPRC='100', TDD_HGPRC='102', TDD_LWPRC='99')
                rows.append(row)
        return httpx.Response(200, content=encoded({'OutBlock_1': rows}), request=request)
    probe = asyncio.run(fetch_live_probe(run_date=at.date(), observation_time=at,
        api_key='synthetic', transport=httpx.MockTransport(reply)))
    probe.live_source = True  # Fixture-owned mock bytes, never real acquisition.
    return probe


def collect(tmp_path, monkeypatch, at, **kwargs):
    probe = probe_at(at, **kwargs)
    async def fetch(**ignored):
        return probe
    monkeypatch.setattr('app.macro.providers.krx.fetch_live_probe', fetch)
    provider = KrxNightFuturesProvider(history_directory=tmp_path)
    result = asyncio.run(provider._collect(datetime.fromisoformat(at)))
    return TypeAdapter(MacroProviderResult).dump_python(result, mode='json')


def summary(value):
    return summarize_night_futures({'observations': [
        {**row, **row['raw_payload']} for row in value['observations']
    ]})


@pytest.mark.parametrize('at,end,baseline', [
    ('2026-11-21T08:10:00+09:00', '2026-11-21', '2026-11-20'),
    ('2026-11-23T08:10:00+09:00', '2026-11-21', '2026-11-20'),
    ('2026-11-24T08:10:00+09:00', '2026-11-24', '2026-11-23'),
    ('2026-11-21T05:59:59+09:00', '2026-11-20', '2026-11-19'),
])
def test_official_end_date_is_not_changed_to_publication_fallback(at, end, baseline):
    mapping = resolve_us_morning_night_reference_date(datetime.fromisoformat(at))
    assert str(mapping.expected_reference_date) == end
    assert str(mapping.regular_reference_date) == baseline


def test_friday_end_date_week_stays_in_progress_until_saturday(tmp_path, monkeypatch):
    value = collect(tmp_path, monkeypatch, '2026-11-20T08:10:00+09:00')
    frames = value['observations'][0]['raw_payload']['night_timeframes']
    assert frames['calendar_contract'] == 'KRX_NIGHT_END_DATE_V1'
    assert frames['weekly']['status'] == 'IN_PROGRESS'
    assert frames['weekly']['future_expected_dates'] == ['2026-11-21']
    assert frames['weekly']['return_pct'] is None


def test_saturday_end_date_closes_week_without_filling_missing_history(tmp_path, monkeypatch):
    value = collect(tmp_path, monkeypatch, '2026-11-21T08:10:00+09:00')
    frames = value['observations'][0]['raw_payload']['night_timeframes']
    assert frames['daily']['status'] == 'FINAL' and frames['daily']['quality'] == 'VALID'
    assert frames['weekly']['status'] == 'FINAL' and frames['weekly']['quality'] == 'PARTIAL_SAFE'
    assert frames['weekly']['missing_dates'] and frames['weekly']['return_pct'] is None
    assert frames['monthly']['status'] == 'IN_PROGRESS'


def test_stale_fallback_is_not_promoted_by_calendar_fix(tmp_path, monkeypatch):
    value = collect(tmp_path, monkeypatch, '2026-11-21T08:10:00+09:00', missing_latest=True)
    assert value['telemetry']['expected_reference_date'] == '2026-11-21'
    row = value['observations'][0]
    assert row['raw_payload']['session_date'] == '2026-11-20'
    assert not row['raw_payload']['reference_date_match']
    assert not summary(value).items


def test_before_finality_never_becomes_user_visible(tmp_path, monkeypatch):
    value = collect(tmp_path, monkeypatch, '2026-11-21T05:59:59+09:00')
    assert not value['telemetry']['finality_valid'] and not summary(value).items


def test_legacy_calendar_is_explicitly_preserved():
    value = {'observations': [{'raw_payload': {'night_timeframes': {'calendar_contract': None}}}]}
    assert sealed_night_end_date_history(value) is False
    assert sealed_night_end_date_history({'observations': []}) is False
    value['observations'][0]['raw_payload']['night_timeframes']['calendar_contract'] = 'KRX_NIGHT_END_DATE_V1'
    assert sealed_night_end_date_history(value) is True


def test_mixed_or_unknown_sealed_calendar_rejected():
    for calendars in ((None, 'KRX_NIGHT_END_DATE_V1'), ('UNAPPROVED',)):
        value = {'observations': [{'raw_payload': {'night_timeframes': {'calendar_contract': c}}} for c in calendars]}
        with pytest.raises(ValueError, match='night_sealed_timeframe_calendar_mixed_or_unknown'):
            sealed_night_end_date_history(value)


def test_current_eligible_row_crosses_visibility_and_exact_numeric_renderer(tmp_path, monkeypatch):
    value = collect(tmp_path, monkeypatch, '2026-11-21T08:10:00+09:00')
    row = json.loads(json.dumps(night_futures_context_row(summary(value).items[0]), default=str))
    gate = night_market_eligibility(row, market='us', assessment_date='2026-11-21', completed_session_date='2026-11-20')
    assert gate['eligible'], gate
    source = dict(session=dict(market='us', assessment_date='2026-11-21', latest_completed_regular_session_date='2026-11-20'),
        night_futures=[row], fact_catalog=[dict(fact_id=row['fact_id'], fact_type='night_futures',
            as_of_date=row['session_date'], fields=row)])
    assert night_futures_user_facing_visibility('us', context=source).visible
    catalog = numeric_catalog(source, market='us', assessment_date='2026-11-21', eligible_refs=[row['fact_id']])
    assert any(c['claim_type'] == 'OFFICIAL_NIGHT' for c in catalog['claims'])
    changed = deepcopy(row);changed['contract_maturity'] = '2027-03'
    assert not night_market_eligibility(changed, market='us', assessment_date='2026-11-21', completed_session_date='2026-11-20')['eligible']


def test_end_date_replay_accepts_only_its_frozen_output(night, tmp_path):
    storage = tmp_path / 'new-end-date-history'
    def reply(request):
        day = request.url.params['basDd']
        name = datetime.strptime(day, '%Y%m%d').date().isoformat() + '.json'
        return httpx.Response(200, content=night['bodies'][name], request=request)
    probe = asyncio.run(fetch_live_probe(run_date=night['observed_at'].astimezone(KST).date(),
        observation_time=night['observed_at'], api_key='synthetic', transport=httpx.MockTransport(reply)))
    probe.live_source = True
    for r in night['history_receipts']:
        persist_krx_response(root=storage, query_date=datetime.strptime(r['request']['params']['basDd'], '%Y%m%d').date(),
            fetched_at=datetime.fromisoformat(r['received_at']), http_status=200, raw_body=night['bodies'][r['artifact']])
    value = TypeAdapter(MacroProviderResult).dump_python(materialize_night_probe(probe, history_directory=storage,
        night_end_dates=True), mode='json')
    args = dict(night, night_end_dates=sealed_night_end_date_history(value), expected_value_sha256=digest(value))
    assert replay_night(**args)['value_sha256'] == digest(value)
    with pytest.raises(ValueError, match='night_owner_value_mismatch'):
        replay_night(**{**args, 'night_end_dates': False})
