from __future__ import annotations

import argparse
import asyncio
import copy
import hashlib
import json
from collections.abc import Mapping, Sequence
from datetime import datetime
from decimal import Decimal, InvalidOperation
from pathlib import Path

from app.services.kr_price_structure_selective_rollout_service import (
    apply_current_price_structure_section,
    build_kr_price_structure_rollout_decision,
    build_kr_price_structure_runtime_context,
    suppress_current_price_structure_surface,
)
from app.services.market_session import market_session_for_ticker
from app.services.ohlcv_client import OHLCV_PROVIDER_REQUEST_LIMIT
from app.services.us_price_structure_selective_rollout_service import (
    build_us_price_structure_rollout_decision,
    build_us_price_structure_runtime_context,
)
from scripts.kr_final_preenable_test_delivery import deliver_test_messages
from scripts.kr_market_preenable_evidence import audit_test_sink, load_env_values


CONTRACT = "provisional-bollinger-expansion-replay-v2"
NAMESPACE = "TEST_ONLY_PROVISIONAL_BOLLINGER_PRICE_LABEL_V2_FULL_MESSAGE"
PROVISIONAL_SEMANTICS = {
    "PROVISIONAL_BOLLINGER_SUPPORT",
    "PROVISIONAL_BOLLINGER_RESISTANCE",
}
STRUCTURAL_SEMANTICS = {
    "NEAR_SUPPORT",
    "NEAR_RESISTANCE",
    "MAJOR_SUPPORT",
    "MAJOR_RESISTANCE",
    "LONG_HORIZON_SUPPORT",
    "LONG_HORIZON_RESISTANCE",
}
MAJOR_SEMANTICS = {"MAJOR_SUPPORT", "MAJOR_RESISTANCE"}
PRICE_SEMANTICS = {
    "CURRENT_QUOTE",
    "STRUCTURE_BASIS_CLOSE",
    "CURRENT_QUOTE_AND_STRUCTURE_BASIS_CLOSE",
}


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


def _rows(payload: object, key: str) -> dict[str, Mapping[str, object]]:
    if not isinstance(payload, Mapping) or not isinstance(payload.get(key), list):
        raise ValueError(f"invalid evidence key: {key}")
    return {
        str(row.get("ticker")): row
        for row in payload[key]
        if isinstance(row, Mapping) and row.get("ticker")
    }


def _message_with_section(message: str, section: str | None) -> str:
    if section:
        return apply_current_price_structure_section(message, section)
    return suppress_current_price_structure_surface(message)


def _message_text(row: Mapping[str, object]) -> str:
    text = row.get("text")
    if isinstance(text, str) and text:
        return text
    payload = row.get("payload")
    if isinstance(payload, Mapping) and isinstance(payload.get("text"), str):
        return str(payload["text"])
    raise ValueError("immutable message text missing")


def _route(row: Mapping[str, object]) -> str:
    core = row.get("common_ai_core")
    if not isinstance(core, Mapping):
        return "AI"
    return str(core.get("final_delivery_mode") or "AI")


def _decimal(value: object) -> Decimal | None:
    try:
        result = Decimal(str(value))
    except (InvalidOperation, TypeError, ValueError):
        return None
    return result if result.is_finite() else None


def _safe_current_quote(
    *,
    ticker: str,
    raw_by_timeframe: Mapping[str, object],
    observed_at: str,
    currency: str,
    security_basis: str,
) -> dict[str, object] | None:
    daily = raw_by_timeframe.get("daily")
    if not isinstance(daily, Sequence) or isinstance(daily, (str, bytes)) or not daily:
        return None
    latest = daily[-1]
    if not isinstance(latest, Mapping):
        return None
    opening = _decimal(latest.get("open"))
    high = _decimal(latest.get("high"))
    low = _decimal(latest.get("low"))
    close = _decimal(latest.get("close"))
    volume = _decimal(latest.get("volume"))
    if None in {opening, high, low, close}:
        return None
    assert opening is not None and high is not None and low is not None and close is not None
    if high < low or not low <= opening <= high or not low <= close <= high:
        return None
    if volume is not None and volume < 0:
        return None
    observed = datetime.fromisoformat(observed_at)
    session = market_session_for_ticker(ticker, observed)
    return {
        "value": str(close),
        "currency": currency,
        "source": "ohlcv_analyst_official_provider",
        "observation_timestamp": observed_at,
        "market_session": session.session,
        "market_session_source": "repository_exchange_calendar",
        "security_basis": security_basis,
        "source_bar_date": latest.get("date"),
    }


def _provisional_lines(section: str) -> list[str]:
    return [
        line
        for line in section.splitlines()
        if "잠정 볼린저" in line or "잠정 " in line and "볼린저 중첩" in line
    ]


def _binding_metadata_complete(binding: Mapping[str, object]) -> bool:
    return bool(
        tuple(binding.get("indicator_bar_states") or ()) == ("PARTIAL",)
        and binding.get("observation_timestamps")
        and binding.get("indicator_bar_starts")
        and binding.get("indicator_bar_expected_closes")
        and binding.get("security_basis")
        and binding.get("adjustment_basis")
        and binding.get("currency")
        and binding.get("fact_ref")
    )


def _confluence_metadata_complete(binding: Mapping[str, object]) -> bool:
    return bool(
        tuple(binding.get("provisional_bollinger_indicator_bar_states") or ())
        == ("PARTIAL",)
        and binding.get("provisional_bollinger_observation_timestamps")
        and binding.get("provisional_bollinger_bar_starts")
        and binding.get("provisional_bollinger_bar_expected_closes")
        and binding.get("security_basis")
        and binding.get("adjustment_basis")
    )


def _display_duplicates(bindings: Sequence[Mapping[str, object]]) -> int:
    displays = [
        str(binding.get("display"))
        for binding in bindings
        if binding.get("display")
        and str(binding.get("semantic_type"))
        in {*STRUCTURAL_SEMANTICS, *PROVISIONAL_SEMANTICS}
    ]
    return len(displays) - len(set(displays))


def _replay(args: argparse.Namespace) -> None:
    raw_payload = _read_json(args.raw_input)
    raw_subjects = _rows(raw_payload, "subjects")
    immutable = {
        "US": {
            "ai": _rows(_read_json(args.us_ai), "messages"),
            "fallback": _rows(_read_json(args.us_fallback), "messages"),
        },
        "KR": {
            "ai": _rows(_read_json(args.kr_ai), "messages"),
            "fallback": _rows(_read_json(args.kr_fallback), "messages"),
        },
    }
    observed_at = str(
        raw_payload.get("observed_at")
        if isinstance(raw_payload, Mapping)
        else args.observed_at
    )
    output_by_market: dict[str, list[dict[str, object]]] = {"US": [], "KR": []}
    messages_by_market: dict[str, list[dict[str, object]]] = {"US": [], "KR": []}
    for ticker in sorted(raw_subjects):
        raw_subject = raw_subjects[ticker]
        raw_by_timeframe = raw_subject.get("raw_by_timeframe")
        if not isinstance(raw_by_timeframe, Mapping):
            raise ValueError(f"raw timeframes missing: {ticker}")
        market = str(raw_subject.get("market") or ("KR" if ticker.isdigit() else "US"))
        ai_baseline = immutable[market]["ai"].get(ticker)
        fallback_baseline = immutable[market]["fallback"].get(ticker)
        if ai_baseline is None or fallback_baseline is None:
            raise ValueError(f"immutable message baseline missing: {ticker}")
        runtime_builder = (
            build_kr_price_structure_runtime_context
            if market == "KR"
            else build_us_price_structure_runtime_context
        )
        structure = dict(
            runtime_builder(
                ticker=ticker,
                cutoff=str(raw_subject.get("cutoff") or ""),
                raw_by_timeframe=raw_by_timeframe,  # type: ignore[arg-type]
                observed_at=observed_at,
                provider_limit=OHLCV_PROVIDER_REQUEST_LIMIT,
            )
        )
        currency = str(structure.get("currency") or ("KRW" if market == "KR" else "USD"))
        security_basis = str(structure.get("security_basis") or "")
        quote = _safe_current_quote(
            ticker=ticker,
            raw_by_timeframe=raw_by_timeframe,
            observed_at=observed_at,
            currency=currency,
            security_basis=security_basis,
        )
        structure["current_quote"] = quote
        decision_builder = (
            build_kr_price_structure_rollout_decision
            if market == "KR"
            else build_us_price_structure_rollout_decision
        )
        decision = decision_builder(
            structure,
            ticker=ticker,
            monitored_subject=True,
            enabled=True,
        )
        without_provisional = copy.deepcopy(structure)
        without_summary = without_provisional.get("summary")
        if isinstance(without_summary, Mapping):
            without_provisional["summary"] = {
                **without_summary,
                "provisional_bollinger_support": None,
                "provisional_bollinger_resistance": None,
            }
        decision_without_provisional = decision_builder(
            without_provisional,
            ticker=ticker,
            monitored_subject=True,
            enabled=True,
        )
        ai = _message_with_section(_message_text(ai_baseline), decision.section)
        fallback = _message_with_section(
            _message_text(fallback_baseline), decision.section
        )
        route = _route(ai_baseline)
        selected = fallback if "FALLBACK" in route.upper() else ai
        bindings = [dict(binding) for binding in decision.numeric_bindings]
        provisional = [
            binding
            for binding in bindings
            if str(binding.get("semantic_type")) in PROVISIONAL_SEMANTICS
        ]
        confluence = [
            binding
            for binding in bindings
            if binding.get("provisional_bollinger_confluence") is True
        ]
        structural = [
            binding
            for binding in bindings
            if str(binding.get("semantic_type")) in STRUCTURAL_SEMANTICS
        ]
        major = [
            binding
            for binding in bindings
            if str(binding.get("semantic_type")) in MAJOR_SEMANTICS
        ]
        price = [
            binding
            for binding in bindings
            if str(binding.get("semantic_type")) in PRICE_SEMANTICS
        ]
        provisional_lines = _provisional_lines(decision.section or "")
        provisional_source_leak = sum(
            any(
                str(family).startswith("PROVISIONAL_BOLLINGER_")
                for family in binding.get("source_families") or ()
            )
            for binding in structural
        )
        major_without_anchor = sum(
            not bool(binding.get("price_anchor_refs")) for binding in major
        )
        bollinger_only_major = sum(
            bool(binding.get("source_families"))
            and all(
                str(family).startswith("BOLLINGER_")
                for family in binding.get("source_families") or ()
            )
            for binding in major
        )
        price_labels = [
            line
            for line in (decision.section or "").splitlines()
            if line.startswith("• 현재가(")
            or line.startswith("• 가격 구조 기준 종가(")
        ]
        ambiguous_price_label = int("• 기준 종가:" in (decision.section or ""))
        duplicate_price_lines = max(0, len(price_labels) - len(set(price_labels)))
        quote_binding = next(
            (
                binding
                for binding in price
                if binding.get("semantic_type")
                in {"CURRENT_QUOTE", "CURRENT_QUOTE_AND_STRUCTURE_BASIS_CLOSE"}
            ),
            None,
        )
        structure_binding = next(
            (
                binding
                for binding in price
                if binding.get("semantic_type")
                in {"STRUCTURE_BASIS_CLOSE", "CURRENT_QUOTE_AND_STRUCTURE_BASIS_CLOSE"}
            ),
            None,
        )
        inferred_quote_session = int(
            quote_binding is not None
            and (
                not quote_binding.get("market_session")
                or not quote_binding.get("observation_timestamp")
                or not quote
                or quote.get("market_session_source")
                != "repository_exchange_calendar"
            )
        )
        parity_lines = [*provisional_lines, *price_labels]
        ai_fallback_parity = all(line in ai and line in fallback for line in parity_lines)
        row = {
            "ticker": ticker,
            "company": raw_subject.get("company"),
            "market": market,
            "observed_at": observed_at,
            "as_of": structure.get("as_of"),
            "current_quote": quote,
            "structure_basis_close": structure.get("structure_basis_close"),
            "structure_basis_session": structure.get("structure_basis_session"),
            "currency": currency,
            "security_basis": security_basis,
            "adjustment_basis": structure.get("adjustment_basis"),
            "eligibility": decision.eligibility.value,
            "eligibility_without_provisional": (
                decision_without_provisional.eligibility.value
            ),
            "provisional_layer_bypass": int(
                decision.eligibility.value
                != decision_without_provisional.eligibility.value
            ),
            "denial_reasons": list(decision.denial_reasons),
            "section": decision.section,
            "numeric_bindings": bindings,
            "provisional_bindings": provisional,
            "provisional_confluence_bindings": confluence,
            "provisional_line_count": len(provisional_lines),
            "provisional_metadata_errors": sum(
                not _binding_metadata_complete(binding) for binding in provisional
            )
            + sum(not _confluence_metadata_complete(binding) for binding in confluence),
            "provisional_authority_leaks": sum(
                binding.get("authoritative") is not False for binding in provisional
            ),
            "provisional_as_structural_sr": provisional_source_leak,
            "major_without_price_anchor": major_without_anchor,
            "bollinger_only_major_visible": bollinger_only_major,
            "duplicate_provisional_range_visible": _display_duplicates(bindings),
            "price_bindings": price,
            "price_labels": price_labels,
            "ambiguous_current_vs_structure_price_label": ambiguous_price_label,
            "structure_basis_close_without_session": int(
                structure_binding is not None
                and not structure_binding.get("structure_basis_session")
            ),
            "duplicate_identical_price_lines": duplicate_price_lines,
            "inferred_quote_session_label_without_evidence": inferred_quote_session,
            "render_validation_errors": list(decision.render_validation_errors),
            "ai_fallback_parity": ai_fallback_parity,
            "ai_preview": ai,
            "fallback_preview": fallback,
            "selected_preview": selected,
            "selected_sha256": _sha(selected),
            "route": route,
        }
        row["status"] = "PASS" if all(
            (
                not row["render_validation_errors"],
                row["provisional_line_count"] <= 1,
                row["provisional_metadata_errors"] == 0,
                row["provisional_authority_leaks"] == 0,
                row["provisional_as_structural_sr"] == 0,
                row["provisional_layer_bypass"] == 0,
                row["major_without_price_anchor"] == 0,
                row["bollinger_only_major_visible"] == 0,
                row["duplicate_provisional_range_visible"] == 0,
                row["ambiguous_current_vs_structure_price_label"] == 0,
                row["structure_basis_close_without_session"] == 0,
                row["duplicate_identical_price_lines"] == 0,
                row["inferred_quote_session_label_without_evidence"] == 0,
                ai_fallback_parity,
            )
        ) else "FAIL"
        output_by_market[market].append(row)
        messages_by_market[market].append(
            {
                "ticker": ticker,
                "route": route,
                "text": selected,
                "logical_identity": f"{NAMESPACE}:{ticker}:{observed_at}",
            }
        )
    provider_calls = (
        raw_payload.get("provider_calls", {})
        if isinstance(raw_payload, Mapping)
        else {}
    )
    for market, output_path in (("US", args.us_output), ("KR", args.kr_output)):
        rows = output_by_market[market]
        failed = [row["ticker"] for row in rows if row["status"] != "PASS"]
        payload = {
            "contract": CONTRACT,
            "market": market,
            "observed_at": observed_at,
            "universe_count": len(rows),
            "rows": rows,
            "messages": messages_by_market[market],
            "failed_tickers": failed,
            "provider_calls": provider_calls,
            "status": "PASS" if not failed else "FAIL",
        }
        _write_json(output_path, payload)
    failed_all = [
        row["ticker"]
        for rows in output_by_market.values()
        for row in rows
        if row["status"] != "PASS"
    ]
    print(
        json.dumps(
            {
                "status": "PASS" if not failed_all else "FAIL",
                "us_count": len(output_by_market["US"]),
                "kr_count": len(output_by_market["KR"]),
                "failed_tickers": failed_all,
            },
            sort_keys=True,
        )
    )


async def _send(args: argparse.Namespace) -> None:
    payloads = [_read_json(path) for path in args.inputs]
    if any(
        not isinstance(payload, Mapping) or payload.get("status") != "PASS"
        for payload in payloads
    ):
        raise ValueError("all replay evidence must be PASS")
    messages = [
        message
        for payload in payloads
        if isinstance(payload, Mapping)
        for message in payload.get("messages", [])
        if isinstance(message, Mapping)
    ]
    if len(messages) != 20 or len({str(row.get("ticker")) for row in messages}) != 20:
        raise ValueError("expected exact 20-subject test payload")
    env = load_env_values(args.env_file)
    sink = audit_test_sink(env)
    if sink.get("available") is not True:
        raise ValueError(f"test sink unavailable: {sink.get('reason')}")
    selected_key = str(sink.get("selected_test_key_name") or "")
    receipt = await deliver_test_messages(
        sorted(messages, key=lambda row: str(row.get("ticker") or "")),
        token=env.get("TELEGRAM_BOT_TOKEN") or "",
        test_chat_id=env.get(selected_key) or "",
        production_chat_id=env.get("TELEGRAM_CHAT_ID") or "",
        test_sink_alias=str(sink["test_sink_alias"]),
        production_sink_alias=str(sink["production_sink_alias"]),
        receipt_path=args.receipt,
        contract="provisional-bollinger-price-label-test-delivery-v2",
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


def main() -> None:
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers(dest="command", required=True)
    replay = subparsers.add_parser("replay")
    replay.add_argument("--raw-input", type=Path, required=True)
    replay.add_argument("--us-ai", type=Path, required=True)
    replay.add_argument("--us-fallback", type=Path, required=True)
    replay.add_argument("--kr-ai", type=Path, required=True)
    replay.add_argument("--kr-fallback", type=Path, required=True)
    replay.add_argument("--observed-at", required=True)
    replay.add_argument("--us-output", type=Path, required=True)
    replay.add_argument("--kr-output", type=Path, required=True)
    send = subparsers.add_parser("send-test")
    send.add_argument("--inputs", type=Path, nargs="+", required=True)
    send.add_argument("--env-file", type=Path, required=True)
    send.add_argument("--receipt", type=Path, required=True)
    args = parser.parse_args()
    if args.command == "replay":
        _replay(args)
    else:
        asyncio.run(_send(args))


if __name__ == "__main__":
    main()
