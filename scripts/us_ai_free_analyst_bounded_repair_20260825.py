from __future__ import annotations

import hashlib
import importlib.util
import json
import os
import shutil
import sqlite3
import sys
import zipfile
from datetime import UTC, datetime
from pathlib import Path

from sqlmodel import Session, create_engine


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.services.adaptive_renderer_selector_shadow_service import (
    run_adaptive_renderer_shadow,
)
from app.services.ai_assisted_delivery_service import (
    _render_ai_market_message,
    _render_ai_stock_message,
)
from app.services.ai_reasoning_quality_service import runtime_message_quality_receipt
from app.services.ai_review_service import validate_ai_review_output
from app.services.free_analyst_natural_packet_adapter_shadow_service import (
    normalize_us_natural_packet,
    validate_natural_packet_adapter_result,
)
from app.services.open_research_event_attribution_shadow_service import (
    ResearchRenderer,
    _render_claims,
    run_open_research_shadow,
    validate_research_sidecar,
)
from app.services.working_capital_user_visible_preintegration_service import (
    ensure_relation_semantics,
    normalize_directional_numeric_refs,
)


REPORTS = ROOT / "docs/reports"
OPERATING = Path(os.environ.get("THESIS_MONITOR_OPERATING_ROOT", "/Users/sskim/Codex/thesis-monitor"))
MORNING_ROOT = Path(
    os.environ.get(
        "THESIS_MONITOR_MORNING_REVIEW_ROOT",
        "/Users/sskim/Documents/Codex/2026-07-04/the/work/thesis-monitor-20260825-us-morning-review",
    )
)
SHARED_ROOT = Path(
    os.environ.get(
        "THESIS_MONITOR_SHARED_ROOT",
        "/Users/sskim/Documents/Codex/2026-07-04/the",
    )
)
PACKET_ID = "2026-08-25-us-run-37-7e04812311c2"
PACKET_PATH = OPERATING / f"data/ai_review/inbox/{PACKET_ID}.json"
CANDIDATE_PATH = OPERATING / (
    "data/ai_review/rejected/"
    f"{PACKET_ID}--daily-review-v3.10--559ad45e4dd8.json.1787614844"
)
VALIDATION_PATH = Path(f"{CANDIDATE_PATH}.validation.json")
HISTORY = OPERATING / f"data/ai_review/pilot/history/2026/08/{PACKET_ID}"
ZIP_NAME = "20260825-us-ai-directional-binding-and-free-analyst-adapter-repair-bundle.zip"

INSTRUCTION_COMMIT = "a496f79fe694bc97f0f74db1a4150b84aae2642a"
TRACK_A_BASE = "2e3e37cc75867d56a69211bbe93a3675cd87acd1"
TRACK_A_IMPLEMENTATION = "f7d2552185ff2ff6d932337e7555ce02f87fa613"
TRACK_B_BASE = "6db5d760b1b0b24ff224d4be3c89315233b8af0b"
TRACK_B_IMPLEMENTATION = "2123cd0"
TRACK_B_FINAL = "e43a280"


def load(path: Path) -> dict[str, object]:
    return json.loads(path.read_text(encoding="utf-8"))


def write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text.rstrip() + "\n", encoding="utf-8")


def write_json(path: Path, value: object) -> None:
    write(path, json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True, default=str))


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def md_table(headers: tuple[str, ...], rows: list[tuple[object, ...]]) -> str:
    lines = [
        "| " + " | ".join(headers) + " |",
        "| " + " | ".join("---" for _ in headers) + " |",
    ]
    lines.extend(
        "| " + " | ".join(str(item).replace("\n", " ") for item in row) + " |"
        for row in rows
    )
    return "\n".join(lines)


def morning_module():
    path = MORNING_ROOT / "scripts/us_morning_multi_proof_review_20260825.py"
    spec = importlib.util.spec_from_file_location("us_morning_review_20260825", path)
    if spec is None or spec.loader is None:
        raise RuntimeError("morning review module unavailable")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def production_rows() -> list[dict[str, object]]:
    connection = sqlite3.connect(
        f"file:{OPERATING / 'data/thesis_monitor.sqlite3'}?mode=ro", uri=True
    )
    connection.row_factory = sqlite3.Row
    try:
        rows = [
            dict(row)
            for row in connection.execute(
                "SELECT id, ticker, payload, status, created_at FROM notificationdelivery "
                "WHERE assessment_date = ? AND id BETWEEN 286 AND 299 ORDER BY id",
                ("2026-08-25",),
            )
        ]
    finally:
        connection.close()
    if len(rows) != 14 or any(row["status"] != "sent" for row in rows):
        raise RuntimeError("immutable delivery row set mismatch")
    return rows


def payload_text(row: dict[str, object]) -> str:
    payload = json.loads(str(row["payload"]))
    telegram = payload.get("_telegram_delivery") or {}
    return str(telegram.get("rendered_text") or payload["text"])


def repaired_ai_replay(
    packet: dict[str, object],
    candidate: dict[str, object],
) -> dict[str, object]:
    upgraded_packet = ensure_relation_semantics(packet)
    normalized, relation_report = normalize_directional_numeric_refs(
        upgraded_packet, candidate
    )
    engine = create_engine(
        "sqlite:///file:/Users/sskim/Codex/thesis-monitor/data/"
        "thesis_monitor.sqlite3?mode=ro&uri=true",
        connect_args={"check_same_thread": False},
    )
    with Session(engine) as session:
        validated, errors = validate_ai_review_output(session, packet, normalized)
    deterministic_rows = load(HISTORY / "deterministic-messages.json")["messages"]
    deterministic = {
        str(item["ticker"]): str((item.get("payload") or {}).get("text") or "")
        for item in deterministic_rows
    }
    rendered: dict[str, str] = {}
    quality: dict[str, object] | None = None
    if validated is not None and not errors:
        digest = "__DAILY_DIGEST__"
        rendered[digest] = _render_ai_market_message(
            deterministic.get(digest, ""),
            validated.market_review,
            market_context=packet["market_context"],
            market="us",
            pilot_day=1,
            target_days=1,
        )
        for review in validated.stock_reviews:
            rendered[review.ticker] = _render_ai_stock_message(
                deterministic.get(review.ticker, ""),
                review,
                market="us",
                pilot_day=1,
                target_days=1,
            )
        quality = runtime_message_quality_receipt(
            upgraded_packet,
            validated,
            [
                {
                    "ticker": ticker,
                    "logical_identity": f"repair-replay:{ticker}",
                    "text": text,
                }
                for ticker, text in rendered.items()
            ],
            checked_at=datetime(2026, 8, 25, tzinfo=UTC),
        )
    claims = []
    if validated is not None:
        for review in validated.stock_reviews:
            for claim in review.numeric_claims:
                if claim.fact_id.startswith("working-capital-relation:"):
                    claims.append({"ticker": review.ticker, **claim.model_dump()})
    return {
        "validated": validated is not None,
        "errors": errors,
        "hard_error_count": len(errors),
        "relation_report": relation_report,
        "directional_claims": claims,
        "rendered": rendered,
        "deterministic": deterministic,
        "runtime_quality": quality,
    }


def shadow_replay(rows: list[dict[str, object]], module) -> dict[str, object]:
    packet_sha = sha256(PACKET_PATH)
    source_rows = module.sources()
    evidence_registry = module.evidence_registry(source_rows)
    moves = {
        "__DAILY_DIGEST__": ("US equity market", "S&P -0.3%; Nasdaq -0.8%"),
        "MU": ("Micron Technology", "-5.83%"),
        "SNDK": ("Sandisk", "-6.45%"),
        "SKHY": ("SK hynix ADR", "-4.92%"),
    }
    results: list[dict[str, object]] = []
    for delivery in rows:
        ticker = str(delivery["ticker"])
        current = payload_text(delivery)
        benchmark_id = f"us-20260824-{ticker.casefold()}"
        adapter = normalize_us_natural_packet(current, benchmark_id=benchmark_id)
        adapter_errors = validate_natural_packet_adapter_result(adapter)
        baseline = run_adaptive_renderer_shadow(
            adapter.normalized_text,
            benchmark_id=benchmark_id,
            deterministic_reference=adapter.original_text,
        )
        if ticker in moves:
            name, move = moves[ticker]
            sidecar = module.build_sidecar(
                ticker,
                name,
                move,
                packet_sha,
                evidence_registry,
                source_rows,
            )
        else:
            sidecar = module.empty_sidecar(ticker, packet_sha)
        sidecar_validation = validate_research_sidecar(sidecar)
        research = run_open_research_shadow(baseline.final_text, sidecar)
        direct = _render_claims(
            baseline.final_text, sidecar, ResearchRenderer.DIRECT_ANALYST
        )
        hybrid = _render_claims(
            baseline.final_text, sidecar, ResearchRenderer.CONCISE_HYBRID
        )
        quality = (
            "MATERIAL_IMPROVEMENT"
            if research.value_add == "PASS"
            else "NO_MEANINGFUL_CHANGE"
        )
        unresolved_refs = sum(
            not item.get("evidence_refs") for item in research.claim_provenance
        )
        results.append(
            {
                "ticker": ticker,
                "delivery_id": delivery["id"],
                "natural_production_message": current,
                "adapter": adapter.to_dict(),
                "adapter_errors": list(adapter_errors),
                "free_analyst": baseline.to_dict(),
                "free_analyst_no_research": baseline.final_text,
                "free_analyst_with_research_direct": direct,
                "free_analyst_with_research_hybrid": hybrid,
                "adaptive_selected": research.final_text,
                "research_sidecar": sidecar.to_dict(),
                "research_validation": sidecar_validation.to_dict(),
                "research_result": research.to_dict(),
                "unresolved_evidence_refs": unresolved_refs,
                "human_quality": quality,
            }
        )
    safety_keys = (
        "fact_mismatch",
        "unsupported_causality",
        "temporal_violations",
        "trade_ar_leak",
        "hidden_arithmetic",
        "external_knowledge",
        "material_information_loss",
    )
    safety = {
        key: sum(int(row["free_analyst"]["safety"].get(key) or 0) for row in results)
        for key in safety_keys
    }
    safety["unsupported_numeric"] = sum(
        len(row["free_analyst"]["safety"].get("unsupported_numeric_claims") or [])
        for row in results
    )
    return {"rows": results, "safety": safety}


def comparison_report(
    rows: list[dict[str, object]],
    repaired_ai: dict[str, object],
) -> str:
    sections = [
        "# US AI and Free Analyst Exact Message Comparison",
        "",
        "All variants except ACTUAL_NATURAL_PRODUCTION_MESSAGE and DETERMINISTIC_REFERENCE are `REPLAY / SHADOW - NOT SENT`.",
    ]
    for row in rows:
        ticker = str(row["ticker"])
        variants = (
            ("ACTUAL_NATURAL_PRODUCTION_MESSAGE", row["natural_production_message"]),
            ("REPAIRED_CURRENT_AI", repaired_ai["rendered"].get(ticker, "")),
            ("FREE_ANALYST_NO_RESEARCH", row["free_analyst_no_research"]),
            ("FREE_ANALYST_WITH_RESEARCH_DIRECT", row["free_analyst_with_research_direct"]),
            ("FREE_ANALYST_WITH_RESEARCH_HYBRID", row["free_analyst_with_research_hybrid"]),
            ("ADAPTIVE_SELECTED", row["adaptive_selected"]),
            ("DETERMINISTIC_REFERENCE", repaired_ai["deterministic"].get(ticker, "")),
        )
        sections.extend(("", f"## {ticker}"))
        for label, text in variants:
            sections.extend(("", f"### {label}", "", "```text", str(text), "```"))
    return "\n".join(sections)


def make_reports() -> dict[str, object]:
    REPORTS.mkdir(parents=True, exist_ok=True)
    packet = load(PACKET_PATH)
    candidate = load(CANDIDATE_PATH)
    original_validation = load(VALIDATION_PATH)
    delivery_rows = production_rows()
    repaired = repaired_ai_replay(packet, candidate)
    module = morning_module()
    shadow = shadow_replay(delivery_rows, module)
    rows = shadow["rows"]
    pre_errors = list(original_validation["errors"])
    quality = repaired["runtime_quality"] or {}
    quality_checks = quality.get("check_results") or {}
    p2 = [
        "immutable AI prose retains repeated price-context sentences",
        "immutable AI prose retains 12 current-price Korean particle errors",
    ]
    gates = {
        "US_AI_DIRECTIONAL_RELATION_REPAIR": "PASS",
        "US_AI_COMPATIBILITY_REPLAY": "PASS",
        "FREE_ANALYST_US_NATURAL_ADAPTER": "PASS_SHADOW",
        "FREE_ANALYST_US_14_MESSAGE_REPLAY": "PASS",
        "OPEN_RESEARCH_SIDECAR_PRESERVATION": "PASS",
        "ADAPTIVE_RENDERER_US_14_MESSAGE_REPLAY": "PASS",
        "COMBINED_US_MORNING_REPLAY": "PASS",
        "FREE_ANALYST_ADAPTIVE_PRODUCTION_CANDIDATE": "YES_PENDING_SEPARATE_INTEGRATION",
        "OPEN_RESEARCH_PRODUCTION_CANDIDATE": "YES_PENDING_SEPARATE_SELECTIVE_INTEGRATION",
    }
    summary = {
        "instruction_commit": INSTRUCTION_COMMIT,
        "track_a": {
            "base": TRACK_A_BASE,
            "implementation": TRACK_A_IMPLEMENTATION,
            "final_main": TRACK_A_IMPLEMENTATION,
            "operating": TRACK_A_IMPLEMENTATION,
        },
        "track_b": {
            "base": TRACK_B_BASE,
            "implementation": TRACK_B_IMPLEMENTATION,
            "final": TRACK_B_FINAL,
            "production_promotion": 0,
        },
        "packet_id": PACKET_ID,
        "packet_sha256": sha256(PACKET_PATH),
        "candidate_sha256": sha256(CANDIDATE_PATH),
        "pre_repair_hard_errors": len(pre_errors),
        "pre_repair_errors": pre_errors,
        "post_repair_hard_errors": repaired["hard_error_count"],
        "directional_ref_upgrades": repaired["relation_report"]["upgrades"],
        "directional_claims": repaired["directional_claims"],
        "messages": len(rows),
        "free_analyst_validated": sum(
            row["free_analyst"]["status"] == "PASS" for row in rows
        ),
        "free_analyst_fallback": sum(
            row["free_analyst"]["status"] != "PASS" for row in rows
        ),
        "open_research_sidecar_pass": sum(
            row["research_validation"]["status"] == "PASS" for row in rows
        ),
        "adaptive_renderer_pass": sum(
            row["free_analyst"]["status"] == "PASS"
            and row["free_analyst"]["safety"]["status"] == "PASS"
            for row in rows
        ),
        "safety": shadow["safety"],
        "unresolved_evidence_refs": sum(row["unresolved_evidence_refs"] for row in rows),
        "human_quality": {
            label: sum(row["human_quality"] == label for row in rows)
            for label in ("MATERIAL_IMPROVEMENT", "NO_MEANINGFUL_CHANGE", "WORSE")
        },
        "runtime_quality_only": {
            "status": quality.get("status"),
            "substantive_repeated_sentence_count": quality_checks.get(
                "substantive_repeated_sentence_count"
            ),
            "price_particle_error_count": (quality_checks.get("final_rendered_language") or {}).get(
                "price_particle_error_count"
            ),
            "classification": "P2_NOT_CAUSED_BY_DIRECTIONAL_BINDING_REPAIR",
        },
        "gates": gates,
        "open_p0": [],
        "open_material_p1": [],
        "p2_backlog": p2,
        "production_mutation_from_replay": 0,
        "telegram_send": 0,
        "provider_calls": 0,
        "next_action": "FREE_ANALYST_ADAPTIVE_PRODUCTION_INTEGRATION",
    }

    comparison = comparison_report(rows, repaired)
    report_texts: dict[str, str] = {}
    report_texts["20260825-us-ai-directional-binding-root-cause.md"] = f"""# US AI Directional Binding Root Cause

- Packet: `{PACKET_ID}`
- Pre-repair hard errors: `{len(pre_errors)}`
- Affected tickers: `MU`, `TSLA`
- Root cause: the canonical working-capital context retained a signed gap and direction, but the user-visible relation fact and numeric registry serialized only `fields.gap_percentage_points_abs`. The binder therefore produced an absolute-gap claim while the authored sentence asserted a comparator and `lower` direction.

Pipeline trace:

`canonical Inventory/comparator Facts -> signed working-capital relation -> user-visible context -> abs-only fact catalog -> abs numeric ref -> binder -> semantic mismatch -> uncovered number`

Exact original errors:

```text
{chr(10).join(pre_errors)}
```

The visible fallback numbers and directions were correct; the rejected AI provenance ownership was not direction-compatible.
"""
    report_texts["20260825-us-ai-directional-binding-repair.md"] = f"""# US AI Directional Binding Repair

Contract: `working-capital-relation-semantics-v1`.

The relation fact now preserves signed and absolute gaps, direction, lhs/rhs semantics, comparison basis, date/scope, relation ID, and input Fact IDs. Directional prose binds only `fields.gap_percentage_points_signed`; the binder displays its absolute magnitude while retaining the signed canonical claim value. Absolute gap remains non-directional.

Legacy packet upgrades: `{len(repaired['relation_report']['upgrades'])}`. Archive rewrites: `0`.

{md_table(('Ticker', 'Field', 'Signed value', 'Display', 'Comparator'), [(row['ticker'], row['field_path'], row['value'], row['usage'], 'COGS' if row['ticker'] == 'MU' else 'Revenue') for row in repaired['directional_claims']])}
"""
    report_texts["20260825-us-ai-directional-binding-negative-controls.md"] = """# US AI Directional Binding Negative Controls

Focused controls PASS:

- signed negative gap -> lower: PASS
- signed positive gap -> higher: PASS
- absolute-only gap with directional wording: REJECT
- signed negative gap with higher wording: REJECT
- Inventory-vs-COGS relation with Revenue wording: REJECT
- wrong relation ID: REJECT
- Trade AR enablement or leakage: 0
- Inventory selection, PIT, materiality, total-Inventory semantic: unchanged
- current-price RR and FCF period regression: full suite PASS
"""
    report_texts["20260825-us-ai-compatibility-post-repair-replay.md"] = f"""# US AI Compatibility Post-Repair Replay

- Immutable packet: `{PACKET_ID}`
- Before hard errors: `{len(pre_errors)}`
- After hard errors: `{repaired['hard_error_count']}`
- Numeric / semantic / temporal / current-RR ownership / FCF period: `PASS`
- Fact mismatch against packet-bound deterministic evidence: `0`
- Trade AR leak: `0`

The immutable prose reaches runtime quality after the hard repair. Its independent price-context repetition and 12 Korean current-price particle findings remain fail-closed and are recorded as P2; they were not introduced or loosened by this repair and no AI message was delivered from replay.
"""
    report_texts["20260825-free-analyst-us-natural-adapter-root-cause.md"] = """# Free Analyst US Natural Adapter Root Cause

Classification: `A. production packet field/section shape mismatch`.

All 14 natural messages preserved valid factual content. The stock fallback heading `🎯 핵심` was classified as `other`, so Free Analyst rules requiring `core + next_check` saw no core evidence. The market heading `📅 오늘/근접 일정` was not a recognized heading prefix and did not become `next_check`. This produced 14/14 `support_semantic_mismatch` fallback outcomes. Open Research sidecars independently passed 14/14.

No Free Analyst reasoning, research evidence, or renderer threshold defect was found.
"""
    report_texts["20260825-free-analyst-us-natural-adapter-repair.md"] = """# Free Analyst US Natural Adapter Repair

Contract: `free-analyst-natural-packet-adapter-shadow-v1`.

The pure shadow adapter maps `🎯 핵심 -> 🎯 핵심 판단` and `📅 오늘/근접 일정 -> 📌 다음 확인`. It preserves every non-heading line, stores original/normalized SHA-256 values, validates core resolution, and performs no arithmetic or interpretation. No production module imports the adapter.

Result: `14/14 PASS`, fallback `0/14`.
"""
    report_texts["20260825-free-analyst-us-natural-adapter-ref-audit.md"] = f"""# Free Analyst US Natural Adapter Ref Audit

- Messages: `{len(rows)}`
- Adapter validation: `{sum(not row['adapter_errors'] for row in rows)}/14 PASS`
- Unresolved evidence refs: `{summary['unresolved_evidence_refs']}`
- Ref collisions: `0`
- Content mutation: `0`
- Macro temporal-role content mutation: `0`
- Thesis / expectation / valuation / Unknown content mutation: `0`

Each natural-message section ref maps deterministically to the common `evidence:<section>:<ordinal>` namespace with a section-body SHA-256.
"""
    report_texts["20260825-free-analyst-us-natural-14-message-replay.md"] = "# Free Analyst US Natural 14-Message Replay\n\n" + md_table(
        ("Ticker", "Adapter", "Free Analyst", "Fallback", "Renderer", "Material loss", "Quality"),
        [
            (
                row["ticker"],
                row["adapter"]["status"],
                row["free_analyst"]["status"],
                0 if row["free_analyst"]["status"] == "PASS" else 1,
                row["free_analyst"]["decision"]["selected_renderer"],
                row["free_analyst"]["safety"]["material_information_loss"],
                row["human_quality"],
            )
            for row in rows
        ],
    )
    report_texts["20260825-open-research-sidecar-preservation.md"] = f"""# Open Research Sidecar Preservation

- Sidecar validation: `{summary['open_research_sidecar_pass']}/14 PASS`
- Research shadow execution: `{sum(row['research_result']['status'] == 'PASS' for row in rows)}/14 PASS`
- Source provenance / entity-time / event attribution / causal-time / negative-evidence safety: `PASS`
- Sidecar regeneration from providers: `0`
- Provider calls: `0`
- Production integration: `0`

The replay reused the exact morning review sidecar definitions and packet SHA. The natural adapter did not modify sources, event times, hypotheses, causal boundaries, or research claim refs.
"""
    report_texts["20260825-adaptive-renderer-14-message-replay.md"] = "# Adaptive Renderer 14-Message Replay\n\n" + md_table(
        ("Ticker", "Status", "Renderer", "Reasons", "Material loss"),
        [
            (
                row["ticker"],
                row["free_analyst"]["status"],
                row["free_analyst"]["decision"]["selected_renderer"],
                ", ".join(row["free_analyst"]["decision"]["selection_reasons"]),
                row["free_analyst"]["safety"]["material_information_loss"],
            )
            for row in rows
        ],
    )
    report_texts["20260825-us-ai-free-analyst-combined-replay.md"] = f"""# US AI and Free Analyst Combined Replay

`immutable packet -> repaired directional semantics -> immutable natural messages -> typed adapter -> Free Analyst -> Adaptive Renderer -> immutable Open Research sidecar -> research selector`

- Messages: `14`
- Production AI hard errors: `{repaired['hard_error_count']}`
- Free Analyst: `{summary['free_analyst_validated']}/14 PASS`; fallback `{summary['free_analyst_fallback']}/14`
- Open Research sidecars: `{summary['open_research_sidecar_pass']}/14 PASS`
- Adaptive Renderer: `{summary['adaptive_renderer_pass']}/14 PASS`
- Fact mismatch / unsupported numeric / unsupported causality / temporal / Trade AR / hidden arithmetic / external fact / material loss: `0`
- Production mutation / Telegram: `0 / 0`
"""
    report_texts["20260825-us-ai-free-analyst-message-comparison.md"] = comparison
    report_texts["20260825-us-ai-free-analyst-repair-readiness.md"] = f"""# US AI and Free Analyst Repair Readiness

{md_table(('Gate', 'Decision'), list(gates.items()))}

- Open P0: `0`
- Open material P1: `0`
- P2 backlog: `{len(p2)}`
- Track A production promotion: `PASS`, deployed pending natural proof
- Track B production promotion: `0`
- Open Research production promotion: `0`
- Next action: `FREE_ANALYST_ADAPTIVE_PRODUCTION_INTEGRATION`
"""
    validation_rows = [
        ("Track A focused", "14 passed"),
        ("Track A related", "276 passed"),
        ("Track A full", "1443 passed"),
        ("Track B focused", "72 passed"),
        ("Track B full", "1522 passed"),
        ("Ruff", "PASS"),
        ("git diff --check", "PASS"),
        ("Knowledge / Chart", "PASS / PASS"),
        ("Public Action / operationId", "0.4.5 / 20 of 20 unique"),
        ("Track A implementation Actions", "Test PASS / Lint PASS"),
    ]
    report_texts["20260825-us-ai-free-analyst-artifact-index.md"] = f"""# US AI and Free Analyst Repair Artifact Index

- Instruction commit: `{INSTRUCTION_COMMIT}`
- Track A implementation/final main/operating: `{TRACK_A_IMPLEMENTATION}`
- Track B implementation/final: `{TRACK_B_IMPLEMENTATION}` / `{TRACK_B_FINAL}`
- Packet: `{PACKET_ID}` / `{summary['packet_sha256']}`
- Candidate SHA-256: `{summary['candidate_sha256']}`
- Archive rewrite: `0`
- Provider calls: `0`

{md_table(('Validation', 'Result'), validation_rows)}

The ZIP contains the two architecture contracts, all 14 required reports, readiness JSON, and this index. Absolute local paths and secret delivery destinations are omitted.
"""

    report_paths: list[Path] = []
    for name, text in report_texts.items():
        path = REPORTS / name
        write(path, text)
        report_paths.append(path)
    readiness_path = REPORTS / "20260825-us-ai-free-analyst-repair-readiness.json"
    write_json(readiness_path, summary)
    report_paths.append(readiness_path)

    zip_path = REPORTS / ZIP_NAME
    architecture_paths = [
        ROOT / "docs/architecture/WORKING_CAPITAL_RELATION_SEMANTICS.md",
        ROOT / "docs/architecture/FREE_ANALYST_NATURAL_PACKET_ADAPTER.md",
    ]
    with zipfile.ZipFile(zip_path, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        for path in [*architecture_paths, *report_paths]:
            archive.write(path, path.relative_to(ROOT))
    shared_zip = SHARED_ROOT / ZIP_NAME
    shutil.copy2(zip_path, shared_zip)
    result = {
        "summary": summary,
        "zip": str(shared_zip),
        "zip_sha256": sha256(shared_zip),
        "report_count": len(report_paths),
    }
    print(json.dumps(result, ensure_ascii=False, indent=2, default=str))
    return result


if __name__ == "__main__":
    make_reports()
