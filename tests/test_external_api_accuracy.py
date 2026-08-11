import asyncio
import hashlib
import json
from datetime import date, datetime, timedelta, timezone

import httpx
from sqlmodel import Session, SQLModel, create_engine, select

from app.models.event import CanonicalIssue, Event
from app.models.financial import DividendHistory, FinancialSnapshot, HistoricalValuationObservation
from app.models.security import (
    ConsensusEstimate,
    ProviderCallTelemetry,
    ProviderResponseCache,
    SecurityMaster,
    ShareCountObservation,
)
from app.providers.dart_text_fallback import extract_preliminary_earnings_facts_from_text
from app.providers.identity import OpenFigiProvider
from app.models.watchlist import WatchlistItem
from app.providers.base import RawEvent
from app.providers.ir import CompanyIRProvider
from app.schemas.thesis import ValuationSnapshot
from app.services.alpha_vantage_service import AlphaVantageService
from app.services.capital_action_service import CapitalActionService
from app.services.data_coverage_service import DataCoverageService
from app.services.event_classifier import classify_event
from app.services.event_identity import (
    attribute_claim_actor,
    event_is_eligible_for_current_analysis,
    validate_source_document_identity,
)
from app.services.event_relevance_service import EventRelevanceService, extract_structured_flags
from app.services.financial_freshness_service import FinancialFreshnessService
from app.services.financial_snapshot_service import upsert_financial_snapshot_from_event
from app.services.financial_validation import validate_event_financials
from app.services.historical_valuation_service import HistoricalValuationService
from app.services.issue_identity_audit_service import IssueIdentityAuditService
from app.services.news_query_service import NewsQueryService
from app.services.collection_service import (
    CollectionService,
    _opendart_reparse_lookback_days,
)
from app.services.sec_financial_snapshot_service import (
    _linked_documents,
    _parse_foreign_financial_release,
)
from app.services.security_master_service import SecurityMasterService
from app.services.provider_telemetry_service import summarize_provider_run
from app.jobs.export_monitoring_messages import _foreign_filing_audit_row


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


def test_brokerage_target_cut_is_not_company_guidance() -> None:
    raw = RawEvent(
        ticker="000660",
        company_name="SK하이닉스",
        date=date(2026, 8, 11),
        source="Naver News",
        provider="naver_news",
        title="키움증권, SK하이닉스 목표가 하향",
        url="https://example.com/brokerage",
        summary="반도체 실적은 올해가 정점이라는 증권사 전망이다.",
        identity_validated=True,
    )
    raw.claim_actor, raw.claim_actor_type = attribute_claim_actor(raw)
    extract_structured_flags(raw)

    assert raw.claim_actor_type == "brokerage"
    assert raw.guidance_changed is False
    assert classify_event(raw).value == "analyst_opinion"


def test_analyst_industry_shortage_is_not_large_order() -> None:
    raw = RawEvent(
        ticker="000660",
        company_name="SK하이닉스",
        date=date(2026, 8, 11),
        source="Financial News",
        provider="google_news_rss",
        title="JP모건, 메모리 공급 부족 2년 더 지속 전망",
        url="https://example.com/shortage",
        summary="SK하이닉스를 언급한 산업 수급 전망이며 신규 계약 발표는 아니다.",
        identity_validated=True,
    )
    raw.claim_actor, raw.claim_actor_type = attribute_claim_actor(raw)

    assert classify_event(raw).value == "analyst_opinion"
    assert classify_event(raw).value != "large_order"


def test_dart_document_identity_mismatch_is_rejected() -> None:
    raw = RawEvent(
        ticker="005930",
        company_name="삼성전자",
        date=date(2026, 8, 11),
        source="OpenDART",
        provider="opendart",
        title="기업설명회 개최",
        url="https://dart.fss.or.kr/dsaf001/main.do?rcpNo=20260701000525",
        summary="공시",
        source_document_id="20260701000525",
        confirmed_facts=["OpenDART receipt number: 20260811000285"],
    )

    assert validate_source_document_identity(raw) is False
    assert raw.document_identity_status == "invalid_mismatch"


def test_legacy_dart_identity_is_backfilled_or_quarantined() -> None:
    engine = _engine()
    with Session(engine) as session:
        valid = Event(
            ticker="005930",
            date=date(2026, 8, 10),
            source="OpenDART",
            provider="opendart",
            title="기업설명회",
            url="https://dart.fss.or.kr/dsaf001/main.do?rcpNo=20260810000001",
            event_type="management_governance",
            confirmed_facts='["OpenDART receipt number: 20260810000001"]',
        )
        invalid = Event(
            ticker="005930",
            date=date(2026, 8, 11),
            source="OpenDART",
            provider="opendart",
            title="임원 지분 보고",
            url="https://dart.fss.or.kr/dsaf001/main.do?rcpNo=20260811000001",
            event_type="management_governance",
            confirmed_facts='["OpenDART receipt number: 20260811000002"]',
            requires_review=True,
            relevance_score=80,
        )
        session.add(valid)
        session.add(invalid)
        session.commit()
        count = IssueIdentityAuditService().audit_document_identity(session, "005930")

    assert count == 1
    assert valid.source_document_id == "20260810000001"
    assert valid.document_identity_status == "validated"
    assert invalid.document_identity_status == "invalid_mismatch"
    assert invalid.requires_review is False


class _TwoDartFilings:
    name = "opendart"

    async def fetch_events(self, ticker: str, lookback_days: int) -> list[RawEvent]:
        return [
            RawEvent(
                ticker=ticker,
                company_name="삼성전자",
                date=date(2026, 8, 11),
                source="OpenDART",
                provider="opendart",
                title="기업설명회 개최",
                url=f"https://dart.fss.or.kr/dsaf001/main.do?rcpNo={receipt}",
                summary="공시",
                source_document_id=receipt,
                confirmed_facts=[f"OpenDART receipt number: {receipt}"],
            )
            for receipt in ("20260811000001", "20260811000002")
        ]


def test_same_title_dart_filings_keep_immutable_receipt_identity() -> None:
    engine = _engine()
    service = CollectionService()
    service.providers = [_TwoDartFilings()]
    service.provider_status.pop("opendart", None)
    with Session(engine) as session:
        session.add(
            WatchlistItem(
                ticker="005930",
                company_name="삼성전자",
                exchange="KRX",
                active=True,
                issuer_type="krx",
            )
        )
        session.commit()
        asyncio.run(service.collect_events(session, "005930", 7))
        events = list(session.exec(select(Event).where(Event.ticker == "005930")).all())

    assert {event.source_document_id for event in events} == {
        "20260811000001",
        "20260811000002",
    }
    assert all(event.source_document_id in event.url for event in events)


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


def test_convertible_warning_rejects_non_convertible_official_source() -> None:
    engine = _engine()
    with Session(engine) as session:
        event = Event(
            ticker="000660",
            date=date(2026, 8, 11),
            source="OpenDART",
            provider="opendart",
            title="유상증자결정",
            url="https://dart.fss.or.kr/dsaf001/main.do?rcpNo=20260811000003",
            event_type="capital_raise",
            confirmed_facts='["OpenDART receipt number: 20260811000003"]',
            source_document_id="20260811000003",
            document_identity_status="validated",
        )
        session.add(event)
        session.flush()
        from app.services.event_identity import event_fingerprint

        issue = CanonicalIssue(
            ticker="000660",
            issue_key="wrong-convertible",
            issue_type="convertible_bond",
            opened_date=date(2026, 8, 11),
            updated_date=date(2026, 8, 11),
            latest_event_date=date(2026, 8, 11),
            title="전환사채 희석",
            economic_status="open",
            event_ids=json.dumps([event_fingerprint(event)]),
        )
        session.add(issue)
        session.commit()
        audit = IssueIdentityAuditService().audit_provenance(session, "000660")

    assert audit[0].valid is False
    assert issue.provenance_status == "invalid_provenance"


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


def test_old_full_with_current_preliminary_has_separate_freshness() -> None:
    engine = _engine()
    with Session(engine) as session:
        session.add(
            FinancialSnapshot(
                ticker="FOREIGNFRESH",
                period="2024-FY",
                snapshot_type="full_statement",
                financial_period_end=date(2024, 12, 31),
                filing_date=date(2025, 4, 17),
            )
        )
        session.add(
            FinancialSnapshot(
                ticker="FOREIGNFRESH",
                period="2026-Q2",
                snapshot_type="preliminary_earnings",
                financial_period_end=date(2026, 6, 30),
                filing_date=date(2026, 7, 16),
            )
        )
        session.commit()
        state = FinancialFreshnessService().assess(
            session, "FOREIGNFRESH", as_of=date(2026, 8, 11)
        )

    assert state.full_financial_availability == "full"
    assert state.full_financial_freshness == "stale"
    assert state.preliminary_financial_freshness == "current"
    assert state.status == "preliminary_only"


def test_foreign_latest_result_is_separate_from_prior_parsing_capability() -> None:
    engine = _engine()
    with Session(engine) as session:
        session.add(
            WatchlistItem(
                ticker="FPI",
                company_name="Foreign Issuer",
                exchange="NASDAQ",
                issuer_type="foreign_private_issuer",
                active=True,
            )
        )
        session.add(
            FinancialSnapshot(
                ticker="FPI",
                period="2024-FY",
                snapshot_type="full_statement",
                financial_period_end=date(2024, 12, 31),
                filing_date=date(2025, 4, 17),
            )
        )
        session.add(
            ProviderResponseCache(
                provider="sec_edgar",
                ticker="FPI",
                data_type="foreign_6k_exhibits",
                status="success",
                payload=json.dumps(
                    {
                        "filing_discovery_coverage": "full",
                        "document_fetch_coverage": "full",
                        "exhibit_discovery_coverage": "partial",
                        "statement_parsing_coverage": "full",
                        "any_statement_parsed": True,
                        "parsing_result": "parsed",
                        "latest_filing_parse_result": "not_financial_exhibit",
                        "latest_financial_statement_period": "2024-12-31",
                        "latest_financial_statement_filing_date": "2025-04-17",
                        "filings": [
                            {
                                "filing_date": "2026-08-06",
                                "parsing_result": "not_financial_exhibit",
                            },
                            {
                                "filing_date": "2025-04-17",
                                "parsing_result": "parsed",
                            },
                        ],
                    }
                ),
            )
        )
        session.commit()
        coverage = DataCoverageService().build(
            session,
            "FPI",
            ValuationSnapshot(
                trailing_valuation_confidence=0.8,
                forward_valuation_confidence=0.7,
            ),
        )

    assert coverage.any_foreign_statement_parsed is True
    assert coverage.latest_foreign_filing_parse_result == "not_financial_exhibit"
    assert coverage.latest_foreign_financial_period == "2024-12-31"
    assert coverage.full_financial_freshness == "stale"
    assert coverage.valuation_confidence < 0.8


def test_stale_preliminary_does_not_hide_unresolved_foreign_filing() -> None:
    engine = _engine()
    with Session(engine) as session:
        session.add_all(
            [
                FinancialSnapshot(
                    ticker="FPISTALE",
                    period="2024-FY",
                    snapshot_type="full_statement",
                    financial_period_end=date(2024, 12, 31),
                    filing_date=date(2025, 4, 17),
                ),
                FinancialSnapshot(
                    ticker="FPISTALE",
                    period="2025-Q2",
                    snapshot_type="preliminary_earnings",
                    financial_period_end=date(2025, 6, 30),
                    filing_date=date(2025, 8, 6),
                ),
                Event(
                    ticker="FPISTALE",
                    date=date(2026, 8, 6),
                    source="SEC EDGAR",
                    provider="sec_edgar",
                    title="Foreign Issuer filed 6-K",
                    url="https://example.com/fpi-6k",
                    event_type="financial_report",
                    financial_report_filed=True,
                    confirmed_facts="[]",
                ),
            ]
        )
        session.commit()
        state = FinancialFreshnessService().assess(
            session, "FPISTALE", as_of=date(2026, 8, 11)
        )

    assert state.preliminary_financial_freshness == "stale"
    assert state.status == "foreign_filing_partial"


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
    assert parsed.reporting_period_source == "document_explicit_date_range"
    assert parsed.reporting_period_confidence == "high"
    assert parsed.revenue == 100_000_000
    assert parsed.operating_income == 20_000_000
    assert parsed.net_income == 15_000_000
    assert parsed.operating_margin == 20


def test_preliminary_period_after_filing_is_quarantined() -> None:
    engine = _engine()
    event = Event(
        ticker="CHRONO",
        date=date(2026, 4, 30),
        source="OpenDART",
        provider="opendart",
        title="연결재무제표기준영업(잠정)실적",
        url="https://example.com/chrono-invalid",
        event_type="financial_report",
        document_type="preliminary_earnings",
        reporting_period_end=date(2026, 6, 30),
        confirmed_facts='["OpenDART financial fact: 매출액 = 100000000 KRW '
        '(period_scope=single-quarter)"]',
    )
    with Session(engine) as session:
        session.add(event)
        session.flush()
        row = upsert_financial_snapshot_from_event(session, event)
        session.commit()
        freshness = FinancialFreshnessService().assess(session, "CHRONO")
        FinancialFreshnessService().assess(session, "CHRONO")

    assert row is not None
    assert row.period_mapping_validation_failed is True
    assert (row.quality_warnings or "").count("financial period end is after filing date") == 1
    assert freshness.latest_preliminary_period is None


def test_valid_preliminary_period_is_current_context() -> None:
    engine = _engine()
    event = Event(
        ticker="CHRONOOK",
        date=date(2026, 7, 29),
        source="OpenDART",
        provider="opendart",
        title="연결재무제표기준영업(잠정)실적",
        url="https://example.com/chrono-valid",
        event_type="financial_report",
        document_type="preliminary_earnings",
        reporting_period_end=date(2026, 6, 30),
        confirmed_facts='["OpenDART financial fact: 매출액 = 100000000 KRW '
        '(period_scope=single-quarter)"]',
    )
    with Session(engine) as session:
        session.add(event)
        session.flush()
        row = upsert_financial_snapshot_from_event(session, event)
        session.commit()
        freshness = FinancialFreshnessService().assess(session, "CHRONOOK")

    assert row is not None
    assert row.period_mapping_validation_failed is False
    assert freshness.latest_preliminary_period == date(2026, 6, 30)


def test_period_mapping_failure_expands_opendart_reparse_window() -> None:
    engine = _engine()
    with Session(engine) as session:
        session.add(
            FinancialSnapshot(
                ticker="PERIODFIX",
                period="legacy-invalid",
                snapshot_type="preliminary_earnings",
                provider="opendart",
                filing_date=date(2026, 4, 30),
                financial_period_end=date(2026, 6, 30),
                period_mapping_validation_failed=True,
                financial_statement_basis_warning=True,
                financial_hard_errors='["financial_period_after_filing_date"]',
            )
        )
        session.commit()

        lookback = _opendart_reparse_lookback_days(
            session,
            "PERIODFIX",
            30,
            as_of=date(2026, 8, 12),
        )

    assert lookback == 105


def test_preliminary_html_table_uses_semantic_rows_and_columns() -> None:
    parsed = extract_preliminary_earnings_facts_from_text(
        """
        <table id="results">
          <tr><td colspan="4">단위 : 백만원, %</td></tr>
          <tr><th colspan="2">구분</th><th>당기실적</th><th>전기실적</th><th colspan="2">전기대비</th><th>전년동기실적</th><th colspan="2">전년동기대비</th></tr>
          <tr><th colspan="2">구분</th><th>(2026년 2분기)</th><th>(2026년 1분기)</th><th>증감율(%)</th><th>전환여부</th><th>(2025년 2분기)</th><th>증감율(%)</th><th>전환여부</th></tr>
          <tr><td rowspan="2">매출액</td><td>당해실적</td><td>79,318</td><td>52,576</td><td>50.9</td><td>-</td><td>22,231</td><td>256.8</td><td>-</td></tr>
          <tr><td>누계실적</td><td>131,895</td><td>-</td><td>-</td><td>-</td><td>39,871</td><td>230.8</td><td>-</td></tr>
          <tr><td rowspan="2">영업이익</td><td>당해실적</td><td>20,542</td><td>17,610</td><td>16.6</td><td>-</td><td>9,212</td><td>123.0</td><td>-</td></tr>
          <tr><td>누계실적</td><td>38,152</td><td>-</td><td>-</td><td>-</td><td>16,653</td><td>129.1</td><td>-</td></tr>
          <tr><td rowspan="2">당기순이익</td><td>당해실적</td><td>15,922</td><td>10,345</td><td>53.9</td><td>-</td><td>6,996</td><td>127.6</td><td>-</td></tr>
          <tr><td>누계실적</td><td>26,268</td><td>-</td><td>-</td><td>-</td><td>15,104</td><td>73.9</td><td>-</td></tr>
        </table>
        """,
        source_receipt_no="20260729800013",
    )

    assert parsed.revenue == 79_318_000_000
    assert parsed.operating_income == 20_542_000_000
    assert parsed.net_income == 15_922_000_000
    assert parsed.qoq_growth == 50.9
    assert parsed.yoy_growth == 256.8
    assert parsed.period_end == date(2026, 6, 30)
    assert parsed.reporting_period_source == "current_header_quarter"
    assert parsed.reporting_period_confidence == "high"
    current_revenue = next(
        field
        for field in parsed.raw_fields
        if field["raw_label"] == "매출액"
        and field["raw_column_header"].startswith("당기실적")
    )
    assert current_revenue["parse_method"] == "html_semantic_table"
    assert current_revenue["source_receipt_no"] == "20260729800013"
    assert current_revenue["table_id"] == "results"


def test_preliminary_parser_selects_complete_consistent_table_candidate() -> None:
    parsed = extract_preliminary_earnings_facts_from_text(
        """
        <table id="summary-noise">
          <tr><td colspan="4">단위 : 백만원, %</td></tr>
          <tr><th colspan="2">구분</th><th>당해실적</th><th>전기실적</th></tr>
          <tr><th colspan="2">구분</th><th>(2026년 2분기)</th><th>(2026년 1분기)</th></tr>
          <tr><td>매출액</td><td>당해실적</td><td>100</td><td>90</td></tr>
          <tr><td>영업이익</td><td>당해실적</td><td>500</td><td>15</td></tr>
        </table>
        <table id="financial-results">
          <tr><td colspan="4">단위 : 백만원, %</td></tr>
          <tr><th colspan="2">구분</th><th>당기실적</th><th>전기실적</th><th>전년동기실적</th></tr>
          <tr><th colspan="2">구분</th><th>(2026년 2분기)</th><th>(2026년 1분기)</th><th>(2025년 2분기)</th></tr>
          <tr><td>매출액</td><td>당기실적</td><td>100</td><td>90</td><td>80</td></tr>
          <tr><td>영업이익</td><td>당기실적</td><td>20</td><td>15</td><td>12</td></tr>
          <tr><td>당기순이익</td><td>당기실적</td><td>12</td><td>10</td><td>8</td></tr>
        </table>
        """
    )

    assert parsed.revenue == 100_000_000
    assert parsed.operating_income == 20_000_000
    assert parsed.net_income == 12_000_000
    assert parsed.period_end == date(2026, 6, 30)
    assert parsed.diagnostics["table_id"] == "financial-results"
    assert parsed.diagnostics["candidate_count"] == 2


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


def test_preliminary_parser_preserves_semantic_raw_fields() -> None:
    parsed = extract_preliminary_earnings_facts_from_text(
        """
        단위 : 백만원 | 당기실적 | 2026-04-01 | 2026-06-30 |
        매출액 | 당해실적 | 79,318,746 | 40,000,000 | 98.3 | 30,000,000 | 164.4 |
        영업이익 | 당해실적 | 60,542,608 | 20,000,000 | 202.7 | 10,000,000 | 505.4 |
        당기순이익 | 당해실적 | 93,922,593 | 15,000,000 | 526.2 | 8,000,000 | 1074.0 |
        """
    )

    assert parsed.raw_fields
    assert {item["raw_label"] for item in parsed.raw_fields} >= {
        "매출액",
        "영업이익",
        "당기순이익",
    }
    assert all(item["raw_unit"] == "백만원" for item in parsed.raw_fields)
    current_fields = [
        item for item in parsed.raw_fields if item["raw_column_header"] == "당기실적"
    ]
    assert len(current_fields) == 3


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


def test_quarantined_financial_event_does_not_trigger_refresh() -> None:
    engine = _engine()
    with Session(engine) as session:
        session.add(
            FinancialSnapshot(
                ticker="FRESHQUARANTINE",
                period="2026-Q2",
                snapshot_type="full_statement",
                financial_period_end=date(2026, 6, 30),
                filing_date=date(2026, 7, 24),
            )
        )
        session.add(
            Event(
                ticker="FRESHQUARANTINE",
                date=date(2026, 10, 10),
                source="OpenDART",
                provider="opendart",
                title="Quarantined Q3 guidance filing",
                url="https://example.com/quarantined-q3",
                event_type="guidance_change",
                confirmed_facts="[]",
                guidance_changed=True,
                reporting_period_end=date(2026, 9, 30),
                document_type="preliminary_earnings",
                document_identity_status="invalid_mismatch",
                identity_status="rejected_document_identity",
                financial_refresh_required=True,
            )
        )
        session.commit()
        state = FinancialFreshnessService().assess(
            session, "FRESHQUARANTINE", as_of=date(2026, 10, 15)
        )
        quarantined = session.exec(select(Event)).one()

    assert state.refresh_required is False
    assert state.status == "current"
    assert state.latest_material_event_date is None
    assert quarantined.financial_refresh_required is False


def test_rejected_financial_candidate_is_not_eligible_for_current_analysis() -> None:
    event = Event(
        ticker="REJECTEDFRESHNESS",
        date=date(2026, 8, 11),
        source="News",
        provider="google_news_rss",
        title="Other company changes guidance",
        url="https://example.com/rejected-guidance",
        event_type="guidance_change",
        guidance_changed=True,
        document_identity_status="unvalidated",
        identity_status="rejected_company_mismatch",
        rejected_reason="article_subject_is_different_security",
    )

    assert event_is_eligible_for_current_analysis(event) is False


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


def test_invalidated_canonical_issue_is_reused_without_duplicate_insert() -> None:
    engine = _engine()
    event = Event(
        ticker="REUSE",
        date=date(2026, 8, 10),
        source="News",
        provider="google_news_rss",
        title="Reuse Corp buyback plan",
        url="https://example.com/reuse-buyback",
        event_type="buyback",
        identity_validated=True,
        identity_status="accepted_exact_company",
        buyback_candidate=True,
    )
    with Session(engine) as session:
        session.add(
            CanonicalIssue(
                ticker="REUSE",
                issue_key=hashlib.sha256(
                    b"REUSE|buyback|2026-08"
                ).hexdigest()[:20],
                issue_type="buyback",
                status="invalidated_source",
                execution_status="cancelled",
                economic_status="resolved",
                provenance_status="invalid_provenance",
                opened_date=date(2026, 8, 10),
                updated_date=date(2026, 8, 10),
                latest_event_date=date(2026, 8, 10),
                title="buyback 경제적 영향",
            )
        )
        session.add(event)
        session.flush()
        issue = CapitalActionService().canonicalize(session, event)
        session.commit()
        issues = list(
            session.exec(
                select(CanonicalIssue).where(CanonicalIssue.ticker == "REUSE")
            ).all()
        )

    assert issue is not None
    assert len(issues) == 1


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


def test_unconfigured_provider_is_counted_as_skip_not_success() -> None:
    engine = _engine()
    service = CollectionService()
    provider = CompanyIRProvider()
    with Session(engine) as session:
        result = asyncio.run(
            service._fetch_provider_events(
                session,
                provider,
                "GOOGL",
                7,
                ["Alphabet"],
                "domestic_us",
            )
        )
        row = session.exec(select(ProviderCallTelemetry)).one()

    assert result == []
    assert row.status == "skipped_not_configured"
    assert row.success_count == 0
    assert row.skip_count == 1


def test_provider_current_run_summary_does_not_reuse_lifetime_success() -> None:
    run_started_at = datetime(2026, 8, 11, 9, 0, tzinfo=timezone.utc)
    row = ProviderCallTelemetry(
        provider="company_ir",
        endpoint="fetch_events",
        ticker="GOOGL",
        attempted_at=run_started_at + timedelta(minutes=1),
        finished_at=run_started_at + timedelta(minutes=1, seconds=1),
        status="skipped_not_configured",
        success_count=74,
        failure_count=2,
        skip_count=8,
    )

    summary = summarize_provider_run([row], run_started_at)

    assert summary["current_run_attempts"] == 1
    assert summary["current_run_successes"] == 0
    assert summary["current_run_failures"] == 0
    assert summary["current_run_skips"] == 1
    assert summary["lifetime_successes"] == 74


def test_validation_failed_component_never_renders_as_no_coverage_warning() -> None:
    engine = _engine()
    with Session(engine) as session:
        session.add(
            FinancialSnapshot(
                ticker="QUALITY",
                period="2026-Q2",
                snapshot_type="preliminary_earnings",
                financial_period_end=date(2026, 6, 30),
                filing_date=date(2026, 7, 29),
                financial_statement_basis_warning=True,
            )
        )
        session.commit()
        coverage = DataCoverageService().build(session, "QUALITY", ValuationSnapshot())

    assert coverage.preliminary_financial_quality == "validation_failed"
    assert "검증에 실패" in (coverage.overall_quality_reason or "")
    assert "경고 없음" not in (coverage.overall_quality_reason or "")


def test_quarantined_history_does_not_lower_current_event_quality() -> None:
    engine = _engine()
    with Session(engine) as session:
        session.add_all(
            [
                Event(
                    ticker="QUALITYEVENT",
                    date=date.today(),
                    source="Company IR",
                    provider="company_ir",
                    title="Current valid company update",
                    url="https://example.com/current-valid",
                    event_type="financial_report",
                    document_identity_status="validated",
                    identity_status="official_identity",
                    confirmed_facts="[]",
                ),
                Event(
                    ticker="QUALITYEVENT",
                    date=date.today() - timedelta(days=30),
                    source="OpenDART",
                    provider="opendart",
                    title="Historical quarantined filing",
                    url="https://example.com/quarantined",
                    event_type="financial_report",
                    document_identity_status="invalid_mismatch",
                    identity_status="rejected_document_identity",
                    confirmed_facts="[]",
                ),
            ]
        )
        session.commit()
        coverage = DataCoverageService().build(
            session, "QUALITYEVENT", ValuationSnapshot()
        )

    assert coverage.event_quality == "fresh"
    assert coverage.current_event_quality == "fresh"
    assert coverage.quarantined_event_count == 1
    assert coverage.identity_audit_status == "quarantined_history_present"


def test_rejected_unrelated_article_does_not_lower_current_event_quality() -> None:
    engine = _engine()
    with Session(engine) as session:
        session.add(
            Event(
                ticker="REJECTED",
                date=date.today(),
                source="News",
                provider="google_news_rss",
                title="Another company announces a capital raise",
                url="https://example.com/rejected-company",
                event_type="capital_raise",
                document_identity_status="unvalidated",
                identity_status="rejected_company_mismatch",
                rejected_reason="article_subject_is_different_security",
                confirmed_facts="[]",
            )
        )
        session.commit()
        coverage = DataCoverageService().build(
            session, "REJECTED", ValuationSnapshot()
        )

    assert coverage.event_quality == "fresh"
    assert coverage.rejected_candidate_count == 1


def test_current_relevant_financial_validation_failure_lowers_event_quality() -> None:
    engine = _engine()
    with Session(engine) as session:
        session.add(
            Event(
                ticker="CURRENTFAIL",
                date=date.today(),
                source="Company IR",
                provider="company_ir",
                title="Current preliminary earnings",
                url="https://example.com/current-fail",
                event_type="financial_report",
                document_identity_status="validated",
                identity_status="official_identity",
                financial_statement_basis_warning=True,
                confirmed_facts="[]",
            )
        )
        session.commit()
        coverage = DataCoverageService().build(
            session, "CURRENTFAIL", ValuationSnapshot()
        )

    assert coverage.event_quality == "validation_failed"


def test_current_official_document_identity_failure_lowers_event_quality() -> None:
    engine = _engine()
    with Session(engine) as session:
        session.add(
            Event(
                ticker="CURRENTIDENTITYFAIL",
                date=date.today(),
                source="OpenDART",
                provider="opendart",
                title="Current filing with mismatched receipt identity",
                url="https://example.com/current-identity-fail",
                event_type="financial_report",
                document_identity_status="invalid_mismatch",
                identity_status="official_identity",
                confirmed_facts="[]",
            )
        )
        session.commit()
        coverage = DataCoverageService().build(
            session, "CURRENTIDENTITYFAIL", ValuationSnapshot()
        )

    assert coverage.event_quality == "validation_failed"
    assert coverage.quarantined_event_count == 1


def test_partial_semantic_table_does_not_mix_flat_fallback_metrics() -> None:
    parsed = extract_preliminary_earnings_facts_from_text(
        """
        <table id="partial-results">
          <tr><th colspan="2">구분</th><th>당해실적</th><th>전기실적</th></tr>
          <tr><th colspan="2">구분</th><th>(2026년 2분기)</th><th>(2026년 1분기)</th></tr>
          <tr><td rowspan="2">매출액</td><td>당해실적</td><td>100</td><td>90</td></tr>
          <tr><td>누계실적</td><td>180</td><td>-</td></tr>
          <tr><td rowspan="2">영업이익</td><td>당해실적</td><td>20</td><td>15</td></tr>
          <tr><td>누계실적</td><td>30</td><td>-</td></tr>
        </table>
        당기순이익 | 당해실적 | 999 | 10
        """
    )

    assert parsed.revenue == 100
    assert parsed.operating_income == 20
    assert parsed.net_income is None
    assert {field["parse_method"] for field in parsed.raw_fields} == {
        "html_semantic_table"
    }
    assert parsed.diagnostics["semantic_table_found"] is True
    assert parsed.diagnostics["metric_labels_found"] == ["매출액", "영업이익"]


def test_flat_fallback_is_used_only_when_semantic_table_is_invalid() -> None:
    parsed = extract_preliminary_earnings_facts_from_text(
        """
        <table id="not-a-semantic-results-table">
          <tr><th>구분</th><th>실적</th></tr>
          <tr><td>참고</td><td>공시 본문</td></tr>
        </table>
        단위: 백만원 | 당해실적 | 2026-06-30 |
        매출액 | 당해실적 | 100 | 90 | 누계실적 | 180 |
        영업이익 | 당해실적 | 20 | 15 | 누계실적 | 30 |
        당기순이익 | 당해실적 | 12 | 10 | 누계실적 | 20
        """
    )

    assert parsed.revenue == 100_000_000
    assert parsed.operating_income == 20_000_000
    assert parsed.net_income == 12_000_000
    assert parsed.diagnostics["semantic_table_found"] is False
    assert {field["parse_method"] for field in parsed.raw_fields} == {
        "flat_token_fallback"
    }


def test_alpha_local_budget_exhaustion_is_a_skip() -> None:
    engine = _engine()
    service = AlphaVantageService()
    service.settings.alpha_vantage_api_key = "test"
    service.settings.alpha_vantage_request_budget = 0
    service.__class__._request_count = 0
    service.__class__._request_date = datetime.now(timezone.utc).date()
    started = datetime.now(timezone.utc) - timedelta(seconds=1)
    with Session(engine) as session:
        _payload, status = asyncio.run(
            service._fetch(session, "IBM", "DIVIDENDS")
        )
        row = session.exec(select(ProviderCallTelemetry)).one()
        summary = summarize_provider_run([row], started)

    assert status == "skipped_budget_exhausted"
    assert row.status == "skipped_budget_exhausted"
    assert row.failure_count == 0
    assert row.skip_count == 1
    assert summary["current_run_failures"] == 0
    assert summary["current_run_skips"] == 1


def test_alpha_provider_rate_limit_remains_a_failure() -> None:
    def handler(_request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json={"Note": "API call frequency rate limit reached"})

    engine = _engine()
    service = AlphaVantageService(transport=httpx.MockTransport(handler))
    service.settings.alpha_vantage_api_key = "test"
    service.settings.alpha_vantage_request_budget = 30
    service.__class__._request_count = 0
    service.__class__._request_date = datetime.now(timezone.utc).date()
    with Session(engine) as session:
        _payload, status = asyncio.run(
            service._fetch(session, "IBM", "OVERVIEW")
        )
        row = session.exec(select(ProviderCallTelemetry)).one()

    assert status == "rate_limited"
    assert row.status == "rate_limited"
    assert row.failure_count == 1
    assert row.skip_count == 0


def test_alpha_same_run_failure_is_not_requested_twice() -> None:
    request_count = 0

    def handler(_request: httpx.Request) -> httpx.Response:
        nonlocal request_count
        request_count += 1
        return httpx.Response(200, json={"Note": "API call frequency rate limit reached"})

    engine = _engine()
    service = AlphaVantageService(transport=httpx.MockTransport(handler))
    service.settings.alpha_vantage_api_key = "test"
    service.settings.alpha_vantage_request_budget = 30
    service.__class__._request_count = 0
    service.__class__._request_date = datetime.now(timezone.utc).date()
    with Session(engine) as session:
        first = asyncio.run(service._fetch(session, "IBM", "OVERVIEW"))
        second = asyncio.run(service._fetch(session, "IBM", "OVERVIEW"))

    assert first == second
    assert first[1] == "rate_limited"
    assert request_count == 1


def test_foreign_audit_row_separates_prior_parse_from_latest_result() -> None:
    row = _foreign_filing_audit_row(
        "TSM",
        {
            "filing_discovery_coverage": "full",
            "document_fetch_coverage": "full",
            "exhibit_discovery_coverage": "full",
            "any_foreign_statement_parsed": True,
            "latest_foreign_filing_parse_result": "not_financial_exhibit",
            "latest_foreign_financial_period": "2026-06-30",
            "per_share_mapping_coverage": "unavailable",
            "valuation_coverage": "partial",
        },
    )

    assert "과거 parsing 성공" in row
    assert "최신 filing 재무 실적표 아님" in row
    assert "ADR/per-share mapping 미확보" in row
