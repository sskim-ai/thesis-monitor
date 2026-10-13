"""Detached current-cycle source authority, never a relabelled proof-only seed."""
from datetime import date, datetime
from typing import Literal

from pydantic import Field, model_validator

from app.services.unified_snapshot_contract import (
    Collection, ContractModel, Role, SnapshotPolicy, digest, pointer, validate_collection,
)
from app.services.unified_source_policy import prohibited_provider
from app.services.unified_stock_acquisition import UNIVERSE

CONTRACT = "production-source-execution-envelope-v1"
POLICY = "production-source-policy-v1"
VALIDATORS = ("current-source-owner-provenance-v1", "production-source-execution-envelope-v1")
SHA = r"^[a-f0-9]{64}$"

# Route names are provider-owned, not caller-defined fallbacks.
ROUTES = {
    "canonical_local": frozenset({"source-owner"}),
    "kiwoom": frozenset({"usa20590", "usa06012", "usa06013", "usa06014", "ka10081", "ka10082", "ka10083",
        "ka20001", "ka20003", "ka20009", "ka10051", "ka10066", "ka10001", "ka10099"}),
    "kis": frozenset({"/uapi/domestic-stock/v1/quotations/estimate-perform",
        "/uapi/domestic-stock/v1/quotations/search-info", "/uapi/domestic-stock/v1/quotations/inquire-price",
        "/uapi/domestic-stock/v1/quotations/inquire-daily-price",
        *('/uapi/domestic-stock/v1/ksdinfo/'+suffix for suffix in
          ('merger-split', 'rev-split', 'bonus-issue', 'paidin-capin', 'cap-dcrs'))}),
    "finnhub": frozenset({"metric", "profile2"}),
    "sec_edgar": frozenset({"discovery", "companyfacts", "filing", "exhibit"}),
    "opendart": frozenset({"list", "document", "financial"}),
    "fred": frozenset({"observations"}),
    "eia": frozenset({"seriesid"}),
    "ecos": frozenset({"KeyStatisticList"}),
    "krx_night_futures": frozenset({"fut_bydd_trd"}),
    "google_news_rss": frozenset({"news"}),
    "naver_news": frozenset({"news"}),
}


class ProductionSourceRole(ContractModel):
    role: Role
    owner_contract: str = Field(min_length=1)
    purpose: Literal["COMPLETED_CLOSE", "TECHNICAL", "FINANCIAL", "BUSINESS", "VALUATION", "MARKET", "NIGHT"]
    required: bool
    declared_fallbacks: tuple[tuple[str, str], ...] = ()

    @model_validator(mode="after")
    def route_ownership(self):
        for provider, route in ((self.role.provider, self.role.route), *self.declared_fallbacks):
            if prohibited_provider(provider) or route not in ROUTES.get(provider, ()):
                raise ValueError("production_undeclared_provider_route")
        if self.role.route in {"usa06012", "usa06013", "usa06014"} and self.purpose != "TECHNICAL":
            raise ValueError("usa06012_technical_only")
        if self.role.route == "usa20590" and self.purpose != "COMPLETED_CLOSE":
            raise ValueError("usa20590_completed_close_only")
        if len(self.declared_fallbacks) != len(set(self.declared_fallbacks)):
            raise ValueError("duplicate_fallback")
        return self


class ProductionSnapshotPolicy(SnapshotPolicy):
    source_policy_version: Literal["production-source-policy-v1"] = POLICY
    source_roles: tuple[ProductionSourceRole, ...]
    code_config_sha256: str = Field(pattern=SHA)
    alpha_vantage_planned_calls: Literal[0] = 0

    @model_validator(mode="after")
    def exact_authority(self):
        if tuple(sorted(self.subjects)) != tuple(sorted(UNIVERSE[self.market])):
            raise ValueError("production_exact_active_universe_required")
        if self.roles != tuple(r.role for r in self.source_roles):
            raise ValueError("production_policy_role_binding")
        if self.validator_contracts != VALIDATORS:
            raise ValueError("production_required_validator_missing")
        if self.universe_owner_sha256 != digest(self.subjects):
            raise ValueError("production_universe_owner_hash_mismatch")
        if self.message_ids != ("MARKET_"+self.market.upper(), *self.subjects):
            raise ValueError("production_message_universe_mismatch")
        prices = [r for r in self.source_roles if r.purpose == "COMPLETED_CLOSE"]
        if sorted(r.role.symbol for r in prices) != sorted(self.subjects) or not all(r.required for r in prices):
            raise ValueError("PLAN_GAP_completed_close_coverage")
        if self.market == "us" and any((r.role.provider, r.role.route) != ("kiwoom", "usa20590") or r.declared_fallbacks for r in prices):
            raise ValueError("usa20590_mandatory_completed_close_owner")
        # This envelope describes consumer roles. Exact request coverage is
        # independently admitted by the canonical ProductionRequestPlan.
        for ticker in self.subjects:
            purposes = {r.purpose for r in self.source_roles if r.role.symbol == ticker}
            if not {'TECHNICAL', 'FINANCIAL', 'BUSINESS', 'VALUATION'} <= purposes:
                raise ValueError("PLAN_GAP_subject_source_family:"+ticker)
        if not any(r.purpose == 'MARKET' for r in self.source_roles):
            raise ValueError("PLAN_GAP_market_context")
        return self


def build_production_policy(*, market, subjects, source_roles, code_config_sha256):
    subjects = tuple(subjects)
    return ProductionSnapshotPolicy(market=market, subjects=subjects,
        roles=tuple(r.role for r in source_roles), source_roles=tuple(source_roles),
        validator_contracts=VALIDATORS, universe_owner_sha256=digest(subjects),
        message_ids=("MARKET_"+market.upper(), *subjects), code_config_sha256=code_config_sha256)


class ProductionRoleResolution(ContractModel):
    role_key: str
    provider: str
    route: str
    owner_contract: str
    state: Literal["AVAILABLE", "TYPED_UNAVAILABLE", "TRANSPORT_FAILED", "INVALID"]
    raw_receipt_sha256: str = Field(pattern=SHA)
    normalized_sha256: str = Field(pattern=SHA)
    owner_result_sha256: str = Field(pattern=SHA)
    provenance_sha256: str = Field(pattern=SHA)
    observed_at: datetime
    current_eligible_count: int = Field(ge=0)
    reason_codes: tuple[str, ...] = ()
    value: object
    owner_result: dict
    provenance: dict

    @model_validator(mode="after")
    def owner_binding(self):
        if (digest(self.value) != self.normalized_sha256 or digest(self.owner_result) != self.owner_result_sha256
                or digest(self.provenance) != self.provenance_sha256 or self.observed_at.utcoffset() is None):
            raise ValueError("production_source_owner_hash_mismatch")
        if self.state == "AVAILABLE" and (self.current_eligible_count != 1 or self.value is None or self.reason_codes):
            raise ValueError("production_current_value_ownership_invalid")
        if self.state == "TYPED_UNAVAILABLE" and (self.current_eligible_count != 0 or self.value is not None or not self.reason_codes):
            raise ValueError("production_typed_denial_invalid")
        return self


class ProductionSourceExecutionEnvelopeV1(ContractModel):
    contract: Literal["production-source-execution-envelope-v1"] = CONTRACT
    execution_purpose: Literal["PRODUCTION_MONITORING"] = "PRODUCTION_MONITORING"
    market: Literal["us", "kr"]
    run_id: str
    attempt_id: str
    generation_id: str
    subjects: tuple[str, ...]
    source_policy_sha256: str = Field(pattern=SHA)
    code_config_sha256: str = Field(pattern=SHA)
    started_at: datetime
    completed_at: datetime
    target_session: date
    required_roles: tuple[str, ...]
    optional_roles: tuple[str, ...]
    resolutions: tuple[ProductionRoleResolution, ...]
    packet_sha256: str = Field(pattern=SHA)

    @model_validator(mode="after")
    def exact_cycle(self):
        if (any(t.utcoffset() is None for t in (self.started_at, self.completed_at))
                or self.started_at > self.completed_at or not self.attempt_id.startswith(self.run_id+"-attempt-")
                or self.generation_id != self.attempt_id):
            raise ValueError("production_source_cycle_binding")
        roles = self.required_roles + self.optional_roles
        if len(set(roles)) != len(roles) or sorted(roles) != sorted(r.role_key for r in self.resolutions):
            raise ValueError("PLAN_GAP_source_role_coverage")
        if any(not self.started_at <= r.observed_at <= self.completed_at for r in self.resolutions):
            raise ValueError("production_source_stale_observation")
        return self


class ProductionCollection(Collection):
    production_envelope: ProductionSourceExecutionEnvelopeV1


def validate_production_collection(collection, *, policy, run_id, attempt_id, started_at, now):
    try:
        policy = ProductionSnapshotPolicy.model_validate(policy.model_dump(mode="json"))
        collection = ProductionCollection.model_validate(collection.model_dump(mode="json"))
    except ValueError:
        return ["production_contract_revalidation_failed"]
    errors = validate_collection(collection, policy=policy, run_id=run_id,
        attempt_id=attempt_id, started_at=started_at, now=now)
    if not isinstance(collection, ProductionCollection) or not isinstance(policy, ProductionSnapshotPolicy):
        return errors + ["production_runtime_source_contract_required"]
    envelope = collection.production_envelope
    if (envelope.run_id, envelope.attempt_id, envelope.market, envelope.subjects,
            envelope.source_policy_sha256, envelope.code_config_sha256, envelope.packet_sha256,
            envelope.started_at, envelope.completed_at) != (
            run_id, attempt_id, policy.market, policy.subjects, digest(policy.model_dump(mode="json")),
            policy.code_config_sha256, digest(collection.packet), collection.started_at, collection.completed_at):
        errors.append("production_source_envelope_binding_mismatch")
    expected = {r.role.key: r for r in policy.source_roles}
    if envelope.required_roles != tuple(k for k, r in expected.items() if r.required) or envelope.optional_roles != tuple(k for k, r in expected.items() if not r.required):
        errors.append("production_required_optional_role_drift")
    receipts = {r.role: r for r in collection.receipts}
    for row in envelope.resolutions:
        spec = expected.get(row.role_key)
        if spec is None:
            errors.append("production_undeclared_role")
            continue
        if (row.provider, row.route, row.owner_contract) != (spec.role.provider, spec.role.route, spec.owner_contract):
            errors.append("production_source_owner_identity")
        # Required means a declared/requested owner, not a guaranteed value.
        # Canonical consumer owners decide whether a typed denial is usable.
        if row.state not in {"AVAILABLE", "TYPED_UNAVAILABLE"}:
            errors.append("production_required_role_not_qualified:"+row.role_key)
        receipt = receipts.get(row.role_key)
        if not receipt or (receipt.raw_sha256, receipt.normalized_sha256) != (row.raw_receipt_sha256, row.normalized_sha256):
            errors.append("production_raw_normalized_receipt_mismatch")
        try:
            if pointer(collection.packet, spec.role.packet_pointer) != row.value:
                errors.append("production_source_value_binding")
        except (KeyError, IndexError, TypeError, ValueError):
            errors.append("production_source_value_absent")
        if row.provenance.get("generation_id") != envelope.generation_id or row.provenance.get("attempt_id") != envelope.attempt_id:
            errors.append("production_source_provenance_generation")
        if (row.provenance.get("target_session") != envelope.target_session.isoformat()
                or row.provenance.get("role") != row.role_key
                or row.provenance.get("raw_receipt_sha256") != row.raw_receipt_sha256
                or row.owner_result.get("contract") != row.owner_contract
                or row.owner_result.get("generation_id") != envelope.generation_id
                or row.owner_result.get("role") != row.role_key
                or row.owner_result.get("raw_receipt_sha256") != row.raw_receipt_sha256
                or row.owner_result.get("normalized_sha256") != row.normalized_sha256
                or row.owner_result.get("state") != row.state
                or row.owner_result.get("current_eligible_count") != row.current_eligible_count):
            errors.append("production_source_owner_provenance_binding")
    return errors
