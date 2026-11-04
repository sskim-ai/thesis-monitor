"""Opt-in completed-window technical input; not a technical signal or Native owner.

NG46 authorizes this bounded adapter, not changes to the historical whole-role
validator. The original packet and dependency engines decide each feature.
"""
from copy import deepcopy
from datetime import date, datetime
import os
from weakref import WeakKeyDictionary

from app.services.completed_session_projection import project_completed_rows
from app.services.current_effective_technical import project
from app.services.ohlcv_feature_engine_service import PROVIDER_REQUEST_LIMIT
from app.services.ohlcv_provider_integrity_service import inspect_normalized_ohlcv_rows
from app.services.packet_owned_technical_context_service import build_packet_owned_technical_context
from app.services.technical_feature_dependency_service import assess_feature_dependency
from app.services.unified_snapshot_contract import digest

CONTRACT = 'projected-completed-window-technical-input-v1'
CONSUMER = 'SCOPED_TECHNICAL_INPUT_REFERENCE'
_ISSUED = WeakKeyDictionary()


class ProjectedTechnicalInput:
    __slots__ = ('__weakref__',)


def review_window(*, read, cutoff, all_rows, projection, rows):
    """Pure original-consumer replay, explicitly not live admission by itself."""
    if (read.role != 'adjusted_daily' or read.timeframe != 'daily' or not read.adjusted
            or read.count != PROVIDER_REQUEST_LIMIT):
        raise ValueError('technical_projected_original_daily_horizon_required')
    selected, expected = project_completed_rows(all_rows, read=read, cutoff=cutoff,
        source_pages=projection['source_pages'])
    if projection != expected or rows != selected:
        raise ValueError('technical_projected_selection_drift')
    target = date.fromisoformat(read.latest_completed_session)
    inspection = inspect_normalized_ohlcv_rows(rows, timeframe=read.timeframe, cutoff=target)
    if not inspection.valid:
        raise ValueError('technical_projected_original_integrity_failed')
    context = build_packet_owned_technical_context(ticker=read.subject, market=read.market,
        session=read.market_state, as_of=cutoff.isoformat(), periods={'daily': rows}, cutoff=target,
        expected_daily_completed=read.latest_completed_session, source='kiwoom', source_version=CONTRACT)
    dates = [date.fromisoformat(r['date']) for r in rows]
    features, ledger = {}, []
    for tf, key in (('daily','D'),('weekly','W'),('monthly','M')):
        original = getattr(context.features,tf)
        quality = context.quality[key]
        allowed = []
        for fact in original.facts:
            assessment = assess_feature_dependency(semantic=fact.semantic, minimum_history=fact.minimum_history,
                row_dates=dates if tf=='daily' else [], invalid_dates=[])
            eligible = (tf=='daily' and quality.usable_for_current_reasoning
                and assessment.classification.value in ('SAFE','SAFE_INDEPENDENT_OF_BAD_ROW','SAFE_AFTER_PROVEN_WARMUP')
                and fact.completed_bar_only and fact.as_of == read.latest_completed_session)
            ledger.append(dict(fact_id=fact.fact_id,semantic=fact.semantic,timeframe=tf,
                status='INPUT_REFERENCE_ELIGIBLE' if eligible else 'DENIED',
                dependency=assessment.model_dump(mode='json'),source_sha256=fact.source_sha256))
            if eligible: allowed.append(fact.model_dump(mode='json'))
        ledger.extend(dict(timeframe=tf,semantic=s,status='UNAVAILABLE_OR_DEPENDENCY_BLOCKED') for s in original.blocked_features)
        features[tf] = dict(facts=allowed,current_role_gate=tf=='daily',quality=quality.model_dump(mode='json'))
    effective = project(context, features)
    eligible = bool(features['daily']['facts']) and context.quality['D'].usable_for_current_reasoning
    result = dict(contract=CONTRACT,status='TECHNICAL_INPUT_REFERENCE_PASS' if eligible else 'TECHNICAL_INPUT_UNAVAILABLE',
        authority='NG46_TASK_AUTHORIZED_BOUNDED_INPUT_ADAPTER_WITH_INHERITED_QUALITY',
        security_id=read.canonical_security_id,entry_id=read.entry_id,timeframe=read.timeframe,
        adjustment_basis='ADJUSTED_OHLCV',cutoff=cutoff.isoformat(),target_session=read.latest_completed_session,
        projection_scope='COMPLETED_SESSION_BEFORE_COUNT',selected_sha256=digest(rows),
        projection_sha256=digest(projection),original_integrity=inspection.model_dump(mode='json'),
        source_limitation=effective.features.daily.source_limitation,
        legacy_whole_payload_result='UNCHANGED_SEPARATE_CONTRACT',
        context=effective.model_dump(mode='json'),feature_ledger=ledger,
        technical_input_reference=eligible,technical_signal=False,completed_price_authority=False,
        financial_use=False,economic_use=False,D01_D02=False,native_use=False,full22_native=False,model_use=False)
    return result


def _current(parent, source, *, dispatcher, entry_id):
    from app.services import current_scoped_source_results as sources
    from app.services.scoped_source_plan import ScopedStockRead
    consumed = sources.read_source_rows(parent,source,dispatcher=dispatcher,entry_id=entry_id)
    receipt = consumed['receipt']
    binding = sources._CAPTURES[dispatcher]
    ordinal, raw_read = next((i,r) for i,r in enumerate(binding['stock_plan']['reads'],1) if r['entry_id']==entry_id)
    read = ScopedStockRead.model_validate(raw_read)
    data = sources._json(binding['worker'],f'projection-{ordinal:03d}.json')
    if receipt['projection'] != data['receipt']:
        raise ValueError('technical_projected_source_receipt_mismatch')
    review = review_window(read=read,cutoff=datetime.fromisoformat(binding['stock_plan']['frozen_at']),
        all_rows=data['all_rows'],projection=data['receipt'],rows=consumed['rows'])
    if not review['technical_input_reference']:
        raise ValueError('technical_projected_original_consumer_unavailable')
    return dict(review,generation_id=receipt['generation_id'],source_receipt_sha256=receipt['receipt_sha256'],
        parent_receipt_sha256=receipt['parent_receipt_sha256'],expires_at=receipt['expires_at'],
        allowed_consumer=CONSUMER,current_binding='LIVE_PARENT_DISPATCHER_ORIGINAL_WORKER_TWO_REPLAYS')


def issue(parent, source, *, dispatcher, entry_id, enabled=False):
    if enabled is not True:
        raise ValueError('technical_projected_input_feature_off')
    value = _current(parent,source,dispatcher=dispatcher,entry_id=entry_id)
    capability = ProjectedTechnicalInput()
    _ISSUED[capability] = dict(parent=parent,source=source,dispatcher=dispatcher,
        entry_id=entry_id,pid=os.getpid(),value=deepcopy(value))
    return capability


def consume(parent, capability, *, dispatcher, entry_id, security_id, generation_id, timeframe, consumer=CONSUMER):
    if type(capability) is not ProjectedTechnicalInput or capability not in _ISSUED or consumer!=CONSUMER:
        raise ValueError('technical_projected_issued_capability_and_consumer_required')
    state = _ISSUED[capability]
    if (state['parent'] is not parent or state['dispatcher'] is not dispatcher
            or state['entry_id']!=entry_id or state['pid']!=os.getpid()):
        raise ValueError('technical_projected_parent_or_role_mismatch')
    value = _current(parent,state['source'],dispatcher=dispatcher,entry_id=entry_id)
    if (value!=state['value'] or value['security_id']!=security_id
            or value['generation_id']!=generation_id or value['timeframe']!=timeframe):
        raise ValueError('technical_projected_binding_or_content_drift')
    return dict(deepcopy(value),receipt_sha256=digest(value))


def revoke(capability):
    if type(capability) is not ProjectedTechnicalInput or capability not in _ISSUED:
        raise ValueError('technical_projected_unissued_or_revoked')
    if _ISSUED[capability]['pid'] != os.getpid():
        raise ValueError('technical_projected_wrong_process')
    del _ISSUED[capability]
