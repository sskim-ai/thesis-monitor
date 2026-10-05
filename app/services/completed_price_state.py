"""Subject-local price availability, replayed from mandatory sealed attempts.

The numeric owner remains kiwoom-us-completed-session-price-v2. This companion
does not turn a missing plan or an implementation error into market evidence.
"""
from datetime import date, datetime
import json
from typing import Literal

from pydantic import Field, TypeAdapter, model_validator

from app.services import kiwoom_completed_close_owner as close
from app.services.sealed_fresh_dispatch import ProviderPlan
from app.services.unified_run_artifacts import sha256_bytes
from app.services.unified_snapshot_contract import ContractModel, digest, encoded

CONTRACT = 'completed-current-price-state-v1'
ROLE = 'COMPLETED_REGULAR_SESSION_CLOSE'
PLAN_GAP = 'PLAN_GAP_REQUIRED_OWNER_NOT_REQUESTED'
SOURCE_FAILED = 'UNAVAILABLE_SOURCE_ACQUISITION_FAILED'
HASH = r'^[a-f0-9]{64}$'


class CurrentPriceState(ContractModel):
    contract: Literal['completed-current-price-state-v1'] = CONTRACT
    ticker: str
    security_id: str
    source_generation: str
    target_session: date
    state: Literal['AVAILABLE', 'PLAN_GAP_REQUIRED_OWNER_NOT_REQUESTED',
        'UNAVAILABLE_SOURCE_ACQUISITION_FAILED', 'DENIED_TARGET_ROW_MISSING',
        'DENIED_TARGET_ROW_INTEGRITY', 'DENIED_SECURITY_OR_SESSION_BINDING']
    required_owner_contract: Literal['kiwoom-us-completed-session-price-v2'] = close.CONTRACT
    required_source_role: Literal['COMPLETED_REGULAR_SESSION_CLOSE'] = ROLE
    planner_slot_ref: str | None
    provider_plan_sha256: str = Field(pattern=HASH)
    source_input_sha256: str = Field(pattern=HASH)
    request_ref: str | None
    attempt_refs: tuple[str, ...]
    source_receipt_ref: str | None
    raw_sha256: str | None = Field(pattern=HASH)
    provider_result: str
    observation_time: datetime
    temporal_provenance: dict
    decision_version: Literal['completed-price-availability-v1'] = 'completed-price-availability-v1'
    field_eligibility: dict
    scope: Literal['SUBJECT_PRICE_CURRENT_SESSION'] = 'SUBJECT_PRICE_CURRENT_SESSION'
    does_not_affect_other_subjects: Literal[True] = True
    reason_code: str
    numeric_owner: close.KiwoomCompletedClose | None = None
    receipt_sha256: str = Field(pattern=HASH)

    @model_validator(mode='after')
    def bound(self):
        body = self.model_dump(mode='json', exclude={'receipt_sha256'})
        if self.receipt_sha256 != digest(body) or self.observation_time.utcoffset() is None:
            raise ValueError('price_state_hash_or_time')
        if self.state == PLAN_GAP:
            if any((self.planner_slot_ref, self.request_ref, self.attempt_refs,
                    self.source_receipt_ref, self.raw_sha256, self.numeric_owner)):
                raise ValueError('price_plan_gap_not_source_evidence')
        elif not all((self.planner_slot_ref, self.request_ref, self.attempt_refs, self.source_receipt_ref)):
            raise ValueError('price_state_requires_planned_attempt')
        if self.state.startswith('DENIED_') and (not self.raw_sha256 or self.provider_result != 'ACQUIRED_SUCCESS_BODY'):
            raise ValueError('semantic_denial_requires_successful_bound_body')
        if (self.numeric_owner is not None) != (self.state == 'AVAILABLE'):
            raise ValueError('price_state_numeric_owner_mismatch')
        if self.field_eligibility != {'current_price': self.state == 'AVAILABLE', 'technical_injection': False}:
            raise ValueError('price_state_field_scope')
        if self.numeric_owner is not None:
            p = self.numeric_owner
            if (p.ticker, p.canonical_security_id, p.generation_id, p.target_session) != (
                    self.ticker, self.security_id, self.source_generation, str(self.target_session)):
                raise ValueError('price_state_numeric_identity')
        return self


def required_slot(provider_plan, read):
    plan = ProviderPlan.model_validate(provider_plan)
    matches = [d for d in plan.descriptors if d.subject == read.subject
               and (d.endpoint_operation == 'usa20590' or d.consumer_role == 'completed_close:' + read.subject)]
    if not matches:
        return None
    if len(matches) != 1:
        raise ValueError('duplicate_completed_close_slot')
    d = matches[0]
    wire = json.loads(d.request_json)
    if (d.provider != 'kiwoom' or d.market != 'us' or d.endpoint_operation != 'usa20590'
            or d.consumer_role != 'completed_close:' + read.subject or not d.mandatory
            or d.consumer_role not in plan.mandatory_roles or d.response_binding is not None
            or d.max_pages != 1 or d.target_period != read.latest_completed_session
            or wire['method'] != 'POST' or wire['url'] != 'https://api.kiwoom.com/api/us/mrkcond'
            or dict(wire['headers']).get('api-id') != 'usa20590'
            or json.loads(wire['body']) != dict(stex_tp=read.exchange, stk_cd=read.subject,
                                               base_dt=read.latest_completed_session.replace('-', ''))):
        raise ValueError('completed_close_planner_binding')
    return d


def require_plan(provider_plan, stock_plan):
    plan = ProviderPlan.model_validate(provider_plan)
    if plan.generation_id != stock_plan.run_id or plan.frozen_at != stock_plan.frozen_at:
        raise ValueError('completed_close_plan_generation')
    reads = [r for r in stock_plan.reads if r.market == 'us' and r.role == 'adjusted_daily']
    slots = [required_slot(plan, r) for r in reads]
    if any(d is None for d in slots):
        raise ValueError(PLAN_GAP)
    return slots


def project_state(*, source, plan, read, security, artifact_reader):
    """No catch-all: only enumerated provider/row failures become typed states."""
    provider = ProviderPlan.model_validate(source['provider_plan'])
    if provider.generation_id != plan.run_id or provider.frozen_at != plan.frozen_at:
        raise ValueError('price_source_generation')
    d = required_slot(provider, read)
    base = dict(ticker=read.subject, security_id=read.canonical_security_id,
        source_generation=plan.run_id, target_session=read.latest_completed_session,
        planner_slot_ref=d.descriptor_sha256 if d else None, provider_plan_sha256=provider.plan_sha256,
        source_input_sha256=digest(source),
        request_ref=d.request_semantic_sha256 if d else None, attempt_refs=[], source_receipt_ref=None,
        raw_sha256=None, observation_time=plan.frozen_at.isoformat(),
        temporal_provenance=dict(frozen_at=plan.frozen_at.isoformat(), target_session=read.latest_completed_session))

    def result(state, reason, classification, numeric=None):
        base['observation_time'] = TypeAdapter(datetime).dump_python(
            datetime.fromisoformat(base['observation_time']), mode='json')
        value = dict(contract=CONTRACT, **base, state=state, required_owner_contract=close.CONTRACT,
            required_source_role=ROLE, provider_result=classification, decision_version='completed-price-availability-v1',
            field_eligibility={'current_price': state == 'AVAILABLE', 'technical_injection': False},
            scope='SUBJECT_PRICE_CURRENT_SESSION', does_not_affect_other_subjects=True,
            reason_code=reason, numeric_owner=numeric.model_dump(mode='json') if numeric else None)
        return CurrentPriceState.model_validate(dict(value, receipt_sha256=digest(value)))

    if d is None:
        return result(PLAN_GAP, PLAN_GAP, 'NOT_PLANNED')

    def load(item):
        raw = artifact_reader(item['path'], item['sha256'])
        if sha256_bytes(raw) != item['sha256']:
            raise ValueError('price_source_artifact_drift')
        return raw

    final = json.loads(load(source['final']))
    if sha256_bytes(load(source['documentation'])) != close.OFFICIAL_SPEC_SHA256:
        raise ValueError('completed_close_official_field_contract_mismatch')
    binding = dict(generation_id=plan.run_id, logical_request_id=d.logical_request_id,
        descriptor_sha256=d.descriptor_sha256, request_sha256=d.request_semantic_sha256,
        plan_sha256=provider.plan_sha256, role=d.consumer_role,
        resolved_request_sha256=sha256_bytes(d.request_json.encode()), parent_receipts={})
    if (any(final.get(k) != v for k, v in binding.items())
            or final['receipt_sha256'] != digest({k: v for k, v in final.items() if k != 'receipt_sha256'})
            or final['status'] not in {'PASS', 'FAILED'} or not final['attempts']
            or len(final['attempts']) > d.max_transport_attempts):
        raise ValueError('price_source_attempt_contract_gap')
    previous = plan.frozen_at
    for ordinal, attempt in enumerate(final['attempts'], 1):
        at, end = (datetime.fromisoformat(attempt[k]) for k in ('started_at', 'finished_at'))
        if (any(attempt.get(k) != v for k, v in binding.items()) or attempt['attempt'] != ordinal
                or at.utcoffset() is None or end.utcoffset() is None or not previous <= at <= end):
            raise ValueError('price_source_attempt_identity_or_time')
        if attempt.get('raw_sha256'):
            load(dict(path=attempt['artifact'], sha256=attempt['raw_sha256']))
        elif attempt.get('artifact'):
            raise ValueError('price_source_body_hash_missing')
        previous = end
    last = final['attempts'][-1]
    base.update(attempt_refs=[digest(a) for a in final['attempts']], source_receipt_ref=final['receipt_sha256'],
        observation_time=last['finished_at'], raw_sha256=last.get('raw_sha256'))
    base['temporal_provenance'].update(requested_at=last['started_at'], received_or_failed_at=last['finished_at'])
    if last['status'] != 200 or not last.get('raw_sha256'):
        return result(SOURCE_FAILED, 'NO_USABLE_RESPONSE_ACQUIRED', 'TRANSPORT_OR_HTTP_FAILURE')
    raw = load(dict(path=last['artifact'], sha256=last['raw_sha256']))
    try:
        body = json.loads(raw)
    except (ValueError, UnicodeDecodeError):
        return result(SOURCE_FAILED, 'PROVIDER_RESPONSE_FORMAT_FAILURE', 'RESPONSE_FORMAT_FAILURE')
    if not isinstance(body, dict) or str(body.get('return_code')) != '0' or not isinstance(body.get('result_list'), list):
        return result(SOURCE_FAILED, 'PROVIDER_RESPONSE_NOT_SUCCESS', 'PROVIDER_OR_FORMAT_FAILURE')
    if final['status'] != 'PASS' or final.get('raw_sha256') != last['raw_sha256']:
        raise ValueError('price_success_body_without_successful_source_receipt')
    wire = json.loads(d.request_json)
    request = dict(ticker=read.subject, canonical_security_id=read.canonical_security_id, currency='USD',
        api_id=d.endpoint_operation, method=wire['method'], path='/api/us/mrkcond',
        generation_id=plan.run_id, started_at=last['started_at'], body=json.loads(wire['body']))
    if not all(isinstance(r, dict) for r in body['result_list']):
        return result('DENIED_TARGET_ROW_INTEGRITY', 'INVALID_PROVIDER_ROW_SHAPE', 'ACQUIRED_SUCCESS_BODY')
    target = [r for r in body['result_list'] if r.get('dt') == request['body']['base_dt']]
    if not target:
        return result('DENIED_TARGET_ROW_MISSING', 'EXACT_TARGET_ROW_ABSENT', 'ACQUIRED_SUCCESS_BODY')
    if len(target) != 1 or any(k not in target[0] for k in ('open_pric', 'high_pric', 'low_pric', 'cur_prc')):
        return result('DENIED_TARGET_ROW_INTEGRITY', 'DUPLICATE_OR_MALFORMED_TARGET_ROW', 'ACQUIRED_SUCCESS_BODY')
    request_raw = encoded(request)
    capture = dict(http_status=200, response_received=True, raw_sha256=sha256_bytes(raw),
        raw_bytes=len(raw), request_sha256=sha256_bytes(request_raw))
    blobs = dict(request=request_raw, capture=encoded(capture), response=raw, documentation=load(source['documentation']))
    wrapped = {k: dict(path=k, sha256=sha256_bytes(v)) for k, v in blobs.items()}
    try:
        numeric = close.project(source=wrapped, plan=plan, read=read, security=security,
                                artifact_reader=lambda path, sha: blobs[path])
    except ValueError as exc:
        reason = str(exc)
        row_errors = {'invalid_usa20590_price_wire_type', 'invalid_usa20590_price',
            'nonpositive_or_nonfinite_usa20590_price', 'completed_close_own_ohlc_integrity_failed'}
        identity_errors = {'completed_close_exact_security_route_or_date_mismatch',
            'completed_close_calendar_target_mismatch', 'completed_close_supplement_time_identity_mismatch'}
        if reason not in row_errors | identity_errors:
            raise
        return result('DENIED_TARGET_ROW_INTEGRITY' if reason in row_errors else 'DENIED_SECURITY_OR_SESSION_BINDING',
                      reason, 'ACQUIRED_SUCCESS_BODY')
    return result('AVAILABLE', 'LOCKED_COMPLETED_CLOSE_OWNER_QUALIFIED', 'ACQUIRED_SUCCESS_BODY', numeric)


def require_runtime(state):
    state = CurrentPriceState.model_validate(state)
    if state.state == PLAN_GAP:
        raise ValueError(PLAN_GAP)
    return state


def materialize_state(*, state, roles, ticker, market, cutoff, observed_at):
    state = require_runtime(state)
    if (state.ticker != ticker or market != 'us' or state.target_session != cutoff):
        raise ValueError('price_state_component_identity')
    if state.numeric_owner is not None:
        result = close.materialize(projection=state.numeric_owner, roles=roles, ticker=ticker,
                                   market=market, cutoff=cutoff, observed_at=observed_at)
    else:
        result = close.materialize_price_context(current_price=None, projection_ref=state.receipt_sha256,
            compatibility=dict(status='UNPROVEN', technical_target_injection_allowed=False,
                reason=close.TECHNICAL_DENIAL, canonical_security_id=state.security_id,
                target_session=str(cutoff), raw_price_display_allowed=False,
                owner='NO_QUALIFIED_US_ACTION_GUARD_IN_DECLARED_CORPUS'),
            roles=roles, ticker=ticker, market=market, cutoff=cutoff, observed_at=observed_at)
    result['completed_price_state_sha256'] = state.receipt_sha256
    result['component_projection_sha256'] = None
    result['component_projection_sha256'] = digest(result)
    return result


def technical_state(roles, *, target_session):
    from app.services.ohlcv_provider_integrity_service import inspect_normalized_ohlcv_rows
    rows = [r for r in roles['adjusted_daily'] if str(r.get('date'))[:10] == str(target_session)]
    integrity = inspect_normalized_ohlcv_rows(rows, timeframe='daily', cutoff=target_session)
    value = dict(contract='chart-target-availability-v1', source_role='usa06012_CHART_HISTORY_TECHNICAL',
        target_session=str(target_session), rows_sha256=digest(rows),
        state='DENIED_TARGET_ROW_INTEGRITY' if rows and not integrity.valid else
            'TARGET_ROW_INTEGRITY_PASS_AUTHORITY_SEPARATE' if rows else 'TARGET_ROW_UNAVAILABLE',
        integrity=integrity.model_dump(mode='json'), current_price_authority=False,
        timing_state='UNRESOLVED', reason=close.TECHNICAL_DENIAL)
    return dict(value, receipt_sha256=digest(value))


def bind_source(technical, *, source, artifacts, security):
    from app.services.unified_stock_acquisition import decode_owned_role
    tech = dict(technical)
    if set(artifacts) & set(tech['artifacts']):
        raise ValueError('price_source_namespace_collision')
    tech['artifacts'] = {**tech['artifacts'], **artifacts}
    def reader(path, sha):
        raw = tech['artifacts'][path]
        if sha256_bytes(raw) != sha:
            raise ValueError('price_source_hash_mismatch')
        return raw
    reads = [r for r in tech['plan'].reads if r.subject == tech['ticker']]
    daily = next(r for r in reads if r.role == 'adjusted_daily')
    state = require_runtime(project_state(source=source, plan=tech['plan'], read=daily,
                                         security=security, artifact_reader=reader))
    roles = {r.role: decode_owned_role(tech['plan'], r, tech['receipts'][r.role], reader) for r in reads}
    tech['components'] = materialize_state(state=state, roles=roles, ticker=daily.subject,
        market=daily.market, cutoff=date.fromisoformat(daily.latest_completed_session),
        observed_at=tech['plan'].frozen_at.isoformat())
    tech['completed_price_source'] = source
    tech['expected_hashes'] = dict(tech['expected_hashes'], components=digest(tech['components']),
                                   completed_price_source=digest(source))
    return tech
