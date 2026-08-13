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
)
from app.services.company_profile_service import (
    company_profile_coverage,
    read_profile_provenance,
)
from app.services.daily_digest import build_daily_digest
from app.services.market_session import market_scope_for_security
from app.services.numeric_semantic_registry import (
    NUMERIC_SEMANTICS,
    build_numeric_registry,
    numeric_registry_coverage,
    usage_direction_matches,
    usage_matches_semantic,
)


logger = logging.getLogger(__name__)

PACKET_SCHEMA_VERSION = "1"
OUTPUT_SCHEMA_VERSION = "3"
ANALYSIS_POLICY_VERSION = "daily-review-v3.3"
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
_STRUCTURAL_NUMBER_PATTERNS = (
    r"\b(?:19|20)\d{2}[-./]\d{1,2}[-./]\d{1,2}\b",
    r"\b(?:19|20)\d{2}\s*년(?:\s*[1-4]\s*분기)?",
    r"\bQ[1-4]\b|\b[1-4]Q\b",
    r"\b[1-3]\s*[~-]\s*[1-3]\s*개\b",
    r"\b(?:1|5|20|60)\s*일(?:간)?\b",
    r"\b(?:3|5|6|12|24|54)\s*개월\b",
    r"(?:핵심\s*(?:요인|근거)|다음\s*확인|확인\s*항목)\s*[1-3]\s*(?:가지|개)",
    r"[1-3]\s*(?:가지|개)\s*(?:핵심\s*(?:요인|근거)|다음\s*확인|확인\s*항목)",
)
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
_INDUSTRY_PATTERNS = (
    ("memory", (r"\bmemory\b", r"\bdram\b", r"\bnand\b", r"메모리")),
    (
        "holding_company",
        (r"\bholding compan(?:y|ies)\b", r"\bholding\b", r"지주회사", r"지주"),
    ),
    ("insurance", (r"\breinsurance\b", r"\binsurance\b", r"재보험", r"보험")),
    ("bank", (r"\bbanking\b", r"\bbank\b", r"은행")),
    ("epc", (r"\bepc\b", r"\bconstruction\b", r"건설", r"플랜트")),
    (
        "saas",
        (
            r"\bsaas\b",
            r"\bannual recurring revenue\b",
            r"\bnet revenue retention\b",
            r"\bsubscription software\b",
            r"구독형 소프트웨어",
        ),
    ),
    ("pre_profit", (r"\brobotaxi\b", r"\bpre[- ]profit\b", r"로보택시")),
    (
        "biotech",
        (
            r"\bbiotech(?:nology)?\b",
            r"\bbiopharma(?:ceutical)?\b",
            r"\bpharmaceuticals?\b",
            r"바이오",
            r"신약",
        ),
    ),
    ("automotive", (r"\bautomotive\b", r"\bautomobile\b", r"자동차", r"완성차")),
    ("shipping", (r"\bshipping\b", r"\btransport(?:ation)?\b", r"해운", r"운송")),
    ("consumer", (r"\bconsumer(?: goods)?\b", r"소비재")),
    (
        "cloud",
        (r"\bcloud computing\b", r"\bpublic cloud\b", r"클라우드 서비스"),
    ),
    ("semiconductor", (r"\bsemiconductor(?:s)?\b", r"반도체")),
)
_THEMATIC_FRAMEWORKS = (
    (
        "hyperscaler_capex_transmission",
        (
            r"\bhyperscaler\b",
            r"\bcloud\s+capex\b",
            r"\bdata[- ]?cent(?:er|re)\b",
            r"하이퍼스케일러",
            r"데이터.?센터",
        ),
    ),
    (
        "fomc_interpretation",
        (r"\bfomc\b", r"\bdot plot\b", r"\bfed(?:eral reserve)?\b", r"연준"),
    ),
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


def chart_knowledge_manifest() -> dict[str, str | int]:
    reference_root = _skill_root() / "references"
    manifest = _read_json(reference_root / "chart-knowledge-manifest.json")
    mirror = reference_root / "stock-chart-value-analysis-knowledge-v1.md"
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
        raise ValueError("Chart Knowledge mirror checksum mismatch")
    return {
        "name": str(manifest["knowledge_name"]),
        "version": str(manifest["knowledge_version"]),
        "sha256": expected,
        "source": str(manifest["source"]),
        "line_count": line_count,
        "byte_count": byte_count,
    }


def _industry_candidates(value: str | None) -> list[str]:
    text = str(value or "").lower()
    return [
        key
        for key, patterns in _INDUSTRY_PATTERNS
        if any(re.search(pattern, text) for pattern in patterns)
    ]


def _dominant_industry_candidate(value: str | None, candidates: list[str]) -> str | None:
    if not candidates:
        return None
    if "holding_company" in candidates:
        return "holding_company"
    if "memory" in candidates and set(candidates).issubset({"memory", "semiconductor"}):
        return "memory"
    if len(candidates) == 1:
        return candidates[0]
    text = str(value or "").lower()
    shares: dict[str, float] = {}
    for candidate, patterns in _INDUSTRY_PATTERNS:
        if candidate not in candidates:
            continue
        for pattern in patterns:
            match = re.search(pattern, text)
            if match is None:
                continue
            window = text[match.start() : match.end() + 40]
            percentage = re.search(r"(\d+(?:\.\d+)?)\s*%", window)
            if percentage:
                shares[candidate] = float(percentage.group(1))
                break
    if not shares:
        return None
    highest = max(shares.values())
    winners = [key for key, value_share in shares.items() if value_share == highest]
    return winners[0] if len(winners) == 1 else None


def _thematic_frameworks(value: str) -> list[str]:
    text = value.lower()
    return [
        framework
        for framework, patterns in _THEMATIC_FRAMEWORKS
        if any(re.search(pattern, text) for pattern in patterns)
    ]


def _chart_knowledge_routing(chart: dict[str, object]) -> dict[str, object]:
    usable = bool(chart.get("available")) and str(chart.get("quality")) in {
        "fresh",
        "provisional",
    }
    required = [
        "chart_principles",
        "chart_holder_new_buyer",
        "chart_multi_timeframe",
        "chart_supply",
        "chart_data_quality",
    ]
    timeframes = chart.get("timeframes")
    values = list(timeframes.values()) if isinstance(timeframes, dict) else []
    if any(isinstance(item, dict) and item.get("bollinger_upper") for item in values):
        required.append("chart_bollinger")
    if any(
        isinstance(item, dict)
        and isinstance(item.get("candle"), dict)
        and item.get("candle")
        for item in values
    ):
        required.append("chart_candle_volume")
    if any(isinstance(item, dict) and item.get("rsi_14") is not None for item in values):
        required.append("chart_rsi")
    if any(isinstance(item, dict) and item.get("macd") is not None for item in values):
        required.append("chart_macd")
    transition = chart.get("price_transition")
    if isinstance(transition, dict) and transition.get("threshold_event") != "baseline":
        required.append("chart_threshold_transition")
    return {
        "available": usable,
        "quality": str(chart.get("quality") or "unavailable"),
        "required_frameworks": list(dict.fromkeys(required)) if usable else [],
        "unavailable_fields": chart.get("unavailable_fields", []),
    }


def _has_explicit_memory_subtype(value: str | None) -> bool:
    text = str(value or "").strip().lower()
    if re.search(r"\b(?:dram|nand|hbm)\b", text) or re.search(
        r"(?:디램|낸드|고대역폭.?메모리)", text
    ):
        return True
    return bool(
        re.fullmatch(
            r"(?:memory|메모리)(?:\s+(?:chip|chips|device|devices|"
            r"semiconductor|semiconductors|반도체))?",
            text,
        )
    )


def investment_framework_routing(
    industry: str | None,
    business_model: str | None,
    thesis_text: str,
    *,
    normalized_industry: str | None = None,
    sector: str | None = None,
    revenue_sources: str | None = None,
    has_earnings: bool,
    preliminary_earnings: bool,
    has_price_context: bool,
    has_adr_basis_risk: bool,
    profile_quality: str | None = None,
) -> dict[str, object]:
    structured_sources = (
        ("structured_industry", "company.industry", industry, "high"),
        ("structured_sector", "company.sector", sector, "high"),
        (
            "structured_business_model",
            "company.business_units",
            business_model,
            "medium",
        ),
        (
            "structured_revenue_sources",
            "company.revenue_sources",
            revenue_sources,
            "low",
        ),
    )
    normalized_key = str(normalized_industry or "").strip()
    normalized_valid = normalized_key in _INDUSTRY_FRAMEWORKS
    industry_key = normalized_key if normalized_valid else "general"
    source = "normalized_profile_taxonomy" if normalized_valid else "unclassified"
    confidence = "high" if normalized_valid else "low"
    evidence: list[str] = (
        [f"company.profile.taxonomy_key={normalized_key}"]
        if normalized_valid
        else []
    )
    selected_index = -1 if normalized_valid else len(structured_sources)
    candidates_by_source: list[tuple[str, str, str | None, str, list[str]]] = []
    for index, (candidate_source, field, value, candidate_confidence) in enumerate(
        structured_sources
    ):
        candidates = _industry_candidates(value)
        candidates_by_source.append(
            (candidate_source, field, value, candidate_confidence, candidates)
        )
        preferred = _dominant_industry_candidate(value, candidates)
        if industry_key == "general" and preferred:
            industry_key = preferred
            source = candidate_source
            confidence = candidate_confidence
            selected_index = index
            evidence.append(f"{field}={value}")

    business_candidates = candidates_by_source[2][4]
    if (
        industry_key == "semiconductor"
        and "memory" in business_candidates
        and _has_explicit_memory_subtype(business_model)
    ):
        industry_key = "memory"
        source = "structured_business_model_subtype"
        confidence = "high"
        evidence.append(f"company.business_units={business_model}")

    if profile_quality in {"ambiguous", "unavailable"}:
        industry_key = "general"
        source = f"profile_{profile_quality}"
        confidence = "low"
        evidence = []
        selected_index = len(structured_sources)
    elif profile_quality == "partial" and confidence == "high":
        confidence = "medium"

    secondary: list[str] = []
    for index, (_candidate_source, field, value, _candidate_confidence, candidates) in enumerate(
        candidates_by_source
    ):
        if index <= selected_index and not (
            source == "structured_business_model_subtype" and index == 2
        ):
            continue
        for candidate in candidates:
            if candidate == industry_key:
                continue
            if framework := _INDUSTRY_FRAMEWORKS.get(candidate):
                secondary.append(framework)
                evidence.append(f"{field}={value}")

    secondary.extend(_thematic_frameworks(thesis_text))
    secondary = list(dict.fromkeys(secondary))
    primary_framework = _INDUSTRY_FRAMEWORKS.get(industry_key)
    required = list(_CORE_FRAMEWORKS)
    if primary_framework:
        required.append(primary_framework)
    required.extend(secondary)
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
        "industry_routing": {
            "primary_framework": primary_framework,
            "secondary_frameworks": secondary,
            "source": source,
            "confidence": confidence,
            "evidence": list(dict.fromkeys(evidence)),
        },
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


def _dict(value: object) -> dict[str, object]:
    if isinstance(value, dict):
        return value
    if not isinstance(value, str):
        return {}
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


def _number(value: object) -> float | None:
    if isinstance(value, (int, float)) and not isinstance(value, bool):
        number = float(value)
        return number if math.isfinite(number) else None
    return None


def _distance_pct(current: float | None, reference: float | None) -> float | None:
    if current is None or reference in {None, 0}:
        return None
    return round((current / reference - 1) * 100, 4)


def _price_transition(
    current: dict[str, object],
    previous: dict[str, object],
) -> dict[str, object]:
    current_state = str(current.get("price_state") or "unavailable")
    previous_state = str(previous.get("price_state") or "baseline")
    event = "no_transition"
    if not previous:
        event = "baseline"
    elif current_state == "above_confirmation" and previous_state != current_state:
        event = "confirmation_crossed"
    elif previous_state == "above_confirmation" and current_state != previous_state:
        event = "confirmation_failed"
    elif current_state == "inside_support" and previous_state != current_state:
        event = "support_entered"
    elif previous_state in {"inside_support", "below_support"} and current_state in {
        "between_confirmation_and_support",
        "above_confirmation",
    }:
        event = "support_reclaimed"
    elif current_state == "below_support" and previous_state != current_state:
        event = "support_broken"
    elif current_state == "below_warning" and previous_state != current_state:
        event = "warning_crossed"
    elif current_state == "below_invalidation" and previous_state != current_state:
        event = "invalidation_crossed"
    retest_status = "not_applicable"
    if current_state == "above_confirmation":
        retest_status = (
            "holding_above_confirmation"
            if previous_state == "above_confirmation"
            else "awaiting_retest"
        )
    elif event == "confirmation_failed":
        retest_status = "failed_retest"
    return {
        "previous_state": previous_state,
        "current_state": current_state,
        "threshold_event": event,
        "crossed_at": (
            current.get("price_as_of")
            if event not in {"baseline", "no_transition"}
            else None
        ),
        "retest_status": retest_status,
    }


def _chart_payload(
    assessment: ThesisAssessment,
    thesis: InvestmentThesis,
    previous: ThesisAssessment | None,
) -> dict[str, object]:
    price_context = _dict(assessment.price_context)
    chart = _public_value(_dict(price_context.get("chart")))
    decision = _dict(price_context.get("decision"))
    previous_decision = (
        _dict(_dict(previous.price_context).get("decision"))
        if previous is not None
        else {}
    )
    rules = _dict(thesis.price_rules)
    current_price = _number(decision.get("current_price"))
    stored_rules = {
        key: value
        for key in (
            "currency",
            "basis",
            "confirmation_price",
            "support_zone_low",
            "support_zone_high",
            "warning_price",
            "invalidation_price",
        )
        if (value := rules.get(key)) is not None
    }
    distances = {
        key: distance
        for field, key in (
            ("confirmation_price", "confirmation_distance_pct"),
            ("support_zone_low", "support_low_distance_pct"),
            ("support_zone_high", "support_high_distance_pct"),
            ("warning_price", "warning_distance_pct"),
            ("invalidation_price", "invalidation_distance_pct"),
        )
        if (distance := _distance_pct(current_price, _number(rules.get(field))))
        is not None
    }
    transition = _price_transition(decision, previous_decision)
    daily = _dict(_dict(chart.get("timeframes")).get("daily"))
    volume_ratio = _number(daily.get("volume_ratio_20"))
    transition["volume_confirmation"] = (
        "above_20d_average"
        if volume_ratio is not None and volume_ratio >= 1
        else "below_20d_average"
        if volume_ratio is not None
        else "unavailable"
    )
    supply = _dict(price_context.get("supply"))
    transition["supply_confirmation"] = str(
        supply.get("primary_signal") or "unavailable"
    )
    return {
        **chart,
        "stored_price_rules": stored_rules,
        "price_transition": transition,
        "distance_from_stored_rules_pct": distances,
        "chart_unknowns": list(
            dict.fromkeys(
                [
                    *(
                        chart.get("unavailable_fields", [])
                        if isinstance(chart.get("unavailable_fields"), list)
                        else []
                    ),
                    *(
                        chart.get("warnings", [])
                        if isinstance(chart.get("warnings"), list)
                        else []
                    ),
                ]
            )
        ),
    }


def _chart_facts(chart: dict[str, object], currency: str) -> list[dict[str, object]]:
    facts: list[dict[str, object]] = []
    timeframes = chart.get("timeframes")
    chart_usable = bool(chart.get("available")) and str(chart.get("quality")) in {
        "fresh",
        "provisional",
    }
    if chart_usable and isinstance(timeframes, dict):
        for timeframe in ("daily", "weekly", "monthly"):
            value = timeframes.get(timeframe)
            if not isinstance(value, dict) or value.get("quality") in {
                "stale",
                "unavailable",
            }:
                continue
            fields = {
                key: item
                for key, item in value.items()
                if key not in {"timeframe", "as_of_date", "quality", "price_basis"}
                and item not in ({}, [], None)
            }
            fields.update(
                {
                    "currency": currency,
                    "timeframe": timeframe,
                    "quality": value.get("quality"),
                    "price_basis": value.get("price_basis"),
                }
            )
            facts.append(
                {
                    "fact_id": f"chart:{timeframe}",
                    "fact_type": "chart_timeframe",
                    "as_of_date": str(value.get("as_of_date") or ""),
                    "source": str(chart.get("source") or "ohlcv_analyst"),
                    "fields": fields,
                }
            )
    rules = chart.get("stored_price_rules")
    distances = chart.get("distance_from_stored_rules_pct")
    if isinstance(rules, dict) and rules:
        fields = {**rules}
        if isinstance(distances, dict):
            fields["distance_pct"] = distances
        fields["currency"] = currency
        facts.append(
            {
                "fact_id": "chart:stored_price_rules",
                "fact_type": "chart_price_rules",
                "as_of_date": str(chart.get("as_of_date") or ""),
                "source": "investment_thesis",
                "fields": fields,
            }
        )
    transition = chart.get("price_transition")
    if isinstance(transition, dict) and transition:
        facts.append(
            {
                "fact_id": "chart:price_transition",
                "fact_type": "chart_transition",
                "as_of_date": str(chart.get("as_of_date") or ""),
                "source": "deterministic_price_state",
                "fields": transition,
            }
        )
    return facts


def _fact_catalog(
    assessment: ThesisAssessment,
    evidence: list[dict[str, object]],
    valuation: dict[str, object],
    price: dict[str, object],
    chart: dict[str, object],
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
    facts.extend(_chart_facts(chart, str(price.get("price", {}).get("currency") or currency)))
    snapshot = _dict(assessment.thesis_snapshot)
    for item in snapshot.get("capital_action_materiality", []):
        if isinstance(item, dict) and (fact := canonical_capital_action_fact(item)):
            facts.append(fact)
    return facts


def _numeric_registry(facts: list[dict[str, object]]) -> list[dict[str, object]]:
    return build_numeric_registry(facts)


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
    profile_provenance = read_profile_provenance(
        assessment.ticker,
        get_settings().data_dir,
    )
    evidence = _material_evidence(assessment)
    valuation = _valuation_payload(assessment)
    price = _price_payload(assessment)
    previous = _previous_assessment(session, assessment)
    chart = _chart_payload(assessment, thesis, previous)
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
    sector = _clean_text(company.sector) if company is not None else None
    business_model = _clean_text(company.business_units) if company is not None else None
    revenue_sources = _clean_text(company.revenue_sources) if company is not None else None
    routing = investment_framework_routing(
        industry,
        business_model,
        thesis_text,
        normalized_industry=str(
            (profile_provenance or {}).get("taxonomy_key") or ""
        )
        or None,
        sector=sector,
        revenue_sources=revenue_sources,
        has_earnings=valuation.get("latest_revenue") is not None,
        preliminary_earnings=bool(valuation.get("earnings_context_is_preliminary")),
        has_price_context=bool(price.get("price")),
        has_adr_basis_risk="adr" in thesis_text.lower()
        or "adr" in json.dumps(valuation, ensure_ascii=False).lower(),
        profile_quality=str((profile_provenance or {}).get("quality") or "") or None,
    )
    chart_routing = _chart_knowledge_routing(chart)
    routing["required_frameworks"] = list(
        dict.fromkeys(
            [
                *routing.get("required_frameworks", []),
                *chart_routing["required_frameworks"],
            ]
        )
    )
    stock = {
        "ticker": assessment.ticker,
        "company_name": item.company_name,
        "industry": industry,
        "sector": sector,
        "business_model": business_model,
        "revenue_sources": revenue_sources,
        "company_profile": {
            key: value
            for key in (
                "quality",
                "source",
                "source_as_of",
                "verified_at",
                "classification_method",
                "reason",
                "taxonomy_key",
            )
            if (value := (profile_provenance or {}).get(key)) is not None
        },
        "knowledge_routing": routing,
        "chart_knowledge_routing": chart_routing,
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
        "chart_context": chart,
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
    facts = _fact_catalog(assessment, evidence, valuation, price, chart)
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
        for item in session.exec(
            select(WatchlistItem).where(WatchlistItem.active.is_(True))
        ).all()
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
    chart_knowledge = chart_knowledge_manifest()
    market_context = _market_packet(session, run_date, market)
    profile_gate = company_profile_coverage(session, get_settings().data_dir)
    numeric_gate = numeric_registry_coverage(
        [
            market_context["numeric_registry"],
            *(stock["numeric_registry"] for stock in stocks),
        ]
    )
    cohort_ready = bool(profile_gate["ready"] and numeric_gate["ready"])
    body = {
        "schema_version": PACKET_SCHEMA_VERSION,
        "analysis_policy_version": ANALYSIS_POLICY_VERSION,
        "knowledge": knowledge,
        "chart_knowledge": chart_knowledge,
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
        "market_context": market_context,
        "stocks": stocks,
        "shadow_cohort": {
            "policy_version": ANALYSIS_POLICY_VERSION,
            "eligible": cohort_ready,
            "profile_gate": {
                key: profile_gate[key]
                for key in (
                    "active_total",
                    "complete_count",
                    "missing_count",
                    "unavailable_count",
                    "ready",
                )
            },
            "numeric_semantic_gate": numeric_gate,
        },
        "ready_for_ai": cohort_ready,
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
    if packet.get("ready_for_ai") is not True:
        return PacketWriteResult(
            status="not_ready",
            packet_id=str(packet.get("packet_id") or "") or None,
            reason="shadow_cohort_activation_gate_failed",
        )
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
            if policy != ANALYSIS_POLICY_VERSION:
                continue
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
                "chart_knowledge_sha256": str(
                    _dict(packet.get("chart_knowledge")).get("sha256") or ""
                ),
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
    return "\n".join(_prose_fields(review).values())


def _prose_fields(review: object) -> dict[str, str]:
    fields = {
        f"unknowns[{index}]": text
        for index, text in enumerate(getattr(review, "unknowns", []))
    }
    if isinstance(review, AIStockReview):
        fields.update(
            {
                "core_judgment.text": review.core_judgment.text,
                "business_earnings.text": review.business_earnings.text,
                "price_positioning.text": review.price_positioning.text,
                "price_positioning.new_observer_view": review.price_positioning.new_observer_view,
                "price_positioning.holder_view": review.price_positioning.holder_view,
                "supply_analysis.text": review.supply_analysis.text,
                "valuation_analysis.text": review.valuation_analysis.text,
                **{
                    f"priority_watch[{index}]": text
                    for index, text in enumerate(review.priority_watch)
                },
                **{
                    f"next_checks[{index}]": text
                    for index, text in enumerate(review.next_checks)
                },
            }
        )
    else:
        fields.update(
            {
                "core_judgment.text": getattr(review, "core_judgment").text,
                **{
                    f"important_changes[{index}].text": item.text
                    for index, item in enumerate(getattr(review, "important_changes", []))
                },
                "market_context.text": getattr(review, "market_context").text,
                "market_assumptions.text": getattr(review, "market_assumptions").text,
            }
        )
    return fields


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
    cleaned = text
    for pattern in _STRUCTURAL_NUMBER_PATTERNS:
        cleaned = re.sub(pattern, "", cleaned, flags=re.IGNORECASE)
    cleaned = re.sub(r"\b(?:thesis\s*)?version\s*\d+\b", "", cleaned, flags=re.IGNORECASE)
    return _numeric_tokens(cleaned)


def _numbers_equal(expected: float, actual: float) -> bool:
    return math.isclose(expected, actual, rel_tol=1e-12, abs_tol=1e-12)


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
    if unit == "points":
        return "%" not in usage and any(
            marker in lowered for marker in ("pt", "point", "포인트", "선물")
        )
    if unit in {"count", "years", "number"}:
        return False
    return True


def _usage_semantic_matches(semantic_type: str, usage: str) -> bool:
    return usage_matches_semantic(semantic_type, usage)


def _normalized_prose(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip()


def _structural_number_spans(text: str) -> list[tuple[int, int]]:
    return [
        match.span()
        for pattern in _STRUCTURAL_NUMBER_PATTERNS
        for match in re.finditer(pattern, text, flags=re.IGNORECASE)
    ]


def _prose_number_occurrences(text: str) -> list[tuple[int, int, str]]:
    structural = _structural_number_spans(text)
    return [
        (match.start(), match.end(), next(iter(_numeric_tokens(match.group(0)))))
        for match in _NUMBER.finditer(text)
        if not any(start <= match.start() and match.end() <= end for start, end in structural)
    ]


def _usage_spans(text: str, usage: str) -> list[tuple[int, int]]:
    spans: list[tuple[int, int]] = []
    start = 0
    while usage and (index := text.find(usage, start)) >= 0:
        spans.append((index, index + len(usage)))
        start = index + 1
    return spans


def _validate_numeric_claims(
    prefix: str,
    review: object,
    registry_value: object,
) -> list[str]:
    errors: list[str] = []
    registry = {
        (str(item.get("fact_id")), str(item.get("field_path"))): item
        for item in registry_value
        if isinstance(item, dict)
    } if isinstance(registry_value, list) else {}
    claims = getattr(review, "numeric_claims", [])
    facts_used = set(getattr(review, "facts_used", []))
    prose = {
        path: _normalized_prose(text)
        for path, text in _prose_fields(review).items()
    }
    coverage: dict[str, list[tuple[int, int, set[str]]]] = {
        path: [] for path in prose
    }
    for claim in claims:
        source = registry.get((claim.fact_id, claim.field_path))
        if source is None:
            errors.append(f"{prefix}:numeric_provenance_not_found:{claim.fact_id}:{claim.field_path}")
            continue
        claim_is_valid = True
        expected = float(source["value"])
        expected_unit = str(source["unit"])
        expected_semantic = str(source.get("semantic_type") or "")
        if source.get("registered") is not True or source.get("prose_allowed") is not True:
            errors.append(
                f"{prefix}:numeric_semantic_not_supported:"
                f"{claim.fact_id}:{claim.field_path}"
            )
            claim_is_valid = False
        if claim.fact_id not in facts_used:
            errors.append(f"{prefix}:numeric_fact_not_declared:{claim.fact_id}")
            claim_is_valid = False
        if claim.unit != expected_unit:
            errors.append(f"{prefix}:numeric_unit_mismatch:{claim.fact_id}:{claim.field_path}")
            claim_is_valid = False
        if claim.semantic_type != expected_semantic:
            errors.append(
                f"{prefix}:numeric_semantic_type_mismatch:"
                f"{claim.fact_id}:{claim.field_path}"
            )
            claim_is_valid = False
        if not _numbers_equal(expected, claim.value):
            errors.append(f"{prefix}:numeric_value_mismatch:{claim.fact_id}:{claim.field_path}")
            claim_is_valid = False
        if not _usage_unit_matches(expected_unit, claim.usage):
            errors.append(f"{prefix}:numeric_usage_unit_mismatch:{claim.fact_id}:{claim.field_path}")
            claim_is_valid = False
        if not _usage_semantic_matches(expected_semantic, claim.usage):
            errors.append(f"{prefix}:numeric_usage_semantic_mismatch:{claim.fact_id}:{claim.field_path}")
            claim_is_valid = False
        if not usage_direction_matches(expected_semantic, expected, claim.usage):
            errors.append(
                f"{prefix}:numeric_usage_direction_mismatch:"
                f"{claim.fact_id}:{claim.field_path}"
            )
            claim_is_valid = False
        display_tokens = _provenance_tokens(claim.usage)
        approved_variants = source.get("approved_display_variants")
        allowed_display_tokens = (
            set().union(
                *(
                    _provenance_tokens(str(variant))
                    for variant in approved_variants
                )
            )
            if isinstance(approved_variants, list) and approved_variants
            else set()
        )
        if not display_tokens or not display_tokens.issubset(allowed_display_tokens):
            errors.append(
                f"{prefix}:numeric_usage_value_mismatch:{claim.fact_id}:{claim.field_path}"
            )
            claim_is_valid = False
        target = prose.get(claim.text_ref)
        if target is None:
            errors.append(f"{prefix}:numeric_text_ref_not_found:{claim.text_ref}")
            continue
        usage = _normalized_prose(claim.usage)
        spans = _usage_spans(target, usage)
        if not spans:
            errors.append(
                f"{prefix}:numeric_usage_not_in_text_ref:"
                f"{claim.fact_id}:{claim.field_path}:{claim.text_ref}"
            )
            continue
        if claim_is_valid:
            coverage[claim.text_ref].extend(
                (start, end, display_tokens) for start, end in spans
            )
    for path, text in prose.items():
        uncovered = []
        for start, end, token in _prose_number_occurrences(text):
            if not any(
                claim_start <= start
                and end <= claim_end
                and token in display_tokens
                for claim_start, claim_end, display_tokens in coverage[path]
            ):
                uncovered.append(token)
        if uncovered:
            errors.append(
                f"{prefix}:numbers_without_provenance:{path}:"
                + ",".join(uncovered)
            )
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
        fact_id
        for item in (
            review.core_judgment,
            review.business_earnings,
            review.price_positioning,
            review.supply_analysis,
            review.valuation_analysis,
        )
        for fact_id in item.fact_ids
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
        industry_routing = routing.get("industry_routing")
        if isinstance(industry_routing, dict):
            primary_framework = str(
                industry_routing.get("primary_framework") or ""
            )
            confidence = str(industry_routing.get("confidence") or "low")
            if (
                confidence == "high"
                and primary_framework
                and primary_framework not in review.frameworks_used
            ):
                errors.append(
                    f"{review.ticker}:industry_framework_missing:{primary_framework}"
                )
    errors.extend(
        _validate_numeric_claims(
            review.ticker,
            review,
            stock.get("numeric_registry"),
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
    chart_knowledge = packet.get("chart_knowledge")
    if not isinstance(chart_knowledge, dict):
        errors.append("identity_mismatch:chart_knowledge")
    else:
        if output.chart_knowledge_version != chart_knowledge.get("version"):
            errors.append("identity_mismatch:chart_knowledge_version")
        if output.chart_knowledge_sha256 != chart_knowledge.get("sha256"):
            errors.append("identity_mismatch:chart_knowledge_sha256")
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
        for item in (
            output.market_review.core_judgment,
            *output.market_review.important_changes,
            output.market_review.market_context,
            output.market_review.market_assumptions,
        )
        for fact_id in item.fact_ids
    }
    if market_interpretation_facts - market_fact_ids:
        errors.append("market_review:interpretation_unknown_fact_ids")
    market_text = "\n".join(_prose_fields(output.market_review).values())
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
        if any(
            not item.fact_ids
            for item in (
                review.core_judgment,
                review.business_earnings,
                review.price_positioning,
                review.supply_analysis,
                review.valuation_analysis,
            )
            if item.text.strip()
        ):
            guardrail_conflicts.append("interpretation_without_fact_reference")
        stock_packet = stock_packets.get(review.ticker, {})
        guardrail_conflicts.extend(_semantic_guardrail_flags(review, stock_packet))
        knowledge_routing = stock_packet.get("knowledge_routing")
        industry_routing = (
            knowledge_routing.get("industry_routing")
            if isinstance(knowledge_routing, dict)
            else {}
        )
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
                "industry_routing": {
                    "primary_expected": (
                        industry_routing.get("primary_framework")
                        if isinstance(industry_routing, dict)
                        else None
                    ),
                    "secondary_allowed": (
                        industry_routing.get("secondary_frameworks", [])
                        if isinstance(industry_routing, dict)
                        else []
                    ),
                    "confidence": (
                        industry_routing.get("confidence", "low")
                        if isinstance(industry_routing, dict)
                        else "low"
                    ),
                    "actual_frameworks_used": review.frameworks_used,
                },
                "facts_used": review.facts_used,
                "numeric_claims": [item.model_dump() for item in review.numeric_claims],
                "unknowns": review.unknowns,
                "ai_summary": review.core_judgment.text,
            }
        )
    return {
        "packet_id": output.packet_id,
        "analysis_policy_version": output.analysis_policy_version,
        "knowledge_version": output.knowledge_version,
        "knowledge_sha256": output.knowledge_sha256,
        "chart_knowledge_version": output.chart_knowledge_version,
        "chart_knowledge_sha256": output.chart_knowledge_sha256,
        "mode": get_settings().ai_review_mode,
        "validated_at": validated_at.isoformat(),
        "official_assessment_mutated": False,
        "telegram_mutated": False,
        "comparisons": comparisons,
    }


def quantitative_grounding_report(
    packet: dict[str, object],
    output: AIDailyReviewOutput,
) -> dict[str, object]:
    stocks = {
        str(item["ticker"]): item
        for item in packet.get("stocks", [])
        if isinstance(item, dict) and item.get("ticker")
    }
    section_prefixes = {
        "core": ("core_judgment.",),
        "earnings": ("business_earnings.",),
        "price": ("price_positioning.",),
        "supply": ("supply_analysis.",),
        "valuation": ("valuation_analysis.",),
    }
    semantic_sections = {
        "earnings": {
            "revenue",
            "operating_income",
            "operating_margin",
            "revenue_qoq",
            "revenue_yoy",
            "operating_income_qoq",
            "operating_income_yoy",
        },
        "price": {
            "share_price",
            "chart_open_price",
            "chart_high_price",
            "chart_low_price",
            "chart_close_price",
            "chart_period_return_pct",
            "chart_range_position_pct",
            "bollinger_upper_price",
            "bollinger_distance_pct",
            "volume_ratio_20",
            "rsi_14",
            "macd",
            "macd_signal",
            "macd_histogram",
            "stored_confirmation_price",
            "stored_support_price",
            "stored_warning_price",
            "stored_invalidation_price",
            "price_rule_distance_pct",
        },
        "supply": {
            semantic
            for semantic in NUMERIC_SEMANTICS
            if "net_buy_qty" in semantic or semantic.startswith("foreign_holding")
        },
        "valuation": {
            "trailing_pe",
            "price_to_book",
            "forward_pe",
            "forward_price_to_book",
            "historical_pe_multiple",
            "historical_pb_multiple",
            "historical_pe_percentile",
            "historical_pb_percentile",
        },
    }
    rows: list[dict[str, object]] = []
    for review in output.stock_reviews:
        stock = stocks.get(review.ticker, {})
        registry = (
            stock.get("numeric_registry", []) if isinstance(stock, dict) else []
        )
        eligible = [
            item
            for item in registry
            if isinstance(item, dict) and item.get("prose_allowed") is True
        ]
        claims = [item.model_dump() for item in review.numeric_claims]
        sections: dict[str, dict[str, int]] = {}
        flags: list[str] = []
        for section, prefixes in section_prefixes.items():
            if section == "core":
                eligible_count = len(eligible)
            else:
                eligible_count = sum(
                    str(item.get("semantic_type")) in semantic_sections[section]
                    for item in eligible
                )
            used_count = sum(
                any(str(item["text_ref"]).startswith(prefix) for prefix in prefixes)
                for item in claims
            )
            sections[section] = {"eligible": eligible_count, "used": used_count}
            minimum = 2 if section in {"core", "earnings", "supply", "valuation"} else 1
            if eligible_count >= minimum and used_count < minimum:
                flags.append(f"insufficient_quantitative_grounding:{section}")
        prose = "\n".join(_prose_fields(review).values())
        if len(eligible) >= 2 and not claims and re.search(
            r"(?:강한\s*실적|높은\s*기대|프리미엄|현금창출.*확인)", prose
        ):
            flags.append("vague_quantitative_language")
        chart = stock.get("chart_context", {}) if isinstance(stock, dict) else {}
        timeframes = chart.get("timeframes", {}) if isinstance(chart, dict) else {}
        rows.append(
            {
                "ticker": review.ticker,
                "eligible_numeric_anchors": len(eligible),
                "numeric_claims_used": len(claims),
                "section_coverage": sections,
                "chart_timeframes_available": sorted(timeframes) if isinstance(timeframes, dict) else [],
                "chart_fact_ids_used": sorted(
                    fact_id for fact_id in review.facts_used if fact_id.startswith("chart:")
                ),
                "flags": flags,
            }
        )
    return {
        "packet_id": output.packet_id,
        "analysis_policy_version": output.analysis_policy_version,
        "status": "flagged" if any(row["flags"] for row in rows) else "passed",
        "stocks": rows,
    }


def _semantic_guardrail_flags(
    review: AIStockReview,
    stock: dict[str, object],
) -> list[str]:
    assertions = "\n".join(_prose_fields(review).values()).lower()
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
    grounding_path = history_dir / output_name.replace(
        ".json", ".quantitative-grounding.json"
    )
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
                str(final_claim.get("chart_knowledge_sha256") or "")
                == str(_dict(packet.get("chart_knowledge")).get("sha256") or ""),
                Path(str(final_claim.get("temp_output_path") or temp_path)) == temp_path,
                Path(str(final_claim.get("final_output_path") or final_path)) == final_path,
                str(candidate.get("packet_id") or "") == packet_id,
                str(candidate.get("claim_id") or "") == claim_id,
                str(candidate.get("analysis_policy_version") or "") == policy_version,
                str(candidate.get("knowledge_sha256") or "") == knowledge_sha,
                str(candidate.get("chart_knowledge_sha256") or "")
                == str(_dict(packet.get("chart_knowledge")).get("sha256") or ""),
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
        _atomic_json(grounding_path, quantitative_grounding_report(packet, output))
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
