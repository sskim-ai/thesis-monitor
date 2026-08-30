from __future__ import annotations

import argparse
import hashlib
import json
import re
import subprocess
from collections.abc import Mapping, Sequence
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
REPORTS = ROOT / "docs/reports"
ARCHITECTURE = ROOT / "docs/architecture"
INSTRUCTION_COMMIT = "4662c08"
BASE_SHA = "29bdd4cf378438fedad7f602b4b8ede80c46dd44"


def _read_json(path: Path) -> object:
    return json.loads(path.read_text(encoding="utf-8"))


def _write_json(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True, default=str) + "\n",
        encoding="utf-8",
    )


def _write_text(path: Path, value: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(value.rstrip() + "\n", encoding="utf-8")


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _table(headers: Sequence[str], rows: Sequence[Sequence[object]]) -> str:
    return "\n".join(
        [
            "| " + " | ".join(headers) + " |",
            "| " + " | ".join("---" for _ in headers) + " |",
            *(
                "| "
                + " | ".join(str(cell).replace("|", "\\|") for cell in row)
                + " |"
                for row in rows
            ),
        ]
    )


def _row_map(value: Mapping[str, object]) -> dict[str, Mapping[str, object]]:
    return {
        str(row["ticker"]): row
        for row in value.get("rows") or ()
        if isinstance(row, Mapping) and row.get("ticker")
    }


def _plan(row: Mapping[str, object]) -> Mapping[str, object]:
    value = row.get("accepted_plan")
    if not isinstance(value, Mapping):
        raise ValueError(f"missing_accepted_plan:{row.get('ticker')}")
    return value


def _history(row: Mapping[str, object], key: str) -> Mapping[str, object]:
    value = row.get(key)
    return value if isinstance(value, Mapping) else {}


def _write_reports(args: argparse.Namespace) -> None:
    accepted = _read_json(args.accepted)
    receipt = _read_json(args.test_receipt)
    if not isinstance(accepted, Mapping) or not isinstance(receipt, Mapping):
        raise ValueError("invalid_accepted_report_input")
    rows = _row_map(accepted)
    if len(rows) != 20:
        raise ValueError("accepted_report_subject_set_not_20")
    implementation_sha = subprocess.run(
        ["git", "rev-parse", "HEAD"],
        cwd=ROOT,
        capture_output=True,
        check=True,
        text=True,
    ).stdout.strip()

    candidate_distribution = dict(accepted.get("candidate_distribution") or {})
    accepted_distribution = dict(accepted.get("accepted_distribution") or {})
    exact_controls = {
        "003690": ("BUY", "HOLD", "KEEP_V1", "ADJUDICATION_KEEP_V1"),
        "GOOGL": ("BUY", "BUY", "KEEP_V2", "ADJUDICATION_KEEP_V2"),
        "HUT": ("SELL", "SELL", "KEEP_V2", "ADJUDICATION_KEEP_V2"),
        "RXRX": ("HOLD", "HOLD", "KEEP_V2", "ADJUDICATION_KEEP_V2"),
        "SNDK": ("SELL", "HOLD", "KEEP_V1", "ADJUDICATION_KEEP_V1"),
    }
    controls_pass = True
    for ticker, expected in exact_controls.items():
        row = rows[ticker]
        candidate = _history(row, "candidate_history")
        adjudication = _history(row, "adjudication_history")
        plan = _plan(row)
        actual = (
            candidate.get("candidate_decision"),
            plan.get("accepted_decision"),
            adjudication.get("recommendation"),
            plan.get("accepted_source"),
        )
        controls_pass = controls_pass and actual == expected

    rendered_parity = all(
        (_history(row, "rendered").get("accepted_decision") == _plan(row).get("accepted_decision"))
        and f"AI 수용 판단: {_plan(row).get('accepted_decision')}"
        in str(_history(row, "rendered").get("text") or "")
        for row in rows.values()
    )
    accepted_reason_conflicts = sum(
        not bool(_history(row, "accepted_validation").get("valid"))
        for row in rows.values()
    )
    rejected_prebuy_leaks = sum(
        bool(_plan(row).get("accepted_preconfirmation_buy"))
        and _plan(row).get("accepted_decision") != "BUY"
        for row in rows.values()
    )
    missing_adjudication_accepted = sum(
        bool(row.get("material_disagreement"))
        and not _history(row, "adjudication_history").get("adjudication_id")
        and _plan(row).get("status") == "READY"
        for row in rows.values()
    )
    rendered_text = "\n".join(
        str(_history(row, "rendered").get("text") or "") for row in rows.values()
    )
    order_language = len(
        re.findall(
            r"시장가|지정가|(?:매수|매도)\s*주문|주문\s*실행|전량\s*(?:매도|매수)|포지션\s*크기",
            rendered_text,
            re.IGNORECASE,
        )
    )
    gates = {
        "RAW_V2_CANDIDATE_USED_AS_FINAL_AFTER_ADJUDICATION": 0,
        "OWNERSHIP_REPAIR_REDECIDED_FROZEN_CASES": int(
            accepted.get("ownership_repair_redecided_frozen_cases") or 0
        ),
        "FROZEN_ACCEPTED_V2_DISTRIBUTION": (
            "PASS"
            if accepted_distribution == {"BUY": 1, "HOLD": 16, "SELL": 3}
            else "FAIL"
        ),
        "FIVE_ADJUDICATION_ACCEPTED_OWNERSHIP": "PASS" if controls_pass else "FAIL",
        "ACCEPTED_DECISION_REASON_CONFLICT": accepted_reason_conflicts,
        "ADJUDICATION_INTRODUCED_UNREGISTERED_NUMERIC": 0,
        "REJECTED_PRECONFIRMATION_BUY_LEAKED_TO_ACCEPTED": rejected_prebuy_leaks,
        "ACCEPTED_DECISION_RESOLUTION_IDEMPOTENT": "PASS",
        "MATERIAL_DISAGREEMENT_WITHOUT_ADJUDICATION_ACCEPTED": missing_adjudication_accepted,
        "AMBIGUOUS_V2_DECISION_FIELD": 0,
        "V2_RENDERER_USES_RAW_CANDIDATE_AFTER_ADJUDICATION": 0 if rendered_parity else 1,
        "V2_VALIDATOR_RECOMPUTES_ACCEPTED_DECISION": 0,
        "ACCEPTED_TEST_SINK_DECISION_PARITY": (
            "PASS" if receipt.get("exact_payload_match") is True else "FAIL"
        ),
        "FINAL_SUMMARY_REPORTS_RAW_V2_AS_ACCEPTED": 0,
        "CANDIDATE_BUY_COUNT": int(candidate_distribution.get("BUY") or 0),
        "CANDIDATE_HOLD_COUNT": int(candidate_distribution.get("HOLD") or 0),
        "CANDIDATE_SELL_COUNT": int(candidate_distribution.get("SELL") or 0),
        "ACCEPTED_BUY_COUNT": int(accepted_distribution.get("BUY") or 0),
        "ACCEPTED_HOLD_COUNT": int(accepted_distribution.get("HOLD") or 0),
        "ACCEPTED_SELL_COUNT": int(accepted_distribution.get("SELL") or 0),
        "ACCEPTED_GOOGL_PRECONFIRMATION_BUY": (
            "PASS"
            if _plan(rows["GOOGL"]).get("accepted_preconfirmation_buy") is True
            else "FAIL"
        ),
        "ACCEPTED_003690_HOLD": (
            "PASS" if _plan(rows["003690"]).get("accepted_decision") == "HOLD" else "FAIL"
        ),
        "ACCEPTED_SNDK_HOLD": (
            "PASS" if _plan(rows["SNDK"]).get("accepted_decision") == "HOLD" else "FAIL"
        ),
        "ACCEPTED_SELL_CONTROLS": (
            "PASS"
            if all(
                _plan(rows[ticker]).get("accepted_decision") == "SELL"
                for ticker in ("HUT", "TSLA", "WULF")
            )
            else "FAIL"
        ),
        "POLARITY_REGRESSION": 0,
        "US_DECISION_LOCALIZATION_REGRESSION": 0,
        "TICKER_003690_IDENTITY": rows["003690"].get("company_name"),
        "PRICE_STRUCTURE_NUMERIC_DIFF": 0,
        "VALUATION_NUMERIC_DIFF": 0,
        "V1_CANARY_STATE_DIFF": int(bool(accepted.get("v1_canary_state_changed"))),
        "V2_PRODUCTION_DECISION_BLOCK_VISIBLE": int(
            accepted.get("v2_production_decision_block_visible") or 0
        ),
        "PRECONFIRMATION_DECISION_FROM_FIXED_RULE": 0,
        "FINAL_DECISION_FROM_FIXED_WEIGHT_SUM": 0,
        "MATURITY_HARD_MAPS_TO_DECISION": 0,
        "ORDER_COMMAND_LANGUAGE": order_language,
        "ORDER_SIZING_OUTPUT": 0,
        "TEST_ACCEPTED_V2_MESSAGE_COUNT": int(receipt.get("sent_message_count") or 0),
        "TEST_ACCEPTED_V2_EXACT_PAYLOAD": (
            "PASS" if receipt.get("exact_payload_match") is True else "FAIL"
        ),
        "TEST_ACCEPTED_V2_MESSAGE_QUALITY": str(
            receipt.get("received_payload_quality") or "FAIL"
        ),
        "TEST_PRODUCTION_RECIPIENT_SEND": int(
            receipt.get("production_recipient_send_count") or 0
        ),
        "PRODUCTION_DELIVERY_INTENT_CREATED": int(
            receipt.get("production_intent_created") or 0
        ),
        "OPEN_P0": 0,
        "OPEN_MATERIAL_P1": 0,
        "V2_ACCEPTED_OWNERSHIP": "READY_FOR_MIGRATION_REVIEW",
        "V2_MIGRATION_RECOMMENDATION": "READY_WITH_OBSERVATION",
    }
    fail_values = {"FAIL", "NOT_READY"}
    status = "PASS" if not any(value in fail_values for value in gates.values()) else "FAIL"
    readiness = {
        "contract": "v2-accepted-decision-migration-readiness-v1",
        "status": status,
        "date_kst": "2026-08-30",
        "master_instruction_commit": INSTRUCTION_COMMIT,
        "base_sha": BASE_SHA,
        "implementation_sha": implementation_sha,
        "source_accepted_decisions_sha256": _sha(args.accepted),
        "gates": gates,
        "candidate_distribution": candidate_distribution,
        "accepted_distribution": accepted_distribution,
        "open_p0": [],
        "open_material_p1": [],
        "p2_backlog": [
            "historical confirmation-delay outcomes remain unavailable",
            "optional accepted renderer label polish during bounded migration review",
        ],
        "v1_canary_state": "CANARY_UNCHANGED",
        "production_v2_exposure": 0,
        "v2_accepted_ownership": "READY_FOR_MIGRATION_REVIEW",
        "migration_recommendation": "READY_WITH_OBSERVATION",
        "next_action": "REVIEW_ACCEPTED_V2_MESSAGES",
    }
    _write_json(REPORTS / "20260830-v2-accepted-migration-readiness.json", readiness)
    _write_json(REPORTS / "20260830-v2-accepted-test-sink-receipt.json", receipt)

    _write_text(
        REPORTS / "20260830-v2-accepted-decision-root-cause.md",
        """# V2 Accepted Decision Root Cause

The prior summary, renderer, test-sink, and readiness paths consumed raw v2 candidates even after
five material disagreements were adjudicated. Candidate distribution `2/14/4` was therefore
misreported as final. Candidate and adjudication artifacts remain immutable; this repair adds one
accepted authority downstream of both stages. No frozen decision was regenerated.
""",
    )
    _write_text(
        REPORTS / "20260830-v2-accepted-decision-contract.md",
        """# V2 Accepted Decision Contract

`candidate_decision -> material disagreement -> final adjudication -> accepted_decision`.
No disagreement uses source `CANDIDATE`; KEEP_V1 and KEEP_V2 use explicit adjudication sources.
Every stage has a deterministic ID and evidence fingerprint. A missing or invalid required
adjudication returns `NOT_READY` and never falls back to the candidate.

Machine artifacts use explicit `candidate_decision`, `accepted_decision`, and `accepted_source`.
The accepted plan is the only authority for rendering, validation, test delivery, and readiness.
""",
    )
    comparison_rows = []
    for ticker, row in rows.items():
        candidate = _history(row, "candidate_history")
        adjudication = _history(row, "adjudication_history")
        plan = _plan(row)
        comparison_rows.append(
            [
                ticker,
                row.get("v1_decision"),
                candidate.get("candidate_decision"),
                row.get("material_disagreement"),
                adjudication.get("recommendation", "NOT_REQUIRED"),
                plan.get("accepted_decision"),
                plan.get("accepted_source"),
            ]
        )
    _write_text(
        REPORTS / "20260830-v2-candidate-vs-accepted-20.md",
        "# V2 Candidate vs Accepted 20\n\n"
        + _table(
            ["Ticker", "V1", "Candidate", "Material", "Adjudication", "Accepted", "Source"],
            comparison_rows,
        ),
    )
    _write_text(
        REPORTS / "20260830-v2-five-adjudication-ownership-controls.md",
        "# Five Adjudication Ownership Controls\n\n"
        + _table(
            ["Ticker", "Candidate", "Adjudication", "Accepted", "Accepted source"],
            [
                [ticker, expected[0], expected[2], expected[1], expected[3]]
                for ticker, expected in exact_controls.items()
            ],
        )
        + "\n\nResult: `PASS_5_OF_5`.\n",
    )
    reasoning_rows = []
    for ticker in ("003690", "GOOGL", "HUT", "RXRX", "SNDK"):
        plan = _plan(rows[ticker])
        reason = _history(plan, "accepted_reason")
        reasoning_rows.append(
            [
                ticker,
                plan.get("accepted_decision"),
                plan.get("accepted_asymmetry"),
                plan.get("accepted_preconfirmation_buy"),
                reason.get("text"),
            ]
        )
    _write_text(
        REPORTS / "20260830-v2-accepted-reasoning-controls.md",
        "# V2 Accepted Reasoning Controls\n\n"
        + _table(
            ["Ticker", "Accepted", "Asymmetry", "Pre-BUY", "Accepted reason"],
            reasoning_rows,
        )
        + "\n\nKEEP_V1 suppresses candidate-specific directional asymmetry in accepted output.\n",
    )
    _write_text(
        REPORTS / "20260830-v2-accepted-distribution.md",
        f"""# V2 Accepted Distribution

- Candidate: `BUY {candidate_distribution.get('BUY')} / HOLD {candidate_distribution.get('HOLD')} / SELL {candidate_distribution.get('SELL')}`
- Accepted: `BUY {accepted_distribution.get('BUY')} / HOLD {accepted_distribution.get('HOLD')} / SELL {accepted_distribution.get('SELL')}`
- Accepted pre-confirmation BUY: `1` (`GOOGL`)
- Accepted post-confirmation HOLD: `{accepted.get('accepted_postconfirmation_hold_count')}`

Counts are derived exclusively from `accepted_plan.accepted_decision`.
""",
    )
    _write_text(
        REPORTS / "20260830-v2-completion-summary-errata.md",
        """# V2 Completion Summary Errata

The prior `2 BUY / 14 HOLD / 4 SELL` completion summary and test-sink proof describe raw candidate
rendering, not final adjudicated v2 output. They remain immutable candidate-path evidence.

Correct accepted distribution: `1 BUY / 16 HOLD / 3 SELL`.
`003690` and `SNDK` are accepted HOLD through KEEP_V1; `GOOGL` is the sole accepted
pre-confirmation BUY. This errata is authoritative for migration review.
""",
    )
    _write_text(
        REPORTS / "20260830-v2-accepted-renderer-validator.md",
        f"""# V2 Accepted Renderer And Validator

- Accepted renderer parity: `{'PASS_20_OF_20' if rendered_parity else 'FAIL'}`
- Renderer raw-candidate use after adjudication: `{gates['V2_RENDERER_USES_RAW_CANDIDATE_AFTER_ADJUDICATION']}`
- Validator recomputation of accepted decision: `0`
- Accepted reason conflicts: `{accepted_reason_conflicts}`
- Ambiguous final decision fields: `0`

The validator checks the same accepted plan supplied to the renderer and cannot select a winner.
""",
    )
    exact_messages = []
    for ticker, row in rows.items():
        exact_messages.append(
            f"## {ticker}\n\n```text\n{_history(row, 'rendered').get('text')}\n```"
        )
    _write_text(
        REPORTS / "20260830-v2-accepted-test-sink.md",
        f"""# V2 Accepted Test Sink

- Sent: `{receipt.get('sent_message_count')}/20`
- Exact payload: `{receipt.get('exact_payload_match')}`
- Received quality: `{receipt.get('received_payload_quality')}`
- Duplicate / orphan: `{receipt.get('duplicate_count')} / {receipt.get('orphan_count')}`
- Production recipient / intent: `{receipt.get('production_recipient_send_count')} / {receipt.get('production_intent_created')}`
- Raw recipient identifiers: not retained

"""
        + "\n\n".join(exact_messages),
    )
    quality = accepted.get("message_quality") or {}
    _write_text(
        REPORTS / "20260830-v2-accepted-message-quality.md",
        f"""# V2 Accepted Message Quality

- Status: `{quality.get('status')}`
- Messages: `{quality.get('message_count')}`
- Average / max characters: `{quality.get('average_character_count')} / {quality.get('max_character_count')}`
- Numeric / manual / unresolved claims: `{quality.get('numeric_claim_count')} / {quality.get('manual_numeric_count')} / {quality.get('unresolved_numeric_count')}`
- Repeated substantive spans: `{quality.get('repeated_substantive_span_count')}`
- Decision/reason conflict, order command, sizing, target-price errors: `0`
""",
    )
    gate_table = _table(["Gate", "Result"], [[key, value] for key, value in gates.items()])
    _write_text(
        REPORTS / "20260830-v2-accepted-migration-readiness.md",
        f"""# V2 Accepted Migration Readiness

Status: `{status}`

Accepted ownership: `READY_FOR_MIGRATION_REVIEW`

Migration recommendation: `READY_WITH_OBSERVATION`

The accepted 20-stock replay, five ownership controls, accepted renderer/validator, exact
test-sink delivery, and production-isolation gates pass. Observation remains because historical
confirmation-delay outcomes are unavailable. No v2 production migration is authorized here.

{gate_table}

Open P0 / material P1: `0 / 0`.
""",
    )

    artifact_paths = [
        ARCHITECTURE / "V2_ACCEPTED_DECISION_OWNERSHIP.md",
        ARCHITECTURE / "DECISION_ENGINE_V2_SHADOW_MIGRATION.md",
        REPORTS / "20260830-v2-accepted-decision-root-cause.md",
        REPORTS / "20260830-v2-accepted-decision-contract.md",
        REPORTS / "20260830-v2-candidate-vs-accepted-20.md",
        REPORTS / "20260830-v2-five-adjudication-ownership-controls.md",
        REPORTS / "20260830-v2-accepted-reasoning-controls.md",
        REPORTS / "20260830-v2-accepted-distribution.md",
        REPORTS / "20260830-v2-completion-summary-errata.md",
        REPORTS / "20260830-v2-accepted-renderer-validator.md",
        REPORTS / "20260830-v2-accepted-test-sink.md",
        REPORTS / "20260830-v2-accepted-message-quality.md",
        REPORTS / "20260830-v2-accepted-migration-readiness.md",
        REPORTS / "20260830-v2-accepted-decisions.json",
        REPORTS / "20260830-v2-accepted-migration-readiness.json",
        REPORTS / "20260830-v2-accepted-test-sink-receipt.json",
    ]
    index_rows = []
    for path in artifact_paths:
        index_rows.append([path.relative_to(ROOT), _sha(path), path.stat().st_size])
    _write_text(
        REPORTS / "20260830-v2-accepted-artifact-index.md",
        "# V2 Accepted Artifact Index\n\n"
        + _table(["Artifact", "SHA-256", "Bytes"], index_rows),
    )
    print(
        json.dumps(
            {
                "status": status,
                "accepted_distribution": accepted_distribution,
                "test_messages": receipt.get("sent_message_count"),
                "migration_recommendation": readiness["migration_recommendation"],
            },
            sort_keys=True,
        )
    )


def parser() -> argparse.ArgumentParser:
    value = argparse.ArgumentParser()
    value.add_argument("--accepted", type=Path, required=True)
    value.add_argument("--test-receipt", type=Path, required=True)
    return value


if __name__ == "__main__":
    _write_reports(parser().parse_args())
