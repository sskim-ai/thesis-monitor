"""Replay selected persisted source rows through their existing read-only owners.

The bridge opens only a new in-memory database. It never locates operating
storage, refreshes providers, or accepts the stored projection as its verdict.
"""

from __future__ import annotations

from datetime import datetime
import hashlib
import json
from pathlib import Path

from sqlmodel import Session, SQLModel, create_engine

from app.models.event import Event
from app.models.financial import FinancialSnapshot
from app.models.macro import MacroEvent, MacroObservation
from app.models.security import ConsensusEstimate, SecurityMaster
from app.services.unified_class_c_owners import (
    FINANCIAL_ROLES, MACRO_ROLES, project_estimate_inventory, project_macro_records,
    project_published_events, project_reported_financial,
)
from app.services.unified_run_artifacts import durable_json
from app.services.unified_snapshot_contract import digest
from app.services.unified_source_composition import C, OwnerAdapter, OwnerProjection, SourceInput, SourceRole
from app.services.unified_source_policy import UnifiedSourcePolicy


MODELS = {m.__tablename__: m for m in (
    SecurityMaster, FinancialSnapshot, Event, MacroObservation, MacroEvent, ConsensusEstimate)}
FED = "central_bank_published_events"
ESTIMATE = "eligible_valuation_estimates"
DENIAL = "no_eligible_consumed_persisted_value"
PROVIDERS = {**FINANCIAL_ROLES, **{k: v[0] for k, v in MACRO_ROLES.items()},
             FED: "federal_reserve", ESTIMATE: "finnhub"}


def _role_family(role, family):
    allowed = {PROVIDERS.get(family)}
    if family == "sec_financial_fundamental_domains":
        allowed.add("sec_edgar")
    if family == "kr_overnight_cross_assets":
        allowed.add("declared_us_macro_sources")
    if (role.acquisition_class != C or family not in PROVIDERS
            or role.provider not in allowed
            or role.key not in {family, family + ":" + role.symbol}):
        raise ValueError("persisted_role_family_mismatch")


def project(session, *, role, ticker, cutoff, policy):
    if role in FINANCIAL_ROLES:
        return project_reported_financial(session, role=role, ticker=ticker, cutoff=cutoff, policy=policy)
    if role in MACRO_ROLES:
        return project_macro_records(session, role=role, cutoff=cutoff, policy=policy)
    if role == FED:
        return project_published_events(session, cutoff=cutoff, policy=policy)
    if role == ESTIMATE:
        # The persisted Finnhub producer records provider-defined forwardPE, not
        # the per-security forward EPS/date required by earnings_receipt. Never
        # turn that inventory into a denominator, even if the number is present.
        return project_estimate_inventory(session, ticker=ticker, cutoff=cutoff, policy=policy)
    raise ValueError("persisted_role_not_implemented")


def _semantic_records(records):
    return [{"table": r["table"], "record_id": r["record_id"], "record": r["record"]} for r in records]


def persisted_owner(*, role: SourceRole, family: str, policy: UnifiedSourcePolicy) -> OwnerAdapter:
    _role_family(role, family)
    def replay(raw: bytes, cutoff: datetime) -> OwnerProjection:
        document = json.loads(raw)
        if (document.get("contract") != "unified-persisted-owner-input-v1"
                or document.get("role") != role.model_dump(mode="json")
                or document.get("family") != family):
            raise ValueError("persisted_input_identity_mismatch")
        original = document["projection"]
        if (digest({k: v for k, v in original.items() if k != "projection_sha256"})
                != original["projection_sha256"] or digest(original["records"]) != original["version"]):
            raise ValueError("persisted_projection_hash_mismatch")
        engine = create_engine("sqlite://")
        try:
            SQLModel.metadata.create_all(engine, tables=[m.__table__ for m in MODELS.values()])
            with Session(engine) as session:
                seen = set()
                for record in original["records"]:
                    table, value = record["table"], record["record"]
                    if (table not in MODELS or str(value.get("id")) != record["record_id"]
                            or (table, record["record_id"]) in seen):
                        raise ValueError("persisted_record_identity_mismatch")
                    seen.add((table, record["record_id"]))
                    policy.check_lineage(value)
                    if table == MacroEvent.__tablename__ and {"inferred_implications", "unknowns"} & value.keys():
                        raise ValueError("stored_model_implication_forbidden")
                    if "raw_payload" in value:
                        policy.check_lineage(json.loads(value["raw_payload"]))
                    session.add(MODELS[table].model_validate(value))
                session.commit()
                current = project(session, role=family, ticker=role.symbol, cutoff=cutoff, policy=policy)
        finally:
            engine.dispose()
        if current["owner_fingerprints"] != original["owner_fingerprints"]:
            raise ValueError("persisted_owner_fingerprint_changed")
        if _semantic_records(current["records"]) != _semantic_records(original["records"]):
            raise ValueError("persisted_selected_record_set_changed")
        if current["normalized_sha256"] != original["normalized_sha256"]:
            raise ValueError("persisted_current_consumption_changed")
        eligible = bool(current["values"]) and current["eligible"]
        # Original observation timestamps remain inside the owner value. The
        # replay cutoff is only an eligibility time, never a new source time.
        return OwnerProjection(current["values"] if eligible else None, role.provider,
            role.market, role.symbol, role.basis, role.session, eligible,
            None if eligible else DENIAL, None, role.key, original["version"])
    fingerprint = digest({"bridge": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        "owner": hashlib.sha256(Path(__file__).with_name("unified_class_c_owners.py").read_bytes()).hexdigest()})
    return OwnerAdapter("unified-persisted-owner-bridge-v1", fingerprint, replay)


def capture_persisted_owner(session: Session, *, root: Path, run_id: str, role: SourceRole,
                           family: str, cutoff: datetime, policy: UnifiedSourcePolicy):
    _role_family(role, family)
    policy.require(role.provider)
    projected = project(session, role=family, ticker=role.symbol, cutoff=cutoff, policy=policy)
    document = {"contract": "unified-persisted-owner-input-v1", "family": family,
                "role": role.model_dump(mode="json"), "projection": projected}
    artifact = "persisted-" + digest(role.model_dump(mode="json")) + ".json"
    durable_json(root / artifact, document, exclusive=True)
    item = SourceInput(role=role.key, run_id=run_id, acquisition_class=C,
        original_record_id=role.key, version=projected["version"], artifact=artifact,
        artifact_sha256=hashlib.sha256((root / artifact).read_bytes()).hexdigest(),
        denial=None if projected["values"] and projected["eligible"] else DENIAL)
    return item, persisted_owner(role=role, family=family, policy=policy)
