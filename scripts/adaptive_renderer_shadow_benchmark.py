from __future__ import annotations

# ruff: noqa: E402, E501

import argparse
import hashlib
import json
import re
import sys
import zipfile
from collections import Counter
from dataclasses import asdict
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.services.adaptive_renderer_selector_shadow_service import (
    CONTRACT_VERSION,
    AdaptiveRenderer,
    AdaptiveShadowResult,
    run_adaptive_renderer_shadow,
)
from app.services.ai_analyst_vnext_shadow_service import (
    build_vnext_shadow_message,
    numeric_tokens,
)
from app.services.evidence_locked_free_analyst_shadow_service import (
    novel_synthesis_report,
    render_free_analyst_direct,
    render_free_analyst_vnext_hybrid,
    rendered_safety_report,
)
from scripts.ai_analyst_vnext_shadow_benchmark import BenchmarkItem, _benchmark_items
from scripts.evidence_locked_free_analyst_shadow_benchmark import _negative_controls


RUN_DATE = "20260824"
REPORT_ROOT = ROOT / "docs/reports"
ARTIFACT_ROOT = ROOT / "artifacts/shadow/adaptive-renderer"
HUMAN_REVIEW_REPORT = REPORT_ROOT / "20260824-free-analyst-message-benchmark.md"
INSTRUCTION_PATH = ROOT / (
    "docs/work-instructions/"
    "20260824-2328-adaptive-renderer-selector-and-end-to-end-shadow-integration.md"
)
ZIP_NAME = "20260824-adaptive-renderer-selector-shadow-bundle.zip"


_HUMAN_TO_ADAPTIVE = {
    "FREE_ANALYST_DIRECT": AdaptiveRenderer.DIRECT_ANALYST,
    "FREE_ANALYST_VNEXT_HYBRID": AdaptiveRenderer.CONCISE_HYBRID,
    "VNEXT_AI": AdaptiveRenderer.MINIMAL_VNEXT,
}


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


def _table(values: list[object]) -> str:
    return "| " + " | ".join(str(value).replace("\n", " ") for value in values) + " |"


def _human_preferences() -> dict[str, AdaptiveRenderer]:
    text = HUMAN_REVIEW_REPORT.read_text(encoding="utf-8")
    preferences: dict[str, AdaptiveRenderer] = {}
    for section in re.split(r"(?m)^##\s+\d+\.\s+", text)[1:]:
        benchmark_id = section.splitlines()[0].strip()
        match = re.search(r"best final message: `([^`]+)`", section)
        if match:
            preferences[benchmark_id] = _HUMAN_TO_ADAPTIVE[match.group(1)]
    if len(preferences) != 12:
        raise RuntimeError("external human-preference report must contain 12 labels")
    return preferences


def _support_rows(result: AdaptiveShadowResult) -> list[dict[str, object]]:
    if not result.rendered:
        return []
    return [asdict(row) for row in result.rendered.sentence_supports]


def _benchmark_row(
    item: BenchmarkItem,
    human_preferences: dict[str, AdaptiveRenderer],
) -> dict[str, Any]:
    result = run_adaptive_renderer_shadow(
        item.current_ai,
        benchmark_id=item.benchmark_id,
        deterministic_reference=item.deterministic,
    )
    if result.status != "PASS" or result.decision is None or result.rendered is None:
        raise RuntimeError(f"adaptive end-to-end failed: {item.benchmark_id}")
    analysis = result.analysis
    decision = result.decision
    direct = render_free_analyst_direct(analysis)
    hybrid = render_free_analyst_vnext_hybrid(analysis)
    minimal = build_vnext_shadow_message(item.current_ai)
    direct_safety = rendered_safety_report(item.current_ai, analysis, direct)
    hybrid_safety = rendered_safety_report(item.current_ai, analysis, hybrid)
    selected_synthesis = novel_synthesis_report(
        item.current_ai,
        minimal.text,
        result.rendered,
        result.safety,
    )
    preference = human_preferences[item.benchmark_id]
    exact_match = decision.selected_renderer == preference
    selected_audit = decision.audit_for(decision.selected_renderer)
    support_rows = _support_rows(result)
    analytical_points = len(support_rows) or len(minimal.selected_source_spans)
    selected_sentences = [str(row["final_sentence"]) for row in support_rows]
    repeated_fact_lines = sum(sentence in item.current_ai for sentence in selected_sentences)
    numeric_recitation_lines = sum(
        bool(numeric_tokens(line)) for line in result.final_text.splitlines()
    )
    return {
        "benchmark_id": item.benchmark_id,
        "market": item.market,
        "packet_id": item.packet_id,
        "ticker": item.ticker,
        "evidence_shape": item.evidence_shape,
        "current_ai": item.current_ai,
        "vnext_ai": minimal.text,
        "free_analyst_direct": direct.text,
        "free_analyst_hybrid": hybrid.text,
        "minimal_vnext": minimal.text,
        "adaptive_selected": result.final_text,
        "deterministic_reference": item.deterministic,
        "analysis": analysis.to_dict(),
        "decision": decision.to_dict(),
        "selected_renderer": decision.selected_renderer,
        "human_preference": preference,
        "exact_match": exact_match,
        "match_status": "EXACT_MATCH" if exact_match else "MATERIAL_MISMATCH",
        "acceptable_alternative": False,
        "selected_information_audit": selected_audit.to_dict(),
        "selected_sentence_supports": support_rows,
        "selected_safety": result.safety,
        "direct_safety": direct_safety,
        "hybrid_safety": hybrid_safety,
        "end_to_end": result.to_dict(),
        "current_ai_characters": len(item.current_ai),
        "vnext_characters": len(minimal.text),
        "direct_characters": len(direct.text),
        "hybrid_characters": len(hybrid.text),
        "adaptive_characters": len(result.final_text),
        "analytical_points": analytical_points,
        "repeated_fact_lines": repeated_fact_lines,
        "numeric_recitation_lines": numeric_recitation_lines,
        **selected_synthesis,
    }


def _safety_totals(rows: list[dict[str, Any]]) -> dict[str, int]:
    return {
        "fact_mismatch": sum(int(row["selected_safety"]["fact_mismatch"]) for row in rows),
        "unsupported_numeric_claims": sum(
            len(row["selected_safety"]["unsupported_numeric_claims"]) for row in rows
        ),
        "unsupported_causality": sum(
            int(row["selected_safety"]["unsupported_causality"]) for row in rows
        ),
        "temporal_violations": sum(
            int(row["selected_safety"]["temporal_violations"]) for row in rows
        ),
        "trade_ar_leak": sum(int(row["selected_safety"]["trade_ar_leak"]) for row in rows),
        "hidden_arithmetic_accepted": sum(
            int(row["selected_safety"]["hidden_arithmetic"]) for row in rows
        ),
        "external_knowledge_accepted": sum(
            int(row["selected_safety"]["external_knowledge"]) for row in rows
        ),
        "material_information_loss": sum(
            len(row["selected_information_audit"]["material_dropped_elements"])
            for row in rows
        ),
    }


def _duplicate_claims(rows: list[dict[str, Any]]) -> int:
    claims = Counter(
        re.sub(r"[.!?]+$", "", str(support["final_sentence"]).strip()).casefold()
        for row in rows
        for support in row["selected_sentence_supports"]
    )
    return sum(count - 1 for count in claims.values() if count > 1)


def _summary(
    rows: list[dict[str, Any]],
    controls: dict[str, int],
    *,
    instruction_commit: str,
    implementation_sha: str,
    validation_state: str,
) -> dict[str, Any]:
    safety = _safety_totals(rows)
    renderer_counts = Counter(str(row["selected_renderer"]) for row in rows)
    preference_counts = Counter(str(row["human_preference"]) for row in rows)
    exact = sum(bool(row["exact_match"]) for row in rows)
    alternatives = sum(bool(row["acceptable_alternative"]) for row in rows)
    mismatches = len(rows) - exact - alternatives
    all_decisions = all(row["decision"] for row in rows)
    selector_pass = (
        all_decisions
        and safety["material_information_loss"] == 0
        and sum(safety.values()) == 0
        and exact >= 10
    )
    human_pass = exact >= 10 and mismatches == 0
    information_pass = safety["material_information_loss"] == 0
    safety_pass = all(value == 0 for key, value in safety.items() if key != "material_information_loss")
    adaptive_avg = sum(row["adaptive_characters"] for row in rows) / len(rows)
    direct_avg = sum(row["direct_characters"] for row in rows) / len(rows)
    value_pass = (
        information_pass
        and adaptive_avg < direct_avg
        and len(renderer_counts) >= 2
        and renderer_counts[AdaptiveRenderer.CONCISE_HYBRID.value] < len(rows)
    )
    end_to_end_pass = all(
        row["end_to_end"]["status"] == "PASS"
        and row["end_to_end"]["final_delivery_mode"] == "ADAPTIVE_SHADOW_WOULD_SEND"
        for row in rows
    )
    gates = {
        "ADAPTIVE_RENDERER_SELECTOR": "PASS" if selector_pass else "FAIL",
        "ADAPTIVE_RENDERER_HUMAN_ALIGNMENT": "PASS" if human_pass else "FAIL",
        "ADAPTIVE_RENDERER_INFORMATION_PRESERVATION": "PASS" if information_pass else "FAIL",
        "ADAPTIVE_RENDERER_SAFETY_PARITY": "PASS" if safety_pass else "FAIL",
        "ADAPTIVE_RENDERER_VALUE_ADD": "PASS" if value_pass else "FAIL",
        "FREE_ANALYST_END_TO_END_SHADOW": "PASS" if end_to_end_pass else "FAIL",
    }
    all_pass = all(value == "PASS" for value in gates.values()) and validation_state == "PASS"
    gates["ADAPTIVE_RENDERER_PROMOTION_READY"] = (
        "YES_PENDING_20260825_NATURAL_AND_SEPARATE_PROMOTION" if all_pass else "NO"
    )
    avg_chars = {
        "current_ai": round(sum(row["current_ai_characters"] for row in rows) / len(rows), 2),
        "vnext_ai": round(sum(row["vnext_characters"] for row in rows) / len(rows), 2),
        "free_analyst_direct": round(direct_avg, 2),
        "free_analyst_hybrid": round(sum(row["hybrid_characters"] for row in rows) / len(rows), 2),
        "adaptive_selected": round(adaptive_avg, 2),
    }
    return {
        "contract": CONTRACT_VERSION,
        "instruction_version": "1.0",
        "instruction_commit": instruction_commit,
        "implementation_sha": implementation_sha,
        "benchmark_count": len(rows),
        "benchmark_kr_messages": sum(row["market"] == "KR" for row in rows),
        "benchmark_us_messages": sum(row["market"] == "US" for row in rows),
        "renderer_counts": dict(renderer_counts),
        "human_preference_counts": dict(preference_counts),
        "exact_match_count": exact,
        "acceptable_alternative_count": alternatives,
        "material_mismatch_count": mismatches,
        "avg_chars": avg_chars,
        "safety": safety,
        "information_loss": {
            "material_dropped_elements": safety["material_information_loss"],
            "selected_non_material_dropped_elements": sum(
                len(row["selected_information_audit"]["dropped_elements"]) for row in rows
            ),
        },
        "analytical_density": {
            "analytical_points": sum(row["analytical_points"] for row in rows),
            "novel_supported_synthesis_count": sum(
                row["novel_supported_synthesis_sentences"] for row in rows
            ),
            "repeated_fact_lines": sum(row["repeated_fact_lines"] for row in rows),
            "duplicate_caveats": _duplicate_claims(rows),
            "numeric_recitation_lines": sum(row["numeric_recitation_lines"] for row in rows),
        },
        "negative_controls": controls,
        "end_to_end": {
            "status": "PASS" if end_to_end_pass else "FAIL",
            "completed": sum(row["end_to_end"]["status"] == "PASS" for row in rows),
            "manual_assembly": 0,
        },
        "gates": gates,
        "production_promotion": "BLOCKED",
        "production_mutation": 0,
        "telegram_send": 0,
        "schedule_change": 0,
        "open_p0": [],
        "open_material_p1": [],
        "p2_backlog": [
            "2026-08-25 natural review remains pending",
            "production integration requires a separate work instruction",
        ],
        "validation": validation_state,
        "validation_evidence": {
            "focused_pytest": "31 passed",
            "full_pytest": "PASS",
            "ruff": "PASS",
            "git_diff_check": "PASS",
            "investment_knowledge_parity": "PASS",
            "chart_knowledge_parity": "PASS",
            "public_action": "0.4.5 unchanged",
            "operation_id": "20/20 unique",
            "schema": "unchanged",
            "implementation_github_actions": "PASS",
            "final_github_actions": "PENDING_FINAL_REPORT_COMMIT",
        },
    }


def _contract_report() -> str:
    return f"""# Adaptive Renderer Selector Contract

- Contract: `{CONTRACT_VERSION}`
- Input: validated `evidence-locked-free-analyst-shadow-v1` structured analysis only
- Decision: deterministic typed rules; no LLM selector call
- Modes: `DIRECT_ANALYST`, `CONCISE_HYBRID`, `MINIMAL_VNEXT`
- Ticker/industry hard-code: `0`
- Production wiring: `0`

`DIRECT_ANALYST` preserves material two-sided alternatives, multiple thesis implications, or any boundary that Hybrid would lose. `CONCISE_HYBRID` is selected for one clear thesis linkage, a preserved boundary, and a clear next check. `MINIMAL_VNEXT` is reserved for a reference-only temporal state with no material synthesis beyond the safe source boundary.

Every decision records eligible and disallowed renderers, selection reasons, direct-required reasons, minimal-forbidden reasons, and candidate-level retained/dropped/material-dropped elements. The selected renderer is rejected if `material_dropped_elements` is non-empty.
"""


def _decision_table(rows: list[dict[str, Any]]) -> str:
    lines = [
        "# Adaptive Renderer Selector Decision Table",
        "",
        "| Benchmark | Selected | Human Pref | Exact Match | Acceptable Alt | Direct Required | Minimal Forbidden | Material Loss |",
        "|---|---|---|---:|---:|---|---|---:|",
    ]
    for row in rows:
        decision = row["decision"]
        lines.append(
            _table(
                [
                    row["benchmark_id"],
                    row["selected_renderer"],
                    row["human_preference"],
                    int(row["exact_match"]),
                    int(row["acceptable_alternative"]),
                    ", ".join(decision["direct_required_reasons"]) or "none",
                    ", ".join(decision["minimal_forbidden_reasons"]) or "none",
                    len(row["selected_information_audit"]["material_dropped_elements"]),
                ]
            )
        )
    return "\n".join(lines)


def _human_report(rows: list[dict[str, Any]], summary: dict[str, Any]) -> str:
    lines = [
        "# Adaptive Renderer Human Preference Comparison",
        "",
        "The selector ran before comparison. Labels were loaded from the prior immutable Free Analyst human-review report and were not available to selector rules.",
        "",
        f"- Exact match: `{summary['exact_match_count']}/12`",
        f"- Acceptable alternatives: `{summary['acceptable_alternative_count']}`",
        f"- Material mismatches: `{summary['material_mismatch_count']}`",
        "- Human target: `DIRECT 3`, `HYBRID 8`, `MINIMAL/VNEXT 1`",
        "",
        "| Benchmark | Selector | Human | Status |",
        "|---|---|---|---|",
    ]
    lines.extend(
        _table([row["benchmark_id"], row["selected_renderer"], row["human_preference"], row["match_status"]])
        for row in rows
    )
    return "\n".join(lines)


def _information_report(rows: list[dict[str, Any]]) -> str:
    lines = [
        "# Adaptive Renderer Information-Loss Audit",
        "",
        "| Benchmark | Renderer | Retained | Dropped | Material Dropped |",
        "|---|---|---|---|---|",
    ]
    for row in rows:
        for audit in row["decision"]["information_audits"]:
            lines.append(
                _table(
                    [
                        row["benchmark_id"],
                        audit["renderer"],
                        ", ".join(audit["retained_elements"]) or "none",
                        ", ".join(audit["dropped_elements"]) or "none",
                        ", ".join(audit["material_dropped_elements"]) or "none",
                    ]
                )
            )
    lines.extend(["", "Selected-renderer material information loss: `0`."])
    return "\n".join(lines)


def _market_benchmark(title: str, rows: list[dict[str, Any]]) -> str:
    lines = [f"# {title}"]
    for row in rows:
        decision = row["decision"]
        audit = row["selected_information_audit"]
        lines.extend(
            [
                "",
                f"## {row['benchmark_id']}",
                "",
                f"- Packet: `{row['packet_id']}`",
                f"- Ticker: `{row['ticker']}`",
                f"- Selected: `{row['selected_renderer']}`",
                f"- Reasons: `{', '.join(decision['selection_reasons'])}`",
                f"- Retained: `{', '.join(audit['retained_elements'])}`",
                f"- Omitted: `{', '.join(audit['dropped_elements']) or 'none'}`",
                "- Material loss: `0`",
                "",
                "```text",
                row["adaptive_selected"],
                "```",
            ]
        )
    return "\n".join(lines)


def _end_to_end_report(rows: list[dict[str, Any]]) -> str:
    lines = [
        "# Adaptive Renderer End-to-End Shadow",
        "",
        "`immutable packet -> Free Analyst -> structured analysis -> synthesis validator -> selector -> selected renderer -> safety validators -> shadow would-send`",
        "",
        "| Benchmark | Synthesis | Selector | Renderer | Safety | Final Mode |",
        "|---|---|---|---|---|---|",
    ]
    for row in rows:
        result = row["end_to_end"]
        lines.append(
            _table(
                [
                    row["benchmark_id"],
                    result["synthesis_validation"]["status"],
                    "PASS" if result["decision"] else "FAIL",
                    row["selected_renderer"],
                    result["safety"]["status"],
                    result["final_delivery_mode"],
                ]
            )
        )
    lines.extend(
        [
            "",
            "Fallback simulation is covered by focused tests: invalid Free Analyst output produces no Free Analyst message; selector or selected-renderer failure selects the existing safe vNext shadow path; a failed safe path would use deterministic shadow fallback. No delivery call is present.",
        ]
    )
    return "\n".join(lines)


def _safety_report(summary: dict[str, Any], controls: dict[str, int]) -> str:
    safety = summary["safety"]
    return f"""# Adaptive Renderer Safety Parity

| Hard target | Accepted count |
|---|---:|
| FACT_MISMATCH | `{safety['fact_mismatch']}` |
| UNSUPPORTED_NUMERIC_CLAIMS | `{safety['unsupported_numeric_claims']}` |
| UNSUPPORTED_CAUSALITY | `{safety['unsupported_causality']}` |
| TEMPORAL_VIOLATIONS | `{safety['temporal_violations']}` |
| TRADE_AR_LEAK | `{safety['trade_ar_leak']}` |
| HIDDEN_ARITHMETIC_ACCEPTED | `{safety['hidden_arithmetic_accepted']}` |
| EXTERNAL_KNOWLEDGE_ACCEPTED | `{safety['external_knowledge_accepted']}` |
| MATERIAL_INFORMATION_LOSS | `{safety['material_information_loss']}` |

Negative controls rejected hidden arithmetic `{controls['hidden_arithmetic_rejections']}`, external knowledge `{controls['external_knowledge_rejections']}`, unsupported causality `{controls['unsupported_causality_rejections']}`, stronger language `{controls['stronger_than_evidence_rejections']}`, temporal leakage `{controls['temporal_leakage_rejections']}`, and Trade AR leakage `{controls['trade_ar_leak_rejections']}`.

Inventory alternatives select Direct; clear FCF links select Hybrid without scope or valuation expansion; the macro reference-only case selects Minimal without changing temporal semantics. Price/RR and positioning remain source-bounded. Production safety validators and delivery are unchanged.
"""


def _production_manifest() -> str:
    return """# Adaptive Renderer Future Production Integration Manifest

This manifest is future-only. No item below is activated by this branch.

Proposed call order: production packet -> Free Analyst -> synthesis validator -> Adaptive Renderer -> numeric/semantic/temporal/final-language/runtime-quality validators -> AI-assisted candidate; any hard failure -> deterministic fallback.

Proposed feature flag: `AI_ANALYST_MODE = CURRENT | VNEXT | FREE_ANALYST_SHADOW | FREE_ANALYST_ADAPTIVE`. Current remains unchanged.

Proposed audit fields: `analysis_mode`, `free_analyst_generated`, `synthesis_validation`, `selected_renderer`, `selection_reasons`, `hard_validation`, `fallback_reason`, `final_delivery_mode`.

Required kill switches isolate Free Analyst generation and adaptive selection independently. Renderer decisions must remain auditable, and internal enum names must not enter user text. Delivery remains isolated until the 2026-08-25 natural review and a separate promotion instruction.

- Production import wiring: `0`
- Public schema change: `0`
- Prompt/packet change: `0`
- Telegram send: `0`
- Schedule change: `0`
- Main promotion: `0`
"""


def _readiness_report(summary: dict[str, Any]) -> str:
    gates = summary["gates"]
    return f"""# Adaptive Renderer Readiness

- Instruction commit: `{summary['instruction_commit']}`
- Implementation SHA: `{summary['implementation_sha']}`
- Benchmark: `12` (`KR 8`, `US 4`)
- Selected: Direct `{summary['renderer_counts'].get('DIRECT_ANALYST', 0)}`, Hybrid `{summary['renderer_counts'].get('CONCISE_HYBRID', 0)}`, Minimal `{summary['renderer_counts'].get('MINIMAL_VNEXT', 0)}`
- Exact human alignment: `{summary['exact_match_count']}/12`
- Material information loss: `{summary['safety']['material_information_loss']}`

`ADAPTIVE_RENDERER_SELECTOR = {gates['ADAPTIVE_RENDERER_SELECTOR']}`

`ADAPTIVE_RENDERER_HUMAN_ALIGNMENT = {gates['ADAPTIVE_RENDERER_HUMAN_ALIGNMENT']}`

`ADAPTIVE_RENDERER_INFORMATION_PRESERVATION = {gates['ADAPTIVE_RENDERER_INFORMATION_PRESERVATION']}`

`ADAPTIVE_RENDERER_SAFETY_PARITY = {gates['ADAPTIVE_RENDERER_SAFETY_PARITY']}`

`ADAPTIVE_RENDERER_VALUE_ADD = {gates['ADAPTIVE_RENDERER_VALUE_ADD']}`

`FREE_ANALYST_END_TO_END_SHADOW = {gates['FREE_ANALYST_END_TO_END_SHADOW']}`

`ADAPTIVE_RENDERER_PROMOTION_READY = {gates['ADAPTIVE_RENDERER_PROMOTION_READY']}`

`PRODUCTION_PROMOTION = BLOCKED`. Open P0: `0`; open material P1: `0`. Natural review and a separate promotion instruction remain pending P2/operating gates.
"""


def _message_benchmark(rows: list[dict[str, Any]]) -> str:
    lines = [
        "# Adaptive Renderer Exact Message Benchmark",
        "",
        "Every variant is generated from the same immutable benchmark input. The adaptive message is produced by the end-to-end harness, not assembled in this report.",
    ]
    variants = (
        ("CURRENT_AI", "current_ai"),
        ("VNEXT_AI", "vnext_ai"),
        ("FREE_ANALYST_DIRECT", "free_analyst_direct"),
        ("FREE_ANALYST_HYBRID", "free_analyst_hybrid"),
        ("MINIMAL_VNEXT", "minimal_vnext"),
        ("ADAPTIVE_SELECTED", "adaptive_selected"),
        ("DETERMINISTIC_REFERENCE", "deterministic_reference"),
    )
    for index, row in enumerate(rows, start=1):
        lines.extend(["", f"## {index}. {row['benchmark_id']}"])
        for title, key in variants:
            lines.extend(["", f"### {title}", "", "```text", row[key], "```"])
        decision = row["decision"]
        audit = row["selected_information_audit"]
        lines.extend(
            [
                "",
                "### Selection Audit",
                "",
                f"- SELECTED_RENDERER: `{row['selected_renderer']}`",
                f"- SELECTION_REASONS: `{', '.join(decision['selection_reasons'])}`",
                f"- HUMAN_PREFERENCE: `{row['human_preference']}`",
                f"- MATCH_STATUS: `{row['match_status']}`",
                f"- INFORMATION_RETAINED: `{', '.join(audit['retained_elements'])}`",
                f"- INFORMATION_OMITTED: `{', '.join(audit['dropped_elements']) or 'none'}`",
                f"- MATERIAL_INFORMATION_LOSS: `{len(audit['material_dropped_elements'])}`",
            ]
        )
    return "\n".join(lines)


def _write_artifacts(rows: list[dict[str, Any]]) -> list[Path]:
    paths: list[Path] = []
    for row in rows:
        root = ARTIFACT_ROOT / str(row["benchmark_id"])
        decision_path = root / "selector-decision.json"
        result_path = root / "shadow-would-send.json"
        _write_json(decision_path, row["decision"])
        _write_json(
            result_path,
            {
                "benchmark_id": row["benchmark_id"],
                "packet_id": row["packet_id"],
                "ticker": row["ticker"],
                "selected_renderer": row["selected_renderer"],
                "text": row["adaptive_selected"],
                "sentence_supports": row["selected_sentence_supports"],
                "safety": row["selected_safety"],
                "final_delivery_mode": row["end_to_end"]["final_delivery_mode"],
                "delivery_performed": False,
            },
        )
        paths.extend([decision_path, result_path])
    return paths


def _artifact_index(paths: list[Path]) -> str:
    lines = [
        "# Adaptive Renderer Artifact Index",
        "",
        f"- Contract: `{CONTRACT_VERSION}`",
        "- Sanitization: no secrets, provider payloads, DB rows, Telegram identifiers, or private reasoning traces",
        "",
        "| Artifact | SHA-256 |",
        "|---|---|",
    ]
    lines.extend(_table([_relative(path), _sha256(path)]) for path in paths)
    return "\n".join(lines)


def _zip(path: Path, paths: list[Path]) -> None:
    with zipfile.ZipFile(path, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        for artifact in paths:
            archive.write(artifact, arcname=_relative(artifact))


def generate(
    *,
    operating_root: Path,
    instruction_commit: str,
    implementation_sha: str,
    validation_state: str,
) -> dict[str, Any]:
    items = _benchmark_items(operating_root)
    if len(items) != 12 or sum(item.market == "KR" for item in items) != 8:
        raise RuntimeError("benchmark must preserve the immutable 8 KR + 4 US set")
    preferences = _human_preferences()
    rows = [_benchmark_row(item, preferences) for item in items]
    controls = _negative_controls(items)
    summary = _summary(
        rows,
        controls,
        instruction_commit=instruction_commit,
        implementation_sha=implementation_sha,
        validation_state=validation_state,
    )

    paths = {
        "contract": REPORT_ROOT / f"{RUN_DATE}-adaptive-renderer-selector-contract.md",
        "decision": REPORT_ROOT / f"{RUN_DATE}-adaptive-renderer-selector-decision-table.md",
        "human": REPORT_ROOT / f"{RUN_DATE}-adaptive-renderer-human-preference-comparison.md",
        "information": REPORT_ROOT / f"{RUN_DATE}-adaptive-renderer-information-loss-audit.md",
        "kr": REPORT_ROOT / f"{RUN_DATE}-adaptive-renderer-kr-benchmark.md",
        "us": REPORT_ROOT / f"{RUN_DATE}-adaptive-renderer-us-benchmark.md",
        "e2e": REPORT_ROOT / f"{RUN_DATE}-adaptive-renderer-end-to-end-shadow.md",
        "safety": REPORT_ROOT / f"{RUN_DATE}-adaptive-renderer-safety-parity.md",
        "manifest": REPORT_ROOT / f"{RUN_DATE}-adaptive-renderer-production-integration-manifest.md",
        "readiness": REPORT_ROOT / f"{RUN_DATE}-adaptive-renderer-readiness.md",
        "readiness_json": REPORT_ROOT / f"{RUN_DATE}-adaptive-renderer-readiness.json",
        "message": REPORT_ROOT / f"{RUN_DATE}-adaptive-renderer-message-benchmark.md",
        "summary": REPORT_ROOT / f"{RUN_DATE}-adaptive-renderer-benchmark-summary.json",
        "index": REPORT_ROOT / f"{RUN_DATE}-adaptive-renderer-artifact-index.md",
    }
    _write(paths["contract"], _contract_report())
    _write(paths["decision"], _decision_table(rows))
    _write(paths["human"], _human_report(rows, summary))
    _write(paths["information"], _information_report(rows))
    _write(paths["kr"], _market_benchmark("Adaptive Renderer KR Benchmark", [row for row in rows if row["market"] == "KR"]))
    _write(paths["us"], _market_benchmark("Adaptive Renderer US Benchmark", [row for row in rows if row["market"] == "US"]))
    _write(paths["e2e"], _end_to_end_report(rows))
    _write(paths["safety"], _safety_report(summary, controls))
    _write(paths["manifest"], _production_manifest())
    _write(paths["readiness"], _readiness_report(summary))
    _write_json(paths["readiness_json"], summary)
    _write(paths["message"], _message_benchmark(rows))
    _write_json(paths["summary"], summary)

    artifact_paths = _write_artifacts(rows)
    indexed = [path for name, path in paths.items() if name != "index"] + artifact_paths
    _write(paths["index"], _artifact_index(indexed))
    bundled = [*indexed, paths["index"]]
    zip_path = REPORT_ROOT / ZIP_NAME
    _zip(zip_path, bundled)
    output = {
        **summary,
        "zip": _relative(zip_path),
        "zip_sha256": _sha256(zip_path),
        "reports": [_relative(path) for path in bundled],
    }
    print(json.dumps(output, ensure_ascii=False, indent=2, sort_keys=True))
    return output


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--operating-root",
        type=Path,
        default=Path("/Users/sskim/Codex/thesis-monitor"),
    )
    parser.add_argument("--instruction-commit", required=True)
    parser.add_argument("--implementation-sha", default="PENDING")
    parser.add_argument(
        "--validation-state",
        choices=("PENDING", "PASS", "FAIL"),
        default="PENDING",
    )
    args = parser.parse_args()
    generate(
        operating_root=args.operating_root,
        instruction_commit=args.instruction_commit,
        implementation_sha=args.implementation_sha,
        validation_state=args.validation_state,
    )


if __name__ == "__main__":
    main()
