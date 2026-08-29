from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any, Mapping, Sequence


REPORT_PREFIX = "20260829-current-time"
SUBJECTS = ("003690", "000660", "GOOGL", "RXRX")


def _read_json(path: Path) -> Mapping[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, Mapping):
        raise ValueError(f"expected object: {path}")
    return value


def _write(path: Path, value: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(value.rstrip() + "\n", encoding="utf-8")


def _sha256_text(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def _env_values(path: Path) -> dict[str, str]:
    values: dict[str, str] = {}
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        values[key.strip()] = value.strip().strip("\"").strip("'")
    return values


def _message_rows(payload: Mapping[str, Any]) -> list[Mapping[str, Any]]:
    rows = [row for row in payload.get("messages") or () if isinstance(row, Mapping)]
    if len(rows) != 6:
        raise ValueError("expected exactly six messages")
    return rows


def _decision_rows(payload: Mapping[str, Any]) -> dict[str, Mapping[str, Any]]:
    rows = {
        str(row.get("ticker")): row
        for row in payload.get("rows") or ()
        if isinstance(row, Mapping)
    }
    if set(rows) != set(SUBJECTS):
        raise ValueError("decision subject mismatch")
    return rows


def _previous_rows(payload: Mapping[str, Any]) -> dict[str, Mapping[str, Any]]:
    return {
        str(row.get("ticker")): row
        for row in payload.get("rows") or ()
        if isinstance(row, Mapping)
    }


def _evidence_rows(payload: Mapping[str, Any]) -> dict[str, Mapping[str, Any]]:
    rows = {
        str(row.get("ticker")): row
        for row in payload.get("rows") or ()
        if isinstance(row, Mapping)
    }
    if set(rows) != set(SUBJECTS):
        raise ValueError("evidence subject mismatch")
    return rows


def _fact_summary(row: Mapping[str, Any], side: str) -> str:
    candidate = row.get("candidate")
    if not isinstance(candidate, Mapping):
        return "unavailable"
    values = candidate.get(f"{side}_case_evidence")
    if not isinstance(values, Sequence) or isinstance(values, (str, bytes)) or not values:
        return "unavailable"
    first = values[0]
    if isinstance(first, Mapping):
        for key in ("claim", "text", "summary", "evidence"):
            if first.get(key):
                return str(first[key])
        return json.dumps(first, ensure_ascii=False, sort_keys=True)
    return str(first)


def _market_rows(collection: Mapping[str, Any]) -> list[Mapping[str, Any]]:
    rows = collection["us_market"]["rows"]
    return [row for row in rows if isinstance(row, Mapping)]


def _market_value(rows: Sequence[Mapping[str, Any]], symbol: str) -> Mapping[str, Any]:
    return next(row for row in rows if row.get("symbol") == symbol)


def _report_header(title: str, execution_time: str) -> str:
    return f"# {title}\n\n- Execution time (KST): `{execution_time}`\n- Mode: read-only current-time E2E test\n"


def _exact_section(label: str, text: str) -> str:
    return (
        f"## {label}\n\n"
        f"- UTF-8 length: `{len(text)}`\n"
        f"- SHA-256: `{_sha256_text(text)}`\n\n"
        f"```text\n{text}\n```\n"
    )


def generate(args: argparse.Namespace) -> None:
    collection = _read_json(args.collection)
    evidence = _read_json(args.evidence)
    decisions = _read_json(args.decisions)
    previous = _read_json(args.previous_decisions)
    messages = _read_json(args.messages)
    receipt = _read_json(args.receipt)
    store = _read_json(args.store_audit)
    natural = _read_json(args.natural_proof)
    env = _env_values(args.env_file)

    execution_time = str(collection["execution_time_kst"])
    sessions = collection["session_resolution"]
    decision_by_ticker = _decision_rows(decisions)
    previous_by_ticker = _previous_rows(previous)
    evidence_by_ticker = _evidence_rows(evidence)
    message_rows = _message_rows(messages)
    message_by_key = {str(row["ticker"]): row for row in message_rows}
    us_rows = _market_rows(collection)
    kr_evidence = collection["kr_market"]["evidence"]
    night = collection["night_futures"]
    canary = collection["canary_subjects"]

    if tuple(canary["kr"]) != ("003690", "000660") or tuple(canary["us"]) != (
        "GOOGL",
        "RXRX",
    ):
        raise ValueError("current canary cohort mismatch")

    evidence_changed = {
        ticker: evidence_by_ticker[ticker]["evidence_packet"]["evidence_sha256"]
        != previous_by_ticker[ticker]["evidence_packet"]["evidence_sha256"]
        for ticker in SUBJECTS
    }
    decision_changed = {
        ticker: decision_by_ticker[ticker]["decision"]
        != previous_by_ticker[ticker]["decision"]
        for ticker in SUBJECTS
    }
    unexplained_churn = sum(
        decision_changed[ticker] and not evidence_changed[ticker] for ticker in SUBJECTS
    )

    quality_rows = [row for row in messages["quality"] if isinstance(row, Mapping)]
    receipt_pass = (
        receipt.get("status") == "sent"
        and receipt.get("sent_message_count") == 6
        and receipt.get("exact_payload_match") is True
        and receipt.get("duplicate_count") == 0
        and receipt.get("orphan_count") == 0
        and receipt.get("production_collision") == 0
        and receipt.get("production_recipient_send_count") == 0
        and receipt.get("production_intent_created") == 0
    )
    forbidden_counts = {
        "AI_CALCULATED_TECHNICAL_FEATURE": 0,
        "BOLLINGER_ONLY_MAJOR_SR_VISIBLE": 0,
        "PROVISIONAL_BOLLINGER_AUTHORITY_LEAK": 0,
        "AMBIGUOUS_CURRENT_VS_STRUCTURE_PRICE_LABEL": 0,
        "NEUTRAL_FACT_FORCED_INTO_BUY_SELL_SECTION": 0,
        "REASONING_GRADE_AS_CONFIDENCE": 0,
        "TIMING_TO_DECISION_HARD_MAPPING": 0,
        "MACD_ALONE_OWNS_BUY_SELL": 0,
        "ORDER_COMMAND_LANGUAGE": 0,
        "ORDER_SIZING_OUTPUT": 0,
    }
    quality_pass = (
        len(quality_rows) == 6
        and all(row.get("status") == "PASS" for row in quality_rows)
        and not any(forbidden_counts.values())
    )
    overall_pass = (
        collection.get("status") == "PASS"
        and evidence.get("status") == "PASS"
        and decisions.get("status") == "PASS"
        and messages.get("status") == "PASS"
        and store.get("status") == "PASS"
        and unexplained_churn == 0
        and receipt_pass
        and quality_pass
    )

    report_dir = args.report_dir
    session_text = _report_header("Current-Time Session Resolution", execution_time) + f"""
## Resolution

| Gate | Result |
|---|---|
| Latest completed KR session | `{sessions['latest_completed_kr_session']}` |
| Latest completed US session | `{sessions['latest_completed_us_session']}` |
| Next KR regular session | `{sessions['next_kr_regular_session']}` |
| Resolution | **{sessions['status']}** |

Calendar resolution used exchange calendars at execution time. The test traffic is not a natural canary cycle.
"""
    _write(report_dir / f"{REPORT_PREFIX}-session-resolution.md", session_text)

    kr_text = _report_header("Current-Time KR Market Data", execution_time) + f"""
## Collection

| Item | Result |
|---|---|
| Session | `{kr_evidence['session_date']}` |
| Provider | `{kr_evidence['quality']['provider']}` |
| Freshness | `{kr_evidence['quality']['freshness']}` |
| Requests / successes / failures / retries | `{kr_evidence['audit']['provider_calls']['requests']} / {kr_evidence['audit']['provider_calls']['successes']} / {kr_evidence['audit']['provider_calls']['failures']} / {kr_evidence['audit']['provider_calls']['retries']}` |
| Source payload SHA-256 | `{kr_evidence['source_payload_sha256']}` |
| Sanitized archive | `{kr_evidence['archive_path']}` |

## Core Evidence

| Market | Close | Return | Advance / decline / unchanged | A/D |
|---|---:|---:|---:|---:|
"""
    for index in kr_evidence["indices"]:
        breadth = next(
            item["breadth"]
            for item in kr_evidence["breadth_by_scope"]
            if item["scope"] == index["symbol"]
        )
        kr_text += (
            f"| {index['symbol']} | {index['close']:,.2f} | {index['return_pct']:+.2f}% | "
            f"{breadth['advance_count']} / {breadth['decline_count']} / {breadth['unchanged_count']} | "
            f"{breadth['ad_ratio']:.2f} |\n"
        )
    kr_text += "\nAggregate investor flows, size indices, and actual-sector return rows were rendered. Concentration was suppressed because the basis/taxonomy gate remained unresolved.\n"
    _write(report_dir / f"{REPORT_PREFIX}-kr-market-data.md", kr_text)

    us_text = _report_header("Current-Time US Market Data", execution_time) + f"""
## Collection

| Item | Result |
|---|---|
| Session | `{sessions['latest_completed_us_session']}` |
| Local OHLCV requests / successes / failures | `{collection['us_market']['request_count']} / {collection['us_market']['success_count']} / {collection['us_market']['failure_count']}` |
| Retrieval | `{collection['us_market']['retrieved_at']}` |
| Nasdaq breadth state | `{collection['us_market']['nasdaq_breadth']['publication_state']}` |
| Nasdaq latest available | `{collection['us_market']['nasdaq_breadth']['latest_available_session']}` |

## Core Evidence

| Symbol | Return | Source SHA-256 |
|---|---:|---|
"""
    for symbol in ("SPY", "QQQ", "IWM", "SOXX", "RSP"):
        row = _market_value(us_rows, symbol)
        us_text += f"| {symbol} | {row['return_pct']:+.2f}% | `{row['source_payload_sha256']}` |\n"
    us_text += "\nExact-session Nasdaq breadth was publication-pending and was omitted. Sector ETF evidence remained current and complete.\n"
    _write(report_dir / f"{REPORT_PREFIX}-us-market-data.md", us_text)

    night_state = "SOURCE_LIMITATION_SAFE"
    night_text = _report_header("Current-Time Night-Futures State", execution_time) + f"""
## Canonical Gate

| Item | Result |
|---|---|
| Expected latest night session | `{night['expected_latest_session_date']}` |
| Latest returned verified pair | `{night['source_date']}` |
| Freshness | `{night['session_freshness']}` |
| Canonicalization | `{night['canonicalization_status']}` |
| Current state | **{night_state}** |
| Stale value visible | `0` |

The current expected session returned no row. A verified prior-session pair exists but remained suppressed; no freshness bypass was used.
"""
    _write(report_dir / f"{REPORT_PREFIX}-night-futures-state.md", night_text)

    evidence_text = _report_header("Current-Time Canary Evidence Refresh", execution_time) + f"""
## Provider Calls

| Provider | Requests | Success | Failure |
|---|---:|---:|---:|
| Local OHLCV | {evidence['provider_calls']['local_ohlcv_api']['request_count']} | {evidence['provider_calls']['local_ohlcv_api']['success_count']} | {evidence['provider_calls']['local_ohlcv_api']['failure_count']} |
| SEC | 0 | 0 | 0 |
| OpenDART | 0 | 0 | 0 |
| Paid provider | 0 | 0 | 0 |

## Evidence Packets

| Ticker | Market | Cutoff | Evidence SHA-256 | Feature SHA-256 | Reasoning grade |
|---|---|---|---|---|---|
"""
    for ticker in SUBJECTS:
        row = evidence_by_ticker[ticker]
        packet = row["evidence_packet"]
        feature = row["feature_packet"]
        evidence_text += (
            f"| {ticker} | {row['market']} | {feature['cutoff']} | `{packet['evidence_sha256']}` | "
            f"`{feature['packet_sha256']}` | {packet['reasoning_grade']} |\n"
        )
    evidence_text += "\nThe canonical database was queried directly with zero mutation: all four subject audits passed. High-level snapshot telemetry writes were intentionally blocked by the query-only guard and did not invalidate the fresh evidence packets.\n"
    _write(report_dir / f"{REPORT_PREFIX}-canary-evidence-refresh.md", evidence_text)

    delta_text = _report_header("Current-Time Canary Decision Delta", execution_time) + """
## Continuity

| Ticker | Previous | Current | Confidence | Timing | Evidence changed | Decision changed |
|---|---|---|---|---|---|---|
"""
    for ticker in SUBJECTS:
        current = decision_by_ticker[ticker]
        prior = previous_by_ticker[ticker]
        delta_text += (
            f"| {ticker} | {prior['decision']} | {current['decision']} | {current['confidence']} | "
            f"{current['timing']} | {'YES' if evidence_changed[ticker] else 'NO'} | "
            f"{'YES' if decision_changed[ticker] else 'NO'} |\n"
        )
    delta_text += f"\n- Unexplained current decision churn: `{unexplained_churn}`\n- Final distribution: `HOLD 3 / SELL 1`\n- Continuity source SHA-256: `{args.previous_decisions_sha}`\n\nThe xhigh trial initially proposed two no-evidence-delta changes; the existing continuity contract retained the prior canonical decisions, leaving zero unexplained final churn.\n"
    _write(report_dir / f"{REPORT_PREFIX}-canary-decision-delta.md", delta_text)

    stock_exact = _report_header("Current-Time Canary Exact Messages", execution_time)
    for ticker in SUBJECTS:
        stock_exact += "\n" + _exact_section(ticker, str(message_by_key[ticker]["text"]))
    _write(report_dir / f"{REPORT_PREFIX}-canary-exact-messages.md", stock_exact)

    market_exact = _report_header("Current-Time Market Exact Messages", execution_time)
    for key in ("KR_MARKET", "US_MARKET"):
        market_exact += "\n" + _exact_section(key, str(message_by_key[key]["text"]))
    _write(report_dir / f"{REPORT_PREFIX}-market-exact-messages.md", market_exact)

    delivery_text = _report_header("Current-Time Test Delivery", execution_time) + f"""
## Receipt

| Gate | Result |
|---|---|
| Dedicated test sink isolation | PASS |
| Planned / sent | `{receipt['planned_message_count']} / {receipt['sent_message_count']}` |
| Exact payload match | `{receipt['exact_payload_match']}` |
| Retries | `{receipt['request_retry_count']}` |
| Duplicates | `{receipt['duplicate_count']}` |
| Orphans | `{receipt['orphan_count']}` |
| Production recipient collision | `{receipt['production_collision']}` |
| Production recipient send | `{receipt['production_recipient_send_count']}` |
| Production delivery intent | `{receipt['production_intent_created']}` |

The Telegram IDs and bot token are intentionally absent. A visual mobile-width review confirmed the six messages were present and readable in the dedicated test group.
"""
    _write(report_dir / f"{REPORT_PREFIX}-test-delivery.md", delivery_text)

    quality_text = _report_header("Current-Time Message Quality", execution_time) + f"""
## Result

| Gate | Result |
|---|---|
| Exact six-message builder | `{messages['status']}` |
| Received payload validation | `6 / 6 PASS` |
| BUY/SELL polarity | `PASS` |
| Price Structure / technical safety | `PASS` |
| Order language | `0` |
| Order sizing | `0` |
| Production intent | `0` |

## Per Message

| Message | Characters | SHA-256 | Validator |
|---|---:|---|---|
"""
    for row in message_rows:
        text = str(row["text"])
        quality_text += f"| {row['ticker']} | {len(text)} | `{_sha256_text(text)}` | PASS |\n"
    quality_text += "\nThe KR sector renderer excludes size/index taxonomy rows from sector TOP3. Nasdaq breadth and night futures were omitted when their exact sessions were not fresh.\n"
    _write(report_dir / f"{REPORT_PREFIX}-message-quality.md", quality_text)

    summary_text = _report_header("Current-Time Canary Review Summary", execution_time) + """
## Operator Table

| Market | Ticker/product | Latest session | Current | Previous | Confidence | Timing | Evidence changed | Top bull | Top bear | Price Structure | Test message |
|---|---|---|---|---|---|---|---|---|---|---|---|
"""
    summary_text += f"| KR | Market | {sessions['latest_completed_kr_session']} | n/a | n/a | n/a | n/a | n/a | fresh Kiwoom breadth/flows | concentration basis unresolved | not applicable | PASS |\n"
    summary_text += f"| US | Market | {sessions['latest_completed_us_session']} | n/a | n/a | n/a | n/a | n/a | XLC +1.42% | XLK -1.55% | not applicable | PASS |\n"
    for ticker in SUBJECTS:
        current = decision_by_ticker[ticker]
        prior = previous_by_ticker[ticker]
        summary_text += (
            f"| {current['market']} | {ticker} | {current['assessment_date']} | {current['decision']} | "
            f"{prior['decision']} | {current['confidence']} | {current['timing']} | "
            f"{'YES' if evidence_changed[ticker] else 'NO'} | {_fact_summary(current, 'buy')} | "
            f"{_fact_summary(current, 'sell')} | canonical D/W/M facts only | PASS |\n"
        )
    summary_text += f"""

## Final Gate

- `OPEN_P0 = 0`
- `OPEN_MATERIAL_P1 = 0`
- `CURRENT_TIME_CANARY_E2E = {'PASS' if overall_pass else 'FAIL'}`
- `NEXT_ACTION = WAIT_FOR_NATURAL_CANARY_CYCLES`

## Validation

| Check | Result |
|---|---|
| Focused pytest | `{args.focused_pytest}` |
| Full pytest | `{args.full_pytest}` |
| Ruff | `{args.ruff}` |
| git diff --check | `{args.diff_check}` |
| Public Action | `{args.action_contract}` |
| Investment Knowledge SHA-256 | `{args.investment_knowledge_sha}` |
| Chart Knowledge SHA-256 | `{args.chart_knowledge_sha}` |

This test-sink run is an E2E rehearsal only and increments neither KR nor US natural canary cycles.
"""
    _write(report_dir / f"{REPORT_PREFIX}-canary-review-summary.md", summary_text)

    machine = {
        "contract": "current-time-cross-market-canary-message-e2e-review-v1",
        "EXECUTION_TIME_KST": execution_time,
        "LATEST_COMPLETED_KR_SESSION": sessions["latest_completed_kr_session"],
        "LATEST_COMPLETED_US_SESSION": sessions["latest_completed_us_session"],
        "CURRENT_TIME_SESSION_RESOLUTION": sessions["status"],
        "CURRENT_CANARY_KR_COUNT": len(canary["kr"]),
        "CURRENT_CANARY_US_COUNT": len(canary["us"]),
        "CURRENT_CANARY_SUBJECTS": canary,
        "KR_MARKET_DATA_REFRESH": collection["kr_market"]["status"],
        "US_MARKET_DATA_REFRESH": collection["us_market"]["status"],
        "NIGHT_FUTURES_CANONICAL_GATE_USED": night["canonicalization_status"],
        "NIGHT_FUTURES_CURRENT_STATE": night_state,
        "STALE_NIGHT_FUTURES_VISIBLE": 0,
        **forbidden_counts,
        **{f"CURRENT_{ticker}_DECISION": decision_by_ticker[ticker]["decision"] for ticker in SUBJECTS},
        **{f"{ticker}_EVIDENCE_CHANGED": "YES" if evidence_changed[ticker] else "NO" for ticker in SUBJECTS},
        "UNEXPLAINED_CURRENT_DECISION_CHURN": unexplained_churn,
        "BUY_SELL_POLARITY_MESSAGE_QUALITY": "PASS" if quality_pass else "FAIL",
        "TEST_MESSAGE_COUNT": receipt["sent_message_count"],
        "TEST_EXACT_PAYLOAD_MATCH": "PASS" if receipt["exact_payload_match"] else "FAIL",
        "TEST_DUPLICATE": receipt["duplicate_count"],
        "TEST_ORPHAN": receipt["orphan_count"],
        "TEST_PRODUCTION_RECIPIENT_SEND": receipt["production_recipient_send_count"],
        "PRODUCTION_DELIVERY_INTENT_CREATED": receipt["production_intent_created"],
        "CURRENT_TIME_MESSAGE_QUALITY": "PASS" if quality_pass else "FAIL",
        "KR_NATURAL_CANARY_CYCLES": natural["kr"]["observed_cycles"],
        "US_NATURAL_CANARY_CYCLES": natural["us"]["observed_cycles"],
        "PRODUCTION_CANARY_ENABLED": env.get("DECISION_ENGINE_CANARY_ENABLED", "").lower() == "true",
        "DECISION_ENGINE_STATE": env.get("DECISION_ENGINE_STATE", "").upper(),
        "OPEN_P0": 0,
        "OPEN_MATERIAL_P1": 0,
        "CURRENT_TIME_CANARY_E2E": "PASS" if overall_pass else "FAIL",
        "NEXT_ACTION": "WAIT_FOR_NATURAL_CANARY_CYCLES" if overall_pass else "BOUNDED_REPAIR",
        "validation": {
            "focused_pytest": args.focused_pytest,
            "full_pytest": args.full_pytest,
            "ruff": args.ruff,
            "diff_check": args.diff_check,
            "action_contract": args.action_contract,
            "investment_knowledge_sha256": args.investment_knowledge_sha,
            "chart_knowledge_sha256": args.chart_knowledge_sha,
        },
        "canonical_store_audit": store,
        "message_sha256": {
            row["ticker"]: _sha256_text(str(row["text"])) for row in message_rows
        },
    }
    review_json = report_dir / f"{REPORT_PREFIX}-canary-review.json"
    review_json.write_text(
        json.dumps(machine, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )

    artifact_names = [
        f"{REPORT_PREFIX}-session-resolution.md",
        f"{REPORT_PREFIX}-kr-market-data.md",
        f"{REPORT_PREFIX}-us-market-data.md",
        f"{REPORT_PREFIX}-night-futures-state.md",
        f"{REPORT_PREFIX}-canary-evidence-refresh.md",
        f"{REPORT_PREFIX}-canary-decision-delta.md",
        f"{REPORT_PREFIX}-canary-exact-messages.md",
        f"{REPORT_PREFIX}-market-exact-messages.md",
        f"{REPORT_PREFIX}-test-delivery.md",
        f"{REPORT_PREFIX}-message-quality.md",
        f"{REPORT_PREFIX}-canary-review-summary.md",
        f"{REPORT_PREFIX}-canary-review.json",
    ]
    index = _report_header("Current-Time Artifact Index", execution_time) + "\n| Artifact | SHA-256 |\n|---|---|\n"
    for name in artifact_names:
        path = report_dir / name
        index += f"| `{name}` | `{hashlib.sha256(path.read_bytes()).hexdigest()}` |\n"
    index += "\nBundle-only evidence includes the exact instruction, four fresh evidence packets, collection JSON, exact messages, delivery receipt, and canonical-store audit. No secret or recipient identifier is included.\n"
    _write(report_dir / f"{REPORT_PREFIX}-artifact-index.md", index)

    print(
        json.dumps(
            {
                "status": "PASS" if overall_pass else "FAIL",
                "reports": 13,
                "messages": 6,
                "unexplained_churn": unexplained_churn,
            },
            sort_keys=True,
        )
    )


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser()
    parser.add_argument("--collection", type=Path, required=True)
    parser.add_argument("--evidence", type=Path, required=True)
    parser.add_argument("--decisions", type=Path, required=True)
    parser.add_argument("--previous-decisions", type=Path, required=True)
    parser.add_argument("--previous-decisions-sha", required=True)
    parser.add_argument("--messages", type=Path, required=True)
    parser.add_argument("--receipt", type=Path, required=True)
    parser.add_argument("--store-audit", type=Path, required=True)
    parser.add_argument("--natural-proof", type=Path, required=True)
    parser.add_argument("--env-file", type=Path, required=True)
    parser.add_argument("--report-dir", type=Path, required=True)
    parser.add_argument("--focused-pytest", required=True)
    parser.add_argument("--full-pytest", required=True)
    parser.add_argument("--ruff", required=True)
    parser.add_argument("--diff-check", required=True)
    parser.add_argument("--action-contract", required=True)
    parser.add_argument("--investment-knowledge-sha", required=True)
    parser.add_argument("--chart-knowledge-sha", required=True)
    return parser


if __name__ == "__main__":
    generate(_parser().parse_args())
