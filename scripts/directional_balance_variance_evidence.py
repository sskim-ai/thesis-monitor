from __future__ import annotations

import argparse
import asyncio
import json
from pathlib import Path

from app.services.accepted_decision_v2_runtime_service import (
    AcceptedV2ProductionBaseline,
    AcceptedV2ProductionContext,
    validate_accepted_v2_production_output,
)
from app.services.accepted_decision_v2_service import (
    AcceptedDecisionSource,
    AcceptedDecisionStatus,
)
from app.services.decision_canary_service import canonical_sha256
from app.services.directional_balance_variance_service import (
    SameEvidenceBalanceObservation,
    audit_same_evidence_balance_variance,
)
from scripts.v2_production_cutover_preflight import _codex_batch, _context


CONTRACT = "directional-balance-variance-evidence-v1"
US_CONTROLS = ("GOOGL",)
KR_CONTROLS = ("000660", "003690", "005930", "047810")


def _write_json(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(
        json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True, default=str) + "\n",
        encoding="utf-8",
    )
    temporary.replace(path)


def _subset_context(
    context: AcceptedV2ProductionContext,
    *,
    tickers: tuple[str, ...],
    claim_id: str,
) -> AcceptedV2ProductionContext:
    evidence = {row.ticker: row for row in context.evidence_packets}
    prior = {row.ticker: row for row in context.prior_accepted}
    missing = set(tickers) - set(evidence)
    if missing:
        raise ValueError("variance_control_ticker_missing:" + ",".join(sorted(missing)))
    return context.model_copy(
        update={
            "claim_id": claim_id,
            "selected_subjects": tickers,
            "evidence_packets": tuple(evidence[ticker] for ticker in tickers),
            "prior_accepted": tuple(prior[ticker] for ticker in tickers if ticker in prior),
        }
    )


def _calibrated_context(
    context: AcceptedV2ProductionContext,
    artifact: object,
) -> AcceptedV2ProductionContext:
    plans = {
        plan.ticker: plan
        for plan in getattr(artifact, "accepted_plans")
        if plan.status == AcceptedDecisionStatus.READY
    }
    if set(plans) != set(context.selected_subjects):
        raise ValueError("variance_calibration_not_ready_for_all_controls")
    packets = {row.ticker: row for row in context.evidence_packets}
    baselines = []
    for ticker in context.selected_subjects:
        plan = plans[ticker]
        if (
            plan.accepted_decision is None
            or plan.accepted_decision_id is None
            or plan.accepted_directional_balance is None
        ):
            raise ValueError(f"variance_calibration_balance_missing:{ticker}")
        baselines.append(
            AcceptedV2ProductionBaseline(
                ticker=ticker,
                market=context.market,
                accepted_decision=plan.accepted_decision,
                evidence_sha256=packets[ticker].evidence_sha256,
                accepted_decision_id=plan.accepted_decision_id,
                source="variance_calibration_accepted",
                accepted_directional_balance=plan.accepted_directional_balance,
                accepted_buy_drivers=plan.accepted_buy_drivers,
                accepted_sell_drivers=plan.accepted_sell_drivers,
                accepted_balance_summary=plan.accepted_balance_summary,
            )
        )
    return context.model_copy(update={"prior_accepted": tuple(baselines)})


def _valid_adjudication(plan: object) -> bool:
    return bool(
        getattr(plan, "adjudication_status") == "FINAL"
        and getattr(plan, "adjudication_id")
        and getattr(plan, "accepted_source")
        in {
            AcceptedDecisionSource.ADJUDICATION_KEEP_V1,
            AcceptedDecisionSource.ADJUDICATION_KEEP_V2,
        }
    )


async def _run(args: argparse.Namespace) -> None:
    args.output_dir.mkdir(parents=True, exist_ok=True)
    controls = (("us", args.us_packet, US_CONTROLS), ("kr", args.kr_packet, KR_CONTROLS))
    combined: dict[str, object] = {}
    for market, packet_path, tickers in controls:
        market_dir = args.output_dir / market
        full = await _context(packet_path, claim_id=f"variance-{market}-20260903")
        context = _subset_context(
            full,
            tickers=tickers,
            claim_id=f"variance-{market}-20260903",
        )
        calibration_dir = market_dir / "calibration"
        calibration_output = _codex_batch(
            context,
            output_dir=calibration_dir,
            timeout=args.timeout,
            state_namespace=f"{context.claim_id}-calibration",
        )
        calibration_artifact = validate_accepted_v2_production_output(context, calibration_output)
        _write_json(
            calibration_dir / "candidate-output.json",
            calibration_output.model_dump(mode="json"),
        )
        _write_json(
            calibration_dir / "accepted-artifact.json",
            calibration_artifact.model_dump(mode="json"),
        )
        frozen = _calibrated_context(context, calibration_artifact)
        _write_json(market_dir / "frozen-context.json", frozen.model_dump(mode="json"))
        candidate_input_sha256 = canonical_sha256(frozen.model_dump(mode="json"))
        observations: dict[str, list[SameEvidenceBalanceObservation]] = {
            ticker: [] for ticker in tickers
        }
        run_rows = []
        for run_number in range(1, args.runs + 1):
            run_id = f"fresh-{run_number}"
            run_dir = market_dir / run_id
            output = _codex_batch(
                frozen,
                output_dir=run_dir,
                timeout=args.timeout,
                state_namespace=f"{frozen.claim_id}-{run_id}",
            )
            artifact = validate_accepted_v2_production_output(frozen, output)
            _write_json(run_dir / "candidate-output.json", output.model_dump(mode="json"))
            _write_json(run_dir / "accepted-artifact.json", artifact.model_dump(mode="json"))
            plans = {plan.ticker: plan for plan in artifact.accepted_plans}
            candidates = {row.ticker: row for row in output.candidates}
            packets = {row.ticker: row for row in frozen.evidence_packets}
            for ticker in tickers:
                plan = plans[ticker]
                candidate = candidates[ticker]
                if (
                    plan.status != AcceptedDecisionStatus.READY
                    or plan.accepted_decision is None
                    or plan.accepted_directional_balance is None
                ):
                    raise ValueError(f"variance_fresh_run_not_ready:{run_id}:{ticker}")
                observations[ticker].append(
                    SameEvidenceBalanceObservation(
                        run_id=run_id,
                        ticker=ticker,
                        packet_id=frozen.packet_id,
                        evidence_sha256=packets[ticker].evidence_sha256,
                        candidate_input_sha256=candidate_input_sha256,
                        candidate_decision=candidate.decision,
                        candidate_directional_balance=candidate.directional_balance,
                        accepted_decision=plan.accepted_decision,
                        accepted_directional_balance=plan.accepted_directional_balance,
                        adjudication_required=plan.material_disagreement,
                        valid_adjudication=_valid_adjudication(plan),
                        adjudication_id=plan.adjudication_id,
                    )
                )
            run_rows.append(
                {
                    "run_id": run_id,
                    "artifact_status": artifact.status,
                    "ready_count": artifact.ready_count,
                    "not_ready_count": artifact.not_ready_count,
                }
            )
        audits = {
            ticker: audit_same_evidence_balance_variance(tuple(rows))
            for ticker, rows in observations.items()
        }
        combined[market] = {
            "packet_id": frozen.packet_id,
            "candidate_input_sha256": candidate_input_sha256,
            "controls": list(tickers),
            "runs": run_rows,
            "observations": {
                ticker: [row.model_dump(mode="json") for row in rows]
                for ticker, rows in observations.items()
            },
            "audits": {ticker: audit.model_dump(mode="json") for ticker, audit in audits.items()},
        }
    boundary_crosses = sum(
        audit["candidate_label_boundary_cross_count"]
        for market in combined.values()
        for audit in market["audits"].values()
    )
    unexplained = sum(
        audit["unexplained_same_evidence_accepted_drift"]
        for market in combined.values()
        for audit in market["audits"].values()
    )
    result = {
        "contract": CONTRACT,
        "status": "PASS" if unexplained == 0 else "FAIL",
        "fresh_execution_count_per_control": args.runs,
        "same_evidence_label_boundary_cross_count": boundary_crosses,
        "unexplained_same_evidence_accepted_drift": unexplained,
        "production_model_majority_voting": 0,
        "production_recipient_send": 0,
        "production_delivery_state_mutation": 0,
        "markets": combined,
    }
    _write_json(args.output_dir / "variance-summary.json", result)
    print(json.dumps(result, ensure_ascii=False, sort_keys=True))
    if result["status"] != "PASS":
        raise ValueError("same_evidence_variance_readiness_failed")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--us-packet", type=Path, required=True)
    parser.add_argument("--kr-packet", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--runs", type=int, default=3)
    parser.add_argument("--timeout", type=int, default=900)
    args = parser.parse_args()
    if args.runs < 3:
        raise ValueError("at_least_three_fresh_executions_required")
    asyncio.run(_run(args))


if __name__ == "__main__":
    main()
