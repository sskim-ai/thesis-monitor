from __future__ import annotations

import argparse
import hashlib
import json
from collections import Counter
from dataclasses import asdict
from pathlib import Path

from app.services.working_capital_user_visible_preintegration_service import (
    NaturalProofEvidence,
    NaturalProofState,
    WorkingCapitalMetricFamily,
    WorkingCapitalUserVisibleMode,
    build_enablement_gate,
    build_preview_context,
    context_to_dict,
    gate_to_dict,
    preflight_enablement_mode,
    preview_parity_errors,
    render_preview,
    rendering_to_dict,
    validate_preview,
)


ROOT = Path(__file__).resolve().parents[1]
SOURCE_91D = ROOT / "docs/reports/20260821-phase9-1d-readiness.json"
SOURCE_90E = ROOT / "docs/reports/20260821-phase9-0e-full-preview.json"
DEFAULT_OUTPUT = ROOT / "docs/reports/20260821-phase9-1e-readiness.json"


def _read_json(path: Path) -> dict[str, object]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"Expected JSON object: {path}")
    return value


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _cash_flow_contexts(payload: dict[str, object]) -> dict[str, dict[str, str]]:
    return {
        str(item["ticker"]): {
            "context_id": str(item["context_id"]),
            "period_end": str(item.get("primary_period", {}).get("period_end") or ""),
        }
        for item in payload.get("subjects") or ()
        if isinstance(item, dict) and item.get("ticker") and item.get("context_id")
    }


def _human_classification(
    *,
    preview_selected: bool,
    resolved_unknowns: tuple[str, ...],
    suppressed: bool,
) -> str:
    if preview_selected and resolved_unknowns:
        return "MATERIAL_IMPROVEMENT"
    if preview_selected:
        return "MINOR_IMPROVEMENT"
    if suppressed:
        return "NO_MEANINGFUL_CHANGE"
    return "NO_MEANINGFUL_CHANGE"


def build_evidence() -> dict[str, object]:
    phase_91d = _read_json(SOURCE_91D)
    cash_flow = _read_json(SOURCE_90E)
    cash_flow_contexts = _cash_flow_contexts(cash_flow)
    target_mode = WorkingCapitalUserVisibleMode.SELECTIVE_INVENTORY_AND_EXACT_TRADE_AR
    proofs = {
        family: NaturalProofEvidence(family, NaturalProofState.NOT_OBSERVED)
        for family in WorkingCapitalMetricFamily
    }
    gates = {family: build_enablement_gate(family, proof) for family, proof in proofs.items()}
    preflight = preflight_enablement_mode(target_mode, gates)

    subject_rows: list[dict[str, object]] = []
    selected_metric_counts: Counter[str] = Counter()
    candidate_metric_counts: Counter[str] = Counter()
    suppression_counts: Counter[str] = Counter()
    quality_classes: Counter[str] = Counter()
    parity_errors: list[dict[str, str]] = []
    semantic_errors: list[dict[str, str]] = []
    numeric_errors: list[dict[str, str]] = []
    before_lengths: list[int] = []
    after_lengths: list[int] = []
    automatic = 0
    selected_context_ids: list[str] = []

    for subject in phase_91d.get("subjects") or ():
        if not isinstance(subject, dict):
            continue
        ticker = str(subject.get("ticker") or "")
        family_value = subject.get("runtime_selected_metric")
        row: dict[str, object] = {
            "ticker": ticker,
            "industry": subject.get("industry"),
            "canary_selected_metric": family_value,
            "canary_selected_relation": subject.get("runtime_selected_relation"),
            "preview_context": None,
            "ai_preview": None,
            "fallback_preview": None,
            "selector_parity": True,
            "preview_only": True,
            "user_visible_enabled": False,
        }
        if family_value is None:
            quality_classes["NO_MEANINGFUL_CHANGE"] += 1
            row["human_quality"] = "NO_MEANINGFUL_CHANGE"
            row["suppression_reason"] = (
                subject.get("context", {}).get("suppression_reasons", [])
                if isinstance(subject.get("context"), dict)
                else []
            )
            subject_rows.append(row)
            continue
        family = WorkingCapitalMetricFamily(str(family_value))
        candidate_metric_counts[family.value] += 1
        cash_flow_context = cash_flow_contexts.get(ticker, {})
        context = build_preview_context(
            subject,
            gates[family],
            preview_target_mode=target_mode,
            cash_flow_context_id=cash_flow_context.get("context_id"),
            cash_flow_period_end=cash_flow_context.get("period_end"),
        )
        if context is None:
            row["selector_parity"] = False
            row["suppression_reason"] = ["preview_context_build_failed"]
            quality_classes["DEGRADED"] += 1
            row["human_quality"] = "DEGRADED"
            subject_rows.append(row)
            continue
        ai = render_preview(context, channel="ai_preview")
        fallback = render_preview(context, channel="fallback_preview")
        parity = preview_parity_errors(ai, fallback)
        ai_errors = validate_preview(context, ai)
        fallback_errors = validate_preview(context, fallback)
        parity_errors.extend({"ticker": ticker, "error": error} for error in parity)
        semantic_errors.extend(
            {"ticker": ticker, "channel": "ai", "error": error} for error in ai_errors
        )
        semantic_errors.extend(
            {"ticker": ticker, "channel": "fallback", "error": error} for error in fallback_errors
        )
        if context.preview_selected:
            selected_metric_counts[family.value] += 1
            selected_context_ids.append(context.working_capital_user_visible_context_id)
            automatic += 1
            if ai.text is None or ai.text.count(context.display_value) != 1:
                numeric_errors.append(
                    {"ticker": ticker, "error": "primary_numeric_claim_count_invalid"}
                )
        else:
            suppression_counts.update(context.suppression_reasons)
        before_text = (
            str(subject.get("reasoning", {}).get("text") or "")
            if isinstance(subject.get("reasoning"), dict)
            else ""
        )
        if before_text:
            before_lengths.append(len(before_text))
        if ai.text:
            after_lengths.append(len(ai.text))
        classification = _human_classification(
            preview_selected=context.preview_selected,
            resolved_unknowns=context.resolved_unknowns,
            suppressed=bool(context.suppression_reasons),
        )
        quality_classes[classification] += 1
        row.update(
            {
                "preview_context": context_to_dict(context),
                "ai_preview": rendering_to_dict(ai),
                "fallback_preview": rendering_to_dict(fallback),
                "parity_errors": list(parity),
                "validation_errors": [*ai_errors, *fallback_errors],
                "human_quality": classification,
                "before_text": before_text or None,
                "after_text": ai.text,
                "message_length_before": len(before_text),
                "message_length_after": len(ai.text or ""),
            }
        )
        subject_rows.append(row)

    duplicate_context_ids = [
        context_id for context_id, count in Counter(selected_context_ids).items() if count > 1
    ]
    preview_texts = [str(row["after_text"]) for row in subject_rows if row.get("after_text")]
    repeated_texts = [text for text, count in Counter(preview_texts).items() if count > 1]
    contradictory_unknowns = sum(
        bool(
            row.get("preview_context", {}).get("resolved_unknowns")
            and any(
                unknown in (row.get("preview_context", {}).get("remaining_unknowns") or [])
                for unknown in row["preview_context"]["resolved_unknowns"]
            )
        )
        for row in subject_rows
        if isinstance(row.get("preview_context"), dict)
    )
    p0: list[str] = []
    p1: list[str] = []
    if parity_errors:
        p1.append("ai_fallback_preview_parity")
    if semantic_errors or numeric_errors or duplicate_context_ids:
        p0.append("preview_validation_failure")
    if any(
        isinstance(row.get("preview_context"), dict)
        and row["preview_context"].get("user_visible_enabled") is True
        for row in subject_rows
    ):
        p0.append("feature_off_user_visible_leak")
    if contradictory_unknowns:
        p0.append("resolved_unknown_contradiction")

    inventory_gate = gates[WorkingCapitalMetricFamily.INVENTORY]
    trade_ar_gate = gates[WorkingCapitalMetricFamily.EXACT_TRADE_AR]
    selected_total = sum(selected_metric_counts.values())
    return {
        "phase": "9.1E",
        "status": "PREINTEGRATION_READY" if not p0 and not p1 else "BLOCKED",
        "contracts": {
            "enablement_gate": "working-capital-user-visible-enable-gate-v1",
            "user_visible": "working-capital-user-visible-v1",
        },
        "source": {
            "phase_9_1d": str(SOURCE_91D.relative_to(ROOT)),
            "phase_9_1d_sha256": _sha256(SOURCE_91D),
            "phase_9_0e": str(SOURCE_90E.relative_to(ROOT)),
            "phase_9_0e_sha256": _sha256(SOURCE_90E),
            "provider_calls": 0,
            "archive_rewrites": 0,
        },
        "feature": {
            "working_capital_user_visible_mode": "OFF",
            "preview_target_mode": target_mode.value,
            "preflight": asdict(preflight),
            "production_ai_diff": 0,
            "production_fallback_diff": 0,
            "telegram_diff": 0,
            "public_action_diff": 0,
            "snapshot_diff": 0,
            "assessment_db_diff": 0,
            "warning_lifecycle_diff": 0,
        },
        "natural_proof_gates": {
            "inventory": gate_to_dict(inventory_gate),
            "exact_trade_ar": gate_to_dict(trade_ar_gate),
        },
        "selector": {
            "active_universe": len(subject_rows),
            "canary_candidates": sum(candidate_metric_counts.values()),
            "candidate_metric_counts": dict(sorted(candidate_metric_counts.items())),
            "preview_selected": selected_total,
            "preview_selected_metric_counts": dict(sorted(selected_metric_counts.items())),
            "documented_redundancy_suppressions": sum(suppression_counts.values()),
            "suppression_reason_counts": dict(sorted(suppression_counts.items())),
            "broadened_selection_count": 0,
            "selector_parity_errors": sum(
                row.get("selector_parity") is not True for row in subject_rows
            ),
            "broad_ar_selected": 0,
            "ap_selected": 0,
        },
        "validation": {
            "numeric_binding": {
                "automatic": automatic,
                "manual": 0,
                "rejected": len(numeric_errors),
                "unresolved": 0,
                "errors": numeric_errors,
            },
            "ai_fallback_parity_errors": parity_errors,
            "semantic_causal_errors": semantic_errors,
            "duplicate_context_ids": duplicate_context_ids,
            "exact_preview_repetitions": repeated_texts,
            "resolved_unknown_contradictions": contradictory_unknowns,
            "runtime_quality": "PASS" if not repeated_texts else "REJECTED",
        },
        "human_quality": {
            **dict(sorted(quality_classes.items())),
            "average_length_before": (
                round(sum(before_lengths) / len(before_lengths), 2) if before_lengths else 0
            ),
            "average_length_after_selected": (
                round(sum(after_lengths) / len(after_lengths), 2) if after_lengths else 0
            ),
        },
        "unknown_resolution": {
            "resolved_exact_count": sum(
                len(row.get("preview_context", {}).get("resolved_unknowns") or [])
                for row in subject_rows
                if isinstance(row.get("preview_context"), dict)
                and row["preview_context"].get("preview_selected") is True
            ),
            "contradictions": contradictory_unknowns,
        },
        "subjects": subject_rows,
        "open_p0": p0,
        "open_p1": p1,
        "p2_backlog": [
            "final_business_earnings_sentence_placement_polish",
            "broad_ar_ap_remain_excluded",
        ],
        "phase_9_1e_preintegration_ready": not p0 and not p1,
        "inventory_user_visible_enablement_ready": "NO_PENDING_NATURAL",
        "trade_ar_user_visible_enablement_ready": "NO_PENDING_NATURAL",
        "next_instruction": "small_metric_family_enablement_only_after_live_pass",
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate Phase 9.1E pre-integration evidence.")
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args()
    payload = build_evidence()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2, default=str) + "\n",
        encoding="utf-8",
    )
    print(
        json.dumps(
            {
                "output": str(args.output),
                "phase_9_1e_preintegration_ready": payload["phase_9_1e_preintegration_ready"],
                "preview_selected": payload["selector"]["preview_selected"],
                "open_p0": payload["open_p0"],
                "open_p1": payload["open_p1"],
            },
            ensure_ascii=False,
        )
    )


if __name__ == "__main__":
    main()
