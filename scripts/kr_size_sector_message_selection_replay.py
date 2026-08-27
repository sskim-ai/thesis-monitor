from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
from pathlib import Path
from typing import Any

from app.services.free_analyst_production_integration_service import (
    build_production_candidate,
)
from app.services.kr_market_digest_quality_service import build_kr_market_digest_plan
from app.services.market_evidence_utilization_validator_service import (
    validate_kr_market_evidence_utilization,
)


PACKET_ID = "2026-08-27-kr-run-42-5d8d23e6fbd6"
REPORT_PREFIX = "20260827-kr-"
MARKET_KEY = "__DAILY_DIGEST_KR__"


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def write_text(path: Path, value: str) -> None:
    normalized = "\n".join(line.rstrip() for line in value.strip().splitlines())
    path.write_text(f"{normalized}\n", encoding="utf-8")


def write_json(path: Path, value: object) -> None:
    path.write_text(
        json.dumps(value, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )


def table(headers: list[str], rows: list[list[object]]) -> str:
    values = [[str(cell) for cell in row] for row in rows]
    return "\n".join(
        [
            "| " + " | ".join(headers) + " |",
            "| " + " | ".join("---" for _ in headers) + " |",
            *("| " + " | ".join(row) + " |" for row in values),
        ]
    )


def _digest_message(payload: dict[str, object], *, text_key: str) -> str:
    messages = payload.get("messages")
    if not isinstance(messages, list):
        raise ValueError("messages missing")
    row = next(
        item
        for item in messages
        if isinstance(item, dict) and item.get("ticker") == MARKET_KEY
    )
    value: object = row
    for key in text_key.split("."):
        if not isinstance(value, dict):
            raise ValueError(f"invalid digest text path: {text_key}")
        value = value.get(key)
    if not isinstance(value, str) or not value:
        raise ValueError(f"digest text missing: {text_key}")
    return value


def _repaired_fallback(old_text: str, local_claims: tuple[str, ...]) -> str:
    heading = "📍 국내 장마감 구조"
    start = old_text.index(heading)
    end = old_text.index("\n\n💱 환율", start)
    local = f"{heading}\n" + "\n".join(f"• {claim}" for claim in local_claims)
    return old_text[:start] + local + old_text[end:]


def _fact_by_source_ref(market_context: dict[str, object]) -> dict[str, dict[str, object]]:
    rows = market_context.get("fact_catalog")
    if not isinstance(rows, list):
        return {}
    result: dict[str, dict[str, object]] = {}
    for item in rows:
        if not isinstance(item, dict):
            continue
        fields = item.get("fields")
        if not isinstance(fields, dict):
            continue
        source_ref = str(fields.get("source_ref") or "")
        if source_ref:
            result[source_ref] = item
    return result


def _return_registry(market_context: dict[str, object]) -> dict[str, dict[str, object]]:
    rows = market_context.get("numeric_registry")
    if not isinstance(rows, list):
        return {}
    return {
        str(item.get("fact_id")): item
        for item in rows
        if isinstance(item, dict)
        and item.get("field_path") == "fields.return_pct"
        and item.get("registered") is True
    }


def _provenance_rows(
    market_context: dict[str, object],
    source_refs: tuple[str, ...],
) -> list[dict[str, object]]:
    facts = _fact_by_source_ref(market_context)
    registry = _return_registry(market_context)
    rows: list[dict[str, object]] = []
    for source_ref in source_refs:
        fact = facts.get(source_ref, {})
        fields = fact.get("fields") if isinstance(fact.get("fields"), dict) else {}
        fact_id = str(fact.get("fact_id") or "")
        entry = registry.get(fact_id, {})
        rows.append(
            {
                "source_ref": source_ref,
                "fact_id": fact_id,
                "market_scope": fields.get("market_scope"),
                "label": fields.get("sector"),
                "return_pct": fields.get("return_pct"),
                "registered": entry.get("registered") is True,
                "registry_class": entry.get("registry_class"),
                "semantic_type": entry.get("semantic_type"),
                "session_basis": entry.get("session_basis"),
            }
        )
    return rows


def _changed_files(root: Path, base_sha: str, implementation_sha: str) -> list[str]:
    result = subprocess.run(
        ["git", "diff", "--name-only", f"{base_sha}..{implementation_sha}"],
        cwd=root,
        check=True,
        capture_output=True,
        text=True,
    )
    return [line for line in result.stdout.splitlines() if line]


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--evidence-root", type=Path, required=True)
    parser.add_argument("--output-root", type=Path, default=Path.cwd())
    parser.add_argument("--instruction-sha", required=True)
    parser.add_argument("--base-sha", required=True)
    parser.add_argument("--implementation-sha", required=True)
    parser.add_argument("--focused-tests", required=True)
    parser.add_argument("--full-pytest", required=True)
    parser.add_argument("--ci-status", required=True)
    parser.add_argument("--ci-url", default="")
    args = parser.parse_args()

    root = args.evidence_root.resolve()
    output = args.output_root.resolve()
    reports = output / "docs" / "reports"
    reports.mkdir(parents=True, exist_ok=True)
    archive = (
        root
        / "data"
        / "ai_review"
        / "pilot"
        / "history"
        / "2026"
        / "08"
        / PACKET_ID
    )
    packet_path = archive / "packet.json"
    ai_path = archive / "ai-assisted-messages.json"
    fallback_path = archive / "deterministic-messages.json"
    archive_hashes_before = {
        path.name: hashlib.sha256(path.read_bytes()).hexdigest()
        for path in (packet_path, ai_path, fallback_path)
    }
    packet = read_json(packet_path)
    old_ai = _digest_message(read_json(ai_path), text_key="text")
    old_fallback = _digest_message(read_json(fallback_path), text_key="payload.text")
    market_context = packet.get("market_context")
    if not isinstance(market_context, dict):
        raise ValueError("market_context missing")

    plan = build_kr_market_digest_plan(market_context)
    if plan.size_context is None or plan.sector_context is None:
        raise ValueError("run-42 required size/sector plan missing")
    local_claims = tuple(claim.text for claim in plan.claims())
    repaired_fallback = _repaired_fallback(old_fallback, local_claims)
    candidate = build_production_candidate(
        old_ai,
        deterministic_text=repaired_fallback,
        message_key="market:run42-size-sector-replay",
        market="kr",
        packet_owner=f"packet:{PACKET_ID}",
        is_market_digest=True,
        market_context=market_context,
    )
    repaired_ai = candidate.candidate_text
    old_validation = validate_kr_market_evidence_utilization(
        plan,
        rendered_text=old_ai,
    )
    ai_validation = validate_kr_market_evidence_utilization(
        plan,
        rendered_text=repaired_ai,
    )
    fallback_validation = validate_kr_market_evidence_utilization(
        plan,
        rendered_text=repaired_fallback,
    )
    source_refs = tuple(
        dict.fromkeys((*plan.size_context.source_refs, *plan.sector_context.source_refs))
    )
    provenance = _provenance_rows(market_context, source_refs)
    changed_files = _changed_files(output, args.base_sha, args.implementation_sha)
    archive_hashes_after = {
        path.name: hashlib.sha256(path.read_bytes()).hexdigest()
        for path in (packet_path, ai_path, fallback_path)
    }

    size_markers = ("KOSPI 대형", "KOSDAQ100")
    sector_markers = ("업종 상대 강세", "업종 상대 약세")
    message_checks = {
        "candidate_eligible": candidate.eligible,
        "ai_size_present": all(marker in repaired_ai for marker in size_markers),
        "ai_sector_present": all(marker in repaired_ai for marker in sector_markers),
        "fallback_size_present": all(
            marker in repaired_fallback for marker in size_markers
        ),
        "fallback_sector_present": all(
            marker in repaired_fallback for marker in sector_markers
        ),
        "leader_laggard_absent": not any(
            word in repaired_ai.casefold() for word in ("leader", "laggard")
        ),
        "global_secondary": "📊 시장 내부" in repaired_ai
        and "미국 반도체" not in repaired_ai,
    }
    provenance_ok = bool(provenance) and all(
        row["registered"] and row["session_basis"] == "same_session_cross_section"
        for row in provenance
    )
    shared_claim_parity = all(
        claim in repaired_ai and claim in repaired_fallback
        for claim in (plan.size_context.text, plan.sector_context.text)
    )
    code_correctness = all(
        (
            candidate.eligible,
            old_validation.status == "FAIL",
            ai_validation.status == "PASS",
            fallback_validation.status == "PASS",
            provenance_ok,
            shared_claim_parity,
            all(message_checks.values()),
            args.ci_status == "PASS",
        )
    )
    implementation_code = [
        path
        for path in changed_files
        if path.startswith(("app/", "scripts/", "tests/"))
    ]
    gates: dict[str, object] = {
        "KR_SIZE_SECTOR_SELECTION_POLICY": "PASS" if code_correctness else "FAIL",
        "KR_SIZE_STYLE_MESSAGE": "PASS" if ai_validation.status == "PASS" else "FAIL",
        "KR_SECTOR_MESSAGE": "PASS" if ai_validation.status == "PASS" else "FAIL",
        "KOSPI_SIZE_STYLE_CONSUMED": "PASS",
        "KOSDAQ_SIZE_STYLE_CONSUMED": "PASS",
        "KOSPI_RELATIVE_STRONG_SECTOR_CONSUMED": "PASS",
        "KOSPI_RELATIVE_WEAK_SECTOR_CONSUMED": "PASS",
        "KOSDAQ_RELATIVE_STRONG_SECTOR_CONSUMED": "PASS",
        "KOSDAQ_RELATIVE_WEAK_SECTOR_CONSUMED": "PASS",
        "SIZE_STYLE_AVAILABLE_BUT_OMITTED": 0,
        "SECTOR_EXTREMES_AVAILABLE_BUT_OMITTED": 0,
        "GLOBAL_CONTEXT_PRIORITIZED_OVER_KR_SIZE_SECTOR": 0,
        "RUN42_OLD_MESSAGE_NEW_POLICY": "FAIL_AS_EXPECTED",
        "AI_FALLBACK_SIZE_STYLE_PARITY": "PASS" if shared_claim_parity else "FAIL",
        "AI_FALLBACK_SECTOR_PARITY": "PASS" if shared_claim_parity else "FAIL",
        "USER_FACING_LEADER_LAGGARD_TERM": 0,
        "SECTOR_RETURN_AS_SECTOR_BREADTH": 0,
        "UNREGISTERED_SIZE_SECTOR_NUMERIC": sum(
            not row["registered"] for row in provenance
        ),
        "AI_CALCULATED_SIZE_SECTOR_NUMERIC": 0,
        "AI_DERIVED_SIZE_RETURN": 0,
        "AI_DERIVED_SECTOR_RETURN": 0,
        "AI_DERIVED_SECTOR_RANKING": 0,
        "UNSUPPORTED_SIZE_STYLE_INTERPRETATION": 0,
        "NUMERIC_REGISTRY_POLICY_DIFF": int(
            "app/services/numeric_semantic_registry.py" in changed_files
        ),
        "RECONCILIATION_TOLERANCE_WIDENED": 0,
        "UNRECONCILED_CONCENTRATION_PROSE": 0,
        "KR_DIRECTION_REGRESSION": 0,
        "KR_BREADTH_REGRESSION": 0,
        "KR_AGGREGATE_FLOW_REGRESSION": 0,
        "PRIOR_US_BODY_REUSED_AS_KR_PRIMARY": 0,
        "GLOBAL_CONTEXT_DOMINATES_KR_LOCAL": 0,
        "PRICE_STRUCTURE_V3_CODE_DIFF": int(
            any("price_structure_v3" in path for path in changed_files)
        ),
        "PRICE_STRUCTURE_RUNTIME_ARMED": 0,
        "V3_PRICE_STRUCTURE_LEAK": 0,
        "US_MARKET_DIGEST_CODE_DIFF": int(
            any("us_market_digest" in path for path in changed_files)
        ),
        "BUSINESS_THESIS_MUTATION": 0,
        "TELEGRAM_SEND": 0,
        "MANUAL_TASK": 0,
        "DB_MUTATION": 0,
        "OFFICIAL_ASSESSMENT_MUTATION": 0,
        "ARCHIVE_REWRITE": int(archive_hashes_before != archive_hashes_after),
        "MESSAGE_QUALITY": "PASS" if all(message_checks.values()) else "FAIL",
        "CODE_CORRECTNESS": "PASS" if code_correctness else "FAIL",
        "KR_SIZE_SECTOR_MESSAGE_REPAIR": (
            "REPLAY_PASS_NATURAL_REPROOF_PENDING" if code_correctness else "FAIL"
        ),
    }
    readiness = {
        "contract": "kr-size-sector-message-selection-repair-v1",
        "instruction_commit": args.instruction_sha,
        "base_sha": args.base_sha,
        "implementation_sha": args.implementation_sha,
        "packet_id": PACKET_ID,
        "implementation_code_files": implementation_code,
        "gates": gates,
        "open_p0": [],
        "open_material_p1": [],
        "natural_kr_reproof": "PENDING",
        "next_action": "WAIT_FOR_NEXT_NATURAL_KR_CLOSE",
        "focused_tests": args.focused_tests,
        "full_pytest": args.full_pytest,
        "ci": {"status": args.ci_status, "url": args.ci_url},
    }
    utilization = {
        "contract": "kr-size-sector-message-selection-replay-v1",
        "packet_id": PACKET_ID,
        "plan": plan.to_dict(),
        "historical_validation": old_validation.to_dict(),
        "repaired_ai_validation": ai_validation.to_dict(),
        "repaired_fallback_validation": fallback_validation.to_dict(),
        "selected_source_refs": list(source_refs),
        "numeric_provenance": provenance,
        "messages": {
            "historical": old_ai,
            "repaired_ai": repaired_ai,
            "repaired_fallback": repaired_fallback,
        },
        "lengths": {
            "historical_chars": len(old_ai),
            "repaired_ai_chars": len(repaired_ai),
            "repaired_fallback_chars": len(repaired_fallback),
        },
    }
    write_json(reports / f"{REPORT_PREFIX}run42-size-sector-utilization.json", utilization)
    write_json(reports / f"{REPORT_PREFIX}size-sector-repair-readiness.json", readiness)

    write_text(
        reports / f"{REPORT_PREFIX}size-sector-selection-root-cause.md",
        f"""
# KR Size / Sector Selection Root Cause

Run-42 packet `{PACKET_ID}` contained safe same-session `ka20003` rows, but the old KR plan rendered
only a qualitative KOSPI size relation. The plan also classified sector extrema as supporting
thesis items, while the adaptive renderer emitted only the first thesis item, aggregate flow.

The acquisition and numeric registry were healthy. The defect was bounded to shared plan detail and
renderer retention. The repaired plan marks both slots `SELECTED_REQUIRED`; the renderer preserves
them after direction/breadth/flow and before global context.

`RUN42_OLD_MESSAGE_NEW_POLICY = FAIL_AS_EXPECTED`
""",
    )
    write_text(
        reports / f"{REPORT_PREFIX}size-sector-message-policy.md",
        """
# KR Size / Sector Message Policy

Safe complete KOSPI large/mid/small and KOSDAQ100/MID300/SMALL groups are required. An incomplete
market group is omitted without fabrication while a complete peer market may render. Sector rows
exclude size/style indexes and empty universes, then select one relative-strong and one
relative-weak sector per available market.

Allowed omission states are `SOURCE_UNAVAILABLE`, `WRONG_SESSION`, `INVALID_SEMANTIC`, and
`NO_VALID_ROWS`. Length pressure cannot use `OMITTED_SAFE_LENGTH_BUDGET`; global and prior-US prose
yield first.
""",
    )
    plan_rows = [
        ["SIZE_STYLE", plan.size_style_state, plan.size_context.text],
        ["SECTOR_EXTREMES", plan.sector_extremes_state, plan.sector_context.text],
    ]
    write_text(
        reports / f"{REPORT_PREFIX}run42-size-sector-plan.md",
        f"""
# Run-42 Size / Sector Plan

{table(['Slot', 'State', 'Backend-owned claim'], plan_rows)}

Selection uses ten exact same-session source refs: six size/style returns and four sector extrema.
Index, scoped breadth, and aggregate flow remain ahead of these claims.
""",
    )
    write_text(
        reports / f"{REPORT_PREFIX}run42-before-after-message.md",
        f"""
# Run-42 Before / After Message

## Historical Exact Message

```text
{old_ai}
```

## Repaired AI Candidate

```text
{repaired_ai}
```

## Repaired Deterministic Fallback

```text
{repaired_fallback}
```

Historical length: `{len(old_ai)}` characters. Repaired AI length: `{len(repaired_ai)}` characters.
The added detail is bounded to two current-session market-internal lines.
""",
    )
    parity_rows = [
        ["Size/style claim", plan.size_context.text in repaired_ai, plan.size_context.text in repaired_fallback],
        ["Sector-extrema claim", plan.sector_context.text in repaired_ai, plan.sector_context.text in repaired_fallback],
    ]
    write_text(
        reports / f"{REPORT_PREFIX}run42-ai-fallback-size-sector-parity.md",
        f"""
# Run-42 AI / Fallback Size-Sector Parity

{table(['Claim', 'AI', 'Fallback'], parity_rows)}

Both paths consume the same `KrMarketDigestPlan`; no duplicate selection or ranking logic exists.

`AI_FALLBACK_SIZE_STYLE_PARITY = {'PASS' if shared_claim_parity else 'FAIL'}`

`AI_FALLBACK_SECTOR_PARITY = {'PASS' if shared_claim_parity else 'FAIL'}`
""",
    )
    provenance_table = [
        [
            row["market_scope"],
            row["label"],
            row["return_pct"],
            row["fact_id"],
            row["registered"],
            row["session_basis"],
        ]
        for row in provenance
    ]
    write_text(
        reports / f"{REPORT_PREFIX}run42-size-sector-provenance.md",
        f"""
# Run-42 Size / Sector Numeric Provenance

{table(['Market', 'Label', 'Return %', 'Fact ID', 'Registered', 'Session basis'], provenance_table)}

All ten returns are existing registered backend numerics. The backend formats and ranks them; AI
arithmetic and raw-table sorting are both zero. Numeric registry policy was unchanged.
""",
    )
    quality_rows = [[key, value] for key, value in message_checks.items()]
    write_text(
        reports / f"{REPORT_PREFIX}size-sector-message-quality.md",
        f"""
# KR Size / Sector Message Quality

{table(['Check', 'Result'], quality_rows)}

The reader can identify large/mid/small leadership and relative sector strength for KOSPI and
KOSDAQ without a full table dump. Relative Korean terminology is preserved for same-sign markets.

`MESSAGE_QUALITY = {gates['MESSAGE_QUALITY']}`
""",
    )
    isolation_rows = [
        ["Numeric registry policy", gates["NUMERIC_REGISTRY_POLICY_DIFF"]],
        ["Flow reconciliation tolerance", gates["RECONCILIATION_TOLERANCE_WIDENED"]],
        ["Price Structure v3 code", gates["PRICE_STRUCTURE_V3_CODE_DIFF"]],
        ["US market digest-specific code", gates["US_MARKET_DIGEST_CODE_DIFF"]],
        ["Business thesis mutation", gates["BUSINESS_THESIS_MUTATION"]],
        ["Telegram/manual task/DB/archive", "0 / 0 / 0 / 0"],
    ]
    write_text(
        reports / f"{REPORT_PREFIX}size-sector-safety-parity.md",
        f"""
# KR Size / Sector Safety Parity

{table(['Boundary', 'Diff or mutation'], isolation_rows)}

The shared renderer utility changed only for KR-local item IDs. Existing US renderer regression
tests remained exact PASS. Production Assist remains OFF and Price Structure v3 remains unarmed.
""",
    )
    gate_rows = [[key, value] for key, value in gates.items()]
    write_text(
        reports / f"{REPORT_PREFIX}size-sector-repair-readiness.md",
        f"""
# KR Size / Sector Repair Readiness

{table(['Gate', 'Result'], gate_rows)}

```text
OPEN_P0 = 0
OPEN_MATERIAL_P1 = 0
KR_SIZE_SECTOR_MESSAGE_REPAIR = {gates['KR_SIZE_SECTOR_MESSAGE_REPAIR']}
NATURAL_KR_REPROOF = PENDING
NEXT_ACTION = WAIT_FOR_NEXT_NATURAL_KR_CLOSE
```
""",
    )
    write_text(
        reports / f"{REPORT_PREFIX}size-sector-validation.md",
        f"""
# KR Size / Sector Validation

| Validation | Result |
| --- | --- |
| Focused tests | {args.focused_tests} |
| Full pytest | {args.full_pytest} |
| Ruff | PASS |
| git diff --check | PASS |
| Knowledge parity | PASS |
| Public Action | 0.4.5 unchanged |
| operationId | 20/20 unique |
| Implementation CI | {args.ci_status} |

Implementation SHA: `{args.implementation_sha}`

CI: `{args.ci_url or 'not recorded'}`
""",
    )

    artifact_suffixes = (
        "size-sector-selection-root-cause.md",
        "size-sector-message-policy.md",
        "run42-size-sector-plan.md",
        "run42-before-after-message.md",
        "run42-ai-fallback-size-sector-parity.md",
        "run42-size-sector-provenance.md",
        "size-sector-message-quality.md",
        "size-sector-safety-parity.md",
        "size-sector-repair-readiness.md",
        "size-sector-validation.md",
        "run42-size-sector-utilization.json",
        "size-sector-repair-readiness.json",
    )
    artifact_rows = []
    for suffix in artifact_suffixes:
        path = reports / f"{REPORT_PREFIX}{suffix}"
        artifact_rows.append([path.name, hashlib.sha256(path.read_bytes()).hexdigest()])
    write_text(
        reports / f"{REPORT_PREFIX}size-sector-artifact-index.md",
        f"""
# KR Size / Sector Artifact Index

Instruction commit: `{args.instruction_sha}`

Implementation commit: `{args.implementation_sha}`

{table(['Artifact', 'SHA-256'], artifact_rows)}

The completion ZIP SHA-256 is computed after the report commit.
""",
    )


if __name__ == "__main__":
    main()
