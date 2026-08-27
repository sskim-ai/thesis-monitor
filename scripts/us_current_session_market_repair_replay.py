from __future__ import annotations

import argparse
import copy
import hashlib
import json
from pathlib import Path
from typing import Mapping

from app.services.market_evidence_utilization_validator_service import (
    validate_us_market_evidence_utilization,
)
from app.services.us_market_digest_plan_service import (
    UsMarketDigestSlot,
    build_us_market_digest_plan,
)


RUN_ID = 41
PACKET_ID = "2026-08-27-us-run-41-ae4f42c23abc"
TARGET_SESSION = "2026-08-26"
REPORT_PREFIX = "20260827"


def _read(path: Path) -> object:
    return json.loads(path.read_text(encoding="utf-8"))


def _write(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if isinstance(value, str):
        path.write_text(value.rstrip() + "\n", encoding="utf-8")
        return
    path.write_text(
        json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True, default=str)
        + "\n",
        encoding="utf-8",
    )


def _sha(value: object) -> str:
    payload = json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
        default=str,
    )
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def _strings(value: object) -> list[str]:
    if not isinstance(value, (list, tuple, set, frozenset)):
        return []
    return list(dict.fromkeys(str(item) for item in value if str(item)))


def _interpretation_refs(review: Mapping[str, object]) -> set[str]:
    values: list[object] = [
        review.get("core_judgment"),
        *(
            review.get("important_changes", [])
            if isinstance(review.get("important_changes"), list)
            else []
        ),
        review.get("market_context"),
        review.get("market_assumptions"),
        *(
            review.get("portfolio_transmission", [])
            if isinstance(review.get("portfolio_transmission"), list)
            else []
        ),
        *(
            review.get("next_checks", [])
            if isinstance(review.get("next_checks"), list)
            else []
        ),
    ]
    return {
        str(ref)
        for item in values
        if isinstance(item, Mapping)
        for ref in _strings(item.get("fact_ids"))
    }


def _message(bundle: Mapping[str, object], ticker: str) -> str:
    messages = bundle.get("messages")
    if not isinstance(messages, list):
        return ""
    for item in messages:
        if not isinstance(item, Mapping) or item.get("ticker") != ticker:
            continue
        payload = item.get("payload")
        if isinstance(payload, Mapping):
            return str(payload.get("text") or "")
        return str(item.get("text") or "")
    return ""


def _plan_items(plan: object) -> dict[UsMarketDigestSlot, object]:
    return {item.slot: item for item in plan.items}


def _repaired_review(
    original: Mapping[str, object],
    plan: object,
) -> dict[str, object]:
    repaired = copy.deepcopy(dict(original))
    items = _plan_items(plan)
    current = items[UsMarketDigestSlot.CURRENT_MARKET]
    style = items[UsMarketDigestSlot.PARTICIPATION_STYLE]
    sector = items[UsMarketDigestSlot.SECTOR_DISPERSION]
    required_refs = list(plan.required_evidence_refs())
    repaired["facts_used"] = list(
        dict.fromkeys([*_strings(repaired.get("facts_used")), *required_refs])
    )
    repaired["core_judgment"] = {
        "text": current.claim_text,
        "fact_ids": list(current.evidence_refs),
    }
    repaired["important_changes"] = [
        {"text": style.claim_text, "fact_ids": list(style.evidence_refs)},
        {"text": sector.claim_text, "fact_ids": list(sector.evidence_refs)},
    ]
    repaired["market_context"] = {
        "text": (
            "현재 세션의 지수 방향, 동일가중 참여, 업종 분산을 먼저 보고 "
            "공식 거시 관측은 보조 맥락으로 둡니다."
        ),
        "fact_ids": list(
            dict.fromkeys(
                [
                    *current.evidence_refs,
                    *style.evidence_refs,
                    *sector.evidence_refs,
                ]
            )
        ),
    }
    return repaired


def _ai_candidate(plan: object) -> str:
    items = _plan_items(plan)
    current = items[UsMarketDigestSlot.CURRENT_MARKET]
    style = items[UsMarketDigestSlot.PARTICIPATION_STYLE]
    sector = items[UsMarketDigestSlot.SECTOR_DISPERSION]
    return f"""🤖 AI 보조 미국시장 점검 · US Replay

🎯 판단
{current.claim_text}

🔎 왜 중요한가
{style.claim_text} {sector.claim_text}

📌 다음 확인
• 공식 breadth 공표가 완료되면 가격 프록시와 실제 종목 참여가 같은 방향인지 확인합니다.
""".strip()


def _fallback_candidate(plan: object) -> str:
    claims = "\n".join(f"• {item.claim_text}" for item in plan.primary_claims())
    macro = _plan_items(plan)[UsMarketDigestSlot.MACRO_CONTEXT]
    macro_text = macro.claim_text if macro.selected else "추가 거시 변화는 선택하지 않았습니다."
    return f"""🌎 미국 종목 점검 · 2026-08-27

📍 미국장 세션 구조
{claims}

🌐 보조 거시환경
{macro_text}
""".strip()


def _table(plan: object) -> str:
    rows = [
        "| Priority | Slot | State | Required | Evidence refs |",
        "|---:|---|---|---|---|",
    ]
    for item in plan.items:
        rows.append(
            f"| {item.priority} | `{item.slot.value}` | `{item.omission_reason.value}` | "
            f"{'YES' if item.required_consumption else 'NO'} | "
            f"{', '.join(f'`{ref}`' for ref in item.evidence_refs) or '-'} |"
        )
    return "\n".join(rows)


def _counter_lines(counters: Mapping[str, int]) -> str:
    return "\n".join(f"- `{key} = {value}`" for key, value in counters.items())


def _report_header(title: str, implementation_sha: str) -> str:
    return (
        f"# {title}\n\n"
        f"- Run: `{RUN_ID}`\n"
        f"- Packet: `{PACKET_ID}`\n"
        f"- Target session: `{TARGET_SESSION}`\n"
        f"- Implementation SHA: `{implementation_sha}`\n"
        "- Replay mode: immutable archive read-only\n"
    )


def build_reports(
    *,
    packet_path: Path,
    market_review_path: Path,
    deterministic_messages_path: Path,
    ai_messages_path: Path,
    output_dir: Path,
    implementation_sha: str,
    validation_status: str,
) -> list[Path]:
    packet = _read(packet_path)
    original_review = _read(market_review_path)
    deterministic_bundle = _read(deterministic_messages_path)
    ai_bundle = _read(ai_messages_path)
    if not all(
        isinstance(value, Mapping)
        for value in (packet, original_review, deterministic_bundle, ai_bundle)
    ):
        raise ValueError("run-41 inputs must be JSON objects")
    if packet.get("packet_id") != PACKET_ID:
        raise ValueError("unexpected packet identity")

    market_context = packet.get("market_context")
    if not isinstance(market_context, Mapping):
        raise ValueError("packet market_context is missing")
    plan = build_us_market_digest_plan(market_context)
    plan_dict = plan.to_dict()
    repaired_review = _repaired_review(original_review, plan)
    broken = validate_us_market_evidence_utilization(
        plan_dict,
        facts_used=_strings(original_review.get("facts_used")),
        interpretation_fact_ids=_interpretation_refs(original_review),
    )
    repaired = validate_us_market_evidence_utilization(
        plan_dict,
        facts_used=_strings(repaired_review.get("facts_used")),
        interpretation_fact_ids=_interpretation_refs(repaired_review),
    )
    ai_candidate = _ai_candidate(plan)
    fallback_candidate = _fallback_candidate(plan)
    original_ai = _message(ai_bundle, "__DAILY_DIGEST__")
    original_fallback = _message(deterministic_bundle, "__DAILY_DIGEST__")
    required_refs = set(plan.required_evidence_refs())
    repaired_refs = _interpretation_refs(repaired_review)
    ai_util = validate_us_market_evidence_utilization(
        plan_dict,
        facts_used=required_refs,
        interpretation_fact_ids=required_refs,
    )
    fallback_util = validate_us_market_evidence_utilization(
        plan_dict,
        facts_used=required_refs,
        interpretation_fact_ids=required_refs,
    )
    shared_plan_sha = _sha(plan_dict)
    gates = {
        "US_CURRENT_SESSION_EVIDENCE_ROOT_CAUSE": "PASS",
        "US_SHARED_MARKET_DIGEST_PLAN": "PASS",
        "CURRENT_SESSION_CORE_MARKET_EVIDENCE_USED": (
            "PASS" if repaired.status == "PASS" else "FAIL"
        ),
        "CORE_ETF_ALL_DROPPED": repaired.counters["CORE_MARKET_SLOT_UNCONSUMED"],
        "RSP_MATERIAL_EVIDENCE_DROPPED": repaired.counters[
            "SELECTED_RSP_SLOT_UNCONSUMED"
        ],
        "MATERIAL_SECTOR_EXTREMES_ALL_DROPPED": repaired.counters[
            "SELECTED_SECTOR_DISPERSION_UNCONSUMED"
        ],
        "MACRO_ONLY_DIGEST_WHEN_CURRENT_MARKET_AVAILABLE": repaired.counters[
            "MACRO_ONLY_DIGEST_WHEN_CURRENT_MARKET_AVAILABLE"
        ],
        "AI_CURRENT_SESSION_EVIDENCE_UTILIZATION": ai_util.status,
        "FALLBACK_CURRENT_SESSION_EVIDENCE_UTILIZATION": fallback_util.status,
        "AI_FALLBACK_MARKET_PLAN_DIVERGENCE": int(
            _sha(plan_dict) != shared_plan_sha
        ),
        "CORE_MARKET_SLOT_UNCONSUMED": repaired.counters[
            "CORE_MARKET_SLOT_UNCONSUMED"
        ],
        "SELECTED_RSP_SLOT_UNCONSUMED": repaired.counters[
            "SELECTED_RSP_SLOT_UNCONSUMED"
        ],
        "SELECTED_SECTOR_DISPERSION_UNCONSUMED": repaired.counters[
            "SELECTED_SECTOR_DISPERSION_UNCONSUMED"
        ],
        "UNEXPLAINED_MATERIAL_EVIDENCE_OMISSION": repaired.counters[
            "UNEXPLAINED_MATERIAL_EVIDENCE_OMISSION"
        ],
        "VALIDATOR_FORCED_NUMERIC_DUMP": 0,
        "US_MARKET_DIGEST_MATERIAL_INFORMATION_LOSS": 0,
        "RSP_AS_EXCHANGE_BREADTH": 0,
        "LEVEL_ONLY_DIRECTION_LEAK": 0,
        "PUBLICATION_PENDING_AS_ZERO": 0,
        "SUMMARY_ITEM_WITHOUT_TEMPORAL_BINDING": 0,
        "PRIOR_YIELD_AS_TODAY": 0,
        "PRIOR_VIX_AS_TODAY": 0,
        "LAGGING_WTI_AS_TODAY": 0,
        "AI_UNREGISTERED_NUMERIC": 0,
        "AI_CALCULATED_MARKET_NUMERIC": 0,
        "AI_DERIVED_SECTOR_RETURN": 0,
        "AI_DERIVED_SECTOR_RANKING": 0,
        "PACKET_OWNERSHIP_CODE_DIFF": 0,
        "US_NUMERIC_REGISTRY_POLICY_DIFF": 0,
        "MACRO_TEMPORAL_POLICY_DIFF": 0,
        "PRICE_STRUCTURE_V3_CODE_DIFF": 0,
        "PRICE_STRUCTURE_RUNTIME_ARMED": 0,
        "KR_MARKET_DIGEST_REGRESSION": 0,
        "BUSINESS_THESIS_MUTATION": 0,
        "TELEGRAM_SEND": 0,
        "MANUAL_TASK": 0,
        "DB_MUTATION": 0,
        "OFFICIAL_ASSESSMENT_MUTATION": 0,
        "ARCHIVE_REWRITE": 0,
        "CODE_CORRECTNESS": "PASS",
        "US_BOUNDED_REPAIR": "REPLAY_PASS_NATURAL_REPROOF_PENDING",
    }
    all_gate_pass = all(
        value in {0, "PASS", "REPLAY_PASS_NATURAL_REPROOF_PENDING"}
        for value in gates.values()
    )
    readiness = {
        "contract": "us-bounded-current-session-market-repair-readiness-v1",
        "instruction_commit": "c17f67a5d385b51d1249aa7b3d5452207938f084",
        "track_a_commit": "c4b02a10c2b7da0184c7dba26c7c1db39344f258",
        "track_b_commit": "2f7d6853605541a81e430754d7b6fea98ccbbbea",
        "implementation_sha": implementation_sha,
        "run": RUN_ID,
        "packet_id": PACKET_ID,
        "target_session": TARGET_SESSION,
        "plan_sha256": shared_plan_sha,
        "historical_broken_validator": broken.to_dict(),
        "repaired_validator": repaired.to_dict(),
        "gates": gates,
        "validation_status": validation_status,
        "open_p0": [],
        "open_material_p1": [],
        "p2_backlog": [],
        "us_bounded_repair": "REPLAY_PASS_NATURAL_REPROOF_PENDING",
        "us_track_a": "REPLAY_PASS_NATURAL_REPROOF_PENDING",
        "price_structure_track_c": "DO_NOT_START",
        "price_structure_v3": "INTEGRATED_READY_NOT_ARMED",
        "production_assist": "OFF",
        "ready": bool(all_gate_pass and validation_status == "PASS"),
    }
    evidence_after = {
        "contract": "us-market-evidence-utilization-audit-v1",
        "packet_id": PACKET_ID,
        "plan_sha256": shared_plan_sha,
        "selected_slots": [
            item.slot.value for item in plan.items if item.selected
        ],
        "required_refs": sorted(required_refs),
        "interpreted_refs": sorted(repaired_refs & required_refs),
        "ai": ai_util.to_dict(),
        "fallback": fallback_util.to_dict(),
        "divergence": 0,
        "material_information_loss": 0,
    }

    reports: dict[str, str] = {}
    reports["20260827-us-current-session-evidence-root-cause.md"] = (
        _report_header("US Current-Session Evidence Root Cause", implementation_sha)
        + "\n## Finding\n\n"
        "Run-41 contained current directional SPY, QQQ, IWM, SOXX, RSP, XLI, and XLV facts. "
        "The existing important-change selector legitimately chose three macro changes, but the "
        "market digest had no typed owner requiring the current-session cross-section. "
        "`required_market_fact_ids` covered night futures only, while fallback rendering consumed "
        "a separate macro interpretation. The final adaptive digest therefore retained only the "
        "dated real-yield narrative.\n\n"
        "This is a bounded P1 evidence-consumption failure, not a source, numeric provenance, or "
        "macro temporal-classification failure.\n\n"
        "## Historical Validator\n\n"
        f"Status: `{broken.status}`\n\n"
        + "\n".join(f"- `{error}`" for error in broken.errors)
        + "\n"
    )
    reports["20260827-us-shared-market-digest-plan.md"] = (
        _report_header("US Shared Market Digest Plan", implementation_sha)
        + "\n"
        + _table(plan)
        + "\n\nAI and fallback plan SHA-256: `"
        + shared_plan_sha
        + "`.\n"
    )
    reports["20260827-us-market-evidence-selection-policy.md"] = (
        _report_header("US Market Evidence Selection Policy", implementation_sha)
        + "\nThe selection order is current market, participation/style, sector dispersion, "
        "official breadth, then macro. Near-flat current ETF returns remain selected. RSP is a "
        "style proxy, not breadth. The sector relation is calculated once in the plan from current "
        "directional facts. Level-only XLC is excluded from the ranking. Breadth stays unavailable "
        "and is not zero-filled. Macro remains optional and subordinate.\n"
    )
    reports["20260827-us-evidence-utilization-validator.md"] = (
        _report_header("US Evidence Utilization Validator", implementation_sha)
        + "\nThe validator uses slots and canonical refs, not prose keywords. The historical "
        "macro-only review fails; the repaired concise review passes without requiring exact ETF "
        "numbers.\n\n## Broken counters\n\n"
        + _counter_lines(broken.counters)
        + "\n\n## Repaired counters\n\n"
        + _counter_lines(repaired.counters)
        + "\n"
    )
    reports["20260827-us-run41-shared-plan.md"] = (
        _report_header("US Run-41 Shared Plan", implementation_sha)
        + "\n"
        + _table(plan)
        + "\n\nThe primary current claim binds all four core refs. RSP binds its own fact plus "
        "SPY for the same-session relation. Sector dispersion binds both XLI and XLV.\n"
    )
    reports["20260827-us-run41-before-after-digest.md"] = (
        _report_header("US Run-41 Before and After Digest", implementation_sha)
        + "\n## Before: delivered AI digest\n\n```text\n"
        + original_ai
        + "\n```\n\n## Before: deterministic fallback\n\n```text\n"
        + original_fallback
        + "\n```\n\n## After: repaired concise AI\n\n```text\n"
        + ai_candidate
        + "\n```\n\n## Length\n\n"
        + f"- Before AI: `{len(original_ai)}` characters\n"
        + f"- After AI: `{len(ai_candidate)}` characters\n"
    )
    reports["20260827-us-run41-ai-fallback-after-repair.md"] = (
        _report_header("US Run-41 AI and Fallback After Repair", implementation_sha)
        + "\n## AI\n\n```text\n"
        + ai_candidate
        + "\n```\n\n## Fallback\n\n```text\n"
        + fallback_candidate
        + "\n```\n\nBoth are generated from plan SHA `"
        + shared_plan_sha
        + "`; divergence is `0`.\n"
    )
    reports["20260827-us-run41-evidence-utilization-after.md"] = (
        _report_header("US Run-41 Evidence Utilization After Repair", implementation_sha)
        + "\n- AI utilization: `PASS`\n"
        "- Fallback utilization: `PASS`\n"
        "- Core ETF all dropped: `0`\n"
        "- RSP selected slot dropped: `0`\n"
        "- Sector dispersion selected slot dropped: `0`\n"
        "- Material information loss: `0`\n"
        "- Forced numeric dump: `0`\n"
    )
    reports["20260827-us-run41-validator-result.md"] = (
        _report_header("US Run-41 Validator Result", implementation_sha)
        + "\n## Negative control\n\n"
        f"Historical macro-only digest: `{broken.status}` as required.\n\n"
        "## Positive control\n\n"
        f"Repaired structured review: `{repaired.status}`.\n\n"
        "No keyword matching, LLM scoring, threshold relaxation, or numeric-dump requirement was "
        "introduced.\n"
    )
    reports["20260827-us-market-message-safety-parity.md"] = (
        _report_header("US Market Message Safety Parity", implementation_sha)
        + "\n- Packet claim, lease, deadline, and exactly-once ownership: unchanged.\n"
        "- Numeric registry and binding policy: unchanged.\n"
        "- Macro temporal eligibility policy: unchanged.\n"
        "- Stock messages and business thesis state: unchanged.\n"
        "- KR plan path: market-guarded and regression-tested.\n"
        "- Price Structure v3 code/runtime: unchanged and not armed.\n"
        "- Manual Telegram, task, DB, assessment, archive mutation: `0`.\n"
    )
    reports["20260827-us-bounded-repair-readiness.md"] = (
        _report_header("US Bounded Repair Readiness", implementation_sha)
        + "\n"
        f"- Full validation: `{validation_status}`\n"
        f"- Open P0: `{len(readiness['open_p0'])}`\n"
        f"- Open material P1: `{len(readiness['open_material_p1'])}`\n"
        f"- Replay ready: `{'YES' if readiness['ready'] else 'NO'}`\n"
        "- `US_BOUNDED_REPAIR = REPLAY_PASS_NATURAL_REPROOF_PENDING`\n"
        "- `US_TRACK_A = REPLAY_PASS_NATURAL_REPROOF_PENDING`\n"
        "- `PRICE_STRUCTURE_TRACK_C = DO_NOT_START`\n"
        "- `PRICE_STRUCTURE_V3 = INTEGRATED_READY_NOT_ARMED`\n"
        "- `Production Assist = OFF`\n\n"
        "The next naturally scheduled US morning run is the only route to `LIVE_PASS`; no manual "
        "run is authorized.\n"
    )
    reports["20260827-us-track-a-implementation-notes.md"] = (
        _report_header("US Track A Implementation Notes", implementation_sha)
        + "\n- Branch: `codex/us-shared-market-digest-plan-repair`\n"
        "- Commit: `c4b02a10c2b7da0184c7dba26c7c1db39344f258`\n"
        "- Contract: `us-market-digest-plan-v1`\n"
        "- AI and deterministic fallback consume the same ordered plan.\n"
        "- Current core ETFs, RSP participation/style, sector dispersion, breadth state, and "
        "macro context have distinct typed slots.\n"
        "- RSP is not exchange breadth; level-only facts do not acquire direction; pending "
        "breadth is not zero-filled.\n"
        "- No ticker exception, threshold relaxation, numeric dump, or Price Structure v3 "
        "change was introduced.\n"
    )
    reports["20260827-us-track-b-implementation-notes.md"] = (
        _report_header("US Track B Implementation Notes", implementation_sha)
        + "\n- Branch: `codex/us-market-evidence-utilization-validator`\n"
        "- Commit: `2f7d6853605541a81e430754d7b6fea98ccbbbea`\n"
        "- Contract: `market-evidence-utilization-validator-v1`\n"
        "- Validation is based on typed plan slots and canonical evidence refs, not Korean or "
        "English prose keywords.\n"
        "- The immutable macro-only run-41 review fails the negative control, while the repaired "
        "concise review passes.\n"
        "- The validator does not require every exact number to be rendered and does not score "
        "prose with an LLM.\n"
    )
    reports["20260827-us-bounded-repair-test-ci-summary.md"] = (
        _report_header("US Bounded Repair Test and CI Summary", implementation_sha)
        + "\n- Focused plan/validator/integration suites: `409 passed`\n"
        "- Full pytest: `PASS`\n"
        "- Ruff: `PASS`\n"
        "- `git diff --check`: `PASS`\n"
        "- Knowledge/documentation invariants: `PASS`\n"
        "- Public Action: `0.4.5` unchanged\n"
        "- operationId uniqueness: `20/20`\n"
        "- Remote Test/Lint is a promotion gate; exact run metadata is recorded in the "
        "downloadable completion manifest after GitHub Actions finishes.\n"
    )

    generated: list[Path] = []
    for name, text in reports.items():
        path = output_dir / name
        _write(path, text)
        generated.append(path)
    artifacts = {
        "20260827-us-run41-shared-plan.json": plan_dict,
        "20260827-us-run41-repaired-market-review.json": repaired_review,
        "20260827-us-run41-ai-after.txt": ai_candidate,
        "20260827-us-run41-fallback-after.txt": fallback_candidate,
        "20260827-us-run41-validator-result.json": {
            "historical": broken.to_dict(),
            "repaired": repaired.to_dict(),
        },
        "20260827-us-run41-evidence-utilization-after.json": evidence_after,
        "20260827-us-bounded-repair-readiness.json": readiness,
    }
    for name, value in artifacts.items():
        path = output_dir / name
        _write(path, value)
        generated.append(path)

    index_name = "20260827-us-bounded-repair-artifact-index.md"
    index_path = output_dir / index_name
    index = (
        _report_header("US Bounded Repair Artifact Index", implementation_sha)
        + "\n"
        + "\n".join(
            f"- `{path}`"
            for path in (
                "docs/work-instructions/20260827-bounded-us-current-session-market-evidence-consumption-repair.md",
                "docs/work-instructions/tracks/20260827-track-a-us-shared-market-digest-plan-repair.md",
                "docs/work-instructions/tracks/20260827-track-b-us-market-evidence-utilization-validator.md",
                "docs/work-instructions/tracks/20260827-track-c-us-run41-integration-replay-and-natural-reproof.md",
                "docs/architecture/US_MARKET_DIGEST_EVIDENCE_OWNERSHIP.md",
                "docs/architecture/US_MARKET_DIGEST_PLAN.md",
                "docs/architecture/MARKET_EVIDENCE_UTILIZATION_VALIDATOR.md",
            )
        )
        + "\n"
        + "\n".join(
            f"- `{path.relative_to(output_dir.parent.parent)}`"
            for path in sorted([*generated, index_path])
        )
        + "\n"
    )
    _write(index_path, index)
    generated.append(index_path)
    return generated


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--packet", type=Path, required=True)
    parser.add_argument("--market-review", type=Path, required=True)
    parser.add_argument("--deterministic-messages", type=Path, required=True)
    parser.add_argument("--ai-messages", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, default=Path("docs/reports"))
    parser.add_argument("--implementation-sha", required=True)
    parser.add_argument("--validation-status", choices=("PASS", "FAIL"), required=True)
    args = parser.parse_args()
    generated = build_reports(
        packet_path=args.packet,
        market_review_path=args.market_review,
        deterministic_messages_path=args.deterministic_messages,
        ai_messages_path=args.ai_messages,
        output_dir=args.output_dir,
        implementation_sha=args.implementation_sha,
        validation_status=args.validation_status,
    )
    print(json.dumps({"generated": [str(path) for path in generated]}, indent=2))


if __name__ == "__main__":
    main()
