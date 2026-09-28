"""Archive-only decision limitation and versioned strategy input contracts.

No production registration, persistence, acquisition or delivery entry point.
The ordinary evidence-based policy is delegated without changed thresholds.
"""
from __future__ import annotations

from copy import deepcopy
from datetime import datetime, timezone
import json
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

from app.services.canonical_evidence_time_service import validate_canonical_time
from app.services.direction_timing_ownership_service import OwnedEvidencePacket
from app.services.unified_snapshot_contract import digest
from scripts import m12ds_r4_r4_policy as policy
from scripts import m12ds_r4_r4_schemas as schemas
from scripts.m12cn_policy_contract import build_subject_catalog
from scripts.m12da_source_use_contract import (
    build_source_use_projection, canonical_sha256, canonical_source_metadata_sha256,
    freeze_source_use_binding, freeze_source_use_input_expectation,
    validate_source_use_current_input,
)
from scripts.r2b_r1_offline_closure import reproject_time
from scripts.financial_direction_eligibility import DENIAL, is_financial, narrow_financial_authority

CONTRACT = "r2b-whole-decision-limitation-v1"
STRATEGY = "versioned-strategy-metadata-v1"
RULE_REF = "canonical:chart:stored_price_rules"
RULE_DENIAL = "STORED_PRICE_RULE_TIME_OWNERSHIP_UNRESOLVED"
DIRECTION_BUCKETS = ("positive", "negative", "holder_support", "holder_risk", "holder_reduce")


def _require(condition, code):
    if not condition:
        raise ValueError(code)


def _utc(value):
    dt = datetime.fromisoformat(value)
    # InvestmentThesis.created_at is UTC; SQLite preserves a naive UTC value.
    return dt.replace(tzinfo=timezone.utc) if dt.tzinfo is None else dt.astimezone(timezone.utc)


def versioned_rule_binding(stock, local, *, cutoff):
    """Prove the exact Class-C row, not a timestamp copied from the projection."""
    ticker = stock["ticker"]
    raw = next(s for s in stock["packet"]["stocks"] if s["ticker"] == ticker)
    facts = [f for f in raw["fact_catalog"] if f["fact_id"] == "chart:stored_price_rules"]
    if not facts:
        return {"status": "NOT_PRESENT", "ticker": ticker, "ref_id": RULE_REF}
    audit = {"contract": STRATEGY, "ticker": ticker, "ref_id": RULE_REF,
             "local_document_sha256": digest(local), "canonical_fact_sha256": digest(facts[0])}
    try:
        _require(local.get("contract") == "unified-local-seed-projection-v1", "local_contract")
        _require(digest(local) == stock["input_hashes"]["local"], "local_source_hash")
        _require(local["market"] == stock["market"], "local_market")
        role = local["roles"]["stored_thesis_and_business_metadata"]
        _require(role["version"] == digest(role["records"]) and role["eligible"], "class_c_version")
        rows = [r for r in role["records"] if r["table"] == "investmentthesis"
                and r["record"].get("ticker") == ticker]
        _require(len(rows) == 1 and len(facts) == 1, "exact_thesis_identity")
        row, fact = rows[0], facts[0]
        record = row["record"]
        _require(str(record["id"]) == row["record_id"] and record["status"] == "active"
                 and record["version"] == raw["thesis_version"], "thesis_version")
        _require(row["original_record_sha256"] == digest(record), "thesis_record_hash")
        rules = json.loads(record["price_rules"])
        _require(rules and rules == raw["chart_context"]["stored_price_rules"]
                 and rules == fact["fields"], "exact_price_rule_values")
        _require(rules.get("currency") and rules.get("basis"), "price_rule_currency_basis")
        _require(fact["source"] == "investment_thesis" and fact["fact_type"] == "chart_price_rules",
                 "price_rule_semantic_owner")
        security = local["roles"]["security_identity"]
        _require(security["version"] == digest(security["records"]), "security_version")
        identities = [r for r in security["records"] if r["table"] == "securitymaster"
                      and r["record"].get("ticker") == ticker]
        _require(len(identities) == 1 and identities[0]["record"].get("canonical_security_id"),
                 "security_identity")
        _require(security["eligible"] and identities[0]["original_record_sha256"] == digest(identities[0]["record"]),
                 "security_record_hash")
        created = record.get("created_at")
        _require(isinstance(created, str) and "T" in created and _utc(created) <= _utc(cutoff),
                 "thesis_version_creation_time")
        audit.update(status="PASS", time_kind="VERSIONED_STRATEGY_METADATA",
            original_as_of=fact.get("as_of_date"), version_created_at=created,
            time_owner="InvestmentThesis.created_at (UTC storage contract)",
            current_market_as_of=False, effective_market_time_claimed=False,
            record_id=row["record_id"], thesis_version=record["version"],
            record_sha256=digest(record), role_version=role["version"],
            canonical_security_id=identities[0]["record"]["canonical_security_id"],
            security_record_sha256=digest(identities[0]["record"]), rules_sha256=digest(rules),
            currency=rules["currency"], basis=rules["basis"], denial_reason=None)
    except (KeyError, TypeError, ValueError, StopIteration) as exc:
        audit.update(status="DENIED", time_kind="SOURCE_DATE_UNAVAILABLE", denial_reason=RULE_DENIAL,
                     detail=str(exc))
    audit["binding_sha256"] = digest(audit)
    return audit


def _filter_denied_rule_view(stock):
    """Remove owner paths, including copied prose; never remove coincident numbers."""
    view = deepcopy(stock)
    ep = view["evidence_packet"]
    # A denied rule may have been copied into a thesis/expectations summary.
    # These entire source fields are withheld, not edited into new evidence.
    denied = {r["ref_id"] for r in ep["evidence"]
              if r["ref_id"] == RULE_REF or r.get("category") in {"thesis", "expectations"}}
    ep["evidence"] = [r for r in ep["evidence"] if r["ref_id"] not in denied]
    view["ownership"]["evidence"] = [r for r in view["ownership"]["evidence"]
                                     if r["ref"]["ref_id"] not in denied]
    view["ownership"]["source_packet"] = deepcopy(ep)
    return view, denied


def source_view(stock, authority, local, *, cutoff):
    view, times, changes = reproject_time(stock)
    strategy = versioned_rule_binding(stock, local, cutoff=cutoff)
    denied = set()
    if strategy["status"] == "DENIED":
        view, denied = _filter_denied_rule_view(view)
    original = {r["ref_id"]: r for r in authority["authority"]["authority_records"]}
    kept = []
    for row in view["evidence_packet"]["evidence"]:
        owner = original.get(row["ref_id"])
        if owner is None or not set(owner["allowed_uses"]) - set(owner["prohibited_uses"]):
            denied.add(row["ref_id"])
            continue
        kept.append(row)
    view["evidence_packet"]["evidence"] = kept
    view["ownership"]["evidence"] = [r for r in view["ownership"]["evidence"]
                                     if r["ref"]["ref_id"] not in denied]
    view["ownership"]["source_packet"] = deepcopy(view["evidence_packet"])
    facts = {"canonical:" + f["fact_id"]: f for f in stock["packet"]["stocks"][0]["fact_catalog"]}
    errors = []
    for row in kept:
        ref = row["ref_id"]
        if ref == RULE_REF:
            _require(strategy["status"] == "PASS", RULE_DENIAL)
        elif ref.startswith("canonical:"):
            try:
                validate_canonical_time(facts[ref], row, ticker=stock["ticker"])
            except ValueError as exc:
                errors.append({"ref_id": ref, "error": str(exc)})
    _require(not errors, "unclassified_model_visible_time:" + json.dumps(errors))
    receipt = {"contract": CONTRACT, "ticker": stock["ticker"],
        "raw_source_sha256": digest(stock), "raw_authority_sha256": digest(authority),
        "derived_evidence_sha256": digest(view["evidence_packet"]),
        "denied_refs": sorted(denied), "strategy": strategy, "time_errors": errors,
        "canonical_time_changes": len(changes), "authority_widened": False}
    receipt["receipt_sha256"] = digest(receipt)
    return view, receipt


def bound_chain(view, authority, *, atomic, generation, source_generation, view_receipt):
    """Hash-linked derivative authority: only narrow original permissions."""
    owned = OwnedEvidencePacket.model_validate(view["ownership"])
    ownership = {"ticker": view["ticker"], "core_ref_ids": sorted(owned.core_refs),
                 "timing_ref_ids": sorted(owned.timing_refs)}
    context = {"evidence_packets": [view["evidence_packet"]], "evidence_ownership": [ownership]}
    cat = build_subject_catalog(context=context, ticker=view["ticker"], atomic_claims=atomic)
    metadata = [r for r in view["evidence_packet"]["evidence"] if r["ref_id"] in cat["all_evidence_refs"]]
    original = authority["authority"]
    _require(original["status"] == "PASS" and not original["authority_errors"], "authority_not_pass")
    original_content = {k: v for k, v in original.items() if k != "authority_manifest_sha256"}
    _require(digest(original_content) == original["authority_manifest_sha256"], "authority_hash")
    derivative = deepcopy(original)
    indexed = {r["ref_id"]: r for r in metadata}
    derivative["authority_records"] = [deepcopy(r) for r in original["authority_records"]
                                        if r["ref_id"] in indexed]
    _require({r["ref_id"] for r in derivative["authority_records"]} == set(indexed), "authority_set")
    financial_metadata = [indexed[r["ref_id"]] for r in derivative["authority_records"]
                          if is_financial(r, indexed[r["ref_id"]])]
    financial_fields = (policy.frozen_fact_fields(view["packet"], view["ticker"], financial_metadata)
                        if financial_metadata else {})
    for record in derivative["authority_records"]:
        ref = record["ref_id"]
        record.update(narrow_financial_authority(record, indexed[ref], financial_fields.get(ref)))
        record["source_metadata_sha256"] = digest(indexed[ref])
        if ref == RULE_REF:
            record["source_period"] = view_receipt["strategy"]["version_created_at"]
        else:
            record["source_period"] = indexed[ref].get("as_of")
    derivative.update(catalog_sha256=canonical_sha256(cat), source_metadata_sha256=canonical_source_metadata_sha256(metadata),
        parent_authority_sha256=digest(original), source_view_receipt_sha256=view_receipt["receipt_sha256"])
    derivative.pop("authority_manifest_sha256")
    derivative["authority_manifest_sha256"] = digest(derivative)
    expectation = freeze_source_use_input_expectation(ticker=view["ticker"], source_generation_id=source_generation,
        execution_generation_id=generation, catalog=cat, source_metadata=metadata, authority_manifest=derivative)
    projection = build_source_use_projection(ticker=view["ticker"], input_generation_id=source_generation,
        execution_generation_id=generation, catalog=cat, authority_manifest=derivative,
        current_input_expectation=expectation)
    binding = freeze_source_use_binding(projection=projection, authority_manifest=derivative,
                                       current_input_expectation=expectation)
    valid = validate_source_use_current_input(projection, binding, expectation, ticker=view["ticker"],
        source_generation_id=source_generation, execution_generation_id=generation, catalog=cat, source_metadata=metadata)
    _require(valid["status"] == "PASS", "current_input_binding")
    chain = dict(authority=derivative, expectation=expectation, projection=projection, binding=binding,
                 validation=valid, source_generation_id=source_generation, execution_generation_id=generation)
    return cat, metadata, chain


def decision_mode(stock, authority, observations):
    _require(stock["status"] == "PASS" and not stock["mandatory_missing"], "source_assembly_incomplete")
    mandatory = [r for r in stock["component_binding"] if r["requirement"] == "MANDATORY"]
    _require(mandatory and all(r["eligible"] and r["selected_value_in_packet"] for r in mandatory),
             "mandatory_price_technical_incomplete")
    _require(authority["status"] == "PASS" and not authority["authority_errors"], "source_authority_incomplete")
    records = authority["authority_records"]
    directional = [r["ref_id"] for r in records if "OVERALL_DIRECTION" in r["allowed_uses"]
                   and "OVERALL_DIRECTION" not in r["prohibited_uses"] and r["authority_state"] == "RESOLVED"]
    if directional:
        _require(observations, "authorized_direction_has_no_observation")
        return "EVIDENCE_BASED"
    _require(not any("HOLDER_STANCE" in r["allowed_uses"] and "HOLDER_STANCE" not in r["prohibited_uses"]
                     for r in records), "unknown_limit_has_holder_entitlement")
    _require(not observations and records and all(r["denial_reasons"] for r in records),
             "unknown_limit_requires_explicit_denials")
    return "UNKNOWN_LIMIT"


def limitation_catalog(stock, authority):
    denials = stock["financial_state"].get("denials") or []
    values = denials if isinstance(denials, list) else [{"field": k, "reason": v} for k, v in denials.items()]
    result = {}
    for denial in values:
        key = "source-recovery:" + digest({"ticker": stock["ticker"], "denial": denial})
        result[key] = {"kind": "QUALIFIED_FINANCIAL_LINEAGE", "source_denial": denial,
                       "authority_sha256": digest(authority)}
    for row in authority["authority_records"]:
        if DENIAL in row["denial_reasons"]:
            key = "source-recovery:" + digest({"ticker": stock["ticker"], "ref": row["ref_id"], "reason": DENIAL})
            result[key] = {"kind": "COMPARABLE_FINANCIAL_OBSERVATION", "source_ref": row["ref_id"],
                           "source_denial": row["denial_reasons"], "authority_sha256": digest(authority)}
        if row["ref_id"].startswith("canonical:event:") and "OVERALL_DIRECTION" not in row["allowed_uses"]:
            key = "source-recovery:" + digest({"ticker": stock["ticker"], "ref": row["ref_id"]})
            result[key] = {"kind": "VERIFIED_BUSINESS_EVENT", "source_ref": row["ref_id"],
                           "source_denial": row["denial_reasons"], "authority_sha256": digest(authority)}
    _require(result, "unknown_limit_source_recovery_missing")
    return result


class UnknownDecision(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    decision_mode: Literal["UNKNOWN_LIMIT"]
    overall_direction: Literal["OBSERVE"]
    new_buyer: Literal["OBSERVE"]
    holder: Literal["OBSERVE"]
    directional_buy_score: None
    directional_sell_score: None
    confidence: None
    limitation_reason: Literal["ZERO_AUTHORIZED_DIRECTIONAL_EVIDENCE"]
    unknowns: list[str] = Field(min_length=1)
    required_next_evidence: list[str] = Field(min_length=1)


def unknown_schema(recovery):
    schema = UnknownDecision.model_json_schema()
    for key in ("unknowns", "required_next_evidence"):
        schema["properties"][key].update(items={"type": "string", "enum": sorted(recovery)},
                                         maxItems=len(recovery), uniqueItems=True)
    return schema


def validate_unknown(raw, *, mode, recovery, capability):
    _require(mode == "UNKNOWN_LIMIT", "unknown_limit_not_applicable")
    _require(all(not capability[k] for k in DIRECTION_BUCKETS), "unknown_limit_directional_capability")
    result = UnknownDecision.model_validate(raw)
    for values in (result.unknowns, result.required_next_evidence):
        _require(len(set(values)) == len(values) and set(values) <= set(recovery), "unknown_recovery_ref")
    _require(set(result.unknowns) == set(result.required_next_evidence), "recovery_gap_mismatch")
    return {"status": "PASS", "decision_mode": mode, "decision_sha256": digest(raw),
            "capability_sha256": digest(capability), "recovery_sha256": digest(recovery)}


def decision_schema(mode, cap, valuation, entry_catalog, recovery):
    if mode == "UNKNOWN_LIMIT":
        _require(all(not cap[k] for k in DIRECTION_BUCKETS), "unknown_limit_directional_capability")
        return unknown_schema(recovery)
    _require(mode == "EVIDENCE_BASED", "unknown_decision_mode")
    return schemas.decision_schema(cap, valuation, entry_catalog)


def validate_decision(raw, *, mode, cap, valuation, recovery):
    if mode == "UNKNOWN_LIMIT":
        receipt = validate_unknown(raw, mode=mode, recovery=recovery, capability=cap)
        return raw, receipt
    _require(mode == "EVIDENCE_BASED", "unknown_decision_mode")
    row = schemas.normalize_decision(raw)
    return row, policy.validate_decision(row, cap, valuation)


def render_unknown(ticker, raw, *, recovery, capability):
    validate_unknown(raw, mode="UNKNOWN_LIMIT", recovery=recovery, capability=capability)
    kinds = {recovery[key]["kind"] for key in raw["required_next_evidence"]}
    next_evidence = []
    if "QUALIFIED_FINANCIAL_LINEAGE" in kinds:
        next_evidence.append("동일 기간·기업 기준으로 검증된 정식 재무 공시의 수치와 출처 연결")
    if "COMPARABLE_FINANCIAL_OBSERVATION" in kinds:
        next_evidence.append("현재 재무 수치는 맥락으로만 사용하며, 방향 판단에는 기간·기업·통화·연결 기준이 맞는 과거 비교 수치가 필요")
    if "VERIFIED_BUSINESS_EVENT" in kinds:
        next_evidence.append("검토 대기 중인 사업 소식을 확인할 공식 원문과 관측된 사업 성과")
    return (f"{ticker} · 판단 근거 제한\n전체·신규 매수자·보유자: 판단 유보\n"
            "방향을 판단할 권한이 검증된 사업 증거가 없어 매수·매도 비율과 방향 확신도를 산출하지 않습니다. "
            "균형 잡힌 투자 의견이나 보유 권고를 뜻하지 않습니다.\n"
            "다음 확인 자료: " + "; ".join(next_evidence)
            + "\n가격·기술 정보는 진입 맥락일 뿐 사업 방향이나 투자 행동의 근거를 대신하지 않습니다.")


LIMIT_PROMPT = """UNKNOWN_LIMIT is a whole-decision evidence limitation, not neutral HOLD.
Overall, New Buyer and Holder must all remain OBSERVE. Ratios and directional
confidence are null. Select only source recovery IDs for unknowns and required
next evidence. Do not create buy, sell, hold, add or reduce claims, fair values,
target prices or price-triggered upgrades/downgrades. CONTEXT is not OVERALL_DIRECTION.
Versioned strategy metadata is stored user configuration, not current market evidence.
The backend renders these typed limits; no free-form directional rationale is allowed.
"""
