"""Immutable local configuration bridge with fresh owner checks on frozen rows.

Replay uses an isolated in-memory database, never the operating database. No
assessment rows, query-time prices, or hidden cache lookups are permitted.
"""

from __future__ import annotations

from datetime import datetime
import hashlib
import json
from pathlib import Path

from sqlmodel import Session, SQLModel, create_engine

from app.models.company import Company
from app.models.security import SecurityMaster
from app.models.thesis import InvestmentThesis
from app.models.watchlist import WatchlistItem
from app.services.unified_class_c_owners import LOCAL_ROLES
from app.services.unified_persisted_projection import project_local_seed
from app.services.unified_run_artifacts import durable_json
from app.services.unified_snapshot_contract import digest
from app.services.unified_source_composition import C, OwnerAdapter, OwnerProjection, SourceInput, SourceRole
from app.services.unified_source_policy import UnifiedSourcePolicy


MODELS = {m.__tablename__: m for m in (WatchlistItem, SecurityMaster, InvestmentThesis, Company)}
WATCH_FIELDS = {"id", "ticker", "company_name", "exchange", "monitoring_requested", "active",
                "onboarding_state", "production_eligible", "activated_at", "first_eligible_session", "created_at"}


def _semantic(records):
    return [{"table": r["table"], "record_id": r["record_id"], "record": r["record"]} for r in records]


def local_owner(*, role: str, market: str, session_key: str, policy: UnifiedSourcePolicy) -> OwnerAdapter:
    if role not in LOCAL_ROLES:
        raise ValueError("unknown_local_seed_role")
    def replay(raw: bytes, cutoff: datetime) -> OwnerProjection:
        document = json.loads(raw)
        if document.get("contract") != "unified-local-seed-projection-v1" or (
            document.get("market"), document.get("session")) != (market, session_key):
            raise ValueError("local_seed_identity_mismatch")
        engine = create_engine("sqlite://")
        try:
            SQLModel.metadata.create_all(engine, tables=[m.__table__ for m in MODELS.values()])
            with Session(engine) as session:
                identities = set()
                for component in document["roles"].values():
                    if component["version"] != digest(component["records"]):
                        raise ValueError("local_record_version_mismatch")
                    for record in component["records"]:
                        table, value = record["table"], record["record"]
                        if table not in MODELS or str(value.get("id")) != record["record_id"]:
                            raise ValueError("local_record_identity_mismatch")
                        identity = (table, record["record_id"])
                        if identity in identities:
                            raise ValueError("duplicate_local_record")
                        identities.add(identity)
                        if table == WatchlistItem.__tablename__ and set(value) - WATCH_FIELDS:
                            raise ValueError("local_seed_previous_assessment_not_allowed")
                        if table == SecurityMaster.__tablename__:
                            policy.require(value.get("identity_provider"))
                        session.add(MODELS[table].model_validate(value))
                session.commit()
                projected = project_local_seed(session, market=market, session_key=session_key,
                                               cutoff=cutoff, policy=policy)
        finally:
            engine.dispose()
        if projected["owner_fingerprints"] != document["owner_fingerprints"]:
            raise ValueError("local_owner_fingerprint_changed")
        for name in LOCAL_ROLES:
            if _semantic(projected["roles"][name]["records"]) != _semantic(document["roles"][name]["records"]):
                raise ValueError("frozen_local_selection_changed")
        component = document["roles"][role]
        eligible = projected["roles"][role]["eligible"]
        if component["eligible"] != eligible:
            raise ValueError("frozen_local_eligibility_changed")
        return OwnerProjection(component, "canonical_local", market, "*", "versioned_configuration",
            session_key, eligible, None if eligible else "local_current_eligibility_failed", None,
            f"{market}:{session_key}:{role}", component["version"])
    fingerprint = digest({"bridge": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
                          "projection": hashlib.sha256(Path(__file__).with_name("unified_persisted_projection.py").read_bytes()).hexdigest()})
    return OwnerAdapter("unified-local-seed-bridge-v1", fingerprint, replay)


def capture_local_seed(session: Session, *, root: Path, run_id: str, market: str,
                       session_key: str, cutoff: datetime, policy: UnifiedSourcePolicy):
    projection = project_local_seed(session, market=market, session_key=session_key, cutoff=cutoff, policy=policy)
    artifact = f"local-{market}.json"
    durable_json(root / artifact, projection, exclusive=True)
    source_sha = hashlib.sha256((root / artifact).read_bytes()).hexdigest()
    roles, inputs, owners = [], [], {}
    for name in LOCAL_ROLES:
        key = f"{market}:{name}"
        owner_name = f"unified_local_seed:{market}:{name}"
        roles.append(SourceRole(key=key, owner=owner_name, market=market, symbol="*", acquisition_class=C,
            mandatory=True, provider="canonical_local", basis="versioned_configuration", session=session_key))
        inputs.append(SourceInput(role=key, run_id=run_id, acquisition_class=C,
            original_record_id=f"{market}:{session_key}:{name}", version=projection["roles"][name]["version"],
            artifact=artifact, artifact_sha256=source_sha))
        owners[owner_name] = local_owner(role=name, market=market, session_key=session_key, policy=policy)
    return tuple(roles), tuple(inputs), owners
