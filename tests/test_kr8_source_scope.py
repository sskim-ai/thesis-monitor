import asyncio
from copy import deepcopy

import httpx
import pytest

from app.services.sealed_fresh_dispatch import SealedDispatcher
from app.services.sealed_source_transport import SealedSourceTransport
from app.services.unified_stock_acquisition import StockPlan, UNIVERSE
from scripts.kr8_source_scope import require_kr8_plan
from scripts.r9_rev11_sealed_plan import compile_plan
from tests.test_r9_rev11_full_plan import compiled


def kr_plan():
    stock, args, _ = compiled()
    raw = stock.model_dump(mode='json')
    raw['contract'] = 'one-shot-kr8-source-acquisition-v1'
    raw['reads'] = [r for r in raw['reads'] if r['market'] == 'kr']
    stock = StockPlan.model_validate(raw)
    args.update(stock=stock,
        identities={t:s for t,s in args['identities'].items() if t in UNIVERSE['kr']},
        news_reads=[r for r in args['news_reads'] if r.market == 'kr'])
    args['config_identities'] = {k:v for k,v in args['config_identities'].items()
        if k in {'kiwoom','opendart','ecos','krx_night_futures','naver_news'}}
    out = compile_plan(**args)
    frozen = dict(out, plan=out['plan'].model_dump(mode='json'),
        stock_plan=stock.model_dump(mode='json'), scope='KR8_ONLY', sessions={'kr':'2026-09-28'},
        us_market_symbols=[], us_market_reads=[], security_records=list(args['identities'].values()))
    return args, out, frozen


def test_kr8_finite_plan_contains_no_us_only_roles():
    args, out, frozen = kr_plan()
    audit = require_kr8_plan(frozen)
    assert audit['stock_roles'] == 32
    assert audit['us_only_descriptors'] == 0
    assert set(out['candidate']['current_subjects']) == set(UNIVERSE['kr'])
    assert set(out['candidate']['macro_queries']) == {'ecos'}
    assert not {'fred','eia','us_market_wire'} & out['candidate']['budgets'].keys()
    assert out['plan'].admission(rev10_receipt=args['rev10_receipt'], owners=out['owners'],
        config_identities=args['config_identities'], credential_presence={p:True for p in args['config_identities']})['live_dispatch_allowed']


@pytest.mark.parametrize('mutation', ['scope','sessions','symbols','news','stock','subjects','macro'])
def test_scope_drift_fails_before_dispatch(mutation):
    _,_,f = kr_plan()
    if mutation == 'scope':
        f.pop('scope')
    elif mutation == 'sessions':
        f['sessions']['us'] = '2026-09-28'
    elif mutation == 'symbols':
        f['us_market_symbols'] = ['SPY']
    elif mutation == 'news':
        f['news_reads'][0]['market'] = 'us'
    elif mutation == 'stock':
        f['stock_plan']['contract'] = 'one-shot-stock-source-acquisition-v1'
    elif mutation == 'subjects':
        f['candidate']['current_subjects'].append('IBM')
    else:
        f['candidate']['macro_queries']['fred'] = {'series':[]}
    with pytest.raises(ValueError):
        require_kr8_plan(f)


@pytest.mark.parametrize('route', ['/api/us/chart','/api/us/stkinfo'])
def test_actual_us_transport_rejected_without_http(tmp_path, route):
    args, out, _ = kr_plan()
    run = SealedDispatcher(plan=out['plan'],root=tmp_path/'dispatch',rev10_receipt=args['rev10_receipt'],
        owners=out['owners'],config_identities=args['config_identities'],
        credential_presence={p:True for p in args['config_identities']})
    calls=[]
    transport=SealedSourceTransport(run,httpx.MockTransport(lambda r:calls.append(r)),providers={'kiwoom'})
    with pytest.raises(BaseException,match='not_unique_sealed_slot'):
        asyncio.run(transport.handle_async_request(httpx.Request('POST','https://api.kiwoom.com'+route,
            json={'stk_cd':'IBM','stex_tp':'NY'},headers={'api-id':'usa06012'})))
    assert not calls and not run.used


def test_kr_plan_rejects_missing_duplicate_and_extra_stock_roles():
    _,_,f = kr_plan()
    for reads in (f['stock_plan']['reads'][:-1], f['stock_plan']['reads']+[f['stock_plan']['reads'][0]]):
        bad=deepcopy(f['stock_plan'])
        bad['reads']=reads
        with pytest.raises(ValueError,match='stock_plan_required'):
            StockPlan.model_validate(bad)


def test_default_all22_contract_remains_complete():
    stock,_,out=compiled()
    assert len(stock.reads)==88 and len(out['candidate']['current_subjects'])==22
    assert 'scope' not in out['candidate']
    assert set(out['candidate']['macro_queries'])=={'fred','eia','ecos'}


def test_kr_publication_replay_excludes_us_only_macro_sources():
    from datetime import datetime, timezone
    from app.services.fresh_publication_replay import replay_fresh_publications
    from tests.test_r9_rev8_fresh_publications import publication_sources
    inputs=publication_sources(datetime(2026,9,28,tzinfo=timezone.utc),'kr-fictional')
    inputs['providers']={'ecos':inputs['providers']['ecos']}
    inputs['market_scope']='KR8_ONLY'
    first=replay_fresh_publications(**inputs)
    assert first==replay_fresh_publications(**inputs)
    assert set(first['providers'])=={'ecos'}
    assert first['external_provider_calls']==0
    inputs.pop('market_scope')
    with pytest.raises(ValueError,match='exact_provider_set'):
        replay_fresh_publications(**inputs)
