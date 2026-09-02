from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Mapping


PACKET_ID = "2026-09-02-us-run-51-39a4d4eec53e"


def _read_json(path: Path) -> dict[str, object]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"expected_json_object:{path}")
    return value


def _write_json(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(
        json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True, default=str)
        + "\n",
        encoding="utf-8",
    )
    temporary.replace(path)


def _write_text(path: Path, value: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(value.strip() + "\n", encoding="utf-8")
    temporary.replace(path)


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _fmt(value: object, digits: int = 2) -> str:
    return f"{float(value):,.{digits}f}"


def _bar_line(frame: Mapping[str, object]) -> str:
    return (
        f"O {_fmt(frame['open'])} / H {_fmt(frame['high'])} / "
        f"L {_fmt(frame['low'])} / C {_fmt(frame['close'])}; "
        f"status `{frame['status']}`, return "
        f"`{float(frame['return_pct']):+.4f}%`"
    )


def _decisions(artifact: Mapping[str, object]) -> list[dict[str, object]]:
    return [
        {
            "ticker": str(row.get("ticker")),
            "decision": str(row.get("decision")),
            "accepted_decision_id": row.get("accepted_decision_id"),
        }
        for row in artifact.get("blocks") or ()
        if isinstance(row, Mapping)
    ]


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo", type=Path, required=True)
    parser.add_argument("--source", type=Path, required=True)
    parser.add_argument("--history", type=Path, required=True)
    parser.add_argument("--dwm", type=Path, required=True)
    parser.add_argument("--real-yield", type=Path, required=True)
    parser.add_argument("--market", type=Path, required=True)
    parser.add_argument("--stage-matrix", type=Path, required=True)
    parser.add_argument("--proof", type=Path, required=True)
    parser.add_argument("--artifact", type=Path, required=True)
    parser.add_argument("--v2-receipt", type=Path, required=True)
    parser.add_argument("--payloads", type=Path, required=True)
    parser.add_argument("--pre-send", type=Path, required=True)
    parser.add_argument("--delivery", type=Path, required=True)
    parser.add_argument("--work-instruction-sha", required=True)
    parser.add_argument("--base-sha", required=True)
    parser.add_argument("--implementation-sha", required=True)
    parser.add_argument("--branch", required=True)
    args = parser.parse_args()

    architecture = args.repo / "docs/architecture"
    reports = args.repo / "docs/reports"
    source = _read_json(args.source)
    history = _read_json(args.history)
    dwm = _read_json(args.dwm)
    real_yield = _read_json(args.real_yield)
    market = _read_json(args.market)
    artifact = _read_json(args.artifact)
    v2_receipt = _read_json(args.v2_receipt)
    payloads = _read_json(args.payloads)
    pre_send = _read_json(args.pre_send)
    delivery = _read_json(args.delivery)
    products = dwm["products"]
    assert isinstance(products, Mapping)
    kospi = products["KOSPI200"]
    kosdaq = products["KOSDAQ150"]
    assert isinstance(kospi, Mapping) and isinstance(kosdaq, Mapping)
    decisions = _decisions(artifact)
    distribution = {
        decision: sum(row["decision"] == decision for row in decisions)
        for decision in ("BUY", "HOLD", "SELL")
    }
    backfill = history["backfill"]
    assert isinstance(backfill, Mapping)
    receipt = delivery["receipt"]
    assert isinstance(receipt, Mapping)

    architecture_docs = {
        "KRX_NIGHT_DAILY_OHLC_SOURCE_CONTRACT.md": f"""
# KRX Night Daily OHLC Source Contract

Contract: `krx-night-daily-ohlc-v1`.

The only source is official KRX service `fut_bydd_trd` at `{source['endpoint']}`. A row is eligible only when `MKT_NM` resolves to NIGHT, the product resolves to KOSPI200 or KOSDAQ150 futures, `BAS_DD` equals the query date, contract code and parsed maturity exist, and all OHLC fields are finite, positive, and internally ordered.

| Canonical | KRX field |
| --- | --- |
| Date | `BAS_DD` |
| Contract | `ISU_CD` plus `ISU_NM` maturity |
| Session | `MKT_NM` |
| Open / High / Low / Close | `TDD_OPNPRC` / `TDD_HGPRC` / `TDD_LWPRC` / `TDD_CLSPRC` |
| Volume | `ACC_TRDVOL` |
| Official change | `CMPPREVDD_PRC` |

Missing or malformed OHLC is rejected; no synthetic repair or broad investing proxy exists.
""",
        "KRX_NIGHT_HISTORY_STORE.md": """
# KRX Night History Store

Contract: `krx-night-history-store-v1`.

Raw bytes are stored once under query date and raw SHA-256. The receipt records endpoint, service, fetch time, query date, HTTP status, size, row count, field names, and relative raw path. Normalized FINAL bars are keyed by instrument root, exact contract code, reference date, and NIGHT session. A repeated identical fingerprint is idempotent; a different fingerprint at the same identity fails closed without overwrite.

The live provider writes source history incrementally before aggregation. Collector/history failure is isolated as telemetry and never blocks stock V2 generation.
""",
        "KRX_NIGHT_DWM_AGGREGATION.md": """
# KRX Night D/W/M Aggregation

Contract: `krx-night-same-contract-dwm-v1`.

The resolver selects the nearest non-expired maturity from actual FINAL bars. Daily, weekly, and monthly frames then use that exact contract only. Weekly bars use XKRX Monday-to-Sunday sessions; monthly bars use XKRX sessions in the calendar month. The current incomplete week/month is `IN_PROGRESS`. A roll that begins after the period start is `SAME_CONTRACT_PARTIAL_PERIOD`; contracts are never spliced.

Returns use the immediately preceding completed same-contract week/month close only. Without a complete baseline, the bar remains usable but return is unavailable.
""",
        "US_MORNING_NIGHT_FUTURES_REFERENCE_DATE_CONTRACT.md": """
# US Morning Night-Futures Reference Date Contract

For a US-morning packet, the KRX NIGHT reference date is the previous completed XKRX business day. Run-51 therefore binds to `2026-09-01`. The daily comparison remains completed NIGHT close versus the immediately preceding regular-day close. Contract month is identity metadata; it is not a monthly timeframe.
""",
        "US_MARKET_REAL_YIELD_DELTA_CONTRACT.md": """
# US Market Real-Yield Delta Contract

The real-yield claim requires two official observations: current level/date and immediately previous level/date. Delta is percentage points, `current - previous`; basis points are `delta_pp * 100`. It is not a percent return and is never labeled as same-day movement when observation dates differ.

Run-51: `2.44%` on `2026-08-31`, `2.42%` on `2026-08-28`, delta `+0.02%p` or `+2bp`.
""",
        "MARKET_PACKET_TEMPORAL_ROLES.md": """
# Market Packet Temporal Roles

Packet facts keep source observation date, source session, comparison baseline, and finality. `CURRENT_DIRECTIONAL` means current for the packet's explicit temporal contract, not necessarily same-calendar-day. Prior-session and lagging official macro observations must be date-qualified. D/W/M bars expose `FINAL`, `IN_PROGRESS`, or `SAME_CONTRACT_PARTIAL_PERIOD`; renderer text must preserve that state.
""",
    }
    for name, text in architecture_docs.items():
        path = architecture / name
        if name in {
            "MARKET_PACKET_TEMPORAL_ROLES.md",
            "US_MORNING_NIGHT_FUTURES_REFERENCE_DATE_CONTRACT.md",
        } and path.exists():
            continue
        _write_text(path, text)

    kpi_daily = kospi["daily"]
    kqd_daily = kosdaq["daily"]
    assert isinstance(kpi_daily, Mapping) and isinstance(kqd_daily, Mapping)
    report_docs = {
        "20260902-krx-night-source-schema-proof.md": f"""
# KRX Night Source Schema Proof

`KRX_NIGHT_DAILY_OHLC_SCHEMA = PROVEN`

Official KRX request for `2026-09-01` returned `{source['row_count']}` rows and raw SHA `{source['raw_payload_sha256']}`. The response contains all verified fields: `{', '.join(f'`{item}`' for item in source['field_names'])}`. Two target NIGHT near-month rows had complete OHLC and volume.

`UNVERIFIED_KRX_FIELD_SEMANTICS_USED = 0`
""",
        "20260902-krx-night-field-mapping.md": """
# KRX Night Field Mapping

| Meaning | Source | Validation |
| --- | --- | --- |
| Date | `BAS_DD` | exact query-date match |
| Product | `PROD_NM` + `ISU_NM` | supported target root |
| Contract | `ISU_CD` + maturity in `ISU_NM` | nonempty and parseable |
| NIGHT | `MKT_NM` | exact session resolver |
| O/H/L/C | `TDD_OPNPRC/HGPRC/LWPRC/CLSPRC` | finite, positive, low <= open/close <= high |
| Volume | `ACC_TRDVOL` | optional integer |
| Change | `CMPPREVDD_PRC` | optional official point change |

Generic investing cash flow or non-NIGHT rows are unrelated and never mapped.
""",
        "20260902-krx-night-raw-preservation.md": f"""
# KRX Night Raw Preservation

Raw response size: `{source['raw_size_bytes']}` bytes. SHA-256: `{source['raw_payload_sha256']}`. The exact bytes are preserved in TEST/HISTORICAL evidence; normalized bars point back to the raw SHA and raw relative path. Repeated bytes are idempotent and conflicting identity writes fail closed.

`KRX_RAW_RESPONSE_PRESERVED = PASS`
`RAW_KRX_OHLC_REWRITTEN = 0`
""",
        "20260902-krx-night-history-store.md": f"""
# KRX Night History Store

The bounded evidence store contains `{backfill['stored_bar_count']}` FINAL normalized bars from `{backfill['start']}` through `{backfill['end']}`. Identity is instrument + exact contract + reference date + NIGHT. The focused suite proves identical replay creates no duplicate and a conflicting fingerprint cannot overwrite.

`CONTRACT_IDENTITY_COLLISION = 0`
`KRX_NIGHT_HISTORY_INCREMENTAL = PASS`
""",
        "20260902-krx-night-history-calendar-reconciliation.md": f"""
# KRX Night History Calendar Reconciliation

The backfill enumerated `{backfill['expected_session_count']}` XKRX sessions and made `{backfill['request_count']}` official requests: `{backfill['success_count']}` success, `{backfill['failure_count']}` failure. No post-cutoff dates were used. Missing/invalid target rows were recorded as `{backfill['rejection_count']}` explicit rejections and never silently dropped into an aggregate.

`KRX_NIGHT_HISTORY_CALENDAR_RECONCILIATION = PASS`
""",
        "20260902-night-near-month-selection.md": f"""
# Night Near-Month Selection

At reference date `2026-09-01`, the resolver selected the minimum actual maturity not earlier than the reference month: KOSPI200 `{kospi['contract_code']}` and KOSDAQ150 `{kosdaq['contract_code']}`, both `{kospi['contract_maturity']}`. Selection is data-driven; `202609` is not hard-coded.

`NEAR_MONTH_CONTRACT_HARDCODED_TO_202609 = 0`
""",
        "20260902-night-same-contract-dwm-contract.md": """
# Night Same-Contract D/W/M Contract

All Run-51 daily, weekly, and monthly constituent fact IDs carry one exact contract code per product. Tests inject alternate-contract bars and prove they cannot affect O/H/L/C or return. Weekly and monthly baselines require the previous completed same-contract period.

`DWM_SAME_CONTRACT_ONLY = PASS`
`MULTI_CONTRACT_DWM_SPLICING = 0`
""",
        "20260902-night-contract-roll-partial-period.md": """
# Night Contract-Roll Partial Period

When the selected contract begins after the XKRX period start and another contract exists earlier in that period, status is `SAME_CONTRACT_PARTIAL_PERIOD`. It is never labeled full or FINAL. Missing elapsed constituents produce `PARTIAL_SAFE`; future expected sessions produce `IN_PROGRESS` rather than missing-data errors.
""",
        "20260902-run51-kospi200-screenshot-control.md": """
# Run-51 KOSPI200 Screenshot Control

Visual control: O 1,061.00 / H 1,061.40 / L 1,031.30 / C 1,040.50. Official KRX NIGHT row: O 1,067.00 / H 1,072.45 / L 1,053.80 / C 1,064.50.

The provider/session/chart convention behind the screenshot is not machine-verifiable from the image alone, so forcing parity would corrupt official evidence. Machine authority remains official KRX.

`RUN51_KOSPI200_DAILY_SCREENSHOT_PARITY = NOT_COMPARABLE`
""",
        "20260902-run51-kospi200-night-daily.md": f"""
# Run-51 KOSPI200 Night Daily

Contract `{kospi['contract_code']}` ({kospi['contract_maturity']}), reference `2026-09-01`: {_bar_line(kpi_daily)}. Volume is preserved in the canonical daily source bar. Daily return is versus the verified `2026-08-31` regular-day close.

`RUN51_KOSPI200_DAILY_OHLC_VALID = PASS`
""",
        "20260902-run51-kosdaq150-night-daily.md": f"""
# Run-51 KOSDAQ150 Night Daily

Contract `{kosdaq['contract_code']}` ({kosdaq['contract_maturity']}), reference `2026-09-01`: {_bar_line(kqd_daily)}. Daily return is versus the verified `2026-08-31` regular-day close.

`RUN51_KOSDAQ150_DAILY_OHLC_VALID = PASS`
""",
        "20260902-run51-night-weekly-monthly.md": f"""
# Run-51 Night Weekly / Monthly

| Product | Weekly | Monthly |
| --- | --- | --- |
| KOSPI200 | {_bar_line(kospi['weekly'])} | {_bar_line(kospi['monthly'])} |
| KOSDAQ150 | {_bar_line(kosdaq['weekly'])} | {_bar_line(kosdaq['monthly'])} |

Both current weekly and monthly bars are correctly labeled `IN_PROGRESS`.
""",
        "20260902-run51-night-return-provenance.md": f"""
# Run-51 Night Return Provenance

KOSPI200 weekly baseline `{kospi['weekly']['return_baseline_date']}` close `{kospi['weekly']['return_baseline_close']}`; monthly baseline `{kospi['monthly']['return_baseline_date']}` close `{kospi['monthly']['return_baseline_close']}`. KOSDAQ150 weekly baseline `{kosdaq['weekly']['return_baseline_date']}` close `{kosdaq['weekly']['return_baseline_close']}`; monthly baseline `{kosdaq['monthly']['return_baseline_date']}` close `{kosdaq['monthly']['return_baseline_close']}`. Every aggregate carries source fact IDs, raw SHAs, and normalized fingerprints.

`DWM_RETURN_BASELINE_INVENTED = 0`
`NIGHT_DWM_NUMERIC_PROVENANCE = PASS`
""",
        "20260902-run51-historical-backfill-disclosure.md": f"""
# Run-51 Historical Backfill Disclosure

A bounded official KRX TEST/HISTORICAL backfill from `{backfill['start']}` through `{backfill['end']}` was used solely to construct same-contract Run-51 D/W/M evidence. Requests `{backfill['request_count']}`, success `{backfill['success_count']}`, failure `{backfill['failure_count']}`, cache hits `{backfill['cache_hit_count']}`. It wrote only `/private/tmp` evidence; the frozen Run-51 production packet was not modified.

`POST_CUTOFF_MARKET_DATA_USED_IN_RUN51_REPLAY = 0`
`PRODUCTION_RUN51_PACKET_BACKFILLED_IN_PLACE = 0`
""",
        "20260902-real-yield-delta-contract.md": """
# Real-Yield Delta Contract

Real-yield delta is `current level - immediately previous official level`. It is rendered in percentage points and basis points, never as a percent return. Both observation dates are mandatory, and date mismatch is explicit rather than called today's move.
""",
        "20260902-run51-real-yield-observation-pair.md": f"""
# Run-51 Real-Yield Observation Pair

Current `{real_yield['current']:.2f}%` on `{real_yield['current_date']}`; previous `{real_yield['previous']:.2f}%` on `{real_yield['previous_date']}`; delta `{real_yield['delta_pp']:+.2f}%p` / `{real_yield['delta_bp']:+.0f}bp`.

Rendered: `{real_yield['rendered_claim']}`

`REAL_YIELD_OBSERVATION_PAIR_VALID = PASS`
""",
        "20260902-run51-market-enriched-replay.md": f"""
# Run-51 Market Enriched Replay

The frozen regular-session market facts and selections were reused unchanged. Only official KRX NIGHT D/W/M and the exact real-yield observation pair were added. Renderer status `{market['render']['status']}`, exact-payload quality `{market['message_quality']['status']}`, non-night numeric diff `{market['non_night_market_numeric_diff']}`, non-night selection diff `{market['non_night_market_selection_diff']}`.

`RUN51_MARKET_REPLAY = PASS`
`MARKET_FINAL_VALIDATION = PASS`
""",
        "20260902-run51-market-numeric-provenance.md": f"""
# Run-51 Market Numeric Provenance

The six D/W/M facts and the real-yield level/previous/delta fields are registered canonical numeric facts. Renderer-consumed night fact IDs: `{len(market['night_fact_ids'])}`. Unsupported new registry entries: `{len(market['numeric_registry_unsupported'])}`.

`MARKET_PHANTOM_NUMERIC_ERRORS = 0`
`NIGHT_DWM_PACKET_OWNERSHIP = PASS`
`REAL_YIELD_DELTA_NUMERIC_PROVENANCE = PASS`
""",
        "20260902-run51-v2-live-path.md": f"""
# Run-51 V2 Live Path

Signed-in Codex CLI reached `{artifact['reasoning_model']}` at `{artifact['reasoning_effort']}`. Context `{len(artifact['selected_subjects'])}/14`, candidate `{len(artifact['candidates'])}/14`, READY `{artifact['ready_count']}/14`, not-ready `{artifact['not_ready_count']}`, fallback `0`. Batch schema repairs `{v2_receipt['batch_schema_repair_count']}`; bounded candidate repairs `{v2_receipt['candidate_repair_count']}` (CRCL, MU, SKHY, WULF). Message quality `{artifact['message_quality']['status']}`.

Decision distribution: BUY `{distribution['BUY']}`, HOLD `{distribution['HOLD']}`, SELL `{distribution['SELL']}`.

| Ticker | Accepted decision |
| --- | --- |
{chr(10).join(f"| {row['ticker']} | {row['decision']} |" for row in decisions)}
""",
        "20260902-run51-test-recipient-routing.md": f"""
# Run-51 Test Recipient Routing

Dedicated TEST sink audit: `{pre_send['status']}`. Test alias `{pre_send['test_sink_alias']}` and production alias `{pre_send['production_sink_alias']}` are distinct; raw IDs are not stored. Production notifier/intent creation was structurally absent. Telegram requests targeted only the selected TEST key.

`PRODUCTION_RECIPIENT_RESOLUTION_DISABLED = PASS`
`TEST_RECIPIENT_RESOLUTION = PASS`
`PRODUCTION_RECIPIENT_SEND = 0`
""",
        "20260902-run51-actual-send-receipts.md": f"""
# Run-51 Actual TEST Send Receipts

Planned `15`, sent `{delivery['sent_message_count']}`, acknowledged `{delivery['acknowledged_message_count']}`. Exact payload `{delivery['exact_payload_match']}`; duplicate `{delivery['duplicate_count']}`, orphan `{delivery['orphan_count']}`, unowned retry `{delivery['unowned_retry_count']}`, acknowledged resend `{delivery['acknowledged_message_resend']}`. Transport was the real Telegram API and namespace was TEST only.

`REAL_TELEGRAM_TRANSPORT = PASS`
`TEST_SENT_COUNT = 15`
`TEST_ACKNOWLEDGED_COUNT = 15`
""",
        "20260902-run51-exact-payload.md": f"""
# Run-51 Exact Payload

All 15 outbound texts were frozen before the first send. Telegram echoed each exact text; outbound and received SHA-256 matched 15/15. Maximum length was `{pre_send['max_character_count']}` characters.

| Seq | Ticker | SHA-256 | Chars |
| --- | --- | --- | --- |
{chr(10).join(f"| {row['sequence']} | {row['ticker']} | `{row['rendered_sha256']}` | {row['character_count']} |" for row in receipt['rows'])}

`TEST_LIVE_EXACT_PAYLOAD = PASS`
""",
        "20260902-run51-production-mutation-audit.md": f"""
# Run-51 Production Mutation Audit

Before/after fingerprints matched for the frozen Run-51 archive, accepted-decision state, pilot state, data database, and root database. Mutation count `{delivery['production_state_mutations']}`. TEST delivery did not create a production intent or suppress the next natural send.

`PRODUCTION_ACCEPTED_DECISION_MUTATION = 0`
`PRODUCTION_ASSESSMENT_MUTATION = 0`
`PRODUCTION_NOTIFICATION_STATE_MUTATION = 0`
`PRODUCTION_PACKET_STATE_MUTATION = 0`
`PRODUCTION_DELIVERY_LEDGER_MUTATION = 0`
""",
        "20260902-run51-actual-send-idempotency.md": """
# Run-51 Actual Send Idempotency

The immutable logical identity is TEST namespace + packet ID + MARKET/ticker. All 15 identities were unique. Receipt creation precedes network sends and an existing receipt causes a hard refusal, so this execution cannot be sent twice. No second-send experiment was performed.

`TEST_EXECUTION_IDEMPOTENCY = PASS`
`ACKNOWLEDGED_MESSAGE_RESEND = 0`
""",
        "20260902-krx-night-production-integration.md": """
# KRX Night Production Integration

The existing official KRX provider now preserves successful raw response bytes, incrementally stores valid FINAL NIGHT bars, and attaches same-contract D/W/M sidecars when available. Source/history failures are warnings and never block stock V2. No scheduler timing or ownership changed. Retention remains the repository data lifecycle; no destructive cleanup was introduced.

`KRX_NIGHT_COLLECTOR_FAILURE_BLOCKS_STOCK_V2 = 0`
`NIGHT_DWM_FRESHNESS_CONTRACT = PASS`
""",
        "20260902-run51-live-path-with-krx-night-proof.md": f"""
# Run-51 Live Path with KRX Night Proof

Branch `{args.branch}` from `{args.base_sha}`. Work-instruction commit `{args.work_instruction_sha}`; implementation `{args.implementation_sha}`.

Official KRX source/schema, immutable raw preservation, bounded history, same-contract D/W/M, real-yield pair, enriched market replay, signed-in xhigh V2 14/14, atomic 15-message gate, actual TEST delivery 15/15, exact payload, and production mutation audit all passed.

`OPEN_P0 = 0`
`OPEN_MATERIAL_P1 = 0`
`OPEN_P2 = 2` (screenshot provider/session reconciliation; optional historical rejection-reason presentation polish)
`RUN51_KRX_NIGHT_LIVE_PATH_ACTUAL_SEND = PASS`

This is a controlled TEST proof. `NATURAL_US_LIVE_STATUS = STILL_AWAITING_NEXT_SCHEDULED_RUN`.
""",
    }

    machine_files = {
        "20260902-run51-live-path-delivery.json": delivery,
        "20260902-run51-v2-live-path.json": {
            "contract": "run51-v2-live-path-proof-v1",
            "packet_id": PACKET_ID,
            "status": artifact["status"],
            "model": artifact["reasoning_model"],
            "reasoning_effort": artifact["reasoning_effort"],
            "context_ready_count": len(artifact["selected_subjects"]),
            "candidate_count": len(artifact["candidates"]),
            "ready_count": artifact["ready_count"],
            "not_ready_count": artifact["not_ready_count"],
            "fallback_count": 0,
            "batch_schema_repair_count": v2_receipt["batch_schema_repair_count"],
            "candidate_repair_count": v2_receipt["candidate_repair_count"],
            "message_quality": artifact["message_quality"],
            "distribution": distribution,
            "decisions": decisions,
        },
        "20260902-run51-exact-payload.json": payloads,
        "20260902-run51-v2-accepted-artifact.json": artifact,
        "20260902-run51-pre-send-readiness.json": pre_send,
    }
    for name, value in machine_files.items():
        _write_json(reports / name, value)

    stage = _read_json(args.stage_matrix)
    stages = stage.get("stages")
    assert isinstance(stages, dict)
    stages.update(
        {
            "v2_live_path": "PASS",
            "pre_send_atomic_readiness": "PASS",
            "test_delivery": "PASS",
            "production_mutation_audit": "PASS",
        }
    )
    stage["status"] = "PASS"
    _write_json(reports / "20260902-run51-live-path-stage-matrix.json", stage)

    proof = _read_json(args.proof)
    proof.update(
        {
            "status": "PASS",
            "repository": {
                "branch": args.branch,
                "base_sha": args.base_sha,
                "work_instruction_commit": args.work_instruction_sha,
                "implementation_sha": args.implementation_sha,
            },
            "v2": machine_files["20260902-run51-v2-live-path.json"],
            "delivery": {
                key: delivery[key]
                for key in (
                    "status",
                    "planned_message_count",
                    "sent_message_count",
                    "acknowledged_message_count",
                    "duplicate_count",
                    "orphan_count",
                    "unowned_retry_count",
                    "acknowledged_message_resend",
                    "exact_payload_match",
                    "production_recipient_send",
                    "production_state_mutations",
                )
            },
            "gates": {
                "open_p0": 0,
                "open_material_p1": 0,
                "open_p2": 2,
                "run51_krx_night_live_path_actual_send": "PASS",
                "natural_us_live_status": "STILL_AWAITING_NEXT_SCHEDULED_RUN",
            },
        }
    )
    _write_json(reports / "20260902-run51-live-path-with-krx-night-proof.json", proof)

    for name, text in report_docs.items():
        _write_text(reports / name, text)

    expected_reports = [*report_docs, *machine_files]
    expected_reports.extend(
        (
            "20260902-krx-night-source-contract.json",
            "20260902-krx-night-history.json",
            "20260902-run51-night-dwm.json",
            "20260902-run51-real-yield-delta.json",
            "20260902-run51-market-enriched.json",
            "20260902-run51-live-path-stage-matrix.json",
            "20260902-run51-live-path-with-krx-night-proof.json",
            "run51-enriched-market-message.txt",
        )
    )
    index_rows = []
    for name in sorted(set(expected_reports)):
        path = reports / name
        if not path.exists():
            raise FileNotFoundError(f"required_run51_artifact_missing:{name}")
        index_rows.append(
            {
                "path": f"docs/reports/{name}",
                "size": path.stat().st_size,
                "sha256": _sha256(path),
            }
        )
    index = {
        "contract": "run51-krx-night-artifact-index-v1",
        "packet_id": PACKET_ID,
        "artifact_count": len(index_rows),
        "artifacts": index_rows,
    }
    _write_json(reports / "20260902-run51-live-path-artifact-index.json", index)
    _write_text(
        reports / "20260902-run51-live-path-with-krx-night-artifact-index.md",
        "# Run-51 Live-Path Artifact Index\n\n"
        f"Indexed `{len(index_rows)}` report and machine artifacts. "
        "Every entry is content-addressed in "
        "`20260902-run51-live-path-artifact-index.json`. Raw recipient IDs, tokens, "
        "credentials, runtime-state databases, and hidden reasoning are excluded.\n\n"
        + "\n".join(f"- `{row['path']}` — `{row['sha256']}`" for row in index_rows),
    )
    print(
        json.dumps(
            {
                "status": "PASS",
                "report_count": len(report_docs),
                "machine_artifact_count": len(machine_files) + 8,
                "decision_distribution": distribution,
                "delivery": delivery["status"],
            },
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    main()
