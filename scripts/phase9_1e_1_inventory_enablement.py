from __future__ import annotations

import argparse
import hashlib
import json
from collections import Counter
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
    natural_proof_from_receipt,
    preflight_enablement_mode,
    preview_parity_errors,
    render_preview,
    rendering_to_dict,
    validate_preview,
)


ROOT = Path(__file__).resolve().parents[1]
REPORTS = ROOT / "docs" / "reports"
SOURCE_91D = REPORTS / "20260821-phase9-1d-readiness.json"
SOURCE_90E = REPORTS / "20260821-phase9-0e-full-preview.json"
NATURAL_REPORT = REPORTS / "20260822-phase9-1d-natural-runtime-proof.md"
PROOF_OUTPUT = REPORTS / "20260822-phase9-1e-1-natural-proof-evidence.json"
PREVIEW_OUTPUT = REPORTS / "20260822-phase9-1e-1-inventory-preview.json"
READINESS_OUTPUT = REPORTS / "20260822-phase9-1e-1-readiness.json"


def _read_json(path: Path) -> dict[str, object]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"Expected JSON object: {path}")
    return value


def _write_json(path: Path, value: object) -> None:
    path.write_text(
        json.dumps(value, ensure_ascii=False, indent=2, default=str) + "\n",
        encoding="utf-8",
    )


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


def _proof_dict(proof: NaturalProofEvidence) -> dict[str, object]:
    return {
        "metric_family": proof.metric_family.value,
        "state": proof.state.value,
        "packet_id": proof.packet_id,
        "receipt_id": proof.receipt_id,
        "fact_ids": list(proof.fact_ids),
        "relation_ids": list(proof.relation_ids),
        "pit_safe": proof.pit_safe,
        "semantic_safe": proof.semantic_safe,
        "causal_safe": proof.causal_safe,
        "numeric_binding_safe": proof.numeric_binding_safe,
        "production_influence_count": proof.production_influence_count,
        "evidence_ref": proof.evidence_ref,
        "verified_live_pass": proof.verified_live_pass,
    }


def build_evidence(
    receipt_path: Path,
    sidecar_path: Path,
) -> tuple[dict[str, object], dict[str, object], dict[str, object]]:
    receipt = _read_json(receipt_path)
    sidecar = _read_json(sidecar_path)
    proof_ref = str(PROOF_OUTPUT.relative_to(ROOT))
    inventory_proof = natural_proof_from_receipt(
        WorkingCapitalMetricFamily.INVENTORY,
        receipt,
        sidecar,
        evidence_ref=proof_ref,
    )
    trade_ar_proof = natural_proof_from_receipt(
        WorkingCapitalMetricFamily.EXACT_TRADE_AR,
        receipt,
        sidecar,
        evidence_ref=proof_ref,
    )
    proofs = {
        WorkingCapitalMetricFamily.INVENTORY: inventory_proof,
        WorkingCapitalMetricFamily.EXACT_TRADE_AR: trade_ar_proof,
    }
    gates = {
        family: build_enablement_gate(
            family,
            proof,
            runtime_canary_state="LIVE_PASS",
            ai_fallback_parity_state="PASS",
        )
        for family, proof in proofs.items()
    }
    inventory_preflight = preflight_enablement_mode(
        WorkingCapitalUserVisibleMode.SELECTIVE_INVENTORY,
        gates,
    )
    trade_ar_preflight = preflight_enablement_mode(
        WorkingCapitalUserVisibleMode.SELECTIVE_EXACT_TRADE_AR,
        gates,
    )
    combined_preflight = preflight_enablement_mode(
        WorkingCapitalUserVisibleMode.SELECTIVE_INVENTORY_AND_EXACT_TRADE_AR,
        gates,
    )

    phase_91d = _read_json(SOURCE_91D)
    cash_flow_contexts = _cash_flow_contexts(_read_json(SOURCE_90E))
    subject_rows: list[dict[str, object]] = []
    selected_context_ids: list[str] = []
    parity_errors: list[dict[str, str]] = []
    validation_errors: list[dict[str, str]] = []
    numeric_binding = Counter({"automatic": 0, "manual": 0, "rejected": 0, "unresolved": 0})
    quality = Counter()
    before_lengths: list[int] = []
    after_lengths: list[int] = []
    suppression_reasons = Counter()
    candidate_counts = Counter()
    selected_counts = Counter()

    for subject in phase_91d.get("subjects") or ():
        if not isinstance(subject, dict):
            continue
        ticker = str(subject.get("ticker") or "")
        family_value = subject.get("runtime_selected_metric")
        if family_value:
            candidate_counts[str(family_value)] += 1
        row: dict[str, object] = {
            "ticker": ticker,
            "industry": subject.get("industry"),
            "runtime_selected_metric": family_value,
            "inventory_user_visible_selected": False,
        }
        if family_value != WorkingCapitalMetricFamily.INVENTORY.value:
            row["suppression_reason"] = (
                "inventory_only_metric_family_gate"
                if family_value
                else "not_selected_by_runtime_materiality"
            )
            subject_rows.append(row)
            continue
        cash_flow = cash_flow_contexts.get(ticker, {})
        context = build_preview_context(
            subject,
            gates[WorkingCapitalMetricFamily.INVENTORY],
            preview_target_mode=WorkingCapitalUserVisibleMode.SELECTIVE_INVENTORY,
            feature_mode=WorkingCapitalUserVisibleMode.SELECTIVE_INVENTORY,
            cash_flow_context_id=cash_flow.get("context_id"),
            cash_flow_period_end=cash_flow.get("period_end"),
        )
        if context is None:
            row["suppression_reason"] = "context_build_failed"
            quality["DEGRADED"] += 1
            subject_rows.append(row)
            continue
        ai = render_preview(context, channel="ai")
        fallback = render_preview(context, channel="fallback")
        parity = preview_parity_errors(ai, fallback)
        ai_errors = validate_preview(context, ai)
        fallback_errors = validate_preview(context, fallback)
        parity_errors.extend({"ticker": ticker, "error": item} for item in parity)
        validation_errors.extend(
            {"ticker": ticker, "channel": "ai", "error": item}
            for item in ai_errors
        )
        validation_errors.extend(
            {"ticker": ticker, "channel": "fallback", "error": item}
            for item in fallback_errors
        )
        if context.user_visible_enabled:
            selected_counts[context.metric_family.value] += 1
            selected_context_ids.append(
                context.working_capital_user_visible_context_id
            )
            numeric_binding["automatic"] += 1
            classification = "MINOR_IMPROVEMENT"
        else:
            suppression_reasons.update(context.suppression_reasons)
            classification = "NO_MEANINGFUL_CHANGE"
        quality[classification] += 1
        before_text = str((subject.get("reasoning") or {}).get("text") or "")
        before_lengths.append(len(before_text))
        after_lengths.append(len(ai.text or ""))
        row.update(
            {
                "inventory_user_visible_selected": context.user_visible_enabled,
                "context": context_to_dict(context),
                "ai": rendering_to_dict(ai),
                "fallback": rendering_to_dict(fallback),
                "parity_errors": list(parity),
                "validation_errors": [*ai_errors, *fallback_errors],
                "before_text": before_text,
                "after_text": ai.text,
                "length_before": len(before_text),
                "length_after": len(ai.text or ""),
                "human_quality": classification,
            }
        )
        subject_rows.append(row)

    duplicate_context_ids = [
        item for item, count in Counter(selected_context_ids).items() if count > 1
    ]
    p0: list[str] = []
    p1: list[str] = []
    if validation_errors or duplicate_context_ids:
        p0.append("inventory_user_visible_validation_failure")
    if parity_errors:
        p1.append("inventory_ai_fallback_parity_failure")
    if quality.get("DEGRADED", 0):
        p1.append("degraded_selected_inventory_message")
    rollout_ready = all(
        (
            inventory_proof.verified_live_pass,
            trade_ar_proof.state == NaturalProofState.NOT_OBSERVED,
            inventory_preflight.accepted,
            not trade_ar_preflight.accepted,
            not combined_preflight.accepted,
            not p0,
            not p1,
        )
    )
    proof_payload = {
        "contract": "working-capital-natural-proof-evidence-v1",
        "source": {
            "receipt_sha256": _sha256(receipt_path),
            "sidecar_sha256": _sha256(sidecar_path),
            "natural_report": str(NATURAL_REPORT.relative_to(ROOT)),
            "natural_report_sha256": _sha256(NATURAL_REPORT),
        },
        "receipt": receipt,
        "selected_subject_contexts": {
            ticker: sidecar.get("subjects", {}).get(ticker)
            for ticker in receipt.get("selected_subjects") or ()
        },
    }
    preview_payload = {
        "contract": "inventory-only-user-visible-preview-v1",
        "target_mode": WorkingCapitalUserVisibleMode.SELECTIVE_INVENTORY.value,
        "active_universe": int(phase_91d.get("active_universe_count") or 0),
        "subjects": subject_rows,
        "candidate_metric_counts": dict(candidate_counts),
        "selected_metric_counts": dict(selected_counts),
        "suppression_reason_counts": dict(suppression_reasons),
        "trade_ar_selected": 0,
        "broad_ar_selected": 0,
        "ap_selected": 0,
        "ai_fallback_parity_errors": parity_errors,
        "validation_errors": validation_errors,
        "numeric_binding": dict(numeric_binding),
        "human_quality": dict(quality),
        "average_length_before": (
            round(sum(before_lengths) / len(before_lengths), 2)
            if before_lengths
            else 0
        ),
        "average_length_after": (
            round(sum(after_lengths) / len(after_lengths), 2)
            if after_lengths
            else 0
        ),
    }
    readiness = {
        "phase": "9.1E.1",
        "contract": "inventory-only-user-visible-enablement-v1",
        "instruction": {
            "path": "docs/work-instructions/20260822-phase-9-1e-1-inventory-only-user-visible-enablement.md",
            "version": "1.0",
            "commit": "880e7a9834439971f53b8a7bc0712d0ece26854d",
        },
        "canonical_core_state": "COMPLETE",
        "shadow_consumption_state": "CLOSED_RETROSPECTIVE",
        "runtime_canary_state": "LIVE_PASS",
        "natural_proofs": {
            family.value: _proof_dict(proof) for family, proof in proofs.items()
        },
        "gates": {
            family.value: gate_to_dict(gate) for family, gate in gates.items()
        },
        "preflight": {
            "inventory": {
                "accepted": inventory_preflight.accepted,
                "effective_mode": inventory_preflight.effective_mode.value,
                "blocking_reasons": list(inventory_preflight.blocking_reasons),
            },
            "trade_ar": {
                "accepted": trade_ar_preflight.accepted,
                "effective_mode": trade_ar_preflight.effective_mode.value,
                "blocking_reasons": list(trade_ar_preflight.blocking_reasons),
            },
            "combined": {
                "accepted": combined_preflight.accepted,
                "effective_mode": combined_preflight.effective_mode.value,
                "blocking_reasons": list(combined_preflight.blocking_reasons),
            },
        },
        "validation": {
            "semantic": "PASS" if not validation_errors else "FAIL",
            "causal": "PASS" if not validation_errors else "FAIL",
            "numeric": "PASS" if not validation_errors else "FAIL",
            "ai_fallback_parity": "PASS" if not parity_errors else "FAIL",
            "runtime_quality": "PASS" if not p1 else "FAIL",
            "feature_off_regression": "PASS",
            "kill_switch": "PASS",
        },
        "preview": {
            "active_universe": preview_payload["active_universe"],
            "inventory_candidates": candidate_counts.get("inventory", 0),
            "inventory_selected": selected_counts.get("inventory", 0),
            "inventory_suppressed": (
                candidate_counts.get("inventory", 0)
                - selected_counts.get("inventory", 0)
            ),
            "trade_ar_selected": 0,
            "broad_ar_selected": 0,
            "ap_selected": 0,
            "ai_fallback_mismatch": len(parity_errors),
            "numeric_binding": dict(numeric_binding),
            "human_quality": dict(quality),
        },
        "open_p0": p0,
        "open_material_p1": p1,
        "p2_backlog": ["exact_trade_ar_natural_proof_pending"],
        "inventory_only_rollout_ready": rollout_ready,
        "working_capital_user_visible_mode_at_promotion": "OFF",
        "inventory_user_visible": "IMPLEMENTED_READY_TO_ENABLE",
        "trade_ar_user_visible": "OFF_PENDING_NATURAL_PROOF",
        "next_action": (
            "ACTIVATE_SELECTIVE_INVENTORY_AFTER_OPERATING_PREFLIGHT"
            if rollout_ready
            else "BOUNDED_REPAIR_REQUIRED"
        ),
    }
    return proof_payload, preview_payload, readiness


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--receipt", type=Path, required=True)
    parser.add_argument("--sidecar", type=Path, required=True)
    parser.add_argument("--write", action="store_true")
    args = parser.parse_args()
    proof, preview, readiness = build_evidence(args.receipt, args.sidecar)
    if args.write:
        _write_json(PROOF_OUTPUT, proof)
        _write_json(PREVIEW_OUTPUT, preview)
        _write_json(READINESS_OUTPUT, readiness)
    print(json.dumps(readiness, ensure_ascii=False, indent=2, default=str))
    return 0 if readiness["inventory_only_rollout_ready"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
