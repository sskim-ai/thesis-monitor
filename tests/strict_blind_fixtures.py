"""Invented source/response fixtures. Never imported by a live adapter."""
from copy import deepcopy

from app.services.provider_valuation_calibration_context import calibration_context
from app.services.unified_snapshot_contract import digest
from scripts import strict_blind_contract as blind
from scripts.kis_eps_wire_calibration import sealed
from scripts.newbuyer_fper_prerequisite_scope import CATEGORIES, blocker_census
from scripts.newbuyer_b2_shadow import qualified_facts
from scripts.m12da_source_use_contract import canonical_sha256, canonical_source_metadata_sha256
from tests.test_m12ds_r2_judgment_policy import data
from tests.test_r9_rev29_valuation_integration import build_valuation


def source_inputs(tmp_path, *, risk=False, denied=(), technical=True, timing="WAIT_FOR_ZONE"):
    value, unavailable = build_valuation(tmp_path, forward_value=None if "FORWARD_PE" in denied else 7)
    if "PER" in denied:
        value["metrics"][0] = deepcopy(unavailable["metrics"][0])
    return from_context(calibration_context(value), risk=risk, technical=technical, timing=timing)


def from_context(vc, *, risk=False, technical=True, timing="WAIT_FOR_ZONE"):
    ticker = vc["ticker"]
    metadata, _, _ = data(-20 if risk else 20, ticker=ticker)
    import json
    current = 100 if timing == "FAVORABLE_NOW" else 120
    price = dict(ref_id="source:price", category="price", as_of="2026-06-30",
        statement=json.dumps(dict(current_price=current, currency="USD", price_basis="regular_close", price_as_of="2026-06-30")))
    metadata.append(price)
    metadata.append(dict(ref_id="source:technical", category="technical", as_of="2026-06-30",
        statement='{"availability":"AVAILABLE","zone_low":90,"zone_high":110}' if technical else
                  '{"availability":"UNAVAILABLE","reason":"insufficient_bars"}'))
    if technical:
        metadata.extend([
            dict(ref_id="source:zone", category="technical", label="chart_support_zone", as_of="2026-06-30",
                statement=json.dumps(dict(timeframe="daily", zone_low=90, zone_high=110, currency="USD"))),
            dict(ref_id="canonical:chart:daily", category="technical", as_of="2026-06-30",
                statement=json.dumps(dict(currency="USD", price_basis="unadjusted", quality="available", candle=dict(close=current)))),
        ])
    owners = [dict(ref_id=r["ref_id"], authority_state="RESOLVED",
        allowed_uses=["CONTEXT", "OVERALL_DIRECTION"] if r["category"] == "earnings" else
            ["CONTEXT", "PRICE_ENTRY_CONTEXT", "ENTRY"],
        source_metadata_sha256=digest(r)) for r in metadata]
    authority = dict(ticker=ticker, source_generation_id=vc["run_id"], status="PASS",
        authority_records=owners, source_metadata_sha256=canonical_source_metadata_sha256(metadata))
    authority["authority_manifest_sha256"] = canonical_sha256(authority)
    facts = qualified_facts({"valuation_context": vc}, ticker, vc["run_id"])
    relevant, qualified, cells = [], [], []
    for r in vc["metric_states"]:
        if r["metric"] not in ("PER", "FORWARD_PE", "fPER", "CURRENT_FY1_FPER"):
            continue
        ref = r["fact_ref"] or "unavailable:" + r["metric"]
        relevant.append(ref)
        usable = ref in facts
        if usable:
            qualified.append(ref)
        for category in CATEGORIES:
            bad = not usable and category == "VALUATION_SOURCE_QUALITY"
            cells.append(dict(category=category, metric=r["metric"], metric_ref=ref, required=True,
                coverage_disposition="PROVEN_APPLICABLE", coverage_proof_kind="COMPOSED_TYPED_OWNER",
                owner_state="DENIED" if bad else "QUALIFIED", owner_contract="fictional-current-owner",
                owner_ref="owner:" + ref, owner_decision_version="fictional-v1", owner_field_eligibility={"owned": True},
                owner_as_of="2026-06-30T00:00:00+00:00", owner_temporal_scope="OBSERVED_AT_RETRIEVAL",
                applies_to_metric_refs=[ref], not_applicable_to_metric_refs=[], not_applicable_reason_codes=[],
                denial_reason_codes=["EXPLICIT_TYPED_DENIAL"] if bad else [], input_refs=["input:" + ref],
                input_sha256=digest(ref), scope_level="METRIC_SCOPED", missing_fields=[]))
    row = sealed(dict(contract="fictional-category-coverage", ticker=ticker,
        canonical_security_id=vc["security_id"], source_generation=vc["run_id"],
        relevant_valuation_metric_refs=relevant, qualified_relevant_valuation_refs=sorted(qualified), categories=cells,
        coverage_complete=True, owner_provenance_complete=True, temporal_provenance_complete=True,
        decision_provenance_complete=True))
    coverage = sealed(dict(contract="REV56COfflineCoverageReproofV1", rows=[row], subjects=1,
        complete_subjects=1, unresolved_required_cells=0, coverage_complete=True,
        owner_provenance_complete=True, temporal_provenance_complete=True, decision_provenance_complete=True))
    return dict(ticker=ticker, market="KR" if vc["ticker"].isdigit() else "US", security_id=vc["security_id"],
        source_generation_id=vc["run_id"], source_sha256=digest(metadata), metadata=metadata,
        authority=authority, frozen_fact_fields={}, valuation_context=deepcopy(vc), coverage=coverage,
        current_price=dict(value=current, currency="USD", basis="regular_close", as_of="2026-06-30", ref_id="source:price"),
        tactical_candidates=[dict(candidate_id="zone", ticker=ticker, security_id=vc["security_id"],
            low=90, high=110, currency="USD", evidence_refs=["source:zone"])] if technical else [],
        census=blocker_census([row], expected_subjects=[ticker]))


def response(subject, audit, *, risk=False, timing="WAIT_FOR_ZONE", valuation="SUPPORTIVE"):
    denied = audit["evaluability"]["evaluability_state"] == "ALL_RELEVANT_METRICS_UNUSABLE"
    values = dict(overall_direction="SELL" if risk else "BUY", new_buyer="AVOID" if risk else
        "WAIT" if denied or valuation != "SUPPORTIVE" else "ATTRACTIVE", entry_timing=timing,
        holder="REVIEW" if risk else "HOLDABLE", active_material_risk=risk,
        valuation_evaluability=audit["evaluability"]["evaluability_state"],
        valuation_state="UNRESOLVED" if denied else valuation)
    refs = {k: v[:1] for k, v in subject["axis_eligible_refs"].items()}
    for axis in ("overall_direction", "holder", "active_material_risk"):
        refs[axis] = ["source:business"]
    usable = audit["evaluability"]["usable_valuation_metric_refs"]
    refs["valuation_evaluability"] = usable[:1] if usable else audit["evaluability"]["relevant_valuation_metric_refs"]
    refs["valuation_state"] = usable[:1] if usable else refs["valuation_evaluability"]
    refs["new_buyer"] = ["source:business"] + usable[:1]
    refs["entry_timing"] = ["source:zone"] if timing != "UNRESOLVED" else ["source:price"]
    return dict(contract=blind.CONTRACT, **{k: subject[k] for k in
        ("generation", "source_generation_id", "ticker", "security_id")}, subject_sha256=digest(subject),
        axes={k: dict(judgment=v, evidence_refs=refs[k], rationale="Observed source evidence; uncertainty remains.",
            confidence="MEDIUM") for k, v in values.items()})
