from __future__ import annotations

import argparse
import json
from pathlib import Path

from app.services.accepted_decision_consistency_service import (
    audit_accepted_decision_consistency,
)
from app.services.accepted_decision_v2_runtime_service import (
    AcceptedV2ProductionArtifact,
    AcceptedV2ProductionBaseline,
    AcceptedV2ProductionBlock,
    _production_message_quality,
)
from app.services.accepted_decision_v2_service import render_accepted_v2_production


DISCLAIMER = "※ 분석 분류이며 주문·자동매매·의무 매매 지시가 아닙니다."


def _load_prior(path: Path) -> dict[str, AcceptedV2ProductionBaseline]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    result: dict[str, AcceptedV2ProductionBaseline] = {}
    for row in payload["rows"]:
        plan = row["accepted_plan"]
        if plan["status"] != "READY":
            continue
        ticker = str(row["ticker"])
        result[ticker] = AcceptedV2ProductionBaseline(
            ticker=ticker,
            market=row["market"],
            accepted_decision=plan["accepted_decision"],
            evidence_sha256=row["evidence_fingerprint"],
            accepted_decision_id=plan["accepted_decision_id"],
            source=path.name,
        )
    return result


def build_proof(*, prior_path: Path, fresh_path: Path) -> dict[str, object]:
    prior_by_ticker = _load_prior(prior_path)
    artifact = AcceptedV2ProductionArtifact.model_validate_json(
        fresh_path.read_text(encoding="utf-8")
    )
    packets = {row.ticker: row for row in artifact.evidence_packets}
    rendered = tuple(
        render_accepted_v2_production(packets[plan.ticker], plan)
        for plan in artifact.accepted_plans
        if plan.accepted_decision is not None and plan.accepted_decision_id is not None
    )
    rendered_by_ticker = {row.ticker: row for row in rendered}
    blocks = tuple(
        AcceptedV2ProductionBlock(
            ticker=plan.ticker,
            decision=plan.accepted_decision,
            accepted_decision_id=str(plan.accepted_decision_id),
            text=rendered_by_ticker[plan.ticker].text,
        )
        for plan in artifact.accepted_plans
        if plan.accepted_decision is not None and plan.accepted_decision_id is not None
    )
    prior = tuple(
        prior_by_ticker[ticker]
        for ticker in artifact.selected_subjects
        if ticker in prior_by_ticker
    )
    audit = audit_accepted_decision_consistency(
        evidence_packets=artifact.evidence_packets,
        prior_accepted=prior,
        accepted_plans=artifact.accepted_plans,
        blocks=blocks,
    )
    fresh_text = "\n".join(row.text for row in blocks)
    legacy_text = "\n".join(row.text for row in artifact.blocks)
    quality = _production_message_quality(rendered)
    changed = [
        row.ticker for row in audit.diagnostics if row.accepted_decision_changed
    ]
    return {
        "contract": "four-track-decision-consistency-proof-v1",
        "status": audit.status,
        "source_prior": str(prior_path),
        "source_fresh": str(fresh_path),
        "subject_count": len(artifact.selected_subjects),
        "prior_comparable_count": len(prior),
        "new_without_prior_count": len(artifact.selected_subjects) - len(prior),
        "changed_accepted_tickers": changed,
        "common_disclaimer_occurrence_in_immutable_source": legacy_text.count(DISCLAIMER),
        "common_disclaimer_occurrence_after_repair": fresh_text.count(DISCLAIMER),
        "fresh_message_quality": quality,
        "unexplained_accepted_decision_drift": audit.unexplained_accepted_decision_drift,
        "raw_candidate_used_as_final": audit.raw_candidate_used_as_final,
        "daily_review_overrides_valid_v2_accepted": (
            audit.daily_review_overrides_valid_v2_accepted
        ),
        "diagnostics": [
            row.model_dump(mode="json") for row in audit.diagnostics
        ],
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--prior", type=Path, required=True)
    parser.add_argument("--fresh", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    proof = build_proof(prior_path=args.prior, fresh_path=args.fresh)
    args.output.write_text(
        json.dumps(proof, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(json.dumps({key: value for key, value in proof.items() if key != "diagnostics"}))
    return 0 if proof["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
