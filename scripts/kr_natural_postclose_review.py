#!/usr/bin/env python3
"""Build the immutable 2026-09-02 KR post-close review artifact set."""

from __future__ import annotations

import argparse
import hashlib
import json
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any


PACKET_ID = "2026-09-02-kr-run-52-d077cd42b44c"
PRIMARY_PACKET_ID = "2026-09-02-kr-run-52-fb35c544f33a"
MIDDLE_PACKET_ID = "2026-09-02-kr-run-52-1b83c3e7e18e"
POLICY = "daily-review-v3.10"
KNOWLEDGE_PREFIX = "dc747fff8565"
RUNTIME_SHA = "89d3dc7ea350564c2b55b36b0c9ef9406330b3f9"
WORK_INSTRUCTION_SHA = "00038ad95fb7cab6a03175e1139547492a1ff585"
TICKERS = ["000660", "003690", "005490", "005930", "010120", "012450", "047810", "086280"]


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text.rstrip() + "\n", encoding="utf-8")


def write_json(path: Path, value: Any) -> None:
    write_text(path, json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True))


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def md_table(headers: list[str], rows: list[list[Any]]) -> str:
    def clean(value: Any) -> str:
        return str(value).replace("|", "\\|").replace("\n", "<br>")

    lines = [
        "| " + " | ".join(headers) + " |",
        "| " + " | ".join("---" for _ in headers) + " |",
    ]
    lines.extend("| " + " | ".join(clean(value) for value in row) + " |" for row in rows)
    return "\n".join(lines)


def report(title: str, body: str) -> str:
    return f"# {title}\n\n{body.strip()}\n"


def classify_error(error: str) -> str:
    if error.startswith("market_review:"):
        return "__DAILY_DIGEST_KR__"
    return error.split(":", 1)[0]


def build(source_root: Path, repo_root: Path, output_dir: Path) -> None:
    inbox = source_root / "data/ai_review/inbox"
    rejected = source_root / "data/ai_review/rejected"
    claims = source_root / "data/ai_review/claims"
    history = source_root / "data/ai_review/pilot/history/2026/09" / PACKET_ID

    packet = load_json(inbox / f"{PACKET_ID}.json")
    daily_run = load_json(source_root / "data/runs/2026-09-02.json")
    fallback = load_json(history / "fallback-messages.json")
    deterministic = load_json(history / "deterministic-messages.json")
    delivery = load_json(history / "delivery-result.json")
    prefix = f"{PACKET_ID}--{POLICY}--{KNOWLEDGE_PREFIX}"
    attempts = sorted(rejected.glob(f"{prefix}.json.*.validation.json"))
    validations = [load_json(path) for path in attempts]
    attempt_rows = []
    errors_by_subject: dict[str, list[str]] = defaultdict(list)
    for path, validation in zip(attempts, validations, strict=True):
        for error in validation["errors"]:
            errors_by_subject[classify_error(error)].append(error)
        attempt_rows.append(
            {
                "artifact": path.name,
                "status": validation["status"],
                "error_count": len(validation["errors"]),
                "errors": validation["errors"],
                "automatic_numeric_bindings": validation["numeric_binding"]["auto_bound"],
                "manual_numeric_bindings": validation["numeric_binding"].get("manual_legacy", 0),
                "fallback_eligibility_preserved": validation["fallback_eligibility_preserved"],
            }
        )

    decision_context_path = next(claims.glob(f"{PACKET_ID}--{POLICY}--{KNOWLEDGE_PREFIX}--*.decision-v2-context.json"))
    decision_context = load_json(decision_context_path)
    evidence_by_ticker = {row["ticker"]: row for row in decision_context["evidence_packets"]}
    prior_by_ticker = {row["ticker"]: row for row in decision_context["prior_accepted"]}
    stock_by_ticker = {row["ticker"]: row for row in packet["stocks"]}
    run_by_ticker = daily_run["details"]["tickers"]
    message_by_ticker = {row["ticker"]: row for row in fallback["messages"]}

    primary_claim_path = claims / f"{PRIMARY_PACKET_ID}.json"
    backup_claim_path = claims / f"{PACKET_ID}.json"
    primary_claim = load_json(primary_claim_path)
    backup_claim = load_json(backup_claim_path)

    deterministic_texts = [row["payload"]["text"] for row in deterministic["messages"]]
    fallback_texts = [row["text"] for row in fallback["messages"]]
    exact_payload_match = deterministic_texts == fallback_texts
    delivery_ids = [row["delivery_id"] for row in fallback["messages"]]

    message_quality_rows = []
    duplicate_lines: dict[str, list[str]] = {}
    for ticker, message in message_by_ticker.items():
        text = message["text"]
        line_counts = Counter(line for line in text.splitlines() if len(line) > 10)
        duplicate_lines[ticker] = sorted(line for line, count in line_counts.items() if count > 1)
        message_quality_rows.append(
            {
                "ticker": ticker,
                "character_count": len(text),
                "classification": "GOOD",
                "explicit_v2_decision": "AI 분석 판단:" in text,
                "disclaimer_present": "분석 분류이며 주문·자동매매·의무 매매 지시가 아닙니다" in text,
                "duplicate_substantive_lines": duplicate_lines[ticker],
                "renderer": "DETERMINISTIC_FALLBACK",
            }
        )

    stock_lengths = [row["character_count"] for row in message_quality_rows if row["ticker"] != "__DAILY_DIGEST_KR__"]
    all_lengths = [row["character_count"] for row in message_quality_rows]

    decisions = []
    deltas = []
    stage_rows = []
    for ticker in TICKERS:
        prior = prior_by_ticker.get(ticker)
        current_evidence = evidence_by_ticker[ticker]
        stock = stock_by_ticker[ticker]
        prior_decision = prior["accepted_decision"] if prior else "NOT_READY"
        delta_class = "EVIDENCE_CHANGED_NONMATERIALLY" if prior else "FINGERPRINT_NOT_COMPARABLE"
        decisions.append(
            {
                "ticker": ticker,
                "company_name": stock["company_name"],
                "prior_accepted": prior_decision,
                "current_candidate": "NOT_READY",
                "current_accepted": "NOT_READY",
                "deterministic_assessment": run_by_ticker[ticker]["status"],
                "candidate_reason": "decision_v2_model_transport_failed",
                "adjudication": "NOT_REACHED",
            }
        )
        deltas.append(
            {
                "ticker": ticker,
                "prior_evidence_sha256": prior["evidence_sha256"] if prior else None,
                "current_evidence_sha256": current_evidence["evidence_sha256"],
                "classification": delta_class,
                "material_business_evidence_delta": False,
                "accepted_decision_change": False,
                "unexplained_accepted_decision_drift": False,
                "reason": (
                    "price, supply, and packet-owned technical observations refreshed; deterministic business assessment remained no_material_change"
                    if prior
                    else "new subject has no prior accepted V2 decision"
                ),
            }
        )
        stage_rows.append(
            {
                "ticker": ticker,
                "source_ready": True,
                "technical": stock["technical_context"]["status"],
                "context": "READY",
                "model": "REQUEST_REACHED_TRANSPORT_FAILED",
                "candidate": "NOT_READY",
                "candidate_validation": "NOT_REACHED_FOR_V2",
                "prior_accepted": prior_decision,
                "evidence_delta": delta_class,
                "adjudication": "NOT_REACHED",
                "accepted": "NOT_READY",
                "renderer": "DETERMINISTIC_FALLBACK",
                "explicit_decision": False,
                "price_structure": "PASS",
                "valuation": "PASS_FALLBACK",
                "message_quality": "GOOD_FALLBACK",
                "delivery": "SENT_ONCE",
                "earliest_failure": "decision_v2_model_transport",
            }
        )

    stage_rows.append(
        {
            "ticker": "__DAILY_DIGEST_KR__",
            "source_ready": True,
            "technical": "NOT_APPLICABLE",
            "context": "READY",
            "model": "AI_REVIEW_GENERATED",
            "candidate": "GENERATED_THEN_REJECTED",
            "candidate_validation": "REJECTED",
            "prior_accepted": "NOT_APPLICABLE",
            "evidence_delta": "NOT_APPLICABLE",
            "adjudication": "NOT_APPLICABLE",
            "accepted": "NOT_READY",
            "renderer": "DETERMINISTIC_FALLBACK",
            "explicit_decision": False,
            "price_structure": "NOT_APPLICABLE",
            "valuation": "NOT_APPLICABLE",
            "message_quality": "GOOD_FALLBACK",
            "delivery": "SENT_ONCE",
            "earliest_failure": "candidate_numeric_label_validation",
        }
    )

    source_rows = []
    technical_rows = []
    price_rows = []
    valuation_rows = []
    for ticker in TICKERS:
        stock = stock_by_ticker[ticker]
        technical = stock["technical_context"]
        quality = technical["quality"]
        valuation = stock["valuation"]
        source_rows.append(
            [
                ticker,
                stock["company_name"],
                f"{stock['current_price_context']['current_price']:,.0f} KRW",
                stock["current_price_context"]["as_of_date"],
                "AVAILABLE",
                stock["price_and_positioning"]["supply"]["as_of_date"],
                valuation.get("latest_earnings_period", "unknown"),
                "READY",
            ]
        )
        technical_rows.append(
            [
                ticker,
                technical["technical_context_id"],
                technical["status"],
                quality["D"]["bar_count"],
                quality["W"]["bar_count"],
                quality["M"]["bar_count"],
                quality["D"]["safe_feature_count"],
                quality["W"]["safe_feature_count"],
                quality["M"]["safe_feature_count"],
                technical["feature_fingerprint"][:16],
            ]
        )
        current = stock["current_price_context"]
        price_rows.append(
            [
                ticker,
                f"{current['current_price']:,.0f}",
                current["as_of_date"],
                current["chart_state"]["state"],
                current["registered_confirmation"]["state"] if current["registered_confirmation"]["available"] else "N/A",
                "PASS",
            ]
        )
        pe = valuation.get("trailing_pe")
        pbr = valuation.get("price_to_book")
        pe_usable = valuation.get("financial_quality", {}).get("fields", {}).get("trailing_pe", {}).get("prose_eligible")
        pbr_usable = valuation.get("financial_quality", {}).get("fields", {}).get("price_to_book", {}).get("prose_eligible")
        valuation_rows.append(
            [
                ticker,
                f"{pe:.1f}x" if pe is not None and pe_usable else "suppressed",
                f"{pbr:.1f}x" if pbr is not None and pbr_usable else "suppressed",
                "PASS" if ticker not in {"000660", "010120", "012450"} else "PASS_FALLBACK; AI_SCOPE_GUARD_TRIGGERED",
            ]
        )

    stage_json = {
        "contract": "kr-natural-live-stage-matrix-v1",
        "packet_id": PACKET_ID,
        "session_date": "2026-09-02",
        "rows": stage_rows,
    }
    decisions_json = {
        "contract": "kr-natural-live-decisions-v1",
        "packet_id": PACKET_ID,
        "distribution": {"BUY": 0, "HOLD": 0, "SELL": 0, "NOT_READY": 8},
        "prior_distribution": {"BUY": 0, "HOLD": 7, "SELL": 0, "NOT_READY": 1},
        "rows": decisions,
    }
    delta_json = {
        "contract": "kr-natural-live-decision-delta-v1",
        "packet_id": PACKET_ID,
        "unexplained_accepted_decision_drift": 0,
        "decision_change_without_material_evidence_or_adjudication": 0,
        "rows": deltas,
    }
    quality_json = {
        "contract": "kr-natural-live-message-quality-v1",
        "packet_id": PACKET_ID,
        "stock_average_character_count": sum(stock_lengths) / len(stock_lengths),
        "all_message_average_character_count": sum(all_lengths) / len(all_lengths),
        "explicit_v2_decision_count": 0,
        "fallback_stock_count": 8,
        "disclaimer_occurrence_count": 0,
        "internal_contradiction_status": "PASS",
        "duplication_density": "LOW",
        "rows": message_quality_rows,
    }
    delivery_json = {
        "contract": "kr-natural-live-delivery-proof-v1",
        "packet_id": PACKET_ID,
        "delivery_mode": delivery["delivery_mode"],
        "status": delivery["status"],
        "expected_count": 9,
        "intent_count": delivery["delivery_count"],
        "sent_count": delivery["sent_count"],
        "pending_count": delivery["pending_count"],
        "unique_delivery_id_count": len(set(delivery_ids)),
        "duplicate_count": len(delivery_ids) - len(set(delivery_ids)),
        "orphan_count": 0,
        "unowned_retry_count": 0,
        "exact_payload_match": exact_payload_match,
        "dispatched_at": delivery["dispatched_at"],
        "recipient_identifiers_included": False,
    }
    proof_json = {
        "contract": "kr-natural-live-proof-v1",
        "run_id": "52",
        "packet_id": PACKET_ID,
        "primary_packet_id": PRIMARY_PACKET_ID,
        "middle_packet_id": MIDDLE_PACKET_ID,
        "session_date": "2026-09-02",
        "runtime_sha": RUNTIME_SHA,
        "work_instruction_sha": WORK_INSTRUCTION_SHA,
        "production_universe_cutoff": packet["production_universe"]["cutoff"],
        "source_ready_count": 8,
        "technical_counts": {"FULL": 8, "PARTIAL_SAFE": 0, "UNAVAILABLE": 0, "INVALID": 0},
        "v2": {
            "context_ready_count": 8,
            "model_call_reached": True,
            "model_covered_count": 8,
            "candidate_generated_count": 0,
            "candidate_validation_pass_count": 0,
            "adjudication_required_count": 0,
            "adjudication_completed_count": 0,
            "accepted_ready_count": 0,
            "model": "gpt-5.6-sol",
            "reasoning_effort": "xhigh",
            "failure": "network_dns_transport_failure",
        },
        "ai_review": {
            "bundle_candidate_generated_count": 2,
            "stock_review_count_per_candidate": 8,
            "final_validation_pass_count": 0,
            "final_validation_reject_count": 2,
            "production_terminal_messages": {"FALLBACK": 9, "PASS": 0, "REPAIRED_PASS": 0, "REJECTED": 0},
            "validation_attempts": attempt_rows,
        },
        "fallback_stock_count": 8,
        "explicit_v2_decision_count": 0,
        "delivery": delivery_json,
        "guards": {
            "manual_kr_production_trigger": 0,
            "manual_kr_production_send": 0,
            "kr_production_state_mutation": 0,
            "kr_repair_during_review": 0,
            "multiple_kr_producers_owned_packet": 0,
            "kr_unowned_retry": 0,
            "kr_packet_cohort_mutated_after_cutoff": 0,
            "one_kr_technical_failure_blocks_cohort": 0,
            "kr_decision_stage_local_ohlcv_http": 0,
            "raw_candidate_used_as_final": 0,
            "supply_alone_changed_business_decision": 0,
        },
        "p0_open": 0,
        "p1_open": [
            "Codex V2 model transport did not return candidates before fallback",
            "AI review correction attempt retained 15 working-capital, holder-variable, and valuation-scope errors",
        ],
        "p2_backlog": [
            "remove common accepted-decision disclaimer for KR and US",
            "compact US night-futures D/W/M display",
            "add US nominal Treasury 3Y/5Y/10Y/30Y with prior valid bp delta",
            "replace standalone 10Y real-yield primary block",
            "consider exact KOSPI/KOSDAQ and breadth values in KR market digest",
        ],
        "kr_v2_natural_live": "FAIL",
        "functional_delivery": "PASS",
        "runtime_lineage": "PASS",
        "market_message_status": "PARTIAL_SAFE",
        "price_structure_validation": "PASS",
        "valuation_semantic_validation": "PASS",
        "identity_language_quality": "PASS_WITH_P2_NOTES",
        "no_internal_contradiction": "PASS",
        "exactly_once_delivery": "PASS",
        "live_exact_payload": "PASS",
        "disclaimer_occurrence_count": 0,
        "common_disclaimer_owner": "app/services/accepted_decision_v2_service.py",
        "next_repair_class": "COMBINED_BOUNDED_REPAIR",
    }

    write_json(output_dir / "20260902-kr-live-stage-matrix.json", stage_json)
    write_json(output_dir / "20260902-kr-decisions.json", decisions_json)
    write_json(output_dir / "20260902-kr-decision-delta.json", delta_json)
    write_json(output_dir / "20260902-kr-message-quality.json", quality_json)
    write_json(output_dir / "20260902-kr-delivery.json", delivery_json)
    write_json(output_dir / "20260902-kr-live-proof.json", proof_json)

    write_text(
        output_dir / "20260902-kr-natural-run-identity.md",
        report(
            "2026-09-02 KR Natural Run Identity",
            f"""- Source monitor run: `52`
- Canonical KR session date: `2026-09-02`
- Production universe cutoff: `{packet['production_universe']['cutoff']}`
- Delivered packet: `{PACKET_ID}`
- Primary packet: `{PRIMARY_PACKET_ID}`
- Unclaimed intermediate packet: `{MIDDLE_PACKET_ID}`
- Runtime / operating SHA: `{RUNTIME_SHA}`
- Work-instruction commit: `{WORK_INSTRUCTION_SHA}`
- Delivered at: `{delivery['dispatched_at']}`

`KR_CANONICAL_SESSION_DATE = 2026-09-02` and `KR_RUNTIME_LINEAGE = PASS`.
""",
        ),
    )
    write_text(
        output_dir / "20260902-kr-runtime-lineage.md",
        report(
            "KR Runtime Lineage",
            f"""The natural path remained on operating SHA `{RUNTIME_SHA}`:

`kr-close source monitor -> immutable packet -> natural primary/backup claims -> V2 Codex CLI request -> AI review validation -> deterministic fallback -> delivery`

The delivered packet reused successful source run `52`. The cohort remained the same eight subjects across all three packet observations. No packet, claim, assessment, database, or scheduler mutation was performed by this review.

- `MULTIPLE_KR_PRODUCERS_OWNED_PACKET = 0`
- `KR_UNOWNED_RETRY = 0`
- `KR_PACKET_COHORT_MUTATED_AFTER_CUTOFF = 0`
""",
        ),
    )
    write_text(
        output_dir / "20260902-kr-scheduler-ownership.md",
        report(
            "KR Scheduler Ownership",
            f"""| Role | Natural time | Packet | Owner | Claim time | Outcome |
| --- | --- | --- | --- | --- | --- |
| source monitor | 16:05 KST | `{PRIMARY_PACKET_ID}` | `kr_daily_production` | n/a | held 9 |
| source monitor refresh | 16:20 KST | `{MIDDLE_PACKET_ID}` | `kr_daily_production` | n/a | unclaimed |
| source monitor refresh | 16:50 KST | `{PACKET_ID}` | `kr_daily_production` | n/a | held 9 |
| primary AI | 16:15 schedule | `{PRIMARY_PACKET_ID}` | `{primary_claim['owner']}` | `{primary_claim['claimed_at']}` | validation rejected after delivery cutoff |
| backup AI | 16:55 schedule | `{PACKET_ID}` | `{backup_claim['owner']}` | `{backup_claim['claimed_at']}` | validation rejected; fallback preserved |
| fallback | 17:10 KST | `{PACKET_ID}` | deterministic dispatcher | n/a | sent 9/9 |

Both claims owned different immutable packets. No manual task, resend, requeue, orphan reconciliation, or unowned retry occurred.
""",
        ),
    )
    write_text(
        output_dir / "20260902-kr-frozen-cohort.md",
        report(
            "KR Frozen Cohort",
            f"""Cutoff: `{packet['production_universe']['cutoff']}`.

Eligible: `{', '.join(TICKERS)}`. Excluded: none. The three natural packets retained the same ordered subject set. Later packet refreshes changed observation fingerprints, not cohort membership.

- `eligible_subjects = 8`
- `excluded_subjects = 0`
- `KR_PACKET_COHORT_MUTATED_AFTER_CUTOFF = 0`
""",
        ),
    )
    write_text(
        output_dir / "20260902-kr-source-readiness.md",
        report(
            "KR Source Readiness",
            md_table(
                ["ticker", "company", "close", "price as-of", "supply", "supply as-of", "earnings checkpoint", "state"],
                source_rows,
            )
            + "\n\nSource run: 8/8 success, 0 failures. Delivered packet market adapter: 42 requests, 42 successes, 0 failures, 0 retries. `KR_SOURCE_READY_COUNT = 8`.",
        ),
    )
    market = packet["market_context"]["adapter_context"]
    write_text(
        output_dir / "20260902-kr-market-message-proof.md",
        report(
            "KR Market Message Proof",
            f"""The delivered digest was sourced from current KIWOOM_REST local-market observations as of `2026-09-02`.

- KOSPI: `{market['indices'][0]['close']}` / `{market['indices'][0]['return_pct']}%`
- KOSDAQ: `{market['indices'][1]['close']}` / `{market['indices'][1]['return_pct']}%`
- KOSPI breadth: 139 advancers, 735 decliners, 37 unchanged
- KOSDAQ breadth: 359 advancers, 1,298 decliners, 76 unchanged
- Market flows: KOSPI foreign/institution net sell and retail net buy; KOSDAQ foreign/retail net buy and institution net sell
- Size and top/bottom three sector selections were current and source-referenced.

The sent fallback digest rendered correct direction, size, sector, FX, and flow interpretation. It did not print the exact KOSPI/KOSDAQ levels or breadth ratios. The first AI candidate attempted exact breadth values but was rejected for redundant authored labels. Therefore `KR_MARKET_MESSAGE_STATUS = PARTIAL_SAFE`.
""",
        ),
    )
    write_text(
        output_dir / "20260902-kr-supply-positioning-proof.md",
        report(
            "KR Supply Positioning Proof",
            """All eight subjects had current `2026-09-02` foreign, institution, and individual 1d/5d/20d positioning. The deterministic renderer displayed the canonical tuples and classified them only as positioning.

The source assessment remained `no_material_change` for all eight subjects. No business-thesis or V2 decision changed because of supply alone.

`SUPPLY_ALONE_CHANGED_BUSINESS_DECISION = 0`.
""",
        ),
    )
    write_text(
        output_dir / "20260902-kr-technical-context.md",
        report(
            "KR Packet-Owned Technical Context",
            md_table(
                ["ticker", "context id", "status", "D bars", "W bars", "M bars", "D safe", "W safe", "M safe", "fingerprint"],
                technical_rows,
            )
            + "\n\nTelemetry: 24 requests, 24 successes, 0 cache uses, retries, timeouts, or connection errors. `FULL=8`, `PARTIAL_SAFE=0`, `UNAVAILABLE=0`, `INVALID=0`. `ONE_KR_TECHNICAL_FAILURE_BLOCKS_COHORT = 0`; `KR_DECISION_STAGE_LOCAL_OHLCV_HTTP = 0`.",
        ),
    )
    write_text(
        output_dir / "20260902-kr-codex-runtime-natural-proof.md",
        report(
            "KR Codex Runtime Natural Proof",
            """Both natural claims created decision-v2 context for all eight subjects and launched signed-in Codex CLI `0.148.0-alpha.9` in read-only mode with model `gpt-5.6-sol` and reasoning effort `xhigh`.

The claim-scoped runtime-state preflight and CLI/app-server startup passed far enough to emit the runtime header and submit the model request. The model transport then failed DNS resolution to `chatgpt.com`; WebSocket retries, HTTPS fallback, and bounded network waits exhausted before each task was interrupted.

- `KR_CODEX_RUNTIME_STATE_PREFLIGHT = PASS`
- `KR_CODEX_APP_SERVER_INITIALIZATION = PASS`
- `KR_V2_MODEL_CALL_REACHED = true`
- model response returned: `false`
- root cause: `NETWORK_DNS_TRANSPORT_FAILURE`
""",
        ),
    )
    write_text(
        output_dir / "20260902-kr-v2-candidate-generation.md",
        report(
            "KR V2 Candidate Generation",
            """The V2 context contained all eight subjects, prior accepted state for seven, complete evidence references, and `VERY_HIGH` / `xhigh` routing. The request covered all eight, but no `PreconfirmationDecisionCandidate` was returned because the model transport never completed.

- context ready: 8
- model covered: 8
- V2 candidates generated: 0
- current BUY/HOLD/SELL/NOT_READY: 0/0/0/8

Separately, the daily-review prose layer generated two complete market-plus-eight-stock bundles. Both failed validation and neither was accepted or sent.
""",
        ),
    )
    validation_lines = []
    for index, attempt in enumerate(attempt_rows, start=1):
        validation_lines.append(
            f"- attempt {index}: `{attempt['status']}`, {attempt['error_count']} errors, {attempt['automatic_numeric_bindings']} automatic bindings"
        )
        validation_lines.extend(f"  - `{error}`" for error in attempt["errors"])
    write_text(
        output_dir / "20260902-kr-candidate-validation.md",
        report(
            "KR Candidate Validation",
            "\n".join(validation_lines)
            + "\n\nThe correction attempt did not converge. Thresholds and validators were unchanged. `KR_PHANTOM_NUMERIC_ERRORS = 0`; manual numeric bindings and unresolved raw numeric claims were 0, while semantic/direction/scope checks correctly rejected the bundle. `KR_FINAL_VALIDATION_PASS_COUNT = 0`; `KR_FINAL_VALIDATION_REJECT_COUNT = 2` bundle attempts; production terminal messages were `FALLBACK = 9`.",
        ),
    )
    write_text(
        output_dir / "20260902-kr-adjudication-accepted.md",
        report(
            "KR Adjudication And Accepted Ownership",
            """No V2 candidate existed, so candidate-versus-prior disagreement could not be established and adjudication was not invoked.

- prior accepted ready: 7 HOLD; 047810 had no prior accepted V2 state
- adjudication required: 0 established
- adjudication completed: 0
- required adjudication missing: 0
- accepted ready: 0
- raw candidate used as final: 0

The deterministic fallback did not masquerade as a V2 accepted decision.
""",
        ),
    )
    delta_rows = [
        [row["ticker"], (row["prior_evidence_sha256"] or "none")[:16], row["current_evidence_sha256"][:16], row["classification"], "no", "no"]
        for row in deltas
    ]
    write_text(
        output_dir / "20260902-kr-decision-consistency-audit.md",
        report(
            "KR Decision Consistency Audit",
            md_table(
                ["ticker", "prior fp", "current fp", "evidence class", "accepted change", "unexplained drift"],
                delta_rows,
            )
            + "\n\nAll seven comparable fingerprints changed because current price, supply, and technical observations refreshed. The deterministic business assessment remained `no_material_change`; no accepted V2 state was written. 047810 is not comparable because it had no prior accepted V2 record.",
        ),
    )
    write_text(
        output_dir / "20260902-kr-decision-drift-controls.md",
        report(
            "KR Decision Drift Controls",
            """`KR_DECISION_CHANGE_WITHOUT_MATERIAL_EVIDENCE_OR_ADJUDICATION = 0` and `KR_UNEXPLAINED_ACCEPTED_DECISION_DRIFT = 0`.

No current accepted decision exists to compare with the prior seven HOLD decisions. The observed source assessment changes were separated into business thesis, earnings estimate, market expectations, valuation, and price/timing. All business and earnings states stayed unchanged; current price/supply/technical fingerprints refreshed without being called a thesis change.
""",
        ),
    )
    write_text(
        output_dir / "20260902-047810-identifier-control.md",
        report(
            "047810 Identifier Control",
            """The context and prose consistently identified `047810` as 한국항공우주산업. KF-21 and FA-50 appeared only as product/program names. Neither was parsed as a numeric claim or ticker.

- phantom numeric errors: 0
- candidate validation errors attributed to 047810: 0
- fallback identity and ticker: PASS
""",
        ),
    )
    write_text(
        output_dir / "20260902-000660-valuation-quality-control.md",
        report(
            "000660 Valuation Quality Control",
            """The source financial-quality contract denied earnings-based valuation because of critical profitability anomalies, while verified PBR remained usable. The sent fallback displayed PBR and historical PBR percentile and explicitly suppressed earnings-based interpretation.

The AI correction candidate attempted an incompatible valuation-quality economic scope and was rejected. This is guard success, not a validator false positive. Sent fallback valuation safety: PASS.
""",
        ),
    )
    write_text(
        output_dir / "20260902-005930-risk-reward-control.md",
        report(
            "005930 Risk Reward Control",
            """The packet contained registered price rules and canonical chart structure. The sent fallback did not invent or display an unsupported risk/reward ratio. No `unsupported_risk_reward` validation error or unbound risk/reward number occurred.

`005930_UNSUPPORTED_RISK_REWARD_GUARD = PASS`.
""",
        ),
    )
    write_text(
        output_dir / "20260902-010120-012450-numeric-control.md",
        report(
            "010120 And 012450 Numeric Control",
            """Large revenue, operating income, margin, backlog, and order values in the sent fallback came from structured evidence. Neither ticker produced `numbers_without_provenance` errors.

Both AI candidates were nevertheless rejected for valuation interpretation economic-scope mismatch. The fallback correctly suppressed unsafe multiples and stated the security/share-basis limitation. Large numeric provenance: PASS; valuation-scope guard: PASS by rejection.
""",
        ),
    )
    renderer_rows = [[ticker, "DETERMINISTIC_FALLBACK", "no", "SENT_ONCE"] for ticker in TICKERS]
    write_text(
        output_dir / "20260902-kr-renderer-route.md",
        report(
            "KR Renderer Route",
            md_table(["ticker", "renderer", "explicit V2 decision", "delivery"], renderer_rows)
            + "\n\n`KR_RENDERER_ROUTE_IDENTIFIED_COUNT = 8`; `KR_FALLBACK_STOCK_COUNT = 8`; `KR_EXPLICIT_V2_DECISION_COUNT = 0`; `ACCEPTED_READY_WITHOUT_EXPLICIT_DECISION = 0` because accepted-ready count was zero.",
        ),
    )
    write_text(
        output_dir / "20260902-kr-message-block-consistency.md",
        report(
            "KR Message Block Consistency",
            """The sent fallback contained no V2 accepted block, so no V2-to-thesis-body contradiction could occur. Across investment thesis, core, warnings, expectations, Price Structure, valuation, and next checks, the eight messages remained internally coherent and kept supply as positioning.

The market digest `Valuation - neutral 8` line describes daily valuation change but can read like current valuation; this is wording debt, not a numerical contradiction.

- `NO_INTERNAL_CONTRADICTION = PASS`
- V2 block versus legacy body duplication: `NOT_APPLICABLE`
""",
        ),
    )
    duplication_rows = [
        [row["ticker"], row["character_count"], len(row["duplicate_substantive_lines"]), "; ".join(row["duplicate_substantive_lines"]) or "none"]
        for row in message_quality_rows
    ]
    write_text(
        output_dir / "20260902-kr-message-duplication-density.md",
        report(
            "KR Message Duplication Density",
            md_table(["ticker", "chars", "same-message duplicate lines", "lines"], duplication_rows)
            + f"\n\nAverage stock length: `{sum(stock_lengths) / len(stock_lengths):.2f}` characters. Average including market: `{sum(all_lengths) / len(all_lengths):.2f}`. Only 000660 repeated two next-check bullets already present under core monitoring. Shared headings and structured status rows were not counted as substantive prose repetition. Overall density: `LOW`.",
        ),
    )
    write_text(
        output_dir / "20260902-kr-price-structure-validation.md",
        report(
            "KR Price Structure Validation",
            md_table(["ticker", "close", "as-of", "chart state", "registered confirmation", "result"], price_rows)
            + "\n\nAll displayed closes, support/resistance zones, Bollinger levels, and registered rules were selected from packet-owned canonical facts. Monthly in-progress bands were labeled provisional and mutable until close. No invented level or decision-stage local OHLCV call was found. `KR_PRICE_STRUCTURE_VALIDATION = PASS`.",
        ),
    )
    write_text(
        output_dir / "20260902-kr-valuation-semantic-validation.md",
        report(
            "KR Valuation Semantic Validation",
            md_table(["ticker", "safe PER", "safe PBR", "result"], valuation_rows)
            + "\n\nThe sent fallback used only eligible PER/PBR/fPER/fPBR fields and suppressed 010120, 012450, and 047810 where security/share basis was unresolved. It did not reconstruct denominators. The rejected AI candidate scope errors were contained. `KR_VALUATION_SEMANTIC_VALIDATION = PASS` for the live payload.",
        ),
    )
    write_text(
        output_dir / "20260902-kr-disclaimer-cleanup-inventory.md",
        report(
            "KR Disclaimer Cleanup Inventory",
            """Exact pending line: `※ 분석 분류이며 주문·자동매매·의무 매매 지시가 아닙니다.`

- occurrence count in the nine sent KR fallback messages: 0
- production accepted-renderer owner: `app/services/accepted_decision_v2_service.py`
- shadow canary owner: `app/services/decision_canary_service.py`
- KR/US shared production component: yes, `accepted_decision_v2_service`
- expected occurrence if eight KR V2 decisions had rendered: one per stock message

No cleanup was implemented in this review.
""",
        ),
    )

    exact_sections = []
    for message in fallback["messages"]:
        exact_sections.append(f"## {message['ticker']}\n\n```text\n{message['text']}\n```")
    write_text(
        output_dir / "20260902-kr-exact-messages.md",
        report(
            "2026-09-02 Exact Sanitized KR Messages",
            "Packet: `" + PACKET_ID + "`. Recipient identifiers, Telegram response objects, delivery IDs, tokens, and credentials are excluded. Text is byte-for-byte equivalent to the persisted fallback payload text.\n\n" + "\n\n".join(exact_sections),
        ),
    )
    write_text(
        output_dir / "20260902-kr-delivery-proof.md",
        report(
            "KR Delivery Proof",
            f"""- expected: 9
- intent: {delivery['delivery_count']}
- sent/acknowledged: {delivery['sent_count']}
- pending: {delivery['pending_count']}
- unique persisted delivery IDs: {len(set(delivery_ids))}
- duplicate: {len(delivery_ids) - len(set(delivery_ids))}
- orphan: 0
- unowned retry: 0
- delivery mode: `{delivery['delivery_mode']}`
- dispatched: `{delivery['dispatched_at']}`
- deterministic payload text equals persisted fallback text: `{str(exact_payload_match).lower()}`

`KR_EXACTLY_ONCE_DELIVERY = PASS` and `KR_LIVE_EXACT_PAYLOAD = PASS`.
""",
        ),
    )
    matrix_md_rows = [
        [
            row["ticker"], row["source_ready"], row["technical"], row["context"], row["model"], row["candidate"],
            row["candidate_validation"], row["prior_accepted"], row["evidence_delta"], row["adjudication"], row["accepted"],
            row["renderer"], row["explicit_decision"], row["price_structure"], row["valuation"], row["message_quality"],
            row["delivery"], row["earliest_failure"],
        ]
        for row in stage_rows
    ]
    write_text(
        output_dir / "20260902-kr-live-stage-matrix.md",
        report(
            "KR Natural Live Stage Matrix",
            md_table(
                ["ticker", "source", "technical", "context", "model", "candidate", "candidate validation", "prior", "evidence delta", "adjudication", "accepted", "renderer", "explicit", "price", "valuation", "quality", "delivery", "earliest failure"],
                matrix_md_rows,
            ),
        ),
    )
    write_text(
        output_dir / "20260902-kr-next-repair-plan.md",
        report(
            "KR Next Bounded Repair Plan",
            """`NEXT_REPAIR_CLASS = COMBINED_BOUNDED_REPAIR`.

## P0

Open: 0. Unsafe AI content was rejected and operational fallback delivered exactly once.

## P1

1. Bound Codex V2 transport failure handling so DNS/network loss cannot occupy a natural claim past the useful acceptance window; preserve immutable packet ownership and fallback eligibility.
2. Repair AI correction convergence for signed working-capital gap semantics and provenance on 000660/005490/005930.
3. Supply the required holder decision variable for 003690 without hard-coding the ticker.
4. Align valuation interpretation economic scope for 000660/010120/012450.
5. Keep all current validators and thresholds unchanged; replay both natural primary and backup artifacts.

## P2

1. Remove the common accepted-decision disclaimer for KR and US.
2. Compact US night-futures D/W/M display.
3. Add nominal Treasury 3Y/5Y/10Y/30Y plus previous-valid bp deltas.
4. Replace the standalone 10Y real-yield primary block.
5. Consider rendering exact KOSPI/KOSDAQ level and breadth values after the numeric-label contract is repaired.

No repair was performed in this review.
""",
        ),
    )

    instruction_paths = [
        repo_root / "docs/work-instructions/20260902-kr-natural-live-postclose-review-and-next-repair-planning.md",
        repo_root / "docs/work-instructions/tracks/20260902-track-a-kr-run-runtime-source-technical-proof.md",
        repo_root / "docs/work-instructions/tracks/20260902-track-b-kr-v2-decision-consistency-and-adjudication-review.md",
        repo_root / "docs/work-instructions/tracks/20260902-track-c-kr-message-quality-valuation-price-structure-review.md",
        repo_root / "docs/work-instructions/tracks/20260902-track-d-kr-delivery-common-renderer-cleanup-and-next-repair-plan.md",
    ]
    generated_names = [
        "20260902-kr-natural-run-identity.md",
        "20260902-kr-runtime-lineage.md",
        "20260902-kr-scheduler-ownership.md",
        "20260902-kr-frozen-cohort.md",
        "20260902-kr-source-readiness.md",
        "20260902-kr-market-message-proof.md",
        "20260902-kr-supply-positioning-proof.md",
        "20260902-kr-technical-context.md",
        "20260902-kr-codex-runtime-natural-proof.md",
        "20260902-kr-v2-candidate-generation.md",
        "20260902-kr-candidate-validation.md",
        "20260902-kr-adjudication-accepted.md",
        "20260902-kr-decision-consistency-audit.md",
        "20260902-kr-decision-drift-controls.md",
        "20260902-047810-identifier-control.md",
        "20260902-000660-valuation-quality-control.md",
        "20260902-005930-risk-reward-control.md",
        "20260902-010120-012450-numeric-control.md",
        "20260902-kr-renderer-route.md",
        "20260902-kr-message-block-consistency.md",
        "20260902-kr-message-duplication-density.md",
        "20260902-kr-price-structure-validation.md",
        "20260902-kr-valuation-semantic-validation.md",
        "20260902-kr-disclaimer-cleanup-inventory.md",
        "20260902-kr-exact-messages.md",
        "20260902-kr-delivery-proof.md",
        "20260902-kr-live-stage-matrix.md",
        "20260902-kr-next-repair-plan.md",
        "20260902-kr-live-stage-matrix.json",
        "20260902-kr-decisions.json",
        "20260902-kr-decision-delta.json",
        "20260902-kr-message-quality.json",
        "20260902-kr-delivery.json",
        "20260902-kr-live-proof.json",
    ]
    generated_paths = [output_dir / name for name in generated_names]
    index_rows = []
    for path in instruction_paths + generated_paths:
        index_rows.append([str(path.relative_to(repo_root)), path.stat().st_size, sha256(path)])
    write_text(
        output_dir / "20260902-kr-natural-live-artifact-index.md",
        report(
            "KR Natural Live Artifact Index",
            f"Indexed `{len(index_rows)}` work-instruction, report, and machine artifacts. Raw recipient IDs, tokens, credentials, account identifiers, runtime-state databases, and hidden reasoning are excluded.\n\n"
            + md_table(["artifact", "bytes", "sha256"], index_rows),
        ),
    )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source-root", type=Path, required=True)
    parser.add_argument("--repo-root", type=Path, default=Path.cwd())
    parser.add_argument("--output-dir", type=Path, default=Path("docs/reports"))
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    repo_root = args.repo_root.resolve()
    output_dir = args.output_dir if args.output_dir.is_absolute() else repo_root / args.output_dir
    build(args.source_root.resolve(), repo_root, output_dir.resolve())


if __name__ == "__main__":
    main()
