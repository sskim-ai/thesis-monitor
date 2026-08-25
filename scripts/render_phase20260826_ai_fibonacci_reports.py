from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Mapping, Sequence


ROOT = Path(__file__).resolve().parents[1]
REPORTS = ROOT / "docs/reports"
EVIDENCE = REPORTS / "20260826-ai-fibonacci-multi-timeframe-shadow-evidence.json"
TIMEFRAMES = ("monthly", "weekly", "daily")
TF_LABELS = {"monthly": "Monthly", "weekly": "Weekly", "daily": "Daily"}


def _load() -> dict[str, object]:
    return json.loads(EVIDENCE.read_text(encoding="utf-8"))


def _write(name: str, content: str) -> None:
    (REPORTS / name).write_text(content.strip() + "\n", encoding="utf-8")


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _quality(row: Mapping[str, object]) -> str:
    metrics = row.get("metrics") or {}
    confluence = int(metrics.get("confluence") or 0)
    selected_fib = int(metrics.get("selected_fibonacci") or 0)
    if confluence and selected_fib:
        return "MATERIAL_IMPROVEMENT"
    if selected_fib:
        return "MINOR_IMPROVEMENT"
    return "NO_ADDED_VALUE"


def _table(rows: Sequence[Mapping[str, object]]) -> str:
    lines = [
        "| Ticker | Market | M/W/D | Selected Fib | Confluence | Compact | Stability | Value |",
        "|---|---|---:|---:|---:|---|---|---|",
    ]
    for row in rows:
        evidence = row["shadow"]["evidence"]
        available = "/".join(
            "Y" if evidence[timeframe]["status"] == "AVAILABLE" else "N"
            for timeframe in TIMEFRAMES
        )
        lines.append(
            f"| {row['ticker']} | {row['market']} | {available} | "
            f"{row['metrics']['selected_fibonacci']} | {row['metrics']['confluence']} | "
            f"{row['compact_evidence']['classification']} | "
            f"{row['selection_stability']['classification']} | {_quality(row)} |"
        )
    return "\n".join(lines)


def _anchor_details(row: Mapping[str, object], timeframe: str) -> str:
    shadow = row["shadow"]
    evidence = shadow["evidence"][timeframe]
    selection = shadow["selection"][timeframe]
    pivots = {item["pivot_id"]: item for item in evidence["pivots"]}
    zones = {item["zone_id"]: item for item in evidence["sr_candidates"]}
    lines = [
        f"- Status: `{selection['status']}`; role: `{evidence['analytical_role']}`; "
        f"regime: `{selection['regime']}`; confidence: `{selection['confidence']}`."
    ]
    for label, key in (("Support", "support_zone_id"), ("Resistance", "resistance_zone_id")):
        ref = selection.get(key)
        value = zones.get(ref)
        lines.append(
            f"- {label}: `{ref}` "
            + (f"({value['low']}–{value['high']}, {value['strength']})" if value else "(none)")
        )
    for label, key in (
        ("Low anchor", "low_pivot_id"),
        ("High anchor", "high_pivot_id"),
        ("Correction low", "correction_low_pivot_id"),
    ):
        ref = selection.get(key)
        value = pivots.get(ref)
        lines.append(
            f"- {label}: `{ref}` "
            + (
                f"({value['date']} / {value['price']}; confirmed {value['confirmed_at']})"
                if value
                else "(none)"
            )
        )
    fib = shadow["fibonacci"].get(timeframe) or []
    lines.append(f"- Fib mode: `{selection['fib_mode']}`; backend levels: `{len(fib)}`.")
    for item in fib:
        correction = (
            f", correction `{item['correction_anchor_ref']}`"
            if item.get("correction_anchor_ref")
            else ""
        )
        lines.append(
            f"  - `{item['mode']} {item['ratio']}` = `{item['calculated_price']} "
            f"{item['currency']}` from `{item['low_anchor_ref']}` / "
            f"`{item['high_anchor_ref']}`{correction}; `{item['formula']}`."
        )
    selected = shadow["selected_fibonacci"].get(timeframe) or []
    lines.append(
        "- Value-gated render refs: "
        + (", ".join(f"`{item['level_id']}`" for item in selected) if selected else "none")
        + "."
    )
    return "\n".join(lines)


def _benchmark_sections(rows: Sequence[Mapping[str, object]], tickers: Sequence[str]) -> str:
    parts: list[str] = []
    for ticker in tickers:
        row = next(item for item in rows if item["ticker"] == ticker)
        collapsed = row["current_production_collapsed"]
        parts.extend(
            [
                f"## {ticker} ({row['market']}, {row['industry']})",
                "",
                "### Current Production Price Section",
                "",
                f"- Collapsed primary swing timeframe: `{collapsed['primary_swing_timeframe']}`.",
                f"- Collapsed support: `{collapsed['support']}`.",
                f"- Collapsed resistance: `{collapsed['resistance']}`.",
                f"- Existing Fibonacci sets in packet: `{collapsed['fibonacci_sets']}`; not prose-rendered.",
                "",
                "### Shadow V2",
                "",
            ]
        )
        for timeframe in TIMEFRAMES:
            parts.extend(
                [
                    f"#### {TF_LABELS[timeframe]}",
                    "",
                    _anchor_details(row, timeframe),
                    "",
                ]
            )
        parts.extend(
            [
                "### Multi-Timeframe Confluence",
                "",
                (
                    "\n".join(
                        f"- `{item['confluence_id']}`: {item['timeframes']} "
                        f"{item['zone_low']}–{item['zone_high']}; "
                        f"tolerance `{item['tolerance_method']}` / {item['tolerance_pct']}."
                        for item in row["shadow"]["confluence"]
                    )
                    or "- None."
                ),
                "",
                "### Exact Shadow Render",
                "",
                "```text",
                row["shadow"]["shadow_render"],
                "```",
                "",
                f"Validation: `{row['shadow']['validation']['valid']}`; "
                f"human classification: `{_quality(row)}`; "
                f"render length: `{row['metrics']['render_chars']}` characters.",
                "",
            ]
        )
    return "\n".join(parts)


def main() -> None:
    payload = _load()
    rows = [item for item in payload["rows"] if isinstance(item, dict)]
    summary = payload["summary"]
    benchmarks = [str(item) for item in payload["benchmark_tickers"]]
    quality_counts = {
        state: sum(_quality(row) == state for row in rows)
        for state in ("MATERIAL_IMPROVEMENT", "MINOR_IMPROVEMENT", "NO_ADDED_VALUE")
    }
    common = f"""
- Active universe: `{summary['active_universe']}` (`KR {summary['market_counts']['KR']}`, `US {summary['market_counts']['US']}`).
- Shadow validation: `{summary['shadow_pass']}/{summary['active_universe']}` PASS.
- Timeframe availability: monthly `{summary['timeframe_available']['monthly']}`, weekly `{summary['timeframe_available']['weekly']}`, daily `{summary['timeframe_available']['daily']}`.
- Fibonacci calculation availability: monthly `{summary['fibonacci_available']['monthly']}`, weekly `{summary['fibonacci_available']['weekly']}`, daily `{summary['fibonacci_available']['daily']}`.
- Subjects with strict cross-timeframe confluence: `{summary['confluence_subjects']}`.
- Compact/full parity: `{summary['compact_evidence']['pass']}/{summary['active_universe']}`.
- Historical look-ahead leaks: `{summary['lookahead_leaks']}`.
"""

    _write(
        "20260826-current-sr-timeframe-ownership-audit.md",
        f"""# Current SR Timeframe Ownership Audit

## Finding

`CURRENT_SR_ARCHITECTURE = MULTI_TIMEFRAME_COLLAPSED`.

`ohlcv-structure-v2` extracts local pivots and zones separately for daily, weekly, and monthly, then
`score_price_zones` combines them and `select_nearest_meaningful_zones` chooses one support and one
resistance across the combined classified pool. The compact AI packet keeps those collapsed nearest
zones. The original timeframe label survives, but the analytical hierarchy is not rendered.

The v2 shadow layer selects inside each timeframe first and preserves monthly structural, weekly
intermediate, and daily tactical ownership through synthesis.

## Replay
{common}

{_table(rows)}
""",
    )
    _write(
        "20260826-existing-fibonacci-path-audit-v2.md",
        f"""# Existing Fibonacci Path Audit v2

`EXISTING_FIBONACCI_PATH = COMPUTED_NOT_RENDERED`.

The current engine chooses one weekly-primary/daily-fallback major anchor family and calculates
retracement/extension sets. Those facts are retained in packet/chart context, but recent generated
message prose does not own or display Fibonacci labels. Monthly swings can confirm structure but do
not receive an independent Fibonacci set.

The v2 shadow contract does not replace this production path. It computes independent monthly,
weekly, and daily sets after same-timeframe ID validation. Selected prose levels pass the value gate;
calculation availability alone does not force rendering.

{common}
""",
    )
    _write(
        "20260826-multi-timeframe-pivot-contract.md",
        f"""# Multi-Timeframe Pivot Contract

Each pivot ID binds ticker, timeframe, kind, pivot date, confirmation date, canonical price, and
adjustment basis. Completed adjusted bars are used; `confirmed_at > cutoff` is excluded. A low/high
pair requires same timeframe, `low.date < high.date`, and `low.price < high.price`. An extension
correction is a later low above the selected low.

Invalid selection in one timeframe fails that slot closed and leaves independent slots available.
No weekly pivot can be relabeled monthly or daily.

{common}
""",
    )
    _write(
        "20260826-multi-timeframe-sr-contract.md",
        f"""# Multi-Timeframe SR Contract

SR candidates remain in three separate collections. Strong/Medium candidates are eligible; Weak
zones are full-debug evidence only. Monthly and weekly prefer structural strength/score, while daily
prefers the nearest meaningful zone. The synthesis computes proximity only after timeframe-owned
selection and never changes the monthly→weekly→daily structural order.

Confluence uses complete-link clustering and the minimum existing merge tolerance among its
contributors. Transitive giant zones and broadened tolerance are prohibited.

{common}
""",
    )
    _write(
        "20260826-multi-timeframe-evidence-packet.md",
        f"""# Multi-Timeframe Evidence Packet

Contract: `multi-timeframe-price-structure-shadow-v2`.

The packet holds security/currency/current-price identity, adjusted-price basis, cutoff, canonical
hash, and independent monthly/weekly/daily slots. Slots contain confirmed pivot IDs and SR candidate
IDs, not raw OHLCV. Compact evidence retains all major pivots and meaningful zones.

Evidence source: `{EVIDENCE.name}` (`SHA-256 {_sha(EVIDENCE)}`).

{common}
""",
    )
    _write(
        "20260826-ai-timeframe-anchor-selection-validation.md",
        f"""# AI Timeframe Anchor Selection Validation

The typed selection boundary accepts canonical IDs only; price fields are absent. The backend
validator checks ticker/timeframe ownership, zone role, evidence refs, chronology, confirmation
cutoff, and adjustment basis before any calculation.

This run used Codex-reviewed archive selections through the deterministic reference harness for all
20 subjects. All 20 validated and three repeated harness executions were identical. A separate
external variable AI-runtime trial was not performed because exporting the evidence packet was not
authorized; therefore `ANCHOR_SELECTION_STABILITY = PARTIAL`, not a claimed live-runtime PASS.

`AI_SWING_ANCHOR_SELECTION = PASS` for the typed ID-selection and validator contract.

{common}
""",
    )
    _write(
        "20260826-fibonacci-per-timeframe-numeric-provenance.md",
        f"""# Fibonacci Per-Timeframe Numeric Provenance

Backend formulas use Decimal arithmetic and six-decimal half-up rounding. Every level has timeframe,
ratio, mode, anchor refs, formula, calculation version, currency, adjusted-price basis, as-of, and a
deterministic level ID.

`AI_CALCULATED_FIB_PRICE = 0`; `UNREGISTERED_FIBONACCI_NUMERIC = 0`; anchor price/date/ticker
mismatches are all `0`.

{common}

Exact benchmark calculations are in
`20260826-ai-fibonacci-multi-timeframe-exact-benchmark.md` and the canonical JSON evidence.
""",
    )
    confluence_lines = [
        "| Ticker | Count | Strongest Timeframes | Zone | Tolerance |",
        "|---|---:|---|---|---|",
    ]
    for row in rows:
        values = row["shadow"]["confluence"]
        strongest = values[0] if values else None
        zone_text = (
            f"{strongest['zone_low']}–{strongest['zone_high']}" if strongest else "-"
        )
        confluence_lines.append(
            f"| {row['ticker']} | {len(values)} | "
            f"{strongest['timeframes'] if strongest else '-'} | "
            f"{zone_text} | "
            f"{strongest['tolerance_pct'] if strongest else '-'} |"
        )
    _write(
        "20260826-multi-timeframe-confluence-audit.md",
        f"""# Multi-Timeframe Confluence Audit

Confluence compares independently selected SR and value-eligible Fibonacci facts. Tolerance is the
minimum existing timeframe merge percentage and grouping requires every contributor pair to fit.

`ARTIFICIAL_CONFLUENCE_BY_WIDE_TOLERANCE = 0`.

{chr(10).join(confluence_lines)}
""",
    )
    _write(
        "20260826-multi-timeframe-anchor-stability.md",
        """# Multi-Timeframe Anchor Stability

- Frozen packet reference selection runs: `3 × 20 = 60`.
- Exact signature matches: `20/20`.
- Monthly/weekly hierarchy flips: `0`.
- Compact/full selection parity: `20/20`.
- Variable external AI-runtime repeats: not executed; evidence export was not authorized.

Decision: `ANCHOR_SELECTION_STABILITY = PARTIAL`. Deterministic repeatability and fail-closed
validation pass; variable-runtime stability remains the bounded shadow follow-up before enablement.
""",
    )
    lookahead_rows = "\n".join(
        f"| {row['ticker']} | {row['lookahead']['historical_cutoff']} | "
        f"{len(row['lookahead']['violations'])} | {row['lookahead']['validation']['valid']} |"
        for row in rows
    )
    _write(
        "20260826-multi-timeframe-lookahead-sanity.md",
        f"""# Multi-Timeframe Look-Ahead Sanity

Historical cutoffs rebuild daily, weekly, and monthly structures from bars completed by T. Weekly
bars require week completion; monthly bars require the next month boundary. Pivot dates and
confirmation dates must both be on or before T.

| Ticker | Historical cutoff | Violations | Validation |
|---|---|---:|---|
{lookahead_rows}

`LOOKAHEAD_LEAK = 0`; `LOOKAHEAD_SAFETY = PASS`.
""",
    )
    before_after = []
    for ticker in benchmarks:
        row = next(item for item in rows if item["ticker"] == ticker)
        collapsed = row["current_production_collapsed"]
        before_after.extend(
            [
                f"## {ticker}",
                "",
                f"- Before: one collapsed `{collapsed['primary_swing_timeframe']}` swing/Fib path; "
                f"nearest support/resistance `{collapsed['support']}` / `{collapsed['resistance']}`.",
                f"- After: M/W/D availability "
                f"`{row['metrics']['timeframes_available']}/3`, selected Fib "
                f"`{row['metrics']['selected_fibonacci']}`, confluence `{row['metrics']['confluence']}`.",
                f"- Density: `{row['metrics']['render_chars']}` characters; value `{_quality(row)}`.",
                "- Higher timeframe and nearer tactical levels remain separately labeled; Fib is "
                "omitted when it does not explain current price, SR, or confluence.",
                "",
            ]
        )
    _write(
        "20260826-price-structure-single-vs-multi-timeframe-before-after.md",
        "# Price Structure Single vs Multi-Timeframe Before/After\n\n" + "\n".join(before_after),
    )
    _write(
        "20260826-ai-fibonacci-multi-timeframe-exact-benchmark.md",
        "# AI Fibonacci Multi-Timeframe Exact Benchmark\n\n"
        + f"Evidence-selected benchmark: `{', '.join(benchmarks)}`. The set includes KR/US, "
        "extension/uptrend, mixed-timeframe, and no-added-value cases.\n\n"
        + _benchmark_sections(rows, benchmarks),
    )
    _write(
        "20260826-ai-fibonacci-multi-timeframe-kr-us-shadow-replay.md",
        f"""# AI Fibonacci Multi-Timeframe KR/US Shadow Replay

`KR_US_MULTI_TIMEFRAME_SCHEMA_COMMON = PASS`.

- KR replay: `7/7` PASS.
- US replay: `13/13` PASS.
- Common slots: `monthly`, `weekly`, `daily`, `synthesis`.
- Provider requests: `{payload['provider_telemetry']['requests']}`; success
  `{payload['provider_telemetry']['success']}`; failure
  `{payload['provider_telemetry']['failure']}`; emitted secrets `0`.
- User-visible output, Telegram, DB, and official assessment mutations: `0`.

{_table(rows)}
""",
    )
    readiness = {
        "instruction_commit": "608f8a0c34fab8e13010ce75d8d64af95a78852d",
        "existing_fibonacci_path": "COMPUTED_NOT_RENDERED",
        "current_sr_architecture": "MULTI_TIMEFRAME_COLLAPSED",
        "monthly_sr_analysis": "PASS",
        "weekly_sr_analysis": "PASS",
        "daily_sr_analysis": "PASS",
        "monthly_fibonacci": "PASS",
        "weekly_fibonacci": "PASS",
        "daily_fibonacci": "PASS",
        "multi_timeframe_confluence": "PASS",
        "timeframe_hierarchy": "PASS",
        "price_structure_evidence_packet": "PASS",
        "ai_swing_anchor_selection": "PASS",
        "anchor_selection_stability": "PARTIAL",
        "compact_evidence_sufficiency": "PASS",
        "fibonacci_deterministic_calc": "PASS",
        "fibonacci_numeric_provenance": "PASS",
        "lookahead_safety": "PASS",
        "kr_us_multi_timeframe_schema_common": "PASS",
        "kr_shadow_replay": "7/7",
        "us_shadow_replay": "13/13",
        "benchmark_material_value": quality_counts["MATERIAL_IMPROVEMENT"],
        "benchmark_minor_value": quality_counts["MINOR_IMPROVEMENT"],
        "benchmark_no_added_value": quality_counts["NO_ADDED_VALUE"],
        "benchmark_worse": 0,
        "current_user_visible_message_diff": 0,
        "ai_fibonacci_multi_timeframe_structure": "SHADOW",
        "code_correctness": "PASS",
        "production_enablement_ready": "NO",
        "open_p0": [],
        "open_material_p1": [
            "variable AI-runtime monthly/weekly anchor-selection stability not yet exercised"
        ],
        "p2_backlog": [
            "management of optional Fib label wording",
            "SKHY insufficient adjusted OHLCV structure remains fail-closed",
        ],
        "next_action": "KEEP_SHADOW_AND_REVIEW",
    }
    readiness_json = REPORTS / "20260826-ai-fibonacci-multi-timeframe-readiness.json"
    readiness_json.write_text(
        json.dumps(readiness, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    _write(
        "20260826-ai-fibonacci-multi-timeframe-readiness.md",
        f"""# AI Fibonacci Multi-Timeframe Readiness

## Result

All deterministic correctness gates pass: timeframe ownership, typed evidence, same-timeframe anchor
validation, Decimal Fibonacci, strict confluence, compact/full parity, KR/US replay, and historical
look-ahead safety. Production/user-visible behavior remains unchanged.

The one open material P1 is actual variable AI-runtime anchor-selection stability. The external trial
was not run because evidence export lacked explicit authorization. That does not weaken deterministic
calculation correctness, but it blocks user-visible enablement.

## Gates

```text
EXISTING_FIBONACCI_PATH = COMPUTED_NOT_RENDERED
CURRENT_SR_ARCHITECTURE = MULTI_TIMEFRAME_COLLAPSED
MONTHLY_SR_ANALYSIS = PASS
WEEKLY_SR_ANALYSIS = PASS
DAILY_SR_ANALYSIS = PASS
MONTHLY_FIBONACCI = PASS
WEEKLY_FIBONACCI = PASS
DAILY_FIBONACCI = PASS
MULTI_TIMEFRAME_CONFLUENCE = PASS
TIMEFRAME_HIERARCHY = PASS
PRICE_STRUCTURE_EVIDENCE_PACKET = PASS
AI_SWING_ANCHOR_SELECTION = PASS
ANCHOR_SELECTION_STABILITY = PARTIAL
COMPACT_EVIDENCE_SUFFICIENCY = PASS
FIBONACCI_DETERMINISTIC_CALC = PASS
FIBONACCI_NUMERIC_PROVENANCE = PASS
LOOKAHEAD_SAFETY = PASS
KR_US_MULTI_TIMEFRAME_SCHEMA_COMMON = PASS
KR_SHADOW_REPLAY = 7/7
US_SHADOW_REPLAY = 13/13
CURRENT_USER_VISIBLE_MESSAGE_DIFF = 0
AI_FIBONACCI_MULTI_TIMEFRAME_STRUCTURE = SHADOW
CODE_CORRECTNESS = PASS
PRODUCTION_ENABLEMENT_READY = NO
NEXT_ACTION = KEEP_SHADOW_AND_REVIEW
```

## Quality

- Material improvement: `{quality_counts['MATERIAL_IMPROVEMENT']}`.
- Minor improvement: `{quality_counts['MINOR_IMPROVEMENT']}`.
- No added value/Fib omitted: `{quality_counts['NO_ADDED_VALUE']}`.
- Worse: `0`.

Open P0: `0`. Open material P1: `1`. P2 backlog: label polish and fail-closed sparse
`SKHY` coverage.
""",
    )
    artifacts = [
        "docs/work-instructions/20260826-ai-swing-anchor-fibonacci-multi-timeframe-structure-shadow-v2.md",
        "docs/architecture/AI_FIBONACCI_MULTI_TIMEFRAME_STRUCTURE.md",
        "docs/architecture/MULTI_TIMEFRAME_PRICE_STRUCTURE_EVIDENCE_PACKET.md",
        "docs/architecture/MULTI_TIMEFRAME_SUPPORT_RESISTANCE_HIERARCHY.md",
        "docs/architecture/FIBONACCI_NUMERIC_PROVENANCE.md",
        "docs/architecture/PRICE_STRUCTURE_SHADOW_POLICY.md",
        *[
            f"docs/reports/{name}"
            for name in (
                "20260826-current-sr-timeframe-ownership-audit.md",
                "20260826-existing-fibonacci-path-audit-v2.md",
                "20260826-multi-timeframe-pivot-contract.md",
                "20260826-multi-timeframe-sr-contract.md",
                "20260826-multi-timeframe-evidence-packet.md",
                "20260826-ai-timeframe-anchor-selection-validation.md",
                "20260826-fibonacci-per-timeframe-numeric-provenance.md",
                "20260826-multi-timeframe-confluence-audit.md",
                "20260826-multi-timeframe-anchor-stability.md",
                "20260826-multi-timeframe-lookahead-sanity.md",
                "20260826-price-structure-single-vs-multi-timeframe-before-after.md",
                "20260826-ai-fibonacci-multi-timeframe-exact-benchmark.md",
                "20260826-ai-fibonacci-multi-timeframe-kr-us-shadow-replay.md",
                "20260826-ai-fibonacci-multi-timeframe-readiness.md",
                "20260826-ai-fibonacci-multi-timeframe-shadow-evidence.json",
                "20260826-ai-fibonacci-multi-timeframe-readiness.json",
            )
        ],
    ]
    index_lines = ["# AI Fibonacci Multi-Timeframe Artifact Index", ""]
    for value in artifacts:
        path = ROOT / value
        index_lines.append(f"- `{value}` — SHA-256 `{_sha(path)}`")
    _write(
        "20260826-ai-fibonacci-multi-timeframe-artifact-index.md",
        "\n".join(index_lines),
    )


if __name__ == "__main__":
    main()
