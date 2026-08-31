import asyncio
import json
from datetime import UTC, datetime, timedelta

from sqlmodel import Session, select

from app.models.company import Company
from app.models.thesis import InvestmentThesis, ThesisAssessment
from app.models.watchlist import WatchlistItem
from app.schemas.thesis import (
    AssessmentStatus,
    EarningsEstimateImpact,
    InvestmentThesisRead,
    MarketExpectationsInput,
    MarketExpectationAssessment,
    MonitoringItemCreate,
    MonitoringItemRead,
    MonitoringItemSummaryRead,
    PriceRulesInput,
    ThesisAssessmentRead,
    ThesisAssessmentCreate,
    ValuationImpact,
    ValuationContext,
    ValuationFrameworkInput,
)
from app.services.local_storage import export_assessment_history, export_thesis
from app.config import get_settings
from app.services.onboarding_readiness_service import (
    begin_onboarding,
    deactivate_onboarding,
    reconcile_onboarding,
)
from app.services.onboarding_reconciler_service import (
    OnboardingAttemptMode,
    resume_onboarding_subject,
)
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
        market_expectations=(
            MarketExpectationsInput.model_validate(_json_dict(thesis.market_expectations))
            if _json_dict(thesis.market_expectations)
            else None
        ),
        valuation_framework=(
            ValuationFrameworkInput.model_validate(_json_dict(thesis.valuation_framework))
            if _json_dict(thesis.valuation_framework)
            else None
        ),
        multiple_expansion_signals=_json_list(thesis.multiple_expansion_signals),
        multiple_compression_signals=_json_list(thesis.multiple_compression_signals),
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
    valuation_context = ValuationContext.model_validate(_json_dict(assessment.valuation_context))
    business_change = assessment.business_thesis_change or assessment.status
    valuation_change = assessment.valuation_change or valuation_context.impact.value
    market_assessment = _json_dict(assessment.market_expectation_assessment)
    if not market_assessment:
        market_assessment = {
            "level": valuation_context.market_expectation_level.value,
            "assessment": "unknown",
            "summary": valuation_context.market_expectation_summary,
            "evidence_basis": [],
        }
    return ThesisAssessmentRead(
        ticker=assessment.ticker,
        thesis_version=assessment.thesis_version,
        assessment_date=assessment.assessment_date,
        status=assessment.status,
        business_thesis_change=business_change,
        valuation_change=valuation_change,
        earnings_estimate_impact=(
            assessment.earnings_estimate_impact or EarningsEstimateImpact.unknown
        ),
        market_expectation_assessment=MarketExpectationAssessment.model_validate(
            market_assessment
        ),
        confirmed_facts=_json_list(assessment.confirmed_facts),
        background_confirmed_facts=_json_list(assessment.background_confirmed_facts),
        inferred_implications=_json_list(assessment.inferred_implications),
        unknowns=_json_list(assessment.unknowns),
        confirmed_warnings=_json_list(assessment.confirmed_warnings),
        new_warnings=_json_list(getattr(assessment, "new_warnings", "[]")),
        open_warnings=_json_list(getattr(assessment, "open_warnings", "[]")),
        open_confirmed_warnings=_json_list(
            getattr(assessment, "open_confirmed_warnings", "[]")
        ),
        persistent_watch_risks=_json_list(
            getattr(assessment, "persistent_watch_risks", "[]")
        ),
        warning_states=_json_dict_list(getattr(assessment, "warning_states", "[]")),
        watch_items=_json_list(assessment.watch_items),
        used_event_fingerprints=_json_list(assessment.used_event_fingerprints),
        score=assessment.score,
        confidence=assessment.confidence,
        summary=assessment.summary,
        new_buyer_view=assessment.new_buyer_view,
        holder_view=assessment.holder_view,
        price_view=assessment.price_view,
        risk_level=assessment.risk_level,
        daily_change_severity=getattr(assessment, "daily_change_severity", "none"),
        structural_risk_level=getattr(
            assessment, "structural_risk_level", "normal"
        ),
        assessment_state=getattr(assessment, "assessment_state", "final"),
        market_session=getattr(assessment, "market_session", "unknown"),
        evidence=json.loads(assessment.evidence),
        price_context=json.loads(assessment.price_context),
        new_buyer_price_view=getattr(assessment, "new_buyer_price_view", ""),
        holder_price_view=getattr(assessment, "holder_price_view", ""),
        valuation_snapshot=_json_dict(
            getattr(assessment, "valuation_snapshot", "{}")
        ),
        valuation_context=valuation_context,
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
    latest_valuation_context = None
    latest_earnings_estimate_impact = None
    if latest_assessment is not None:
        latest_status = AssessmentStatus(latest_assessment.status)
        latest_assessment_date = latest_assessment.assessment_date
        valuation = ValuationContext.model_validate(
            _json_dict(latest_assessment.valuation_context)
        )
        latest_valuation_context = ValuationImpact(
            latest_assessment.valuation_change or valuation.impact.value
        )
        latest_earnings_estimate_impact = EarningsEstimateImpact(
            latest_assessment.earnings_estimate_impact or "unknown"
        )
        snapshot = _assessment_snapshot(latest_assessment)
        current_summary = snapshot.get("current_thesis") or latest_assessment.summary
    readiness = _json_dict(getattr(item, "onboarding_readiness", "{}"))
    blockers = readiness.get("blocking_requirements", [])
    blocker_values = (
        [str(value) for value in blockers] if isinstance(blockers, list) else []
    )
    if (
        item.active
        and item.production_eligible
        and item.onboarding_state == "ACTIVE"
    ):
        registration_message = (
            "✅ 모니터링 등록 완료\n"
            "현재 상태: ACTIVE_READY\n"
            "다음 eligible cycle부터 자동 점검"
        )
    else:
        remaining = ", ".join(blocker_values) or "자동 온보딩 재검증"
        registration_message = (
            "🟡 모니터링 등록 준비 중\n"
            "현재 상태: PENDING_ONBOARDING\n"
            f"남은 단계: {remaining}\n"
            "자동 온보딩이 계속 진행됩니다."
        )
    return MonitoringItemRead(
        ticker=item.ticker,
        company_name=item.company_name,
        exchange=item.exchange,
        active=item.active,
        monitoring_requested=item.monitoring_requested,
        onboarding_state=item.onboarding_state,
        production_eligible=item.production_eligible,
        onboarding_blockers=blocker_values,
        onboarding_retry_class=item.onboarding_retry_class,
        onboarding_next_retry_at=item.onboarding_next_retry_at,
        registration_status_message=registration_message,
        first_eligible_session=item.first_eligible_session,
        thesis=thesis_to_read(thesis),
        latest_status=latest_status,
        latest_assessment_date=latest_assessment_date,
        latest_valuation_context=latest_valuation_context,
        latest_earnings_estimate_impact=latest_earnings_estimate_impact,
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
    expectations = thesis.market_expectations if thesis else None
    framework = thesis.valuation_framework if thesis else None
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
        market_expectation_level=expectations.level.value if expectations else "unknown",
        market_expectation_summary=expectations.summary if expectations else "",
        valuation_primary_method=framework.primary_method if framework else "",
        multiple_expansion_signals=thesis.multiple_expansion_signals if thesis else [],
        multiple_compression_signals=thesis.multiple_compression_signals if thesis else [],
        latest_status=item.latest_status.value if item.latest_status else "",
        latest_assessment_date=(
            item.latest_assessment_date.isoformat() if item.latest_assessment_date else ""
        ),
        latest_valuation_context=(
            item.latest_valuation_context.value if item.latest_valuation_context else ""
        ),
        latest_earnings_estimate_impact=(
            item.latest_earnings_estimate_impact.value
            if item.latest_earnings_estimate_impact
            else ""
        ),
    )


def record_assessment(
    session: Session,
    ticker: str,
    payload: ThesisAssessmentCreate,
) -> ThesisAssessmentRead | None:
    ticker = normalize_ticker(ticker)
    item = session.exec(select(WatchlistItem).where(WatchlistItem.ticker == ticker)).first()
    thesis = _latest_thesis(session, ticker)
    if item is None or thesis is None:
        return None

    thesis_read = thesis_to_read(thesis)
    assert thesis_read is not None
    market_assessment = payload.market_expectation_assessment
    if market_assessment is None:
        baseline = thesis_read.market_expectations
        market_assessment = MarketExpectationAssessment(
            level=baseline.level if baseline else "unknown",
            assessment="unknown",
            summary=baseline.summary if baseline else "",
            evidence_basis=[],
        )
    valuation_context = ValuationContext(
        impact=payload.valuation_context,
        summary={
            "expansion": "멀티플 확장 조건이 우세합니다.",
            "compression": "멀티플 압축 조건이 우세합니다.",
            "mixed": "멀티플 확장과 압축 근거가 함께 존재합니다.",
            "neutral": "Valuation을 바꿀 중요한 신규 근거가 없습니다.",
            "unknown": "Valuation 영향을 판단할 근거가 부족합니다.",
        }[payload.valuation_context.value],
        market_expectation_level=market_assessment.level,
        market_expectation_summary=market_assessment.summary,
        primary_method=(
            thesis_read.valuation_framework.primary_method
            if thesis_read.valuation_framework
            else ""
        ),
    )
    summary = payload.summary or "저장된 근거를 기준으로 일일 투자 논리 평가를 기록했습니다."
    snapshot = {
        "base_thesis": thesis.core_thesis,
        "thesis_version": thesis.version,
        "effective_date": payload.assessment_date.isoformat(),
        "status": payload.business_thesis_change.value,
        "current_thesis": f"{thesis.core_thesis} 현재 평가: {summary}",
        "thesis_drivers": thesis_read.thesis_drivers,
        "validation_metrics": thesis_read.validation_metrics,
        "price_rules": (
            thesis_read.price_rules.model_dump(mode="json", exclude_none=True)
            if thesis_read.price_rules
            else None
        ),
        "market_expectations": (
            thesis_read.market_expectations.model_dump(mode="json", exclude_none=True)
            if thesis_read.market_expectations
            else None
        ),
        "valuation_framework": (
            thesis_read.valuation_framework.model_dump(mode="json", exclude_none=True)
            if thesis_read.valuation_framework
            else None
        ),
        "multiple_expansion_signals": thesis_read.multiple_expansion_signals,
        "multiple_compression_signals": thesis_read.multiple_compression_signals,
        "valuation_context": valuation_context.model_dump(mode="json"),
        "supporting_evidence": [],
        "weakening_evidence": [],
        "invalidation_evidence": [],
    }
    assessment = session.exec(
        select(ThesisAssessment).where(
            ThesisAssessment.ticker == ticker,
            ThesisAssessment.assessment_date == payload.assessment_date,
        )
    ).first()
    if assessment is None:
        assessment = ThesisAssessment(
            ticker=ticker,
            thesis_version=thesis.version,
            assessment_date=payload.assessment_date,
            status=payload.business_thesis_change.value,
            summary=summary,
            new_buyer_view=payload.new_buyer_view,
            holder_view=payload.holder_view,
            price_view=payload.price_view,
            risk_level=payload.risk_level,
        )
        session.add(assessment)
    assessment.thesis_version = thesis.version
    assessment.status = payload.business_thesis_change.value
    assessment.business_thesis_change = payload.business_thesis_change.value
    assessment.valuation_change = payload.valuation_context.value
    assessment.earnings_estimate_impact = payload.earnings_estimate_impact.value
    assessment.market_expectation_assessment = market_assessment.model_dump_json()
    assessment.confirmed_facts = json.dumps(payload.confirmed_facts, ensure_ascii=False)
    assessment.inferred_implications = json.dumps(
        payload.inferred_implications, ensure_ascii=False
    )
    assessment.unknowns = json.dumps(payload.unknowns, ensure_ascii=False)
    assessment.score = 0
    assessment.confidence = payload.confidence
    assessment.summary = summary
    assessment.new_buyer_view = payload.new_buyer_view
    assessment.holder_view = payload.holder_view
    assessment.price_view = payload.price_view
    assessment.risk_level = payload.risk_level
    assessment.evidence = "[]"
    assessment.price_context = "{}"
    assessment.valuation_context = valuation_context.model_dump_json()
    assessment.thesis_snapshot = json.dumps(snapshot, ensure_ascii=False)
    item.latest_status = payload.business_thesis_change.value
    item.latest_assessment_date = payload.assessment_date
    item.latest_valuation_context = payload.valuation_context.value
    item.latest_earnings_estimate_impact = payload.earnings_estimate_impact.value
    session.flush()
    reconcile_onboarding(session, item)
    session.commit()
    session.refresh(assessment)
    export_assessment_history(session, ticker)
    return assessment_to_read(assessment)


def register_monitoring_item(
    session: Session,
    payload: MonitoringItemCreate,
) -> MonitoringItemRead:
    ticker = normalize_ticker(payload.ticker)
    item = session.exec(select(WatchlistItem).where(WatchlistItem.ticker == ticker)).first()
    was_new = item is None
    if item is None:
        item = WatchlistItem(
            ticker=ticker,
            company_name=payload.company_name,
            exchange=payload.exchange,
            notes="Investment thesis monitoring",
            active=False,
            monitoring_requested=True,
            onboarding_state="PENDING_ONBOARDING",
            production_eligible=False,
        )
        session.add(item)
    else:
        item.company_name = payload.company_name
        item.exchange = payload.exchange

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
        payload.market_expectations.model_dump(mode="json", exclude_none=True)
        if payload.market_expectations
        else {},
        payload.valuation_framework.model_dump(mode="json", exclude_none=True)
        if payload.valuation_framework
        else {},
        payload.multiple_expansion_signals,
        payload.multiple_compression_signals,
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
            _json_dict(active_thesis.market_expectations),
            _json_dict(active_thesis.valuation_framework),
            _json_list(active_thesis.multiple_expansion_signals),
            _json_list(active_thesis.multiple_compression_signals),
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
            market_expectations=json.dumps(
                payload.market_expectations.model_dump(mode="json", exclude_none=True)
                if payload.market_expectations
                else {},
                ensure_ascii=False,
            ),
            valuation_framework=json.dumps(
                payload.valuation_framework.model_dump(mode="json", exclude_none=True)
                if payload.valuation_framework
                else {},
                ensure_ascii=False,
            ),
            multiple_expansion_signals=json.dumps(
                payload.multiple_expansion_signals, ensure_ascii=False
            ),
            multiple_compression_signals=json.dumps(
                payload.multiple_compression_signals, ensure_ascii=False
            ),
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

    requires_onboarding = bool(
        was_new
        or existing_values != requested_values
        or not (
            item.active
            and item.production_eligible
            and item.onboarding_state == "ACTIVE"
        )
    )
    if requires_onboarding:
        begin_onboarding(item)
    session.flush()
    reconcile_onboarding(session, item)
    session.commit()
    session.refresh(item)
    if thesis is not None:
        session.refresh(thesis)
        export_thesis(thesis)
    return _monitoring_item_read(session, item, thesis)


async def register_monitoring_item_with_continuation(
    session: Session,
    payload: MonitoringItemCreate,
) -> MonitoringItemRead:
    initial = register_monitoring_item(session, payload)
    if initial.active and initial.production_eligible:
        return initial
    item = session.exec(
        select(WatchlistItem).where(WatchlistItem.ticker == initial.ticker)
    ).one()
    try:
        async with asyncio.timeout(
            get_settings().onboarding_immediate_timeout_seconds
        ):
            await resume_onboarding_subject(
                session,
                item,
                origin="registration_immediate_continuation",
                mode=OnboardingAttemptMode.IMMEDIATE,
            )
    except TimeoutError:
        session.rollback()
        item = session.exec(
            select(WatchlistItem).where(WatchlistItem.ticker == initial.ticker)
        ).one()
        current = datetime.now(UTC)
        item.onboarding_retry_class = "RETRYABLE"
        item.onboarding_last_attempt_at = current
        item.onboarding_last_attempt_origin = "registration_immediate_continuation"
        item.onboarding_last_error = "TimeoutError:immediate_continuation_timeout"
        item.onboarding_next_retry_at = current + timedelta(
            minutes=get_settings().onboarding_retry_base_minutes
        )
        session.add(item)
        session.commit()
    session.refresh(item)
    return _monitoring_item_read(session, item, _latest_thesis(session, item.ticker))


def list_monitoring_items(session: Session, active_only: bool = True) -> list[MonitoringItemRead]:
    query = select(WatchlistItem)
    if active_only:
        query = query.where(
            WatchlistItem.active.is_(True),
            WatchlistItem.production_eligible.is_(True),
            WatchlistItem.onboarding_state == "ACTIVE",
        )
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
    deactivate_onboarding(item)
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
