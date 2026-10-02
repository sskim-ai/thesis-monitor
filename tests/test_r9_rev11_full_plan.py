import asyncio
import json

import httpx
import pytest

from app.services.sealed_fresh_dispatch import SealedDispatcher
from app.services.sealed_native_bridge import require_complete_stock_window
from app.services.sealed_response_binding import resolve_response_binding
from app.services.sealed_source_transport import SealedSourceTransport
from app.services.unified_snapshot_contract import encoded
from app.services.unified_stock_event_input import make_read
from scripts.r9_rev11_sealed_plan import compile_plan
from tests.rev10_cohort_fixtures import plan_and_securities
from tests.test_r9_rev11_sealed_dispatch import ROOT, CONFIG


def compiled(**overrides):
    stock, securities = plan_and_securities()
    records = []
    for rows in securities.values():
        for row in rows:
            i = len(records) + 1
            records.append(dict(row, id=i, cik=str(i) if row['country'] == 'US' else None,
                                corp_code=str(i).zfill(8) if row['country'] == 'KR' else None))
    news = [make_read(security=s, market='us' if s['country'] == 'US' else 'kr',
        run_id=stock.run_id, lookback_days=3, security_records=records) for s in records]
    args = dict(stock=stock, identities={s['ticker']: s for s in records}, news_reads=news,
        config_identities={p: CONFIG for p in ('kiwoom', 'sec_edgar', 'opendart', 'fred', 'eia', 'ecos',
            'krx_night_futures', 'google_news_rss', 'naver_news')}, rev10_receipt=ROOT,
        configured_kr_pages=50, kr_post_acquisition_completeness_approved=True)
    args.update(overrides)
    return stock, args, compile_plan(**args)


def test_whole_precompiled_plan_covers_current_registry():
    stock, args, out = compiled()
    plan = out['plan']
    admission = plan.admission(rev10_receipt=ROOT, owners=out['owners'],
        config_identities=args['config_identities'], credential_presence={p: True for p in args['config_identities']})
    assert admission['live_dispatch_allowed'], admission
    assert len([r for r in out['role_coverage'] if r.startswith('stock:')]) == len(stock.reads) == 88
    assert len([r for r in out['role_coverage'] if r.startswith('financial:')]) == 22
    assert len(out['optional_valuation']) == 22
    assert all(r['classification'] == 'EVENT_OPTIONAL_PLANNED' for k, r in out['role_coverage'].items() if k.startswith('events:'))
    assert all(r['configured_cap'] == 50 and r['request_local_cap'] <= r['accepted_bound'] for r in out['kr_page_proof'])
    assert all(r['global_setting_changed'] is False for r in out['kr_page_proof'])
    assert out['acquisition_fragment_not_source_qualification']


def test_kr_post_acquisition_policy_requires_explicit_approval():
    with pytest.raises(ValueError, match='explicit_kr'):
        compiled(kr_post_acquisition_completeness_approved=False)


def test_us_exchange_exact_unique_response_binding():
    _, _, out = compiled()
    d = next(d for d in out['plan'].descriptors if d.logical_request_id == 'us_market:SPY')
    parents = {key: dict(status='PASS', request=json.loads(next(p.request_json for p in out['plan'].descriptors
        if p.logical_request_id == key)), raw=encoded({'list': [{'stk_cd': 'SPY'}] if exchange == 'NA' else []}))
        for key, exchange in zip(d.response_binding.parents, ('ND', 'NY', 'NA'), strict=True)}
    public, _ = resolve_response_binding(d.request_json, d.response_binding, parents)
    assert json.loads(json.loads(public)['body'])['stex_tp'] == 'NA'
    parents[d.response_binding.parents[0]]['raw'] = encoded({'list': [{'stk_cd': 'SPY'}]})
    with pytest.raises(ValueError, match='symbol_not_unique'):
        resolve_response_binding(d.request_json, d.response_binding, parents)


def test_native_transport_rejects_unplanned_before_network(tmp_path):
    _, args, out = compiled()
    run = SealedDispatcher(plan=out['plan'], root=tmp_path/'run', rev10_receipt=ROOT, owners=out['owners'],
        config_identities=args['config_identities'], credential_presence={p: True for p in args['config_identities']})
    calls = []
    transport = SealedSourceTransport(run, httpx.MockTransport(lambda r: calls.append(r)), providers={'kiwoom'})
    with pytest.raises(BaseException, match='not_unique_sealed_slot'):
        asyncio.run(transport.handle_async_request(httpx.Request('GET', 'https://api.kiwoom.com/private')))
    assert not calls and not run.used


@pytest.mark.parametrize('rows,pending,key,allowed', [(300, True, 'cursor', True), (299, True, 'cursor', False),
    (299, False, '', True), (300, True, '', False), (0, False, '', False)])
def test_consumer_completeness_never_infers_page_success(rows, pending, key, allowed):
    stock, _ = plan_and_securities()
    read = next(r for r in stock.reads if r.market == 'kr')
    receipt = dict(status='CAPTURED', pages=[dict(response_continuation={'cont_yn': 'Y' if pending else 'N', 'next_key': key})])
    if allowed:
        assert require_complete_stock_window(read, receipt, [{}] * rows)['consumer_complete']
    else:
        with pytest.raises(ValueError, match='SOURCE_PARTIAL'):
            require_complete_stock_window(read, receipt, [{}] * rows)
