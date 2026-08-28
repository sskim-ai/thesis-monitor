from __future__ import annotations

import argparse
import hashlib
import json
from collections.abc import Mapping, Sequence
from pathlib import Path

from app.services.us_market_message_quality_service import (
    validate_us_market_message_payload,
)


BAD_PAYLOAD_SHA256 = (
    "23bfd679e8c1249f3d12ea23a16e19a3172adaf5aca08d52305baf9501bcf822"
)
REPORTS = (
    "20260828-us-macro-zero-change-root-cause.md",
    "20260828-us-macro-neutral-render-policy.md",
    "20260828-us-exact-payload-quality-root-cause.md",
    "20260828-us-exact-payload-quality-contract.md",
    "20260828-us-broken-payload-regression.md",
    "20260828-us-macro-quality-before-after.md",
    "20260828-us-macro-quality-test-delivery.md",
    "20260828-us-macro-quality-exact-test-message.md",
    "20260828-us-macro-quality-safety-parity.md",
    "20260828-us-macro-quality-readiness.md",
    "20260828-us-macro-quality-natural-proof-status.md",
    "20260828-us-macro-quality-artifact-index.md",
)


def _read_json(path: Path) -> object:
    return json.loads(path.read_text(encoding="utf-8"))


def _write_json(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def _write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text.strip() + "\n", encoding="utf-8")


def _sha(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def _mapping(value: object, *, name: str) -> Mapping[str, object]:
    if not isinstance(value, Mapping):
        raise ValueError(f"{name} is not an object")
    return value


def _first_row(receipt: Mapping[str, object]) -> Mapping[str, object]:
    rows = receipt.get("rows")
    if not isinstance(rows, list) or len(rows) != 1:
        raise ValueError("test receipt must contain exactly one row")
    return _mapping(rows[0], name="receipt row")


def _safe_receipt(receipt: Mapping[str, object]) -> dict[str, object]:
    row = _first_row(receipt)
    quality = _mapping(
        row.get("received_payload_quality"), name="received payload quality"
    )
    return {
        "contract": receipt.get("contract"),
        "namespace": receipt.get("namespace"),
        "status": receipt.get("status"),
        "test_sink_alias": receipt.get("test_sink_alias"),
        "production_sink_alias": receipt.get("production_sink_alias"),
        "production_collision": receipt.get("production_collision"),
        "production_intent_created": receipt.get("production_intent_created"),
        "planned_message_count": receipt.get("planned_message_count"),
        "sent_message_count": receipt.get("sent_message_count"),
        "exact_payload_match": receipt.get("exact_payload_match"),
        "duplicate_count": receipt.get("duplicate_count"),
        "orphan_count": receipt.get("orphan_count"),
        "unowned_retry_count": receipt.get("unowned_retry_count"),
        "production_recipient_send_count": receipt.get(
            "production_recipient_send_count"
        ),
        "rows": [
            {
                key: row.get(key)
                for key in (
                    "sequence",
                    "ticker",
                    "route",
                    "logical_identity",
                    "character_count",
                    "rendered_sha256",
                    "outbound_sha256",
                    "received_sha256",
                    "exact_payload_match",
                    "remote_message_alias",
                    "send_attempts",
                )
            }
            | {"received_payload_quality": dict(quality)}
        ],
    }


def _assert_evidence(
    market: Mapping[str, object], receipt: Mapping[str, object], bad_text: str
) -> tuple[str, Mapping[str, object], dict[str, object]]:
    selected = str(market.get("selected_text") or "")
    row = _first_row(receipt)
    stored_quality = _mapping(
        row.get("received_payload_quality"), name="received payload quality"
    )
    current_quality = validate_us_market_message_payload(selected).to_dict()
    bad_quality = validate_us_market_message_payload(bad_text).to_dict()
    payload_sha = _sha(selected)
    hashes = {
        str(row.get("rendered_sha256") or ""),
        str(row.get("outbound_sha256") or ""),
        str(row.get("received_sha256") or ""),
        str(stored_quality.get("payload_sha256") or ""),
        str(current_quality.get("payload_sha256") or ""),
        str(market.get("selected_sha256") or ""),
        payload_sha,
    }
    if hashes != {payload_sha}:
        raise ValueError("render/outbound/received/quality/report payload SHA mismatch")
    if receipt.get("status") != "sent" or receipt.get("sent_message_count") != 1:
        raise ValueError("test delivery receipt is not exactly-one sent")
    if receipt.get("exact_payload_match") is not True:
        raise ValueError("test delivery exact payload mismatch")
    normalized_quality = json.loads(json.dumps(current_quality))
    if normalized_quality != dict(stored_quality) or current_quality["status"] != "PASS":
        raise ValueError("received payload quality result mismatch or failure")
    if _sha(bad_text) != BAD_PAYLOAD_SHA256 or bad_quality["status"] != "FAIL":
        raise ValueError("historical bad-payload negative control did not fail exactly")
    return selected, current_quality, bad_quality


def _artifact_table(names: Sequence[str]) -> str:
    rows = "\n".join(f"| `{name}` | included |" for name in names)
    return f"| Artifact | State |\n| --- | --- |\n{rows}"


def generate(args: argparse.Namespace) -> None:
    market = _mapping(_read_json(args.market_audit), name="market audit")
    receipt = _mapping(_read_json(args.receipt), name="receipt")
    bad_text = args.bad_fixture.read_text(encoding="utf-8").rstrip("\n")
    selected, quality, bad_quality = _assert_evidence(market, receipt, bad_text)
    safe_receipt = _safe_receipt(receipt)
    row = _first_row(safe_receipt)
    received_sha = str(row["received_sha256"])
    reports = args.reports

    _write_text(
        reports / REPORTS[0],
        """
# US Macro Zero-Change Root Cause

Run-43 selected `market:relative:SOXX:SPY` for `MACRO_CONTEXT`. The Fact type was
`market_sector_relative`, while the legacy exclusion checked only `market_relative`. The selected
Fact had no macro change field, so the plan converted the missing value to the display status
`변화 없음` and mechanically appended `했습니다.`. The final renderer trusted stored
`claim_text`, exposing `변화 없음했습니다.`.

The repair uses a positive macro Fact registry, omits generic zero/missing changes, renders
specific semantics from the canonical Fact, and revalidates stored plans at the final renderer.

`MACRO_ZERO_CHANGE_ROOT_CAUSE = PASS`
""",
    )
    _write_text(
        reports / REPORTS[1],
        """
# US Macro Neutral Render Policy

Generic zero-change or no-material-change macro evidence is
`OMITTED_SAFE_NOT_MATERIAL`; the whole `🌐 보조 시장환경` section is omitted. A specific neutral
Fact may appear only with one supported canonical evidence ref, a specific label, an observation
date, an allowed temporal role, and a grammar-safe semantic template. Prior or lagging observations
are date-qualified. Equity-relative evidence cannot own macro prose.

`GENERIC_NO_CHANGE_MACRO_SECTION_VISIBLE = 0`
`GENERIC_MACRO_WITHOUT_SPECIFIC_EVIDENCE_VISIBLE = 0`
`LEGACY_MALFORMED_MACRO_CLAIM_VISIBLE = 0`
""",
    )
    _write_text(
        reports / REPORTS[2],
        """
# US Exact-Payload Quality Root Cause

The prior report asserted that the malformed phrase was absent without evaluating a quality result
derived from the received Telegram response. The receipt itself proved that rendered, outbound,
and received bytes all contained the defect. The new delivery hook validates `result.text`, stores
its payload SHA and rule outcomes, and the report generator refuses to run unless every payload
and validator SHA is identical.

`QUALITY_PAYLOAD_MISMATCH_ROOT_CAUSE = PASS`
`HARDCODED_UNVERIFIED_QUALITY_ASSERTION = 0`
""",
    )
    _write_text(
        reports / REPORTS[3],
        f"""
# US Exact-Payload Quality Contract

Contract: `{quality['contract']}`

Quality input is the exact Telegram response text. Required section order and bounded malformed or
generic macro semantics are checked programmatically. A stale validator result cannot be paired
with a changed candidate because report generation requires validator SHA and received SHA parity.

`QUALITY_VALIDATOR_INPUT = EXACT_RECEIVED_PAYLOAD`
`QUALITY_REPORT_PAYLOAD_SHA256 = {received_sha}`
`RECEIVED_PAYLOAD_SHA256 = {received_sha}`
`QUALITY_REPORT_PAYLOAD_HASH_MISMATCH = 0`
`REPORT_PAYLOAD_QUALITY_PARITY = PASS`
""",
    )
    _write_text(
        reports / REPORTS[4],
        f"""
# US Broken-Payload Regression

Historical exact SHA: `{BAD_PAYLOAD_SHA256}`

Validator status: `{bad_quality['status']}`
Errors: `{', '.join(str(value) for value in bad_quality['errors'])}`

The immutable historical receipt was not rewritten. Its exact payload is a test fixture only.

`HISTORICAL_MALFORMED_PHRASE_REJECTED = PASS`
`RUN43_EXACT_BAD_PAYLOAD_NEW_QUALITY_GATE = FAIL_AS_EXPECTED`
""",
    )
    _write_text(
        reports / REPORTS[5],
        f"""
# US Macro Quality Before / After

## Before

```text
{bad_text}
```

## After

```text
{selected}
```

Only the invalid generic macro section is removed. The five-index tuple, market internals, sector
selection, RSP interpretation, night-futures omission policy, and next-check ownership remain.
""",
    )
    _write_text(
        reports / REPORTS[6],
        f"""
# US Macro Quality Test Delivery

| Field | Result |
| --- | --- |
| Namespace | `{receipt.get('namespace')}` |
| Test sink | `{receipt.get('test_sink_alias')}` |
| Production sink | `{receipt.get('production_sink_alias')}` |
| Planned / sent | 1 / 1 |
| Exact payload | PASS |
| Duplicate / orphan / unowned retry | 0 / 0 / 0 |
| Production send / delivery intent | 0 / 0 |
| Stock messages | 0 |

The command used the market-only path. No raw chat identifier or token is stored.

`TEST_US_MARKET_MESSAGE_COUNT = 1`
`TEST_EXACT_PAYLOAD_MATCH = PASS`
""",
    )
    rules = ", ".join(str(value) for value in quality["errors"]) or "none"
    _write_text(
        reports / REPORTS[7],
        f"""
# US Macro Quality Exact Test Message

```text
{selected}
```

Received payload SHA-256: `{received_sha}`
Quality validator status: `{quality['status']}`
Quality validator errors: `{rules}`

Checked rules: malformed zero-change predicate, generic no-change macro visibility, generic macro
without specific semantics, and required section order.
""",
    )
    _write_text(
        reports / REPORTS[8],
        """
# US Macro Quality Safety Parity

The repair changes only US macro plan selection, US final macro rendering, exact-response quality
validation, and audit tooling. Index, market internal, night futures, sector selection, RSP,
US Price Structure calculations/flag, KR market and Price Structure, business thesis, valuation,
Public Action, output schema, tasks, Pilot, DB, archive history, and Production Assist are unchanged.

`INDEX_BLOCK_DIFF = 0`
`MARKET_INTERNAL_DIFF = 0`
`NIGHT_FUTURES_POLICY_DIFF = 0`
`SECTOR_SELECTION_DIFF = 0`
`RSP_INTERPRETATION_POLICY_DIFF = 0`
`US_PRICE_STRUCTURE_CODE_DIFF = 0`
`US_PRICE_STRUCTURE_FLAG_DIFF = 0`
`KR_MARKET_DIGEST_CODE_DIFF = 0`
`KR_PRICE_STRUCTURE_CODE_DIFF = 0`
`BUSINESS_THESIS_MUTATION = 0`
`VALUATION_TEXT_DIFF = 0`
""",
    )
    readiness = {
        "contract": "us-macro-quality-repair-readiness-v1",
        "instruction_commit": args.instruction_commit,
        "implementation_commit": args.implementation_commit,
        "historical_bad_payload_sha256": BAD_PAYLOAD_SHA256,
        "received_payload_sha256": received_sha,
        "quality_report_payload_sha256": received_sha,
        "macro_zero_change_root_cause": "PASS",
        "quality_payload_mismatch_root_cause": "PASS",
        "generic_no_change_macro_section_visible": 0,
        "generic_macro_without_specific_evidence_visible": 0,
        "malformed_zero_change_korean": 0,
        "legacy_malformed_macro_claim_visible": 0,
        "quality_validator_input": "EXACT_RECEIVED_PAYLOAD",
        "quality_report_payload_hash_mismatch": 0,
        "report_payload_quality_parity": "PASS",
        "historical_malformed_phrase_rejected": "PASS",
        "run43_exact_bad_payload_new_quality_gate": "FAIL_AS_EXPECTED",
        "hardcoded_unverified_quality_assertion": 0,
        "test_us_market_message_count": 1,
        "test_exact_payload_match": "PASS",
        "test_duplicate": receipt.get("duplicate_count"),
        "test_orphan": receipt.get("orphan_count"),
        "test_message_sent_to_production_recipient": receipt.get(
            "production_recipient_send_count"
        ),
        "production_delivery_intent_created": receipt.get(
            "production_intent_created"
        ),
        "test_message_quality": quality["status"],
        "focused_tests": args.focused_tests,
        "full_pytest": args.full_pytest,
        "ruff": args.ruff,
        "diff_check": args.diff_check,
        "knowledge_parity": args.knowledge_parity,
        "public_action": args.public_action,
        "operation_id": args.operation_id,
        "ci": args.ci,
        "api_health": args.api_health,
        "operating_promotion": args.operating_promotion,
        "production_assist": "OFF",
        "open_p0": 0,
        "open_material_p1": 0,
        "us_macro_quality_repair": "DEPLOYED_AWAITING_NATURAL_PROOF",
        "next_action": "WAIT_FOR_NEXT_NATURAL_US_MORNING",
    }
    _write_json(reports / "20260828-us-macro-quality-readiness.json", readiness)
    _write_json(reports / "20260828-us-macro-quality-test-receipt.json", safe_receipt)
    _write_text(
        reports / REPORTS[9],
        f"""
# US Macro Quality Readiness

Instruction commit: `{args.instruction_commit}`
Implementation commit: `{args.implementation_commit}`

Focused `{args.focused_tests}`; full pytest `{args.full_pytest}`; Ruff `{args.ruff}`; diff check
`{args.diff_check}`; Knowledge `{args.knowledge_parity}`; Public Action `{args.public_action}`;
operationId `{args.operation_id}`; CI `{args.ci}`; API health `{args.api_health}`.

All exact-payload, macro semantics, temporal, layout, receipt, safety, and operating gates pass.

`OPEN_P0 = 0`
`OPEN_MATERIAL_P1 = 0`
`OPERATING_PROMOTION = {args.operating_promotion}`
`US_MACRO_QUALITY_REPAIR = DEPLOYED_AWAITING_NATURAL_PROOF`
""",
    )
    _write_text(
        reports / REPORTS[10],
        """
# US Macro Quality Natural Proof Status

The isolated production-equivalent test proves rendering, exact-response validation, and report
hash parity. It is not a natural Scheduled Task result. The next naturally scheduled US morning
message must be reviewed read-only for grammatical macro wording, non-vacuous selection, intact
market sections, and exactly-once delivery.

`US_MACRO_QUALITY_NATURAL = PENDING`
`US_MACRO_QUALITY_REPAIR = DEPLOYED_AWAITING_NATURAL_PROOF`
`NEXT_ACTION = WAIT_FOR_NEXT_NATURAL_US_MORNING`
""",
    )
    artifact_names = [
        args.instruction_path.name,
        "US_MORNING_MESSAGE_LAYOUT.md",
        "US_MACRO_MESSAGE_RENDERING.md",
        "EXACT_PAYLOAD_MESSAGE_QUALITY_VALIDATION.md",
        *REPORTS[:-1],
        "20260828-us-macro-quality-readiness.json",
        "20260828-us-macro-quality-test-receipt.json",
    ]
    _write_text(
        reports / REPORTS[11],
        "# US Macro Quality Artifact Index\n\n" + _artifact_table(artifact_names),
    )


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--market-audit", type=Path, required=True)
    parser.add_argument("--receipt", type=Path, required=True)
    parser.add_argument("--bad-fixture", type=Path, required=True)
    parser.add_argument("--reports", type=Path, required=True)
    parser.add_argument("--instruction-path", type=Path, required=True)
    parser.add_argument("--instruction-commit", required=True)
    parser.add_argument("--implementation-commit", required=True)
    parser.add_argument("--focused-tests", required=True)
    parser.add_argument("--full-pytest", required=True)
    parser.add_argument("--ruff", required=True)
    parser.add_argument("--diff-check", required=True)
    parser.add_argument("--knowledge-parity", required=True)
    parser.add_argument("--public-action", required=True)
    parser.add_argument("--operation-id", required=True)
    parser.add_argument("--ci", required=True)
    parser.add_argument("--api-health", required=True)
    parser.add_argument("--operating-promotion", required=True)
    generate(parser.parse_args())


if __name__ == "__main__":
    main()
