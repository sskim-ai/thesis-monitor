"""Opt-in exhausted daily-source reference, never the required 1000-bar input."""
from copy import deepcopy
from datetime import date, datetime
import os
from pathlib import Path
from weakref import WeakKeyDictionary

from app.services.market_session import korea_market_session, us_market_session, _exchange_calendar
from app.services.ohlcv_feature_engine_service import build_multi_timeframe_feature_packet
from app.services.ohlcv_provider_integrity_service import inspect_normalized_ohlcv_rows
from app.services.unified_snapshot_contract import digest
from app.services.sealed_native_bridge import require_complete_stock_window

CONTRACT = 'source-exhausted-short-history-reference-v1'
CONSUMER = 'SCOPED_SHORT_HISTORY_REFERENCE_ONLY'
_ISSUED = WeakKeyDictionary()


def requirements():
    """Availability gates mirror the original engine, not new calculations.

    Some original formulas have a longer activation gate than their numeric
    dependency (MACD signal, stochastic, OBV). Both remain unchanged.
    """
    out = {'close': 1}
    out.update({f'return_{n}': n+1 for n in (1,5,10,20,60,120,252)})
    out.update({f'{kind}_{n}': n for n in (20,60,120,252) for kind in (
        'rolling_high','rolling_low','distance_from_high','distance_from_low','max_drawdown')})
    out.update({f'{kind}_{n}': n for n in (5,10,20,50,100,200) for kind in ('sma','close_vs_sma','ema')})
    out.update({name: 21 for name in ('higher_high_count_20','lower_low_count_20','trend_sequence_20',
        'realized_volatility_20','donchian_high_20','donchian_low_20','donchian_breakout_20')})
    out.update({name:34 for name in ('macd_12_26','macd_signal_9','macd_histogram','macd_state')})
    out.update({name:15 for name in ('rsi_14','rsi_state','mfi_14')})
    out.update({name:14 for name in ('atr_14','atr_pct_14')})
    out.update({name:20 for name in ('bollinger_20_2_mid','bollinger_20_2_upper','bollinger_20_2_lower',
        'bollinger_20_2_state','volume_ratio_20','obv','cmf_20')})
    out.update({name:28 for name in ('adx_14','plus_di_14','minus_di_14','dmi_state')})
    out.update(gap_latest=2,roc_10=11,roc_20=21,stochastic_k_14=16,stochastic_d_3=16)
    return out


def review_rows(*, read, cutoff, all_rows, source_receipt, source_pages):
    """Pure review. Only live custody can turn this data into a capability."""
    if (read.market not in {'us','kr'} or read.timeframe!='daily' or read.role!='adjusted_daily'
            or not read.adjusted or read.count!=1000 or cutoff.utcoffset() is None or not source_pages):
        raise ValueError('short_reference_original_daily_contract_required')
    state=(korea_market_session if read.market=='kr' else us_market_session)(cutoff)
    target=state.latest_completed_regular_session_date.isoformat()
    if read.latest_completed_session!=target:
        raise ValueError('short_reference_session_mismatch')
    dates=[r['date'] for r in all_rows]
    query=date.fromisoformat(read.query_date[:4]+'-'+read.query_date[4:6]+'-'+read.query_date[6:8])
    if (not dates or len(set(dates))!=len(dates) or max(dates)>query.isoformat()
            or (dates!=sorted(dates) and dates!=sorted(dates,reverse=True))):
        raise ValueError('short_reference_source_order_or_identity_gap')
    rows=sorted((dict(r) for r in all_rows if r['date']<=target),key=lambda r:r['date'])
    if not 0<len(rows)<1000 or rows[-1]['date']!=target:
        raise ValueError('short_reference_short_current_window_required')
    calendar='XKRX' if read.market=='kr' else 'XNYS'
    expected=[d.date().isoformat() for d in _exchange_calendar(calendar).sessions_in_range(rows[0]['date'],target)]
    if [r['date'] for r in rows]!=expected:
        raise ValueError('short_reference_calendar_coverage_gap')
    inspection=inspect_normalized_ohlcv_rows(rows,timeframe='daily',cutoff=date.fromisoformat(target))
    if not inspection.valid:
        raise ValueError('short_reference_original_quality_failed')
    window=require_complete_stock_window(read,source_receipt,rows)
    last=source_receipt['pages'][-1]['response_continuation']
    if not window['source_exhausted'] or last!={'cont_yn':'N','next_key':''}:
        raise ValueError('short_reference_source_not_exhausted')
    if [p['sha256'] for p in source_pages]!=[p['source_sha256'] for p in source_receipt['pages']]:
        raise ValueError('short_reference_page_identity_mismatch')
    packet=build_multi_timeframe_feature_packet(ticker=read.subject,periods={'daily':rows},cutoff=date.fromisoformat(target))
    facts={f.semantic:f.model_dump(mode='json') for f in packet.daily.facts}
    expected_features=requirements()
    if set(facts)-set(expected_features):
        raise ValueError('short_reference_engine_catalog_drift')
    ledger=[dict(semantic=name,activation_minimum=n,
        status='AVAILABLE' if name in facts else 'HISTORY_INSUFFICIENT' if len(rows)<n else 'UNAVAILABLE_ENGINE_PREDICATE')
        for name,n in sorted(expected_features.items())]
    value=dict(contract=CONTRACT,consumer=CONSUMER,security_id=read.canonical_security_id,entry_id=read.entry_id,
        market=read.market,calendar=calendar,cutoff=cutoff.isoformat(),target_session=target,
        adjustment_basis='ADJUSTED_OHLCV',currency='KRW' if read.market=='kr' else 'USD',
        all_rows_sha256=digest(all_rows),rows_sha256=digest(rows),actual_bars=len(rows),
        source_exhausted=True,source_pages=source_pages,excluded_after_session=len(all_rows)-len(rows),
        legal_listing_inception='UNPROVEN',coverage_before_first_source_bar='UNPROVEN',
        facts=facts,availability=ledger,original_quality=inspection.model_dump(mode='json'),
        technical_signal=False,projected_1000=False,completed_price_authority=False,financial_use=False,
        valuation_use=False,economic_use=False,native_use=False,full22_native=False,D01_D02=False,model_use=False)
    return rows,value


def _current(parent, dispatcher, entry_id):
    from app.services import current_scoped_source_results as s
    from app.services.current_scoped_source_dispatch import CurrentScopedDispatcher
    if type(dispatcher) is not CurrentScopedDispatcher:
        raise ValueError('short_reference_original_dispatcher_required')
    binding=s._CAPTURES.get(dispatcher)
    if not binding or binding['parent'] is not parent:
        raise ValueError('short_reference_live_capture_required')
    parent_receipt,spec,plan,stock,capture,worker=s._context(parent,binding['wire'],binding['stock_plan'],
        dispatcher,binding['capture'],binding['worker'])
    commands,replays=s._worker_custody(parent,dispatcher,plan,stock,capture,worker)
    ordinal,read=next((i,r) for i,r in enumerate(stock.reads,1) if r.entry_id==entry_id)
    original=s._json(worker/'stocks',f'role-{ordinal:03d}.receipt.json')
    proof=s._stock_role(stock,read,original,worker/'stocks',dispatcher,capture,plan,replays.get(entry_id))
    if proof['two_original_owner_replays']!='PASS' or proof['original_window_validation']['status']!='PASS':
        raise ValueError('short_reference_original_replay_required')
    name=f'short-reference-{ordinal:03d}.json'
    raw=s._read(worker,name);data=s._json(worker,name)
    result=dict(status='SHORT_REFERENCE_REPLAY_PASS',entry_id=entry_id,artifact=name,sha256=s._sha(raw))
    matches=[c for c in commands if c['command']=={'short_reference':entry_id}
        and c['result_sha256']==digest(result) and not c['sealed_receipts']]
    frozen_path=Path(binding['bridge'].frozen)
    frozen=s._json(frozen_path.parent,frozen_path.name)
    if len(matches)!=1 or data['parser_pins']!=frozen['external_pins']:
        raise ValueError('short_reference_original_parser_custody_required')
    rows,review=review_rows(read=read,cutoff=stock.frozen_at,all_rows=data['all_rows'],
        source_receipt=original,source_pages=data['receipt']['source_pages'])
    if review!=data['receipt'] or rows!=data['rows']:
        raise ValueError('short_reference_replay_drift')
    subject=next(s for s in spec.config.subjects if s.security_id==read.canonical_security_id)
    return dict(review,issuer_id=subject.issuer_id,generation_id=plan.generation_id,
        source_generation_id=original['run_id'],observed_at=original['completed_at'],
        parent_receipt_sha256=digest(parent_receipt),source_receipt_sha256=digest(original),
        expires_at=parent_receipt['expires_at'])


class ShortHistoryReference:
    __slots__=('__weakref__',)


def issue(parent, *, dispatcher, entry_id, enabled=False):
    if enabled is not True: raise ValueError('short_reference_feature_off')
    value=_current(parent,dispatcher,entry_id)
    cap=ShortHistoryReference()
    _ISSUED[cap]=dict(parent=parent,dispatcher=dispatcher,entry_id=entry_id,value=deepcopy(value),pid=os.getpid())
    return cap


def consume(parent, cap, *, dispatcher, entry_id, security_id, generation_id, consumer=CONSUMER):
    if type(cap) is not ShortHistoryReference or cap not in _ISSUED or consumer!=CONSUMER:
        raise ValueError('short_reference_issued_capability_and_consumer_required')
    stored=_ISSUED[cap]
    if (stored['parent'] is not parent or stored['dispatcher'] is not dispatcher
            or stored['entry_id']!=entry_id or stored['pid']!=os.getpid()):
        raise ValueError('short_reference_lifetime_mismatch')
    value=_current(parent,dispatcher,entry_id)
    if value!=stored['value'] or value['security_id']!=security_id or value['generation_id']!=generation_id:
        raise ValueError('short_reference_binding_drift')
    return dict(deepcopy(value),receipt_sha256=digest(value))


def revoke(cap):
    if type(cap) is not ShortHistoryReference or cap not in _ISSUED or _ISSUED[cap]['pid']!=os.getpid():
        raise ValueError('short_reference_unissued_or_revoked')
    del _ISSUED[cap]
