import asyncio
from copy import deepcopy
from datetime import datetime, timezone

import httpx
import pytest

from app.macro.providers.ecos import EcosProvider
from app.macro.providers.market import normalize_market_observation
from app.services.macro_source_time import publication_context, source_period
from app.services.market_display_plan import build_display_plan, render_display_plan, final_display_audit, US_SECTORS
from app.services.market_intelligence_service import _observation_fact
from app.services.numeric_semantic_registry import build_numeric_registry

NOW = datetime(2026, 9, 28, 0, tzinfo=timezone.utc)


def temporal(series, period='2026-09-25', latest=True):
    return publication_context(provider='fixture', series=series, period=period,
        query_as_of=NOW, retrieved_at=NOW, response_bytes=b'synthetic source',
        cadence='daily', latest_verified=latest)


def source(market='us'):
    facts = []
    for i, series in enumerate(('SPY', 'QQQ', 'IWM', *US_SECTORS)):
        item = dict(value=101., previous_value=100., change_value=1., change_pct=float(i),
            quality_status='fresh', observed_at='2026-09-25', provider='fixture',
            raw_payload={'previous_observation_date': '2026-09-24'})
        if series in {'SPY', 'QQQ', 'IWM'}:
            item['change_pct'] = 1.
        facts.append(_observation_fact(series, item, NOW.date()))
    for series in ('DGS10', 'DFII10', 'T10YIE', 'DCOILWTICO', 'VIXCLS', 'USDKRW'):
        facts.append(_observation_fact(series, dict(value=4., quality_status='fresh', observed_at='2026-09-25',
            raw_payload={'publication_context': temporal(series)}), NOW.date()))
    return dict(session=dict(market=market, assessment_date='2026-09-28', latest_completed_regular_session_date='2026-09-25'),
                fact_catalog=facts, numeric_registry=build_numeric_registry(facts), night_futures=[])


def plan(s, market='us'):
    return build_display_plan(s, market=market, assessment_date='2026-09-28',
                              eligible_refs=[f['fact_id'] for f in s['fact_catalog']])


def test_internal_vs_display_and_exact_order():
    s = source()
    p = plan(s)
    blocks = list(dict.fromkeys(i.block_id for i in p.items))
    assert blocks == ['header', 'indices', 'macro', 'judgment', 'sectors', 'night']
    text = render_display_plan(p, s, '시장 판단: 방향 혼재')
    assert 'SPY: 101.00 USD · +1.00 USD (+1.00%)' in text
    assert '2026-09-25 관측' in text
    assert '원/달러' not in text and 'KOSDAQ150' not in text
    assert all(label + ': 자료 부족' in text for label in ('일', '주', '월'))
    assert p.items[-1].status == 'UNAVAILABLE'
    assert len(s['fact_catalog']) > len({ref for item in p.items for ref in item.fact_ids})
    assert final_display_audit(text, p, s, '시장 판단: 방향 혼재')['status'] == 'PASS'
    assert final_display_audit(text+' invented 999', p, s, '시장 판단: 방향 혼재')['status'] == 'FAIL'


def test_kr_venue_separation_and_required_fx():
    s = source('kr')
    for venue in ('KOSPI', 'KOSDAQ'):
        for i in range(6):
            s['fact_catalog'].append(dict(fact_id=f'{venue}:{i}', fact_type='market_cross_section_sector',
                as_of_date='2026-09-25', fields=dict(market_scope=venue, taxonomy='kiwoom-sector-index-v1',
                    metric_role='actual_sector_breadth', sector=venue+chr(65+i), return_pct=float(i),
                    sector_code=str(i), source_ref=f'kiwoom:ka20003:{venue}:{i}:2026-09-25')))
    s['numeric_registry'] = build_numeric_registry(s['fact_catalog'])
    p = plan(s, 'kr')
    assert list(dict.fromkeys(i.block_id for i in p.items)) == ['header', 'judgment', 'sectors', 'fx']
    selected = [i for i in p.items if i.block_id == 'sectors']
    assert len(selected) == 4 and all(i.status == 'AVAILABLE' for i in selected)
    assert all(all(ref.startswith(i.proof['venue']) for ref in i.fact_ids) for i in selected)
    assert p.items[-1].status == 'AVAILABLE'
    usd = next(f for f in s['fact_catalog'] if f['fields'].get('series_code') == 'USDKRW')
    usd['fields'].pop('publication_context')
    assert plan(s, 'kr').items[-1].status == 'UNAVAILABLE'


def test_permutations_ties_and_stale_do_not_rank():
    s = source()
    expected = [i for i in plan(s).items if i.block_id == 'sectors']
    s['fact_catalog'].reverse()
    s['numeric_registry'].reverse()
    assert [i for i in plan(s).items if i.block_id == 'sectors'] == expected
    for f in s['fact_catalog']:
        if f['fact_type'] == 'market_sector':
            f['as_of_date'] = '2026-09-24'
    assert all(i.status == 'UNAVAILABLE' for i in plan(s).items if i.block_id == 'sectors')


def test_selected_tamper_or_invention_fails():
    s = source()
    p = plan(s)
    bad = p.model_copy(update={'items': (p.items[0].model_copy(update={'text': 'made up'}), *p.items[1:])})
    with pytest.raises(ValueError, match='binding_mismatch'):
        render_display_plan(bad, s, '혼재')
    s['fact_catalog'][0]['fields']['close'] = 999.
    with pytest.raises(ValueError, match='binding_mismatch'):
        render_display_plan(p, s, '혼재')


@pytest.mark.parametrize('token', [None, '', '2026Q5', '20261301', '20260230'])
def test_missing_invalid_period_not_query_date(token):
    with pytest.raises(ValueError):
        source_period(token)


def test_source_date_precision_and_currentness():
    p = temporal('monthly', '2026-08')
    assert p['observation_date'] == '2026-08-01' and p['observation_precision'] == 'monthly'
    assert p['published_at'] is None and p['freshness_state'] == 'LATEST_PUBLISHED_VERIFIED'
    assert not p['direction_eligible']
    with pytest.raises(ValueError):
        source_period('202608', daily_required=True)
    with pytest.raises(ValueError, match='future_macro'):
        temporal('fx', '2026-09-29')
    assert temporal('fx', latest=False)['display_eligible'] is False


def test_ecos_owns_observation_date_and_denies_missing(monkeypatch):
    from types import SimpleNamespace
    import app.macro.providers.ecos as owner
    monkeypatch.setattr(owner, 'get_settings', lambda: SimpleNamespace(ecos_api_key='synthetic', macro_provider_timeout_seconds=1))
    rows = [dict(KEYSTAT_NAME='원/달러 환율', DATA_VALUE='1,300', CYCLE='20260925', UNIT_NAME='원')]
    def collect():
        return asyncio.run(EcosProvider(httpx.MockTransport(lambda r: httpx.Response(200,
            json={'KeyStatisticList': {'row': rows}}))).collect(NOW))
    result = collect()
    assert result.observations[0].observed_at.date().isoformat() == '2026-09-25'
    del rows[0]['CYCLE']
    rows[0]['TIME'] = '20260925'
    assert not collect().observations


def test_market_two_same_response_regular_closes():
    payload = {'periods': {'daily': [dict(date='2026-09-24', close=100), dict(date='2026-09-25', close=101)]}}
    row = normalize_market_observation(payload, symbol='SPY', source_url='https://fixture/ohlcv')
    assert row.change_value == 1 and row.change_pct == pytest.approx(1)
    assert row.raw_payload['previous_observation_date'] == '2026-09-24'
    bad = deepcopy(payload)
    bad['periods']['daily'][0]['date'] = '2026-09-23'
    with pytest.raises(ValueError, match='nonadjacent'):
        normalize_market_observation(bad, symbol='SPY', source_url='https://fixture/ohlcv')


def test_duplicate_sector_identity_cannot_supply_six_ranked_rows():
    s = source()
    duplicate = deepcopy(next(f for f in s['fact_catalog'] if f['fact_type'] == 'market_sector'))
    duplicate['fact_id'] += ':duplicate'
    s['fact_catalog'].append(duplicate)
    s['numeric_registry'] = build_numeric_registry(s['fact_catalog'])
    with pytest.raises(ValueError, match='ambiguous_display_sector'):
        plan(s)


def test_fred_latest_qualified_row_and_prior_are_distinct(monkeypatch):
    from types import SimpleNamespace
    import app.macro.providers.fred as owner
    monkeypatch.setattr(owner, 'get_settings', lambda: SimpleNamespace(fred_api_key='synthetic', macro_provider_timeout_seconds=1))
    monkeypatch.setattr(owner, 'FRED_SERIES', {'DGS10': ('rates', 'percent', 'daily')})
    rows = [dict(date='2026-09-24', value='4.1'), dict(date='2026-09-26', value='.'),
            dict(date='2026-09-25', value='4.2')]
    requests = []
    def respond(request):
        requests.append(request)
        return httpx.Response(200, json={'observations': rows})
    def collect():
        return asyncio.run(owner.FredProvider(httpx.MockTransport(respond)).collect(NOW))
    result = collect()
    assert len(requests) == 1 and requests[0].url.params['limit'] == '5'
    assert requests[0].url.params['sort_order'] == 'desc'
    assert [r.observed_at.date().isoformat() for r in result.observations] == ['2026-09-24', '2026-09-25']
    assert [r.raw_payload['publication_context']['latest_available_at_query_time'] for r in result.observations] == [False, True]
    assert all(r.raw_payload['publication_context']['published_at'] is None for r in result.observations)
    rows.append(dict(date='2026-09-25', value='4.3'))
    assert not collect().observations


def test_eia_period_is_not_query_time_or_claimed_latest(monkeypatch):
    from types import SimpleNamespace
    import app.macro.providers.eia as owner
    monkeypatch.setattr(owner, 'get_settings', lambda: SimpleNamespace(eia_api_key='synthetic', macro_provider_timeout_seconds=1))
    monkeypatch.setattr(owner, 'EIA_SERIES', {'PET.WCESTUS1.W': ('WCESTUS1', 'crude_inventory', 'thousand_barrels')})
    result = asyncio.run(owner.EiaProvider(httpx.MockTransport(lambda request: httpx.Response(200,
        json={'response': {'data': [{'period': '2026-09-18', 'value': 123, 'units': 'thousand_barrels'}]}}))).collect(NOW))
    assert len(result.observations) == 1
    row = result.observations[0]
    assert row.observed_at.date().isoformat() == '2026-09-18'
    assert row.raw_payload['publication_context']['freshness_state'] == 'PUBLICATION_CURRENTNESS_UNPROVEN'
    assert not row.raw_payload['publication_context']['display_eligible']


def test_accepted_market_renderer_consumes_bound_selected_plan():
    from app.services.accepted_calibration_message_service import (
        AcceptedMarketCalibration, calibration_market_render, digest,
    )
    s = source()
    display = plan(s)
    decision = dict(market='US', regime='MIXED', confidence='LOW', breadth_state='관측 범위 제한',
        leadership='업종별 차이', flows_or_participation='참여 범위 확인', rates_or_macro_context='금리 맥락')
    receipt = dict(status='PASS', errors=[], market='us', assessment_date='2026-09-28',
        source_context_sha256=digest(s), decision_sha256=digest(decision),
        display_plan_sha256=digest(display.model_dump(mode='json')))
    accepted = AcceptedMarketCalibration(market='us', assessment_date='2026-09-28', source_context=s,
        decision=decision, acceptance=receipt, acceptance_sha256=digest(receipt), display_plan=display)
    text = calibration_market_render(accepted)
    assert text.index('SPY') < text.index('시장 판단') < text.index('TOP3')
    assert '원/달러' not in text
    mutated = accepted.model_copy(update={'display_plan': display.model_copy(update={'completed_session': '2026-09-24'})})
    with pytest.raises(ValueError):
        calibration_market_render(mutated)
