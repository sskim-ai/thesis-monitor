"""Changed selected compiler/wiring boundaries, not synthetic live Owner PASS."""
from datetime import datetime, timezone
import asyncio
from types import SimpleNamespace

import pytest

from app.models.security import SecurityMaster
from app.services import selected_source_registration as registration
from app.services.selected_kis_sources import build_plan as kis_plan, validate_plan
from app.services.selected_source_dispatch import SelectedSourceDispatcher
from app.services.selected_source_plan import (
    build_stock_plan, compile_selected_plan, decode_stock_plan, request_budget, SCOPE,
)
from app.services.unified_snapshot_contract import digest
from app.services.unified_stock_event_input import make_read

AT=datetime(2026,11,11,8,tzinfo=timezone.utc)
COUNTS=dict(adjusted_daily=1000,adjusted_weekly=700,adjusted_monthly=300,unadjusted_weekly_valuation=700)


def compile_market(market,ticker,*,issuer_type=None):
    security=SecurityMaster(id=123,ticker=ticker,exchange='NASDAQ' if market=='us' else 'KOSPI',
        country=market.upper() if market=='us' else 'KR',company_name='Boundary '+ticker,
        canonical_security_id='TEST:SEC:'+ticker,canonical_company_id='TEST:ISS:'+ticker,
        identity_provider='sec_edgar' if market=='us' else 'opendart',
        issuer_type=issuer_type or ('domestic_us' if market=='us' else 'domestic_kr'),
        cik='12345' if market=='us' else None,corp_code='00123456' if market=='kr' else None).model_dump(mode='json')
    stock=build_stock_plan(market=market,identities={ticker:security},at=AT,
        generation='BOUNDARY-'+market,code_sha='a'*40,counts=COUNTS)
    news=make_read(security=security,market=market,run_id=stock.run_id,lookback_days=3,security_records=[security])
    args=dict(stock=stock,identities={ticker:security},news_reads=[news],
        config_identities={p:digest('NOT_A_CREDENTIAL:'+p) for p in
            ('kiwoom','sec_edgar','opendart','fred','eia','ecos','krx_night_futures','finnhub','google_news_rss','naver_news')},
        configured_kr_pages=20,kr_post_acquisition_completeness_approved=True,exact_financial_owner=True,
        valuation_market_types={} if market=='us' else {ticker:'0'},transient_retry_max=0)
    kp=kis_plan(generation=stock.run_id,as_of=AT.isoformat(),securities={ticker:dict(security,currency='KRW')},static_hashes={}) if market=='kr' else None
    return compile_selected_plan(compiler_args=args,kis_plan=kp),args,kp


@pytest.mark.parametrize('market,ticker,kind',[('us','NEWX','domestic_us'),('us','NEWADS','foreign_private_issuer'),('kr','123456',None)])
def test_generic_selected_original_slot_compiler(market,ticker,kind):
    c,args,k=compile_market(market,ticker,issuer_type=kind)
    p=c['plan'];budget=request_budget(c,k)
    assert p.subjects==(ticker,) and len(args['stock'].reads)==4
    assert all(d.transient_retry_max==0 for d in p.descriptors)
    assert budget['total']==len(p.descriptors)+(k['maximum_physical_HTTP'] if k else 0)
    assert {t for t in c['candidate']['financial_plans']}=={ticker}
    assert c['candidate']['dispatch_allowed'] is False and args['stock'].planning_only
    from app.services.unified_stock_acquisition import StockPlan
    with pytest.raises(ValueError):StockPlan.model_validate(args['stock'].model_dump(mode='json'))
    assert compile_selected_plan(compiler_args=args,kis_plan=k)['plan']==p


def test_kis_selected_budget_identity_and_no_authentication(monkeypatch):
    from scripts import kr8_kis_integration as original
    c,args,k=compile_market('kr','123456')
    assert validate_plan(k)==('123456',) and k['maximum_physical_HTTP']==28
    assert original._subjects(k)==('123456',)
    bad={**k,'maximum_physical_HTTP':29}
    with pytest.raises(ValueError,match='reproduction'):validate_plan(bad)
    wrong={**k,'generation_id':'OTHER'}
    with pytest.raises(ValueError):compile_selected_plan(compiler_args=args,kis_plan=wrong)
    # No historical KR8 fixed roster is rewritten.
    assert len(original.SUBJECTS)==8 and original.CONTRACT=='kr8-fresh-kis-source-integration-v1'


def test_selected_default_off_and_public_receipts_do_not_admit(tmp_path):
    c,args,k=compile_market('us','NEWX')
    with pytest.raises(ValueError,match='default_off'):
        SelectedSourceDispatcher(plan=c['plan'],compiler_args=args,kis_plan=k,registration_owner={},policy=None,
            config_identities={},credential_presence={},repository_root=tmp_path,root=tmp_path/'wire',
            approved_plan_sha256=c['plan'].plan_sha256,approved_provider_caps=request_budget(c)['providers'],guard=lambda:None)
    with pytest.raises(ValueError,match='live_backend_owner'):
        registration.local_seed({'status':'PASS'},stock=args['stock'],policy=None)
    with pytest.raises(ValueError):
        decode_stock_plan({'scope':'ALL22','stock_plan':args['stock'].model_dump(mode='json')})
    with pytest.raises(ValueError,match='current_exact_plan'):
        SelectedSourceDispatcher(enabled=True,plan=c['plan'],compiler_args=args,kis_plan=k,registration_owner={},policy=None,
            config_identities={},credential_presence={},repository_root=tmp_path,root=tmp_path/'wire',
            approved_plan_sha256=c['plan'].plan_sha256,approved_provider_caps=request_budget(c)['providers'],guard=lambda:None)
    assert not (tmp_path/'wire').exists()


def test_one_capture_two_market_handoff_without_query_or_private_output(monkeypatch):
    events=[];capture=object()
    monkeypatch.setattr(registration.original,'_approval',lambda _:SimpleNamespace(event_id='TEST',subjects=('NEWX','123456')))
    monkeypatch.setattr(registration,'capture_authorized_class_c',lambda _:events.append('capture') or capture)
    monkeypatch.setattr(registration,'captured_private_snapshot',lambda _: (b'PRIVATE_NOT_EXPORTED',{'query_count':5}))
    def issue(**kwargs):
        assert kwargs['capture'] is capture
        events.append(kwargs['market'])
        return object(),{}
    monkeypatch.setattr(registration.original,'issue_prospective_owner',issue)
    kwargs=dict(permission=SimpleNamespace(event_id='TEST',subjects=('NEWX','123456')),approval=object(),
        generations={'us':'US_CHILD','kr':'KR_CHILD'},policy=None)
    with pytest.raises(ValueError,match='default_off'):registration.capture_markets(**kwargs)
    _,owners,receipt=registration.capture_markets(**kwargs,enabled=True)
    assert events==['capture','us','kr'] and set(owners)=={'us','kr'} and receipt=={'query_count':5}


def test_runtime_database_target_is_metadata_only(tmp_path):
    p=tmp_path/'registration';p.write_bytes(b'not a DB; no reader is used')
    resolved,device,inode=registration.database_target(SimpleNamespace(database_url='sqlite:///registration'),runtime_directory=tmp_path)
    assert resolved==p and (device,inode)==(p.stat().st_dev,p.stat().st_ino)
    link=tmp_path/'link';link.symlink_to(p)
    with pytest.raises(ValueError,match='symlink'):
        registration.database_target(SimpleNamespace(database_url='sqlite:///link'),runtime_directory=tmp_path)
    with pytest.raises(ValueError):registration.database_target(SimpleNamespace(database_url='sqlite://'),runtime_directory=tmp_path)


def test_selected_acquisition_and_context_fail_before_io(tmp_path):
    from app.services.canonical_source_acquisition import acquire_all
    from app.services.selected_source_context import freeze_registered_child
    from app.services.unified_live_source_transport import SourceSafetyStop
    c,args,_=compile_market('us','NEWX')
    frozen=dict(scope=SCOPE,selected_market='us',generation_id=args['stock'].run_id,
        stock_plan=args['stock'].model_dump(mode='json'))
    with pytest.raises(SourceSafetyStop,match='current_dispatch'):
        asyncio.run(acquire_all(root=tmp_path/'never',frozen=frozen,settings=None,
            dispatcher=SimpleNamespace(plan=c['plan']),inner=None,policy=None,guard=lambda:None))
    with pytest.raises(ValueError,match='default_off'):
        freeze_registered_child(registration_owner=None,policy=None,code_sha='a'*40,native={},native_owner_root='',
            config_identities={},configured_kr_pages=20,listing_rows=[],kis_static_hashes={})
    assert not (tmp_path/'never').exists()


def test_selected_quota_and_uncertain_transport_stop_without_retry(monkeypatch):
    from app.services.sealed_fresh_dispatch import SealedDispatcher
    from app.services.unified_live_source_transport import SourceSafetyStop
    for status,error,stopped in [(503,None,False),(429,None,True),(None,'ReadTimeout',True)]:
        wire=object.__new__(SelectedSourceDispatcher);wire.halted=False
        wire._require_current=lambda:None
        calls=[]
        async def returned(*args,**kwargs):
            calls.append('one physical executor entry')
            return dict(attempts=[dict(status=status,error=error)])
        monkeypatch.setattr(SealedDispatcher,'execute',returned)
        if stopped:
            with pytest.raises(SourceSafetyStop):asyncio.run(wire.execute())
        else:asyncio.run(wire.execute())
        assert len(calls)==1 and wire.halted is stopped


def test_compact_input_cannot_be_exported_as_original_stock():
    from scripts.fresh_source_only_export import source_only_fresh_stock
    with pytest.raises(ValueError,match='source_only_fresh_contract_required'):
        source_only_fresh_stock({'contract':'C22C_EXISTING_SOURCE_DATED_INVESTMENT_INPUT'},{})
