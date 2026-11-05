import copy
from datetime import datetime,timezone

import pytest
from sqlmodel import SQLModel,Session,create_engine
from app.services.unified_persisted_owner_bridge import project,MODELS,project_retained_publications
from app.services.unified_source_policy import UnifiedSourcePolicy
from app.services.unified_snapshot_contract import digest
from app.services.canonical_market_projection import PUBLICATIONS,_publication_facts
from app.services.canonical_source_composition import validate_fresh_context_generation
from app.services.historical_indicator_reuse import _calendar_periods,requirements
from app.services.vnext_dated_calendar import POLICY
from app.services.unified_source_composition import A,B,D,SourceRole,SourceInput,_resolve

NOW=datetime(2026,11,5,tzinfo=timezone.utc)
POLICY_SET=UnifiedSourcePolicy(frozenset(('fred','eia','ecos','federal_reserve','ohlcv_analyst')))

@pytest.fixture
def empty_packet():
    engine=create_engine('sqlite://')
    SQLModel.metadata.create_all(engine,tables=[m.__table__ for m in MODELS.values()])
    try:
        with Session(engine) as session:
            docs={}
            for role in PUBLICATIONS:
                p=project(session,role=role,ticker='*',cutoff=NOW,policy=POLICY_SET)
                docs['class-c/'+role+'.json']=dict(source_sha256=digest(p),projection=p)
        return dict(publication_context=docs,class_c_versions={n:d['source_sha256'] for n,d in docs.items()})
    finally:engine.dispose()

@pytest.mark.parametrize('role',PUBLICATIONS)
def test_original_optional_empty_owner_has_bound_denial(empty_packet,role):
    facts,denials,_=_publication_facts(empty_packet,NOW.date())
    assert not facts
    assert len(denials)==5
    assert any(role in d['path'] and d['version'] for d in denials)

@pytest.mark.parametrize('field,value',[('role','other'),('eligible',True),('version','0'*64),
    ('projection_sha256','0'*64),('records',[{'unbound':True}])])
def test_empty_denial_cannot_change_identity_or_hash(empty_packet,field,value):
    p=empty_packet['publication_context']['class-c/energy.json']['projection'];p[field]=value
    with pytest.raises(ValueError,match='denial_not_owner_bound'):_publication_facts(empty_packet,NOW.date())

@pytest.mark.parametrize('klass',[A,B])
def test_mandatory_source_still_cannot_use_optional_denial(tmp_path,klass):
    r=SourceRole(key='required',owner='original',market='us',symbol='*',acquisition_class=klass,
        mandatory=True,provider='fred',basis='original',session='original')
    item=SourceInput(role='required',run_id='run',acquisition_class=D,denial='no_source')
    with pytest.raises(ValueError,match='mandatory_source_unavailable'):
        _resolve(item,r,root=tmp_path,run_id='run',start=NOW,cutoff=NOW,attempt_id=None,policy=POLICY_SET,owners={})

@pytest.mark.parametrize('change',['none','run','policy'])
def test_original_generation_guard(change):
    inputs=dict(run_id='source-original',run_started_at=NOW,policy=POLICY_SET)
    kwargs=dict(parent_run_id='source-original',started_at=NOW,source_policy_sha256=digest(sorted(POLICY_SET.allowed_providers)))
    if change=='run':kwargs['parent_run_id']='different-run'
    if change=='policy':kwargs['source_policy_sha256']='0'*64
    if change=='none':validate_fresh_context_generation(inputs,**kwargs)
    else:
        with pytest.raises(ValueError,match='generation_or_policy'):validate_fresh_context_generation(inputs,**kwargs)

@pytest.mark.parametrize('day',['2026-06-03','2026-07-17'])
def test_existing_calendar_correction_not_source_gap(day):
    legacy=_calendar_periods('kr','2026-05-01','2026-11-05','daily')
    corrected=_calendar_periods('kr','2026-05-01','2026-11-05','daily',POLICY)
    assert day in legacy and day not in corrected

@pytest.mark.parametrize('market,timeframe,policy',[('kr','weekly',POLICY),('us','daily',POLICY),('kr','daily','unknown')])
def test_opt_in_does_not_change_other_timeframes(market,timeframe,policy):
    with pytest.raises(ValueError,match='daily_kr_only'):_calendar_periods(market,'2026-01-01','2026-11-05',timeframe,policy)

def test_retained_adapter_does_not_accept_raw_provider_result():
    with pytest.raises(ValueError,match='envelope_invalid'):
        project_retained_publications({'provider':'fred'},bodies={},cutoff=NOW,policy=POLICY_SET)

def test_optional_provider_identity_not_interchangeable():
    from app.services.unified_class_c_owners import MACRO_ROLES
    from app.macro.providers.fred import FRED_SERIES
    from app.macro.providers.eia import EIA_SERIES
    assert MACRO_ROLES['kr_overnight_cross_assets']==('ohlcv_analyst',)
    assert MACRO_ROLES['energy']==('eia',) and 'DCOILWTICO' in FRED_SERIES
    assert 'DCOILWTICO' not in EIA_SERIES

def test_timeframe_reference_periods_are_not_daily_translation():
    w=requirements(['RETURN_20D','RETURN_60D','DRAWDOWN_52W'],'weekly')
    assert w['RETURN_20D']['period_unit']=='WEEK_BARS'
    assert w['RETURN_60D']['coverage_reference_bars']==60
    assert w['DRAWDOWN_52W']['coverage_reference_bars']==252
