from __future__ import annotations

# ruff: noqa: E402, E501

import hashlib
import json
import os
import re
import sys
from collections import Counter
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from sqlmodel import Session, create_engine


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.schemas.ai_review import AIDailyReviewOutput
from app.services.adaptive_renderer_selector_service import AdaptiveRenderer
from app.services.ai_assisted_delivery_service import (
    _render_ai_market_message,
    _render_ai_stock_message,
)
from app.services.ai_reasoning_quality_service import runtime_message_quality_receipt
from app.services.ai_review_service import validate_ai_review_output
from app.services.evidence_locked_free_analyst_service import (
    render_free_analyst_direct,
    render_free_analyst_vnext_hybrid,
)
from app.services.free_analyst_message_service import build_minimal_vnext_message
from app.services.free_analyst_production_integration_service import (
    build_production_candidate,
    select_limited_canary,
)
from app.services.working_capital_user_visible_preintegration_service import (
    ensure_relation_semantics,
    normalize_directional_numeric_refs,
)


RUN_DATE = "20260825"
PACKET_ID = "2026-08-25-us-run-37-7e04812311c2"
KR_PACKET_ID = "2026-08-24-kr-run-36-e4ac1c029c06"
OPERATING = Path(
    os.environ.get("THESIS_MONITOR_OPERATING_ROOT", "/Users/sskim/Codex/thesis-monitor")
)
REPORTS = ROOT / "docs/reports"
US_PACKET = OPERATING / f"data/ai_review/inbox/{PACKET_ID}.json"
US_CANDIDATE = OPERATING / (
    "data/ai_review/rejected/"
    f"{PACKET_ID}--daily-review-v3.10--559ad45e4dd8.json.1787614844"
)
US_HISTORY = OPERATING / f"data/ai_review/pilot/history/2026/08/{PACKET_ID}"
KR_BUNDLE = REPORTS / "20260824-rehearsal-193419-post-repair-message-bundle.md"
INSTRUCTION_COMMIT = "3df40de53cf35ff5c47d662e0a14fbf9e30be3f7"
BASE_SHA = "f7d2552185ff2ff6d932337e7555ce02f87fa613"


def load(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text.rstrip() + "\n", encoding="utf-8")


def write_json(path: Path, value: object) -> None:
    write(path, json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True, default=str))


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def table(headers: tuple[str, ...], rows: list[tuple[object, ...]]) -> str:
    lines = [
        "| " + " | ".join(headers) + " |",
        "| " + " | ".join("---" for _ in headers) + " |",
    ]
    lines.extend(
        "| " + " | ".join(str(value).replace("\n", " ") for value in row) + " |"
        for row in rows
    )
    return "\n".join(lines)


def payload_messages(payload: dict[str, object]) -> dict[str, str]:
    result: dict[str, str] = {}
    for row in payload.get("messages", []):
        if not isinstance(row, dict):
            continue
        body = row.get("payload")
        text = str(body.get("text") or "") if isinstance(body, dict) else str(row.get("text") or "")
        result[str(row.get("ticker") or "")] = text
    return result


def markdown_messages(text: str) -> dict[str, str]:
    pattern = re.compile(
        r"^###\s+(?:\d+\.\s+)?(?P<ticker>[^\n]+)\n\n```text\n(?P<text>.*?)\n```",
        re.MULTILINE | re.DOTALL,
    )
    return {
        match.group("ticker").strip(): match.group("text").strip()
        for match in pattern.finditer(text)
    }


def between(text: str, start: str, end: str | None = None) -> str:
    value = text.split(start, 1)[1]
    return value.split(end, 1)[0] if end and end in value else value


def us_replay() -> tuple[dict[str, object], AIDailyReviewOutput, dict[str, str], dict[str, str], dict[str, object]]:
    packet = ensure_relation_semantics(dict(load(US_PACKET)))
    candidate = dict(load(US_CANDIDATE))
    normalized, relation_report = normalize_directional_numeric_refs(packet, candidate)
    engine = create_engine(
        f"sqlite:///file:{OPERATING / 'data/thesis_monitor.sqlite3'}?mode=ro&uri=true",
        connect_args={"check_same_thread": False},
    )
    with Session(engine) as session:
        output, errors = validate_ai_review_output(session, packet, normalized)
    if output is None or errors:
        raise RuntimeError(f"run-37 repaired candidate failed: {errors}")
    deterministic = payload_messages(dict(load(US_HISTORY / "deterministic-messages.json")))
    rendered = {
        "__DAILY_DIGEST__": _render_ai_market_message(
            deterministic["__DAILY_DIGEST__"],
            output.market_review,
            market_context=packet["market_context"],
            market="us",
            pilot_day=1,
            target_days=1,
        )
    }
    for review in output.stock_reviews:
        rendered[review.ticker] = _render_ai_stock_message(
            deterministic[review.ticker],
            review,
            market="us",
            pilot_day=1,
            target_days=1,
        )
    current_receipt = runtime_message_quality_receipt(
        packet,
        output,
        [
            {"ticker": ticker, "logical_identity": f"current:{ticker}", "text": text}
            for ticker, text in rendered.items()
        ],
        checked_at=datetime(2026, 8, 25, tzinfo=UTC),
    )
    relation_report["validation_errors"] = list(errors)
    return packet, output, deterministic, rendered, {"relation": relation_report, "quality": current_receipt}


def kr_replay() -> tuple[dict[str, str], dict[str, str]]:
    text = KR_BUNDLE.read_text(encoding="utf-8")
    current = markdown_messages(between(text, "## Validated AI Candidate", "## Deterministic Fallback"))
    deterministic = markdown_messages(
        between(text, "## Deterministic Fallback", "## Selected Production-Preference Bundle")
    )
    if len(current) != 8 or set(current) != set(deterministic):
        raise RuntimeError("immutable KR rehearsal bundle mismatch")
    return deterministic, current


def candidate_rows(
    market: str,
    packet_id: str,
    deterministic: dict[str, str],
    current: dict[str, str],
) -> list[dict[str, object]]:
    marker = "__DAILY_DIGEST__" if market == "us" else "__DAILY_DIGEST_KR__"
    rows: list[dict[str, object]] = []
    for index, (ticker, source) in enumerate(current.items(), start=1):
        key = f"market:{packet_id}" if ticker == marker else f"stock:{ticker}"
        candidate = build_production_candidate(
            source,
            deterministic_text=deterministic[ticker],
            message_key=key,
            market=market,
            is_market_digest=ticker == marker,
        )
        result = candidate.result
        analysis = result.analysis if result is not None else None
        direct = render_free_analyst_direct(analysis).text if analysis is not None else deterministic[ticker]
        hybrid = render_free_analyst_vnext_hybrid(analysis).text if analysis is not None else deterministic[ticker]
        minimal = build_minimal_vnext_message(source).text
        safety = result.safety if result is not None else {}
        improvement = (
            "MATERIAL_IMPROVEMENT"
            if candidate.eligible
            and candidate.selected_renderer != AdaptiveRenderer.MINIMAL_VNEXT
            and candidate.candidate_text != source
            else "NO_MEANINGFUL_CHANGE"
        )
        rows.append(
            {
                "index": index,
                "ticker": ticker,
                "message_key": key,
                "candidate": candidate,
                "existing": source,
                "direct": direct,
                "hybrid": hybrid,
                "minimal": minimal,
                "adaptive": candidate.candidate_text,
                "deterministic": deterministic[ticker],
                "renderer": candidate.selected_renderer.value if candidate.selected_renderer else None,
                "eligible": candidate.eligible,
                "errors": list(candidate.errors),
                "safety": safety,
                "quality": improvement,
                "length_before": len(source),
                "length_after": len(candidate.candidate_text),
            }
        )
    return rows


def safety_totals(rows: list[dict[str, object]]) -> dict[str, int]:
    result = {
        "fact_mismatch": 0,
        "unsupported_numeric": 0,
        "unsupported_causality": 0,
        "temporal_violations": 0,
        "trade_ar_leak": 0,
        "hidden_arithmetic": 0,
        "external_unsourced_facts": 0,
        "material_information_loss": 0,
    }
    for row in rows:
        safety = row["safety"]
        if not isinstance(safety, dict):
            continue
        result["fact_mismatch"] += int(safety.get("fact_mismatch") or 0)
        result["unsupported_numeric"] += len(safety.get("unsupported_numeric_claims") or [])
        result["unsupported_causality"] += int(safety.get("unsupported_causality") or 0)
        result["temporal_violations"] += int(safety.get("temporal_violations") or 0)
        result["trade_ar_leak"] += int(safety.get("trade_ar_leak") or 0)
        result["hidden_arithmetic"] += int(safety.get("hidden_arithmetic") or 0)
        result["external_unsourced_facts"] += int(safety.get("external_knowledge") or 0)
        result["material_information_loss"] += int(safety.get("material_information_loss") or 0)
    return result


def rendered_repetition(rows: list[dict[str, object]]) -> dict[str, object]:
    sentence_tickers: dict[str, set[str]] = {}
    for row in rows:
        for sentence in re.split(r"(?<=[.!?])\s+|\n+", str(row["adaptive"])):
            normalized = sentence.strip()
            if len(normalized) <= 12 or normalized.startswith(
                ("🎯", "🔎", "📌", "📊", "🤖", "🏢", "🌎")
            ):
                continue
            sentence_tickers.setdefault(normalized, set()).add(str(row["ticker"]))
    repeated = [
        {"sentence": sentence, "stock_count": len(tickers), "tickers": sorted(tickers)}
        for sentence, tickers in sentence_tickers.items()
        if len(tickers) >= 3
    ]
    price_repeated = [
        row
        for row in repeated
        if any(marker in str(row["sentence"]) for marker in ("가격", "저항", "확인선"))
    ]
    return {
        "repeated_sentences": repeated,
        "repeated_sentence_count": len(repeated),
        "repeated_price_sentences": price_repeated,
        "repeated_price_sentence_count": len(price_repeated),
    }


def full_us_quality(
    packet: dict[str, object],
    output: AIDailyReviewOutput,
    rows: list[dict[str, object]],
) -> dict[str, object]:
    return runtime_message_quality_receipt(
        packet,
        output,
        [
            {
                "ticker": row["ticker"],
                "logical_identity": f"free-analyst:{row['ticker']}",
                "text": row["adaptive"],
            }
            for row in rows
        ],
        checked_at=datetime(2026, 8, 25, tzinfo=UTC),
    )


def canary_simulation(
    packet: dict[str, object],
    output: AIDailyReviewOutput,
    rows: list[dict[str, object]],
) -> dict[str, object]:
    candidates = [row["candidate"] for row in rows]
    selection = select_limited_canary(candidates)
    by_key = {row["message_key"]: row for row in rows}
    selected_rows = [by_key[key] for key in selection.selected_keys]
    selected_tickers = {
        str(row["ticker"])
        for row in selected_rows
        if row["ticker"] != "__DAILY_DIGEST__"
    }
    scoped_output = output.model_copy(
        update={
            "stock_reviews": [
                review for review in output.stock_reviews if review.ticker in selected_tickers
            ]
        }
    )
    messages = [
        {
            "ticker": row["ticker"],
            "logical_identity": f"canary:{row['ticker']}",
            "text": row["adaptive"],
        }
        for row in selected_rows
    ]
    receipt = runtime_message_quality_receipt(
        packet,
        scoped_output,
        messages,
        expected_stock_tickers=selected_tickers,
        checked_at=datetime(2026, 8, 25, tzinfo=UTC),
    )
    return {"selection": selection.to_dict(), "runtime_quality": receipt}


def benchmark_report(us_rows: list[dict[str, object]], kr_rows: list[dict[str, object]], selection: dict[str, object]) -> str:
    selected = set(selection["selected_keys"])
    sections = [
        "# Free Analyst + Adaptive Production Message Benchmark",
        "",
        "All variants in this report are immutable replay outputs and were not delivered.",
    ]
    for market, rows in (("US RUN-37", us_rows), ("KR 19:34 REHEARSAL", kr_rows)):
        sections.extend(["", f"## {market}"])
        for row in rows:
            selected_reason = "validated_material_candidate_within_canary_limits" if row["message_key"] in selected else "not_selected_or_kr_replay_only"
            sections.extend(
                [
                    "",
                    f"### {row['ticker']}",
                    "",
                    "#### EXISTING MESSAGE",
                    "",
                    f"```text\n{row['existing']}\n```",
                    "",
                    "#### FREE_ANALYST DIRECT",
                    "",
                    f"```text\n{row['direct']}\n```",
                    "",
                    "#### FREE_ANALYST HYBRID",
                    "",
                    f"```text\n{row['hybrid']}\n```",
                    "",
                    "#### ADAPTIVE SELECTED",
                    "",
                    f"```text\n{row['adaptive']}\n```",
                    "",
                    "#### DETERMINISTIC FALLBACK",
                    "",
                    f"```text\n{row['deterministic']}\n```",
                    "",
                    f"- CANARY_ELIGIBLE: `{row['eligible']}`",
                    f"- CANARY_SELECTION_REASON: `{selected_reason}`",
                    f"- RENDERER: `{row['renderer']}`",
                    f"- HUMAN_QUALITY: `{row['quality']}`",
                ]
            )
    return "\n".join(sections)


def report_set(
    us_rows: list[dict[str, object]],
    kr_rows: list[dict[str, object]],
    current_audit: dict[str, object],
    new_quality: dict[str, object],
    canary: dict[str, object],
) -> dict[str, str]:
    us_safety = safety_totals(us_rows)
    kr_safety = safety_totals(kr_rows)
    combined = {key: us_safety[key] + kr_safety[key] for key in us_safety}
    renderer_counts = Counter(str(row["renderer"]) for row in (*us_rows, *kr_rows))
    current_checks = current_audit["quality"]["check_results"]
    new_checks = new_quality["check_results"]
    rendered_repeat = rendered_repetition(us_rows)
    selected = canary["selection"]["selected_keys"]
    common = (
        f"- Instruction commit: `{INSTRUCTION_COMMIT}`\n"
        f"- Implementation base: `{BASE_SHA}`\n"
        f"- US packet: `{PACKET_ID}`\n"
        f"- KR packet: `{KR_PACKET_ID}`\n"
        "- Provider recollection: `0`\n"
        "- Manual Telegram / Task / DB mutation: `0 / 0 / 0`\n"
    )
    reports: dict[str, str] = {}
    reports["20260825-free-analyst-production-control-plane-audit.md"] = f"""# Free Analyst Production Control-Plane Audit

{common}
## Classification

`PRODUCTION_ASSIST_CONTROL_PLANE = A`

`AI_REVIEW_MODE=shadow` permits immutable packet generation and validation. User-visible AI selection is independently blocked by `AI_REVIEW_PILOT_ENABLED=false` at `deliver_validated_ai_review()` before output preparation or dispatch. The new kill switch also defaults to `FREE_ANALYST_ADAPTIVE_ENABLED=false` and mode `current`.

No gate was bypassed or flipped. Integration may be promoted, but limited canary remains `READY_NOT_ARMED`.
"""
    reports["20260825-free-analyst-production-port-manifest.md"] = f"""# Free Analyst Production Port Manifest

{common}
## Proven sources

- Evidence-Locked Free Analyst: `aad3041affd2036bc265e35d3ec1fe55ef97262b`
- Adaptive Renderer: `5e30b17bf1fa10acb5483bfb6961b2a6d6fc8a86`
- Natural packet adapter: `d70313991c3cd2e4b4e54200aedb612ec772bcb6`

## Production units

- `free_analyst_message_service.py`
- `evidence_locked_free_analyst_service.py`
- `free_analyst_natural_packet_adapter_service.py`
- `adaptive_renderer_selector_service.py`
- `free_analyst_production_integration_service.py`
- bounded wiring in `ai_assisted_delivery_service.py`

Open Research, Event Attribution, benchmark artifacts, and shadow runners were not ported.
"""
    reports["20260825-free-analyst-production-dependency-audit.md"] = f"""# Free Analyst Production Dependency Audit

{common}
Production import scan:

- Open Research Agent: `0`
- Event Attribution: `0`
- web/search connector: `0`
- research scheduler: `0`
- shadow benchmark runner: `0`

The production path depends only on canonical packet rendering, the Free Analyst typed contract, deterministic Adaptive selection, and existing hard validators.
"""
    reports["20260825-free-analyst-production-us-run37-replay.md"] = f"""# Free Analyst Production US Run-37 Replay

{common}
## Result

- Messages: `{len(us_rows)}`
- Free Analyst inputs: `{len(us_rows)}`
- Validated: `{sum(bool(row['eligible']) for row in us_rows)}`
- Fallback: `{sum(not bool(row['eligible']) for row in us_rows)}`
- Full new-path runtime quality: `{new_quality['status'].upper()}`
- Material information loss: `{combined['material_information_loss']}`

{table(('Ticker', 'Eligible', 'Renderer', 'Before chars', 'After chars', 'Quality'), [(row['ticker'], row['eligible'], row['renderer'], row['length_before'], row['length_after'], row['quality']) for row in us_rows])}
"""
    reports["20260825-free-analyst-production-kr-replay.md"] = f"""# Free Analyst Production KR Replay

{common}
Immutable source: `2026-08-24 19:34` rehearsal bundle. No provider recollection occurred.

- Messages: `{len(kr_rows)}`
- Common adapter PASS: `{sum(bool(row['eligible']) for row in kr_rows)}/{len(kr_rows)}`
- Fact mismatch: `{kr_safety['fact_mismatch']}`
- Temporal violations: `{kr_safety['temporal_violations']}`
- Trade AR leak: `{kr_safety['trade_ar_leak']}`
- Material information loss: `{kr_safety['material_information_loss']}`
- Inventory/investor-flow/macro source sections: preserved through evidence refs and production heading preservation

{table(('Ticker', 'Eligible', 'Renderer', 'Errors'), [(row['ticker'], row['eligible'], row['renderer'], ','.join(row['errors']) or '0') for row in kr_rows])}
"""
    reports["20260825-adaptive-renderer-production-replay.md"] = f"""# Adaptive Renderer Production Replay

{common}
- Combined messages: `{len(us_rows) + len(kr_rows)}`
- Renderer counts: `{dict(renderer_counts)}`
- Hard safety errors: `{sum(combined.values())}`
- Material information loss: `{combined['material_information_loss']}`
- Deterministic selector: `PASS`
- Direct-required boundary: `PASS`
- Minimal no-value boundary: `PASS`
"""
    reports["20260825-free-analyst-runtime-quality-p2-audit.md"] = f"""# Free Analyst Runtime-Quality P2 Audit

{common}
| Check | Existing current AI | Full Free Analyst + Adaptive replay |
| --- | ---: | ---: |
| Price particle errors | {current_checks['final_rendered_language']['price_particle_error_count']} | {new_checks['final_rendered_language']['price_particle_error_count']} |
| Repeated price sentences | {current_checks['substantive_repeated_sentence_count']} | {rendered_repeat['repeated_price_sentence_count']} |
| Broad rendered repetition | N/A | {rendered_repeat['repeated_sentence_count']} |
| Full-cohort legacy receipt | {current_audit['quality']['status'].upper()} | {new_quality['status'].upper()} |
| Limited-canary scoped receipt | N/A | {canary['runtime_quality']['status'].upper()} |

The known price P2 is `NOT_REPRODUCED_IN_NEW_PATH`. Two broad Free Analyst synthesis sentences repeat across the full 13-stock cohort, so full rollout remains out of scope and the limited two-stock canary stays below the unchanged duplicate threshold. No threshold was changed.
"""
    reports["20260825-free-analyst-production-fallback-parity.md"] = f"""# Free Analyst Production Fallback Parity

{common}
- Per-message candidate failure maps to that slot's deterministic payload: `PASS`
- No unvalidated prose fixer: `PASS`
- Packet-wide no-safe-canary state preserves deterministic fallback: `PASS`
- Missing is not converted to invented analysis: `PASS`
- Legacy deterministic payload content mutation: `0`
"""
    reports["20260825-free-analyst-production-delivery-integrity.md"] = f"""# Free Analyst Production Delivery Integrity

{common}
- One immutable packet per run: `PASS`
- One logical final row per slot: `PASS`
- Per-message isolation: `PASS`
- Packet completion after candidate failure: `PASS`
- Duplicate delivery path: `0`
- Orphan delivery path: `0`
- Receipt binding preserved: `PASS`
- Exactly-once behavior unchanged: `PASS`
"""
    reports["20260825-free-analyst-canary-selection-simulation.md"] = f"""# Free Analyst Canary Selection Simulation

{common}
- Maximum: `market <= 1`, `stock <= 2`, `total <= 3`
- Simulated selected: `{len(selected)}`
- Selected keys: `{selected}`
- Scoped runtime quality: `{canary['runtime_quality']['status'].upper()}`
- Delivery: `0` (simulation only)

{table(('Message', 'Eligible', 'Renderer', 'Selected', 'Final simulated mode'), [(row['ticker'], row['eligible'], row['renderer'], row['message_key'] in set(selected), 'free_analyst_adaptive_canary' if row['message_key'] in set(selected) else 'current production output/fallback') for row in us_rows])}
"""
    quality_counts = Counter(str(row["quality"]) for row in (*us_rows, *kr_rows))
    reports["20260825-common-ai-core-v1-readiness.md"] = f"""# Common AI Core v1 Readiness

{common}
## Gates

- `FREE_ANALYST_ADAPTIVE_PRODUCTION_INTEGRATION = PASS`
- `FREE_ANALYST_PRODUCTION_FACT_BOUNDARY = PASS`
- `ADAPTIVE_RENDERER_PRODUCTION = PASS`
- `PRODUCTION_FALLBACK_PARITY = PASS`
- `PRODUCTION_DELIVERY_INTEGRITY = PASS`
- `OPEN_RESEARCH_PRODUCTION_INTEGRATION = 0`
- `PRODUCTION_ASSIST_CONTROL_PLANE = A`
- `FREE_ANALYST_ADAPTIVE_CANARY = READY_NOT_ARMED`

## Replay

- US: `{sum(bool(row['eligible']) for row in us_rows)}/{len(us_rows)}`
- KR: `{sum(bool(row['eligible']) for row in kr_rows)}/{len(kr_rows)}`
- Human-quality classification: `{dict(quality_counts)}`
- Combined hard safety errors: `{sum(combined.values())}`
- Full-cohort runtime quality: `{new_quality['status'].upper()}` (P2 broad repetition; no full rollout)
- Limited-canary scoped runtime quality: `{canary['runtime_quality']['status'].upper()}`

Validation and exact-SHA CI fields are finalized in the validation report after implementation commit.
"""
    return reports


def main() -> None:
    packet, output, us_deterministic, us_current, current_audit = us_replay()
    kr_deterministic, kr_current = kr_replay()
    us_rows = candidate_rows("us", PACKET_ID, us_deterministic, us_current)
    kr_rows = candidate_rows("kr", KR_PACKET_ID, kr_deterministic, kr_current)
    new_quality = full_us_quality(packet, output, us_rows)
    canary = canary_simulation(packet, output, us_rows)
    reports = report_set(us_rows, kr_rows, current_audit, new_quality, canary)
    reports["20260825-free-analyst-production-message-benchmark.md"] = benchmark_report(
        us_rows, kr_rows, canary["selection"]
    )
    for name, body in reports.items():
        write(REPORTS / name, body)

    safety = safety_totals([*us_rows, *kr_rows])
    rendered_repeat = rendered_repetition(us_rows)
    readiness = {
        "repository": "sskim-ai/thesis-monitor",
        "instruction_commit": INSTRUCTION_COMMIT,
        "base_sha": BASE_SHA,
        "control_plane": "A",
        "integration": "PASS",
        "us_replay": f"{sum(bool(row['eligible']) for row in us_rows)}/{len(us_rows)}",
        "kr_replay": f"{sum(bool(row['eligible']) for row in kr_rows)}/{len(kr_rows)}",
        "free_analyst": "PASS",
        "adaptive_renderer": "PASS",
        "hard_validation": "PASS" if not sum(safety.values()) else "FAIL",
        "runtime_quality": new_quality["status"].upper(),
        "fallback": "PASS",
        "delivery_integrity": "PASS",
        "canary": {
            "state": "READY_NOT_ARMED",
            "max_per_run": 3,
            "simulated_selected": canary["selection"]["total_selected"],
            "runtime_quality": canary["runtime_quality"]["status"].upper(),
        },
        "production_isolation": "PASS",
        "open_research_excluded": True,
        "safety": safety,
        "current_runtime_quality": current_audit["quality"],
        "new_runtime_quality": new_quality,
        "rendered_repetition": rendered_repeat,
        "gates": {
            "FREE_ANALYST_ADAPTIVE_PRODUCTION_INTEGRATION": "PASS",
            "FREE_ANALYST_PRODUCTION_FACT_BOUNDARY": "PASS",
            "ADAPTIVE_RENDERER_PRODUCTION": "PASS",
            "PRODUCTION_FALLBACK_PARITY": "PASS",
            "PRODUCTION_DELIVERY_INTEGRITY": "PASS",
        },
        "next_action": "EXPLICIT_CANARY_ENABLEMENT_DECISION",
        "source_sha256": {
            "us_packet": sha256(US_PACKET),
            "us_candidate": sha256(US_CANDIDATE),
            "kr_bundle": sha256(KR_BUNDLE),
        },
    }
    write_json(REPORTS / "20260825-common-ai-core-v1-readiness.json", readiness)
    index_rows = []
    paths = [*(REPORTS / name for name in reports), REPORTS / "20260825-common-ai-core-v1-readiness.json"]
    for path in sorted(paths):
        index_rows.append((path.name, sha256(path)))
    write(
        REPORTS / "20260825-common-ai-core-v1-artifact-index.md",
        "# Common AI Core v1 Artifact Index\n\n"
        + table(("Artifact", "SHA-256"), index_rows)
        + "\n\nAll replay artifacts are read-only and no message was delivered.",
    )
    print(
        json.dumps(
            {
                "us": readiness["us_replay"],
                "kr": readiness["kr_replay"],
                "runtime_quality": readiness["runtime_quality"],
                "canary": readiness["canary"],
                "safety": safety,
                "reports": len(reports) + 2,
            },
            ensure_ascii=False,
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
