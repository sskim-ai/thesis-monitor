from __future__ import annotations

import fcntl
import hashlib
import json
import logging
import math
import os
import re
import socket
import uuid
from contextlib import contextmanager
from dataclasses import asdict, dataclass
from datetime import UTC, date, datetime, timedelta
from pathlib import Path
from tempfile import NamedTemporaryFile
from typing import Iterator, Literal

from pydantic import ValidationError
from sqlmodel import Session, select

from app.config import get_settings
from app.models.macro import MacroBriefing
from app.models.company import Company
from app.models.security import SecurityMaster
from app.models.thesis import InvestmentThesis, MonitorRun, ThesisAssessment
from app.models.watchlist import WatchlistItem
from app.schemas.ai_review import AIDailyReviewOutput, AIStockReview
from app.services.canonical_fact_service import (
    canonical_capital_action_fact,
    canonical_event_fact,
    compact_krw_amount,
)
from app.services.daily_digest import build_daily_digest
from app.services.market_session import market_scope_for_security


logger = logging.getLogger(__name__)

PACKET_SCHEMA_VERSION = "1"
OUTPUT_SCHEMA_VERSION = "1"
ANALYSIS_POLICY_VERSION = "daily-review-v2"
AIReviewMarket = Literal["us", "kr"]

_INTERNAL_TEXT = re.compile(
    r"(?:opendart|\bfs_div\b|\bsj_div\b|\bperiod_scope\b|\bamount_scope\b|"
    r"\breport_code\b|\bprovider\s*(?:=|:)|\bparser\s*(?:=|:)|"
    r"\bselected_for_valuation\s*(?:=|:)|\bthstrm_nm\s*(?:=|:)|"
    r"\bunit\s*(?:=|:))",
    re.IGNORECASE,
)
_INTERNAL_KEYS = {
    "provider",
    "parser",
    "raw_payload",
    "raw_reference",
    "source_url",
    "selected_for_valuation",
    "fs_div",
    "sj_div",
    "period_scope",
    "amount_scope",
    "report_code",
    "thstrm_nm",
    "unit",
}
_NUMBER = re.compile(r"(?<![\w])[-+]?\d[\d,]*(?:\.\d+)?%?")
_INVALID_HISTORY = {"price_share_basis_unverified", "price_share_basis_mismatch"}
_COMPARABLE_HISTORY = {"normal", "comparable", "verified"}


@dataclass(frozen=True)
class PacketWriteResult:
    status: str
    packet_id: str | None = None
    path: str | None = None
    created: bool = False
    reason: str | None = None


@dataclass(frozen=True)
class ClaimResult:
    status: str
    packet_id: str | None = None
    claim_id: str | None = None
    packet_path: str | None = None
    claim_path: str | None = None
    temp_output_path: str | None = None
    final_output_path: str | None = None
    reason: str | None = None


@dataclass(frozen=True)
class OutputValidationResult:
    status: str
    packet_id: str | None = None
    output_path: str | None = None
    comparison_path: str | None = None
    errors: tuple[str, ...] = ()


_CORE_FRAMEWORKS = (
    "fact_interpretation_unknown",
    "initial_thesis",
    "market_expectations",
    "risk_kill_condition",
    "multiple_expansion_compression",
    "macro_transmission",
    "valuation_basis_comparability",
    "monitoring_data_quality",
)
_INDUSTRY_FRAMEWORKS = {
    "memory": "memory_valuation",
    "semiconductor": "semiconductor_valuation",
    "insurance": "insurance_reinsurance_valuation",
    "bank": "bank_valuation",
    "epc": "epc_construction_valuation",
    "saas": "saas_recurring_revenue_valuation",
    "biotech": "biotech_valuation",
    "pre_profit": "pre_profit_valuation",
    "automotive": "automotive_valuation",
    "shipping": "shipping_transport_valuation",
    "holding_company": "holding_company_valuation",
    "consumer": "consumer_valuation",
    "cloud": "cloud_platform_valuation",
}
_INDUSTRY_MARKERS = (
    ("memory", ("memory", "메모리", "dram", "nand")),
    ("insurance", ("insurance", "reinsurance", "보험", "재보험")),
    ("bank", ("bank", "은행")),
    ("epc", ("epc", "construction", "건설", "플랜트")),
    ("saas", ("saas", "arr", "recurring revenue", "반복매출")),
    ("biotech", ("biotech", "biopharma", "바이오", "신약")),
    ("pre_profit", ("robotaxi", "pre-profit", "pre profit", "로보택시")),
    ("automotive", ("automotive", "automobile", "자동차", "완성차")),
    ("shipping", ("shipping", "transport", "해운", "운송")),
    ("holding_company", ("holding company", "지주")),
    ("consumer", ("consumer", "소비재")),
    ("cloud", ("cloud", "platform", "클라우드", "플랫폼")),
    ("semiconductor", ("semiconductor", "반도체")),
)


def _root() -> Path:
    return Path(get_settings().data_dir) / "ai_review"


def _directory(name: str) -> Path:
    path = _root() / name
    path.mkdir(parents=True, exist_ok=True)
    return path


def ensure_ai_review_layout() -> None:
    for child in ("inbox", "claims", "locks", "outbox", "rejected", "history"):
        _directory(child)


def _skill_root() -> Path:
    return (
        Path(__file__).resolve().parents[2]
        / ".agents"
        / "skills"
        / "thesis-monitor-daily-review"
    )


def knowledge_manifest() -> dict[str, str | int]:
    reference_root = _skill_root() / "references"
    manifest = _read_json(reference_root / "knowledge-manifest.json")
    mirror = reference_root / "investment-thesis-analysis-monitoring-knowledge.md"
    source = Path(__file__).resolve().parents[2] / str(manifest.get("source_path") or "")
    expected = str(manifest.get("sha256") or "")
    source_bytes = source.read_bytes()
    mirror_hash = hashlib.sha256(mirror.read_bytes()).hexdigest()
    source_hash = hashlib.sha256(source_bytes).hexdigest()
    line_count = len(source_bytes.splitlines())
    byte_count = len(source_bytes)
    if (
        not expected
        or mirror_hash != expected
        or source_hash != expected
        or int(manifest.get("line_count") or -1) != line_count
        or int(manifest.get("byte_count") or -1) != byte_count
    ):
        raise ValueError("Investment Knowledge mirror checksum mismatch")
    return {
        "name": str(manifest["knowledge_name"]),
        "version": str(manifest["knowledge_version"]),
        "sha256": expected,
        "source": str(manifest["source"]),
        "line_count": line_count,
        "byte_count": byte_count,
    }


def investment_framework_routing(
    industry: str | None,
    business_model: str | None,
    thesis_text: str,
    *,
    has_earnings: bool,
    preliminary_earnings: bool,
    has_price_context: bool,
    has_adr_basis_risk: bool,
) -> dict[str, object]:
    haystack = " ".join(
        item.lower() for item in (industry, business_model, thesis_text) if item
    )
    industry_key = "general"
    for candidate, markers in _INDUSTRY_MARKERS:
        if any(marker in haystack for marker in markers):
            industry_key = candidate
            break
    required = list(_CORE_FRAMEWORKS)
    if framework := _INDUSTRY_FRAMEWORKS.get(industry_key):
        required.append(framework)
    if has_earnings:
        required.extend(("financial_calculation_safety", "earnings_quality"))
    if preliminary_earnings:
        required.append("provisional_earnings")
    if has_price_context:
        required.extend(("price_ohlcv", "holder_new_buyer"))
    if has_adr_basis_risk:
        required.append("adr_share_basis")
    return {
        "industry_key": industry_key,
        "required_frameworks": list(dict.fromkeys(required)),
        "knowledge_index": "references/knowledge-index.md",
    }


def _atomic_json(path: Path, payload: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with NamedTemporaryFile("w", encoding="utf-8", dir=path.parent, delete=False) as handle:
        json.dump(payload, handle, ensure_ascii=False, indent=2, sort_keys=True, default=str)
        handle.write("\n")
        handle.flush()
        os.fsync(handle.fileno())
        temporary = Path(handle.name)
    os.replace(temporary, path)


@contextmanager
def _packet_lock(packet_id: str) -> Iterator[Path]:
    lock_key = hashlib.sha256(packet_id.encode("utf-8")).hexdigest()
    lock_path = _directory("locks") / f"{lock_key}.lock"
    descriptor = os.open(lock_path, os.O_RDWR | os.O_CREAT, 0o600)
    try:
        fcntl.flock(descriptor, fcntl.LOCK_EX)
        yield lock_path
    finally:
        fcntl.flock(descriptor, fcntl.LOCK_UN)
        os.close(descriptor)


def _json(value: str, fallback: object) -> object:
    try:
        return json.loads(value)
    except (json.JSONDecodeError, TypeError):
        return fallback


def _dict(value: str) -> dict[str, object]:
    parsed = _json(value, {})
    return parsed if isinstance(parsed, dict) else {}


def _list(value: str) -> list[object]:
    parsed = _json(value, [])
    return parsed if isinstance(parsed, list) else []


def _clean_text(value: object) -> str | None:
    text = str(value or "").strip()
    if not text or _INTERNAL_TEXT.search(text):
        return None
    return text


def _clean_texts(values: object) -> list[str]:
    if not isinstance(values, list):
        return []
    return list(
        dict.fromkeys(text for item in values if (text := _clean_text(item)) is not None)
    )


def _public_value(value: object) -> object:
    if isinstance(value, dict):
        return {
            str(key): cleaned
            for key, item in value.items()
            if str(key).lower() not in _INTERNAL_KEYS
            and (cleaned := _public_value(item)) not in (None, [], {})
        }
    if isinstance(value, list):
        return [cleaned for item in value if (cleaned := _public_value(item)) is not None]
    if isinstance(value, str):
        return _clean_text(value)
    return value


def _scope_for_item(session: Session, item: WatchlistItem) -> str:
    security = session.exec(
        select(SecurityMaster).where(SecurityMaster.ticker == item.ticker)
    ).first()
    exchange = item.exchange or (security.exchange if security is not None else None)
    return market_scope_for_security(item.ticker, exchange)


def _run_type(market: AIReviewMarket) -> str:
    return f"daily_{market}"


def _source_run(
    session: Session,
    run_date: date,
    market: AIReviewMarket,
) -> MonitorRun | None:
    return session.exec(
        select(MonitorRun).where(
            MonitorRun.run_date == run_date,
            MonitorRun.run_type == _run_type(market),
        )
    ).first()


def _previous_assessment(
    session: Session,
    assessment: ThesisAssessment,
) -> ThesisAssessment | None:
    return session.exec(
        select(ThesisAssessment)
        .where(
            ThesisAssessment.ticker == assessment.ticker,
            ThesisAssessment.thesis_version == assessment.thesis_version,
            ThesisAssessment.assessment_date < assessment.assessment_date,
        )
        .order_by(ThesisAssessment.assessment_date.desc(), ThesisAssessment.id.desc())
    ).first()


def _assessment_mode(assessment: ThesisAssessment) -> str:
    snapshot = _dict(assessment.thesis_snapshot)
    return str(snapshot.get("assessment_mode") or "daily_delta")


def _material_evidence(assessment: ThesisAssessment) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    for item in _list(assessment.evidence):
        if not isinstance(item, dict):
            continue
        fingerprint = _clean_text(item.get("fingerprint") or item.get("event_fingerprint"))
        title = _clean_text(item.get("title") or item.get("contract_name"))
        materiality = str(item.get("materiality") or "unknown")
        if fingerprint is None or title is None or materiality == "immaterial":
            continue
        rows.append(
            {
                "date": str(item.get("date") or item.get("event_date") or ""),
                "type": str(item.get("event_type") or item.get("type") or "unknown"),
                "title": title,
                "direction": str(item.get("direction") or "neutral"),
                "materiality": materiality,
                **{
                    key: value
                    for key in (
                        "contract_name",
                        "contract_amount",
                        "counterparty",
                        "contract_period",
                        "sales_ratio_pct",
                        "region",
                        "relevance_score",
                    )
                    if (value := _public_value(item.get(key))) is not None
                },
                "event_fingerprint": fingerprint,
            }
        )
    return rows


def _valuation_payload(assessment: ThesisAssessment) -> dict[str, object]:
    snapshot = _dict(assessment.valuation_snapshot)
    fields = (
        "current_price",
        "currency",
        "price_as_of",
        "latest_earnings_period",
        "earnings_context_is_preliminary",
        "latest_revenue",
        "latest_operating_income",
        "latest_operating_margin",
        "latest_revenue_qoq",
        "latest_revenue_yoy",
        "latest_operating_income_qoq",
        "latest_operating_income_yoy",
        "ttm_eps",
        "bvps",
        "forward_eps",
        "forward_bvps",
        "trailing_pe",
        "price_to_book",
        "forward_pe",
        "forward_price_to_book",
        "forward_pe_source",
        "forward_pe_method",
        "forward_price_to_book_source",
        "forward_price_to_book_method",
        "forecast_method",
        "forward_basis",
        "forward_book_basis",
        "estimate_period",
        "historical_comparability",
        "valuation_relative_position",
        "valuation_relative_basis",
        "quality",
    )
    result = {key: snapshot.get(key) for key in fields if snapshot.get(key) is not None}
    comparability = str(snapshot.get("historical_comparability") or "normal")
    if comparability in _COMPARABLE_HISTORY:
        for key in ("historical_pe_statistics", "historical_pb_statistics"):
            value = snapshot.get(key)
            if isinstance(value, dict):
                result[key] = _public_value(value)
    else:
        result["historical_comparison_withheld"] = True
    return result


def _price_payload(assessment: ThesisAssessment) -> dict[str, object]:
    context = _dict(assessment.price_context)
    decision = context.get("decision")
    supply = context.get("supply")
    decision_fields = (
        "current_price",
        "currency",
        "price_as_of",
        "exchange_trade_date",
        "latest_completed_regular_session_date",
        "price_basis",
        "current_position",
        "price_state",
        "price_state_confirmation",
    )
    supply_fields = (
        "available",
        "as_of_date",
        "foreign_net_buy_qty",
        "institution_net_buy_qty",
        "individual_net_buy_qty",
        "foreign_net_buy_qty_5",
        "institution_net_buy_qty_5",
        "individual_net_buy_qty_5",
        "foreign_net_buy_qty_20",
        "institution_net_buy_qty_20",
        "individual_net_buy_qty_20",
        "foreign_holding_qty",
        "foreign_holding_ratio",
        "quality",
        "primary_signal",
        "confidence",
        "validation_status",
    )
    return {
        "price": {
            key: decision.get(key)
            for key in decision_fields
            if isinstance(decision, dict) and decision.get(key) is not None
        },
        "supply": {
            key: supply.get(key)
            for key in supply_fields
            if isinstance(supply, dict) and supply.get(key) is not None
        },
        "cautions": _clean_texts(context.get("warnings")),
    }


def _fact_catalog(
    assessment: ThesisAssessment,
    evidence: list[dict[str, object]],
    valuation: dict[str, object],
    price: dict[str, object],
) -> list[dict[str, object]]:
    facts = [fact for item in evidence if (fact := canonical_event_fact(item))]
    currency = str(valuation.get("currency") or "unknown")
    period = str(valuation.get("latest_earnings_period") or "latest")
    earnings_fields: dict[str, object] = {
        "period": period,
        "preliminary": bool(valuation.get("earnings_context_is_preliminary")),
    }
    earnings_values = {
        "revenue": "latest_revenue",
        "operating_income": "latest_operating_income",
    }
    for target, source in earnings_values.items():
        if (value := valuation.get(source)) is not None:
            earnings_fields[target] = {"value": value, "currency": currency}
    for target, source in (
        ("operating_margin_pct", "latest_operating_margin"),
        ("revenue_qoq_pct", "latest_revenue_qoq"),
        ("revenue_yoy_pct", "latest_revenue_yoy"),
        ("operating_income_qoq_pct", "latest_operating_income_qoq"),
        ("operating_income_yoy_pct", "latest_operating_income_yoy"),
    ):
        if (value := valuation.get(source)) is not None:
            earnings_fields[target] = value
    if len(earnings_fields) > 2:
        facts.append(
            {
                "fact_id": f"earnings:{period}",
                "fact_type": "earnings",
                "as_of_date": period,
                "fields": earnings_fields,
            }
        )
    valuation_fields = {
        key: value
        for key, value in valuation.items()
        if key
        in {
            "ttm_eps",
            "bvps",
            "forward_eps",
            "forward_bvps",
            "trailing_pe",
            "price_to_book",
            "forward_pe",
            "forward_price_to_book",
            "forward_pe_source",
            "forward_pe_method",
            "forward_price_to_book_source",
            "forward_price_to_book_method",
            "forecast_method",
            "forward_basis",
            "forward_book_basis",
            "estimate_period",
            "historical_comparability",
            "historical_pe_statistics",
            "historical_pb_statistics",
            "historical_comparison_withheld",
            "valuation_relative_position",
            "valuation_relative_basis",
        }
    }
    if valuation_fields:
        valuation_fields["currency"] = currency
        facts.append(
            {
                "fact_id": "valuation:current",
                "fact_type": "valuation",
                "as_of_date": str(valuation.get("price_as_of") or ""),
                "fields": valuation_fields,
            }
        )
    price_fields = price.get("price")
    if isinstance(price_fields, dict) and price_fields:
        facts.append(
            {
                "fact_id": "price:current",
                "fact_type": "price",
                "as_of_date": str(price_fields.get("price_as_of") or ""),
                "fields": price_fields,
            }
        )
    supply_fields = price.get("supply")
    if isinstance(supply_fields, dict) and supply_fields:
        facts.append(
            {
                "fact_id": f"positioning:{supply_fields.get('as_of_date') or 'latest'}",
                "fact_type": "positioning",
                "as_of_date": str(supply_fields.get("as_of_date") or ""),
                "fields": supply_fields,
            }
        )
    snapshot = _dict(assessment.thesis_snapshot)
    for item in snapshot.get("capital_action_materiality", []):
        if isinstance(item, dict) and (fact := canonical_capital_action_fact(item)):
            facts.append(fact)
    return facts


def _numeric_unit(field_path: str, fields: dict[str, object]) -> str:
    key = field_path.rsplit(".", 1)[-1]
    if key == "value":
        parent_path = field_path.rsplit(".", 1)[0]
        node: object = fields
        for part in parent_path.split(".")[1:]:
            node = node.get(part) if isinstance(node, dict) else None
        if isinstance(node, dict) and node.get("currency"):
            return str(node["currency"])
    if key.endswith("_pct") or key in {
        "change_pct",
        "percent_change",
        "foreign_holding_ratio",
        "current_percentile",
    }:
        return "pct"
    if "shares" in key or key.endswith("_qty") or "_qty_" in key:
        return "shares"
    if key in {"trailing_pe", "price_to_book", "forward_pe", "forward_price_to_book"}:
        return "x"
    if key in {"ttm_eps", "bvps", "forward_eps", "forward_bvps", "current_price"}:
        return str(fields.get("currency") or "unknown")
    return "number"


def _numeric_registry(facts: list[dict[str, object]]) -> list[dict[str, object]]:
    registry: list[dict[str, object]] = []
    for fact in facts:
        fact_id = str(fact.get("fact_id") or "")
        fields = fact.get("fields")
        if not fact_id or not isinstance(fields, dict):
            continue

        def walk(value: object, path: str) -> None:
            if isinstance(value, dict):
                for key, item in value.items():
                    walk(item, f"{path}.{key}")
            elif isinstance(value, list):
                for index, item in enumerate(value):
                    walk(item, f"{path}.{index}")
            elif isinstance(value, (int, float)) and not isinstance(value, bool):
                registry.append(
                    {
                        "fact_id": fact_id,
                        "field_path": path,
                        "value": value,
                        "unit": _numeric_unit(path, fields),
                        "semantic_type": path.rsplit(".", 1)[-1],
                    }
                )

        walk(fields, "fields")
    return registry


def _stock_packet(
    session: Session,
    item: WatchlistItem,
    assessment: ThesisAssessment,
) -> dict[str, object] | None:
    thesis = session.exec(
        select(InvestmentThesis).where(
            InvestmentThesis.ticker == assessment.ticker,
            InvestmentThesis.version == assessment.thesis_version,
        )
    ).first()
    if thesis is None:
        return None
    company = session.exec(
        select(Company).where(Company.ticker == assessment.ticker)
    ).first()
    evidence = _material_evidence(assessment)
    valuation = _valuation_payload(assessment)
    price = _price_payload(assessment)
    previous = _previous_assessment(session, assessment)
    current_expectation = _public_value(_dict(assessment.market_expectation_assessment))
    thesis_text = " ".join(
        filter(
            None,
            (
                thesis.core_thesis,
                json.dumps(_dict(thesis.valuation_framework), ensure_ascii=False),
                json.dumps(_list(thesis.thesis_drivers), ensure_ascii=False),
            ),
        )
    )
    industry = _clean_text(company.industry) if company is not None else None
    business_model = _clean_text(company.business_units) if company is not None else None
    routing = investment_framework_routing(
        industry,
        business_model,
        thesis_text,
        has_earnings=valuation.get("latest_revenue") is not None,
        preliminary_earnings=bool(valuation.get("earnings_context_is_preliminary")),
        has_price_context=bool(price.get("price")),
        has_adr_basis_risk="adr" in thesis_text.lower()
        or "adr" in json.dumps(valuation, ensure_ascii=False).lower(),
    )
    stock = {
        "ticker": assessment.ticker,
        "company_name": item.company_name,
        "industry": industry,
        "business_model": business_model,
        "knowledge_routing": routing,
        "thesis_version": assessment.thesis_version,
        "assessment_mode": _assessment_mode(assessment),
        "thesis": {
            "core_thesis": thesis.core_thesis,
            "time_horizon": thesis.time_horizon,
            "thesis_drivers": _public_value(_list(thesis.thesis_drivers)),
            "validation_metrics": _public_value(_list(thesis.validation_metrics)),
            "strengthen_signals": _public_value(_list(thesis.strengthen_signals)),
            "weaken_signals": _public_value(_list(thesis.weaken_signals)),
            "invalidation_signals": _public_value(_list(thesis.invalidation_signals)),
            "market_expectations": _public_value(_dict(thesis.market_expectations)),
            "valuation_framework": _public_value(_dict(thesis.valuation_framework)),
            "persistent_risks": _clean_texts(_list(assessment.persistent_watch_risks)),
            "macro_exposures": _public_value(_list(thesis.macro_exposures)),
        },
        "deterministic_assessment": {
            "business_thesis_change": (
                assessment.business_thesis_change or assessment.status
            ),
            "daily_change_severity": assessment.daily_change_severity,
            "earnings_estimate_impact": assessment.earnings_estimate_impact or "unknown",
            "valuation_change": assessment.valuation_change or "unknown",
            "risk_level": assessment.risk_level,
            "structural_risk_level": assessment.structural_risk_level,
            "market_expectation": current_expectation,
            "summary": _clean_text(assessment.summary) or "",
            "confirmed_warnings": _clean_texts(_list(assessment.confirmed_warnings)),
        },
        "evidence": evidence,
        "valuation": valuation,
        "price_and_positioning": price,
        "unknowns": _clean_texts(_list(assessment.unknowns)),
        "data_cautions": list(
            dict.fromkeys(
                [
                    *_clean_texts(_list(assessment.open_warnings)),
                    *_clean_texts(_list(assessment.open_confirmed_warnings)),
                    *price.get("cautions", []),
                ]
            )
        ),
        "previous_assessment": (
            {
                "assessment_date": previous.assessment_date.isoformat(),
                "business_thesis_change": (
                    previous.business_thesis_change or previous.status
                ),
                "earnings_estimate_impact": previous.earnings_estimate_impact,
                "valuation_change": previous.valuation_change,
                "summary": _clean_text(previous.summary) or "",
            }
            if previous is not None
            else None
        ),
    }
    facts = _fact_catalog(assessment, evidence, valuation, price)
    stock["fact_catalog"] = facts
    stock["numeric_registry"] = _numeric_registry(facts)
    return stock


def _market_packet(
    session: Session,
    run_date: date,
    market: AIReviewMarket,
) -> dict[str, object]:
    digest = build_daily_digest(session, run_date, market_scope=market)
    market_facts: list[dict[str, object]] = []
    for index, text in enumerate(digest.macro.key_changes, start=1):
        if clean := _clean_text(text):
            market_facts.append(
                {
                    "fact_id": f"market:change:{index}",
                    "fact_type": "macro_change",
                    "as_of_date": run_date.isoformat(),
                    "fields": {"text": clean},
                }
            )
    night_futures = [asdict(item) for item in digest.night_futures.items]
    for index, item in enumerate(night_futures, start=1):
        market_facts.append(
            {
                "fact_id": f"market:night_futures:{index}",
                "fact_type": "night_futures",
                "as_of_date": str(item.get("session_date") or run_date),
                "fields": _public_value(item),
            }
        )
    fx_items = []
    if digest.kr_close_fx is not None:
        fx_items = [asdict(item) for item in digest.kr_close_fx.items]
        for index, item in enumerate(fx_items, start=1):
            market_facts.append(
                {
                    "fact_id": f"market:fx:{index}",
                    "fact_type": "fx",
                    "as_of_date": run_date.isoformat(),
                    "fields": _public_value(item),
                }
            )
    briefing = session.exec(
        select(MacroBriefing).where(
            MacroBriefing.briefing_date == run_date,
            MacroBriefing.briefing_type == "morning",
        )
    ).first()
    macro_theses = _public_value(_list(briefing.macro_theses)) if briefing else []
    return {
        "regime": {
            "label": digest.macro.regime_label,
            "confidence": digest.macro.confidence,
            "one_line": digest.macro.one_line,
            "axes": [
                {"axis": axis, "explanation": explanation}
                for axis, explanation in digest.macro.axis_explanations
            ],
        },
        "important_changes": _clean_texts(digest.macro.key_changes),
        "integrated_view": _clean_texts(digest.macro.integrated_view),
        "market_assumptions": _clean_texts(digest.macro.market_assumptions),
        "market_theses": macro_theses,
        "night_futures": night_futures,
        "fx": fx_items,
        "data_cautions": _clean_texts(digest.data_quality.items),
        "fact_catalog": market_facts,
        "numeric_registry": _numeric_registry(market_facts),
        "knowledge_routing": {
            "required_frameworks": [*_CORE_FRAMEWORKS, "macro_transmission"],
            "knowledge_index": "references/knowledge-index.md",
        },
    }


def build_ai_review_packet(
    session: Session,
    run_date: date,
    market: AIReviewMarket,
    *,
    generated_at: datetime | None = None,
) -> dict[str, object] | None:
    run = _source_run(session, run_date, market)
    if run is None or run.status != "success" or run.id is None:
        return None
    items = [
        item
        for item in session.exec(select(WatchlistItem)).all()
        if _scope_for_item(session, item) == market
    ]
    assessments = {
        assessment.ticker: assessment
        for assessment in session.exec(
            select(ThesisAssessment).where(
                ThesisAssessment.assessment_date == run_date,
                ThesisAssessment.ticker.in_([item.ticker for item in items]),
            )
        ).all()
    } if items else {}
    stocks = [
        stock
        for item in sorted(items, key=lambda value: value.ticker)
        if (assessment := assessments.get(item.ticker)) is not None
        and (stock := _stock_packet(session, item, assessment)) is not None
    ]
    if len(stocks) != run.success_count:
        return None
    knowledge = knowledge_manifest()
    body = {
        "schema_version": PACKET_SCHEMA_VERSION,
        "analysis_policy_version": ANALYSIS_POLICY_VERSION,
        "knowledge": knowledge,
        "market": market,
        "assessment_date": run_date.isoformat(),
        "source_monitor_run_id": str(run.id),
        "source_monitor_run": {
            "status": run.status,
            "ticker_count": run.ticker_count,
            "success_count": run.success_count,
            "failure_count": run.failure_count,
            "completed_at": run.completed_at,
        },
        "market_context": _market_packet(session, run_date, market),
        "stocks": stocks,
        "ready_for_ai": True,
    }
    canonical = json.dumps(body, ensure_ascii=False, sort_keys=True, default=str)
    digest = hashlib.sha256(canonical.encode("utf-8")).hexdigest()[:12]
    packet_id = f"{run_date.isoformat()}-{market}-run-{run.id}-{digest}"
    return {
        **body,
        "packet_id": packet_id,
        "generated_at": (generated_at or datetime.now(UTC)).astimezone(UTC).isoformat(),
    }


def write_ai_review_packet(
    session: Session,
    run_date: date,
    market: AIReviewMarket,
    *,
    generated_at: datetime | None = None,
) -> PacketWriteResult:
    if get_settings().ai_review_mode == "off":
        return PacketWriteResult(status="disabled", reason="ai_review_mode_off")
    packet = build_ai_review_packet(session, run_date, market, generated_at=generated_at)
    if packet is None:
        return PacketWriteResult(status="not_ready", reason="successful_complete_run_required")
    ensure_ai_review_layout()
    packet_id = str(packet["packet_id"])
    path = _directory("inbox") / f"{packet_id}.json"
    if path.exists():
        return PacketWriteResult(
            status="already_exists", packet_id=packet_id, path=str(path), created=False
        )
    _atomic_json(path, packet)
    return PacketWriteResult(status="created", packet_id=packet_id, path=str(path), created=True)


def try_write_ai_review_packet(
    session: Session,
    run_date: date,
    market: AIReviewMarket,
    *,
    generated_at: datetime | None = None,
) -> PacketWriteResult:
    try:
        return write_ai_review_packet(session, run_date, market, generated_at=generated_at)
    except Exception as exc:  # noqa: BLE001
        logger.warning("AI review packet generation failed: %s", type(exc).__name__)
        return PacketWriteResult(status="failed", reason=type(exc).__name__)


def _completion_name(
    packet_id: str,
    policy_version: str,
    knowledge_sha256: str,
) -> str:
    safe_policy = re.sub(r"[^A-Za-z0-9_.-]+", "-", policy_version)
    return f"{packet_id}--{safe_policy}--{knowledge_sha256[:12]}.json"


def _read_json(path: Path) -> dict[str, object]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError("JSON document must be an object")
    return value


def claim_next_ai_review_packet(
    market: AIReviewMarket,
    *,
    owner: str | None = None,
    now: datetime | None = None,
    catchup_hours: int | None = None,
    lease_minutes: int | None = None,
) -> ClaimResult:
    ensure_ai_review_layout()
    current = (now or datetime.now(UTC)).astimezone(UTC)
    settings = get_settings()
    catchup = timedelta(
        hours=catchup_hours
        if catchup_hours is not None
        else settings.ai_review_shadow_catchup_hours
    )
    lease = timedelta(
        minutes=lease_minutes
        if lease_minutes is not None
        else settings.ai_review_claim_lease_minutes
    )
    candidates: dict[tuple[str, str, str], tuple[datetime, Path, dict[str, object]]] = {}
    for packet_path in _directory("inbox").glob("*.json"):
        try:
            packet = _read_json(packet_path)
            if packet.get("market") != market or packet.get("ready_for_ai") is not True:
                continue
            generated_at = datetime.fromisoformat(str(packet["generated_at"]))
            if generated_at.tzinfo is None:
                generated_at = generated_at.replace(tzinfo=UTC)
            if generated_at.astimezone(UTC) < current - catchup:
                continue
            packet_id = str(packet["packet_id"])
            policy = str(packet.get("analysis_policy_version") or ANALYSIS_POLICY_VERSION)
            knowledge = packet.get("knowledge")
            knowledge_sha = (
                str(knowledge.get("sha256") or "")
                if isinstance(knowledge, dict)
                else ""
            )
            if not knowledge_sha:
                continue
        except (KeyError, ValueError, json.JSONDecodeError):
            continue
        identity = (
            str(packet.get("market") or ""),
            str(packet.get("assessment_date") or ""),
            str(packet.get("source_monitor_run_id") or ""),
        )
        previous = candidates.get(identity)
        if previous is None or generated_at > previous[0]:
            candidates[identity] = (generated_at, packet_path, packet)
    ordered = sorted(
        candidates.values(),
        key=lambda item: (str(item[2].get("assessment_date") or ""), item[0]),
        reverse=True,
    )
    for _generated_at, packet_path, packet in ordered:
        packet_id = str(packet["packet_id"])
        policy = str(packet.get("analysis_policy_version") or ANALYSIS_POLICY_VERSION)
        knowledge = packet.get("knowledge")
        knowledge_sha = (
            str(knowledge.get("sha256") or "") if isinstance(knowledge, dict) else ""
        )
        output_name = _completion_name(packet_id, policy, knowledge_sha)
        final_path = _directory("outbox") / output_name
        claim_path = _directory("claims") / f"{packet_id}.json"
        with _packet_lock(packet_id):
            if final_path.exists():
                continue
            if claim_path.exists():
                try:
                    claim = _read_json(claim_path)
                    expires_at = datetime.fromisoformat(str(claim["expires_at"]))
                    if expires_at.tzinfo is None:
                        expires_at = expires_at.replace(tzinfo=UTC)
                    if expires_at.astimezone(UTC) > current:
                        continue
                except (KeyError, ValueError, json.JSONDecodeError):
                    pass
            claim_id = str(uuid.uuid4())
            temp_path = final_path.parent / f"{final_path.stem}--{claim_id}.json.tmp"
            claim = {
                "packet_id": packet_id,
                "claim_id": claim_id,
                "market": market,
                "analysis_policy_version": policy,
                "knowledge_sha256": knowledge_sha,
                "owner": owner or socket.gethostname(),
                "claimed_at": current.isoformat(),
                "expires_at": (current + lease).isoformat(),
                "lease_expires_at": (current + lease).isoformat(),
                "packet_path": str(packet_path),
                "temp_output_path": str(temp_path),
                "final_output_path": str(final_path),
            }
            _atomic_json(claim_path, claim)
        return ClaimResult(
            status="claimed",
            packet_id=packet_id,
            claim_id=claim_id,
            packet_path=str(packet_path),
            claim_path=str(claim_path),
            temp_output_path=str(temp_path),
            final_output_path=str(final_path),
        )
    return ClaimResult(status="no_pending_packet", reason="no_eligible_unclaimed_packet")


def _review_text(review: AIStockReview) -> str:
    return "\n".join(
        [
            *(item.text for item in review.interpretation),
            *(item.usage for item in review.numeric_claims),
            *review.unknowns,
            review.summary,
            review.holder_view,
            review.new_buyer_view,
            *review.next_checks,
        ]
    )


def _numeric_tokens(value: object) -> set[str]:
    text = json.dumps(value, ensure_ascii=False, default=str) if not isinstance(value, str) else value
    tokens: set[str] = set()
    for match in _NUMBER.finditer(text):
        raw = match.group(0).lstrip("+").rstrip("%").replace(",", "")
        try:
            tokens.add(f"{float(raw):.12g}")
        except ValueError:
            continue
    return tokens


def _provenance_tokens(text: str) -> set[str]:
    cleaned = re.sub(r"\b(?:19|20)\d{2}[-./]\d{1,2}[-./]\d{1,2}\b", "", text)
    cleaned = re.sub(r"\b(?:19|20)\d{2}\s*년\b", "", cleaned)
    cleaned = re.sub(r"\bQ[1-4]\b|\b[1-4]Q\b", "", cleaned, flags=re.IGNORECASE)
    cleaned = re.sub(r"\b[1-4]\s*분기\b", "", cleaned)
    cleaned = re.sub(r"\b(?:thesis\s*)?version\s*\d+\b", "", cleaned, flags=re.IGNORECASE)
    cleaned = re.sub(r"\b[1-3]\s*[~-]\s*[1-3]\s*개\b", "", cleaned)
    return _numeric_tokens(cleaned)


def _numbers_equal(expected: float, actual: float, unit: str) -> bool:
    if math.isclose(expected, actual, rel_tol=1e-12, abs_tol=1e-12):
        return True
    if unit == "pct":
        return any(math.isclose(round(expected, digits), actual) for digits in (1, 2, 4))
    return False


def _usage_unit_matches(unit: str, usage: str) -> bool:
    lowered = usage.lower()
    if unit == "pct":
        return "%" in usage or "percent" in lowered or "퍼센트" in usage
    if unit == "KRW":
        return any(marker in usage for marker in ("원", "억원", "조")) or "krw" in lowered
    if unit == "USD":
        return "$" in usage or "usd" in lowered or "달러" in usage
    if unit == "shares":
        return "주" in usage or "share" in lowered
    if unit == "x":
        return "배" in usage or "multiple" in lowered
    return True


def _semantic_markers(field_path: str) -> tuple[str, ...]:
    mappings = (
        ("operating_margin", ("영업이익률", "operating margin")),
        ("operating_income", ("영업이익", "operating income")),
        ("revenue", ("매출", "revenue")),
        ("current_price", ("현재가", "주가", "가격", "price")),
        ("contract_amount", ("계약금액", "수주금액", "contract amount", "order value")),
        ("share_ratio", ("주식", "지분", "share ratio")),
        ("market_cap_ratio", ("시가총액", "market cap")),
        ("forward_pe", ("fper", "forward pe", "선행 per")),
        ("trailing_pe", ("per", "trailing pe")),
        ("price_to_book", ("pbr", "price to book")),
        ("eps", ("eps", "주당순이익")),
        ("bvps", ("bvps", "주당순자산")),
    )
    lowered = field_path.lower()
    for marker, labels in mappings:
        if marker in lowered:
            return labels
    return ()


def _usage_semantic_matches(field_path: str, usage: str) -> bool:
    labels = _semantic_markers(field_path)
    lowered = usage.lower()
    return not labels or any(label in lowered for label in labels)


def _allowed_display_tokens(expected: float, unit: str) -> set[str]:
    tokens = _numeric_tokens(str(expected))
    if unit == "pct":
        for digits in (1, 2, 4):
            tokens.update(_numeric_tokens(str(round(expected, digits))))
    if unit == "KRW" and (compact := compact_krw_amount(expected)):
        tokens.update(_numeric_tokens(compact))
    return tokens


def _validate_numeric_claims(
    prefix: str,
    review: object,
    registry_value: object,
    rendered: str,
) -> list[str]:
    errors: list[str] = []
    registry = {
        (str(item.get("fact_id")), str(item.get("field_path"))): item
        for item in registry_value
        if isinstance(item, dict)
    } if isinstance(registry_value, list) else {}
    claims = getattr(review, "numeric_claims", [])
    claim_usage_tokens: set[str] = set()
    facts_used = set(getattr(review, "facts_used", []))
    for claim in claims:
        source = registry.get((claim.fact_id, claim.field_path))
        if source is None:
            errors.append(f"{prefix}:numeric_provenance_not_found:{claim.fact_id}:{claim.field_path}")
            continue
        expected = float(source["value"])
        expected_unit = str(source["unit"])
        if claim.fact_id not in facts_used:
            errors.append(f"{prefix}:numeric_fact_not_declared:{claim.fact_id}")
        if claim.unit != expected_unit:
            errors.append(f"{prefix}:numeric_unit_mismatch:{claim.fact_id}:{claim.field_path}")
        if not _numbers_equal(expected, claim.value, expected_unit):
            errors.append(f"{prefix}:numeric_value_mismatch:{claim.fact_id}:{claim.field_path}")
        if not _usage_unit_matches(expected_unit, claim.usage):
            errors.append(f"{prefix}:numeric_usage_unit_mismatch:{claim.fact_id}:{claim.field_path}")
        if not _usage_semantic_matches(claim.field_path, claim.usage):
            errors.append(f"{prefix}:numeric_usage_semantic_mismatch:{claim.fact_id}:{claim.field_path}")
        display_tokens = _provenance_tokens(claim.usage)
        if not display_tokens or not display_tokens.issubset(
            _allowed_display_tokens(expected, expected_unit)
        ):
            errors.append(
                f"{prefix}:numeric_usage_value_mismatch:{claim.fact_id}:{claim.field_path}"
            )
        claim_usage_tokens.update(display_tokens)
    unsupported = sorted(_provenance_tokens(rendered) - claim_usage_tokens)
    if unsupported:
        errors.append(f"{prefix}:numbers_without_provenance:{','.join(unsupported)}")
    return errors


def _validate_stock_review(
    review: AIStockReview,
    stock: dict[str, object],
) -> list[str]:
    errors: list[str] = []
    fact_catalog = stock.get("fact_catalog", [])
    valid_fact_ids = {
        str(item.get("fact_id"))
        for item in fact_catalog
        if isinstance(item, dict) and item.get("fact_id")
    }
    invalid_facts = sorted(set(review.facts_used) - valid_fact_ids)
    if invalid_facts:
        errors.append(f"{review.ticker}:unknown_fact_ids:{','.join(invalid_facts)}")
    rendered = _review_text(review)
    if _INTERNAL_TEXT.search(rendered):
        errors.append(f"{review.ticker}:forbidden_internal_metadata")
    interpretation_facts = {
        fact_id for item in review.interpretation for fact_id in item.fact_ids
    }
    unknown_interpretation_facts = sorted(interpretation_facts - valid_fact_ids)
    if unknown_interpretation_facts:
        errors.append(
            f"{review.ticker}:interpretation_unknown_fact_ids:"
            + ",".join(unknown_interpretation_facts)
        )
    routing = stock.get("knowledge_routing")
    allowed_frameworks = {
        str(item)
        for item in routing.get("required_frameworks", [])
    } if isinstance(routing, dict) else set()
    invalid_frameworks = sorted(set(review.frameworks_used) - allowed_frameworks)
    if invalid_frameworks:
        errors.append(
            f"{review.ticker}:framework_not_allowed:{','.join(invalid_frameworks)}"
        )
    if isinstance(routing, dict):
        industry_key = str(routing.get("industry_key") or "general")
        industry_framework = _INDUSTRY_FRAMEWORKS.get(industry_key)
        if industry_framework and industry_framework not in review.frameworks_used:
            errors.append(f"{review.ticker}:industry_framework_missing:{industry_framework}")
    errors.extend(
        _validate_numeric_claims(
            review.ticker,
            review,
            stock.get("numeric_registry"),
            rendered,
        )
    )
    valuation = stock.get("valuation", {})
    if isinstance(valuation, dict):
        forward_source = str(valuation.get("forward_pe_source") or "")
        if forward_source == "modeled_forward" and re.search(
            r"(?:시장|애널리스트)\s*(?:컨센서스|예상)\s*EPS", rendered
        ):
            errors.append(f"{review.ticker}:modeled_forward_called_consensus")
        if str(valuation.get("historical_comparability") or "") in _INVALID_HISTORY and re.search(
            r"(?:역사적|과거)\s*(?:백분위|배수)", rendered
        ):
            errors.append(f"{review.ticker}:invalid_historical_comparison_used")
    return errors


def _current_thesis_version(session: Session, ticker: str) -> int | None:
    item = session.exec(
        select(WatchlistItem).where(WatchlistItem.ticker == ticker)
    ).first()
    if item is None:
        return None
    thesis = session.exec(
        select(InvestmentThesis)
        .where(InvestmentThesis.ticker == ticker)
        .order_by(InvestmentThesis.version.desc())
    ).first()
    return thesis.version if thesis is not None else None


def validate_ai_review_output(
    session: Session,
    packet: dict[str, object],
    output_value: object,
) -> tuple[AIDailyReviewOutput | None, list[str]]:
    try:
        output = AIDailyReviewOutput.model_validate(output_value)
    except ValidationError as exc:
        return None, [f"schema:{item['loc']}:{item['type']}" for item in exc.errors()]
    errors: list[str] = []
    for key in ("packet_id", "market", "assessment_date", "analysis_policy_version"):
        if getattr(output, key) != packet.get(key):
            errors.append(f"identity_mismatch:{key}")
    knowledge = packet.get("knowledge")
    if not isinstance(knowledge, dict):
        errors.append("identity_mismatch:knowledge")
    else:
        if output.knowledge_version != knowledge.get("version"):
            errors.append("identity_mismatch:knowledge_version")
        if output.knowledge_sha256 != knowledge.get("sha256"):
            errors.append("identity_mismatch:knowledge_sha256")
    if output.schema_version != OUTPUT_SCHEMA_VERSION:
        errors.append("identity_mismatch:schema_version")
    stocks = {
        str(item.get("ticker")): item
        for item in packet.get("stocks", [])
        if isinstance(item, dict) and item.get("ticker")
    }
    reviews = {item.ticker: item for item in output.stock_reviews}
    if set(reviews) != set(stocks) or len(reviews) != len(output.stock_reviews):
        errors.append("ticker_set_mismatch")
    for ticker, review in reviews.items():
        stock = stocks.get(ticker)
        if stock is None:
            continue
        if review.thesis_version != stock.get("thesis_version"):
            errors.append(f"{ticker}:thesis_version_mismatch")
        if _current_thesis_version(session, ticker) != review.thesis_version:
            errors.append(f"{ticker}:not_currently_monitored_at_version")
        errors.extend(_validate_stock_review(review, stock))
    market_fact_ids = {
        str(item.get("fact_id"))
        for item in packet.get("market_context", {}).get("fact_catalog", [])
        if isinstance(item, dict) and item.get("fact_id")
    } if isinstance(packet.get("market_context"), dict) else set()
    if set(output.market_review.facts_used) - market_fact_ids:
        errors.append("market_review:unknown_fact_ids")
    market_interpretation_facts = {
        fact_id
        for item in output.market_review.interpretation
        for fact_id in item.fact_ids
    }
    if market_interpretation_facts - market_fact_ids:
        errors.append("market_review:interpretation_unknown_fact_ids")
    market_text = "\n".join(
        [
            *(item.text for item in output.market_review.interpretation),
            *(item.usage for item in output.market_review.numeric_claims),
            *output.market_review.unknowns,
            output.market_review.summary,
        ]
    )
    if _INTERNAL_TEXT.search(market_text):
        errors.append("market_review:forbidden_internal_metadata")
    market_context = packet.get("market_context", {})
    market_routing = (
        market_context.get("knowledge_routing")
        if isinstance(market_context, dict)
        else None
    )
    allowed_market_frameworks = {
        str(item)
        for item in market_routing.get("required_frameworks", [])
    } if isinstance(market_routing, dict) else set()
    invalid_market_frameworks = sorted(
        set(output.market_review.frameworks_used) - allowed_market_frameworks
    )
    if invalid_market_frameworks:
        errors.append(
            "market_review:framework_not_allowed:" + ",".join(invalid_market_frameworks)
        )
    errors.extend(
        _validate_numeric_claims(
            "market_review",
            output.market_review,
            market_context.get("numeric_registry")
            if isinstance(market_context, dict)
            else None,
            market_text,
        )
    )
    return output, list(dict.fromkeys(errors))


def _comparison_payload(
    packet: dict[str, object],
    output: AIDailyReviewOutput,
    validated_at: datetime,
) -> dict[str, object]:
    deterministic = {
        str(item["ticker"]): item.get("deterministic_assessment", {})
        for item in packet.get("stocks", [])
        if isinstance(item, dict) and item.get("ticker")
    }
    comparisons = []
    stock_packets = {
        str(item["ticker"]): item
        for item in packet.get("stocks", [])
        if isinstance(item, dict) and item.get("ticker")
    }
    for review in output.stock_reviews:
        base = deterministic.get(review.ticker, {})
        base_status = (
            str(base.get("business_thesis_change") or "unknown")
            if isinstance(base, dict)
            else "unknown"
        )
        warnings = base.get("confirmed_warnings", []) if isinstance(base, dict) else []
        guardrail_conflicts = []
        if warnings and review.ai_thesis_assessment == "no_material_change":
            guardrail_conflicts.append("deterministic_warning_requires_human_review")
        if any(not item.fact_ids for item in review.interpretation):
            guardrail_conflicts.append("interpretation_without_fact_reference")
        stock_packet = stock_packets.get(review.ticker, {})
        guardrail_conflicts.extend(_semantic_guardrail_flags(review, stock_packet))
        comparisons.append(
            {
                "ticker": review.ticker,
                "thesis_version": review.thesis_version,
                "deterministic_status": base_status,
                "ai_proposed_status": review.ai_thesis_assessment,
                "status_match": base_status == review.ai_thesis_assessment,
                "deterministic_warnings": warnings,
                "guardrail_conflicts": guardrail_conflicts,
                "frameworks_used": review.frameworks_used,
                "facts_used": review.facts_used,
                "numeric_claims": [item.model_dump() for item in review.numeric_claims],
                "unknowns": review.unknowns,
                "ai_summary": review.summary,
            }
        )
    return {
        "packet_id": output.packet_id,
        "analysis_policy_version": output.analysis_policy_version,
        "knowledge_version": output.knowledge_version,
        "knowledge_sha256": output.knowledge_sha256,
        "mode": get_settings().ai_review_mode,
        "validated_at": validated_at.isoformat(),
        "official_assessment_mutated": False,
        "telegram_mutated": False,
        "comparisons": comparisons,
    }


def _semantic_guardrail_flags(
    review: AIStockReview,
    stock: dict[str, object],
) -> list[str]:
    assertions = "\n".join(
        [
            *(item.text for item in review.interpretation),
            review.summary,
            review.holder_view,
            review.new_buyer_view,
        ]
    ).lower()
    facts = json.dumps(stock.get("fact_catalog", []), ensure_ascii=False).lower()
    change = r"(?:improv|increas|decreas|rose|fell|개선|증가|감소|상승|하락|확대|축소)"
    metrics = {
        "free_cash_flow": (r"(?:free cash flow|\bfcf\b|잉여현금흐름)", ("free_cash_flow", "fcf")),
        "inventory": (r"(?:inventory|재고)", ("inventory", "재고")),
        "roic": (r"(?:\broic\b|투하자본수익률)", ("roic",)),
        "nrr": (r"(?:\bnrr\b|net revenue retention)", ("nrr", "net_revenue_retention")),
        "arr": (r"(?:\barr\b|annual recurring revenue)", ("arr", "annual_recurring_revenue")),
        "project_margin": (r"(?:project margin|contract margin|수주 마진|프로젝트 마진)", ("project_margin", "contract_margin")),
    }
    flags: list[str] = []
    for name, (metric_pattern, fact_markers) in metrics.items():
        if (
            re.search(metric_pattern, assertions)
            and re.search(change, assertions)
            and not any(marker in facts for marker in fact_markers)
        ):
            flags.append(f"unsupported_claim:{name}")
    routing = stock.get("knowledge_routing")
    industry_key = (
        str(routing.get("industry_key") or "general")
        if isinstance(routing, dict)
        else "general"
    )
    if industry_key == "memory" and re.search(
        r"(?:low|낮은)\s*(?:current\s*)?per.*(?:undervalu|저평가)",
        assertions,
    ):
        flags.append("memory_low_per_only_conclusion")
    fact_types = {
        str(item.get("fact_type") or "")
        for item in stock.get("fact_catalog", [])
        if isinstance(item, dict) and item.get("fact_id") in review.facts_used
    }
    if review.ai_thesis_assessment in {"strengthened", "weakened"} and fact_types and fact_types <= {
        "price",
        "positioning",
    }:
        flags.append("price_or_positioning_only_thesis_change")
    return flags


def finalize_ai_review_output(
    session: Session,
    packet_id: str,
    *,
    claim_id: str,
    policy_version: str = ANALYSIS_POLICY_VERSION,
    now: datetime | None = None,
) -> OutputValidationResult:
    ensure_ai_review_layout()
    packet_path = _directory("inbox") / f"{packet_id}.json"
    if not packet_path.exists():
        return OutputValidationResult(
            status="not_ready",
            packet_id=packet_id,
            errors=("packet_missing",),
        )
    try:
        packet = _read_json(packet_path)
        knowledge = packet.get("knowledge")
        knowledge_sha = (
            str(knowledge.get("sha256") or "") if isinstance(knowledge, dict) else ""
        )
    except (ValueError, json.JSONDecodeError) as exc:
        return OutputValidationResult(
            status="rejected", packet_id=packet_id, errors=(type(exc).__name__,)
        )
    output_name = _completion_name(packet_id, policy_version, knowledge_sha)
    final_path = _directory("outbox") / output_name
    temp_path = final_path.parent / f"{final_path.stem}--{claim_id}.json.tmp"
    claim_path = _directory("claims") / f"{packet_id}.json"
    with _packet_lock(packet_id):
        if final_path.exists():
            try:
                completed_claim = str(_read_json(final_path).get("claim_id") or "")
            except (ValueError, json.JSONDecodeError):
                completed_claim = ""
            if completed_claim == claim_id:
                return OutputValidationResult(
                    status="already_completed",
                    packet_id=packet_id,
                    output_path=str(final_path),
                )
            if temp_path.exists():
                rejected = _directory("rejected") / (
                    f"{output_name}.{claim_id}.stale_claim_output"
                )
                os.replace(temp_path, rejected)
            return OutputValidationResult(
                status="rejected",
                packet_id=packet_id,
                output_path=str(final_path),
                errors=("stale_claim_output",),
            )
        try:
            active_claim = _read_json(claim_path)
        except (FileNotFoundError, ValueError, json.JSONDecodeError):
            active_claim = {}
        if str(active_claim.get("claim_id") or "") != claim_id:
            if temp_path.exists():
                rejected = _directory("rejected") / (
                    f"{output_name}.{claim_id}.stale_claim_output"
                )
                os.replace(temp_path, rejected)
            return OutputValidationResult(
                status="rejected",
                packet_id=packet_id,
                errors=("stale_claim_output",),
            )
        active_temp = Path(str(active_claim.get("temp_output_path") or temp_path))
        if active_temp != temp_path or not temp_path.exists():
            return OutputValidationResult(
                status="not_ready",
                packet_id=packet_id,
                errors=("claim_temp_output_missing",),
            )
    try:
        candidate = _read_json(temp_path)
    except (ValueError, json.JSONDecodeError) as exc:
        return OutputValidationResult(
            status="rejected", packet_id=packet_id, errors=(type(exc).__name__,)
        )
    if candidate.get("claim_id") != claim_id:
        output = None
        errors = ["stale_claim_output"]
    else:
        output, errors = validate_ai_review_output(session, packet, candidate)
    if output is None or errors:
        rejected = _directory("rejected") / f"{output_name}.{int(datetime.now(UTC).timestamp())}"
        os.replace(temp_path, rejected)
        return OutputValidationResult(
            status="rejected", packet_id=packet_id, errors=tuple(errors)
        )
    validated_at = (now or datetime.now(UTC)).astimezone(UTC)
    history_dir = _directory("history") / f"{validated_at:%Y}" / f"{validated_at:%m}"
    history_dir.mkdir(parents=True, exist_ok=True)
    history_output = history_dir / output_name
    comparison_path = history_dir / output_name.replace(".json", ".comparison.json")
    with _packet_lock(packet_id):
        if final_path.exists():
            try:
                completed_claim = str(_read_json(final_path).get("claim_id") or "")
            except (ValueError, json.JSONDecodeError):
                completed_claim = ""
            if completed_claim == claim_id:
                return OutputValidationResult(
                    status="already_completed",
                    packet_id=packet_id,
                    output_path=str(final_path),
                )
            if temp_path.exists():
                rejected = _directory("rejected") / (
                    f"{output_name}.{claim_id}.stale_claim_output"
                )
                os.replace(temp_path, rejected)
            return OutputValidationResult(
                status="rejected",
                packet_id=packet_id,
                output_path=str(final_path),
                errors=("stale_claim_output",),
            )
        try:
            final_claim = _read_json(claim_path)
        except (FileNotFoundError, ValueError, json.JSONDecodeError):
            final_claim = {}
        claim_identity_matches = all(
            (
                str(final_claim.get("claim_id") or "") == claim_id,
                str(final_claim.get("packet_id") or "") == packet_id,
                str(final_claim.get("analysis_policy_version") or "") == policy_version,
                str(final_claim.get("knowledge_sha256") or "") == knowledge_sha,
                Path(str(final_claim.get("temp_output_path") or temp_path)) == temp_path,
                Path(str(final_claim.get("final_output_path") or final_path)) == final_path,
                str(candidate.get("packet_id") or "") == packet_id,
                str(candidate.get("claim_id") or "") == claim_id,
                str(candidate.get("analysis_policy_version") or "") == policy_version,
                str(candidate.get("knowledge_sha256") or "") == knowledge_sha,
            )
        )
        if not claim_identity_matches:
            rejected = _directory("rejected") / (
                f"{output_name}.{claim_id}.stale_claim_output"
            )
            if temp_path.exists():
                os.replace(temp_path, rejected)
            return OutputValidationResult(
                status="rejected",
                packet_id=packet_id,
                errors=("stale_claim_output",),
            )
        os.replace(temp_path, final_path)
        _atomic_json(history_output, candidate)
        _atomic_json(comparison_path, _comparison_payload(packet, output, validated_at))
        current_claim = _read_json(claim_path)
        if str(current_claim.get("claim_id") or "") == claim_id:
            claim_path.unlink(missing_ok=True)
    return OutputValidationResult(
        status="completed",
        packet_id=packet_id,
        output_path=str(final_path),
        comparison_path=str(comparison_path),
    )


def ai_review_health(
    review_date: date,
    market: AIReviewMarket,
) -> dict[str, object]:
    ensure_ai_review_layout()
    packets = []
    for path in sorted(_directory("inbox").glob(f"{review_date.isoformat()}-{market}-*.json")):
        packet = _read_json(path)
        packet_id = str(packet.get("packet_id") or "")
        policy = str(packet.get("analysis_policy_version") or ANALYSIS_POLICY_VERSION)
        knowledge = packet.get("knowledge")
        knowledge_sha = (
            str(knowledge.get("sha256") or "") if isinstance(knowledge, dict) else ""
        )
        final = _directory("outbox") / _completion_name(
            packet_id, policy, knowledge_sha
        )
        claim = _directory("claims") / f"{packet_id}.json"
        packets.append(
            {
                "packet_id": packet_id,
                "generated": True,
                "claimed": claim.exists(),
                "completed": final.exists(),
                "validation_passed": final.exists(),
            }
        )
    return {"assessment_date": review_date.isoformat(), "market": market, "packets": packets}
