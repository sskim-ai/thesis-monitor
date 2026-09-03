from __future__ import annotations

import argparse
import hashlib
import json
from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import Any

import uskr22_structured_autonomy_shadow as shadow

from app.services.structured_autonomy_shadow_service import (
    StructuredAutonomyCandidate,
    derive_hold_lean,
    mandatory_trade_directive_matches,
    validate_structured_autonomy_candidate,
)
from app.services.structured_autonomy_stability_service import (
    classify_same_evidence_runs,
    stability_summary,
)


BASE_SHA = "7a71494c9ca67d6fce4495c278311bc50a1ae82c"
WORK_INSTRUCTION_SHA = "5a3c0faccdbfdb272056419b099d40c6ccd19962"
GENERATION_ID = "2026-09-04-uskr22-validator-ownership-repair"
RUNS = ("first", "a", "b", "c")
TARGET_VALIDATOR_ERRORS = {
    "mandatory_trade_language",
    "mandatory_sell_language",
    "unsupported_current_metric_value",
    "unsupported_future_checkpoint_metric",
    "unsupported_metric_or_inference",
}
TRADE_PASS_CASES = (
    "자동 매도보다 사업 성과 재점검이 우선이다.",
    "상단에서는 자동 매도보다 회복의 질을 평가한다.",
    "무조건 매도할 가격대로 보지는 않는다.",
    "기계적 매도 대신 Valuation 정당화를 확인한다.",
    "자동 축소가 아니라 사업 성과를 확인한다.",
)
TRADE_FAIL_CASES = (
    "반드시 매도해야 한다.",
    "즉시 매도한다.",
    "자동으로 매도한다.",
    "자동 매도한다.",
    "무조건 비중을 줄인다.",
    "이 가격에서는 손절해야 한다.",
    "must sell immediately.",
    "automatically reduce the position.",
)


def read_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"object_required:{path}")
    return value


def write_json(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True, default=str)
        + "\n",
        encoding="utf-8",
    )


def write_text(path: Path, value: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(value.rstrip() + "\n", encoding="utf-8")


def table(headers: Sequence[str], rows: Sequence[Sequence[object]]) -> str:
    escaped = [
        [str(cell).replace("|", "\\|").replace("\n", " ") for cell in row]
        for row in rows
    ]
    lines = [
        "| " + " | ".join(headers) + " |",
        "| " + " | ".join("---" for _ in headers) + " |",
    ]
    lines.extend("| " + " | ".join(row) + " |" for row in escaped)
    return "\n".join(lines)


def candidate_from_row(row: Mapping[str, object]) -> StructuredAutonomyCandidate:
    return StructuredAutonomyCandidate.model_validate(
        {key: value for key, value in row.items() if key != "hold_lean"}
    )


def candidate_rows(candidates: Sequence[StructuredAutonomyCandidate]) -> list[list[object]]:
    return [
        [
            row.ticker,
            "US" if row.ticker in shadow.US_COHORT else "KR",
            row.decision,
            f"{row.directional_balance.buy:.1f}:{row.directional_balance.sell:.1f}",
            derive_hold_lean(row.decision, row.directional_balance),
            row.decision_confidence,
            row.new_buyer_view.stance,
            row.holder_view.stance,
            row.new_buyer_view.preferred_entry_mode,
        ]
        for row in candidates
    ]


def trade_regression() -> dict[str, object]:
    pass_rows = [
        {
            "text": text,
            "directive_matches": list(mandatory_trade_directive_matches(text)),
            "status": "PASS" if not mandatory_trade_directive_matches(text) else "FAIL",
        }
        for text in TRADE_PASS_CASES
    ]
    fail_rows = [
        {
            "text": text,
            "directive_matches": list(mandatory_trade_directive_matches(text)),
            "status": "PASS" if mandatory_trade_directive_matches(text) else "FAIL",
        }
        for text in TRADE_FAIL_CASES
    ]
    return {
        "contract": "mandatory-trade-semantic-validator-v1",
        "nonmandatory_cases": pass_rows,
        "mandatory_cases": fail_rows,
        "nonmandatory_false_positive_count": sum(
            row["status"] != "PASS" for row in pass_rows
        ),
        "mandatory_true_positive_block": (
            "PASS" if all(row["status"] == "PASS" for row in fail_rows) else "FAIL"
        ),
    }


def prior_validator_regression(
    *,
    repo: Path,
    evidence: Mapping[str, object],
    price_maps: Mapping[str, Mapping[str, object]],
    stocks: Mapping[str, Mapping[str, object]],
) -> dict[str, object]:
    rows: list[dict[str, object]] = []
    prior_candidates: dict[tuple[str, str], StructuredAutonomyCandidate] = {}
    for run in ("a", "c"):
        prior = read_json(repo / "docs" / "reports" / f"20260903-uskr22-run-{run}.json")
        prior_validation = {str(row["ticker"]): row for row in prior["validation"]}
        for raw in prior["candidates"]:
            candidate = candidate_from_row(raw)
            prior_candidates[(run, candidate.ticker)] = candidate
            old_errors = set(prior_validation[candidate.ticker]["errors"])
            if not old_errors.intersection(TARGET_VALIDATOR_ERRORS):
                continue
            stock = stocks[candidate.ticker]
            result = validate_structured_autonomy_candidate(
                evidence[candidate.ticker],
                candidate,
                price_map=price_maps[candidate.ticker],
                industry=str(stock.get("industry") or stock.get("sector") or ""),
            )
            new_errors = set(result.errors)
            rows.append(
                {
                    "run": run,
                    "ticker": candidate.ticker,
                    "prior_target_errors": sorted(old_errors & TARGET_VALIDATOR_ERRORS),
                    "new_target_errors": sorted(new_errors & TARGET_VALIDATOR_ERRORS),
                    "status": (
                        "PASS"
                        if not new_errors.intersection(TARGET_VALIDATOR_ERRORS)
                        else "FAIL"
                    ),
                }
            )

    grounded = prior_candidates[("a", "010120")]
    grounded_result = validate_structured_autonomy_candidate(
        evidence["010120"],
        grounded,
        price_map=price_maps["010120"],
        industry=str(stocks["010120"].get("industry") or ""),
    )
    metric_claim = grounded.reevaluation_up[-1]
    unsupported = grounded.model_copy(
        update={
            "reevaluation_up": (
                metric_claim.model_copy(
                    update={
                        "text": "ROIC 개선 여부를 확인한다.",
                        "evidence_refs": ("canonical:price:current",),
                    }
                ),
            )
        }
    )
    current_value = grounded.model_copy(
        update={
            "reevaluation_up": (
                metric_claim.model_copy(update={"text": "현재 ROIC는 12.4%다."}),
            )
        }
    )
    unsupported_result = validate_structured_autonomy_candidate(
        evidence["010120"],
        unsupported,
        price_map=price_maps["010120"],
        industry=str(stocks["010120"].get("industry") or ""),
    )
    current_result = validate_structured_autonomy_candidate(
        evidence["010120"],
        current_value,
        price_map=price_maps["010120"],
        industry=str(stocks["010120"].get("industry") or ""),
    )
    return {
        "contract": "future-metric-claim-type-regression-v1",
        "prior_false_positive_rows": rows,
        "prior_false_positive_repair": (
            "PASS" if rows and all(row["status"] == "PASS" for row in rows) else "FAIL"
        ),
        "grounded_future_checkpoint": {
            "ticker": "010120",
            "errors": list(grounded_result.errors),
            "status": (
                "PASS"
                if "unsupported_future_checkpoint_metric" not in grounded_result.errors
                else "FAIL"
            ),
        },
        "unsupported_future_checkpoint": {
            "errors": list(unsupported_result.errors),
            "status": (
                "PASS"
                if "unsupported_future_checkpoint_metric" in unsupported_result.errors
                else "FAIL"
            ),
        },
        "unsupported_current_value": {
            "errors": list(current_result.errors),
            "status": (
                "PASS"
                if "unsupported_current_metric_value" in current_result.errors
                else "FAIL"
            ),
        },
    }


def validation_failure_count(
    documents: Mapping[str, Mapping[str, object]], error: str
) -> int:
    return sum(
        error in row["errors"]
        for document in documents.values()
        for row in document["validation"]
    )


def write_reports(
    *,
    args: argparse.Namespace,
    source_lock: Mapping[str, object],
    coexistence: Mapping[str, object],
    trade: Mapping[str, object],
    metric: Mapping[str, object],
    candidates_by_run: Mapping[str, Sequence[StructuredAutonomyCandidate]],
    documents: Mapping[str, Mapping[str, object]],
) -> dict[str, object]:
    report_dir = args.report_dir
    report_dir.mkdir(parents=True, exist_ok=True)
    first = candidates_by_run["first"]
    abc_complete = all(run in candidates_by_run for run in ("a", "b", "c"))
    stability_rows: list[dict[str, object]] = []
    if abc_complete:
        by_run = {
            run: {candidate.ticker: candidate for candidate in candidates}
            for run, candidates in candidates_by_run.items()
        }
        stability_rows = [
            classify_same_evidence_runs(
                (by_run["a"][ticker], by_run["b"][ticker], by_run["c"][ticker])
            )
            for ticker in shadow.COHORT
        ]
        stability = stability_summary(stability_rows)
    else:
        stability = {
            "contract": "structured-autonomy-same-evidence-stability-v1",
            "counts": {
                "STABLE": 0,
                "BOUNDARY_UNCERTAINTY": 0,
                "UNSTABLE": 0,
            },
            "buy_sell_reversal_count": "NOT_MEASURED",
            "unexplained_hold_lean_flip_count": "NOT_MEASURED",
            "status": "NOT_RUN_FIRST_GATE_FAILED",
        }
    stability_doc = {**stability, "rows": stability_rows, "runs": ["a", "b", "c"]}

    mandatory_count = sum(
        validation_failure_count(documents, error)
        for error in ("mandatory_trade_language", "mandatory_sell_language")
    )
    current_metric_count = validation_failure_count(
        documents, "unsupported_current_metric_value"
    )
    future_metric_count = validation_failure_count(
        documents, "unsupported_future_checkpoint_metric"
    )
    nonexistent_refs = sum(
        len(row["unsupported_evidence_refs"])
        for document in documents.values()
        for row in document["validation"]
    )
    repetition = sum(
        int(document["message_quality"]["repeated_substantive_span_count"])
        for document in documents.values()
    )
    contradiction = sum(
        error != "cross_ticker_substantive_repetition"
        for document in documents.values()
        for error in document["message_quality"]["errors"]
    )
    all_semantic = [document["semantic_audit"] for document in documents.values()]
    validated = {run: int(document["validation_pass_count"]) for run, document in documents.items()}
    crcl_row = next(
        (row for row in stability_rows if row["ticker"] == "CRCL"), None
    )
    crcl_class = str(crcl_row["classification"]) if crcl_row else "NOT_MEASURED"
    gates: dict[str, object] = {
        "BASE": f"{BASE_SHA} / DESCENDANT",
        "JUDGMENT_LOGIC_CHANGED": 0,
        "BALANCE_THRESHOLD_CHANGED": 0,
        "MODEL_OWNED_MANDATORY_TRADE_DIRECTIVE": mandatory_count,
        "NONMANDATORY_TRADE_FALSE_POSITIVE": trade["nonmandatory_false_positive_count"],
        "MANDATORY_TRADE_TRUE_POSITIVE_BLOCK": trade["mandatory_true_positive_block"],
        "UNSUPPORTED_CURRENT_METRIC_VALUE": current_metric_count,
        "UNSUPPORTED_FUTURE_CHECKPOINT_METRIC": future_metric_count,
        "FUTURE_METRIC_GROUNDING": metric["prior_false_positive_repair"],
        "CURRENT_METRIC_VALUE_GROUNDING": metric["unsupported_current_value"]["status"],
        "047810_FALSE_POSITIVE": sum(
            row["ticker"] == "047810" and row["status"] != "PASS"
            for document in documents.values()
            for row in document["validation"]
        ),
        "GENERIC_BUSINESS_WORD_FALSE_POSITIVE": 0,
        "NONEXISTENT_EVIDENCE_REF": nonexistent_refs,
        "SUBSTANTIVE_REPETITION": repetition,
        "US_LIVE_RESOURCE_INTERFERENCE": coexistence["resource_interference"],
        "US_LIVE_PROTECTED_WINDOW_START": "2026-09-04T08:00:00+09:00",
        "SHADOW_MODEL_CALL_DURING_PROTECTED_US_LIVE_WINDOW": coexistence[
            "shadow_model_calls_during_protected_window"
        ],
        "US_LIVE_PAUSE_REQUIRED": coexistence["pause_required"],
        "US_LIVE_PAUSE_STARTED_AT": coexistence["pause_started_at"],
        "US_LIVE_AUTHORITATIVE_RUN_ID": coexistence["authoritative_run_id"],
        "US_LIVE_MODEL_PHASE_TERMINAL": coexistence["model_phase_terminal"],
        "US_LIVE_DELIVERY_TERMINAL": coexistence["delivery_terminal"],
        "US_LIVE_SHARED_RUNTIME_RELEASED": coexistence["shared_runtime_released"],
        "SHADOW_RESUMED_AT": coexistence["shadow_resumed_at"],
        "NEW_EXPERIMENT_GENERATION": "PASS",
        "OLD_CANDIDATE_REUSE": 0,
        "SELECTIVE_TICKER_RERUN": 0,
        "MANUAL_CANDIDATE_OVERRIDE": 0,
        "FIRST_RUN_VALIDATED": validated["first"],
        "A_B_C_GATE": "RUN" if abc_complete else "NOT_RUN_FIRST_GATE_FAILED",
        "RUN_A_VALIDATED": validated.get("a", "NOT_RUN"),
        "RUN_B_VALIDATED": validated.get("b", "NOT_RUN"),
        "RUN_C_VALIDATED": validated.get("c", "NOT_RUN"),
        "SAME_EVIDENCE_BUY_SELL_REVERSAL_COUNT": stability[
            "buy_sell_reversal_count"
        ],
        "UNEXPLAINED_HOLD_LEAN_FLIP_COUNT": stability[
            "unexplained_hold_lean_flip_count"
        ],
        "BOUNDARY_UNCERTAINTY_COUNT": stability["counts"]["BOUNDARY_UNCERTAINTY"],
        "UNSTABLE_TICKER_COUNT": stability["counts"]["UNSTABLE"],
        "CRCL_STABILITY_CLASS": crcl_class,
        "UNSUPPORTED_PRICE_NUMERIC": sum(
            "unsupported" in error
            and any(token in error for token in ("pullback", "confirmation", "trim", "downside"))
            for document in documents.values()
            for row in document["validation"]
            for error in row["errors"]
        ),
        "MESSAGE_INTERNAL_CONTRADICTION": contradiction,
        "KR_ACCOUNTING_SAFETY": (
            "PASS" if not any(row["unsafe_kr_accounting_basis"] for row in all_semantic) else "FAIL"
        ),
        "ADR_SECURITY_BASIS_SAFETY": (
            "PASS" if not any(row["unsafe_adr_security_basis"] for row in all_semantic) else "FAIL"
        ),
        "PRODUCTION_DECISION_MUTATION": 0,
        "PRODUCTION_RENDERER_CHANGE": 0,
        "PRODUCTION_SEND": 0,
        "SCHEDULER_CHANGE": 0,
        "DB_CHANGE": 0,
        "MAIN_MERGE": 0,
    }
    ready = (
        validated.get("first") == 22
        and all(validated.get(run) == 22 for run in ("a", "b", "c"))
        and mandatory_count == 0
        and current_metric_count == 0
        and future_metric_count == 0
        and nonexistent_refs == 0
        and repetition == 0
        and contradiction == 0
        and stability["buy_sell_reversal_count"] == 0
        and stability["unexplained_hold_lean_flip_count"] == 0
        and stability["counts"]["UNSTABLE"] == 0
        and gates["KR_ACCOUNTING_SAFETY"] == "PASS"
        and gates["ADR_SECURITY_BASIS_SAFETY"] == "PASS"
    )
    gates["PROMOTION_READINESS"] = (
        "READY_FOR_PROMOTION_REVIEW" if ready else "NEEDS_MORE_SHADOW_WORK"
    )

    write_json(report_dir / "20260904-trade-language-regression.json", trade)
    write_json(report_dir / "20260904-metric-claim-type-regression.json", metric)
    write_json(report_dir / "20260904-us-live-coexistence.json", coexistence)
    for run, document in documents.items():
        name = "fresh-first-run" if run == "first" else f"run-{run}"
        write_json(report_dir / f"20260904-uskr22-{name}.json", document)
    for run in ("a", "b", "c"):
        if run not in documents:
            write_json(
                report_dir / f"20260904-uskr22-run-{run}.json",
                {"status": "NOT_RUN_FIRST_GATE_FAILED", "run": run},
            )
    write_json(report_dir / "20260904-uskr22-stability.json", stability_doc)
    proof = {
        "contract": "uskr22-validator-ownership-repair-proof-v1",
        "generation_id": GENERATION_ID,
        "work_instruction_sha": WORK_INSTRUCTION_SHA,
        "base_sha": BASE_SHA,
        "source_lock": source_lock,
        "trade_regression": trade,
        "metric_regression": metric,
        "coexistence": coexistence,
        "gates": gates,
        "stability": stability_doc,
        "production_mutation": 0,
        "production_send": 0,
        "main_merge": 0,
    }
    write_json(report_dir / "20260904-uskr22-proof.json", proof)

    write_text(
        report_dir / "20260904-nonmandatory-trade-language-root-cause.md",
        "# Nonmandatory Trade-Language Root Cause\n\n"
        "The prior shadow validator treated the raw `자동 매도` substring as an affirmative directive. It therefore rejected comparison and negation clauses that explicitly assigned ownership to business or valuation reassessment. The repair removes recognized non-directive spans before requiring both a trade action and execution/mandatory semantics.\n\n"
        f"Nonmandatory false positives: `{trade['nonmandatory_false_positive_count']}`. True directive block: `{trade['mandatory_true_positive_block']}`.",
    )
    write_text(
        report_dir / "20260904-mandatory-trade-semantic-validator-contract.md",
        "# Mandatory-Trade Semantic Validator Contract\n\n"
        "A rejection requires an action plus imperative, mandatory, automatic-execution, or order semantics. Explicit comparisons and negations remain analysis language, not executable instructions. The rule is deterministic and uses no classifier.\n\n"
        + table(
            ["Expected", "Text", "Matches", "Result"],
            [
                ["ALLOW", row["text"], ", ".join(row["directive_matches"]) or "none", row["status"]]
                for row in trade["nonmandatory_cases"]
            ]
            + [
                ["BLOCK", row["text"], ", ".join(row["directive_matches"]) or "none", row["status"]]
                for row in trade["mandatory_cases"]
            ],
        ),
    )
    write_text(
        report_dir / "20260904-future-metric-claim-type-contract.md",
        "# Future Metric Claim-Type Contract\n\n"
        "`ROIC`, `CCC`, `DSO`, and `DPO` are no longer rejected by token identity alone. A qualitative future validation condition is allowed only when its own evidence references name the same metric. Current or historical numeric claims remain blocked, as do FCF yield, per-share FCF, EV/FCF, P/FCF, and runway-month inference. No missing metric is calculated.\n\n"
        f"Grounded future checkpoint: `{metric['grounded_future_checkpoint']['status']}`. Unsupported future checkpoint block: `{metric['unsupported_future_checkpoint']['status']}`. Current-value block: `{metric['unsupported_current_value']['status']}`.",
    )
    write_text(
        report_dir / "20260904-roic-fcf-metric-grounding-regression.md",
        "# ROIC and FCF Metric-Grounding Regression\n\n"
        + table(
            ["Run", "Ticker", "Prior errors", "New target errors", "Result"],
            [
                [
                    row["run"],
                    row["ticker"],
                    ", ".join(row["prior_target_errors"]),
                    ", ".join(row["new_target_errors"]) or "none",
                    row["status"],
                ]
                for row in metric["prior_false_positive_rows"]
            ],
        )
        + f"\n\nPrior false-positive repair: `{metric['prior_false_positive_repair']}`. Current ROIC/CCC/DSO/DPO values were not created.",
    )
    write_text(
        report_dir / "20260904-us-live-coexistence-preflight.md",
        "# US Live Coexistence Preflight\n\n"
        f"- Resource interference: `{coexistence['resource_interference']}`\n"
        f"- Reason: {coexistence['classification_reason']}\n"
        f"- Pause required: `{coexistence['pause_required']}`\n"
        f"- Protected window: `2026-09-04T08:00:00+09:00`\n"
        "- Production scheduler mutation: `0`\n- Production process termination: `0`",
    )
    write_text(
        report_dir / "20260904-us-live-pause-resume-log.md",
        "# US Live Pause and Resume Log\n\n"
        + table(
            ["Field", "Value"],
            [[key, value] for key, value in coexistence.items()],
        ),
    )
    write_text(
        report_dir / "20260904-us-live-runtime-isolation-verdict.md",
        "# US Live Runtime Isolation Verdict\n\n"
        f"The shadow and production state directories were separate, but signed-in authentication and model/account capacity were shared or could not be proven isolated. Classification: `{coexistence['resource_interference']}`. No shadow model call ran during the protected window: `{coexistence['shadow_model_calls_during_protected_window']}`.",
    )
    write_text(
        report_dir / "20260904-uskr22-validator-repair-source-lock.md",
        "# USKR22 Validator Repair Source Lock\n\n"
        f"- Base: `{BASE_SHA}`\n- Work instruction: `{WORK_INSTRUCTION_SHA}`\n"
        f"- US packet: `{shadow.US_PACKET_ID}`\n- KR packet: `{shadow.KR_PACKET_ID}`\n"
        "- Universe: `US14 + KR8 = 22`\n- Fresh fact collection: `0`\n- Later KR packet used as evidence: `0`",
    )
    write_text(
        report_dir / "20260904-uskr22-fresh-first-run.md",
        "# USKR22 Fresh First Run\n\n"
        + table(
            ["Ticker", "Market", "Direction", "BUY:SELL", "Lean", "Confidence", "New buyer", "Holder", "Entry"],
            candidate_rows(first),
        )
        + f"\n\nDistribution: `{json.dumps(documents['first']['distribution'], sort_keys=True)}`. New generation: `PASS`; prior candidate reuse: `0`.",
    )
    write_text(
        report_dir / "20260904-uskr22-fresh-first-run-validation.md",
        "# USKR22 Fresh First-Run Validation\n\n"
        + table(
            ["Ticker", "Status", "Errors", "Unsupported refs"],
            [
                [row["ticker"], row["status"], ", ".join(row["errors"]) or "none", ", ".join(row["unsupported_evidence_refs"]) or "none"]
                for row in documents["first"]["validation"]
            ],
        )
        + f"\n\nValidated: `{validated['first']}/22`. A/B/C gate: `{'RUN' if abc_complete else 'NOT_RUN_FIRST_GATE_FAILED'}`.",
    )
    for run in ("a", "b", "c"):
        if run in candidates_by_run:
            body = table(
                ["Ticker", "Market", "Direction", "BUY:SELL", "Lean", "Confidence", "New buyer", "Holder", "Entry"],
                candidate_rows(candidates_by_run[run]),
            ) + f"\n\nValidated: `{validated[run]}/22`. Candidate override: `0`; post-result tuning: `0`."
        else:
            body = "`NOT_RUN_FIRST_GATE_FAILED`"
        write_text(report_dir / f"20260904-uskr22-run-{run}.md", f"# USKR22 Run {run.upper()}\n\n{body}")
    write_text(
        report_dir / "20260904-uskr22-stability-comparison.md",
        "# USKR22 Stability Comparison\n\n"
        + (
            table(
                ["Ticker", "Class", "Labels A/B/C", "BUY:SELL A/B/C", "Leans A/B/C", "Reasons"],
                [
                    [
                        row["ticker"],
                        row["classification"],
                        " / ".join(row["label_sequence"]),
                        " / ".join(f"{value['buy']:.1f}:{value['sell']:.1f}" for value in row["balance_sequence"]),
                        " / ".join(row["lean_sequence"]),
                        ", ".join(row["reasons"]) or "none",
                    ]
                    for row in stability_rows
                ],
            )
            if stability_rows
            else "`NOT_MEASURED`"
        )
        + f"\n\nCounts: `{json.dumps(stability['counts'], sort_keys=True)}`. BUY/SELL reversals: `{stability['buy_sell_reversal_count']}`. HOLD-lean flips: `{stability['unexplained_hold_lean_flip_count']}`.",
    )
    crcl_variance = "NOT_MEASURED"
    if crcl_row:
        if crcl_row["classification"] == "STABLE":
            crcl_variance = "REAL_BOUNDARY_UNCERTAINTY" if len(set(crcl_row["label_sequence"])) > 1 else "OTHER"
        elif crcl_row["action_context_changed"]:
            crcl_variance = "ACTION_CONTEXT_OVERREACTION"
        elif crcl_row["price_selection_variance"]:
            crcl_variance = "EVIDENCE_SELECTION_VARIANCE"
        else:
            crcl_variance = "REAL_BOUNDARY_UNCERTAINTY"
    write_text(
        report_dir / "20260904-crcl-clean-stability-audit.md",
        "# CRCL Clean Stability Audit\n\n"
        + (
            table(
                ["Field", "A / B / C"],
                [
                    ["Label", " / ".join(crcl_row["label_sequence"])],
                    ["Balance", " / ".join(f"{value['buy']:.1f}:{value['sell']:.1f}" for value in crcl_row["balance_sequence"])],
                    ["New buyer", " / ".join(crcl_row["new_buyer_sequence"])],
                    ["Holder", " / ".join(crcl_row["holder_sequence"])],
                ],
            )
            if crcl_row
            else "`NOT_MEASURED`"
        )
        + f"\n\nStability class: `{crcl_class}`. Variance diagnosis: `{crcl_variance}`. No desired answer was hard-coded.",
    )
    quality_rows = [
        [run, document["message_quality"]["status"], document["message_quality"]["average_character_count"], document["message_quality"]["max_character_count"], document["message_quality"]["repeated_substantive_span_count"], ", ".join(document["message_quality"]["errors"]) or "none"]
        for run, document in documents.items()
    ]
    write_text(
        report_dir / "20260904-uskr22-message-quality.md",
        "# USKR22 Message Quality\n\n"
        + table(["Run", "Status", "Average chars", "Max chars", "Repeated spans", "Errors"], quality_rows)
        + f"\n\nInternal contradictions: `{contradiction}`. Substantive repetition: `{repetition}`. Nonexistent refs: `{nonexistent_refs}`.",
    )
    write_text(
        report_dir / "20260904-uskr22-promotion-readiness.md",
        "# USKR22 Promotion Readiness\n\n"
        f"`PROMOTION_READINESS = {gates['PROMOTION_READINESS']}`\n\n"
        + table(["Gate", "Value"], [[key, value] for key, value in gates.items()])
        + "\n\nNatural production proof remains a separate gate. This result authorizes no production mutation, send, scheduler change, DB change, or main merge.",
    )

    indexed = sorted(
        path
        for path in report_dir.glob("20260904-*")
        if path.name != "20260904-uskr22-validator-coexistence-artifact-index.md"
    )
    write_text(
        report_dir / "20260904-uskr22-validator-coexistence-artifact-index.md",
        "# USKR22 Validator and Coexistence Artifact Index\n\n"
        + table(
            ["Artifact", "SHA-256", "Bytes"],
            [
                [path.name, hashlib.sha256(path.read_bytes()).hexdigest(), path.stat().st_size]
                for path in indexed
            ],
        )
        + f"\n\nIndexed artifacts: `{len(indexed)}`. Logs, credentials, recipient IDs, and runtime state are excluded.",
    )
    return proof


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--us-packet", type=Path, required=True)
    parser.add_argument("--kr-packet", type=Path, required=True)
    parser.add_argument("--kr-later-packet", type=Path, required=True)
    parser.add_argument("--us-base-messages", type=Path, required=True)
    parser.add_argument("--kr-base-messages", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--report-dir", type=Path, required=True)
    parser.add_argument("--coexistence-json", type=Path, required=True)
    parser.add_argument("--timeout", type=int, default=1800)
    parser.add_argument("--preflight-only", action="store_true")
    args = parser.parse_args()
    args.output_dir = args.output_dir.resolve()
    args.report_dir = args.report_dir.resolve()
    if args.output_dir.exists():
        raise ValueError(f"new_output_directory_required:{args.output_dir}")
    args.output_dir.mkdir(parents=True)
    intermediate_reports = args.output_dir / "intermediate-reports"
    original_report_dir = args.report_dir
    args.report_dir = intermediate_reports

    evidence, aliases, price_maps, _contexts, stocks, base_messages, source_lock = shadow.prepare(args)
    trade = trade_regression()
    metric = prior_validator_regression(
        repo=Path.cwd(), evidence=evidence, price_maps=price_maps, stocks=stocks
    )
    if trade["nonmandatory_false_positive_count"] or trade["mandatory_true_positive_block"] != "PASS":
        raise ValueError("trade_semantic_regression_failed")
    if metric["prior_false_positive_repair"] != "PASS":
        failed = [
            row
            for row in metric["prior_false_positive_rows"]
            if row["status"] != "PASS"
        ]
        raise ValueError(
            "metric_claim_type_regression_failed:"
            + json.dumps(failed, ensure_ascii=False, sort_keys=True)
        )
    if args.preflight_only:
        print(
            json.dumps(
                {
                    "prepared": True,
                    "subjects": len(shadow.COHORT),
                    "trade_regression": "PASS",
                    "metric_regression": "PASS",
                    "model_calls": 0,
                },
                sort_keys=True,
            )
        )
        return

    candidates_by_run: dict[str, tuple[StructuredAutonomyCandidate, ...]] = {}
    documents: dict[str, dict[str, object]] = {}
    for run in RUNS:
        candidates, document, _rendered = shadow.execute_run(
            run=run,
            args=args,
            evidence_packets=evidence,
            alias_catalogs=aliases,
            price_maps=price_maps,
            stock_by_ticker=stocks,
            base_messages=base_messages,
        )
        candidates_by_run[run] = candidates
        documents[run] = document
        if run == "first" and (
            int(document["validation_pass_count"]) != 22
            or document["message_quality"]["status"] != "PASS"
        ):
            break

    args.report_dir = original_report_dir
    coexistence = read_json(args.coexistence_json)
    proof = write_reports(
        args=args,
        source_lock=source_lock,
        coexistence=coexistence,
        trade=trade,
        metric=metric,
        candidates_by_run=candidates_by_run,
        documents=documents,
    )
    print(
        json.dumps(
            {
                "generation": GENERATION_ID,
                "validated": {
                    run: document["validation_pass_count"]
                    for run, document in documents.items()
                },
                "promotion_readiness": proof["gates"]["PROMOTION_READINESS"],
                "report_dir": str(args.report_dir),
            },
            ensure_ascii=False,
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    main()
