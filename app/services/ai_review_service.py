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
from app.models.financial import FinancialSnapshot
from app.models.macro import MacroBriefing, ThesisMacroImpact
from app.models.company import Company
from app.models.security import SecurityMaster
from app.models.thesis import InvestmentThesis, MonitorRun, ThesisAssessment
from app.models.watchlist import WatchlistItem
from app.schemas.ai_review import AIDailyReviewOutput, AIStockReview
from app.services.ai_reasoning_quality_service import normalize_decision_text
from app.services.canonical_fact_service import (
    canonical_capital_action_fact,
    canonical_event_fact,
)
from app.services.company_profile_service import (
    company_profile_coverage,
    read_profile_provenance,
)
from app.services.daily_digest import build_daily_digest
from app.services.financial_quality_service import (
    build_financial_quality_state,
    field_quality,
)
from app.services.financial_amount_period_service import (
    AMOUNT_PERIOD_CONTRACT,
    STATEMENT_BASIS_CONTRACT,
    apply_comparison_period_metadata,
    financial_amount_period_label,
    financial_amount_period_lineage,
    unique_financial_source_row,
)
from app.services.market_session import market_scope_for_security
from app.services.market_intelligence_service import build_market_intelligence
from app.services.night_futures import NIGHT_FUTURES_SERIES
from app.services.official_security_identity_service import (
    load_official_identity_provenance,
)
from app.services.numeric_provenance_service import (
    TYPED_VALUATION_CONTRACT,
    bind_numeric_fact_references,
    canonical_numeric_label_mismatch,
    redundant_numeric_label_before,
)
from app.services.security_identity_service import (
    IDENTITY_CONFLICT,
    IDENTITY_UNKNOWN,
    VERIFIED_DEPOSITARY,
    VERIFIED_NON_DEPOSITARY,
    resolve_packet_security_identity,
    resolve_security_identity,
)
from app.services.numeric_semantic_registry import (
    NUMERIC_SEMANTICS,
    build_numeric_registry,
    numeric_registry_coverage,
    usage_direction_matches,
    usage_matches_semantic,
)
from app.services.ohlcv_structure_service import ALGORITHM_VERSION
from app.services.valuation_snapshot_service import (
    _earnings_quarters,
    _latest_balance,
    _valid_quarters,
)


logger = logging.getLogger(__name__)

PACKET_SCHEMA_VERSION = "1"
OUTPUT_SCHEMA_VERSION = "4"
ANALYSIS_POLICY_VERSION = "daily-review-v3.10"
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
_NUMBER = re.compile(
    r"(?<![\w])[-+]?(?:\d{1,3}(?:,\d{3})+|\d+)(?:\.\d+)?%?"
)
_STRUCTURAL_NUMBER_PATTERNS = (
    r"\bS&P\s*500\b",
    r"\bRussell\s*2000\b",
    r"\bKOSPI\s*200\b",
    r"\bKOSDAQ\s*150\b",
    r"\b(?:미국\s*)?10\s*년물\b",
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
    structure = chart.get("structure")
    availability = (
        structure.get("availability")
        if isinstance(structure, dict) and isinstance(structure.get("availability"), dict)
        else {}
    )
    for available_key, framework in (
        ("atr", "chart_atr"),
        ("support_resistance", "chart_support_resistance"),
        ("box_ranges", "chart_box"),
        ("major_swings", "chart_major_swing"),
        ("fibonacci", "chart_fibonacci"),
        ("risk_reward", "chart_risk_reward"),
        ("invalidation", "chart_invalidation"),
        ("chart_state_machine", "chart_state_machine"),
    ):
        if availability.get(available_key) is True:
            required.append(framework)
    elliott = structure.get("elliott") if isinstance(structure, dict) else None
    if (
        availability.get("elliott_wave") is True
        and isinstance(elliott, dict)
        and elliott.get("usable_in_core") is True
    ):
        required.append("chart_elliott")
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


def _list(value: object) -> list[object]:
    if isinstance(value, list):
        return value
    if not isinstance(value, str):
        return []
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


def _financial_source_metadata(
    session: Session,
    assessment: ThesisAssessment,
    snapshot: dict[str, object],
) -> dict[str, object]:
    persisted = _dict(snapshot.get("financial_quality_source_metadata"))
    period = str(snapshot.get("latest_earnings_period") or "")
    if not period and not persisted:
        return {}
    rows = list(session.exec(
        select(FinancialSnapshot).where(FinancialSnapshot.ticker == assessment.ticker)
    ).all())
    calculated_at = str(snapshot.get("valuation_calculated_at") or "")
    cutoff: datetime | None = None
    if calculated_at:
        try:
            cutoff = datetime.fromisoformat(calculated_at.replace("Z", "+00:00"))
            if cutoff.tzinfo is None:
                cutoff = cutoff.replace(tzinfo=UTC)
        except ValueError:
            cutoff = None

    def available(row: FinancialSnapshot) -> bool:
        filed = row.filing_date or row.reported_date
        if filed and filed > assessment.assessment_date:
            return False
        created = row.created_at
        if cutoff is not None and created is not None:
            if created.tzinfo is None:
                created = created.replace(tzinfo=UTC)
            if created > cutoff:
                return False
        return True

    rows = [row for row in rows if available(row)]

    def row_period(row: FinancialSnapshot) -> str:
        return str(row.financial_period_end or row.financials_as_of or row.period)[:10]

    def metadata(
        row: FinancialSnapshot,
        field: str | None = None,
    ) -> dict[str, object]:
        value = {
            "period": row_period(row),
            "period_type": row.period_type,
            "fiscal_year": row.fiscal_year,
            "period_scope": row.period_scope,
            "is_cumulative": row.is_cumulative,
            "source_type": row.snapshot_type,
            "provider": row.provider,
            "filing_date": str(row.filing_date or row.reported_date or "") or None,
            "hard_errors": _list(row.financial_hard_errors),
            "soft_outliers": _list(row.financial_soft_outliers),
            "financial_statement_basis_warning": row.financial_statement_basis_warning,
            "period_mapping_validation_failed": row.period_mapping_validation_failed,
            "margin_quality_review": row.margin_quality_review,
            "lineage_verified": True,
        }
        if field is not None and row.provider == "opendart":
            value.update(financial_amount_period_lineage(row, field))
        return value

    def enrich_persisted_period_metadata(value: object) -> object:
        if isinstance(value, list):
            return [enrich_persisted_period_metadata(item) for item in value]
        if not isinstance(value, dict):
            return value
        enriched = {
            key: enrich_persisted_period_metadata(item)
            for key, item in value.items()
        }
        item_period = str(enriched.get("period") or "")[:10]
        if not item_period:
            return enriched
        item_source = str(enriched.get("source_type") or "")
        item_provider = str(enriched.get("provider") or "")
        item_filing = str(enriched.get("filing_date") or "")[:10]
        matches = [
            row
            for row in rows
            if row_period(row) == item_period
            and (not item_source or row.snapshot_type == item_source)
            and (not item_provider or row.provider == item_provider)
            and (
                not item_filing
                or str(row.filing_date or row.reported_date or "")[:10]
                == item_filing
            )
        ]
        for field in ("period_type", "fiscal_year", "period_scope", "is_cumulative"):
            if enriched.get(field) is not None:
                continue
            values = {getattr(row, field) for row in matches if getattr(row, field) is not None}
            if len(values) == 1:
                enriched[field] = values.pop()
        return enriched

    if persisted:
        enriched_persisted = _dict(enrich_persisted_period_metadata(persisted))
        enriched_persisted["financial_amount_period_contract"] = (
            AMOUNT_PERIOD_CONTRACT
        )
        enriched_persisted["financial_statement_basis_contract"] = (
            STATEMENT_BASIS_CONTRACT
        )
        enriched_direct = _dict(enriched_persisted.get("direct_field_sources"))
        for field, values in enriched_direct.items():
            if not isinstance(values, list):
                continue
            for item in values:
                if not isinstance(item, dict):
                    continue
                item_period = str(item.get("period") or "")[:10]
                item_filing = str(item.get("filing_date") or "")[:10]
                matches = [
                    row
                    for row in rows
                    if row_period(row) == item_period
                    and (
                        not item_filing
                        or str(row.filing_date or row.reported_date or "")[:10]
                        == item_filing
                    )
                ]
                sourced_matches = [row for row in matches if row.source_filing_id]
                if sourced_matches:
                    matches = sourced_matches
                matched_row = unique_financial_source_row(matches, field)
                if matched_row is not None and matched_row.provider == "opendart":
                    item.update(financial_amount_period_lineage(matched_row, field))
            comparison = (
                "qoq"
                if str(field).endswith("_qoq")
                else "yoy"
                if str(field).endswith("_yoy")
                else None
            )
            if comparison:
                apply_comparison_period_metadata(
                    [item for item in values if isinstance(item, dict)],
                    comparison=comparison,
                )
        return enriched_persisted

    def match_series(item: dict[str, object]) -> FinancialSnapshot | None:
        item_period = str(item.get("period") or "")[:10]
        item_source = str(item.get("source") or "")
        item_filing = str(item.get("filing") or "")[:10]
        candidates = [
            row
            for row in rows
            if row_period(row) == item_period
            and (not item_source or row.snapshot_type == item_source)
            and (
                not item_filing
                or str(row.filing_date or row.reported_date or "")[:10] == item_filing
            )
        ]
        for field in ("revenue", "operating_income", "net_income"):
            value = item.get(field)
            matched = [row for row in candidates if value is None or getattr(row, field) == value]
            if matched:
                candidates = matched
        return max(candidates, key=lambda item: item.id or 0) if candidates else None

    candidates = [
        row
        for row in rows
        if row_period(row) == period[:10]
        and (
            not snapshot.get("earnings_context_source")
            or row.snapshot_type == snapshot.get("earnings_context_source")
        )
    ]
    matched_candidates = [
        row
        for row in candidates
        if (
            snapshot.get("latest_revenue") is None
            or row.revenue == snapshot.get("latest_revenue")
        )
        and (
            snapshot.get("latest_operating_income") is None
            or row.operating_income == snapshot.get("latest_operating_income")
        )
    ]
    if matched_candidates:
        candidates = matched_candidates
    if not candidates:
        return {}
    row = max(
        candidates,
        key=lambda item: (
            item.filing_date or item.reported_date or date.min,
            item.id or 0,
        ),
    )
    result = metadata(row)
    result["financial_amount_period_contract"] = AMOUNT_PERIOD_CONTRACT
    result["financial_statement_basis_contract"] = STATEMENT_BASIS_CONTRACT

    quarter_series = [
        item
        for item in _list(snapshot.get("earnings_quarter_series"))
        if isinstance(item, dict)
    ]
    ttm_sources: list[dict[str, object]] = []
    for item in quarter_series:
        matched = match_series(item)
        if matched is None:
            ttm_sources.append(
                {
                    "period": item.get("period"),
                    "source_type": item.get("source"),
                    "filing_date": item.get("filing"),
                    "lineage_verified": False,
                }
            )
        else:
            ttm_sources.append(metadata(matched))
    result["ttm_sources"] = ttm_sources

    selected_quarters = _earnings_quarters(rows)
    latest = selected_quarters[-1] if selected_quarters else row
    latest_period = latest.financial_period_end or latest.financials_as_of
    prior = None
    prior_year = None
    if latest_period:
        previous = [
            candidate
            for candidate in selected_quarters
            if (candidate_period := candidate.financial_period_end or candidate.financials_as_of)
            and candidate_period < latest_period
        ]
        if previous:
            candidate = max(
                previous,
                key=lambda item: item.financial_period_end or item.financials_as_of or date.min,
            )
            candidate_period = candidate.financial_period_end or candidate.financials_as_of
            if candidate_period and 60 <= (latest_period - candidate_period).days <= 120:
                prior = candidate
        prior_year = next(
            (
                candidate
                for candidate in selected_quarters
                if (candidate_period := candidate.financial_period_end or candidate.financials_as_of)
                and 330 <= (latest_period - candidate_period).days <= 400
            ),
            None,
        )
    direct_field_sources: dict[str, list[dict[str, object]]] = {
        field: [metadata(row, field)]
        for field in (
            "latest_revenue",
            "latest_operating_income",
            "latest_operating_margin",
        )
    }
    if prior is not None:
        for field in ("latest_revenue_qoq", "latest_operating_income_qoq"):
            records = [metadata(row, field), metadata(prior, field)]
            apply_comparison_period_metadata(records, comparison="qoq")
            direct_field_sources[field] = records
    if prior_year is not None:
        for field in ("latest_revenue_yoy", "latest_operating_income_yoy"):
            records = [metadata(row, field), metadata(prior_year, field)]
            apply_comparison_period_metadata(records, comparison="yoy")
            direct_field_sources[field] = records
    result["direct_field_sources"] = direct_field_sources

    minimum = get_settings().valuation_model_min_quarters
    modeled_sources = selected_quarters[-minimum:]
    result["modeled_forward_sources"] = [metadata(item) for item in modeled_sources]
    result["modeled_forward_expected_count"] = minimum
    full_quarters = _valid_quarters(rows)
    modeled_book_sources = (
        full_quarters[-minimum:]
        if any(item.snapshot_type == "preliminary_earnings" for item in modeled_sources)
        else modeled_sources
    )
    result["modeled_forward_book_sources"] = [
        metadata(item) for item in modeled_book_sources
    ]
    result["modeled_forward_book_expected_count"] = minimum

    balance = _latest_balance(rows)
    if balance is not None:
        balance_metadata = metadata(balance)
        expected_book_period = str(snapshot.get("pbr_denominator_period_end") or "")
        expected_book_filing = str(snapshot.get("pbr_denominator_filing_date") or "")
        balance_metadata["lineage_verified"] = bool(
            expected_book_period
            and row_period(balance) == expected_book_period[:10]
            and (
                not expected_book_filing
                or str(balance.filing_date or balance.reported_date or "")[:10]
                == expected_book_filing[:10]
            )
        )
        result["book_source"] = balance_metadata
    return result


def _valuation_payload(
    session: Session,
    assessment: ThesisAssessment,
) -> dict[str, object]:
    snapshot = _dict(assessment.valuation_snapshot)
    watchlist_item = session.exec(
        select(WatchlistItem).where(WatchlistItem.ticker == assessment.ticker)
    ).first()
    security_master = session.exec(
        select(SecurityMaster).where(SecurityMaster.ticker == assessment.ticker)
    ).first()
    identity = resolve_security_identity(
        company_name=(
            watchlist_item.company_name
            if watchlist_item is not None
            else security_master.company_name
            if security_master is not None
            else assessment.ticker
        ),
        watchlist_item=watchlist_item,
        security_master=security_master,
        legacy_issuer_type=str(snapshot.get("resolved_issuer_type") or ""),
        legacy_security_type=str(snapshot.get("resolved_security_type") or ""),
        legacy_is_depositary=(
            snapshot.get("is_depositary_security")
            if isinstance(snapshot.get("is_depositary_security"), bool)
            else None
        ),
        identity_provenance=load_official_identity_provenance(
            session, assessment.ticker
        ),
    )
    snapshot.update(
        {
            "resolved_issuer_type": identity["selected_issuer_type"],
            "resolved_security_type": identity["selected_security_type"],
            "is_depositary_security": (
                identity["identity_state"] == VERIFIED_DEPOSITARY
                or (
                    identity["identity_state"] == IDENTITY_UNKNOWN
                    and identity.get("is_depositary_evidence_present") is True
                )
            ),
            "security_identity_state": identity["identity_state"],
            "security_identity_decision_version": identity["decision_version"],
            "security_identity_evidence": identity["evidence_sources"],
            "security_identity_evidence_values": identity["evidence_values"],
            "security_identity_conflict_reasons": identity["conflict_reasons"],
            "security_identity_resolved_conflict_reasons": identity[
                "resolved_conflict_reasons"
            ],
            "security_identity_verification_status": identity[
                "verification_status"
            ],
            "security_identity_as_of": identity["as_of"],
            "security_identity_source_provenance": identity[
                "source_provenance"
            ],
            "security_identity_source_tier": identity["source_tier"],
            "security_identity_verification_source_tier": identity[
                "verification_source_tier"
            ],
            "security_identity_provenance": identity["identity_provenance"],
            "security_identity_eligibility_decision": identity[
                "eligibility_decision"
            ],
            "security_identity_selected_issuer_type": identity[
                "selected_issuer_type"
            ],
            "security_identity_selected_security_type": identity[
                "selected_security_type"
            ],
            "security_identity_selected_adr_ratio": identity[
                "selected_adr_ratio"
            ],
            "security_identity_selected_adr_ratio_source": identity[
                "selected_adr_ratio_source"
            ],
            "security_identity_adr_ratio_direction": identity[
                "adr_ratio_direction"
            ],
            "security_identity_depositary_evidence_present": identity[
                "is_depositary_evidence_present"
            ],
        }
    )
    fields = (
        "current_price",
        "currency",
        "financial_currency",
        "price_as_of",
        "price_basis",
        "latest_earnings_period",
        "latest_earnings_period_type",
        "latest_earnings_fiscal_year",
        "latest_earnings_period_scope",
        "latest_earnings_is_cumulative",
        "earnings_context_is_preliminary",
        "latest_revenue",
        "latest_operating_income",
        "latest_operating_margin",
        "latest_revenue_qoq",
        "latest_revenue_yoy",
        "latest_operating_income_qoq",
        "latest_operating_income_yoy",
        "ttm_period_start",
        "ttm_period_end",
        "ttm_source_filings",
        "ttm_contains_preliminary",
        "ttm_eps_usable",
        "earnings_quarter_series",
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
        "forward_pe_input_period",
        "forward_price_to_book_source",
        "forward_price_to_book_method",
        "forward_pb_input_period",
        "forecast_method",
        "forward_basis",
        "forward_book_basis",
        "estimate_period",
        "historical_comparability",
        "valuation_relative_position",
        "valuation_relative_basis",
        "quality",
        "provider",
        "resolved_issuer_type",
        "resolved_security_type",
        "is_depositary_security",
        "security_identity_state",
        "security_identity_decision_version",
        "security_identity_evidence",
        "security_identity_evidence_values",
        "security_identity_conflict_reasons",
        "security_identity_resolved_conflict_reasons",
        "security_identity_verification_status",
        "security_identity_as_of",
        "security_identity_source_provenance",
        "security_identity_source_tier",
        "security_identity_verification_source_tier",
        "security_identity_provenance",
        "security_identity_eligibility_decision",
        "security_identity_selected_issuer_type",
        "security_identity_selected_security_type",
        "security_identity_selected_adr_ratio",
        "security_identity_selected_adr_ratio_source",
        "security_identity_adr_ratio_direction",
        "security_identity_depositary_evidence_present",
        "eps_currency",
        "eps_security_basis",
        "book_currency",
        "valuation_calculated_at",
        "trailing_pe_denominator_period_end",
        "trailing_pe_denominator_filing_date",
        "pbr_denominator_period_end",
        "pbr_denominator_filing_date",
        "trailing_pe_basis_status",
        "price_to_book_basis_status",
        "forward_pe_basis_status",
        "forward_price_to_book_basis_status",
        "trailing_pe_basis_conflict",
        "price_to_book_basis_conflict",
        "forward_pe_basis_conflict",
        "forward_price_to_book_basis_conflict",
    )
    result = {key: snapshot.get(key) for key in fields if snapshot.get(key) is not None}
    source_metadata = _financial_source_metadata(session, assessment, snapshot)
    result["financial_quality"] = build_financial_quality_state(
        snapshot,
        source_metadata=source_metadata,
    )
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


def _compact_chart_structure(structure: dict[str, object]) -> dict[str, object]:
    zones = _dict(structure.get("zones"))
    boxes = _dict(structure.get("boxes"))
    major = _dict(structure.get("major_swings"))
    elliott = _dict(structure.get("elliott"))
    compact_elliott = {
        key: value
        for key in (
            "available",
            "tentative_count",
            "confidence",
            "possible_diagonal",
            "usable_in_core",
            "reason",
            "blocking_unknowns",
        )
        if (value := elliott.get(key)) is not None
    }
    if elliott.get("usable_in_core") is True:
        compact_elliott["points"] = _list(elliott.get("points"))[-6:]
    meaningful_supports = [
        item
        for item in [*_list(zones.get("active")), *_list(zones.get("support"))]
        if isinstance(item, dict) and item.get("strength") in {"Strong", "Medium"}
    ]
    meaningful_resistances = [
        item
        for item in _list(zones.get("resistance"))
        if isinstance(item, dict) and item.get("strength") in {"Strong", "Medium"}
    ]
    return {
        "algorithm_version": structure.get("algorithm_version"),
        "as_of_date": structure.get("as_of_date"),
        "price_basis": structure.get("price_basis"),
        "availability": _dict(structure.get("availability")),
        "atr": _dict(structure.get("atr")),
        "nearest_supports": meaningful_supports[:2],
        "nearest_resistance": meaningful_resistances[:1],
        "active_zones": _list(zones.get("active"))[:2],
        "boxes": {
            timeframe: _list(boxes.get(timeframe))[:1]
            for timeframe in ("daily", "weekly", "monthly")
            if _list(boxes.get(timeframe))
        },
        "major_swings": {
            "primary_timeframe": major.get("primary_timeframe"),
            "fallback_used": major.get("fallback_used"),
            "recent_points": _list(major.get("points"))[-6:],
        },
        "major_anchors": _dict(structure.get("major_anchors")),
        "elliott": compact_elliott,
        "fibonacci": _dict(structure.get("fibonacci")),
        "fibonacci_status": _dict(structure.get("fibonacci_status")),
        "invalidation": _dict(structure.get("invalidation")),
        "risk_reward": _dict(structure.get("risk_reward")),
        "supply_classification": _dict(structure.get("supply_classification")),
        "chart_state": _dict(structure.get("chart_state")),
    }


def _chart_payload(
    assessment: ThesisAssessment,
    thesis: InvestmentThesis,
    previous: ThesisAssessment | None,
) -> dict[str, object]:
    price_context = _dict(assessment.price_context)
    chart = _public_value(_dict(price_context.get("chart")))
    if isinstance(chart, dict) and isinstance(chart.get("structure"), dict):
        chart["structure"] = _public_value(
            _compact_chart_structure(_dict(chart.get("structure")))
        )
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
    structure = chart.get("structure")
    if chart_usable and isinstance(structure, dict):
        atr = _dict(structure.get("atr"))
        for timeframe in ("daily", "weekly", "monthly"):
            value = _dict(atr.get(timeframe))
            if value.get("available") is not True or _number(value.get("value")) is None:
                continue
            facts.append(
                {
                    "fact_id": f"chart:structure:atr:{timeframe}",
                    "fact_type": "chart_structure_atr",
                    "as_of_date": str(structure.get("as_of_date") or ""),
                    "source": "deterministic_ohlcv_structure",
                    "fields": {
                        "value": value["value"],
                        "currency": currency,
                        "timeframe": timeframe,
                        "period": "Wilder 14",
                        "algorithm_version": structure.get("algorithm_version"),
                    },
                }
            )
        for category, fact_type in (
            ("nearest_supports", "chart_support_zone"),
            ("nearest_resistance", "chart_resistance_zone"),
            ("active_zones", "chart_active_zone"),
        ):
            for index, item in enumerate(_list(structure.get(category)), start=1):
                if not isinstance(item, dict):
                    continue
                fields = {
                    key: item[key]
                    for key in (
                        "zone_low",
                        "zone_high",
                        "distance_pct",
                        "distance_to_lower_pct",
                        "distance_to_upper_pct",
                        "timeframe",
                        "strength",
                    )
                    if item.get(key) is not None
                }
                fields["currency"] = currency
                facts.append(
                    {
                        "fact_id": f"chart:structure:{category}:{index}",
                        "fact_type": fact_type,
                        "as_of_date": str(structure.get("as_of_date") or ""),
                        "source": "deterministic_ohlcv_structure",
                        "fields": fields,
                    }
                )
        for timeframe, items in _dict(structure.get("boxes")).items():
            for index, item in enumerate(_list(items), start=1):
                if not isinstance(item, dict):
                    continue
                facts.append(
                    {
                        "fact_id": f"chart:structure:box:{timeframe}:{index}",
                        "fact_type": "chart_box",
                        "as_of_date": str(structure.get("as_of_date") or ""),
                        "source": "deterministic_ohlcv_structure",
                        "fields": {
                            "box_low": item.get("box_low"),
                            "box_high": item.get("box_high"),
                            "width_pct": item.get("width_pct"),
                            "currency": currency,
                            "timeframe": timeframe,
                        },
                    }
                )
        major = _dict(structure.get("major_swings"))
        for index, item in enumerate(_list(major.get("recent_points")), start=1):
            if not isinstance(item, dict):
                continue
            facts.append(
                {
                    "fact_id": f"chart:structure:major_swing:{index}",
                    "fact_type": "chart_major_swing",
                    "as_of_date": str(item.get("date") or ""),
                    "source": "deterministic_ohlcv_structure",
                    "fields": {
                        "price": item.get("price"),
                        "currency": currency,
                        "timeframe": item.get("timeframe"),
                        "kind": item.get("kind"),
                        "confirmed_at": item.get("confirmed_at"),
                    },
                }
            )
        for name, item in _dict(structure.get("fibonacci")).items():
            if not isinstance(item, dict):
                continue
            if item.get("usable_as_context") is not True:
                continue
            facts.append(
                {
                    "fact_id": f"chart:structure:fibonacci:{name}",
                    "fact_type": "chart_fibonacci",
                    "as_of_date": str(item.get("high_date") or ""),
                    "source": "deterministic_ohlcv_structure",
                    "fields": {
                        "low_price": item.get("low_price"),
                        "high_price": item.get("high_price"),
                        "retracements": item.get("retracements", {}),
                        "extensions": item.get("extensions", {}),
                        "currency": currency,
                        "anchor_type": item.get("anchor_type"),
                        "low_date": item.get("low_date"),
                        "high_date": item.get("high_date"),
                        "timeframe": item.get("timeframe"),
                        "confidence": item.get("confidence"),
                    },
                }
            )
        invalidation = _dict(structure.get("invalidation"))
        if invalidation.get("available") is True:
            facts.append(
                {
                    "fact_id": "chart:structure:invalidation",
                    "fact_type": "chart_invalidation",
                    "as_of_date": str(structure.get("as_of_date") or ""),
                    "source": "deterministic_ohlcv_structure",
                    "fields": {
                        key: value
                        for key in (
                            "price",
                            "entry",
                            "support_low",
                            "buffer",
                            "scenario",
                            "timeframe",
                            "status",
                            "chart_only",
                            "currency",
                        )
                        if (
                            value := currency if key == "currency" else invalidation.get(key)
                        )
                        is not None
                    },
                }
            )
        risk_reward = _dict(structure.get("risk_reward"))
        if risk_reward.get("available") is True:
            for scenario in ("current_price", "support_entry"):
                value = _dict(risk_reward.get(scenario))
                if not value:
                    continue
                facts.append(
                    {
                        "fact_id": f"chart:structure:risk_reward:{scenario}",
                        "fact_type": f"chart_risk_reward_{scenario}",
                        "as_of_date": str(structure.get("as_of_date") or ""),
                        "source": "deterministic_ohlcv_structure",
                        "fields": {
                            **{
                                key: value.get(key)
                                for key in (
                                    "entry",
                                    "target",
                                    "invalidation",
                                    "upside",
                                    "downside",
                                    "ratio",
                                    "scenario",
                                    "classification",
                                )
                                if value.get(key) is not None
                            },
                            "rr_basis": scenario,
                            "currency": currency,
                        },
                    }
                )
        state = _dict(structure.get("chart_state"))
        if state:
            facts.append(
                {
                    "fact_id": "chart:structure:state",
                    "fact_type": "chart_state",
                    "as_of_date": str(structure.get("as_of_date") or ""),
                    "source": "deterministic_ohlcv_structure",
                    "fields": {
                        key: state.get(key)
                        for key in (
                            "state",
                            "confidence",
                            "reasons",
                            "blocking_unknowns",
                            "user_semantics",
                        )
                        if state.get(key) not in (None, [], {})
                    },
                }
            )
    return facts


def _financial_period_label(
    period: str,
    period_type: str,
    fiscal_year: object,
    period_scope: str,
    is_cumulative: bool,
) -> str | None:
    try:
        year = int(fiscal_year) if fiscal_year is not None else int(period[:4])
    except (TypeError, ValueError):
        return None
    normalized = period_type.strip().upper()
    scope = period_scope.strip().lower()
    cumulative_scope = any(
        marker in scope for marker in ("cumulative", "half-year", "half_year", "ytd")
    )
    single_quarter_scope = scope in {"single-quarter", "single_quarter", "quarter"}
    if normalized == "Q1":
        suffix = "1분기"
    elif normalized == "Q2":
        suffix = "상반기 누적" if is_cumulative or cumulative_scope else "2분기"
    elif normalized == "H1":
        if single_quarter_scope and not is_cumulative:
            suffix = "2분기"
        elif is_cumulative or cumulative_scope:
            suffix = "상반기 누적"
        else:
            return None
    elif normalized == "Q3":
        suffix = "3분기 누적" if is_cumulative or cumulative_scope else "3분기"
    elif normalized == "FY":
        suffix = "연간"
    else:
        return None
    return f"{year}년 {suffix}"


def _valuation_forward_period_status(value: str | None) -> str:
    normalized = str(value or "").strip()
    if not normalized:
        return "unknown"
    try:
        date.fromisoformat(normalized)
    except ValueError:
        return "provider_defined"
    return "exact"


def _fact_catalog(
    assessment: ThesisAssessment,
    evidence: list[dict[str, object]],
    valuation: dict[str, object],
    price: dict[str, object],
    chart: dict[str, object],
    monitoring_state: dict[str, object],
) -> list[dict[str, object]]:
    facts = [fact for item in evidence if (fact := canonical_event_fact(item))]
    financial_quality = _dict(valuation.get("financial_quality"))
    currency = str(valuation.get("currency") or "unknown")
    financial_currency_value = valuation.get("financial_currency")
    financial_currency = (
        str(financial_currency_value).strip()
        if financial_currency_value is not None
        else ""
    ) or "unknown"
    period = str(valuation.get("latest_earnings_period") or "latest")
    identity_state = str(valuation.get("security_identity_state") or IDENTITY_UNKNOWN)
    identity_provenance = _dict(valuation.get("security_identity_provenance"))
    identity_evidence = _dict(identity_provenance.get("evidence"))
    identity_field_provenance = _dict(identity_provenance.get("field_provenance"))
    ratio = valuation.get("security_identity_selected_adr_ratio")
    if not isinstance(ratio, (int, float)):
        ratio = identity_evidence.get("adr_ratio")
    ratio_direction = valuation.get("security_identity_adr_ratio_direction")
    if not ratio_direction:
        ratio_direction = identity_evidence.get("adr_ratio_direction")
    ratio_provenance = _dict(identity_field_provenance.get("adr_ratio"))
    direction_provenance = _dict(
        identity_field_provenance.get("adr_ratio_direction")
    )
    ratio_verified = bool(
        identity_state == VERIFIED_DEPOSITARY
        and isinstance(ratio, (int, float))
        and float(ratio) > 0
        and ratio_direction
        and all(
            item.get("verification_status") == "verified"
            and item.get("source_tier") == "tier_a_authoritative"
            and (item.get("source_url") or item.get("source_reference"))
            for item in (ratio_provenance, direction_provenance)
        )
    )
    facts.append(
        {
            "fact_id": "security_identity:current",
            "fact_type": "security_identity",
            "as_of_date": str(valuation.get("security_identity_as_of") or ""),
            "source": str(
                valuation.get("security_identity_source_provenance")
                or "deterministic_security_identity"
            ),
            "fields": {
                "identity_state": identity_state,
                "verification_status": valuation.get(
                    "security_identity_verification_status"
                ),
                "conflict_reasons": valuation.get(
                    "security_identity_conflict_reasons", []
                ),
                "resolved_conflict_reasons": valuation.get(
                    "security_identity_resolved_conflict_reasons", []
                ),
                "source_tier": valuation.get(
                    "security_identity_verification_source_tier"
                )
                or valuation.get("security_identity_source_tier"),
                "identity_record_source_tier": valuation.get(
                    "security_identity_source_tier"
                ),
                "identity_provenance": valuation.get(
                    "security_identity_provenance", {}
                ),
                "eligibility_decision": valuation.get(
                    "security_identity_eligibility_decision"
                ),
                "decision_version": valuation.get(
                    "security_identity_decision_version"
                ),
                "selected_issuer_type": valuation.get(
                    "security_identity_selected_issuer_type"
                )
                or valuation.get("resolved_issuer_type"),
                "selected_security_type": valuation.get(
                    "security_identity_selected_security_type"
                )
                or valuation.get("resolved_security_type"),
                "depositary_evidence_present": valuation.get(
                    "security_identity_depositary_evidence_present"
                ),
                "depositary_ratio": valuation.get(
                    "security_identity_selected_adr_ratio"
                ) if not ratio_verified else ratio,
                "depositary_ratio_source": valuation.get(
                    "security_identity_selected_adr_ratio_source"
                ) if not ratio_verified else (
                    ratio_provenance.get("source_url")
                    or ratio_provenance.get("source_reference")
                ),
                "depositary_ratio_direction": valuation.get(
                    "security_identity_adr_ratio_direction"
                ) if not ratio_verified else ratio_direction,
            },
            "prose_eligible": True,
            "interpretation_eligible": True,
            "numeric_registry_eligible": False,
        }
    )
    basis_statuses = {
        metric: valuation.get(field)
        for metric, field in (
            ("trailing_pe", "trailing_pe_basis_status"),
            ("price_to_book", "price_to_book_basis_status"),
            ("forward_pe", "forward_pe_basis_status"),
            ("forward_price_to_book", "forward_price_to_book_basis_status"),
        )
        if valuation.get(field) is not None
    }
    basis_quality = _dict(financial_quality.get("fields"))
    facts.append(
        {
            "fact_id": "security_basis:current",
            "fact_type": "security_basis",
            "as_of_date": str(valuation.get("price_as_of") or ""),
            "source": "deterministic_per_security_basis",
            "fields": {
                "security_identity_state": identity_state,
                "depositary_ratio_state": (
                    "verified"
                    if ratio_verified
                    else "not_applicable"
                    if identity_state == VERIFIED_NON_DEPOSITARY
                    else "unknown"
                ),
                "valuation_basis_statuses": basis_statuses,
                "price_currency": valuation.get("currency"),
                "earnings_per_share_currency": valuation.get("eps_currency"),
                "book_value_currency": valuation.get("book_currency"),
                "earnings_per_share_security_basis": valuation.get(
                    "eps_security_basis"
                ),
                "eligibility_decision": valuation.get(
                    "security_identity_eligibility_decision"
                ),
                "field_eligibility": {
                    field: {
                        key: quality.get(key)
                        for key in (
                            "state",
                            "prose_eligible",
                            "denial_reason",
                            "lineage_verification_status",
                        )
                    }
                    for field, quality in basis_quality.items()
                    if isinstance(quality, dict)
                    and field
                    in {
                        "ttm_eps",
                        "trailing_pe",
                        "forward_eps",
                        "forward_pe",
                        "bvps",
                        "price_to_book",
                        "forward_bvps",
                        "forward_price_to_book",
                    }
                },
            },
            "prose_eligible": True,
            "interpretation_eligible": True,
            "numeric_registry_eligible": False,
        }
    )
    current_monitoring = _dict(monitoring_state.get("current"))
    previous_monitoring = _dict(monitoring_state.get("previous"))
    monitoring_delta = _dict(monitoring_state.get("delta"))
    current_confirmation = _dict(
        _dict(_dict(current_monitoring.get("price_structure")).get("registered_rule_state")).get(
            "confirmation"
        )
    )
    previous_confirmation = _dict(
        _dict(_dict(previous_monitoring.get("price_structure")).get("registered_rule_state")).get(
            "confirmation"
        )
    )
    confirmation_transition = monitoring_delta.get("confirmation_transition")
    if confirmation_transition:
        facts.append(
            {
                "fact_id": "monitoring:confirmation_transition",
                "fact_type": "monitoring_transition",
                "as_of_date": str(
                    _dict(current_monitoring.get("price_structure")).get("as_of_date")
                    or assessment.assessment_date.isoformat()
                ),
                "source": "deterministic_monitoring_state",
                "fields": {
                    "previous_state": previous_confirmation.get("state"),
                    "current_state": current_confirmation.get("state"),
                    "transition": confirmation_transition,
                },
                "prose_eligible": True,
                "interpretation_eligible": True,
                "numeric_registry_eligible": False,
            }
        )
    rr_previous = _number(monitoring_delta.get("rr_previous"))
    rr_current = _number(monitoring_delta.get("rr_current"))
    if rr_previous is not None and rr_current is not None:
        facts.append(
            {
                "fact_id": "monitoring:risk_reward_transition",
                "fact_type": "monitoring_metric_transition",
                "as_of_date": str(
                    _dict(current_monitoring.get("price_structure")).get("as_of_date")
                    or assessment.assessment_date.isoformat()
                ),
                "source": "deterministic_monitoring_state",
                "fields": {
                    "previous_ratio": rr_previous,
                    "current_ratio": rr_current,
                    "change_state": monitoring_delta.get("rr_change"),
                },
                "prose_eligible": True,
                "interpretation_eligible": True,
            }
        )
    if financial_quality:
        field_states = {
            str(item.get("state") or "unknown")
            for item in _dict(financial_quality.get("fields")).values()
            if isinstance(item, dict)
        }
        aggregate_state = (
            "denied"
            if "denied" in field_states
            else "caution_usable"
            if "caution_usable" in field_states
            else "verified_usable"
            if "verified_usable" in field_states
            else "unknown"
        )
        source_snapshot = _dict(financial_quality.get("source_snapshot"))
        facts.append(
            {
                "fact_id": f"financial_quality:{period}",
                "fact_type": "financial_quality",
                "as_of_date": period,
                "source": "deterministic_financial_validation",
                "fields": {
                    "state": aggregate_state,
                    "reason_codes": financial_quality.get(
                        "quality_reason_codes", []
                    ),
                    "source_type": source_snapshot.get("source_type"),
                    "source_period": source_snapshot.get("period"),
                    "decision_version": financial_quality.get("decision_version"),
                },
                "prose_eligible": True,
            }
        )
        valuation_coherence = _dict(financial_quality.get("valuation_coherence"))
        if valuation_coherence:
            facts.append(
                {
                    "fact_id": "valuation:book_quality",
                    "fact_type": "valuation_quality",
                    "as_of_date": str(valuation.get("price_as_of") or ""),
                    "source": "deterministic_valuation_coherence",
                    "fields": valuation_coherence,
                    "prose_eligible": True,
                    "interpretation_eligible": True,
                    "numeric_registry_eligible": False,
                }
            )
    earnings_period_type = str(
        valuation.get("latest_earnings_period_type")
        or _dict(financial_quality.get("source_snapshot")).get("period_type")
        or ""
    )
    earnings_fiscal_year = valuation.get("latest_earnings_fiscal_year") or _dict(
        financial_quality.get("source_snapshot")
    ).get("fiscal_year")
    earnings_period_scope = str(
        valuation.get("latest_earnings_period_scope")
        or _dict(financial_quality.get("source_snapshot")).get("period_scope")
        or ""
    )
    earnings_is_cumulative = bool(
        valuation.get("latest_earnings_is_cumulative")
        or _dict(financial_quality.get("source_snapshot")).get("is_cumulative")
    )
    direct_quality = _dict(financial_quality.get("fields"))
    field_period_labels = {
        field: financial_amount_period_label(_dict(quality))
        for field, quality in direct_quality.items()
        if field.startswith("latest_") and isinstance(quality, dict)
    }
    field_statement_basis = {
        field: {
            "contract": _dict(quality).get("statement_basis_contract"),
            "state": _dict(quality).get("statement_basis_state"),
            "basis": _dict(quality).get("consolidated_separate_basis"),
            "source": _dict(quality).get("statement_basis_source"),
        }
        for field, quality in direct_quality.items()
        if field.startswith("latest_") and isinstance(quality, dict)
    }
    period_label = field_period_labels.get("latest_operating_income") or field_period_labels.get(
        "latest_revenue"
    )
    direct_financial_providers = {
        str(_dict(value).get("provider") or "")
        for key, value in direct_quality.items()
        if key.startswith("latest_") and isinstance(value, dict)
    }
    if period_label is None and "opendart" not in direct_financial_providers:
        period_label = _financial_period_label(
            period,
            earnings_period_type,
            earnings_fiscal_year,
            earnings_period_scope,
            earnings_is_cumulative,
        )
    earnings_fields: dict[str, object] = {
        "period": period,
        "period_type": earnings_period_type or None,
        "period_label": period_label,
        "field_period_labels": field_period_labels,
        "field_statement_basis": field_statement_basis,
        "financial_period_required": True,
        "preliminary": bool(valuation.get("earnings_context_is_preliminary")),
    }
    earnings_values = {
        "revenue": "latest_revenue",
        "operating_income": "latest_operating_income",
    }
    earnings_field_quality: dict[str, object] = {}
    for target, source in earnings_values.items():
        if (value := valuation.get(source)) is not None:
            earnings_fields[target] = {
                "value": value,
                "currency": financial_currency,
            }
            if quality := field_quality(financial_quality, source):
                earnings_field_quality[f"fields.{target}.value"] = quality
    for target, source in (
        ("operating_margin_pct", "latest_operating_margin"),
        ("revenue_qoq_pct", "latest_revenue_qoq"),
        ("revenue_yoy_pct", "latest_revenue_yoy"),
        ("operating_income_qoq_pct", "latest_operating_income_qoq"),
        ("operating_income_yoy_pct", "latest_operating_income_yoy"),
    ):
        if (value := valuation.get(source)) is not None:
            earnings_fields[target] = value
            if quality := field_quality(financial_quality, source):
                earnings_field_quality[f"fields.{target}"] = quality
    if len(earnings_fields) > 2:
        earnings_quality_records = [
            _dict(item) for item in earnings_field_quality.values()
        ]
        earnings_interpretation_eligible = bool(
            earnings_quality_records
            and all(
                item.get("state") in {"verified_usable", "caution_usable"}
                and item.get("prose_eligible") is True
                for item in earnings_quality_records
            )
        )
        facts.append(
            {
                "fact_id": f"earnings:{period}",
                "fact_type": "earnings",
                "as_of_date": period,
                "fields": earnings_fields,
                "financial_quality": financial_quality,
                "field_quality": earnings_field_quality,
                "prose_eligible": any(
                    _dict(item).get("prose_eligible") is True
                    for item in earnings_field_quality.values()
                ),
                "interpretation_eligible": earnings_interpretation_eligible,
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
        valuation_field_quality = {
            f"fields.{field}": quality
            for field in (
                "ttm_eps",
                "trailing_pe",
                "forward_eps",
                "forward_pe",
                "bvps",
                "price_to_book",
                "forward_bvps",
                "forward_price_to_book",
                "historical_pe_statistics.current_value",
                "historical_pe_statistics.current_percentile",
                "historical_pb_statistics.current_value",
                "historical_pb_statistics.current_percentile",
            )
            if (quality := field_quality(financial_quality, field))
        }
        valuation_quality_records = [
            _dict(item) for item in valuation_field_quality.values()
        ]
        valuation_interpretation_eligible = bool(
            not valuation_quality_records
            or all(
                item.get("state") in {"verified_usable", "caution_usable"}
                and item.get("prose_eligible") is True
                for item in valuation_quality_records
            )
        )
        facts.append(
            {
                "fact_id": "valuation:current",
                "fact_type": "valuation",
                "as_of_date": str(valuation.get("price_as_of") or ""),
                "fields": valuation_fields,
                "financial_quality": financial_quality,
                "field_quality": valuation_field_quality,
                "interpretation_eligible": valuation_interpretation_eligible,
                "interpretation_denial_reason": (
                    None
                    if valuation_interpretation_eligible
                    else "mixed_financial_lineage_requires_homogeneous_fact"
                ),
            }
        )

        def add_interpretation_fact(
            fact_id: str,
            field_names: tuple[str, ...],
        ) -> None:
            fields = {
                field: valuation_fields[field]
                for field in field_names
                if field in valuation_fields
            }
            if not fields:
                return
            quality_by_path = {
                path: quality
                for path, quality in valuation_field_quality.items()
                if any(
                    path == f"fields.{field}"
                    or path.startswith(f"fields.{field}.")
                    for field in field_names
                )
            }
            quality_records = [_dict(item) for item in quality_by_path.values()]
            eligible = bool(
                quality_records
                and all(
                    item.get("state") in {"verified_usable", "caution_usable"}
                    and item.get("prose_eligible") is True
                    for item in quality_records
                )
            )
            facts.append(
                {
                    "fact_id": fact_id,
                    "fact_type": "valuation_interpretation",
                    "as_of_date": str(valuation.get("price_as_of") or ""),
                    "fields": fields,
                    "field_quality": quality_by_path,
                    "prose_eligible": eligible,
                    "interpretation_eligible": eligible,
                    "interpretation_denial_reason": (
                        None if eligible else "financial_lineage_not_prose_eligible"
                    ),
                    "numeric_registry_eligible": False,
                }
            )

        add_interpretation_fact(
            "valuation:trailing_earnings",
            ("ttm_eps", "trailing_pe"),
        )
        forward_pe_fact_id = (
            "valuation:consensus_forward_earnings"
            if valuation.get("forward_pe_source") == "consensus_forward"
            else "valuation:modeled_forward_earnings"
            if valuation.get("forward_pe_source") == "modeled_forward"
            else "valuation:forward_earnings_unknown"
        )
        add_interpretation_fact(
            forward_pe_fact_id,
            ("forward_eps", "forward_pe"),
        )
        add_interpretation_fact(
            "valuation:book",
            ("bvps", "price_to_book"),
        )
        add_interpretation_fact(
            "valuation:book_value",
            ("bvps",),
        )
        add_interpretation_fact(
            "valuation:current_pbr",
            ("price_to_book",),
        )
        forward_book_fact_id = (
            "valuation:modeled_forward_book"
            if valuation.get("forward_price_to_book_source") == "modeled_forward"
            else "valuation:consensus_forward_book"
            if valuation.get("forward_price_to_book_source") == "consensus_forward"
            else "valuation:forward_book_unknown"
        )
        add_interpretation_fact(
            forward_book_fact_id,
            ("forward_bvps", "forward_price_to_book"),
        )
        add_interpretation_fact(
            "valuation:historical_pe",
            ("historical_pe_statistics",),
        )
        add_interpretation_fact(
            "valuation:historical_pb",
            ("historical_pb_statistics",),
        )
        trailing_pe = _number(valuation.get("trailing_pe"))
        forward_pe = _number(valuation.get("forward_pe"))
        if trailing_pe is not None and forward_pe is not None:
            trailing_quality = _dict(valuation_field_quality.get("fields.trailing_pe"))
            forward_quality = _dict(valuation_field_quality.get("fields.forward_pe"))
            forward_source = str(valuation.get("forward_pe_source") or "unknown")
            trailing_basis = str(valuation.get("trailing_pe_basis_status") or "")
            forward_basis_status = str(valuation.get("forward_pe_basis_status") or "")
            price_basis = str(valuation.get("price_basis") or "")
            price_as_of = str(valuation.get("price_as_of") or "")
            trailing_period = str(
                valuation.get("trailing_pe_denominator_period_end") or ""
            )
            forward_period = str(valuation.get("forward_pe_input_period") or "")
            trailing_security_basis = str(
                valuation.get("eps_security_basis") or "unknown"
            )
            comparable_statuses = {
                "directly_comparable",
                "normalized_to_current_security",
            }
            provider_native_consensus = bool(
                forward_source == "consensus_forward"
                and identity_state == VERIFIED_NON_DEPOSITARY
                and forward_basis_status == "not_applicable"
            )
            reasons: list[str] = []
            if trailing_quality.get("prose_eligible") is not True:
                reasons.append("trailing_multiple_not_prose_eligible")
            if forward_quality.get("prose_eligible") is not True:
                reasons.append("forward_multiple_not_prose_eligible")
            if trailing_basis not in comparable_statuses:
                reasons.append("trailing_security_basis_unverified")
            if (
                forward_basis_status not in comparable_statuses
                and not provider_native_consensus
            ):
                reasons.append("forward_security_basis_unverified")
            if identity_state not in {
                VERIFIED_DEPOSITARY,
                VERIFIED_NON_DEPOSITARY,
            }:
                reasons.append("security_identity_unverified")
            if not currency:
                reasons.append("price_currency_unverified")
            if price_basis in {"", "unavailable", "unknown"} or not price_as_of:
                reasons.append("price_basis_unverified")
            if not trailing_period:
                reasons.append("trailing_denominator_period_unverified")
            if not forward_period:
                reasons.append("forward_denominator_period_unverified")
            if trailing_security_basis != "current_security":
                reasons.append("trailing_share_basis_unverified")
            forward_period_status = _valuation_forward_period_status(
                forward_period
            )
            basis_comparable = not reasons
            multiple_direction = (
                "forward_higher"
                if forward_pe > trailing_pe
                else "forward_lower"
                if forward_pe < trailing_pe
                else "unchanged"
            )
            denominator_direction = (
                "forward_denominator_lower"
                if forward_pe > trailing_pe
                else "forward_denominator_higher"
                if forward_pe < trailing_pe
                else "unchanged"
            )
            facts.append(
                {
                    "fact_id": "valuation:multiple_relation",
                    "fact_type": "valuation_multiple_relation",
                    "as_of_date": str(valuation.get("price_as_of") or ""),
                    "source": "deterministic_valuation_relation",
                    "fields": {
                        "trailing_metric": "PER",
                        "trailing_value": trailing_pe,
                        "forward_metric": "fPER",
                        "forward_value": forward_pe,
                        "forward_source": forward_source,
                        "security_identity_state": identity_state,
                        "price_currency": currency,
                        "price_basis": price_basis or None,
                        "price_as_of": price_as_of or None,
                        "trailing_share_basis": trailing_security_basis,
                        "forward_share_basis": (
                            "current_security_provider_contract"
                            if provider_native_consensus
                            else trailing_security_basis
                        ),
                        "trailing_denominator_period": trailing_period or None,
                        "forward_denominator_period": forward_period or None,
                        "forward_period_status": forward_period_status,
                        "security_basis": identity_state,
                        "currency_basis": currency or None,
                        "trailing_basis_status": trailing_basis or None,
                        "forward_basis_status": forward_basis_status or None,
                        "basis_comparable": basis_comparable,
                        "multiple_direction": multiple_direction,
                        "denominator_direction": denominator_direction,
                        "interpretation_eligibility": (
                            "eligible" if basis_comparable else "unknown"
                        ),
                        "reason_codes": reasons,
                    },
                    "prose_eligible": True,
                    "interpretation_eligible": basis_comparable,
                    "numeric_registry_eligible": False,
                }
            )
    peer = _dict(_dict(monitoring_state.get("current")).get("peer_valuation"))
    peer_metrics = _dict(peer.get("metrics"))
    peer_fields: dict[str, object] = {
        "peer_group": peer.get("peer_group"),
        "peer_group_version": peer.get("peer_group_version"),
        "sample_quality": peer.get("sample_quality"),
    }
    for metric, prefix in (
        ("trailing_pe", "pe"),
        ("price_to_book", "pb"),
    ):
        value = _dict(peer_metrics.get(metric))
        if value.get("available") is not True:
            continue
        for source, target in (
            ("median", f"{prefix}_median"),
            ("mean", f"{prefix}_mean"),
            ("percentile_25", f"{prefix}_percentile_25"),
            ("percentile_75", f"{prefix}_percentile_75"),
            ("sample_count", f"{prefix}_sample_count"),
            ("company_vs_median_pct", f"company_{prefix}_vs_median_pct"),
        ):
            if value.get(source) is not None:
                peer_fields[target] = value[source]
    if any(key.endswith(("_median", "_mean")) for key in peer_fields):
        facts.append(
            {
                "fact_id": "valuation:peer",
                "fact_type": "peer_valuation",
                "as_of_date": str(peer.get("as_of_date") or ""),
                "source": str(
                    peer.get("provider")
                    or "validated_active_monitoring_assessments"
                ),
                "fields": peer_fields,
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


def _state_grounding_requirements(
    monitoring_state: dict[str, object],
    facts: list[dict[str, object]],
) -> dict[str, list[dict[str, object]]]:
    current = _dict(monitoring_state.get("current"))
    structure = _dict(current.get("price_structure"))
    price_requirements: list[dict[str, object]] = []
    if _number(structure.get("current_price")) is not None:
        price_requirements.append(
            {
                "fact_id": "price:current",
                "field_paths": ["fields.current_price"],
                "reason": "current_price",
            }
        )

    def matching_zone_fact(
        state_key: str,
        fact_types: set[str],
    ) -> dict[str, object] | None:
        zone = _dict(structure.get(state_key))
        if zone.get("available") is not True:
            return None
        for fact in facts:
            if str(fact.get("fact_type") or "") not in fact_types:
                continue
            fields = _dict(fact.get("fields"))
            if (
                _number(fields.get("zone_low")) == _number(zone.get("zone_low"))
                and _number(fields.get("zone_high")) == _number(zone.get("zone_high"))
            ):
                return {
                    "fact_id": fact.get("fact_id"),
                    "field_paths": ["fields.zone_low", "fields.zone_high"],
                    "reason": state_key,
                }
        return None

    for requirement in (
        matching_zone_fact(
            "active_support", {"chart_support_zone", "chart_active_zone"}
        ),
        matching_zone_fact("active_resistance", {"chart_resistance_zone"}),
    ):
        if requirement is not None:
            price_requirements.append(requirement)
    risk_reward = _dict(structure.get("risk_reward"))
    if (
        risk_reward.get("available") is True
        and _dict(risk_reward.get("current_price")).get("ratio") is not None
    ):
        price_requirements.append(
            {
                "fact_id": "chart:structure:risk_reward:current_price",
                "field_paths": ["fields.ratio"],
                "reason": "current_price_risk_reward",
            }
        )
    peer = _dict(current.get("peer_valuation"))
    peer_metrics = _dict(peer.get("metrics"))
    peer_field_paths: list[str] = []
    for metric, prefix in (
        ("trailing_pe", "pe"),
        ("price_to_book", "pb"),
    ):
        if _dict(peer_metrics.get(metric)).get("available") is True:
            peer_field_paths.extend(
                [
                    f"fields.{prefix}_median",
                    f"fields.company_{prefix}_vs_median_pct",
                ]
            )
    valuation_requirements = (
        [
            {
                "fact_id": "valuation:peer",
                "field_paths": peer_field_paths,
                "reason": "sufficient_peer_valuation",
            }
        ]
        if peer_field_paths
        and any(fact.get("fact_id") == "valuation:peer" for fact in facts)
        else []
    )
    return {
        "price": price_requirements,
        "valuation": valuation_requirements,
    }


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
    valuation = _valuation_payload(session, assessment)
    price = _price_payload(assessment)
    previous = _previous_assessment(session, assessment)
    chart = _chart_payload(assessment, thesis, previous)
    monitoring_state = _public_value(
        _dict(_dict(assessment.price_context).get("monitoring_state"))
    )
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
        "monitoring_state": monitoring_state,
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
    facts = _fact_catalog(
        assessment,
        evidence,
        valuation,
        price,
        chart,
        monitoring_state,
    )
    stock["fact_catalog"] = facts
    stock["numeric_registry"] = _numeric_registry(facts)
    stock["typed_valuation_interpretation_contract"] = (
        TYPED_VALUATION_CONTRACT
    )
    stock["state_grounding_requirements"] = _state_grounding_requirements(
        monitoring_state,
        facts,
    )
    return stock


def _market_packet(
    session: Session,
    run_date: date,
    market: AIReviewMarket,
    stocks: list[dict[str, object]],
) -> dict[str, object]:
    digest = build_daily_digest(session, run_date, market_scope=market)
    briefing = session.exec(
        select(MacroBriefing).where(
            MacroBriefing.briefing_date == run_date,
            MacroBriefing.briefing_type == "morning",
        )
    ).first()
    tickers = [str(stock["ticker"]) for stock in stocks]
    impact_rows = (
        session.exec(
            select(ThesisMacroImpact).where(
                ThesisMacroImpact.assessment_date == run_date,
                ThesisMacroImpact.ticker.in_(tickers),
            )
        ).all()
        if tickers
        else []
    )
    intelligence = build_market_intelligence(
        briefing,
        run_date,
        stocks,
        [
            {
                "ticker": impact.ticker,
                "direction": impact.direction,
                "channels": _public_value(_list(impact.channels)),
                "evidence": _public_value(_list(impact.evidence)),
            }
            for impact in impact_rows
        ],
        market=market,
    )
    market_facts = list(intelligence["fact_catalog"])
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
    night_fact_ids = [
        f"market:night_futures:{index}"
        for index, _item in enumerate(night_futures, start=1)
    ]
    briefing_market = (
        _dict(_json(briefing.market_summary, {})) if briefing is not None else {}
    )
    gate = _dict(briefing_market.get("night_futures_gate"))
    night_by_series = {
        str(item.get("series_code")): item
        for item in night_futures
        if isinstance(item, dict) and item.get("series_code")
    }
    fact_id_by_series = {
        str(item.get("series_code")): f"market:night_futures:{index}"
        for index, item in enumerate(night_futures, start=1)
        if isinstance(item, dict) and item.get("series_code")
    }
    night_audit = {
        "expected_session": gate.get("expected_session"),
        "query_time": gate.get("last_query_at") or gate.get("first_query_at"),
        "products": [
            {
                "series_code": series_code,
                "query_time": gate.get(
                    "KOSPI200_first_available_at"
                    if series_code == "KRX_KOSPI200_NIGHT_FUT"
                    else "KOSDAQ150_first_available_at"
                ),
                "source_session": (
                    night_by_series.get(series_code, {}).get("session_date")
                ),
                "freshness": (
                    "fresh" if series_code in night_by_series else "unavailable"
                ),
                "verified_contract": series_code in night_by_series,
                "selected_for_market_packet": series_code in night_by_series,
                "market_packet_included": series_code in night_by_series,
                "ai_fact_catalog_included": series_code in fact_id_by_series,
                "fact_id": fact_id_by_series.get(series_code),
                "ai_facts_used": False,
                "rendered_in_telegram": False,
            }
            for series_code in NIGHT_FUTURES_SERIES
        ],
    }
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
    macro_theses = _public_value(_list(briefing.macro_theses)) if briefing else []
    return {
        "session": {
            "market": market,
            "assessment_date": run_date.isoformat(),
            "market_session": digest.macro.market_session,
            "assessment_state": digest.macro.assessment_state,
        },
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
        "key_change_fact_ids": intelligence["key_change_fact_ids"],
        "required_market_fact_ids": night_fact_ids if market == "us" else [],
        "integrated_view": _clean_texts(digest.macro.integrated_view),
        "market_assumptions": _clean_texts(digest.macro.market_assumptions),
        "market_theses": macro_theses,
        "coverage": intelligence["coverage"],
        "portfolio_exposure_groups": intelligence["portfolio_exposure_groups"],
        "transmission_candidates": intelligence["transmission_candidates"],
        "market_unknowns": intelligence["unknowns"],
        "night_futures": night_futures,
        "night_futures_cautions": list(digest.night_futures.cautions),
        "night_futures_audit": night_audit,
        "fx": fx_items,
        "data_cautions": _clean_texts(digest.data_quality.items),
        "fact_catalog": market_facts,
        "numeric_registry": _numeric_registry(market_facts),
        "knowledge_routing": {
            "required_frameworks": [*_CORE_FRAMEWORKS, "macro_transmission"],
            "knowledge_index": "references/knowledge-index.md",
        },
        "_stock_transmissions": intelligence["stock_transmissions"],
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
    market_context = _market_packet(session, run_date, market, stocks)
    stock_transmissions = market_context.pop("_stock_transmissions", {})
    market_facts_by_id = {
        str(fact["fact_id"]): fact
        for fact in market_context["fact_catalog"]
        if isinstance(fact, dict) and fact.get("fact_id")
    }
    for stock in stocks:
        links = (
            stock_transmissions.get(str(stock["ticker"]), [])
            if isinstance(stock_transmissions, dict)
            else []
        )
        stock["market_transmission"] = {
            "relevant_market_facts": links,
            "not_fundamental_confirmation": bool(links),
        }
        relevant_ids = {
            str(link.get("fact_id"))
            for link in links
            if isinstance(link, dict) and link.get("fact_id")
        }
        stock["fact_catalog"].extend(
            market_facts_by_id[fact_id]
            for fact_id in sorted(relevant_ids)
            if fact_id in market_facts_by_id
        )
        stock["numeric_registry"] = _numeric_registry(stock["fact_catalog"])
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
        "output_schema_version": OUTPUT_SCHEMA_VERSION,
        "analysis_policy_version": ANALYSIS_POLICY_VERSION,
        "structure_algorithm_version": ALGORITHM_VERSION,
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
                **{
                    f"portfolio_transmission[{index}].text": item.text
                    for index, item in enumerate(
                        getattr(review, "portfolio_transmission", [])
                    )
                },
                **{
                    f"next_checks[{index}].text": item.text
                    for index, item in enumerate(getattr(review, "next_checks", []))
                },
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
    if unit == "TWD":
        return "nt$" in lowered or "twd" in lowered or "대만달러" in usage
    if unit == "shares":
        return "주" in usage or "share" in lowered
    if unit == "x":
        return "배" in usage or "multiple" in lowered
    if unit == "points":
        return "%" not in usage and any(
            marker in lowered for marker in ("pt", "point", "포인트", "선물")
        )
    if unit == "bp":
        return "bp" in lowered or "베이시스포인트" in usage
    if unit == "USD_per_barrel":
        return (
            ("$" in usage or "usd" in lowered or "달러" in usage)
            and ("bbl" in lowered or "배럴" in usage)
        )
    if unit == "index":
        return "%" not in usage
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
        expected_scope = str(source.get("scope") or "")
        allowed_scopes = (
            {"market", "both"}
            if prefix == "market_review"
            else {"stock", "both"}
        )
        if expected_scope not in allowed_scopes:
            errors.append(
                f"{prefix}:numeric_semantic_scope_mismatch:"
                f"{claim.fact_id}:{claim.field_path}:{expected_scope}"
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
        if label_mismatch := canonical_numeric_label_mismatch(source, claim.usage):
            errors.append(
                f"{prefix}:numeric_{label_mismatch}_label_mismatch:"
                f"{claim.fact_id}:{claim.field_path}:{claim.text_ref}"
            )
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
        if any(
            redundant_numeric_label_before(target, start, source)
            for start, _ in spans
        ):
            errors.append(
                f"{prefix}:numeric_repeated_bound_label:"
                f"{claim.fact_id}:{claim.field_path}:{claim.text_ref}"
            )
            claim_is_valid = False
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


_CONSENSUS_LANGUAGE = re.compile(
    r"(?:시장|애널리스트)\s*(?:컨센서스|예상)|\bconsensus\b",
    re.IGNORECASE,
)
_MODELED_LANGUAGE = re.compile(
    r"내부\s*(?:추정|모델)|\bfy1\s*model\b|\bmodeled\b",
    re.IGNORECASE,
)
_FORWARD_PE_LANGUAGE = re.compile(
    r"(?:fper|선행\s*per|forward\s*pe|eps)",
    re.IGNORECASE,
)
_FORWARD_PB_LANGUAGE = re.compile(
    r"(?:fpbr|선행\s*pbr|forward\s*pbr|bvps)",
    re.IGNORECASE,
)
_FORWARD_SOURCE_METRIC_MAX_GAP = 12


def _span_gap(left: re.Match[str], right: re.Match[str]) -> int:
    if left.end() <= right.start():
        return right.start() - left.end()
    if right.end() <= left.start():
        return left.start() - right.end()
    return 0


def _metric_local_forward_sources(text: str) -> dict[str, set[str]]:
    sources: dict[str, set[str]] = {"pe": set(), "pbr": set()}
    for sentence in re.split(r"(?<=[.!?])\s+|\n+", text):
        metrics = [
            *(("pe", match) for match in _FORWARD_PE_LANGUAGE.finditer(sentence)),
            *(("pbr", match) for match in _FORWARD_PB_LANGUAGE.finditer(sentence)),
        ]
        source_matches = [
            *(("consensus_forward", match) for match in _CONSENSUS_LANGUAGE.finditer(sentence)),
            *(("modeled_forward", match) for match in _MODELED_LANGUAGE.finditer(sentence)),
        ]
        for source, source_match in source_matches:
            candidates = sorted(
                (_span_gap(source_match, metric_match), family)
                for family, metric_match in metrics
            )
            if not candidates or candidates[0][0] > _FORWARD_SOURCE_METRIC_MAX_GAP:
                continue
            nearest_gap = candidates[0][0]
            nearest_families = {
                family for gap, family in candidates if gap == nearest_gap
            }
            if len(nearest_families) == 1:
                sources[nearest_families.pop()].add(source)
    return sources


def _forward_source_language_errors(
    ticker: str,
    valuation: dict[str, object],
    rendered: str,
) -> list[str]:
    errors: list[str] = []
    local_sources = _metric_local_forward_sources(rendered)
    contracts = (
        ("forward_pe_source", "pe", ""),
        ("forward_price_to_book_source", "pbr", "_pbr"),
    )
    for source_field, family, suffix in contracts:
        source = str(valuation.get(source_field) or "unavailable")
        used_sources = local_sources[family]
        uses_consensus = "consensus_forward" in used_sources
        uses_modeled = "modeled_forward" in used_sources
        if source == "modeled_forward" and uses_consensus:
            errors.append(f"{ticker}:modeled_forward{suffix}_called_consensus")
        elif source == "consensus_forward" and uses_modeled:
            errors.append(f"{ticker}:consensus_forward{suffix}_called_modeled")
        elif source not in {"modeled_forward", "consensus_forward"}:
            if uses_consensus or uses_modeled:
                errors.append(f"{ticker}:unknown_forward{suffix}_source_labeled")
    return errors


_CONFIRMATION_STATES = (
    "retest_in_progress",
    "failed_breakout",
    "holding_above",
    "retest_held",
    "not_reached",
    "crossed",
)
_CONFIRMATION_STATE_ALIASES = {
    "retest_in_progress": "retest_in_progress",
    "재시험 진행": "retest_in_progress",
    "retest in progress": "retest_in_progress",
    "failed_breakout": "failed_breakout",
    "돌파 실패": "failed_breakout",
    "failed breakout": "failed_breakout",
    "holding_above": "holding_above",
    "holding": "holding_above",
    "돌파 후 유지": "holding_above",
    "상단 유지": "holding_above",
    "holding above": "holding_above",
    "retest_held": "retest_held",
    "재시험 유지": "retest_held",
    "retest held": "retest_held",
    "not_reached": "not_reached",
    "미도달": "not_reached",
    "not reached": "not_reached",
    "crossed": "crossed",
    "돌파 확인": "crossed",
}
_CONFIRMATION_STATE_TEXT = "|".join(
    re.escape(value)
    for value in sorted(_CONFIRMATION_STATE_ALIASES, key=len, reverse=True)
)
_CONFIRMATION_CANONICAL_TRANSITION = re.compile(
    rf"\b(?P<previous>{'|'.join(_CONFIRMATION_STATES)})_to_"
    rf"(?P<current>{'|'.join(_CONFIRMATION_STATES)})\b",
    re.IGNORECASE,
)
_CONFIRMATION_FROM_TO = re.compile(
    rf"(?P<previous>{_CONFIRMATION_STATE_TEXT})\s*(?:상태)?에서\s*"
    rf"(?P<current>{_CONFIRMATION_STATE_TEXT})\s*(?:상태)?(?:로|으로)\s*"
    r"(?:바뀌|전환|변경|이동)",
    re.IGNORECASE,
)
_CONFIRMATION_TO_ONLY = re.compile(
    rf"(?P<current>{_CONFIRMATION_STATE_TEXT})\s*(?:상태)?(?:로|으로)\s*"
    r"(?:바뀌|전환|변경)",
    re.IGNORECASE,
)
_CONFIRMATION_CURRENT_ASSERTION = re.compile(
    rf"(?:현재\s*)?(?:확인\s*)?(?:상태|confirmation)\s*(?:은|는|이|가|:)\s*"
    rf"(?P<current>{_CONFIRMATION_STATE_TEXT})",
    re.IGNORECASE,
)


def _confirmation_state(value: str) -> str:
    normalized = value.strip().lower().replace("_", " ")
    return _CONFIRMATION_STATE_ALIASES.get(
        normalized,
        normalized.replace(" ", "_"),
    )


def _confirmation_transition_errors(
    ticker: str,
    monitoring_state: dict[str, object],
    review: AIStockReview,
) -> list[str]:
    current = _dict(monitoring_state.get("current"))
    previous = _dict(monitoring_state.get("previous"))
    current_state = str(
        _dict(
            _dict(_dict(current.get("price_structure")).get("registered_rule_state")).get(
                "confirmation"
            )
        ).get("state")
        or ""
    )
    previous_state = str(
        _dict(
            _dict(_dict(previous.get("price_structure")).get("registered_rule_state")).get(
                "confirmation"
            )
        ).get("state")
        or ""
    )
    transition = str(_dict(monitoring_state.get("delta")).get("confirmation_transition") or "")
    if not transition or not current_state:
        return []

    errors: list[str] = []
    for text_ref, text in _prose_fields(review).items():
        from_to_matches = list(_CONFIRMATION_FROM_TO.finditer(text))
        from_to_spans = [item.span() for item in from_to_matches]
        claims: list[tuple[str | None, str]] = []
        claims.extend(
            (match.group("previous").lower(), match.group("current").lower())
            for match in _CONFIRMATION_CANONICAL_TRANSITION.finditer(text)
        )
        claims.extend(
            (
                _confirmation_state(match.group("previous")),
                _confirmation_state(match.group("current")),
            )
            for match in from_to_matches
        )
        claims.extend(
            (None, _confirmation_state(match.group("current")))
            for match in _CONFIRMATION_TO_ONLY.finditer(text)
            if not any(
                start <= match.start() and match.end() <= end
                for start, end in from_to_spans
            )
        )
        claims.extend(
            (None, _confirmation_state(match.group("current")))
            for match in _CONFIRMATION_CURRENT_ASSERTION.finditer(text)
            if not any(
                match.start() < end and start < match.end()
                for start, end in from_to_spans
            )
        )
        for claimed_previous, claimed_current in claims:
            if claimed_previous is not None and claimed_previous != previous_state:
                errors.append(
                    f"{ticker}:confirmation_transition_previous_state_mismatch:"
                    f"{text_ref}:{claimed_previous}:{previous_state}"
                )
            if claimed_current != current_state:
                errors.append(
                    f"{ticker}:confirmation_transition_current_state_mismatch:"
                    f"{text_ref}:{claimed_current}:{current_state}"
                )
        if transition in text and transition != f"{previous_state}_to_{current_state}":
            errors.append(
                f"{ticker}:confirmation_transition_contract_mismatch:"
                f"{text_ref}:{transition}:{previous_state}_to_{current_state}"
            )
    return list(dict.fromkeys(errors))


_IDENTITY_UNVERIFIED_LANGUAGE = re.compile(
    r"(?:증권\s*(?:정체성|신원)|(?:ADR|ADS|예탁증권)\s*여부)"
    r".{0,24}(?:검증되지|미검증|미확인|불명|unknown)",
    re.IGNORECASE,
)
_IDENTITY_VERIFIED_LANGUAGE = re.compile(
    r"(?:증권\s*(?:정체성|신원)|ADR|ADS|예탁증권)"
    r".{0,24}(?:검증(?:됐|됨|완료)|확인(?:됐|됨)|verified)",
    re.IGNORECASE,
)
_NON_DEPOSITARY_CALLED_DEPOSITARY = re.compile(
    r"(?:(?:현재\s*)?(?:증권|주식|종목).{0,16}(?:ADR|ADS|예탁증권)"
    r"|(?:ADR|ADS|예탁증권).{0,12}(?:입니다|이다|임|로\s*확인))",
    re.IGNORECASE,
)
_DEPOSITARY_CALLED_COMMON_STOCK = re.compile(
    r"(?:현재\s*)?(?:증권|주식|종목)?.{0,12}(?:보통주|common\s+(?:stock|share))"
    r".{0,12}(?:입니다|이다|임|로\s*확인)?",
    re.IGNORECASE,
)
_EXPLICIT_SECURITY_TYPE_LANGUAGE = re.compile(
    r"(?:\bADR\b|\bADS\b|예탁증권|보통주|common\s+(?:stock|share)|외국\s*상장주식)",
    re.IGNORECASE,
)
_VERIFIED_DEPOSITARY_RATIO_LANGUAGE = re.compile(
    r"(?:공식|검증된|확인된).{0,12}(?:예탁)?비율|(?:예탁)?비율.{0,12}(?:검증|확인)",
    re.IGNORECASE,
)
_US_KR_SUPPLY_HORIZON_LANGUAGE = re.compile(
    r"(?:\b(?:1|5|20)\s*일(?:간)?\b.{0,24}(?:투자주체|외국인|기관|수급|순매수|순매도)"
    r"|당일.{0,8}단기.{0,8}중기.{0,16}(?:투자주체|수급|순매수|순매도))",
    re.IGNORECASE,
)
_INVESTOR_FLOW_LANGUAGE = re.compile(
    r"(?:투자주체\s*수급|(?:외국인|기관|개인).{0,16}(?:수급|순매수|순매도))",
    re.IGNORECASE,
)
_GENERIC_STOCK_SUPPLY_LANGUAGE = re.compile(
    r"(?:수급(?:\s*(?:부재|공백|우호|약화|강화|개선|악화))?"
    r"|매수\s*주체|공동\s*(?:매수|매도)|외국인|기관|개인|순매수|순매도)",
    re.IGNORECASE,
)
_KR_SUPPLY_DIRECTION = re.compile(
    r"(?P<direction>순매수|순매도|매수\s*우위|매도\s*우위|매수|매도)",
    re.IGNORECASE,
)
_FINANCIAL_PERIOD_USAGE = re.compile(
    r"\b20\d{2}년\s*(?:[1-4]분기|상반기\s*누적|3분기\s*누적|연간)\b"
)
_FINANCIAL_STATEMENT_BASIS_USAGE = re.compile(r"(?:연결|별도)\s*기준")
_FINANCIAL_CUMULATIVE_LANGUAGE = re.compile(
    r"(?:상반기\s*누적|(?:3분기|9개월)\s*누적|누적\s*(?:매출|이익|실적)|"
    r"(?:매출|이익|실적)\s*누적)"
)
_FINANCIAL_SINGLE_QUARTER_LANGUAGE = re.compile(r"(?:단일\s*분기|분기\s*단일)")
_FINANCIAL_PERIOD_SEMANTICS = {
    "revenue",
    "operating_income",
    "net_income",
    "operating_margin",
    "revenue_qoq",
    "revenue_yoy",
    "operating_income_qoq",
    "operating_income_yoy",
}
_NEGATIVE_BOOK_LANGUAGE = re.compile(
    r"(?:음의\s*(?:BVPS|주당순자산|장부가치)|"
    r"(?:BVPS|주당순자산|장부가치)(?:가|는|은)?\s*음수|자본잠식)",
    re.IGNORECASE,
)
_HISTORICAL_VALUATION_LANGUAGE = re.compile(
    r"(?:역사적|과거|자체\s*역사).{0,24}(?:PER|PBR|배수|백분위|상단|하단|높|낮)",
    re.IGNORECASE,
)
_PEER_VALUATION_LANGUAGE = re.compile(
    r"(?:peer|피어|동종|업종).{0,24}(?:premium|discount|프리미엄|할인|높|낮|비싸|싸)",
    re.IGNORECASE,
)
_ABSOLUTE_VALUATION_JUDGMENT = re.compile(
    r"(?:(?:PER|PBR|fPER|fPBR|배수).{0,32}"
    r"(?:고평가|저평가|비싸|싸다|부담|기대가?\s*(?:높|낮))|"
    r"(?:고평가|저평가|기대\s*부담).{0,32}(?:PER|PBR|fPER|fPBR|배수))",
    re.IGNORECASE,
)


def _section_fact_ids(review: AIStockReview, text_ref: str) -> set[str]:
    if text_ref.startswith("core_judgment."):
        return set(review.core_judgment.fact_ids)
    if text_ref.startswith("business_earnings."):
        return set(review.business_earnings.fact_ids)
    if text_ref.startswith("price_positioning."):
        return set(review.price_positioning.fact_ids)
    if text_ref.startswith("supply_analysis."):
        return set(review.supply_analysis.fact_ids)
    if text_ref.startswith("valuation_analysis."):
        return set(review.valuation_analysis.fact_ids)
    return set()


def _claims_in_sentence(
    review: AIStockReview,
    text_ref: str,
    sentence: str,
) -> list[object]:
    return [
        claim
        for claim in review.numeric_claims
        if claim.text_ref == text_ref and claim.usage in sentence
    ]


def _kr_supply_grounding_errors(
    ticker: str,
    market: AIReviewMarket | None,
    review: AIStockReview,
) -> list[str]:
    if market != "kr":
        return []
    errors: list[str] = []
    actor_semantics = {
        "외국인": {
            "1d": "foreign_net_buy_qty",
            "5d": "foreign_net_buy_qty_5d",
            "20d": "foreign_net_buy_qty_20d",
        },
        "기관": {
            "1d": "institution_net_buy_qty",
            "5d": "institution_net_buy_qty_5d",
            "20d": "institution_net_buy_qty_20d",
        },
    }
    for text_ref, text in _prose_fields(review).items():
        for sentence in re.split(r"(?<=[.!?])\s+|\n+", text):
            if not _KR_SUPPLY_DIRECTION.search(sentence):
                continue
            claims = _claims_in_sentence(review, text_ref, sentence)
            if re.search(r"(?:당일|1\s*일).{0,12}공동\s*(?:매수|매도)", sentence):
                required = {
                    "foreign_net_buy_qty",
                    "institution_net_buy_qty",
                }
                claimed = {str(claim.semantic_type) for claim in claims}
                if not required.issubset(claimed):
                    errors.append(
                        f"{ticker}:kr_supply_joint_1d_grounding_missing:{text_ref}"
                    )
            for actor, horizons in actor_semantics.items():
                actor_pattern = re.compile(
                    rf"{actor}\s*(?P<horizon>당일|1\s*일|5\s*일|20\s*일)?"
                    r"[^.!?\n]{0,16}?(?P<direction>순매수|순매도|매수\s*우위|매도\s*우위)",
                    re.IGNORECASE,
                )
                for match in actor_pattern.finditer(sentence):
                    raw_horizon = (match.group("horizon") or "").replace(" ", "")
                    horizon = {
                        "": "1d",
                        "당일": "1d",
                        "1일": "1d",
                        "5일": "5d",
                        "20일": "20d",
                    }[raw_horizon]
                    semantic = horizons[horizon]
                    matching = []
                    for claim in claims:
                        if claim.semantic_type != semantic:
                            continue
                        usage_start = sentence.find(claim.usage)
                        usage_end = usage_start + len(claim.usage)
                        if usage_start >= 0 and (
                            usage_start < match.end() and match.start() < usage_end
                        ):
                            matching.append(claim)
                    if not matching:
                        errors.append(
                            f"{ticker}:kr_supply_actor_horizon_grounding_missing:"
                            f"{text_ref}:{actor}:{horizon}"
                        )
                        continue
                    direction_text = match.group("direction")
                    for claim in matching:
                        if (
                            claim.value < 0
                            and "매수" in direction_text
                            and "매도" not in direction_text
                        ) or (
                            claim.value >= 0
                            and "매도" in direction_text
                            and "매수" not in direction_text
                        ):
                            errors.append(
                                f"{ticker}:kr_supply_direction_mismatch:"
                                f"{text_ref}:{actor}:{horizon}"
                            )
    return list(dict.fromkeys(errors))


def _financial_period_language_errors(
    ticker: str,
    review: AIStockReview,
) -> list[str]:
    errors: list[str] = []
    prose_fields = _prose_fields(review)
    for claim in review.numeric_claims:
        if claim.semantic_type not in _FINANCIAL_PERIOD_SEMANTICS:
            continue
        if not _FINANCIAL_PERIOD_USAGE.search(claim.usage):
            errors.append(
                f"{ticker}:financial_period_label_missing:"
                f"{claim.fact_id}:{claim.field_path}:{claim.text_ref}"
            )
            continue
        if (
            claim.unit == "KRW"
            and not _FINANCIAL_STATEMENT_BASIS_USAGE.search(claim.usage)
        ):
            errors.append(
                f"{ticker}:financial_statement_basis_label_missing:"
                f"{claim.fact_id}:{claim.field_path}:{claim.text_ref}"
            )
            continue
        text = prose_fields.get(claim.text_ref, "")
        usage_start = text.find(claim.usage)
        if usage_start < 0:
            continue
        sentence_start = max(
            text.rfind(".", 0, usage_start),
            text.rfind("!", 0, usage_start),
            text.rfind("?", 0, usage_start),
            text.rfind("\n", 0, usage_start),
        ) + 1
        sentence_ends = [
            index
            for index in (
                text.find(".", usage_start),
                text.find("!", usage_start),
                text.find("?", usage_start),
                text.find("\n", usage_start),
            )
            if index >= 0
        ]
        sentence_end = min(sentence_ends) if sentence_ends else len(text)
        sentence = text[sentence_start:sentence_end]
        usage_is_cumulative = bool(re.search(r"(?:상반기|3분기)\s*누적", claim.usage))
        usage_is_single_quarter = bool(
            re.search(r"20\d{2}년\s*[1-4]분기", claim.usage)
            and not usage_is_cumulative
        )
        if usage_is_single_quarter and _FINANCIAL_CUMULATIVE_LANGUAGE.search(sentence):
            errors.append(
                f"{ticker}:financial_amount_period_prose_mismatch:"
                f"{claim.fact_id}:{claim.field_path}:{claim.text_ref}:single_quarter"
            )
        if usage_is_cumulative and _FINANCIAL_SINGLE_QUARTER_LANGUAGE.search(sentence):
            errors.append(
                f"{ticker}:financial_amount_period_prose_mismatch:"
                f"{claim.fact_id}:{claim.field_path}:{claim.text_ref}:cumulative"
            )
    return list(dict.fromkeys(errors))


def _valuation_interpretation_evidence_errors(
    ticker: str,
    review: AIStockReview,
) -> list[str]:
    errors: list[str] = []
    historical_semantics = {
        "historical_pe_percentile",
        "historical_pb_percentile",
        "company_pe_vs_median_pct",
        "company_pb_vs_median_pct",
    }
    peer_semantics = {
        "peer_pe_multiple",
        "peer_pb_multiple",
        "peer_pe_relative_pct",
        "peer_pb_relative_pct",
    }
    for text_ref, text in _prose_fields(review).items():
        facts = _section_fact_ids(review, text_ref)
        claims = [
            claim for claim in review.numeric_claims if claim.text_ref == text_ref
        ]
        if _NEGATIVE_BOOK_LANGUAGE.search(text) and not facts.intersection(
            {"valuation:book_value", "valuation:book_quality"}
        ):
            errors.append(
                f"{ticker}:negative_book_interpretation_without_homogeneous_fact:"
                f"{text_ref}"
            )
        if _HISTORICAL_VALUATION_LANGUAGE.search(text) and not any(
            claim.semantic_type in historical_semantics for claim in claims
        ):
            errors.append(
                f"{ticker}:historical_valuation_interpretation_without_comparison:"
                f"{text_ref}"
            )
        if _PEER_VALUATION_LANGUAGE.search(text) and not any(
            claim.semantic_type in peer_semantics for claim in claims
        ):
            errors.append(
                f"{ticker}:peer_valuation_interpretation_without_comparison:"
                f"{text_ref}"
            )
        comparison_supported = any(
            claim.semantic_type in historical_semantics | peer_semantics
            for claim in claims
        ) or any(fact_id.startswith("market_expectation:") for fact_id in facts)
        if _ABSOLUTE_VALUATION_JUDGMENT.search(text) and not comparison_supported:
            errors.append(
                f"{ticker}:absolute_valuation_judgment_without_comparison:"
                f"{text_ref}"
            )
    return list(dict.fromkeys(errors))


def _security_identity_language_errors(
    ticker: str,
    identity_value: str | dict[str, object],
    review: AIStockReview,
) -> list[str]:
    identity = identity_value if isinstance(identity_value, dict) else {}
    identity_state = str(
        identity.get("identity_state") if identity else identity_value
    )
    identity_provenance = _dict(identity.get("identity_provenance"))
    identity_evidence = _dict(identity_provenance.get("evidence"))
    field_provenance = _dict(identity_provenance.get("field_provenance"))
    ratio_fact = _dict(field_provenance.get("adr_ratio"))
    direction_fact = _dict(field_provenance.get("adr_ratio_direction"))
    ratio = _number(
        identity.get("selected_adr_ratio") or identity_evidence.get("adr_ratio")
    )
    ratio_direction = str(
        identity.get("adr_ratio_direction")
        or identity_provenance.get("adr_ratio_direction")
        or identity_evidence.get("adr_ratio_direction")
        or ""
    )
    ratio_verified = bool(
        identity_state == VERIFIED_DEPOSITARY
        and ratio is not None
        and ratio > 0
        and ratio_direction == "ordinary_shares_per_adr"
        and ratio_fact.get("verification_status") == "verified"
        and direction_fact.get("verification_status") == "verified"
        and _number(ratio_fact.get("value")) == ratio
        and direction_fact.get("value") == ratio_direction
        and ratio_fact.get("source_url")
        and direction_fact.get("source_url")
    )
    errors: list[str] = []
    for text_ref, text in _prose_fields(review).items():
        if (
            identity_state in {VERIFIED_DEPOSITARY, VERIFIED_NON_DEPOSITARY}
            and _IDENTITY_UNVERIFIED_LANGUAGE.search(text)
        ):
            errors.append(
                f"{ticker}:verified_security_identity_described_as_unverified:{text_ref}"
            )
        if (
            identity_state in {IDENTITY_CONFLICT, IDENTITY_UNKNOWN}
            and _IDENTITY_VERIFIED_LANGUAGE.search(text)
        ):
            errors.append(
                f"{ticker}:unverified_security_identity_described_as_verified:{text_ref}"
            )
        if (
            identity_state == VERIFIED_NON_DEPOSITARY
            and _NON_DEPOSITARY_CALLED_DEPOSITARY.search(text)
        ):
            errors.append(
                f"{ticker}:non_depositary_described_as_depositary:{text_ref}"
            )
        if (
            identity_state == VERIFIED_DEPOSITARY
            and _DEPOSITARY_CALLED_COMMON_STOCK.search(text)
        ):
            errors.append(
                f"{ticker}:depositary_described_as_common_stock:{text_ref}"
            )
        if (
            identity_state in {IDENTITY_CONFLICT, IDENTITY_UNKNOWN}
            and _EXPLICIT_SECURITY_TYPE_LANGUAGE.search(text)
        ):
            errors.append(
                f"{ticker}:unverified_security_type_asserted:{text_ref}"
            )
        if (
            not ratio_verified
            and _VERIFIED_DEPOSITARY_RATIO_LANGUAGE.search(text)
        ):
            errors.append(
                f"{ticker}:unverified_depositary_ratio_described_as_verified:{text_ref}"
            )
    return list(dict.fromkeys(errors))


_RR_LANGUAGE = re.compile(r"(?:차트\s*)?손익비|\bRR\b|risk.?reward", re.IGNORECASE)
_POSITIVE_COMPARISON = re.compile(r"개선|상승|확대|회복")
_NEGATIVE_COMPARISON = re.compile(r"악화|하락|축소|둔화")
_OTHER_COMPARATIVE_SUBJECT = re.compile(
    r"이익률|마진|매출|가격|거래량|실적|수급|현금흐름|재고|가동률|수익성"
)


def _risk_reward_comparative_errors(
    ticker: str,
    monitoring_state: dict[str, object],
    review: AIStockReview,
) -> list[str]:
    delta = _dict(monitoring_state.get("delta"))
    previous = _number(delta.get("rr_previous"))
    current = _number(delta.get("rr_current"))
    errors: list[str] = []
    for text_ref, text in _prose_fields(review).items():
        for sentence in re.split(r"(?<=[.!?])\s+|\n+", text):
            mentions = list(_RR_LANGUAGE.finditer(sentence))
            if not mentions:
                continue
            comparison_matches = [
                *(('positive', match) for match in _POSITIVE_COMPARISON.finditer(sentence)),
                *(('negative', match) for match in _NEGATIVE_COMPARISON.finditer(sentence)),
            ]
            local_directions = {
                direction
                for direction, comparison in comparison_matches
                if any(
                    abs(comparison.start() - mention.end()) <= 32
                    and not _OTHER_COMPARATIVE_SUBJECT.search(
                        sentence[
                            min(comparison.end(), mention.end()) : max(
                                comparison.start(), mention.start()
                            )
                        ]
                    )
                    for mention in mentions
                )
            }
            if not local_directions:
                continue
            transition_claim_paths = {
                claim.field_path
                for claim in review.numeric_claims
                if claim.text_ref == text_ref
                and claim.fact_id == "monitoring:risk_reward_transition"
                and claim.usage in sentence
            }
            required = {"fields.previous_ratio", "fields.current_ratio"}
            if not required.issubset(transition_claim_paths):
                errors.append(
                    f"{ticker}:unsupported_risk_reward_comparison:{text_ref}"
                )
                continue
            if previous is None or current is None:
                errors.append(
                    f"{ticker}:risk_reward_comparison_lineage_missing:{text_ref}"
                )
                continue
            if (
                "positive" in local_directions and current <= previous
            ) or (
                "negative" in local_directions and current >= previous
            ):
                errors.append(
                    f"{ticker}:risk_reward_comparison_direction_mismatch:{text_ref}"
                )
    return list(dict.fromkeys(errors))


_SUPPORT_ENTRY_RR_BASIS = re.compile(
    r"(?:동적\s*)?지지(?:구간)?[^.!?\n]{0,18}(?:접근|도달|가정|조건부)",
    re.IGNORECASE,
)


def _risk_reward_basis_errors(
    ticker: str,
    review: AIStockReview,
) -> list[str]:
    errors: list[str] = []
    for text_ref, text in _prose_fields(review).items():
        claims = [
            claim
            for claim in review.numeric_claims
            if claim.text_ref == text_ref
            and "risk_reward" in claim.semantic_type
        ]
        for claim in claims:
            if claim.semantic_type == "risk_reward_ratio":
                errors.append(f"{ticker}:risk_reward_basis_missing:{text_ref}")
            if (
                claim.semantic_type == "support_entry_risk_reward_ratio"
                and not _SUPPORT_ENTRY_RR_BASIS.search(text)
            ):
                errors.append(
                    f"{ticker}:support_entry_risk_reward_basis_not_disclosed:{text_ref}"
                )
            if (
                claim.semantic_type == "current_price_risk_reward_ratio"
                and "지지 접근 가정 차트 손익비" in claim.usage
            ):
                errors.append(
                    f"{ticker}:current_price_risk_reward_mislabeled:{text_ref}"
                )
            if (
                claim.semantic_type == "current_price_risk_reward_ratio"
                and re.search(
                    rf"(?:동적\s*)?지지(?:구간)?[^.!?\n]{{0,28}}"
                    rf"(?:접근|도달|가정|조건부)[^.!?\n]{{0,28}}"
                    rf"{re.escape(claim.usage)}",
                    text,
                )
            ):
                errors.append(
                    f"{ticker}:current_price_risk_reward_used_as_support_scenario:"
                    f"{text_ref}"
                )
            if (
                claim.semantic_type == "support_entry_risk_reward_ratio"
                and re.search(
                    rf"(?:현재가|현재\s*가격).{{0,28}}{re.escape(claim.usage)}"
                    rf"|{re.escape(claim.usage)}.{{0,28}}(?:현재가|현재\s*가격)",
                    text,
                )
            ):
                errors.append(
                    f"{ticker}:support_entry_risk_reward_used_as_current_price:"
                    f"{text_ref}"
                )
        if text_ref == "core_judgment.text" and any(
            claim.semantic_type == "support_entry_risk_reward_ratio"
            for claim in claims
        ) and not any(
            claim.semantic_type == "current_price_risk_reward_ratio"
            for claim in claims
        ):
            errors.append(
                f"{ticker}:support_entry_risk_reward_used_as_primary_current_rr:"
                f"{text_ref}"
            )
    return list(dict.fromkeys(errors))


def _market_supply_language_errors(
    ticker: str,
    market: AIReviewMarket | None,
    stock: dict[str, object],
    review: AIStockReview,
) -> list[str]:
    if market != "us":
        return []
    errors: list[str] = []
    prose = _prose_fields(review)
    has_investor_flow_fact = any(
        str(item.get("semantic_type") or "").startswith(
            (
                "us_investor_flow",
                "us_fund_flow",
                "short_interest_positioning",
                "foreign_net_buy_qty",
                "institution_net_buy_qty",
            )
        )
        and item.get("prose_allowed") is True
        for item in stock.get("numeric_registry", [])
        if isinstance(item, dict)
    )
    for text_ref, text in prose.items():
        if _US_KR_SUPPLY_HORIZON_LANGUAGE.search(text):
            errors.append(f"{ticker}:us_kr_supply_horizon_language:{text_ref}")
        if not has_investor_flow_fact and (
            _INVESTOR_FLOW_LANGUAGE.search(text)
            or _GENERIC_STOCK_SUPPLY_LANGUAGE.search(text)
        ):
            errors.append(f"{ticker}:us_investor_flow_not_in_packet:{text_ref}")
    return list(dict.fromkeys(errors))


def _validate_stock_review(
    review: AIStockReview,
    stock: dict[str, object],
    market: AIReviewMarket | None = None,
) -> list[str]:
    errors: list[str] = []
    if normalize_decision_text(
        review.price_positioning.new_observer_view
    ) == normalize_decision_text(review.price_positioning.holder_view):
        errors.append(f"{review.ticker}:observer_holder_not_distinct")
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
    denied_financial_facts = {
        str(item.get("fact_id"))
        for item in fact_catalog
        if isinstance(item, dict)
        and item.get("interpretation_eligible") is False
    }
    denied_interpretation_facts = sorted(
        interpretation_facts.intersection(denied_financial_facts)
    )
    if denied_interpretation_facts:
        errors.append(
            f"{review.ticker}:financial_quality_denied_fact_used:"
            + ",".join(denied_interpretation_facts)
        )
    valuation = _dict(stock.get("valuation"))
    identity = resolve_packet_security_identity(stock)
    identity_state = str(identity.get("identity_state") or IDENTITY_UNKNOWN)
    identity_contract_present = bool(
        valuation.get("security_identity_decision_version")
    )
    errors.extend(_security_identity_language_errors(review.ticker, identity, review))
    errors.extend(
        _confirmation_transition_errors(
            review.ticker,
            _dict(stock.get("monitoring_state")),
            review,
        )
    )
    errors.extend(
        _risk_reward_comparative_errors(
            review.ticker,
            _dict(stock.get("monitoring_state")),
            review,
        )
    )
    errors.extend(_risk_reward_basis_errors(review.ticker, review))
    errors.extend(
        _market_supply_language_errors(review.ticker, market, stock, review)
    )
    errors.extend(_kr_supply_grounding_errors(review.ticker, market, review))
    errors.extend(_financial_period_language_errors(review.ticker, review))
    errors.extend(_valuation_interpretation_evidence_errors(review.ticker, review))
    identity_blocks_valuation = bool(
        identity_state == IDENTITY_CONFLICT
        or (identity_contract_present and identity_state == IDENTITY_UNKNOWN)
    )
    if identity_blocks_valuation:
        security_basis_fact_ids = {
            str(item.get("fact_id"))
            for item in fact_catalog
            if isinstance(item, dict)
            and item.get("fact_type")
            in {"valuation", "valuation_interpretation", "peer_valuation"}
        }
        denied_identity_facts = sorted(
            interpretation_facts.intersection(security_basis_fact_ids)
        )
        if denied_identity_facts:
            errors.append(
                f"{review.ticker}:security_identity_denied_fact_used:"
                + ",".join(denied_identity_facts)
            )
        denied_identity_claims = sorted(
            {
                claim.fact_id
                for claim in review.numeric_claims
                if claim.fact_id in security_basis_fact_ids
            }
        )
        if denied_identity_claims:
            errors.append(
                f"{review.ticker}:security_identity_denied_numeric_claim:"
                + ",".join(denied_identity_claims)
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
    grounding = _dict(stock.get("state_grounding_requirements"))
    price_fact_ids = set(review.price_positioning.fact_ids)
    price_claims = {
        (claim.fact_id, claim.field_path)
        for claim in review.numeric_claims
        if claim.text_ref.startswith("price_positioning.")
    }
    for requirement in _list(grounding.get("price")):
        if not isinstance(requirement, dict):
            continue
        fact_id = str(requirement.get("fact_id") or "")
        if fact_id and fact_id not in price_fact_ids:
            errors.append(
                f"{review.ticker}:current_price_structure_fact_missing:{fact_id}"
            )
        for field_path in requirement.get("field_paths", []) or []:
            if (fact_id, str(field_path)) not in price_claims:
                errors.append(
                    f"{review.ticker}:current_price_structure_numeric_missing:"
                    f"{fact_id}:{field_path}"
                )
    valuation_fact_ids = set(review.valuation_analysis.fact_ids)
    valuation_claims = {
        (claim.fact_id, claim.field_path)
        for claim in review.numeric_claims
        if claim.text_ref.startswith("valuation_analysis.")
    }
    for requirement in _list(grounding.get("valuation")):
        if not isinstance(requirement, dict):
            continue
        fact_id = str(requirement.get("fact_id") or "")
        if fact_id and fact_id not in valuation_fact_ids:
            errors.append(f"{review.ticker}:peer_valuation_fact_missing:{fact_id}")
        for field_path in requirement.get("field_paths", []) or []:
            if (fact_id, str(field_path)) not in valuation_claims:
                errors.append(
                    f"{review.ticker}:peer_valuation_numeric_grounding_missing:"
                    f"{fact_id}:{field_path}"
                )
    eligible_numeric = [
        item
        for item in stock.get("numeric_registry", [])
        if isinstance(item, dict)
        and item.get("registered") is True
        and item.get("prose_allowed") is True
        and str(item.get("scope") or "") in {"stock", "both"}
    ]
    if len(eligible_numeric) >= 4 and not review.numeric_claims:
        errors.append(f"{review.ticker}:numeric_grounding_hard_fail")
    if valuation:
        errors.extend(
            _forward_source_language_errors(review.ticker, valuation, rendered)
        )
        if str(valuation.get("historical_comparability") or "") in _INVALID_HISTORY and re.search(
            r"(?:역사적|과거)\s*(?:백분위|배수)", rendered
        ):
            errors.append(f"{review.ticker}:invalid_historical_comparison_used")
        if re.search(
            r"\b\d+(?:\.\d+)?%\s*(?:고평가|저평가)",
            rendered,
            flags=re.IGNORECASE,
        ):
            errors.append(f"{review.ticker}:historical_percentile_misrepresented")
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


def _validate_bound_ai_review_output(
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
        errors.extend(
            _validate_stock_review(
                review,
                stock,
                str(packet.get("market") or "") or None,
            )
        )
    market_context = packet.get("market_context")
    market_fact_ids = {
        str(item.get("fact_id"))
        for item in market_context.get("fact_catalog", [])
        if isinstance(item, dict) and item.get("fact_id")
    } if isinstance(market_context, dict) else set()
    if set(output.market_review.facts_used) - market_fact_ids:
        errors.append("market_review:unknown_fact_ids")
    market_interpretation_facts = {
        fact_id
        for item in (
            output.market_review.core_judgment,
            *output.market_review.important_changes,
            output.market_review.market_context,
            output.market_review.market_assumptions,
            *output.market_review.portfolio_transmission,
            *output.market_review.next_checks,
        )
        for fact_id in item.fact_ids
    }
    if market_interpretation_facts - market_fact_ids:
        errors.append("market_review:interpretation_unknown_fact_ids")
    required_market_facts = {
        str(item)
        for item in (
            market_context.get("required_market_fact_ids", [])
            if isinstance(market_context, dict)
            else []
        )
    }
    missing_required_facts = sorted(
        required_market_facts - set(output.market_review.facts_used)
    )
    if missing_required_facts:
        errors.append(
            "market_review:required_market_facts_missing:"
            + ",".join(missing_required_facts)
        )
    missing_required_interpretation = sorted(
        required_market_facts - market_interpretation_facts
    )
    if missing_required_interpretation:
        errors.append(
            "market_review:required_market_interpretation_missing:"
            + ",".join(missing_required_interpretation)
        )
    important_change_facts = {
        fact_id
        for item in output.market_review.important_changes
        for fact_id in item.fact_ids
    }
    missing_required_changes = sorted(
        required_market_facts - important_change_facts
    )
    if missing_required_changes:
        errors.append(
            "market_review:night_futures_change_missing:"
            + ",".join(missing_required_changes)
        )
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
    portfolio_groups = {
        str(item.get("group_key"))
        for item in market_context.get("portfolio_exposure_groups", [])
        if isinstance(item, dict) and item.get("group_key")
    } if isinstance(market_context, dict) else set()
    transmission_facts: dict[str, set[str]] = {}
    if isinstance(market_context, dict):
        for item in market_context.get("transmission_candidates", []):
            if not isinstance(item, dict):
                continue
            group = str(item.get("portfolio_group") or "")
            fact_id = str(item.get("market_fact_id") or "")
            if group and fact_id:
                transmission_facts.setdefault(group, set()).add(fact_id)
    for index, item in enumerate(output.market_review.portfolio_transmission):
        if item.portfolio_group not in portfolio_groups:
            errors.append(
                f"market_review:portfolio_group_not_found:{item.portfolio_group}"
            )
        if not item.fact_ids:
            errors.append(
                f"market_review:portfolio_transmission_without_fact:{index}"
            )
            continue
        allowed = transmission_facts.get(item.portfolio_group, set())
        invalid = sorted(set(item.fact_ids) - allowed)
        if invalid:
            errors.append(
                "market_review:portfolio_transmission_fact_mismatch:"
                f"{item.portfolio_group}:" + ",".join(invalid)
            )
    for index, item in enumerate(output.market_review.next_checks):
        if not item.fact_ids:
            errors.append(f"market_review:next_check_without_fact:{index}")
        if re.search(
            r"(?:향후|추가).{0,8}시장\s*상황.{0,8}확인",
            item.text,
            flags=re.IGNORECASE,
        ):
            errors.append(f"market_review:generic_next_check:{index}")
    errors.extend(
        _validate_numeric_claims(
            "market_review",
            output.market_review,
            market_context.get("numeric_registry")
            if isinstance(market_context, dict)
            else None,
        )
    )
    market_registry = (
        market_context.get("numeric_registry", [])
        if isinstance(market_context, dict)
        else []
    )
    market_eligible_numeric = [
        item
        for item in market_registry
        if isinstance(item, dict)
        and item.get("registered") is True
        and item.get("prose_allowed") is True
        and str(item.get("scope") or "") in {"market", "both"}
    ]
    if len(market_eligible_numeric) >= 4 and not output.market_review.numeric_claims:
        errors.append("market_review:numeric_grounding_hard_fail")
    numeric_claim_fact_ids = {
        item.fact_id for item in output.market_review.numeric_claims
    }
    missing_required_numeric = sorted(
        required_market_facts - numeric_claim_fact_ids
    )
    if missing_required_numeric:
        errors.append(
            "market_review:night_futures_numeric_grounding_missing:"
            + ",".join(missing_required_numeric)
        )
    return output, list(dict.fromkeys(errors))


def validate_ai_review_output(
    session: Session,
    packet: dict[str, object],
    output_value: object,
) -> tuple[AIDailyReviewOutput | None, list[str]]:
    binding = bind_numeric_fact_references(packet, output_value)
    typed_errors = list(
        _dict(binding.report.get("typed_valuation_interpretations")).get(
            "errors", []
        )
    )
    if binding.errors:
        return None, list(dict.fromkeys([*binding.errors, *typed_errors]))
    output, errors = _validate_bound_ai_review_output(session, packet, binding.output)
    return output, list(dict.fromkeys([*errors, *typed_errors]))


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
    market_context = packet.get("market_context", {})
    market_registry = (
        market_context.get("numeric_registry", [])
        if isinstance(market_context, dict)
        else []
    )
    market_eligible = [
        item
        for item in market_registry
        if isinstance(item, dict) and item.get("prose_allowed") is True
    ]
    market_claims = [
        item.model_dump() for item in output.market_review.numeric_claims
    ]
    market_flags: list[str] = []
    market_hard_failures: list[str] = []
    if len(market_eligible) >= 2 and len(market_claims) < 2:
        market_flags.append("insufficient_market_quantitative_grounding")
    if len(market_eligible) >= 4 and not market_claims:
        market_hard_failures.append("numeric_grounding_hard_fail:market")
    key_change_ids = {
        str(item)
        for item in (
            market_context.get("key_change_fact_ids", [])
            if isinstance(market_context, dict)
            else []
        )
    }
    candidate_fact_ids = {
        str(item.get("market_fact_id"))
        for item in (
            market_context.get("transmission_candidates", [])
            if isinstance(market_context, dict)
            else []
        )
        if isinstance(item, dict) and item.get("market_fact_id")
    }
    transmitted_fact_ids = {
        fact_id
        for item in output.market_review.portfolio_transmission
        for fact_id in item.fact_ids
    }
    if (key_change_ids & candidate_fact_ids) - transmitted_fact_ids:
        market_flags.append("market_fact_without_transmission")
    if any(not item.fact_ids for item in output.market_review.portfolio_transmission):
        market_flags.append("portfolio_transmission_without_fact")
    if any(not item.fact_ids for item in output.market_review.next_checks):
        market_flags.append("market_next_check_without_fact")
    if any(
        re.search(
            r"(?:향후|추가).{0,8}시장\s*상황.{0,8}확인",
            item.text,
            flags=re.IGNORECASE,
        )
        for item in output.market_review.next_checks
    ):
        market_flags.append("generic_market_next_check")
    user_market_prose = "\n".join(
        [
            output.market_review.core_judgment.text,
            *(item.text for item in output.market_review.important_changes),
            output.market_review.market_context.text,
            *(item.text for item in output.market_review.portfolio_transmission),
            *(item.text for item in output.market_review.next_checks),
        ]
    )
    if len(market_eligible) >= 2 and len(market_claims) < 2 and re.search(
        r"(?:시장이\s*혼조|시장\s*신호.*혼재|위험선호.*엇갈)", user_market_prose
    ):
        market_flags.append("generic_market_summary")
    market_report = {
        "eligible_numeric_anchors": len(market_eligible),
        "numeric_claims_used": len(market_claims),
        "selected_change_fact_ids": sorted(key_change_ids),
        "portfolio_transmission_count": len(
            output.market_review.portfolio_transmission
        ),
        "next_check_count": len(output.market_review.next_checks),
        "hard_failures": market_hard_failures,
        "flags": market_flags,
    }
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
            "peer_pe_multiple",
            "peer_pb_multiple",
            "peer_pe_relative_pct",
            "peer_pb_relative_pct",
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
        hard_failures: list[str] = []
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
        claim_semantics_by_section = {
            section: {
                str(item.get("semantic_type"))
                for item in claims
                if any(
                    str(item.get("text_ref") or "").startswith(prefix)
                    for prefix in prefixes
                )
            }
            for section, prefixes in section_prefixes.items()
        }
        eligible_semantics = {
            str(item.get("semantic_type")) for item in eligible
        }
        generic_requirements = (
            (
                "price",
                review.price_positioning.text,
                r"(?:가까운\s*저항|동적\s*지지|불리한\s*손익비)",
                {
                    "support_zone_price",
                    "resistance_zone_price",
                    "risk_reward_ratio",
                },
            ),
            (
                "supply",
                review.supply_analysis.text,
                r"중기\s*공동\s*수급",
                {"foreign_net_buy_qty_20d", "institution_net_buy_qty_20d"},
            ),
            (
                "valuation",
                review.valuation_analysis.text,
                r"(?:높은\s*valuation|역사적으로\s*높은\s*수준)",
                {"historical_pe_percentile", "historical_pb_percentile"},
            ),
        )
        for section, text, pattern, required_semantics in generic_requirements:
            available = eligible_semantics & required_semantics
            used = claim_semantics_by_section.get(section, set()) & required_semantics
            if available and re.search(pattern, text, flags=re.IGNORECASE) and not used:
                flags.append(f"generic_numeric_phrase_without_anchor:{section}")
        if len(eligible) >= 2 and not claims and re.search(
            r"(?:강한\s*실적|높은\s*기대|프리미엄|현금창출.*확인)", prose
        ):
            flags.append("vague_quantitative_language")
        if len(eligible) >= 4 and not claims:
            hard_failures.append(
                f"numeric_grounding_hard_fail:{review.ticker}"
            )
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
                "hard_failures": hard_failures,
                "flags": flags,
            }
        )
    return {
        "packet_id": output.packet_id,
        "analysis_policy_version": output.analysis_policy_version,
        "status": (
            "failed"
            if market_hard_failures
            or any(row["hard_failures"] for row in rows)
            else (
                "flagged"
                if market_flags or any(row["flags"] for row in rows)
                else "passed"
            )
        ),
        "market": market_report,
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


def _raw_text_at_ref(review: object, text_ref: str) -> str | None:
    node = review
    for part in text_ref.split("."):
        match = re.fullmatch(r"([A-Za-z_][A-Za-z0-9_]*)(?:\[([0-9]+)\])?", part)
        if match is None or not isinstance(node, dict):
            return None
        key, raw_index = match.groups()
        node = node.get(key)
        if raw_index is not None:
            if not isinstance(node, list) or int(raw_index) >= len(node):
                return None
            node = node[int(raw_index)]
    return node if isinstance(node, str) else None


def _numeric_correction_context(
    packet: dict[str, object],
    candidate: dict[str, object],
    errors: list[str],
) -> list[dict[str, object]]:
    packet_stocks = {
        str(item.get("ticker") or ""): item
        for item in packet.get("stocks", [])
        if isinstance(item, dict)
    }
    candidate_stocks = {
        str(item.get("ticker") or ""): item
        for item in candidate.get("stock_reviews", [])
        if isinstance(item, dict)
    }
    contexts: list[dict[str, object]] = []
    for error in errors:
        prefix = error.split(":", maxsplit=1)[0]
        if prefix == "market_review":
            review = candidate.get("market_review")
            market_context = packet.get("market_context")
            registry = (
                market_context.get("numeric_registry", [])
                if isinstance(market_context, dict)
                else []
            )
        else:
            review = candidate_stocks.get(prefix)
            stock = packet_stocks.get(prefix)
            registry = stock.get("numeric_registry", []) if isinstance(stock, dict) else []
        text_ref = None
        tokens: set[str] = set()
        marker = ":numbers_without_provenance:"
        if marker in error:
            _, remainder = error.split(marker, maxsplit=1)
            text_ref, _, token_text = remainder.partition(":")
            tokens = {item for item in token_text.split(",") if item}
        rendered_phrase = (
            _raw_text_at_ref(review, text_ref)
            if isinstance(review, dict) and text_ref
            else None
        )
        candidates: list[dict[str, object]] = []
        for source in registry if isinstance(registry, list) else []:
            if not isinstance(source, dict):
                continue
            variants = source.get("approved_display_variants")
            variant_tokens = set().union(
                *(
                    _provenance_tokens(str(variant))
                    for variant in variants
                )
            ) if isinstance(variants, list) and variants else set()
            referenced = (
                str(source.get("fact_id") or "") in error
                and str(source.get("field_path") or "") in error
            )
            if not referenced and (not tokens or not tokens & variant_tokens):
                continue
            candidates.append(
                {
                    "fact_id": source.get("fact_id"),
                    "field_path": source.get("field_path"),
                    "canonical_raw_value": source.get("value"),
                    "canonical_unit": source.get("unit"),
                    "canonical_semantic": source.get("semantic_type"),
                    "approved_formatted_value": source.get(
                        "canonical_display_value"
                    ),
                }
            )
        contexts.append(
            {
                "error": error,
                "text_ref": text_ref,
                "rendered_phrase": rendered_phrase,
                "canonical_candidates": candidates,
                "allowed_actions": [
                    "correct_reference",
                    "correct_wording",
                    "remove_unsafe_number",
                ],
            }
        )
    return contexts


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
    binding = bind_numeric_fact_references(packet, candidate)
    binding_report = dict(binding.report)
    typed_errors = list(
        _dict(binding_report.get("typed_valuation_interpretations")).get(
            "errors", []
        )
    )
    if candidate.get("claim_id") != claim_id:
        output = None
        errors = ["stale_claim_output"]
    elif binding.errors:
        output = None
        errors = list(binding.errors)
    else:
        output, errors = _validate_bound_ai_review_output(
            session,
            packet,
            binding.output,
        )
        errors = list(dict.fromkeys([*errors, *typed_errors]))
    if output is None or errors:
        rejected = _directory("rejected") / f"{output_name}.{int(datetime.now(UTC).timestamp())}"
        os.replace(temp_path, rejected)
        _atomic_json(
            Path(f"{rejected}.validation.json"),
            {
                "packet_id": packet_id,
                "claim_id": claim_id,
                "status": "rejected",
                "errors": errors,
                "numeric_binding": binding_report,
                "correction_context": _numeric_correction_context(
                    packet,
                    candidate,
                    errors,
                ),
                "fallback_eligibility_preserved": True,
            },
        )
        return OutputValidationResult(
            status="rejected", packet_id=packet_id, errors=tuple(errors)
        )
    validated_candidate = output.model_dump(mode="json")
    binding_report["user_visible_numeric_tokens"] = sum(
        len(_prose_number_occurrences(text))
        for review in (output.market_review, *output.stock_reviews)
        for text in _prose_fields(review).values()
    )
    validated_at = (now or datetime.now(UTC)).astimezone(UTC)
    history_dir = _directory("history") / f"{validated_at:%Y}" / f"{validated_at:%m}"
    history_dir.mkdir(parents=True, exist_ok=True)
    history_output = history_dir / output_name
    comparison_path = history_dir / output_name.replace(".json", ".comparison.json")
    grounding_path = history_dir / output_name.replace(
        ".json", ".quantitative-grounding.json"
    )
    binding_path = history_dir / output_name.replace(
        ".json", ".numeric-binding.json"
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
        _atomic_json(temp_path, validated_candidate)
        os.replace(temp_path, final_path)
        _atomic_json(history_output, validated_candidate)
        _atomic_json(comparison_path, _comparison_payload(packet, output, validated_at))
        _atomic_json(grounding_path, quantitative_grounding_report(packet, output))
        _atomic_json(binding_path, binding_report)
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
