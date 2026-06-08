import json
import logging
import re
from datetime import date, timedelta

from sqlmodel import Session, select

from app.config import get_settings
from app.models.company import Company
from app.models.event import Event
from app.models.financial import FinancialSnapshot
from app.providers.base import RawEvent
from app.providers.mock import MockProvider
from app.providers.registry import provider_priority
from app.schemas.company import CompanyProfile
from app.schemas.event import FinancialImpact, ThesisEvent, ThesisEventResponse
from app.schemas.financial import EarningsCheckpointResponse
from app.services.event_classifier import classify_event
from app.services.event_interpreter import enrich_raw_event
from app.services.financial_snapshot_service import upsert_financial_snapshot_from_event
from app.services.thesis_scoring import score_event

logger = logging.getLogger(__name__)


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
        financial_impact=FinancialImpact(
            revenue_guidance_changed=event.revenue_guidance_changed,
            margin_guidance_changed=event.margin_guidance_changed,
            margin_quality_review=event.margin_quality_review,
            financial_statement_basis_warning=event.financial_statement_basis_warning,
            fcf_impact_known=event.fcf_impact_known,
            dilution_risk=event.dilution_risk,
            capex_impact_known=event.capex_impact_known,
            inventory_risk=event.inventory_risk,
            receivables_risk=event.receivables_risk,
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
    return Event(
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
        revenue_guidance_changed="guidance" in lower_text or "가이던스" in lower_text,
        margin_guidance_changed="margin" in lower_text or "마진" in lower_text,
        margin_quality_review=margin_quality_review,
        financial_statement_basis_warning=basis_warning,
        fcf_impact_known="fcf" in lower_text or "free cash flow" in lower_text,
        dilution_risk=event_type.value in {"capital_raise", "convertible_bond", "warrant"},
        capex_impact_known="capex" in lower_text or "capital expenditure" in lower_text,
        inventory_risk="inventory" in lower_text or "재고" in lower_text,
        receivables_risk="receivables" in lower_text or "accounts receivable" in lower_text or "매출채권" in lower_text,
        requires_review=relevance.requires_review,
        relevance_score=relevance.relevance_score,
        relevance_reason=relevance.reason,
    )


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
    duplicate.revenue_guidance_changed = event.revenue_guidance_changed
    duplicate.margin_guidance_changed = event.margin_guidance_changed
    duplicate.margin_quality_review = event.margin_quality_review
    duplicate.financial_statement_basis_warning = event.financial_statement_basis_warning
    duplicate.fcf_impact_known = event.fcf_impact_known
    duplicate.dilution_risk = event.dilution_risk
    duplicate.capex_impact_known = event.capex_impact_known
    duplicate.inventory_risk = event.inventory_risk
    duplicate.receivables_risk = event.receivables_risk
    duplicate.requires_review = event.requires_review
    duplicate.relevance_score = event.relevance_score
    duplicate.relevance_reason = event.relevance_reason


class CollectionService:
    def __init__(self) -> None:
        settings = get_settings()
        self.providers = provider_priority(
            include_live_news=settings.enable_live_providers,
            include_mock_provider=settings.include_mock_provider,
        )
        self.profile_fallback_provider = MockProvider()

    async def collect_events(self, session: Session, ticker: str, lookback_days: int) -> list[Event]:
        ticker = ticker.upper()
        collected: list[Event] = []
        seen_urls: set[str] = set()
        seen_titles: set[str] = set()
        for provider in self.providers:
            try:
                raw_events = await provider.fetch_events(ticker, lookback_days)
            except Exception as exc:  # noqa: BLE001
                logger.warning("Provider %s failed for %s: %s", provider.name, ticker, exc)
                continue
            for raw_event in raw_events:
                title_key = _normalize_title(raw_event.title)
                if raw_event.url in seen_urls or title_key in seen_titles:
                    continue
                seen_urls.add(raw_event.url)
                seen_titles.add(title_key)
                event = _raw_event_to_model(raw_event)
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
                    _sync_financial_quality_flags(event)
                    collected.append(event)
                else:
                    _refresh_duplicate_event(duplicate, event)
                    upsert_financial_snapshot_from_event(session, duplicate)
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
    ) -> ThesisEventResponse:
        ticker = ticker.upper()
        await self.collect_events(session, ticker, lookback_days)
        cutoff = date.today() - timedelta(days=lookback_days)
        query = select(Event).where(Event.ticker == ticker, Event.date >= cutoff)
        if requires_review_only:
            query = query.where(Event.requires_review.is_(True))
        if provider:
            query = query.where(Event.provider == provider)
        events = list(session.exec(query.order_by(Event.date.desc(), Event.relevance_score.desc())).all())
        company = session.exec(select(Company).where(Company.ticker == ticker)).first()
        company_name = company.company_name if company else (events[0].company_name if events else None)
        return ThesisEventResponse(
            ticker=ticker,
            company_name=company_name,
            lookback_days=lookback_days,
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
        ticker = ticker.upper()
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
        return CompanyProfile(ticker=ticker, company_name=ticker)

    async def get_earnings_checkpoints(
        self, session: Session, ticker: str
    ) -> EarningsCheckpointResponse:
        ticker = ticker.upper()
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
            return EarningsCheckpointResponse(
                ticker=ticker,
                checkpoints=[
                    "Revenue growth vs guidance",
                    "Gross margin and operating margin",
                    "FCF after capex",
                    "Inventory and receivables trend",
                    "Customer concentration and demand signals",
                ],
            )
        return EarningsCheckpointResponse(ticker=ticker, checkpoints=[])
