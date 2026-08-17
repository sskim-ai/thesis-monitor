from __future__ import annotations

import argparse
import asyncio
from datetime import date, timedelta
import hashlib
import json
import os
from pathlib import Path
from typing import Iterable

from sqlmodel import Session, create_engine, select

from app.config import get_settings
from app.models.security import SecurityMaster
from app.models.watchlist import WatchlistItem
from app.providers.opendart_corp_codes import load_opendart_companies
from app.services.numeric_provenance_service import bind_numeric_fact_references
from app.services.numeric_semantic_registry import build_numeric_registry
from app.services.opendart_financial_recovery_service import OpenDartRecoveryClient


REPRESENTATIVE_TICKERS = ("005930", "005490", "086280", "003690", "000660")
QUALITY_FIELD_MAP = {
    "latest_revenue": "revenue",
    "latest_operating_income": "operating_income",
    "latest_net_income": "net_income",
}
GROWTH_FIELD_LABELS = {
    "revenue": "매출",
    "operating_income": "영업이익",
    "net_income": "순이익",
}


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Archive-only OpenDART authoritative financial recovery"
    )
    parser.add_argument("--database", required=True, type=Path)
    parser.add_argument("--source-packet", required=True, type=Path)
    parser.add_argument("--source-messages", required=True, type=Path)
    parser.add_argument("--cache-dir", required=True, type=Path)
    parser.add_argument("--audit-output", required=True, type=Path)
    parser.add_argument("--preview-output", required=True, type=Path)
    parser.add_argument("--lookback-days", type=int, default=500)
    parser.add_argument("--max-filings", type=int, default=1)
    return parser


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for chunk in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _json_default(value: object) -> str:
    if isinstance(value, date):
        return value.isoformat()
    raise TypeError(type(value).__name__)


def _write_json(path: Path, value: object) -> None:
    payload = json.dumps(
        value,
        ensure_ascii=False,
        indent=2,
        sort_keys=True,
        default=_json_default,
    ) + "\n"
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f".{path.name}.{os.getpid()}.tmp")
    temporary.write_text(payload, encoding="utf-8")
    os.replace(temporary, path)


def _write_text(path: Path, value: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f".{path.name}.{os.getpid()}.tmp")
    temporary.write_text(value, encoding="utf-8")
    os.replace(temporary, path)


def _load_json(path: Path) -> dict[str, object]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"expected JSON object: {path}")
    return value


def _active_kr(database: Path) -> tuple[list[dict[str, str]], str]:
    url = f"sqlite:///file:{database.resolve()}?mode=ro&immutable=1&uri=true"
    engine = create_engine(url)
    with Session(engine) as session:
        watchlist = list(
            session.exec(
                select(WatchlistItem).where(WatchlistItem.active.is_(True))
            ).all()
        )
        security = {
            row.ticker: row
            for row in session.exec(select(SecurityMaster)).all()
        }
    rows = [
        {
            "ticker": item.ticker,
            "company_name": item.company_name,
            "corp_code": str(
                getattr(security.get(item.ticker), "corp_code", None) or ""
            ),
        }
        for item in watchlist
        if item.ticker.isdigit() and len(item.ticker) == 6
    ]
    return sorted(rows, key=lambda item: item["ticker"]), _sha256(database)


def _find_values(value: object, key: str) -> Iterable[object]:
    if isinstance(value, dict):
        for name, item in value.items():
            if name == key:
                yield item
            yield from _find_values(item, key)
    elif isinstance(value, list):
        for item in value:
            yield from _find_values(item, key)


def _blocked_fields(packet_stock: dict[str, object]) -> set[str]:
    blocked = {
        QUALITY_FIELD_MAP[item]
        for values in _find_values(packet_stock, "denied_fields")
        if isinstance(values, list)
        for item in values
        if item in QUALITY_FIELD_MAP
    }
    critical = {
        str(reason)
        for values in _find_values(packet_stock, "critical_reason_codes")
        if isinstance(values, list)
        for reason in values
    }
    if critical:
        blocked.update({"revenue", "operating_income", "net_income"})
    return blocked


def _source_packet_fields(packet_stock: dict[str, object]) -> dict[str, object]:
    earnings = next(
        (
            item
            for item in packet_stock.get("fact_catalog", [])
            if isinstance(item, dict) and item.get("fact_type") == "earnings"
        ),
        {},
    )
    fields = earnings.get("fields") if isinstance(earnings, dict) else {}
    quality = earnings.get("field_quality") if isinstance(earnings, dict) else {}
    output: dict[str, object] = {}
    for name, path in (
        ("revenue", "fields.revenue.value"),
        ("operating_income", "fields.operating_income.value"),
        ("operating_margin", "fields.operating_margin_pct"),
        ("revenue_yoy", "fields.revenue_yoy_pct"),
        ("operating_income_yoy", "fields.operating_income_yoy_pct"),
    ):
        cursor: object = fields
        for part in path.removeprefix("fields.").split("."):
            cursor = cursor.get(part) if isinstance(cursor, dict) else None
        field_quality = quality.get(path) if isinstance(quality, dict) else None
        output[name] = {
            "value": cursor,
            "quality_state": (
                field_quality.get("state")
                if isinstance(field_quality, dict)
                else "unknown"
            ),
            "prose_eligible": (
                field_quality.get("prose_eligible") is True
                if isinstance(field_quality, dict)
                else False
            ),
            "financial_lineage_contract": None,
        }
    return output


def _period_label(lineage: dict[str, object]) -> str:
    end = date.fromisoformat(str(lineage["amount_period_end"]))
    scope = lineage.get("amount_period_type")
    period = (
        f"{end.year}년 {end.month // 3}분기"
        if scope == "single_quarter"
        else f"{end.year}년 상반기 누적"
        if scope == "year_to_date_cumulative" and end.month == 6
        else f"{end.year}년 {end.month}월 말"
        if scope == "point_in_time"
        else f"{end.year}년 연간"
    )
    basis = (
        "연결 기준"
        if lineage.get("statement_basis_state") == "verified_consolidated"
        else "별도 기준"
    )
    return f"{period} {basis}"


def _financial_fact(ticker: str, recovered: dict[str, object]) -> dict[str, object]:
    fields = recovered["fields"]
    earnings: dict[str, object] = {
        "financial_period_required": True,
        "field_period_labels": {},
        "field_statement_basis": {},
    }
    quality: dict[str, object] = {}
    mapping = {
        "revenue": ("revenue", "latest_revenue"),
        "operating_income": ("operating_income", "latest_operating_income"),
    }
    for name, (target, period_key) in mapping.items():
        item = fields[name]
        lineage = item.get("lineage") if isinstance(item, dict) else None
        if not isinstance(lineage, dict) or item.get("status") != "verified_usable":
            continue
        earnings[target] = {"value": item["value"], "currency": lineage["currency"]}
        earnings["field_period_labels"][period_key] = _period_label(lineage)
        earnings["field_statement_basis"][period_key] = {
            "state": lineage["statement_basis_state"],
            "basis": lineage["statement_basis"],
        }
        quality[f"fields.{target}.value"] = {
            "state": "verified_usable",
            "prose_eligible": True,
            "source_filing_identifier": lineage["source_filing"],
            "source_row_identity": lineage["source_row_identity"],
            "amount_period_type": lineage["amount_period_type"],
            "amount_period_start": lineage["amount_period_start"],
            "amount_period_end": lineage["amount_period_end"],
            "statement_basis_state": lineage["statement_basis_state"],
        }
    margin = fields["operating_margin"]
    if margin.get("status") == "verified_usable":
        earnings["operating_margin_pct"] = margin["value"]
        operating = fields["operating_income"]["lineage"]
        earnings["field_period_labels"]["latest_operating_margin"] = _period_label(
            operating
        )
        quality["fields.operating_margin_pct"] = {
            "state": "verified_usable",
            "prose_eligible": True,
        }
    for name, target, period_key in (
        ("revenue", "revenue_yoy_pct", "latest_revenue_yoy"),
        (
            "operating_income",
            "operating_income_yoy_pct",
            "latest_operating_income_yoy",
        ),
    ):
        item = fields[name]
        yoy = item.get("yoy") if isinstance(item, dict) else None
        lineage = item.get("lineage") if isinstance(item, dict) else None
        if (
            isinstance(yoy, dict)
            and yoy.get("status") == "verified_usable"
            and isinstance(lineage, dict)
        ):
            earnings[target] = yoy["value"]
            earnings["field_period_labels"][period_key] = _period_label(lineage)
            quality[f"fields.{target}"] = {
                "state": "verified_usable",
                "prose_eligible": True,
            }
    return {
        "fact_id": f"earnings:recovery:{ticker}",
        "fact_type": "earnings",
        "fields": earnings,
        "field_quality": quality,
    }


def _withheld_growth_labels(recovered: dict[str, object]) -> list[str]:
    fields = recovered["fields"]
    return [
        label
        for name, label in GROWTH_FIELD_LABELS.items()
        if fields[name].get("status") == "verified_usable"
        and fields[name].get("yoy", {}).get("status") != "verified_usable"
    ]


def _bind_recovery_message(
    ticker: str,
    company_name: str,
    recovered: dict[str, object],
) -> tuple[str, dict[str, object]]:
    fact = _financial_fact(ticker, recovered)
    registry = build_numeric_registry([fact])
    refs: list[dict[str, str]] = []
    placeholders: list[str] = []
    fields = fact["fields"]
    for ref_id, field_path in (
        ("revenue", "fields.revenue.value"),
        ("operating_income", "fields.operating_income.value"),
        ("operating_margin", "fields.operating_margin_pct"),
        ("revenue_yoy", "fields.revenue_yoy_pct"),
        ("operating_income_yoy", "fields.operating_income_yoy_pct"),
    ):
        cursor: object = fields
        for part in field_path.removeprefix("fields.").split("."):
            cursor = cursor.get(part) if isinstance(cursor, dict) else None
        if cursor is None:
            continue
        refs.append(
            {
                "ref_id": ref_id,
                "fact_id": fact["fact_id"],
                "field_path": field_path,
                "text_ref": "core_judgment.text",
            }
        )
        placeholders.append(f"{{{{numeric:{ref_id}}}}}")
    if placeholders:
        text = "최근 정식 공시에서 확인한 항목입니다.\n• " + "\n• ".join(
            placeholders
        )
    else:
        text = (
            "최근 정식 공시의 손익 항목을 재확인했지만 기존의 중대한 재무 품질 "
            "충돌이 해소되지 않아 손익 금액과 파생 비교는 계속 사용하지 않습니다."
        )
    withheld = _withheld_growth_labels(recovered)
    if withheld:
        text += (
            f" {'·'.join(withheld)} 금액은 확인되지만 전년 동기와 같은 기준인지 "
            "확인되지 않아 해당 성장률은 표시하지 않습니다."
        )
    packet = {
        "stocks": [{"ticker": ticker, "numeric_registry": registry}]
    }
    output = {
        "stock_reviews": [
            {
                "ticker": ticker,
                "facts_used": [fact["fact_id"]],
                "core_judgment": {"text": text},
                "numeric_claims": [],
                "numeric_fact_refs": refs,
            }
        ]
    }
    bound = bind_numeric_fact_references(packet, output)
    final = bound.output["stock_reviews"][0]["core_judgment"]["text"]
    message = (
        "🤖 KR 재무 회복 점검\n\n"
        f"🏢 {company_name}({ticker})\n\n"
        "📈 사업·실적\n"
        f"{final}"
    )
    return message, bound.report


async def _run(args: argparse.Namespace) -> tuple[dict[str, object], str]:
    settings = get_settings()
    if not settings.opendart_api_key:
        raise RuntimeError("OPENDART_API_KEY is not configured")
    active, database_sha = _active_kr(args.database)
    packet = _load_json(args.source_packet)
    packet_stocks = {
        str(item.get("ticker") or ""): item
        for item in packet.get("stocks", [])
        if isinstance(item, dict)
    }
    messages = _load_json(args.source_messages)
    before_messages = {
        str(item.get("ticker") or ""): str(item.get("text") or "")
        for item in messages.get("messages", [])
        if isinstance(item, dict)
    }
    companies = await load_opendart_companies(settings.opendart_api_key)
    by_ticker = {item.stock_code: item for item in companies if item.stock_code}
    client = OpenDartRecoveryClient(settings.opendart_api_key, args.cache_dir)
    results: dict[str, dict[str, object]] = {}
    api_failures: list[dict[str, str]] = []
    begin = date.today() - timedelta(days=args.lookback_days)
    for item in active:
        company = by_ticker.get(item["ticker"])
        corp_code = item["corp_code"] or (company.corp_code if company else "")
        if not corp_code:
            api_failures.append(
                {"ticker": item["ticker"], "reason": "corp_code_unresolved"}
            )
            continue
        try:
            selected, history = await client.discover(
                ticker=item["ticker"],
                corp_code=corp_code,
                begin=begin,
                end=date.today(),
                limit=args.max_filings,
            )
            if not selected:
                raise ValueError("formal_filing_unavailable")
            call_start = client.provider_calls
            recovered = await client.recover_filing(
                selected[0],
                blocked_fields=_blocked_fields(packet_stocks.get(item["ticker"], {})),
            )
            recovered["provider_calls_for_ticker"] = client.provider_calls - call_start
        except Exception as error:
            api_failures.append(
                {"ticker": item["ticker"], "reason": type(error).__name__}
            )
            continue
        recovered["filing_history"] = [filing.__dict__ for filing in history]
        recovered["company_name"] = item["company_name"]
        recovered["before_source_packet_fields"] = _source_packet_fields(
            packet_stocks.get(item["ticker"], {})
        )
        results[item["ticker"]] = recovered

    previews: list[str] = []
    binding: dict[str, object] = {}
    before_after: dict[str, object] = {}
    for ticker in REPRESENTATIVE_TICKERS:
        if ticker not in results:
            continue
        message, report = _bind_recovery_message(
            ticker, str(results[ticker]["company_name"]), results[ticker]
        )
        previews.append(message)
        binding[ticker] = report
        before_after[ticker] = {
            "before_message": before_messages.get(ticker),
            "after_shadow_message": message,
            "human_quality_status": "pending_work_human_review",
        }

    field_items = [
        field
        for result in results.values()
        for field in result["fields"].values()
        if isinstance(field, dict)
    ]
    direct_names = {
        "revenue",
        "operating_income",
        "net_income",
        "assets",
        "equity",
        "inventory",
        "operating_cash_flow",
    }
    direct_fields = [
        result["fields"][name]
        for result in results.values()
        for name in direct_names
    ]
    growth_fields = [
        field["yoy"]
        for result in results.values()
        for name, field in result["fields"].items()
        if name in {"revenue", "operating_income", "net_income"}
        and isinstance(field, dict)
        and isinstance(field.get("yoy"), dict)
    ]
    audit = {
        "contract": "phase8-1-1-authoritative-financial-recovery-audit-v1",
        "source_database_sha256": database_sha,
        "source_packet": args.source_packet.name,
        "source_packet_sha256": _sha256(args.source_packet),
        "source_messages_sha256": _sha256(args.source_messages),
        "raw_cache_root": str(args.cache_dir),
        "active_tickers": [item["ticker"] for item in active],
        "results": results,
        "before_after": before_after,
        "numeric_binding": binding,
        "summary": {
            "active_count": len(active),
            "recovered_ticker_count": len(results),
            "api_failures": api_failures,
            "provider_calls": client.provider_calls + 1,
            "corp_code_directory_calls": 1,
            "safe_direct_facts": sum(
                item.get("status") == "verified_usable" for item in direct_fields
            ),
            "safe_income_statement_amounts": sum(
                result["fields"][name].get("status") == "verified_usable"
                for result in results.values()
                for name in ("revenue", "operating_income", "net_income")
            ),
            "safe_operating_margins": sum(
                result["fields"]["operating_margin"].get("status")
                == "verified_usable"
                for result in results.values()
            ),
            "safe_inventory_facts": sum(
                result["fields"]["inventory"].get("status") == "verified_usable"
                for result in results.values()
            ),
            "denied_direct_facts": sum(
                item.get("status") == "denied" for item in direct_fields
            ),
            "unknown_direct_facts": sum(
                item.get("status") == "unknown" for item in direct_fields
            ),
            "safe_yoy": sum(
                item.get("status") == "verified_usable" for item in growth_fields
            ),
            "withheld_yoy": sum(
                item.get("status") != "verified_usable" for item in growth_fields
            ),
            "xbrl_attempts": sum(
                int(result["xbrl"]["attempts"]) for result in results.values()
            ),
            "xbrl_resolved": sum(
                int(result["xbrl"]["resolved"]) for result in results.values()
            ),
            "xbrl_cache_hits": client.xbrl_cache_hits,
            "capex_component_candidates": sum(
                len(result["capex_components"]) for result in results.values()
            ),
            "capex_aggregation_eligible": sum(
                item.get("aggregation_eligible") is True
                for result in results.values()
                for item in result["capex_components"]
            ),
            "all_field_records": len(field_items),
        },
        "mutations": {
            "telegram_sends": 0,
            "operating_database": 0,
            "assessment": 0,
            "archive": 0,
            "pilot": 0,
            "scheduled_tasks": 0,
            "production_assist": 0,
        },
        "human_quality_status": "pending_work_human_review",
    }
    preview = "# Phase 8.1.1 KR Financial Recovery Before / After\n\n"
    preview += (
        "Archive-only shadow output. No Telegram send, assessment change, database write, "
        "or Pilot mutation occurred.\n\n"
    )
    sections: list[str] = []
    for ticker, after in zip(
        (ticker for ticker in REPRESENTATIVE_TICKERS if ticker in results), previews
    ):
        before = before_messages.get(ticker, "Persisted message unavailable")
        sections.append(
            f"## {results[ticker]['company_name']} ({ticker})\n\n"
            "### Before: persisted natural-live payload\n\n"
            f"{before}\n\n"
            "### After: archive-only recovered financial payload\n\n"
            f"{after}"
        )
    preview += "\n\n---\n\n".join(sections) + "\n"
    return audit, preview


def main() -> None:
    args = _parser().parse_args()
    audit, preview = asyncio.run(_run(args))
    _write_json(args.audit_output, audit)
    _write_text(args.preview_output, preview)


if __name__ == "__main__":
    main()
