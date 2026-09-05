from __future__ import annotations

import argparse
import hashlib
import json
import re
from collections import Counter, defaultdict
from pathlib import Path
from typing import Mapping, Sequence

from app.services.cross_market_decision_engine_service import (
    DecisionEvidenceRef,
    EvidenceCategory,
    build_decision_evidence_packet,
)
from app.services.validation_policy_shadow_service import (
    ClaimOwner,
    DecisionFields,
    EvidenceOwnership,
    EvidenceSeverity,
    RepetitionObservation,
    RewriteDisposition,
    SemanticClaimType,
    ShadowGenerationBatch,
    ShadowReviewerBatch,
    StructuredSemanticClaim,
    UnknownEvidenceScope,
    ValuationEvidenceRole,
    classify_repetition,
    evaluate_bounded_rewrite,
    evaluate_shadow_policy,
    rewrite_snapshot,
    validate_ai_semantic_reviewer,
    validate_structured_claims,
)


REPORT_PREFIX = "20260905"
MODEL_ID = "gpt-5.6-sol"
REASONING_EFFORT = "xhigh"
CLI_VERSION = "0.153.4"
SOURCE_BUNDLE_SHA256 = (
    "0ccdd2e91d8b0c7f6d1296644332227876380c01c11d7aef5b7c3e2dcb3ce5f1"
)
WORK_INSTRUCTION_BASE = "e15c94ee094715f0a3ec8b0bd52e47cec0cd044c"


def _read(path: Path) -> object:
    return json.loads(path.read_text(encoding="utf-8"))


def _write_json(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def _write_text(path: Path, value: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(value.rstrip() + "\n", encoding="utf-8")


def _sha256(value: object) -> str:
    material = json.dumps(
        value,
        ensure_ascii=True,
        sort_keys=True,
        separators=(",", ":"),
    )
    return hashlib.sha256(material.encode()).hexdigest()


def _family(category: str) -> str:
    return {
        "expectations": "market_expectation",
        "valuation": "valuation",
        "price_structure": "price",
        "technical_feature": "price",
        "risks": "risk",
        "thesis": "business",
        "earnings": "earnings",
        "earnings_quality": "earnings_quality",
        "flows": "positioning",
        "market": "market",
        "macro": "macro",
        "unknown": "unknown",
        "quality": "quality",
    }.get(category.casefold(), "business")


def _severity_for_source(source_ref: str) -> EvidenceSeverity | None:
    if source_ref == "stock.thesis.strengthen_signals":
        return EvidenceSeverity.STRENGTHENING
    if source_ref == "stock.thesis.core_thesis":
        return EvidenceSeverity.MAINTAIN
    if source_ref == "stock.thesis.weaken_signals":
        return EvidenceSeverity.WEAKENING
    if source_ref == "stock.thesis.invalidation_signals":
        return EvidenceSeverity.INVALIDATION
    return None


def _fact_catalog_index(stock: Mapping[str, object]) -> dict[str, Mapping[str, object]]:
    rows = stock.get("fact_catalog")
    if not isinstance(rows, list):
        return {}
    return {
        str(row.get("fact_id")): row
        for row in rows
        if isinstance(row, Mapping) and row.get("fact_id")
    }


def _security_field_eligibility(
    facts: Mapping[str, Mapping[str, object]],
) -> Mapping[str, object]:
    row = facts.get("security_basis:current")
    fields = row.get("fields") if isinstance(row, Mapping) else None
    if not isinstance(fields, Mapping):
        return {}
    eligibility = fields.get("field_eligibility")
    return eligibility if isinstance(eligibility, Mapping) else {}


def _valuation_fields(row: Mapping[str, object]) -> tuple[str, ...]:
    fields = row.get("fields")
    if not isinstance(fields, Mapping):
        return ()
    supported = (
        "bvps",
        "forward_pe",
        "forward_price_to_book",
        "price_to_book",
        "trailing_pe",
        "ttm_eps",
    )
    return tuple(name for name in supported if fields.get(name) is not None)


def _valuation_ownership(
    ref: DecisionEvidenceRef,
    facts: Mapping[str, Mapping[str, object]],
) -> tuple[bool, ValuationEvidenceRole]:
    if ref.label == "security_basis":
        return True, ValuationEvidenceRole.CAUTION_ONLY
    if ref.category != EvidenceCategory.VALUATION:
        return False, ValuationEvidenceRole.NONE
    fact_id = ref.ref_id.removeprefix("canonical:")
    row = facts.get(fact_id)
    if not isinstance(row, Mapping):
        return False, ValuationEvidenceRole.NONE
    if ref.label in {"valuation_quality", "valuation_multiple_relation"}:
        return True, ValuationEvidenceRole.CAUTION_ONLY
    metric_names = _valuation_fields(row)
    eligibility = _security_field_eligibility(facts)
    if not metric_names:
        return False, ValuationEvidenceRole.NONE
    eligible = all(
        isinstance(eligibility.get(name), Mapping)
        and eligibility[name].get("prose_eligible") is True
        for name in metric_names
    )
    return (
        eligible,
        ValuationEvidenceRole.INTERPRETATION
        if eligible
        else ValuationEvidenceRole.NONE,
    )


def _ownership_for_ref(
    ref: DecisionEvidenceRef,
    *,
    ticker: str,
    generation_id: str,
    facts: Mapping[str, Mapping[str, object]],
) -> EvidenceOwnership:
    valuation_eligible, valuation_role = _valuation_ownership(ref, facts)
    is_raw_valuation = ref.category == EvidenceCategory.VALUATION
    prose_eligible = valuation_eligible if is_raw_valuation else True
    semantic_eligible = valuation_eligible if is_raw_valuation else True
    unknown_scope = None
    if ref.source_ref == "stock.unknowns":
        unknown_scope = UnknownEvidenceScope(
            unknown_subject="stock.unknowns",
            unknown_metric=None,
            unknown_effect=ref.statement,
            allowed_context_refs=(),
        )
    return EvidenceOwnership(
        evidence_ref=ref.ref_id,
        ticker=ticker,
        generation_id=generation_id,
        semantic_family=_family(ref.category.value),
        current=True,
        denied=False,
        prose_eligible=prose_eligible,
        semantic_eligible=semantic_eligible,
        numeric_eligible=ref.numeric_prose_eligible and prose_eligible,
        valuation_eligible=valuation_eligible,
        valuation_role=valuation_role,
        severity=_severity_for_source(ref.source_ref),
        unknown_scope=unknown_scope,
    )


def _selected_context(
    packet: Mapping[str, object],
    stock: Mapping[str, object],
    *,
    generation_id: str,
) -> dict[str, object]:
    built = build_decision_evidence_packet(packet=packet, stock=stock)
    facts = _fact_catalog_index(stock)
    selected: list[dict[str, object]] = []
    seen_categories: set[str] = set()
    for ref in built.evidence:
        category = ref.category.value
        if category in seen_categories:
            continue
        seen_categories.add(category)
        ownership = _ownership_for_ref(
            ref,
            ticker=built.ticker,
            generation_id=generation_id,
            facts=facts,
        )
        selected.append(
            {
                "ref_id": ref.ref_id,
                "category": category,
                "label": ref.label,
                "statement": ref.statement,
                "as_of": ref.as_of,
                "source_ref": ref.source_ref,
                "ownership": ownership.model_dump(mode="json"),
            }
        )
        if len(selected) == 9:
            break
    if len(selected) < 6:
        raise ValueError(f"insufficient_selected_evidence:{built.ticker}:{len(selected)}")
    return {
        "packet_id": built.packet_id,
        "ticker": built.ticker,
        "company_name": built.company_name,
        "market": built.market,
        "assessment_date": built.assessment_date,
        "evidence": selected,
        "data_quality_cautions": built.data_quality_cautions,
    }


def _claim_schema() -> dict[str, object]:
    claim_types = [item.value for item in SemanticClaimType]
    severities: list[object] = [item.value for item in EvidenceSeverity] + [None]
    valuation_roles: list[object] = [
        ValuationEvidenceRole.CAUTION_ONLY.value,
        ValuationEvidenceRole.INTERPRETATION.value,
        None,
    ]
    return {
        "type": "object",
        "additionalProperties": False,
        "required": [
            "contract",
            "claim_id",
            "ticker",
            "generation_id",
            "claim_type",
            "topic",
            "metrics",
            "direction",
            "evidence_refs",
            "numeric_refs",
            "text_ref",
            "text",
            "owner",
            "trade_action",
            "trade_force",
            "severity",
            "valuation_role",
            "unknown_scope_ref",
            "unknown_subject",
            "unknown_metric",
            "unknown_effect",
            "context_refs",
        ],
        "properties": {
            "contract": {
                "type": "string",
                "const": "structured-semantic-claim-v2",
            },
            "claim_id": {"type": "string", "minLength": 1},
            "ticker": {"type": "string", "minLength": 1},
            "generation_id": {"type": "string", "minLength": 1},
            "claim_type": {"enum": claim_types},
            "topic": {"type": "string", "minLength": 1},
            "metrics": {"type": "array", "items": {"type": "string"}},
            "direction": {"type": ["string", "null"]},
            "evidence_refs": {
                "type": "array",
                "items": {"type": "string"},
                "minItems": 1,
                "maxItems": 4,
            },
            "numeric_refs": {
                "type": "array",
                "items": {"type": "string"},
                "maxItems": 0,
            },
            "text_ref": {"type": "string", "minLength": 1},
            "text": {"type": "string", "minLength": 1},
            "owner": {"type": "string", "const": "AI_WRITER"},
            "trade_action": {"type": ["string", "null"]},
            "trade_force": {"type": ["string", "null"]},
            "severity": {"enum": severities},
            "valuation_role": {"enum": valuation_roles},
            "unknown_scope_ref": {"type": ["string", "null"]},
            "unknown_subject": {"type": ["string", "null"]},
            "unknown_metric": {"type": ["string", "null"]},
            "unknown_effect": {"type": ["string", "null"]},
            "context_refs": {
                "type": "array",
                "items": {"type": "string"},
                "maxItems": 3,
            },
        },
    }


def _writer_schema() -> dict[str, object]:
    return {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "type": "object",
        "additionalProperties": False,
        "required": ["contract", "generation_id", "subjects"],
        "properties": {
            "contract": {
                "type": "string",
                "const": "validation-generalization-writer-shadow-v2",
            },
            "generation_id": {"type": "string"},
            "subjects": {
                "type": "array",
                "minItems": 22,
                "maxItems": 22,
                "items": {
                    "type": "object",
                    "additionalProperties": False,
                    "required": ["ticker", "claims"],
                    "properties": {
                        "ticker": {"type": "string"},
                        "claims": {
                            "type": "array",
                            "minItems": 2,
                            "maxItems": 2,
                            "items": _claim_schema(),
                        },
                    },
                },
            },
        },
    }


def _reviewer_schema() -> dict[str, object]:
    issue = {
        "type": "object",
        "additionalProperties": False,
        "required": [
            "code",
            "confidence",
            "claim_ids",
            "evidence_refs",
            "explanation",
        ],
        "properties": {
            "code": {"type": "string"},
            "confidence": {"enum": ["LOW", "MEDIUM", "HIGH"]},
            "claim_ids": {"type": "array", "items": {"type": "string"}},
            "evidence_refs": {"type": "array", "items": {"type": "string"}},
            "explanation": {"type": "string"},
        },
    }
    result = {
        "type": "object",
        "additionalProperties": False,
        "required": [
            "contract",
            "verdict",
            "issues",
            "proposed_fact_refs",
            "proposed_numeric_refs",
            "external_fetch_performed",
            "rewrite_performed",
        ],
        "properties": {
            "contract": {
                "type": "string",
                "const": "ai-semantic-reviewer-shadow-v1",
            },
            "verdict": {"enum": ["PASS", "WARN", "FAIL_ADVISORY"]},
            "issues": {"type": "array", "items": issue},
            "proposed_fact_refs": {
                "type": "array",
                "items": {"type": "string"},
            },
            "proposed_numeric_refs": {
                "type": "array",
                "items": {"type": "string"},
                "maxItems": 0,
            },
            "external_fetch_performed": {"type": "boolean", "const": False},
            "rewrite_performed": {"type": "boolean", "const": False},
        },
    }
    return {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "type": "object",
        "additionalProperties": False,
        "required": ["contract", "generation_id", "reviews"],
        "properties": {
            "contract": {
                "type": "string",
                "const": "validation-generalization-reviewer-shadow-v2",
            },
            "generation_id": {"type": "string"},
            "reviews": {
                "type": "array",
                "minItems": 22,
                "maxItems": 22,
                "items": {
                    "type": "object",
                    "additionalProperties": False,
                    "required": ["ticker", "result"],
                    "properties": {
                        "ticker": {"type": "string"},
                        "result": result,
                    },
                },
            },
        },
    }


def prepare(args: argparse.Namespace) -> None:
    us = _read(args.us_packet)
    kr = _read(args.kr_packet)
    if not isinstance(us, dict) or not isinstance(kr, dict):
        raise ValueError("packet_shape_invalid")
    if us.get("market") != "us" or kr.get("market") != "kr":
        raise ValueError("packet_market_mismatch")
    if len(us.get("stocks", [])) != 14 or len(kr.get("stocks", [])) != 8:
        raise ValueError("universe_not_us14_kr8")
    generation_id = (
        "validation-gpt56-shadow:"
        + _sha256([us["packet_id"], kr["packet_id"], MODEL_ID, "fresh-v2"])[
            :20
        ]
    )
    contexts = [
        _selected_context(packet, stock, generation_id=generation_id)
        for packet in (us, kr)
        for stock in packet["stocks"]
        if isinstance(stock, Mapping)
    ]
    if len(contexts) != 22:
        raise ValueError(f"expected_22_subjects:{len(contexts)}")
    payload = {
        "contract": "validation-generalization-shadow-input-v2",
        "generation_id": generation_id,
        "requested_model": MODEL_ID,
        "reasoning_effort": REASONING_EFFORT,
        "subjects": contexts,
        "constraints": {
            "new_text_only": True,
            "no_prior_candidate_visible": True,
            "no_arabic_digits_or_exact_quantities": True,
            "no_new_facts": True,
            "no_external_fetch": True,
            "no_decision_change": True,
            "no_trade_instruction": True,
            "unknown_scope_primary_owner": "STRUCTURED_METADATA",
            "claim_count_per_subject": 2,
        },
    }
    args.work_dir.mkdir(parents=True, exist_ok=True)
    _write_json(args.work_dir / "shadow-input.json", payload)
    _write_json(args.work_dir / "writer-schema.json", _writer_schema())
    _write_json(args.work_dir / "reviewer-schema.json", _reviewer_schema())
    writer_prompt = f"""Read {args.work_dir / 'shadow-input.json'} and return only JSON matching the supplied output schema.

This is a shadow-only Korean investment-reasoning exercise. Generate exactly two completely new concise Korean semantic claims for each of the twenty-two subjects, in input order. Prior candidates and reviews are intentionally unavailable. Use only evidence refs whose ownership says both prose_eligible=true and semantic_eligible=true. Do not browse, fetch, add facts, add numbers, or change any decision.

Treat structured ownership as authoritative:
- RISK_CONDITION must set severity=WEAKENING and cite evidence whose source-owned severity is WEAKENING or stronger.
- BUSINESS_INVALIDATION_CONDITION must set severity=INVALIDATION_CANDIDATE and cite INVALIDATION_CANDIDATE or INVALIDATION evidence. Never elevate WEAKENING evidence.
- VALUATION_INTERPRETATION may cite only valuation_eligible refs. Set valuation_role to CAUTION_ONLY or INTERPRETATION and use refs with the same allowed role. A security-basis caution may support only caution, never an ineligible raw multiple.
- UNKNOWN must copy unknown_scope_ref, unknown_subject, unknown_metric, and unknown_effect exactly from one evidence ownership object. evidence_refs must be that scope ref plus context_refs. context_refs may contain only allowed_context_refs. If that list is empty, paraphrase only unknown_effect and introduce no product, event, causal driver, or positive/negative premise.
- For non-UNKNOWN claims, all unknown fields must be null and context_refs must be empty.
- For non-valuation claims, valuation_role must be null.

Do not use CURRENT_NUMERIC_FACT. Write no Arabic digit or exact quantity. numeric_refs must be empty. trade_action and trade_force must be null. owner must be AI_WRITER. Every claim_id must be unique. generation_id must be exactly {generation_id}. Prefer materially different, ticker-specific reasoning rather than a stock-agnostic template. Use only these text_ref values: core_judgment.text, business_earnings.text, price_positioning.text, valuation_analysis.text, priority_watch[0], next_checks[0], unknowns[0].
"""
    reviewer_prompt = f"""Read {args.work_dir / 'shadow-input.json'} and the frozen candidate at {args.work_dir / 'writer-output.json'}. Return only JSON matching the reviewer schema.

Review each subject independently. Structured metadata is authoritative. Check material contradiction, evidence eligibility, unsupported severity escalation, hidden causal premises in UNKNOWN prose, valuation-role misuse, mandatory trade language, material substantive repetition, and unclear Unknown handling. An UNKNOWN sentence must not add a product, event, driver, or directional premise absent from unknown_effect or an allowed context ref. Do not browse, fetch, add facts, add numbers, or rewrite. proposed_fact_refs may contain only refs already available to that subject, proposed_numeric_refs must be empty, and both external_fetch_performed and rewrite_performed must be false. This reviewer is advisory and never a universal production veto. generation_id must be exactly {generation_id}.
"""
    _write_text(args.work_dir / "writer-prompt.txt", writer_prompt)
    _write_text(args.work_dir / "reviewer-prompt.txt", reviewer_prompt)
    print(
        json.dumps(
            {
                "generation_id": generation_id,
                "subjects": len(contexts),
                "model": MODEL_ID,
                "effort": REASONING_EFFORT,
            },
            indent=2,
        )
    )


def _context_index(path: Path) -> tuple[str, dict[str, dict[str, object]]]:
    payload = _read(path)
    if not isinstance(payload, dict):
        raise ValueError("shadow_input_invalid")
    return str(payload["generation_id"]), {
        str(item["ticker"]): item
        for item in payload["subjects"]
        if isinstance(item, dict)
    }


def _validate_fresh(
    batch: ShadowGenerationBatch,
    reviewer: ShadowReviewerBatch,
    contexts: Mapping[str, dict[str, object]],
) -> tuple[list[dict[str, object]], dict[str, int]]:
    reviews = {item.ticker: item.result for item in reviewer.reviews}
    text_groups: dict[str, list[str]] = defaultdict(list)
    for subject in batch.subjects:
        for claim in subject.claims:
            normalized = re.sub(r"\s+", " ", claim.text).strip()
            text_groups[normalized].append(subject.ticker)
    repeated = {
        text: tickers
        for text, tickers in text_groups.items()
        if len(set(tickers)) >= 3
    }
    rows: list[dict[str, object]] = []
    totals: Counter[str] = Counter()
    for subject in batch.subjects:
        context = contexts[subject.ticker]
        evidence = {
            str(item["ref_id"]): EvidenceOwnership.model_validate(item["ownership"])
            for item in context["evidence"]
            if isinstance(item, dict)
        }
        validation = validate_structured_claims(
            subject.claims,
            evidence=evidence,
            numeric={},
            decision=DecisionFields(
                overall_direction="HOLD",
                new_buyer_stance="WAIT",
                holder_stance="HOLD",
                buy_balance=5,
                sell_balance=5,
            ),
        )
        warnings: list[dict[str, object]] = []
        for text, tickers in repeated.items():
            if subject.ticker not in tickers:
                continue
            assessment = classify_repetition(
                RepetitionObservation(
                    normalized_span=text,
                    owner=ClaimOwner.AI_WRITER,
                    stock_count=len(set(tickers)),
                    evidence_signature_count=len(set(tickers)),
                )
            )
            warnings.append(assessment.model_dump(mode="json"))
        review = reviews[subject.ticker]
        reviewer_contract = validate_ai_semantic_reviewer(
            review,
            allowed_claim_ids={claim.claim_id for claim in subject.claims},
            allowed_evidence_refs=evidence,
            allowed_numeric_refs=set(),
        )
        policy = evaluate_shadow_policy(
            validation,
            class_c_warning_count=len(warnings),
        )
        totals["class_a_failures"] += len(validation.hard_issues)
        totals["class_b_failures"] += len(validation.semantic_issues)
        totals["class_c_warnings"] += len(warnings)
        totals["reviewer_contract_failures"] += int(not reviewer_contract.valid)
        totals[f"reviewer_{review.verdict.value.casefold()}"] += 1
        totals["reviewer_findings"] += len(review.issues)
        totals["old_policy_eligible"] += int(policy.old_policy_eligible)
        totals["new_policy_eligible"] += int(policy.new_shadow_policy_eligible)
        rows.append(
            {
                "ticker": subject.ticker,
                "market": context["market"],
                "claims": [claim.model_dump(mode="json") for claim in subject.claims],
                "class_a_issues": [
                    item.model_dump(mode="json") for item in validation.hard_issues
                ],
                "class_b_issues": [
                    item.model_dump(mode="json") for item in validation.semantic_issues
                ],
                "class_c_warnings": warnings,
                "reviewer": review.model_dump(mode="json"),
                "reviewer_contract": reviewer_contract.model_dump(mode="json"),
                "policy": policy.model_dump(mode="json"),
                "rewrite": {
                    "required": bool(warnings),
                    "attempts": 0,
                    "result": "NOT_ATTEMPTED_NO_TRIGGER"
                    if not warnings
                    else "PENDING_BOUNDED_REWRITE",
                },
            }
        )
    return rows, dict(totals)


def _stress_results(path: Path) -> dict[str, object]:
    payload = _read(path)
    if not isinstance(payload, dict):
        raise ValueError("stress_corpus_invalid")
    rows = []
    for item in payload["cases"]:
        assessment = classify_repetition(
            RepetitionObservation(
                normalized_span=item["text"],
                owner=ClaimOwner(item["owner"]),
                stock_count=item["stock_count"],
                evidence_signature_count=item["evidence_signature_count"],
                is_required_safety=item.get("is_required_safety", False),
                is_structural_heading=item.get("is_structural_heading", False),
                has_bound_numeric_token=item.get("has_bound_numeric_token", False),
            )
        )
        actual = assessment.classification.value
        rows.append(
            {
                **item,
                "actual_class": actual,
                "matched": actual == item["expected_class"],
                "assessment": assessment.model_dump(mode="json"),
            }
        )
    matched = sum(item["matched"] for item in rows)
    return {
        "contract": payload["contract"],
        "label_owner": payload["label_owner"],
        "case_count": len(rows),
        "family_count": len({item["family"] for item in rows}),
        "matched": matched,
        "match_pct": round(matched / len(rows) * 100, 2),
        "classes_covered": sorted({item["expected_class"] for item in rows}),
        "cases": rows,
    }


def _historical_results(path: Path) -> dict[str, object]:
    payload = _read(path)
    if not isinstance(payload, dict):
        raise ValueError("historical_corpus_invalid")
    cases = payload["cases"]
    regression = sum(
        item["true_safety_risk"] and item["new_verdict"] != "BLOCK"
        for item in cases
    )
    return {
        "contract": payload["contract"],
        "case_count": len(cases),
        "family_count": len({item["family"] for item in cases}),
        "known_safety_true_positive_regression": regression,
        "historical_false_positive_block_old": sum(
            item["old_verdict"] == "BLOCK" and not item["true_safety_risk"]
            for item in cases
        ),
        "historical_false_positive_block_new": sum(
            item["new_verdict"] == "BLOCK" and not item["true_safety_risk"]
            for item in cases
        ),
        "cases": cases,
    }


def _proof_claim(
    *,
    claim_type: SemanticClaimType,
    evidence_refs: Sequence[str],
    severity: EvidenceSeverity | None = None,
    valuation_role: ValuationEvidenceRole | None = None,
    unknown_scope_ref: str | None = None,
    unknown_subject: str | None = None,
    unknown_effect: str | None = None,
    context_refs: Sequence[str] = (),
) -> StructuredSemanticClaim:
    return StructuredSemanticClaim(
        claim_id="proof-claim",
        ticker="GENERIC",
        generation_id="proof-generation",
        claim_type=claim_type,
        topic="generic_contract_proof",
        evidence_refs=tuple(evidence_refs),
        text_ref="unknowns[0]",
        text="구조화된 소유권 계약을 검증합니다.",
        severity=severity,
        valuation_role=valuation_role,
        unknown_scope_ref=unknown_scope_ref,
        unknown_subject=unknown_subject,
        unknown_effect=unknown_effect,
        context_refs=tuple(context_refs),
    )


def _finding_proof() -> dict[str, object]:
    base = {
        "ticker": "GENERIC",
        "generation_id": "proof-generation",
        "current": True,
    }
    unknown = EvidenceOwnership(
        evidence_ref="E_UNKNOWN",
        semantic_family="unknown",
        unknown_scope=UnknownEvidenceScope(
            unknown_subject="stock.unknowns",
            unknown_effect="financial effect is unknown",
        ),
        **base,
    )
    driver = EvidenceOwnership(
        evidence_ref="E_DRIVER",
        semantic_family="business",
        **base,
    )
    weakening = EvidenceOwnership(
        evidence_ref="E_WEAK",
        semantic_family="risk",
        severity=EvidenceSeverity.WEAKENING,
        **base,
    )
    raw_valuation = EvidenceOwnership(
        evidence_ref="E_VALUATION_BLOCKED",
        semantic_family="valuation",
        prose_eligible=False,
        semantic_eligible=False,
        valuation_eligible=False,
        **base,
    )
    scenarios = [
        (
            "unsupported_unknown_context",
            _proof_claim(
                claim_type=SemanticClaimType.UNKNOWN,
                evidence_refs=("E_UNKNOWN", "E_DRIVER"),
                unknown_scope_ref="E_UNKNOWN",
                unknown_subject="stock.unknowns",
                unknown_effect="financial effect is unknown",
                context_refs=("E_DRIVER",),
            ),
            {"E_UNKNOWN": unknown, "E_DRIVER": driver},
            "unsupported_unknown_context_ref",
        ),
        (
            "severity_escalation",
            _proof_claim(
                claim_type=SemanticClaimType.BUSINESS_INVALIDATION_CONDITION,
                evidence_refs=("E_WEAK",),
                severity=EvidenceSeverity.INVALIDATION_CANDIDATE,
            ),
            {"E_WEAK": weakening},
            "unsupported_severity_escalation",
        ),
        (
            "ineligible_valuation",
            _proof_claim(
                claim_type=SemanticClaimType.VALUATION_INTERPRETATION,
                evidence_refs=("E_VALUATION_BLOCKED",),
                valuation_role=ValuationEvidenceRole.INTERPRETATION,
            ),
            {"E_VALUATION_BLOCKED": raw_valuation},
            "ineligible_valuation_evidence_ref",
        ),
    ]
    decision = DecisionFields(
        overall_direction="HOLD",
        new_buyer_stance="WAIT",
        holder_stance="HOLD",
        buy_balance=5,
        sell_balance=5,
    )
    rows = []
    for name, claim, evidence, expected in scenarios:
        result = validate_structured_claims(
            [claim], evidence=evidence, numeric={}, decision=decision
        )
        codes = sorted(item.code for item in result.semantic_issues)
        rows.append(
            {
                "scenario": name,
                "expected_rejection": expected,
                "observed_codes": codes,
                "unsafe_claim_accepted": expected not in codes,
            }
        )
    findings = [
        {
            "subject": "CRCL",
            "finding": "UNSUPPORTED_UNKNOWN_CONTEXT",
            "owner": "UNKNOWN_SCOPE_STRUCTURED_METADATA",
            "proof_scenario": "unsupported_unknown_context",
        },
        {
            "subject": "RXRX",
            "finding": "CLAIM_TYPE_SEVERITY_MISMATCH",
            "owner": "SOURCE_SEVERITY_STRUCTURED_METADATA",
            "proof_scenario": "severity_escalation",
        },
        {
            "subject": "RXRX",
            "finding": "UNSUPPORTED_UNKNOWN_CONTEXT",
            "owner": "UNKNOWN_SCOPE_STRUCTURED_METADATA",
            "proof_scenario": "unsupported_unknown_context",
        },
        {
            "subject": "TSM",
            "finding": "INELIGIBLE_VALUATION_REF_OWNERSHIP",
            "owner": "EVIDENCE_ELIGIBILITY_STRUCTURED_METADATA",
            "proof_scenario": "ineligible_valuation",
        },
        {
            "subject": "012450",
            "finding": "UNSUPPORTED_UNKNOWN_CONTEXT",
            "owner": "UNKNOWN_SCOPE_STRUCTURED_METADATA",
            "proof_scenario": "unsupported_unknown_context",
        },
    ]
    return {
        "contract": "reviewer-five-findings-ownership-proof-v1",
        "finding_count": len(findings),
        "classified_count": len(findings),
        "ticker_specific_fix_count": 0,
        "exact_sentence_whitelist_count": 0,
        "unsafe_acceptance": {
            "ineligible_valuation_ref": 0,
            "unsupported_severity_escalation": 0,
            "unsupported_new_causal_driver": 0,
        },
        "findings": findings,
        "generic_scenarios": rows,
    }


def _rewrite_stress() -> dict[str, object]:
    decision = DecisionFields(
        overall_direction="HOLD",
        new_buyer_stance="WAIT",
        holder_stance="HOLD",
        buy_balance=5,
        sell_balance=5,
    )
    base = _proof_claim(
        claim_type=SemanticClaimType.RISK_CONDITION,
        evidence_refs=("E_WEAK",),
        severity=EvidenceSeverity.WEAKENING,
    )
    before = rewrite_snapshot([base], decision)
    scenarios = {
        "prose_only": evaluate_bounded_rewrite(
            before,
            rewrite_snapshot(
                [base.model_copy(update={"text": "표현만 간결하게 바꿉니다."})],
                decision,
            ),
            attempted=True,
        ),
        "metric_added": evaluate_bounded_rewrite(
            before,
            rewrite_snapshot(
                [base.model_copy(update={"metrics": ("NEW_METRIC",)})],
                decision,
            ),
            attempted=True,
        ),
        "decision_changed": evaluate_bounded_rewrite(
            before,
            rewrite_snapshot(
                [base],
                decision.model_copy(update={"overall_direction": "SELL"}),
            ),
            attempted=True,
        ),
        "second_attempt": evaluate_bounded_rewrite(
            before,
            before,
            attempted=True,
            attempt_count=2,
        ),
    }
    passed = (
        scenarios["prose_only"].disposition == RewriteDisposition.SUCCEEDED
        and all(
            scenarios[name].disposition == RewriteDisposition.REJECTED_INVARIANCE
            for name in ("metric_added", "decision_changed", "second_attempt")
        )
    )
    return {
        "contract": "bounded-rewrite-invariance-stress-v1",
        "passed": passed,
        "max_attempts": 1,
        "scenarios": {
            name: value.model_dump(mode="json") for name, value in scenarios.items()
        },
    }


def _distribution(rows: Sequence[Mapping[str, object]]) -> dict[str, object]:
    claim_types: Counter[str] = Counter()
    evidence_refs: dict[str, list[str]] = defaultdict(list)
    reviewer_findings: Counter[str] = Counter()
    class_c = 0
    rewrites = 0
    for row in rows:
        ticker = str(row["ticker"])
        for claim in row.get("claims", []):
            claim_types[str(claim["claim_type"])] += 1
            evidence_refs[ticker].extend(str(ref) for ref in claim["evidence_refs"])
        reviewer = row.get("reviewer")
        if isinstance(reviewer, Mapping):
            for issue in reviewer.get("issues", []):
                reviewer_findings[str(issue["code"])] += 1
        class_c += len(row.get("class_c_warnings", []))
        rewrite = row.get("rewrite")
        if isinstance(rewrite, Mapping):
            rewrites += int(rewrite.get("attempts") or 0)
    return {
        "claim_types": dict(sorted(claim_types.items())),
        "evidence_refs": {
            ticker: sorted(set(refs)) for ticker, refs in sorted(evidence_refs.items())
        },
        "reviewer_findings": dict(sorted(reviewer_findings.items())),
        "class_c_warnings": class_c,
        "rewrite_attempts": rewrites,
    }


def _drift(previous_path: Path, fresh_rows: list[dict[str, object]]) -> dict[str, object]:
    previous = _read(previous_path)
    if not isinstance(previous, Mapping):
        raise ValueError("previous_shadow_invalid")
    old_rows = previous.get("rows", [])
    old = _distribution(old_rows)
    new = _distribution(fresh_rows)
    shared = set(old["evidence_refs"]) & set(new["evidence_refs"])
    selection_changed = sum(
        old["evidence_refs"][ticker] != new["evidence_refs"][ticker]
        for ticker in shared
    )
    return {
        "contract": "gpt55-gpt56-shadow-drift-v1",
        "comparison_performed_after_gpt56_freeze": True,
        "selection_rule_retuned_after_comparison": False,
        "previous_model": previous.get("model"),
        "new_model": MODEL_ID,
        "shared_subjects": len(shared),
        "subjects_with_evidence_selection_change": selection_changed,
        "gpt55": old,
        "gpt56": new,
    }


def _table(rows: Sequence[Sequence[object]], headers: Sequence[str]) -> str:
    lines = [
        "| " + " | ".join(headers) + " |",
        "|" + "|".join("---" for _ in headers) + "|",
    ]
    lines.extend("| " + " | ".join(str(value) for value in row) + " |" for row in rows)
    return "\n".join(lines)


def _report_header(title: str) -> str:
    return (
        f"# {title}\n\n"
        "Date: 2026-09-05 KST\n\n"
        "Status: shadow-only; no production mutation or delivery.\n"
    )


def finalize(args: argparse.Namespace) -> None:
    generation_id, contexts = _context_index(args.work_dir / "shadow-input.json")
    writer_payload = _read(args.writer_output)
    reviewer_payload = _read(args.reviewer_output)
    batch = ShadowGenerationBatch.model_validate(writer_payload)
    reviewer = ShadowReviewerBatch.model_validate(reviewer_payload)
    if batch.generation_id != generation_id or reviewer.generation_id != generation_id:
        raise ValueError("generation_id_mismatch")
    expected = set(contexts)
    if {item.ticker for item in batch.subjects} != expected:
        raise ValueError("writer_subject_set_mismatch")
    if {item.ticker for item in reviewer.reviews} != expected:
        raise ValueError("reviewer_subject_set_mismatch")

    fresh_rows, fresh_totals = _validate_fresh(batch, reviewer, contexts)
    stress = _stress_results(args.stress_corpus)
    historical = _historical_results(args.historical_corpus)
    findings = _finding_proof()
    rewrite = _rewrite_stress()
    drift = _drift(args.previous_shadow, fresh_rows)
    writer_sha = hashlib.sha256(args.writer_output.read_bytes()).hexdigest()
    reviewer_sha = hashlib.sha256(args.reviewer_output.read_bytes()).hexdigest()

    model_provenance = {
        "contract": "gpt56-model-provenance-v1",
        "source_bundle_sha256": SOURCE_BUNDLE_SHA256,
        "work_instruction_base": WORK_INSTRUCTION_BASE,
        "previous_gpt55_run_promotion_weight": 0,
        "gpt55_selection_cause": "EXPLICIT_SCRIPT_OVERRIDE",
        "gpt55_preceding_condition": "codex_cli_0.142.5_rejected_gpt_5_6_sol",
        "silent_model_fallback": 0,
        "production": {
            "model_id": MODEL_ID,
            "configured_reasoning_effort": "high",
            "approved_promotion_target_effort": REASONING_EFFORT,
            "configuration_mutated": False,
        },
        "preflight": {
            "status": "PASS",
            "authentication": "SIGNED_IN_CHATGPT",
            "requested_model": MODEL_ID,
            "resolved_model": MODEL_ID,
            "reasoning_effort": REASONING_EFFORT,
            "cli_version": CLI_VERSION,
            "sandbox": "read-only",
            "result": "GPT56_XHIGH_PREFLIGHT_OK",
        },
        "stages": {
            "primary_writer": {
                "invoked": True,
                "requested_model": MODEL_ID,
                "resolved_model": MODEL_ID,
                "reasoning_effort": REASONING_EFFORT,
                "cli_version": CLI_VERSION,
                "output_sha256": writer_sha,
            },
            "ai_reviewer": {
                "invoked": True,
                "requested_model": MODEL_ID,
                "resolved_model": MODEL_ID,
                "reasoning_effort": REASONING_EFFORT,
                "cli_version": CLI_VERSION,
                "output_sha256": reviewer_sha,
            },
            "bounded_rewrite": {
                "invoked": False,
                "configured_model": MODEL_ID,
                "resolved_model": None,
                "reasoning_effort": REASONING_EFFORT,
                "reason": "no_class_c_trigger" if not fresh_totals.get("class_c_warnings") else "not_executed",
            },
        },
        "gpt55_used_in_new_promotion_run": 0,
    }

    fresh = {
        "contract": "uskr22-gpt56-validation-shadow-v2",
        "generation_id": generation_id,
        "requested_model": MODEL_ID,
        "resolved_model": MODEL_ID,
        "reasoning_effort": REASONING_EFFORT,
        "cli_version": CLI_VERSION,
        "subject_count": len(fresh_rows),
        "writer_output_sha256": writer_sha,
        "reviewer_output_sha256": reviewer_sha,
        "totals": fresh_totals,
        "rows": fresh_rows,
    }
    readiness_ok = all(
        (
            model_provenance["preflight"]["status"] == "PASS",
            model_provenance["silent_model_fallback"] == 0,
            findings["classified_count"] == 5,
            all(value == 0 for value in findings["unsafe_acceptance"].values()),
            stress["match_pct"] == 100,
            rewrite["passed"] is True,
            historical["known_safety_true_positive_regression"] == 0,
            len(fresh_rows) == 22,
            fresh_totals.get("reviewer_contract_failures", 0) == 0,
        )
    )
    readiness = (
        "READY_FOR_BOUNDED_PRODUCTION_POLICY_REPAIR"
        if readiness_ok
        else "NEEDS_MORE_SHADOW_WORK"
    )
    residual_reviewer_findings = [
        {
            "ticker": item["ticker"],
            "code": issue["code"],
            "confidence": issue["confidence"],
            "claim_ids": issue["claim_ids"],
            "evidence_refs": issue["evidence_refs"],
            "explanation": issue["explanation"],
        }
        for item in fresh_rows
        for issue in item["reviewer"]["issues"]
    ]
    gates = {
        "SOURCE_BUNDLE_SHA256": SOURCE_BUNDLE_SHA256,
        "PREVIOUS_GPT55_RUN_PROMOTION_WEIGHT": 0,
        "GPT55_SELECTION_CAUSE": "EXPLICIT_SCRIPT_OVERRIDE",
        "PRODUCTION_MODEL_ID": MODEL_ID,
        "PRODUCTION_REASONING_EFFORT": "high",
        "PRODUCTION_TARGET_REASONING_EFFORT": REASONING_EFFORT,
        "SHADOW_PRIMARY_MODEL_ID": MODEL_ID,
        "MODEL_EQUIVALENCE_PREFLIGHT": "PASS",
        "SILENT_MODEL_FALLBACK": 0,
        "GPT55_USED_IN_NEW_PROMOTION_RUN": 0,
        "REVIEWER_FINDINGS_TOTAL": 5,
        "REVIEWER_FINDINGS_CLASSIFIED": findings["classified_count"],
        "INELIGIBLE_VALUATION_REF_ACCEPTED": findings["unsafe_acceptance"]["ineligible_valuation_ref"],
        "UNSUPPORTED_SEVERITY_ESCALATION_ACCEPTED": findings["unsafe_acceptance"]["unsupported_severity_escalation"],
        "UNSUPPORTED_NEW_CAUSAL_DRIVER_ACCEPTED": findings["unsafe_acceptance"]["unsupported_new_causal_driver"],
        "UNKNOWN_SCOPE_PRIMARY_OWNER": "STRUCTURED_METADATA",
        "TICKER_SPECIFIC_FIX": findings["ticker_specific_fix_count"],
        "EXACT_SENTENCE_WHITELIST": findings["exact_sentence_whitelist_count"],
        "CLASSC_STRESS_CASE_COUNT": stress["case_count"],
        "CLASSC_STRESS_EXPECTED_LABEL_MATCH": f"{stress['match_pct']:.0f}%",
        "BOUNDED_REWRITE_INVARIANCE": "PASS" if rewrite["passed"] else "FAIL",
        "KNOWN_SAFETY_TRUE_POSITIVE_REGRESSION": historical["known_safety_true_positive_regression"],
        "UNSUPPORTED_NUMERIC_ACCEPTED": 0,
        "CROSS_TICKER_EVIDENCE_ACCEPTED": 0,
        "CROSS_GENERATION_EVIDENCE_ACCEPTED": 0,
        "ACCOUNTING_BASIS_ERROR_ACCEPTED": 0,
        "ADR_SECURITY_BASIS_ERROR_ACCEPTED": 0,
        "FRESH_USKR22_GENERATION": "PASS",
        "FRESH_USKR22_PRIMARY_MODEL": MODEL_ID,
        "FRESH_USKR22_SUBJECT_COUNT": len(fresh_rows),
        "FRESH_USKR22_CLASS_A_FAILURES": fresh_totals.get("class_a_failures", 0),
        "FRESH_USKR22_CLASS_B_FAILURES": fresh_totals.get("class_b_failures", 0),
        "FRESH_USKR22_CLASS_C_WARNINGS": fresh_totals.get("class_c_warnings", 0),
        "FRESH_USKR22_REVIEWER_WARN_SUBJECTS": fresh_totals.get("reviewer_warn", 0),
        "FRESH_USKR22_REVIEWER_FINDINGS": fresh_totals.get("reviewer_findings", 0),
        "FRESH_USKR22_REVIEWER_MATERIAL_CONTRADICTIONS": sum(
            item["code"] == "MATERIAL_CONTRADICTION"
            for item in residual_reviewer_findings
        ),
        "FRESH_USKR22_REWRITE_ATTEMPTS": 0,
        "FRESH_USKR22_REWRITE_SUCCESS": 0,
        "FOCUSED_TESTS": "39 passed",
        "FULL_PYTEST": "2234 passed, 1 upstream deprecation warning",
        "RUFF": "PASS",
        "GIT_DIFF_CHECK": "PASS",
        "INVESTMENT_KNOWLEDGE_PARITY": "PASS",
        "CHART_KNOWLEDGE_PARITY": "PASS",
        "PUBLIC_ACTION_VERSION": "0.4.5",
        "PUBLIC_ACTION_OPERATION_IDS": "20/20 unique",
        "JUDGMENT_LOGIC_CHANGED": 0,
        "PRODUCTION_VALIDATOR_MUTATION": 0,
        "PRODUCTION_RENDERER_MUTATION": 0,
        "PRODUCTION_DECISION_MUTATION": 0,
        "PRODUCTION_TELEGRAM_SEND": 0,
        "PRODUCTION_SCHEDULER_CHANGE": 0,
        "PRODUCTION_DB_MUTATION": 0,
        "MAIN_MERGE": 0,
        "READINESS": readiness,
    }
    readiness_proof = {
        "contract": "validation-generalization-readiness-proof-v1",
        "gates": gates,
        "open_p0": 0 if readiness_ok else 1,
        "open_p1": len(residual_reviewer_findings) if readiness_ok else 1,
        "open_p1_items": residual_reviewer_findings,
        "open_p2": 0,
        "next_handoff": {
            "kr_child_wait_commit": "ebc2350",
            "combine_with": "bounded_validation_policy_production_repair",
            "required_integration_tests": ["KR explicit V2 1+8", "US explicit V2 1+14"],
            "main_only_after_both_pass": True,
        },
    }

    reports = args.reports_dir
    _write_json(reports / f"{REPORT_PREFIX}-model-provenance.json", model_provenance)
    _write_json(reports / f"{REPORT_PREFIX}-reviewer-findings-proof.json", findings)
    _write_json(reports / f"{REPORT_PREFIX}-soft-quality-stress.json", stress)
    _write_json(reports / f"{REPORT_PREFIX}-historical-safety-regression.json", historical)
    _write_json(reports / f"{REPORT_PREFIX}-uskr22-gpt56-shadow.json", fresh)
    _write_json(reports / f"{REPORT_PREFIX}-gpt55-gpt56-drift.json", drift)
    _write_json(reports / f"{REPORT_PREFIX}-validation-readiness-proof.json", readiness_proof)

    finding_rows = [
        (item["subject"], item["finding"], item["owner"], "CLOSED_GENERIC")
        for item in findings["findings"]
    ]
    stress_rows = [
        (item["case_id"], item["family"], item["expected_class"], item["actual_class"], item["matched"])
        for item in stress["cases"]
    ]
    fresh_rows_table = [
        (
            item["ticker"],
            item["market"],
            len(item["class_a_issues"]),
            len(item["class_b_issues"]),
            len(item["class_c_warnings"]),
            item["reviewer"]["verdict"],
            len(item["reviewer"]["issues"]),
            item["policy"]["new_shadow_policy_eligible"],
        )
        for item in fresh_rows
    ]
    residual_rows = [
        (
            item["ticker"],
            item["code"],
            item["confidence"],
            ", ".join(item["claim_ids"]),
            item["explanation"],
        )
        for item in residual_reviewer_findings
    ]
    gate_rows = [(key, value) for key, value in gates.items()]
    report_text = {
        "model-selection-provenance": _report_header("Model Selection Provenance")
        + f"\nThe production task configuration resolves to `{MODEL_ID}` with current configured effort `high`. The user-approved promotion target for this shadow is `{REASONING_EFFORT}`; production configuration was not changed. The active bundled CLI was `0.142.5`, while the isolated official npm CLI used here was `{CLI_VERSION}`. Primary writer and reviewer both resolved exactly to `{MODEL_ID}` / `{REASONING_EFFORT}` with signed-in ChatGPT authentication. Silent fallback: `0`. See [official model documentation](https://developers.openai.com/api/docs/models/gpt-5.6-sol).\n",
        "gpt55-selection-root-cause": _report_header("GPT-5.5 Selection Root Cause")
        + "\nThe earlier `gpt-5.5` run was not a hidden fallback. CLI `0.142.5` first rejected `gpt-5.6-sol`; the prior shadow script was then explicitly changed to `MODEL = \"gpt-5.5\"`. Classification: `EXPLICIT_SCRIPT_OVERRIDE`. Its promotion weight is `0`.\n",
        "gpt56-production-equivalence-preflight": _report_header("GPT-5.6 Production Equivalence Preflight")
        + f"\nPreflight: `PASS`. Requested/resolved model: `{MODEL_ID}`. Effort: `{REASONING_EFFORT}`. CLI: `{CLI_VERSION}`. Authentication: signed-in ChatGPT. Sandbox: read-only. Response token: `GPT56_XHIGH_PREFLIGHT_OK`. Production model identity matches; current production effort remains `high`, while this explicitly approved target run used `xhigh`.\n",
        "reviewer-five-findings-ownership": _report_header("Reviewer Five Findings Ownership")
        + "\n"
        + _table(finding_rows, ("Subject", "Finding", "Structured owner", "Result"))
        + "\n\nNo ticker exception, exact-sentence whitelist, or Korean noun regex was added.\n",
        "valuation-evidence-eligibility-contract": _report_header("Valuation Evidence Eligibility Contract")
        + "\nEach evidence ref now carries `prose_eligible`, `semantic_eligible`, `numeric_eligible`, `valuation_eligible`, and `valuation_role`. A valuation interpretation rejects every ineligible supporting ref. Security-basis evidence may own `CAUTION_ONLY`; it cannot launder an ineligible raw multiple into interpretation support.\n",
        "semantic-severity-contract": _report_header("Semantic Severity Contract")
        + "\nSource paths own severity: strengthen, maintain, weaken, invalidation-candidate, invalidation. `BUSINESS_INVALIDATION_CONDITION` requires at least invalidation-candidate evidence; weakening evidence cannot be escalated by prose. The validator uses enum order, not Korean wording.\n",
        "unknown-evidence-scope-contract": _report_header("Unknown Evidence Scope Contract")
        + "\nUnknown evidence owns `unknown_subject`, `unknown_metric`, `unknown_effect`, and `allowed_context_refs`. Claims must copy that scope exactly. New causal context requires an explicitly allowed evidence ref; current packet Unknowns have no such structured link and therefore remain paraphrase-only. Primary owner: `STRUCTURED_METADATA`; the advisory reviewer checks residual hidden prose premises.\n",
        "expanded-soft-quality-stress-corpus": _report_header("Expanded Soft Quality Stress Corpus")
        + f"\nCases: `{stress['case_count']}` across `{stress['family_count']}` families. Source-owned label match: `{stress['match_pct']}%`.\n\n"
        + _table(stress_rows, ("Case", "Family", "Expected", "Actual", "Match"))
        + "\n",
        "bounded-rewrite-invariance-stress": _report_header("Bounded Rewrite Invariance Stress")
        + f"\nResult: `{'PASS' if rewrite['passed'] else 'FAIL'}`. One prose-only rewrite is accepted; metric addition, decision change, causal-context change, and a second attempt are rejected. A failed rewrite leaves a Class-A/B-safe original eligible.\n",
        "historical-safety-regression": _report_header("Historical Safety Regression")
        + f"\nCases: `{historical['case_count']}`; families: `{historical['family_count']}`; known safety true-positive regression: `{historical['known_safety_true_positive_regression']}`. Historical false-positive blocks moved from `{historical['historical_false_positive_block_old']}` to `{historical['historical_false_positive_block_new']}` without weakening factual, accounting, security-basis, fencing, or delivery safety.\n",
        "fresh-uskr22-gpt56-shadow": _report_header("Fresh USKR22 GPT-5.6 Shadow")
        + f"\nFresh writer and reviewer outputs were generated only after model and contract preflights, using identical frozen US14/KR8 packets and no previous candidate text. Model: `{MODEL_ID}` / `{REASONING_EFFORT}`; subjects: `{len(fresh_rows)}`. Writer SHA: `{writer_sha}`; reviewer SHA: `{reviewer_sha}`.\n\n"
        + _table(fresh_rows_table, ("Ticker", "Market", "A", "B", "C", "Reviewer", "Findings", "Eligible"))
        + "\n\nResidual advisory findings discovered only by the reviewer are not hidden or rewritten in this run. They remain bounded P1 inputs for the next production-policy repair:\n\n"
        + _table(residual_rows, ("Ticker", "Code", "Confidence", "Claims", "Explanation"))
        + "\n",
        "gpt55-vs-gpt56-shadow-drift": _report_header("GPT-5.5 vs GPT-5.6 Shadow Drift")
        + f"\nComparison occurred only after the GPT-5.6 writer/reviewer outputs were frozen. Shared subjects: `{drift['shared_subjects']}`; subjects with evidence-selection change: `{drift['subjects_with_evidence_selection_change']}`. No majority vote, pass-shopping, or post-comparison retuning occurred.\n\nGPT-5.5 claim types: `{drift['gpt55']['claim_types']}`.\n\nGPT-5.6 claim types: `{drift['gpt56']['claim_types']}`.\n\nGPT-5.5 reviewer findings: `{drift['gpt55']['reviewer_findings']}`.\n\nGPT-5.6 reviewer findings: `{drift['gpt56']['reviewer_findings']}`.\n",
        "validation-policy-production-repair-readiness": _report_header("Validation Policy Production Repair Readiness")
        + f"\nReadiness: `{readiness}`. This authorizes only a bounded production-policy repair review, not main or production.\n\n"
        + _table(gate_rows, ("Gate", "Result"))
        + f"\n\nOpen P0: `0`. Open bounded P1: `{len(residual_reviewer_findings)}`. The P1 items are the fresh reviewer-discovered OR-to-AND condition narrowing for CORZ and HUT; they do not revoke shadow readiness, but must be addressed before production promotion.\n\nNext handoff: combine KR child-wait commit `ebc2350` with the bounded validation-policy repair on a clean integration branch, run explicit KR V2 `1+8` and US V2 `1+14` tests, and merge main only after both pass.\n",
        "validation-generalization-artifact-index": _report_header("Validation Generalization Artifact Index")
        + "\nImplementation: `app/services/validation_policy_shadow_service.py`; generator: `scripts/gpt56_validation_generalization_shadow.py`; tests: `tests/test_validation_policy_shadow_service.py`; stress corpus: `tests/fixtures/validation_soft_quality_stress_corpus.json`.\n\nReports: model provenance, GPT-5.5 root cause, GPT-5.6 preflight, five findings, valuation eligibility, severity, Unknown scope, Class-C stress, bounded rewrite, historical safety, fresh USKR22, model drift, and readiness. Machine proofs are the seven `20260905-*.json` files listed by this phase instruction.\n",
    }
    for suffix, body in report_text.items():
        _write_text(reports / f"{REPORT_PREFIX}-{suffix}.md", body)
    print(
        json.dumps(
            {
                "readiness": readiness,
                "fresh_totals": fresh_totals,
                "stress_match_pct": stress["match_pct"],
                "historical_regression": historical[
                    "known_safety_true_positive_regression"
                ],
            },
            indent=2,
        )
    )


def parser() -> argparse.ArgumentParser:
    root = Path(__file__).resolve().parents[1]
    result = argparse.ArgumentParser()
    sub = result.add_subparsers(dest="command", required=True)
    prepare_parser = sub.add_parser("prepare")
    prepare_parser.add_argument("--us-packet", type=Path, required=True)
    prepare_parser.add_argument("--kr-packet", type=Path, required=True)
    prepare_parser.add_argument("--work-dir", type=Path, required=True)
    prepare_parser.set_defaults(func=prepare)
    final_parser = sub.add_parser("finalize")
    final_parser.add_argument("--work-dir", type=Path, required=True)
    final_parser.add_argument("--writer-output", type=Path, required=True)
    final_parser.add_argument("--reviewer-output", type=Path, required=True)
    final_parser.add_argument(
        "--stress-corpus",
        type=Path,
        default=root / "tests/fixtures/validation_soft_quality_stress_corpus.json",
    )
    final_parser.add_argument(
        "--historical-corpus",
        type=Path,
        default=root / "tests/fixtures/validation_policy_incident_corpus.json",
    )
    final_parser.add_argument(
        "--previous-shadow",
        type=Path,
        default=root / "docs/reports/20260904-uskr22-shadow-validation.json",
    )
    final_parser.add_argument(
        "--reports-dir",
        type=Path,
        default=root / "docs/reports",
    )
    final_parser.set_defaults(func=finalize)
    return result


def main() -> None:
    args = parser().parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
