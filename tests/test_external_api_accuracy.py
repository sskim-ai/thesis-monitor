import asyncio
from datetime import date, datetime, timedelta, timezone

import httpx
from sqlmodel import Session, SQLModel, create_engine, select

from app.models.event import CanonicalIssue, Event
from app.models.financial import DividendHistory, FinancialSnapshot, HistoricalValuationObservation
from app.models.security import (
    ConsensusEstimate,
    ProviderCallTelemetry,
    SecurityMaster,
    ShareCountObservation,
)
from app.providers.dart_text_fallback import extract_preliminary_earnings_facts_from_text
from app.providers.identity import OpenFigiProvider
from app.models.watchlist import WatchlistItem
from app.providers.base import RawEvent
from app.schemas.thesis import ValuationSnapshot
from app.services.alpha_vantage_service import AlphaVantageService
from app.services.data_coverage_service import DataCoverageService
from app.services.event_classifier import classify_event
from app.services.event_relevance_service import EventRelevanceService, extract_structured_flags
from app.services.financial_freshness_service import FinancialFreshnessService
from app.services.financial_snapshot_service import upsert_financial_snapshot_from_event
from app.services.financial_validation import validate_event_financials
from app.services.historical_valuation_service import HistoricalValuationService
from app.services.issue_identity_audit_service import IssueIdentityAuditService
from app.services.news_query_service import NewsQueryService
from app.services.sec_financial_snapshot_service import (
    _linked_documents,
    _parse_foreign_financial_release,
)
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


def test_opendart_preliminary_earnings_are_normalized() -> None:
    parsed = extract_preliminary_earnings_facts_from_text(
        """
        단위 : 백만원 | 당기실적 | 2026-04-01 | 2026-06-30 |
        매출액 | 당해실적 | 100 | 90 | 11.1 | 80 | 25.0 | 누계실적 | 180 |
        영업이익 | 당해실적 | 20 | 15 | 33.3 | 10 | 100.0 | 누계실적 | 30 |
        당기순이익 | 당해실적 | 15 | 12 | 25.0 | 8 | 87.5 | 누계실적 | 23 |
        """
    )

    assert parsed.period_end == date(2026, 6, 30)
    assert parsed.revenue == 100_000_000
    assert parsed.operating_income == 20_000_000
    assert parsed.net_income == 15_000_000
    assert parsed.operating_margin == 20


def test_cumulative_preliminary_event_creates_standalone_q2_snapshot() -> None:
    engine = _engine()
    event = Event(
        ticker="PREQ2",
        date=date(2026, 7, 29),
        source="OpenDART",
        provider="opendart",
        title="연결재무제표기준영업(잠정)실적",
        url="https://example.com/preq2",
        event_type="financial_report",
        document_type="preliminary_earnings",
        reporting_period_end=date(2026, 6, 30),
        confirmed_facts='["OpenDART receipt number: 202607290001", '
        '"OpenDART financial cumulative fact: 매출액 = 180000000 KRW '
        '(잠정실적; thstrm_nm=2026년 2분기; unit=KRW; period_scope=single-quarter; '
        'amount_scope=cumulative; report_code=preliminary)", '
        '"OpenDART financial cumulative fact: 영업이익 = 30000000 KRW '
        '(잠정실적; thstrm_nm=2026년 2분기; unit=KRW; period_scope=single-quarter; '
        'amount_scope=cumulative; report_code=preliminary)"]',
    )
    with Session(engine) as session:
        session.add(
            FinancialSnapshot(
                ticker="PREQ2",
                period="2026-Q1",
                snapshot_type="full_statement",
                provider="opendart",
                fiscal_year=2026,
                period_type="Q1",
                cumulative_revenue=80_000_000,
                cumulative_operating_income=10_000_000,
                filing_date=date(2026, 5, 15),
                reported_date=date(2026, 5, 15),
            )
        )
        session.add(event)
        session.flush()
        row = upsert_financial_snapshot_from_event(session, event)

    assert row is not None
    assert row.snapshot_type == "preliminary_earnings"
    assert row.revenue == 100_000_000
    assert row.operating_income == 20_000_000


def test_invalid_preliminary_numbers_keep_period_but_not_financial_values() -> None:
    engine = _engine()
    event = Event(
        ticker="BADPRE",
        date=date(2026, 7, 29),
        source="OpenDART",
        provider="opendart",
        title="연결재무제표기준영업(잠정)실적",
        url="https://example.com/badpre",
        event_type="financial_report",
        document_type="preliminary_earnings",
        reporting_period_end=date(2026, 6, 30),
        confirmed_facts='["OpenDART receipt number: 202607290002", '
        '"OpenDART financial cumulative fact: 매출액 = 180 KRW '
        '(period_scope=single-quarter; amount_scope=cumulative)", '
        '"OpenDART financial cumulative fact: 영업이익 = 150 KRW '
        '(period_scope=single-quarter; amount_scope=cumulative)"]',
    )
    validation = validate_event_financials(event, operating_margin_upper_bound=60)
    with Session(engine) as session:
        session.add(event)
        session.flush()
        row = upsert_financial_snapshot_from_event(session, event)

    assert validation.valid is False
    assert row is not None
    assert row.financial_period_end == date(2026, 6, 30)
    assert row.revenue is None
    assert row.operating_income is None
    assert row.financial_statement_basis_warning is True


def test_same_period_follow_up_does_not_require_financial_refresh() -> None:
    engine = _engine()
    with Session(engine) as session:
        session.add(
            FinancialSnapshot(
                ticker="SAME",
                period="2026-Q2",
                snapshot_type="full_statement",
                financial_period_end=date(2026, 6, 30),
                filing_date=date(2026, 7, 24),
            )
        )
        session.add(
            Event(
                ticker="SAME",
                date=date(2026, 7, 25),
                source="News",
                provider="google_news_rss",
                title="Q2 earnings commentary",
                url="https://example.com/same-q2",
                event_type="financial_report",
                confirmed_facts="[]",
                financial_report_filed=True,
                reporting_period_end=date(2026, 6, 30),
                document_type="follow_up_commentary",
            )
        )
        session.commit()
        state = FinancialFreshnessService().assess(session, "SAME")

    assert state.refresh_required is False
    assert state.status == "current"


def test_newer_reporting_period_requires_financial_refresh() -> None:
    engine = _engine()
    with Session(engine) as session:
        session.add(
            FinancialSnapshot(
                ticker="NEWER",
                period="2026-Q1",
                snapshot_type="full_statement",
                financial_period_end=date(2026, 3, 31),
                filing_date=date(2026, 5, 15),
            )
        )
        session.add(
            Event(
                ticker="NEWER",
                date=date(2026, 7, 25),
                source="Company",
                provider="company_ir",
                title="Q2 earnings release",
                url="https://example.com/newer-q2",
                event_type="financial_report",
                confirmed_facts="[]",
                financial_report_filed=True,
                reporting_period_end=date(2026, 6, 30),
                document_type="preliminary_earnings",
            )
        )
        session.commit()
        state = FinancialFreshnessService().assess(session, "NEWER")

    assert state.refresh_required is True
    assert state.refresh_reason == "newer_reporting_period_detected"


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
        telemetry = session.exec(select(ProviderCallTelemetry)).all()

    assert all(status == "fresh" for status in bundle.statuses.values())
    assert estimate.estimate_mean == 12.5
    assert shares.diluted_shares == 1000
    assert dividend.dividend_per_share == 0.25
    assert AlphaVantageService.overview_metrics(bundle)["forward_pe"] == 18
    assert {row.endpoint for row in telemetry} == {
        "EARNINGS_ESTIMATES",
        "SHARES_OUTSTANDING",
        "DIVIDENDS",
        "SPLITS",
        "OVERVIEW",
    }


def test_buy_back_phrase_is_normalized_as_candidate() -> None:
    raw = RawEvent(
        ticker="SNDK",
        company_name="SanDisk",
        date=date.today(),
        source="News",
        provider="google_news_rss",
        title="SanDisk Can Now Buy Back $15.5 Billion",
        url="https://example.com/buy-back",
        summary="The company can buy back shares under the authorization.",
        identity_validated=True,
    )
    extract_structured_flags(raw)

    assert raw.buyback_candidate is True
    assert raw.confirmed_buyback is False


def test_foreign_release_link_and_financial_values_are_detected() -> None:
    primary = '<a href="earnings.htm">Press release with second quarter results</a>'
    release = """
        Results for the quarter ended June 30, 2026.
        Consolidated revenue was NT$1,270.38 billion.
        Net income was NT$706.56 billion and diluted EPS was NT$27.25.
        Operating margin was 60.3%.
    """

    assert _linked_documents(primary) == [
        ("earnings.htm", "Press release with second quarter results")
    ]
    parsed = _parse_foreign_financial_release(release)
    assert parsed is not None
    assert parsed["period_end"] == "2026-06-30"
    assert parsed["revenue"] == 1_270_380_000_000
    assert parsed["net_income"] == 706_560_000_000
    assert parsed["currency"] == "TWD"


def test_openfigi_identity_mismatch_does_not_overwrite_security_master() -> None:
    def handler(_request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            200,
            json=[
                {
                    "data": [
                        {"figi": "BBG000TEST", "ticker": "IBM", "name": "Intel Corp"}
                    ]
                }
            ],
        )

    engine = _engine()
    provider = OpenFigiProvider(transport=httpx.MockTransport(handler))
    provider.settings.openfigi_api_key = "test"
    with Session(engine) as session:
        security = _security(session, "IBM", "International Business Machines")
        mapped, reason = asyncio.run(provider.enrich(session, security))
        session.commit()
        refreshed = session.exec(
            select(SecurityMaster).where(SecurityMaster.ticker == security.ticker)
        ).one()

    assert mapped is False
    assert reason == "identity_mismatch"
    assert refreshed is not None and refreshed.figi is None


def test_ambiguous_ticker_query_uses_company_aliases() -> None:
    engine = _engine()
    with Session(engine) as session:
        security = _security(session, "MU", "Micron Technology")
        query = NewsQueryService().query(security)

    assert '"micron technology"' in query.lower()
    assert query != "MU"


def test_forward_value_with_incomplete_metadata_is_partial_consensus() -> None:
    engine = _engine()
    snapshot = ValuationSnapshot(
        forward_pe=19.3,
        forward_pe_status="value",
        forward_pe_source="consensus_forward",
        estimate_provider="finnhub",
        consensus_status="unavailable",
    )
    with Session(engine) as session:
        session.add(
            FinancialSnapshot(
                ticker="CONS",
                period="2026-Q2",
                snapshot_type="full_statement",
                financial_period_end=date(2026, 6, 30),
                filing_date=date(2026, 7, 25),
            )
        )
        session.commit()
        coverage = DataCoverageService().build(session, "CONS", snapshot)

    assert coverage.consensus_quality == "partial"
    assert coverage.overall_data_quality == "partial"
    assert "Consensus" in (coverage.overall_quality_reason or "")
