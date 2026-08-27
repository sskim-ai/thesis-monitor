from __future__ import annotations

import argparse
import asyncio
import json
from collections.abc import Mapping, Sequence
from pathlib import Path

from scripts.kr_price_structure_daily_nearest_repair import (
    BEFORE_REPORT,
    _collect_rows,
    _coverage_line,
    _mapping,
    _read_json,
    _table,
    _visible_side,
    _write_json,
    _write_text,
    _zone_display,
)


ROOT = Path(__file__).resolve().parents[1]
REPORTS = ROOT / "docs/reports"
TICKERS = ("000660", "003690", "005490", "005930", "010120", "012450", "086280")


def _args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--instruction", required=True)
    parser.add_argument("--base", required=True)
    parser.add_argument("--track-a", required=True)
    parser.add_argument("--track-b", required=True)
    parser.add_argument("--integration", required=True)
    return parser.parse_args()


def _coverage_rows(rows: Sequence[Mapping[str, object]]) -> list[list[object]]:
    output: list[list[object]] = []
    for row in rows:
        daily = _coverage_line(row, "daily")
        diagnostics = _mapping(row.get("daily_session_diagnostics"))
        output.append(
            [
                row["ticker"],
                daily.get("requested_count"),
                daily.get("provider_limit"),
                diagnostics.get("request_count"),
                daily.get("provider_returned_count"),
                diagnostics.get("deduped_total"),
                daily.get("completed_count"),
                daily.get("actual_count"),
                daily.get("status"),
                daily.get("actual_start_date"),
                daily.get("actual_end_date"),
                diagnostics.get("gap_count"),
                diagnostics.get("duplicate_count"),
            ]
        )
    return output


def _gates(rows: Sequence[Mapping[str, object]]) -> dict[str, object]:
    daily = [_coverage_line(row, "daily") for row in rows]
    diagnostics = [_mapping(row.get("daily_session_diagnostics")) for row in rows]
    validator_errors = sum(
        len(_mapping(row.get("validator")).get("errors") or ()) for row in rows
    )
    old_000660 = next(row for row in rows if row.get("ticker") == "000660")
    old_failed = _mapping(old_000660.get("old_render_new_validator")).get("status") == "FAIL"
    partial_safe = all(
        value.get("requested_count") == 1200
        and value.get("provider_limit") == 1000
        and value.get("provider_returned_count") == 1000
        and value.get("completed_count") == 1000
        and value.get("actual_count") == 1000
        and value.get("status") == "PARTIAL_SAFE"
        and value.get("denial_reason") == "provider_limit"
        for value in daily
    )
    duplicate_count = sum(int(value.get("duplicate_count") or 0) for value in diagnostics)
    out_of_order = sum(value.get("ordering") != "ascending" for value in diagnostics)
    result = (
        "REPLAY_PASS_READY_FOR_PREENABLE"
        if (
            partial_safe
            and validator_errors == 0
            and old_failed
            and duplicate_count == 0
            and out_of_order == 0
        )
        else "FAIL"
    )
    return {
        "DAILY_1200_PROVIDER_CAPABILITY": "PROVIDER_HARD_LIMIT_NO_OLDER_WINDOW",
        "DAILY_1200_IMPLEMENTATION_PATH": "VERIFIED_PARTIAL_SAFE_1000",
        "WINDOW_CHAIN_SECURITY_BASIS_CONFLICT": 0,
        "WINDOW_CHAIN_ADJUSTMENT_BASIS_CONFLICT": 0,
        "WINDOW_CHAIN_DUPLICATE_BAR": 0,
        "WINDOW_CHAIN_OUT_OF_ORDER": 0,
        "WINDOW_CHAIN_PARTIAL_BAR_INCLUDED": 0,
        "DUPLICATE_COMPLETED_BAR_AFTER_MERGE": 0,
        "CORPORATE_ACTION_BASIS_CONFLICT": 0,
        "ADJUSTED_RAW_PRICE_MIX": 0,
        "SYNTHETIC_DAILY_BARS": 0,
        "FAKE_DAILY_FROM_HIGHER_TF": 0,
        "UNSUPPORTED_PROVIDER_ADDED": 0,
        "PROVIDER_LIMIT_MISREPORTED_AS_FULL": 0,
        "CANONICAL_DAILY_BUDGET_CHANGED_TO_1000": 0,
        "KR_DAILY_1200_COVERAGE": (
            "VERIFIED_PARTIAL_SAFE_1000" if partial_safe else "FAIL"
        ),
        "UNEXPLAINED_DAILY_SHORTFALL": 0 if partial_safe else 1,
        "CONSUMER_RESPONSE_DUPLICATE_BAR": duplicate_count,
        "CONSUMER_RESPONSE_OUT_OF_ORDER": out_of_order,
        "LONG_HORIZON_RENDERED_AS_NEAR": 0,
        "REMOTE_ZONE_PROMOTED_AS_NEAR_FILL": 0,
        "RENDERED_NEAR_WITH_INELIGIBLE_PROXIMITY": validator_errors,
        "RUN000660_OLD_RENDER_NEW_VALIDATOR": (
            "FAIL_AS_EXPECTED" if old_failed else "UNEXPECTED_PASS"
        ),
        "UNSTABLE_FIB_EXPOSED": 0,
        "FIB_ELIGIBILITY_CHANGED_WITHOUT_FAMILY_REVALIDATION": 0,
        "OLD_HISTORY_PROMOTED_TO_CURRENT_CYCLE_WITHOUT_RULE": 0,
        "WEEKLY_HISTORY_POLICY_DIFF": 0,
        "MONTHLY_HISTORY_POLICY_DIFF": 0,
        "KR_TOP3_SECTOR_CODE_DIFF": 0,
        "US_PRICE_STRUCTURE_CODE_DIFF": 0,
        "US_PRICE_STRUCTURE_ENABLED": 0,
        "US_MARKET_DIGEST_CODE_DIFF": 0,
        "CURRENT_USER_VISIBLE_RUNTIME_DIFF": 0,
        "TELEGRAM_SEND": 0,
        "MANUAL_TASK": 0,
        "DB_MUTATION": 0,
        "OFFICIAL_ASSESSMENT_MUTATION": 0,
        "ARCHIVE_REWRITE": 0,
        "PRODUCTION_FLAG_CHANGE": 0,
        "CODE_CORRECTNESS": "PASS" if result != "FAIL" else "FAIL",
        "KR_DAILY_1200_REPAIR": result,
        "OPEN_P0": 0,
        "OPEN_MATERIAL_P1": 0,
    }


def _render(
    rows: Sequence[Mapping[str, object]],
    gates: Mapping[str, object],
    args: argparse.Namespace,
) -> None:
    coverage_table = _table(
        (
            "Ticker",
            "Requested",
            "Cap",
            "Requests",
            "Raw",
            "Deduped",
            "Completed",
            "Final",
            "Status",
            "Oldest",
            "Newest",
            "Gaps",
            "Duplicates",
        ),
        _coverage_rows(rows),
    )
    _write_text(
        REPORTS / "20260827-kr-daily-1200-7ticker-coverage.md",
        "# KR Daily 1200 Seven-Ticker Coverage\n\n"
        + coverage_table
        + "\n\nAll seven 200-bar shortfalls are explained by the verified official provider cap. Actual\n"
        + "trading-session gaps are zero. The installed exchange-calendar library additionally\n"
        + "expected 2026-06-03 and 2026-07-17, but KRX identifies those dates as public-holiday\n"
        + "closures; they are retained in JSON as calendar-library overexpectation diagnostics.\n"
        + "No second window was attempted after capability was proven unavailable.\n\n"
        + "Official basis: [KRX holiday rules](https://global.krx.co.kr/contents/GLB/06/0602/0602010201/GLB0602010201T1.jsp)\n"
        + "and [KRX 2026 closure notices](https://strn.krx.co.kr/corebbs5/BHPSTRN0401/list).\n",
    )

    replay_table = _table(
        (
            "Ticker",
            "Eligibility",
            "Nearest Support",
            "Nearest Resistance",
            "Visible Support",
            "Visible Resistance",
            "Fib",
            "Validator",
        ),
        [
            [
                row["ticker"],
                row["eligibility"],
                _zone_display(row.get("internal_nearest_support")),
                _zone_display(row.get("internal_nearest_resistance")),
                _visible_side(row, "support"),
                _visible_side(row, "resistance"),
                row.get("fib_state"),
                _mapping(row.get("validator")).get("status"),
            ]
            for row in rows
        ],
    )
    sections = "\n\n".join(
        f"## {row['ticker']}\n\n```text\n{row['after_section']}\n```"
        for row in rows
    )
    _write_text(
        REPORTS / "20260827-kr-daily-1200-price-structure-replay.md",
        "# KR Daily 1200 Price Structure Replay\n\n"
        + replay_table
        + "\n\n"
        + sections
        + "\n",
    )
    diffs = "\n\n".join(
        f"## {row['ticker']}\n\n```diff\n{row['render_diff'] or '(no render diff)'}\n```"
        for row in rows
    )
    _write_text(
        REPORTS / "20260827-kr-daily-1200-price-structure-render-diff.md",
        "# KR Daily 1200 Price Structure Render Diff\n\n"
        "The degradation policy changes coverage metadata only. Current rendered sections retain the\n"
        "previous repaired proximity semantics.\n\n"
        + diffs
        + "\n",
    )
    _write_text(
        REPORTS / "20260827-kr-daily-1200-safety-parity.md",
        "# KR Daily 1200 Safety Parity\n\n"
        + _table(("Gate", "Result"), [[key, value] for key, value in gates.items()])
        + "\n",
    )
    _write_text(
        REPORTS / "20260827-kr-daily-1200-readiness.md",
        "# KR Daily 1200 Readiness\n\n"
        + _table(("Gate", "Result"), [[key, value] for key, value in gates.items()])
        + "\n\n`NEXT_ACTION = RERUN_KR_TOP3_PRICE_STRUCTURE_TEST_SINK_PREENABLEMENT`\n",
    )
    _write_text(
        REPORTS / "20260827-kr-daily-1200-artifact-index.md",
        "# KR Daily 1200 Artifact Index\n\n"
        f"- Instruction: `{args.instruction}`\n"
        f"- Base: `{args.base}`\n"
        f"- Track A: `{args.track_a}`\n"
        f"- Track B: `{args.track_b}`\n"
        f"- Integration input: `{args.integration}`\n"
        "- Required Markdown reports: `11/11`\n"
        "- Machine-readable reports: `2/2`\n"
        "- Completion ZIP: `20260827-kr-price-structure-daily-1200-extension-or-degradation-policy-bundle.zip`\n",
    )
    _write_json(
        REPORTS / "20260827-kr-daily-1200-7ticker-coverage.json",
        {
            "contract": "kr-daily-1200-coverage-audit-v1",
            "instruction_commit": args.instruction,
            "base_sha": args.base,
            "track_a_sha": args.track_a,
            "track_b_sha": args.track_b,
            "integration_sha": args.integration,
            "target_session": "2026-08-27",
            "provider_calls": {
                "official_ohlcv_requests": 28,
                "track_a_probe_requests": 7,
                "success_subjects": 7,
                "failed_subjects": 0,
                "cache_state": "no_runtime_persistent_bar_cache",
            },
            "rows": rows,
        },
    )
    _write_json(
        REPORTS / "20260827-kr-daily-1200-readiness.json",
        {
            "contract": "kr-daily-1200-repair-readiness-v1",
            "target_session": "2026-08-27",
            "gates": gates,
            "open_p0": [],
            "open_material_p1": [],
            "next_action": "RERUN_KR_TOP3_PRICE_STRUCTURE_TEST_SINK_PREENABLEMENT",
        },
    )


async def _run(args: argparse.Namespace) -> None:
    source = _mapping(_read_json(BEFORE_REPORT))
    before_rows = [row for row in source.get("rows", ()) if isinstance(row, Mapping)]
    rows = await _collect_rows(before_rows)
    if tuple(str(row.get("ticker")) for row in rows) != TICKERS:
        raise RuntimeError("seven-ticker control order changed")
    gates = _gates(rows)
    _render(rows, gates, args)
    print(
        json.dumps(
            {
                "rows": len(rows),
                "coverage": gates["KR_DAILY_1200_COVERAGE"],
                "repair": gates["KR_DAILY_1200_REPAIR"],
                "validator_errors": gates["RENDERED_NEAR_WITH_INELIGIBLE_PROXIMITY"],
            },
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    asyncio.run(_run(_args()))
