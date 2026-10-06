"""Source-only seven-axis review. No acquisition, model dispatch or production use.

The source authority and B2 metric owners remain authoritative. This adapter
does not import an accepted decision, a Core claim, or an economic target.
"""
from copy import deepcopy
import json

from app.services.unified_snapshot_contract import digest
from scripts.fresh_source_only_export import reject_review_contamination
from scripts.r2b_r2_contract import policy as business
from scripts import newbuyer_b2_v2_policy as metrics
from scripts.newbuyer_b2_shadow import qualified_facts, tactical_catalog
from scripts.newbuyer_b2_contract import obj, validate_json_schema, timing
from scripts.m12cs_r1_provider_schema import (
    project_provider_wire_schema, scan_provider_structured_output_schema,
)
from scripts.m12da_source_use_contract import (
    canonical_sha256, canonical_source_metadata_sha256,
)

CONTRACT = "strict-blind-seven-axis-v1"
AXES = {
    "overall_direction": ["BUY", "HOLD", "SELL"],
    "new_buyer": ["ATTRACTIVE", "WAIT", "AVOID"],
    "entry_timing": ["FAVORABLE_NOW", "WAIT_FOR_ZONE", "UNRESOLVED"],
    "holder": ["HOLDABLE", "REVIEW", "REDUCE"],
    "active_material_risk": [False, True],
    "valuation_evaluability": ["EVALUABLE", "ALL_RELEVANT_METRICS_UNUSABLE"],
    "valuation_state": ["SUPPORTIVE", "NEUTRAL", "BURDENSOME", "UNRESOLVED"],
}
FORBIDDEN = frozenset({
    "atomic_claims", "frozen_business_claims", "frozen_overall", "business_gate",
    "active_risk_state", "timing_state", "valuation_evaluability", "valuation_state",
    "overall_direction", "new_buyer", "holder", "target_label", "expected_label",
    "blind_judgments", "blind_comparison", "v1_v2_delta", "accepted_b",
    "frozen_pass_a_classification", "r2_policy_capability", "legacy_confidence",
})
RUBRIC = {
    "contract": CONTRACT, "authority": "REVISED_REV59_SEVEN_AXIS_RUBRIC",
    "axes": AXES, "timing_may_override_fundamental": False,
    "active_material_risk_requires_avoid": True,
    "usable_metric_requires_resolved_valuation_judgment": True,
    "positive_eligible_business_supportive_no_risk_requires_attractive": True,
    "economic_agreement_threshold": None, "ticker_exceptions": [],
}
PROMPT = """Independently assess the seven axes from this source-only package.
Do not use tools, external knowledge, earlier judgments, ticker targets or desired distributions.
Overall BUY/HOLD/SELL concerns observed business direction, not price or valuation.
NewBuyer ATTRACTIVE/WAIT/AVOID concerns fundamental/valuation attractiveness, separate from timing.
Entry timing is FAVORABLE_NOW, WAIT_FOR_ZONE or UNRESOLVED, never a fundamental fair-value claim.
Holder is HOLDABLE, REVIEW or REDUCE. Holding-relevant observed material risk supports REVIEW;
REDUCE needs verified persistent deterioration or realized impairment, not one weak period.
Active material risk is a separate boolean judgment grounded in observed adverse business evidence.
An active material risk requires NewBuyer AVOID. Do not convert missing data or a future condition into a realized risk.
When a relevant metric is usable, valuation is EVALUABLE and SUPPORTIVE/NEUTRAL/BURDENSOME.
Only complete typed denials of all relevant metrics support ALL_RELEVANT_METRICS_UNUSABLE and UNRESOLVED.
One denied metric must not invalidate another usable metric. PBR needs owned asset relevance.
Positive eligible business direction plus SUPPORTIVE valuation and no active risk requires ATTRACTIVE,
even when entry timing is WAIT_FOR_ZONE or UNRESOLVED. Confidence is diagnostic, not a hidden veto.
Use exact axis-eligible evidence refs. Respect per-metric identity, horizon, currency, period and denials.
No unavailable reconstruction, universal P/E cutoff, implied EPS, fair value, target or new numeric fact.
The input owns exact numbers; rationales must be short, qualitative and contain no numeric literals.
Do not infer recurring profit, persistent impairment, cash runway, ROIC or FCF yield without an owner.
Return only the specified JSON, with a short rationale and confidence for every axis.
"""


def require(ok, code):
    if not ok:
        raise ValueError(code)


def reject_contamination(value):
    reject_review_contamination(value)
    if isinstance(value, dict):
        for key, child in value.items():
            require(key.lower() not in FORBIDDEN, "BLIND_DOWNSTREAM_LABEL:" + key)
            reject_contamination(child)
    elif isinstance(value, (list, tuple)):
        for child in value:
            reject_contamination(child)
    elif isinstance(value, str) and value.lstrip().startswith(("{", "[")):
        try:
            parsed = json.loads(value)
        except ValueError:
            return
        reject_contamination(parsed)


def _refs(records, predicate):
    return sorted(ref for ref, row in records.items() if predicate(row))


def project_subject(inputs, *, generation):
    """Consume current source metadata and sealed category coverage, not B outputs."""
    require(set(inputs) == {"ticker", "market", "security_id", "source_generation_id",
        "source_sha256", "metadata", "authority", "frozen_fact_fields", "valuation_context",
        "coverage", "census", "current_price", "tactical_candidates"}, "BLIND_SOURCE_INPUT_SHAPE")
    reject_contamination(inputs)
    ticker, authority, metadata = (inputs[k] for k in ("ticker", "authority", "metadata"))
    require(inputs["market"] in ("US", "KR") and generation and ticker
        and inputs["security_id"] and len(inputs["source_sha256"]) == 64, "BLIND_SOURCE_IDENTITY")
    require(authority["authority_manifest_sha256"] == canonical_sha256({k: v for k, v
        in authority.items() if k != "authority_manifest_sha256"})
        and authority["source_generation_id"] == inputs["source_generation_id"]
        and authority["ticker"] == ticker
        and authority["source_metadata_sha256"] == canonical_source_metadata_sha256(metadata)
        and authority["status"] == "PASS", "BLIND_SOURCE_AUTHORITY_BINDING")
    rows = {r["ref_id"]: r for r in metadata}
    owners = {r["ref_id"]: r for r in authority["authority_records"]}
    require(len(rows) == len(metadata) and len(owners) == len(authority["authority_records"])
        and set(rows) == set(owners), "BLIND_SOURCE_REF_UNIVERSE")
    evidence = {}
    for ref, row in rows.items():
        owner = owners[ref]
        # r2b_r2_contract.bound_chain owns row hashes with unified UTF-8 digest;
        # its aggregate/manifest fields retain the source-authority serializer.
        require(owner["source_metadata_sha256"] == digest(row),
            "BLIND_SOURCE_ROW_BINDING")
        if owner["authority_state"] != "RESOLVED":
            continue
        evidence[ref] = dict(kind="SOURCE", value=deepcopy(row),
            allowed_uses=deepcopy(owner["allowed_uses"]),
            source_authority_sha256=digest(owner), source_sha256=digest(row))
    coverage, census = inputs["coverage"], inputs["census"]
    coverage_rows = metrics.coverage_gate(coverage, census, coverage["receipt_sha256"], census["receipt_sha256"])
    subject = dict(ticker=ticker, security_id=inputs["security_id"],
        source_generation_id=inputs["source_generation_id"], facts=qualified_facts(
            {"valuation_context": inputs["valuation_context"]}, ticker, inputs["source_generation_id"]))
    evaluability, resolution, all_denied = metrics.evaluability(subject, coverage_rows[ticker],
        census, coverage["receipt_sha256"])
    require(evaluability["evaluability_state"] != "INVALID_INCOMPLETE_CONTRACT",
        "BLIND_CONTRADICTORY_METRIC_OWNERSHIP")
    for row in resolution:
        ref = row["metric_ref"]
        require(ref not in evidence, "BLIND_REF_ROLE_COLLISION")
        fact = subject["facts"].get(ref) if row["state"] == "USABLE" else None
        evidence[ref] = dict(kind="VALUATION_METRIC", state=row["state"], metric=row["metric"],
            value=deepcopy(fact), typed_denials=[deepcopy(b) for b in census["rows"]
                if b["blocker_ref"] in row["exact_blocker_refs"]],
            relevant=row["relevant"], source_sha256=digest(row),
            allowed_uses=["VALUATION"] if fact else [])
    # Deterministic observations check evidence capability privately. Their polarity
    # and downstream classifications are deliberately absent from the model input.
    observations = business.observations(metadata, authority, inputs["frozen_fact_fields"])
    ranges = tactical_catalog(dict(current_price=inputs["current_price"], decision_evidence=metadata,
        source_use_projection=dict(source_permissions=list(owners.values())),
        r2_eligible_range_catalog=dict(tactical_candidates=inputs["tactical_candidates"])),
        ticker, inputs["security_id"])
    timing_options = []
    for candidate in ranges:
        relation = timing(dict(ticker=ticker, security_id=inputs["security_id"],
            tactical_catalog=ranges, current_price=inputs["current_price"],
            selected_tactical_candidate=candidate["candidate_id"]))
        if relation["state"] != "UNRESOLVED":
            timing_options.append(dict(state=relation["state"], evidence_refs=candidate["evidence_refs"]))
    directional = sorted({r["source_ref"] for r in observations.values()})
    context = _refs(evidence, lambda r: r["kind"] == "SOURCE" and "CONTEXT" in r["allowed_uses"])
    timing_refs = _refs(evidence, lambda r: r["kind"] == "SOURCE" and bool(
        {"ENTRY", "PRICE_ENTRY_CONTEXT"} & set(r["allowed_uses"])))
    usable = evaluability["usable_valuation_metric_refs"]
    relevant = evaluability["relevant_valuation_metric_refs"]
    require(context and relevant, "BLIND_EMPTY_SOURCE_OR_METRICS")
    axes = dict(overall_direction=sorted(set(directional + context)),
        new_buyer=sorted(set(directional + relevant + context)), entry_timing=timing_refs or context,
        holder=directional, active_material_risk=directional or context,
        valuation_evaluability=relevant, valuation_state=usable or relevant)
    require(all(axes.values()), "BLIND_AXIS_EVIDENCE_GAP")
    result = dict(contract=CONTRACT, generation=generation, source_generation_id=inputs["source_generation_id"],
        ticker=ticker, market=inputs["market"], security_id=inputs["security_id"],
        source_sha256=inputs["source_sha256"], source_input_sha256=digest(inputs),
        evidence=evidence, axis_eligible_refs=axes,
        fact_fields=deepcopy(inputs["frozen_fact_fields"]),
        current_price=deepcopy(inputs["current_price"]),
        tactical_candidates=deepcopy(ranges),
        ownership=dict(source_authority_sha256=authority["authority_manifest_sha256"],
            coverage_sha256=coverage["receipt_sha256"], census_sha256=census["receipt_sha256"]),
        rubric_sha256=digest(RUBRIC))
    # 'axis_eligible_refs' is a static permission table, not a judgment or model label.
    return result, dict(observations=observations, evaluability=evaluability,
        all_denied=all_denied, resolution=resolution, timing_options=timing_options,
        source_input_sha256=digest(inputs))


def package(source):
    require(source.get("generation") and source.get("blind_inputs"), "BLIND_EMPTY_SUBJECTS")
    rows = {}
    for ticker, inputs in source["blind_inputs"].items():
        require(inputs["ticker"] == ticker, "BLIND_TICKER_BINDING")
        rows[ticker] = project_subject(inputs, generation=source["generation"])[0]
    return dict(contract=CONTRACT, generation=source["generation"],
        source_sha256=digest(source), subjects=rows, rubric_sha256=digest(RUBRIC))


def validate_package(value, source):
    return value == package(source)


def response_schema(subject):
    axes = {}
    for name, values in AXES.items():
        axes[name] = obj(dict(judgment={"type": "boolean" if name == "active_material_risk" else "string",
                                      "enum": values},
            evidence_refs={"type": "array", "items": {"type": "string", "enum": subject["axis_eligible_refs"][name]},
                "minItems": 1, "maxItems": len(subject["axis_eligible_refs"][name]), "uniqueItems": True},
            rationale={"type": "string", "minLength": 1, "maxLength": 500},
            confidence={"type": "string", "enum": ["LOW", "MEDIUM", "HIGH"]}))
    return obj(dict(contract={"const": CONTRACT},
        **{k: {"const": subject[k]} for k in ("generation", "source_generation_id", "ticker", "security_id")},
        subject_sha256={"const": digest(subject)}, axes=obj(axes)))


def payload(subject):
    internal = response_schema(subject)
    wire, receipt = project_provider_wire_schema(internal)
    require(scan_provider_structured_output_schema(wire)["status"] == "PASS", "BLIND_PROVIDER_SCHEMA_GAP")
    return dict(prompt=PROMPT, input=deepcopy(subject), response_schema=wire), receipt


def validate_output(output, subject, audit):
    errors = validate_json_schema(output, response_schema(subject))
    if errors:
        return dict(status="FAIL", category="SOURCE_BINDING", errors=errors, retryable=False)
    axes = output["axes"]
    judgments = {k: v["judgment"] for k, v in axes.items()}
    def need(ok, code):
        if not ok:
            errors.append(code)
    for axis, row in axes.items():
        need(len(set(row["evidence_refs"])) == len(row["evidence_refs"]), "DUPLICATE_AXIS_REF:" + axis)
        need(not any(c.isnumeric() for c in row["rationale"]), "UNBOUND_NUMERIC_CLAIM:" + axis)
    expected = audit["evaluability"]["evaluability_state"]
    need(judgments["valuation_evaluability"] == expected, "CROSS_METRIC_EVALUABILITY")
    need((judgments["valuation_state"] == "UNRESOLVED") == (expected == "ALL_RELEVANT_METRICS_UNUSABLE"),
        "VALUATION_STATE_AVAILABILITY")
    usable = set(audit["evaluability"]["usable_valuation_metric_refs"])
    if usable:
        need(set(axes["valuation_state"]["evidence_refs"]) <= usable, "BLOCKED_METRIC_USE")
        need(bool(set(axes["valuation_evaluability"]["evidence_refs"]) & usable), "USABLE_METRIC_OMITTED")
    else:
        required = set(audit["evaluability"]["relevant_valuation_metric_refs"])
        need(set(axes["valuation_evaluability"]["evidence_refs"]) == required, "ALL_UNUSABLE_PROOF_INCOMPLETE")
    observations = list(audit["observations"].values())
    pos = {r["source_ref"] for r in observations if r["effect"] == business.Effect.POSITIVE}
    neg = {r["source_ref"] for r in observations if r["effect"] in business.ADVERSE}
    persistent = {r["source_ref"] for r in observations if r["effect"] in business.ADVERSE
        and (r["persistence_verified"] or r["impairment_realized"])}
    sell = {r["source_ref"] for r in observations if r["effect"] in
        (business.Effect.DETERIORATION, business.Effect.IMPAIRMENT)} | persistent
    direction_refs = set(axes["overall_direction"]["evidence_refs"])
    if judgments["overall_direction"] != "HOLD":
        need(bool(direction_refs & (pos if judgments["overall_direction"] == "BUY" else sell)),
            "BUSINESS_DIRECTION_CAPABILITY")
    risk = judgments["active_material_risk"]
    if risk:
        need(bool(set(axes["active_material_risk"]["evidence_refs"]) & neg), "ACTIVE_RISK_WITHOUT_ADVERSE_FACT")
        need(judgments["new_buyer"] == "AVOID", "ACTIVE_RISK_REQUIRES_AVOID")
        need(judgments["holder"] != "HOLDABLE", "ACTIVE_RISK_HOLDER_SUPPRESSION")
    if judgments["holder"] in ("REVIEW", "REDUCE"):
        need(risk, "HOLDER_MATERIAL_RISK_AXIS_MISMATCH")
        need(bool(set(axes["holder"]["evidence_refs"]) & (persistent if judgments["holder"] == "REDUCE" else neg)),
            "HOLDER_EVIDENCE_SCOPE")
    if judgments["overall_direction"] == "BUY" and judgments["valuation_state"] == "SUPPORTIVE" and not risk:
        need(judgments["new_buyer"] == "ATTRACTIVE", "TIMING_OR_CONFIDENCE_OVERWROTE_FUNDAMENTAL")
    if judgments["new_buyer"] == "ATTRACTIVE":
        need(judgments["overall_direction"] == "BUY" and judgments["valuation_state"] == "SUPPORTIVE"
            and not risk, "ATTRACTIVE_WITHOUT_SUPPORT")
        need(bool(set(axes["new_buyer"]["evidence_refs"]) & usable), "ATTRACTIVE_WITHOUT_USABLE_METRIC")
    if judgments["entry_timing"] != "UNRESOLVED":
        need(all(bool({"ENTRY", "PRICE_ENTRY_CONTEXT"} & set(subject["evidence"][r]["allowed_uses"]))
            for r in axes["entry_timing"]["evidence_refs"]), "TIMING_WITHOUT_PRICE_EVIDENCE")
        selected = set(axes["entry_timing"]["evidence_refs"])
        need(any(r["state"] == judgments["entry_timing"] and set(r["evidence_refs"]) <= selected
            for r in audit["timing_options"]), "TIMING_WITHOUT_OWNED_RANGE_RELATION")
    return dict(status="FAIL" if errors else "PASS", category="CONTRACT_SEMANTICS", errors=errors,
        retryable=False, economic_correctness_proven=False,
        free_prose_semantics="QUALITATIVE_REVIEW_REQUIRED; no numeric literals or unowned output fields")
