"""Versioned event-review discovery, deliberately outside decision authority."""
from copy import deepcopy

from app.services.canonical_fact_service import canonical_event_fact
from app.services.fundamental_input_policy import source_use
from app.services.persisted_business_event_owner import replay_persisted_event
from app.services.unified_snapshot_contract import digest
from app.services.unified_stock_event_input import replay_news
from scripts.m12cn_policy_contract import build_subject_catalog
from scripts.m12da_source_use_contract import SourceUse, canonical_sha256
from scripts.m12dk_current_source_authority import freeze_current_source_binding
from scripts.m12dr_offline_source_closure import context


CONTRACT = "context-only-authority-discovery-v1"
PURPOSE = "CONTEXT_ONLY_AUTHORITY_DISCOVERY"
_DENIED = sorted(use.value for use in SourceUse if use != SourceUse.CONTEXT)


def _require_purpose(purpose, use=SourceUse.CONTEXT.value):
    if purpose != PURPOSE or use != SourceUse.CONTEXT.value:
        raise ValueError("context_discovery_purpose_or_use_denied")


def _seal(view):
    view["view_sha256"] = canonical_sha256(view)
    return view


def _require_exact_view(view, expected):
    if (type(view) is not dict or set(view) != set(expected)
            or type(view.get("context_records")) is not list
            or any(type(row) is not dict for row in view["context_records"])
            or canonical_sha256(view) != canonical_sha256(expected)):
        raise ValueError("context_discovery_trusted_input_mismatch")


def build_context_discovery_v1(*, ticker, source_generation_id, execution_generation_id,
                               source_packet, evidence_packet, catalog, frozen_binding,
                               purpose=PURPOSE):
    """Discover unverified event candidates from exact, independently frozen inputs."""
    _require_purpose(purpose)
    if any(type(value) is not str or not value for value in
           (ticker, source_generation_id, execution_generation_id)):
        raise ValueError("context_discovery_identity_missing")
    expected_binding = freeze_current_source_binding(
        source_generation_id=source_generation_id, source_packet=source_packet,
        evidence_packet=evidence_packet)
    if (expected_binding != frozen_binding or ticker != expected_binding["ticker"]
            or canonical_sha256(expected_binding) != canonical_sha256(frozen_binding)):
        raise ValueError("context_discovery_frozen_binding_mismatch")
    # Rebuild the legacy projection; caller labels and rehashed metadata are not owners.
    legacy_context = context(source_packet, execution_generation_id)
    expected_packet = next(row for row in legacy_context["evidence_packets"]
                           if row["ticker"] == ticker)
    expected_catalog = build_subject_catalog(
        context=legacy_context, ticker=ticker, atomic_claims=[])
    if (canonical_sha256(evidence_packet) != canonical_sha256(expected_packet)
            or canonical_sha256(catalog) != canonical_sha256(expected_catalog)):
        raise ValueError("context_discovery_legacy_projection_mismatch")
    stock = next(row for row in source_packet["stocks"] if row["ticker"] == ticker)
    facts = [canonical_event_fact(row) for row in stock.get("evidence", [])]
    actual = [row for row in stock["fact_catalog"] if row["fact_id"].startswith("event:")]
    if (any(row is None for row in facts)
            or canonical_sha256(facts) != canonical_sha256(actual)
            or len({row["fact_id"] for row in facts}) != len(facts)):
        raise ValueError("context_discovery_canonical_event_mismatch")
    facts_by_ref = {"canonical:" + row["fact_id"]: row for row in facts}
    rows = [row for row in evidence_packet["evidence"]
            if row["ref_id"].startswith("canonical:event:")
            or row["source_ref"].startswith("stock.fact_catalog.event:")]
    if len(rows) != len(facts) or {row["ref_id"] for row in rows} != set(facts_by_ref):
        raise ValueError("context_discovery_event_ref_set_mismatch")
    actionable = set().union(*(set(catalog.get(key, [])) for key in (
        "all_evidence_refs", "core_evidence_refs", "timing_evidence_refs", "valuation_evidence_refs")))
    if actionable & set(facts_by_ref):
        raise ValueError("context_discovery_action_catalog_overlap")
    records = []
    for row in sorted(rows, key=lambda item: item["ref_id"]):
        fact = facts_by_ref[row["ref_id"]]
        path = "stock.fact_catalog." + fact["fact_id"]
        expected_use = source_use(source_ref=path, security_id=ticker,
                                  canonical=True, event=True).model_dump(mode="json")
        if row["source_ref"] != path or row.get("source_use") != expected_use:
            raise ValueError("context_discovery_event_producer_mismatch")
        records.append(dict(ref_id=row["ref_id"], source_ref=path,
            event_fingerprint=fact["source_event_fingerprint"],
            source_metadata_sha256=canonical_sha256(row), authority_state="UNRESOLVED",
            allowed_uses=[SourceUse.CONTEXT.value], prohibited_uses=list(_DENIED),
            requires_review=True, source_scope="unverified_event_context_only_requires_review"))
    return _seal(dict(contract=CONTRACT, purpose=PURPOSE, ticker=ticker,
        market=source_packet["market"], source_generation_id=source_generation_id,
        execution_generation_id=execution_generation_id, cutoff=source_packet["generated_at"],
        packet_id=source_packet["packet_id"], source_binding_sha256=expected_binding["binding_sha256"],
        decision_catalog_sha256=canonical_sha256(catalog),
        context_refs=[row["ref_id"] for row in records], context_records=records,
        persisted_event_receipt_sha256=None, original_run_id=None, original_acquisition_id=None))


def _resolved_from_inputs(*, event_inputs, observed_business_union, persisted_event_receipt,
                          **frozen_inputs):
    if (type(observed_business_union) is not list
            or any(type(row) is not dict for row in observed_business_union)):
        raise ValueError("context_discovery_observed_event_union_shape")
    expected = build_context_discovery_v1(**frozen_inputs)
    source, receipt = replay_persisted_event(**event_inputs)
    if (receipt["ticker"] != expected["ticker"] or receipt["market"] != expected["market"]
            or receipt["current_run_id"] != expected["source_generation_id"]
            or receipt["current_eligibility_cutoff"] != expected["cutoff"]
            or canonical_sha256(receipt) != canonical_sha256(persisted_event_receipt)):
        raise ValueError("context_discovery_replay_identity_mismatch")
    replayed = replay_news(source, security=source.read.security,
        business_cutoff=event_inputs["cutoff"], policy=event_inputs["policy"],
        source_query_cutoff=event_inputs.get("source_query_cutoff"))
    stock = next(row for row in frozen_inputs["source_packet"]["stocks"]
                 if row["ticker"] == expected["ticker"])
    if canonical_sha256(stock["evidence"]) != canonical_sha256(replayed["evidence"]):
        raise ValueError("context_discovery_raw_replay_source_mismatch")
    selected = {row["event_fingerprint"]: row for row in replayed["selected"]
                if row["status"] == "PASS"}
    wanted = []
    for record in expected["context_records"]:
        event = selected.get(record["event_fingerprint"])
        if event is None or event.get("requires_review") is not True:
            raise ValueError("context_discovery_selected_event_requires_review")
        wanted.append(dict(status="PASS", source_kind="PERSISTED_BUSINESS_EVENT",
            ref_id=record["ref_id"], ticker=expected["ticker"],
            event_fingerprint=record["event_fingerprint"],
            source_receipt_sha256=replayed["source_receipt_sha256"], raw_sha256=replayed["raw_sha256"],
            event=event, persisted_source_receipt_sha256=digest(receipt)))
    event_rows = [row for row in observed_business_union
                  if row.get("source_kind") in {"BUSINESS_EVENT", "PERSISTED_BUSINESS_EVENT"}
                  or str(row.get("ref_id", "")).startswith("canonical:event:")
                  or row.get("ref_id") in expected["context_refs"]]
    if canonical_sha256(sorted(event_rows, key=lambda row: row.get("ref_id", ""))) != canonical_sha256(wanted):
        raise ValueError("context_discovery_observed_event_union_mismatch")
    expected.pop("view_sha256")
    expected.update(persisted_event_receipt_sha256=digest(receipt),
        original_run_id=receipt["original_run_id"], original_acquisition_id=receipt["original_acquisition_id"])
    for record in expected["context_records"]:
        record.update(authority_state="RESOLVED",
                      source_scope="source_verified_headline_context_only_requires_review")
    return _seal(expected)


def resolve_persisted_context_v1(view, *, event_inputs, observed_business_union,
                                 persisted_event_receipt, **frozen_inputs):
    _require_exact_view(view, build_context_discovery_v1(**frozen_inputs))
    return _resolved_from_inputs(event_inputs=event_inputs,
        observed_business_union=observed_business_union,
        persisted_event_receipt=persisted_event_receipt, **frozen_inputs)


def validate_context_discovery_v1(view, *, event_inputs, observed_business_union,
                                  persisted_event_receipt, use=SourceUse.CONTEXT.value,
                                  **frozen_inputs):
    """Recompute from trusted replay/frozen inputs, never accept a public self-hash."""
    _require_purpose(frozen_inputs.get("purpose", PURPOSE), use)
    expected = _resolved_from_inputs(event_inputs=event_inputs,
        observed_business_union=observed_business_union,
        persisted_event_receipt=persisted_event_receipt, **frozen_inputs)
    _require_exact_view(view, expected)
    return deepcopy(expected)
