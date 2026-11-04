"""Owner-replayed historical references, never replacement acquisition receipts.

Only the trusted backend opens an independently pinned archive. Public reference
JSON cannot restore a live capability. A/B current acquisition stays mandatory.
"""

from copy import deepcopy
from datetime import datetime
from hashlib import sha256
import json
from pathlib import PurePosixPath
from weakref import WeakKeyDictionary

from app.services.retained_raw_stock_materializer import RetainedArchive, _relative
from app.services.unified_snapshot_contract import digest
from app.services.unified_stock_acquisition import StockPlan, decode_owned_role
from app.services.sealed_native_bridge import require_complete_stock_window

CONTRACT = "prior-source-historical-use-v1"
PURPOSE = "MANUAL_SHADOW_UNSENT"
_STORES = WeakKeyDictionary()
_REFERENCES = WeakKeyDictionary()


class PriorSourceStore:
    __slots__ = ("__weakref__",)


class StockReference:
    __slots__ = ("__weakref__",)


def open_prior_store(*, archive, archive_sha256, manifest_sha256, content_map_member):
    """Control-plane entry: pins must come from the independently accepted seal."""
    retained = RetainedArchive(
        archive,
        archive_sha256=archive_sha256,
        manifest_member="manifest.json",
        manifest_sha256=manifest_sha256,
    )
    mapping = retained.json(content_map_member, "sealed_logical_source_map")
    if mapping.get("contract") != "exact-byte-content-addressed-evidence-v1":
        raise ValueError("prior_source_map_contract")
    for name, row in mapping["files"].items():
        _relative(name)
        blob = str(_relative(row["blob"]))
        if blob != "blobs/" + row["sha256"] or retained.files.get(blob) != {
            k: row[k] for k in ("bytes", "sha256")
        }:
            raise ValueError("prior_source_map_binding")
    handle = PriorSourceStore()
    _STORES[handle] = (retained, mapping["files"])
    return handle


def read_prior_source(store, name):
    if type(store) is not PriorSourceStore or store not in _STORES:
        raise ValueError("prior_source_live_store_required")
    retained, mapping = _STORES[store]
    name = str(_relative(name))
    if name not in mapping:
        raise ValueError("prior_source_not_in_seal")
    return retained.read(mapping[name]["blob"], "original:" + name)


def replay_stock_reference(*, store, plan_member, receipt_member, entry_id):
    frozen = json.loads(read_prior_source(store, plan_member))
    plan = StockPlan.model_validate(frozen["stock_plan"])
    if frozen["generation_id"] != plan.run_id:
        raise ValueError("prior_original_generation_mismatch")
    read = next((r for r in plan.reads if r.entry_id == entry_id), None)
    if read is None:
        raise ValueError("prior_original_read_missing")
    receipt_raw = read_prior_source(store, receipt_member)
    receipt = json.loads(receipt_raw)
    parent = PurePosixPath(receipt_member).parent

    def source(name, pin):
        raw = read_prior_source(store, str(parent / _relative(name)))
        if sha256(raw).hexdigest() != pin:
            raise ValueError("prior_original_artifact_hash")
        return raw

    rows = decode_owned_role(plan, read, receipt, source)
    require_complete_stock_window(read, receipt, rows)
    retained, _ = _STORES[store]
    identity = dict(
        contract=CONTRACT,
        origin_archive_sha256=retained.archive_sha256,
        origin_generation=plan.run_id,
        origin_plan_sha256=digest(plan.model_dump(mode="json")),
        original_receipt_sha256=sha256(receipt_raw).hexdigest(),
        receipt_member=receipt_member,
        acquisition_id=plan.acquisition_id,
        source_observed_at=receipt["completed_at"],
        requested_at=receipt["started_at"],
        normalized_sha256=receipt["normalized_sha256"],
        source_pages=[
            dict(
                sha256=p["source_sha256"],
                requested_at=p["requested_at"],
                received_at=p["received_at"],
                request_sha256=p["request_sha256"],
            )
            for p in receipt["pages"]
        ],
        read=read.model_dump(mode="json"),
        historical_owner="decode_owned_role",
        original_owner_code_pins=plan.owner_files,
        origin_frozen_at=plan.frozen_at.isoformat(),
        source_use_authority="NOT_CURRENT_ACQUISITION_NOT_D02",
    )
    handle = StockReference()
    _REFERENCES[handle] = (store, json.dumps(identity), json.dumps(rows))
    return handle, deepcopy(identity)


def _reference(handle):
    if type(handle) is not StockReference or handle not in _REFERENCES:
        raise ValueError("prior_source_live_reference_required")
    store, identity, rows = _REFERENCES[handle]
    if store not in _STORES:
        raise ValueError("prior_source_store_revoked")
    return json.loads(identity), json.loads(rows)


def classify_stock_use(
    reference,
    *,
    consumer_generation,
    cutoff,
    security_id,
    market,
    session,
    role,
    consumer,
    use_axis,
    purpose=PURPOSE,
):
    origin, _ = _reference(reference)
    read = origin["read"]
    if (
        not consumer_generation
        or consumer_generation == origin["origin_generation"]
        or purpose != PURPOSE
        or cutoff.utcoffset() is None
        or datetime.fromisoformat(origin["source_observed_at"]) > cutoff
    ):
        raise ValueError("prior_use_generation_time_or_scope")
    if (
        read["canonical_security_id"],
        read["market"],
        read["latest_completed_session"],
        read["role"],
    ) != (security_id, market, session, role):
        raise ValueError("prior_use_identity_basis_session")
    from app.services.prospective_class_c_owner import completed_clock

    if session != completed_clock(market, cutoff)["target"]:
        raise ValueError("prior_use_completed_session_changed")
    context = (
        consumer == "TECHNICAL_CONTEXT"
        and use_axis == "HISTORICAL_CHART_CONTEXT"
        and read["adjusted"]
    )
    result = dict(
        contract=CONTRACT,
        origin=origin,
        consumer_generation=consumer_generation,
        cutoff=cutoff.isoformat(),
        security_id=security_id,
        market=market,
        session=session,
        role=role,
        consumer=consumer,
        use_axis=use_axis,
        purpose=purpose,
        decision="DENIED" if context else "FRESH_WINDOW_REQUIRED",
        reason="HISTORICAL_CHART_REUSE_POLICY_AND_CORRECTION_AUTHORITY_REQUIRED"
        if context
        else "CURRENT_ACQUISITION_WINDOW_REQUIRED",
        D01="HISTORICAL_SOURCE_ONLY",
        D02="NOT_GRANTED",
        current_required_acquisition="NOT_SATISFIED",
        correction_state="NO_POST_CAPTURE_REVISION_ATTESTATION",
        expiry="NO_CURRENT_USE_ISSUED",
        allowed_semantics="Original-generation audit replay only; no native current consumer permission",
        denied_semantics=[
            "current_quote",
            "unadjusted_valuation",
            "investment_direction",
            "fresh_acquisition",
        ],
    )
    return result


def revoke_prior_store(store):
    if store not in _STORES:
        raise ValueError("prior_source_live_store_required")
    del _STORES[store]
