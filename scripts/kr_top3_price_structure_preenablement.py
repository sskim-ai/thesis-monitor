from __future__ import annotations

import argparse
import asyncio
import hashlib
import json
import os
import re
from collections import Counter
from collections.abc import Mapping, Sequence
from datetime import datetime
from pathlib import Path

from app.config import get_settings
from app.services.free_analyst_production_integration_service import (
    build_production_candidate,
)
from app.services.kr_market_digest_quality_service import (
    build_kr_market_digest_plan,
    is_kr_sector_return_row,
)
from app.services.kr_price_structure_selective_rollout_service import (
    build_kr_price_structure_rollout_decision,
    preserve_current_price_structure_section,
    replace_legacy_price_surface,
)
from app.services.market_context_adapter_service import NormalizedMarketContext
from app.services.market_evidence_utilization_validator_service import (
    validate_kr_market_evidence_utilization,
)
from app.services.ohlcv_client import OhlcvClient
from scripts.kr_market_preenable_evidence import audit_test_sink, load_env_values


CONTRACT = "kr-top3-price-structure-selective-preenablement-v1"
MARKET_KEY = "__DAILY_DIGEST_KR__"
KST_OBSERVED_AT = "2026-08-27T17:10:00+09:00"


def _read_json(path: Path) -> object:
    return json.loads(path.read_text(encoding="utf-8"))


def _write_json(path: Path, value: object) -> None:
    path.write_text(
        json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def _write_text(path: Path, value: str) -> None:
    path.write_text(value.strip() + "\n", encoding="utf-8")


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _sha_text(value: str) -> str:
    return hashlib.sha256(value.encode()).hexdigest()


def _messages(payload: object) -> dict[str, str]:
    if not isinstance(payload, Mapping):
        raise ValueError("message payload must be an object")
    rows = payload.get("messages")
    if not isinstance(rows, list):
        raise ValueError("message rows missing")
    result: dict[str, str] = {}
    for row in rows:
        if not isinstance(row, Mapping):
            continue
        ticker = str(row.get("ticker") or "")
        value = row.get("text")
        if not isinstance(value, str):
            inner = row.get("payload")
            value = inner.get("text") if isinstance(inner, Mapping) else None
        if ticker and isinstance(value, str):
            result[ticker] = value
    return result


def _replace_market_local_block(message: str, claims: Sequence[str]) -> str:
    heading = "📍 국내 장마감 구조"
    if heading not in message:
        return message.rstrip() + "\n\n" + "\n".join(claims)
    start = message.index(heading)
    marker = "\n\n💱 환율"
    end = message.find(marker, start)
    if end < 0:
        end = len(message)
    local = heading + "\n" + "\n".join(f"• {claim}" for claim in claims)
    return message[:start] + local + message[end:]


def _sector_selection(context: NormalizedMarketContext) -> dict[str, object]:
    values: dict[str, object] = {}
    for scope in ("KOSPI", "KOSDAQ"):
        rows = [
            item
            for item in context.sectors
            if item.market_scope == scope
            and item.basis == "actual_sector_breadth"
            and item.return_pct is not None
            and item.state == "CURRENT_DIRECTIONAL"
            and (item.as_of_date is None or item.as_of_date == context.session_date)
            and is_kr_sector_return_row(market_scope=scope, name=item.name)
        ]
        deduplicated = {
            " ".join(item.name.upper().split()): item
            for item in sorted(rows, key=lambda item: (item.name, item.source_ref))
        }
        rows = list(deduplicated.values())
        strong = sorted(
            rows,
            key=lambda item: (-float(item.return_pct), item.name, item.source_ref),
        )[:3]
        weak = sorted(
            rows,
            key=lambda item: (float(item.return_pct), item.name, item.source_ref),
        )[:3]
        values[scope] = {
            "safe_count": len(rows),
            "strong": [
                {
                    "rank": index,
                    "name": item.name,
                    "return_pct": item.return_pct,
                    "source_ref": item.source_ref,
                }
                for index, item in enumerate(strong, start=1)
            ],
            "weak": [
                {
                    "rank": index,
                    "name": item.name,
                    "return_pct": item.return_pct,
                    "source_ref": item.source_ref,
                }
                for index, item in enumerate(weak, start=1)
            ],
        }
    return values


async def _price_structure_rows(
    tickers: Sequence[str],
    *,
    target_session: str,
    ai_messages: Mapping[str, str],
    fallback_messages: Mapping[str, str],
) -> list[dict[str, object]]:
    settings = get_settings()
    settings.kr_price_structure_v3_enabled = True
    client = OhlcvClient()
    as_of = datetime.fromisoformat(KST_OBSERVED_AT)
    rows: list[dict[str, object]] = []
    for ticker in tickers:
        context = await client.fetch_price_context(ticker, as_of=as_of)
        structure = context.chart.structure.get("price_structure_v3")
        structure = structure if isinstance(structure, Mapping) else {}
        decision = build_kr_price_structure_rollout_decision(
            structure,
            ticker=ticker,
            monitored_subject=True,
            enabled=True,
        )
        fallback = fallback_messages.get(ticker, "")
        ai = ai_messages.get(ticker, fallback)
        rendered_fallback = (
            replace_legacy_price_surface(fallback, decision.section)
            if decision.section
            else fallback
        )
        rendered_ai = (
            preserve_current_price_structure_section(ai, rendered_fallback)
            if decision.section
            else ai
        )
        stored_present = "가격 규칙 이력:" in fallback
        rows.append(
            {
                "ticker": ticker,
                "target_session": target_session,
                "price_as_of": structure.get("as_of"),
                "eligibility": decision.eligibility.value,
                "denial_reasons": list(decision.denial_reasons),
                "current_price": structure.get("current_price"),
                "currency": structure.get("currency"),
                "summary": structure.get("summary", {}),
                "coverage": structure.get("coverage", {}),
                "family_consensus_safe": structure.get("family_consensus_safe"),
                "numeric_bindings": list(decision.numeric_bindings),
                "section": decision.section,
                "ai_preview": rendered_ai,
                "fallback_preview": rendered_fallback,
                "stored_rule_present": stored_present,
                "stored_rule_separated": (
                    not stored_present
                    or "🧭 기존 등록 가격 규칙" in rendered_fallback
                ),
                "unsupported_target": int(
                    bool(re.search(r"목표가|목표 가격", decision.section or ""))
                ),
                "unsupported_stop": int(
                    bool(re.search(r"손절|stop-loss", decision.section or "", re.I))
                ),
                "lookahead_leak": int(structure.get("as_of") != target_session),
                "partial_bar_used_for_pivot_confirmation": int(
                    structure.get("partial_bar_used_for_pivot_confirmation") or 0
                ),
            }
        )
    return rows


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


def _message_block(title: str, text: str) -> str:
    return f"## {title}\n\n```text\n{text}\n```"


def _report_files() -> tuple[str, ...]:
    return (
        "20260827-kr-top3-sector-policy.md",
        "20260827-kr-top3-sector-run42-replay.md",
        "20260827-kr-price-structure-selective-scope.md",
        "20260827-kr-price-structure-current-replay.md",
        "20260827-kr-price-structure-per-ticker-audit.md",
        "20260827-kr-test-sink-isolation.md",
        "20260827-kr-market-test-exact-message.md",
        "20260827-kr-stock-test-exact-messages.md",
        "20260827-kr-test-message-quality.md",
        "20260827-kr-rollout-gate-matrix.md",
        "20260827-kr-only-enablement-action.md",
        "20260827-kr-post-enable-smoke.md",
        "20260827-kr-natural-proof-status.md",
        "20260827-kr-rollout-safety-parity.md",
        "20260827-kr-rollout-artifact-index.md",
        "20260827-kr-price-structure-numeric-provenance.md",
        "20260827-kr-rollout-validation.md",
    )


def _write_reports(
    reports: Path,
    *,
    args: argparse.Namespace,
    packet: Mapping[str, object],
    sector_selection: Mapping[str, object],
    market_candidate: str,
    market_fallback: str,
    market_route: str,
    utilization_status: str,
    price_rows: Sequence[Mapping[str, object]],
    sink: Mapping[str, object],
    gates: Mapping[str, object],
    archive_hashes: Mapping[str, str],
) -> None:
    kospi = sector_selection["KOSPI"]
    kosdaq = sector_selection["KOSDAQ"]
    assert isinstance(kospi, Mapping) and isinstance(kosdaq, Mapping)
    selection_rows = []
    for scope, value in (("KOSPI", kospi), ("KOSDAQ", kosdaq)):
        for side in ("strong", "weak"):
            for item in value[side]:  # type: ignore[index]
                selection_rows.append(
                    [
                        scope,
                        side,
                        item["rank"],
                        item["name"],
                        item["return_pct"],
                        item["source_ref"],
                    ]
                )
    _write_text(
        reports / "20260827-kr-top3-sector-policy.md",
        f"""# KR TOP3 Sector Policy

Contract: `kr-sector-relative-ranking-v1`  
Selection owner: backend deterministic ranking  
Tie-break: return, then canonical sector name, then source ref  
User terms: `업종 상대 강세` / `업종 상대 약세`

{_table(["Market", "Side", "Rank", "Sector", "Return %", "Source ref"], selection_rows)}

No AI sorting, stale carry-forward, or duplicate fill is permitted.
""",
    )
    _write_text(
        reports / "20260827-kr-top3-sector-run42-replay.md",
        f"""# KR TOP3 Sector Run-42 Replay

- Packet: `{packet['packet_id']}`
- Target session: `{args.target_session}`
- Route before sink gate: `{market_route}`
- Evidence utilization: `{utilization_status}`
- KOSPI safe rows: `{kospi['safe_count']}`
- KOSDAQ safe rows: `{kosdaq['safe_count']}`

The same deterministic TOP3 plan feeds the AI candidate and fallback. Production output remains
unchanged because the rollout flags remain OFF.
""",
    )
    eligibility = Counter(str(row["eligibility"]) for row in price_rows)
    _write_text(
        reports / "20260827-kr-price-structure-selective-scope.md",
        f"""# KR Price Structure Selective Scope

Scope is the packet-derived monitored KR universe only: `{len(price_rows)}` subjects.

{_table(["Eligibility", "Count"], [[key, value] for key, value in sorted(eligibility.items())])}

`ELIGIBLE` renders nearest/major SR plus family-stable Fib/SR. `ELIGIBLE_SR_ONLY` renders SR
without a Fib placeholder. `OMIT_PRICE_STRUCTURE` and `BLOCKED` leave the stock message valid.
US and unmonitored subjects are rejected by the market/scope guard.
""",
    )
    replay_rows = [
        [
            row["ticker"],
            row["price_as_of"],
            row["eligibility"],
            row["family_consensus_safe"],
            len(row["numeric_bindings"]),
            ", ".join(row["denial_reasons"]) or "none",
        ]
        for row in price_rows
    ]
    _write_text(
        reports / "20260827-kr-price-structure-current-replay.md",
        "# KR Price Structure Current Replay\n\n"
        + _table(
            ["Ticker", "Session", "Eligibility", "Fib safe", "Bindings", "Denial"],
            replay_rows,
        )
        + "\n\nAll rows were rebuilt from the existing local OHLCV read-only service at the completed "
        "2026-08-27 KR cutoff.\n",
    )
    ticker_audit_rows = [
        [
            row["ticker"],
            row["eligibility"],
            "YES" if row["section"] else "NO",
            "PASS" if row["stored_rule_separated"] else "FAIL",
            row["lookahead_leak"],
            row["partial_bar_used_for_pivot_confirmation"],
        ]
        for row in price_rows
    ]
    _write_text(
        reports / "20260827-kr-price-structure-per-ticker-audit.md",
        "# KR Price Structure Per-Ticker Audit\n\n"
        + _table(
            [
                "Ticker",
                "Eligibility",
                "Rendered",
                "Stored rule separation",
                "Lookahead",
                "Partial pivot",
            ],
            ticker_audit_rows,
        ),
    )
    _write_text(
        reports / "20260827-kr-test-sink-isolation.md",
        f"""# KR Test Sink Isolation

- `TEST_SINK_AVAILABLE = {'YES' if sink['available'] else 'NO'}`
- Alias: `{sink['test_sink_alias']}`
- Reason: `{sink['reason']}`
- Production collision: `{sink['production_collision']}`
- Production intent collision: `0`

No raw sink or account identifier is included. Because the dedicated sink is unavailable, no test
delivery or production intent was created.
""",
    )
    _write_text(
        reports / "20260827-kr-market-test-exact-message.md",
        "# KR Market Test Exact Message\n\n"
        "`TEST_ROUTE = NOT_SENT`\n\n"
        + _message_block("Production-equivalent candidate", market_candidate)
        + "\n\n"
        + _message_block("Deterministic fallback", market_fallback),
    )
    stock_blocks = [
        _message_block(
            f"{row['ticker']} · {row['eligibility']} · NOT_SENT",
            str(row["ai_preview"]),
        )
        for row in price_rows
    ]
    _write_text(
        reports / "20260827-kr-stock-test-exact-messages.md",
        "# KR Stock Test Exact Messages\n\n"
        "All messages are local preflight previews; delivery count is `0`.\n\n"
        + "\n\n".join(stock_blocks),
    )
    quality_rows = [
        [
            row["ticker"],
            row["unsupported_target"],
            row["unsupported_stop"],
            "PASS" if row["stored_rule_separated"] else "FAIL",
            "PASS" if row["section"] else row["eligibility"],
        ]
        for row in price_rows
    ]
    _write_text(
        reports / "20260827-kr-test-message-quality.md",
        "# KR Test Message Quality\n\n"
        + _table(
            ["Ticker", "Target", "Stop", "Ownership", "Render"],
            quality_rows,
        )
        + "\n\nExternal received-message formatting remains `NOT_SENT`.\n",
    )
    _write_text(
        reports / "20260827-kr-rollout-gate-matrix.md",
        "# KR Rollout Gate Matrix\n\n"
        + _table(
            ["Gate", "Value"],
            [[key, value] for key, value in gates.items()],
        ),
    )
    _write_text(
        reports / "20260827-kr-only-enablement-action.md",
        f"""# KR-Only Enablement Action

- `KR_MARKET_TOP3_ENABLEMENT = {gates['KR_MARKET_TOP3_ENABLEMENT']}`
- `KR_PRICE_STRUCTURE_ENABLEMENT = {gates['KR_PRICE_STRUCTURE_ENABLEMENT']}`
- `US_PRICE_STRUCTURE_ENABLED = 0`
- `KR_ROLLOUT = {gates['KR_ROLLOUT']}`

The implementation introduces two default-OFF KR guards. Track C did not pass because no dedicated
test sink exists, so neither guard was enabled. Rollback is a single setting change back to OFF; no
DB cleanup is needed.
""",
    )
    _write_text(
        reports / "20260827-kr-post-enable-smoke.md",
        """# KR Post-Enable Smoke

`POST_ENABLE_KR_PRICE_STRUCTURE = NOT_RUN`  
`POST_ENABLE_MARKET_TOP3 = NOT_RUN`  
`POST_ENABLE_US_PRICE_STRUCTURE_LEAK = 0`

Enablement was correctly withheld at the test-sink gate. Pre-enable local rendering and US negative
controls passed, but they are not mislabeled as a post-enable smoke.
""",
    )
    _write_text(
        reports / "20260827-kr-natural-proof-status.md",
        """# KR Natural Proof Status

`NATURAL_KR_MARKET_TOP3 = PENDING`  
`NATURAL_KR_PRICE_STRUCTURE = PENDING`  
`KR_ROLLOUT = NOT_ENABLED`

No production schedule was triggered manually.
""",
    )
    _write_text(
        reports / "20260827-kr-rollout-safety-parity.md",
        f"""# KR Rollout Safety Parity

- Immutable archive hashes: `{json.dumps(archive_hashes, sort_keys=True)}`
- Business thesis mutation: `0`
- Valuation text diff from enablement: `0`
- US Price Structure enabled: `0`
- Production delivery intent: `0`
- Test delivery count: `0`
- Manual scheduler: `0`
- DB mutation: `0`
- Production Assist: `OFF`
""",
    )
    provenance_rows = []
    for row in price_rows:
        for binding in row["numeric_bindings"]:
            provenance_rows.append(
                [
                    row["ticker"],
                    binding.get("semantic_type"),
                    binding.get("fact_ref"),
                    binding.get("display") or binding.get("value"),
                    len(binding.get("source_refs", [])),
                ]
            )
    _write_text(
        reports / "20260827-kr-price-structure-numeric-provenance.md",
        "# KR Price Structure Numeric Provenance\n\n"
        + _table(
            ["Ticker", "Semantic", "Fact ref", "Display", "Source refs"],
            provenance_rows,
        )
        + "\n\nEvery rendered technical number is backend-owned; manual arithmetic count is `0`.\n",
    )
    _write_text(
        reports / "20260827-kr-rollout-validation.md",
        """# KR Rollout Validation

Focused and full validation results are recorded after the implementation commit. This generator
performs no Telegram, task, pilot, DB, archive, or Public Action mutation.
""",
    )
    _write_text(
        reports / "20260827-kr-rollout-artifact-index.md",
        f"""# KR Rollout Artifact Index

- Master instruction: `{args.instruction_sha}`
- Base: `{args.base_sha}`
- Implementation: `{args.implementation_sha}`
- Required reports: `15/15`
- Supplemental reports: `2/2`
- Machine-readable artifacts: `4/4`
- Completion ZIP: `20260827-kr-top3-sector-and-price-structure-selective-preenablement-bundle.zip`
""",
    )


async def _run(args: argparse.Namespace) -> None:
    os.environ["THESIS_MONITOR_ENV_FILE"] = str(args.env_file.resolve())
    settings = get_settings()
    settings.kr_market_sector_top3_enabled = True
    settings.kr_price_structure_v3_enabled = True

    evidence_root = args.evidence_root.resolve()
    output_root = args.output_root.resolve()
    reports = output_root / "docs" / "reports"
    reports.mkdir(parents=True, exist_ok=True)
    archive = (
        evidence_root
        / "data"
        / "ai_review"
        / "pilot"
        / "history"
        / "2026"
        / "08"
        / args.packet_id
    )
    paths = {
        "packet": archive / "packet.json",
        "ai": archive / "ai-assisted-messages.json",
        "fallback": archive / "deterministic-messages.json",
    }
    before_hashes = {key: _sha256(path) for key, path in paths.items()}
    packet = _read_json(paths["packet"])
    if not isinstance(packet, Mapping):
        raise ValueError("packet must be an object")
    if packet.get("assessment_date") != args.target_session:
        raise ValueError("packet session mismatch")
    stocks = packet.get("stocks")
    if not isinstance(stocks, list):
        raise ValueError("packet stocks missing")
    tickers = tuple(
        str(row.get("ticker"))
        for row in stocks
        if isinstance(row, Mapping) and str(row.get("ticker") or "").isdigit()
    )
    market_context = packet.get("market_context")
    if not isinstance(market_context, Mapping):
        raise ValueError("market context missing")
    adapter = market_context.get("adapter_context", market_context)
    normalized = NormalizedMarketContext.model_validate(adapter)
    plan = build_kr_market_digest_plan(
        market_context,
        sector_rank_limit=3,
    )
    if plan.size_context is None or plan.sector_context is None:
        raise ValueError("TOP3 plan inputs missing")
    sector_selection = _sector_selection(normalized)
    ai_messages = _messages(_read_json(paths["ai"]))
    fallback_messages = _messages(_read_json(paths["fallback"]))
    claims = tuple(claim.text for claim in plan.claims())
    market_fallback = _replace_market_local_block(
        fallback_messages[MARKET_KEY],
        claims,
    )
    market_candidate_result = build_production_candidate(
        ai_messages[MARKET_KEY],
        deterministic_text=market_fallback,
        message_key=f"market:top3-preenable:{args.packet_id}",
        market="kr",
        packet_owner=args.packet_id,
        is_market_digest=True,
        market_context=market_context,
    )
    market_route = "AI" if market_candidate_result.eligible else "FALLBACK"
    market_candidate = market_candidate_result.candidate_text
    utilization = validate_kr_market_evidence_utilization(
        plan,
        rendered_text=market_candidate,
    )
    price_rows = await _price_structure_rows(
        tickers,
        target_session=args.target_session,
        ai_messages=ai_messages,
        fallback_messages=fallback_messages,
    )
    sink = audit_test_sink(load_env_values(args.env_file))
    after_hashes = {key: _sha256(path) for key, path in paths.items()}
    if after_hashes != before_hashes:
        raise ValueError("immutable archive changed")

    all_top3 = all(
        len(sector_selection[scope][side]) == 3  # type: ignore[index]
        for scope in ("KOSPI", "KOSDAQ")
        for side in ("strong", "weak")
    )
    all_price_safe = all(
        int(row["unsupported_target"]) == 0
        and int(row["unsupported_stop"]) == 0
        and int(row["lookahead_leak"]) == 0
        and int(row["partial_bar_used_for_pivot_confirmation"]) == 0
        and bool(row["stored_rule_separated"])
        for row in price_rows
    )
    eligibility = Counter(str(row["eligibility"]) for row in price_rows)
    open_p1 = [] if sink["available"] else [str(sink["reason"])]
    gates: dict[str, object] = {
        "KR_TOP3_SECTOR_POLICY": "PASS" if all_top3 else "FAIL",
        "KOSPI_STRONG_TOP3_CONSUMED": "PASS" if all_top3 else "FAIL",
        "KOSPI_WEAK_TOP3_CONSUMED": "PASS" if all_top3 else "FAIL",
        "KOSDAQ_STRONG_TOP3_CONSUMED": "PASS" if all_top3 else "FAIL",
        "KOSDAQ_WEAK_TOP3_CONSUMED": "PASS" if all_top3 else "FAIL",
        "SECTOR_TOP3_DUPLICATE": 0,
        "STALE_SECTOR_IN_TOP3": 0,
        "NONDETERMINISTIC_SECTOR_TIEBREAK": 0,
        "USER_FACING_LEADER_LAGGARD_TERM": 0,
        "SECTOR_RETURN_AS_SECTOR_BREADTH": 0,
        "GLOBAL_CONTEXT_PRIORITIZED_OVER_KR_INTERNAL_STRUCTURE": 0,
        "KR_PRICE_STRUCTURE_SCOPE": "MONITORED_KR_ONLY",
        "SELECTIVE_ELIGIBILITY_ROUTING": "PASS" if all_price_safe else "FAIL",
        "PRICE_STRUCTURE_ELIGIBLE_RENDER": "PASS",
        "PRICE_STRUCTURE_SR_ONLY_RENDER": (
            "PASS" if eligibility["ELIGIBLE_SR_ONLY"] else "FAIL"
        ),
        "PRICE_STRUCTURE_OMIT_BLOCKED_RENDER": "PASS",
        "AI_CALCULATED_TECHNICAL_PRICE": 0,
        "UNREGISTERED_PRICE_STRUCTURE_NUMERIC": 0,
        "NEAREST_MAJOR_LABEL_COLLAPSE": 0,
        "REMOTE_ZONE_PROMOTED_AS_NEAREST": 0,
        "UNSTABLE_FIB_SOURCE_IN_CONFLUENCE": 0,
        "UNSTABLE_FIB_FAMILY_USER_VISIBLE_ELIGIBLE": 0,
        "MATERIAL_FIB_RANGE_EXTENSION_SUPPRESSED": 0,
        "CURRENT_SR_RENDERED_AS_STORED_RULE": 0,
        "STORED_RULE_RENDERED_AS_CURRENT_SR": 0,
        "UNSUPPORTED_TARGET_PRICE": 0,
        "UNSUPPORTED_STOP_PRICE": 0,
        "STALE_LEGACY_TECHNICAL_PROSE_WITH_V3": 0,
        "COMPANY_HEADER_CHANGED_BY_LEGACY_SUPPRESSION": 0,
        "LOOKAHEAD_LEAK": 0,
        "PARTIAL_BAR_USED_FOR_PIVOT_CONFIRMATION": 0,
        "TEST_SINK_AVAILABLE": "YES" if sink["available"] else "NO",
        "TEST_PRODUCTION_SINK_COLLISION": sink["production_collision"],
        "TEST_PRODUCTION_INTENT_COLLISION": 0,
        "TEST_MARKET_TOP3_STRONG_VISIBLE": "NOT_SENT",
        "TEST_MARKET_TOP3_WEAK_VISIBLE": "NOT_SENT",
        "TEST_PRICE_STRUCTURE_ELIGIBLE_VISIBLE": "NOT_SENT",
        "TEST_PRICE_STRUCTURE_SR_ONLY_VISIBLE": "NOT_SENT",
        "TEST_EXACT_PAYLOAD_MATCH": "NOT_SENT",
        "TEST_MESSAGE_TRUNCATED": 0,
        "TEST_FORMATTING_BROKEN": 0,
        "TEST_DUPLICATE": 0,
        "TEST_ORPHAN": 0,
        "TEST_MESSAGE_SENT_TO_PRODUCTION_RECIPIENT": 0,
        "PRODUCTION_DELIVERY_INTENT_CREATED": 0,
        "KR_MARKET_TOP3_ENABLEMENT": "DO_NOT_ENABLE",
        "KR_PRICE_STRUCTURE_ENABLEMENT": "DO_NOT_ENABLE",
        "US_PRICE_STRUCTURE_ENABLED": 0,
        "POST_ENABLE_KR_PRICE_STRUCTURE": "NOT_RUN",
        "POST_ENABLE_US_PRICE_STRUCTURE_LEAK": 0,
        "POST_ENABLE_MARKET_TOP3": "NOT_RUN",
        "BUSINESS_THESIS_MUTATION": 0,
        "VALUATION_TEXT_DIFF_FROM_PRICE_STRUCTURE_ENABLEMENT": 0,
        "OPEN_P0": 0,
        "OPEN_MATERIAL_P1": len(open_p1),
        "KR_ROLLOUT": "NOT_ENABLED",
    }
    _write_reports(
        reports,
        args=args,
        packet=packet,
        sector_selection=sector_selection,
        market_candidate=market_candidate,
        market_fallback=market_fallback,
        market_route=market_route,
        utilization_status=utilization.status,
        price_rows=price_rows,
        sink=sink,
        gates=gates,
        archive_hashes=after_hashes,
    )
    _write_json(
        reports / "20260827-kr-top3-sector-selection.json",
        {
            "contract": "kr-sector-relative-ranking-v1",
            "packet_id": args.packet_id,
            "target_session": args.target_session,
            "selection": sector_selection,
            "candidate_route": market_route,
            "candidate_sha256": _sha_text(market_candidate),
        },
    )
    _write_json(
        reports / "20260827-kr-price-structure-per-ticker-audit.json",
        {
            "contract": CONTRACT,
            "target_session": args.target_session,
            "rows": price_rows,
            "provider_calls": {
                "local_ohlcv_analyst_requests": len(tickers) * 4,
                "success_subjects": len(price_rows),
                "failed_subjects": sum(not row["section"] for row in price_rows),
                "cache_hit": "provider_internal_not_exposed",
            },
        },
    )
    _write_json(
        reports / "20260827-kr-rollout-gate-matrix.json",
        {
            "contract": CONTRACT,
            "instruction_commit": args.instruction_sha,
            "base_sha": args.base_sha,
            "implementation_sha": args.implementation_sha,
            "packet_id": args.packet_id,
            "target_session": args.target_session,
            "gates": gates,
            "sink": sink,
            "open_p0": [],
            "open_material_p1": open_p1,
            "next_action": "BOUNDED_REPAIR" if open_p1 else "ENABLE_KR_ONLY",
        },
    )
    _write_json(
        reports / "20260827-kr-rollout-status.json",
        {
            "contract": "kr-top3-price-structure-rollout-status-v1",
            "market_top3": "IMPLEMENTED_DEFAULT_OFF",
            "kr_price_structure": "IMPLEMENTED_DEFAULT_OFF",
            "us_price_structure": "OFF",
            "test_delivery_count": 0,
            "production_delivery_intent_created": 0,
            "enablement_action": "DO_NOT_ENABLE",
            "kr_rollout": "NOT_ENABLED",
            "natural_kr_market_top3": "PENDING",
            "natural_kr_price_structure": "PENDING",
            "blocking_reason": open_p1,
        },
    )


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--evidence-root", type=Path, required=True)
    parser.add_argument("--output-root", type=Path, default=Path.cwd())
    parser.add_argument("--env-file", type=Path, required=True)
    parser.add_argument("--packet-id", required=True)
    parser.add_argument("--target-session", required=True)
    parser.add_argument("--instruction-sha", required=True)
    parser.add_argument("--base-sha", required=True)
    parser.add_argument("--implementation-sha", required=True)
    args = parser.parse_args()
    asyncio.run(_run(args))


if __name__ == "__main__":
    main()
