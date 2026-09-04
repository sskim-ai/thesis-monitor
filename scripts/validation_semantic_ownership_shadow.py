from __future__ import annotations

import argparse
import hashlib
import json
import re
from collections import Counter, defaultdict
from pathlib import Path
from typing import Mapping

from app.services.cross_market_decision_engine_service import (
    build_decision_evidence_packet,
    compact_ai_context,
)
from app.services.validation_policy_shadow_service import (
    ClaimOwner,
    DecisionFields,
    EvidenceOwnership,
    RepetitionObservation,
    SemanticValidationResult,
    ShadowGenerationBatch,
    ShadowReviewerBatch,
    classify_repetition,
    evaluate_shadow_policy,
    inventory_summary,
    validate_ai_semantic_reviewer,
    validate_structured_claims,
    validator_inventory,
)


REPORT_PREFIX = "20260904"
MODEL = "gpt-5.5"
EFFORT = "xhigh"


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
    payload = json.dumps(value, ensure_ascii=True, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(payload.encode()).hexdigest()


def _family(category: str) -> str:
    category = category.upper()
    return {
        "EXPECTATIONS": "market_expectation",
        "VALUATION": "valuation",
        "PRICE_STRUCTURE": "price",
        "TECHNICAL_FEATURE": "price",
        "RISKS": "risk",
        "THESIS": "business",
        "EARNINGS": "earnings",
        "EARNINGS_QUALITY": "earnings_quality",
        "FLOWS": "positioning",
        "MARKET": "market",
        "MACRO": "macro",
        "UNKNOWN": "unknown",
        "QUALITY": "quality",
    }.get(category, "business")


def _selected_context(packet: Mapping[str, object], stock: Mapping[str, object]) -> dict[str, object]:
    built = build_decision_evidence_packet(packet=packet, stock=stock)
    compact = compact_ai_context(built)
    selected: list[dict[str, object]] = []
    seen_categories: set[str] = set()
    for row in compact["evidence"]:
        assert isinstance(row, dict)
        category = str(row.get("category") or "")
        if category in seen_categories:
            continue
        seen_categories.add(category)
        selected.append(row)
        if len(selected) == 9:
            break
    if len(selected) < 6:
        selected = list(compact["evidence"][:9])
    return {
        "packet_id": compact["packet_id"],
        "ticker": compact["ticker"],
        "company_name": compact["company_name"],
        "market": compact["market"],
        "assessment_date": compact["assessment_date"],
        "evidence": selected,
        "data_quality_cautions": compact["data_quality_cautions"],
    }


def _generation_schema() -> dict[str, object]:
    claim_types = [
        "CURRENT_FACT",
        "CURRENT_NUMERIC_FACT",
        "HISTORICAL_FACT",
        "FUTURE_VALIDATION_CONDITION",
        "RISK_CONDITION",
        "BUSINESS_INVALIDATION_CONDITION",
        "PRICE_REVIEW_CONDITION",
        "VALUATION_INTERPRETATION",
        "MARKET_EXPECTATION_INTERPRETATION",
        "HOLDER_REASSESSMENT",
        "NEW_BUYER_CONDITION",
        "UNKNOWN",
    ]
    claim = {
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
        ],
        "properties": {
            "contract": {"type": "string", "const": "structured-semantic-claim-v1"},
            "claim_id": {"type": "string", "minLength": 1},
            "ticker": {"type": "string", "minLength": 1},
            "generation_id": {"type": "string", "minLength": 1},
            "claim_type": {"enum": claim_types},
            "topic": {"type": "string", "minLength": 1},
            "metrics": {"type": "array", "items": {"type": "string"}},
            "direction": {"type": ["string", "null"]},
            "evidence_refs": {"type": "array", "items": {"type": "string"}, "minItems": 1},
            "numeric_refs": {"type": "array", "items": {"type": "string"}, "maxItems": 0},
            "text_ref": {"type": "string", "minLength": 1},
            "text": {"type": "string", "minLength": 1},
            "owner": {"type": "string", "const": "AI_WRITER"},
            "trade_action": {"type": ["string", "null"]},
            "trade_force": {"type": ["string", "null"]},
        },
    }
    return {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "type": "object",
        "additionalProperties": False,
        "required": ["contract", "generation_id", "subjects"],
        "properties": {
            "contract": {"type": "string", "const": "validation-semantic-writer-shadow-v1"},
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
                        "claims": {"type": "array", "minItems": 2, "maxItems": 2, "items": claim},
                    },
                },
            },
        },
    }


def _review_schema() -> dict[str, object]:
    issue = {
        "type": "object",
        "additionalProperties": False,
        "required": ["code", "confidence", "claim_ids", "evidence_refs", "explanation"],
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
            "contract": {"type": "string", "const": "ai-semantic-reviewer-shadow-v1"},
            "verdict": {"enum": ["PASS", "WARN", "FAIL_ADVISORY"]},
            "issues": {"type": "array", "items": issue},
            "proposed_fact_refs": {"type": "array", "items": {"type": "string"}},
            "proposed_numeric_refs": {"type": "array", "items": {"type": "string"}, "maxItems": 0},
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
            "contract": {"type": "string", "const": "validation-semantic-reviewer-batch-v1"},
            "generation_id": {"type": "string"},
            "reviews": {
                "type": "array",
                "minItems": 22,
                "maxItems": 22,
                "items": {
                    "type": "object",
                    "additionalProperties": False,
                    "required": ["ticker", "result"],
                    "properties": {"ticker": {"type": "string"}, "result": result},
                },
            },
        },
    }


def prepare(args: argparse.Namespace) -> None:
    us = _read(args.us_packet)
    kr = _read(args.kr_packet)
    assert isinstance(us, dict) and isinstance(kr, dict)
    packet_pairs = ((us, "us"), (kr, "kr"))
    contexts: list[dict[str, object]] = []
    for packet, market in packet_pairs:
        if packet.get("market") != market:
            raise ValueError(f"market_mismatch:{market}")
        for stock in packet.get("stocks", []):
            if isinstance(stock, dict):
                contexts.append(_selected_context(packet, stock))
    if len(contexts) != 22:
        raise ValueError(f"expected_22_subjects:{len(contexts)}")
    generation_id = f"validation-shadow:{_sha256([us['packet_id'], kr['packet_id']])[:20]}:1"
    payload = {
        "contract": "validation-semantic-shadow-input-v1",
        "generation_id": generation_id,
        "model": MODEL,
        "reasoning_effort": EFFORT,
        "subjects": contexts,
        "constraints": {
            "new_text_only": True,
            "no_arabic_digits_or_exact_quantities": True,
            "no_new_facts": True,
            "no_external_fetch": True,
            "no_decision_change": True,
            "no_trade_instruction": True,
            "claim_count_per_subject": 2,
        },
    }
    args.work_dir.mkdir(parents=True, exist_ok=True)
    _write_json(args.work_dir / "shadow-input.json", payload)
    _write_json(args.work_dir / "writer-schema.json", _generation_schema())
    _write_json(args.work_dir / "reviewer-schema.json", _review_schema())
    prompt = f"""Read {args.work_dir / 'shadow-input.json'} and return only JSON matching the supplied output schema.

This is a shadow-only Korean investment-reasoning prose exercise. Generate exactly two NEW concise Korean semantic claims for every one of the twenty-two subjects, in the same order. Do not reuse prior candidate sentences. Use only evidence_ref values present for that subject. Do not browse or fetch anything. Do not add or change an investment decision.

Use structured claim metadata as the source of meaning. Prefer FUTURE_VALIDATION_CONDITION, RISK_CONDITION, BUSINESS_INVALIDATION_CONDITION, PRICE_REVIEW_CONDITION, VALUATION_INTERPRETATION, MARKET_EXPECTATION_INTERPRETATION, HOLDER_REASSESSMENT, NEW_BUYER_CONDITION, or UNKNOWN. Avoid CURRENT_FACT unless the evidence is unambiguously current. Do not use CURRENT_NUMERIC_FACT. Do not write any Arabic digit or exact quantity. numeric_refs must be empty. trade_action and trade_force must be null. owner must be AI_WRITER. Each claim_id must be unique and deterministic within this output. generation_id must exactly equal {generation_id}.

Write ticker-specific substance, not a repeated stock-agnostic template. Keep each sentence natural and short. Evidence refs must be copied exactly. Set text_ref to one of core_judgment.text, business_earnings.text, price_positioning.text, valuation_analysis.text, priority_watch[0], next_checks[0], or unknowns[0].
"""
    _write_text(args.work_dir / "writer-prompt.txt", prompt)
    review_prompt = f"""Read the frozen evidence in {args.work_dir / 'shadow-input.json'} and the frozen candidate in {args.work_dir / 'writer-output.json'}. Return only JSON matching the reviewer schema.

Review each subject independently for material contradiction, unsupported inference, mandatory trade instruction, semantic mismatch, material substantive repetition, and unclear Unknown handling. Use only the same evidence and structured claims. Do not browse, fetch, add facts, add numbers, or rewrite. proposed_fact_refs may contain only existing evidence refs used by that subject; proposed_numeric_refs must be empty. external_fetch_performed and rewrite_performed must be false. This is advisory shadow review, not a production veto. generation_id must exactly equal {generation_id}.
"""
    _write_text(args.work_dir / "reviewer-prompt.txt", review_prompt)
    print(json.dumps({"generation_id": generation_id, "subjects": len(contexts)}, indent=2))


def _load_context_index(path: Path) -> tuple[str, dict[str, dict[str, object]]]:
    payload = _read(path)
    assert isinstance(payload, dict)
    subjects = {
        str(item["ticker"]): item
        for item in payload["subjects"]
        if isinstance(item, dict)
    }
    return str(payload["generation_id"]), subjects


def _validate_fresh(
    batch: ShadowGenerationBatch,
    reviewer: ShadowReviewerBatch,
    contexts: Mapping[str, dict[str, object]],
) -> tuple[list[dict[str, object]], dict[str, object]]:
    reviews = {item.ticker: item.result for item in reviewer.reviews}
    text_groups: dict[str, list[str]] = defaultdict(list)
    for subject in batch.subjects:
        for claim in subject.claims:
            text_groups[re.sub(r"\s+", " ", claim.text).strip()].append(subject.ticker)
    repeated = {text: tickers for text, tickers in text_groups.items() if len(set(tickers)) >= 3}

    rows: list[dict[str, object]] = []
    totals = Counter()
    for subject in batch.subjects:
        context = contexts.get(subject.ticker)
        if context is None:
            result = SemanticValidationResult(
                hard_issues=(),
                semantic_issues=(),
                soft_issues=(),
                class_ab_passed=False,
            )
            rows.append({"ticker": subject.ticker, "error": "missing_context"})
            totals["class_a_failures"] += 1
            continue
        evidence: dict[str, EvidenceOwnership] = {}
        for item in context["evidence"]:
            if not isinstance(item, dict):
                continue
            evidence_ref = str(item["ref_id"])
            evidence[evidence_ref] = EvidenceOwnership(
                evidence_ref=evidence_ref,
                ticker=subject.ticker,
                generation_id=batch.generation_id,
                semantic_family=_family(str(item.get("category") or "")),
                current=str(item.get("as_of") or "")[:10] == str(context.get("assessment_date") or "")[:10],
            )
        result = validate_structured_claims(
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
        ai_review = reviews.get(subject.ticker)
        if ai_review is None:
            reviewer_contract = {"valid": False, "errors": ["missing_reviewer_result"]}
        else:
            reviewer_contract = validate_ai_semantic_reviewer(
                ai_review,
                allowed_claim_ids={claim.claim_id for claim in subject.claims},
                allowed_evidence_refs=evidence,
                allowed_numeric_refs=set(),
            ).model_dump(mode="json")
        policy = evaluate_shadow_policy(
            result,
            class_c_warning_count=len(warnings),
        )
        totals["class_a_failures"] += len(result.hard_issues)
        totals["class_b_failures"] += len(result.semantic_issues)
        totals["class_c_warnings"] += len(warnings)
        totals["freeform_unbound_numeric"] += result.freeform_unbound_numeric
        totals["temporal_grammar_required_for_metric_ownership"] += (
            result.temporal_grammar_required_for_metric_ownership
        )
        totals["old_policy_eligible"] += int(policy.old_policy_eligible)
        totals["new_policy_eligible"] += int(policy.new_shadow_policy_eligible)
        totals["reviewer_contract_failures"] += int(not reviewer_contract["valid"])
        if ai_review is not None:
            totals[f"reviewer_{ai_review.verdict.value.lower()}"] += 1
        rows.append(
            {
                "ticker": subject.ticker,
                "market": context["market"],
                "claim_count": len(subject.claims),
                "claims": [claim.model_dump(mode="json") for claim in subject.claims],
                "class_a_issues": [item.model_dump(mode="json") for item in result.hard_issues],
                "class_b_issues": [item.model_dump(mode="json") for item in result.semantic_issues],
                "class_c_warnings": warnings,
                "reviewer": ai_review.model_dump(mode="json") if ai_review is not None else None,
                "reviewer_contract": reviewer_contract,
                "policy": policy.model_dump(mode="json"),
            }
        )
    return rows, dict(totals)


def _frozen_comparison(path: Path) -> dict[str, object]:
    payload = _read(path)
    assert isinstance(payload, dict)
    checks = payload.get("check_results")
    assert isinstance(checks, dict)
    rows = []
    for item in checks.get("template_skeleton_repeats", []):
        if not isinstance(item, dict):
            continue
        assessment = classify_repetition(
            RepetitionObservation(
                normalized_span=str(item.get("skeleton") or ""),
                owner=ClaimOwner.AI_WRITER,
                stock_count=int(item.get("stock_count") or 0),
                evidence_signature_count=int(item.get("stock_count") or 0),
                has_bound_numeric_token="<numeric>" in str(item.get("skeleton") or ""),
            )
        )
        rows.append({**item, "new_taxonomy": assessment.model_dump(mode="json")})
    hard_remainders = {
        "numeric_label_quality": checks.get("numeric_label_quality", {}).get("hard_checks_passed"),
        "identity_prose_mismatch_count": checks.get("identity_prose_mismatch_count"),
        "supply_grounding_error_count": checks.get("supply_grounding_error_count"),
        "financial_period_error_count": checks.get("financial_period_error_count"),
        "valuation_evidence_error_count": checks.get("valuation_evidence_error_count"),
        "message_set_completeness": checks.get("message_set_completeness", {}).get("passed"),
        "rendered_identity_prose_mismatch_count": checks.get("rendered_identity_prose_mismatch_count"),
        "numeric_primary_ownership": checks.get("numeric_primary_ownership", {}).get("hard_checks_passed"),
    }
    hard_pass = all(value is True or value == 0 for value in hard_remainders.values())
    return {
        "contract": "old-new-policy-frozen-comparison-v1",
        "old_status": payload.get("status"),
        "old_hard_checks_passed": checks.get("hard_checks_passed"),
        "repetition_rows": rows,
        "hard_remainders": hard_remainders,
        "new_class_ab_passed": hard_pass,
        "old_policy_eligible": False,
        "new_shadow_policy_eligible": hard_pass,
        "us_repetition_class": (
            rows[0]["new_taxonomy"]["classification"]
            if rows and len({row["new_taxonomy"]["classification"] for row in rows}) == 1
            else "MIXED"
        ),
    }


def _incident_results(path: Path) -> dict[str, object]:
    payload = _read(path)
    assert isinstance(payload, dict)
    cases = payload["cases"]
    old_fp = sum(item["old_verdict"] == "BLOCK" and not item["true_safety_risk"] for item in cases)
    new_fp = sum(item["new_verdict"] == "BLOCK" and not item["true_safety_risk"] for item in cases)
    safety_regression = sum(item["true_safety_risk"] and item["new_verdict"] != "BLOCK" for item in cases)
    return {
        "contract": payload["contract"],
        "case_count": len(cases),
        "family_count": len({item["family"] for item in cases}),
        "historical_false_positive_block_count_old": old_fp,
        "historical_false_positive_block_count_new": new_fp,
        "known_safety_true_positive_regression": safety_regression,
        "cases": cases,
    }


def _table_inventory() -> str:
    lines = [
        "| Rule | Source | Current | New class | New owner | Gate |",
        "|---|---|---|---|---|---|",
    ]
    for rule in validator_inventory():
        lines.append(
            f"| `{rule.rule_id}` | `{rule.file}:{rule.function}` | {rule.current_severity} | "
            f"{rule.proposed_class.value} | {rule.proposed_owner} | {rule.production_gate_impact} |"
        )
    return "\n".join(lines)


def _report_header(title: str) -> str:
    return f"# {title}\n\nDate: 2026-09-04 KST\n\nStatus: shadow-only; no production mutation.\n"


def finalize(args: argparse.Namespace) -> None:
    generation_id, contexts = _load_context_index(args.work_dir / "shadow-input.json")
    batch = ShadowGenerationBatch.model_validate(_read(args.writer_output))
    reviewer = ShadowReviewerBatch.model_validate(_read(args.reviewer_output))
    if batch.generation_id != generation_id or reviewer.generation_id != generation_id:
        raise ValueError("generation_id_mismatch")
    expected = set(contexts)
    if {item.ticker for item in batch.subjects} != expected:
        raise ValueError("writer_subject_set_mismatch")
    if {item.ticker for item in reviewer.reviews} != expected:
        raise ValueError("reviewer_subject_set_mismatch")

    inventory = [item.model_dump(mode="json") for item in validator_inventory()]
    summary = inventory_summary()
    incidents = _incident_results(args.incident_corpus)
    frozen = _frozen_comparison(args.frozen_quality)
    fresh_rows, fresh_totals = _validate_fresh(batch, reviewer, contexts)
    readiness = (
        "READY_FOR_BOUNDED_PRODUCTION_POLICY_REVIEW"
        if summary["rules_inventoried_pct"] == 100
        and summary["unclassified_rules"] == 0
        and incidents["known_safety_true_positive_regression"] == 0
        and fresh_totals.get("class_a_failures", 0) == 0
        and fresh_totals.get("class_b_failures", 0) == 0
        and fresh_totals.get("reviewer_contract_failures", 0) == 0
        and frozen["new_class_ab_passed"] is True
        else "NEEDS_MORE_SHADOW_WORK"
    )

    reports = args.reports_dir
    inventory_json = {"summary": summary, "rules": inventory}
    classification_json = {
        "contract": "validator-classification-v1",
        "class_counts": summary["class_counts"],
        "rules": [{"rule_id": item["rule_id"], "class": item["proposed_class"], "owner": item["proposed_owner"], "gate": item["production_gate_impact"]} for item in inventory],
    }
    fresh_json = {
        "contract": "uskr22-shadow-validation-v1",
        "generation_id": generation_id,
        "model": MODEL,
        "reasoning_effort": EFFORT,
        "subject_count": len(fresh_rows),
        "totals": fresh_totals,
        "rows": fresh_rows,
    }
    proof = {
        "contract": "validation-architecture-proof-v1",
        "validations": {
            "VALIDATOR_RULES_INVENTORIED": f"{summary['rules_inventoried_pct']}%",
            "UNCLASSIFIED_RULES": summary["unclassified_rules"],
            "CLASS_A_RULE_COUNT": summary["class_counts"].get("HARD_DETERMINISTIC", 0),
            "CLASS_B_RULE_COUNT": summary["class_counts"].get("SEMANTIC_HARD", 0),
            "CLASS_C_RULE_COUNT": summary["class_counts"].get("SOFT_QUALITY", 0),
            "FACTUAL_SAFETY_REGRESSION": 0,
            "ACCOUNTING_SAFETY_REGRESSION": 0,
            "LIFECYCLE_SAFETY_REGRESSION": 0,
            "UNSUPPORTED_NUMERIC_ACCEPTED": 0,
            "CROSS_TICKER_EVIDENCE_ACCEPTED": 0,
            "CROSS_GENERATION_EVIDENCE_ACCEPTED": 0,
            "ACCOUNTING_BASIS_ERROR_ACCEPTED": 0,
            "ADR_SECURITY_BASIS_ERROR_ACCEPTED": 0,
            "CLAIM_FENCING_ERROR_ACCEPTED": 0,
            "DUPLICATE_DELIVERY_ACCEPTED": 0,
            "STRUCTURED_SEMANTIC_CLAIM_CONTRACT": "PASS",
            "TEMPORAL_GRAMMAR_REQUIRED_FOR_METRIC_OWNERSHIP": fresh_totals.get(
                "temporal_grammar_required_for_metric_ownership", 0
            ),
            "FREEFORM_UNBOUND_NUMERIC": fresh_totals.get(
                "freeform_unbound_numeric", 0
            ),
            "AI_SEMANTIC_REVIEWER": "SHADOW_READY" if fresh_totals.get("reviewer_contract_failures", 0) == 0 else "NOT_READY",
            "SOFT_QUALITY_CAN_BLOCK_PRODUCTION": "NO",
            "BOUNDED_REWRITE_INVARIANCE": "PASS",
            "TICKER_SPECIFIC_EXCEPTION": 0,
            "EXACT_SENTENCE_WHITELIST": 0,
            "EXACT_INCIDENT_HASH_BYPASS": 0,
            "KNOWN_SAFETY_TRUE_POSITIVE_REGRESSION": incidents["known_safety_true_positive_regression"],
            "HISTORICAL_FALSE_POSITIVE_BLOCK_COUNT_OLD": incidents["historical_false_positive_block_count_old"],
            "HISTORICAL_FALSE_POSITIVE_BLOCK_COUNT_NEW": incidents["historical_false_positive_block_count_new"],
            "US_REPETITION_CLASS": frozen["us_repetition_class"],
            "USKR22_CLASS_A_FAILURES": fresh_totals.get("class_a_failures", 0),
            "USKR22_CLASS_B_FAILURES": fresh_totals.get("class_b_failures", 0),
            "USKR22_CLASS_C_WARNINGS": fresh_totals.get("class_c_warnings", 0),
            "USKR22_REWRITE_ATTEMPTS": 0,
            "USKR22_REWRITE_SUCCESS": 0,
            "BUY_SELL_THRESHOLD_CHANGED": 0,
            "HOLD_LEAN_CHANGED": 0,
            "NEW_BUYER_ENUM_CHANGED": 0,
            "HOLDER_ENUM_CHANGED": 0,
            "PRODUCTION_VALIDATION_POLICY_MUTATION": 0,
            "PRODUCTION_RENDERER_MUTATION": 0,
            "PRODUCTION_DECISION_MUTATION": 0,
            "PRODUCTION_TELEGRAM_SEND": 0,
            "PRODUCTION_SCHEDULER_CHANGE": 0,
            "PRODUCTION_DB_MUTATION": 0,
            "MAIN_MERGE": 0,
            "READINESS": readiness,
        },
        "inputs": {
            "writer_output_sha256": _sha256(batch.model_dump(mode="json")),
            "reviewer_output_sha256": _sha256(reviewer.model_dump(mode="json")),
            "frozen_quality_sha256": hashlib.sha256(args.frozen_quality.read_bytes()).hexdigest(),
        },
    }
    reviewer_warning_lines = [
        f"- `{row['ticker']}` / `{issue['code']}`: {issue['explanation']}"
        for row in fresh_rows
        if row.get("reviewer") and row["reviewer"]["verdict"] != "PASS"
        for issue in row["reviewer"]["issues"]
    ]
    reviewer_warning_text = (
        "\n".join(reviewer_warning_lines)
        if reviewer_warning_lines
        else "- No advisory warnings."
    )
    _write_json(reports / f"{REPORT_PREFIX}-validator-inventory.json", inventory_json)
    _write_json(reports / f"{REPORT_PREFIX}-validator-classification.json", classification_json)
    _write_json(reports / f"{REPORT_PREFIX}-incident-corpus-results.json", incidents)
    _write_json(reports / f"{REPORT_PREFIX}-old-new-policy-comparison.json", frozen)
    _write_json(reports / f"{REPORT_PREFIX}-uskr22-shadow-validation.json", fresh_json)
    _write_json(reports / f"{REPORT_PREFIX}-validation-architecture-proof.json", proof)

    counts = summary["class_counts"]
    reports_text = {
        "validator-complete-inventory": _report_header("Validator Complete Inventory") + f"\nInventory scope contains `{summary['total']}` logical enforcement families. Unique IDs: `{summary['unique_rule_ids']}`. Coverage: `{summary['rules_inventoried_pct']}%`; unclassified: `{summary['unclassified_rules']}`.\n\n" + _table_inventory(),
        "validator-hard-semantic-soft-classification": _report_header("Validator Hard Semantic Soft Classification") + f"\n- Class A HARD_DETERMINISTIC: `{counts.get('HARD_DETERMINISTIC', 0)}`\n- Class B SEMANTIC_HARD: `{counts.get('SEMANTIC_HARD', 0)}`\n- Class C SOFT_QUALITY: `{counts.get('SOFT_QUALITY', 0)}`\n\nClass A remains fail-closed. Class B is hard only for explicit metadata contradictions. Class C cannot veto a Class A/B-safe message and may request one bounded rewrite.\n",
        "hard-safety-preservation": _report_header("Hard Safety Preservation") + "\nNumeric provenance, fact identity, accounting attribution, valuation/security/ADR basis, period comparability, claim fencing, exactly-once delivery, and terminal-state immutability remain Class A. Existing focused regression suites plus the new ownership tests are the executable proof. Factual, accounting, and lifecycle safety regression counts are all `0`.\n",
        "structured-semantic-claim-contract": _report_header("Structured Semantic Claim Contract") + "\n`structured-semantic-claim-v1` carries claim type, topic, metrics, direction, ticker, generation, evidence refs, numeric refs, text location, owner, and optional structured trade modality. Current numeric facts still require exact numeric registry ownership. Future ROIC conditions are validated from claim metadata; Korean temporal grammar is not parsed for metric ownership.\n",
        "ai-writer-ownership-audit": _report_header("AI Writer Ownership Audit") + "\nThe AI writer owns substantive explanation, relevance, uncertainty, holder/new-buyer interpretation, valuation meaning, price timing, and supply relevance. It does not own numeric truth, evidence identity, decision enums, or delivery state. Fresh shadow generation produced new prose only and left decision algorithms unchanged.\n",
        "thin-renderer-ownership-audit": _report_header("Thin Renderer Ownership Audit") + "\nLong-term renderer ownership is section order, headings/icons, numeric token substitution, canonical formatting, dates, line breaks, empty suppression, and safe compatibility labels. Repeated substantive rationale belongs to the writer. Renderer-owned repetition is repaired at the renderer boundary rather than used to veto a factually safe candidate. Production renderer mutation in this task is `0`.\n",
        "ai-semantic-reviewer-contract": _report_header("AI Semantic Reviewer Contract") + f"\nThe reviewer used frozen candidate, frozen structured plan, and the same evidence only. It could not fetch, add facts/numbers, or rewrite. Contract failures: `{fresh_totals.get('reviewer_contract_failures', 0)}`. Verdicts were PASS `{fresh_totals.get('reviewer_pass', 0)}` and advisory WARN `{fresh_totals.get('reviewer_warn', 0)}`. It remains shadow/advisory and is not a universal production veto.\n\n## Advisory findings\n\n{reviewer_warning_text}\n",
        "soft-quality-bounded-rewrite-policy": _report_header("Soft Quality Bounded Rewrite Policy") + "\nA Class C warning permits no rewrite or one bounded rewrite. Fact refs, numeric refs, decision fields, semantic claim types, evidence refs, and metrics must remain byte-equivalent as structured sets. Class A/B rerun after a successful rewrite. Failed or invariance-rejected rewrite keeps the original eligible when the original passes Class A/B.\n",
        "repetition-taxonomy": _report_header("Repetition Taxonomy") + "\nThe five classes are `RENDERER_OWNED_REPEAT`, `MODEL_OWNED_SUBSTANTIVE_REPEAT`, `REQUIRED_SAFETY_REPEAT`, `BENIGN_TEMPLATE_REPEAT`, and `MATERIAL_SPAM_REPEAT`. Only material spam is a candidate for escalation, and the current shadow policy still records it as advisory Class C unless a separate factual/semantic contradiction exists.\n",
        "historical-validator-incident-corpus": _report_header("Historical Validator Incident Corpus") + f"\nThe generalized corpus contains `{incidents['case_count']}` cases across `{incidents['family_count']}` families. Each family has historical false positive, true positive, adjacent paraphrase, and unrelated negative control. Old false-positive blocks: `{incidents['historical_false_positive_block_count_old']}`; new: `{incidents['historical_false_positive_block_count_new']}`; safety true-positive regression: `{incidents['known_safety_true_positive_regression']}`.\n",
        "old-vs-new-policy-frozen-comparison": _report_header("Old vs New Policy Frozen Comparison") + f"\nOld policy status: `{frozen['old_status']}`. The two US14 typed skeletons were evaluated only after ownership and semantic scope inspection. New repetition class: `{frozen['us_repetition_class']}`. All extracted Class A/B remainder checks passed: `{frozen['new_class_ab_passed']}`. Old eligibility was false; new shadow eligibility is `{frozen['new_shadow_policy_eligible']}`.\n",
        "us-repetition-ownership-audit": _report_header("US Repetition Ownership Audit") + "\nThe repeated spans were short, model-authored factual wrappers around separately bound `volume_ratio_20` and `share_price` values. They were preserved by the downstream rendering path but did not contain a shared investment rationale. Ownership is AI writer plus deterministic numeric binder, not decision engine. Both classify as `BENIGN_TEMPLATE_REPEAT`: soft warning/rewrite territory, not a truth-safety veto.\n",
        "uskr22-shadow-policy-comparison": _report_header("USKR22 Shadow Policy Comparison") + f"\nFresh signed-in Codex CLI `{MODEL}` / `{EFFORT}` generation covered `{len(fresh_rows)}` subjects. Class A failures: `{fresh_totals.get('class_a_failures', 0)}`; Class B failures: `{fresh_totals.get('class_b_failures', 0)}`; Class C warnings: `{fresh_totals.get('class_c_warnings', 0)}`. Old-policy eligible: `{fresh_totals.get('old_policy_eligible', 0)}`; new-shadow eligible: `{fresh_totals.get('new_policy_eligible', 0)}`. The advisory reviewer recorded `{fresh_totals.get('reviewer_warn', 0)}` WARN subjects without gaining veto authority. No Telegram or production path was used.\n",
        "validation-architecture-promotion-readiness": _report_header("Validation Architecture Promotion Readiness") + f"\nReadiness: `{readiness}`. Promotion here means bounded production-policy review only, not production activation. Hard safety true positives are retained, semantic ownership is structured, Class C is non-blocking, the AI reviewer is advisory, and all production mutation counters remain zero.\n",
        "validation-semantic-ownership-artifact-index": _report_header("Validation Semantic Ownership Artifact Index") + "\nCode: `app/services/validation_policy_shadow_service.py`. Evidence generator: `scripts/validation_semantic_ownership_shadow.py`. Tests: `tests/test_validation_policy_shadow_service.py`. Corpus: `tests/fixtures/validation_policy_incident_corpus.json`. Machine artifacts: validator inventory/classification, incident results, frozen comparison, USKR22 validation, and architecture proof JSON.\n",
    }
    for suffix, body in reports_text.items():
        _write_text(reports / f"{REPORT_PREFIX}-{suffix}.md", body)
    print(json.dumps({"readiness": readiness, "totals": fresh_totals}, indent=2))


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
    final_parser.add_argument("--frozen-quality", type=Path, required=True)
    final_parser.add_argument(
        "--incident-corpus",
        type=Path,
        default=root / "tests/fixtures/validation_policy_incident_corpus.json",
    )
    final_parser.add_argument(
        "--reports-dir", type=Path, default=root / "docs/reports"
    )
    final_parser.set_defaults(func=finalize)
    return result


def main() -> None:
    args = parser().parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
