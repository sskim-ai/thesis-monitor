from copy import deepcopy
from datetime import datetime, timedelta, timezone

import httpx
import pytest

from app.macro.providers.eia import EIA_SERIES
from app.macro.providers.fred import FRED_SERIES
from app.services.fresh_publication_replay import public_request, replay_fresh_publications
from app.services.unified_run_artifacts import sha256_bytes
from app.services.unified_snapshot_contract import digest, encoded
from app.services.unified_source_policy import UnifiedSourcePolicy
from scripts.r2b_r5_market_adapter import _publication_facts


@pytest.fixture
def sources():
    return publication_sources(datetime(2026, 9, 28, tzinfo=timezone.utc), 'synthetic-rev8')


def publication_sources(start, run_id, *, as_of=None):
    as_of = as_of or start
    latest = start.date() - timedelta(days=3)
    prior = latest - timedelta(days=1)
    providers = {name: dict(receipts=[], bodies={}, body_hashes={}) for name in ('fred', 'eia', 'ecos')}

    def add(name, url, params, payload):
        target = providers[name]
        path = f'{name}-{len(target["receipts"])}.json'
        raw = encoded(payload)
        target['bodies'][path] = raw
        target['body_hashes'][path] = sha256_bytes(raw)
        target['receipts'].append(dict(run_id=run_id, provider=name, artifact=path,
            artifact_sha256=sha256_bytes(raw), outcome='HTTP_RESPONSE', http_status=200,
            requested_at=as_of.isoformat(), received_at=(as_of + timedelta(seconds=1)).isoformat(),
            request=public_request(httpx.Request('GET', url, params=params))))

    for series in FRED_SERIES:
        add('fred', 'https://api.stlouisfed.org/fred/series/observations',
            dict(series_id=series, api_key='fixture-secret', file_type='json', sort_order='desc', limit=5,
                 observation_end=start.date().isoformat()),
            {'observations': [{'date': latest.isoformat(), 'value': '4.2'}, {'date': prior.isoformat(), 'value': '4.1'}]})
    for series in EIA_SERIES:
        add('eia', 'https://api.eia.gov/v2/seriesid/' + series, dict(api_key='fixture-secret', length=1),
            {'response': {'data': [{'period': '2026-09-18', 'value': '12', 'units': 'fixture_unit'}]}})
    add('ecos', 'https://ecos.bok.or.kr/api/KeyStatisticList/fixture-secret/json/kr/1/100', {},
        {'KeyStatisticList': {'row': [
            {'KEYSTAT_NAME': name, 'CYCLE': period, 'DATA_VALUE': value, 'UNIT_NAME': unit}
            for name, period, value, unit in [('한국은행 기준금리', latest.strftime('%Y%m%d'), '2.5', 'percent'),
                ('원/달러 환율', latest.strftime('%Y%m%d'), '1300', 'KRW'), ('소비자물가지수', '202608', '120', 'index'),
                ('M2', '202607', '200', 'KRW')]]}})
    return dict(run_id=run_id, run_started_at=start, as_of=as_of,
        acquisition_cutoff=start + timedelta(minutes=1), providers=providers,
        policy=UnifiedSourcePolicy(frozenset(providers)))


def test_fresh_publication_replay_preserves_source_period_and_retrieval(sources):
    first = replay_fresh_publications(**sources)
    assert first == replay_fresh_publications(**sources)
    assert first['external_provider_calls'] == 0
    fred = first['providers']['fred']['value']['observations']
    assert len(fred) == len(FRED_SERIES) * 2
    assert all(row['observed_at'].startswith(('2026-09-24', '2026-09-25')) for row in fred)
    for row in fred:
        temporal = row['raw_payload']['publication_context']
        assert temporal['query_as_of'].startswith('2026-09-28')
        assert temporal['retrieved_at'] == '2026-09-28T00:00:01+00:00'
        assert temporal['direction_eligible'] is False
    assert not first['providers']['ecos']['value']['warnings']
    assert 'fixture-secret' not in str(first)
    packet = dict(publication_context=first, market_sources={'run_id': 'synthetic-rev8'})
    facts, denials, refs = _publication_facts(packet, sources['as_of'].date())
    assert facts and refs and denials
    assert all(f['as_of_date'] <= '2026-09-25' for f in facts)
    assert digest(facts) == digest(_publication_facts(packet, sources['as_of'].date())[0])
    real = next(f for f in facts if f['fields']['series_code'] == 'DFII10')['fields']
    assert real['previous_observation_date'] == '2026-09-24'
    assert real['previous_level_pct'] == 4.1
    assert real['change_pp'] == pytest.approx(0.1)
    assert real['change_bp'] == pytest.approx(10)
    assert real['today_signal_eligible'] is False
    assert real['important_change_eligible'] is False


@pytest.mark.parametrize('mutation', ['raw', 'run', 'time', 'query', 'missing', 'extra'])
def test_fresh_publication_invalid_binding_fails_before_authority(sources, mutation):
    p = sources['providers']['fred']
    row = p['receipts'][0]
    if mutation == 'raw':
        p['bodies'][row['artifact']] = b'{}'
    elif mutation == 'run':
        row['run_id'] = 'old'
    elif mutation == 'time':
        row['received_at'] = '2025-01-01T00:00:00+00:00'
    elif mutation == 'query':
        row['request']['params']['series_id'] = 'UNDECLARED'
    elif mutation == 'missing':
        sources['providers'].pop('eia')
    else:
        p['receipts'].append(deepcopy(row))
    with pytest.raises(ValueError):
        replay_fresh_publications(**sources)
