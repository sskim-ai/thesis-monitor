"""Default-OFF scoped replay into the existing canonical stock owners.

This is an offline diagnostic boundary. A canonical packet is not current
identity, raw-parser replay, market completeness, D02 or model admission.
"""
from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from typing import Literal

from pydantic import Field
from app.models.security import SecurityMaster

from app.services.fresh_financial_stock_owner import assemble_fresh_stock
from app.services.scoped_source_plan import (
    R22ScopedSourcePlanV1, ScopedStockRead, validate_scoped_structure,
)
from app.services.sealed_native_bridge import require_complete_stock_window
from app.services.unified_snapshot_contract import ContractModel, digest
from app.services.unified_stock_acquisition import decode_owned_role
from app.services.unified_run_artifacts import sha256_bytes

ROOT = Path(__file__).resolve().parents[2]
OWNER_FILES = (
    "app/services/scoped_native_source.py", "app/services/fresh_financial_stock_owner.py",
    "app/services/unified_stock_owner.py", "app/services/bounded_financial_stock_owner.py",
    "app/services/sealed_native_bridge.py", "app/services/cross_market_decision_engine_service.py",
    "app/services/direction_timing_ownership_service.py",
)


class ScopedOwnerReplayPlan(ContractModel):
    """Explicit per-read owner protocol; never a legacy StockPlan or 22-stock plan."""
    contract: Literal["scoped-canonical-owner-replay-v1"] = "scoped-canonical-owner-replay-v1"
    scope: Literal["OFFLINE_DIAGNOSTIC_ONLY"] = "OFFLINE_DIAGNOSTIC_ONLY"
    source_plan_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    run_id: str
    acquisition_id: str
    frozen_at: datetime
    implementation_sha: str
    reads: tuple[ScopedStockRead, ...]
    owner_sha256: dict[str, str]


def owner_replay_plan(scoped, *, compiler_inputs, enabled=False):
    if enabled is not True:
        raise ValueError("scoped_native_feature_off")
    scoped = R22ScopedSourcePlanV1.model_validate(scoped)
    validate_scoped_structure(scoped, **compiler_inputs)
    return ScopedOwnerReplayPlan(source_plan_sha256=scoped.plan_sha256,
        run_id=scoped.request_plan.generation_id,
        acquisition_id=scoped.request_plan.generation_id + ":scoped-owner-replay",
        frozen_at=scoped.request_plan.frozen_at,
        implementation_sha=scoped.request_plan.code_sha, reads=scoped.stock_reads,
        owner_sha256={name: sha256_bytes((ROOT / name).read_bytes()) for name in OWNER_FILES})


def replay_scoped_stock(scoped, *, compiler_inputs, ticker, owner_inputs, enabled=False):
    """Call real financial/technical/DecisionEvidencePacket builders, without grants.

    Inputs are the existing canonical owner inputs, not LaneSourcePacketV1,
    prebuilt evidence, caller PASS flags, or a substituted historical StockPlan.
    The output is intentionally ineligible for direct model dispatch.
    """
    plan = owner_replay_plan(scoped, compiler_inputs=compiler_inputs, enabled=enabled)
    scoped = R22ScopedSourcePlanV1.model_validate(scoped)
    bindings = [b for b in scoped.identities if b.subject.ticker == ticker]
    if len(bindings) != 1:
        raise ValueError("scoped_native_subject_not_planned")
    subject = bindings[0].subject
    allowed = {"technical_inputs", "financial_inputs", "valuation_inputs", "event_inputs", "source_window"}
    if set(owner_inputs) - allowed or not {"technical_inputs", "financial_inputs"} <= set(owner_inputs):
        raise ValueError("scoped_native_canonical_inputs_required")
    technical = owner_inputs["technical_inputs"]
    if type(technical["plan"]) is not ScopedOwnerReplayPlan or technical["plan"] != plan:
        raise ValueError("scoped_native_plan_identity")
    if technical["ticker"] != ticker:
        raise ValueError("scoped_native_subject_identity")
    financial_plan = owner_inputs["financial_inputs"]["plan"]
    security = financial_plan["security"]
    original = compiler_inputs["catalog"].record(bindings[0], at=compiler_inputs["at"])
    def identity(value):
        # Detached SQLite row IDs are transport-local; canonical IDs and every
        # security/issuer/property field remain equal to the sealed record.
        row = SecurityMaster.model_validate(value)
        # Match the inherited routing owner's UTC convention for SQLite's
        # naive updated_at; original sealed bytes remain separately pinned.
        if row.updated_at is not None:
            row.updated_at = (row.updated_at.replace(tzinfo=timezone.utc) if row.updated_at.utcoffset() is None
                              else row.updated_at.astimezone(timezone.utc))
        return row.model_dump(mode="json", exclude={"id"})
    local = [r["record"] for role in technical["local_seed"]["roles"].values()
        for r in role["records"] if r["table"] == "securitymaster" and r["record"].get("ticker") == ticker]
    if (digest(original) != bindings[0].record_sha256 or identity(security) != identity(original)
            or len(local) != 1 or identity(local[0]) != identity(original)):
        raise ValueError("scoped_native_sealed_identity_record_mismatch")
    if (security.get("ticker"), security.get("canonical_security_id"),
            security.get("cik") if subject.market == "us" else security.get("corp_code"),
            security.get("exchange")) != (ticker, subject.security_id, subject.issuer_id, subject.venue):
        raise ValueError("scoped_native_financial_security_identity")
    if (financial_plan["run_id"] != plan.run_id
            or financial_plan["cutoff"] != plan.frozen_at.isoformat()):
        raise ValueError("scoped_native_financial_generation_identity")
    reads = [r for r in plan.reads if r.subject == ticker]
    if set(technical["receipts"]) != {r.role for r in reads}:
        raise ValueError("scoped_native_role_membership")

    def reader(path, sha):
        # decode_owned_role checks the bytes itself; no normalizer result trust.
        return technical["artifacts"][path]

    for read in reads:
        receipt = technical["receipts"][read.role]
        rows = decode_owned_role(plan, read, receipt, reader)
        require_complete_stock_window(read, receipt, rows)
    result = assemble_fresh_stock(**owner_inputs)
    if (result["fresh_run_id"] != plan.run_id
            or result["packet"]["stocks"][0]["ticker"] != ticker):
        raise ValueError("scoped_native_owner_output_identity")
    return dict(contract="scoped-native-canonical-diagnostic-v1",
        source_plan_sha256=scoped.plan_sha256, owner_plan_sha256=digest(plan.model_dump(mode="json")),
        ticker=ticker, canonical_owner_result=result,
        canonical_owner_status=result["status"],
        native_type="DecisionEvidencePacket", native_evidence_sha256=digest(result["evidence_packet"]),
        source_use="NOT_ADMITTED", model_dispatch_allowed=False,
        missing_admission=["CURRENT_SECURITY_AND_ETF_IDENTITY", "SEALED_NATIVE_RAW_PARSER_REPLAY",
            "COMPLETE_MARKET_SOURCE_OWNER_REPLAY", "CURRENT_D01_D02", "RESOURCE_ADMISSION"],
        source_generation=plan.run_id, historical_identity_generation=bindings[0].source_generation)
