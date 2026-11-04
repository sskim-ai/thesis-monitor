"""Synthetic property tests, not real issuer eligibility."""
from datetime import datetime, timedelta, timezone
from types import SimpleNamespace

import pytest
from app.services.completed_session_projection import project_completed_rows, finite_history
from app.services.market_session import korea_market_session, us_market_session
from app.services.scoped_source_plan import ScopedCaptureSelection, compile_scoped_wire_contract
from test_current_scoped_source_owner import setup_parent
from app.services import current_scoped_source_owner as owner


def inputs(market='kr', ticker='UNSEEN', cutoff=None):
    cutoff=cutoff or datetime(2026,10,22,3,tzinfo=timezone.utc)
    state=(korea_market_session if market=='kr' else us_market_session)(cutoff)
    target=state.latest_completed_regular_session_date
    rows=[dict(date=(target-timedelta(days=i)).isoformat(),open=10.,high=12.,low=9.,close=11.,volume=100.) for i in range(6)]
    read=SimpleNamespace(timeframe='daily',market=market,latest_completed_session=target.isoformat(),
        query_date=cutoff.strftime('%Y%m%d'),count=5,entry_id=f'{market}:{ticker}:adjusted_daily',
        canonical_security_id=f'security:{ticker}',adjusted=True)
    return rows,read,cutoff


@pytest.mark.parametrize('market,ticker', [('kr','111111'),('us','NEWCOMMON'),('us','NEWADS'),('kr','NEWLIST')])
def test_equivalent_evidence_not_ticker(market,ticker):
    rows,read,cutoff=inputs(market,ticker)
    selected,proof=project_completed_rows(rows,read=read,cutoff=cutoff,source_pages=[{'sha256':'a'*64}])
    assert len(selected)==5 and proof['completed_unique_rows']==6
    assert not any(proof[k] for k in ('raw_rewritten','technical_signal','economic_use','native_use'))


@pytest.mark.parametrize('cutoff',[datetime(2026,10,22,3,tzinfo=timezone.utc),datetime(2026,10,23,3,tzinfo=timezone.utc)])
def test_uncompleted_before_truncation_and_dynamic_calendar(cutoff):
    rows,read,cutoff=inputs(cutoff=cutoff)
    rows.insert(0,{**rows[0],'date':cutoff.date().isoformat(),'volume':0})
    selected,proof=project_completed_rows(rows,read=read,cutoff=cutoff,source_pages=[{'sha256':'a'*64}])
    assert len(selected)==5 and proof['completed_unique_rows']==6 and len(proof['excluded'])==1
    assert selected[-1]['date']==read.latest_completed_session


@pytest.mark.parametrize('mutation',['duplicate','order','invalid_older','wrong_calendar','future','short'])
def test_invalid_source_not_hidden_by_selection(mutation):
    rows,read,cutoff=inputs()
    if mutation=='duplicate': rows.append(rows[-1])
    elif mutation=='order': rows[1],rows[2]=rows[2],rows[1]
    elif mutation=='invalid_older': rows[-1]['high']=1
    elif mutation=='wrong_calendar': read.latest_completed_session='2000-01-01'
    elif mutation=='future': rows[0]['date']='2099-01-01'
    else: rows=rows[:4]
    with pytest.raises(ValueError): project_completed_rows(rows,read=read,cutoff=cutoff,source_pages=[{'sha256':'a'*64}])


def test_basis_preserved_not_promoted_and_finite_history():
    rows,read,cutoff=inputs()
    read.adjusted=False
    _,proof=project_completed_rows(rows,read=read,cutoff=cutoff,source_pages=[{'sha256':'a'*64}])
    assert not proof['adjusted']
    read.count=1000
    d=finite_history(read,available_rows=73,exhausted=True,first_date=rows[-1]['date'],last_date=rows[0]['date'])
    assert d['status']=='FINITE_LISTING_HISTORY' and not d['native_use']
    assert d['legal_listing_date']=='NOT_INDEPENDENTLY_VERIFIED'


def test_explicit_subset_parent_preserves_registered_scope_and_budget(tmp_path):
    args,_,identities=setup_parent(tmp_path,three_types=True)
    spec=args['spec']
    selection=ScopedCaptureSelection(stock_markets=('kr',),stock_roles=('adjusted_daily',),market_contexts=('kr',),us_completed_closes=False)
    spec=spec.model_copy(update={'config':spec.config.model_copy(update={'kr_max_pages':20,'capture_selection':selection}), 'maximum_attempts':160})
    wire=compile_scoped_wire_contract(config=spec.config,identities=identities,generation_id=spec.generation_id,
        at=spec.cutoff,code_sha=spec.code_sha,provider_config_sha256=spec.provider_config_sha256,retries=0)
    parent=owner.issue_parent(**{**args,'spec':spec,'plan':wire['request_plan']})
    assert len(spec.config.subjects)==3 and len(wire['stock_reads'])==1
    assert owner.resolve_parent(parent)['planned_attempts']==56
    assert not wire['us_market_symbols'] and len(wire['price_pairs'])==3
    assert not owner.resolve_parent(parent)['full22_native']
