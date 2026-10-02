import asyncio
from copy import deepcopy
from datetime import date, datetime, timedelta, timezone

import httpx
import pytest
from pydantic import TypeAdapter

from app.jobs.probe_krx_night_futures import fetch_live_probe, KRX_FUTURES_DAILY_URL
from app.macro.providers.base import MacroProviderResult
from app.macro.providers.krx import materialize_night_probe
from app.services.current_fresh_valuation import derive_current_valuation
from app.services.issuer_business_bridge import identity_bridge
from app.services.krx_night_history_service import persist_krx_response
from app.services.unified_run_artifacts import sha256_bytes
from app.services.unified_sealed_context import replay_night
from app.services.unified_snapshot_contract import digest, encoded
from app.services.unified_source_policy import UnifiedSourcePolicy
from tests.test_issuer_business_bridge import fixture as bridge_fixture
from tests.test_krx_night_futures_probe import _row


@pytest.fixture
def night(tmp_path):
    at = datetime(2026, 9, 2, 23, 10, tzinfo=timezone.utc)
    start = at - timedelta(minutes=1)
    bodies, hashes, receipts = {}, {}, {}
    for day in ('2026-08-31', '2026-09-01', '2026-09-02', '2026-09-03'):
        rows = []
        if day != '2026-09-03':
            for session, close in (('정규', '100'), ('야간', '101')):
                row = _row('KOSPI 200 선물', session, 'A016C000',
                    '코스피200 F 202612' + (' 야간' if session == '야간' else ''),
                    close, day.replace('-', ''), '1' if session == '야간' else None)
                row.update(TDD_OPNPRC='100', TDD_HGPRC='102', TDD_LWPRC='99')
                rows.append(row)
        body = encoded({'OutBlock_1': rows})
        name = day + '.json'
        bodies[name], hashes[name] = body, sha256_bytes(body)
        receipts[day] = dict(run_id='synthetic-fresh-night', acquisition_id='night-once', provider='krx_night_futures',
            outcome='HTTP_RESPONSE', http_status=200, artifact=name, artifact_sha256=hashes[name],
            requested_at=start.isoformat(), received_at=at.isoformat(),
            request=dict(method='GET', route=KRX_FUTURES_DAILY_URL, params={'basDd': day.replace('-', '')}))
    def reply(request):
        day = datetime.strptime(request.url.params['basDd'], '%Y%m%d').date().isoformat()
        return httpx.Response(200, content=bodies[day + '.json'])
    probe = asyncio.run(fetch_live_probe(run_date=date(2026, 9, 3), observation_time=at,
        api_key='fixture', transport=httpx.MockTransport(reply)))
    probe.live_source = True
    persist_krx_response(root=tmp_path, query_date=date(2026, 8, 31), fetched_at=at,
        http_status=200, raw_body=bodies['2026-08-31.json'])
    expected = TypeAdapter(MacroProviderResult).dump_python(materialize_night_probe(probe, history_directory=tmp_path), mode='json')
    return dict(receipts=[receipts[d.isoformat()] for d in probe.queried_dates],
        history_receipts=[receipts['2026-08-31']], bodies=bodies, body_hashes=hashes,
        observed_at=at, run_id='synthetic-fresh-night', acquisition_id='night-once',
        expected_value_sha256=digest(expected), policy=UnifiedSourcePolicy(frozenset({'krx_night_futures'})),
        run_started_at=start, acquisition_cutoff=at)


def test_same_run_raw_history_recreates_kospi200_dwm_only(night):
    result = replay_night(**night)
    assert result == replay_night(**night)
    assert result['network_calls'] == 0
    rows = result['value']['observations']
    assert [r['raw_payload']['product'] for r in rows] == ['KOSPI200']
    frames = rows[0]['raw_payload']['night_timeframes']
    assert all(not frames[k]['missing_dates'] for k in ('daily', 'weekly', 'monthly'))
    hashes = set(night['body_hashes'].values())
    assert all(set(frames[k]['source_raw_sha256']) <= hashes for k in ('daily', 'weekly', 'monthly'))


@pytest.mark.parametrize('change', ['epoch', 'route', 'body', 'overlap'])
def test_night_history_cannot_be_substituted_or_borrowed(night, change):
    row = night['history_receipts'][0]
    if change == 'epoch':
        row['requested_at'] = '2025-01-01T00:00:00+00:00'
    elif change == 'route':
        row['request']['route'] = 'https://other.invalid/'
    elif change == 'body':
        night['bodies'][row['artifact']] = b'{}'
    else:
        row['request']['params']['basDd'] = '20260901'
    with pytest.raises(ValueError):
        replay_night(**night)


def test_issuer_bridge_keeps_target_price_and_unavailable_multiples():
    args = bridge_fixture()
    bridge = identity_bridge(**args)
    assert bridge['status'] == 'PASS'
    target = {**args['target'], 'company_name': 'Synthetic issuer'}
    inputs = dict(ticker=target['ticker'], run_id='new', security=target,
        price=dict(contract='current-price-context-v1', current_price=100, currency='USD',
            as_of_date='2026-09-25', price_basis='close'), projection={}, issuer_bridge=bridge)
    view = derive_current_valuation(**inputs)
    assert view.ticker == target['ticker'] and view.currency == 'USD' and view.price == 100
    assert len(view.metrics) == 3 and all(m.value is None and not m.display_eligible for m in view.metrics)
    assert all(digest(bridge) in m.input_hashes for m in view.metrics)
    changed = deepcopy(bridge)
    changed['security_valuation_transfer'] = True
    changed['receipt_sha256'] = digest({k:v for k,v in changed.items() if k != 'receipt_sha256'})
    with pytest.raises(ValueError, match='scope_invalid'):
        derive_current_valuation(**{**inputs, 'issuer_bridge': changed})
