"""Small opt-in KRX acquisition and independently replayed Source-only adapter.

No registration, Full Market Parent, AI, DB, scheduler or delivery authority.
"""
from dataclasses import dataclass
from datetime import date, datetime, timezone
import hashlib
import json
from pathlib import Path
from tempfile import TemporaryDirectory

import httpx
from pydantic import TypeAdapter

from app.jobs.probe_krx_night_futures import (
    KRX_FUTURES_DAILY_URL, KST, _rows, _attach_fetch_telemetry,
    fetch_live_probe, parse_krx_futures_payloads, exact_payload_error,
)
from app.macro.providers.krx import materialize_night_probe
from app.macro.providers.base import MacroProviderResult
from app.services.krx_night_history_service import persist_krx_response
from app.services.market_numeric_claim_service import numeric_catalog, render_typed_market_facts, final_market_numeric_audit
from app.services.market_session import us_market_session
from app.services.night_futures import summarize_night_futures, night_futures_context_row
from app.services.night_futures_session_mapping_service import resolve_us_morning_night_reference_date
from app.services.official_night_market_eligibility_service import night_market_eligibility
from app.services.unified_aggregate_receipt import AggregateChild, AggregateReceipt, ArtifactBinding, verify_aggregate
from app.services.unified_run_acquisition import RunRead, RunAcquisitionObserver
from app.services.unified_run_artifacts import durable_json
from app.services.unified_snapshot_contract import digest
from app.services.unified_source_composition import OwnerAdapter, OwnerProjection
from app.services.unified_source_policy import UnifiedSourcePolicy

CONTRACT = 'krx-exact-date-source-only-v1'
ROLE = 'krx_two_date_source_only'
PROVIDER = 'krx_night_futures'
POLICY = UnifiedSourcePolicy(frozenset((PROVIDER,)))
FILES = ('app/services/krx_source_only.py', 'app/jobs/probe_krx_night_futures.py',
    'app/macro/providers/krx.py', 'app/services/night_futures.py',
    'app/services/krx_night_history_service.py', 'app/services/official_night_market_eligibility_service.py',
    'app/services/night_futures_session_mapping_service.py', 'app/services/market_numeric_claim_service.py',
    'app/services/us_full_message_service.py', 'app/services/unified_run_acquisition.py',
    'app/services/unified_source_observer.py', 'app/services/unified_aggregate_receipt.py',
    'app/services/unified_source_composition.py', 'app/services/unified_source_policy.py',
    'app/services/unified_source_replay.py', 'app/services/unified_snapshot_contract.py')


def code_pins():
    root = Path(__file__).resolve().parents[2]
    return {n: hashlib.sha256((root / n).read_bytes()).hexdigest() for n in FILES}


@dataclass
class SourceOnlyParent:
    """Local one-shot dispatch state, not an external approval/capability token."""
    root: Path
    observer: RunAcquisitionObserver
    plan_sha256: str
    used: bool = False


def issue_source_only_parent(*, root: Path, run_id: str, exact_dates: tuple[date, ...], cutoff: datetime,
                             live_enabled: bool = False):
    if (cutoff.utcoffset() is None or not isinstance(exact_dates, tuple)
            or not 1 <= len(exact_dates) <= 2 or any(type(d) is not date for d in exact_dates)
            or exact_dates != tuple(sorted(set(exact_dates)))
            or any(d > cutoff.astimezone(KST).date() for d in exact_dates)):
        raise ValueError('krx_source_only_exact_dates_and_aware_cutoff_required')
    observer = RunAcquisitionObserver(root=root, run_id=run_id, acquisition_id=run_id+'-KRX',
        provider=PROVIDER, role=ROLE, policy=POLICY,
        reads=tuple(RunRead(key=str(d), route=KRX_FUTURES_DAILY_URL,
            params={'basDd': d.strftime('%Y%m%d')}, max_requests=1) for d in exact_dates))
    plan = {**observer.identity, 'contract':CONTRACT, 'exact_dates':[str(d) for d in exact_dates],
        'cutoff':cutoff.isoformat(), 'maximum_physical_HTTP':len(exact_dates), 'retry':0,
        'follow_redirects':False, 'hard_stop_on_error':True, 'code_pins':code_pins(),
        'full_market_parent':False, 'model_use':False, 'production':False,
        'execution_mode':'LIVE' if live_enabled is True else 'OFFLINE_MOCK'}
    durable_json(root/'source-only-plan.json', plan, exclusive=True)
    return SourceOnlyParent(root, observer, hashlib.sha256((root/'source-only-plan.json').read_bytes()).hexdigest())


def _project(plan, receipts, bodies):
    dates = [date.fromisoformat(d) for d in plan['exact_dates']]
    if plan.get('contract') != CONTRACT or plan.get('code_pins') != code_pins():
        raise ValueError('krx_source_only_code_or_contract_changed')
    if (plan.get('retry') != 0 or plan.get('follow_redirects') is not False
            or plan.get('hard_stop_on_error') is not True or plan.get('maximum_physical_HTTP') != len(dates)
            or plan.get('full_market_parent') is not False or plan.get('production') is not False
            or plan.get('model_use') is not False or plan.get('execution_mode') not in {'LIVE','OFFLINE_MOCK'}):
        raise ValueError('krx_source_only_scope_changed')
    if not receipts or len(receipts) > len(dates) or len(receipts) != len(bodies):
        raise ValueError('krx_source_only_receipt_count')
    payloads, hashes = {}, {}
    error = None
    received = None
    for i, (r, body) in enumerate(zip(receipts, bodies, strict=True)):
        d = dates[i]
        if (r.get('request') != dict(method='GET', route=KRX_FUTURES_DAILY_URL, params={'basDd':d.strftime('%Y%m%d')})
                or r.get('read_key') != str(d) or r.get('ordinal') != i+1 or r.get('role') != ROLE):
            raise ValueError('krx_source_only_child_request_or_role')
        for k in ('run_id','acquisition_id','acquisition_class','provider'):
            if r.get(k) != plan.get(k):raise ValueError('krx_source_only_child_run')
        previous_received = received
        requested, received = (datetime.fromisoformat(r[k]) for k in ('requested_at','received_at'))
        if requested.utcoffset() is None or received.utcoffset() is None or requested > received:
            raise ValueError('krx_source_only_child_time')
        if previous_received is not None and requested < previous_received:
            raise ValueError('krx_source_only_child_sequence_time')
        if r['outcome'] == 'TRANSPORT_ERROR':
            error = 'TRANSPORT_ERROR'
        elif r['outcome'] != 'HTTP_RESPONSE' or body is None or hashlib.sha256(body).hexdigest() != r['artifact_sha256']:
            raise ValueError('krx_source_only_raw_hash_or_outcome')
        elif r['http_status'] != 200:
            error = 'HTTP_'+str(r['http_status'])
        else:
            try:
                payload = json.loads(body); error = exact_payload_error(payload, d)
                if not error:payloads[d], hashes[d] = payload, r['artifact_sha256']
            except (ValueError, TypeError, AttributeError):error = 'INVALID_JSON_OR_SCHEMA'
        if error and i != len(receipts)-1:
            raise ValueError('krx_source_only_request_after_first_error')
    if not error and len(receipts) != len(dates):
        raise ValueError('krx_source_only_successful_read_missing')
    cutoff = datetime.fromisoformat(plan['cutoff'])
    received = received.astimezone(timezone.utc)
    probe = parse_krx_futures_payloads(payloads, fetched_at=received,
        queried_dates=dates[:len(receipts)], payload_sha256_by_date=hashes)
    mapping = resolve_us_morning_night_reference_date(received)
    expected = mapping.night_trade_date if mapping else None
    probe = _attach_fetch_telemetry(probe,payloads=payloads,expected_session=expected,observation_time=received)
    probe.session_freshness = ('fresh' if probe.night_session_usable and probe.source_date==expected
        and probe.finality_valid and not error else 'unverified')
    with TemporaryDirectory(prefix='krx-source-only-replay-') as temporary:
        history = Path(temporary)
        for r, body in zip(receipts,bodies,strict=True):
            d = datetime.strptime(r['request']['params']['basDd'],'%Y%m%d').date()
            if d in payloads:
                persist_krx_response(root=history, query_date=d,
                    fetched_at=datetime.fromisoformat(r['received_at']), http_status=200, raw_body=body)
        result = materialize_night_probe(probe,history_directory=history,night_end_dates=True)
    observations = [dict(**o.__dict__) for o in result.observations]
    flat = [{**o, **o['raw_payload'], 'retrieved_at':received.isoformat()} for o in observations]
    summary = summarize_night_futures({'observations':flat})
    rows = [json.loads(json.dumps(night_futures_context_row(item),default=lambda v:v.isoformat())) for item in summary.items]
    assessed, completed = received.astimezone(KST).date().isoformat(), us_market_session(received).latest_completed_regular_session_date.isoformat()
    gates = [night_market_eligibility(row,market='us',assessment_date=assessed,completed_session_date=completed) for row in rows]
    eligible = [row for row,gate in zip(rows,gates,strict=True) if gate['eligible']]
    source = dict(session=dict(market='us',assessment_date=assessed,latest_completed_regular_session_date=completed),
        night_futures=rows, fact_catalog=[dict(fact_id=row['fact_id'],fact_type='night_futures',as_of_date=row['session_date'],fields=row) for row in rows],numeric_registry=[])
    catalog = numeric_catalog(source,market='us',assessment_date=assessed,eligible_refs=[r['fact_id'] for r in eligible])
    narrative = 'SOURCE-ONLY · NO-SEND'
    body = render_typed_market_facts(catalog,source)+'\n\n'+narrative
    audit = final_market_numeric_audit(body,catalog,source,narrative)
    if audit['status'] != 'PASS':raise ValueError('krx_source_only_numeric_final_audit')
    text = f"실제 수신: {received.isoformat()}\n요청 평가 cutoff: {cutoff.isoformat()}\n"+body
    if not eligible:text += '\n야간 일봉: 자료 부족. '+(error or probe.reason or '동일계약 현재 적격 원본 미확보')
    return dict(contract=CONTRACT,run_id=plan['run_id'],status='SOURCE_ONLY_DAILY_PASS' if eligible else 'SOURCE_ONLY_PARTIAL',
        physical_HTTP=len(receipts),source_mode=plan['execution_mode'],
        financial_HTTP=len(receipts) if plan['execution_mode']=='LIVE' else 0,
        error=error,probe_reason=probe.reason,available_at=received.isoformat(),provider_published_at=None,
        assessment_cutoff=cutoff.isoformat(),eligible_at_requested_cutoff=bool(eligible and received<=cutoff),
        late_capture=received>cutoff,source=source,gates=gates,numeric_catalog=catalog,numeric_audit=audit,
        provider_value=TypeAdapter(MacroProviderResult).dump_python(result,mode='json'),
        text=text,text_sha256=hashlib.sha256(text.encode()).hexdigest(),
        full_market_parent=False,model_use=False,production=False,NO_SEND=True,default_enabled=False,Strict_READY='0/22')


async def collect_source_only(parent, *, enabled=False, api_key=None, transport=None):
    """Real network stays OFF unless explicitly enabled by the manual command."""
    if type(parent) is not SourceOnlyParent or parent.used:
        raise ValueError('krx_source_only_parent_reused')
    if transport is None and enabled is not True:raise ValueError('krx_source_only_live_default_OFF')
    if transport is not None and type(transport) is not httpx.MockTransport:
        raise ValueError('krx_source_only_test_transport_must_be_explicit_mock')
    root, observer = parent.root, parent.observer
    raw_plan=(root/'source-only-plan.json').read_bytes()
    if hashlib.sha256(raw_plan).hexdigest()!=parent.plan_sha256:raise ValueError('krx_source_only_plan_changed')
    plan=json.loads(raw_plan)
    if ((plan['execution_mode']=='LIVE' and (enabled is not True or transport is not None))
            or (plan['execution_mode']=='OFFLINE_MOCK' and type(transport) is not httpx.MockTransport)):
        raise ValueError('krx_source_only_live_mock_mode_mismatch')
    if plan['code_pins']!=code_pins():raise ValueError('krx_source_only_code_changed')
    parent.used=True; observer.begin(provider=PROVIDER,role=ROLE)
    probe=await fetch_live_probe(observation_time=datetime.fromisoformat(plan['cutoff']),api_key=api_key,
        exact_dates=tuple(date.fromisoformat(d) for d in plan['exact_dates']),hard_stop_on_error=True,
        source_observer=observer,transport=transport)
    receipts=[json.loads(p.read_bytes()) for p in sorted(root.glob('read-*.response.json'))]
    if not receipts:
        observer.finish(normalized=None,contract=CONTRACT,fingerprint=digest(code_pins()),denial=probe.reason)
        return dict(status='SOURCE_ONLY_UNAVAILABLE_BEFORE_SEND',physical_HTTP=0,reason=probe.reason)
    if any(r['outcome']=='BODY_WITHHELD_SECRET_RISK' for r in receipts):
        observer.finish(normalized=None,contract=CONTRACT,fingerprint=digest(code_pins()),denial='SOURCE_BODY_WITHHELD')
        return dict(status='SOURCE_ONLY_BODY_WITHHELD',physical_HTTP=len(receipts),reason='SECRET_RISK',
            full_market_parent=False,model_use=False,NO_SEND=True)
    bodies=[(root/r['artifact']).read_bytes() if r.get('artifact') else None for r in receipts]
    value=_project(plan,receipts,bodies)
    observer.finish(normalized=value,contract=CONTRACT,fingerprint=digest(code_pins()))
    durable_json(root/'projection.json',value,exclusive=True)
    children=tuple(AggregateChild(child_id=f'read-{i:04d}',receipt=ArtifactBinding(path=f'read-{i:04d}.response.json',
        sha256=hashlib.sha256((root/f'read-{i:04d}.response.json').read_bytes()).hexdigest())) for i in range(1,len(receipts)+1))
    wire=dict(owner=CONTRACT,run_id=plan['run_id'],acquisition_class=plan['acquisition_class'],attempt_id=None,acquisition_id=plan['acquisition_id'],
        role=ROLE,market='us',symbol='*',provider=PROVIDER,basis='same_contract_night_daily_source_only',session=plan['exact_dates'][-1],
        requested_at=receipts[0]['requested_at'],received_at=receipts[-1]['received_at'],artifact='projection.json',
        artifact_sha256=hashlib.sha256((root/'projection.json').read_bytes()).hexdigest(),
        plan=ArtifactBinding(path='source-only-plan.json',sha256=parent.plan_sha256).model_dump(mode='json'),
        expected_child_ids=[c.child_id for c in children],children=[c.model_dump(mode='json') for c in children],normalized_sha256=digest(value),
        validator_contract=CONTRACT,coverage=dict(source_only=True,production=False,full_market_parent=False,model_use=False),contract='unified-transitive-source-receipt-v1')
    receipt=AggregateReceipt.model_validate({**wire,'aggregate_sha256':digest(wire)})
    durable_json(root/'aggregate.json',receipt.model_dump(mode='json'),exclusive=True)
    return replay_source_only(root=root,receipt=receipt,plan_sha256=parent.plan_sha256,cutoff=receipt.received_at)


def replay_source_only(*, root, receipt, plan_sha256, cutoff):
    """No network. A separate process can reproduce and audit the whole body."""
    receipt=AggregateReceipt.model_validate(receipt)
    if receipt.plan.sha256!=plan_sha256:raise ValueError('krx_source_only_frozen_plan_required')
    graph=verify_aggregate(root,receipt,policy=POLICY,cutoff=cutoff)
    plan=json.loads(graph.plan)
    if (receipt.owner,receipt.validator_contract,receipt.role,receipt.basis,receipt.session)!=(
            CONTRACT,CONTRACT,ROLE,'same_contract_night_daily_source_only',plan['exact_dates'][-1]):
        raise ValueError('krx_source_only_aggregate_role')
    if receipt.coverage!=dict(source_only=True,production=False,full_market_parent=False,model_use=False):
        raise ValueError('krx_source_only_aggregate_scope')
    if (receipt.market,receipt.symbol,receipt.provider)!=('us','*',PROVIDER):
        raise ValueError('krx_source_only_aggregate_identity')
    if (receipt.requested_at.isoformat()!=graph.child_receipts[0]['requested_at']
            or receipt.received_at.isoformat()!=graph.child_receipts[-1]['received_at']):
        raise ValueError('krx_source_only_aggregate_clock')
    value=_project(plan,graph.child_receipts,graph.child_bodies)
    if digest(value)!=receipt.normalized_sha256 or json.loads(graph.normalized)!=value:
        raise ValueError('krx_source_only_owner_projection_mismatch')
    return value


def source_only_adapter(*, root, plan_sha256):
    def deny_single(_raw,_cutoff):raise ValueError('krx_source_only_transitive_graph_required')
    def project(graph,cutoff):
        value=replay_source_only(root=root,receipt=graph.receipt,plan_sha256=plan_sha256,cutoff=cutoff)
        return OwnerProjection(value,PROVIDER,'us','*','same_contract_night_daily_source_only',
            graph.receipt.session,value['status']=='SOURCE_ONLY_DAILY_PASS',None if value['status']=='SOURCE_ONLY_DAILY_PASS' else 'daily_unavailable',
            graph.receipt.received_at)
    return OwnerAdapter(CONTRACT,digest(code_pins()),deny_single,project)
