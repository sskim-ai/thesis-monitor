from __future__ import annotations

import argparse
import asyncio
import hashlib
import json
import sqlite3
from collections.abc import Mapping, Sequence
from datetime import datetime
from decimal import Decimal
from pathlib import Path

import httpx

from app.config import get_settings
from app.services.kr_price_structure_selective_rollout_service import (
    build_kr_price_structure_runtime_context,
    build_kr_price_structure_rollout_decision,
    preserve_price_structure_sections,
    replace_legacy_price_surface,
    suppress_current_price_structure_surface,
)
from app.services.ohlcv_client import (
    OHLCV_PROVIDER_REQUEST_LIMIT,
    PRICE_STRUCTURE_PERIOD_COUNTS,
    OhlcvClient,
)
from app.services.us_price_structure_selective_rollout_service import (
    build_us_price_structure_runtime_context,
    build_us_price_structure_rollout_decision,
)
from scripts.kr_final_preenable_test_delivery import deliver_test_messages
from scripts.kr_market_preenable_evidence import audit_test_sink, load_env_values


CONTRACT = "major-sr-reality-gate-evidence-v1"
NAMESPACE = "TEST_ONLY_MAJOR_SR_REALITY_GATE"
MAJOR_SEMANTICS = ("MAJOR_SUPPORT", "MAJOR_RESISTANCE")


def _read_json(path: Path) -> object:
    return json.loads(path.read_text(encoding="utf-8"))


def _write_json(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(
        json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    temporary.replace(path)


def _sha(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def _active_universe(database: Path) -> list[dict[str, str]]:
    connection = sqlite3.connect(f"file:{database}?mode=ro", uri=True)
    try:
        rows = connection.execute(
            """
            SELECT ticker, company_name
            FROM watchlistitem
            WHERE active = 1
            ORDER BY ticker
            """
        ).fetchall()
    finally:
        connection.close()
    return [
        {"ticker": str(ticker), "company": str(company)}
        for ticker, company in rows
    ]


def _raw_subjects(path: Path) -> dict[str, Mapping[str, object]]:
    payload = _read_json(path)
    if not isinstance(payload, Mapping) or not isinstance(
        payload.get("subjects"), list
    ):
        raise ValueError(f"invalid raw evidence bundle: {path}")
    return {
        str(row.get("ticker")): row
        for row in payload["subjects"]
        if isinstance(row, Mapping) and row.get("ticker")
    }


def _message_rows(path: Path) -> dict[str, Mapping[str, object]]:
    payload = _read_json(path)
    if not isinstance(payload, Mapping) or not isinstance(payload.get("messages"), list):
        raise ValueError(f"invalid message bundle: {path}")
    return {
        str(row.get("ticker")): row
        for row in payload["messages"]
        if isinstance(row, Mapping) and row.get("ticker")
    }


def _message_text(row: Mapping[str, object]) -> str:
    text = row.get("text")
    if isinstance(text, str):
        return text
    payload = row.get("payload")
    if isinstance(payload, Mapping) and isinstance(payload.get("text"), str):
        return str(payload["text"])
    raise ValueError("message text missing")


def _route(row: Mapping[str, object]) -> str:
    core = row.get("common_ai_core")
    if not isinstance(core, Mapping):
        return "AI"
    return str(core.get("final_delivery_mode") or "AI")


def _zone_by_semantic(
    summary: Mapping[str, object],
    semantic: str,
) -> Mapping[str, object] | None:
    key = {
        "MAJOR_SUPPORT": "major_structural_support",
        "MAJOR_RESISTANCE": "major_structural_resistance",
    }[semantic]
    selection = summary.get(key)
    if not isinstance(selection, Mapping):
        return None
    zone = selection.get("zone")
    return zone if isinstance(zone, Mapping) else None


def _major_audit(
    summary: Mapping[str, object],
    bindings: Sequence[Mapping[str, object]],
) -> dict[str, object]:
    by_semantic = {
        str(binding.get("semantic_type")): binding
        for binding in bindings
        if str(binding.get("semantic_type")) in MAJOR_SEMANTICS
    }
    output: dict[str, object] = {}
    for semantic in MAJOR_SEMANTICS:
        zone = _zone_by_semantic(summary, semantic)
        binding = by_semantic.get(semantic)
        families = list(zone.get("source_families") or ()) if zone else []
        output[semantic] = {
            "visible": binding is not None,
            "zone_id": binding.get("fact_ref") if binding else None,
            "display": binding.get("display") if binding else None,
            "source_families": families,
            "source_refs": list(zone.get("source_refs") or ()) if zone else [],
            "price_anchor_refs": (
                list(binding.get("price_anchor_refs") or ()) if binding else []
            ),
            "reaction_count": zone.get("reaction_count") if zone else None,
            "historical_interaction_count": (
                zone.get("historical_interaction_count") if zone else None
            ),
            "last_meaningful_interaction": (
                zone.get("last_meaningful_interaction") if zone else None
            ),
            "last_price_interaction_date": (
                zone.get("last_price_interaction_date") if zone else None
            ),
            "indicator_observation_dates": (
                list(zone.get("indicator_observation_dates") or ()) if zone else []
            ),
            "structural_score": zone.get("structural_score") if zone else None,
            "active_relevance": zone.get("active_relevance") if zone else None,
        }
    return output


def _preview(
    *,
    decision: object,
    ai_row: Mapping[str, object],
    fallback_row: Mapping[str, object],
) -> tuple[str, str, str, str]:
    section = getattr(decision, "section")
    ai = _message_text(ai_row)
    fallback = _message_text(fallback_row)
    if section:
        fallback_preview = replace_legacy_price_surface(fallback, section)
        ai_preview = preserve_price_structure_sections(ai, fallback_preview)
    else:
        fallback_preview = suppress_current_price_structure_surface(fallback)
        ai_preview = suppress_current_price_structure_surface(ai)
    route = _route(ai_row)
    selected = fallback_preview if "FALLBACK" in route.upper() else ai_preview
    return ai_preview, fallback_preview, selected, route


async def _snapshot(args: argparse.Namespace) -> None:
    settings = get_settings()
    settings.us_price_structure_v3_enabled = True
    settings.kr_price_structure_v3_enabled = True
    universe = [
        subject
        for subject in _active_universe(args.database)
        if args.market == "ALL"
        or (args.market == "KR") == subject["ticker"].isdigit()
    ]
    archives = {
        "US": args.us_archive,
        "KR": args.kr_archive,
    }
    bundles = {
        market: {
            "ai": _message_rows(archive / "ai-assisted-messages.json"),
            "fallback": _message_rows(archive / "deterministic-messages.json"),
        }
        for market, archive in archives.items()
    }
    client = OhlcvClient()
    raw_subjects = _raw_subjects(args.raw_input) if args.raw_input else {}
    observed_at = datetime.fromisoformat(args.observed_at)
    rows: list[dict[str, object]] = []
    messages: list[dict[str, object]] = []
    for subject in universe:
        ticker = subject["ticker"]
        market = "KR" if ticker.isdigit() else "US"
        ai_row = bundles[market]["ai"].get(ticker)
        fallback_row = bundles[market]["fallback"].get(ticker)
        if ai_row is None or fallback_row is None:
            raise ValueError(f"immutable message baseline missing: {ticker}")
        raw_subject = raw_subjects.get(ticker)
        if raw_subject is not None:
            raw_by_timeframe = raw_subject.get("raw_by_timeframe")
            if not isinstance(raw_by_timeframe, Mapping):
                raise ValueError(f"raw timeframes missing: {ticker}")
            runtime_builder = (
                build_kr_price_structure_runtime_context
                if market == "KR"
                else build_us_price_structure_runtime_context
            )
            structure = runtime_builder(
                ticker=ticker,
                cutoff=str(raw_subject.get("cutoff") or ""),
                raw_by_timeframe=raw_by_timeframe,  # type: ignore[arg-type]
                observed_at=args.observed_at,
                provider_limit=OHLCV_PROVIDER_REQUEST_LIMIT,
            )
        else:
            context = await client.fetch_price_context(ticker, as_of=observed_at)
            structure = context.chart.structure.get("price_structure_v3")
        if not isinstance(structure, Mapping):
            raise ValueError(f"price structure context missing: {ticker}")
        if Decimal(str(structure.get("current_price") or 0)) <= 0:
            raise ValueError(f"price structure source data unavailable: {ticker}")
        builder = (
            build_kr_price_structure_rollout_decision
            if market == "KR"
            else build_us_price_structure_rollout_decision
        )
        decision = builder(
            structure,
            ticker=ticker,
            monitored_subject=True,
            enabled=True,
        )
        ai_preview, fallback_preview, selected, route = _preview(
            decision=decision,
            ai_row=ai_row,
            fallback_row=fallback_row,
        )
        summary = structure.get("summary")
        summary = summary if isinstance(summary, Mapping) else {}
        bindings = [dict(binding) for binding in decision.numeric_bindings]
        major = _major_audit(summary, bindings)
        major_bindings = [
            binding
            for binding in bindings
            if str(binding.get("semantic_type")) in MAJOR_SEMANTICS
        ]
        major_without_anchor = sum(
            not bool(binding.get("price_anchor_refs")) for binding in major_bindings
        )
        dynamic_only_major = sum(
            bool(item.get("visible"))
            and bool(item.get("source_families"))
            and all(
                str(family).startswith(("BOLLINGER_", "FIBONACCI_"))
                for family in item["source_families"]
            )
            for item in major.values()
            if isinstance(item, Mapping)
        )
        ai_fallback_parity = all(
            str(binding.get("display") or "") in ai_preview
            and str(binding.get("display") or "") in fallback_preview
            for binding in major_bindings
        )
        row = {
            **subject,
            "market": market,
            "raw_source_sha256": (
                raw_subject.get("raw_source_sha256") if raw_subject else None
            ),
            "as_of": structure.get("as_of"),
            "current_price": structure.get("current_price"),
            "currency": structure.get("currency"),
            "security_basis": structure.get("security_basis"),
            "adjustment_basis": structure.get("adjustment_basis"),
            "eligibility": decision.eligibility.value,
            "denial_reasons": list(decision.denial_reasons),
            "summary": summary,
            "section": decision.section,
            "numeric_bindings": bindings,
            "major": major,
            "major_without_price_anchor": major_without_anchor,
            "dynamic_only_major_visible": dynamic_only_major,
            "render_validation_errors": list(decision.render_validation_errors),
            "ai_fallback_major_parity": ai_fallback_parity,
            "ai_preview": ai_preview,
            "fallback_preview": fallback_preview,
            "selected_preview": selected,
            "selected_sha256": _sha(selected),
            "route": route,
            "unsupported_target": int("목표 가격" in (decision.section or "")),
            "unsupported_stop": int("손절" in (decision.section or "")),
        }
        row["status"] = "PASS" if all(
            (
                not major_without_anchor,
                not dynamic_only_major,
                not row["render_validation_errors"],
                ai_fallback_parity,
                row["unsupported_target"] == 0,
                row["unsupported_stop"] == 0,
            )
        ) else "FAIL"
        rows.append(row)
        messages.append(
            {
                "ticker": ticker,
                "route": route,
                "text": selected,
                "logical_identity": f"{NAMESPACE}:{ticker}:{structure.get('as_of')}",
            }
        )
    failed = [row["ticker"] for row in rows if row["status"] != "PASS"]
    payload: dict[str, object] = {
        "contract": CONTRACT,
        "observed_at": args.observed_at,
        "universe_count": len(rows),
        "us_count": sum(row["market"] == "US" for row in rows),
        "kr_count": sum(row["market"] == "KR" for row in rows),
        "rows": rows,
        "messages": messages,
        "failed_tickers": failed,
        "status": "PASS" if not failed else "FAIL",
        "provider_calls": {
            "local_ohlcv_analyst_requests": 0 if args.raw_input else len(rows) * 4,
            "success_subjects": len(rows),
            "failed_subjects": 0,
            "cache_hit": len(rows) if args.raw_input else "provider_internal_not_exposed",
        },
    }
    _write_json(args.output, payload)
    print(
        json.dumps(
            {
                "status": payload["status"],
                "universe_count": payload["universe_count"],
                "failed_tickers": failed,
            },
            ensure_ascii=False,
            sort_keys=True,
        )
    )


async def _capture(args: argparse.Namespace) -> None:
    settings = get_settings()
    api_key = settings.ohlcv_api_key or settings.action_api_key
    headers = {"X-API-Key": api_key} if api_key else {}
    observed_at = datetime.fromisoformat(args.observed_at)
    subjects: list[dict[str, object]] = []
    request_count = 0
    async with httpx.AsyncClient(
        base_url=settings.ohlcv_base_url.rstrip("/"),
        headers=headers,
        timeout=settings.ohlcv_timeout_seconds,
    ) as client:
        for subject in _active_universe(args.database):
            ticker = subject["ticker"]
            market = "KR" if ticker.isdigit() else "US"
            cutoff = args.kr_cutoff if market == "KR" else args.us_cutoff
            raw_by_timeframe: dict[str, list[dict[str, object]]] = {}
            for timeframe, requested_count in PRICE_STRUCTURE_PERIOD_COUNTS.items():
                response = await client.get(
                    "/ohlcv",
                    params={
                        "symbol": ticker,
                        "periods": timeframe,
                        "count": min(
                            requested_count, OHLCV_PROVIDER_REQUEST_LIMIT
                        ),
                        "include_indicators": "true",
                        "indicator_limit": 1,
                        "adjusted": "true",
                    },
                )
                request_count += 1
                response.raise_for_status()
                payload = response.json()
                bars = payload.get("periods", {}).get(timeframe, [])
                if not isinstance(bars, list) or not bars:
                    raise ValueError(
                        f"captured source data unavailable: {ticker}/{timeframe}"
                    )
                if timeframe == "daily" and isinstance(
                    payload.get("supply_demand"), Mapping
                ):
                    latest = bars[-1]
                    if isinstance(latest, Mapping):
                        bars[-1] = {
                            **latest,
                            "supply_demand": payload["supply_demand"],
                        }
                raw_by_timeframe[timeframe] = bars
            raw_json = json.dumps(
                raw_by_timeframe,
                ensure_ascii=False,
                sort_keys=True,
                separators=(",", ":"),
            )
            subjects.append(
                {
                    **subject,
                    "market": market,
                    "cutoff": cutoff,
                    "raw_source_sha256": _sha(raw_json),
                    "raw_by_timeframe": raw_by_timeframe,
                }
            )
    output = {
        "contract": "major-sr-reality-gate-raw-source-v1",
        "observed_at": observed_at.isoformat(),
        "subjects": subjects,
        "provider_calls": {
            "local_ohlcv_analyst_requests": request_count,
            "success": request_count,
            "failure": 0,
            "cache_hit": 0,
        },
    }
    _write_json(args.output, output)
    print(
        json.dumps(
            {
                "status": "PASS",
                "subjects": len(subjects),
                "requests": request_count,
            },
            sort_keys=True,
        )
    )


async def _send(args: argparse.Namespace) -> None:
    payload = _read_json(args.input)
    if not isinstance(payload, Mapping) or payload.get("status") != "PASS":
        raise ValueError("replay evidence is not PASS")
    messages = payload.get("messages")
    if not isinstance(messages, list) or len(messages) != 20:
        raise ValueError("expected exact 20-subject test payload")
    env = load_env_values(args.env_file)
    sink = audit_test_sink(env)
    if sink.get("available") is not True:
        raise ValueError(f"test sink unavailable: {sink.get('reason')}")
    selected_key = str(sink.get("selected_test_key_name") or "")
    receipt = await deliver_test_messages(
        messages,
        token=env.get("TELEGRAM_BOT_TOKEN") or "",
        test_chat_id=env.get(selected_key) or "",
        production_chat_id=env.get("TELEGRAM_CHAT_ID") or "",
        test_sink_alias=str(sink["test_sink_alias"]),
        production_sink_alias=str(sink["production_sink_alias"]),
        receipt_path=args.receipt,
        contract="major-sr-reality-gate-test-delivery-v1",
        namespace=NAMESPACE,
    )
    print(
        json.dumps(
            {
                "status": receipt["status"],
                "sent_message_count": receipt["sent_message_count"],
                "exact_payload_match": receipt["exact_payload_match"],
                "test_sink_alias": sink["test_sink_alias"],
                "production_sink_alias": sink["production_sink_alias"],
            },
            ensure_ascii=False,
            sort_keys=True,
        )
    )


def _merge(args: argparse.Namespace) -> None:
    payloads = [_read_json(path) for path in args.inputs]
    if any(
        not isinstance(payload, Mapping) or payload.get("status") != "PASS"
        for payload in payloads
    ):
        raise ValueError("all snapshot inputs must be PASS")
    rows = [
        row
        for payload in payloads
        if isinstance(payload, Mapping)
        for row in payload.get("rows", [])
        if isinstance(row, Mapping)
    ]
    messages = [
        message
        for payload in payloads
        if isinstance(payload, Mapping)
        for message in payload.get("messages", [])
        if isinstance(message, Mapping)
    ]
    tickers = [str(row.get("ticker") or "") for row in rows]
    if len(rows) != 20 or len(set(tickers)) != 20 or len(messages) != 20:
        raise ValueError("merged evidence must contain exact 20-subject universe")
    merged = {
        "contract": CONTRACT,
        "observed_at": payloads[0].get("observed_at"),  # type: ignore[union-attr]
        "universe_count": len(rows),
        "us_count": sum(row.get("market") == "US" for row in rows),
        "kr_count": sum(row.get("market") == "KR" for row in rows),
        "rows": sorted(rows, key=lambda row: str(row.get("ticker") or "")),
        "messages": sorted(
            messages, key=lambda row: str(row.get("ticker") or "")
        ),
        "failed_tickers": [],
        "status": "PASS",
        "provider_calls": {
            "local_ohlcv_analyst_requests": sum(
                int(
                    payload.get("provider_calls", {}).get(
                        "local_ohlcv_analyst_requests", 0
                    )
                )
                for payload in payloads
                if isinstance(payload, Mapping)
                and isinstance(payload.get("provider_calls"), Mapping)
            ),
            "success_subjects": len(rows),
            "failed_subjects": 0,
            "cache_hit": "provider_internal_not_exposed",
        },
    }
    _write_json(args.output, merged)
    print(json.dumps({"status": "PASS", "universe_count": 20}, sort_keys=True))


def main() -> None:
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers(dest="command", required=True)
    snapshot = subparsers.add_parser("snapshot")
    snapshot.add_argument("--database", type=Path, required=True)
    snapshot.add_argument("--us-archive", type=Path, required=True)
    snapshot.add_argument("--kr-archive", type=Path, required=True)
    snapshot.add_argument("--observed-at", required=True)
    snapshot.add_argument("--output", type=Path, required=True)
    snapshot.add_argument("--market", choices=("ALL", "US", "KR"), default="ALL")
    snapshot.add_argument("--raw-input", type=Path)
    capture = subparsers.add_parser("capture")
    capture.add_argument("--database", type=Path, required=True)
    capture.add_argument("--observed-at", required=True)
    capture.add_argument("--us-cutoff", required=True)
    capture.add_argument("--kr-cutoff", required=True)
    capture.add_argument("--output", type=Path, required=True)
    send = subparsers.add_parser("send-test")
    send.add_argument("--input", type=Path, required=True)
    send.add_argument("--env-file", type=Path, required=True)
    send.add_argument("--receipt", type=Path, required=True)
    merge = subparsers.add_parser("merge")
    merge.add_argument("--inputs", type=Path, nargs="+", required=True)
    merge.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if args.command == "capture":
        asyncio.run(_capture(args))
    elif args.command == "snapshot":
        asyncio.run(_snapshot(args))
    elif args.command == "send-test":
        asyncio.run(_send(args))
    else:
        _merge(args)


if __name__ == "__main__":
    main()
