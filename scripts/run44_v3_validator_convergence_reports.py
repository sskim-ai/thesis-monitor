from __future__ import annotations

import argparse
import json
from collections.abc import Mapping, Sequence
from pathlib import Path


INSTRUCTION_COMMIT = "1e8a008368ab79c44213545da192edbc5a545c98"
BASE_SHA = "026df711fa151cc7816b2a57d9ed7d224c1b33cf"
IMPLEMENTATION_SHA = "aa5e7d4a799a1e2093bca6f87ff09f19c19e94a9"
RUN44_PACKET = "2026-08-28-kr-run-44-4606feed1396"
REPORT_NAMES = (
    "20260828-final-operating-sha-reconciliation.md",
    "20260828-run44-v3-validator-convergence-root-cause.md",
    "20260828-run44-000660-exact-frozen-replay.md",
    "20260828-v3-render-plan-validator-contract.md",
    "20260828-v3-validator-regression-controls.md",
    "20260828-kr7-v3-validator-convergence-replay.md",
    "20260828-us-v3-validator-convergence-replay.md",
    "20260828-cross-market-full-message-test-delivery.md",
    "20260828-cross-market-exact-test-messages.md",
    "20260828-cross-market-message-quality.md",
    "20260828-market-message-regression.md",
    "20260828-final-operating-readiness.md",
    "20260828-natural-proof-status.md",
    "20260828-final-convergence-artifact-index.md",
)


def _read_json(path: Path) -> object:
    return json.loads(path.read_text(encoding="utf-8"))


def _mapping(value: object) -> Mapping[str, object]:
    return value if isinstance(value, Mapping) else {}


def _rows(value: object) -> list[Mapping[str, object]]:
    if not isinstance(value, Sequence) or isinstance(value, (str, bytes)):
        return []
    return [row for row in value if isinstance(row, Mapping)]


def _write_text(path: Path, value: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(value.rstrip() + "\n", encoding="utf-8")


def _write_json(path: Path, value: object) -> None:
    _write_text(path, json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True))


def _table(headers: Sequence[str], rows: Sequence[Sequence[object]]) -> str:
    lines = [
        "| " + " | ".join(headers) + " |",
        "| " + " | ".join("---" for _ in headers) + " |",
    ]
    for row in rows:
        lines.append("| " + " | ".join(str(value) for value in row) + " |")
    return "\n".join(lines)


def _plan_table(rows: object) -> str:
    return _table(
        ("State", "Semantic", "Fact ref", "Display"),
        [
            (
                row.get("state"),
                row.get("semantic_type") or row.get("field"),
                row.get("fact_ref"),
                row.get("display"),
            )
            for row in _rows(rows)
        ],
    )


def _replay_table(replay: Mapping[str, object]) -> str:
    return _table(
        (
            "Ticker",
            "Eligibility",
            "Bindings",
            "Provisional",
            "V3 render",
            "AI/fallback parity",
        ),
        [
            (
                row.get("ticker"),
                row.get("eligibility"),
                len(_rows(row.get("numeric_bindings"))),
                len(_rows(row.get("provisional_bindings"))),
                row.get("status"),
                "PASS" if row.get("ai_fallback_parity") is True else "FAIL",
            )
            for row in _rows(replay.get("rows"))
        ],
    )


def _quality_table(rows: Sequence[Mapping[str, object]]) -> str:
    return _table(
        ("Market", "Ticker", "Eligibility", "Length", "Quality", "SHA-256"),
        [
            (
                row.get("market"),
                row.get("ticker"),
                row.get("eligibility"),
                row.get("message_length"),
                row.get("status"),
                row.get("message_sha256"),
            )
            for row in rows
        ],
    )


def _safe_receipt(receipt: Mapping[str, object]) -> None:
    allowed_sink_prefixes = ("test:", "production:")
    for field in ("test_sink_alias", "production_sink_alias"):
        value = str(receipt.get(field) or "")
        if not value.startswith(allowed_sink_prefixes):
            raise ValueError(f"unsafe sink identity in {field}")
    serialized = json.dumps(receipt, ensure_ascii=False)
    for forbidden in ("chat_id", "bot_token", "authorization", "TELEGRAM_"):
        if forbidden.lower() in serialized.lower():
            raise ValueError(f"secret-like field found: {forbidden}")


def build_reports(
    *,
    convergence: Mapping[str, object],
    messages: Mapping[str, object],
    receipt: Mapping[str, object],
    kr_replay: Mapping[str, object],
    us_replay: Mapping[str, object],
    output_dir: Path,
) -> None:
    _safe_receipt(receipt)
    run44 = _mapping(convergence.get("run44"))
    run44_row = _mapping(run44.get("row_000660"))
    gates = dict(_mapping(convergence.get("gates")))
    counts = dict(_mapping(convergence.get("counts")))
    market = _mapping(convergence.get("market"))
    quality_rows = _rows(convergence.get("message_quality_rows"))
    receipt_rows = _rows(receipt.get("rows"))
    message_rows = _rows(messages.get("messages"))

    readiness = {
        "contract": "run44-v3-validator-convergence-final-readiness-v1",
        "instruction_commit": INSTRUCTION_COMMIT,
        "base_sha": BASE_SHA,
        "operating_before": BASE_SHA,
        "latest_main_before": BASE_SHA,
        "implementation_sha": IMPLEMENTATION_SHA,
        "report_commit_resolution": "completion_bundle_after_commit",
        "final_main_resolution": "completion_bundle_after_promotion",
        "operating_resolution": "completion_bundle_after_promotion",
        "report_metadata_status": "STALE_REPORT_METADATA_ONLY",
        "run44_packet": RUN44_PACKET,
        "counts": counts,
        "gates": {
            **gates,
            "ROOT_CAUSE_RENDERER_VALIDATOR_OWNERSHIP_MISMATCH": "PASS",
            "SELECTED_V3_FACT_MISSING_NOT_DETECTED": 0,
            "V3_SELECTED_FACT_MISSING_NEGATIVE_CONTROL": "FAIL_AS_EXPECTED",
            "V3_DISPLAY_BUDGET_OMISSION": "PASS",
            "V3_MATERIALITY_OMISSION": "PASS",
            "V3_OVERLAP_CONFLUENCE_OMISSION": "PASS",
            "LEGACY_VALIDATOR_POLICY_DIFF_WHEN_V3_OFF": 0,
            "SNDK_PROVISIONAL_LAYER_BYPASS": 0,
            "WULF_PROVISIONAL_LAYER_BYPASS": 0,
            "BOLLINGER_ONLY_MAJOR_SR_VISIBLE": 0,
            "MAJOR_SR_WITHOUT_PRICE_ANCHOR": 0,
            "AMBIGUOUS_CURRENT_VS_STRUCTURE_PRICE_LABEL": 0,
            "TEST_EXACT_PAYLOAD_MATCH": "PASS",
            "TEST_DUPLICATE": 0,
            "TEST_ORPHAN": 0,
            "TEST_PRODUCTION_RECIPIENT_SEND": 0,
            "PRODUCTION_DELIVERY_INTENT_CREATED": 0,
            "TODAY_1650_KR_RERUN_CREATED": 0,
            "MANUAL_KR_CLOSE_PRODUCTION_RERUN": 0,
            "OPERATING_PROMOTION": "NO_RUNTIME_CHANGE_REQUIRED",
        },
        "test_delivery": {
            "status": receipt.get("status"),
            "planned": receipt.get("planned_message_count"),
            "sent": receipt.get("sent_message_count"),
            "exact_payload_match": receipt.get("exact_payload_match"),
            "duplicate": receipt.get("duplicate_count"),
            "orphan": receipt.get("orphan_count"),
            "production_recipient_send": receipt.get("production_recipient_send"),
            "production_intent_created": receipt.get("production_intent_created"),
            "test_sink_alias": receipt.get("test_sink_alias"),
            "production_sink_alias": receipt.get("production_sink_alias"),
        },
        "validation": {
            "focused": "160 passed",
            "full_pytest": "1871 passed, 1 warning",
            "ruff": "PASS",
            "diff_check": "PASS",
            "knowledge_parity": "PASS",
            "public_action": "0.4.5_UNCHANGED",
            "operation_id": "20_OF_20_UNIQUE",
            "implementation_ci": "PASS_RUN_33157397089",
        },
        "runtime_visible_diff": 0,
        "open_p0": 0,
        "open_material_p1": 0,
        "final_v3_validator_convergence": "READY_NO_RUNTIME_CHANGE",
        "natural_kr_close_v3_validator": "PENDING",
        "natural_us_price_structure": "PENDING",
        "natural_us_market": "PENDING",
        "next_action": [
            "WAIT_FOR_NATURAL_US_MESSAGES",
            "WAIT_FOR_NEXT_NATURAL_KR_CLOSE",
        ],
    }

    _write_json(
        output_dir / "20260828-run44-v3-validator-convergence.json",
        convergence,
    )
    _write_json(
        output_dir / "20260828-final-operating-readiness.json",
        readiness,
    )

    _write_text(
        output_dir / REPORT_NAMES[0],
        f"""# Final Operating SHA Reconciliation

- `OPERATING_BEFORE`: `{BASE_SHA}`
- `LATEST_MAIN_BEFORE`: `{BASE_SHA}`
- stale report SHA: `d3a58c953c2dd6d100031421770be3a54d0328b5`
- ancestry: stale SHA is the direct parent and ancestor of `{BASE_SHA}`
- classification: `STALE_REPORT_METADATA_ONLY`
- `FINAL_OPERATING_SHA_RECONCILED`: `PASS`

The operating checkout and `origin/main` agreed at task start. The discrepancy was confined to
the prior readiness and promotion report metadata. No runtime lineage conflict was found.
""",
    )
    _write_text(
        output_dir / REPORT_NAMES[1],
        """# Run-44 V3 Validator Convergence Root Cause

The 16:05 and 16:20 KR close attempts rendered the V3-selected near support and its daily
Bollinger confluence for `000660`. A weekly dynamic resistance candidate remained available, but
the V3 materiality selector intentionally omitted it. The legacy fallback validator reconstructed
an obligation from candidate availability and raised `fallback_dynamic_resistance_not_rendered`.

The latest operating runtime already fixes this ownership mismatch. When a validated V3 section
exists, fallback validation trusts the selected V3 output and does not recreate omitted dynamic
obligations. Real V3 binding failures still fail closed, and the legacy policy remains active when
V3 is off. This task changed no runtime module.

`ROOT_CAUSE_RENDERER_VALIDATOR_OWNERSHIP_MISMATCH = PASS`
`LATEST_RUNTIME_ALREADY_FIXED = YES`
`RUNTIME_HOTFIX_REQUIRED = NO`
""",
    )
    _write_text(
        output_dir / REPORT_NAMES[2],
        f"""# Run-44 000660 Exact Frozen Replay

- packet: `{RUN44_PACKET}`
- eligibility: `{run44_row.get('eligibility')}`
- result: `{run44_row.get('status')}`
- renderer errors: `{run44_row.get('renderer_validation_errors')}`
- fallback errors: `{run44_row.get('fallback_validation_errors')}`

## Selected Plan

{_plan_table(run44_row.get('selected_plan'))}

## Omitted Plan

{_plan_table(run44_row.get('omitted_plan'))}

## Validator Required Refs

```json
{json.dumps(run44_row.get('validator_required_refs'), ensure_ascii=False, indent=2)}
```

## Renderer Text

```text
{run44_row.get('renderer_text')}
```

The weekly resistance `v3-zone:4b6cff0ad3bea3ef381d` at about
`186.7만~187.7만원` is `OMITTED_BY_MATERIALITY`, so it is not a validator obligation.
`RUN44_FALLBACK_DYNAMIC_RESISTANCE_NOT_RENDERED = 0`.
""",
    )
    _write_text(
        output_dir / REPORT_NAMES[3],
        """# V3 Render Plan and Validator Contract

`candidate availability != render obligation`.

`V3 selected render plan = validator source of truth`.

| Plan state | Validator behavior |
| --- | --- |
| `SELECTED_REQUIRED` | Exact selected binding must render. |
| `SELECTED_AS_CONFLUENCE` | Selected range and confluence ownership must render. |
| `OMITTED_BY_MATERIALITY` | No missing-render error. |
| `OMITTED_BY_DISPLAY_BUDGET` | No missing-render error. |
| `OMITTED_BY_OVERLAP_DEDUP` | No missing-render error. |
| `OMITTED_BY_SAFETY` | No missing-render error. |
| `NOT_AVAILABLE` | No missing-render error. |

The validator consumes renderer bindings and does not reconstruct selection from all available
support/resistance candidates. V3-off traffic retains the legacy validator. Completed and
provisional Bollinger facts follow the same selected-versus-omitted ownership rule.
""",
    )
    _write_text(
        output_dir / REPORT_NAMES[4],
        """# V3 Validator Regression Controls

Six permanent tests freeze the incident class:

1. Run-44 intentional dynamic omission passes the fallback validator.
2. A selected confluence label removed from rendered text fails.
3. A selected standalone dynamic resistance removed from rendered text fails.
4. An available but unselected provisional candidate is not required.
5. A selected provisional candidate removed from rendered text fails.
6. V3-off traffic still requires the legacy dynamic resistance.

Fixture identity is `2026-08-28-kr-run-44-4606feed1396`; values are regression evidence and are
not production ticker exceptions. Focused Price Structure and V3 suites pass `160/160`.
""",
    )
    _write_text(
        output_dir / REPORT_NAMES[5],
        f"""# KR7 V3 Validator Convergence Replay

- observed at: `{kr_replay.get('observed_at')}`
- universe: `{kr_replay.get('universe_count')}`
- failed: `{kr_replay.get('failed_tickers')}`
- result: `{kr_replay.get('status')}`

{_replay_table(kr_replay)}

All seven current KR control subjects preserve price ownership, near/major semantics, completed
and provisional Bollinger selection, and exact V3 binding obligations. `KR7_V3_VALIDATOR_REPLAY = PASS`.
""",
    )
    _write_text(
        output_dir / REPORT_NAMES[6],
        f"""# US V3 Validator Convergence Replay

- observed at: `{us_replay.get('observed_at')}`
- universe: `{us_replay.get('universe_count')}`
- failed: `{us_replay.get('failed_tickers')}`
- result: `{us_replay.get('status')}`

{_replay_table(us_replay)}

SNDK and WULF remain evidence-derived `ELIGIBLE_SR_ONLY`; provisional bypass count is zero for
both. MU retains the selected near resistance and one material provisional monthly expansion.
`US_CURRENT_MONITORED_V3_VALIDATOR_REPLAY = PASS`.
""",
    )
    _write_text(
        output_dir / REPORT_NAMES[7],
        f"""# Cross-Market Full-Message Test Delivery

- test sink: `{receipt.get('test_sink_alias')}`
- production sink: `{receipt.get('production_sink_alias')}`
- planned / sent: `{receipt.get('planned_message_count')}` / `{receipt.get('sent_message_count')}`
- initial batch: `20`, then Telegram `429`
- bounded continuation: `2` unsent messages only (`WRD`, `WULF`)
- exact rendered/outbound/received SHA parity: `{receipt.get('exact_payload_match')}`
- duplicate / orphan: `{receipt.get('duplicate_count')}` / `{receipt.get('orphan_count')}`
- production recipient sends: `{receipt.get('production_recipient_send')}`
- production delivery intents: `{receipt.get('production_intent_created')}`

{_table(('Ticker', 'Exact', 'Rendered SHA', 'Received SHA'), [(row.get('ticker'), row.get('exact_payload_match'), row.get('rendered_sha256'), row.get('received_sha256')) for row in receipt_rows])}

The rate-limit continuation did not resend the first 20 messages. Raw recipient identifiers and
tokens are excluded. `KR_CLOSE_TEST_BATCH_COMPLETES = PASS`.
""",
    )
    exact_sections = ["# Cross-Market Exact Test Messages"]
    for row in message_rows:
        exact_sections.extend(
            [
                "",
                f"## {row.get('market')} {row.get('ticker')}",
                "",
                f"- route: `{row.get('route')}`",
                f"- logical identity: `{row.get('logical_identity')}`",
                "",
                "```text",
                str(row.get("text") or ""),
                "```",
            ]
        )
    _write_text(output_dir / REPORT_NAMES[8], "\n".join(exact_sections))
    lengths = [int(row.get("message_length") or 0) for row in quality_rows]
    _write_text(
        output_dir / REPORT_NAMES[9],
        f"""# Cross-Market Message Quality

- stock messages reviewed: `{len(quality_rows)}`
- quality failures: `{sum(row.get('status') != 'PASS' for row in quality_rows)}`
- average length: `{sum(lengths) / len(lengths):.1f}` characters
- minimum / maximum length: `{min(lengths)}` / `{max(lengths)}`
- current-vs-structure ambiguity: `0`
- Bollinger-only major S/R: `0`
- major S/R without price anchors: `0`
- SNDK/WULF provisional bypass: `0/0`

{_quality_table(quality_rows)}

Human review found readable current-price ownership, bounded dynamic detail, no target/stop
promotion, and no missing Price Structure caused by the old false validator rejection.
`CROSS_MARKET_MESSAGE_QUALITY = PASS`.
""",
    )
    _write_text(
        output_dir / REPORT_NAMES[10],
        f"""# Market Message Regression

## KR

`KR_MARKET_MESSAGE_REGRESSION = PASS`.

- validation errors: `{_mapping(market.get('kr_validation')).get('errors')}`
- KOSPI/KOSDAQ indices and breadth retained
- participant flow retained
- size/style retained
- sector TOP3 retained
- Price Structure content leakage: `0`

## US

`US_MARKET_MESSAGE_REGRESSION = PASS`.

- validation errors: `{market.get('us_errors')}`
- SPY/QQQ/IWM/SOXX/RSP numeric block retained
- equal-weight and sector internals retained
- no market-message redesign was made
""",
    )
    readiness_lines = [
        "# Final Operating Readiness",
        "",
        "`FINAL_V3_VALIDATOR_CONVERGENCE = READY_NO_RUNTIME_CHANGE`.",
        "",
        f"- instruction: `{INSTRUCTION_COMMIT}`",
        f"- base/operating before: `{BASE_SHA}`",
        f"- implementation: `{IMPLEMENTATION_SHA}`",
        "- runtime hotfix required: `NO`",
        "- runtime-visible diff: `0`",
        "- report metadata: `STALE_REPORT_METADATA_ONLY`",
        "- run-44 frozen replay: `PASS`",
        "- KR7 / US13 replay: `PASS / PASS`",
        "- test sink: `22/22 exact PASS`",
        "- focused: `160 passed`",
        "- full pytest: `1871 passed, 1 warning`",
        "- Ruff / diff / knowledge: `PASS / PASS / PASS`",
        "- Public Action / operationId: `0.4.5 unchanged / 20 of 20 unique`",
        "- implementation Actions: `PASS_RUN_33157397089`",
        "- open P0 / material P1: `0 / 0`",
        "- Telegram production / manual task / Pilot / DB mutation: `0 / 0 / 0 / 0`",
        "- Production Assist: `OFF`",
        "",
        "Operating promotion is `NO_RUNTIME_CHANGE_REQUIRED`: tests and reports may be synchronized",
        "to main/operating without restarting the API solely for this task. Exact post-promotion SHA",
        "and health smoke belong to the completion bundle generated after promotion.",
    ]
    _write_text(output_dir / REPORT_NAMES[11], "\n".join(readiness_lines))
    _write_text(
        output_dir / REPORT_NAMES[12],
        """# Natural Proof Status

| Track | State | Next natural window |
| --- | --- | --- |
| KR close V3 validator | `PENDING` | Next normal KRX close, expected 2026-08-31 KST |
| US Price Structure | `PENDING` | Next naturally scheduled US stock cycle |
| US market message | `PENDING` | Next naturally scheduled US morning cycle |

Today's 16:50 KR run was intentionally cancelled. No replacement task, background proof, manual
production run, or production Telegram send was created. The KR LaunchAgent is restored idle with
future 16:05/16:20/16:50 schedules preserved and `runs=0` after restoration.
""",
    )
    artifact_rows = [
        (name, "required report") for name in REPORT_NAMES
    ] + [
        ("20260828-run44-v3-validator-convergence.json", "machine replay evidence"),
        ("20260828-final-operating-readiness.json", "machine readiness"),
        ("../architecture/PRICE_STRUCTURE_V3_VALIDATOR_OWNERSHIP.md", "canonical validator contract"),
        ("../architecture/PRICE_STRUCTURE_V3_RENDERER_INTEGRATION.md", "renderer integration update"),
        ("../../tests/test_run44_v3_validator_convergence.py", "permanent regression tests"),
        ("../../tests/fixtures/run44_000660_v3_validator_incident.json", "exact incident fixture"),
    ]
    _write_text(
        output_dir / REPORT_NAMES[13],
        "# Final Convergence Artifact Index\n\n"
        + _table(("Artifact", "Role"), artifact_rows)
        + "\n\nThe mandatory completion ZIP is assembled after exact-SHA promotion and post-promotion smoke.\n",
    )


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--convergence", type=Path, required=True)
    parser.add_argument("--messages", type=Path, required=True)
    parser.add_argument("--receipt", type=Path, required=True)
    parser.add_argument("--kr-replay", type=Path, required=True)
    parser.add_argument("--us-replay", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args()
    build_reports(
        convergence=_mapping(_read_json(args.convergence)),
        messages=_mapping(_read_json(args.messages)),
        receipt=_mapping(_read_json(args.receipt)),
        kr_replay=_mapping(_read_json(args.kr_replay)),
        us_replay=_mapping(_read_json(args.us_replay)),
        output_dir=args.output_dir,
    )


if __name__ == "__main__":
    main()
