from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.services.free_analyst_message_service import (  # noqa: E402
    cross_message_synthesis_specificity_report,
    entity_specific_synthesis_report,
)
from app.services.free_analyst_production_integration_service import (  # noqa: E402
    build_production_candidate,
    select_limited_canary,
)
from scripts.kiwoom_kr_enriched_replay import build_replay as build_kr_replay  # noqa: E402


def _load(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"expected JSON object: {path}")
    return value


def _safety_totals(rows: list[dict[str, object]]) -> dict[str, int]:
    keys = (
        "fact_mismatch",
        "unsupported_causality",
        "temporal_violations",
        "trade_ar_leak",
        "hidden_arithmetic",
        "external_knowledge",
        "material_information_loss",
        "entity_owner_mismatch",
        "ticker_owner_mismatch",
        "market_owner_mismatch",
        "packet_owner_mismatch",
        "support_ref_owner_mismatch",
        "industry_context_mismatch",
    )
    return {
        key: sum(int((row.get("safety") or {}).get(key) or 0) for row in rows)
        for key in keys
    }


def _us_replay(baseline: dict[str, Any]) -> dict[str, object]:
    candidates = []
    rows: list[dict[str, object]] = []
    before_messages: list[dict[str, object]] = []
    for row in baseline["messages"]:
        source = str(row["enriched_pre_quality"])
        reference = str(row["deterministic_reference"])
        candidate = build_production_candidate(
            source,
            deterministic_text=reference,
            message_key=str(row["message_key"]),
            market="us",
            packet_owner=str(baseline["packet_id"]),
            is_market_digest=bool(row["is_market_digest"]),
        )
        candidates.append(candidate)
        industry_owner = (
            candidate.result.analysis.industry_context_owner
            if candidate.result is not None
            else "general"
        )
        specificity = (candidate.quality_v2 or {}).get("entity_specific_synthesis") or {}
        before_text = str(row["enriched_post_quality_v2"])
        before_specificity = (
            entity_specific_synthesis_report(
                before_text,
                support_text=f"{source}\n\n{reference}",
                selected_renderer=str(row.get("selected_renderer") or ""),
            )
            if not row["is_market_digest"]
            else None
        )
        if not row["is_market_digest"]:
            before_messages.append(
                {
                    "message_key": row["message_key"],
                    "industry_owner": industry_owner,
                    "text": before_text,
                    "specific_support_available": specificity.get(
                        "specific_support_available", False
                    ),
                    "supported_discriminators": specificity.get(
                        "supported_discriminators", []
                    ),
                }
            )
        if row["is_market_digest"] or before_text == candidate.candidate_text:
            human_quality = "GOOD_CURRENT_STATE"
        elif specificity.get("status") == "PASS":
            human_quality = "MINOR_IMPROVEMENT"
        else:
            human_quality = "REGRESSION"
        rows.append(
            {
                "ticker": row["ticker"],
                "message_key": row["message_key"],
                "is_market_digest": row["is_market_digest"],
                "pre_repair": before_text,
                "post_repair": candidate.candidate_text,
                "deterministic_reference": reference,
                "eligible": candidate.eligible,
                "errors": list(candidate.errors),
                "selected_renderer": candidate.selected_renderer,
                "industry_owner": industry_owner,
                "specificity_before": before_specificity,
                "specificity_after": specificity or None,
                "quality_v2": candidate.quality_v2,
                "safety": candidate.result.safety if candidate.result else {},
                "human_quality": human_quality,
            }
        )
    selection = select_limited_canary(candidates)
    selected = set(selection.selected_keys)
    for row in rows:
        row["canary_selected"] = row["message_key"] in selected
    before_cross = cross_message_synthesis_specificity_report(before_messages)
    after_cross = selection.specificity_audit
    before_rejected = set(before_cross["rejected_message_keys"])
    after_rejected = set(after_cross["rejected_message_keys"])
    for row in rows:
        key = str(row["message_key"])
        if key in before_rejected and key not in after_rejected:
            row["human_quality"] = "MATERIAL_IMPROVEMENT"
        elif (
            row["human_quality"] == "MINOR_IMPROVEMENT"
            and (row.get("specificity_before") or {}).get("status") == "PASS"
            and key not in before_rejected
        ):
            row["human_quality"] = "GOOD_CURRENT_STATE"
    return {
        "contract": "us-entity-specific-replay-v1",
        "packet_id": baseline["packet_id"],
        "packet_immutable": True,
        "message_count": len(rows),
        "eligible_count": sum(bool(row["eligible"]) for row in rows),
        "before_cross_message_specificity": before_cross,
        "after_cross_message_specificity": after_cross,
        "safety_totals": _safety_totals(rows),
        "human_quality": {
            label: sum(row["human_quality"] == label for row in rows)
            for label in (
                "MATERIAL_IMPROVEMENT",
                "MINOR_IMPROVEMENT",
                "GOOD_CURRENT_STATE",
                "NO_MEANINGFUL_CHANGE",
                "REGRESSION",
            )
        },
        "canary_selection": selection.to_dict(),
        "messages": rows,
    }


def build_evidence(
    *,
    kr_packet: dict[str, Any],
    kr_baseline: dict[str, Any],
    kr_evidence: dict[str, Any],
    us_baseline: dict[str, Any],
) -> dict[str, object]:
    kr = build_kr_replay(kr_packet, kr_baseline, kr_evidence)
    us = _us_replay(us_baseline)
    return {
        "contract": "kr-us-bounded-quality-evidence-v1",
        "archive_only": True,
        "provider_calls": 0,
        "production_mutations": 0,
        "kr": kr,
        "us": us,
    }


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Reproduce the bounded KR digest and US entity-specific quality repair."
    )
    parser.add_argument("--kr-packet", required=True, type=Path)
    parser.add_argument("--kr-baseline", required=True, type=Path)
    parser.add_argument("--kr-evidence", required=True, type=Path)
    parser.add_argument("--us-baseline", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    result = build_evidence(
        kr_packet=_load(args.kr_packet),
        kr_baseline=_load(args.kr_baseline),
        kr_evidence=_load(args.kr_evidence),
        us_baseline=_load(args.us_baseline),
    )
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True, default=str) + "\n",
        encoding="utf-8",
    )
    print(
        json.dumps(
            {
                "kr_messages": result["kr"]["message_count"],
                "kr_eligible": result["kr"]["eligible_count"],
                "us_messages": result["us"]["message_count"],
                "us_eligible": result["us"]["eligible_count"],
                "us_cross_message": result["us"][
                    "after_cross_message_specificity"
                ]["status"],
            },
            ensure_ascii=False,
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
