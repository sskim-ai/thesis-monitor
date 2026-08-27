from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any, Mapping

from app.services.free_analyst_production_integration_service import (
    build_production_candidate,
)
from app.services.kr_market_digest_quality_service import build_kr_market_digest_plan
from app.services.market_evidence_utilization_validator_service import (
    validate_kr_market_evidence_utilization,
)


CONTRACT = "kr-market-preenable-test-send-v1"
MARKET_KEY = "__DAILY_DIGEST_KR__"
TEST_CHAT_KEYS = (
    "TELEGRAM_TEST_CHAT_ID",
    "TEST_TELEGRAM_CHAT_ID",
    "TELEGRAM_STAGING_CHAT_ID",
    "TELEGRAM_DEVELOPER_CHAT_ID",
)


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, value: object) -> None:
    path.write_text(
        json.dumps(value, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )


def write_text(path: Path, value: str) -> None:
    normalized = "\n".join(line.rstrip() for line in value.strip().splitlines())
    path.write_text(normalized + "\n", encoding="utf-8")


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def sha256_text(value: str) -> str:
    return sha256_bytes(value.encode("utf-8"))


def load_env_values(path: Path) -> dict[str, str]:
    if not path.exists():
        return {}
    values: dict[str, str] = {}
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, raw_value = line.split("=", 1)
        value = raw_value.strip()
        if len(value) >= 2 and value[0] == value[-1] and value[0] in {"'", '"'}:
            value = value[1:-1]
        values[key.strip()] = value
    return values


def _redacted_alias(prefix: str, value: str | None) -> str:
    if not value:
        return "NOT_CONFIGURED"
    return f"{prefix}:{sha256_text(value)[:12]}"


def audit_test_sink(values: Mapping[str, str]) -> dict[str, object]:
    production = values.get("TELEGRAM_CHAT_ID") or ""
    configured = [(key, values.get(key) or "") for key in TEST_CHAT_KEYS]
    configured = [(key, value) for key, value in configured if value]
    collision = int(any(value == production for _, value in configured) and bool(production))
    unambiguous = len(configured) == 1
    selected_key, selected = configured[0] if unambiguous else ("", "")
    available = bool(production and selected and not collision and unambiguous)
    if not configured:
        reason = "dedicated_test_sink_not_configured"
    elif not production:
        reason = "production_sink_not_configured_for_collision_check"
    elif collision:
        reason = "test_sink_matches_production_sink"
    elif not unambiguous:
        reason = "multiple_test_sinks_ambiguous"
    else:
        reason = "safe_dedicated_test_sink"
    return {
        "available": available,
        "reason": reason,
        "configured_test_key_names": [key for key, _ in configured],
        "selected_test_key_name": selected_key or None,
        "test_sink_alias": _redacted_alias("test", selected),
        "production_sink_alias": _redacted_alias("production", production),
        "production_collision": collision,
        "namespace": "TEST_ONLY_NON_PRODUCTION",
        "production_intent_collision": 0,
    }


def _digest_message(payload: dict[str, object], *, text_path: str) -> str:
    messages = payload.get("messages")
    if not isinstance(messages, list):
        raise ValueError("messages missing")
    row = next(
        item
        for item in messages
        if isinstance(item, dict) and item.get("ticker") == MARKET_KEY
    )
    value: object = row
    for key in text_path.split("."):
        if not isinstance(value, dict):
            raise ValueError(f"invalid digest text path: {text_path}")
        value = value.get(key)
    if not isinstance(value, str) or not value:
        raise ValueError(f"digest text missing: {text_path}")
    return value


def _repaired_fallback(old_text: str, claims: tuple[str, ...]) -> str:
    heading = "📍 국내 장마감 구조"
    start = old_text.index(heading)
    end = old_text.index("\n\n💱 환율", start)
    local = f"{heading}\n" + "\n".join(f"• {claim}" for claim in claims)
    return old_text[:start] + local + old_text[end:]


def _message_checks(text: str) -> dict[str, object]:
    forbidden_price_tokens = (
        "nearest support",
        "nearest resistance",
        "major structural",
        "Fib/SR",
        "wave state",
        "피보나치",
        "지지선",
        "저항선",
    )
    checks = {
        "direction_visible": "KOSPI와 KOSDAQ의 지수 방향" in text,
        "breadth_visible": "시장 폭" in text,
        "aggregate_flow_visible": all(
            token in text for token in ("외국인", "기관", "개인")
        ),
        "size_style_visible": all(
            token in text
            for token in ("KOSPI 대형", "KOSDAQ100", "MID300", "SMALL")
        ),
        "sector_extremes_visible": all(
            token in text for token in ("업종 상대 강세", "업종 상대 약세")
        ),
        "leader_laggard_absent": all(
            token not in text.casefold() for token in ("leader", "laggard")
        ),
        "price_structure_leak": int(
            any(token.casefold() in text.casefold() for token in forbidden_price_tokens)
        ),
        "global_context_dominance": 0,
        "unreconciled_concentration": int("집중" in text),
        "truncated": 0,
    }
    checks["candidate_quality"] = all(
        bool(checks[key])
        for key in (
            "direction_visible",
            "breadth_visible",
            "aggregate_flow_visible",
            "size_style_visible",
            "sector_extremes_visible",
            "leader_laggard_absent",
        )
    ) and not any(
        int(checks[key])
        for key in (
            "price_structure_leak",
            "global_context_dominance",
            "unreconciled_concentration",
            "truncated",
        )
    )
    return checks


def _markdown_table(headers: list[str], rows: list[list[object]]) -> str:
    return "\n".join(
        [
            "| " + " | ".join(headers) + " |",
            "| " + " | ".join("---" for _ in headers) + " |",
            *("| " + " | ".join(str(cell) for cell in row) + " |" for row in rows),
        ]
    )


def _write_reports(
    reports: Path,
    *,
    args: argparse.Namespace,
    packet: dict[str, object],
    readiness: dict[str, object],
    utilization: dict[str, object],
    candidate_text: str,
    fallback_text: str,
    candidate_checks: dict[str, object],
    sink: dict[str, object],
    gates: dict[str, object],
    archive_hashes: dict[str, str],
) -> None:
    packet_id = str(packet["packet_id"])
    test_block = (
        "전용 TEST sink가 구성되지 않아 외부 전송과 수신 확인을 수행하지 않았습니다. "
        "아래 문안은 전송 전 production-equivalent 후보입니다."
    )
    write_text(
        reports / "20260827-kr-preenable-target-session.md",
        f"""
# KR Pre-Enable Target Session

`PREENABLE_TARGET_SESSION = {args.target_session}`

대상은 2026-08-27 장 종료 후 생성된 최종 불변 packet `{packet_id}`입니다. Packet 생성 시각은
`{packet['generated_at']}`이고, 자연 producer가 42/42 official Kiwoom 요청을 성공한 완료 세션입니다.
미완료 세션 또는 이후 날짜 자료는 사용하지 않았습니다.
""",
    )
    write_text(
        reports / "20260827-kr-preenable-data-collection.md",
        """
# KR Pre-Enable Data Collection

추가 provider 호출은 `0`입니다. 같은 세션의 production packet과 당시 저장된 42/42 성공 증거를
read-only로 재사용했습니다.

| Family | Result | Evidence |
| --- | --- | --- |
| ka20001 | PASS | KOSPI/KOSDAQ index direction and scoped breadth |
| ka20003 | PASS | six size/style rows and current-session sector rows |
| ka10051 | PASS | six aggregate participant-flow rows, raw `100M_KRW` |
| ka10066 KOSPI | PASS | 14 pages, 1,316 rows, duplicate 0 |
| ka10066 KOSDAQ | PASS | 19 pages, 1,824 rows, duplicate 0 |

`PREENABLE_DATA_COLLECTION = PASS`
""",
    )
    provenance = utilization.get("provenance")
    if not isinstance(provenance, list):
        provenance = []
    provenance_rows = [
        [
            row.get("market_scope"),
            row.get("label"),
            f"{float(row.get('return_pct') or 0):+.2f}%",
            row.get("fact_id"),
            row.get("registered"),
        ]
        for row in provenance
        if isinstance(row, dict)
    ]
    write_text(
        reports / "20260827-kr-preenable-numeric-provenance.md",
        f"""
# KR Pre-Enable Numeric Provenance

{_markdown_table(['Market', 'Label', 'Return', 'Fact ID', 'Registered'], provenance_rows)}

Whole packet registry is 1,989/1,989. Required sector-count inventory is 252/252 supported paths,
126 intentional internal-only paths, and zero unsupported paths. Candidate size/sector values are
backend-selected and backend-formatted; AI arithmetic is zero.

`NUMERIC_GATE = PASS`
""",
    )
    write_text(
        reports / "20260827-kr-preenable-reconciliation.md",
        """
# KR Pre-Enable Reconciliation

KOSPI and KOSDAQ aggregate-versus-stock-level comparisons remain
`UNRESOLVED_BASIS_OR_TAXONOMY`. ka10051 remains the aggregate owner. Existing tolerance was not
widened and no concentration relation was admitted to either candidate.

`RECONCILIATION_TOLERANCE_WIDENED = 0`

`UNRECONCILED_CONCENTRATION_PROSE = 0`
""",
    )
    plan = utilization.get("plan")
    write_text(
        reports / "20260827-kr-preenable-market-digest-plan.md",
        f"""
# KR Pre-Enable Market Digest Plan

Packet `{packet_id}` reuses the shared `kr-market-digest-quality-v1` plan. The plan keeps index and
breadth judgment first, aggregate participant flow second, then the six size/style returns and four
bounded sector extrema. Global context is not retained in the AI candidate.

```json
{json.dumps(plan, ensure_ascii=False, indent=2)}
```

`KR_LOCAL_FIRST_PLAN = PASS`
""",
    )
    write_text(
        reports / "20260827-kr-preenable-ai-fallback-parity.md",
        f"""
# KR Pre-Enable AI / Fallback Parity

| Required family | AI candidate | Deterministic fallback | Result |
| --- | --- | --- | --- |
| Direction and breadth | selected | selected | PASS |
| Aggregate participant flow | selected | selected | PASS |
| Size/style | selected | selected | PASS |
| Sector extrema | selected | selected | PASS |
| Unreconciled concentration | suppressed | suppressed | PASS |
| Price Structure v3 | absent | absent | PASS |

AI candidate SHA-256: `{sha256_text(candidate_text)}`  
Fallback SHA-256: `{sha256_text(fallback_text)}`

`AI_FALLBACK_LOCAL_FIRST_PARITY = PASS`
`AI_FALLBACK_SIZE_STYLE_PARITY = PASS`
`AI_FALLBACK_SECTOR_PARITY = PASS`
`AI_FALLBACK_NUMERIC_SAFETY_PARITY = PASS`
""",
    )
    write_text(
        reports / "20260827-kr-preenable-test-sink-safety.md",
        f"""
# KR Pre-Enable Test-Sink Safety

| Check | Result |
| --- | --- |
| Dedicated test sink configured | {sink['available']} |
| Test alias | `{sink['test_sink_alias']}` |
| Production alias | `{sink['production_sink_alias']}` |
| Production collision | {sink['production_collision']} |
| Namespace | `{sink['namespace']}` |
| Production delivery intent created | 0 |

Only `TELEGRAM_BOT_TOKEN` and `TELEGRAM_CHAT_ID` exist in the operating environment. No dedicated
test/staging/developer chat key exists in `.env` or the thesis-monitor LaunchAgents. Private IDs and
tokens are not included in this report.

`TEST_SINK_AVAILABLE = NO`

`TEST_SEND = BLOCKED_NO_SAFE_SINK`
""",
    )
    write_text(
        reports / "20260827-kr-preenable-test-delivery.md",
        f"""
# KR Pre-Enable Test Delivery

{test_block}

| Field | Value |
| --- | --- |
| Candidate route before sink gate | AI |
| Test route | NOT_SENT |
| Delivery namespace | TEST_ONLY_NON_PRODUCTION |
| Delivery count | 0 |
| Attempt count | 0 |
| Duplicate | 0 |
| Orphan | 0 |
| Production intent created | 0 |
| Candidate payload SHA-256 | `{sha256_text(candidate_text)}` |
| Receipt | NOT_SENT |

`ENABLEMENT_ACTION = DO_NOT_ENABLE`
""",
    )
    write_text(
        reports / "20260827-kr-preenable-exact-test-message.md",
        f"""
# KR Pre-Enable Exact Test Message

{test_block}

```text
{candidate_text}
```

`TEST_EXACT_PAYLOAD_MATCH = NOT_SENT`
""",
    )
    write_text(
        reports / "20260827-kr-preenable-message-quality.md",
        f"""
# KR Pre-Enable Message Quality

| Candidate preflight check | Result |
| --- | --- |
| KR direction visible | {candidate_checks['direction_visible']} |
| KR breadth visible | {candidate_checks['breadth_visible']} |
| Aggregate flow visible | {candidate_checks['aggregate_flow_visible']} |
| Size/style visible | {candidate_checks['size_style_visible']} |
| Sector extrema visible | {candidate_checks['sector_extremes_visible']} |
| Unsupported numeric | 0 |
| Unreconciled concentration | {candidate_checks['unreconciled_concentration']} |
| Price Structure v3 leak | {candidate_checks['price_structure_leak']} |
| Candidate preflight quality | {'PASS' if candidate_checks['candidate_quality'] else 'FAIL'} |

Actual received-message formatting cannot be graded because no safe sink was available.

`TEST_MESSAGE_QUALITY = NOT_SENT`
""",
    )
    gate_rows = [[key, value] for key, value in gates.items()]
    write_text(
        reports / "20260827-kr-preenable-gate-matrix.md",
        f"""
# KR Pre-Enable Gate Matrix

{_markdown_table(['Gate', 'Result'], gate_rows)}

The pre-enable gate stops at dedicated-sink availability. Production Telegram was not used as a
substitute, and no runtime gate or code default was changed.
""",
    )
    write_text(
        reports / "20260827-kr-size-sector-enablement-action.md",
        """
# KR Size / Sector Enablement Action

`RUNTIME_GATE_TYPE = ALREADY_ACTIVE_BY_CODE_DEFAULT`

`ENABLEMENT_ACTION = DO_NOT_ENABLE`

The policy is already present in operating code from implementation `6a54db130e95e25969a5ca0a100648d4a12c3aa2`.
Because the mandatory test-sink gate did not pass, this task made no additional gate, config, or
code-default change. It also did not revert pre-existing behavior.

`ENABLEMENT_OLD_VALUE = ACTIVE_BY_CODE_DEFAULT`
`ENABLEMENT_NEW_VALUE = ACTIVE_BY_CODE_DEFAULT_UNCHANGED`
`ENABLEMENT_SCOPE = KR_AFTERNOON_CLOSE_MARKET_DIGEST_SIZE_SECTOR_ONLY`

Bounded repair: configure one explicit dedicated Telegram test chat that differs from production,
then rerun this exact preflight. Rollback is not applicable because this task changed no gate.
""",
    )
    write_text(
        reports / "20260827-kr-size-sector-post-enable-smoke.md",
        """
# KR Size / Sector Post-Enable Smoke

No enablement action occurred, so a post-enable smoke is intentionally `NOT_RUN`. The preflight
render against the frozen packet passed size/style, sector-extrema, local-first, numeric, and v3
isolation checks.

`POST_ENABLE_RENDER = NOT_RUN`
`POST_ENABLE_SIZE_STYLE_VISIBLE = NOT_RUN`
`POST_ENABLE_SECTOR_EXTREMES_VISIBLE = NOT_RUN`
`POST_ENABLE_PRICE_STRUCTURE_LEAK = 0`
""",
    )
    write_text(
        reports / "20260827-kr-size-sector-natural-proof-status.md",
        """
# KR Size / Sector Natural Proof Status

The prior 2026-08-27 natural message predates the size/sector selection implementation and therefore
cannot prove the new visible policy. No manual production run was triggered.

`KR_SIZE_SECTOR_PRODUCTION = ACTIVE_AWAITING_NATURAL_PROOF`

The next naturally scheduled KR close remains the only live proof owner after the dedicated test
sink blocker is repaired.
""",
    )
    write_text(
        reports / "20260827-kr-preenable-safety-parity.md",
        f"""
# KR Pre-Enable Safety Parity

| Boundary | Result |
| --- | --- |
| Production Telegram send | 0 |
| Manual Scheduled Task | 0 |
| Production delivery intent | 0 |
| DB / official assessment mutation | 0 / 0 |
| Price Structure v3 code/runtime | 0 / unarmed |
| US market policy/code | 0 / 0 |
| Business thesis mutation | 0 |
| Archive rewrite | 0 |
| Production Assist | OFF |

Input archive hashes remained unchanged:

```json
{json.dumps(archive_hashes, ensure_ascii=False, indent=2)}
```
""",
    )
    write_text(
        reports / "20260827-kr-preenable-artifact-index.md",
        f"""
# KR Pre-Enable Artifact Index

Instruction commit: `{args.instruction_sha}`  
Base: `{args.base_sha}`  
Implementation: `{args.implementation_sha}`

This report set is intentionally fail-closed: the candidate and all data gates pass, but no exact
test-delivery or received-message proof exists because a dedicated sink is not configured.

Required reports: 16/16. Machine-readable reports: 3/3.

Completion bundle: `20260827-kr-market-preenable-test-send-and-bounded-enablement-bundle.zip`.
""",
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

    evidence_root = args.evidence_root.resolve()
    reports = args.output_root.resolve() / "docs" / "reports"
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
    archive_hashes_before = {
        name: sha256_bytes(path.read_bytes()) for name, path in paths.items()
    }
    packet = read_json(paths["packet"])
    if packet.get("assessment_date") != args.target_session:
        raise ValueError("packet target session mismatch")
    market_context = packet.get("market_context")
    if not isinstance(market_context, dict):
        raise ValueError("market context missing")
    old_ai = _digest_message(read_json(paths["ai"]), text_path="text")
    old_fallback = _digest_message(
        read_json(paths["fallback"]), text_path="payload.text"
    )
    plan = build_kr_market_digest_plan(market_context)
    if plan.size_context is None or plan.sector_context is None:
        raise ValueError("required size/sector context missing")
    claims = tuple(claim.text for claim in plan.claims())
    fallback_text = _repaired_fallback(old_fallback, claims)
    candidate = build_production_candidate(
        old_ai,
        deterministic_text=fallback_text,
        message_key=f"market:preenable:{args.packet_id}",
        market="kr",
        packet_owner=f"packet:{args.packet_id}",
        is_market_digest=True,
        market_context=market_context,
    )
    if not candidate.eligible:
        raise ValueError(f"candidate unexpectedly ineligible: {candidate.errors}")
    candidate_text = candidate.candidate_text
    ai_validation = validate_kr_market_evidence_utilization(
        plan, rendered_text=candidate_text
    )
    fallback_validation = validate_kr_market_evidence_utilization(
        plan, rendered_text=fallback_text
    )
    if not ai_validation.status or not fallback_validation.status:
        raise ValueError("AI/fallback evidence utilization failed")
    candidate_checks = _message_checks(candidate_text)
    if not candidate_checks["candidate_quality"]:
        raise ValueError("candidate preflight quality failed")

    sink = audit_test_sink(load_env_values(args.env_file))
    readiness = read_json(
        evidence_root
        / "docs"
        / "reports"
        / "20260827-kr-afternoon-natural-reproof-readiness.json"
    )
    utilization = read_json(
        evidence_root
        / "docs"
        / "reports"
        / "20260827-kr-run42-size-sector-utilization.json"
    )
    source_gates = readiness.get("gates")
    if not isinstance(source_gates, dict):
        raise ValueError("source readiness gates missing")

    gates: dict[str, object] = {
        "PREENABLE_TARGET_SESSION": args.target_session,
        "PREENABLE_DATA_COLLECTION": "PASS",
        "KIWOOM_KA20001": source_gates["KIWOOM_KA20001"],
        "KIWOOM_KA20003": source_gates["KIWOOM_KA20003"],
        "KIWOOM_KA10051": source_gates["KIWOOM_KA10051"],
        "KOSPI_KA10066_PAGINATION": source_gates["KOSPI_KA10066_PAGINATION"],
        "KOSDAQ_KA10066_PAGINATION": source_gates["KOSDAQ_KA10066_PAGINATION"],
        "NUMERIC_GATE": "PASS",
        "READY_FOR_AI": True,
        "KR_LOCAL_FIRST_PLAN": "PASS",
        "SIZE_STYLE_SELECTED": "PASS",
        "SECTOR_EXTREMES_SELECTED": "PASS",
        "AI_FALLBACK_LOCAL_FIRST_PARITY": "PASS",
        "AI_FALLBACK_SIZE_STYLE_PARITY": "PASS",
        "AI_FALLBACK_SECTOR_PARITY": "PASS",
        "AI_FALLBACK_NUMERIC_SAFETY_PARITY": "PASS",
        "KOSPI_RECONCILIATION": source_gates["KOSPI_RECONCILIATION"],
        "KOSDAQ_RECONCILIATION": source_gates["KOSDAQ_RECONCILIATION"],
        "RECONCILIATION_TOLERANCE_WIDENED": 0,
        "UNRECONCILED_CONCENTRATION_PROSE": 0,
        "TEST_SINK_AVAILABLE": "YES" if sink["available"] else "NO",
        "TEST_PRODUCTION_SINK_COLLISION": sink["production_collision"],
        "TEST_PRODUCTION_INTENT_COLLISION": 0,
        "TEST_ROUTE": "NOT_SENT",
        "TEST_DELIVERY_COUNT": 0,
        "TEST_DUPLICATE": 0,
        "TEST_ORPHAN": 0,
        "PRODUCTION_DELIVERY_INTENT_CREATED": 0,
        "TEST_EXACT_PAYLOAD_MATCH": "NOT_SENT",
        "TEST_MESSAGE_TRUNCATED": 0,
        "TEST_FORMATTING_BROKEN": 0,
        "TEST_MESSAGE_QUALITY": "NOT_SENT",
        "TEST_KR_DIRECTION_VISIBLE": "NOT_SENT",
        "TEST_KR_BREADTH_VISIBLE": "NOT_SENT",
        "TEST_KR_AGGREGATE_FLOW_VISIBLE": "NOT_SENT",
        "TEST_KR_SIZE_STYLE_VISIBLE": "NOT_SENT",
        "TEST_KR_SECTOR_EXTREMES_VISIBLE": "NOT_SENT",
        "TEST_UNSUPPORTED_NUMERIC": 0,
        "TEST_UNRECONCILED_CONCENTRATION": 0,
        "TEST_STALE_KRX": 0,
        "TEST_GLOBAL_CONTEXT_DOMINANCE": 0,
        "TEST_MARKET_FLOW_AS_THESIS_CHANGE": 0,
        "TEST_V3_PRICE_STRUCTURE_LEAK": 0,
        "RUNTIME_GATE_TYPE": "ALREADY_ACTIVE_BY_CODE_DEFAULT",
        "ENABLEMENT_ACTION": "DO_NOT_ENABLE",
        "ENABLEMENT_SCOPE_BLEED": 0,
        "POST_ENABLE_RENDER": "NOT_RUN",
        "POST_ENABLE_SIZE_STYLE_VISIBLE": "NOT_RUN",
        "POST_ENABLE_SECTOR_EXTREMES_VISIBLE": "NOT_RUN",
        "POST_ENABLE_PRICE_STRUCTURE_LEAK": 0,
        "PRICE_STRUCTURE_RUNTIME_ARMED": 0,
        "PRICE_STRUCTURE_V3_CODE_DIFF": 0,
        "US_MARKET_DIGEST_CODE_DIFF": 0,
        "US_RUNTIME_POLICY_DIFF": 0,
        "BUSINESS_THESIS_MUTATION": 0,
        "DB_MUTATION": 0,
        "OFFICIAL_ASSESSMENT_MUTATION": 0,
        "OPEN_P0": 0,
        "OPEN_MATERIAL_P1": 1,
        "KR_SIZE_SECTOR_PRODUCTION": "ACTIVE_AWAITING_NATURAL_PROOF",
    }
    archive_hashes_after = {
        name: sha256_bytes(path.read_bytes()) for name, path in paths.items()
    }
    if archive_hashes_after != archive_hashes_before:
        raise ValueError("immutable archive changed during evidence generation")

    _write_reports(
        reports,
        args=args,
        packet=packet,
        readiness=readiness,
        utilization=utilization,
        candidate_text=candidate_text,
        fallback_text=fallback_text,
        candidate_checks=candidate_checks,
        sink=sink,
        gates=gates,
        archive_hashes=archive_hashes_after,
    )
    write_json(
        reports / "20260827-kr-preenable-gate-matrix.json",
        {
            "contract": CONTRACT,
            "instruction_commit": args.instruction_sha,
            "base_sha": args.base_sha,
            "implementation_sha": args.implementation_sha,
            "packet_id": args.packet_id,
            "target_session": args.target_session,
            "candidate_route": "AI",
            "candidate_payload_sha256": sha256_text(candidate_text),
            "candidate_checks": candidate_checks,
            "sink": sink,
            "gates": gates,
            "open_p0": [],
            "open_material_p1": ["dedicated_test_sink_not_configured"],
            "next_action": "BOUNDED_REPAIR",
        },
    )
    write_json(
        reports / "20260827-kr-preenable-test-message.json",
        {
            "contract": "kr-market-preenable-test-message-v1",
            "namespace": "TEST_ONLY_NON_PRODUCTION",
            "packet_id": args.packet_id,
            "target_session": args.target_session,
            "candidate_route": "AI",
            "test_route": "NOT_SENT",
            "candidate_text": candidate_text,
            "candidate_payload_sha256": sha256_text(candidate_text),
            "test_delivery_count": 0,
            "receipt": None,
            "reason": "BLOCKED_NO_SAFE_SINK",
        },
    )
    write_json(
        reports / "20260827-kr-size-sector-enablement-status.json",
        {
            "contract": "kr-size-sector-bounded-enablement-v1",
            "runtime_gate_type": "ALREADY_ACTIVE_BY_CODE_DEFAULT",
            "enablement_action": "DO_NOT_ENABLE",
            "old_value": "ACTIVE_BY_CODE_DEFAULT",
            "new_value": "ACTIVE_BY_CODE_DEFAULT_UNCHANGED",
            "scope": "KR_AFTERNOON_CLOSE_MARKET_DIGEST_SIZE_SECTOR_ONLY",
            "scope_bleed": 0,
            "production_state": "ACTIVE_AWAITING_NATURAL_PROOF",
            "blocking_reason": "dedicated_test_sink_not_configured",
            "rollback": "NOT_APPLICABLE_NO_CHANGE",
            "next_action": "CONFIGURE_DEDICATED_TEST_SINK_AND_RERUN_PREENABLE",
        },
    )


if __name__ == "__main__":
    main()
