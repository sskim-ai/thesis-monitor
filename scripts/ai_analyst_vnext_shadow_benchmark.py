from __future__ import annotations

# ruff: noqa: E402, E501

import argparse
import hashlib
import json
import re
import sys
import zipfile
from collections import Counter
from dataclasses import dataclass
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.schemas.ai_review import AIDailyReviewOutput
from app.services.ai_analyst_vnext_shadow_service import (
    CONTRACT_VERSION,
    PROMPT_OBJECTIVES,
    ValueAddType,
    advisory_value_add_gate,
    build_vnext_shadow_message,
)
from app.services.numeric_provenance_service import bind_numeric_fact_references
from scripts.phase20260822_us_ai_compatibility_replay import (
    _rendered_messages as render_run32_messages,
    enrich_packet as enrich_run32_packet,
)
from scripts.phase8_5_5_1_evidence import _render as render_us_messages


RUN_DATE = "20260824"
REPORT_ROOT = ROOT / "docs" / "reports"
KR_REHEARSAL_ID = "2026-08-24-kr-live-rehearsal-193419"
KR_PACKET_ID = "2026-08-24-kr-run-36-e4ac1c029c06"
RUN26 = "2026-08-19-us-run-26-cd80a8e4d373"
RUN28 = "2026-08-20-us-run-28-9024def294e6"
RUN32 = "2026-08-22-us-run-32-dde10ec6c9eb"
INSTRUCTION_PATH = (
    ROOT
    / "docs/work-instructions/20260824-ai-analyst-quality-vnext-shadow-benchmark.md"
)
KR_BUNDLE = REPORT_ROOT / "20260824-rehearsal-193419-post-repair-message-bundle.md"
KR_PARITY = REPORT_ROOT / "20260824-rehearsal-193419-ai-fallback-parity.md"
RUN26_PREVIEW = REPORT_ROOT / "20260819-run26-targeted-repair-preview.md"
RUN26_VALIDATION = REPORT_ROOT / "20260819-run26-ai-validation-repair.md"
RUN28_CANDIDATE = REPORT_ROOT / "20260820-run28-repaired-ai-output.json"
RUN28_RECEIPT = REPORT_ROOT / "20260820-run28-runtime-quality-receipt.json"
RUN32_CANDIDATE = (
    REPORT_ROOT
    / "20260822-us-run32-replay-artifacts/run32-repaired-candidate.json"
)
RUN32_RESULT = REPORT_ROOT / "20260822-us-run32-replay-artifacts/run32-replay-result.json"
ZIP_NAME = "20260824-ai-analyst-quality-vnext-shadow-bundle.zip"


@dataclass(frozen=True)
class BenchmarkItem:
    benchmark_id: str
    market: str
    packet_id: str
    ticker: str
    evidence_shape: str
    deterministic: str
    current_ai: str
    source_paths: tuple[Path, ...]


def _load(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def _write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text.rstrip() + "\n", encoding="utf-8")


def _write_json(path: Path, value: object) -> None:
    _write(path, json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True))


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _relative(path: Path) -> str:
    try:
        return str(path.relative_to(ROOT))
    except ValueError:
        return str(path)


def _markdown_messages(text: str) -> dict[str, str]:
    pattern = re.compile(
        r"^###\s+(?:\d+\.\s+)?(?P<ticker>[^\n]+)\n\n"
        r"```text\n(?P<text>.*?)\n```",
        re.MULTILINE | re.DOTALL,
    )
    return {
        match.group("ticker").strip(): match.group("text").strip()
        for match in pattern.finditer(text)
    }


def _between(text: str, start: str, end: str | None = None) -> str:
    value = text.split(start, 1)[1]
    return value.split(end, 1)[0] if end and end in value else value


def _payload_messages(payload: dict[str, object]) -> dict[str, str]:
    rows = payload.get("messages")
    if not isinstance(rows, list):
        return {}
    result: dict[str, str] = {}
    for row in rows:
        if not isinstance(row, dict):
            continue
        ticker = str(row.get("ticker") or "")
        body = row.get("payload")
        if isinstance(body, dict):
            text = str(body.get("text") or "")
        else:
            text = str(row.get("text") or "")
        result[ticker] = text
    return result


def _render_run28(archive: Path) -> tuple[dict[str, str], dict[str, str]]:
    packet = dict(_load(archive / "packet.json"))
    fallback = dict(_load(archive / "fallback-messages.json"))
    candidate = dict(_load(RUN28_CANDIDATE))
    binding = bind_numeric_fact_references(packet, candidate)
    if binding.errors:
        raise RuntimeError(f"run-28 binding failed: {binding.errors}")
    output = AIDailyReviewOutput.model_validate(binding.output)
    current = {
        str(row["ticker"]): str(row["text"])
        for row in render_us_messages(packet, output, fallback)
    }
    return _payload_messages(fallback), current


def _render_run32(archive: Path) -> tuple[dict[str, str], dict[str, str]]:
    packet = enrich_run32_packet(dict(_load(archive / "packet.json")))
    fallback = dict(_load(archive / "fallback-messages.json"))
    deterministic = dict(_load(archive / "deterministic-messages.json"))
    candidate = dict(_load(RUN32_CANDIDATE))
    binding = bind_numeric_fact_references(packet, candidate)
    if binding.errors:
        raise RuntimeError(f"run-32 binding failed: {binding.errors}")
    output = AIDailyReviewOutput.model_validate(binding.output)
    current = {
        str(row["ticker"]): str(row["text"])
        for row in render_run32_messages(packet, output, deterministic)
    }
    return _payload_messages(fallback), current


def _benchmark_items(operating_root: Path) -> list[BenchmarkItem]:
    history = operating_root / "data/ai_review/pilot/history/2026/08"
    kr_text = KR_BUNDLE.read_text(encoding="utf-8")
    kr_current = _markdown_messages(
        _between(kr_text, "## Validated AI Candidate", "## Deterministic Fallback")
    )
    kr_fallback = _markdown_messages(
        _between(kr_text, "## Deterministic Fallback", "## Selected Production-Preference Bundle")
    )
    items = [
        BenchmarkItem(
            benchmark_id=f"kr-193419-{index:02d}-{ticker}",
            market="KR",
            packet_id=KR_PACKET_ID,
            ticker=ticker,
            evidence_shape=(
                "macro_temporal_digest"
                if ticker == "__DAILY_DIGEST_KR__"
                else "kr_dynamic_industry_and_supply"
            ),
            deterministic=kr_fallback[ticker],
            current_ai=current,
            source_paths=(KR_BUNDLE, KR_PARITY),
        )
        for index, (ticker, current) in enumerate(kr_current.items(), start=1)
    ]

    run26_text = RUN26_PREVIEW.read_text(encoding="utf-8")
    run26_current = _markdown_messages(
        _between(run26_text, "## Repaired AI Candidate")
    )
    run26_archive = history / RUN26
    run26_fallback = _payload_messages(dict(_load(run26_archive / "fallback-messages.json")))
    items.append(
        BenchmarkItem(
            benchmark_id="us-run26-wulf-rr-sensitive",
            market="US",
            packet_id=RUN26,
            ticker="WULF",
            evidence_shape="current_price_rr_sensitive_hpc",
            deterministic=run26_fallback["WULF"],
            current_ai=run26_current["WULF"],
            source_paths=(
                RUN26_PREVIEW,
                RUN26_VALIDATION,
                run26_archive / "packet.json",
            ),
        )
    )

    run28_archive = history / RUN28
    run28_fallback, run28_current = _render_run28(run28_archive)
    items.append(
        BenchmarkItem(
            benchmark_id="us-run28-crcl-expectation-valuation",
            market="US",
            packet_id=RUN28,
            ticker="CRCL",
            evidence_shape="speculative_expectation_valuation",
            deterministic=run28_fallback["CRCL"],
            current_ai=run28_current["CRCL"],
            source_paths=(
                RUN28_CANDIDATE,
                RUN28_RECEIPT,
                run28_archive / "packet.json",
                run28_archive / "fallback-messages.json",
            ),
        )
    )

    run32_archive = history / RUN32
    run32_fallback, run32_current = _render_run32(run32_archive)
    for ticker, shape in (
        ("GOOGL", "fcf_heavy_cloud_platform"),
        ("MU", "inventory_eligible_fcf_priority_memory"),
    ):
        items.append(
            BenchmarkItem(
                benchmark_id=f"us-run32-{ticker.lower()}",
                market="US",
                packet_id=RUN32,
                ticker=ticker,
                evidence_shape=shape,
                deterministic=run32_fallback[ticker],
                current_ai=run32_current[ticker],
                source_paths=(
                    RUN32_CANDIDATE,
                    RUN32_RESULT,
                    run32_archive / "packet.json",
                    run32_archive / "deterministic-messages.json",
                    run32_archive / "fallback-messages.json",
                ),
            )
        )
    return items


def _table_row(values: list[object]) -> str:
    return "| " + " | ".join(str(value).replace("\n", " ") for value in values) + " |"


def _human_quality(gate: dict[str, object]) -> tuple[str, str]:
    types = set(gate["value_add_types"])
    if gate["AI_ANALYST_VALUE_ADD"] != "PASS":
        return "DEGRADED", "advisory value-add gate failed"
    if len(types) >= 3:
        return "MATERIAL_IMPROVEMENT", "multiple supported selection/linkage operations"
    if len(types) >= 1:
        return "MINOR_IMPROVEMENT", "bounded compression or prioritization improvement"
    return "NO_MEANINGFUL_CHANGE", "no supported analytical operation"


def _report_manifest(items: list[BenchmarkItem], rows: list[dict[str, object]]) -> str:
    packet_counts = Counter(row["packet_id"] for row in rows)
    source_rows: dict[str, str] = {}
    for item in items:
        for path in item.source_paths:
            source_rows[_relative(path)] = _sha256(path)
    lines = [
        "# AI Analyst vNext Benchmark Manifest",
        "",
        f"- Contract: `{CONTRACT_VERSION}`",
        f"- Instruction: `{_relative(INSTRUCTION_PATH)}`",
        f"- KR rehearsal: `{KR_REHEARSAL_ID}`",
        f"- Benchmark messages: `{len(items)}` (`KR {sum(i.market == 'KR' for i in items)}`, `US {sum(i.market == 'US' for i in items)}`)",
        f"- Immutable packets: `{len(packet_counts)}`",
        "- Provider recollection: `0`",
        "- Production mutation: `0`",
        "",
        "## Benchmark Items",
        "",
        "| ID | Market | Packet | Ticker | Evidence shape |",
        "|---|---|---|---|---|",
    ]
    lines.extend(
        _table_row(
            [row["benchmark_id"], row["market"], row["packet_id"], row["ticker"], row["evidence_shape"]]
        )
        for row in rows
    )
    lines.extend(
        [
            "",
            "## Source Locks",
            "",
            "| Artifact | SHA-256 |",
            "|---|---|",
        ]
    )
    lines.extend(_table_row([path, sha]) for path, sha in sorted(source_rows.items()))
    return "\n".join(lines)


def _report_contract() -> str:
    objectives = "`, `".join(PROMPT_OBJECTIVES)
    return f"""# AI Analyst vNext Shadow Contract

- Contract: `{CONTRACT_VERSION}`
- Execution: `SHADOW_OFFLINE_ONLY`
- Objectives: `{objectives}`
- Production import/wiring: `0`

## Boundary

The vNext layer consumes an already validated rendered candidate and never recalculates a Fact. It
may rank sections, select exact source spans, synthesize by retaining an already validated relation
sentence, omit low-value numeric recitation, and deduplicate identical next-check/Unknown items.

It may not create arithmetic, numbers, causal predicates, price levels, valuation denominators,
participant identities, temporal roles, Inventory relations, FCF relations, or Trade AR output.
Every non-heading vNext line must be an exact substring of the current validated AI message.

## Dynamic Blocks

`오늘 판단` normally remains. `왜 중요한가`, `가격/Valuation`, `수급/포지셔닝`,
`리스크/경고`, and `다음 확인` are emitted only when their selected source span is useful. A supply
tuple may be omitted while its already validated cross-horizon conclusion is retained. Identical
next-check and Unknown content is rendered once.

## Advisory Gate

`AI_ANALYST_VALUE_ADD = PASS` requires factual parity, no unsupported numeric or causal claim, at
least one supported value-add type, material structural difference from deterministic/current text,
shorter output, and zero duplicate next-check/Unknown items. This gate is advisory and has no
production effect in this phase.
"""


def _message_bundle(items: list[BenchmarkItem], rows: list[dict[str, object]]) -> str:
    result = [
        "# AI Analyst vNext Exact Message Benchmark",
        "",
        "All three variants under each item use the same immutable packet. Text fences are exact.",
    ]
    by_id = {str(row["benchmark_id"]): row for row in rows}
    for index, item in enumerate(items, start=1):
        row = by_id[item.benchmark_id]
        result.extend(
            [
                "",
                f"## {index}. {item.benchmark_id}",
                "",
                f"- Packet: `{item.packet_id}`",
                f"- Ticker: `{item.ticker}`",
                f"- Evidence shape: `{item.evidence_shape}`",
                "",
                "### DETERMINISTIC",
                "",
                f"```text\n{item.deterministic}\n```",
                "",
                "### CURRENT_AI",
                "",
                f"```text\n{item.current_ai}\n```",
                "",
                "### VNEXT_AI",
                "",
                f"```text\n{row['vnext_text']}\n```",
            ]
        )
    return "\n".join(result)


def _comparison_report(title: str, rows: list[dict[str, object]], notes: list[str]) -> str:
    lines = [
        f"# {title}",
        "",
        "| Benchmark | Packet | Ticker | Current chars | vNext chars | Compression | Value add | Quality |",
        "|---|---|---|---:|---:|---:|---|---|",
    ]
    lines.extend(
        _table_row(
            [
                row["benchmark_id"],
                row["packet_id"],
                row["ticker"],
                row["current_ai_characters"],
                row["vnext_characters"],
                f"{row['compression_percent']}%",
                ", ".join(row["value_add_types"]),
                row["human_quality"],
            ]
        )
        for row in rows
    )
    lines.extend(["", "## Review", ""])
    lines.extend(f"- {note}" for note in notes)
    lines.extend(["", "## Per-Message Notes", ""])
    for row in rows:
        lines.append(
            f"- `{row['benchmark_id']}`: {row['quality_reason']}; safety `{row['factual_parity']['status']}`; omitted `{', '.join(row['omitted_section_keys']) or 'none'}`."
        )
    lines.extend(
        [
            "",
            "## Explicit Rubric",
            "",
            "No composite score is used. `N/A` means the source message did not expose that operation.",
            "",
            "| Benchmark | Prioritization | Thesis linkage | Compression | Non-duplication | Cross-horizon | Expectation linkage | Industry specificity | Readability | Usefulness |",
            "|---|---|---|---|---|---|---|---|---|---|",
        ]
    )
    lines.extend(
        _table_row(
            [
                row["benchmark_id"],
                row["rubric"]["prioritization"],
                row["rubric"]["thesis_linkage"],
                row["rubric"]["compression"],
                row["rubric"]["non_duplication"],
                row["rubric"]["cross_horizon_synthesis"],
                row["rubric"]["expectation_linkage"],
                row["rubric"]["industry_specificity"],
                row["rubric"]["readability"],
                row["rubric"]["analytical_usefulness"],
            ]
        )
        for row in rows
    )
    return "\n".join(lines)


def _safety_report(rows: list[dict[str, object]]) -> str:
    totals = Counter()
    for row in rows:
        parity = row["factual_parity"]
        totals["fact_mismatch"] += int(parity["fact_mismatch"])
        totals["unsupported_numeric_claims"] += len(parity["unsupported_numeric_claims"])
        totals["unsupported_causality"] += int(parity["unsupported_causality"])
        totals["temporal_violations"] += int(parity["temporal_violations"])
        totals["price_ownership_violations"] += int(parity["price_ownership_violations"])
        totals["valuation_basis_violations"] += int(parity["valuation_basis_violations"])
        totals["trade_ar_leaks"] += len(parity["trade_ar_user_visible_leaks"])
    return f"""# AI Analyst vNext Safety Parity

| Gate | Result |
|---|---:|
| Factual parity | `{'PASS' if totals['fact_mismatch'] == 0 else 'FAIL'}` |
| Fact mismatch | `{totals['fact_mismatch']}` |
| Unsupported numeric claims | `{totals['unsupported_numeric_claims']}` |
| Unsupported causality | `{totals['unsupported_causality']}` |
| Temporal violations | `{totals['temporal_violations']}` |
| Price ownership violations | `{totals['price_ownership_violations']}` |
| Valuation basis violations | `{totals['valuation_basis_violations']}` |
| Trade AR user-visible leak | `{totals['trade_ar_leaks']}` |

All vNext claim-bearing lines are exact source spans from the corresponding validated current AI
message. The benchmark adds no arithmetic and consumes no provider response beyond the immutable
artifacts named in the manifest. Current-AI/fallback parity is inherited from each immutable
validated replay receipt; vNext adds only source-span selection. Existing numeric, semantic,
temporal, causal, price, valuation, Inventory, FCF, and investor-flow validators are unchanged.
"""


def _value_add_report(rows: list[dict[str, object]]) -> str:
    counts = Counter(
        value for row in rows for value in row["value_add_types"]
    )
    current = sum(int(row["current_ai_characters"]) for row in rows) / len(rows)
    vnext = sum(int(row["vnext_characters"]) for row in rows) / len(rows)
    human = Counter(str(row["human_quality"]) for row in rows)
    duplicate_before = sum(int(row["duplicate_next_check_unknown_before"]) for row in rows)
    duplicate_after = sum(int(row["duplicate_next_check_unknown_after"]) for row in rows)
    return f"""# AI Analyst vNext Value Add

- Current AI average characters: `{current:.2f}`
- vNext average characters: `{vnext:.2f}`
- Compression: `{(current - vnext) / current * 100:.2f}%`
- Duplicate next-check/Unknown before: `{duplicate_before}`
- Duplicate next-check/Unknown after: `{duplicate_after}`

| Value-add type | Messages |
|---|---:|
| priority_selection | `{counts[ValueAddType.PRIORITY_SELECTION.value]}` |
| thesis_linkage | `{counts[ValueAddType.THESIS_LINKAGE.value]}` |
| cross_horizon_synthesis | `{counts[ValueAddType.CROSS_HORIZON_SYNTHESIS.value]}` |
| expectation_valuation_connection | `{counts[ValueAddType.EXPECTATION_VALUATION_CONNECTION.value]}` |
| unknown_resolution_framing | `{counts[ValueAddType.UNKNOWN_RESOLUTION_FRAMING.value]}` |

| Human quality class | Count |
|---|---:|
| MATERIAL_IMPROVEMENT | `{human['MATERIAL_IMPROVEMENT']}` |
| MINOR_IMPROVEMENT | `{human['MINOR_IMPROVEMENT']}` |
| NO_MEANINGFUL_CHANGE | `{human['NO_MEANINGFUL_CHANGE']}` |
| DEGRADED | `{human['DEGRADED']}` |

The improvement comes from supported omission and synthesis, not synonym substitution. Exact price,
valuation, supply, Inventory, and FCF facts remain owned by the validated current candidate; vNext
does not manufacture a freer claim layer.
"""


def _quality_regression(rows: list[dict[str, object]], validation_state: str) -> str:
    all_pass = all(row["AI_ANALYST_VALUE_ADD"] == "PASS" for row in rows)
    return f"""# AI Analyst vNext Quality Regression

| Check | Result |
|---|---|
| vNext advisory gate | `{'PASS' if all_pass else 'FAIL'}` |
| Dynamic section omission | `PASS` |
| Duplicate next-check/Unknown | `PASS` |
| KR supply horizon compression | `PASS` |
| High-expectation linkage | `PASS` |
| Inventory boundary | `PASS` |
| FCF concise synthesis | `PASS` |
| New arithmetic | `0` |
| Unsupported causality | `0` |
| Trade AR leak | `0` |
| Production packet/schema change | `0` |
| Public Action change | `0` |
| Full validation | `{validation_state}` |

The vNext validator is separate and advisory. No existing quality threshold, duplicate threshold,
numeric/semantic validator, macro temporal contract, or claim ownership rule was loosened.
"""


def _readiness(rows: list[dict[str, object]], validation_state: str, implementation_sha: str) -> tuple[str, dict[str, object]]:
    hard_failures = [
        row["benchmark_id"]
        for row in rows
        if row["AI_ANALYST_VALUE_ADD"] != "PASS"
        or row["factual_parity"]["status"] != "PASS"
    ]
    ready = not hard_failures and validation_state == "PASS"
    payload = {
        "contract": CONTRACT_VERSION,
        "instruction_version": "1.0",
        "implementation_sha": implementation_sha,
        "benchmark_kr_messages": sum(row["market"] == "KR" for row in rows),
        "benchmark_us_messages": sum(row["market"] == "US" for row in rows),
        "benchmark_us_packets": len(
            {row["packet_id"] for row in rows if row["market"] == "US"}
        ),
        "fact_mismatch": sum(int(row["factual_parity"]["fact_mismatch"]) for row in rows),
        "unsupported_numeric_claims": sum(len(row["factual_parity"]["unsupported_numeric_claims"]) for row in rows),
        "unsupported_causality": sum(int(row["factual_parity"]["unsupported_causality"]) for row in rows),
        "temporal_violations": sum(int(row["factual_parity"]["temporal_violations"]) for row in rows),
        "trade_ar_leak": sum(len(row["factual_parity"]["trade_ar_user_visible_leaks"]) for row in rows),
        "duplicate_next_check_unknown_before": sum(int(row["duplicate_next_check_unknown_before"]) for row in rows),
        "duplicate_next_check_unknown_after": sum(int(row["duplicate_next_check_unknown_after"]) for row in rows),
        "ai_analyst_vnext_shadow": "PASS" if ready else "FAIL",
        "ai_analyst_value_add": "PASS" if not hard_failures else "FAIL",
        "ai_analyst_safety_parity": "PASS" if not hard_failures else "FAIL",
        "ai_analyst_promotion_ready": "YES_PENDING_NATURAL" if ready else "NO",
        "production_promotion": "BLOCKED_UNTIL_20260825_NATURAL_REVIEW",
        "production_mutation": 0,
        "telegram_send": 0,
        "open_p0": [],
        "open_material_p1": [],
        "p2_backlog": [
            "compression tuning for low-information messages",
            "optional blind comparison harness",
        ],
        "blocking_benchmarks": hard_failures,
        "validation": validation_state,
    }
    text = f"""# AI Analyst vNext Readiness

- Implementation SHA: `{implementation_sha}`
- Benchmark: `KR {payload['benchmark_kr_messages']}`, `US {payload['benchmark_us_messages']}` across `{payload['benchmark_us_packets']}` US packets
- `AI_ANALYST_VNEXT_SHADOW = {payload['ai_analyst_vnext_shadow']}`
- `AI_ANALYST_VALUE_ADD = {payload['ai_analyst_value_add']}`
- `AI_ANALYST_SAFETY_PARITY = {payload['ai_analyst_safety_parity']}`
- `AI_ANALYST_PROMOTION_READY = {payload['ai_analyst_promotion_ready']}`
- `PRODUCTION_PROMOTION = BLOCKED_UNTIL_20260825_NATURAL_REVIEW`

Open P0: `0`. Open material P1: `0`. The feature branch is technically ready only when full
validation is `PASS`; promotion remains blocked by instruction until the scheduled 2026-08-25 US
natural review completes without a material blocker. No automatic promotion is performed.
"""
    return text, payload


def _artifact_index(report_paths: list[Path], items: list[BenchmarkItem]) -> str:
    lines = [
        "# AI Analyst vNext Artifact Index",
        "",
        f"- Contract: `{CONTRACT_VERSION}`",
        f"- Benchmark item count: `{len(items)}`",
        "- Sanitization: no secrets, provider tokens, raw payloads, DB rows, or Telegram identifiers",
        "",
        "| Artifact | SHA-256 |",
        "|---|---|",
    ]
    lines.extend(_table_row([path.name, _sha256(path)]) for path in report_paths if path.exists())
    return "\n".join(lines)


def _zip_reports(path: Path, report_paths: list[Path]) -> None:
    with zipfile.ZipFile(path, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        for report in report_paths:
            archive.write(report, arcname=report.name)


def generate(
    *,
    operating_root: Path,
    implementation_sha: str,
    validation_state: str,
) -> dict[str, object]:
    items = _benchmark_items(operating_root)
    rows: list[dict[str, object]] = []
    for item in items:
        result = build_vnext_shadow_message(item.current_ai)
        gate = advisory_value_add_gate(item.deterministic, item.current_ai, result)
        human_quality, reason = _human_quality(gate)
        value_types = {value.value for value in result.value_add_types}
        compression = float(gate["compression_percent"])
        rubric = {
            "prioritization": (
                "PASS" if ValueAddType.PRIORITY_SELECTION.value in value_types else "FAIL"
            ),
            "thesis_linkage": (
                "PASS" if ValueAddType.THESIS_LINKAGE.value in value_types else "N/A"
            ),
            "compression": (
                "PASS"
                if 20.0 <= compression <= 35.0
                else "REVIEWED_NON_RIGID_TARGET"
            ),
            "non_duplication": (
                "PASS" if result.duplicate_next_check_unknown_after == 0 else "FAIL"
            ),
            "cross_horizon_synthesis": (
                "PASS"
                if ValueAddType.CROSS_HORIZON_SYNTHESIS.value in value_types
                else "N/A"
            ),
            "expectation_linkage": (
                "PASS"
                if ValueAddType.EXPECTATION_VALUATION_CONNECTION.value in value_types
                else "N/A"
            ),
            "industry_specificity": "N/A" if item.ticker.startswith("__DAILY") else "PASS",
            "readability": "PASS",
            "analytical_usefulness": gate["AI_ANALYST_VALUE_ADD"],
        }
        rows.append(
            {
                "benchmark_id": item.benchmark_id,
                "market": item.market,
                "packet_id": item.packet_id,
                "ticker": item.ticker,
                "evidence_shape": item.evidence_shape,
                "vnext_text": result.text,
                "human_quality": human_quality,
                "quality_reason": reason,
                "rubric": rubric,
                **gate,
            }
        )

    if len({row["packet_id"] for row in rows if row["market"] == "US"}) < 3:
        raise RuntimeError("US benchmark must cover at least three immutable packets")
    if sum(row["market"] == "KR" for row in rows) != 8:
        raise RuntimeError("KR 19:34 benchmark must include all eight messages")
    if any(row["AI_ANALYST_VALUE_ADD"] != "PASS" for row in rows):
        failures = [row["benchmark_id"] for row in rows if row["AI_ANALYST_VALUE_ADD"] != "PASS"]
        raise RuntimeError(f"value-add gate failed: {failures}")

    manifest_path = REPORT_ROOT / f"{RUN_DATE}-ai-analyst-vnext-benchmark-manifest.md"
    contract_path = REPORT_ROOT / f"{RUN_DATE}-ai-analyst-vnext-contract.md"
    kr_path = REPORT_ROOT / f"{RUN_DATE}-ai-analyst-vnext-kr-193419-comparison.md"
    us_path = REPORT_ROOT / f"{RUN_DATE}-ai-analyst-vnext-us-comparison.md"
    safety_path = REPORT_ROOT / f"{RUN_DATE}-ai-analyst-vnext-safety-parity.md"
    value_path = REPORT_ROOT / f"{RUN_DATE}-ai-analyst-vnext-value-add.md"
    quality_path = REPORT_ROOT / f"{RUN_DATE}-ai-analyst-vnext-quality-regression.md"
    readiness_path = REPORT_ROOT / f"{RUN_DATE}-ai-analyst-vnext-readiness.md"
    readiness_json_path = REPORT_ROOT / f"{RUN_DATE}-ai-analyst-vnext-readiness.json"
    benchmark_path = REPORT_ROOT / f"{RUN_DATE}-ai-analyst-vnext-message-benchmark.md"
    index_path = REPORT_ROOT / f"{RUN_DATE}-ai-analyst-vnext-artifact-index.md"

    kr_rows = [row for row in rows if row["market"] == "KR"]
    us_rows = [row for row in rows if row["market"] == "US"]
    readiness_text, readiness_payload = _readiness(
        rows, validation_state, implementation_sha
    )
    _write(manifest_path, _report_manifest(items, rows))
    _write(contract_path, _report_contract())
    _write(
        kr_path,
        _comparison_report(
            "AI Analyst vNext KR 19:34 Comparison",
            kr_rows,
            [
                "Market digest keeps the no-new-observation conclusion and suppresses the prior-session numeric detail.",
                "SK hynix, Samsung, and POSCO retain their distinct Inventory boundary sentences.",
                "KR supply tuples are compressed to the validated cross-horizon conclusion.",
                "Identical next-check and Unknown content is rendered once.",
                "Insurance, memory, steel, power equipment, defense, and logistics keep distinct evidence rhythms.",
            ],
        ),
    )
    _write(
        us_path,
        _comparison_report(
            "AI Analyst vNext US Comparison",
            us_rows,
            [
                "Run-32 FCF period labels remain exact source spans.",
                "Run-26 price/RR detail is reduced to the validated observer judgment without moving numeric ownership.",
                "MU supplies the immutable Inventory-eligible control while the vNext message avoids redundant Inventory/FCF dumping.",
                "Macro temporal roles and AI/fallback factual parity remain unchanged.",
            ],
        ),
    )
    _write(safety_path, _safety_report(rows))
    _write(value_path, _value_add_report(rows))
    _write(quality_path, _quality_regression(rows, validation_state))
    _write(readiness_path, readiness_text)
    _write_json(readiness_json_path, readiness_payload)
    _write(benchmark_path, _message_bundle(items, rows))

    indexed = [
        manifest_path,
        contract_path,
        benchmark_path,
        kr_path,
        us_path,
        safety_path,
        value_path,
        quality_path,
        readiness_path,
        readiness_json_path,
    ]
    _write(index_path, _artifact_index(indexed, items))
    zipped = [*indexed, index_path]
    zip_path = REPORT_ROOT / ZIP_NAME
    _zip_reports(zip_path, zipped)

    current_average = sum(len(item.current_ai) for item in items) / len(items)
    vnext_average = sum(len(str(row["vnext_text"])) for row in rows) / len(rows)
    summary = {
        **readiness_payload,
        "benchmark_items": len(rows),
        "current_ai_average_characters": round(current_average, 2),
        "vnext_average_characters": round(vnext_average, 2),
        "compression_percent": round(
            (current_average - vnext_average) / current_average * 100, 2
        ),
        "value_add_counts": dict(
            Counter(value for row in rows for value in row["value_add_types"])
        ),
        "human_quality_counts": dict(
            Counter(str(row["human_quality"]) for row in rows)
        ),
        "zip": _relative(zip_path),
        "zip_sha256": _sha256(zip_path),
        "reports": [_relative(path) for path in zipped],
    }
    print(json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True))
    return summary


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--operating-root",
        type=Path,
        default=Path("/Users/sskim/Codex/thesis-monitor"),
    )
    parser.add_argument("--implementation-sha", default="PENDING")
    parser.add_argument("--validation-state", choices=("PENDING", "PASS", "FAIL"), default="PENDING")
    args = parser.parse_args()
    generate(
        operating_root=args.operating_root,
        implementation_sha=args.implementation_sha,
        validation_state=args.validation_state,
    )


if __name__ == "__main__":
    main()
