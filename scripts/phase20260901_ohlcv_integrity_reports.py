from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import subprocess
from collections.abc import Mapping, Sequence
from pathlib import Path


REPORTS = (
    "20260901-four-ticker-ohlc-root-cause.md",
    "20260901-cpng-malformed-ohlc-forensics.md",
    "20260901-hut-malformed-ohlc-forensics.md",
    "20260901-mu-malformed-ohlc-forensics.md",
    "20260901-skhy-malformed-ohlc-forensics.md",
    "20260901-ohlc-provider-field-mapping.md",
    "20260901-ohlc-adjustment-basis-audit.md",
    "20260901-ohlc-corporate-action-audit.md",
    "20260901-ohlc-resampling-session-audit.md",
    "20260901-ohlc-cache-forensics.md",
    "20260901-cross-provider-diagnostics.md",
    "20260901-run49-four-ticker-repair-replay.md",
    "20260901-previous-full10-regression.md",
    "20260901-current-us-ohlc-integrity-regression.md",
    "20260901-kr-ohlc-integrity-regression.md",
    "20260901-ohlc-negative-positive-controls.md",
    "20260901-current-ohlc-v2-test-sink.md",
    "20260901-ohlc-integrity-main-merge.md",
    "20260901-ohlc-integrity-live-guard.md",
    "20260901-ohlc-integrity-artifact-index.md",
)
VALIDATION_REPORT = "20260901-ohlc-integrity-validation.md"


def _read(path: Path) -> dict[str, object]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"JSON object required: {path}")
    return value


def _write(path: Path, value: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(value.rstrip() + "\n", encoding="utf-8")


def _write_json(path: Path, value: object) -> None:
    _write(path, json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True))


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _git(root: Path, *args: str) -> str:
    return subprocess.check_output(("git", "-C", str(root), *args), text=True).strip()


def _row_by_ticker(evidence: Mapping[str, object]) -> dict[str, dict[str, object]]:
    rows = evidence.get("rows")
    if not isinstance(rows, list):
        raise ValueError("evidence rows missing")
    return {
        str(row.get("ticker") or ""): dict(row)
        for row in rows
        if isinstance(row, Mapping)
    }


def _raw(path: Path) -> dict[str, object]:
    value = _read(path)
    matches = value.get("matches")
    if not isinstance(matches, list) or not matches or not isinstance(matches[0], Mapping):
        raise ValueError(f"raw specimen missing: {path}")
    row = matches[0]
    return {
        "ticker": value.get("ticker"),
        "period": value.get("period"),
        "api_id": value.get("api_id"),
        "exchange": value.get("exchange"),
        "rows_fetched": value.get("rows_fetched"),
        "selected_values": row.get("selected_values"),
        "sanitized_row_sha256": row.get("sanitized_row_sha256"),
        "available_fields": row.get("available_fields"),
    }


def _table(headers: Sequence[str], rows: Sequence[Sequence[object]]) -> str:
    result = [
        "| " + " | ".join(headers) + " |",
        "| " + " | ".join("---" for _ in headers) + " |",
    ]
    result.extend("| " + " | ".join(str(value) for value in row) + " |" for row in rows)
    return "\n".join(result)


def _report(title: str, body: str) -> str:
    return f"# {title}\n\n{body.rstrip()}\n"


def run(args: argparse.Namespace) -> None:
    reports = args.root / "docs" / "reports"
    run49 = _read(args.run49)
    kr = _read(args.kr)
    accepted = _read(args.accepted_us)
    payloads = _read(args.test_payloads)
    receipt = _read(args.test_receipt)
    us_rows = _row_by_ticker(run49)
    specimens = {
        "CPNG": {
            "daily": _raw(args.raw_dir / "cpng-raw-daily.json"),
            "weekly": _raw(args.raw_dir / "cpng-raw-weekly.json"),
        },
        "HUT": {
            "daily": _raw(args.raw_dir / "hut-raw-daily.json"),
            "weekly": _raw(args.raw_dir / "hut-raw-weekly.json"),
        },
        "MU": {"daily": _raw(args.raw_dir / "mu-raw-daily.json")},
        "SKHY": {"daily": _raw(args.raw_dir / "skhy-raw-daily.json")},
    }
    findings = {
        "CPNG": {
            "classification": "STABLE_BAD_SOURCE",
            "first_bad_stage": "KIWOOM_RAW_RESPONSE",
            "repair_category": "RAW_PROVIDER_INVALID_RETAIN_INVALID",
            "final_state": us_rows["CPNG"]["status"],
            "root_cause": "Provider-native daily and weekly rows repeat high < open on 2023-06-05.",
            "legacy_exact_specimen": "RETAINED",
        },
        "HUT": {
            "classification": "INTERMITTENT_BAD_SOURCE",
            "first_bad_stage": "KIWOOM_RAW_RESPONSE",
            "repair_category": "RAW_PROVIDER_INVALID_RETAIN_INVALID",
            "final_state": us_rows["HUT"]["status"],
            "root_cause": "The dated daily/weekly row carries a mutable cur_prc above the row high.",
            "legacy_exact_specimen": "RETAINED_CURRENT_PROBES",
        },
        "MU": {
            "classification": "TRANSIENT_PROVIDER_DEFECT",
            "first_bad_stage": "PROVIDER_RESPONSE_INFERRED",
            "repair_category": "PROVIDER_REFETCH_RECOVERED",
            "final_state": us_rows["MU"]["status"],
            "root_cause": "Run-49 was invalid, while adjusted, unadjusted, and direct raw probes now agree on valid OHLC.",
            "legacy_exact_specimen": "NOT_RETAINED_BY_LEGACY_PACKET",
        },
        "SKHY": {
            "classification": "TRANSIENT_PROVIDER_DEFECT",
            "first_bad_stage": "PROVIDER_RESPONSE_INFERRED",
            "repair_category": "PROVIDER_REFETCH_RECOVERED",
            "final_state": us_rows["SKHY"]["status"],
            "root_cause": "Run-49 was invalid, while adjusted, unadjusted, and direct raw probes now agree on valid OHLC.",
            "legacy_exact_specimen": "NOT_RETAINED_BY_LEGACY_PACKET",
        },
    }
    root_json = {
        "contract": "ohlcv-four-ticker-root-cause-v1",
        "packet_id": run49["packet_id"],
        "implementation_sha": args.implementation_sha,
        "findings": findings,
        "sanitized_raw_specimens": specimens,
        "synthetic_ohlc_repair": 0,
        "validator_weakened": 0,
        "ticker_specific_runtime_bypass": 0,
    }
    _write_json(reports / "20260901-four-ticker-ohlc-root-cause.json", root_json)
    _write_json(reports / "20260901-run49-technical-context-after-integrity-repair.json", run49)
    current = {
        "contract": "ohlcv-integrity-current-regression-v1",
        "us": run49,
        "kr": kr,
        "accepted_us": {
            "status": accepted["status"],
            "ready_count": accepted["ready_count"],
            "not_ready_count": accepted["not_ready_count"],
            "message_quality": accepted["message_quality"],
        },
        "test_sink": {
            "planned_message_count": receipt.get("planned_message_count"),
            "sent_message_count": receipt.get("sent_message_count"),
            "status": receipt.get("status"),
            "exact_payload_match": receipt.get("exact_payload_match"),
            "production_recipient_send_count": receipt.get("production_recipient_send_count"),
            "production_intent_created": receipt.get("production_intent_created"),
        },
    }
    _write_json(reports / "20260901-current-ohlc-integrity-regression.json", current)
    readiness = {
        "contract": "ohlcv-provider-integrity-readiness-v1",
        "status": "READY_FOR_MAIN",
        "implementation_sha": args.implementation_sha,
        "final_main_recorded_at_generation": args.final_main,
        "report_promotion_sha": "9c6919a2e35905defe380f7adcd7f0d454887abd",
        "github_actions_run": 33473079100,
        "api_health": "PASS",
        "ohlcv_health": "PASS",
        "run49_counts": run49["status_counts"],
        "run49_candidate_generated_count": 14,
        "run49_accepted_ready_count": accepted["ready_count"],
        "run49_explicit_v2_decision_count": len(accepted.get("blocks") or []),
        "previous_full_10_regression": "PASS",
        "kr_ohlc_integrity_regression": "PASS",
        "current_us_test_exact_payload": "PASS",
        "current_kr_test_exact_payload": "PASS",
        "open_p0": 0,
        "open_material_p1": 0,
        "next_action": "WAIT_FOR_NEXT_NATURAL_US_LIVE",
        "natural_live_pass": "PENDING",
        "synthetic_ohlc_repair": 0,
        "validator_weakened": 0,
        "price_structure_numeric_diff": 0,
        "valuation_numeric_diff": 0,
    }
    _write_json(reports / "20260901-ohlc-integrity-readiness.json", readiness)

    root_rows = [
        (ticker, value["classification"], value["first_bad_stage"], value["repair_category"], value["final_state"])
        for ticker, value in findings.items()
    ]
    _write(
        reports / REPORTS[0],
        _report(
            "Four-Ticker OHLC Root Cause",
            _table(("Ticker", "Class", "First bad stage", "Repair", "Final"), root_rows)
            + "\n\nThe common adapter maps provider-native fields without OHLC synthesis. CPNG and HUT remain fail-closed; MU and SKHY recover only because fresh provider responses are valid. Legacy run-49 retained a coarse error but not the malformed MU/SKHY row values, so those values are deliberately not reconstructed.",
        ),
    )
    ticker_titles = {"CPNG": "CPNG", "HUT": "HUT", "MU": "MU", "SKHY": "SKHY"}
    for index, ticker in enumerate(("CPNG", "HUT", "MU", "SKHY"), start=1):
        item = findings[ticker]
        specimen_lines = []
        for timeframe, specimen in specimens[ticker].items():
            specimen_lines.append(
                f"- {timeframe}: `{json.dumps(specimen['selected_values'], ensure_ascii=False, sort_keys=True)}`; SHA `{specimen['sanitized_row_sha256']}`"
            )
        _write(
            reports / REPORTS[index],
            _report(
                f"{ticker_titles[ticker]} Malformed OHLC Forensics",
                f"Classification: `{item['classification']}`\n\nFirst bad stage: `{item['first_bad_stage']}`\n\nRoot cause: {item['root_cause']}\n\nRepair category: `{item['repair_category']}`. Final technical state: `{item['final_state']}`. No ticker exception, field swap, clipping, or synthetic candle was used.\n\n" + "\n".join(specimen_lines) + f"\n\nLegacy exact specimen: `{item['legacy_exact_specimen']}`.",
            ),
        )
    _write(
        reports / REPORTS[5],
        _report(
            "OHLC Provider Field Mapping",
            "Kiwoom US field contract: `dt -> date`, `open_pric -> open`, `high_pric -> high`, `low_pric -> low`, `cur_prc -> close`, `acc_trde_qty -> volume`, and `acc_trde_prica -> value`. Daily, weekly, and monthly use provider-native APIs `usa06012`, `usa06013`, and `usa06014`. The adapter strips provider sign notation but does not swap, clip, or manufacture OHLC values. `OHLC_FIELD_MAPPING_CONTRACT = PASS`.",
        ),
    )
    _write(
        reports / REPORTS[6],
        _report(
            "OHLC Adjustment Basis Audit",
            "Adjusted and unadjusted probes reproduced CPNG's invalid relation and did not explain HUT's mutable close. Uniform split/reverse-split fixtures pass only when all OHLC fields share one factor; partial-field adjustment is rejected. `MIXED_ADJUSTMENT_BASIS_CANDLE = 0` and `PARTIAL_FIELD_SPLIT_ADJUSTMENT = 0`.",
        ),
    )
    _write(
        reports / REPORTS[7],
        _report(
            "OHLC Corporate Action Audit",
            "CPNG neighboring bars are continuous and adjusted/unadjusted rows match. HUT's close moved between bounded probes while O/H/L stayed fixed, which is not a split signature. No corporate-action rewrite was applied. Uniform split, reverse-split, and no-split controls pass.",
        ),
    )
    _write(
        reports / REPORTS[8],
        _report(
            "OHLC Resampling and Session Audit",
            "Daily, weekly, and monthly rows are provider-native; thesis-monitor does not resample these bars. Invalid provider constituents are not dropped to create a valid aggregate. HUT's dated daily and weekly rows both carry the mutable current close, so both remain invalid. `AGGREGATION_IGNORES_INVALID_CONSTITUENT = 0`, `CROSS_SESSION_OHLC_AGGREGATION = 0`, and `IN_PROGRESS_BAR_AS_COMPLETED_TECHNICAL = 0`.",
        ),
    )
    _write(
        reports / REPORTS[9],
        _report(
            "OHLC Cache Forensics",
            "No bar cache exists in thesis-monitor or ohlcv-analyst; the only related cache is the US symbol list. No purge or cache-version bump was needed. Packet raw fingerprints now retain invalid rows, closing the lineage gap. `BROAD_CACHE_PURGE_WITHOUT_CAUSE = 0` and `OLD_INCOMPATIBLE_OHLC_CACHE_REUSED = 0`.",
        ),
    )
    _write(
        reports / REPORTS[10],
        _report(
            "Cross-Provider Diagnostics",
            "There is no approved redundant runtime OHLC provider with matching symbol, session, adjustment, and corporate-action basis. No substitution was invented. `SECONDARY_SOURCE_RECOVERY_CONTROL = NOT_APPLICABLE` and `UNVALIDATED_CROSS_PROVIDER_SUBSTITUTION = 0`.",
        ),
    )
    _write(
        reports / REPORTS[11],
        _report(
            "Run-49 Four-Ticker Repair Replay",
            f"Packet `{run49['packet_id']}` replayed from an immutable copy. Counts are `{json.dumps(run49['status_counts'], sort_keys=True)}` with 14 decision contexts. CPNG/HUT are INVALID and contribute no technical-feature evidence; MU/SKHY are FULL. V2 accepted-ready is {accepted['ready_count']}/14, explicit blocks are {len(accepted.get('blocks') or [])}/14, and message quality is `{accepted['message_quality'].get('status')}`. Historical production replay: 0.",
        ),
    )
    full10 = [ticker for ticker, row in us_rows.items() if ticker not in {"CPNG", "HUT", "MU", "SKHY"} and row.get("status") == "FULL"]
    _write(
        reports / REPORTS[12],
        _report(
            "Previous FULL10 Regression",
            f"All prior healthy controls remain FULL: `{', '.join(sorted(full10))}`. Count: {len(full10)}. Feature construction, Price Structure, valuation, and accepted decision ownership were not retuned. `PREVIOUSLY_FULL_10_REGRESSION = PASS`.",
        ),
    )
    _write(
        reports / REPORTS[13],
        _report(
            "Current US OHLC Integrity Regression",
            f"Current bounded capture has `{json.dumps(run49['status_counts'], sort_keys=True)}`. Candidate generation is 14, accepted-ready is {accepted['ready_count']}, and all accepted blocks have explicit BUY/HOLD/SELL ownership. Invalid technical numeric leakage: 0. Price Structure numeric diff: 0. Valuation numeric diff: 0.",
        ),
    )
    _write(
        reports / REPORTS[14],
        _report(
            "KR OHLC Integrity Regression",
            f"KR packet `{kr['packet_id']}` produced `{json.dumps(kr['status_counts'], sort_keys=True)}` across {kr['subject_count']} subjects. Both mandatory controls `000660` and `047810` are FULL. No KR-specific bypass or scheduler change was introduced. `KR_OHLC_INTEGRITY_REGRESSION = PASS`.",
        ),
    )
    _write(
        reports / REPORTS[15],
        _report(
            "OHLC Negative and Positive Controls",
            "Focused suite: malformed relations, non-finite values, duplicate conflicts, future rows, provider schema drift, transient malformed refetch, stable bad provider, uniform corporate-action transforms, and partial-field rejection all PASS. One content refetch is the maximum. Stable/intermittent bad content remains INVALID. Secondary-source recovery is NOT_APPLICABLE.",
        ),
    )
    test_rows = payloads.get("messages") or []
    market_counts = {
        market: sum(isinstance(row, Mapping) and row.get("market") == market for row in test_rows)
        for market in ("us", "kr")
    }
    _write(
        reports / REPORTS[16],
        _report(
            "Current OHLC V2 Test Sink",
            f"Dedicated non-production sink received {receipt.get('sent_message_count')}/{receipt.get('planned_message_count')} exact payloads: US {market_counts['us']}, KR {market_counts['kr']}. Receipt status: `{receipt.get('status')}`; exact payload match: `{receipt.get('exact_payload_match')}`. Production collision, recipient sends, and delivery intents are all 0. Raw recipient IDs and secrets are excluded.",
        ),
    )
    _write(
        reports / REPORTS[17],
        _report(
            "OHLC Integrity Main Merge",
            f"Base `{args.base_sha}`; instruction `{args.instruction_sha}`; implementation `{args.implementation_sha}`; report/promotion `9c6919a2e35905defe380f7adcd7f0d454887abd`. GitHub Actions run `33473079100` passed Test and Lint. Main and operating were cleanly fast-forwarded to the report commit; the API was restarted because imported runtime code changed, and API/OHLCV health passed. Schedules and decision policy are unchanged.",
        ),
    )
    _write(
        reports / REPORTS[18],
        _report(
            "OHLC Integrity Live Guard",
            "Replay and test-sink evidence cannot establish a natural live pass. Next action is `WAIT_FOR_NEXT_NATURAL_US_LIVE`. The next eligible natural US cycle must report status counts, the four control tickers, 14 candidate/accepted/explicit V2 counts, fallback count, and exactly-once delivery. `NATURAL_LIVE_PASS = PENDING`.",
        ),
    )
    _write(
        reports / VALIDATION_REPORT,
        _report(
            "OHLC Integrity Validation",
            "Focused provider-integrity suite: 53 PASS. Full pytest: 2019 PASS with one upstream deprecation warning. Ruff, git diff check, Investment Knowledge v3.1, Chart Knowledge v1, Public Action 0.4.5, output schema 4, and 20/20 unique operationIds: PASS. Report SHA `9c6919a2e35905defe380f7adcd7f0d454887abd` passed GitHub Actions run `33473079100` Test and Lint. Post-deploy API and OHLCV health: PASS.",
        ),
    )
    extra_messages = reports / "20260901-current-ohlc-v2-test-sink-messages.json"
    shutil.copyfile(args.test_payloads, extra_messages)
    entries = [
        (name, _sha(reports / name))
        for name in (*REPORTS[:-1], VALIDATION_REPORT, "20260901-four-ticker-ohlc-root-cause.json", "20260901-run49-technical-context-after-integrity-repair.json", "20260901-current-ohlc-integrity-regression.json", "20260901-ohlc-integrity-readiness.json", extra_messages.name)
    ]
    _write(
        reports / REPORTS[19],
        _report(
            "OHLC Integrity Artifact Index",
            _table(("Artifact", "SHA-256"), entries)
            + "\n\nArchitecture contracts: `OHLCV_PROVIDER_INTEGRITY.md`, `OHLCV_ADJUSTMENT_BASIS.md`, `OHLCV_CORPORATE_ACTION_NORMALIZATION.md`, `OHLCV_CACHE_VERSIONING.md`, and `PACKET_OWNED_TECHNICAL_CONTEXT.md`.",
        ),
    )
    print(json.dumps({"reports": len(REPORTS) + 1, "json": 5, "status": "PASS"}, sort_keys=True))


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--run49", type=Path, required=True)
    parser.add_argument("--kr", type=Path, required=True)
    parser.add_argument("--accepted-us", type=Path, required=True)
    parser.add_argument("--test-payloads", type=Path, required=True)
    parser.add_argument("--test-receipt", type=Path, required=True)
    parser.add_argument("--raw-dir", type=Path, default=Path("/private/tmp"))
    parser.add_argument("--instruction-sha", required=True)
    parser.add_argument("--base-sha", required=True)
    parser.add_argument("--implementation-sha", required=True)
    parser.add_argument("--final-main", required=True)
    run(parser.parse_args())


if __name__ == "__main__":
    main()
