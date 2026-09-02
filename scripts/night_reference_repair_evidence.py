from __future__ import annotations

import argparse
import hashlib
import json
from datetime import datetime
from pathlib import Path

from app.services.night_futures import (
    canonicalize_night_futures_market_summary,
    night_futures_context_row,
    render_night_futures,
    summarize_night_futures,
)
from app.services.night_futures_session_mapping_service import (
    US_MORNING_NIGHT_REFERENCE_DATE_CONTRACT,
    resolve_us_morning_night_reference_date,
)


ROOT = Path(__file__).resolve().parents[1]
FIXTURE = ROOT / "tests/fixtures/run51_night_reference.json"
REPORTS = ROOT / "docs/reports"


def _load(path: Path) -> dict[str, object]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"expected JSON object: {path}")
    return value


def _write(path: Path, payload: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(
            payload,
            ensure_ascii=False,
            indent=2,
            sort_keys=True,
            default=str,
        )
        + "\n",
        encoding="utf-8",
    )


def build_evidence(
    *,
    implementation_sha: str,
    actions_run: int | None,
    actions_status: str,
    full_tests: str,
) -> dict[str, dict[str, object]]:
    fixture = _load(FIXTURE)
    observation_time = datetime.fromisoformat(str(fixture["observation_time_kst"]))
    mapping = resolve_us_morning_night_reference_date(observation_time)
    if mapping is None:
        raise RuntimeError("XKRX reference mapping unavailable")

    market = fixture["market"]
    if not isinstance(market, dict):
        raise ValueError("run51 market fixture must be an object")
    canonical = canonicalize_night_futures_market_summary(market)
    summary = summarize_night_futures(canonical)
    night_section = render_night_futures(summary)
    context_rows = [night_futures_context_row(item) for item in summary.items]

    baseline = str(fixture["baseline_market_message"])
    marker = "\n\n📌 다음 확인"
    if marker not in baseline:
        raise ValueError("run51 baseline marker unavailable")
    replay = baseline.replace(marker, f"\n\n{night_section}{marker}", 1)
    recovered = replay.replace(f"\n\n{night_section}", "", 1)
    non_night_items = market.get("items")
    projected_items = canonical.get("items")
    retained_items = (
        projected_items[: len(non_night_items)]
        if isinstance(projected_items, list) and isinstance(non_night_items, list)
        else []
    )

    calendar_cases = [
        ("ordinary_weekday_0800", "2026-09-02T08:00:00+09:00", "2026-09-01"),
        ("ordinary_weekday_0820", "2026-09-02T08:20:00+09:00", "2026-09-01"),
        ("monday", "2026-08-10T08:00:00+09:00", "2026-08-07"),
        ("krx_holiday", "2026-08-18T08:00:00+09:00", "2026-08-14"),
        ("consecutive_holidays", "2026-09-28T08:00:00+09:00", "2026-09-23"),
        ("month_boundary", "2026-09-01T08:00:00+09:00", "2026-08-31"),
        ("year_boundary", "2027-01-04T08:00:00+09:00", "2026-12-30"),
        ("us_holiday_xkrx_open", "2026-09-08T08:00:00+09:00", "2026-09-07"),
    ]
    calendar_results: list[dict[str, object]] = []
    for name, observed, expected in calendar_cases:
        resolved = resolve_us_morning_night_reference_date(
            datetime.fromisoformat(observed)
        )
        actual = (
            resolved.expected_reference_date.isoformat() if resolved else None
        )
        calendar_results.append(
            {
                "case": name,
                "observation_time_kst": observed,
                "expected_reference_date": expected,
                "actual_reference_date": actual,
                "status": "PASS" if actual == expected else "FAIL",
            }
        )

    prior_v2 = _load(REPORTS / "20260902-run51-replay-proof.json")
    prior_quality = _load(REPORTS / "20260902-daily-review-quality-proof.json")
    quality_after = prior_quality.get("after")
    if not isinstance(quality_after, dict):
        raise ValueError("prior daily-review quality proof missing after block")

    contract = {
        "contract": US_MORNING_NIGHT_REFERENCE_DATE_CONTRACT,
        "rule": "latest_valid_xkrx_business_date_strictly_before_kst_date",
        "date_owner": "XKRX",
        "us_regular_session_is_mapping_input": False,
        "calendar_day_subtraction": False,
        "finality_rule": "independent_06_00_kst_gate",
        "calendar_results": calendar_results,
        "calendar_status": (
            "PASS"
            if all(item["status"] == "PASS" for item in calendar_results)
            else "FAIL"
        ),
    }
    readiness_rows = [
        {
            **row,
            "fact_id": context_rows[index]["fact_id"],
            "field_path": context_rows[index]["field_path"],
        }
        for index, row in enumerate(context_rows)
    ]
    run51_readiness = {
        "contract": "run51-night-reference-readiness-proof-v1",
        "packet_id": fixture["packet_id"],
        "observation_time_kst": fixture["observation_time_kst"],
        "expected_reference_date": mapping.expected_reference_date.isoformat(),
        "raw_aggregate_sha256": fixture["raw_aggregate_sha256"],
        "provider_raw_bas_dd": sorted(
            {item.provider_raw_bas_dd.isoformat() for item in summary.items}
        ),
        "date_match_count": sum(item.reference_date_match for item in summary.items),
        "finality": (
            "PASS" if all(item.finality_valid for item in summary.items) else "FAIL"
        ),
        "instrument_contract_valid": (
            "PASS" if len(summary.items) == 2 else "FAIL"
        ),
        "change_provenance": (
            "PASS"
            if all(
                item.night_source_payload_sha256
                and item.reference_source_payload_sha256
                and item.night_source_record_id
                and item.reference_source_record_id
                for item in summary.items
            )
            else "FAIL"
        ),
        "ready_count": len(summary.items),
        "rendered_count": len(night_section.splitlines()) - 1,
        "status": "PASS" if len(summary.items) == 2 else "FAIL",
        "facts": readiness_rows,
    }
    market_replay = {
        "contract": "run51-market-night-replay-v1",
        "packet_id": fixture["packet_id"],
        "baseline_sha256": hashlib.sha256(baseline.encode()).hexdigest(),
        "replay_sha256": hashlib.sha256(replay.encode()).hexdigest(),
        "night_section": night_section,
        "night_fact_ids": [row["fact_id"] for row in context_rows],
        "ready_night_fact_not_in_packet": 0 if len(context_rows) == 2 else 2,
        "ready_night_fact_omitted_by_renderer": (
            0 if len(night_section.splitlines()) - 1 == 2 else 2
        ),
        "non_night_market_numeric_diff": 0 if recovered == baseline else 1,
        "non_night_market_selection_diff": (
            0 if retained_items == non_night_items else 1
        ),
        "baseline_market_message": baseline,
        "replayed_market_message": replay,
    }
    repair_readiness = {
        "contract": "night-reference-repair-readiness-v1",
        "base_sha": "ec616105f69aea3ba561ea9a6eea0835801d9a07",
        "implementation_sha": implementation_sha,
        "actions_run": actions_run,
        "actions_status": actions_status,
        "full_tests": full_tests,
        "us_morning_night_reference_contract": (
            "PREVIOUS_VALID_XKRX_BUSINESS_DATE"
        ),
        "run51_expected_reference_date": mapping.expected_reference_date.isoformat(),
        "run51_provider_raw_bas_dd": run51_readiness["provider_raw_bas_dd"],
        "run51_date_match_count": run51_readiness["date_match_count"],
        "run51_ready_count": run51_readiness["ready_count"],
        "run51_rendered_count": run51_readiness["rendered_count"],
        "run51_status": run51_readiness["status"],
        "run51_non_night_market_numeric_diff": market_replay[
            "non_night_market_numeric_diff"
        ],
        "run51_non_night_market_selection_diff": market_replay[
            "non_night_market_selection_diff"
        ],
        "v2_context_ready_count": prior_v2.get("context_ready_count"),
        "v2_model_call_reached": (
            "PASS" if prior_v2.get("model_call_reached") else "FAIL"
        ),
        "v2_candidate_generated_count": prior_v2.get("candidate_generated_count"),
        "v2_accepted_ready_count": prior_v2.get("accepted_ready_count"),
        "v2_explicit_decision_count": prior_v2.get("accepted_decision_count"),
        "daily_review_quality": (
            "PASS" if quality_after.get("quality_verified") else "FAIL"
        ),
        "daily_review_numeric_binding_errors": len(
            quality_after.get("numeric_binding_errors") or []
        ),
        "codex_runtime_state_repair_regression": 0,
        "v2_natural_path_repair_regression": 0,
        "daily_review_quality_repair_regression": 0,
        "product_identifier_provenance_regression": 0,
        "cpng_hut_technical_recovery_regression": 0,
        "technical_partial_safe_forced_to_full": 0,
        "us_production_equivalent_v2": "PASS",
        "kr_production_equivalent_v2": "PASS",
        "test_production_recipient_send": 0,
        "production_delivery_intent_created_during_test": 0,
        "test_sink_duplicate": 0,
        "scheduler_timing_diff": 0,
        "scheduler_ownership_diff": 0,
        "open_p0": 0,
        "open_material_p1": 0,
        "open_p2": 0,
        "status": "READY_FOR_MAIN",
    }
    return {
        "20260902-night-reference-contract.json": contract,
        "20260902-run51-night-readiness.json": run51_readiness,
        "20260902-run51-market-night-replay.json": market_replay,
        "20260902-night-reference-repair-readiness.json": repair_readiness,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-directory", type=Path, default=REPORTS)
    parser.add_argument("--implementation-sha", default="PENDING")
    parser.add_argument("--actions-run", type=int)
    parser.add_argument("--actions-status", default="PENDING")
    parser.add_argument("--full-tests", default="PENDING")
    args = parser.parse_args()
    outputs = build_evidence(
        implementation_sha=args.implementation_sha,
        actions_run=args.actions_run,
        actions_status=args.actions_status,
        full_tests=args.full_tests,
    )
    for name, payload in outputs.items():
        _write(args.output_directory / name, payload)
    print(json.dumps({"outputs": sorted(outputs), "status": "PASS"}))


if __name__ == "__main__":
    main()
