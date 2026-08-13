from __future__ import annotations

import hashlib
import json
import logging
import os
import re
import socket
from dataclasses import asdict, dataclass
from datetime import UTC, date, datetime, timedelta
from pathlib import Path
from tempfile import NamedTemporaryFile
from typing import Literal

from pydantic import ValidationError
from sqlmodel import Session, select

from app.config import get_settings
from app.models.macro import MacroBriefing
from app.models.security import SecurityMaster
from app.models.thesis import InvestmentThesis, MonitorRun, ThesisAssessment
from app.models.watchlist import WatchlistItem
from app.schemas.ai_review import AIDailyReviewOutput, AIStockReview
from app.services.daily_digest import build_daily_digest
from app.services.market_session import market_scope_for_security


logger = logging.getLogger(__name__)

PACKET_SCHEMA_VERSION = "1"
OUTPUT_SCHEMA_VERSION = "1"
ANALYSIS_POLICY_VERSION = "daily-review-v1"
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


def _root() -> Path:
    return Path(get_settings().data_dir) / "ai_review"


def _directory(name: str) -> Path:
    path = _root() / name
    path.mkdir(parents=True, exist_ok=True)
    return path


def ensure_ai_review_layout() -> None:
    for child in ("inbox", "claims", "outbox", "rejected", "history"):
        _directory(child)


def _atomic_json(path: Path, payload: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with NamedTemporaryFile("w", encoding="utf-8", dir=path.parent, delete=False) as handle:
        json.dump(payload, handle, ensure_ascii=False, indent=2, sort_keys=True, default=str)
        handle.write("\n")
        temporary = Path(handle.name)
    os.replace(temporary, path)


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
    ticker = assessment.ticker
    facts: list[dict[str, object]] = []
    for index, item in enumerate(evidence, start=1):
        facts.append(
            {
                "fact_id": f"{ticker}:event:{index}:{item['event_fingerprint']}",
                "category": "event",
                "fact": item,
            }
        )
    if valuation:
        facts.append(
            {
                "fact_id": f"{ticker}:valuation",
                "category": "earnings_valuation",
                "fact": valuation,
            }
        )
    if price.get("price"):
        facts.append(
            {
                "fact_id": f"{ticker}:price",
                "category": "price",
                "fact": price["price"],
            }
        )
    if price.get("supply"):
        facts.append(
            {
                "fact_id": f"{ticker}:supply",
                "category": "positioning",
                "fact": price["supply"],
            }
        )
    return facts


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
    evidence = _material_evidence(assessment)
    valuation = _valuation_payload(assessment)
    price = _price_payload(assessment)
    previous = _previous_assessment(session, assessment)
    current_expectation = _public_value(_dict(assessment.market_expectation_assessment))
    stock = {
        "ticker": assessment.ticker,
        "company_name": item.company_name,
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
    stock["fact_catalog"] = _fact_catalog(assessment, evidence, valuation, price)
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
                {"fact_id": f"market:change:{index}", "category": "macro", "fact": clean}
            )
    night_futures = [asdict(item) for item in digest.night_futures.items]
    for index, item in enumerate(night_futures, start=1):
        market_facts.append(
            {
                "fact_id": f"market:night_futures:{index}",
                "category": "night_futures",
                "fact": item,
            }
        )
    fx_items = []
    if digest.kr_close_fx is not None:
        fx_items = [asdict(item) for item in digest.kr_close_fx.items]
        for index, item in enumerate(fx_items, start=1):
            market_facts.append(
                {"fact_id": f"market:fx:{index}", "category": "fx", "fact": item}
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
    body = {
        "schema_version": PACKET_SCHEMA_VERSION,
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
        "analysis_policy_version": ANALYSIS_POLICY_VERSION,
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


def _completion_name(packet_id: str, policy_version: str) -> str:
    safe_policy = re.sub(r"[^A-Za-z0-9_.-]+", "-", policy_version)
    return f"{packet_id}--{safe_policy}.json"


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
        output_name = _completion_name(packet_id, policy)
        final_path = _directory("outbox") / output_name
        if final_path.exists():
            continue
        claim_path = _directory("claims") / f"{packet_id}.json"
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
            claim_path.unlink(missing_ok=True)
        claim = {
            "packet_id": packet_id,
            "market": market,
            "analysis_policy_version": policy,
            "owner": owner or socket.gethostname(),
            "claimed_at": current.isoformat(),
            "expires_at": (current + lease).isoformat(),
            "packet_path": str(packet_path),
            "temp_output_path": str(final_path.with_suffix(".json.tmp")),
            "final_output_path": str(final_path),
        }
        try:
            descriptor = os.open(claim_path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
        except FileExistsError:
            continue
        with os.fdopen(descriptor, "w", encoding="utf-8") as handle:
            json.dump(claim, handle, ensure_ascii=False, indent=2)
            handle.write("\n")
        return ClaimResult(
            status="claimed",
            packet_id=packet_id,
            packet_path=str(packet_path),
            claim_path=str(claim_path),
            temp_output_path=str(final_path.with_suffix(".json.tmp")),
            final_output_path=str(final_path),
        )
    return ClaimResult(status="no_pending_packet", reason="no_eligible_unclaimed_packet")


def _review_text(review: AIStockReview) -> str:
    return "\n".join(
        [
            *review.interpretation,
            *review.unknowns,
            review.summary,
            review.holder_view,
            review.new_buyer_view,
            *review.next_checks,
        ]
    )


def _numeric_tokens(value: object) -> set[str]:
    text = json.dumps(value, ensure_ascii=False, default=str) if not isinstance(value, str) else value
    return {match.group(0).lstrip("+") for match in _NUMBER.finditer(text)}


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
    allowed_numbers = _numeric_tokens(stock)
    unsupported_numbers = sorted(_numeric_tokens(rendered) - allowed_numbers)
    if unsupported_numbers:
        errors.append(
            f"{review.ticker}:numbers_not_in_packet:{','.join(unsupported_numbers)}"
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
    market_text = "\n".join(
        [
            *output.market_review.interpretation,
            *output.market_review.unknowns,
            output.market_review.summary,
        ]
    )
    if _INTERNAL_TEXT.search(market_text):
        errors.append("market_review:forbidden_internal_metadata")
    market_context = packet.get("market_context", {})
    unsupported_market_numbers = sorted(
        _numeric_tokens(market_text) - _numeric_tokens(market_context)
    )
    if unsupported_market_numbers:
        errors.append(
            "market_review:numbers_not_in_packet:"
            + ",".join(unsupported_market_numbers)
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
        comparisons.append(
            {
                "ticker": review.ticker,
                "thesis_version": review.thesis_version,
                "deterministic_status": base_status,
                "ai_proposed_status": review.ai_thesis_assessment,
                "status_match": base_status == review.ai_thesis_assessment,
                "deterministic_warnings": warnings,
                "guardrail_conflicts": guardrail_conflicts,
                "ai_summary": review.summary,
            }
        )
    return {
        "packet_id": output.packet_id,
        "analysis_policy_version": output.analysis_policy_version,
        "mode": get_settings().ai_review_mode,
        "validated_at": validated_at.isoformat(),
        "official_assessment_mutated": False,
        "telegram_mutated": False,
        "comparisons": comparisons,
    }


def finalize_ai_review_output(
    session: Session,
    packet_id: str,
    *,
    policy_version: str = ANALYSIS_POLICY_VERSION,
    now: datetime | None = None,
) -> OutputValidationResult:
    ensure_ai_review_layout()
    packet_path = _directory("inbox") / f"{packet_id}.json"
    output_name = _completion_name(packet_id, policy_version)
    final_path = _directory("outbox") / output_name
    temp_path = final_path.with_suffix(".json.tmp")
    if final_path.exists():
        return OutputValidationResult(
            status="already_completed", packet_id=packet_id, output_path=str(final_path)
        )
    if not packet_path.exists() or not temp_path.exists():
        return OutputValidationResult(
            status="not_ready",
            packet_id=packet_id,
            errors=("packet_or_temp_output_missing",),
        )
    try:
        packet = _read_json(packet_path)
        candidate = _read_json(temp_path)
    except (ValueError, json.JSONDecodeError) as exc:
        return OutputValidationResult(
            status="rejected", packet_id=packet_id, errors=(type(exc).__name__,)
        )
    output, errors = validate_ai_review_output(session, packet, candidate)
    if output is None or errors:
        rejected = _directory("rejected") / f"{output_name}.{int(datetime.now(UTC).timestamp())}"
        os.replace(temp_path, rejected)
        return OutputValidationResult(
            status="rejected", packet_id=packet_id, errors=tuple(errors)
        )
    validated_at = (now or datetime.now(UTC)).astimezone(UTC)
    os.replace(temp_path, final_path)
    history_dir = _directory("history") / f"{validated_at:%Y}" / f"{validated_at:%m}"
    history_dir.mkdir(parents=True, exist_ok=True)
    history_output = history_dir / output_name
    _atomic_json(history_output, candidate)
    comparison_path = history_dir / output_name.replace(".json", ".comparison.json")
    _atomic_json(comparison_path, _comparison_payload(packet, output, validated_at))
    (_directory("claims") / f"{packet_id}.json").unlink(missing_ok=True)
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
        final = _directory("outbox") / _completion_name(packet_id, policy)
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
