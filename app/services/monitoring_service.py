import json

from sqlmodel import Session, select

from app.models.company import Company
from app.models.thesis import InvestmentThesis, ThesisAssessment
from app.models.watchlist import WatchlistItem
from app.schemas.thesis import (
    AssessmentStatus,
    InvestmentThesisRead,
    MonitoringItemCreate,
    MonitoringItemRead,
    MonitoringItemSummaryRead,
    PriceRulesInput,
    ThesisAssessmentRead,
)
from app.services.local_storage import export_thesis
from app.utils.tickers import normalize_ticker


def _json_list(value: str) -> list[str]:
    parsed = json.loads(value)
    return parsed if isinstance(parsed, list) else []


def _json_dict_list(value: str) -> list[dict[str, object]]:
    parsed = json.loads(value)
    return [item for item in parsed if isinstance(item, dict)] if isinstance(parsed, list) else []


def _json_dict(value: str) -> dict[str, object]:
    parsed = json.loads(value)
    return parsed if isinstance(parsed, dict) else {}


def _assessment_snapshot(assessment: ThesisAssessment) -> dict[str, object]:
    try:
        parsed = json.loads(assessment.thesis_snapshot)
    except json.JSONDecodeError:
        parsed = {}
    required = {"base_thesis", "thesis_version", "effective_date", "status", "current_thesis"}
    if isinstance(parsed, dict) and required.issubset(parsed):
        return parsed
    return {
        "base_thesis": assessment.summary,
        "thesis_version": assessment.thesis_version,
        "effective_date": str(assessment.assessment_date),
        "status": assessment.status,
        "current_thesis": assessment.summary,
        "supporting_evidence": [],
        "weakening_evidence": [],
        "invalidation_evidence": [],
    }


def thesis_to_read(thesis: InvestmentThesis | None) -> InvestmentThesisRead | None:
    if thesis is None:
        return None
    return InvestmentThesisRead(
        ticker=thesis.ticker,
        version=thesis.version,
        core_thesis=thesis.core_thesis,
        time_horizon=thesis.time_horizon,
        thesis_drivers=_json_list(thesis.thesis_drivers),
        validation_metrics=_json_list(thesis.validation_metrics),
        strengthen_signals=_json_list(thesis.strengthen_signals),
        weaken_signals=_json_list(thesis.weaken_signals),
        invalidation_signals=_json_list(thesis.invalidation_signals),
        price_rules=(
            PriceRulesInput.model_validate(_json_dict(thesis.price_rules))
            if _json_dict(thesis.price_rules)
            else None
        ),
        macro_exposures=_json_dict_list(thesis.macro_exposures),
        status=thesis.status,
        source=thesis.source,
        created_at=thesis.created_at,
    )


def assessment_to_read(assessment: ThesisAssessment) -> ThesisAssessmentRead:
    return ThesisAssessmentRead(
        ticker=assessment.ticker,
        thesis_version=assessment.thesis_version,
        assessment_date=assessment.assessment_date,
        status=assessment.status,
        score=assessment.score,
        confidence=assessment.confidence,
        summary=assessment.summary,
        new_buyer_view=assessment.new_buyer_view,
        holder_view=assessment.holder_view,
        price_view=assessment.price_view,
        risk_level=assessment.risk_level,
        evidence=json.loads(assessment.evidence),
        price_context=json.loads(assessment.price_context),
        thesis_snapshot=_assessment_snapshot(assessment),
        created_at=assessment.created_at,
    )


def _latest_thesis(session: Session, ticker: str) -> InvestmentThesis | None:
    return session.exec(
        select(InvestmentThesis)
        .where(InvestmentThesis.ticker == ticker, InvestmentThesis.status == "active")
        .order_by(InvestmentThesis.version.desc())
    ).first()


def _monitoring_item_read(
    session: Session,
    item: WatchlistItem,
    thesis: InvestmentThesis | None,
) -> MonitoringItemRead:
    latest_assessment = session.exec(
        select(ThesisAssessment)
        .where(ThesisAssessment.ticker == item.ticker)
        .order_by(ThesisAssessment.assessment_date.desc())
    ).first()
    current_summary = thesis.core_thesis if thesis else None
    latest_status = None
    latest_assessment_date = None
    if latest_assessment is not None:
        latest_status = AssessmentStatus(latest_assessment.status)
        latest_assessment_date = latest_assessment.assessment_date
        snapshot = _assessment_snapshot(latest_assessment)
        current_summary = snapshot.get("current_thesis") or latest_assessment.summary
    return MonitoringItemRead(
        ticker=item.ticker,
        company_name=item.company_name,
        exchange=item.exchange,
        active=item.active,
        thesis=thesis_to_read(thesis),
        latest_status=latest_status,
        latest_assessment_date=latest_assessment_date,
        current_thesis_summary=current_summary,
    )


def _price_rules_summary(rules: PriceRulesInput | None) -> list[str]:
    if rules is None:
        return []
    def display(value: float) -> str:
        return f"{value:.15g}"

    currency = f" {rules.currency}" if rules.currency else ""
    summaries: list[str] = []
    if rules.confirmation_price is not None:
        summaries.append(
            f"confirmation close >= {display(rules.confirmation_price)}{currency}"
        )
    if rules.support_zone_low is not None and rules.support_zone_high is not None:
        summaries.append(
            "support close "
            f"{display(rules.support_zone_low)}-{display(rules.support_zone_high)}{currency}"
        )
    if rules.warning_price is not None:
        summaries.append(f"warning close < {display(rules.warning_price)}{currency}")
    if rules.invalidation_price is not None:
        summaries.append(
            f"invalidation close < {display(rules.invalidation_price)}{currency}"
        )
    return summaries


def _monitoring_item_summary(item: MonitoringItemRead) -> MonitoringItemSummaryRead:
    thesis = item.thesis
    return MonitoringItemSummaryRead(
        ticker=item.ticker,
        company_name=item.company_name,
        exchange=item.exchange or "",
        active=item.active,
        thesis_version=thesis.version if thesis else 0,
        core_thesis=thesis.core_thesis if thesis else "",
        thesis_drivers=thesis.thesis_drivers if thesis else [],
        validation_metrics=thesis.validation_metrics if thesis else [],
        price_rules_summary=_price_rules_summary(thesis.price_rules if thesis else None),
        latest_status=item.latest_status.value if item.latest_status else "",
        latest_assessment_date=(
            item.latest_assessment_date.isoformat() if item.latest_assessment_date else ""
        ),
    )


def register_monitoring_item(
    session: Session,
    payload: MonitoringItemCreate,
) -> MonitoringItemRead:
    ticker = normalize_ticker(payload.ticker)
    item = session.exec(select(WatchlistItem).where(WatchlistItem.ticker == ticker)).first()
    if item is None:
        item = WatchlistItem(
            ticker=ticker,
            company_name=payload.company_name,
            exchange=payload.exchange,
            notes="Investment thesis monitoring",
            active=True,
        )
        session.add(item)
    else:
        item.company_name = payload.company_name
        item.exchange = payload.exchange
        item.active = True

    company = session.exec(select(Company).where(Company.ticker == ticker)).first()
    if company is None:
        session.add(
            Company(
                ticker=ticker,
                company_name=payload.company_name,
                exchange=payload.exchange,
            )
        )
    else:
        company.company_name = payload.company_name
        company.exchange = payload.exchange

    active_thesis = _latest_thesis(session, ticker)
    requested_values = (
        payload.core_thesis,
        payload.time_horizon,
        payload.thesis_drivers,
        payload.validation_metrics,
        payload.strengthen_signals,
        payload.weaken_signals,
        payload.invalidation_signals,
        payload.price_rules.model_dump(mode="json", exclude_none=True)
        if payload.price_rules
        else {},
        [item.model_dump(mode="json") for item in payload.macro_exposures],
    )
    existing_values = None
    if active_thesis is not None:
        existing_values = (
            active_thesis.core_thesis,
            active_thesis.time_horizon,
            _json_list(active_thesis.thesis_drivers),
            _json_list(active_thesis.validation_metrics),
            _json_list(active_thesis.strengthen_signals),
            _json_list(active_thesis.weaken_signals),
            _json_list(active_thesis.invalidation_signals),
            _json_dict(active_thesis.price_rules),
            _json_dict_list(active_thesis.macro_exposures),
        )

    if existing_values == requested_values:
        thesis = active_thesis
    else:
        version = (active_thesis.version + 1) if active_thesis else 1
        if active_thesis is not None:
            active_thesis.status = "superseded"
        thesis = InvestmentThesis(
            ticker=ticker,
            version=version,
            core_thesis=payload.core_thesis,
            time_horizon=payload.time_horizon,
            thesis_drivers=json.dumps(payload.thesis_drivers, ensure_ascii=False),
            validation_metrics=json.dumps(payload.validation_metrics, ensure_ascii=False),
            strengthen_signals=json.dumps(payload.strengthen_signals, ensure_ascii=False),
            weaken_signals=json.dumps(payload.weaken_signals, ensure_ascii=False),
            invalidation_signals=json.dumps(payload.invalidation_signals, ensure_ascii=False),
            price_rules=json.dumps(
                payload.price_rules.model_dump(mode="json", exclude_none=True)
                if payload.price_rules
                else {},
                ensure_ascii=False,
            ),
            macro_exposures=json.dumps(
                [item.model_dump(mode="json") for item in payload.macro_exposures],
                ensure_ascii=False,
            ),
            status="active",
        )
        session.add(thesis)

    session.commit()
    session.refresh(item)
    if thesis is not None:
        session.refresh(thesis)
        export_thesis(thesis)
    return _monitoring_item_read(session, item, thesis)


def list_monitoring_items(session: Session, active_only: bool = True) -> list[MonitoringItemRead]:
    query = select(WatchlistItem)
    if active_only:
        query = query.where(WatchlistItem.active.is_(True))
    items = session.exec(query.order_by(WatchlistItem.ticker)).all()
    return [
        _monitoring_item_read(session, item, _latest_thesis(session, item.ticker))
        for item in items
    ]


def list_monitoring_summaries(
    session: Session,
    active_only: bool = True,
) -> list[MonitoringItemSummaryRead]:
    return [
        _monitoring_item_summary(item)
        for item in list_monitoring_items(session, active_only=active_only)
    ]


def get_monitoring_item(session: Session, ticker: str) -> MonitoringItemRead | None:
    ticker = normalize_ticker(ticker)
    item = session.exec(select(WatchlistItem).where(WatchlistItem.ticker == ticker)).first()
    if item is None:
        return None
    return _monitoring_item_read(session, item, _latest_thesis(session, ticker))


def deactivate_monitoring_item(session: Session, ticker: str) -> MonitoringItemRead | None:
    ticker = normalize_ticker(ticker)
    item = session.exec(select(WatchlistItem).where(WatchlistItem.ticker == ticker)).first()
    if item is None:
        return None
    item.active = False
    session.commit()
    session.refresh(item)
    return _monitoring_item_read(session, item, _latest_thesis(session, ticker))


def list_assessments(
    session: Session,
    ticker: str,
    limit: int = 30,
) -> list[ThesisAssessmentRead]:
    ticker = normalize_ticker(ticker)
    assessments = session.exec(
        select(ThesisAssessment)
        .where(ThesisAssessment.ticker == ticker)
        .order_by(ThesisAssessment.assessment_date.desc())
        .limit(limit)
    ).all()
    return [assessment_to_read(item) for item in assessments]
