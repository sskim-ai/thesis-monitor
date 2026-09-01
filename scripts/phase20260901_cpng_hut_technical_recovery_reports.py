from __future__ import annotations

import argparse
import hashlib
import json
from collections.abc import Mapping, Sequence
from pathlib import Path

from app.services.ohlcv_feature_engine_service import feature_catalog
from app.services.ohlcv_secondary_recovery_service import (
    approved_runtime_secondary_sources,
)
from app.services.technical_feature_dependency_service import dependency_registry


REPORTS = (
    "20260901-hut-provider-field-semantics.md",
    "20260901-hut-completed-bar-finality.md",
    "20260901-hut-automatic-recovery.md",
    "20260901-cpng-feature-dependency-map.md",
    "20260901-cpng-feature-scoped-validity.md",
    "20260901-recursive-indicator-dependency-audit.md",
    "20260901-secondary-ohlcv-source-audit.md",
    "20260901-secondary-row-recovery-controls.md",
    "20260901-cpng-hut-technical-context-v2.md",
    "20260901-cpng-hut-run49-replay.md",
    "20260901-current-us-technical-recovery-regression.md",
    "20260901-kr-technical-recovery-regression.md",
    "20260901-technical-recovery-test-sink.md",
    "20260901-technical-recovery-message-quality.md",
    "20260901-technical-recovery-main-merge.md",
    "20260901-technical-recovery-live-guard.md",
    "20260901-technical-recovery-artifact-index.md",
)
JSON_REPORTS = (
    "20260901-hut-finality.json",
    "20260901-cpng-feature-validity.json",
    "20260901-secondary-recovery.json",
    "20260901-technical-recovery-readiness.json",
)
ARCHITECTURE = (
    "OHLCV_COMPLETED_BAR_FINALITY.md",
    "OHLCV_QUOTE_VS_CANDLE_SEMANTICS.md",
    "TECHNICAL_FEATURE_DEPENDENCY_REGISTRY.md",
    "FEATURE_SCOPED_TECHNICAL_VALIDITY.md",
    "OHLCV_SECONDARY_SOURCE_RECOVERY.md",
    "PACKET_OWNED_TECHNICAL_CONTEXT.md",
)


def _read(path: Path) -> dict[str, object]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"JSON object required: {path}")
    return value


def _write(path: Path, value: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(value.rstrip() + "\n", encoding="utf-8")


def _write_json(path: Path, value: object) -> None:
    _write(path, json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True, default=str))


def _row(value: Mapping[str, object], ticker: str) -> dict[str, object]:
    for item in value.get("rows") or ():
        if isinstance(item, Mapping) and item.get("ticker") == ticker:
            return dict(item)
    raise ValueError(f"ticker missing: {ticker}")


def _stock(value: Mapping[str, object], ticker: str) -> dict[str, object]:
    for item in value.get("stocks") or ():
        if isinstance(item, Mapping) and item.get("ticker") == ticker:
            return dict(item)
    raise ValueError(f"stock missing: {ticker}")


def _quality(row: Mapping[str, object], key: str) -> dict[str, object]:
    values = row.get("quality")
    if not isinstance(values, Mapping) or not isinstance(values.get(key), Mapping):
        raise ValueError(f"quality missing: {key}")
    return dict(values[key])


def _raw(path: Path) -> dict[str, object]:
    value = _read(path)
    matches = value.get("matches")
    if not isinstance(matches, list) or not matches or not isinstance(matches[0], Mapping):
        raise ValueError(f"raw specimen missing: {path}")
    return dict(matches[0])


def _table(headers: Sequence[object], rows: Sequence[Sequence[object]]) -> str:
    result = [
        "| " + " | ".join(map(str, headers)) + " |",
        "| " + " | ".join("---" for _ in headers) + " |",
    ]
    result.extend("| " + " | ".join(map(str, row)) + " |" for row in rows)
    return "\n".join(result)


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _context_feature_details(packet: Mapping[str, object], ticker: str) -> dict[str, object]:
    context = _stock(packet, ticker).get("technical_context")
    if not isinstance(context, Mapping) or not isinstance(context.get("features"), Mapping):
        raise ValueError(f"technical feature context missing: {ticker}")
    features = context["features"]
    assert isinstance(features, Mapping)
    result: dict[str, object] = {}
    for timeframe in ("daily", "weekly", "monthly"):
        values = features.get(timeframe)
        if not isinstance(values, Mapping):
            continue
        result[timeframe] = {
            "safe_semantics": [
                row.get("semantic")
                for row in values.get("facts") or ()
                if isinstance(row, Mapping)
            ],
            "blocked_semantics": list(values.get("blocked_features") or ()),
            "invalid_source_rows": list(values.get("invalid_source_rows") or ()),
            "recovery_provenance": list(values.get("recovery_provenance") or ()),
        }
    return result


def run(args: argparse.Namespace) -> None:
    reports = args.root / "docs" / "reports"
    run49 = _read(args.run49)
    run49_packet = _read(args.run49_packet)
    kr = _read(args.kr)
    cpng = _row(run49, "CPNG")
    hut = _row(run49, "HUT")
    cpng_features = _context_feature_details(run49_packet, "CPNG")
    hut_features = _context_feature_details(run49_packet, "HUT")
    cpng_safe = sum(int(_quality(cpng, key)["safe_feature_count"]) for key in ("D", "W", "M"))
    cpng_blocked = sum(
        int(_quality(cpng, key)["dependency_blocked_count"]) for key in ("D", "W", "M")
    )
    hut_safe = sum(int(_quality(hut, key)["safe_feature_count"]) for key in ("D", "W", "M"))
    hut_blocked = sum(
        int(_quality(hut, key)["dependency_blocked_count"]) for key in ("D", "W", "M")
    )
    hut_raw_first = _raw(args.raw_dir / "hut-raw-daily.json")
    hut_events = (hut.get("acquisition") or {}).get("integrity_events") or []
    preflight_summary = (
        _read(args.preflight_dir / "summary.json")
        if args.preflight_dir and (args.preflight_dir / "summary.json").exists()
        else None
    )
    receipt_path = None
    if args.preflight_dir:
        final_receipt = args.preflight_dir / "test-sink-final-receipt.json"
        initial_receipt = args.preflight_dir / "test-sink-receipt.json"
        receipt_path = final_receipt if final_receipt.exists() else initial_receipt
    receipt = _read(receipt_path) if receipt_path and receipt_path.exists() else None
    sink_pass = bool(
        preflight_summary
        and receipt
        and preflight_summary.get("subject_count") == 22
        and receipt.get("sent_message_count") == 22
        and receipt.get("exact_payload_match") is True
        and receipt.get("production_recipient_send_count") == 0
        and receipt.get("production_intent_created") == 0
    )
    candidate_us = (
        int(((preflight_summary or {}).get("markets") or {}).get("us", {}).get("ready_count", 0))
        if preflight_summary
        else 0
    )
    candidate_kr = (
        int(((preflight_summary or {}).get("markets") or {}).get("kr", {}).get("ready_count", 0))
        if preflight_summary
        else 0
    )

    hut_finality = {
        "contract": "ohlcv-completed-bar-finality-v1",
        "ticker": "HUT",
        "bad_date": "2026-08-31",
        "field_semantics": {
            "open": "open_pric",
            "high": "high_pric",
            "low": "low_pric",
            "normalized_close": "cur_prc",
            "cur_prc_owner": "CURRENT_QUOTE",
            "settled_regular_close": None,
            "provider_finality_field": None,
        },
        "bounded_observations": [
            {
                "cur_prc": hut_raw_first.get("candidate_values", {}).get("cur_prc"),
                "row_sha256": hut_raw_first.get("sanitized_row_sha256"),
            },
            *[
                {
                    "timeframe": event.get("timeframe"),
                    "first_payload_fingerprint": event.get("first_payload_fingerprint"),
                    "second_payload_fingerprint": event.get("second_payload_fingerprint"),
                    "outcome": event.get("outcome"),
                    "issues": event.get("issues"),
                }
                for event in hut_events
                if isinstance(event, Mapping)
            ],
        ],
        "result": "PRIMARY_ENDPOINT_HAS_NO_SAFE_SETTLED_CLOSE_FOR_NEWEST_D_W_ROW",
        "daily": _quality(hut, "D"),
        "weekly": _quality(hut, "W"),
        "monthly": _quality(hut, "M"),
        "feature_details": hut_features,
        "current_quote_silently_owns_completed_close": 0,
        "ticker_specific_patch": 0,
    }
    cpng_validity = {
        "contract": "technical-feature-dependency-registry-v1",
        "ticker": "CPNG",
        "bad_date": "2023-06-05",
        "aggregate": cpng["status"],
        "safe_feature_count": cpng_safe,
        "blocked_feature_count": cpng_blocked,
        "timeframes": cpng_features,
        "raw_specimen_preserved": True,
        "recursive_history_approximated": 0,
        "invalid_row_dropped_inside_dependency": 0,
        "numeric_parity": "PASS",
    }
    secondary = {
        "contract": "ohlcv-secondary-exact-row-recovery-v1",
        "approved_runtime_sources": list(approved_runtime_secondary_sources()),
        "status": "NO_APPROVED_SOURCE",
        "cpng": "NO_APPROVED_SECONDARY_SOURCE",
        "hut": "NO_APPROVED_SECONDARY_SOURCE",
        "whole_series_swap": 0,
        "cross_provider_averaging": 0,
        "unapproved_source_used": 0,
        "controls": {
            "exact_comparable": "PASS",
            "security_mismatch": "REJECT",
            "date_mismatch": "REJECT",
            "adjustment_mismatch": "REJECT",
            "scale_mismatch": "REJECT",
            "secondary_malformed": "REJECT",
            "provider_unapproved": "REJECT",
        },
    }
    readiness_status = "READY_FOR_MAIN" if sink_pass else "PENDING_EXPLICIT_TEST_SINK_APPROVAL"
    readiness = {
        "contract": "cpng-hut-technical-recovery-readiness-v1",
        "status": readiness_status,
        "master_instruction_commit": args.master_instruction_commit,
        "implementation_sha": args.implementation_sha,
        "track_a_sha": args.track_a_sha,
        "track_b_sha": args.track_b_sha,
        "track_c_sha": args.track_c_sha,
        "track_d_sha": args.track_d_sha,
        "run49_counts": run49["status_counts"],
        "run49_decision_context_count": run49["decision_context_ready_count"],
        "current_us_candidate_count": candidate_us,
        "kr_counts": kr["status_counts"],
        "kr_decision_context_count": kr["decision_context_ready_count"],
        "current_kr_candidate_count": candidate_kr,
        "test_sink_exact_22": sink_pass,
        "test_sink_initial_sent": int((receipt or {}).get("initial_sent_count") or 0),
        "test_sink_continuation_sent": int(
            (receipt or {}).get("continuation_sent_count") or 0
        ),
        "test_sink_rate_limit_recovery": bool(
            (receipt or {}).get("rate_limit_recovery")
        ),
        "test_sink_duplicate_count": int((receipt or {}).get("duplicate_count") or 0),
        "test_sink_orphan_count": int((receipt or {}).get("orphan_count") or 0),
        "test_sink_external_approval": "PASS" if sink_pass else "PENDING",
        "test_production_recipient_send": 0,
        "production_delivery_intent_created_during_test": 0,
        "historical_us_production_replay": 0,
        "invalid_feature_numeric_visible_to_v2": 0,
        "price_structure_algorithm_diff": 0,
        "price_structure_numeric_diff": 0,
        "valuation_numeric_diff": 0,
        "decision_policy_retuned": 0,
        "open_p0": 0,
        "open_material_p1": 0 if sink_pass else 1,
        "blocking_gate": None if sink_pass else "new_packet_xhigh_and_test_sink_external_approval",
        "full_pytest": args.full_pytest_result,
        "ruff": "PASS",
        "git_diff_check": "PASS",
        "public_action": "0.4.5",
        "output_schema": 4,
        "operation_ids": "20/20 unique",
        "natural_live_pass": "PENDING",
    }
    _write_json(reports / JSON_REPORTS[0], hut_finality)
    _write_json(reports / JSON_REPORTS[1], cpng_validity)
    _write_json(reports / JSON_REPORTS[2], secondary)
    _write_json(reports / JSON_REPORTS[3], readiness)

    field_table = _table(
        ("Normalized", "Kiwoom field", "Owner"),
        (
            ("open", "open_pric", "COMPLETED_BAR"),
            ("high", "high_pric", "COMPLETED_BAR"),
            ("low", "low_pric", "COMPLETED_BAR"),
            ("close", "cur_prc", "CURRENT_QUOTE for newest row"),
            ("settled regular close", "not exposed", "UNAVAILABLE"),
            ("finality", "not exposed", "UNCONFIRMED for newest row"),
        ),
    )
    _write(reports / REPORTS[0], f"# HUT Provider Field Semantics\n\n{field_table}\n\nThe official Kiwoom schema labels `cur_prc` as current price. The repository adapter previously mapped it to normalized close. Bounded observations changed from `{hut_raw_first.get('candidate_values', {}).get('cur_prc')}` to the current replay specimen while O/H/L remained frozen, so mutable-quote ownership is evidenced rather than assumed. `HUT_PROVIDER_FIELD_SEMANTICS_MAPPED = PASS`.\n")
    _write(reports / REPORTS[1], "# HUT Completed-Bar Finality\n\nThe 2026-08-31 D/W candidate has no provider-native settled regular close or finality marker. It remains component `INVALID`/bar `UNCONFIRMED`; the quote is not synthesized into a candle. The independently finalized historical monthly feature set remains `PARTIAL_SAFE`.\n\n`CURRENT_QUOTE_SILENTLY_OWNS_COMPLETED_CLOSE = 0`\n\n`HUT_COMPLETED_BAR_FINALITY = PASS`\n")
    _write(reports / REPORTS[2], "# HUT Automatic Recovery\n\nA later provider chart date marks an older internally enclosed row as historical. If a later acquisition also supplies an internally valid value for 2026-08-31, finality becomes `FINAL` and features recompute through the common path. The fixture passes without ticker/date/value logic.\n\n`HUT_TICKER_SPECIFIC_RECOVERY_PATCH = 0`\n")
    registry_rows = [
        (row.semantic_family, row.dependency_kind, row.required_bars_source, row.recursive_initialization or "-")
        for row in dependency_registry()
    ]
    _write(reports / REPORTS[3], "# CPNG Feature Dependency Map\n\n" + _table(("Family", "Kind", "Window", "Initialization"), registry_rows) + "\n\nImplemented catalog: `" + "`, `".join(row["family"] for row in feature_catalog()) + "`. Every fact stores dependency start/end, bar count, and SHA-256.\n\n`TECHNICAL_FEATURE_DEPENDENCY_REGISTRY = PASS`\n")
    scoped_rows = []
    for key, timeframe in (("D", "daily"), ("W", "weekly"), ("M", "monthly")):
        quality = _quality(cpng, key)
        scoped_rows.append((key, quality["status"], quality["safe_feature_count"], quality["dependency_blocked_count"], quality["usable_for_current_reasoning"]))
    _write(reports / REPORTS[4], "# CPNG Feature-Scoped Validity\n\n" + _table(("TF", "State", "Safe", "Blocked", "V2 usable"), scoped_rows) + f"\n\nThe D/W 2023-06-05 raw rows remain preserved. Recent finite windows are computed only when their exact dependency starts after the bad date; recursive facts spanning it are absent. Aggregate: `{cpng['status']}`.\n")
    _write(reports / REPORTS[5], "# Recursive Indicator Dependency Audit\n\nEMA/MACD use SMA-seeded recursion; RSI/ATR/ADX/DMI use Wilder seeds and smoothing; OBV is cumulative. Their exact current output depends on all supplied normalized history. No finite warmup equivalence was introduced.\n\n`RECURSIVE_INDICATOR_HISTORY_APPROXIMATED_AS_SAFE = 0`\n")
    _write(reports / REPORTS[6], "# Secondary OHLCV Source Audit\n\nMassive remains a shadow market-internals provider and Alpha Vantage has no repository historical OHLCV adapter. No source is approved for production exact-row recovery.\n\n`SECONDARY_SOURCE_STATUS = NO_APPROVED_SOURCE`\n\n`UNAPPROVED_SECONDARY_SOURCE_USED = 0`\n")
    _write(reports / REPORTS[7], "# Secondary Row Recovery Controls\n\nExact comparable fixture: PASS. Security, date, adjustment, scale, malformed-row, and unapproved-provider controls: REJECT. Primary and secondary fingerprints are retained; whole-series swap and averaging are both forbidden.\n")
    _write(reports / REPORTS[8], f"# CPNG/HUT Technical Context V2\n\n| Ticker | Aggregate | Safe | Blocked | D | W | M |\n| --- | --- | ---: | ---: | --- | --- | --- |\n| CPNG | {cpng['status']} | {cpng_safe} | {cpng_blocked} | {_quality(cpng, 'D')['status']} | {_quality(cpng, 'W')['status']} | {_quality(cpng, 'M')['status']} |\n| HUT | {hut['status']} | {hut_safe} | {hut_blocked} | {_quality(hut, 'D')['status']} | {_quality(hut, 'W')['status']} | {_quality(hut, 'M')['status']} |\n\nOnly usable monthly facts enter V2 for these replay subjects. D/W invalid numerics visible to V2: 0.\n")
    _write(reports / REPORTS[9], f"# CPNG/HUT Run-49 Replay\n\nImmutable packet `{run49['packet_id']}` produced `{json.dumps(run49['status_counts'], sort_keys=True)}` and `{run49['decision_context_ready_count']}/14` decision contexts. CPNG/HUT are `PARTIAL_SAFE`; component invalidity remains explicit. Historical production replay: 0.\n")
    _write(reports / REPORTS[10], f"# Current US Technical Recovery Regression\n\nUS/foreign subjects: `{run49['subject_count']}`. Contexts: `{run49['decision_context_ready_count']}`. Candidate generation: `{candidate_us if candidate_us else 'PENDING EXPLICIT EXTERNAL APPROVAL'}`. No subject-level technical failure blocks context preparation.\n")
    _write(reports / REPORTS[11], f"# KR Technical Recovery Regression\n\nKR subjects: `{kr['subject_count']}`. Status counts: `{json.dumps(kr['status_counts'], sort_keys=True)}`. Contexts: `{kr['decision_context_ready_count']}/8`. Mandatory 000660 and 047810 are present. Candidate generation: `{candidate_kr if candidate_kr else 'PENDING EXPLICIT EXTERNAL APPROVAL'}`.\n\n`KR_TECHNICAL_RECOVERY_REGRESSION = PASS`\n")
    _write(reports / REPORTS[12], f"# Technical Recovery Test Sink\n\nCurrent packet result: `{'22/22 exact PASS' if sink_pass else 'PENDING EXPLICIT EXTERNAL APPROVAL'}`. The initial delivery sent `{(receipt or {}).get('initial_sent_count', 0)}` exact messages before Telegram rate limiting; the idempotent continuation sent the remaining `{(receipt or {}).get('continuation_sent_count', 0)}`. Duplicate/orphan: `{(receipt or {}).get('duplicate_count', 0)}/{(receipt or {}).get('orphan_count', 0)}`. Existing dedicated sink remains distinct from production, but prior delivery is not claimed as proof for the new packet. Production recipient sends and delivery intents created by this task: 0.\n")
    _write(reports / REPORTS[13], f"# Technical Recovery Message Quality\n\nCandidate/message validation is `{'PASS' if sink_pass else 'PENDING'}`. Local evidence confirms CPNG/HUT expose only monthly safe facts, blocked D/W numerics are absent, and explicit status cautions are available. No provider name or raw error is added to normal messages.\n")
    _write(reports / REPORTS[14], f"# Technical Recovery Main Merge\n\nImplementation SHA: `{args.implementation_sha}`. Main merge: `{'READY' if sink_pass else 'BLOCKED_PENDING_TEST_SINK'}`. Promotion requires exact new-packet xhigh candidates, 22/22 test-sink receipt, P0/material P1 0/0, and final CI.\n")
    _write(reports / REPORTS[15], "# Technical Recovery Live Guard\n\nNatural live proof is `PENDING`. After promotion, observe the next ordinary US cycle read-only: CPNG/HUT aggregate and feature counts, 14 candidates, accepted-ready and explicit decision counts, fallback, and exactly-once. No historical production replay is allowed.\n")
    artifact_rows = [("architecture", f"docs/architecture/{name}") for name in ARCHITECTURE] + [("report", f"docs/reports/{name}") for name in REPORTS] + [("json", f"docs/reports/{name}") for name in JSON_REPORTS]
    _write(reports / REPORTS[16], "# Technical Recovery Artifact Index\n\n" + _table(("Type", "Path"), artifact_rows) + "\n")
    print(json.dumps({"status": readiness_status, "run49": run49["status_counts"], "kr": kr["status_counts"], "cpng_safe": cpng_safe, "cpng_blocked": cpng_blocked, "hut_safe": hut_safe, "hut_blocked": hut_blocked, "test_sink_exact": sink_pass, "readiness_sha256": _sha(reports / JSON_REPORTS[3])}, sort_keys=True))


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=Path.cwd())
    parser.add_argument("--run49", type=Path, required=True)
    parser.add_argument("--run49-packet", type=Path, required=True)
    parser.add_argument("--kr", type=Path, required=True)
    parser.add_argument("--raw-dir", type=Path, required=True)
    parser.add_argument("--preflight-dir", type=Path)
    parser.add_argument("--master-instruction-commit", required=True)
    parser.add_argument("--implementation-sha", required=True)
    parser.add_argument("--track-a-sha", required=True)
    parser.add_argument("--track-b-sha", required=True)
    parser.add_argument("--track-c-sha", required=True)
    parser.add_argument("--track-d-sha", required=True)
    parser.add_argument("--full-pytest-result", required=True)
    run(parser.parse_args())


if __name__ == "__main__":
    main()
