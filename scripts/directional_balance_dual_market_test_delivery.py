from __future__ import annotations

import argparse
import asyncio
import hashlib
import json
import re
from collections.abc import Mapping
from pathlib import Path

from app.config import get_settings
from app.services.accepted_decision_v2_runtime_service import (
    REASONING_EFFORT,
    REASONING_MODEL,
    AcceptedV2ProductionArtifact,
)
from app.services.us_full_message_service import render_us_full_market_message
from app.services.us_market_message_quality_service import (
    validate_us_market_message_payload,
)
from scripts.kr_final_preenable_test_delivery import deliver_test_messages
from scripts.kr_market_preenable_evidence import audit_test_sink, load_env_values
from scripts.v2_production_cutover_preflight import _production_payloads


CONTRACT = "directional-balance-dual-market-test-delivery-v1"
NAMESPACE = "DIRECTIONAL_BALANCE_DUAL_MARKET_TEST_ONLY"
BALANCE_LINE = re.compile(
    r"^판단 균형: BUY (?P<buy>\d+(?:\.5)?) : SELL (?P<sell>\d+(?:\.5)?)$",
    re.MULTILINE,
)
TREASURY_SERIES = ("DGS3", "DGS5", "DGS10", "DGS30")


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


def _sha256_text(value: str) -> str:
    return hashlib.sha256(value.encode()).hexdigest()


def _sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _file_fingerprint(path: Path) -> dict[str, object]:
    return {
        "exists": path.exists(),
        "size": path.stat().st_size if path.exists() else None,
        "sha256": _sha256_file(path) if path.exists() else None,
    }


def _tree_fingerprint(path: Path) -> dict[str, object]:
    rows = [
        {
            "path": str(item.relative_to(path)),
            "size": item.stat().st_size,
            "sha256": _sha256_file(item),
        }
        for item in sorted(path.rglob("*"))
        if item.is_file()
    ]
    encoded = json.dumps(rows, sort_keys=True, separators=(",", ":")).encode()
    return {
        "exists": path.exists(),
        "file_count": len(rows),
        "sha256": hashlib.sha256(encoded).hexdigest(),
    }


def _production_snapshot(
    production_root: Path,
    *,
    us_packet_dir: Path,
    kr_packet_dir: Path,
) -> dict[str, object]:
    return {
        "contract": "directional-balance-production-mutation-snapshot-v1",
        "us_packet_archive": _tree_fingerprint(us_packet_dir),
        "kr_packet_archive": _tree_fingerprint(kr_packet_dir),
        "accepted_decision_state": _file_fingerprint(
            production_root / "data/ai_review/decision_v2/state.json"
        ),
        "pilot_state_v3": _file_fingerprint(
            production_root / "data/ai_review/pilot/state-v3.json"
        ),
        "data_database": _file_fingerprint(
            production_root / "data/thesis_monitor.sqlite3"
        ),
        "root_database": _file_fingerprint(production_root / "thesis_monitor.sqlite3"),
    }


def _treasury_facts(fixture: Mapping[str, object]) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    for item in fixture.get("observations") or ():
        if not isinstance(item, Mapping):
            continue
        series = str(item.get("series_code") or "")
        if series not in TREASURY_SERIES:
            continue
        current = float(item["current_pct"])
        previous = float(item["previous_pct"])
        current_date = str(item["current_date"])
        rows.append(
            {
                "fact_id": f"market:nominal_yield:{series}",
                "fact_type": "market_nominal_yield",
                "as_of_date": current_date,
                "fields": {
                    "series_code": series,
                    "label": str(item["label"]),
                    "level_pct": current,
                    "previous_level_pct": previous,
                    "previous_observation_date": str(item["previous_date"]),
                    "change_bp": round((current - previous) * 100, 8),
                    "temporal_role": "CURRENT_OBSERVATION",
                    "today_signal_eligible": True,
                    "structured_state": "CURRENT_DIRECTIONAL",
                },
            }
        )
    if {row["fields"]["series_code"] for row in rows} != set(TREASURY_SERIES):
        raise ValueError("dual_market_treasury_fixture_incomplete")
    return rows


def _us_market_message(packet: Mapping[str, object], fixture: Mapping[str, object]) -> str:
    context = dict(packet.get("market_context") or {})
    facts = [dict(row) for row in context.get("fact_catalog") or () if isinstance(row, Mapping)]
    facts = [
        row
        for row in facts
        if not (
            row.get("fact_type") == "market_nominal_yield"
            and isinstance(row.get("fields"), Mapping)
            and row["fields"].get("series_code") in TREASURY_SERIES
        )
    ]
    facts.extend(_treasury_facts(fixture))
    context["fact_catalog"] = facts
    rendered = render_us_full_market_message(context)
    quality = validate_us_market_message_payload(rendered.text)
    if (
        rendered.status != "PASS"
        or quality.status != "PASS"
        or rendered.night_fact_ids
        or len(rendered.treasury_fact_ids) != 4
        or "야간선물" in rendered.text
    ):
        raise ValueError("dual_market_us_market_message_failed")
    return rendered.text


def _deterministic_market_message(path: Path, marker: str) -> str:
    rows = _read_json(path).get("messages") or ()
    match = next(
        (
            row
            for row in rows
            if isinstance(row, Mapping) and str(row.get("ticker") or "") == marker
        ),
        None,
    )
    payload = match.get("payload") if isinstance(match, Mapping) else None
    text = str(payload.get("text") or "") if isinstance(payload, Mapping) else ""
    if not text:
        raise ValueError(f"dual_market_deterministic_market_missing:{marker}")
    return text


def _artifact(path: Path, market: str) -> AcceptedV2ProductionArtifact:
    artifact = AcceptedV2ProductionArtifact.model_validate(_read_json(path))
    if (
        artifact.market != market
        or artifact.status != "PASS"
        or artifact.ready_count != len(artifact.selected_subjects)
        or artifact.not_ready_count != 0
        or artifact.reasoning_model != REASONING_MODEL
        or artifact.reasoning_effort != REASONING_EFFORT
        or artifact.message_quality.get("status") != "PASS"
    ):
        raise ValueError(f"dual_market_artifact_not_ready:{market}")
    return artifact


def _messages(args: argparse.Namespace) -> tuple[list[dict[str, object]], dict[str, object]]:
    us_artifact = _artifact(args.us_artifact, "us")
    kr_artifact = _artifact(args.kr_artifact, "kr")
    us_packet = _read_json(args.us_packet)
    kr_packet = _read_json(args.kr_packet)
    if (
        us_artifact.packet_id != us_packet.get("packet_id")
        or kr_artifact.packet_id != kr_packet.get("packet_id")
    ):
        raise ValueError("dual_market_packet_artifact_identity_mismatch")

    stock_rows = _production_payloads(
        (us_artifact, kr_artifact),
        (args.us_deterministic, args.kr_deterministic),
    )
    by_ticker = {str(row["ticker"]): dict(row) for row in stock_rows}
    if len(by_ticker) != len(stock_rows):
        raise ValueError("dual_market_stock_payload_duplicate")

    us_market = _us_market_message(us_packet, _read_json(args.treasury_fixture))
    kr_market = _deterministic_market_message(
        args.kr_deterministic,
        "__DAILY_DIGEST_KR__",
    )
    messages: list[dict[str, object]] = []
    for market, artifact, market_text in (
        ("us", us_artifact, us_market),
        ("kr", kr_artifact, kr_market),
    ):
        messages.append(
            {
                "ticker": f"MARKET_{market.upper()}",
                "market": market,
                "route": "MARKET_CURRENT_RENDER",
                "text": market_text,
                "logical_identity": f"{NAMESPACE}:{artifact.packet_id}:MARKET",
                "rendered_sha256": _sha256_text(market_text),
            }
        )
        for ticker in artifact.selected_subjects:
            row = by_ticker.get(ticker)
            if row is None:
                raise ValueError(f"dual_market_stock_payload_missing:{ticker}")
            row["market"] = market
            row["logical_identity"] = f"{NAMESPACE}:{artifact.packet_id}:{ticker}"
            messages.append(row)

    stock_messages = [row for row in messages if not str(row["ticker"]).startswith("MARKET_")]
    balance_matches = [BALANCE_LINE.findall(str(row["text"])) for row in stock_messages]
    balances_valid = all(
        len(matches) == 1 and float(matches[0][0]) + float(matches[0][1]) == 10
        for matches in balance_matches
    )
    identities = [str(row["logical_identity"]) for row in messages]
    checks = {
        "us_context_candidate_accepted_explicit": len(us_artifact.selected_subjects)
        == len(us_artifact.evidence_packets)
        == len(us_artifact.candidates)
        == len(us_artifact.accepted_plans)
        == len(us_artifact.blocks),
        "kr_context_candidate_accepted_explicit": len(kr_artifact.selected_subjects)
        == len(kr_artifact.evidence_packets)
        == len(kr_artifact.candidates)
        == len(kr_artifact.accepted_plans)
        == len(kr_artifact.blocks),
        "fallback_zero": all(row.get("route") == "V2_ACCEPTED" for row in stock_messages),
        "balance_visible_all_stocks": balances_valid,
        "message_count_exact": len(messages)
        == len(us_artifact.selected_subjects) + len(kr_artifact.selected_subjects) + 2,
        "logical_identity_unique": len(identities) == len(set(identities)),
        "telegram_length_valid": all(
            len(str(row["text"])) <= get_settings().telegram_message_max_chars
            for row in messages
        ),
        "us_night_futures_absent": "야간선물" not in us_market,
        "us_treasury_curve_present": all(
            f"• {years}년:" in us_market for years in (3, 5, 10, 30)
        ),
    }
    summary = {
        "contract": CONTRACT,
        "status": "PASS" if all(checks.values()) else "FAIL",
        "checks": checks,
        "markets": {
            "us": {
                "packet_id": us_artifact.packet_id,
                "subject_count": len(us_artifact.selected_subjects),
                "ready_count": us_artifact.ready_count,
                "message_count": len(us_artifact.selected_subjects) + 1,
            },
            "kr": {
                "packet_id": kr_artifact.packet_id,
                "subject_count": len(kr_artifact.selected_subjects),
                "ready_count": kr_artifact.ready_count,
                "message_count": len(kr_artifact.selected_subjects) + 1,
            },
        },
        "message_count": len(messages),
        "stock_message_count": len(stock_messages),
        "market_message_count": 2,
        "reasoning_model": REASONING_MODEL,
        "reasoning_effort": REASONING_EFFORT,
        "production_recipient_send": 0,
        "production_delivery_state_mutation": 0,
    }
    return messages, summary


def _received_quality(text: str) -> dict[str, object]:
    if text.startswith("🇺🇸 미국시장 마감"):
        return validate_us_market_message_payload(text).to_dict()
    if BALANCE_LINE.search(text):
        matches = BALANCE_LINE.findall(text)
        valid = len(matches) == 1 and float(matches[0][0]) + float(matches[0][1]) == 10
        return {"contract": "directional-balance-received-v1", "status": "PASS" if valid else "FAIL"}
    return {
        "contract": "kr-market-received-v1",
        "status": "PASS" if text.startswith("🇰🇷") and bool(text.strip()) else "FAIL",
    }


def _prepare(args: argparse.Namespace) -> None:
    messages, summary = _messages(args)
    values = load_env_values(args.env_file)
    sink = audit_test_sink(values)
    if sink.get("available") is not True or sink.get("production_collision") != 0:
        raise ValueError("dual_market_test_sink_unavailable_or_colliding")
    summary["test_sink"] = sink
    if summary["status"] != "PASS":
        raise ValueError("dual_market_pre_send_readiness_failed")
    args.output_dir.mkdir(parents=True, exist_ok=True)
    if (args.output_dir / "test-sink-receipt.json").exists():
        raise FileExistsError("dual_market_test_receipt_already_exists")
    _write_json(args.output_dir / "production-payloads.json", {"messages": messages})
    _write_json(args.output_dir / "pre-send-readiness.json", summary)
    _write_json(
        args.output_dir / "production-before.json",
        _production_snapshot(
            args.production_root,
            us_packet_dir=args.us_deterministic.parent,
            kr_packet_dir=args.kr_deterministic.parent,
        ),
    )
    print(json.dumps(summary, ensure_ascii=False, sort_keys=True))


async def _send(args: argparse.Namespace) -> None:
    readiness = _read_json(args.output_dir / "pre-send-readiness.json")
    if readiness.get("status") != "PASS":
        raise ValueError("dual_market_send_without_readiness")
    messages = [
        row
        for row in _read_json(args.output_dir / "production-payloads.json").get("messages") or ()
        if isinstance(row, Mapping)
    ]
    values = load_env_values(args.env_file)
    sink = audit_test_sink(values)
    if sink.get("available") is not True or sink.get("production_collision") != 0:
        raise ValueError("dual_market_test_sink_unavailable_or_colliding")
    selected_key = str(sink.get("selected_test_key_name") or "")
    receipt = await deliver_test_messages(
        messages,
        token=values.get("TELEGRAM_BOT_TOKEN", ""),
        test_chat_id=values.get(selected_key, ""),
        production_chat_id=values.get("TELEGRAM_CHAT_ID", ""),
        test_sink_alias=str(sink["test_sink_alias"]),
        production_sink_alias=str(sink["production_sink_alias"]),
        receipt_path=args.output_dir / "test-sink-receipt.json",
        contract=CONTRACT,
        namespace=NAMESPACE,
        received_payload_validator=_received_quality,
        inter_message_delay_seconds=3.2,
    )
    before = _read_json(args.output_dir / "production-before.json")
    after = _production_snapshot(
        args.production_root,
        us_packet_dir=args.us_deterministic.parent,
        kr_packet_dir=args.kr_deterministic.parent,
    )
    _write_json(args.output_dir / "production-after.json", after)
    mutation_diff = {
        key: before.get(key) != after.get(key)
        for key in (
            "us_packet_archive",
            "kr_packet_archive",
            "accepted_decision_state",
            "pilot_state_v3",
            "data_database",
            "root_database",
        )
    }
    final = {
        "contract": CONTRACT,
        "status": (
            "PASS"
            if receipt.get("status") == "sent"
            and receipt.get("sent_message_count") == len(messages)
            and receipt.get("exact_payload_match") is True
            and receipt.get("duplicate_count") == 0
            and receipt.get("production_recipient_send_count") == 0
            and not any(mutation_diff.values())
            else "FAIL"
        ),
        "planned_message_count": len(messages),
        "sent_message_count": receipt.get("sent_message_count"),
        "exact_payload_match": receipt.get("exact_payload_match"),
        "duplicate_count": receipt.get("duplicate_count"),
        "production_recipient_send": receipt.get("production_recipient_send_count", 0),
        "production_delivery_state_mutation": sum(mutation_diff.values()),
        "production_mutation_diff": mutation_diff,
        "test_sink_alias": sink.get("test_sink_alias"),
        "production_sink_alias": sink.get("production_sink_alias"),
    }
    _write_json(args.output_dir / "delivery-summary.json", final)
    print(json.dumps(final, ensure_ascii=False, sort_keys=True))


async def _run(args: argparse.Namespace) -> None:
    if args.command == "prepare":
        _prepare(args)
    else:
        await _send(args)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("command", choices=("prepare", "send"))
    parser.add_argument("--us-artifact", type=Path, required=True)
    parser.add_argument("--kr-artifact", type=Path, required=True)
    parser.add_argument("--us-packet", type=Path, required=True)
    parser.add_argument("--kr-packet", type=Path, required=True)
    parser.add_argument("--us-deterministic", type=Path, required=True)
    parser.add_argument("--kr-deterministic", type=Path, required=True)
    parser.add_argument("--treasury-fixture", type=Path, required=True)
    parser.add_argument("--env-file", type=Path, required=True)
    parser.add_argument("--production-root", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    asyncio.run(_run(parser.parse_args()))


if __name__ == "__main__":
    main()
