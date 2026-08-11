import asyncio
from datetime import date, datetime, timedelta, timezone

import httpx
from sqlmodel import Session, SQLModel, create_engine, select

from app.models.event import CanonicalIssue, Event
from app.models.financial import DividendHistory, FinancialSnapshot, HistoricalValuationObservation
from app.models.security import ConsensusEstimate, SecurityMaster, ShareCountObservation
from app.models.watchlist import WatchlistItem
from app.providers.base import RawEvent
from app.schemas.thesis import ValuationSnapshot
from app.services.alpha_vantage_service import AlphaVantageService
from app.services.event_classifier import classify_event
from app.services.event_relevance_service import EventRelevanceService, extract_structured_flags
from app.services.financial_freshness_service import FinancialFreshnessService
from app.services.historical_valuation_service import HistoricalValuationService
from app.services.issue_identity_audit_service import IssueIdentityAuditService
from app.services.security_master_service import SecurityMasterService


def _engine():
    engine = create_engine("sqlite://")
    SQLModel.metadata.create_all(engine)
    return engine


def _security(session: Session, ticker: str, name: str) -> SecurityMaster:
    session.add(
        WatchlistItem(
            ticker=ticker,
            company_name=name,
            exchange="NYSE",
            active=True,
        )
    )
    session.flush()
    return SecurityMasterService().ensure(session, ticker)


def test_tsm_intel_capital_raise_is_rejected_before_material_flags() -> None:
    engine = _engine()
    raw = RawEvent(
        ticker="TSM",
        company_name=None,
        date=date.today(),
        source="News",
        provider="naver_news",
        title="Capital raise expectations focus on Intel (INTC)",
        url="https://example.com/intel",
        summary="Intel considers an equity offering. TSMC is not the transaction subject.",
        dilution_risk=True,
    )
    with Session(engine) as session:
        target = _security(session, "TSM", "TSMC")
        verdict = EventRelevanceService().validate(session, raw, target)
        if not verdict.accepted:
            EventRelevanceService.clear_material_flags(raw)
        raw.identity_status = verdict.status
        raw.identity_validated = verdict.accepted

    assert verdict.accepted is False
    assert raw.dilution_risk is False
    assert classify_event(raw).value == "non_thesis_noise"


def test_sndk_relevant_revenue_guidance_cannot_be_noise() -> None:
    engine = _engine()
    raw = RawEvent(
        ticker="SNDK",
        company_name=None,
        date=date.today(),
        source="News",
        provider="google_news_rss",
        title="SanDisk revenue forecast falls below expectations",
        url="https://example.com/sndk-guidance",
        summary="SNDK lowered its revenue outlook after reporting results.",
    )
    with Session(engine) as session:
        target = _security(session, "SNDK", "SanDisk")
        verdict = EventRelevanceService().validate(session, raw, target)
        raw.identity_validated = verdict.accepted
        raw.identity_status = verdict.status
        extract_structured_flags(raw)

    assert raw.guidance_changed is True
    assert raw.revenue_guidance_changed is True
    assert classify_event(raw).value == "revenue_guidance_change"


def test_news_buyback_is_candidate_until_officially_verified() -> None:
    engine = _engine()
    raw = RawEvent(
        ticker="SNDK",
        company_name=None,
        date=date.today(),
        source="News",
        provider="google_news_rss",
        title="SanDisk announces a share repurchase authorization",
        url="https://example.com/sndk-buyback",
        summary="SNDK discussed a new buyback plan.",
    )
    with Session(engine) as session:
        target = _security(session, "SNDK", "SanDisk")
        verdict = EventRelevanceService().validate(session, raw, target)
        raw.identity_validated = verdict.accepted
        raw.identity_status = verdict.status
        extract_structured_flags(raw)

    assert raw.buyback_candidate is True
    assert raw.confirmed_buyback is False
    assert classify_event(raw).value == "capital_allocation"


def test_open_issue_identity_audit_resolves_wrong_company_warning() -> None:
    engine = _engine()
    with Session(engine) as session:
        _security(session, "TSM", "TSMC")
        event = Event(
            ticker="TSM",
            date=date.today(),
            source="News",
            provider="naver_news",
            title="Intel capital raise plan",
            url="https://example.com/intel-raise",
            raw_summary="Intel is the transaction subject.",
            event_type="capital_raise",
            confirmed_facts="[]",
            dilution_risk=True,
            issue_id="wrong-issue",
            corporate_action_id="wrong-issue",
        )
        issue = CanonicalIssue(
            ticker="TSM",
            issue_key="wrong-issue",
            issue_type="capital_raise",
            opened_date=date.today(),
            updated_date=date.today(),
            latest_event_date=date.today(),
            title="capital raise warning",
            economic_status="open",
        )
        session.add(event)
        session.add(issue)
        session.commit()
        resolved = IssueIdentityAuditService().audit(session, "TSM")
        session.commit()
        issue_status = session.get(CanonicalIssue, issue.id).economic_status
        event_type = session.get(Event, event.id).event_type
        dilution_risk = session.get(Event, event.id).dilution_risk

    assert resolved == 1
    assert issue_status == "resolved"
    assert event_type == "non_thesis_noise"
    assert dilution_risk is False


def test_full_and_preliminary_financial_periods_are_separate() -> None:
    engine = _engine()
    with Session(engine) as session:
        session.add(
            FinancialSnapshot(
                ticker="PRELIM",
                period="2026-Q1",
                snapshot_type="full_statement",
                financial_period_end=date(2026, 3, 31),
                filing_date=date(2026, 5, 15),
            )
        )
        session.add(
            FinancialSnapshot(
                ticker="PRELIM",
                period="2026-Q2",
                snapshot_type="preliminary_earnings",
                financial_period_end=date(2026, 6, 30),
                filing_date=date(2026, 7, 25),
            )
        )
        session.add(
            Event(
                ticker="PRELIM",
                date=date(2026, 7, 25),
                source="Company",
                provider="opendart",
                title="Q2 preliminary earnings",
                url="https://example.com/prelim",
                event_type="guidance_change",
                confirmed_facts="[]",
                guidance_changed=True,
            )
        )
        session.commit()
        state = FinancialFreshnessService().assess(session, "PRELIM")

    assert state.latest_full_period == date(2026, 3, 31)
    assert state.latest_preliminary_period == date(2026, 6, 30)
    assert state.refresh_result == "preliminary_only"


def test_historical_distribution_deduplicates_iso_weeks() -> None:
    observations = []
    start = date(2025, 1, 6)
    for week in range(52):
        for offset in (0, 3):
            observations.append(
                HistoricalValuationObservation(
                    ticker="WEEKLY",
                    observation_date=start + timedelta(days=7 * week + offset),
                    price=10,
                    trailing_pe=10 + week / 10,
                )
            )
    snapshot = ValuationSnapshot(trailing_pe=12)
    HistoricalValuationService().apply(
        snapshot, observations, {"primary_method": "forward P/E"}, "WEEKLY"
    )

    stats = snapshot.historical_pe_statistics
    assert stats is not None
    assert stats.raw_observation_count == 104
    assert stats.deduplicated_observation_count == 52
    assert stats.current_percentile is not None
    assert stats.sampling_frequency == "weekly_last_valid_close"


def test_alpha_vantage_estimates_shares_dividends_and_splits_are_cached() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        function = request.url.params["function"]
        payloads = {
            "EARNINGS_ESTIMATES": {
                "annualEarningsEstimates": [
                    {
                        "fiscalDateEnding": "2027-12-31",
                        "estimatedEPS": "12.5",
                        "estimatedEPSHigh": "13.0",
                        "estimatedEPSLow": "11.8",
                        "numberOfAnalysts": "20",
                    }
                ]
            },
            "SHARES_OUTSTANDING": {
                "annualReports": [
                    {"fiscalDateEnding": "2025-12-31", "reportedSharesOutstanding": "1000"}
                ]
            },
            "DIVIDENDS": {
                "data": [
                    {"recordDate": "2025-03-01", "paymentDate": "2025-03-20", "amount": "0.25"}
                ]
            },
            "SPLITS": {"data": [{"effectiveDate": "2025-01-01", "splitFactor": "2:1"}]},
            "OVERVIEW": {"PERatio": "20", "ForwardPE": "18", "PriceToBookRatio": "5"},
        }
        return httpx.Response(200, json=payloads[function])

    engine = _engine()
    service = AlphaVantageService(transport=httpx.MockTransport(handler))
    service.settings.alpha_vantage_api_key = "test"
    service.__class__._request_count = 0
    service.__class__._request_date = datetime.now(timezone.utc).date()
    with Session(engine) as session:
        bundle = asyncio.run(service.collect(session, "GOOGL"))
        session.commit()
        estimate = session.exec(select(ConsensusEstimate)).one()
        shares = session.exec(select(ShareCountObservation)).one()
        dividend = session.exec(select(DividendHistory)).one()

    assert all(status == "fresh" for status in bundle.statuses.values())
    assert estimate.estimate_mean == 12.5
    assert shares.diluted_shares == 1000
    assert dividend.dividend_per_share == 0.25
    assert AlphaVantageService.overview_metrics(bundle)["forward_pe"] == 18
