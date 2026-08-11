import asyncio
import json
import logging
import re
from datetime import date, timedelta

from sqlmodel import Session, select

from app.config import get_settings
from app.models.company import Company
from app.models.event import Event
from app.models.financial import FinancialSnapshot
from app.models.watchlist import WatchlistItem
from app.providers.base import RawEvent
from app.providers.mock import MockProvider
from app.providers.registry import provider_priority
from app.schemas.company import CompanyProfile
from app.schemas.event import (
    BackfillStatus,
    EventFinancialMetrics,
    FinancialImpact,
    ThesisEvent,
    ThesisEventResponse,
)
from app.schemas.financial import EarningsCheckpoint, EarningsCheckpointResponse
from app.services.event_classifier import classify_event
from app.services.event_identity import event_fingerprint
from app.services.event_interpreter import enrich_raw_event
from app.services.event_relevance_service import (
    EventRelevanceService,
    extract_structured_flags,
)
from app.services.financial_backfill_service import backfill_financial_snapshots
from app.services.financial_validation import validate_event_financials
from app.services.financial_snapshot_service import upsert_financial_snapshot_from_event
from app.services.capital_action_service import CapitalActionService
from app.services.dividend_history_service import DividendHistoryService
from app.services.security_master_service import SecurityMasterService
from app.services.thesis_scoring import score_event
from app.utils.tickers import COMPANY_NAME_ALIASES, normalize_ticker

logger = logging.getLogger(__name__)
MIN_COMPARABLE_SNAPSHOTS = 2
def _list_from_text(value: str | None) -> list[str]:
    if not value:
        return []
    return [part.strip() for part in value.split(",") if part.strip()]


def _normalize_title(value: str) -> str:
    normalized = re.sub(r"[^a-z0-9가-힣]+", " ", value.lower())
    return re.sub(r"\s+", " ", normalized).strip()


def _json_list(value: str | None) -> list[str]:
    if not value:
        return []
    try:
        parsed = json.loads(value)
    except json.JSONDecodeError:
        return []
    return parsed if isinstance(parsed, list) else []


def _quality_flags_from_lists(unknowns: list[str], implications: list[str]) -> tuple[bool, bool]:
    text = " ".join([*unknowns, *implications]).lower()
    margin_quality_review = "margin" in text and "quality warning" in text
    financial_statement_basis_warning = (
        "basis" in text and "warning" in text
    ) or "verify basis consistency" in text
    return margin_quality_review, financial_statement_basis_warning


def _sync_financial_quality_flags(event: Event) -> None:
    margin_quality_review, basis_warning = _quality_flags_from_lists(
        _json_list(event.unknowns),
        _json_list(event.inferred_implications),
    )
    event.margin_quality_review = margin_quality_review
    event.financial_statement_basis_warning = basis_warning


def _event_to_schema(event: Event) -> ThesisEvent:
    _sync_financial_quality_flags(event)
    return ThesisEvent(
        date=event.date,
        source=event.source,
        provider=event.provider if event.provider != "unknown" else "legacy",
        title=event.title,
        url=event.url,
        event_type=event.event_type,
        confirmed_facts=json.loads(event.confirmed_facts),
        inferred_implications=json.loads(event.inferred_implications),
        unknowns=json.loads(event.unknowns),
        financial_metrics=EventFinancialMetrics(
            revenue=event.revenue,
            operating_income=event.operating_income,
            net_income=event.net_income,
            operating_margin=event.operating_margin,
            yoy_growth=event.yoy_growth,
            qoq_growth=event.qoq_growth,
            capex_amount=event.capex_amount,
            financing_amount=event.financing_amount,
            dilution_amount=event.dilution_amount,
        ),
        financial_impact=FinancialImpact(
            revenue_guidance_changed=event.revenue_guidance_changed,
            margin_guidance_changed=event.margin_guidance_changed,
            guidance_changed=event.guidance_changed,
            earnings_guidance_changed=event.earnings_guidance_changed,
            cash_flow_guidance_changed=event.cash_flow_guidance_changed,
            major_order_change=event.major_order_change,
            production_delay=event.production_delay,
            material_customer_change=event.material_customer_change,
            operating_cash_flow_impact_known=event.operating_cash_flow_impact_known,
            margin_quality_review=event.margin_quality_review,
            financial_statement_basis_warning=event.financial_statement_basis_warning,
            fcf_impact_known=event.fcf_impact_known,
            dilution_risk=event.dilution_risk,
            debt_liquidity_risk=event.debt_liquidity_risk,
            accounting_issue=event.accounting_issue,
            regulatory_material=event.regulatory_material,
            financial_report_filed=event.financial_report_filed,
            capex_impact_known=event.capex_impact_known,
            inventory_risk=event.inventory_risk,
            receivables_risk=event.receivables_risk,
            buyback_candidate=event.buyback_candidate,
            confirmed_buyback=event.confirmed_buyback,
        ),
        thesis_relevance={
            "requires_review": event.requires_review,
            "relevance_score": event.relevance_score,
            "reason": event.relevance_reason,
        },
    )


def _raw_event_to_model(raw_event: RawEvent) -> Event:
    raw_event = enrich_raw_event(raw_event)
    event_type = classify_event(raw_event)
    relevance = score_event(raw_event, event_type)
    lower_text = f"{raw_event.title} {raw_event.summary} {' '.join(raw_event.confirmed_facts)}".lower()
    unknowns = list(raw_event.unknowns)
    implications = list(raw_event.inferred_implications)
    margin_quality_review, basis_warning = _quality_flags_from_lists(unknowns, implications)
    event = Event(
        ticker=raw_event.ticker.upper(),
        company_name=raw_event.company_name,
        date=raw_event.date,
        source=raw_event.source,
        provider=raw_event.provider,
        title=raw_event.title,
        url=raw_event.url,
        raw_summary=raw_event.summary,
        event_type=event_type.value,
        keywords=json.dumps(raw_event.keywords),
        confirmed_facts=json.dumps(raw_event.confirmed_facts),
        inferred_implications=json.dumps(implications),
        unknowns=json.dumps(unknowns),
        revenue=raw_event.revenue,
        operating_income=raw_event.operating_income,
        net_income=raw_event.net_income,
        operating_margin=raw_event.operating_margin,
        yoy_growth=raw_event.yoy_growth,
        qoq_growth=raw_event.qoq_growth,
        capex_amount=raw_event.capex_amount,
        financing_amount=raw_event.financing_amount,
        dilution_amount=raw_event.dilution_amount,
        revenue_guidance_changed=raw_event.revenue_guidance_changed,
        margin_guidance_changed=raw_event.margin_guidance_changed or "margin" in lower_text or "마진" in lower_text,
        guidance_changed=raw_event.guidance_changed or "guidance" in lower_text or "가이던스" in lower_text,
        earnings_guidance_changed=raw_event.earnings_guidance_changed,
        cash_flow_guidance_changed=raw_event.cash_flow_guidance_changed,
        major_order_change=raw_event.major_order_change,
        production_delay=raw_event.production_delay or event_type.value == "production_delay",
        material_customer_change=raw_event.material_customer_change,
        operating_cash_flow_impact_known=(
            raw_event.operating_cash_flow_impact_known
            or "operating cash flow" in lower_text
            or "cash from operations" in lower_text
        ),
        margin_quality_review=margin_quality_review,
        financial_statement_basis_warning=basis_warning,
        fcf_impact_known=raw_event.fcf_impact_known or "fcf" in lower_text or "free cash flow" in lower_text,
        dilution_risk=raw_event.dilution_risk or event_type.value in {"capital_raise", "convertible_bond", "warrant", "dilution"},
        debt_liquidity_risk=raw_event.debt_liquidity_risk or event_type.value in {"debt_liquidity", "debt_liquidity_risk"},
        accounting_issue=raw_event.accounting_issue or event_type.value == "accounting_issue",
        regulatory_material=raw_event.regulatory_material or event_type.value == "regulatory_material",
        financial_report_filed=raw_event.financial_report_filed,
        capex_impact_known="capex" in lower_text or "capital expenditure" in lower_text,
        inventory_risk="inventory" in lower_text or "재고" in lower_text,
        receivables_risk="receivables" in lower_text or "accounts receivable" in lower_text or "매출채권" in lower_text,
        requires_review=relevance.requires_review,
        relevance_score=relevance.relevance_score,
        relevance_reason=relevance.reason,
        identity_validated=raw_event.identity_validated,
        identity_status=raw_event.identity_status,
        subject_company_id=raw_event.subject_ticker or raw_event.subject_company_name,
        relevance_evidence=json.dumps(raw_event.relevance_evidence, ensure_ascii=False),
        rejected_reason=raw_event.rejected_reason,
        buyback_candidate=raw_event.buyback_candidate,
        confirmed_buyback=raw_event.confirmed_buyback,
    )
    structured_material = any(
        (
            raw_event.guidance_changed,
            raw_event.revenue_guidance_changed,
            raw_event.margin_guidance_changed,
            raw_event.earnings_guidance_changed,
            raw_event.cash_flow_guidance_changed,
            raw_event.fcf_impact_known,
            raw_event.material_customer_change,
            raw_event.major_order_change,
            raw_event.production_delay,
            raw_event.dilution_risk,
            raw_event.debt_liquidity_risk,
            raw_event.accounting_issue,
            raw_event.regulatory_material,
            raw_event.financial_report_filed,
            raw_event.buyback_candidate,
            raw_event.confirmed_buyback,
        )
    )
    if structured_material and event_type.value != "non_thesis_noise":
        event.classification_override_reason = "structured_material_flag"
    event.financial_refresh_required = event_type.value in {
        "earnings_beat",
        "earnings_miss",
        "earnings_surprise",
        "guidance_change",
        "revenue_guidance_change",
        "margin_guidance_change",
        "financial_report",
    }
    validate_event_financials(
        event,
        operating_margin_upper_bound=get_settings().financial_operating_margin_upper_bound,
    )
    return event


def _refresh_duplicate_event(duplicate: Event, event: Event) -> None:
    duplicate.company_name = event.company_name or duplicate.company_name
    duplicate.source = event.source or duplicate.source
    duplicate.provider = event.provider or duplicate.provider
    duplicate.raw_summary = event.raw_summary or duplicate.raw_summary
    duplicate.event_type = event.event_type
    duplicate.keywords = event.keywords
    duplicate.confirmed_facts = event.confirmed_facts
    duplicate.inferred_implications = event.inferred_implications
    duplicate.unknowns = event.unknowns
    duplicate.revenue = event.revenue
    duplicate.operating_income = event.operating_income
    duplicate.net_income = event.net_income
    duplicate.operating_margin = event.operating_margin
    duplicate.yoy_growth = event.yoy_growth
    duplicate.qoq_growth = event.qoq_growth
    duplicate.capex_amount = event.capex_amount
    duplicate.financing_amount = event.financing_amount
    duplicate.dilution_amount = event.dilution_amount
    duplicate.revenue_guidance_changed = event.revenue_guidance_changed
    duplicate.margin_guidance_changed = event.margin_guidance_changed
    duplicate.guidance_changed = event.guidance_changed
    duplicate.earnings_guidance_changed = event.earnings_guidance_changed
    duplicate.cash_flow_guidance_changed = event.cash_flow_guidance_changed
    duplicate.major_order_change = event.major_order_change
    duplicate.production_delay = event.production_delay
    duplicate.material_customer_change = event.material_customer_change
    duplicate.operating_cash_flow_impact_known = event.operating_cash_flow_impact_known
    duplicate.margin_quality_review = event.margin_quality_review
    duplicate.financial_statement_basis_warning = event.financial_statement_basis_warning
    duplicate.fcf_impact_known = event.fcf_impact_known
    duplicate.dilution_risk = event.dilution_risk
    duplicate.debt_liquidity_risk = event.debt_liquidity_risk
    duplicate.accounting_issue = event.accounting_issue
    duplicate.regulatory_material = event.regulatory_material
    duplicate.financial_report_filed = event.financial_report_filed
    duplicate.capex_impact_known = event.capex_impact_known
    duplicate.inventory_risk = event.inventory_risk
    duplicate.receivables_risk = event.receivables_risk
    duplicate.requires_review = event.requires_review
    duplicate.relevance_score = event.relevance_score
    duplicate.relevance_reason = event.relevance_reason
    duplicate.classification_override_reason = event.classification_override_reason
    duplicate.financial_refresh_required = event.financial_refresh_required
    duplicate.identity_validated = event.identity_validated
    duplicate.identity_status = event.identity_status
    duplicate.subject_company_id = event.subject_company_id
    duplicate.relevance_evidence = event.relevance_evidence
    duplicate.rejected_reason = event.rejected_reason
    duplicate.buyback_candidate = event.buyback_candidate
    duplicate.confirmed_buyback = event.confirmed_buyback


class CollectionService:
    def __init__(self) -> None:
        settings = get_settings()
        self.providers = provider_priority(
            include_live_news=settings.enable_live_providers,
            include_mock_provider=settings.include_mock_provider,
        )
        self.profile_fallback_provider = MockProvider()
        self.dividend_service = DividendHistoryService()
        self.capital_action_service = CapitalActionService()
        self.security_service = SecurityMasterService()
        self.relevance_service = EventRelevanceService()

    def _connect_event_data(self, session: Session, event: Event) -> None:
        self.dividend_service.ingest_event(session, event)
        self.capital_action_service.reconcile_identity(session, event)
        self.capital_action_service.canonicalize(session, event)

    async def _fetch_provider_events(
        self,
        provider,
        ticker: str,
        lookback_days: int,
    ) -> list[RawEvent]:
        settings = get_settings()
        attempts = max(1, settings.monitor_retry_attempts)
        last_error: Exception | None = None
        for attempt in range(attempts):
            try:
                return await provider.fetch_events(ticker, lookback_days)
            except Exception as exc:  # noqa: BLE001
                last_error = exc
                if attempt + 1 < attempts:
                    delay = settings.monitor_retry_base_seconds * (2**attempt)
                    if delay > 0:
                        await asyncio.sleep(delay)
        assert last_error is not None
        raise last_error

    def _snapshot_count(self, session: Session, ticker: str, provider: str | None) -> int:
        query = select(FinancialSnapshot).where(FinancialSnapshot.ticker == ticker)
        if provider:
            query = query.where(FinancialSnapshot.provider == provider)
        return len(session.exec(query).all())

    async def _maybe_backfill_financial_snapshots(
        self,
        session: Session,
        ticker: str,
        provider: str | None,
        auto_backfill: bool,
        backfill_years: int,
    ) -> BackfillStatus:
        backfill_provider = provider or "opendart"
        before_count = self._snapshot_count(session, ticker, backfill_provider)
        status = BackfillStatus(
            requested=auto_backfill,
            provider=backfill_provider,
            years=backfill_years,
            snapshot_count_before=before_count,
            snapshot_count_after=before_count,
        )
        if not auto_backfill:
            return status
        if backfill_provider != "opendart":
            status.skipped = True
            status.reason = "unsupported_provider"
            return status
        if before_count >= MIN_COMPARABLE_SNAPSHOTS:
            status.skipped = True
            status.reason = "sufficient_snapshots"
            return status
        result = await backfill_financial_snapshots(
            session=session,
            ticker=ticker,
            years=backfill_years,
            provider=backfill_provider,
        )
        after_count = self._snapshot_count(session, ticker, backfill_provider)
        status.executed = True
        status.reason = "executed"
        status.snapshot_count_after = after_count
        status.backfilled_count = result.backfilled_count
        status.report_count = result.report_count
        status.warnings = result.warnings
        return status

    async def collect_events(self, session: Session, ticker: str, lookback_days: int) -> list[Event]:
        ticker = normalize_ticker(ticker)
        company = session.exec(select(Company).where(Company.ticker == ticker)).first()
        watchlist_item = session.exec(
            select(WatchlistItem).where(WatchlistItem.ticker == ticker)
        ).first()
        company_name = (
            (company.company_name if company else None)
            or (watchlist_item.company_name if watchlist_item else None)
            or COMPANY_NAME_ALIASES.get(ticker)
        )
        target_security = self.security_service.ensure(session, ticker)
        collected: list[Event] = []
        seen_urls: set[str] = set()
        seen_titles: set[str] = set()
        seen_fingerprints: set[str] = set()
        for provider in self.providers:
            try:
                raw_events = await self._fetch_provider_events(provider, ticker, lookback_days)
            except Exception as exc:  # noqa: BLE001
                logger.warning("Provider %s failed for %s: %s", provider.name, ticker, exc)
                continue
            for raw_event in raw_events:
                verdict = self.relevance_service.validate(
                    session, raw_event, target_security
                )
                raw_event.identity_validated = verdict.accepted
                raw_event.identity_status = verdict.status
                raw_event.subject_company_name = verdict.subject_company_id
                raw_event.relevance_evidence = verdict.evidence
                raw_event.rejected_reason = verdict.reason
                if verdict.accepted:
                    extract_structured_flags(raw_event)
                else:
                    self.relevance_service.clear_material_flags(raw_event)
                if not raw_event.company_name:
                    raw_event.company_name = company_name
                title_key = _normalize_title(raw_event.title)
                if raw_event.url in seen_urls or title_key in seen_titles:
                    continue
                seen_urls.add(raw_event.url)
                seen_titles.add(title_key)
                event = _raw_event_to_model(raw_event)
                fingerprint = event_fingerprint(event)
                if fingerprint in seen_fingerprints:
                    continue
                seen_fingerprints.add(fingerprint)
                candidates = session.exec(
                    select(Event).where(
                        Event.ticker == event.ticker,
                        Event.date == event.date,
                        Event.event_type == event.event_type,
                        Event.provider == event.provider,
                    )
                ).all()
                duplicate = next(
                    (item for item in candidates if event_fingerprint(item) == fingerprint),
                    None,
                )
                if duplicate is None:
                    duplicate = session.exec(
                        select(Event).where(
                            Event.ticker == event.ticker,
                            (Event.url == event.url) | (Event.title == event.title),
                        )
                    ).first()
                if duplicate is None:
                    session.add(event)
                    session.flush()
                    upsert_financial_snapshot_from_event(session, event)
                    self._connect_event_data(session, event)
                    _sync_financial_quality_flags(event)
                    collected.append(event)
                else:
                    _refresh_duplicate_event(duplicate, event)
                    upsert_financial_snapshot_from_event(session, duplicate)
                    self._connect_event_data(session, duplicate)
                    _sync_financial_quality_flags(duplicate)
        session.commit()
        return collected

    async def get_thesis_events(
        self,
        session: Session,
        ticker: str,
        lookback_days: int,
        requires_review_only: bool = False,
        provider: str | None = None,
        auto_backfill: bool = False,
        backfill_years: int = 5,
    ) -> ThesisEventResponse:
        ticker = normalize_ticker(ticker)
        backfill_status = await self._maybe_backfill_financial_snapshots(
            session=session,
            ticker=ticker,
            provider=provider,
            auto_backfill=auto_backfill,
            backfill_years=backfill_years,
        )
        await self.collect_events(session, ticker, lookback_days)
        cutoff = date.today() - timedelta(days=lookback_days)
        query = select(Event).where(Event.ticker == ticker, Event.date >= cutoff)
        if requires_review_only:
            query = query.where(Event.requires_review.is_(True))
        if provider:
            query = query.where(Event.provider == provider)
        events = list(session.exec(query.order_by(Event.date.desc(), Event.relevance_score.desc())).all())
        company = session.exec(select(Company).where(Company.ticker == ticker)).first()
        company_name = (
            (company.company_name if company else None)
            or (events[0].company_name if events else None)
            or COMPANY_NAME_ALIASES.get(ticker)
        )
        backfill_status.snapshot_count_after = self._snapshot_count(session, ticker, backfill_status.provider)
        return ThesisEventResponse(
            ticker=ticker,
            company_name=company_name,
            lookback_days=lookback_days,
            backfill_status=backfill_status,
            events=[_event_to_schema(event) for event in events],
        )

    def _company_model_to_profile(self, company: Company) -> CompanyProfile:
        return CompanyProfile(
            ticker=company.ticker,
            company_name=company.company_name,
            exchange=company.exchange,
            industry=company.industry,
            sector=company.sector,
            business_units=_list_from_text(company.business_units),
            major_revenue_sources=_list_from_text(company.revenue_sources),
            major_customers=_list_from_text(company.major_customers),
            ir_url=company.ir_url,
            filings_url=company.filings_url,
        )

    async def get_company_profile(self, session: Session, ticker: str) -> CompanyProfile:
        ticker = normalize_ticker(ticker)
        company = session.exec(select(Company).where(Company.ticker == ticker)).first()
        if company is not None:
            return self._company_model_to_profile(company)
        for provider in self.providers:
            try:
                profile = await provider.fetch_company_profile(ticker)
            except Exception as exc:  # noqa: BLE001
                logger.warning("Provider %s profile lookup failed for %s: %s", provider.name, ticker, exc)
                continue
            if profile is not None:
                return profile
        fallback_profile = await self.profile_fallback_provider.fetch_company_profile(ticker)
        if fallback_profile is not None:
            return fallback_profile
        return CompanyProfile(ticker=ticker, company_name=COMPANY_NAME_ALIASES.get(ticker, ticker))

    async def get_earnings_checkpoints(
        self, session: Session, ticker: str
    ) -> EarningsCheckpointResponse:
        ticker = normalize_ticker(ticker)
        for provider in self.providers:
            try:
                response = await provider.fetch_earnings(ticker)
            except Exception as exc:  # noqa: BLE001
                logger.warning("Provider %s earnings lookup failed for %s: %s", provider.name, ticker, exc)
                continue
            if response is not None:
                return response
        fallback_response = await self.profile_fallback_provider.fetch_earnings(ticker)
        if fallback_response is not None:
            return fallback_response
        snapshots = session.exec(
            select(FinancialSnapshot)
            .where(FinancialSnapshot.ticker == ticker)
            .order_by(FinancialSnapshot.reported_date.desc())
        ).all()
        if snapshots:
            latest = snapshots[0]
            previous = snapshots[1] if len(snapshots) > 1 else None
            revenue_growth = None
            if (
                previous is not None
                and latest.revenue is not None
                and previous.revenue not in {None, 0}
            ):
                revenue_growth = (latest.revenue / previous.revenue - 1) * 100
            return EarningsCheckpointResponse(
                ticker=ticker,
                checkpoints=[
                    "Revenue growth vs guidance",
                    "Gross margin and operating margin",
                    "FCF after capex",
                    "Inventory and receivables trend",
                    "Customer concentration and demand signals",
                ],
                latest=EarningsCheckpoint(
                    ticker=ticker,
                    period=latest.period,
                    reported_date=latest.reported_date,
                    revenue=latest.revenue,
                    operating_income=latest.operating_income,
                    net_income=latest.net_income,
                    eps=latest.eps,
                    operating_cash_flow=latest.operating_cash_flow,
                    fcf=latest.fcf,
                    free_cash_flow=latest.fcf,
                    capex=latest.capex,
                    gross_margin=latest.gross_margin,
                    operating_margin=latest.operating_margin,
                    guidance=latest.guidance,
                    backlog=latest.backlog,
                    inventory=latest.inventory,
                    accounts_receivable=latest.accounts_receivable,
                    debt=latest.debt,
                    cash=latest.cash,
                    stock_based_compensation=latest.stock_based_compensation,
                    dilution_notes=latest.dilution_notes,
                    revenue_growth=revenue_growth,
                ),
                provider_status="available",
            )
        return EarningsCheckpointResponse(
            ticker=ticker,
            checkpoints=[],
            provider_status="unavailable",
            unavailable_reason="No provider earnings response or stored financial snapshot is available.",
        )
