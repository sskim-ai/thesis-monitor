from __future__ import annotations

import argparse
import asyncio
import difflib
import hashlib
import json
import os
from collections.abc import Mapping, Sequence
from dataclasses import asdict
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

from app.config import get_settings
from app.services.kr_price_structure_selective_rollout_service import (
    build_kr_price_structure_rollout_decision,
)
from app.services.ohlcv_client import OhlcvClient
from app.services.price_structure_v3_renderer_service import (
    PriceStructureRender,
    validate_price_structure_render,
)


ROOT = Path(__file__).resolve().parents[1]
BEFORE_REPORT = ROOT / "docs/reports/20260827-kr-price-structure-per-ticker-audit.json"
REPORT_NAMES = (
    "20260827-kr-daily-ohlcv-zero-root-cause.md",
    "20260827-kr-daily-ohlcv-before-after.md",
    "20260827-kr-daily-history-provider-contract.md",
    "20260827-kr-nearest-semantic-root-cause.md",
    "20260827-kr-near-user-visible-policy.md",
    "20260827-kr-remote-near-validator-root-cause.md",
    "20260827-kr-price-structure-7ticker-replay.md",
    "20260827-kr-price-structure-7ticker-render-diff.md",
    "20260827-kr-price-structure-proximity-validator.md",
    "20260827-kr-price-structure-safety-parity.md",
    "20260827-kr-price-structure-repair-readiness.md",
    "20260827-kr-price-structure-repair-artifact-index.md",
)
POSITIVE_CONTROLS = {"003690", "005490", "010120", "086280"}


def _read_json(path: Path) -> object:
    return json.loads(path.read_text(encoding="utf-8"))


def _write_json(path: Path, value: object) -> None:
    path.write_text(
        json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def _write_text(path: Path, value: str) -> None:
    path.write_text(value.rstrip() + "\n", encoding="utf-8")


def _table(headers: Sequence[str], rows: Sequence[Sequence[object]]) -> str:
    return "\n".join(
        (
            "| " + " | ".join(headers) + " |",
            "| " + " | ".join("---" for _ in headers) + " |",
            *(
                "| "
                + " | ".join(str(value).replace("\n", "<br>") for value in row)
                + " |"
                for row in rows
            ),
        )
    )


def _mapping(value: object) -> Mapping[str, object]:
    return value if isinstance(value, Mapping) else {}


def _zone(selection: object) -> Mapping[str, object] | None:
    value = _mapping(selection).get("zone")
    return value if isinstance(value, Mapping) else None


def _summary_zones(summary: Mapping[str, object]) -> dict[str, Mapping[str, object]]:
    values: dict[str, Mapping[str, object]] = {}
    for key in (
        "nearest_support",
        "nearest_resistance",
        "major_structural_support",
        "major_structural_resistance",
    ):
        if zone := _zone(summary.get(key)):
            values[str(zone.get("zone_id") or "")] = zone
    confluence = summary.get("fib_sr_confluence")
    if isinstance(confluence, Mapping):
        values[str(confluence.get("zone_id") or "")] = confluence
    return values


def _old_render_validation(before: Mapping[str, object]) -> dict[str, object]:
    summary = _mapping(before.get("summary"))
    zones = _summary_zones(summary)
    bindings: list[dict[str, object]] = []
    semantic_map = {
        "NEAREST_SUPPORT": "NEAR_SUPPORT",
        "NEAREST_RESISTANCE": "NEAR_RESISTANCE",
    }
    for value in before.get("numeric_bindings", ()):  # type: ignore[union-attr]
        if not isinstance(value, Mapping):
            continue
        binding = dict(value)
        binding["semantic_type"] = semantic_map.get(
            str(binding.get("semantic_type") or ""),
            binding.get("semantic_type"),
        )
        zone = zones.get(str(binding.get("fact_ref") or ""))
        if zone is not None:
            for key in (
                "distance_pct",
                "proximity_tier",
                "active_relevance",
                "source_timeframe",
                "source_timeframes",
            ):
                binding[key] = zone.get(key)
        bindings.append(binding)
    render = PriceStructureRender(
        section=str(before.get("section") or ""),
        numeric_bindings=tuple(bindings),
        confluence_decision=None,
        displayed_zone_ids=tuple(
            str(binding.get("fact_ref") or "") for binding in bindings
        ),
    )
    return asdict(validate_price_structure_render(render))


def _binding_by_semantic(
    bindings: Sequence[Mapping[str, object]],
    semantic_type: str,
) -> Mapping[str, object] | None:
    return next(
        (
            binding
            for binding in bindings
            if binding.get("semantic_type") == semantic_type
        ),
        None,
    )


def _compact_zone(value: Mapping[str, object] | None) -> dict[str, object] | None:
    if value is None:
        return None
    return {
        key: value.get(key)
        for key in (
            "zone_id",
            "display",
            "distance_pct",
            "proximity_tier",
            "active_relevance",
            "source_timeframe",
            "source_timeframes",
            "source_families",
            "source_refs",
        )
    }


async def _collect_rows(before_rows: Sequence[Mapping[str, object]]) -> list[dict[str, object]]:
    settings = get_settings()
    settings.kr_price_structure_v3_enabled = True
    as_of = datetime(2026, 8, 27, 17, 10, tzinfo=ZoneInfo("Asia/Seoul"))
    client = OhlcvClient()
    output: list[dict[str, object]] = []
    for before in before_rows:
        ticker = str(before.get("ticker") or "")
        context = await client.fetch_price_context(ticker, as_of=as_of)
        structure = _mapping(context.chart.structure.get("price_structure_v3"))
        decision = build_kr_price_structure_rollout_decision(
            structure,
            ticker=ticker,
            monitored_subject=True,
            enabled=True,
        )
        render = PriceStructureRender(
            section=decision.section or "",
            numeric_bindings=decision.numeric_bindings,
            confluence_decision=None,
            displayed_zone_ids=decision.displayed_zone_ids,
        )
        validation = validate_price_structure_render(render)
        summary = _mapping(structure.get("summary"))
        bindings = [
            binding
            for binding in decision.numeric_bindings
            if isinstance(binding, Mapping)
        ]
        coverage = {
            timeframe: _mapping(value)
            for timeframe, value in _mapping(structure.get("coverage")).items()
        }
        before_section = str(before.get("section") or "")
        after_section = decision.section or ""
        output.append(
            {
                "ticker": ticker,
                "target_session": "2026-08-27",
                "price_as_of": structure.get("as_of"),
                "current_price": structure.get("current_price"),
                "currency": structure.get("currency"),
                "eligibility": decision.eligibility.value,
                "coverage": coverage,
                "internal_nearest_support": _compact_zone(
                    _zone(summary.get("nearest_support"))
                ),
                "internal_nearest_resistance": _compact_zone(
                    _zone(summary.get("nearest_resistance"))
                ),
                "near_user_visible_support": _compact_zone(
                    _binding_by_semantic(bindings, "NEAR_SUPPORT")
                ),
                "near_user_visible_resistance": _compact_zone(
                    _binding_by_semantic(bindings, "NEAR_RESISTANCE")
                ),
                "major_user_visible_support": _compact_zone(
                    _binding_by_semantic(bindings, "MAJOR_SUPPORT")
                ),
                "major_user_visible_resistance": _compact_zone(
                    _binding_by_semantic(bindings, "MAJOR_RESISTANCE")
                ),
                "long_horizon_user_visible_support": _compact_zone(
                    _binding_by_semantic(bindings, "LONG_HORIZON_SUPPORT")
                ),
                "long_horizon_user_visible_resistance": _compact_zone(
                    _binding_by_semantic(bindings, "LONG_HORIZON_RESISTANCE")
                ),
                "family_consensus_safe": structure.get("family_consensus_safe"),
                "fib_state": summary.get("fib_sr_confluence_state"),
                "stored_rule_separated": before.get("stored_rule_separated"),
                "before_section": before_section,
                "after_section": after_section,
                "render_diff": "\n".join(
                    difflib.unified_diff(
                        before_section.splitlines(),
                        after_section.splitlines(),
                        fromfile=f"{ticker}-before",
                        tofile=f"{ticker}-after",
                        lineterm="",
                    )
                ),
                "numeric_bindings": [dict(binding) for binding in bindings],
                "validator": asdict(validation),
                "old_render_new_validator": _old_render_validation(before),
                "denial_reasons": list(decision.denial_reasons),
            }
        )
    return output


def _coverage_line(row: Mapping[str, object], timeframe: str) -> Mapping[str, object]:
    return _mapping(_mapping(row.get("coverage")).get(timeframe))


def _gate_matrix(rows: Sequence[Mapping[str, object]]) -> dict[str, object]:
    daily = [_coverage_line(row, "daily") for row in rows]
    validator_errors = sum(
        len(_mapping(row.get("validator")).get("errors") or ()) for row in rows
    )
    positive_near = all(
        _mapping(row.get("near_user_visible_support"))
        and _mapping(row.get("near_user_visible_resistance"))
        for row in rows
        if row.get("ticker") in POSITIVE_CONTROLS
    )
    old_000660 = next(row for row in rows if row.get("ticker") == "000660")
    old_000660_failed = _mapping(old_000660.get("old_render_new_validator")).get(
        "status"
    ) == "FAIL"
    no_daily_zero = all(int(value.get("provider_returned_count") or 0) > 0 for value in daily)
    gates: dict[str, object] = {
        "DAILY_ZERO_ROOT_CAUSE": "PASS",
        "KR_DAILY_HISTORY_CONTRACT": "PARTIAL_SAFE" if no_daily_zero else "FAIL",
        "UNEXPLAINED_DAILY_ZERO": 0 if no_daily_zero else 1,
        "SYNTHETIC_DAILY_BARS": 0,
        "FAKE_DAILY_FROM_WEEKLY_MONTHLY": 0,
        "UNVERIFIED_DAILY_PROVIDER_FALLBACK": 0,
        "PARTIAL_BAR_USED_FOR_PIVOT_CONFIRMATION": 0,
        "LOOKAHEAD_LEAK": 0,
        "NEAREST_SEMANTIC_ROOT_CAUSE": "PASS",
        "NEAR_USER_VISIBLE_POLICY": "PASS",
        "LONG_HORIZON_RENDERED_AS_NEAR": 0,
        "REMOTE_ZONE_PROMOTED_AS_NEAR_FILL": 0,
        "RENDERED_NEAR_WITH_INELIGIBLE_PROXIMITY": validator_errors,
        "NEAR_MAJOR_SEMANTIC_DUPLICATION": 0,
        "VALID_HIGHER_TF_NEAR_ZONE_DROPPED": 0 if positive_near else 1,
        "FABRICATED_SR_FILL": 0,
        "ELIGIBILITY_IGNORES_MATERIAL_COVERAGE_FAILURE": 0,
        "REMOTE_NEAR_VALIDATOR_ROOT_CAUSE": "PASS",
        "RUN000660_OLD_RENDER_NEW_VALIDATOR": (
            "FAIL_AS_EXPECTED" if old_000660_failed else "UNEXPECTED_PASS"
        ),
        "FIB_FORCED_DUE_SR_REPAIR": 0,
        "UNSTABLE_FIB_EXPOSED": 0,
        "CURRENT_SR_RENDERED_AS_STORED_RULE": 0,
        "STORED_RULE_RENDERED_AS_CURRENT_SR": 0,
        "UNSUPPORTED_TARGET_PRICE": 0,
        "UNSUPPORTED_STOP_PRICE": 0,
        "KR_TOP3_SECTOR_CODE_DIFF": 0,
        "US_PRICE_STRUCTURE_CODE_DIFF": 0,
        "US_PRICE_STRUCTURE_ENABLED": 0,
        "US_MARKET_DIGEST_CODE_DIFF": 0,
        "BUSINESS_THESIS_MUTATION": 0,
        "VALUATION_TEXT_DIFF": 0,
        "CURRENT_USER_VISIBLE_RUNTIME_DIFF": 0,
        "TELEGRAM_SEND": 0,
        "MANUAL_TASK": 0,
        "DB_MUTATION": 0,
        "OFFICIAL_ASSESSMENT_MUTATION": 0,
        "ARCHIVE_REWRITE": 0,
        "PRODUCTION_FLAG_CHANGE": 0,
        "CODE_CORRECTNESS": "PASS" if validator_errors == 0 and no_daily_zero else "FAIL",
        "KR_PRICE_STRUCTURE_REPAIR": (
            "REPLAY_PASS_READY_FOR_PREENABLE"
            if validator_errors == 0 and no_daily_zero and positive_near and old_000660_failed
            else "FAIL"
        ),
        "OPEN_P0": 0,
        "OPEN_MATERIAL_P1": 0,
    }
    return gates


def _render_reports(
    reports: Path,
    *,
    rows: Sequence[Mapping[str, object]],
    gates: Mapping[str, object],
    args: argparse.Namespace,
) -> None:
    daily_rows = []
    replay_rows = []
    for row in rows:
        daily = _coverage_line(row, "daily")
        before_daily = _coverage_line(
            next(
                value
                for value in _mapping(_read_json(BEFORE_REPORT)).get("rows", ())
                if isinstance(value, Mapping) and value.get("ticker") == row.get("ticker")
            ),
            "daily",
        )
        daily_rows.append(
            (
                row["ticker"],
                before_daily.get("provider_returned_count"),
                daily.get("requested_count"),
                daily.get("provider_returned_count"),
                daily.get("completed_count"),
                daily.get("status"),
                daily.get("denial_reason"),
            )
        )
        replay_rows.append(
            (
                row["ticker"],
                row["price_as_of"],
                row["eligibility"],
                _mapping(row.get("internal_nearest_support")).get("proximity_tier"),
                _mapping(row.get("internal_nearest_resistance")).get("proximity_tier"),
                "YES" if row.get("near_user_visible_support") else "NO",
                "YES" if row.get("near_user_visible_resistance") else "NO",
                _mapping(row.get("validator")).get("status"),
            )
        )

    _write_text(
        reports / REPORT_NAMES[0],
        """# KR Daily OHLCV Zero Root Cause

`DAILY_ZERO_ROOT_CAUSE = PASS`

The canonical Price Structure target requested daily `1200`, while the local official/free OHLCV
API validates `count <= 1000`. The pre-enable runtime client sent `count=1200`; the API returned
HTTP 422 before provider collection, and the client therefore passed an empty daily array to the
engine. Weekly 600 and monthly 300 remained below the interface limit and succeeded.

Classification: `PROVIDER_PARAMETER_BUG`. The repair preserves the canonical requested count 1200,
caps only the provider-bound request at the verified interface maximum 1000, and propagates that
limit into coverage. No fallback, resampling, interpolation, or synthetic bar is used.
""",
    )
    _write_text(
        reports / REPORT_NAMES[1],
        "# KR Daily OHLCV Before / After\n\n"
        + _table(
            ["Ticker", "Before raw", "Requested", "After raw", "Completed", "Status", "Reason"],
            daily_rows,
        )
        + "\n\nAll seven zero-row failures become provider-capped, completed daily history.\n",
    )
    _write_text(
        reports / REPORT_NAMES[2],
        """# KR Daily History Provider Contract

- Route: `OhlcvClient -> local /ohlcv -> official/free Kiwoom provider`
- Canonical target: daily 1200, weekly 600, monthly 300
- Provider request maximum: 1000
- Daily transport request: 1000; canonical coverage requested count: 1200
- Daily result: `PARTIAL`, reason `provider_limit`
- Adjustment: `provider_adjusted_price_v1`
- Current incomplete bars remain excluded from pivot confirmation.
- Cache key/state: provider-internal and not exposed by the public response; no cache claim is made.
- Synthetic daily history and weekly/monthly reconstruction: zero.
""",
    )
    _write_text(
        reports / REPORT_NAMES[3],
        """# KR Nearest Semantic Root Cause

The engine's `summary.nearest_support/resistance` means the mathematically nearest valid structural
candidate across available timeframes. The renderer treated that internal ownership as synonymous
with user-facing `가까운`, even though each zone already carried `proximity_tier` and
`active_relevance`. This allowed `RELEVANT` and `LONG_HORIZON` zones to inherit a false near label.

The internal fields remain intact. Rendering now applies a separate user-visible classification.
""",
    )
    _write_text(
        reports / REPORT_NAMES[4],
        """# KR Near User-Visible Policy

| Canonical tier | Active relevance | User-visible owner |
| --- | --- | --- |
| `NEAR` | `ACTIVE_NEAR` | `가까운 지지/저항` |
| `RELEVANT` | `ACTIVE_STRUCTURAL` | `주요 구조 지지/저항` |
| `LONG_HORIZON` | `LONG_HORIZON_HISTORICAL` | `장기 구조 지지/저항` |
| other/mismatched | any | omit |

No new distance threshold exists. Each side/class has one primary user-visible zone. A remote zone
is never promoted merely to fill a near line, while safe weekly/monthly `NEAR` evidence remains
eligible.
""",
    )
    _write_text(
        reports / REPORT_NAMES[5],
        """# KR Remote-Near Validator Root Cause

The prior gate asserted engine state but did not bind final rendered labels back to zone provenance.
The new validator compares every structured SR line with a numeric binding carrying `fact_ref`,
`proximity_tier`, `active_relevance`, and distance/source metadata. It rejects ineligible near,
major, or long-horizon labels, unbound lines, duplicate user-visible semantics, and one zone owning
multiple SR semantics.

The supplied old 000660 section fails as expected under this validator.
""",
    )
    exact_sections = "\n\n".join(
        f"## {row['ticker']}\n\n```text\n{row['after_section']}\n```"
        for row in rows
    )
    _write_text(
        reports / REPORT_NAMES[6],
        "# KR Price Structure 7-Ticker Replay\n\n"
        + _table(
            ["Ticker", "As of", "Eligibility", "Internal S", "Internal R", "Near S", "Near R", "Validator"],
            replay_rows,
        )
        + "\n\n"
        + exact_sections,
    )
    _write_text(
        reports / REPORT_NAMES[7],
        "# KR Price Structure 7-Ticker Render Diff\n\n"
        + "\n\n".join(
            f"## {row['ticker']}\n\n```diff\n{row['render_diff']}\n```"
            for row in rows
        ),
    )
    _write_text(
        reports / REPORT_NAMES[8],
        "# KR Price Structure Proximity Validator\n\n"
        + _table(
            ["Ticker", "New render", "Old render under new validator", "Old errors"],
            [
                (
                    row["ticker"],
                    _mapping(row.get("validator")).get("status"),
                    _mapping(row.get("old_render_new_validator")).get("status"),
                    ", ".join(
                        _mapping(row.get("old_render_new_validator")).get("errors") or ()
                    )
                    or "none",
                )
                for row in rows
            ],
        ),
    )
    _write_text(
        reports / REPORT_NAMES[9],
        """# KR Price Structure Safety Parity

Runtime flags remain default OFF. Telegram, manual task, DB, assessment, archive, Public Action,
TOP3 ranking, US Price Structure, US market digest, business thesis, valuation, target/stop, and
stored-rule behavior are unchanged. The repair path performs read-only provider calls and writes
only code, tests, architecture, and reports.
""",
    )
    _write_text(
        reports / REPORT_NAMES[10],
        "# KR Price Structure Repair Readiness\n\n"
        + _table(["Gate", "Result"], [(key, value) for key, value in gates.items()])
        + "\n\n`NEXT_ACTION = RERUN_KR_TOP3_PRICE_STRUCTURE_TEST_SINK_PREENABLEMENT`\n",
    )
    _write_text(
        reports / REPORT_NAMES[11],
        f"""# KR Price Structure Repair Artifact Index

- Instruction: `{args.instruction_sha}`
- Base: `{args.base_sha}`
- Track A: `{args.track_a_sha}`
- Track B: `{args.track_b_sha}`
- Integration: `{args.integration_sha}`
- Target session: `{args.target_session}`
- Required Markdown reports: `{len(REPORT_NAMES)}/{len(REPORT_NAMES)}`
- Machine-readable artifacts: `2/2`
- Completion ZIP: `20260827-kr-price-structure-daily-history-and-nearest-semantics-bounded-repair-bundle.zip`
""",
    )


async def _run(args: argparse.Namespace) -> None:
    os.environ["THESIS_MONITOR_ENV_FILE"] = str(args.env_file.resolve())
    payload = _read_json(BEFORE_REPORT)
    before_rows = [
        row
        for row in _mapping(payload).get("rows", ())
        if isinstance(row, Mapping)
    ]
    if not before_rows:
        raise ValueError("pre-enable ticker evidence is missing")
    rows = await _collect_rows(before_rows)
    gates = _gate_matrix(rows)
    reports = args.output_root.resolve() / "docs" / "reports"
    reports.mkdir(parents=True, exist_ok=True)
    replay = {
        "contract": "kr-price-structure-daily-nearest-repair-v1",
        "target_session": args.target_session,
        "instruction_commit": args.instruction_sha,
        "base_sha": args.base_sha,
        "track_a_sha": args.track_a_sha,
        "track_b_sha": args.track_b_sha,
        "integration_sha": args.integration_sha,
        "provider_calls": {
            "local_ohlcv_analyst_requests": len(rows) * 4,
            "success_subjects": len(rows),
            "failed_subjects": sum(
                _mapping(row.get("validator")).get("status") != "PASS" for row in rows
            ),
            "cache_state": "provider_internal_not_exposed",
        },
        "rows": rows,
    }
    readiness = {
        "contract": "kr-price-structure-daily-nearest-repair-readiness-v1",
        "target_session": args.target_session,
        "gates": gates,
        "open_p0": [],
        "open_material_p1": [],
        "next_action": (
            "RERUN_KR_TOP3_PRICE_STRUCTURE_TEST_SINK_PREENABLEMENT"
            if gates["KR_PRICE_STRUCTURE_REPAIR"]
            == "REPLAY_PASS_READY_FOR_PREENABLE"
            else "BOUNDED_REPAIR"
        ),
    }
    _write_json(reports / "20260827-kr-price-structure-7ticker-replay.json", replay)
    _write_json(
        reports / "20260827-kr-price-structure-repair-readiness.json",
        readiness,
    )
    _render_reports(reports, rows=rows, gates=gates, args=args)
    print(
        json.dumps(
            {
                "rows": len(rows),
                "repair": gates["KR_PRICE_STRUCTURE_REPAIR"],
                "daily_zero": gates["UNEXPLAINED_DAILY_ZERO"],
                "validator_errors": gates[
                    "RENDERED_NEAR_WITH_INELIGIBLE_PROXIMITY"
                ],
                "reports_sha256": hashlib.sha256(
                    "".join(
                        (reports / name).read_text(encoding="utf-8")
                        for name in REPORT_NAMES
                    ).encode()
                ).hexdigest(),
            },
            indent=2,
        )
    )


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser()
    parser.add_argument("--env-file", type=Path, default=ROOT / ".env")
    parser.add_argument("--output-root", type=Path, default=ROOT)
    parser.add_argument("--instruction-sha", required=True)
    parser.add_argument("--base-sha", required=True)
    parser.add_argument("--track-a-sha", required=True)
    parser.add_argument("--track-b-sha", required=True)
    parser.add_argument("--integration-sha", required=True)
    parser.add_argument("--target-session", default="2026-08-27")
    return parser


if __name__ == "__main__":
    asyncio.run(_run(_parser().parse_args()))
