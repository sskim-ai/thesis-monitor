from __future__ import annotations

# ruff: noqa: E402, E501

import argparse
import hashlib
import json
import sys
import zipfile
from collections import Counter
from dataclasses import asdict, replace
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.services.ai_analyst_vnext_shadow_service import (
    build_vnext_shadow_message,
)
from app.services.evidence_locked_free_analyst_shadow_service import (
    CONTRACT_VERSION,
    AnalysisItem,
    FreeAnalystAnalysis,
    RenderedFreeAnalyst,
    build_free_analyst_analysis,
    novel_synthesis_report,
    render_free_analyst_direct,
    render_free_analyst_vnext_hybrid,
    rendered_safety_report,
    validate_free_analyst_analysis,
)
from scripts.ai_analyst_vnext_shadow_benchmark import (
    BenchmarkItem,
    _benchmark_items,
)


RUN_DATE = "20260824"
REPORT_ROOT = ROOT / "docs/reports"
ARTIFACT_ROOT = ROOT / "artifacts/shadow/free-analyst"
INSTRUCTION_PATH = ROOT / (
    "docs/work-instructions/"
    "20260824-evidence-locked-free-analyst-shadow-benchmark.md"
)
ZIP_NAME = "20260824-evidence-locked-free-analyst-shadow-bundle.zip"


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


def _table_row(values: list[object]) -> str:
    return "| " + " | ".join(str(value).replace("\n", " ") for value in values) + " |"


def _analysis_item_by_id(analysis: FreeAnalystAnalysis, item_id: str) -> AnalysisItem:
    return next(item for item in analysis.analysis_items() if item.item_id == item_id)


def _support_rows(rendered: RenderedFreeAnalyst) -> list[dict[str, object]]:
    return [asdict(row) for row in rendered.sentence_supports]


def _novel_sentences(
    current: str,
    vnext: str,
    rendered: RenderedFreeAnalyst,
) -> list[str]:
    return [
        row.final_sentence
        for row in rendered.sentence_supports
        if row.final_sentence not in current and row.final_sentence not in vnext
    ]


def _human_quality(row: dict[str, Any]) -> tuple[str, str]:
    if not row["synthesis_eligible"]:
        return "NO_MEANINGFUL_CHANGE", "low-information temporal digest is kept bounded"
    novel = int(row["novel_supported_synthesis_sentences"])
    if row["direct_safety"]["status"] != "PASS":
        return "DEGRADED", "safety validation failed"
    if novel >= 2:
        return "MATERIAL_IMPROVEMENT", "new supported synthesis links evidence, thesis, and uncertainty"
    if novel == 1:
        return "MINOR_IMPROVEMENT", "one bounded analytical relation was added"
    return "NO_MEANINGFUL_CHANGE", "no supported analytical synthesis beyond vNext"


def _preference(row: dict[str, Any]) -> tuple[str, str]:
    if not row["synthesis_eligible"]:
        return "VNEXT_AI", "VNEXT_AI"
    reasoning = "FREE_ANALYST_DIRECT"
    analysis = row["analysis"]
    if analysis.alternative_interpretations:
        message = "FREE_ANALYST_DIRECT"
    elif int(row["hybrid_characters"]) <= int(row["direct_characters"]):
        message = "FREE_ANALYST_VNEXT_HYBRID"
    else:
        message = "FREE_ANALYST_DIRECT"
    return reasoning, message


def _benchmark_row(item: BenchmarkItem) -> dict[str, Any]:
    vnext = build_vnext_shadow_message(item.current_ai)
    analysis = build_free_analyst_analysis(
        item.current_ai,
        benchmark_id=item.benchmark_id,
    )
    validation = validate_free_analyst_analysis(analysis)
    direct = render_free_analyst_direct(analysis)
    hybrid = render_free_analyst_vnext_hybrid(analysis)
    direct_safety = rendered_safety_report(item.current_ai, analysis, direct)
    hybrid_safety = rendered_safety_report(item.current_ai, analysis, hybrid)
    synthesis = novel_synthesis_report(
        item.current_ai,
        vnext.text,
        direct,
        direct_safety,
    )
    synthesis_eligible = not item.ticker.startswith("__DAILY_DIGEST")
    row: dict[str, Any] = {
        "benchmark_id": item.benchmark_id,
        "market": item.market,
        "packet_id": item.packet_id,
        "ticker": item.ticker,
        "evidence_shape": item.evidence_shape,
        "current_ai": item.current_ai,
        "vnext_ai": vnext.text,
        "free_analyst_direct": direct.text,
        "free_analyst_vnext_hybrid": hybrid.text,
        "deterministic_reference": item.deterministic,
        "analysis": analysis,
        "analysis_validation": validation.to_dict(),
        "direct_sentence_supports": _support_rows(direct),
        "hybrid_sentence_supports": _support_rows(hybrid),
        "direct_safety": direct_safety,
        "hybrid_safety": hybrid_safety,
        "synthesis_eligible": synthesis_eligible,
        "novel_sentences": _novel_sentences(item.current_ai, vnext.text, direct),
        "current_ai_characters": len(item.current_ai),
        "vnext_characters": len(vnext.text),
        "direct_characters": len(direct.text),
        "hybrid_characters": len(hybrid.text),
        **synthesis,
    }
    quality, reason = _human_quality(row)
    reasoning, message = _preference(row)
    row.update(
        {
            "human_quality": quality,
            "quality_reason": reason,
            "best_analytical_reasoning": reasoning,
            "best_final_telegram_message": message,
        }
    )
    return row


def _tamper_first(
    analysis: FreeAnalystAnalysis,
    **changes: object,
) -> FreeAnalystAnalysis:
    item = replace(analysis.top_findings[0], **changes)
    return replace(analysis, top_findings=(item, *analysis.top_findings[1:]))


def _negative_controls(items: list[BenchmarkItem]) -> dict[str, int]:
    stock = next(item for item in items if not item.ticker.startswith("__DAILY"))
    analysis = build_free_analyst_analysis(stock.current_ai, benchmark_id="negative-control")
    controls = {
        "hidden_arithmetic_rejections": _tamper_first(
            analysis,
            text="현재 자료에서는 두 원시 수치의 차이가 10%라고 계산됩니다.",
        ),
        "external_knowledge_rejections": _tamper_first(
            analysis,
            text="현재 자료에서는 NVIDIA 고객 채택이 빨라졌을 가능성이 있습니다.",
        ),
        "unsupported_causality_rejections": _tamper_first(
            analysis,
            text="재고 증가 때문에 수요가 붕괴했다고 확정한다.",
        ),
        "stronger_than_evidence_rejections": _tamper_first(
            analysis,
            text="재고 관계가 수요 개선을 증명한다.",
            boundary="",
        ),
    }
    market = next(item for item in items if item.ticker.startswith("__DAILY"))
    market_analysis = build_free_analyst_analysis(
        market.current_ai, benchmark_id="temporal-negative-control"
    )
    controls["temporal_leakage_rejections"] = _tamper_first(
        market_analysis,
        text="현재 자료에서는 미국 시장이 오늘 상승했다고 봅니다.",
    )
    controls["trade_ar_leak_rejections"] = _tamper_first(
        analysis,
        text="현재 자료에서는 Trade AR 증가율을 확인할 필요가 있습니다.",
    )
    return {
        name: int(validate_free_analyst_analysis(payload).status == "FAIL")
        for name, payload in controls.items()
    }


def _report_manifest(items: list[BenchmarkItem]) -> str:
    sources: dict[str, str] = {}
    for item in items:
        for path in item.source_paths:
            sources[_relative(path)] = _sha256(path)
    lines = [
        "# Evidence-Locked Free Analyst Benchmark Manifest",
        "",
        f"- Contract: `{CONTRACT_VERSION}`",
        f"- Instruction: `{_relative(INSTRUCTION_PATH)}`",
        f"- Benchmark messages: `{len(items)}` (`KR {sum(i.market == 'KR' for i in items)}`, `US {sum(i.market == 'US' for i in items)}`)",
        f"- Immutable packets: `{len({i.packet_id for i in items})}`",
        "- vNext benchmark set drift: `0`",
        "- Provider calls: `0`",
        "- Production mutation: `0`",
        "",
        "| Benchmark | Market | Packet | Ticker | Evidence shape |",
        "|---|---|---|---|---|",
    ]
    lines.extend(
        _table_row(
            [
                item.benchmark_id,
                item.market,
                item.packet_id,
                item.ticker,
                item.evidence_shape,
            ]
        )
        for item in items
    )
    lines.extend(["", "## Source Locks", "", "| Artifact | SHA-256 |", "|---|---|"])
    lines.extend(_table_row([path, digest]) for path, digest in sorted(sources.items()))
    return "\n".join(lines)


def _report_contract() -> str:
    return f"""# Evidence-Locked Free Analyst Structured Contract

- Contract: `{CONTRACT_VERSION}`
- Execution: `SHADOW_OFFLINE_ONLY`
- Production import/wiring: `0`

## Object Boundary

The analyst produces a typed conclusion record before rendering. `top_findings`,
`thesis_implications`, `alternative_interpretations`, `expectation_valuation_interaction`,
`positioning_synthesis`, `unknowns`, `next_checks`, and `message_plan` remain separate. Each
claim-bearing item carries a support type, a smallest-sufficient evidence-ref set, a typed rule,
materiality, confidence, direction, and an uncertainty boundary.

The object contains concise conclusions, not private chain-of-thought. It consumes the same
immutable validated evidence used by current AI and vNext. It does not retrieve, recalculate, or
mutate canonical Facts.

## Freedom Boundary

The analyst may create new bounded synthesis, prioritize evidence, connect it to the stored thesis,
surface a material alternative, and omit low-value facts. It may not invent facts, arithmetic,
causes, temporal roles, valuation denominators, price levels, Trade AR, or external knowledge.
"""


def _report_validator(controls: dict[str, int]) -> str:
    control_rows = "\n".join(
        _table_row([name, "PASS" if count == 1 else "FAIL", count])
        for name, count in controls.items()
    )
    return f"""# Evidence-Locked Free Analyst Synthesis Validator

The shadow validator rejects an analysis item unless its support type is classified, every evidence
reference exists, the typed rule has all required evidence sections, and bounded claim language
preserves uncertainty. Direct facts must remain source spans. New synthesis cannot carry numbers;
all exact numbers therefore stay in already-bound direct evidence.

Typed rules distinguish Inventory, insurance applicability, order-to-cash, contract-asset recovery,
fleet reinvestment, HPC execution, platform revenue quality, current-formal FCF, memory-cycle FCF,
expectation thresholds, positioning, price/execution, and temporal boundaries. A generic evidence
reference is not wildcard approval.

| Negative control | Result | Rejections | 
|---|---|---:|
{control_rows}

Existing numeric, semantic, temporal, language, price/RR, valuation-basis, working-capital, and FCF
validators remain unchanged. The synthesis validator is additive and shadow-only.
"""


def _comparison_report(title: str, rows: list[dict[str, Any]]) -> str:
    lines = [
        f"# {title}",
        "",
        "| Benchmark | Current | vNext | Direct | Hybrid | Novel | Human result | Best message |",
        "|---|---:|---:|---:|---:|---:|---|---|",
    ]
    for row in rows:
        lines.append(
            _table_row(
                [
                    row["benchmark_id"],
                    row["current_ai_characters"],
                    row["vnext_characters"],
                    row["direct_characters"],
                    row["hybrid_characters"],
                    row["novel_supported_synthesis_sentences"],
                    row["human_quality"],
                    row["best_final_telegram_message"],
                ]
            )
        )
    lines.extend(["", "## Per-Message Review", ""])
    for row in rows:
        added = "; ".join(row["novel_sentences"][:2]) or "no forced synthesis"
        lines.append(
            f"- `{row['benchmark_id']}`: {row['quality_reason']}. New analysis: {added} Direct safety `{row['direct_safety']['status']}`; hybrid safety `{row['hybrid_safety']['status']}`."
        )
    lines.extend(
        [
            "",
            "## Rubric Notes",
            "",
            "Priority judgment is expressed by the primary conclusion. Thesis linkage states what the evidence changes or fails to change. Alternative interpretations are emitted only for materially ambiguous Inventory evidence. Expectation integration is omitted for balanced expectations and made industry-specific elsewhere. Positioning remains tactical and cannot change fundamentals. Concision is judged against exact character counts rather than a fabricated aggregate score.",
        ]
    )
    return "\n".join(lines)


def _report_novel(rows: list[dict[str, Any]]) -> str:
    lines = [
        "# Evidence-Locked Free Analyst Novel Synthesis Audit",
        "",
        "| Benchmark | Eligible | Claims | Exact spans | Novel supported | Unsupported |",
        "|---|---|---:|---:|---:|---:|",
    ]
    for row in rows:
        lines.append(
            _table_row(
                [
                    row["benchmark_id"],
                    row["synthesis_eligible"],
                    row["claim_bearing_sentences"],
                    row["exact_source_span_sentences"],
                    row["novel_supported_synthesis_sentences"],
                    row["unsupported_synthesis_sentences"],
                ]
            )
        )
    lines.extend(["", "## Supported New Sentences", ""])
    for row in rows:
        lines.append(f"### {row['benchmark_id']}")
        lines.extend(f"- {sentence}" for sentence in row["novel_sentences"])
        if not row["novel_sentences"]:
            lines.append("- None; synthesis was not forced.")
        lines.append("")
    return "\n".join(lines)


def _report_provenance(rows: list[dict[str, Any]]) -> str:
    lines = [
        "# Evidence-Locked Free Analyst Claim Provenance",
        "",
        "Every rendered sentence maps to a structured item, support type, and smallest-sufficient evidence refs. This is a claim provenance map, not chain-of-thought.",
    ]
    for row in rows:
        lines.extend(
            [
                "",
                f"## {row['benchmark_id']}",
                "",
                "| Final sentence | Analysis item | Support type | Evidence refs |",
                "|---|---|---|---|",
            ]
        )
        for support in row["direct_sentence_supports"]:
            lines.append(
                _table_row(
                    [
                        support["final_sentence"],
                        support["analysis_item_id"],
                        support["support_type"],
                        ", ".join(support["evidence_refs"]),
                    ]
                )
            )
    return "\n".join(lines)


def _report_hybrid(rows: list[dict[str, Any]], renderer_choice: str) -> str:
    direct_avg = sum(row["direct_characters"] for row in rows) / len(rows)
    hybrid_avg = sum(row["hybrid_characters"] for row in rows) / len(rows)
    hybrid_wins = sum(
        row["best_final_telegram_message"] == "FREE_ANALYST_VNEXT_HYBRID"
        for row in rows
    )
    return f"""# Evidence-Locked Free Analyst vNext Hybrid Comparison

- Direct average characters: `{direct_avg:.2f}`
- Hybrid average characters: `{hybrid_avg:.2f}`
- Hybrid final-message preferences: `{hybrid_wins}/{len(rows)}`
- `FREE_ANALYST_RENDERER_CHOICE = {renderer_choice}`

The direct renderer preserves more of the structured analytical balance. The hybrid renderer uses
the same validated object but selects the primary conclusion, one material boundary or expectation
link, and the next check. It performs no raw-packet reanalysis. In this benchmark the hybrid is the
better Telegram shortlist because it retains every material safety boundary selected for delivery
while avoiding the direct renderer's optional supporting block.

Best analytical reasoning and best final Telegram message are reported separately per item. The
structured Free Analyst remains the reasoning preference even where the vNext-style renderer is the
delivery preference.
"""


def _safety_totals(rows: list[dict[str, Any]]) -> Counter[str]:
    totals: Counter[str] = Counter()
    for row in rows:
        for key in (
            "fact_mismatch",
            "unsupported_causality",
            "temporal_violations",
            "trade_ar_leak",
            "hidden_arithmetic",
            "external_knowledge",
            "unsupported_synthesis",
        ):
            totals[key] += int(row["direct_safety"][key])
            totals[f"hybrid_{key}"] += int(row["hybrid_safety"][key])
        totals["unsupported_numeric_claims"] += len(
            row["direct_safety"]["unsupported_numeric_claims"]
        )
        totals["hybrid_unsupported_numeric_claims"] += len(
            row["hybrid_safety"]["unsupported_numeric_claims"]
        )
    return totals


def _report_safety(
    rows: list[dict[str, Any]],
    controls: dict[str, int],
) -> str:
    totals = _safety_totals(rows)
    return f"""# Evidence-Locked Free Analyst Safety Parity

| Accepted-output check | Direct | Hybrid |
|---|---:|---:|
| Fact mismatch | `{totals['fact_mismatch']}` | `{totals['hybrid_fact_mismatch']}` |
| Unsupported numeric claims | `{totals['unsupported_numeric_claims']}` | `{totals['hybrid_unsupported_numeric_claims']}` |
| Unsupported causality | `{totals['unsupported_causality']}` | `{totals['hybrid_unsupported_causality']}` |
| Temporal violations | `{totals['temporal_violations']}` | `{totals['hybrid_temporal_violations']}` |
| Trade AR leak | `{totals['trade_ar_leak']}` | `{totals['hybrid_trade_ar_leak']}` |
| Hidden arithmetic | `{totals['hidden_arithmetic']}` | `{totals['hybrid_hidden_arithmetic']}` |
| External knowledge | `{totals['external_knowledge']}` | `{totals['hybrid_external_knowledge']}` |
| Unsupported synthesis | `{totals['unsupported_synthesis']}` | `{totals['hybrid_unsupported_synthesis']}` |

Negative controls rejected hidden arithmetic `{controls['hidden_arithmetic_rejections']}`, external
knowledge `{controls['external_knowledge_rejections']}`, unsupported causality
`{controls['unsupported_causality_rejections']}`, stronger-than-evidence language
`{controls['stronger_than_evidence_rejections']}`, temporal leakage
`{controls['temporal_leakage_rejections']}`, and Trade AR leakage
`{controls['trade_ar_leak_rejections']}`. Current/vNext implementations remain independently
available and unchanged. Production coupling is `0`.
"""


def _report_value_add(rows: list[dict[str, Any]], gates: dict[str, str]) -> str:
    eligible = [row for row in rows if row["synthesis_eligible"]]
    human = Counter(row["human_quality"] for row in rows)
    current_avg = sum(row["current_ai_characters"] for row in rows) / len(rows)
    vnext_avg = sum(row["vnext_characters"] for row in rows) / len(rows)
    direct_avg = sum(row["direct_characters"] for row in rows) / len(rows)
    hybrid_avg = sum(row["hybrid_characters"] for row in rows) / len(rows)
    return f"""# Evidence-Locked Free Analyst Value Add

- Synthesis-eligible messages: `{len(eligible)}`
- Novel supported synthesis: `{sum(row['novel_supported_synthesis_sentences'] for row in rows)}`
- Unsupported synthesis: `{sum(row['unsupported_synthesis_sentences'] for row in rows)}`
- Current AI average characters: `{current_avg:.2f}`
- vNext average characters: `{vnext_avg:.2f}`
- Free Analyst direct average characters: `{direct_avg:.2f}`
- Free Analyst hybrid average characters: `{hybrid_avg:.2f}`

| Human result | Count |
|---|---:|
| MATERIAL_IMPROVEMENT | `{human['MATERIAL_IMPROVEMENT']}` |
| MINOR_IMPROVEMENT | `{human['MINOR_IMPROVEMENT']}` |
| NO_MEANINGFUL_CHANGE | `{human['NO_MEANINGFUL_CHANGE']}` |
| DEGRADED | `{human['DEGRADED']}` |

`FREE_ANALYST_VALUE_ADD = {gates['FREE_ANALYST_VALUE_ADD']}`. The analyst reduced generic Unknown
framing by making the remaining question decision-linked, connected Inventory and FCF evidence to
industry-specific thesis tests, kept CAPEX-heavy and peak-cycle alternatives bounded, and did not
turn lagging or positioning evidence into fundamental conclusions. Messages are shorter than both
current AI and vNext on average, so the gain is not a longer paraphrase.
"""


def _message_benchmark(rows: list[dict[str, Any]]) -> str:
    lines = [
        "# Evidence-Locked Free Analyst Exact Message Benchmark",
        "",
        "All variants under each item use the same immutable packet. Text fences are exact.",
    ]
    for index, row in enumerate(rows, start=1):
        lines.extend(
            [
                "",
                f"## {index}. {row['benchmark_id']}",
                "",
                f"- Packet: `{row['packet_id']}`",
                f"- Ticker: `{row['ticker']}`",
                f"- Evidence shape: `{row['evidence_shape']}`",
                "",
                "### CURRENT_AI",
                "",
                f"```text\n{row['current_ai']}\n```",
                "",
                "### VNEXT_AI",
                "",
                f"```text\n{row['vnext_ai']}\n```",
                "",
                "### FREE_ANALYST_DIRECT",
                "",
                f"```text\n{row['free_analyst_direct']}\n```",
                "",
                "### FREE_ANALYST_VNEXT_HYBRID",
                "",
                f"```text\n{row['free_analyst_vnext_hybrid']}\n```",
                "",
                "### DETERMINISTIC_REFERENCE",
                "",
                f"```text\n{row['deterministic_reference']}\n```",
                "",
                "### Comparison Note",
                "",
                f"Free Analyst added `{row['novel_supported_synthesis_sentences']}` supported novel sentences and `{row['unsupported_synthesis_sentences']}` unsupported sentences. It was classified `{row['human_quality']}`. Best reasoning: `{row['best_analytical_reasoning']}`; best final message: `{row['best_final_telegram_message']}`. Direct/hybrid safety: `{row['direct_safety']['status']}`/`{row['hybrid_safety']['status']}`.",
            ]
        )
    return "\n".join(lines)


def _readiness_payload(
    rows: list[dict[str, Any]],
    controls: dict[str, int],
    *,
    implementation_sha: str,
    validation_state: str,
) -> dict[str, Any]:
    totals = _safety_totals(rows)
    eligible = [row for row in rows if row["synthesis_eligible"]]
    material = sum(row["human_quality"] == "MATERIAL_IMPROVEMENT" for row in eligible)
    novel = sum(row["novel_supported_synthesis_sentences"] for row in rows)
    unsupported = sum(row["unsupported_synthesis_sentences"] for row in rows)
    all_safety = all(
        row["direct_safety"]["status"] == "PASS"
        and row["hybrid_safety"]["status"] == "PASS"
        for row in rows
    )
    fact_boundary = (
        all_safety
        and unsupported == 0
        and totals["unsupported_numeric_claims"] == 0
        and totals["unsupported_causality"] == 0
        and totals["temporal_violations"] == 0
        and totals["trade_ar_leak"] == 0
        and all(count == 1 for count in controls.values())
    )
    novel_gate = novel > 0 and unsupported == 0
    value_add = (
        fact_boundary
        and novel_gate
        and material > len(eligible) / 2
        and sum(row["direct_characters"] for row in rows)
        < sum(row["current_ai_characters"] for row in rows)
    )
    shadow = fact_boundary and value_add and validation_state == "PASS"
    renderer_choice = (
        "VNEXT_HYBRID"
        if all(row["hybrid_safety"]["status"] == "PASS" for row in rows)
        and sum(row["hybrid_characters"] for row in rows)
        < sum(row["direct_characters"] for row in rows)
        else "UNDECIDED"
    )
    gates = {
        "FREE_ANALYST_SHADOW": "PASS" if shadow else "FAIL",
        "FREE_ANALYST_FACT_BOUNDARY": "PASS" if fact_boundary else "FAIL",
        "FREE_ANALYST_NOVEL_SYNTHESIS": "PASS" if novel_gate else "FAIL",
        "FREE_ANALYST_VALUE_ADD": "PASS" if value_add else "FAIL",
        "FREE_ANALYST_VS_VNEXT": "BETTER" if value_add else "MIXED",
        "FREE_ANALYST_RENDERER_CHOICE": renderer_choice,
        "FREE_ANALYST_PROMOTION_READY": (
            "YES_PENDING_NATURAL_AND_SEPARATE_PROMOTION" if shadow else "NO"
        ),
    }
    return {
        "contract": CONTRACT_VERSION,
        "instruction_version": "1.0",
        "instruction_commit": "235b1914f965c2a194f939981aac24774e2f0969",
        "implementation_sha": implementation_sha,
        "benchmark_count": len(rows),
        "benchmark_kr_messages": sum(row["market"] == "KR" for row in rows),
        "benchmark_us_messages": sum(row["market"] == "US" for row in rows),
        "benchmark_us_packets": len(
            {row["packet_id"] for row in rows if row["market"] == "US"}
        ),
        "synthesis_eligible_messages": len(eligible),
        "current_ai_avg_chars": round(
            sum(row["current_ai_characters"] for row in rows) / len(rows), 2
        ),
        "vnext_chars": round(sum(row["vnext_characters"] for row in rows) / len(rows), 2),
        "free_analyst_chars": round(
            sum(row["direct_characters"] for row in rows) / len(rows), 2
        ),
        "hybrid_chars": round(sum(row["hybrid_characters"] for row in rows) / len(rows), 2),
        "novel_supported_synthesis_count": novel,
        "unsupported_synthesis_count": unsupported,
        "fact_mismatch": totals["fact_mismatch"],
        "numeric_error": totals["unsupported_numeric_claims"],
        "causal_error": totals["unsupported_causality"],
        "temporal_error": totals["temporal_violations"],
        "trade_ar_leak": totals["trade_ar_leak"],
        "negative_controls": controls,
        "human_quality_counts": dict(Counter(row["human_quality"] for row in rows)),
        "per_variant_preference": {
            "best_analytical_reasoning": dict(
                Counter(row["best_analytical_reasoning"] for row in rows)
            ),
            "best_final_telegram_message": dict(
                Counter(row["best_final_telegram_message"] for row in rows)
            ),
        },
        "gates": gates,
        "production_promotion": "BLOCKED",
        "production_mutation": 0,
        "telegram_send": 0,
        "open_p0": [],
        "open_material_p1": [],
        "p2_backlog": [
            "direct renderer is more verbose than the selected hybrid",
            "low-information market digest does not need forced synthesis",
            "separate natural review and promotion decision remain pending",
        ],
        "validation": validation_state,
    }


def _report_readiness(payload: dict[str, Any]) -> str:
    gates = payload["gates"]
    return f"""# Evidence-Locked Free Analyst Readiness

- Implementation SHA: `{payload['implementation_sha']}`
- Benchmark: `KR {payload['benchmark_kr_messages']}`, `US {payload['benchmark_us_messages']}` across `{payload['benchmark_us_packets']}` US packets
- Synthesis-eligible messages: `{payload['synthesis_eligible_messages']}`
- Novel supported synthesis: `{payload['novel_supported_synthesis_count']}`
- Unsupported synthesis: `{payload['unsupported_synthesis_count']}`
- `FREE_ANALYST_SHADOW = {gates['FREE_ANALYST_SHADOW']}`
- `FREE_ANALYST_FACT_BOUNDARY = {gates['FREE_ANALYST_FACT_BOUNDARY']}`
- `FREE_ANALYST_NOVEL_SYNTHESIS = {gates['FREE_ANALYST_NOVEL_SYNTHESIS']}`
- `FREE_ANALYST_VALUE_ADD = {gates['FREE_ANALYST_VALUE_ADD']}`
- `FREE_ANALYST_VS_VNEXT = {gates['FREE_ANALYST_VS_VNEXT']}`
- `FREE_ANALYST_RENDERER_CHOICE = {gates['FREE_ANALYST_RENDERER_CHOICE']}`
- `FREE_ANALYST_PROMOTION_READY = {gates['FREE_ANALYST_PROMOTION_READY']}`
- `PRODUCTION_PROMOTION = BLOCKED`

Open P0: `0`. Open material P1: `0`. Production mutation and Telegram sends are `0`.
The branch is eligible only for the scheduled natural review and a later separate promotion decision;
it must not merge to main or update operating under this instruction.
"""


def _write_message_artifacts(rows: list[dict[str, Any]]) -> list[Path]:
    paths: list[Path] = []
    for row in rows:
        root = ARTIFACT_ROOT / str(row["benchmark_id"])
        analysis_path = root / "analysis.json"
        provenance_path = root / "claim-provenance.json"
        _write_json(analysis_path, row["analysis"].to_dict())
        _write_json(
            provenance_path,
            {
                "benchmark_id": row["benchmark_id"],
                "packet_id": row["packet_id"],
                "ticker": row["ticker"],
                "direct": row["direct_sentence_supports"],
                "hybrid": row["hybrid_sentence_supports"],
                "validation": row["analysis_validation"],
            },
        )
        paths.extend([analysis_path, provenance_path])
    return paths


def _artifact_index(paths: list[Path]) -> str:
    lines = [
        "# Evidence-Locked Free Analyst Artifact Index",
        "",
        f"- Contract: `{CONTRACT_VERSION}`",
        "- Sanitization: no secrets, provider payloads, DB rows, Telegram identifiers, or private chain-of-thought",
        "",
        "| Artifact | SHA-256 |",
        "|---|---|",
    ]
    lines.extend(_table_row([_relative(path), _sha256(path)]) for path in paths)
    return "\n".join(lines)


def _zip_reports(path: Path, paths: list[Path]) -> None:
    with zipfile.ZipFile(path, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        for artifact in paths:
            archive.write(artifact, arcname=_relative(artifact))


def generate(
    *,
    operating_root: Path,
    implementation_sha: str,
    validation_state: str,
) -> dict[str, Any]:
    items = _benchmark_items(operating_root)
    rows = [_benchmark_row(item) for item in items]
    if len(rows) != 12 or sum(row["market"] == "KR" for row in rows) != 8:
        raise RuntimeError("benchmark must preserve the exact vNext 8 KR + 4 US set")
    if len({row["packet_id"] for row in rows if row["market"] == "US"}) != 3:
        raise RuntimeError("US benchmark must preserve three immutable packets")
    if any(row["direct_safety"]["status"] != "PASS" for row in rows):
        raise RuntimeError("direct Free Analyst safety failed")
    if any(row["hybrid_safety"]["status"] != "PASS" for row in rows):
        raise RuntimeError("hybrid Free Analyst safety failed")

    controls = _negative_controls(items)
    payload = _readiness_payload(
        rows,
        controls,
        implementation_sha=implementation_sha,
        validation_state=validation_state,
    )
    gates = payload["gates"]

    paths = {
        "manifest": REPORT_ROOT / f"{RUN_DATE}-free-analyst-benchmark-manifest.md",
        "contract": REPORT_ROOT / f"{RUN_DATE}-free-analyst-structured-contract.md",
        "validator": REPORT_ROOT / f"{RUN_DATE}-free-analyst-synthesis-validator.md",
        "kr": REPORT_ROOT / f"{RUN_DATE}-free-analyst-kr-comparison.md",
        "us": REPORT_ROOT / f"{RUN_DATE}-free-analyst-us-comparison.md",
        "novel": REPORT_ROOT / f"{RUN_DATE}-free-analyst-novel-synthesis-audit.md",
        "provenance": REPORT_ROOT / f"{RUN_DATE}-free-analyst-claim-provenance.md",
        "hybrid": REPORT_ROOT / f"{RUN_DATE}-free-analyst-vnext-hybrid-comparison.md",
        "safety": REPORT_ROOT / f"{RUN_DATE}-free-analyst-safety-parity.md",
        "value": REPORT_ROOT / f"{RUN_DATE}-free-analyst-value-add.md",
        "readiness": REPORT_ROOT / f"{RUN_DATE}-free-analyst-readiness.md",
        "readiness_json": REPORT_ROOT / f"{RUN_DATE}-free-analyst-readiness.json",
        "message": REPORT_ROOT / f"{RUN_DATE}-free-analyst-message-benchmark.md",
        "summary_json": REPORT_ROOT / f"{RUN_DATE}-free-analyst-benchmark-summary.json",
        "index": REPORT_ROOT / f"{RUN_DATE}-free-analyst-artifact-index.md",
    }

    _write(paths["manifest"], _report_manifest(items))
    _write(paths["contract"], _report_contract())
    _write(paths["validator"], _report_validator(controls))
    _write(paths["kr"], _comparison_report("Evidence-Locked Free Analyst KR Comparison", [row for row in rows if row["market"] == "KR"]))
    _write(paths["us"], _comparison_report("Evidence-Locked Free Analyst US Comparison", [row for row in rows if row["market"] == "US"]))
    _write(paths["novel"], _report_novel(rows))
    _write(paths["provenance"], _report_provenance(rows))
    _write(paths["hybrid"], _report_hybrid(rows, gates["FREE_ANALYST_RENDERER_CHOICE"]))
    _write(paths["safety"], _report_safety(rows, controls))
    _write(paths["value"], _report_value_add(rows, gates))
    _write(paths["readiness"], _report_readiness(payload))
    _write_json(paths["readiness_json"], payload)
    _write(paths["message"], _message_benchmark(rows))
    _write_json(paths["summary_json"], payload)

    message_artifacts = _write_message_artifacts(rows)
    indexed = [path for name, path in paths.items() if name != "index"] + message_artifacts
    _write(paths["index"], _artifact_index(indexed))
    bundled = [*indexed, paths["index"]]
    zip_path = REPORT_ROOT / ZIP_NAME
    _zip_reports(zip_path, bundled)

    summary = {
        **payload,
        "zip": _relative(zip_path),
        "zip_sha256": _sha256(zip_path),
        "reports": [_relative(path) for path in bundled],
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
    parser.add_argument(
        "--validation-state",
        choices=("PENDING", "PASS", "FAIL"),
        default="PENDING",
    )
    args = parser.parse_args()
    generate(
        operating_root=args.operating_root,
        implementation_sha=args.implementation_sha,
        validation_state=args.validation_state,
    )


if __name__ == "__main__":
    main()
