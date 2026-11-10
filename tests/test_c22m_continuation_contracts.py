"""New opt-in boundaries only. No provider, model or persistent DB calls."""
from copy import deepcopy
from datetime import date,datetime,timezone
import json
from pathlib import Path
import pytest
from app.services.unified_snapshot_contract import digest
from app.services.scoped_source_plan import ScopedConfig,ScopedPriceCaptureSelectionV2,HistoryCounts,compile_scoped_wire_contract
from app.services.scoped_routing_identity import ScopedSubject
from app.services.pending_completed_close_contract import requirements
from app.services.dated_market_legacy_adapter import _render_component_sectors as render_component_sectors,verify_component_sector_text,render_night_dwm_preview
from app.services.market_display_plan import US_SECTORS


def close_case(market):
    subject=ScopedSubject(ticker='123456' if market=='kr' else 'EXAMPLE',market=market,security_id='fixture-security',
        issuer_id='fixture-issuer',venue='KRX' if market=='kr' else 'NASDAQ',currency='KRW' if market=='kr' else 'USD')
    counts=HistoryCounts(adjusted_daily=2,adjusted_weekly=2,adjusted_monthly=2,unadjusted_weekly_valuation=2)
    config=ScopedConfig(subjects=(subject,),kr_history=counts,us_history=counts,kr_max_pages=2,
        capture_selection=ScopedPriceCaptureSelectionV2(contract='scoped-price-capture-selection-v2',close_security_ids=(subject.security_id,)))
    at=datetime(2026,11,10,1,tzinfo=timezone.utc)
    wire=compile_scoped_wire_contract(config=config,identities={subject.ticker:dict(exchange=subject.venue,canonical_security_id=subject.security_id)},
        generation_id='fixture',at=at,code_sha='a'*40,provider_config_sha256='b'*64,retries=0)
    return config,wire


@pytest.mark.parametrize('market',['kr','us'])
def test_selected_close_compiler_basis_and_bound(market):
    config,wire=close_case(market);rows=requirements(config,wire)
    assert rows==(dict(security_id='fixture-security',session='2026-11-09'),)
    assert wire['price_pairs'][0].basis==('ADJUSTED_STOCK_CHART' if market=='kr' else 'REGULAR_STOCK_CLOSE')
    assert sum(d.max_transport_attempts for d in wire['request_plan'].descriptors)==(3 if market=='kr' else 2)


@pytest.mark.parametrize('kind',['basis','session','wire','extra_subject','credential'])
def test_selected_close_tampering_rejected(kind):
    config,wire=close_case('kr');wire=deepcopy(wire)
    if kind in {'basis','session'}:
        p=wire['price_pairs'][0];wire['price_pairs']=(p.model_copy(update={'basis':'REGULAR_STOCK_CLOSE'} if kind=='basis' else {'target':date(2099,1,1)}),)
    elif kind=='extra_subject':
        config=config.model_copy(update={'subjects':config.subjects+(config.subjects[0].model_copy(update={'ticker':'654321','security_id':'outside'}),)})
    else:
        plan=wire['request_plan'];descriptors=list(plan.descriptors);i=0 if kind=='credential' else 1
        descriptors[i]=descriptors[i].model_copy(update={'request_json':descriptors[i].request_json.replace('[REDACTED]','changed') if kind=='credential' else '{}'})
        wire['request_plan']=plan.model_copy(update={'descriptors':tuple(descriptors)})
    with pytest.raises(ValueError):requirements(config,wire)


def reference(market='us',count=6):
    session='2026-11-05'
    if market=='us':
        value=dict(observations=[dict(series_code=s,unit='usd',market_session='us_regular',observed_at=session+'T00:00:00Z',change_pct=float(i),
            raw_payload=dict(return_basis='same_response_adjacent_adjusted_regular_closes')) for i,s in enumerate(US_SECTORS[:count])])
    else:
        names=['음식료/담배','화학','제약','금속','기계장비','전기전자']
        value=dict(sectors=[dict(sector=n,sector_code=str(i),market_scope=m,taxonomy='kiwoom-sector-index-v1',metric_role='actual_sector_breadth',
            return_pct=float(i),listed_count=10,source_ref=f'kiwoom:ka20003:{m}:{i}:{session}') for m in ('KOSPI','KOSDAQ') for i,n in enumerate(names[:count])])
    return dict(scope='DATED_SOURCE_INSPECTION_NOT_MARKET_CONTEXT',market=market,completed_session=session,
        original_cold_status='ORIGINAL_COMPONENT_OWNER_COLD_PASS_NOT_FULL_PARENT',full_market_parent=False,value=value,value_sha256=digest(value),
        original_bundle_sha256='a'*64,original_component_sha256='b'*64)


@pytest.mark.parametrize('market',['us','kr'])
@pytest.mark.parametrize('count',[5,6])
def test_canonical_three_plus_three_threshold(market,count):
    r=render_component_sectors(reference(market,count));items=r['selected_items']
    assert len(items)==(2 if market=='us' else 4)
    assert all(i['status']==('AVAILABLE' if count==6 else 'UNAVAILABLE') for i in items)
    if count==6:
        ids=[ref for i in items for ref in i['fact_ids']];assert len(ids)==len(set(ids))
    assert r['full_market_parent'] is False and r['market_judgment'] is None and r['NO_SEND']


@pytest.mark.parametrize('kind',['duplicate','unit','date','metric','sha','final_text'])
def test_sector_source_and_final_binding(kind):
    ref=reference('kr' if kind=='metric' else 'us')
    key='sectors' if kind=='metric' else 'observations';rows=ref['value'][key]
    if kind=='duplicate':rows.append(deepcopy(rows[0]))
    if kind=='unit':rows[0]['unit']='KRW'
    if kind=='date':rows[0]['observed_at']='2099-01-01T00:00:00Z'
    if kind=='metric':rows[0]['metric_role']='sector_price_proxy'
    if kind!='sha':ref['value_sha256']=digest(ref['value'])
    if kind=='sha':ref['value_sha256']='0'*64
    if kind=='final_text':
        with pytest.raises(ValueError):verify_component_sector_text('tampered',ref)
    else:
        with pytest.raises(ValueError):render_component_sectors(ref)


def test_sector_ties_order_and_nonsector_kr_exclusion():
    ref=reference('kr');rows=ref['value']['sectors']
    rows.append(dict(rows[-1],sector='KOSDAQ 150',sector_code='999',return_pct=999))
    for row in rows:row['return_pct']=1.
    ref['value_sha256']=digest(ref['value']);first=render_component_sectors(ref)
    rows.reverse();ref['value_sha256']=digest(ref['value']);second=render_component_sectors(ref)
    assert first['text']==second['text'] and 'KOSDAQ 150' not in second['text']


def flow_result():
    from app.services.market_cross_section_service import MarketCrossSection,MarketCrossSectionQuality,MarketFlowFact
    from app.services.kiwoom_kr_market_context_service import KiwoomMarketContextCollection,KiwoomCollectionAudit
    at=datetime(2026,11,6,10,tzinfo=timezone.utc);session=at.date()
    flows=[MarketFlowFact(actor=a,market=m,net_buy_amount=100_000_000,currency='KRW',exchange_basis='KRX_NXT_INTEGRATED',
        source_unit='100M_KRW',source_unit_scale_krw=100_000_000,source_ref=f'kiwoom:ka10051:{m}:{session}') for m in ('KOSPI','KOSDAQ') for a in ('foreign','institution','retail')]
    section=MarketCrossSection(market='KR',session_date=session,as_of=at,source_payload_sha256='a'*64,market_flows=flows,
        quality=MarketCrossSectionQuality(provider='kiwoom_rest',provider_role='fixture',coverage='partial',freshness='fresh',universe_version='fixture'))
    audit=KiwoomCollectionAudit(session_date=session,observed_at=at,session_identity={},pagination={},unit_contract={},reconciliation=[],provider_calls={},blocked_concentration_markets={'KOSPI':['UNRESOLVED_BASIS_OR_TAXONOMY']})
    return KiwoomMarketContextCollection(section,audit,{})


@pytest.mark.parametrize('kind',['valid','unit','scope','actor_duplicate','session'])
def test_aggregate_only_never_grants_concentration(kind):
    from app.services.unified_aggregate_owners import aggregate_flow_reference
    r=flow_result()
    if kind=='unit':r.cross_section.market_flows[0].source_unit='1M_KRW'
    if kind=='scope':r.cross_section.market_flows[0].exchange_basis='KRX_ONLY'
    if kind=='actor_duplicate':r.cross_section.market_flows[0].actor='institution'
    if kind=='session':r.audit.session_date=date(2099,1,1)
    if kind=='valid':
        v=aggregate_flow_reference(r,session='2026-11-06')
        assert len(v['market_flows'])==6 and v['concentration']==[] and not v['concentration_eligible'] and not v['full_market_parent']
    else:
        with pytest.raises(ValueError):aggregate_flow_reference(r,session='2026-11-06')


@pytest.mark.parametrize('kind',['partial','missing','rollover','maturity','baseline','holiday'])
def test_manual_night_uses_typed_dwm_not_daily_fallback(kind):
    from tests.test_m12ds_r4_r1_night_eligibility import row
    r=row()
    if kind=='missing':r.pop('night_timeframes')
    if kind=='rollover':r['night_timeframes']['weekly']['contract_code']='other'
    if kind=='maturity':r['night_timeframes']['monthly']['contract_maturity']='2099-12'
    if kind=='baseline':r['reference_price']=999
    if kind=='holiday':r['session_date']='2026-09-20'
    source=dict(session=dict(market='us',assessment_date='2026-09-22',latest_completed_regular_session_date='2026-09-21'),
        fact_catalog=[dict(fact_id=r['fact_id'],fact_type='night_futures',as_of_date='2026-09-21',fields=deepcopy(r))],numeric_registry=[],night_futures=[r])
    result=render_night_dwm_preview(source,assessment_date='2026-09-22',eligible_refs=[r['fact_id']])
    assert result['NO_SEND'] and not result['full_market_parent']
    assert result['state']==('PARTIAL_DWM_EXPLICIT_PERIODS' if kind=='partial' else 'PARTIAL_NIGHT_UNAVAILABLE')


def selected_capture_args():
    from app.services.fresh_publication_replay import SELECTED_FRED
    from app.services.unified_source_policy import UnifiedSourcePolicy
    root=Path(__file__).resolve().parents[2]/'thesis-monitor-vnext-balanced-20261029/data/vnext/c5r-20261105/official-source'
    freeze=json.loads((root/'freeze.json').read_bytes());capture=json.loads((root/'capture.json').read_bytes());inputs={}
    for name in ('fred','ecos'):
        receipts=json.loads((root/name/'capture-summary.json').read_bytes())['receipts']
        if name=='fred':
            by={r['request']['params']['series_id']:r for r in receipts};receipts=[by[s] for s in SELECTED_FRED]
        bodies={r['artifact']:(root/name/r['artifact']).read_bytes() for r in receipts}
        inputs[name]=dict(receipts=receipts,bodies=bodies,body_hashes={k:__import__('hashlib').sha256(v).hexdigest() for k,v in bodies.items()})
    return dict(run_id=inputs['fred']['receipts'][0]['run_id'],
        run_started_at=datetime.fromisoformat(freeze['started_at']),as_of=datetime.fromisoformat(freeze['as_of']),
        acquisition_cutoff=datetime.fromisoformat(capture['ended_at']),providers=inputs,policy=UnifiedSourcePolicy(frozenset(('fred','ecos'))))


def test_selected_macro_exact_eight_original_responses():
    from app.services.fresh_publication_replay import replay_selected_market_publications,SELECTED_FRED
    result=replay_selected_market_publications(**selected_capture_args())
    assert result['contract']=='dated-selected-market-publication-replay-v1' and result['external_provider_calls']==0
    assert set(o['series_code'] for o in result['providers']['fred']['value']['observations'])==set(SELECTED_FRED)
    assert [o['series_code'] for o in result['providers']['ecos']['value']['observations']]==['USDKRW']
    for name in ('fred','ecos'):assert len(result['providers'][name]['original_receipts'])==(7 if name=='fred' else 1)


@pytest.mark.parametrize('kind',['unit','future'])
def test_selected_macro_semantic_changes_in_bound_response(kind):
    import hashlib
    from app.services.fresh_publication_replay import replay_selected_market_publications
    args=selected_capture_args();provider='ecos' if kind=='unit' else 'fred';data=args['providers'][provider]
    r=data['receipts'][0];name=r['artifact'];body=json.loads(data['bodies'][name])
    if kind=='unit':
        for row in body['KeyStatisticList']['row']:
            if row['KEYSTAT_NAME'] in {'원/달러 환율','원/달러 환율(종가)'}:row['UNIT_NAME']='USD'
    else:next(row for row in body['observations'] if row.get('value') not in (None,'.'))['date']='2099-12-31'
    raw=json.dumps(body).encode();data['bodies'][name]=raw;data['body_hashes'][name]=hashlib.sha256(raw).hexdigest();r['artifact_sha256']=data['body_hashes'][name]
    with pytest.raises(ValueError):replay_selected_market_publications(**args)


@pytest.mark.parametrize('kind',['extra_eia','missing_ecos','wrong_scope'])
def test_selected_macro_exact_provider_set_rejects_before_io(kind):
    from app.services.fresh_publication_replay import replay_selected_market_publications
    from app.services.unified_source_policy import UnifiedSourcePolicy
    at=datetime(2026,11,5,tzinfo=timezone.utc)
    providers={'fred':{},'ecos':{}}
    if kind=='extra_eia':providers['eia']={}
    if kind=='missing_ecos':providers.pop('ecos')
    with pytest.raises(ValueError):replay_selected_market_publications(run_id='test',run_started_at=at,as_of=at,
        acquisition_cutoff=at,providers=providers,policy=UnifiedSourcePolicy(frozenset(providers)),market_scope='KR8_ONLY' if kind=='wrong_scope' else 'ALL22')


@pytest.mark.parametrize('kind',['off','seal_hash','symlink','fake_reference','valid'])
def test_retained_sector_custody_entrypoint(tmp_path,kind):
    from app.services.dated_market_legacy_adapter import render_retained_component_sectors
    workspace=Path(__file__).resolve().parents[3]
    archive=workspace/'maintenance/20261110-c22m-v1/C22M_V1_SOURCE_FIELD_RECOVERY_AND_E2E_PLAN.zip'
    ref=workspace/'maintenance/20261106-c15/C15_US_DATED_SOURCE_REFERENCE.json'
    kwargs=dict(archive_path=archive,archive_sha256='d0e1e948425d231ac450803ac960533083ef7ceb04fa50a0072ee545aa429ff5',reference_path=ref,market='us',enabled=kind!='off')
    if kind=='seal_hash':kwargs['archive_sha256']='0'*64
    if kind=='symlink':
        link=tmp_path/'ref.json';link.symlink_to(ref);kwargs['reference_path']=link
    if kind=='fake_reference':
        value=json.loads(ref.read_bytes());value['value']['observations'][4]['change_pct']=999;value['value_sha256']=digest(value['value'])
        p=tmp_path/'fake.json';p.write_text(json.dumps(value));kwargs['reference_path']=p
    if kind=='valid':
        result=render_retained_component_sectors(**kwargs)
        assert result['scope']=='SOURCE_VERIFIED_FIELD_PREVIEW_ONLY' and not result['full_market_parent']
    else:
        with pytest.raises(ValueError):render_retained_component_sectors(**kwargs)


def test_night_actual_engine_closed_month_and_week(tmp_path):
    from datetime import timedelta
    from tests.test_krx_night_history_service import _bar
    from tests.test_m12ds_r4_r1_night_eligibility import row
    from app.services.krx_night_history_service import store_normalized_bar,build_same_contract_timeframes
    from app.services.market_session import is_exchange_session_date
    day=date(2025,12,30)
    while day<=date(2026,1,30):
        if is_exchange_session_date('XKRX',day):store_normalized_bar(tmp_path,_bar(day,contract='FUTURE',maturity='2026-03'))
        day+=timedelta(days=1)
    frames=build_same_contract_timeframes(tmp_path,instrument_root='KOSPI200',reference_date=date(2026,1,30),daily_baseline_date=date(2026,1,29),daily_baseline_close=101)
    assert frames is not None
    r=row();r.update(session_date='2026-01-30',reference_date='2026-01-29',expected_reference_date='2026-01-30',provider_raw_bas_dd='2026-01-30',
        night_source_record_id='2026-01-30:NIGHT:FUTURE',reference_source_record_id='2026-01-29:REGULAR:FUTURE',contract_maturity='2026-03',
        value=101,reference_price=101,change_value=0,change_pct=0,night_timeframes=frames.model_dump(mode='json'))
    source=dict(session=dict(market='us',assessment_date='2026-02-02',latest_completed_regular_session_date='2026-01-30'),
        fact_catalog=[dict(fact_id=r['fact_id'],fact_type='night_futures',as_of_date='2026-01-30',fields=deepcopy(r))],numeric_registry=[],night_futures=[r])
    result=render_night_dwm_preview(source,assessment_date='2026-02-02',eligible_refs=[r['fact_id']])
    assert result['state']=='DATED_DWM_COMPLETE'


def test_new_flow_role_and_text_hash_boundary():
    import hashlib
    from app.services.unified_aggregate_owners import kiwoom_aggregate_owner
    from app.services.unified_source_composition import SourceRole
    from app.services.unified_source_policy import UnifiedSourcePolicy
    role=SourceRole(key='unrelated_role',owner='kiwoom_pages',market='kr',symbol='*',acquisition_class='ATTEMPT_FRESH',mandatory=True,
        provider='kiwoom_rest',basis='query_time',session='2026-11-06')
    with pytest.raises(ValueError,match='original_market_role'):
        kiwoom_aggregate_owner(role=role,observed_at=datetime(2026,11,6,tzinfo=timezone.utc),max_pages=20,max_requests_per_page=1,
            policy=UnifiedSourcePolicy(frozenset(('kiwoom_rest',))),aggregate_flows_only=True)
    preview=render_component_sectors(reference())
    assert preview['text_sha256']==hashlib.sha256(preview['text'].encode()).hexdigest()


def test_sector_duplicate_reference_and_null_basis_boundary():
    ref=reference('kr');rows=ref['value']['sectors'];rows[1]['source_ref']=rows[0]['source_ref'];ref['value_sha256']=digest(ref['value'])
    with pytest.raises(ValueError,match='duplicate_source_ref'):render_component_sectors(ref)
    ref=reference('kr');rows=ref['value']['sectors'];rows.append(dict(rows[0],sector_code='new-null',source_ref='kiwoom:ka20003:KOSPI:new-null:2026-11-05',metric_role='sector_price_proxy',return_pct=None))
    ref['value_sha256']=digest(ref['value']);result=render_component_sectors(ref)
    assert all(i['status']=='AVAILABLE' for i in result['selected_items'])
