"""Explicit operator-approved, prospective UNSENT membership for one live run.

The trusted control plane records consent, then captures the authorized source.
Neither a public receipt nor a rehashed projection can create either capability.
This does not authenticate historical onboarding or grant financial data use.
"""

from copy import deepcopy
from datetime import datetime, timedelta, timezone
from importlib.metadata import version
import json
from weakref import WeakKeyDictionary, ref

from pydantic import AwareDatetime, BaseModel, ConfigDict, Field

from app.services.market_session import NEW_YORK, SEOUL, _exchange_calendar
from app.services.minimal_class_c_export import captured_private_snapshot, project_captured_export
from app.services.unified_cycle_owner import LEGACY_DENIAL, policy_fingerprints
from app.services.unified_snapshot_contract import digest

CONTRACT = "prospective-manual-shadow-class-c-owner-v1"
SCOPE = "MANUAL_SHADOW_UNSENT"


def _now():
    return datetime.now(timezone.utc)


class ApprovalDecision(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    event_id: str = Field(min_length=1)
    user_message_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    approved: bool
    effective_at: AwareDatetime
    expires_at: AwareDatetime
    subjects: tuple[str, ...]


class OperatorApproval:
    __slots__ = ("__weakref__",)


class ProspectiveOwner:
    __slots__ = ("__weakref__",)


_APPROVALS: WeakKeyDictionary = WeakKeyDictionary()
_OWNERS: WeakKeyDictionary = WeakKeyDictionary()
_ISSUED_RUNS: WeakKeyDictionary = WeakKeyDictionary()


class SourceIntakeOwner:
    """Live captured registration intent; not a Prospective/Production Owner."""
    __slots__ = ('__weakref__',)


_INTAKES: WeakKeyDictionary = WeakKeyDictionary()
_FRESH_INTAKE_IDENTITIES: WeakKeyDictionary = WeakKeyDictionary()


class IdentityDiscoveryOwner:
    """Captured intent permits official identity reads only, never financial use."""
    __slots__ = ('__weakref__',)


_DISCOVERY: WeakKeyDictionary = WeakKeyDictionary()


def issue_identity_discovery_owner(*, approval, capture, generation_id, policy):
    import os
    from pathlib import Path
    from app.services.minimal_class_c_export import MODELS
    from app.services.onboarding_readiness_service import evaluate_identity_discovery
    decision = _approval(approval)
    raw, captured = captured_private_snapshot(capture)
    cutoff = datetime.fromisoformat(captured['cutoff'])
    rows = json.loads(raw)
    if (not generation_id or not decision.effective_at <= cutoff <= _now()
            or _now()-cutoff > timedelta(hours=1)
            or captured['permission_event'] != decision.event_id):
        raise ValueError('identity_discovery_current_authorized_capture_required')
    indices = {}
    for table, values in rows.items():
        if len({r['ticker'] for r in values}) != len(values):
            raise ValueError('identity_discovery_duplicate_registration')
        indices[table] = {r['ticker']: MODELS[table].model_validate(r) for r in values}
    if set(indices['watchlistitem']) != set(decision.subjects):
        raise ValueError('identity_discovery_exact_approved_subjects')
    results = {ticker: evaluate_identity_discovery(item, indices['securitymaster'].get(ticker),
        indices['company'].get(ticker), indices['investmentthesis'].get(ticker),
        cutoff=cutoff, policy=policy) for ticker, item in indices['watchlistitem'].items()}
    code_paths = (Path(__file__), Path(__file__).parent/'onboarding_readiness_service.py')
    pins = {str(p): digest(p.read_bytes().hex()) for p in code_paths}
    public = dict(contract='identity-discovery-owner-v1', generation_id=generation_id,
        capture_sha256=digest(captured), subjects=results, source_use=False,
        financial_use=False, current_production_ready=False, send=False)
    handle = IdentityDiscoveryOwner()
    _DISCOVERY[handle] = dict(approval=approval, capture=capture, public=deepcopy(public),
        pid=os.getpid(), pins=pins, cutoff=cutoff)
    return handle, public


def require_identity_discovery(handle, *, generation_id, ticker):
    import os
    from pathlib import Path
    if type(handle) is not IdentityDiscoveryOwner or handle not in _DISCOVERY:
        raise ValueError('identity_discovery_live_owner_required')
    state = _DISCOVERY[handle]
    _approval(state['approval'])
    raw, receipt = captured_private_snapshot(state['capture'])
    if (state['pid'] != os.getpid() or generation_id != state['public']['generation_id']
            or _now()-state['cutoff'] > timedelta(hours=1)
            or state['public']['capture_sha256'] != digest(receipt)
            or any(digest(Path(p).read_bytes().hex()) != s for p, s in state['pins'].items())):
        raise ValueError('identity_discovery_expired_or_changed')
    subject = state['public']['subjects'].get(ticker)
    if not subject or not subject['identity_discovery_eligible']:
        raise ValueError('identity_discovery_subject_denied')
    # This private input remains unverified registration metadata; no quality
    # field is changed and no SourceIntake/Production capability is issued.
    rows = json.loads(raw)
    return deepcopy(next(r for r in rows['securitymaster'] if r['ticker'] == ticker))


def revoke_identity_discovery(handle):
    if type(handle) is not IdentityDiscoveryOwner or handle not in _DISCOVERY:
        raise ValueError('identity_discovery_live_owner_required')
    del _DISCOVERY[handle]


def issue_source_intake_owner(*, approval, capture, market, generation_id, policy, fresh_identity_reader=None):
    from app.services.minimal_class_c_export import MODELS
    from app.services.onboarding_readiness_service import evaluate_source_intake
    decision = _approval(approval)
    raw, receipt = captured_private_snapshot(capture)
    cutoff = datetime.fromisoformat(receipt['cutoff'])
    if (market not in {'kr', 'us'} or not generation_id
            or not decision.effective_at <= cutoff <= _now()
            or _now()-cutoff > timedelta(hours=1)):
        raise ValueError('source_intake_current_authorized_capture_required')
    rows = json.loads(raw)
    indices = {}
    for table, values in rows.items():
        if len({r['ticker'] for r in values}) != len(values):
            raise ValueError('source_intake_duplicate_identity')
        indices[table] = {r['ticker']: MODELS[table].model_validate(r) for r in values}
    from app.services.market_session import market_scope_for_security
    results = {};fresh_identities={};fresh_proofs={}
    for ticker, item in indices['watchlistitem'].items():
        if market_scope_for_security(ticker, item.exchange) != market:
            continue
        if ticker not in decision.subjects:
            raise ValueError('source_intake_subject_not_authorized')
        security=indices['securitymaster'].get(ticker);fresh_denial=None
        if fresh_identity_reader is not None:
            from app.services.fresh_registered_identity import resolve,FreshIdentityUnavailable
            if security is None:raise ValueError('fresh_intake_original_registration_identity_required')
            try:
                security,proof=resolve(fresh_identity_reader,security,not_before=decision.effective_at)
            except FreshIdentityUnavailable as exc:fresh_denial=str(exc)
            else:
                fresh_identities[ticker]=security.model_dump(mode='json');fresh_proofs[ticker]=proof
        results[ticker] = evaluate_source_intake(item, security,
            indices['company'].get(ticker), indices['investmentthesis'].get(ticker),
            cutoff=cutoff, policy=policy)
        if fresh_denial:
            results[ticker]['denials'].append('fresh_identity:'+fresh_denial)
            results[ticker]['registered_source_intake_eligible']=False
        elif fresh_identity_reader is not None:
            # Authenticated fresh field-Owner evidence supplies provenance; the
            # stored registration-quality flags themselves remain unchanged.
            results[ticker]['denials']=[d for d in results[ticker]['denials']
                if d not in {'IDENTITY_QUALITY_UNVERIFIED','IDENTITY_PROVIDER_MISSING'}]
            results[ticker]['registered_source_intake_eligible']=not results[ticker]['denials']
            results[ticker]['fresh_source_identity']=deepcopy(fresh_proofs[ticker])
        results[ticker]['registration_sha256'] = digest(item.model_dump(mode='json'))
    if not results:
        raise ValueError('source_intake_empty_market')
    from hashlib import sha256
    from pathlib import Path
    public = dict(contract='source-intake-fresh-official-eligibility-v2' if fresh_identity_reader is not None else 'source-intake-eligibility-v1', generation_id=generation_id,
        market=market, issued_at=_now().isoformat(), cutoff=cutoff.isoformat(),
        expires_at=min(decision.expires_at,cutoff+timedelta(hours=1)).isoformat(),
        approval_sha256=digest(decision.model_dump(mode='json')),
        capture_sha256=digest(receipt), original_rows_sha256=receipt['original_rows_sha256'],
        implementation_sha256=sha256(Path(__file__).read_bytes()).hexdigest(),
        readiness_sha256=sha256((Path(__file__).parent/'onboarding_readiness_service.py').read_bytes()).hexdigest(),
        identity_policy_sha256=digest(sorted(policy.allowed_providers)), subjects=results,
        production_seed_qualified=False, source_or_economic_authority=False, send=False)
    handle = SourceIntakeOwner()
    _INTAKES[handle] = (approval, capture, json.dumps(public))
    if fresh_identity_reader is not None:
        _FRESH_INTAKE_IDENTITIES[handle]=dict(reader=fresh_identity_reader,identities=fresh_identities,proofs=fresh_proofs)
    return handle, deepcopy(public)


def require_source_intake(owner, *, generation_id, ticker, registration=None):
    from hashlib import sha256
    from pathlib import Path
    if type(owner) is not SourceIntakeOwner or owner not in _INTAKES:
        raise ValueError('source_intake_live_owner_required')
    approval, capture, document = _INTAKES[owner]
    _approval(approval)
    receipt = json.loads(document)
    _, captured = captured_private_snapshot(capture)
    if (receipt['capture_sha256'] != digest(captured)
            or receipt['generation_id'] != generation_id
            or _now() >= datetime.fromisoformat(receipt['expires_at'])
            or receipt['implementation_sha256'] != sha256(Path(__file__).read_bytes()).hexdigest()
            or receipt['readiness_sha256'] != sha256((Path(__file__).parent/'onboarding_readiness_service.py').read_bytes()).hexdigest()):
        raise ValueError('source_intake_binding_expired_or_changed')
    subject = receipt['subjects'].get(ticker)
    if not subject or not subject['registered_source_intake_eligible']:
        raise ValueError('source_intake_subject_denied')
    if owner in _FRESH_INTAKE_IDENTITIES:
        from app.services.fresh_registered_identity import resolve
        from app.services.minimal_class_c_export import MODELS
        raw,_=captured_private_snapshot(capture)
        original=next(r for r in json.loads(raw)['securitymaster'] if r['ticker']==ticker)
        fresh=_FRESH_INTAKE_IDENTITIES[owner]
        current,proof=resolve(fresh['reader'],MODELS['securitymaster'].model_validate(original),
            not_before=_approval(approval).effective_at)
        if current.model_dump(mode='json')!=fresh['identities'][ticker] or proof!=fresh['proofs'][ticker]:
            raise ValueError('fresh_source_intake_identity_changed')
    if registration is not None and subject['registration_sha256'] != digest(registration.model_dump(mode='json')):
        raise ValueError('source_intake_registration_changed')
    return deepcopy(subject)


def revoke_source_intake(owner):
    if type(owner) is not SourceIntakeOwner or owner not in _INTAKES:
        raise ValueError('source_intake_live_owner_required')
    del _INTAKES[owner]
    _FRESH_INTAKE_IDENTITIES.pop(owner,None)


def source_intake_snapshot(owner, *, generation_id, subjects, policy):
    """Private typed adapter input. A receipt alone cannot recover this state."""
    if type(owner) is not SourceIntakeOwner or owner not in _INTAKES:
        raise ValueError('source_intake_live_owner_required')
    approval,capture,document = _INTAKES[owner]
    receipt=json.loads(document)
    if (not subjects or len(set(subjects)) != len(subjects)
            or receipt['identity_policy_sha256'] != digest(sorted(policy.allowed_providers))):
        raise ValueError('source_intake_adapter_policy_or_subjects')
    for ticker in subjects:
        require_source_intake(owner,generation_id=generation_id,ticker=ticker)
    raw,captured=captured_private_snapshot(capture)
    rows=json.loads(raw)
    identities={r['ticker']:r for r in rows['securitymaster'] if r['ticker'] in subjects}
    if owner in _FRESH_INTAKE_IDENTITIES:
        identities={t:deepcopy(_FRESH_INTAKE_IDENTITIES[owner]['identities'][t]) for t in subjects}
    if set(identities)!=set(subjects):
        raise ValueError('source_intake_adapter_identity_coverage')
    return identities,receipt,capture,approval


def record_backend_approval(decision: ApprovalDecision) -> OperatorApproval:
    """Trusted operator adapter only, never called with model/request payloads.

The adapter must bind an actual explicit human decision in its audit trail.
This is a control-plane capability issuance API, not a consent-discovery API.
"""
    now = _now()
    if (not decision.approved or not decision.subjects
            or len(set(decision.subjects)) != len(decision.subjects)
            or not decision.effective_at <= now < decision.expires_at
            or decision.expires_at - decision.effective_at > timedelta(days=1)):
        raise ValueError("prospective_explicit_bounded_operator_approval_required")
    handle = OperatorApproval()
    _APPROVALS[handle] = decision.model_dump_json()
    return handle


def revoke_approval(approval):
    if approval not in _APPROVALS:
        raise ValueError("prospective_live_operator_approval_required")
    del _APPROVALS[approval]


def _approval(handle):
    if type(handle) is not OperatorApproval or handle not in _APPROVALS:
        raise ValueError("prospective_live_operator_approval_required")
    decision = ApprovalDecision.model_validate_json(_APPROVALS[handle])
    if not decision.effective_at <= _now() < decision.expires_at:
        raise ValueError("prospective_approval_expired")
    return decision


def completed_clock(market, cutoff):
    if market not in {"kr", "us"} or cutoff.utcoffset() is None:
        raise ValueError("prospective_market_clock_invalid")
    name, zone = ("XKRX", SEOUL) if market == "kr" else ("XNYS", NEW_YORK)
    cal = _exchange_calendar(name)
    target = cal.date_to_session(cutoff.astimezone(zone).date(), direction="previous")
    if cal.session_close(target).to_pydatetime() > cutoff:
        target = cal.previous_session(target)
    prior = cal.previous_session(target)
    return dict(calendar=name, calendar_version=version("exchange-calendars"),
        target=target.date().isoformat(), prior=prior.date().isoformat(),
        target_close=cal.session_close(target).to_pydatetime().isoformat(),
        prior_close=cal.session_close(prior).to_pydatetime().isoformat())


def issue_prospective_owner(*, approval, capture, market, source_generation_id,
                            generation_id, policy, purpose=SCOPE):
    decision = _approval(approval)
    raw, capture_receipt = captured_private_snapshot(capture)
    cutoff = datetime.fromisoformat(capture_receipt["cutoff"])
    if (purpose != SCOPE or not source_generation_id or not generation_id
            or not decision.effective_at <= cutoff <= _now()
            or _now() - cutoff > timedelta(hours=1)):
        raise ValueError("prospective_scope_or_current_capture_required")
    clock = completed_clock(market, cutoff)
    original = project_captured_export(capture, market=market, session_key=clock["target"], policy=policy)
    run_key = (generation_id, market)
    existing = _ISSUED_RUNS.setdefault(approval, {}).get(run_key)
    if existing is not None:
        handle = existing()
        previous, previous_receipt = _state(handle)
        if (previous != original or previous_receipt["source_generation_id"] != source_generation_id
                or previous_receipt["capture_receipt_sha256"] != digest(capture_receipt)):
            raise ValueError("prospective_duplicate_run_source_changed")
        return handle, apply_prospective_owner(original, original=original, owner=handle)
    subjects = original["universe"]["eligible_subjects"]
    if not subjects or not set(subjects) <= set(decision.subjects):
        raise ValueError("prospective_subject_not_operator_authorized")
    records = {t: {} for t in subjects}
    for component in original["roles"].values():
        for row in component["records"]:
            if row["record"]["ticker"] in records:
                records[row["record"]["ticker"]][row["table"]] = row
    bindings = {}
    for ticker, rows in records.items():
        if not {"watchlistitem", "securitymaster", "investmentthesis"} <= rows.keys():
            raise ValueError("prospective_registration_identity_thesis_missing")
        watch, security, thesis = [rows[t]["record"] for t in
            ("watchlistitem", "securitymaster", "investmentthesis")]
        if (not all(watch.get(k) is True for k in ("active", "monitoring_requested", "production_eligible"))
                or watch["onboarding_state"] != "ACTIVE" or not watch["activated_at"]
                or thesis["status"] != "active" or not thesis["core_thesis"].strip()
                or not security["canonical_security_id"]):
            raise ValueError("prospective_active_registration_and_thesis_required")
        bindings[ticker] = dict(security_id=security["canonical_security_id"], exchange=security["exchange"],
            thesis_version=thesis["version"], original_first_eligible_session=watch["first_eligible_session"],
            original_record_hashes={t: r["original_record_sha256"] for t, r in rows.items()})
    from hashlib import sha256
    from pathlib import Path

    receipt = dict(contract=CONTRACT, purpose=purpose, approval_event=decision.event_id,
        approval_sha256=digest(decision.model_dump(mode="json")), effective_at=decision.effective_at.isoformat(),
        expires_at=min(decision.expires_at, cutoff + timedelta(hours=1)).isoformat(),
        cutoff=cutoff.isoformat(), issued_at=_now().isoformat(), source_generation_id=source_generation_id,
        generation_id=generation_id, source_export_sha256=sha256(raw).hexdigest(),
        capture_receipt_sha256=digest(capture_receipt), source_projection_sha256=digest(original),
        market=market, calendar=clock, bindings=bindings, historical_writer_authority="NOT_AVAILABLE",
        policy_fingerprints=policy_fingerprints(), owner_sha256=sha256(Path(__file__).read_bytes()).hexdigest(),
        identity_policy_sha256=digest(sorted(policy.allowed_providers)),
        schema_sha256=digest(ApprovalDecision.model_json_schema()), scope="MEMBERSHIP_ONLY_NOT_D01_D02")
    handle = ProspectiveOwner()
    _OWNERS[handle] = (approval, json.dumps(original), json.dumps(receipt))
    _ISSUED_RUNS[approval][run_key] = ref(handle)
    return handle, apply_prospective_owner(original, original=original, owner=handle)


def _state(owner):
    if type(owner) is not ProspectiveOwner or owner not in _OWNERS:
        raise ValueError("prospective_live_backend_owner_required")
    approval, document, receipt = _OWNERS[owner]
    _approval(approval)
    receipt = json.loads(receipt)
    from hashlib import sha256
    from pathlib import Path

    if receipt["owner_sha256"] != sha256(Path(__file__).read_bytes()).hexdigest():
        raise ValueError("prospective_owner_implementation_changed")
    if _now() >= datetime.fromisoformat(receipt["expires_at"]):
        raise ValueError("prospective_owner_expired")
    if receipt["policy_fingerprints"] != policy_fingerprints():
        raise ValueError("prospective_policy_changed")
    if receipt["calendar"] != completed_clock(receipt["market"], datetime.fromisoformat(receipt["cutoff"])):
        raise ValueError("prospective_calendar_changed")
    return json.loads(document), receipt


def require_generation(owner, generation_id, *, purpose=SCOPE):
    _, receipt = _state(owner)
    if receipt["generation_id"] != generation_id or receipt["purpose"] != purpose:
        raise ValueError("prospective_generation_or_purpose_mismatch")


def revoke_prospective_owner(owner):
    _state(owner)
    del _OWNERS[owner]


def apply_prospective_owner(document, *, original, owner):
    authenticated, receipt = _state(owner)
    for k in ("universe", "owner_fingerprints", "market", "cutoff", "session"):
        if original.get(k) != authenticated.get(k) or document.get(k) != authenticated.get(k):
            raise ValueError("prospective_authenticated_selection_mismatch")
    if set(original["roles"]) != set(authenticated["roles"]) or set(document["roles"]) != set(authenticated["roles"]):
        raise ValueError("prospective_role_membership_mismatch")
    for role, component in authenticated["roles"].items():
        if original["roles"][role]["records"] != component["records"]:
            raise ValueError("prospective_original_rows_changed")
        def semantic(rows):
            return [{k: r[k] for k in ("table", "record_id", "record")} for r in rows]
        if semantic(document["roles"][role]["records"]) != semantic(component["records"]):
            raise ValueError("prospective_replayed_rows_changed")
    result = deepcopy(document)
    result["denials"] = []
    for denial in [*authenticated["denials"], *document["denials"]]:
        if denial["reason"] == LEGACY_DENIAL and denial["ticker"] in receipt["bindings"]:
            continue
        if denial not in result["denials"]:
            result["denials"].append(deepcopy(denial))
    for role in result["roles"]:
        eligible = not any(d["role"] == role for d in result["denials"])
        if role != "universe":
            eligible = eligible and authenticated["roles"][role]["eligible"] and document["roles"][role]["eligible"]
        result["roles"][role]["eligible"] = eligible
    result["prospective_owner_receipt"] = receipt
    return result
