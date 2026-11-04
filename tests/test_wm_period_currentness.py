"""P3B only: calendar hypotheses never become provider or live authority."""
from copy import deepcopy
from datetime import datetime, timezone
from types import SimpleNamespace

import pytest

from app.services import wm_period_currentness as w
from app.services import current_scoped_source_results as owner
from app.services import registered_source_batch as batch
from app.services.unified_snapshot_contract import digest


def case(*, timeframe='weekly', market='us', target='2026-11-03', labels=('2026-10-26','2026-11-02'), observed='2026-11-04T00:57:29+00:00'):
    fields=dict(market=market, exchange='NY' if market=='us' else 'KRX', timeframe=timeframe,
        latest_completed_session=target, count=len(labels), provider='kiwoom',
        api_id=('usa06013' if timeframe=='weekly' else 'usa06014') if market=='us' else ('ka10082' if timeframe=='weekly' else 'ka10083'),
        entry_id=market+':FICTIONAL:adjusted_'+timeframe,canonical_security_id='fictional-identity')
    read=SimpleNamespace(**fields);read.model_dump=lambda **kwargs:fields.copy()
    rows=[dict(date=d,open=1,high=2,low=1,close=2,volume=10) for d in labels]
    receipt=dict(entry=fields.copy(),status='CAPTURED',normalized_sha256=digest(rows),
        completed_at=observed,run_id='original',acquisition_id='original-capture',
        pages=[dict(entry_id=read.entry_id,provider='kiwoom',source_sha256='a'*64)])
    proof=dict(status='ORIGINAL_SOURCE_ROLE_REPLAY_PASS',two_original_owner_replays='PASS',
        original_role_validation=dict(status='PASS',current_session_aligned=False),
        original_window_validation=dict(status='PASS'),requested_count_reached=True)
    return read,rows,receipt,proof,datetime.fromisoformat(observed),datetime.fromisoformat(observed)


def view(c, **kwargs):
    read,rows,_,_,observed,cutoff=c
    return w.period_view(rows,read=read,observed_at=observed,cutoff=cutoff,**kwargs)


def test_week_start_is_provisional_not_completed_or_authorized():
    c=case();result=view(c,label_basis='FIRST_TRADING_SESSION')
    assert result['latest_calendar_state']=='PROVISIONAL_ACTIVE_PERIOD'
    assert result['hypothetical_closed_rows']==1 and result['hypothetical_provisional_rows']==1
    assert not result['source_only_eligible'] and not result['technical_signal']
    assert c[3]['original_role_validation']['current_session_aligned'] is False


def test_month_start_retains_raw_count_and_excludes_active_from_closed():
    result=view(case(timeframe='monthly',labels=('2026-10-01','2026-11-02')),label_basis='FIRST_TRADING_SESSION')
    assert result['raw_rows']==2 and result['hypothetical_closed_rows']==1
    assert result['period_end']=='2026-11-30' and result['latest_calendar_state']=='PROVISIONAL_ACTIVE_PERIOD'


def test_holiday_week_uses_first_trading_session_not_monday():
    c=case(target='2026-09-08',labels=('2026-09-08',),observed='2026-09-09T01:00:00+00:00')
    assert view(c,label_basis='FIRST_TRADING_SESSION')['first_trading_session']=='2026-09-08'
    with pytest.raises(ValueError):view(case(target='2026-09-08',labels=('2026-09-07',),observed='2026-09-09T01:00:00+00:00'),label_basis='FIRST_TRADING_SESSION')


def test_closed_week_and_month_are_not_blanket_provisional():
    c=case(target='2026-10-30',labels=('2026-10-26',),observed='2026-10-31T01:00:00+00:00')
    assert view(c,label_basis='FIRST_TRADING_SESSION')['latest_calendar_state']=='CLOSED_PERIOD'
    c=case(timeframe='monthly',target='2026-10-30',labels=('2026-10-01',),observed='2026-10-31T01:00:00+00:00')
    assert view(c,label_basis='FIRST_TRADING_SESSION')['latest_calendar_state']=='CLOSED_PERIOD'


def test_week_month_turn_stale_previous_period_rejected():
    for c in (case(labels=('2026-10-26',)),case(timeframe='monthly',labels=('2026-10-01',))):
        with pytest.raises(ValueError,match='wm_stale_latest_period'):view(c)


def test_wrong_exchange_and_future_label_rejected():
    c=case();c[0].exchange='KRX'
    with pytest.raises(ValueError,match='wm_exchange_mismatch'):view(c)
    with pytest.raises(ValueError):view(case(labels=('2026-11-09',)))


def test_unknown_label_contract_is_not_inferred_from_matching_pattern():
    c=case();result=view(c)
    assert result['label_basis']=='UNKNOWN' and result['hypothetical_closed_rows'] is None
    with pytest.raises(ValueError,match='wm_provider_label_semantics_unverified'):
        w.source_period_proof(c[1],read=c[0],receipt=c[2],original_proof=c[3],cutoff=c[5],parser_pins={})
    assert not w._LABEL_CONTRACTS


def test_unknown_basis_and_wrong_first_session_rejected():
    with pytest.raises(ValueError):view(case(),label_basis='caller-approved')
    with pytest.raises(ValueError,match='wm_provider_label_basis_mismatch'):
        view(case(labels=('2026-11-03',)),label_basis='FIRST_TRADING_SESSION')


def test_insufficient_history_duplicate_and_bad_dates_rejected():
    c=case();c[0].count=3
    with pytest.raises(ValueError):view(c)
    for labels in (('2026-11-02','2026-11-02'),('2026-11-03','2026-11-02'),('not-date',)):
        with pytest.raises(ValueError):view(case(labels=labels))


def test_observation_timezone_and_completed_session_are_bound():
    c=case();c=list(c);c[4]=c[4].replace(tzinfo=None)
    with pytest.raises(ValueError):view(c)
    with pytest.raises(ValueError,match='wm_completed_daily_session_mismatch'):
        view(case(target='2026-11-02'))


def test_original_receipt_and_hash_mismatch_fail_before_semantics():
    for mutation in ('sha','entry','pages'):
        c=case()
        if mutation=='sha':c[2]['normalized_sha256']='0'*64
        elif mutation=='entry':c[2]['entry']['exchange']='ND'
        else:c[2]['pages']=[]
        with pytest.raises(ValueError,match='wm_original_source_binding'):
            w.source_period_proof(c[1],read=c[0],receipt=c[2],original_proof=c[3],cutoff=c[5],parser_pins={})


def test_original_quality_and_replay_are_not_replaced_by_calendar():
    c=case();c[3]['original_window_validation']['status']='GAP'
    with pytest.raises(ValueError,match='wm_original_replay_required'):
        w.source_period_proof(c[1],read=c[0],receipt=c[2],original_proof=c[3],cutoff=c[5],parser_pins={})


def test_kr_and_us_use_different_holiday_calendars():
    result=view(case(market='kr',target='2026-09-07',labels=('2026-09-07',),observed='2026-09-07T07:00:00+00:00'),label_basis='FIRST_TRADING_SESSION')
    assert result['calendar']=='XKRX' and result['first_trading_session']=='2026-09-07'


def test_live_owner_and_cold_prerequisites_cannot_be_resurrected(monkeypatch):
    class Unissued:
        pass
    with pytest.raises(ValueError,match='scoped_role_live_capture_required'):
        owner.issue_source_result(Unissued(),dispatcher=Unissued(),entry_id='fictional')
    fake=SimpleNamespace(batch_id='fictional',roles=(),security_ids=(),sessions=(),public=lambda:{})
    monkeypatch.setattr(batch.Batch,'parse',lambda _:fake)
    data=dict(batch={},contract='registered-source-batch-cold-v1',batch_id='fictional',
        batch_sha256=digest({}),expected_reads=[dict(entry_id='fictional')],
        receipts=[dict(contract='current-scoped-role-source-receipt-v2-wm')],artifacts=[{}])
    with pytest.raises(ValueError,match='cold_wm_v2_semantic_readback_not_qualified'):
        batch.validate_cold_roles(data,lambda _:pytest.fail('no reads without accepted contract'))


def test_daily_policy_unchanged_and_no_ticker_specific_policy():
    from app.services import unified_stock_acquisition as original
    import inspect
    text=inspect.getsource(original.validate_role)
    assert 'max(dates) == read.latest_completed_session' in text
    with pytest.raises(ValueError,match='wm_timeframe_required'):
        c=case();c[0].timeframe='daily';view(c)
    policy=inspect.getsource(w)
    assert all(ticker not in policy for ticker in ('IBM','003690','2026-11-03'))


def test_caller_cannot_supply_approved_spec_and_dates_are_not_rewritten():
    c=case();before=deepcopy(c[1]);view(c,label_basis='FIRST_TRADING_SESSION')
    assert c[1]==before
    with pytest.raises(TypeError):
        w.source_period_proof(c[1],read=c[0],receipt=c[2],original_proof=c[3],cutoff=c[5],parser_pins={},approved=True)
