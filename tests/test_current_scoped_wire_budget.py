"""Synthetic configuration proves wire accounting, not real source admission."""
from datetime import datetime, timezone

import pytest

from app.services.scoped_routing_identity import ScopedSubject
from app.services.scoped_source_plan import HistoryCounts, ScopedConfig, compile_scoped_wire_contract


def wire(*, names=('FUTUREADS','FUTUREUS','654321'), retries=0, enabled_v3=True):
    subjects=tuple(ScopedSubject(ticker=t,market='kr' if i==2 else 'us',
        security_id='security-'+t,issuer_id=str(i+100).zfill(8 if i==2 else 10),
        venue='KRX' if i==2 else 'NASDAQ',currency='KRW' if i==2 else 'USD')
        for i,t in enumerate(names))
    counts=HistoryCounts(adjusted_daily=1000 if enabled_v3 else 700,
        adjusted_weekly=700,adjusted_monthly=300,unadjusted_weekly_valuation=300)
    config=ScopedConfig(subjects=subjects,kr_history=counts,us_history=counts,kr_max_pages=7 if enabled_v3 else 5)
    identities={s.ticker:dict(exchange=s.venue,canonical_security_id=s.security_id) for s in subjects}
    return compile_scoped_wire_contract(config=config,identities=identities,
        generation_id='synthetic-scoped-wire',at=datetime(2026,10,22,1,tzinfo=timezone.utc),
        code_sha='a'*40,provider_config_sha256='b'*64,retries=retries)


@pytest.mark.parametrize('enabled,ceiling',[(False,140),(True,152)])
def test_original_warmup_and_all_market_page_allowances(enabled,ceiling):
    result=wire(enabled_v3=enabled)
    plan=result['request_plan']
    assert len(plan.descriptors)==ceiling
    assert sum(d.max_transport_attempts for d in plan.descriptors)==ceiling
    assert len({d.group_id for d in plan.descriptors})==50
    assert len(result['stock_reads'])==12
    assert len(result['us_market_symbols'])==22
    assert all(r.count >= (300 if r.timeframe=='monthly' or not r.adjusted else 700)
        for r in result['stock_reads'])


def test_original_retry_accounting_not_client_only():
    plan=wire(retries=2)['request_plan']
    assert sum(d.max_transport_attempts for d in plan.descriptors)==456


def test_unseen_names_do_not_change_page_or_role_behavior():
    first,second=wire(),wire(names=('UNSEENADR','UNSEENUS','765432'))
    def signature(result):
        return [(r.market,r.role,r.count,r.max_pages,r.timeframe,r.adjusted) for r in result['stock_reads']]
    assert signature(first)==signature(second)
    assert len(first['request_plan'].descriptors)==len(second['request_plan'].descriptors)
    assert first['request_plan'].plan_sha256!=second['request_plan'].plan_sha256


@pytest.mark.parametrize('value',[-1,3,True,0.0])
def test_invalid_retry_bounds(value):
    with pytest.raises(ValueError,match='scoped_retry_bound'):
        wire(retries=value)
