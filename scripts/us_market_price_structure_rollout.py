from __future__ import annotations

import argparse
import asyncio
import hashlib
import json
import sqlite3
from collections import Counter
from collections.abc import Mapping, Sequence
from datetime import datetime
from pathlib import Path

from app.config import get_settings
from app.services.kr_price_structure_selective_rollout_service import (
    preserve_price_structure_sections,
    replace_legacy_price_surface,
    suppress_current_price_structure_surface,
)
from app.services.ohlcv_client import OhlcvClient
from app.services.us_full_message_service import (
    preserve_us_full_message_layout,
    render_us_full_market_message,
)
from app.services.us_market_message_quality_service import (
    validate_us_market_message_payload,
)
from app.services.us_price_structure_selective_rollout_service import (
    build_us_price_structure_rollout_decision,
)
from scripts.kr_final_preenable_test_delivery import deliver_test_messages
from scripts.kr_market_preenable_evidence import audit_test_sink, load_env_values


CONTRACT = "us-market-price-structure-rollout-evidence-v1"
MARKET_NAMESPACE = "TEST_ONLY_US_FULL_MARKET_MESSAGE"
STOCK_NAMESPACE = "TEST_ONLY_US_PRICE_STRUCTURE_FULL_UNIVERSE"


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


def _sha_text(value: str) -> str:
    return hashlib.sha256(value.encode()).hexdigest()


def _message_text(row: Mapping[str, object]) -> str:
    value = row.get("text")
    if isinstance(value, str):
        return value
    payload = row.get("payload")
    if isinstance(payload, Mapping) and isinstance(payload.get("text"), str):
        return str(payload["text"])
    raise ValueError("message text missing")


def _message_rows(payload: object) -> dict[str, Mapping[str, object]]:
    if not isinstance(payload, Mapping) or not isinstance(payload.get("messages"), list):
        raise ValueError("message payload invalid")
    return {
        str(row.get("ticker")): row
        for row in payload["messages"]
        if isinstance(row, Mapping) and row.get("ticker")
    }


def _route(row: Mapping[str, object]) -> str:
    core = row.get("common_ai_core")
    if not isinstance(core, Mapping):
        return "AI"
    return str(core.get("final_delivery_mode") or "AI")


def _active_us_universe(database: Path) -> list[dict[str, object]]:
    connection = sqlite3.connect(f"file:{database}?mode=ro", uri=True)
    try:
        rows = connection.execute(
            """
            SELECT ticker, company_name, exchange, issuer_type,
                   ordinary_share_identifier, adr_ratio, adr_currency,
                   underlying_currency
            FROM watchlistitem
            WHERE active = 1
            ORDER BY ticker
            """
        ).fetchall()
    finally:
        connection.close()
    return [
        {
            "ticker": str(row[0]),
            "company": str(row[1]),
            "exchange": row[2],
            "issuer_type": row[3],
            "ordinary_share_identifier": row[4],
            "adr_ratio": row[5],
            "adr_currency": row[6],
            "underlying_currency": row[7],
        }
        for row in rows
        if not str(row[0]).isdigit()
    ]


def _coverage(context: Mapping[str, object]) -> dict[str, object]:
    coverage = context.get("coverage")
    return dict(coverage) if isinstance(coverage, Mapping) else {}


def _selected_message(
    *,
    route: str,
    ai_preview: str,
    fallback_preview: str,
) -> str:
    return fallback_preview if "FALLBACK" in route.upper() else ai_preview


def _market_evidence(
    *,
    packet_id: str,
    market_context: Mapping[str, object],
    ai_rows: Mapping[str, Mapping[str, object]],
) -> tuple[dict[str, object], list[dict[str, object]]]:
    rendered = render_us_full_market_message(market_context)
    if rendered.status != "PASS":
        raise ValueError(f"US full-message render failed: {rendered.validation_errors}")
    ai_row = ai_rows.get("__DAILY_DIGEST__")
    if ai_row is None:
        raise ValueError("US market AI message missing")
    ai_preview = preserve_us_full_message_layout(
        _message_text(ai_row), deterministic_text=rendered.text
    )
    route = _route(ai_row)
    selected = _selected_message(
        route=route,
        ai_preview=ai_preview,
        fallback_preview=rendered.text,
    )
    facts = market_context.get("fact_catalog")
    facts = facts if isinstance(facts, list) else []
    by_id = {
        str(fact.get("fact_id")): fact
        for fact in facts
        if isinstance(fact, Mapping) and fact.get("fact_id")
    }
    numeric_refs = [
        *rendered.index_fact_ids,
        *rendered.sector_fact_ids,
        *rendered.night_fact_ids,
    ]
    unresolved_refs = [ref for ref in numeric_refs if ref not in by_id and "night" not in ref]
    checks = {
        "render_status": rendered.status,
        "index_symbols_visible": all(
            selected.count(f"• {symbol} ") == 1
            for symbol in ("SPY", "QQQ", "IWM", "SOXX", "RSP")
        ),
        "strong_sector_numeric_visible": selected.count("• 업종 강세:") == 1,
        "weak_sector_numeric_visible": selected.count("• 업종 약세:") == 1,
        "section_order": rendered.section_order,
        "numeric_ref_count": len(numeric_refs),
        "unresolved_numeric_ref_count": len(unresolved_refs),
        "ai_fallback_required_section_parity": all(
            heading in ai_preview and heading in rendered.text
            for heading in ("📈 주요 지수", "🔎 시장 내부", "📌 다음 확인")
        ),
        "night_futures_section_visible": "🌙 한국 야간선물" in selected,
        "night_futures_safe_omission": (
            bool(rendered.night_fact_ids) or "🌙 한국 야간선물" not in selected
        ),
        "character_count": len(selected),
    }
    quality = validate_us_market_message_payload(selected)
    checks["status"] = "PASS" if all(
        (
            checks["index_symbols_visible"],
            checks["strong_sector_numeric_visible"],
            checks["weak_sector_numeric_visible"],
            checks["unresolved_numeric_ref_count"] == 0,
            checks["ai_fallback_required_section_parity"],
            checks["night_futures_safe_omission"],
            len(selected) <= 3500,
            quality.status == "PASS",
        )
    ) else "FAIL"
    evidence = {
        "contract": CONTRACT,
        "packet_id": packet_id,
        "route": route,
        "selected_text": selected,
        "ai_preview": ai_preview,
        "fallback_preview": rendered.text,
        "render": rendered.to_dict(),
        "checks": checks,
        "selected_sha256": _sha_text(selected),
        "quality": quality.to_dict(),
    }
    messages = [
        {
            "ticker": "__DAILY_DIGEST__",
            "route": route,
            "text": selected,
            "logical_identity": f"{MARKET_NAMESPACE}:{packet_id}:market",
        }
    ]
    return evidence, messages


async def _price_structure_evidence(
    *,
    packet_id: str,
    target_session: str,
    observed_at: datetime,
    universe: Sequence[Mapping[str, object]],
    packet_tickers: Sequence[str],
    ai_rows: Mapping[str, Mapping[str, object]],
    fallback_rows: Mapping[str, Mapping[str, object]],
) -> tuple[dict[str, object], list[dict[str, object]]]:
    universe_tickers = [str(row["ticker"]) for row in universe]
    if set(universe_tickers) != set(packet_tickers):
        raise ValueError(
            f"active universe differs from immutable message baseline: "
            f"active={universe_tickers}, packet={sorted(packet_tickers)}"
        )
    settings = get_settings()
    settings.us_price_structure_v3_enabled = True
    client = OhlcvClient()
    rows: list[dict[str, object]] = []
    messages: list[dict[str, object]] = []
    for subject in universe:
        ticker = str(subject["ticker"])
        context = await client.fetch_price_context(ticker, as_of=observed_at)
        price_context = context.model_dump(mode="json")
        structure = context.chart.structure.get("price_structure_v3")
        structure = structure if isinstance(structure, Mapping) else {}
        decision = build_us_price_structure_rollout_decision(
            structure,
            ticker=ticker,
            monitored_subject=True,
            enabled=True,
        )
        fallback_row = fallback_rows.get(ticker)
        ai_row = ai_rows.get(ticker)
        if fallback_row is None or ai_row is None:
            raise ValueError(f"message baseline missing: {ticker}")
        fallback = _message_text(fallback_row)
        ai = _message_text(ai_row)
        if decision.section:
            fallback_preview = replace_legacy_price_surface(
                fallback, decision.section
            )
            ai_preview = preserve_price_structure_sections(ai, fallback_preview)
        else:
            fallback_preview = suppress_current_price_structure_surface(fallback)
            ai_preview = suppress_current_price_structure_surface(ai)
        route = _route(ai_row)
        selected = _selected_message(
            route=route,
            ai_preview=ai_preview,
            fallback_preview=fallback_preview,
        )
        first_line = fallback.splitlines()[0]
        current_section_count = selected.count("📐 현재 가격 구조")
        expected_section_count = int(decision.section is not None)
        stored_rule_present = "가격 규칙 이력:" in fallback
        numeric_refs = [
            str(binding.get("fact_ref") or "") for binding in decision.numeric_bindings
        ]
        coverage = _coverage(structure)
        daily_coverage = coverage.get("daily")
        daily_coverage = (
            daily_coverage if isinstance(daily_coverage, Mapping) else {}
        )
        daily_actual_end = str(daily_coverage.get("actual_end_date") or "")
        source_session_aligned = bool(
            daily_actual_end and daily_actual_end == target_session
        )
        row = {
            **dict(subject),
            "target_session": target_session,
            "price_as_of": structure.get("as_of"),
            "currency": structure.get("currency"),
            "security_basis": f"US_LISTED:{ticker}",
            "price_context": price_context,
            "coverage": coverage,
            "daily_actual_end_date": daily_actual_end or None,
            "source_session_aligned": source_session_aligned,
            "eligibility": decision.eligibility.value,
            "denial_reasons": list(decision.denial_reasons),
            "section": decision.section,
            "numeric_bindings": list(decision.numeric_bindings),
            "displayed_zone_ids": list(decision.displayed_zone_ids),
            "numeric_fact_refs": numeric_refs,
            "route": route,
            "ai_preview": ai_preview,
            "fallback_preview": fallback_preview,
            "selected_preview": selected,
            "selected_sha256": _sha_text(selected),
            "company_header_intact": selected.splitlines().count(first_line) == 1,
            "expected_section_count": expected_section_count,
            "actual_section_count": current_section_count,
            "section_count_match": current_section_count == expected_section_count,
            "stored_rule_present": stored_rule_present,
            "stored_rule_separated": (
                not stored_rule_present
                or decision.section is None
                or "🧭 기존 등록 가격 규칙" in selected
            ),
            "ai_fallback_numeric_parity": (
                not decision.section
                or all(
                    binding.get("display") in ai_preview
                    and binding.get("display") in fallback_preview
                    for binding in decision.numeric_bindings
                    if binding.get("display")
                )
            ),
            "partial_bar_used_for_pivot_confirmation": int(
                structure.get("partial_bar_used_for_pivot_confirmation") or 0
            ),
            "lookahead_leak": int(structure.get("as_of") != target_session),
            "wrong_session_data_visible": int(
                decision.section is not None and not source_session_aligned
            ),
            "security_basis_conflict": int(structure.get("currency") != "USD"),
            "unsupported_target": int("목표 가격" in (decision.section or "")),
            "unsupported_stop": int("손절" in (decision.section or "")),
            "render_validation_errors": list(decision.render_validation_errors),
            "character_count": len(selected),
        }
        row["quality_status"] = "PASS" if all(
            (
                row["company_header_intact"],
                row["section_count_match"],
                row["stored_rule_separated"],
                row["ai_fallback_numeric_parity"],
                row["partial_bar_used_for_pivot_confirmation"] == 0,
                row["lookahead_leak"] == 0,
                row["wrong_session_data_visible"] == 0,
                row["security_basis_conflict"] == 0,
                row["unsupported_target"] == 0,
                row["unsupported_stop"] == 0,
                not row["render_validation_errors"],
                len(selected) <= 3500,
            )
        ) else "FAIL"
        rows.append(row)
        messages.append(
            {
                "ticker": ticker,
                "route": route,
                "text": selected,
                "logical_identity": f"{STOCK_NAMESPACE}:{packet_id}:stock:{ticker}",
            }
        )
    eligibility = Counter(str(row["eligibility"]) for row in rows)
    failures = [str(row["ticker"]) for row in rows if row["quality_status"] != "PASS"]
    evidence = {
        "contract": CONTRACT,
        "packet_id": packet_id,
        "target_session": target_session,
        "active_universe_count": len(universe),
        "active_tickers": universe_tickers,
        "eligibility_counts": dict(sorted(eligibility.items())),
        "rows": rows,
        "test_stock_message_count": len(messages),
        "test_stock_fail_count": len(failures),
        "failed_tickers": failures,
        "status": "PASS" if not failures and len(rows) == len(universe) else "FAIL",
    }
    return evidence, messages


async def _deliver(
    *,
    messages: Sequence[Mapping[str, object]],
    env: Mapping[str, str],
    sink: Mapping[str, object],
    receipt_path: Path,
    contract: str,
    namespace: str,
) -> dict[str, object]:
    selected_key = str(sink.get("selected_test_key_name") or "")
    return await deliver_test_messages(
        messages,
        token=env.get("TELEGRAM_BOT_TOKEN") or "",
        test_chat_id=env.get(selected_key) or "",
        production_chat_id=env.get("TELEGRAM_CHAT_ID") or "",
        test_sink_alias=str(sink["test_sink_alias"]),
        production_sink_alias=str(sink["production_sink_alias"]),
        receipt_path=receipt_path,
        contract=contract,
        namespace=namespace,
        received_payload_validator=(
            (lambda text: validate_us_market_message_payload(text).to_dict())
            if namespace == MARKET_NAMESPACE
            else None
        ),
    )


async def _run(args: argparse.Namespace) -> None:
    if args.market_only and args.send_stocks:
        raise ValueError("--market-only cannot be combined with --send-stocks")
    if args.market_only and args.reuse_audit:
        raise ValueError("--market-only does not reuse the combined rollout audit")
    packet = _read_json(args.archive / "packet.json")
    if not isinstance(packet, Mapping):
        raise ValueError("packet invalid")
    packet_id = str(packet.get("packet_id") or "")
    stocks = packet.get("stocks")
    if not packet_id or not isinstance(stocks, list):
        raise ValueError("packet identity or stock rows missing")
    packet_tickers = [
        str(row.get("ticker"))
        for row in stocks
        if isinstance(row, Mapping) and row.get("ticker")
    ]
    ai_rows = _message_rows(_read_json(args.archive / "ai-assisted-messages.json"))
    market_context = _read_json(args.archive / "market-context.json")
    if not isinstance(market_context, Mapping):
        raise ValueError("market context invalid")
    env = load_env_values(args.env_file)
    sink = audit_test_sink(env)
    if sink.get("available") is not True:
        raise ValueError(f"test sink unavailable: {sink.get('reason')}")

    if args.market_only:
        market_evidence, market_messages = _market_evidence(
            packet_id=packet_id,
            market_context=market_context,
            ai_rows=ai_rows,
        )
        market_evidence["test_sink"] = sink
        _write_json(args.market_output, market_evidence)
        summary: dict[str, object] = {
            "contract": CONTRACT,
            "packet_id": packet_id,
            "market_only": True,
            "market_status": market_evidence["checks"]["status"],
            "stock_evidence_built": False,
            "stock_messages_sent": 0,
            "test_sink_alias": sink["test_sink_alias"],
            "production_sink_alias": sink["production_sink_alias"],
            "production_collision": sink["production_collision"],
        }
        if args.send_market:
            if market_evidence["checks"]["status"] != "PASS":
                raise ValueError("market preflight failed")
            receipt = await _deliver(
                messages=market_messages,
                env=env,
                sink=sink,
                receipt_path=args.market_receipt,
                contract="us-macro-quality-test-delivery-v1",
                namespace=MARKET_NAMESPACE,
            )
            summary["market_test_delivery"] = {
                "status": receipt["status"],
                "sent_message_count": receipt["sent_message_count"],
                "exact_payload_match": receipt["exact_payload_match"],
            }
        print(json.dumps(summary, ensure_ascii=False, sort_keys=True))
        return

    fallback_rows = _message_rows(_read_json(args.archive / "deterministic-messages.json"))
    universe = _active_us_universe(args.database)

    if args.reuse_audit:
        market_evidence = _read_json(args.market_output)
        price_evidence = _read_json(args.price_output)
        if not isinstance(market_evidence, Mapping) or not isinstance(
            price_evidence, Mapping
        ):
            raise ValueError("existing rollout audits invalid")
        if (
            market_evidence.get("packet_id") != packet_id
            or price_evidence.get("packet_id") != packet_id
        ):
            raise ValueError("existing rollout audit packet mismatch")
        selected_market = str(market_evidence.get("selected_text") or "")
        if _sha_text(selected_market) != market_evidence.get("selected_sha256"):
            raise ValueError("existing market audit payload hash mismatch")
        market_messages = [
            {
                "ticker": "__DAILY_DIGEST__",
                "route": str(market_evidence.get("route") or ""),
                "text": selected_market,
                "logical_identity": f"{MARKET_NAMESPACE}:{packet_id}:market",
            }
        ]
        price_rows = price_evidence.get("rows")
        if not isinstance(price_rows, list):
            raise ValueError("existing price audit rows missing")
        stock_messages = []
        for row in price_rows:
            if not isinstance(row, Mapping):
                raise ValueError("existing price audit row invalid")
            text = str(row.get("selected_preview") or "")
            if _sha_text(text) != row.get("selected_sha256"):
                raise ValueError(f"existing stock audit payload hash mismatch: {row.get('ticker')}")
            ticker = str(row.get("ticker") or "")
            stock_messages.append(
                {
                    "ticker": ticker,
                    "route": str(row.get("route") or ""),
                    "text": text,
                    "logical_identity": f"{STOCK_NAMESPACE}:{packet_id}:stock:{ticker}",
                }
            )
    else:
        market_evidence, market_messages = _market_evidence(
            packet_id=packet_id,
            market_context=market_context,
            ai_rows=ai_rows,
        )
        price_evidence, stock_messages = await _price_structure_evidence(
            packet_id=packet_id,
            target_session=args.target_session,
            observed_at=datetime.fromisoformat(args.observed_at),
            universe=universe,
            packet_tickers=packet_tickers,
            ai_rows=ai_rows,
            fallback_rows=fallback_rows,
        )
        market_evidence["test_sink"] = sink
        price_evidence["test_sink"] = sink
        _write_json(args.market_output, market_evidence)
        _write_json(args.price_output, price_evidence)

    summary: dict[str, object] = {
        "contract": CONTRACT,
        "packet_id": packet_id,
        "market_status": market_evidence["checks"]["status"],
        "price_structure_status": price_evidence["status"],
        "active_universe_count": price_evidence["active_universe_count"],
        "eligibility_counts": price_evidence["eligibility_counts"],
        "test_sink_alias": sink["test_sink_alias"],
        "production_sink_alias": sink["production_sink_alias"],
        "production_collision": sink["production_collision"],
    }
    if args.send_market:
        if market_evidence["checks"]["status"] != "PASS":
            raise ValueError("market preflight failed")
        receipt = await _deliver(
            messages=market_messages,
            env=env,
            sink=sink,
            receipt_path=args.market_receipt,
            contract="us-full-market-message-test-delivery-v1",
            namespace=MARKET_NAMESPACE,
        )
        summary["market_test_delivery"] = {
            "status": receipt["status"],
            "sent_message_count": receipt["sent_message_count"],
            "exact_payload_match": receipt["exact_payload_match"],
        }
    if args.send_stocks:
        if price_evidence["status"] != "PASS":
            raise ValueError("price-structure preflight failed")
        receipt = await _deliver(
            messages=stock_messages,
            env=env,
            sink=sink,
            receipt_path=args.stock_receipt,
            contract="us-price-structure-test-delivery-v1",
            namespace=STOCK_NAMESPACE,
        )
        summary["stock_test_delivery"] = {
            "status": receipt["status"],
            "sent_message_count": receipt["sent_message_count"],
            "exact_payload_match": receipt["exact_payload_match"],
        }
    print(json.dumps(summary, ensure_ascii=False, sort_keys=True))


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--archive", type=Path, required=True)
    parser.add_argument("--database", type=Path, required=True)
    parser.add_argument("--env-file", type=Path, required=True)
    parser.add_argument("--target-session", required=True)
    parser.add_argument("--observed-at", required=True)
    parser.add_argument("--market-output", type=Path, required=True)
    parser.add_argument("--price-output", type=Path, required=True)
    parser.add_argument("--market-receipt", type=Path, required=True)
    parser.add_argument("--stock-receipt", type=Path, required=True)
    parser.add_argument("--send-market", action="store_true")
    parser.add_argument("--send-stocks", action="store_true")
    parser.add_argument("--reuse-audit", action="store_true")
    parser.add_argument("--market-only", action="store_true")
    asyncio.run(_run(parser.parse_args()))


if __name__ == "__main__":
    main()
