"""Bounded raw-byte price reproof, not current identity or source-use admission.

The parent supplies independently frozen plan/source/code anchors. This module
does not compile a ProviderPlan, impersonate StockPlan, dispatch, or issue use
permissions. Only the US regular-stock same-response adapter is qualified here.
"""
from datetime import date, datetime
import json
from pathlib import Path
from typing import Literal

from pydantic import Field, TypeAdapter, model_validator

from app.services import completed_price_state, kiwoom_completed_close_owner as close
from app.services.market_session import preceding_exchange_session_date, us_market_session
from app.services.ohlcv_provider_integrity_service import (
    BAR_FIELDS, canonical_fingerprint, inspect_normalized_ohlcv_rows,
)
from app.services.scoped_source_plan import (
    OWNER_FILES as PLAN_OWNER_FILES, PricePairRequirement, R22ScopedSourcePlanV1,
)
from app.services.sealed_fresh_dispatch import RequestPlan, decode_request_plan
from app.services.unified_run_artifacts import sha256_bytes
from app.services.unified_snapshot_contract import ContractModel, digest, encoded

ROOT = Path(__file__).resolve().parents[2]
SHA = r"^[a-f0-9]{64}$"
CONTRACT = "scoped-price-pair-reproof-v1"
OWNER_FILES = tuple(sorted(set(PLAN_OWNER_FILES) | {
    "app/services/scoped_price_pair_owner.py",
    "app/services/completed_price_state.py",
    "app/services/ohlcv_provider_integrity_service.py",
    "app/services/price_structure_wave_fibonacci_v3_service.py",
    "app/services/sealed_fresh_dispatch.py",
    "app/services/sealed_response_binding.py",
    "app/services/unified_run_artifacts.py",
    "app/services/unified_snapshot_contract.py",
}))
MAX_ARTIFACT_BYTES = 24 * 1024 * 1024
MAX_REPLAY_BYTES = 4 * MAX_ARTIFACT_BYTES
PRICE_ERRORS = frozenset({"invalid_usa20590_price_wire_type", "invalid_usa20590_price",
                         "nonpositive_or_nonfinite_usa20590_price"})


class ScopedPriceReplayContext(ContractModel):
    """Explicit scoped read context for the original price owner's protocol.

    The acquisition_id is a reproof namespace, not a claimed new acquisition.
    All scoped reads and the complete source plan remain bound in model_dump.
    This is deliberately not accepted by legacy StockPlan admission.
    """
    contract: Literal["scoped-price-replay-context-v1"] = "scoped-price-replay-context-v1"
    scoped_plan: R22ScopedSourcePlanV1

    @property
    def run_id(self):
        return self.scoped_plan.request_plan.generation_id

    @property
    def frozen_at(self):
        return self.scoped_plan.request_plan.frozen_at

    @property
    def reads(self):
        return self.scoped_plan.stock_reads

    @property
    def acquisition_id(self):
        return "scoped-price-reproof-" + self.scoped_plan.plan_sha256


class PairObservation(ContractModel):
    role: Literal["PRIOR", "CURRENT"]
    session: date
    open: float = Field(gt=0, allow_inf_nan=False)
    high: float = Field(gt=0, allow_inf_nan=False)
    low: float = Field(gt=0, allow_inf_nan=False)
    close: float = Field(gt=0, allow_inf_nan=False)
    raw_sha256: str = Field(pattern=SHA)
    raw_row_sha256: str = Field(pattern=SHA)
    normalized_row_sha256: str = Field(pattern=SHA)
    row_fingerprint: str = Field(pattern=SHA)


class PricePairReproof(ContractModel):
    contract: Literal["scoped-price-pair-reproof-v1"] = CONTRACT
    requirement: PricePairRequirement
    scoped_plan_sha256: str = Field(pattern=SHA)
    owner_set_sha256: str = Field(pattern=SHA)
    source_input_sha256: str | None = Field(default=None, pattern=SHA)
    provider_plan_sha256: str | None = Field(default=None, pattern=SHA)
    generation_id: str
    frozen_at: datetime
    status: Literal["PAIR_REPROVED", "SOURCE_UNAVAILABLE", "OWNER_UNQUALIFIED", "UNSUPPORTED_ADAPTER"]
    reason_code: str
    current_state: completed_price_state.CurrentPriceState | None = None
    observations: tuple[PairObservation, ...] = ()
    source_use_grant: Literal["NOT_ISSUED"] = "NOT_ISSUED"
    current_identity_authority: Literal[False] = False
    native_source_use: Literal["NOT_ADMITTED"] = "NOT_ADMITTED"
    technical_injection_allowed: Literal[False] = False
    receipt_sha256: str = Field(pattern=SHA)

    @model_validator(mode="after")
    def bound(self):
        if self.receipt_sha256 != digest(self.model_dump(mode="json", exclude={"receipt_sha256"})):
            raise ValueError("scoped_pair_receipt_hash")
        if self.frozen_at.utcoffset() is None:
            raise ValueError("scoped_pair_timezone_required")
        if self.status != "PAIR_REPROVED":
            if self.observations:
                raise ValueError("scoped_pair_denial_has_observations")
            return self
        req, state = self.requirement, self.current_state
        if (req.source_api, req.market, req.instrument_kind, req.basis, req.currency) != (
                "usa20590", "us", "STOCK", "REGULAR_STOCK_CLOSE", "USD"):
            raise ValueError("scoped_pair_basis_mismatch")
        if (state is None or state.state != "AVAILABLE" or state.numeric_owner is None
                or not self.source_input_sha256 or not self.provider_plan_sha256
                or (state.ticker, state.security_id, state.source_generation, state.target_session) != (
                    req.symbol, req.security_ref, self.generation_id, req.target)
                or state.provider_plan_sha256 != self.provider_plan_sha256
                or state.source_input_sha256 != self.source_input_sha256):
            raise ValueError("scoped_pair_current_owner_binding")
        if (len(self.observations) != 2
                or [(r.role, r.session) for r in self.observations] != [("PRIOR", req.prior), ("CURRENT", req.target)]
                or req.prior != preceding_exchange_session_date("XNYS", req.target)
                or any(r.raw_sha256 != state.raw_sha256 for r in self.observations)):
            raise ValueError("scoped_pair_exact_same_response_sessions")
        current = self.observations[1]
        if (current.normalized_row_sha256 != state.numeric_owner.normalized_sha256
                or current.row_fingerprint != state.numeric_owner.selected_row_fingerprint
                or current.close != state.numeric_owner.current_price):
            raise ValueError("scoped_pair_current_projection_drift")
        return self


def owner_hashes():
    """Bounded source-file census for parent presealing; not an authority grant."""
    result = {}
    for name in OWNER_FILES:
        path = ROOT / name
        if path.is_symlink() or not path.resolve().is_relative_to(ROOT):
            raise ValueError("scoped_pair_owner_path")
        result[name] = sha256_bytes(path.read_bytes())
    return result


def _scope(plan, role, expected_plan, expected_owners):
    plan = R22ScopedSourcePlanV1.model_validate(
        plan.model_dump(mode="json") if isinstance(plan, R22ScopedSourcePlanV1) else plan)
    if plan.plan_sha256 != expected_plan:
        raise ValueError("scoped_pair_plan_anchor_mismatch")
    if set(expected_owners) != set(OWNER_FILES) or owner_hashes() != expected_owners:
        raise ValueError("scoped_pair_owner_drift")
    if json.loads(plan.owner_files_json) != {n: expected_owners[n] for n in PLAN_OWNER_FILES}:
        raise ValueError("scoped_pair_planning_owner_drift")
    if plan.config_sha256 != digest(plan.config.model_dump(mode="json")):
        raise ValueError("scoped_pair_config_drift")
    matches = [r for r in plan.price_pairs if r.role == role]
    if len(matches) != 1:
        raise ValueError("scoped_pair_role_missing_or_duplicate")
    req = matches[0]
    sessions = [s for s in plan.sessions if s.market == req.market]
    if len(sessions) != 1 or (req.target, req.prior) != (sessions[0].target, sessions[0].prior):
        raise ValueError("scoped_pair_session_binding")
    return plan, req


def reprove_price_pair(*, scoped_plan, role, source, security, artifact_reader,
                       expected_scoped_plan_sha256, expected_source_sha256, expected_owner_hashes):
    """Replay captured bytes only. Anchors must come from the parent's preseal.

    A serialized receipt (even rehashed) is not trusted: consumers should call
    validate_price_pair with the same independently sealed inputs. No current
    identity, dispatch, D01/D02, valuation, or technical permission is minted.
    """
    owners = dict(expected_owner_hashes)
    plan, req = _scope(scoped_plan, role, expected_scoped_plan_sha256, owners)
    source = json.loads(encoded(source)) if source is not None else None
    source_sha = digest(source) if source is not None else None
    if source_sha != expected_source_sha256:
        raise ValueError("scoped_pair_source_anchor_mismatch")
    base = dict(requirement=req, scoped_plan_sha256=plan.plan_sha256,
        owner_set_sha256=digest(owners), source_input_sha256=source_sha,
        generation_id=plan.request_plan.generation_id, frozen_at=plan.request_plan.frozen_at)

    def result(status, reason, *, state=None, rows=(), provider=None):
        if owner_hashes() != owners:
            raise ValueError("scoped_pair_owner_drift")
        # Canonicalize nested model/date values before sealing the receipt.
        body = dict(base, status=status, reason_code=reason, current_state=state,
            observations=rows, provider_plan_sha256=provider,
            contract=CONTRACT, source_use_grant="NOT_ISSUED", current_identity_authority=False,
            native_source_use="NOT_ADMITTED", technical_injection_allowed=False)
        body = json.loads(encoded({k: v.model_dump(mode="json") if hasattr(v, "model_dump") else
            [r.model_dump(mode="json") for r in v] if k == "observations" else
            TypeAdapter(datetime).dump_python(v, mode="json") if isinstance(v, datetime) else v
            for k, v in body.items()}))
        return PricePairReproof(**body, receipt_sha256=digest(body))

    if req.instrument_kind == "INDEX":
        return result("UNSUPPORTED_ADAPTER", "INDEX_ORIGINAL_PAIR_OWNER_NOT_CONNECTED")
    if req.instrument_kind == "ETF_PROXY":
        return result("UNSUPPORTED_ADAPTER", "ETF_AGGREGATE_OWNER_NOT_CONNECTED")
    if req.market == "kr":
        return result("UNSUPPORTED_ADAPTER", "KR_ADJUSTED_PAIR_OWNER_NOT_CONNECTED")
    if (req.source_api, req.instrument_kind, req.basis, req.currency) != (
            "usa20590", "STOCK", "REGULAR_STOCK_CLOSE", "USD"):
        raise ValueError("scoped_pair_basis_mismatch")
    if source is None:
        return result("SOURCE_UNAVAILABLE", "CAPTURED_SOURCE_INPUT_MISSING")
    provider = decode_request_plan(source["provider_plan"])
    provider_base = {name: getattr(provider, name) for name in RequestPlan.model_fields}
    if RequestPlan(**provider_base) != plan.request_plan:
        raise ValueError("scoped_pair_provider_plan_mismatch")
    reads = [r for r in plan.stock_reads if r.subject == req.symbol and r.role == "adjusted_daily"]
    subjects = [s for s in plan.config.subjects if s.ticker == req.symbol]
    if len(reads) != 1 or len(subjects) != 1:
        raise ValueError("scoped_pair_read_or_subject_missing")
    read, subject = reads[0], subjects[0]
    bindings = [b for b in plan.identities if b.subject == subject]
    if len(bindings) != 1:
        raise ValueError("scoped_pair_security_record_mismatch")
    binding = bindings[0]
    if (security.get("cik"), security.get("security_type"), security.get("issuer_type"),
            security.get("canonical_company_id")) != (
            subject.issuer_id, binding.security_type, binding.issuer_type, binding.company_id):
        raise ValueError("scoped_pair_security_record_mismatch")
    if "currency" in security and security["currency"] != subject.currency:
        raise ValueError("scoped_pair_security_currency_mismatch")
    # Currency may be explicit on replay even when absent from the sealed catalog.
    catalog_record = {k: v for k, v in security.items() if k != "currency"}
    if binding.record_sha256 not in {digest(security), digest(catalog_record)}:
        raise ValueError("scoped_pair_security_record_mismatch")
    if binding.security_type != "common_stock":
        return result("UNSUPPORTED_ADAPTER", "REGULAR_COMMON_STOCK_OWNER_REQUIRED")
    exchange = {"NASDAQ": "ND", "NYSE": "NY", "AMEX": "NA"}
    if ((read.market, read.canonical_security_id, read.latest_completed_session, read.exchange) != (
                "us", req.security_ref, str(req.target), exchange.get(subject.venue, subject.venue))
            or (subject.market, subject.security_id, subject.currency) != ("us", req.security_ref, "USD")
            or us_market_session(plan.request_plan.frozen_at).latest_completed_regular_session_date != req.target
            or req.prior != preceding_exchange_session_date("XNYS", req.target)):
        raise ValueError("scoped_pair_read_identity_or_calendar")
    slot = completed_price_state.required_source_slot(provider, read)
    if slot is None or slot.logical_request_id != req.descriptor_id:
        raise ValueError("scoped_pair_required_slot_missing")

    cache, used = {}, 0
    def load(path, sha):
        nonlocal used
        key = (path, sha)
        if key not in cache:
            raw = artifact_reader(path, sha)
            if not isinstance(raw, bytes) or sha256_bytes(raw) != sha:
                raise ValueError("scoped_pair_artifact_drift")
            if len(raw) > MAX_ARTIFACT_BYTES or used + len(raw) > MAX_REPLAY_BYTES:
                raise ValueError("scoped_pair_replay_byte_bound")
            cache[key], used = raw, used + len(raw)
        return cache[key]

    context = ScopedPriceReplayContext(scoped_plan=plan)
    state = completed_price_state.project_state(source=source, plan=context, read=read,
        security=dict(security), artifact_reader=load)
    if state.state != "AVAILABLE":
        status = "SOURCE_UNAVAILABLE" if state.state == completed_price_state.SOURCE_FAILED else "OWNER_UNQUALIFIED"
        return result(status, "CURRENT_OWNER_UNAVAILABLE", state=state, provider=provider.plan_sha256)
    final = json.loads(load(source["final"]["path"], source["final"]["sha256"]))
    last = final["attempts"][-1]
    raw = load(last["artifact"], last["raw_sha256"])
    body = json.loads(raw)
    prior = [r for r in body["result_list"] if r.get("dt") == req.prior.strftime("%Y%m%d")]
    if len(prior) != 1:
        return result("OWNER_UNQUALIFIED", "EXACT_PRIOR_ROW_MISSING" if not prior else "DUPLICATE_PRIOR_ROW",
            state=state, provider=provider.plan_sha256)
    fields = (("open", "open_pric"), ("high", "high_pric"), ("low", "low_pric"), ("close", "cur_prc"))
    if any(field not in prior[0] for _, field in fields):
        return result("OWNER_UNQUALIFIED", "PRIOR_ROW_FIELDS_MISSING", state=state, provider=provider.plan_sha256)
    try:
        prior_row = dict(date=str(req.prior), **{key: close._wire_price(prior[0][field]) for key, field in fields})
    except ValueError as exc:
        if str(exc) not in PRICE_ERRORS:
            raise
        return result("OWNER_UNQUALIFIED", "PRIOR_PRICE_WIRE_INVALID", state=state, provider=provider.plan_sha256)
    current_row = state.numeric_owner.selected_row
    if not inspect_normalized_ohlcv_rows([prior_row, current_row], timeframe="daily", cutoff=req.target).valid:
        return result("OWNER_UNQUALIFIED", "PRIOR_OHLC_INTEGRITY_FAILED", state=state, provider=provider.plan_sha256)
    current_raw = next(r for r in body["result_list"] if r.get("dt") == req.target.strftime("%Y%m%d"))
    observations = tuple(PairObservation(role=role_name, session=row["date"],
        **{key: row[key] for key, _ in fields}, raw_sha256=sha256_bytes(raw),
        raw_row_sha256=digest(raw_row), normalized_row_sha256=digest(row),
        row_fingerprint=canonical_fingerprint({k: row.get(k) for k in BAR_FIELDS}))
        for role_name, row, raw_row in (("PRIOR", prior_row, prior[0]), ("CURRENT", current_row, current_raw)))
    return result("PAIR_REPROVED", "SAME_RESPONSE_PAIR_REPROVED", state=state,
        rows=observations, provider=provider.plan_sha256)


def validate_price_pair(receipt, **replay_inputs):
    actual = reprove_price_pair(**replay_inputs)
    supplied = PricePairReproof.model_validate(receipt)
    if supplied != actual:
        raise ValueError("scoped_pair_replay_mismatch")
    return actual
