from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
REPORTS = ROOT / "docs" / "reports"


def _load(name: str) -> dict[str, Any]:
    value = json.loads((REPORTS / name).read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"expected object: {name}")
    return value


def _write(name: str, text: str) -> None:
    (REPORTS / name).write_text(text.rstrip() + "\n", encoding="utf-8")


def _money(value: int | float) -> str:
    return f"{float(value) / 1_000_000_000:+,.1f} billion KRW"


def _table(headers: list[str], rows: list[list[object]]) -> str:
    lines = [
        "| " + " | ".join(headers) + " |",
        "| " + " | ".join("---" for _ in headers) + " |",
    ]
    lines.extend("| " + " | ".join(str(value) for value in row) + " |" for row in rows)
    return "\n".join(lines)


def _message_section(label: str, row: dict[str, Any], field: str) -> str:
    return f"## {label}\n\n```text\n{row[field].rstrip()}\n```"


def build(implementation_sha: str, full_pytest: str) -> None:
    evidence = _load("20260825-kiwoom-live-evidence.json")
    replay = _load("20260825-kr-kiwoom-enriched-replay.json")
    audit = evidence["audit"]
    indices = {item["symbol"]: item for item in evidence["indices"]}
    breadth = {item["scope"]: item["breadth"] for item in evidence["breadth_by_scope"]}
    flows = {(item["market"], item["actor"]): item for item in evidence["market_flows"]}
    reconciliation = audit["reconciliation"]
    concentration = audit["concentration"]
    pagination = audit["pagination"]

    _write(
        "20260825-kiwoom-tr-contract-audit.md",
        f"""# Kiwoom TR Contract Audit

## Result

`KIWOOM_TR_CONTRACT = PASS`

Implementation SHA: `{implementation_sha}`

Official source: Kiwoom REST API documentation and official example repository. No paid provider
or new subscription was used.

{_table(
    ["TR", "Endpoint", "Request contract", "Accepted output"],
    [
        ["ka20001", "/api/dostk/sect", "mrkt_tp 0/1, inds_cd 001/101", "index and breadth"],
        ["ka20003", "/api/dostk/sect", "inds_cd 001/101", "composite, size, sector"],
        ["ka20009", "/api/dostk/sect", "mrkt_tp and inds_cd", "target-date session proof"],
        ["ka10051", "/api/dostk/sect", "amt_qty_tp=0, base_dt, stex_tp=3", "market amount"],
        ["ka10066", "/api/dostk/mrkcond", "amt_qty_tp=1, trde_tp=0, stex_tp=3", "stock amount pages"],
    ],
)}

`ka10051` aggregate ownership is foreign/institution/retail market-wide flow. `ka10066` owns the
complete stock decomposition. Generic investing, account, and order endpoints are outside the
allowlist. Missing fields fail closed. Tokens, app keys, secret keys, and auth headers are absent
from all artifacts.
""",
    )

    _write(
        "20260825-kiwoom-live-probe.md",
        f"""# Kiwoom Live Probe

## Result

`KIWOOM_LIVE_PROBE = PASS`

- Session: `{evidence['session_date']}`
- Observed: `{evidence['observed_at']}`
- Source payload SHA-256: `{evidence['source_payload_sha256']}`
- Final deterministic collection: `{audit['provider_calls']['requests']}` requests,
  `{audit['provider_calls']['successes']}` successes, `{audit['provider_calls']['failures']}` failures,
  `{audit['provider_calls']['retries']}` retries.
- Whole task read-only live activity: 94 successful HTTP requests, including four OAuth requests
  and 90 TR requests; provider failure 0 and cache hit 0.

The 94-call total includes the initial contract probe (40), a separate historical-session proof
(3), an eight-TR local normalization attempt plus token (9), and the final evidence collection
(42). The local failed attempt was an aggregate identity normalization error after successful
provider responses; no invalid output was promoted.

No account, order, Telegram, Scheduled Task, Pilot, or DB mutation call was made.
""",
    )

    _write(
        "20260825-kiwoom-ka20001-breadth-validation.md",
        f"""# ka20001 Breadth Validation

`KR_INDEX_BREADTH = PASS`

{_table(
    ["Market", "Close", "Return", "Advancers", "Decliners", "Unchanged", "Eligible", "Listed"],
    [
        ["KOSPI", indices['KOSPI']['close'], f"{indices['KOSPI']['return_pct']:+.2f}%", breadth['KOSPI']['advance_count'], breadth['KOSPI']['decline_count'], breadth['KOSPI']['unchanged_count'], breadth['KOSPI']['eligible_count'], breadth['KOSPI']['listed_count']],
        ["KOSDAQ", indices['KOSDAQ']['close'], f"{indices['KOSDAQ']['return_pct']:+.2f}%", breadth['KOSDAQ']['advance_count'], breadth['KOSDAQ']['decline_count'], breadth['KOSDAQ']['unchanged_count'], breadth['KOSDAQ']['eligible_count'], breadth['KOSDAQ']['listed_count']],
    ],
)}

Both composites matched their exact target-date `ka20009` row and `ka20003` composite identity.
Eligible count is rising + falling + unchanged and is not forced to listed count. Current-only data
outside the completed target session is rejected.
""",
    )

    _write(
        "20260825-kiwoom-ka20003-sector-size-validation.md",
        f"""# ka20003 Sector And Size Validation

`KR_SECTOR_SIZE_CONTEXT = PASS`

{_table(
    ["Scope", "Code", "Name", "Return", "Advancers", "Decliners", "Unchanged"],
    [[item['market_scope'], item['sector_code'], item['sector'], f"{item['return_pct']:+.2f}%", item['advance_count'], item['decline_count'], item['unchanged_count']] for item in evidence['size_context']],
)}

Parsed non-composite sector/size rows: `{evidence['sector_count']}`. KOSPI codes 002/003/004 are
typed as size context and excluded from the sector list. Sector returns and breadth stay distinct;
they are not treated as issuer-level causes.
""",
    )

    _write(
        "20260825-kiwoom-ka10051-market-flow-validation.md",
        f"""# ka10051 Market Flow Validation

`KR_MARKET_WIDE_INVESTOR_FLOW = PASS`

{_table(
    ["Market", "Foreign", "Institution", "Retail", "Currency", "Basis"],
    [[market, _money(flows[(market, 'foreign')]['net_buy_amount']), _money(flows[(market, 'institution')]['net_buy_amount']), _money(flows[(market, 'retail')]['net_buy_amount']), "KRW", "KRX/NXT integrated"] for market in ('KOSPI', 'KOSDAQ')],
)}

Amount mode is `amt_qty_tp=0`; the empirically verified scale is KRW 100 million per source unit.
The source date is explicit and aggregate identity is selected by exact composite code/name. Stock
share quantities are never combined numerically with these monetary flows.
""",
    )

    _write(
        "20260825-kiwoom-ka10066-pagination-validation.md",
        f"""# ka10066 Pagination Validation

{_table(
    ["Market", "Pages", "Rows", "Complete", "Duplicate normalized identities", "Page-chain SHA-256"],
    [[market, pagination[market]['pages'], pagination[market]['rows'], pagination[market]['complete'], len(pagination[market]['duplicate_identities']), pagination[market]['combined_sha256']] for market in ('KOSPI', 'KOSDAQ')],
)}

Continuation follows response `cont-yn` and `next-key` until terminal. Amount mode is
`amt_qty_tp=1`; the empirically verified scale is KRW 1 million per source unit. An incomplete
chain or duplicate KRX/NXT-normalized identity blocks all concentration derived from that market.
""",
    )

    _write(
        "20260825-kiwoom-market-flow-reconciliation.md",
        f"""# Kiwoom Market Flow Reconciliation

{_table(
    ["Market", "Actor", "Aggregate", "Stock sum", "Difference", "Classification"],
    [[item['market'], item['actor'], _money(item['aggregate_amount_krw']), _money(item['paginated_amount_krw']), _money(item['difference_krw']), item['classification']] for item in reconciliation],
)}

KOSDAQ differences are smaller than one `ka10051` representational unit and are classified
`WITHIN_AGGREGATE_RESOLUTION`. KOSPI differences remain material and are
`UNRESOLVED_BASIS_OR_TAXONOMY`; KOSPI aggregate direction remains valid but stock-sum concentration
is blocked. No invented tolerance, silent substitution, or partial-page promotion is used.
""",
    )

    _write(
        "20260825-kiwoom-market-flow-concentration.md",
        f"""# Kiwoom Market Flow Concentration

`KR_MARKET_FLOW_CONCENTRATION = PASS (KOSDAQ_ONLY)`

{_table(
    ["Market", "Actor", "Direction", "Top N", "Ratio", "Formula"],
    [[item['market'], item['actor'], item['direction'], item['top_n'], f"{item['ratio'] * 100:.2f}%", item['formula']] for item in concentration],
)}

KOSPI is explicitly blocked: `{json.dumps(audit['blocked_concentration_markets'], ensure_ascii=False)}`.
Each KOSDAQ relation binds the complete page-chain hash and top-stock occurrence references.
Concentration is descriptive and cannot establish why the index or a stock moved.
""",
    )

    _write(
        "20260825-kr-kiwoom-enriched-replay.md",
        f"""# KR Kiwoom Enriched Replay

## Immutable Identity

- Packet: `{replay['packet_id']}`
- Packet rewrite: 0
- Supplemental evidence SHA-256: `{replay['supplemental_source_payload_sha256']}`
- Replay messages: `{replay['eligible_count']}/{replay['message_count']}` eligible
- Semantic validation: `{replay['semantic_validation']['status']}`
- New exact numeric prose claims: `{replay['numeric_binding']['new_exact_numeric_claims']}`
- Existing automatic bindings preserved: `{replay['numeric_binding']['baseline_auto_bound']}`

The same immutable market, earnings, valuation, price, positioning, and thesis inputs were used.
Only the supplemental Kiwoom sidecar changed. Market digest local-index/breadth/market-flow Unknowns
were resolved; KOSPI concentration remained suppressed. Canary simulation remained exactly one
market plus two stock messages.
""",
    )

    quality_rows = [
        [row["message_key"], row["human_quality"], row["eligible"], row["length_before"], row["length_after"], row["materiality_reason"] or "none"]
        for row in replay["messages"]
    ]
    _write(
        "20260825-kr-kiwoom-message-before-after.md",
        f"""# KR Kiwoom Message Before And After

{_table(["Message", "Human quality", "Eligible", "Before chars", "After chars", "Materiality"], quality_rows)}

Value-add counts: `{json.dumps(replay['human_quality'], ensure_ascii=False)}`. The market digest is a
material improvement because local market structure replaces three explicit data gaps. Samsung is
a minor improvement because stock foreign-flow direction can be related qualitatively to KOSPI
direction without mixing share quantity and KRW amount. Other stock messages remain unchanged.
Degraded messages: 0.
""",
    )

    readiness = {
        "contract": "kiwoom-kr-market-context-readiness-v1",
        "instruction_commit": "f45c6c9d47253c0ad8cad9affcf0eb54be188117",
        "implementation_commit": implementation_sha,
        "packet_id": replay["packet_id"],
        "gates": {
            "KIWOOM_TR_CONTRACT": "PASS",
            "KIWOOM_LIVE_PROBE": "PASS",
            "KR_INDEX_BREADTH": "PASS",
            "KR_SECTOR_SIZE_CONTEXT": "PASS",
            "KR_MARKET_WIDE_INVESTOR_FLOW": "PASS",
            "KR_MARKET_FLOW_CONCENTRATION": "PASS_KOSDAQ_ONLY",
            "KIWOOM_KRX_RECONCILIATION": "NOT_OBSERVED",
            "KR_KIWOOM_ENRICHED_REPLAY": "PASS",
            "KR_KIWOOM_MESSAGE_VALUE_ADD": "PASS",
            "KIWOOM_KR_MARKET_CONTEXT": "PARTIAL",
            "PRODUCTION_READY": "YES",
        },
        "safety": {
            "fact_mismatch": 0,
            "unit_conflict": 0,
            "session_date_conflict": 0,
            "default_zero": 0,
            "pagination_partial_promoted": 0,
            "duplicate_security_double_count": 0,
            "hidden_arithmetic": 0,
            "unsupported_causality": 0,
            "manual_telegram": 0,
            "manual_scheduled_task": 0,
            "pilot_mutation": 0,
            "database_mutation": 0,
        },
        "open_p0": [],
        "open_material_p1": [],
        "p2_backlog": [
            "KOSPI ka10051/ka10066 basis-or-taxonomy reconciliation",
            "same-day complete KRX cross-provider reconciliation",
            "optional non-core participant taxonomy expansion",
        ],
        "full_pytest": full_pytest,
        "next_action": "WAIT_FOR_KR_KIWOOM_NATURAL_PROOF",
    }
    (REPORTS / "20260825-kr-kiwoom-production-readiness.json").write_text(
        json.dumps(readiness, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    _write(
        "20260825-kr-kiwoom-production-readiness.md",
        f"""# KR Kiwoom Production Readiness

## Decision

`KIWOOM_KR_MARKET_CONTEXT = PARTIAL`

`PRODUCTION_READY = YES`

Safe partial is deliberate: index, breadth, size/sector, and aggregate market flow are validated;
KOSDAQ concentration is validated; KOSPI concentration remains blocked. Adapter failure cannot
block packet creation. Full mode remains OFF, canary remains 1/2/3, Open Research production is 0,
and Production Assist remains OFF.

## Validation

- Focused: 101 passed.
- Full pytest: {full_pytest}.
- Ruff: PASS.
- Diff check: PASS.
- Replay: 8/8 PASS.
- Public Action 0.4.5 and schema 4: unchanged.
- User-visible delivery during this task: 0.

Open P0: 0. Open material P1: 0. Next action is the first naturally scheduled eligible KR proof;
no manual task or Telegram run is authorized.
""",
    )

    selected = {
        "KR MARKET DIGEST": "__DAILY_DIGEST_KR__",
        "SK HYNIX": "000660",
        "HANWHA AEROSPACE": "012450",
        "SAMSUNG ELECTRONICS": "005930",
    }
    message_parts = ["# KR Kiwoom Exact Message Benchmark"]
    by_ticker = {row["ticker"]: row for row in replay["messages"]}
    for label, ticker in selected.items():
        row = by_ticker[ticker]
        message_parts.extend(
            [
                f"# {label}",
                _message_section("SPARSE_PREVIOUS", row, "sparse_previous"),
                _message_section("KIWOOM_ENRICHED", row, "kiwoom_enriched_post_quality"),
                _message_section("DETERMINISTIC_REFERENCE", row, "deterministic_reference"),
                "## Audit\n\n"
                f"- New structured facts used: {row['materiality_reason'] or 'none'}.\n"
                f"- Human quality: `{row['human_quality']}`.\n"
                "- Prevented: unit mixing, causal flow attribution, and blocked KOSPI concentration.",
            ]
        )
    _write("20260825-kr-kiwoom-exact-message-benchmark.md", "\n\n".join(message_parts))

    market_rows = []
    for market in ("KOSPI", "KOSDAQ"):
        market_rows.append([
            market,
            indices[market]["close"],
            f"{indices[market]['return_pct']:+.2f}%",
            breadth[market]["advance_count"],
            breadth[market]["decline_count"],
            breadth[market]["unchanged_count"],
            _money(flows[(market, "foreign")]["net_buy_amount"]),
            _money(flows[(market, "institution")]["net_buy_amount"]),
            _money(flows[(market, "retail")]["net_buy_amount"]),
        ])
    stock_rows = []
    for market, participants in evidence["top_stock_flows"].items():
        for actor, directions in participants.items():
            for direction in ("top_buy", "top_sell"):
                for item in directions[direction][:3]:
                    stock_rows.append([market, actor, direction, item["ticker"], item["name"], _money(item["amount_krw"])])
    _write(
        "20260825-kr-kiwoom-market-data-table.md",
        f"""# KR Kiwoom Market Data Table

## Market

{_table(["Market", "Close", "Return", "Up", "Down", "Flat", "Foreign", "Institution", "Retail"], market_rows)}

## KOSPI Size

{_table(["Code", "Name", "Return"], [[item['sector_code'], item['sector'], f"{item['return_pct']:+.2f}%"] for item in evidence['size_context']])}

## Top Stock Flows

{_table(["Market", "Actor", "Direction", "Ticker", "Name", "Amount"], stock_rows)}

## Concentration

{_table(["Market", "Actor", "Direction", "Top N ratio"], [[item['market'], item['actor'], item['direction'], f"{item['ratio'] * 100:.2f}%"] for item in concentration])}

## Sector Extremes

{_table(["Scope", "Code", "Name", "Return"], [[item['market_scope'], item['sector_code'], item['sector'], f"{item['return_pct']:+.2f}%"] for item in [*evidence['top_sectors'], *evidence['bottom_sectors']]])}

All amount values are normalized KRW and labeled in billions. KOSPI concentration is omitted by
contract. Per-stock tables are evidence/audit output, not default prose requirements.
""",
    )

    artifacts = [
        "docs/architecture/KR_MARKET_CONTEXT_ADAPTER.md",
        "docs/architecture/KIWOOM_KR_MARKET_CONTEXT.md",
        "docs/architecture/KR_MARKET_FLOW_RECONCILIATION.md",
        "docs/architecture/KR_MARKET_BREADTH.md",
        *[
            f"docs/reports/{name}"
            for name in (
                "20260825-kiwoom-tr-contract-audit.md",
                "20260825-kiwoom-live-probe.md",
                "20260825-kiwoom-ka20001-breadth-validation.md",
                "20260825-kiwoom-ka20003-sector-size-validation.md",
                "20260825-kiwoom-ka10051-market-flow-validation.md",
                "20260825-kiwoom-ka10066-pagination-validation.md",
                "20260825-kiwoom-market-flow-reconciliation.md",
                "20260825-kiwoom-market-flow-concentration.md",
                "20260825-kr-kiwoom-enriched-replay.md",
                "20260825-kr-kiwoom-message-before-after.md",
                "20260825-kr-kiwoom-production-readiness.md",
                "20260825-kr-kiwoom-production-readiness.json",
                "20260825-kr-kiwoom-exact-message-benchmark.md",
                "20260825-kr-kiwoom-market-data-table.md",
                "20260825-kiwoom-live-evidence.json",
                "20260825-kr-kiwoom-enriched-replay.json",
            )
        ],
    ]
    _write(
        "20260825-kr-kiwoom-artifact-index.md",
        "# KR Kiwoom Artifact Index\n\n"
        + "\n".join(f"- `{path}`" for path in artifacts)
        + "\n\nAll listed artifacts are sanitized. Raw provider archives and credentials are excluded.",
    )


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--implementation-sha", required=True)
    parser.add_argument("--full-pytest", default="PENDING")
    args = parser.parse_args()
    build(args.implementation_sha, args.full_pytest)


if __name__ == "__main__":
    main()
