"""Freeze one selected child from an existing, current in-memory registration.

The caller seals original protocol documents separately and supplies the native
inspection result. This function opens no database and loads no credentials.
"""
from datetime import datetime
from zoneinfo import ZoneInfo

from app.services import prospective_class_c_owner as registration
from app.services.selected_kis_sources import build_plan as build_kis_plan
from app.services.selected_source_plan import SCOPE, COUNTS, build_stock_plan, compile_selected_plan
from app.services.selected_source_registration import local_seed
from app.services.provider_native_valuation_acquisition import routing_markets
from app.services.unified_snapshot_contract import digest
from app.services.unified_stock_event_input import make_read


def freeze_registered_child(*, registration_owner, policy, code_sha, native, native_owner_root,
                            config_identities, configured_kr_pages, listing_rows, kis_static_hashes,
                            completed_close_documentation=None, official_identities=None,
                            consumer_policy=None, master_id=None, ohlcv_source_url=None, enabled=False, run_ledger=None):
    if enabled is not True:
        raise ValueError('selected_source_context_default_off')
    if run_ledger is None:
        raise ValueError('selected_one_campaign_ledger_required')
    document,receipt=registration._state(registration_owner)
    market,generation=receipt['market'],receipt['generation_id']
    if consumer_policy is not None:
        if not master_id or master_id==generation:
            raise ValueError('selected_distinct_master_id_required')
        if market=='us' and (not ohlcv_source_url or not completed_close_documentation):
            raise ValueError('selected_original_market_route_and_close_documentation_required')
    registration.require_generation(registration_owner,generation)
    at=datetime.fromisoformat(receipt['cutoff'])
    identities={r['record']['ticker']:r['record']
        for role in document['roles'].values() for r in role['records'] if r['table']=='securitymaster'}
    if set(identities)!=set(receipt['bindings']):
        raise ValueError('selected_current_identity_coverage_required')
    stock=build_stock_plan(market=market,identities=identities,at=at,generation=generation,
        code_sha=code_sha,counts=COUNTS,native=native,registration_sha256=digest(receipt))
    private_local=local_seed(registration_owner,stock=stock,policy=policy)
    records=list(identities.values())
    news=[make_read(security=s,market=market,run_id=generation,lookback_days=3,security_records=records) for s in records]
    compiler=dict(stock=stock,identities=identities,news_reads=news,config_identities=config_identities,
        configured_kr_pages=configured_kr_pages,kr_post_acquisition_completeness_approved=True,
        exact_financial_owner=True,valuation_market_types=routing_markets(identities,listing_rows=listing_rows),
        transient_retry_max=0)
    if consumer_policy is not None:
        compiler['selected_consumer_policy']=consumer_policy
    kis=build_kis_plan(generation=generation,as_of=at.isoformat(),
        securities={t:dict(s,currency='KRW') for t,s in identities.items()},static_hashes=kis_static_hashes) if market=='kr' else None
    compiled=compile_selected_plan(compiler_args=compiler,kis_plan=kis)
    target=next(iter({r.latest_completed_session for r in stock.reads}))
    symbols=compiled['candidate']['us_market_symbols']
    frozen=dict(**{k:v for k,v in compiled.items() if k!='plan'},scope=SCOPE,selected_market=market,
        execution_purpose=registration.SCOPE,generation_id=generation,frozen_at=at.isoformat(),
        plan=compiled['plan'].model_dump(mode='json'),stock_plan=stock.model_dump(mode='json'),
        security_records=records,native_owner=native,native_owner_root=str(native_owner_root),
        us_market_symbols=symbols,us_market_reads=[dict(role='us_market:'+s,symbol=s,market='us',
            provider='ohlcv_analyst',response_provider='kiwoom',period='daily',adjusted=True,
            session_date=target,max_requests=1,params=dict(symbol=s,market='US',periods='daily',count=2,
                include_indicators='false',indicator_limit=0,adjusted='true')) for s in symbols],
        sessions={market:target},query_kst_date=at.astimezone(ZoneInfo('Asia/Seoul')).date().isoformat(),
        kr_local_cap=min(configured_kr_pages,20),config_identities=config_identities,
        completed_close_documentation=completed_close_documentation,
        valuation_official_identities=official_identities or {},registration_receipt_sha256=digest(receipt),
        private_class_c_storage='MEMORY_ONLY',financial_use_granted=False)
    if master_id is not None:frozen['master_id']=master_id
    if ohlcv_source_url is not None:frozen['ohlcv_source_url']=ohlcv_source_url
    if run_ledger is not None:
        child=run_ledger.identity['children'][market]
        if child['generation']!=generation or tuple(child['subjects'])!=stock.subjects:
            raise ValueError('selected_shared_budget_child_scope_changed')
        frozen['shared_run_ledger']=run_ledger.worker_binding()
    return frozen,compiler,kis,private_local
