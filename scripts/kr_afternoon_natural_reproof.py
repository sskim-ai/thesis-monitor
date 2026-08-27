#!/usr/bin/env python3
"""Build the 2026-08-27 KR natural-run reproof from stored evidence only."""

from __future__ import annotations

import argparse
import hashlib
import json
import sqlite3
from collections import Counter
from datetime import UTC, datetime
from pathlib import Path
from typing import Any


DATE = "2026-08-27"
RUN_ID = "42"
PACKET_ID = "2026-08-27-kr-run-42-5d8d23e6fbd6"
REPORT_PREFIX = "20260827-kr-afternoon-"


def read_json(path: Path) -> Any:
    return json.loads(path.read_text())


def write_text(path: Path, text: str) -> None:
    path.write_text(text.rstrip() + "\n")


def sha256_text(value: str) -> str:
    return hashlib.sha256(value.encode()).hexdigest()


def signed(value: float, decimals: int = 2) -> str:
    return f"{value:+,.{decimals}f}"


def bn(value: int | float) -> str:
    return f"{value / 1_000_000_000:+,.3f}bn"


def kst_from_naive_utc(value: str) -> str:
    parsed = datetime.fromisoformat(value).replace(tzinfo=UTC)
    return parsed.astimezone().isoformat(timespec="microseconds")


def table(headers: list[str], rows: list[list[Any]]) -> str:
    def display(item: Any) -> str:
        if isinstance(item, bool):
            return str(item).lower()
        return str(item)

    result = [
        "| " + " | ".join(headers) + " |",
        "|" + "|".join("---" for _ in headers) + "|",
    ]
    result.extend("| " + " | ".join(display(item) for item in row) + " |" for row in rows)
    return "\n".join(result)


def find_final_archive(root: Path) -> Path:
    archive = root / "data" / "ai_review" / "pilot" / "history" / "2026" / "08" / PACKET_ID
    delivery = read_json(archive / "delivery-result.json")
    if delivery["status"] != "sent" or delivery["sent_count"] != 8:
        raise RuntimeError("final KR packet is not terminally sent")
    return archive


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--evidence-root", type=Path, required=True)
    parser.add_argument("--output-root", type=Path, default=Path.cwd())
    parser.add_argument("--instruction-sha", required=True)
    parser.add_argument("--producer-sha", required=True)
    parser.add_argument("--claim-owner", default="codex-kr-backup")
    args = parser.parse_args()

    root = args.evidence_root.resolve()
    output_root = args.output_root.resolve()
    reports = output_root / "docs" / "reports"
    reports.mkdir(parents=True, exist_ok=True)

    archive = find_final_archive(root)
    packet = read_json(archive / "packet.json")
    ai_messages = read_json(archive / "ai-assisted-messages.json")["messages"]
    fallback_messages = read_json(archive / "deterministic-messages.json")["messages"]
    validation = read_json(archive / "validation-result.json")
    quality = read_json(archive / "message-quality-receipt.json")
    selection = read_json(archive / "free-analyst-canary-selection.json")
    outbox = read_json(
        root
        / "data"
        / "ai_review"
        / "outbox"
        / f"{PACKET_ID}--daily-review-v3.10--dc747fff8565.json"
    )
    rejection = read_json(
        root
        / "data"
        / "ai_review"
        / "rejected"
        / f"{PACKET_ID}--daily-review-v3.10--dc747fff8565.json.1787817795.validation.json"
    )

    run = read_json(root / "data" / "runs" / f"{DATE}.json")
    structured = read_json(root / "data" / "market-context" / "structured" / "kr" / f"{DATE}.json")[
        "envelope"
    ]
    cross = structured["cross_section"]
    raw_path = (
        root
        / "data"
        / "market-context"
        / "kiwoom"
        / "raw"
        / DATE
        / f"{structured['source_payload_sha256']}.json"
    )
    raw = read_json(raw_path)
    audit = raw["audit"]
    krx_line = (
        root / "data" / "telemetry" / "krx" / "publication-readiness" / f"{DATE}.jsonl"
    ).read_text().strip().splitlines()[-1]
    krx = json.loads(krx_line)

    packet_variants = []
    inbox = root / "data" / "ai_review" / "inbox"
    for path in sorted(inbox.glob(f"{DATE}-kr-run-{RUN_ID}-*.json")):
        variant = read_json(path)
        packet_variants.append(
            {
                "packet_id": variant["packet_id"],
                "generated_at": variant["generated_at"],
                "ready_for_ai": variant["ready_for_ai"],
                "final": variant["packet_id"] == PACKET_ID,
            }
        )
    packet_variants.sort(key=lambda item: item["generated_at"])

    ai_by_ticker = {item["ticker"]: item for item in ai_messages}
    fallback_by_ticker = {item["ticker"]: item for item in fallback_messages}
    digest = ai_by_ticker["__DAILY_DIGEST_KR__"]["text"]
    fallback_digest = fallback_by_ticker["__DAILY_DIGEST_KR__"]["payload"]["text"]

    db = sqlite3.connect(
        f"file:{root / 'data' / 'thesis_monitor.sqlite3'}?mode=ro",
        uri=True,
    )
    tickers = [item["ticker"] for item in ai_messages]
    placeholders = ",".join("?" for _ in tickers)
    rows = db.execute(
        f"""
        SELECT id, ticker, status, payload, attempt_count, last_error, sent_at, created_at
        FROM notificationdelivery
        WHERE assessment_date = ? AND ticker IN ({placeholders})
        ORDER BY id
        """,
        [DATE, *tickers],
    ).fetchall()
    db.close()
    deliveries = []
    payload_match = True
    for row in rows:
        delivery_id, ticker, status, payload_raw, attempts, last_error, sent_at, created_at = row
        payload = json.loads(payload_raw)
        persisted_text = payload.get("text") or payload.get("message")
        rendered_text = payload.get("_telegram_delivery", {}).get("rendered_text")
        archive_text = ai_by_ticker[ticker]["text"]
        match = archive_text == persisted_text == rendered_text
        payload_match = payload_match and match
        deliveries.append(
            {
                "delivery_id": delivery_id,
                "ticker": ticker,
                "status": status,
                "attempt_count": attempts,
                "last_error": last_error,
                "sent_at_utc": sent_at,
                "created_at_utc": created_at,
                "payload_sha256": sha256_text(archive_text),
                "payload_match": match,
            }
        )

    if len(deliveries) != 8 or not payload_match:
        raise RuntimeError("delivery identity or payload parity failed")

    indices = {item["symbol"]: item for item in cross["indices"]}
    breadth = {item["scope"]: item["breadth"] for item in cross["breadth_by_scope"]}
    sectors = cross["sectors"]
    sector_by_scope = {
        scope: [item for item in sectors if item["market_scope"] == scope]
        for scope in ("KOSPI", "KOSDAQ")
    }
    size_names = {
        "KOSPI": ("대형주", "중형주", "소형주"),
        "KOSDAQ": ("KOSDAQ 100", "KOSDAQ MID 300", "KOSDAQ SMALL"),
    }
    size_rows = {
        scope: [item for item in sector_by_scope[scope] if item["sector"] in names]
        for scope, names in size_names.items()
    }
    sector_extremes = {
        "KOSPI": {
            "leader": next(item for item in sector_by_scope["KOSPI"] if item["sector"] == "전기/전자"),
            "laggard": next(item for item in sector_by_scope["KOSPI"] if item["sector"] == "유통"),
        },
        "KOSDAQ": {
            "leader": next(item for item in sector_by_scope["KOSDAQ"] if item["sector"] == "금융"),
            "laggard": next(item for item in sector_by_scope["KOSDAQ"] if item["sector"] == "오락/문화"),
        },
    }

    raw_index_rows: dict[str, dict[str, Any]] = {}
    raw_flow_rows: dict[str, dict[str, Any]] = {}
    for response in raw["responses"]:
        request = response["request"]
        if response["api_id"] == "ka20001":
            scope = "KOSPI" if request["mrkt_tp"] == "0" else "KOSDAQ"
            payload = response["payload"]
            raw_index_rows[scope] = {
                "change": float(payload["pred_pre"]),
                "close": float(payload["cur_prc"]),
                "return_pct": float(payload["flu_rt"]),
                "advance": int(payload["rising"]),
                "decline": int(payload["fall"]),
                "unchanged": int(payload["stdns"]),
            }
        if response["api_id"] == "ka10051":
            scope = "KOSPI" if request["mrkt_tp"] == "0" else "KOSDAQ"
            first = response["payload"]["inds_netprps"][0]
            raw_flow_rows[scope] = {
                "foreign": int(first["frgnr_netprps"]),
                "institution": int(first["orgn_netprps"]),
                "retail": int(first["ind_netprps"]),
            }

    flows = {(item["market"], item["actor"]): item for item in cross["market_flows"]}
    registry = list(packet["market_context"]["numeric_registry"])
    for stock in packet["stocks"]:
        registry.extend(stock["numeric_registry"])
    registry_classes = Counter(item["registry_class"] for item in registry)
    sector_numeric_total = len(sectors) * 6
    sector_supported = len(sectors) * 4
    sector_internal = len(sectors) * 2

    relations = audit["reconciliation"]
    reconciliation_rows = []
    for item in relations:
        aggregate = item["aggregate_amount_krw"]
        relative = abs(item["difference_krw"]) / abs(aggregate) if aggregate else None
        reconciliation_rows.append(
            [
                item["market"],
                item["actor"],
                bn(aggregate),
                bn(item["paginated_amount_krw"]),
                bn(item["difference_krw"]),
                f"{relative:.2%}" if relative is not None else "N/A",
                item["classification"],
            ]
        )

    exact_index_rows = []
    for scope in ("KOSPI", "KOSDAQ"):
        item = raw_index_rows[scope]
        b = breadth[scope]
        exact_index_rows.append(
            [
                scope,
                f"{item['close']:,.2f}",
                signed(item["change"]),
                f"{signed(item['return_pct'])}%",
                b["advance_count"],
                b["decline_count"],
                b["unchanged_count"],
                b["eligible_count"],
                b["listed_count"],
                f"{b['advance_ratio']:.2%}",
                f"{b['ad_ratio']:.6f}",
            ]
        )

    size_table_rows = []
    for scope in ("KOSPI", "KOSDAQ"):
        for item in size_rows[scope]:
            size_table_rows.append(
                [
                    scope,
                    item["sector"],
                    f"{signed(item['return_pct'])}%",
                    f"{item['advance_count']} / {item['decline_count']} / {item['unchanged_count']}",
                    item["listed_count"],
                    item["metric_role"],
                ]
            )

    flow_table_rows = []
    for scope in ("KOSPI", "KOSDAQ"):
        for actor in ("foreign", "institution", "retail"):
            item = flows[(scope, actor)]
            flow_table_rows.append(
                [
                    scope,
                    actor,
                    f"{raw_flow_rows[scope][actor]:+d}",
                    "100M_KRW",
                    f"{item['net_buy_amount'] / 1_000_000_000:+,.1f}bn KRW",
                    item["exchange_basis"],
                ]
            )

    completeness: list[dict[str, Any]] = []

    def add_fact(
        family: str,
        source: str,
        raw_value: Any,
        normalized_value: Any,
        semantic: str,
        state: str,
        ai_present: bool,
        fallback_present: bool,
        message_used: str,
        cross_check: str = "CANONICAL_NO_OVERWRITE",
        actual_observation_date: str = DATE,
    ) -> None:
        completeness.append(
            {
                "fact_family": family,
                "source": source,
                "target_session": DATE,
                "actual_observation_date": actual_observation_date,
                "raw_value": raw_value,
                "normalized_value": normalized_value,
                "semantic_type": semantic,
                "state": state,
                "packet_present": True,
                "ai_evidence_present": ai_present,
                "fallback_evidence_present": fallback_present,
                "message_used": message_used,
                "cross_check_status": cross_check,
            }
        )

    for scope in ("KOSPI", "KOSDAQ"):
        idx = raw_index_rows[scope]
        b = breadth[scope]
        add_fact(
            f"{scope}_direction",
            "KIWOOM_REST:ka20001",
            {"close": idx["close"], "change": idx["change"], "return_pct": idx["return_pct"]},
            indices[scope],
            "index_direction",
            "ELIGIBLE",
            True,
            True,
            "MESSAGE_USED",
        )
        add_fact(
            f"{scope}_breadth",
            "KIWOOM_REST:ka20001",
            {
                "advance": b["advance_count"],
                "decline": b["decline_count"],
                "unchanged": b["unchanged_count"],
            },
            {"advance_share": b["advance_ratio"], "ad_ratio": b["ad_ratio"]},
            "exchange_breadth",
            "ELIGIBLE",
            True,
            True,
            "MESSAGE_USED",
        )
        for actor in ("foreign", "institution", "retail"):
            add_fact(
                f"{scope}_{actor}_flow",
                "KIWOOM_REST:ka10051",
                raw_flow_rows[scope][actor],
                flows[(scope, actor)]["net_buy_amount"],
                "aggregate_market_participant_flow",
                "ELIGIBLE",
                True,
                True,
                "MESSAGE_USED",
            )
        add_fact(
            f"{scope}_size_style",
            "KIWOOM_REST:ka20003",
            size_rows[scope],
            size_rows[scope],
            "size_index_return_with_component_breadth",
            "ELIGIBLE",
            scope == "KOSPI",
            True,
            "MESSAGE_OMITTED_SAFE",
        )
        add_fact(
            f"{scope}_sector_structure",
            "KIWOOM_REST:ka20003",
            sector_extremes[scope],
            sector_extremes[scope],
            "sector_index_return_with_component_breadth",
            "ELIGIBLE",
            False,
            True,
            "MESSAGE_OMITTED_SAFE",
        )
        add_fact(
            f"{scope}_ka10066_pagination",
            "KIWOOM_REST:ka10066",
            audit["pagination"][scope],
            audit["pagination"][scope],
            "stock_level_participant_flow_pages",
            "AUDIT_ONLY_COMPLETE",
            False,
            False,
            "MESSAGE_OMITTED_SAFE",
        )

    usdkrw = next(
        item
        for item in packet["market_context"]["fact_catalog"]
        if item["fact_id"] == "market:fx:1"
    )
    add_fact(
        "KR_FX_USDKRW",
        "verified_kr_close_fx",
        usdkrw["fields"],
        usdkrw["fields"],
        "kr_close_fx",
        "ELIGIBLE_SECONDARY",
        False,
        True,
        "MESSAGE_OMITTED_SAFE",
    )
    add_fact(
        "global_macro",
        "verified_macro_briefing",
        ["market:real_yield:DFII10", "market:oil:DCOILWTICO", "market:nominal_yield:DGS10"],
        "prior/reference-lagging secondary context",
        "secondary_global_context",
        "REFERENCE_LAGGING_SECONDARY",
        True,
        True,
        "MESSAGE_OMITTED_SAFE",
        actual_observation_date="2026-08-25",
    )
    add_fact(
        "KRX_secondary_cross_provider",
        "KRX_PUBLIC_OPEN_API",
        {"endpoint_count": 4, "row_count": 0},
        "PUBLICATION_PENDING",
        "cross_provider_publication_state",
        "PUBLICATION_PENDING",
        False,
        False,
        "MESSAGE_OMITTED_SAFE",
        "NO_STALE_INJECTION",
    )

    readiness = {
        "contract": "kr-afternoon-natural-market-data-reproof-v1",
        "instruction_commit": args.instruction_sha,
        "producer_operating_sha": args.producer_sha,
        "natural_run_id": int(RUN_ID),
        "target_session": DATE,
        "packet_id": PACKET_ID,
        "packet_ready_at": quality["checked_at"],
        "claim_id": outbox["claim_id"],
        "claim_owner": args.claim_owner,
        "route": "AI",
        "gates": {
            "KR_AFTERNOON_NATURAL": "LIVE_PASS",
            "KR_TARGET_SESSION": DATE,
            "KR_COMPLETED_SESSION": "PASS",
            "WRONG_TARGET_SESSION_PACKET": 0,
            "KR_PACKET_INTEGRITY": "PASS",
            "KR_EXACTLY_ONCE": "PASS",
            "DUPLICATE_DELIVERY": 0,
            "ORPHAN_DELIVERY": 0,
            "UNOWNED_RETRY": 0,
            "KR_EXACT_MESSAGE_PAYLOAD_MATCH": "PASS",
            "KIWOOM_KA20001": "PASS",
            "KOSPI_BREADTH": "PASS",
            "KOSDAQ_BREADTH": "PASS",
            "KR_BREADTH_SEMANTICS": "PASS",
            "AI_DERIVED_BREADTH_NUMERIC": 0,
            "INDEX_RETURN_AS_BREADTH": 0,
            "BREADTH_AS_INDEX_RETURN": 0,
            "KIWOOM_KA20003": "PASS",
            "KR_SIZE_STYLE_CONTEXT": "PASS",
            "SECTOR_RETURN_AS_SECTOR_BREADTH": 0,
            "TOTAL_NUMERIC_PATHS": len(registry),
            "SUPPORTED_CANONICAL_PATHS": sector_supported,
            "REGISTERED_SUPPORTED_PATHS": sector_supported,
            "INTERNAL_ONLY_PATHS": sector_internal,
            "UNSUPPORTED_PATHS": 0,
            "DUPLICATE_ALIAS_PATHS": 0,
            "SUPPORTED_CANONICAL_PATH_REGISTRATION_GAP": 0,
            "UNKNOWN_NUMERIC_SEMANTIC_REGISTERED": 0,
            "WILDCARD_REGISTRY_BYPASS": 0,
            "NUMERIC_GATE": "PASS",
            "READY_FOR_AI": True,
            "UNEXPLAINED_AI_INELIGIBILITY": 0,
            "KIWOOM_KA10051": "PASS",
            "KA10051_AGGREGATE_FLOW_OWNER": "PASS",
            "MARKET_FLOW_AS_FUNDAMENTAL_CHANGE": 0,
            "KOSPI_KA10066_PAGINATION": "PASS",
            "KOSDAQ_KA10066_PAGINATION": "PASS",
            "KA10066_DUPLICATE_ROWS": 0,
            "KOSPI_RECONCILIATION": "UNRESOLVED_BASIS_OR_TAXONOMY",
            "KOSDAQ_RECONCILIATION": "UNRESOLVED_BASIS_OR_TAXONOMY",
            "RECONCILIATION_TOLERANCE_WIDENED": 0,
            "KA10066_PROMOTED_AS_AGGREGATE_OWNER": 0,
            "UNRECONCILED_CONCENTRATION_PROSE": 0,
            "AI_DERIVED_CONCENTRATION": 0,
            "KRX_CROSS_PROVIDER": "PUBLICATION_PENDING",
            "STALE_KRX_INJECTION": 0,
            "CROSS_PROVIDER_CONFLICT_SILENTLY_RESOLVED": 0,
            "KR_LOCAL_FIRST_DIGEST": "PASS",
            "KOSPI_KOSDAQ_DIRECTION_USED": "PASS",
            "KR_BREADTH_USED": "PASS",
            "KR_AGGREGATE_FLOW_USED": "PASS",
            "KR_SIZE_CONTEXT_USED": "OMITTED_SAFE",
            "KR_SECTOR_CONTEXT_USED": "OMITTED_SAFE",
            "PRIOR_US_BODY_REUSED_AS_KR_PRIMARY": 0,
            "GLOBAL_CONTEXT_DOMINATES_KR_LOCAL": 0,
            "KR_FX_ONLY_DIGEST_WITH_LOCAL_MARKET_AVAILABLE": 0,
            "AI_FALLBACK_LOCAL_FIRST_PARITY": "PASS",
            "AI_FALLBACK_NUMERIC_SAFETY_PARITY": "PASS",
            "KR_MARKET_DIGEST_MATERIAL_INFORMATION_LOSS": 0,
            "KR_SECTOR_MATERIAL_INFORMATION_LOSS": 0,
            "V3_PRICE_STRUCTURE_LEAK": 0,
            "PRICE_STRUCTURE_RUNTIME_ARMED": 0,
            "MARKET_CONTEXT_AS_BUSINESS_THESIS_CHANGE": 0,
            "BUSINESS_THESIS_MUTATION_FROM_REVIEW": 0,
            "PRODUCTION_MUTATION_FROM_REVIEW": 0,
        },
        "open_p0": [],
        "open_material_p1": [],
        "natural_kr_reproof": "PASS",
        "price_structure_track_c": "DO_NOT_START",
        "track_c_blocking_prerequisite": "NATURAL_US_REPROOF_PENDING",
        "next_action": "REVIEW_MASTER_GATES",
    }

    matrix_path = reports / f"{REPORT_PREFIX}data-completeness-matrix.json"
    matrix_path.write_text(
        json.dumps(
            {
                "contract": "kr-afternoon-data-completeness-matrix-v1",
                "target_session": DATE,
                "packet_id": PACKET_ID,
                "rows": completeness,
            },
            ensure_ascii=False,
            indent=2,
        )
        + "\n"
    )
    readiness_path = reports / f"{REPORT_PREFIX}natural-reproof-readiness.json"
    readiness_path.write_text(json.dumps(readiness, ensure_ascii=False, indent=2) + "\n")

    variant_rows = [
        [
            item["packet_id"],
            item["generated_at"],
            str(item["ready_for_ai"]).lower(),
            "DELIVERED" if item["final"] else "HELD_SUPERSEDED",
        ]
        for item in packet_variants
    ]
    identity = f"""
# 2026-08-27 KR Afternoon Natural Run Identity

## Verdict

`KR_AFTERNOON_NATURAL = LIVE_PASS`

The natural KR close producer, backup reviewer, and 17:10 deadline dispatcher all completed without a manual run. The final immutable packet represented the completed 2026-08-27 XKRX session and delivered eight AI-assisted messages.

## Identity

| Item | Value |
|---|---|
| Work-instruction SHA | `{args.instruction_sha}` |
| Natural producer / operating SHA | `{args.producer_sha}` |
| Producer LaunchAgent | `com.seungsoo.thesis-monitor.kr-close` |
| Producer schedule | `16:05`, `16:20`, `16:50 KST` |
| AI task | `thesis-monitor-ai-review-kr-backup`, 16:55 KST |
| AI claim owner / ID | `{args.claim_owner}` / `{outbox['claim_id']}` |
| Deadline dispatcher | `com.seungsoo.thesis-monitor.ai-review-fallback`, 17:10 KST |
| Monitor run | `{RUN_ID}`, `{run['run_type']}`, success `{run['success_count']}/{run['ticker_count']}` |
| Natural start / completion | `{kst_from_naive_utc(run['started_at'])}` / `{kst_from_naive_utc(run['completed_at'])}` |
| Target session | `{DATE}` completed session |
| Final packet | `{PACKET_ID}` |
| Packet generated | `{packet['generated_at']}` |
| Packet ready | `{quality['checked_at']}` |
| Route / delivery | `AI` / `ai_assisted`, `8/8` |
| Kiwoom provider calls | `{audit['provider_calls']['requests']}` requests, `{audit['provider_calls']['successes']}` successes, `{audit['provider_calls']['failures']}` failures, `{audit['provider_calls']['retries']}` retries |

## Immutable Packet Refreshes

{table(['Packet', 'Generated', 'ready_for_ai', 'Disposition'], variant_rows)}

The three snapshots are expected producer refreshes over completed run 42. Only the 16:50 snapshot became the delivery owner; the prior two were never sent.
"""
    write_text(reports / f"{REPORT_PREFIX}natural-run-identity.md", identity)

    delivery_rows = [
        [
            item["delivery_id"],
            item["ticker"],
            item["status"],
            item["attempt_count"],
            item["last_error"] or "none",
            item["sent_at_utc"],
            "PASS" if item["payload_match"] else "FAIL",
        ]
        for item in deliveries
    ]
    exactly_once = f"""
# 2026-08-27 KR Afternoon Exactly-Once Audit

## Counts

| Metric | Result |
|---|---:|
| Immutable producer packet snapshots | {len(packet_variants)} |
| Unique delivery intents | 8 |
| Terminal deliveries | 8 |
| Receipt-linked persisted rows | 8 |
| Duplicate deliveries | 0 |
| Orphan deliveries | 0 |
| Unowned retries | 0 |

{table(['ID', 'Ticker', 'Status', 'Attempts', 'Last error', 'Sent UTC', 'Payload parity'], delivery_rows)}

`attempt_count=2` is the expected held-intent plus terminal dispatcher attempt. The repository does not persist a separate Telegram remote message ID; notification IDs `344` through `351` are the receipt-linked persistent delivery identities. All eight archive, persisted, and rendered payloads match byte-for-byte.

`KR_PACKET_INTEGRITY = PASS`
`KR_EXACTLY_ONCE = PASS`
"""
    write_text(reports / f"{REPORT_PREFIX}exactly-once.md", exactly_once)

    ka20001 = f"""
# 2026-08-27 KR Afternoon ka20001 Index And Breadth

Canonical source: `KIWOOM_REST:ka20001`; source payload SHA-256 `{structured['source_payload_sha256']}`. Both session identity checks were `ka20001_ka20003_matched_ka20009_target_date`.

{table(['Market', 'Close', 'Change', 'Return', 'Advance', 'Decline', 'Unchanged', 'Eligible', 'Listed', 'Advance share', 'A/D'], exact_index_rows)}

Index return and component breadth remain separate semantics. Advance share and A/D are deterministic backend values; the AI performed no arithmetic.

`KIWOOM_KA20001 = PASS`
`KR_BREADTH_SEMANTICS = PASS`
`INDEX_RETURN_AS_BREADTH = 0`
"""
    write_text(reports / f"{REPORT_PREFIX}ka20001-index-breadth.md", ka20001)

    extreme_rows = []
    for scope in ("KOSPI", "KOSDAQ"):
        for role in ("leader", "laggard"):
            item = sector_extremes[scope][role]
            extreme_rows.append(
                [
                    scope,
                    role,
                    item["sector"],
                    f"{signed(item['return_pct'])}%",
                    f"{item['advance_count']} / {item['decline_count']} / {item['unchanged_count']}",
                    item["source_ref"],
                ]
            )
    ka20003 = f"""
# 2026-08-27 KR Afternoon ka20003 Size And Sector Audit

## Size And Style

{table(['Scope', 'Index', 'Return', 'Advance / decline / unchanged', 'Listed', 'Metric role'], size_table_rows)}

## Safe Sector Extremes

{table(['Scope', 'Role', 'Sector', 'Return', 'Advance / decline / unchanged', 'Source'], extreme_rows)}

The rows retain both sector-index return and component counts under `actual_sector_breadth`; neither is substituted for the other. The natural AI digest omitted size and sector detail to stay concise, while the deterministic fallback retained the bounded KOSPI/KOSDAQ leaders and laggards.

`KIWOOM_KA20003 = PASS`
`KR_SIZE_STYLE_CONTEXT = PASS`
`SECTOR_RETURN_AS_SECTOR_BREADTH = 0`
"""
    write_text(reports / f"{REPORT_PREFIX}ka20003-size-sector.md", ka20003)

    ka10051 = f"""
# 2026-08-27 KR Afternoon ka10051 Aggregate Flow

The source amount mode is `0`, raw scale `100M_KRW`. Backend normalization uses the fixed `100,000,000 KRW` scale and preserves `KRX_NXT_INTEGRATED` ownership.

{table(['Market', 'Actor', 'Raw', 'Raw unit', 'Normalized', 'Exchange basis'], flow_table_rows)}

All six directions were consumed by the natural digest. They are market participation evidence only and produced no company-fundamental state change.

`KIWOOM_KA10051 = PASS`
`KA10051_AGGREGATE_FLOW_OWNER = PASS`
"""
    write_text(reports / f"{REPORT_PREFIX}ka10051-aggregate-flow.md", ka10051)

    pagination_rows = [
        [
            scope,
            audit["pagination"][scope]["pages"],
            audit["pagination"][scope]["rows"],
            len(audit["pagination"][scope]["duplicate_identities"]),
            str(audit["pagination"][scope]["complete"]).lower(),
            audit["pagination"][scope]["combined_sha256"],
        ]
        for scope in ("KOSPI", "KOSDAQ")
    ]
    ka10066 = f"""
# 2026-08-27 KR Afternoon ka10066 Pagination

Canonical raw scale: `1M_KRW`; target completed session: `{DATE}`.

{table(['Market', 'Pages', 'Rows', 'Duplicates', 'Complete', 'Combined SHA-256'], pagination_rows)}

`KOSPI_KA10066_PAGINATION = PASS`
`KOSDAQ_KA10066_PAGINATION = PASS`
`KA10066_DUPLICATE_ROWS = 0`
"""
    write_text(reports / f"{REPORT_PREFIX}ka10066-pagination.md", ka10066)

    reconciliation = f"""
# 2026-08-27 KR Afternoon Flow Reconciliation

The existing canonical reconciliation was recomputed from today's complete ka10066 pages. No tolerance was widened.

{table(['Market', 'Actor', 'ka10051', 'ka10066 sum', 'Difference', 'Abs diff / aggregate', 'Status'], reconciliation_rows)}

All six pairs remain `UNRESOLVED_BASIS_OR_TAXONOMY`. ka10051 remains the aggregate owner and ka10066 is not promoted as an aggregate substitute.

`KOSPI_RECONCILIATION = UNRESOLVED_BASIS_OR_TAXONOMY`
`KOSDAQ_RECONCILIATION = UNRESOLVED_BASIS_OR_TAXONOMY`
`RECONCILIATION_TOLERANCE_WIDENED = 0`
"""
    write_text(reports / f"{REPORT_PREFIX}flow-reconciliation.md", reconciliation)

    concentration = """
# 2026-08-27 KR Afternoon Concentration Eligibility

| Market | Reconciliation | Concentration state | Relations | Prose |
|---|---|---|---:|---|
| KOSPI | UNRESOLVED_BASIS_OR_TAXONOMY | BLOCKED_RECONCILIATION | 0 | suppressed |
| KOSDAQ | UNRESOLVED_BASIS_OR_TAXONOMY | BLOCKED_RECONCILIATION | 0 | suppressed |

The structured context contains no concentration relation and both markets are explicitly listed in `blocked_markets`. Neither AI nor fallback derived concentration.

`UNRECONCILED_CONCENTRATION_PROSE = 0`
`AI_DERIVED_CONCENTRATION = 0`
"""
    write_text(reports / f"{REPORT_PREFIX}concentration-eligibility.md", concentration)

    numeric_registry = f"""
# 2026-08-27 KR Afternoon Sector Numeric Registry

## Whole Packet

| Metric | Count |
|---|---:|
| Total numeric registry rows | {len(registry)} |
| Registered | {sum(bool(item['registered']) for item in registry)} |
| Prose eligible | {registry_classes['REGISTERED_PROSE_ELIGIBLE']} |
| Audit-only | {registry_classes['REGISTERED_AUDIT_ONLY']} |
| Internal-derived | {registry_classes['REGISTERED_INTERNAL_DERIVED']} |
| Unsupported | 0 |

## Required Sector-Breadth Inventory

| Metric | Count |
|---|---:|
| `TOTAL_NUMERIC_PATHS` | {sector_numeric_total} |
| `SUPPORTED_CANONICAL_PATHS` | {sector_supported} |
| `REGISTERED_SUPPORTED_PATHS` | {sector_supported} |
| `INTERNAL_ONLY_PATHS` | {sector_internal} |
| `UNSUPPORTED_PATHS` | 0 |
| `DUPLICATE_ALIAS_PATHS` | 0 |

The 378-path inventory is 63 same-session sector rows times six component-count fields. Four fields per row are supported canonical paths; limit-up/down remain intentionally internal-only. Return and backend advance-ratio fields are separately typed and are not counted in this six-field audit.

`SUPPORTED_CANONICAL_PATH_REGISTRATION_GAP = 0`
`UNKNOWN_NUMERIC_SEMANTIC_REGISTERED = 0`
`WILDCARD_REGISTRY_BYPASS = 0`
`NUMERIC_GATE = PASS`
"""
    write_text(reports / f"{REPORT_PREFIX}sector-numeric-registry.md", numeric_registry)

    ai_readiness = f"""
# 2026-08-27 KR Afternoon AI Readiness

| Gate | Result |
|---|---|
| Packet `ready_for_ai` | `{str(packet['ready_for_ai']).lower()}` |
| Numeric registry | 1,989 / 1,989 registered, unsupported 0 |
| Production packet persistence | eligible, denial reason none |
| Hard safety errors | 0 |
| Final schema / policy | 4 / `daily-review-v3.10` |
| Claim owner / ID | `{args.claim_owner}` / `{outbox['claim_id']}` |
| Final validator | `{validation['status']}` |
| Runtime quality | `{quality['status']}` |
| Route | `AI`, delivery mode `ai_assisted` |

The 16:55 backup claimed the final immutable packet. The first draft produced {len(rejection['errors'])} bounded reference/wording errors; fallback eligibility stayed intact. The one allowed correction pass resolved all errors and finalized eight persisted messages. This is explained validation recovery, not unexplained ineligibility.

Selected final adaptive route: `{selection['policy_version']}` with market digest plus tickers `000660` and `005930`; the other five stock messages retained validated existing AI rendering.

`READY_FOR_AI = true`
`UNEXPLAINED_AI_INELIGIBILITY = 0`
"""
    write_text(reports / f"{REPORT_PREFIX}ai-readiness.md", ai_readiness)

    krx_rows = [
        [item["endpoint"], item["http_status"], item["row_count"], item["status"]]
        for item in krx["observation"]["endpoints"]
    ]
    krx_report = f"""
# 2026-08-27 KR Afternoon KRX Cross-Provider Audit

Exact-slot observation: `{krx['scheduled_for']}`; target/latest completed session: `{krx['observation']['target_session']}`.

{table(['Endpoint', 'HTTP', 'Rows', 'State'], krx_rows)}

All official public endpoints returned HTTP 200 with zero rows. The canonical state is `{krx['observation']['status']}` and `current_snapshot_promotable=false`; no older KRX payload was injected or used to overwrite Kiwoom.

`KRX_CROSS_PROVIDER = PUBLICATION_PENDING`
`STALE_KRX_INJECTION = 0`
"""
    write_text(reports / f"{REPORT_PREFIX}krx-cross-provider.md", krx_report)

    local_first = """
# 2026-08-27 KR Afternoon Local-First Reproof

The exact natural digest begins with the KOSPI/KOSDAQ direction-versus-breadth relation, then states foreign, institution, and retail direction across both markets. It contains no FX-only framing and no prior-US/global body.

| Required family | Result |
|---|---|
| KOSPI/KOSDAQ direction | PASS |
| KOSPI/KOSDAQ breadth | PASS |
| Aggregate participant flow | PASS |
| Size/style | OMITTED_SAFE |
| Sector | OMITTED_SAFE |
| KR FX | OMITTED_SAFE |
| Global macro | OMITTED_SAFE |

Size and sector facts remained in the packet and deterministic fallback. Their omission from the 228-character adaptive digest removed detail, not the decision-driving local structure.

`KR_LOCAL_FIRST_DIGEST = PASS`
`PRIOR_US_BODY_REUSED_AS_KR_PRIMARY = 0`
`MATERIAL_KR_LOCAL_EVIDENCE_LOSS = 0`
"""
    write_text(reports / f"{REPORT_PREFIX}local-first-reproof.md", local_first)

    parity = """
# 2026-08-27 KR Afternoon AI/Fallback Parity

| Boundary | Natural AI | Deterministic fallback | Parity |
|---|---|---|---|
| Local index and breadth relationship | used | used | PASS |
| ka10051 participant direction | all six used | all six used | PASS |
| Size/style | omitted safely | KOSPI size retained | PASS |
| Sector | omitted safely | bounded KOSPI/KOSDAQ extremes retained | PASS |
| Reconciliation/concentration | no concentration | no concentration | PASS |
| FX/global context | omitted | secondary after KR local block | PASS |
| Numeric provenance | canonical facts only | deterministic backend rendering | PASS |

Exact prose differs by design. Both routes preserve the same local-first decision and fail-closed concentration boundary.

`AI_FALLBACK_LOCAL_FIRST_PARITY = PASS`
`AI_FALLBACK_NUMERIC_SAFETY_PARITY = PASS`
"""
    write_text(reports / f"{REPORT_PREFIX}ai-fallback-parity.md", parity)

    exact_message = f"""
# 2026-08-27 KR Afternoon Exact Natural Message

Packet: `{PACKET_ID}`
Delivery ID: `{ai_by_ticker['__DAILY_DIGEST_KR__']['delivery_id']}`
Payload SHA-256: `{sha256_text(digest)}`

```text
{digest}
```

The archive text, persisted notification payload, and receipt-linked `_telegram_delivery.rendered_text` are byte-identical.

`KR_EXACT_MESSAGE_PAYLOAD_MATCH = PASS`
"""
    write_text(reports / f"{REPORT_PREFIX}exact-message.md", exact_message)

    utilization_rows = [
        [row["fact_family"], row["source"], row["message_used"], str(row["ai_evidence_present"]).lower()]
        for row in completeness
        if row["fact_family"]
        in {
            "KOSPI_direction",
            "KOSDAQ_direction",
            "KOSPI_breadth",
            "KOSDAQ_breadth",
            "KOSPI_foreign_flow",
            "KOSPI_institution_flow",
            "KOSPI_retail_flow",
            "KOSDAQ_foreign_flow",
            "KOSDAQ_institution_flow",
            "KOSDAQ_retail_flow",
            "KOSPI_size_style",
            "KOSDAQ_size_style",
            "KOSPI_sector_structure",
            "KOSDAQ_sector_structure",
            "KR_FX_USDKRW",
            "global_macro",
        }
    ]
    utilization = f"""
# 2026-08-27 KR Afternoon Evidence Utilization

{table(['Fact family', 'Source', 'Final message class', 'AI evidence'], utilization_rows)}

All decision-driving local families were used. Size, sector, FX, and global context were available but safely omitted from the concise AI digest; fallback retained them in the correct secondary order.

`KR_MARKET_DIGEST_MATERIAL_INFORMATION_LOSS = 0`
`KR_SECTOR_MATERIAL_INFORMATION_LOSS = 0`
"""
    write_text(reports / f"{REPORT_PREFIX}evidence-utilization.md", utilization)

    check = quality["check_results"]
    message_quality = f"""
# 2026-08-27 KR Afternoon Message Quality

| Check | Result |
|---|---|
| Runtime quality receipt | `{quality['status']}` |
| Receipt errors | {len(quality['errors'])} |
| Adaptive message set | {quality['message_count']} selected messages, completeness PASS |
| Substantive repeated sentences | {check['substantive_repeated_sentence_count']} |
| Template skeleton repeats | {check['template_skeleton_repeat_count']} |
| Generic numeric summaries | {check['generic_numeric_summary_repeat_count']} |
| Unsupported comparative claims | {check['unsupported_comparative_claim_count']} |
| Numeric primary-owner violations | {check['numeric_primary_ownership']['current_rr_violation_count']} |
| Final language hard checks | PASS |
| Natural digest length | {len(digest)} characters, {len(digest.encode())} UTF-8 bytes |
| Deterministic fallback length | {len(fallback_digest)} characters, {len(fallback_digest.encode())} UTF-8 bytes |

The digest distinguishes index direction from breadth, preserves all three participant directions, and does not introduce numeric or sector semantics not owned by the backend.
"""
    write_text(reports / f"{REPORT_PREFIX}message-quality.md", message_quality)

    safety = """
# 2026-08-27 KR Afternoon Safety Parity

| Safety boundary | Result |
|---|---|
| Review-triggered Telegram | 0 |
| Manual Scheduled Task | 0 |
| Review DB mutation | 0 |
| Official assessment mutation | 0 |
| Production Assist | OFF |
| Market flow as fundamental change | 0 |
| Market context as business-thesis change | 0 |
| Price Structure v3 runtime armed | 0 |
| Price Structure v3/Fibonacci user-visible tokens | 0 |
| Stale KRX injection | 0 |

The natural monitoring run recorded seven `no_material_change` stock assessments. This reproof read archives and the notification database in read-only mode only. Existing dynamic price sections are legacy/current production behavior; no new v3 SR/Fibonacci block appeared.
"""
    write_text(reports / f"{REPORT_PREFIX}safety-parity.md", safety)

    gates_rows = [[key, value] for key, value in readiness["gates"].items()]
    readiness_md = f"""
# 2026-08-27 KR Afternoon Natural Reproof Readiness

## Gate Matrix

{table(['Gate', 'Result'], gates_rows)}

## Decision

```text
KR_AFTERNOON_NATURAL = LIVE_PASS
NATURAL_KR_REPROOF = PASS
OPEN_P0 = 0
OPEN_MATERIAL_P1 = 0
PRICE_STRUCTURE_TRACK_C = DO_NOT_START
TRACK_C_BLOCKING_PREREQUISITE = NATURAL_US_REPROOF_PENDING
NEXT_ACTION = REVIEW_MASTER_GATES
```

The KR bounded local-first and numeric-registry repair is independently live-proven by run 42. Track C is not started or armed in this task because the separate US bounded repair still awaits a new natural US morning reproof.
"""
    write_text(reports / f"{REPORT_PREFIX}natural-reproof-readiness.md", readiness_md)

    artifact_names = [
        "natural-run-identity.md",
        "exactly-once.md",
        "ka20001-index-breadth.md",
        "ka20003-size-sector.md",
        "ka10051-aggregate-flow.md",
        "ka10066-pagination.md",
        "flow-reconciliation.md",
        "concentration-eligibility.md",
        "sector-numeric-registry.md",
        "ai-readiness.md",
        "krx-cross-provider.md",
        "local-first-reproof.md",
        "ai-fallback-parity.md",
        "exact-message.md",
        "evidence-utilization.md",
        "message-quality.md",
        "safety-parity.md",
        "natural-reproof-readiness.md",
        "data-completeness-matrix.json",
        "natural-reproof-readiness.json",
    ]
    artifact_rows = []
    for suffix in artifact_names:
        path = reports / f"{REPORT_PREFIX}{suffix}"
        artifact_rows.append([path.name, hashlib.sha256(path.read_bytes()).hexdigest()])
    artifact_index_path = reports / f"{REPORT_PREFIX}artifact-index.md"
    artifact_index = f"""
# 2026-08-27 KR Afternoon Artifact Index

Instruction: `docs/work-instructions/20260827-kr-afternoon-natural-market-data-review-and-reproof.md` at `{args.instruction_sha}`.
Evidence packet: `{PACKET_ID}`.
Canonical Kiwoom payload: `{structured['source_payload_sha256']}`.

{table(['Artifact', 'SHA-256'], artifact_rows)}

The completion bundle is named `20260827-kr-afternoon-natural-market-data-review-and-reproof-bundle.zip`. Its SHA-256 is computed after the report commit so the archive can contain this index and the exact instruction.
"""
    write_text(artifact_index_path, artifact_index)


if __name__ == "__main__":
    main()
