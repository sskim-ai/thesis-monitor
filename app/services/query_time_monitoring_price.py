"""Versioned chart snapshot, never strict close, valuation or current authority."""
from datetime import datetime
from zoneinfo import ZoneInfo

from app.services.ohlcv_provider_integrity_service import inspect_normalized_ohlcv_rows
from app.services.unified_snapshot_contract import digest

CONTRACT = 'query-time-monitoring-price-v1'


def project_monitoring_rows(rows, *, read, frozen_at, observed_at, source_pages):
    if (read.timeframe != 'daily' or not rows or frozen_at.utcoffset() is None
            or observed_at.utcoffset() is None or observed_at < frozen_at
            or not source_pages or any(len(p['sha256']) != 64 for p in source_pages)):
        raise ValueError('monitoring_snapshot_source_identity_required')
    market_date = observed_at.astimezone(ZoneInfo('Asia/Seoul' if read.market == 'kr' else 'America/New_York')).date()
    ordered = sorted(rows, key=lambda r: r['date'])
    latest = ordered[-1]
    if str(latest['date']) < read.latest_completed_session:
        raise ValueError('monitoring_snapshot_stale_source_not_current')
    selected = ordered[-read.count:]
    window = inspect_normalized_ohlcv_rows(selected, timeframe='daily', cutoff=market_date)
    quote = inspect_normalized_ohlcv_rows([latest], timeframe='daily', cutoff=market_date)
    unique_latest = sum(str(r['date']) == str(latest['date']) for r in rows) == 1
    eligible = window.valid and len(selected) == read.count
    observation = None
    if quote.valid and unique_latest:
        observation = dict(contract=CONTRACT, semantics='QUERY_TIME_SNAPSHOT', finality_claim='NOT_CLAIMED',
            strict_close_eligible=False, security_id=read.canonical_security_id, ticker=read.subject,
            market=read.market, exchange=read.exchange, currency='KRW' if read.market=='kr' else 'USD', provider=read.provider, owner=read.owner,
            api_id=read.api_id, route=read.route, adjusted=read.adjusted,
            basis='ADJUSTED_CHART' if read.adjusted else 'UNADJUSTED_CHART',
            source_session=str(latest['date']), latest_completed_session=read.latest_completed_session,
            observed_at=observed_at.isoformat(), frozen_at=frozen_at.isoformat(),
            value=latest['close'], row_sha256=digest(latest), source_pages=source_pages,
            financial_use=False, valuation_use=False, native_use=False, technical_signal=False)
        observation['sha256'] = digest(observation)
    return dict(contract=CONTRACT, rows=selected, rows_sha256=digest(selected),
        observation=observation, window_eligible=eligible,
        status='MONITORING_SNAPSHOT_AVAILABLE' if quote.valid and unique_latest else 'MONITORING_SNAPSHOT_UNAVAILABLE_CHART_QUALITY',
        latest_violations=[i.violation.value for i in quote.issues]+([] if unique_latest else ['DUPLICATE_LATEST_ROW']),
        window_violations=sorted({i.violation.value for i in window.issues}),
        strict_close_eligible=False, finality_claim='NOT_CLAIMED',
        current_source_authority=False, native_use=False)


def consume_monitoring_price(value, *, security_id, adjusted, use='SOURCE_ONLY_DISPLAY'):
    observation = value['observation']
    if observation is None:
        raise ValueError('monitoring_snapshot_unavailable')
    core = dict(observation); expected = core.pop('sha256')
    if (value['contract'] != CONTRACT or digest(core) != expected
            or observation['contract'] != CONTRACT or observation['security_id'] != security_id
            or observation['adjusted'] is not adjusted or observation['strict_close_eligible'] is not False
            or observation['finality_claim'] != 'NOT_CLAIMED'
            or value['strict_close_eligible'] is not False or value['finality_claim'] != 'NOT_CLAIMED'
            or any(observation[k] is not False for k in ('valuation_use','financial_use','native_use','technical_signal'))
            or use not in ('SOURCE_ONLY_DISPLAY','SOURCE_ONLY_TECHNICAL_REFERENCE')
            or (use == 'SOURCE_ONLY_TECHNICAL_REFERENCE' and not value['window_eligible'])):
        raise ValueError('monitoring_snapshot_scope_identity_or_finality_denied')
    return dict(observation)


def render_monitoring_price(value, *, security_id, adjusted):
    """Source-only display adapter; never a strict valuation denominator."""
    if value['observation'] is None:
        return 'UNAVAILABLE: CHART_SOURCE_QUALITY'
    observation=consume_monitoring_price(value,security_id=security_id,adjusted=adjusted)
    return (f"{observation['value']} {observation['currency']} | QUERY_TIME_SNAPSHOT | "
        f"source session {observation['source_session']} | observed {observation['observed_at']} | "
        'finality NOT_CLAIMED')


def validate_monitoring_readback(value, *, rows, read, frozen_at, observed_at, source_pages):
    actual = project_monitoring_rows(rows, read=read, frozen_at=frozen_at,
        observed_at=observed_at, source_pages=source_pages)
    if actual != value:
        raise ValueError('monitoring_snapshot_readback_mismatch')
    if actual['observation'] is not None:
        consume_monitoring_price(actual, security_id=read.canonical_security_id, adjusted=read.adjusted)
    return dict(status='MONITORING_SNAPSHOT_COLD_PASS_NOT_OWNER_REISSUANCE',
        available=actual['observation'] is not None, window_eligible=actual['window_eligible'],
        strict_close_eligible=False, finality_claim='NOT_CLAIMED', current_source_authority=False)


def replay_retained_monitoring(*, worker_root, capture_root, frozen, read, dispatcher_plan, external_root):
    """Original retained raw/parser/custody replay, never a live Owner grant."""
    import json
    from types import SimpleNamespace
    from app.services.unified_stock_acquisition import bound_artifact, decode_owned_role
    from app.services.wm_period_currentness import pure_parser
    from app.services.sealed_fresh_dispatch import consume_bound_result
    from app.services.unified_run_artifacts import sha256_bytes
    stock=frozen['stock_plan'];reads=stock['reads']
    ordinal=next(i for i,r in enumerate(reads,1) if r==read.model_dump(mode='json'))
    receipt=json.loads((worker_root/'stocks'/f'role-{ordinal:03d}.receipt.json').read_bytes())
    plan=SimpleNamespace(run_id=stock['run_id'],acquisition_id=stock['acquisition_id'],
        frozen_at=datetime.fromisoformat(stock['frozen_at']),model_dump=lambda **_:stock)
    decode_owned_role(plan,read,receipt,lambda path,s:bound_artifact(worker_root/'stocks',path,s))
    replays=[]
    for number in (1,2):
        raw=(worker_root/f'raw-owner-replay-{number}.json').read_bytes();rows=__import__('json').loads(raw)
        commands=[json.loads(p.read_bytes()) for p in worker_root.glob('command-*.json')]
        expected=dict(status='REPLAY_RESULT',rows=rows,sha256=sha256_bytes(raw))
        if len([c for c in commands if c['command']=={'replay':number}
                and c['result_sha256']==digest(expected) and not c['sealed_receipts']])!=1:
            raise ValueError('monitoring_retained_original_replay_custody')
        row=next(r for r in rows if r['entry_id']==read.entry_id)
        if row['network_calls']!=0 or row['normalized_sha256']!=receipt['normalized_sha256']:
            raise ValueError('monitoring_retained_original_replay_identity')
        replays.append(rows)
    if replays[0]!=replays[1]:raise ValueError('monitoring_retained_replays_disagree')
    parser=pure_parser(external_root,frozen['external_pins']);all_rows=[];pages=[]
    keys=['result_list','output','data'] if read.market=='us' else ['stk_dt_pole_chart_qry','output','data']
    for page in receipt['pages']:
        raw=bound_artifact(worker_root/'stocks',page['artifact'],page['source_sha256'])
        slots=[d for d in dispatcher_plan.descriptors if d.consumer_role=='stock:'+read.entry_id and d.page_ordinal==page['page_ordinal']]
        if len(slots)!=1:raise ValueError('monitoring_retained_exact_slot_required')
        d=slots[0];final=json.loads((capture_root/'receipts'/d.logical_request_id/'final.json').read_bytes())
        consume_bound_result(root=capture_root,plan=dispatcher_plan,logical_id=d.logical_request_id,receipt_sha256=final['receipt_sha256'])
        if bound_artifact(capture_root,d.raw_path,page['source_sha256'])!=raw:
            raise ValueError('monitoring_retained_sealed_raw_mismatch')
        source=parser._find_rows(json.loads(raw),keys)
        for row in source:
            normalized=parser._normalize_rows([row],1)
            if len(normalized)!=1:raise ValueError('monitoring_original_parser_dropped_row')
            all_rows.extend(normalized)
        pages.append(dict(page=page['page_ordinal'],sha256=page['source_sha256'],rows=len(source)))
    value=project_monitoring_rows(all_rows,read=read,frozen_at=plan.frozen_at,
        observed_at=datetime.fromisoformat(receipt['completed_at']),source_pages=pages)
    return dict(generation_id=stock['run_id'],original_receipt_sha256=digest(receipt),
        authority='RETAINED_HISTORICAL_ONLY_NO_OWNER_REISSUANCE',value=value,
        input=dict(read=read.model_dump(mode='json'),frozen_at=plan.frozen_at.isoformat(),
            observed_at=receipt['completed_at'],source_pages=pages),HTTP=0)
