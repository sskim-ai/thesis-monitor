from __future__ import annotations

import argparse
import asyncio
import hashlib
import json
import sqlite3
from collections.abc import Mapping
from datetime import date, datetime
from pathlib import Path

from app.services.night_futures import (
    NIGHT_FUTURES_SERIES,
    canonicalize_night_futures_market_summary,
    night_futures_context_row,
    summarize_night_futures,
)
from app.services.us_full_message_service import render_us_full_market_message
from app.services.us_market_message_quality_service import (
    validate_us_market_message_payload,
)
from scripts.kr_final_preenable_test_delivery import deliver_test_messages
from scripts.kr_market_preenable_evidence import audit_test_sink, load_env_values


CONTRACT = "us-night-futures-historical-fixture-v1"
NAMESPACE = "TEST_ONLY_US_NIGHT_FUTURES_HISTORICAL_FIXTURE"


def _read_json(path: Path) -> object:
    return json.loads(path.read_text(encoding="utf-8"))


def _json_default(value: object) -> str:
    if isinstance(value, (date, datetime)):
        return value.isoformat()
    raise TypeError(f"not JSON serializable: {type(value).__name__}")


def _write_json(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(
        json.dumps(
            value,
            ensure_ascii=False,
            indent=2,
            sort_keys=True,
            default=_json_default,
        )
        + "\n",
        encoding="utf-8",
    )
    temporary.replace(path)


def _sha_text(value: str) -> str:
    return hashlib.sha256(value.encode()).hexdigest()


def _historical_rows(database: Path, session: str) -> tuple[int, list[dict[str, object]]]:
    connection = sqlite3.connect(f"file:{database}?mode=ro", uri=True)
    try:
        records = connection.execute(
            """
            SELECT id, market_summary
            FROM macrobriefing
            WHERE briefing_type = 'morning'
            ORDER BY id DESC
            """
        ).fetchall()
    finally:
        connection.close()
    for briefing_id, raw_summary in records:
        summary = json.loads(str(raw_summary))
        observations = summary.get("observations")
        observations = observations if isinstance(observations, list) else []
        by_series = {
            str(row.get("series_code")): dict(row)
            for row in observations
            if isinstance(row, Mapping)
            and row.get("series_code") in NIGHT_FUTURES_SERIES
            and str(row.get("session_date") or "") == session
        }
        if set(by_series) != set(NIGHT_FUTURES_SERIES):
            continue
        rows = []
        for series in NIGHT_FUTURES_SERIES:
            row = by_series[series]
            row["expected_latest_session_date"] = session
            row["session_freshness"] = "fresh"
            rows.append(row)
        return int(briefing_id), rows
    raise ValueError(f"verified historical night-futures pair missing: {session}")


def build_fixture(
    *,
    database: Path,
    market_context_path: Path,
    session: str,
) -> tuple[dict[str, object], list[dict[str, object]]]:
    briefing_id, rows = _historical_rows(database, session)
    historical_market = {
        "items": [],
        "observations": rows,
        "night_futures_gate": {
            "query_attempted": True,
            "expected_session": session,
            "ready_products": list(NIGHT_FUTURES_SERIES),
            "state": "historical_fixture_ready",
        },
    }
    canonical = canonicalize_night_futures_market_summary(historical_market)
    summary = summarize_night_futures(canonical)
    if len(summary.items) != len(NIGHT_FUTURES_SERIES):
        raise ValueError("historical fixture failed canonical gate")
    context_rows = [night_futures_context_row(item) for item in summary.items]
    projections = [
        item for item in canonical["items"] if isinstance(item, Mapping)
    ]
    parity = all(
        projection.get("fact_id") == context.get("fact_id")
        and projection.get("field_path") == context.get("field_path")
        and projection.get("value") == context.get("change_pct")
        and projection.get("session") == session
        and projection.get("state") == context.get("state")
        for projection, context in zip(projections, context_rows, strict=True)
    )
    market_context = _read_json(market_context_path)
    if not isinstance(market_context, Mapping):
        raise ValueError("market context invalid")
    fixture_context = dict(market_context)
    fixture_context["night_futures"] = context_rows
    render = render_us_full_market_message(fixture_context)
    fixture_text = (
        f"TEST FIXTURE · {session} 야간선물 과거 세션 표시 검증\n"
        "실제 자연 발송 아님\n\n"
        f"{render.text}"
    )
    quality = validate_us_market_message_payload(fixture_text)
    checks = {
        "canonical_pair_count": len(summary.items),
        "summary_context_parity": parity,
        "fixed_fact_ids": [row["fact_id"] for row in context_rows]
        == ["market:night_futures:1", "market:night_futures:2"],
        "field_paths": [row["field_path"] for row in context_rows]
        == ["fields.change_pct", "fields.change_pct"],
        "night_section_visible": "🌙 한국 야간선물" in fixture_text,
        "historical_label_visible": fixture_text.startswith("TEST FIXTURE"),
        "render_status": render.status,
        "quality_status": quality.status,
    }
    status = "PASS" if all(
        (
            checks["canonical_pair_count"] == 2,
            checks["summary_context_parity"],
            checks["fixed_fact_ids"],
            checks["field_paths"],
            checks["night_section_visible"],
            checks["historical_label_visible"],
            checks["render_status"] == "PASS",
            checks["quality_status"] == "PASS",
        )
    ) else "FAIL"
    evidence = {
        "contract": CONTRACT,
        "status": status,
        "fixture_session": session,
        "source_briefing_id": briefing_id,
        "canonical_summary_projection": projections,
        "canonical_context_rows": context_rows,
        "render": render.to_dict(),
        "message": fixture_text,
        "message_sha256": _sha_text(fixture_text),
        "quality": quality.to_dict(),
        "checks": checks,
    }
    messages = [
        {
            "ticker": "__NIGHT_FUTURES_FIXTURE__",
            "route": "FIXTURE",
            "text": fixture_text,
            "logical_identity": f"{NAMESPACE}:{session}",
        }
    ]
    return evidence, messages


async def _run(args: argparse.Namespace) -> None:
    evidence, messages = build_fixture(
        database=args.database,
        market_context_path=args.market_context,
        session=args.fixture_session,
    )
    env = load_env_values(args.env_file)
    sink = audit_test_sink(env)
    if sink.get("available") is not True:
        raise ValueError(f"test sink unavailable: {sink.get('reason')}")
    evidence["test_sink"] = sink
    _write_json(args.output, evidence)
    summary: dict[str, object] = {
        "contract": CONTRACT,
        "status": evidence["status"],
        "fixture_session": args.fixture_session,
        "test_sink_alias": sink["test_sink_alias"],
        "production_sink_alias": sink["production_sink_alias"],
        "production_collision": sink["production_collision"],
    }
    if args.send:
        if evidence["status"] != "PASS":
            raise ValueError("historical fixture preflight failed")
        selected_key = str(sink.get("selected_test_key_name") or "")
        receipt = await deliver_test_messages(
            messages,
            token=env.get("TELEGRAM_BOT_TOKEN") or "",
            test_chat_id=env.get(selected_key) or "",
            production_chat_id=env.get("TELEGRAM_CHAT_ID") or "",
            test_sink_alias=str(sink["test_sink_alias"]),
            production_sink_alias=str(sink["production_sink_alias"]),
            receipt_path=args.receipt,
            contract=CONTRACT,
            namespace=NAMESPACE,
            received_payload_validator=lambda text: validate_us_market_message_payload(
                text
            ).to_dict(),
        )
        summary["delivery"] = {
            "status": receipt["status"],
            "sent_message_count": receipt["sent_message_count"],
            "exact_payload_match": receipt["exact_payload_match"],
        }
    print(json.dumps(summary, ensure_ascii=False, sort_keys=True))


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--database", type=Path, required=True)
    parser.add_argument("--market-context", type=Path, required=True)
    parser.add_argument("--env-file", type=Path, required=True)
    parser.add_argument("--fixture-session", required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--receipt", type=Path, required=True)
    parser.add_argument("--send", action="store_true")
    asyncio.run(_run(parser.parse_args()))


if __name__ == "__main__":
    main()
