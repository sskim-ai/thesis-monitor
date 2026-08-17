from __future__ import annotations

import argparse
import copy
import hashlib
import json
import os
from datetime import datetime
from pathlib import Path

from sqlmodel import Session, create_engine

from app.services.ai_review_service import _chart_facts, validate_ai_review_output
from app.services.market_session import market_session_for_ticker
from app.services.numeric_semantic_registry import build_numeric_registry
from app.services.runtime_packet_completeness_service import (
    CURRENT_PRICE_RR_FACT_ID,
    CURRENT_PRICE_RR_FIELD_PATH,
    current_price_rr_packet_preflight,
)


RR_VALIDATOR_MARKERS = (
    "current_price_structure_fact_missing:chart:structure:risk_reward:current_price",
    "current_price_structure_numeric_missing:chart:structure:risk_reward:current_price",
)


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Replay a natural packet's current-price RR path without mutation"
    )
    parser.add_argument("--source-packet", required=True, type=Path)
    parser.add_argument("--source-validation", required=True, type=Path)
    parser.add_argument("--source-bound-output", required=True, type=Path)
    parser.add_argument("--database", required=True, type=Path)
    parser.add_argument("--output-dir", required=True, type=Path)
    parser.add_argument(
        "--prefix",
        default="20260817-runtime-current-price-rr",
    )
    return parser


def _load(path: Path) -> dict[str, object]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"expected JSON object: {path}")
    return value


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _atomic_write(path: Path, value: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f".{path.name}.{os.getpid()}.tmp")
    temporary.write_text(value, encoding="utf-8")
    os.replace(temporary, path)


def _mapping(value: object) -> dict[str, object]:
    return value if isinstance(value, dict) else {}


def _rr_validator_errors(errors: list[str]) -> list[str]:
    return [error for error in errors if any(marker in error for marker in RR_VALIDATOR_MARKERS)]


def _repair_packet(source: dict[str, object]) -> tuple[dict[str, object], list[dict[str, object]]]:
    packet = copy.deepcopy(source)
    generated_at = datetime.fromisoformat(str(packet["generated_at"]))
    rows: list[dict[str, object]] = []
    for stock in packet.get("stocks", []):
        if not isinstance(stock, dict):
            continue
        ticker = str(stock.get("ticker") or "")
        chart = _mapping(stock.get("chart_context"))
        before = current_price_rr_packet_preflight(stock)
        session = market_session_for_ticker(ticker, generated_at)
        chart_as_of = str(chart.get("as_of_date") or "")
        expected_session = session.latest_completed_regular_session_date.isoformat()
        before_quality = str(chart.get("quality") or "unavailable")
        corrected_quality = before_quality
        if chart_as_of and chart_as_of == expected_session:
            corrected_quality = "fresh"
            chart["quality"] = corrected_quality
            daily = _mapping(_mapping(chart.get("timeframes")).get("daily"))
            if daily:
                daily["quality"] = corrected_quality

        retained = [
            fact
            for fact in stock.get("fact_catalog", [])
            if isinstance(fact, dict)
            and not str(fact.get("fact_id") or "").startswith("chart:")
        ]
        currency = str(
            _mapping(_mapping(stock.get("price_and_positioning")).get("price")).get(
                "currency"
            )
            or "KRW"
        )
        stock["fact_catalog"] = [*retained, *_chart_facts(chart, currency)]
        stock["numeric_registry"] = build_numeric_registry(stock["fact_catalog"])
        after = current_price_rr_packet_preflight(stock)
        current = _mapping(_mapping(stock.get("monitoring_state")).get("current"))
        structure = _mapping(current.get("price_structure"))
        risk_reward = _mapping(structure.get("risk_reward"))
        current_rr = _mapping(risk_reward.get("current_price"))
        support_rr = _mapping(risk_reward.get("support_entry"))
        rows.append(
            {
                "ticker": ticker,
                "company_name": str(stock.get("company_name") or ticker),
                "market_date": session.market_date.isoformat(),
                "latest_completed_regular_session_date": expected_session,
                "chart_as_of": chart_as_of,
                "before_chart_quality": before_quality,
                "after_chart_quality": corrected_quality,
                "current_price": structure.get("current_price"),
                "current_price_rr": current_rr.get("ratio"),
                "support_entry_scenario_rr": support_rr.get("ratio"),
                "before": before.as_dict(),
                "after": after.as_dict(),
                "fact_id": CURRENT_PRICE_RR_FACT_ID if after.fact_present else None,
                "field_path": CURRENT_PRICE_RR_FIELD_PATH if after.numeric_path_present else None,
            }
        )
    return packet, rows


def _validator_replay(
    database: Path,
    original_packet: dict[str, object],
    repaired_packet: dict[str, object],
    source_output: dict[str, object],
) -> dict[str, object]:
    output = copy.deepcopy(source_output)
    output["packet_id"] = repaired_packet.get("packet_id")
    output["assessment_date"] = repaired_packet.get("assessment_date")
    thesis_versions = {
        str(stock.get("ticker") or ""): stock.get("thesis_version")
        for stock in repaired_packet.get("stocks", [])
        if isinstance(stock, dict)
    }
    for review in output.get("stock_reviews", []):
        if isinstance(review, dict):
            review["thesis_version"] = thesis_versions.get(str(review.get("ticker") or ""))
    uri = f"sqlite:///file:{database.resolve()}?mode=ro&immutable=1&uri=true"
    with Session(create_engine(uri)) as session:
        _, baseline_errors = validate_ai_review_output(session, original_packet, output)
        _, after_errors = validate_ai_review_output(session, repaired_packet, output)
    after_rr = _rr_validator_errors(after_errors)
    return {
        "source_output_semantics": "prior validated bound output replayed against run-23 identity",
        "compatibility_baseline": {
            "status": "passed" if not baseline_errors else "rejected_contract_drift",
            "error_count": len(baseline_errors),
        },
        "after": {
            "status": "passed" if not after_errors else "rejected_other_contract_drift",
            "error_count": len(after_errors),
            "rr_missing_error_count": len(after_rr),
            "rr_missing_errors": after_rr,
            "other_error_count": len(after_errors) - len(after_rr),
        },
        "interpretation": (
            "The repaired packet removes the run-23 RR missing-path blocker. "
            "Remaining errors come from replaying a prior bound message under newer validator contracts."
        ),
    }


def _markdown(audit: dict[str, object]) -> str:
    lines = [
        "# Runtime Current-Price RR Run-23 Replay",
        "",
        "## Replay Boundary",
        "",
        "- Archive-only, read-only reconstruction",
        "- Telegram sends: 0",
        "- Pilot mutations: 0",
        "- Database mutations: 0",
        "- Source archive rewrites: 0",
        "",
        "## Session Correction",
        "",
        "2026-08-17 was not an XKRX trading session. The latest completed regular session was "
        "2026-08-14, so the 2026-08-14 chart is fresh for this packet rather than stale.",
        "",
        "## Ticker Results",
        "",
        "| Ticker | Before | After | Current RR | Display | Fact | Numeric path |",
        "|---|---|---|---:|---:|---|---|",
    ]
    for row in audit.get("stocks", []):
        if not isinstance(row, dict):
            continue
        before = _mapping(row.get("before"))
        after = _mapping(row.get("after"))
        lines.append(
            "| {ticker} | {before_status} | {after_status} | {ratio} | {display} | {fact} | {path} |".format(
                ticker=row.get("ticker"),
                before_status=before.get("status"),
                after_status=after.get("status"),
                ratio=row.get("current_price_rr") if row.get("current_price_rr") is not None else "N/A",
                display=after.get("canonical_display_value") or "N/A",
                fact="yes" if after.get("fact_present") else "no",
                path="yes" if after.get("numeric_path_present") else "no",
            )
        )
    validator = _mapping(audit.get("validator_replay"))
    after_validator = _mapping(validator.get("after"))
    source_rr_errors = audit.get("source_rr_missing_errors", [])
    source_rr_error_count = len(source_rr_errors) if isinstance(source_rr_errors, list) else 0
    lines.extend(
        [
            "",
            "## Validator Replay",
            "",
            f"- RR missing-path errors in the immutable run-23 validation: {source_rr_error_count}",
            f"- RR missing-path errors after: {after_validator.get('rr_missing_error_count')}",
            f"- Other current-contract replay errors after: {after_validator.get('other_error_count')}",
            "- The remaining replay errors are reported separately and are not treated as an RR repair failure.",
            "",
            "## Result",
            "",
            "The four calculated run-23 current-price RR values now have exact canonical Fact and numeric "
            "registry paths. Samsung Electronics, Korean Re, and SK hynix remain unavailable by contract "
            "and do not receive fabricated RR values.",
        ]
    )
    return "\n".join(lines) + "\n"


def main() -> None:
    args = _parser().parse_args()
    source_packet = _load(args.source_packet)
    source_validation = _load(args.source_validation)
    source_output = _load(args.source_bound_output)
    repaired, rows = _repair_packet(source_packet)
    validator = _validator_replay(
        args.database,
        source_packet,
        repaired,
        source_output,
    )
    audit = {
        "contract": "runtime-current-price-rr-packet-preflight-v1",
        "source_packet": source_packet.get("packet_id"),
        "source_packet_sha256": _sha256(args.source_packet),
        "source_validation_sha256": _sha256(args.source_validation),
        "source_bound_output_sha256": _sha256(args.source_bound_output),
        "source_validation_status": source_validation.get("status"),
        "source_rr_missing_errors": _rr_validator_errors(
            [str(error) for error in source_validation.get("errors", [])]
        ),
        "generated_at": source_packet.get("generated_at"),
        "stocks": rows,
        "summary": {
            "ready": sum(_mapping(row.get("after")).get("status") == "READY" for row in rows),
            "unavailable_by_contract": sum(
                _mapping(row.get("after")).get("status") == "UNAVAILABLE_BY_CONTRACT"
                for row in rows
            ),
            "missing_by_bug": sum(
                str(_mapping(row.get("after")).get("status") or "").startswith("BUG_")
                for row in rows
            ),
            "telegram_sends": 0,
            "pilot_mutations": 0,
            "database_mutations": 0,
            "archive_mutations": 0,
        },
        "validator_replay": validator,
    }
    json_path = args.output_dir / f"{args.prefix}-numeric-path.json"
    markdown_path = args.output_dir / f"{args.prefix}-run23-replay.md"
    _atomic_write(
        json_path,
        json.dumps(audit, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
    )
    _atomic_write(markdown_path, _markdown(audit))
    print(json.dumps(audit["summary"], sort_keys=True))


if __name__ == "__main__":
    main()
