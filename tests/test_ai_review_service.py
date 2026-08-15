import copy
import hashlib
import json
import threading
from concurrent.futures import ThreadPoolExecutor
from datetime import UTC, date, datetime, timedelta
from pathlib import Path

import pytest
from sqlalchemy.pool import StaticPool
from sqlmodel import SQLModel, Session, create_engine, select

import app.services.ai_review_service as ai_review_service
from app.config import get_settings
from app.models.company import Company
from app.models.financial import FinancialSnapshot
from app.models.macro import MacroBriefing
from app.models.thesis import (
    InvestmentThesis,
    MonitorRun,
    NotificationDelivery,
    ThesisAssessment,
)
from app.models.watchlist import WatchlistItem
from app.schemas.ai_review import AIDailyReviewOutput
from app.services.ai_review_service import (
    build_ai_review_packet,
    claim_next_ai_review_packet,
    finalize_ai_review_output,
    investment_framework_routing,
    knowledge_manifest,
    validate_ai_review_output,
    write_ai_review_packet,
)
from app.services.numeric_semantic_registry import (
    canonical_display_value,
    semantic_spec,
)
from scripts.sync_custom_gpt_knowledge import (
    CANONICAL_PATH,
    MANIFEST_PATH,
    SKILL_PATH,
    UPLOAD_PATH,
    sync_repository_mirror,
    validate_repository_mirror,
)


RUN_DATE = date(2026, 8, 14)


def _engine():
    value = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    SQLModel.metadata.create_all(value)
    return value


def _settings(monkeypatch, tmp_path: Path) -> None:
    settings = get_settings().model_copy(
        update={
            "data_dir": str(tmp_path),
            "ai_review_mode": "shadow",
            "ai_review_claim_lease_minutes": 30,
            "ai_review_shadow_catchup_hours": 24,
        }
    )
    monkeypatch.setattr("app.services.ai_review_service.get_settings", lambda: settings)
    provenance_dir = tmp_path / "company_profile_provenance"
    provenance_dir.mkdir(parents=True, exist_ok=True)
    for ticker, taxonomy_key in (("PACKETUS", "memory"), ("123450", None)):
        (provenance_dir / f"{ticker}.json").write_text(
            json.dumps(
                {
                    "schema_version": "1",
                    "ticker": ticker,
                    "quality": "verified",
                    "source": "fixture_official_profile",
                    "source_as_of": "2026-08-13",
                    "verified_at": "2026-08-13T00:00:00+00:00",
                    "classification_method": "official_industry_code",
                    "taxonomy_key": taxonomy_key,
                }
            ),
            encoding="utf-8",
        )


def _assessment(
    ticker: str,
    assessment_date: date,
    *,
    thesis_version: int = 2,
) -> ThesisAssessment:
    return ThesisAssessment(
        ticker=ticker,
        thesis_version=thesis_version,
        assessment_date=assessment_date,
        status="no_material_change",
        business_thesis_change="no_material_change",
        valuation_change="neutral",
        earnings_estimate_impact="unchanged",
        summary="Verified demand and earnings evidence remains consistent with the thesis.",
        new_buyer_view="Wait for the next verified order update.",
        holder_view="Monitor execution against the stated thesis drivers.",
        price_view="Price context is separate from the business thesis.",
        risk_level="normal",
        evidence=json.dumps(
            [
                {
                    "date": assessment_date.isoformat(),
                    "event_type": "contract",
                    "title": "Verified material customer order",
                    "direction": "strengthen",
                    "materiality": "material",
                    "fingerprint": "event-D",
                    "contract_name": "Verified data-center equipment order",
                    "contract_amount": 318_964_597_910,
                    "counterparty": "Verified Customer",
                    "contract_period": "2026-08-14 to 2028-12-31",
                    "sales_ratio_pct": 12.4,
                    "raw_fact": "provider=opendart unit=KRW",
                }
            ]
        ),
        confirmed_facts=json.dumps(
            ["OpenDART financial fact: provider=opendart fs_div=CFS unit=KRW"]
        ),
        confirmed_warnings=json.dumps(["Execution timing remains a confirmed watch item."]),
        unknowns=json.dumps(["The next customer delivery date is not yet confirmed."]),
        open_warnings=json.dumps(["A verified timing caution remains open."]),
        persistent_watch_risks=json.dumps(["Customer concentration"]),
        valuation_snapshot=json.dumps(
            {
                "current_price": 100.0,
                "currency": "USD",
                "financial_currency": "USD",
                "price_as_of": assessment_date.isoformat(),
                "latest_earnings_period": "2026-06-30",
                "latest_revenue": 500.0,
                "latest_operating_income": 50.0,
                "latest_operating_margin": 10.0,
                "ttm_eps_usable": True,
                "trailing_pe": 20.0,
                "trailing_pe_denominator_period_end": "2026-06-30",
                "trailing_pe_denominator_filing_date": "2026-08-01",
                "trailing_pe_basis_status": "directly_comparable",
                "price_to_book": 3.0,
                "pbr_denominator_period_end": "2026-06-30",
                "pbr_denominator_filing_date": "2026-08-01",
                "price_to_book_basis_status": "directly_comparable",
                "forward_pe": 18.0,
                "forward_eps": 5.5,
                "forward_pe_source": "modeled_forward",
                "forward_pe_input_period": "FY1",
                "forward_pe_basis_status": "directly_comparable",
                "forecast_method": "normalized_roe",
                "earnings_quarter_series": [
                    {
                        "period": period,
                        "source": "full_statement",
                        "filing": filing,
                        "normalized_eps_usable": True,
                    }
                    for period, filing in (
                        ("2025-09-30", "2025-11-01"),
                        ("2025-12-31", "2026-02-01"),
                        ("2026-03-31", "2026-05-01"),
                        ("2026-06-30", "2026-08-01"),
                    )
                ],
                "historical_comparability": "price_share_basis_mismatch",
                "historical_pe_statistics": {"current_percentile": 90.0},
            }
        ),
        price_context=json.dumps(
            {
                "decision": {
                    "current_price": 100.0,
                    "currency": "USD",
                    "price_as_of": assessment_date.isoformat(),
                    "current_position": "mid range",
                },
                "supply": {"available": False},
                "warnings": [],
            }
        ),
        valuation_context=json.dumps({"impact": "neutral"}),
        thesis_snapshot=json.dumps(
            {
                "assessment_mode": "daily_delta",
                "capital_action_materiality": [
                    {
                        "event_fingerprint": "treasury-D",
                        "event_date": assessment_date.isoformat(),
                        "transaction_shares": 32_520,
                        "share_denominator": 29_700_000,
                        "share_denominator_source": "common_shares_outstanding",
                        "share_ratio_pct": 0.1095,
                        "transaction_amount": 6_780_420_000,
                        "market_cap": 6_192_450_000_000,
                        "market_cap_ratio_pct": 0.1095,
                        "purpose": "employee compensation",
                        "level": "immaterial",
                        "reason": "small employee treasury-stock transaction",
                    }
                ],
            }
        ),
    )


def _seed(session: Session) -> None:
    ticker = "PACKETUS"
    session.add(
        Company(
            ticker=ticker,
            company_name="Packet Corp",
            exchange="NASDAQ",
            industry="Memory semiconductor",
            business_units="DRAM and NAND",
        )
    )
    session.add(WatchlistItem(ticker=ticker, company_name="Packet Corp", exchange="NASDAQ"))
    session.add(
        InvestmentThesis(
            ticker=ticker,
            version=2,
            core_thesis="Verified demand converts into durable cash flow.",
            thesis_drivers=json.dumps(["Order conversion", "Margin execution"]),
            validation_metrics=json.dumps(["Revenue", "Operating margin"]),
            strengthen_signals=json.dumps(["Material order growth"]),
            weaken_signals=json.dumps(["Margin deterioration"]),
            invalidation_signals=json.dumps(["Structural customer loss"]),
            market_expectations=json.dumps({"level": "balanced"}),
            valuation_framework=json.dumps({"primary_method": "earnings multiple"}),
            macro_exposures=json.dumps(["rates"]),
        )
    )
    session.add(_assessment(ticker, RUN_DATE - timedelta(days=1)))
    session.add(_assessment(ticker, RUN_DATE))
    for index, (period_end, filing) in enumerate(
        (
            (date(2024, 9, 30), date(2024, 11, 1)),
            (date(2024, 12, 31), date(2025, 2, 1)),
            (date(2025, 3, 31), date(2025, 5, 1)),
            (date(2025, 6, 30), date(2025, 8, 1)),
            (date(2025, 9, 30), date(2025, 11, 1)),
            (date(2025, 12, 31), date(2026, 2, 1)),
            (date(2026, 3, 31), date(2026, 5, 1)),
            (date(2026, 6, 30), date(2026, 8, 1)),
        )
    ):
        session.add(
            FinancialSnapshot(
                ticker=ticker,
                period=period_end.isoformat(),
                snapshot_type="full_statement",
                period_type=("Q1", "H1", "Q3", "FY")[index % 4],
                financial_period_end=period_end,
                financials_as_of=period_end,
                filing_date=filing,
                reported_date=filing,
                provider="fixture_provider",
                source="fixture_filing",
                currency="USD",
                revenue=500.0,
                operating_income=50.0,
                net_income=25.0,
                diluted_eps=1.25,
                common_equity=1_000.0,
                common_shares_outstanding=30.0,
            )
        )
    session.add(
        MonitorRun(
            run_date=RUN_DATE,
            run_type="daily_us",
            status="success",
            completed_at=datetime(2026, 8, 13, 23, 0, tzinfo=UTC),
            ticker_count=1,
            success_count=1,
            failure_count=0,
        )
    )
    session.add(
        MacroBriefing(
            briefing_date=RUN_DATE,
            briefing_type="morning",
            as_of=datetime(2026, 8, 14, 8, 20, tzinfo=UTC),
            headline="mixed",
            market_summary=json.dumps({"observations": []}),
            regime_summary=json.dumps(
                {
                    "label": "mixed",
                    "summary": "Signals are mixed.",
                    "confidence": 0.5,
                    "growth_momentum": 0,
                    "inflation_pressure": 0,
                    "liquidity_condition": 0,
                    "financial_conditions": 0,
                    "risk_appetite": 0,
                    "earnings_momentum": 0,
                }
            ),
            today_calendar="[]",
            macro_theses="[]",
            ticker_impacts="[]",
            data_quality="[]",
            kakao_text="legacy",
            status="ready",
            dedupe_key="macro:2026-08-14:morning",
        )
    )
    session.add(
        NotificationDelivery(
            ticker=ticker,
            assessment_date=RUN_DATE,
            channel="telegram",
            status="sent",
            payload=json.dumps({"text": "deterministic", "type": "daily_stock_analysis"}),
        )
    )
    session.commit()


def _seed_kr(session: Session) -> None:
    ticker = "123450"
    session.add(
        Company(
            ticker=ticker,
            company_name="Packet Korea",
            exchange="KRX",
            industry="Industrial Products",
            sector="Industrials",
        )
    )
    session.add(WatchlistItem(ticker=ticker, company_name="Packet Korea", exchange="KRX"))
    session.add(
        InvestmentThesis(
            ticker=ticker,
            version=1,
            core_thesis="Verified domestic demand supports cash generation.",
        )
    )
    session.add(_assessment(ticker, RUN_DATE, thesis_version=1))
    session.add(
        MonitorRun(
            run_date=RUN_DATE,
            run_type="daily_kr",
            status="success",
            completed_at=datetime(2026, 8, 14, 7, 10, tzinfo=UTC),
            ticker_count=1,
            success_count=1,
            failure_count=0,
        )
    )
    session.add(
        MacroBriefing(
            briefing_date=RUN_DATE,
            briefing_type="morning",
            as_of=datetime(2026, 8, 14, 0, 0, tzinfo=UTC),
            headline="mixed",
            market_summary=json.dumps({"observations": []}),
            regime_summary=json.dumps(
                {
                    "label": "mixed",
                    "summary": "Signals are mixed.",
                    "confidence": 0.5,
                }
            ),
            today_calendar="[]",
            macro_theses="[]",
            ticker_impacts="[]",
            data_quality="[]",
            kakao_text="legacy",
            status="ready",
            dedupe_key="macro:2026-08-14:kr-fixture",
        )
    )
    session.add(
        MacroBriefing(
            briefing_date=RUN_DATE,
            briefing_type="kr_close",
            as_of=datetime(2026, 8, 14, 7, 5, tzinfo=UTC),
            headline="KR close FX",
            market_summary=json.dumps(
                {
                    "fx": [
                        {
                            "series_code": "USDKRW_KR_CLOSE",
                            "value": 1417.4,
                            "change_value": 1.2,
                            "change_pct": 0.08,
                        }
                    ]
                }
            ),
            regime_summary="{}",
            today_calendar="[]",
            macro_theses="[]",
            ticker_impacts="[]",
            data_quality="[]",
            kakao_text="legacy",
            status="ready",
            dedupe_key="macro:2026-08-14:kr-close-fixture",
        )
    )
    session.commit()


def _set_fresh_night_futures(session: Session, *series_codes: str) -> None:
    briefing = session.exec(
        select(MacroBriefing).where(
            MacroBriefing.briefing_date == RUN_DATE,
            MacroBriefing.briefing_type == "morning",
        )
    ).one()
    observations = []
    for series_code in series_codes:
        is_kospi = series_code == "KRX_KOSPI200_NIGHT_FUT"
        observations.append(
            {
                "series_code": series_code,
                "category": "kr_night_futures",
                "value": 431.25 if is_kospi else 1432.5,
                "unit": "index_points",
                "change_value": 2.85 if is_kospi else -4.2,
                "change_pct": 0.67 if is_kospi else -0.29,
                "observed_at": "2026-08-13 00:00:00",
                "retrieved_at": "2026-08-14 08:05:00",
                "market_session": "kr_night",
                "quality_status": "fresh",
                "trade_date": "2026-08-13",
                "expected_latest_session_date": "2026-08-13",
                "session_freshness": "fresh",
            }
        )
    briefing.market_summary = json.dumps(
        {
            "observations": observations,
            "night_futures_gate": {
                "expected_session": "2026-08-13",
                "query_attempted": True,
                "first_query_at": "2026-08-14T08:05:00+09:00",
                "last_query_at": "2026-08-14T08:05:00+09:00",
                "KOSPI200_first_available_at": (
                    "2026-08-14T08:05:00+09:00"
                    if "KRX_KOSPI200_NIGHT_FUT" in series_codes
                    else None
                ),
                "KOSDAQ150_first_available_at": (
                    "2026-08-14T08:05:00+09:00"
                    if "KRX_KOSDAQ150_NIGHT_FUT" in series_codes
                    else None
                ),
            },
        }
    )
    session.add(briefing)
    session.commit()


def _valid_output(
    packet: dict[str, object],
    *,
    claim_id: str = "fixture-claim",
) -> dict[str, object]:
    stock = packet["stocks"][0]
    facts = stock["fact_catalog"]
    market_facts = packet["market_context"]["fact_catalog"]
    price_numeric = next(
        item
        for item in stock["numeric_registry"]
        if item["fact_id"] == "price:current"
        and item["field_path"] == "fields.current_price"
    )
    price_display = next(
        str(item)
        for item in price_numeric["approved_display_variants"]
        if str(item).startswith("$")
    )
    price_usage = f"현재가 {price_display}"
    return {
        "schema_version": "4",
        "packet_id": packet["packet_id"],
        "claim_id": claim_id,
        "analysis_policy_version": packet["analysis_policy_version"],
        "knowledge_version": packet["knowledge"]["version"],
        "knowledge_sha256": packet["knowledge"]["sha256"],
        "chart_knowledge_version": packet["chart_knowledge"]["version"],
        "chart_knowledge_sha256": packet["chart_knowledge"]["sha256"],
        "market": packet["market"],
        "assessment_date": packet["assessment_date"],
        "market_review": {
            "facts_used": [market_facts[0]["fact_id"]] if market_facts else [],
            "frameworks_used": ["macro_transmission"],
            "core_judgment": {
                "text": "Keep the market context separate from company fundamentals.",
                "fact_ids": [market_facts[0]["fact_id"]] if market_facts else [],
            },
            "important_changes": [
                {
                    "text": "The verified market inputs do not establish a new regime.",
                    "fact_ids": [market_facts[0]["fact_id"]] if market_facts else [],
                }
            ],
            "market_context": {
                "text": "The verified market inputs remain mixed.",
                "fact_ids": [market_facts[0]["fact_id"]] if market_facts else [],
            },
            "market_assumptions": {
                "text": "Do not infer a new regime without additional verified evidence.",
                "fact_ids": [market_facts[0]["fact_id"]] if market_facts else [],
            },
            "portfolio_transmission": [],
            "next_checks": [],
            "numeric_claims": [],
            "unknowns": ["Direction remains uncertain."],
        },
        "stock_reviews": [
            {
                "ticker": stock["ticker"],
                "thesis_version": stock["thesis_version"],
                "ai_thesis_assessment": "no_material_change",
                "earnings_estimate_view": "unchanged",
                "valuation_view": "neutral",
                "facts_used": [facts[0]["fact_id"], "price:current"],
                "frameworks_used": ["memory_valuation", "market_expectations"],
                "core_judgment": {
                    "text": "The evidence is supportive but does not require a status change.",
                    "fact_ids": [facts[0]["fact_id"]],
                },
                "business_earnings": {
                    "text": "The verified order supports the existing demand thesis.",
                    "fact_ids": [facts[0]["fact_id"]],
                },
                "price_positioning": {
                    "text": f"{price_usage}은 기업의 질과 별도인 가격 맥락입니다.",
                    "new_observer_view": "Separate company quality from entry valuation.",
                    "holder_view": "Track price confirmation without changing the thesis status.",
                    "fact_ids": ["price:current"],
                },
                "supply_analysis": {
                    "text": "Positioning alone does not change the business thesis.",
                    "fact_ids": [],
                },
                "valuation_analysis": {
                    "text": "Valuation remains a separate decision layer.",
                    "fact_ids": ["valuation:current"],
                },
                "numeric_claims": [
                    {
                        "fact_id": price_numeric["fact_id"],
                        "field_path": price_numeric["field_path"],
                        "value": price_numeric["value"],
                        "unit": price_numeric["unit"],
                        "semantic_type": price_numeric["semantic_type"],
                        "text_ref": "price_positioning.text",
                        "usage": price_usage,
                    }
                ],
                "unknowns": ["Delivery timing remains unknown."],
                "priority_watch": ["Track execution and margin delivery."],
                "next_checks": ["Confirm the next customer delivery update."],
                "confidence": 0.8,
            }
        ],
    }


def test_packet_is_immutable_version_isolated_and_sanitized(monkeypatch, tmp_path: Path) -> None:
    _settings(monkeypatch, tmp_path)
    with Session(_engine()) as session:
        _seed(session)

        first = write_ai_review_packet(
            session,
            RUN_DATE,
            "us",
            generated_at=datetime(2026, 8, 14, 0, 0, tzinfo=UTC),
        )
        second = write_ai_review_packet(
            session,
            RUN_DATE,
            "us",
            generated_at=datetime(2026, 8, 14, 0, 5, tzinfo=UTC),
        )
        packet = json.loads(Path(first.path).read_text(encoding="utf-8"))

    assert first.status == "created"
    assert second.status == "already_exists"
    assert first.packet_id == second.packet_id
    manifest = knowledge_manifest()
    assert packet["knowledge"]["version"] == manifest["version"]
    assert packet["knowledge"]["sha256"] == manifest["sha256"]
    assert packet["stocks"][0]["previous_assessment"]["assessment_date"] == "2026-08-13"
    assert packet["stocks"][0]["valuation"]["historical_comparison_withheld"] is True
    assert "historical_pe_statistics" not in packet["stocks"][0]["valuation"]
    rendered = json.dumps(packet, ensure_ascii=False)
    for token in ("OpenDART", "fs_div", "provider=", "unit=KRW", "raw_fact"):
        assert token not in rendered

    stock = packet["stocks"][0]
    facts = {item["fact_id"]: item for item in stock["fact_catalog"]}
    contract = next(item for item in facts.values() if item["fact_type"] == "contract_award")
    assert contract["fields"]["contract_amount"] == {
        "value": 318_964_597_910,
        "currency": "KRW",
    }
    assert contract["fields"]["counterparty"] == "Verified Customer"
    assert contract["fields"]["contract_period"] == "2026-08-14 to 2028-12-31"
    assert contract["fields"]["sales_ratio_pct"] == 12.4
    capital = facts["event:treasury-D:capital_allocation"]
    assert capital["fields"]["transaction_shares"] == 32_520
    assert capital["fields"]["share_ratio_pct"] == 0.1095
    assert capital["fields"]["purpose"] == "employee compensation"
    assert capital["fields"]["materiality"] == "immaterial"
    assert stock["knowledge_routing"]["industry_key"] == "memory"
    assert "memory_valuation" in stock["knowledge_routing"]["required_frameworks"]
    assert any(
        item["field_path"] == "fields.contract_amount.value"
        and item["semantic_type"] == "contract_amount"
        and item["unit"] == "KRW"
        and "3,190억원" in item["approved_display_variants"]
        for item in stock["numeric_registry"]
    )


def test_kr_packet_is_ready_after_successful_close_and_contains_verified_fx(
    monkeypatch,
    tmp_path: Path,
) -> None:
    _settings(monkeypatch, tmp_path)
    with Session(_engine()) as session:
        _seed_kr(session)

        result = write_ai_review_packet(
            session,
            RUN_DATE,
            "kr",
            generated_at=datetime(2026, 8, 14, 7, 15, tzinfo=UTC),
        )
        packet = json.loads(Path(result.path).read_text(encoding="utf-8"))

    assert result.status == "created"
    assert packet["market"] == "kr"
    assert packet["source_monitor_run"]["status"] == "success"
    assert packet["market_context"]["fx"] == [
        {
            "series_code": "USDKRW_KR_CLOSE",
            "label": "원/달러",
            "value": 1417.4,
            "change_value": 1.2,
            "change_pct": 0.08,
        }
    ]
    assert {
        item["field_path"]: (item["semantic_type"], item["unit"])
        for item in packet["market_context"]["numeric_registry"]
    } == {
        "fields.value": ("fx_rate", "KRW"),
        "fields.change_value": ("fx_point_change", "KRW"),
        "fields.change_pct": ("fx_return_pct", "pct"),
    }


def test_claim_backup_atomic_finalize_and_shadow_no_mutation(monkeypatch, tmp_path: Path) -> None:
    _settings(monkeypatch, tmp_path)
    with Session(_engine()) as session:
        _seed(session)
        packet_result = write_ai_review_packet(
            session,
            RUN_DATE,
            "us",
            generated_at=datetime(2026, 8, 14, 0, 0, tzinfo=UTC),
        )
        before_assessment = session.exec(select(ThesisAssessment).where(
            ThesisAssessment.assessment_date == RUN_DATE
        )).one().model_dump()
        before_delivery = session.exec(select(NotificationDelivery)).one().model_dump()

        claim = claim_next_ai_review_packet(
            "us",
            owner="backup",
            now=datetime(2026, 8, 14, 0, 10, tzinfo=UTC),
        )
        duplicate_claim = claim_next_ai_review_packet(
            "us",
            owner="other",
            now=datetime(2026, 8, 14, 0, 11, tzinfo=UTC),
        )
        packet = json.loads(Path(packet_result.path).read_text(encoding="utf-8"))
        Path(claim.temp_output_path).write_text(
            json.dumps(_valid_output(packet, claim_id=claim.claim_id), ensure_ascii=False),
            encoding="utf-8",
        )
        assert not Path(claim.final_output_path).exists()
        completed = finalize_ai_review_output(
            session,
            packet_result.packet_id,
            claim_id=claim.claim_id,
            now=datetime(2026, 8, 14, 0, 12, tzinfo=UTC),
        )
        after_assessment = session.exec(select(ThesisAssessment).where(
            ThesisAssessment.assessment_date == RUN_DATE
        )).one().model_dump()
        after_delivery = session.exec(select(NotificationDelivery)).one().model_dump()

    assert claim.status == "claimed"
    assert duplicate_claim.status == "no_pending_packet"
    assert completed.status == "completed"
    assert Path(completed.output_path).exists()
    assert Path(completed.comparison_path).exists()
    assert before_assessment == after_assessment
    assert before_delivery == after_delivery


def test_finalize_persists_bound_schema4_and_binding_telemetry(
    monkeypatch,
    tmp_path: Path,
) -> None:
    _settings(monkeypatch, tmp_path)
    with Session(_engine()) as session:
        _seed(session)
        packet_result = write_ai_review_packet(
            session,
            RUN_DATE,
            "us",
            generated_at=datetime(2026, 8, 14, 0, 0, tzinfo=UTC),
        )
        claim = claim_next_ai_review_packet(
            "us",
            owner="binder",
            now=datetime(2026, 8, 14, 0, 10, tzinfo=UTC),
        )
        packet = json.loads(Path(packet_result.path).read_text(encoding="utf-8"))
        draft = _valid_output(packet, claim_id=claim.claim_id)
        review = draft["stock_reviews"][0]
        review["price_positioning"]["text"] = "{{numeric:price_now}} 가격 맥락입니다."
        review["numeric_claims"] = []
        review["numeric_fact_refs"] = [
            {
                "ref_id": "price_now",
                "fact_id": "price:current",
                "field_path": "fields.current_price",
                "text_ref": "price_positioning.text",
            }
        ]
        Path(claim.temp_output_path).write_text(
            json.dumps(draft, ensure_ascii=False),
            encoding="utf-8",
        )

        result = finalize_ai_review_output(
            session,
            packet_result.packet_id,
            claim_id=claim.claim_id,
            now=datetime(2026, 8, 14, 0, 12, tzinfo=UTC),
        )

    assert result.status == "completed"
    final = json.loads(Path(result.output_path).read_text(encoding="utf-8"))
    assert "numeric_fact_refs" not in json.dumps(final)
    assert final["stock_reviews"][0]["price_positioning"]["text"].startswith(
        "현재가 $100"
    )
    binding = next(
        (tmp_path / "ai_review" / "history" / "2026" / "08").glob(
            "*.numeric-binding.json"
        )
    )
    report = json.loads(binding.read_text())
    assert report["status"] == "passed"
    assert report["auto_bound"] == 1
    assert report["manual_legacy"] == 0
    assert report["rejected"] == 0
    assert report["formatting_failures"] == 0


def test_finalize_rejection_archives_canonical_correction_context(
    monkeypatch,
    tmp_path: Path,
) -> None:
    _settings(monkeypatch, tmp_path)
    with Session(_engine()) as session:
        _seed(session)
        packet_result = write_ai_review_packet(
            session,
            RUN_DATE,
            "us",
            generated_at=datetime(2026, 8, 14, 0, 0, tzinfo=UTC),
        )
        claim = claim_next_ai_review_packet(
            "us",
            owner="correction-context",
            now=datetime(2026, 8, 14, 0, 10, tzinfo=UTC),
        )
        packet = json.loads(Path(packet_result.path).read_text(encoding="utf-8"))
        draft = _valid_output(packet, claim_id=claim.claim_id)
        draft["stock_reviews"][0]["valuation_analysis"]["text"] = (
            "내부 추정 EPS $5.5는 수익성 확인이 필요합니다."
        )
        Path(claim.temp_output_path).write_text(
            json.dumps(draft, ensure_ascii=False),
            encoding="utf-8",
        )

        result = finalize_ai_review_output(
            session,
            packet_result.packet_id,
            claim_id=claim.claim_id,
            now=datetime(2026, 8, 14, 0, 12, tzinfo=UTC),
        )

    assert result.status == "rejected"
    sidecar = next((tmp_path / "ai_review" / "rejected").glob("*.validation.json"))
    report = json.loads(sidecar.read_text())
    assert report["fallback_eligibility_preserved"] is True
    context = next(
        item
        for item in report["correction_context"]
        if "numbers_without_provenance" in item["error"]
    )
    assert context["text_ref"] == "valuation_analysis.text"
    assert context["rendered_phrase"] == "내부 추정 EPS $5.5는 수익성 확인이 필요합니다."
    assert context["allowed_actions"] == [
        "correct_reference",
        "correct_wording",
        "remove_unsafe_number",
    ]
    candidate = next(
        item
        for item in context["canonical_candidates"]
        if item["field_path"] == "fields.forward_eps"
    )
    assert candidate["canonical_raw_value"] == 5.5
    assert candidate["canonical_unit"] == "USD"
    assert candidate["canonical_semantic"] == "forward_eps"
    assert candidate["approved_formatted_value"] == "$5.5"


def test_stale_claim_is_recovered_without_duplicate_completion(monkeypatch, tmp_path: Path) -> None:
    _settings(monkeypatch, tmp_path)
    with Session(_engine()) as session:
        _seed(session)
        write_ai_review_packet(
            session,
            RUN_DATE,
            "us",
            generated_at=datetime(2026, 8, 14, 0, 0, tzinfo=UTC),
        )

    first = claim_next_ai_review_packet(
        "us", owner="primary", now=datetime(2026, 8, 14, 0, 1, tzinfo=UTC)
    )
    recovered = claim_next_ai_review_packet(
        "us", owner="backup", now=datetime(2026, 8, 14, 0, 32, tzinfo=UTC)
    )

    assert first.status == "claimed"
    assert first.claim_id != recovered.claim_id
    assert recovered.status == "claimed"
    assert recovered.packet_id == first.packet_id
    claim_data = json.loads(Path(recovered.claim_path).read_text(encoding="utf-8"))
    assert claim_data["owner"] == "backup"
    assert claim_data["claim_id"] == recovered.claim_id
    assert first.temp_output_path != recovered.temp_output_path


def test_new_packet_version_supersedes_older_run_snapshot_for_claiming(
    monkeypatch,
    tmp_path: Path,
) -> None:
    _settings(monkeypatch, tmp_path)
    with Session(_engine()) as session:
        _seed(session)
        first = write_ai_review_packet(
            session,
            RUN_DATE,
            "us",
            generated_at=datetime(2026, 8, 14, 0, 0, tzinfo=UTC),
        )
        assessment = session.exec(
            select(ThesisAssessment).where(ThesisAssessment.assessment_date == RUN_DATE)
        ).one()
        assessment.summary = "A later immutable assessment snapshot."
        session.add(assessment)
        session.commit()
        second = write_ai_review_packet(
            session,
            RUN_DATE,
            "us",
            generated_at=datetime(2026, 8, 14, 0, 5, tzinfo=UTC),
        )

        claim = claim_next_ai_review_packet(
            "us",
            owner="primary",
            now=datetime(2026, 8, 14, 0, 10, tzinfo=UTC),
        )
        packet = json.loads(Path(claim.packet_path).read_text(encoding="utf-8"))
        Path(claim.temp_output_path).write_text(
            json.dumps(_valid_output(packet, claim_id=claim.claim_id), ensure_ascii=False),
            encoding="utf-8",
        )
        completed = finalize_ai_review_output(
            session, claim.packet_id, claim_id=claim.claim_id
        )
        backup = claim_next_ai_review_packet(
            "us",
            owner="backup",
            now=datetime(2026, 8, 14, 0, 20, tzinfo=UTC),
        )

    assert first.packet_id != second.packet_id
    assert claim.packet_id == second.packet_id
    assert completed.status == "completed"
    assert backup.status == "no_pending_packet"


def test_output_guardrails_reject_mismatch_hallucination_and_bad_basis(
    monkeypatch,
    tmp_path: Path,
) -> None:
    _settings(monkeypatch, tmp_path)
    with Session(_engine()) as session:
        _seed(session)
        packet = build_ai_review_packet(session, RUN_DATE, "us")
        assert packet is not None

        version_mismatch = _valid_output(packet)
        version_mismatch["stock_reviews"][0]["thesis_version"] = 1
        _, errors = validate_ai_review_output(session, packet, version_mismatch)
        assert any("thesis_version_mismatch" in item for item in errors)

        hallucination = _valid_output(packet)
        hallucination["stock_reviews"][0]["core_judgment"]["text"] = "Revenue reached 999 billion."
        _, errors = validate_ai_review_output(session, packet, hallucination)
        assert any(
            "numbers_without_provenance:core_judgment.text:999" in item for item in errors
        )

        modeled_as_consensus = _valid_output(packet)
        modeled_as_consensus["stock_reviews"][0]["valuation_analysis"]["text"] = "시장 컨센서스 EPS가 반영됐습니다."
        _, errors = validate_ai_review_output(session, packet, modeled_as_consensus)
        assert any("modeled_forward_called_consensus" in item for item in errors)

        consensus_packet = copy.deepcopy(packet)
        consensus_packet["stocks"][0]["valuation"]["forward_pe_source"] = (
            "consensus_forward"
        )
        consensus_as_modeled = _valid_output(consensus_packet)
        consensus_as_modeled["stock_reviews"][0]["valuation_analysis"]["text"] = (
            "내부 추정 fPER가 반영됐습니다."
        )
        _, errors = validate_ai_review_output(
            session,
            consensus_packet,
            consensus_as_modeled,
        )
        assert any("consensus_forward_called_modeled" in item for item in errors)

        unknown_packet = copy.deepcopy(packet)
        unknown_packet["stocks"][0]["valuation"]["forward_pe_source"] = "unavailable"
        unknown_as_consensus = _valid_output(unknown_packet)
        unknown_as_consensus["stock_reviews"][0]["valuation_analysis"]["text"] = (
            "시장 예상 fPER가 반영됐습니다."
        )
        _, errors = validate_ai_review_output(
            session,
            unknown_packet,
            unknown_as_consensus,
        )
        assert any("unknown_forward_source_labeled" in item for item in errors)

        modeled_pbr_as_consensus = _valid_output(packet)
        modeled_pbr_as_consensus["stock_reviews"][0]["valuation_analysis"][
            "text"
        ] = "시장 예상 fPBR가 반영됐습니다."
        packet["stocks"][0]["valuation"]["forward_price_to_book_source"] = (
            "modeled_forward"
        )
        _, errors = validate_ai_review_output(
            session,
            packet,
            modeled_pbr_as_consensus,
        )
        assert any("modeled_forward_pbr_called_consensus" in item for item in errors)

        identical_audience = _valid_output(packet)
        price = identical_audience["stock_reviews"][0]["price_positioning"]
        price["holder_view"] = price["new_observer_view"]
        _, errors = validate_ai_review_output(session, packet, identical_audience)
        assert any("observer_holder_not_distinct" in item for item in errors)

        invalid_history = _valid_output(packet)
        invalid_history["stock_reviews"][0]["valuation_analysis"]["text"] = "과거 배수 기준으로 저평가입니다."
        _, errors = validate_ai_review_output(session, packet, invalid_history)
        assert any("invalid_historical_comparison_used" in item for item in errors)

        knowledge_mismatch = _valid_output(packet)
        knowledge_mismatch["knowledge_sha256"] = "0" * 64
        _, errors = validate_ai_review_output(session, packet, knowledge_mismatch)
        assert "identity_mismatch:knowledge_sha256" in errors


@pytest.mark.parametrize(
    ("valuation", "text"),
    [
        (
            {
                "forward_pe_source": "modeled_forward",
                "forward_price_to_book_source": "modeled_forward",
            },
            "내부 추정 fPER 10배와 내부 추정 fPBR 2배를 함께 봅니다.",
        ),
        (
            {
                "forward_pe_source": "consensus_forward",
                "forward_price_to_book_source": "consensus_forward",
            },
            "시장 예상 fPER 10배와 시장 예상 fPBR 2배를 함께 봅니다.",
        ),
        (
            {
                "forward_pe_source": "consensus_forward",
                "forward_price_to_book_source": "modeled_forward",
            },
            "시장 예상 fPER 10배와 내부 추정 fPBR 2배를 함께 봅니다.",
        ),
        (
            {
                "forward_pe_source": "modeled_forward",
                "forward_price_to_book_source": "consensus_forward",
            },
            "내부 추정 fPER 10배와 시장 예상 fPBR 2배를 함께 봅니다.",
        ),
        (
            {
                "forward_pe_source": "consensus_forward",
                "forward_price_to_book_source": "modeled_forward",
            },
            "시장 예상 EPS와 내부 추정 BVPS를 함께 봅니다.",
        ),
        (
            {
                "forward_pe_source": "modeled_forward",
                "forward_price_to_book_source": "consensus_forward",
            },
            "내부 추정 EPS와 시장 예상 BVPS를 함께 봅니다.",
        ),
    ],
)
def test_forward_source_language_accepts_metric_local_mixed_sources(
    valuation: dict[str, object],
    text: str,
) -> None:
    assert ai_review_service._forward_source_language_errors(
        "GENERIC",
        valuation,
        text,
    ) == []


@pytest.mark.parametrize(
    ("valuation", "text", "expected"),
    [
        (
            {"forward_pe_source": "modeled_forward"},
            "시장 예상 fPER 10배입니다.",
            "modeled_forward_called_consensus",
        ),
        (
            {"forward_pe_source": "consensus_forward"},
            "내부 추정 fPER 10배입니다.",
            "consensus_forward_called_modeled",
        ),
        (
            {"forward_price_to_book_source": "modeled_forward"},
            "시장 예상 fPBR 2배입니다.",
            "modeled_forward_pbr_called_consensus",
        ),
        (
            {"forward_price_to_book_source": "consensus_forward"},
            "내부 추정 fPBR 2배입니다.",
            "consensus_forward_pbr_called_modeled",
        ),
        (
            {"forward_pe_source": "unavailable"},
            "시장 예상 fPER 10배입니다.",
            "unknown_forward_source_labeled",
        ),
        (
            {"forward_price_to_book_source": "unavailable"},
            "내부 추정 fPBR 2배입니다.",
            "unknown_forward_pbr_source_labeled",
        ),
    ],
)
def test_forward_source_language_rejects_metric_local_mismatch(
    valuation: dict[str, object],
    text: str,
    expected: str,
) -> None:
    errors = ai_review_service._forward_source_language_errors(
        "GENERIC",
        valuation,
        text,
    )
    assert errors == [f"GENERIC:{expected}"]


def test_forward_source_language_does_not_leak_across_metrics_or_sentences() -> None:
    valuation = {
        "forward_pe_source": "consensus_forward",
        "forward_price_to_book_source": "modeled_forward",
    }
    assert ai_review_service._forward_source_language_errors(
        "GENERIC",
        valuation,
        (
            "시장 예상 fPER는 이익 확대를 전제합니다. "
            "내부 추정 fPBR은 장부가 개선을 전제합니다."
        ),
    ) == []
    assert ai_review_service._forward_source_language_errors(
        "GENERIC",
        valuation,
        (
            "시장 예상 fPER를 확인합니다. "
            "기업 내부 모델의 운영 가정은 별도 자료입니다."
        ),
    ) == []


def test_numeric_claims_require_exact_semantic_provenance_and_allow_display_formatting(
    monkeypatch,
    tmp_path: Path,
) -> None:
    _settings(monkeypatch, tmp_path)
    with Session(_engine()) as session:
        _seed(session)
        packet = build_ai_review_packet(session, RUN_DATE, "us")
        assert packet is not None
        stock = packet["stocks"][0]

        valid = _valid_output(packet)
        review = valid["stock_reviews"][0]
        earnings = next(
            item for item in stock["fact_catalog"] if item["fact_type"] == "earnings"
        )
        review["facts_used"].append(earnings["fact_id"])
        review["business_earnings"] = {
            "text": "영업이익률 10%는 현재 수익성의 확인된 기준입니다.",
            "fact_ids": [earnings["fact_id"]],
        }
        review["numeric_claims"].append(
            {
                "fact_id": earnings["fact_id"],
                "field_path": "fields.operating_margin_pct",
                "value": 10.0,
                "unit": "pct",
                "semantic_type": "operating_margin",
                "text_ref": "business_earnings.text",
                "usage": "영업이익률 10%",
            }
        )
        _, errors = validate_ai_review_output(session, packet, valid)
        assert errors == []

        contract = next(
            item for item in stock["fact_catalog"] if item["fact_type"] == "contract_award"
        )
        krw = _valid_output(packet)
        krw_review = krw["stock_reviews"][0]
        krw_review["facts_used"].append(contract["fact_id"])
        krw_review["business_earnings"] = {
            "text": "계약금액 3,190억원은 확인된 수주 규모입니다.",
            "fact_ids": [contract["fact_id"]],
        }
        krw_review["numeric_claims"].append(
            {
                "fact_id": contract["fact_id"],
                "field_path": "fields.contract_amount.value",
                "value": 318_964_597_910,
                "unit": "KRW",
                "semantic_type": "contract_amount",
                "text_ref": "business_earnings.text",
                "usage": "계약금액 3,190억원",
            }
        )
        _, errors = validate_ai_review_output(session, packet, krw)
        assert errors == []

        wrong_semantic = _valid_output(packet)
        wrong_review = wrong_semantic["stock_reviews"][0]
        wrong_review["facts_used"] = ["price:current"]
        wrong_review["business_earnings"] = {
            "text": "매출 성장률은 100 USD입니다.",
            "fact_ids": ["price:current"],
        }
        wrong_review["numeric_claims"] = [
            {
                "fact_id": "price:current",
                "field_path": "fields.current_price",
                "value": 100,
                "unit": "USD",
                "semantic_type": "share_price",
                "text_ref": "business_earnings.text",
                "usage": "매출 성장률 100 USD",
            }
        ]
        _, errors = validate_ai_review_output(session, packet, wrong_semantic)
        assert any("numeric_usage_semantic_mismatch" in item for item in errors)

        unsupported_derived = _valid_output(packet)
        unsupported_derived["stock_reviews"][0]["core_judgment"]["text"] = "추정 성장률은 55%입니다."
        _, errors = validate_ai_review_output(session, packet, unsupported_derived)
        assert any(
            "numbers_without_provenance:core_judgment.text:55" in item for item in errors
        )


def test_percentage_rounding_uses_the_exact_capital_action_field(
    monkeypatch,
    tmp_path: Path,
) -> None:
    _settings(monkeypatch, tmp_path)
    with Session(_engine()) as session:
        _seed(session)
        packet = build_ai_review_packet(session, RUN_DATE, "us")
        assert packet is not None
        capital = next(
            item
            for item in packet["stocks"][0]["fact_catalog"]
            if item["fact_type"] == "treasury_stock_transaction"
        )
        output = _valid_output(packet)
        review = output["stock_reviews"][0]
        review["facts_used"].append(capital["fact_id"])
        review["core_judgment"] = {
            "text": "처분 주식 비율 약 0.11%는 소규모입니다.",
            "fact_ids": [capital["fact_id"]],
        }
        review["numeric_claims"].append(
            {
                "fact_id": capital["fact_id"],
                "field_path": "fields.share_ratio_pct",
                "value": 0.1095,
                "unit": "pct",
                "semantic_type": "share_ratio",
                "text_ref": "core_judgment.text",
                "usage": "처분 주식 비율 약 0.11%",
            }
        )
        _, errors = validate_ai_review_output(session, packet, output)

    assert errors == []


def test_numeric_claim_is_fenced_to_exact_prose_location(
    monkeypatch,
    tmp_path: Path,
) -> None:
    _settings(monkeypatch, tmp_path)
    with Session(_engine()) as session:
        _seed(session)
        packet = build_ai_review_packet(session, RUN_DATE, "us")
        assert packet is not None
        output = _valid_output(packet)
        review = output["stock_reviews"][0]
        review["facts_used"] = ["price:current"]
        review["core_judgment"]["text"] = "매출 성장률은 100%입니다."
        review["price_positioning"]["holder_view"] = "현재가 100 USD에서는 실행 가격을 분리해 봅니다."
        review["numeric_claims"] = [
            {
                "fact_id": "price:current",
                "field_path": "fields.current_price",
                "value": 100,
                "unit": "USD",
                "semantic_type": "share_price",
                "text_ref": "price_positioning.holder_view",
                "usage": "현재가 100 USD",
            }
        ]
        _, errors = validate_ai_review_output(session, packet, output)

    assert any(
        "numbers_without_provenance:core_judgment.text:100" in error for error in errors
    )
    assert not any(
        "numbers_without_provenance:price_positioning.holder_view:100" in error for error in errors
    )


def test_numeric_claim_requires_valid_text_ref_usage_and_semantic_type(
    monkeypatch,
    tmp_path: Path,
) -> None:
    _settings(monkeypatch, tmp_path)
    with Session(_engine()) as session:
        _seed(session)
        packet = build_ai_review_packet(session, RUN_DATE, "us")
        assert packet is not None
        output = _valid_output(packet)
        review = output["stock_reviews"][0]
        review["facts_used"] = ["price:current"]
        review["core_judgment"]["text"] = "현재가 100 USD는 확인된 가격입니다."
        review["numeric_claims"] = [
            {
                "fact_id": "price:current",
                "field_path": "fields.current_price",
                "value": 100,
                "unit": "USD",
                "semantic_type": "revenue_yoy",
                "text_ref": "price_positioning.holder_view",
                "usage": "현재가 100 USD",
            }
        ]
        _, errors = validate_ai_review_output(session, packet, output)

    assert any("numeric_semantic_type_mismatch" in error for error in errors)
    assert any("numeric_usage_not_in_text_ref" in error for error in errors)
    assert any("numbers_without_provenance:core_judgment.text:100" in error for error in errors)


def test_numeric_display_rounding_rejects_unapproved_value(
    monkeypatch,
    tmp_path: Path,
) -> None:
    _settings(monkeypatch, tmp_path)
    with Session(_engine()) as session:
        _seed(session)
        packet = build_ai_review_packet(session, RUN_DATE, "us")
        assert packet is not None
        capital = next(
            item
            for item in packet["stocks"][0]["fact_catalog"]
            if item["fact_type"] == "treasury_stock_transaction"
        )
        output = _valid_output(packet)
        review = output["stock_reviews"][0]
        review["facts_used"] = [capital["fact_id"]]
        review["core_judgment"]["text"] = "처분 주식 비율 약 0.2%는 소규모입니다."
        review["numeric_claims"] = [
            {
                "fact_id": capital["fact_id"],
                "field_path": "fields.share_ratio_pct",
                "value": 0.1095,
                "unit": "pct",
                "semantic_type": "share_ratio",
                "text_ref": "core_judgment.text",
                "usage": "처분 주식 비율 약 0.2%",
            }
        ]
        _, errors = validate_ai_review_output(session, packet, output)

    assert any("numeric_usage_value_mismatch" in error for error in errors)
    assert any("numbers_without_provenance:core_judgment.text:0.2" in error for error in errors)


def test_market_numeric_prose_and_structural_dates_are_validated(
    monkeypatch,
    tmp_path: Path,
) -> None:
    _settings(monkeypatch, tmp_path)
    with Session(_engine()) as session:
        _seed(session)
        packet = build_ai_review_packet(session, RUN_DATE, "us")
        assert packet is not None
        context = packet["market_context"]
        context["fact_catalog"].append(
            {
                "fact_id": "market:test:return",
                "fact_type": "market_return",
                "as_of_date": RUN_DATE.isoformat(),
                "fields": {"percent_change": -3.17},
            }
        )
        context["numeric_registry"] = ai_review_service._numeric_registry(
            context["fact_catalog"]
        )
        output = _valid_output(packet)
        market_review = output["market_review"]
        market_review["facts_used"] = ["market:test:return"]
        market_review["core_judgment"]["text"] = "2026년 2분기 기준 시장 등락률은 -3.17%입니다."
        market_review["numeric_claims"] = [
            {
                "fact_id": "market:test:return",
                "field_path": "fields.percent_change",
                "value": -3.17,
                "unit": "pct",
                "semantic_type": "market_return_pct",
                "text_ref": "core_judgment.text",
                "usage": "시장 등락률은 -3.17%",
            }
        ]
        _, errors = validate_ai_review_output(session, packet, output)

    assert errors == []


def test_signed_positive_market_numeric_prose_is_grounded(
    monkeypatch,
    tmp_path: Path,
) -> None:
    _settings(monkeypatch, tmp_path)
    with Session(_engine()) as session:
        _seed(session)
        packet = build_ai_review_packet(session, RUN_DATE, "us")
        assert packet is not None
        context = packet["market_context"]
        context["fact_catalog"].append(
            {
                "fact_id": "market:test:positive-return",
                "fact_type": "market_return",
                "as_of_date": RUN_DATE.isoformat(),
                "fields": {"percent_change": 0.67},
            }
        )
        context["numeric_registry"] = ai_review_service._numeric_registry(
            context["fact_catalog"]
        )
        output = _valid_output(packet)
        market_review = output["market_review"]
        market_review["facts_used"] = ["market:test:positive-return"]
        market_review["core_judgment"]["text"] = "시장 등락률은 +0.67%였습니다."
        market_review["numeric_claims"] = [
            {
                "fact_id": "market:test:positive-return",
                "field_path": "fields.percent_change",
                "value": 0.67,
                "unit": "pct",
                "semantic_type": "market_return_pct",
                "text_ref": "core_judgment.text",
                "usage": "시장 등락률은 +0.67%",
            }
        ]
        _, errors = validate_ai_review_output(session, packet, output)

    assert errors == []


def test_multiple_and_invented_derived_number_validation(
    monkeypatch,
    tmp_path: Path,
) -> None:
    _settings(monkeypatch, tmp_path)
    with Session(_engine()) as session:
        _seed(session)
        packet = build_ai_review_packet(session, RUN_DATE, "us")
        assert packet is not None
        output = _valid_output(packet)
        review = output["stock_reviews"][0]
        review["facts_used"] = ["valuation:current"]
        review["valuation_analysis"]["text"] = "현재 PER 20배는 확인됐지만 순이익률 10%는 제공되지 않았습니다."
        review["numeric_claims"] = [
            {
                "fact_id": "valuation:current",
                "field_path": "fields.trailing_pe",
                "value": 20,
                "unit": "x",
                "semantic_type": "trailing_pe",
                "text_ref": "valuation_analysis.text",
                "usage": "현재 PER 20배",
            }
        ]
        _, errors = validate_ai_review_output(session, packet, output)

    assert not any("valuation_analysis.text:20" in error for error in errors)
    assert any("numbers_without_provenance:valuation_analysis.text:10" in error for error in errors)


def test_structural_count_whitelist_does_not_hide_business_quantity(
    monkeypatch,
    tmp_path: Path,
) -> None:
    _settings(monkeypatch, tmp_path)
    with Session(_engine()) as session:
        _seed(session)
        packet = build_ai_review_packet(session, RUN_DATE, "us")
        assert packet is not None
        output = _valid_output(packet)
        review = output["stock_reviews"][0]
        review["core_judgment"]["text"] = "핵심 요인 2가지를 봤지만 계약 수량 100개는 근거가 없습니다."
        review["numeric_claims"] = []
        _, errors = validate_ai_review_output(session, packet, output)

    assert not any("core_judgment.text:2" in error for error in errors)
    assert any("numbers_without_provenance:core_judgment.text:100" in error for error in errors)


def test_claim_fence_rejects_expired_primary_after_backup_reclaim(
    monkeypatch,
    tmp_path: Path,
) -> None:
    _settings(monkeypatch, tmp_path)
    with Session(_engine()) as session:
        _seed(session)
        write_ai_review_packet(
            session,
            RUN_DATE,
            "us",
            generated_at=datetime(2026, 8, 14, 0, 0, tzinfo=UTC),
        )
        primary = claim_next_ai_review_packet(
            "us", owner="us-primary", now=datetime(2026, 8, 14, 8, 50, tzinfo=UTC)
        )
        active_worker = claim_next_ai_review_packet(
            "us", owner="early-backup", now=datetime(2026, 8, 14, 9, 10, tzinfo=UTC)
        )
        backup = claim_next_ai_review_packet(
            "us", owner="us-backup", now=datetime(2026, 8, 14, 9, 30, tzinfo=UTC)
        )
        packet = json.loads(Path(backup.packet_path).read_text(encoding="utf-8"))
        Path(primary.temp_output_path).write_text(
            json.dumps(_valid_output(packet, claim_id=primary.claim_id)), encoding="utf-8"
        )
        Path(backup.temp_output_path).write_text(
            json.dumps(_valid_output(packet, claim_id=backup.claim_id)), encoding="utf-8"
        )
        winner = finalize_ai_review_output(
            session, backup.packet_id, claim_id=backup.claim_id
        )
        stale = finalize_ai_review_output(
            session, primary.packet_id, claim_id=primary.claim_id
        )
        final_payload = json.loads(Path(winner.output_path).read_text(encoding="utf-8"))

    assert active_worker.status == "no_pending_packet"
    assert backup.status == "claimed"
    assert winner.status == "completed"
    assert stale.status == "rejected"
    assert stale.errors == ("stale_claim_output",)
    assert final_payload["claim_id"] == backup.claim_id


def test_us_primary_short_lease_allows_0830_backup_reclaim(
    monkeypatch,
    tmp_path: Path,
) -> None:
    _settings(monkeypatch, tmp_path)
    with Session(_engine()) as session:
        _seed(session)
        write_ai_review_packet(
            session,
            RUN_DATE,
            "us",
            generated_at=datetime(2026, 8, 14, 0, 10, tzinfo=UTC),
        )
        primary = claim_next_ai_review_packet(
            "us",
            owner="us-primary",
            now=datetime(2026, 8, 14, 0, 15, tzinfo=UTC),
            lease_minutes=10,
        )
        early = claim_next_ai_review_packet(
            "us",
            owner="us-backup-early",
            now=datetime(2026, 8, 14, 0, 24, tzinfo=UTC),
        )
        backup = claim_next_ai_review_packet(
            "us",
            owner="us-backup",
            now=datetime(2026, 8, 14, 0, 30, tzinfo=UTC),
        )

    assert primary.status == "claimed"
    assert early.status == "no_pending_packet"
    assert backup.status == "claimed"
    assert backup.claim_id != primary.claim_id
    assert json.loads(Path(backup.claim_path).read_text())["owner"] == "us-backup"
    assert primary.temp_output_path != backup.temp_output_path


def test_expired_claim_can_finalize_when_no_worker_reclaims(
    monkeypatch,
    tmp_path: Path,
) -> None:
    _settings(monkeypatch, tmp_path)
    with Session(_engine()) as session:
        _seed(session)
        result = write_ai_review_packet(
            session,
            RUN_DATE,
            "us",
            generated_at=datetime(2026, 8, 14, 0, 0, tzinfo=UTC),
        )
        claim = claim_next_ai_review_packet(
            "us", owner="primary", now=datetime(2026, 8, 14, 8, 50, tzinfo=UTC)
        )
        packet = json.loads(Path(result.path).read_text(encoding="utf-8"))
        Path(claim.temp_output_path).write_text(
            json.dumps(_valid_output(packet, claim_id=claim.claim_id)), encoding="utf-8"
        )
        completed = finalize_ai_review_output(
            session,
            claim.packet_id,
            claim_id=claim.claim_id,
            now=datetime(2026, 8, 14, 9, 30, tzinfo=UTC),
        )

    assert completed.status == "completed"


def test_packet_lock_serializes_simultaneous_claims(monkeypatch, tmp_path: Path) -> None:
    _settings(monkeypatch, tmp_path)
    with Session(_engine()) as session:
        _seed(session)
        write_ai_review_packet(
            session,
            RUN_DATE,
            "us",
            generated_at=datetime(2026, 8, 14, 0, 0, tzinfo=UTC),
        )

    barrier = threading.Barrier(2)

    def claim(owner: str):
        barrier.wait(timeout=5)
        return claim_next_ai_review_packet(
            "us",
            owner=owner,
            now=datetime(2026, 8, 14, 8, 50, tzinfo=UTC),
        )

    with ThreadPoolExecutor(max_workers=2) as executor:
        results = list(executor.map(claim, ("primary", "backup")))

    assert sorted(item.status for item in results) == ["claimed", "no_pending_packet"]
    winner = next(item for item in results if item.status == "claimed")
    active = json.loads(Path(winner.claim_path).read_text(encoding="utf-8"))
    assert active["claim_id"] == winner.claim_id


def test_packet_lock_prevents_reclaim_after_finalizer_wins(
    monkeypatch,
    tmp_path: Path,
) -> None:
    _settings(monkeypatch, tmp_path)
    engine = _engine()
    with Session(engine) as session:
        _seed(session)
        result = write_ai_review_packet(
            session,
            RUN_DATE,
            "us",
            generated_at=datetime(2026, 8, 14, 0, 0, tzinfo=UTC),
        )
    primary = claim_next_ai_review_packet(
        "us", owner="primary", now=datetime(2026, 8, 14, 8, 50, tzinfo=UTC)
    )
    packet = json.loads(Path(result.path).read_text(encoding="utf-8"))
    Path(primary.temp_output_path).write_text(
        json.dumps(_valid_output(packet, claim_id=primary.claim_id)),
        encoding="utf-8",
    )

    original_read = ai_review_service._read_json
    final_lock_held = threading.Event()
    release_finalizer = threading.Event()
    claim_reads = 0

    def pausing_read(path: Path):
        nonlocal claim_reads
        value = original_read(path)
        if threading.current_thread().name == "finalizer" and path == Path(primary.claim_path):
            claim_reads += 1
            if claim_reads == 2:
                final_lock_held.set()
                assert release_finalizer.wait(timeout=5)
        return value

    monkeypatch.setattr(ai_review_service, "_read_json", pausing_read)
    outcomes: dict[str, object] = {}

    def finalize() -> None:
        with Session(engine) as session:
            outcomes["final"] = finalize_ai_review_output(
                session,
                primary.packet_id,
                claim_id=primary.claim_id,
            )

    def reclaim() -> None:
        outcomes["backup"] = claim_next_ai_review_packet(
            "us",
            owner="backup",
            now=datetime(2026, 8, 14, 9, 30, tzinfo=UTC),
        )

    final_thread = threading.Thread(target=finalize, name="finalizer")
    final_thread.start()
    assert final_lock_held.wait(timeout=5)
    backup_thread = threading.Thread(target=reclaim, name="backup")
    backup_thread.start()
    backup_thread.join(timeout=0.1)
    assert backup_thread.is_alive()
    release_finalizer.set()
    final_thread.join(timeout=5)
    backup_thread.join(timeout=5)

    assert outcomes["final"].status == "completed"
    assert outcomes["backup"].status == "no_pending_packet"
    final_payload = json.loads(Path(primary.final_output_path).read_text(encoding="utf-8"))
    assert final_payload["claim_id"] == primary.claim_id


def test_packet_lock_reclaim_fences_stale_finalizer_and_preserves_new_claim(
    monkeypatch,
    tmp_path: Path,
) -> None:
    _settings(monkeypatch, tmp_path)
    engine = _engine()
    with Session(engine) as session:
        _seed(session)
        result = write_ai_review_packet(
            session,
            RUN_DATE,
            "us",
            generated_at=datetime(2026, 8, 14, 0, 0, tzinfo=UTC),
        )
    primary = claim_next_ai_review_packet(
        "us", owner="primary", now=datetime(2026, 8, 14, 8, 50, tzinfo=UTC)
    )
    packet = json.loads(Path(result.path).read_text(encoding="utf-8"))
    Path(primary.temp_output_path).write_text(
        json.dumps(_valid_output(packet, claim_id=primary.claim_id)),
        encoding="utf-8",
    )

    original_atomic = ai_review_service._atomic_json
    reclaim_lock_held = threading.Event()
    release_backup = threading.Event()

    def pausing_atomic(path: Path, payload: object) -> None:
        if (
            threading.current_thread().name == "backup"
            and path == Path(primary.claim_path)
        ):
            reclaim_lock_held.set()
            assert release_backup.wait(timeout=5)
        original_atomic(path, payload)

    monkeypatch.setattr(ai_review_service, "_atomic_json", pausing_atomic)
    outcomes: dict[str, object] = {}

    def reclaim() -> None:
        outcomes["backup"] = claim_next_ai_review_packet(
            "us",
            owner="backup",
            now=datetime(2026, 8, 14, 9, 30, tzinfo=UTC),
        )

    def finalize() -> None:
        with Session(engine) as session:
            outcomes["final"] = finalize_ai_review_output(
                session,
                primary.packet_id,
                claim_id=primary.claim_id,
            )

    backup_thread = threading.Thread(target=reclaim, name="backup")
    backup_thread.start()
    assert reclaim_lock_held.wait(timeout=5)
    final_thread = threading.Thread(target=finalize, name="finalizer")
    final_thread.start()
    final_thread.join(timeout=0.1)
    assert final_thread.is_alive()
    release_backup.set()
    backup_thread.join(timeout=5)
    final_thread.join(timeout=5)

    backup = outcomes["backup"]
    stale = outcomes["final"]
    active = json.loads(Path(primary.claim_path).read_text(encoding="utf-8"))
    assert backup.status == "claimed"
    assert stale.status == "rejected"
    assert stale.errors == ("stale_claim_output",)
    assert active["claim_id"] == backup.claim_id
    assert not Path(primary.final_output_path).exists()


def test_full_knowledge_manifest_and_industry_routing_are_valid() -> None:
    root = Path(__file__).resolve().parents[1]
    references = root / ".agents" / "skills" / "thesis-monitor-daily-review" / "references"
    source = root / CANONICAL_PATH
    upload = root / UPLOAD_PATH
    mirror = root / SKILL_PATH
    manifest = knowledge_manifest()

    assert source.read_bytes() == upload.read_bytes()
    assert source.read_bytes() == mirror.read_bytes()
    assert hashlib.sha256(mirror.read_bytes()).hexdigest() == manifest["sha256"]
    assert len(source.read_bytes()) == manifest["byte_count"]
    assert len(source.read_bytes().splitlines()) == manifest["line_count"]
    assert manifest["version"] == "3.0"
    index = (references / "knowledge-index.md").read_text(encoding="utf-8")
    knowledge = mirror.read_text(encoding="utf-8")
    for heading in (
        "## 5. Earnings Quality",
        "## 6. Market Expectations & Surprise",
        "## 10. Risk / Early Warning / Kill Condition",
        "## 12. Macro Transmission",
        "### 12.3 FOMC Interpretation Framework",
        "### 12.4 Hyperscaler CAPEX Transmission",
        "## 13. 공식 잠정실적",
        "## 14. Valuation Basis Comparability",
        "## 18. Initial Analysis 사용자 답변 Template",
    ):
        assert heading in knowledge
    for framework in (
        "earnings_quality",
        "memory_valuation",
        "insurance_reinsurance_valuation",
        "epc_construction_valuation",
        "saas_recurring_revenue_valuation",
        "adr_share_basis",
    ):
        assert framework in index


def test_canonical_knowledge_import_preserves_exact_bytes(tmp_path: Path) -> None:
    root = tmp_path / "repository"
    references = root / ".agents" / "skills" / "thesis-monitor-daily-review" / "references"
    references.mkdir(parents=True)
    canonical = root / CANONICAL_PATH
    canonical.parent.mkdir(parents=True)
    canonical_bytes = b"\xef\xbb\xbf# Canonical\r\n\r\nExact bytes without final newline"
    canonical.write_bytes(canonical_bytes)

    metrics = sync_repository_mirror(
        root,
        mirror_revision="test-canonical-import",
    )
    validated = validate_repository_mirror(root)
    upload = (root / UPLOAD_PATH).read_bytes()
    runtime = (root / SKILL_PATH).read_bytes()
    manifest = json.loads((root / MANIFEST_PATH).read_text(encoding="utf-8"))

    assert upload == canonical_bytes
    assert runtime == canonical_bytes
    assert metrics == validated
    assert manifest["sha256"] == hashlib.sha256(canonical_bytes).hexdigest()
    assert manifest["source_role"] == "knowledge_v3_canonical"
    assert manifest["knowledge_version"] == "3.0"
    assert "/Users/" not in json.dumps(manifest)


def test_knowledge_v3_sources_decisions_and_safety_markers() -> None:
    root = Path(__file__).resolve().parents[1]
    knowledge_root = root / "docs" / "knowledge"
    current = knowledge_root / "archive" / "current-custom-gpt-knowledge-before-v3.md"
    donor = knowledge_root / "archive" / "1-thesis_monitor_analysis_knowledge_v2.md"
    canonical = root / CANONICAL_PATH
    decisions = json.loads(
        (knowledge_root / "knowledge-v3-merge-decisions.json").read_text(
            encoding="utf-8"
        )
    )
    source_expectations = (
        (
            current,
            "2acc979bcfc06c7fa8c30ddbbb0a73e1f30017359d9668613970fd1bb0fd8518",
            648,
            28988,
        ),
        (
            donor,
            "9c769f6be1ea6d17b858a14b35a7b2cd63201c0dc8066f7b05368d9bab967176",
            942,
            16599,
        ),
    )
    for path, expected_hash, expected_lines, expected_bytes in source_expectations:
        payload = path.read_bytes()
        assert hashlib.sha256(payload).hexdigest() == expected_hash
        assert len(payload.splitlines()) == expected_lines
        assert len(payload) == expected_bytes

    payload = canonical.read_bytes()
    text = payload.decode("utf-8")
    assert decisions["v3"]["sha256"] == hashlib.sha256(payload).hexdigest()
    assert decisions["v3"]["line_count"] == len(payload.splitlines())
    assert decisions["v3"]["byte_count"] == len(payload)
    classifications = {
        item["classification"] for item in decisions["decisions"]
    }
    assert classifications == {
        "KEEP_CURRENT",
        "MERGE_FROM_V2",
        "REWRITE_COMBINED",
        "DROP_V2",
        "OPERATIONAL_NOT_KNOWLEDGE",
    }

    safety_markers = (
        "최근 한 분기 EPS에 4를 곱하는 식의 임의 연율화는 금지",
        "ratio 방향이 함께 확인된 경우에만 직접 계산",
        "Historical percentile은 과거 분포와 같은 회계·주식 기준",
        "내부 모델 추정치를 시장 컨센서스라고 표현하지 않는다",
        "실제 Action 또는 backend packet에 제공된 지표만 사용",
        "수급만으로 사업 논리, 이익 추정, Valuation 또는 warning lifecycle을 변경하지 않는다",
    )
    for marker in safety_markers:
        assert marker in text

    analytical_depth_markers = (
        "Decision",
        "Dot Plot",
        "Press Conference",
        "Hyperscaler CAPEX",
        "Budget → Order → Shipment → Revenue Recognition",
        "가격 상승 + 거래량 증가",
    )
    for marker in analytical_depth_markers:
        assert marker in text

    forbidden_or_operational = (
        "80+: 고품질 재검토 후보",
        "<1.0      추격 위험",
        "Local Share Equivalent",
        "07:50",
        "08:45",
        "16:05",
        "LaunchAgent",
    )
    for marker in forbidden_or_operational:
        assert marker not in text


def test_dual_knowledge_policy_identity_starts_v38_stateful_cohort() -> None:
    assert ai_review_service.ANALYSIS_POLICY_VERSION == "daily-review-v3.10"
    assert ai_review_service.OUTPUT_SCHEMA_VERSION == "4"
    manifest = knowledge_manifest()
    assert manifest["version"] == "3.0"
    assert manifest["sha256"] == (
        "559ad45e4dd86cb0aec9bb09b51a5dc816bf323e8c2b4fd050cf28960a5a9d18"
    )
    chart_manifest = ai_review_service.chart_knowledge_manifest()
    assert chart_manifest["version"] == "1.0"
    assert chart_manifest["sha256"] == (
        "beee64559831479168f1347c43d979391126926d73e2473ce837cefbf0ede19b"
    )


def test_chart_knowledge_source_and_runtime_are_byte_identical() -> None:
    root = Path(__file__).resolve().parents[1]
    source = root / "docs" / "knowledge" / "stock-chart-value-analysis-knowledge-v1.md"
    runtime = (
        root
        / ".agents"
        / "skills"
        / "thesis-monitor-daily-review"
        / "references"
        / "stock-chart-value-analysis-knowledge-v1.md"
    )
    manifest = json.loads(
        (
            runtime.parent / "chart-knowledge-manifest.json"
        ).read_text(encoding="utf-8")
    )
    payload = source.read_bytes()

    assert payload == runtime.read_bytes()
    assert hashlib.sha256(payload).hexdigest() == manifest["sha256"]
    assert len(payload.splitlines()) == manifest["line_count"] == 2472
    assert len(payload) == manifest["byte_count"] == 51132


def test_packet_adds_fresh_chart_context_transition_and_numeric_provenance(
    monkeypatch,
    tmp_path: Path,
) -> None:
    _settings(monkeypatch, tmp_path)
    with Session(_engine()) as session:
        _seed(session)
        thesis = session.exec(
            select(InvestmentThesis).where(InvestmentThesis.ticker == "PACKETUS")
        ).one()
        thesis.price_rules = json.dumps(
            {
                "currency": "USD",
                "basis": "adjusted_close",
                "confirmation_price": 95.0,
                "support_zone_low": 80.0,
                "support_zone_high": 85.0,
                "warning_price": 75.0,
                "invalidation_price": 70.0,
            }
        )
        assessments = session.exec(
            select(ThesisAssessment)
            .where(ThesisAssessment.ticker == "PACKETUS")
            .order_by(ThesisAssessment.assessment_date)
        ).all()
        previous, current = assessments
        previous.price_context = json.dumps(
            {
                "decision": {
                    "current_price": 90.0,
                    "currency": "USD",
                    "price_as_of": (RUN_DATE - timedelta(days=1)).isoformat(),
                    "price_state": "between_confirmation_and_support",
                }
            }
        )
        current.price_context = json.dumps(
            {
                "decision": {
                    "current_price": 100.0,
                    "currency": "USD",
                    "price_as_of": RUN_DATE.isoformat(),
                    "price_state": "above_confirmation",
                },
                "supply": {
                    "available": True,
                    "as_of_date": RUN_DATE.isoformat(),
                    "foreign_net_buy_qty": 10,
                    "foreign_net_buy_qty_5": 50,
                    "foreign_net_buy_qty_20": -200,
                    "primary_signal": "mixed",
                },
                "chart": {
                    "available": True,
                    "source": "ohlcv_analyst",
                    "as_of_date": RUN_DATE.isoformat(),
                    "quality": "fresh",
                    "price_basis": "adjusted_close",
                    "timeframes": {
                        "daily": {
                            "timeframe": "daily",
                            "as_of_date": RUN_DATE.isoformat(),
                            "quality": "fresh",
                            "price_basis": "adjusted_close",
                            "candle": {
                                "open": 98.0,
                                "high": 102.0,
                                "low": 97.0,
                                "close": 100.0,
                                "volume": 1000,
                            },
                            "bollinger_upper": {"3_month": 101.0},
                            "bollinger_distance_pct": {"3_month": -0.9901},
                            "volume_ratio_20": 1.2,
                            "rsi_14": 61.4,
                            "macd": 3.2,
                        },
                        "weekly": {
                            "timeframe": "weekly",
                            "quality": "unavailable",
                        },
                    },
                    "unavailable_fields": ["support_zones", "atr", "elliott_wave"],
                    "structure": {
                        "algorithm_version": "ohlcv-structure-v2",
                        "as_of_date": RUN_DATE.isoformat(),
                        "price_basis": "adjusted_close",
                        "availability": {
                            "atr": True,
                            "support_resistance": True,
                            "box_ranges": True,
                            "major_swings": True,
                            "elliott_wave": True,
                            "fibonacci": True,
                            "risk_reward": True,
                            "invalidation": True,
                            "chart_state_machine": True,
                        },
                        "atr": {
                            "daily": {
                                "available": True,
                                "period": 14,
                                "method": "wilder_recursive",
                                "value": 3.5,
                            }
                        },
                        "zones": {
                            "support": [
                                {
                                    "zone_low": 90.0,
                                    "zone_high": 93.0,
                                    "distance_pct": 7.0,
                                    "timeframe": "daily",
                                    "strength": "Strong",
                                }
                            ],
                            "resistance": [
                                {
                                    "zone_low": 108.0,
                                    "zone_high": 110.0,
                                    "distance_pct": 8.0,
                                    "timeframe": "weekly",
                                    "strength": "Medium",
                                }
                            ],
                            "active": [],
                        },
                        "boxes": {
                            "daily": [
                                {"box_low": 90.0, "box_high": 110.0, "width_pct": 20.0}
                            ]
                        },
                        "major_swings": {
                            "primary_timeframe": "weekly",
                            "fallback_used": False,
                            "points": [
                                {
                                    "date": "2026-05-01",
                                    "price": 80.0,
                                    "kind": "low",
                                    "timeframe": "weekly",
                                    "confirmed_at": "2026-05-29",
                                },
                                {
                                    "date": "2026-07-01",
                                    "price": 120.0,
                                    "kind": "high",
                                    "timeframe": "weekly",
                                    "confirmed_at": "2026-07-29",
                                },
                            ],
                        },
                        "major_anchors": {},
                        "elliott": {
                            "available": True,
                            "tentative_count": True,
                            "confidence": "low",
                            "usable_in_core": False,
                        },
                        "fibonacci": {
                            "long_term": {
                                "anchor_type": "long_term",
                                "low_price": 80.0,
                                "low_date": "2026-05-01",
                                "high_price": 120.0,
                                "high_date": "2026-07-01",
                                "timeframe": "weekly",
                                "confidence": "high",
                                "usable_in_core": True,
                                "usable_as_context": True,
                                "usable_as_sole_core_reason": True,
                                "audit_only": False,
                                "retracements": {"0.5": 100.0},
                                "extensions": {"1.618": 144.72},
                            }
                        },
                        "fibonacci_status": {
                            "available": True,
                            "reason": None,
                            "anchor_alignment": {"valid": True, "reason": None},
                        },
                        "invalidation": {
                            "available": True,
                            "price": 87.0,
                            "entry": 91.5,
                            "support_low": 90.0,
                            "buffer": 3.0,
                            "scenario": "support_entry",
                            "timeframe": "daily",
                            "status": "intact",
                            "chart_only": True,
                        },
                        "risk_reward": {
                            "available": True,
                            "current_price": {
                                "entry": 100.0,
                                "target": 108.0,
                                "invalidation": 87.0,
                                "upside": 8.0,
                                "downside": 13.0,
                                "ratio": 0.615385,
                                "scenario": "current_price",
                                "classification": "poor_chase",
                            }
                        },
                        "supply_classification": {
                            "classification": "unavailable",
                            "confidence": "low",
                        },
                        "chart_state": {
                            "state": "WAIT",
                            "confidence": "medium",
                            "reasons": ["rr_below_1_5"],
                            "blocking_unknowns": ["verified_supply_unavailable"],
                            "user_semantics": "price_structure_wait_not_sell_command",
                        },
                    },
                },
            }
        )
        session.add(thesis)
        session.add(previous)
        session.add(current)
        session.commit()

        packet = build_ai_review_packet(session, RUN_DATE, "us")

    assert packet is not None
    stock = packet["stocks"][0]
    chart = stock["chart_context"]
    assert chart["source"] == "ohlcv_analyst"
    assert chart["price_transition"]["threshold_event"] == "confirmation_crossed"
    assert chart["price_transition"]["retest_status"] == "awaiting_retest"
    assert chart["price_transition"]["volume_confirmation"] == "above_20d_average"
    assert chart["distance_from_stored_rules_pct"]["confirmation_distance_pct"] == (
        pytest.approx(5.2632)
    )
    fact_ids = {item["fact_id"] for item in stock["fact_catalog"]}
    assert {
        "chart:daily",
        "chart:stored_price_rules",
        "chart:price_transition",
        "chart:structure:atr:daily",
        "chart:structure:nearest_supports:1",
        "chart:structure:nearest_resistance:1",
        "chart:structure:box:daily:1",
        "chart:structure:major_swing:1",
        "chart:structure:fibonacci:long_term",
        "chart:structure:invalidation",
        "chart:structure:risk_reward:current_price",
        "chart:structure:state",
    } <= fact_ids
    assert "chart:weekly" not in fact_ids
    semantics = {item["semantic_type"] for item in stock["numeric_registry"]}
    assert {
        "chart_close_price",
        "bollinger_upper_price",
        "bollinger_distance_pct",
        "volume_ratio_20",
        "rsi_14",
        "stored_confirmation_price",
        "foreign_net_buy_qty_5d",
        "foreign_net_buy_qty_20d",
        "chart_atr",
        "support_zone_price",
        "resistance_zone_price",
        "box_boundary_price",
        "major_swing_price",
        "fibonacci_retracement_price",
        "fibonacci_extension_price",
        "chart_invalidation_price",
        "risk_reward_ratio",
    } <= semantics
    assert stock["chart_knowledge_routing"]["available"] is True
    assert "chart_bollinger" in stock["chart_knowledge_routing"]["required_frameworks"]
    assert "chart_support_resistance" in stock["chart_knowledge_routing"]["required_frameworks"]
    assert "chart_elliott" not in stock["chart_knowledge_routing"]["required_frameworks"]
    assert chart["structure"]["algorithm_version"] == "ohlcv-structure-v2"
    assert "all_zones" not in chart["structure"]
    assert "local_pivots" not in chart["structure"]


def test_low_confidence_fibonacci_is_audit_only_and_not_an_ai_fact() -> None:
    chart = {
        "available": True,
        "quality": "fresh",
        "timeframes": {},
        "structure": {
            "as_of_date": RUN_DATE.isoformat(),
            "fibonacci": {
                "long_term": {
                    "anchor_type": "long_term",
                    "low_price": 80.0,
                    "low_date": "2026-05-01",
                    "high_price": 120.0,
                    "high_date": "2026-07-01",
                    "timeframe": "weekly",
                    "confidence": "low",
                    "usable_in_core": False,
                    "usable_as_context": False,
                    "usable_as_sole_core_reason": False,
                    "audit_only": True,
                    "retracements": {"0.5": 100.0},
                    "extensions": {"1.618": 144.72},
                }
            },
        },
    }

    facts = ai_review_service._chart_facts(chart, "USD")

    assert not any(
        fact["fact_id"] == "chart:structure:fibonacci:long_term"
        for fact in facts
    )


def test_stale_chart_is_not_routed_or_exposed_as_numeric_fact(
    monkeypatch,
    tmp_path: Path,
) -> None:
    _settings(monkeypatch, tmp_path)
    with Session(_engine()) as session:
        _seed(session)
        current = session.exec(
            select(ThesisAssessment).where(
                ThesisAssessment.ticker == "PACKETUS",
                ThesisAssessment.assessment_date == RUN_DATE,
            )
        ).one()
        current.price_context = json.dumps(
            {
                "decision": {"current_price": 100.0, "currency": "USD"},
                "chart": {
                    "available": True,
                    "quality": "stale",
                    "price_basis": "adjusted_close",
                    "timeframes": {
                        "daily": {
                            "timeframe": "daily",
                            "quality": "stale",
                            "candle": {"close": 100.0},
                            "rsi_14": 70.0,
                        }
                    },
                },
            }
        )
        session.add(current)
        session.commit()

        packet = build_ai_review_packet(session, RUN_DATE, "us")

    assert packet is not None
    stock = packet["stocks"][0]
    assert stock["chart_knowledge_routing"]["available"] is False
    assert stock["chart_knowledge_routing"]["required_frameworks"] == []
    assert not any(
        item["fact_type"] == "chart_timeframe" for item in stock["fact_catalog"]
    )


def test_price_transition_baseline_does_not_inherit_another_thesis_version() -> None:
    transition = ai_review_service._price_transition(
        {
            "price_state": "above_confirmation",
            "price_as_of": RUN_DATE.isoformat(),
        },
        {},
    )

    assert transition["previous_state"] == "baseline"
    assert transition["threshold_event"] == "baseline"


def test_numeric_semantics_fail_closed_for_unknown_and_disallowed_fields(
    monkeypatch,
    tmp_path: Path,
) -> None:
    _settings(monkeypatch, tmp_path)
    with Session(_engine()) as session:
        _seed(session)
        packet = build_ai_review_packet(session, RUN_DATE, "us")
        assert packet is not None
        stock = packet["stocks"][0]
        stock["fact_catalog"].append(
            {
                "fact_id": "event:mystery",
                "fact_type": "mystery_event",
                "as_of_date": RUN_DATE.isoformat(),
                "fields": {"mystery_ratio": 7.0},
            }
        )
        stock["numeric_registry"] = ai_review_service._numeric_registry(
            stock["fact_catalog"]
        )
        unknown = next(
            item
            for item in stock["numeric_registry"]
            if item["fact_id"] == "event:mystery"
        )
        assert unknown["registered"] is False
        assert unknown["prose_allowed"] is False

        output = _valid_output(packet)
        review = output["stock_reviews"][0]
        review["facts_used"] = ["event:mystery"]
        review["core_judgment"]["text"] = "미확인 비율 7은 사용할 수 없습니다."
        review["numeric_claims"] = [
            {
                "fact_id": "event:mystery",
                "field_path": "fields.mystery_ratio",
                "value": 7,
                "unit": "number",
                "semantic_type": unknown["semantic_type"],
                "text_ref": "core_judgment.text",
                "usage": "미확인 비율 7",
            }
        ]
        _, errors = validate_ai_review_output(session, packet, output)

    assert any("numeric_semantic_not_supported" in error for error in errors)


def test_numeric_semantics_reject_cross_metric_labels(
    monkeypatch,
    tmp_path: Path,
) -> None:
    _settings(monkeypatch, tmp_path)
    with Session(_engine()) as session:
        _seed(session)
        packet = build_ai_review_packet(session, RUN_DATE, "us")
        assert packet is not None
        stock = packet["stocks"][0]
        positioning = {
            "fact_id": "positioning:test",
            "fact_type": "positioning",
            "as_of_date": RUN_DATE.isoformat(),
            "fields": {"foreign_net_buy_qty": -100},
        }
        stock["fact_catalog"].append(positioning)
        stock["numeric_registry"] = ai_review_service._numeric_registry(
            stock["fact_catalog"]
        )

        output = _valid_output(packet)
        review = output["stock_reviews"][0]
        review["facts_used"] = ["positioning:test"]
        review["supply_analysis"]["text"] = "기관 순매도 -100주는 확인된 수급입니다."
        review["numeric_claims"] = [
            {
                "fact_id": "positioning:test",
                "field_path": "fields.foreign_net_buy_qty",
                "value": -100,
                "unit": "shares",
                "semantic_type": "foreign_net_buy_qty",
                "text_ref": "supply_analysis.text",
                "usage": "기관 순매도 -100주",
            }
        ]
        _, supply_errors = validate_ai_review_output(session, packet, output)

        valuation = _valid_output(packet)
        valuation_review = valuation["stock_reviews"][0]
        valuation_review["facts_used"] = ["valuation:current"]
        valuation_review["valuation_analysis"]["text"] = "현재 PBR 20배는 확인된 배수입니다."
        valuation_review["numeric_claims"] = [
            {
                "fact_id": "valuation:current",
                "field_path": "fields.trailing_pe",
                "value": 20,
                "unit": "x",
                "semantic_type": "trailing_pe",
                "text_ref": "valuation_analysis.text",
                "usage": "현재 PBR 20배",
            }
        ]
        _, valuation_errors = validate_ai_review_output(session, packet, valuation)

    assert any("numeric_usage_semantic_mismatch" in error for error in supply_errors)
    assert any("numeric_usage_semantic_mismatch" in error for error in valuation_errors)


def test_market_numeric_semantics_distinguish_futures_close_and_return(
    monkeypatch,
    tmp_path: Path,
) -> None:
    _settings(monkeypatch, tmp_path)
    with Session(_engine()) as session:
        _seed(session)
        packet = build_ai_review_packet(session, RUN_DATE, "us")
        assert packet is not None
        context = packet["market_context"]
        context["fact_catalog"].append(
            {
                "fact_id": "market:test:futures",
                "fact_type": "night_futures",
                "as_of_date": RUN_DATE.isoformat(),
                "fields": {"value": 431.25, "change_pct": 0.67},
            }
        )
        context["numeric_registry"] = ai_review_service._numeric_registry(
            context["fact_catalog"]
        )
        output = _valid_output(packet)
        review = output["market_review"]
        review["facts_used"] = ["market:test:futures"]
        review["core_judgment"]["text"] = "야간선물 등락률은 431.25%입니다."
        review["numeric_claims"] = [
            {
                "fact_id": "market:test:futures",
                "field_path": "fields.value",
                "value": 431.25,
                "unit": "points",
                "semantic_type": "futures_close",
                "text_ref": "core_judgment.text",
                "usage": "야간선물 등락률은 431.25%",
            }
        ]
        _, errors = validate_ai_review_output(session, packet, output)

    assert any("numeric_usage_unit_mismatch" in error for error in errors)
    assert any("numeric_usage_semantic_mismatch" in error for error in errors)


def test_numeric_registry_distinguishes_all_night_futures_fields() -> None:
    registry = ai_review_service._numeric_registry(
        [
            {
                "fact_id": "market:test:futures-fields",
                "fact_type": "night_futures",
                "fields": {
                    "value": 431.25,
                    "change_value": -2.5,
                    "change_pct": -0.58,
                },
            }
        ]
    )

    assert {
        item["field_path"]: (item["semantic_type"], item["unit"])
        for item in registry
    } == {
        "fields.value": ("futures_close", "points"),
        "fields.change_value": ("futures_point_change", "points"),
        "fields.change_pct": ("futures_return_pct", "pct"),
    }


def test_chart_numeric_semantics_reject_indicator_and_price_label_swap(
    monkeypatch,
    tmp_path: Path,
) -> None:
    _settings(monkeypatch, tmp_path)
    with Session(_engine()) as session:
        _seed(session)
        packet = build_ai_review_packet(session, RUN_DATE, "us")
        assert packet is not None
        stock = packet["stocks"][0]
        stock["fact_catalog"].append(
            {
                "fact_id": "chart:daily",
                "fact_type": "chart_timeframe",
                "as_of_date": RUN_DATE.isoformat(),
                "fields": {
                    "currency": "USD",
                    "bollinger_upper": {"3_month": 101.0},
                    "rsi_14": 61.4,
                },
            }
        )
        stock["numeric_registry"] = ai_review_service._numeric_registry(
            stock["fact_catalog"]
        )
        output = _valid_output(packet)
        review = output["stock_reviews"][0]
        review["facts_used"] = ["chart:daily"]
        review["price_positioning"]["text"] = "RSI14는 101달러입니다."
        review["numeric_claims"] = [
            {
                "fact_id": "chart:daily",
                "field_path": "fields.bollinger_upper.3_month",
                "value": 101.0,
                "unit": "USD",
                "semantic_type": "bollinger_upper_price",
                "text_ref": "price_positioning.text",
                "usage": "RSI14는 101달러",
            }
        ]

        _, errors = validate_ai_review_output(session, packet, output)

    assert any("numeric_usage_semantic_mismatch" in error for error in errors)


def test_structure_numeric_semantics_reject_zone_and_atr_label_swaps(
    monkeypatch,
    tmp_path: Path,
) -> None:
    _settings(monkeypatch, tmp_path)
    with Session(_engine()) as session:
        _seed(session)
        packet = build_ai_review_packet(session, RUN_DATE, "us")
        assert packet is not None
        stock = packet["stocks"][0]
        stock["fact_catalog"].extend(
            [
                {
                    "fact_id": "chart:structure:atr:daily",
                    "fact_type": "chart_structure_atr",
                    "fields": {"currency": "USD", "value": 3.5},
                },
                {
                    "fact_id": "chart:structure:nearest_supports:1",
                    "fact_type": "chart_support_zone",
                    "fields": {"currency": "USD", "zone_low": 90.0},
                },
            ]
        )
        stock["numeric_registry"] = ai_review_service._numeric_registry(
            stock["fact_catalog"]
        )

        zone_output = _valid_output(packet)
        zone_review = zone_output["stock_reviews"][0]
        zone_review["facts_used"] = ["chart:structure:nearest_supports:1"]
        zone_review["price_positioning"]["text"] = "동적 저항구간은 90달러입니다."
        zone_review["numeric_claims"] = [
            {
                "fact_id": "chart:structure:nearest_supports:1",
                "field_path": "fields.zone_low",
                "value": 90.0,
                "unit": "USD",
                "semantic_type": "support_zone_price",
                "text_ref": "price_positioning.text",
                "usage": "동적 저항구간은 90달러",
            }
        ]
        _, zone_errors = validate_ai_review_output(session, packet, zone_output)

        atr_output = _valid_output(packet)
        atr_review = atr_output["stock_reviews"][0]
        atr_review["facts_used"] = ["chart:structure:atr:daily"]
        atr_review["price_positioning"]["text"] = "매출은 3.5달러입니다."
        atr_review["numeric_claims"] = [
            {
                "fact_id": "chart:structure:atr:daily",
                "field_path": "fields.value",
                "value": 3.5,
                "unit": "USD",
                "semantic_type": "chart_atr",
                "text_ref": "price_positioning.text",
                "usage": "매출은 3.5달러",
            }
        ]
        _, atr_errors = validate_ai_review_output(session, packet, atr_output)

    assert any("numeric_usage_semantic_mismatch" in error for error in zone_errors)
    assert any("numeric_usage_semantic_mismatch" in error for error in atr_errors)


def test_supply_horizon_registry_keeps_1d_5d_20d_semantics_distinct() -> None:
    registry = ai_review_service._numeric_registry(
        [
            {
                "fact_id": "positioning:horizons",
                "fact_type": "positioning",
                "fields": {
                    "foreign_net_buy_qty": 10,
                    "foreign_net_buy_qty_5": 50,
                    "foreign_net_buy_qty_20": -200,
                },
            }
        ]
    )

    assert {
        item["field_path"]: item["semantic_type"] for item in registry
    } == {
        "fields.foreign_net_buy_qty": "foreign_net_buy_qty",
        "fields.foreign_net_buy_qty_5": "foreign_net_buy_qty_5d",
        "fields.foreign_net_buy_qty_20": "foreign_net_buy_qty_20d",
    }


def test_krw_compact_formatter_is_limited_to_amount_semantics() -> None:
    registry = ai_review_service._numeric_registry(
        [
            {
                "fact_id": "price:current",
                "fact_type": "price",
                "fields": {"current_price": 1_593_000, "currency": "KRW"},
            },
            {
                "fact_id": "event:order",
                "fact_type": "contract_award",
                "fields": {
                    "contract_amount": {"value": 319_000_000_000, "currency": "KRW"}
                },
            },
        ]
    )
    price = next(item for item in registry if item["fact_id"] == "price:current")
    order = next(item for item in registry if item["fact_id"] == "event:order")

    assert "0억원" not in price["approved_display_variants"]
    assert "1,593,000원" in price["approved_display_variants"]
    assert "3,190억원" in order["approved_display_variants"]


def test_ratio_multiple_formatter_allows_backend_approved_rounding() -> None:
    registry = ai_review_service._numeric_registry(
        [
            {
                "fact_id": "chart:daily",
                "fact_type": "chart_timeframe",
                "fields": {"volume_ratio_20": 0.8053185211136238},
            }
        ]
    )

    assert "0.81배" in registry[0]["approved_display_variants"]


@pytest.mark.parametrize(
    ("semantic_type", "value", "unit", "expected"),
    [
        ("share_price", 868.390314, "USD", "$868.39"),
        ("share_price", 197_803, "KRW", "197,803원"),
        ("revenue", 41_456_000_000, "USD", "$41.46B"),
        ("revenue", 1_270_380_000_000, "TWD", "NT$1.27T"),
        ("revenue", 41_456_000_000, "KRW", "415억원"),
        ("oil_return_pct", 3.4285, "pct", "+3.4%"),
        ("real_yield_change_bp", -2.9999, "bp", "-3bp"),
        ("trailing_pe", 10.273, "x", "10.27배"),
        ("foreign_net_buy_qty_5d", -115_230, "shares", "115,230주"),
        ("support_zone_price", 914.929686, "USD", "$914.93"),
        ("risk_reward_ratio", 0.466, "x", "0.47배"),
    ],
)
def test_canonical_numeric_formatters(
    semantic_type: str,
    value: float,
    unit: str,
    expected: str,
) -> None:
    spec = semantic_spec(semantic_type)

    assert spec is not None
    assert canonical_display_value(spec, value, unit) == expected


def test_chart_and_supply_horizon_labels_are_structural_not_financial_values() -> None:
    text = "5일 외국인 순매수 100주와 20일 거래량비 0.81배, 3개월 상단선"
    occurrences = ai_review_service._prose_number_occurrences(text)

    assert [item[2] for item in occurrences] == ["100", "0.81"]
    assert ai_review_service._provenance_tokens(text) == {"100", "0.81"}


def test_market_index_names_and_yield_tenor_are_structural_numbers() -> None:
    text = (
        "S&P500 등락률 +0.22%, Russell 2000 등락률 +0.64%, "
        "미국 10년물 금리 -2bp"
    )

    assert ai_review_service._provenance_tokens(text) == {"0.22", "0.64", "-2"}


def test_quantitative_grounding_hard_fails_zero_claims_when_safe_numbers_exist(
    monkeypatch,
    tmp_path: Path,
) -> None:
    _settings(monkeypatch, tmp_path)
    with Session(_engine()) as session:
        _seed(session)
        packet = build_ai_review_packet(session, RUN_DATE, "us")
        assert packet is not None
        raw_output = _valid_output(packet)
        raw_output["stock_reviews"][0]["core_judgment"]["text"] = (
            "강한 실적과 프리미엄을 함께 확인해야 합니다."
        )
        raw_output["stock_reviews"][0]["price_positioning"]["text"] = (
            "가격 맥락은 기업의 질과 분리합니다."
        )
        raw_output["stock_reviews"][0]["numeric_claims"] = []
        output, errors = validate_ai_review_output(session, packet, raw_output)

    assert "PACKETUS:numeric_grounding_hard_fail" in errors
    assert output is not None
    report = ai_review_service.quantitative_grounding_report(packet, output)
    row = report["stocks"][0]
    assert report["status"] == "failed"
    assert "numeric_grounding_hard_fail:PACKETUS" in row["hard_failures"]
    assert "vague_quantitative_language" in row["flags"]
    assert "insufficient_quantitative_grounding:core" in row["flags"]
    assert "insufficient_quantitative_grounding:earnings" in row["flags"]
    assert "insufficient_quantitative_grounding:valuation" in row["flags"]


def test_sparse_stock_allows_zero_numeric_claims(monkeypatch, tmp_path: Path) -> None:
    _settings(monkeypatch, tmp_path)
    with Session(_engine()) as session:
        _seed(session)
        packet = build_ai_review_packet(session, RUN_DATE, "us")
        assert packet is not None
        output = _valid_output(packet)
        packet["stocks"][0]["numeric_registry"] = packet["stocks"][0][
            "numeric_registry"
        ][:3]
        output["stock_reviews"][0]["price_positioning"]["text"] = (
            "가격 자료가 부족해 판단을 보류합니다."
        )
        output["stock_reviews"][0]["numeric_claims"] = []
        _, errors = validate_ai_review_output(session, packet, output)

    assert "PACKETUS:numeric_grounding_hard_fail" not in errors


def test_state_price_grounding_requires_exact_fact_and_numeric_fields(
    monkeypatch,
    tmp_path: Path,
) -> None:
    _settings(monkeypatch, tmp_path)
    with Session(_engine()) as session:
        _seed(session)
        packet = build_ai_review_packet(session, RUN_DATE, "us")
        assert packet is not None
        packet["stocks"][0]["state_grounding_requirements"] = {
            "price": [
                {
                    "fact_id": "price:current",
                    "field_paths": ["fields.current_price"],
                    "reason": "current_price_structure",
                }
            ],
            "valuation": [],
        }
        valid = _valid_output(packet)
        _, valid_errors = validate_ai_review_output(session, packet, valid)

        invalid = _valid_output(packet)
        invalid["stock_reviews"][0]["price_positioning"]["fact_ids"] = []
        invalid["stock_reviews"][0]["numeric_claims"] = []
        _, invalid_errors = validate_ai_review_output(session, packet, invalid)

    assert not any("current_price_structure" in item for item in valid_errors)
    assert (
        "PACKETUS:current_price_structure_fact_missing:price:current"
        in invalid_errors
    )
    assert (
        "PACKETUS:current_price_structure_numeric_missing:"
        "price:current:fields.current_price"
        in invalid_errors
    )


def test_state_grounding_requires_current_price_when_available() -> None:
    requirements = ai_review_service._state_grounding_requirements(  # noqa: SLF001
        {
            "current": {
                "price_structure": {
                    "current_price": 211_000,
                    "active_support": {"available": False},
                    "active_resistance": {"available": False},
                    "risk_reward": {"available": False},
                }
            }
        },
        [
            {
                "fact_id": "price:current",
                "fact_type": "price",
                "fields": {"current_price": 211_000},
            }
        ],
    )

    assert requirements["price"] == [
        {
            "fact_id": "price:current",
            "field_paths": ["fields.current_price"],
            "reason": "current_price",
        }
    ]


def test_state_grounding_requires_peer_median_and_relative_value() -> None:
    requirements = ai_review_service._state_grounding_requirements(  # noqa: SLF001
        {
            "current": {
                "price_structure": {},
                "peer_valuation": {
                    "available": True,
                    "metrics": {
                        "trailing_pe": {"available": True},
                        "price_to_book": {"available": False},
                    },
                },
            }
        },
        [{"fact_id": "valuation:peer", "fact_type": "peer_valuation"}],
    )

    assert requirements["valuation"] == [
        {
            "fact_id": "valuation:peer",
            "field_paths": [
                "fields.pe_median",
                "fields.company_pe_vs_median_pct",
            ],
            "reason": "sufficient_peer_valuation",
        }
    ]


def test_historical_percentile_is_not_an_overvaluation_percentage(
    monkeypatch,
    tmp_path: Path,
) -> None:
    _settings(monkeypatch, tmp_path)
    with Session(_engine()) as session:
        _seed(session)
        packet = build_ai_review_packet(session, RUN_DATE, "us")
        assert packet is not None
        output = _valid_output(packet)
        output["stock_reviews"][0]["valuation_analysis"]["text"] = (
            "현재 배수는 92.8% 고평가 상태입니다."
        )
        _, errors = validate_ai_review_output(session, packet, output)

    assert "PACKETUS:historical_percentile_misrepresented" in errors


def test_numeric_fact_reference_is_bound_to_canonical_value_and_claim(
    monkeypatch,
    tmp_path: Path,
) -> None:
    _settings(monkeypatch, tmp_path)
    with Session(_engine()) as session:
        _seed(session)
        packet = build_ai_review_packet(session, RUN_DATE, "us")
        assert packet is not None
        draft = _valid_output(packet)
        review = draft["stock_reviews"][0]
        review["price_positioning"]["text"] = (
            "{{numeric:price_now}}은 기업의 질과 별도인 가격 맥락입니다."
        )
        review["numeric_claims"] = []
        review["numeric_fact_refs"] = [
            {
                "ref_id": "price_now",
                "fact_id": "price:current",
                "field_path": "fields.current_price",
                "text_ref": "price_positioning.text",
            }
        ]

        output, errors = validate_ai_review_output(session, packet, draft)

    assert errors == []
    assert output is not None
    assert output.stock_reviews[0].price_positioning.text.startswith("현재가 $100")
    assert output.stock_reviews[0].numeric_claims[0].model_dump() == {
        "fact_id": "price:current",
        "field_path": "fields.current_price",
        "value": 100.0,
        "unit": "USD",
        "semantic_type": "share_price",
        "text_ref": "price_positioning.text",
        "usage": "현재가 $100",
    }
    assert "{{numeric:price_now}}" in draft["stock_reviews"][0]["price_positioning"]["text"]


def test_numeric_fact_reference_missing_source_fails_closed(
    monkeypatch,
    tmp_path: Path,
) -> None:
    _settings(monkeypatch, tmp_path)
    with Session(_engine()) as session:
        _seed(session)
        packet = build_ai_review_packet(session, RUN_DATE, "us")
        assert packet is not None
        draft = _valid_output(packet)
        review = draft["stock_reviews"][0]
        review["price_positioning"]["text"] = "{{numeric:missing}}"
        review["numeric_claims"] = []
        review["numeric_fact_refs"] = [
            {
                "ref_id": "missing",
                "fact_id": "price:missing",
                "field_path": "fields.current_price",
                "text_ref": "price_positioning.text",
            }
        ]

        output, errors = validate_ai_review_output(session, packet, draft)

    assert output is None
    assert errors == [
        "PACKETUS:numeric_fact_ref_source_not_found:"
        "missing:price:missing:fields.current_price"
    ]


def test_malformed_numeric_placeholder_fails_closed(
    monkeypatch,
    tmp_path: Path,
) -> None:
    _settings(monkeypatch, tmp_path)
    with Session(_engine()) as session:
        _seed(session)
        packet = build_ai_review_packet(session, RUN_DATE, "us")
        assert packet is not None
        draft = _valid_output(packet)
        draft["stock_reviews"][0]["price_positioning"]["text"] = (
            "{{numeric:123 invalid}} 가격 맥락입니다."
        )

        output, errors = validate_ai_review_output(session, packet, draft)

    assert output is None
    assert errors == [
        "PACKETUS:numeric_fact_ref_unresolved_placeholder:"
        "{{numeric:123 invalid}}"
    ]


def test_modeled_forward_binding_uses_source_aware_label(
    monkeypatch,
    tmp_path: Path,
) -> None:
    _settings(monkeypatch, tmp_path)
    with Session(_engine()) as session:
        _seed(session)
        packet = build_ai_review_packet(session, RUN_DATE, "us")
        assert packet is not None
        draft = _valid_output(packet)
        review = draft["stock_reviews"][0]
        review["facts_used"].append("valuation:current")
        review["valuation_analysis"]["text"] = (
            "{{numeric:modeled_fper}}는 내부 정상화 가정의 결과입니다."
        )
        review["numeric_fact_refs"] = [
            {
                "ref_id": "modeled_fper",
                "fact_id": "valuation:current",
                "field_path": "fields.forward_pe",
                "text_ref": "valuation_analysis.text",
            }
        ]

        output, errors = validate_ai_review_output(session, packet, draft)

    assert errors == []
    assert output is not None
    assert output.stock_reviews[0].valuation_analysis.text.startswith(
        "내부 추정 fPER 18배"
    )
    assert output.stock_reviews[0].numeric_claims[-1].usage == "내부 추정 fPER 18배"


def test_numeric_token_span_excludes_trailing_sentence_comma(
    monkeypatch,
    tmp_path: Path,
) -> None:
    _settings(monkeypatch, tmp_path)
    with Session(_engine()) as session:
        _seed(session)
        packet = build_ai_review_packet(session, RUN_DATE, "us")
        assert packet is not None
        output = _valid_output(packet)
        review = output["stock_reviews"][0]
        review["facts_used"].append("earnings:2026-06-30")
        review["business_earnings"] = {
            "text": "매출 $500, 매출 성장이 확인됐습니다.",
            "fact_ids": ["earnings:2026-06-30"],
        }
        review["numeric_claims"].append(
            {
                "fact_id": "earnings:2026-06-30",
                "field_path": "fields.revenue.value",
                "value": 500,
                "unit": "USD",
                "semantic_type": "revenue",
                "text_ref": "business_earnings.text",
                "usage": "매출 $500",
            }
        )

        _, errors = validate_ai_review_output(session, packet, output)

    assert not any("business_earnings.text:500" in item for item in errors)


def test_hut_forward_eps_without_reference_remains_rejected(
    monkeypatch,
    tmp_path: Path,
) -> None:
    _settings(monkeypatch, tmp_path)
    with Session(_engine()) as session:
        _seed(session)
        packet = build_ai_review_packet(session, RUN_DATE, "us")
        assert packet is not None
        output = _valid_output(packet)
        review = output["stock_reviews"][0]
        review["valuation_analysis"]["text"] = (
            "내부 추정 fPER는 높고 추정 EPS $0.59는 계약 수익성 확인이 필요합니다."
        )

        _, errors = validate_ai_review_output(session, packet, output)

    assert any(
        "numbers_without_provenance:valuation_analysis.text:0.59" in item
        for item in errors
    )


def test_earnings_fact_uses_financial_currency_not_adr_price_currency(
    monkeypatch,
    tmp_path: Path,
) -> None:
    _settings(monkeypatch, tmp_path)
    with Session(_engine()) as session:
        _seed(session)
        assessment = session.exec(
            select(ThesisAssessment).where(
                ThesisAssessment.ticker == "PACKETUS",
                ThesisAssessment.assessment_date == RUN_DATE,
            )
        ).one()
        snapshot = json.loads(assessment.valuation_snapshot)
        snapshot["currency"] = "USD"
        snapshot["financial_currency"] = "TWD"
        snapshot["latest_revenue"] = 1_270_380_000_000
        assessment.valuation_snapshot = json.dumps(snapshot)
        session.add(assessment)
        session.commit()
        packet = build_ai_review_packet(session, RUN_DATE, "us")
        assert packet is not None

    stock = packet["stocks"][0]
    earnings = next(
        item for item in stock["fact_catalog"] if item["fact_type"] == "earnings"
    )
    revenue = next(
        item
        for item in stock["numeric_registry"]
        if item["fact_id"] == earnings["fact_id"]
        and item["field_path"] == "fields.revenue.value"
    )
    price = next(
        item
        for item in stock["numeric_registry"]
        if item["fact_id"] == "price:current"
        and item["field_path"] == "fields.current_price"
    )
    assert earnings["fields"]["revenue"]["currency"] == "TWD"
    assert revenue["unit"] == "TWD"
    assert revenue["prose_allowed"] is True
    assert "NT$1.27T" in revenue["approved_display_variants"]
    assert price["unit"] == "USD"


def _packet_with_earnings_currency(
    monkeypatch,
    tmp_path: Path,
    *,
    price_currency: str,
    financial_currency: str | None,
    revenue: float = 1_270_380_000_000,
    operating_income: float = 766_600_000_000,
) -> dict[str, object]:
    _settings(monkeypatch, tmp_path)
    with Session(_engine()) as session:
        _seed(session)
        assessment = session.exec(
            select(ThesisAssessment).where(
                ThesisAssessment.ticker == "PACKETUS",
                ThesisAssessment.assessment_date == RUN_DATE,
            )
        ).one()
        valuation = json.loads(assessment.valuation_snapshot)
        valuation.update(
            {
                "currency": price_currency,
                "financial_currency": financial_currency,
                "latest_revenue": revenue,
                "latest_operating_income": operating_income,
                "latest_operating_margin": 60.34,
                "latest_revenue_qoq": 12.5,
                "latest_revenue_yoy": 40.1,
                "latest_operating_income_qoq": 8.2,
                "latest_operating_income_yoy": 55.6,
            }
        )
        price_context = json.loads(assessment.price_context)
        price_context["decision"]["currency"] = price_currency
        assessment.valuation_snapshot = json.dumps(valuation)
        assessment.price_context = json.dumps(price_context)
        session.add(assessment)
        session.commit()
        packet = build_ai_review_packet(session, RUN_DATE, "us")
        assert packet is not None
        return packet


def _earnings_registry(
    packet: dict[str, object],
) -> tuple[dict[str, object], dict[str, dict[str, object]]]:
    stock = packet["stocks"][0]
    earnings = next(
        item for item in stock["fact_catalog"] if item["fact_type"] == "earnings"
    )
    registry = {
        item["field_path"]: item
        for item in stock["numeric_registry"]
        if item["fact_id"] == earnings["fact_id"]
    }
    return earnings, registry


@pytest.mark.parametrize("price_currency", ["USD", "KRW"])
@pytest.mark.parametrize("financial_currency", [None, "", "   "])
def test_missing_financial_currency_never_inherits_price_currency(
    monkeypatch,
    tmp_path: Path,
    price_currency: str,
    financial_currency: str | None,
) -> None:
    packet = _packet_with_earnings_currency(
        monkeypatch,
        tmp_path,
        price_currency=price_currency,
        financial_currency=financial_currency,
    )
    earnings, registry = _earnings_registry(packet)
    price_entry = next(
        item
        for item in packet["stocks"][0]["numeric_registry"]
        if item["fact_id"] == "price:current"
        and item["field_path"] == "fields.current_price"
    )

    for field in ("revenue", "operating_income"):
        source = earnings["fields"][field]
        entry = registry[f"fields.{field}.value"]
        assert source["currency"] == "unknown"
        assert entry["unit"] == "unknown"
        assert entry["registered"] is True
        assert entry["prose_allowed"] is False
        assert entry["canonical_display_value"] is None
        assert entry["approved_display_variants"] == []
        rendered = json.dumps(entry, ensure_ascii=False)
        assert "NT$" not in rendered
        assert "$" not in rendered
        assert "원" not in rendered
    assert price_entry["unit"] == price_currency
    assert registry["fields.operating_margin_pct"]["prose_allowed"] is True
    assert registry["fields.revenue_qoq_pct"]["prose_allowed"] is True
    assert registry["fields.revenue_yoy_pct"]["prose_allowed"] is True
    assert registry["fields.operating_income_qoq_pct"]["prose_allowed"] is True
    assert registry["fields.operating_income_yoy_pct"]["prose_allowed"] is True


def test_unsupported_financial_currency_is_preserved_and_prose_denied(
    monkeypatch,
    tmp_path: Path,
) -> None:
    packet = _packet_with_earnings_currency(
        monkeypatch,
        tmp_path,
        price_currency="USD",
        financial_currency="GBP",
    )
    earnings, registry = _earnings_registry(packet)
    revenue = registry["fields.revenue.value"]

    assert earnings["fields"]["revenue"]["currency"] == "GBP"
    assert revenue["unit"] == "GBP"
    assert revenue["registered"] is True
    assert revenue["prose_allowed"] is False
    assert revenue["canonical_display_value"] is None
    assert revenue["approved_display_variants"] == []


@pytest.mark.parametrize(
    ("financial_currency", "revenue", "expected"),
    [
        ("USD", 41_456_000_000, "$41.46B"),
        ("KRW", 41_456_000_000, "415억원"),
        ("TWD", 1_270_380_000_000, "NT$1.27T"),
    ],
)
def test_verified_financial_currency_keeps_canonical_formatter(
    monkeypatch,
    tmp_path: Path,
    financial_currency: str,
    revenue: float,
    expected: str,
) -> None:
    packet = _packet_with_earnings_currency(
        monkeypatch,
        tmp_path,
        price_currency="USD",
        financial_currency=financial_currency,
        revenue=revenue,
    )
    earnings, registry = _earnings_registry(packet)
    revenue_entry = registry["fields.revenue.value"]
    price_entry = next(
        item
        for item in packet["stocks"][0]["numeric_registry"]
        if item["fact_id"] == "price:current"
        and item["field_path"] == "fields.current_price"
    )

    assert earnings["fields"]["revenue"]["currency"] == financial_currency
    assert revenue_entry["unit"] == financial_currency
    assert revenue_entry["prose_allowed"] is True
    assert revenue_entry["canonical_display_value"] == expected
    assert price_entry["unit"] == "USD"


def test_twd_financial_amounts_remain_separate_from_usd_security_price(
    monkeypatch,
    tmp_path: Path,
) -> None:
    packet = _packet_with_earnings_currency(
        monkeypatch,
        tmp_path,
        price_currency="USD",
        financial_currency="TWD",
    )
    _earnings, registry = _earnings_registry(packet)

    assert registry["fields.revenue.value"]["canonical_display_value"] == "NT$1.27T"
    assert (
        registry["fields.operating_income.value"]["canonical_display_value"]
        == "NT$766.6B"
    )


def test_unknown_currency_monetary_binding_and_raw_prose_fail_closed(
    monkeypatch,
    tmp_path: Path,
) -> None:
    packet = _packet_with_earnings_currency(
        monkeypatch,
        tmp_path,
        price_currency="USD",
        financial_currency=None,
    )
    earnings, _registry = _earnings_registry(packet)
    draft = _valid_output(packet)
    review = draft["stock_reviews"][0]
    review["facts_used"].append(earnings["fact_id"])
    review["business_earnings"] = {
        "text": "{{numeric:revenue}}의 재무 통화 basis를 확인해야 합니다.",
        "fact_ids": [earnings["fact_id"]],
    }
    review["numeric_fact_refs"] = [
        {
            "ref_id": "revenue",
            "fact_id": earnings["fact_id"],
            "field_path": "fields.revenue.value",
            "text_ref": "business_earnings.text",
        }
    ]

    with Session(_engine()) as validation_session:
        _seed(validation_session)
        bound_output, binding_errors = validate_ai_review_output(
            validation_session, packet, draft
        )

        raw_draft = _valid_output(packet)
        raw_review = raw_draft["stock_reviews"][0]
        raw_review["facts_used"].append(earnings["fact_id"])
        raw_review["business_earnings"] = {
            "text": (
                "매출 $1,270,380,000,000은 재무 통화 basis가 "
                "확인되지 않았습니다."
            ),
            "fact_ids": [earnings["fact_id"]],
        }
        _raw_output, raw_errors = validate_ai_review_output(
            validation_session, packet, raw_draft
        )

    assert bound_output is None
    assert binding_errors == [
        "PACKETUS:numeric_fact_ref_semantic_not_supported:"
        f"revenue:{earnings['fact_id']}:fields.revenue.value"
    ]
    assert any(
        "numbers_without_provenance:business_earnings.text:1.27038e+12" in error
        for error in raw_errors
    )


def test_unknown_currency_can_be_described_without_raw_monetary_number(
    monkeypatch,
    tmp_path: Path,
) -> None:
    packet = _packet_with_earnings_currency(
        monkeypatch,
        tmp_path,
        price_currency="USD",
        financial_currency=None,
    )
    earnings, _registry = _earnings_registry(packet)
    draft = _valid_output(packet)
    review = draft["stock_reviews"][0]
    review["facts_used"].append(earnings["fact_id"])
    review["business_earnings"] = {
        "text": (
            "매출 금액은 확인됐지만 재무 통화 basis가 확인되지 않아 "
            "정량 표기는 보류합니다."
        ),
        "fact_ids": [earnings["fact_id"]],
    }

    with Session(_engine()) as validation_session:
        _seed(validation_session)
        output, errors = validate_ai_review_output(validation_session, packet, draft)

    assert errors == []
    assert output is not None


def test_critical_financial_outlier_taints_packet_registry_and_raw_prose(
    monkeypatch,
    tmp_path: Path,
) -> None:
    _settings(monkeypatch, tmp_path)
    with Session(_engine()) as session:
        _seed(session)
        assessment = session.exec(
            select(ThesisAssessment).where(
                ThesisAssessment.ticker == "PACKETUS",
                ThesisAssessment.assessment_date == RUN_DATE,
            )
        ).one()
        valuation = json.loads(assessment.valuation_snapshot)
        valuation.update(
            {
                "earnings_context_source": "preliminary_earnings",
                "earnings_context_is_preliminary": True,
                "ttm_contains_preliminary": True,
                "latest_revenue": 79_318_700_000_000,
                "latest_operating_income": 60_500_000_000_000,
                "latest_operating_margin": 76.3,
                "latest_revenue_yoy": 256.8,
                "latest_operating_income_yoy": 557.2,
                "ttm_eps": 13.89,
                "trailing_pe": 7.2,
                "forward_eps": 6.1,
                "forward_pe": 16.38,
                "forward_pe_source": "modeled_forward",
                "price_to_book": 3.0,
                "historical_comparability": "normal",
                "historical_pe_statistics": {
                    "current_value": 7.2,
                    "current_percentile": 12.0,
                },
                "historical_pb_statistics": {"current_percentile": 88.0},
                "data_coverage": {
                    "reason_codes": ["preliminary_profitability_outlier"]
                },
            }
        )
        valuation["earnings_quarter_series"][-1].update(
            {
                "source": "preliminary_earnings",
                "filing": "2026-08-02",
                "revenue": 79_318_700_000_000,
                "operating_income": 60_500_000_000_000,
            }
        )
        session.add(
            FinancialSnapshot(
                ticker="PACKETUS",
                period="2026-06-30 preliminary",
                snapshot_type="preliminary_earnings",
                financial_period_end=date(2026, 6, 30),
                financials_as_of=date(2026, 6, 30),
                filing_date=date(2026, 8, 2),
                reported_date=date(2026, 8, 2),
                provider="fixture_provider",
                source="fixture_preliminary",
                currency="USD",
                revenue=79_318_700_000_000,
                operating_income=60_500_000_000_000,
                financial_soft_outliers=json.dumps(
                    [
                        "net_income_exceeds_revenue",
                        "unusually_high_or_low_operating_margin",
                    ]
                ),
            )
        )
        assessment.valuation_snapshot = json.dumps(valuation)
        session.add(assessment)
        session.commit()
        packet = build_ai_review_packet(session, RUN_DATE, "us")
        assert packet is not None
        stock = packet["stocks"][0]
        registry = {
            (item["fact_id"], item["field_path"]): item
            for item in stock["numeric_registry"]
        }
        earnings_fact = next(
            item for item in stock["fact_catalog"] if item["fact_type"] == "earnings"
        )
        quality_fact = next(
            item
            for item in stock["fact_catalog"]
            if item["fact_type"] == "financial_quality"
        )
        assert quality_fact["prose_eligible"] is True
        assert quality_fact["fields"]["state"] == "denied"
        assert "preliminary_profitability_outlier" in quality_fact["fields"][
            "reason_codes"
        ]
        output = _valid_output(packet)
        review = output["stock_reviews"][0]
        review["facts_used"].append(earnings_fact["fact_id"])
        review["business_earnings"] = {
            "text": "매출 79318700000000원으로 강한 이익 사이클입니다.",
            "fact_ids": [earnings_fact["fact_id"]],
        }

        _, errors = validate_ai_review_output(session, packet, output)

    for fact_id, path in (
        (earnings_fact["fact_id"], "fields.revenue.value"),
        (earnings_fact["fact_id"], "fields.operating_margin_pct"),
            ("valuation:current", "fields.trailing_pe"),
            (
                "valuation:current",
                "fields.historical_pe_statistics.current_percentile",
        ),
    ):
        entry = registry[(fact_id, path)]
        assert entry["financial_quality_state"] == "denied"
        assert entry["prose_allowed"] is False
        assert entry["canonical_display_value"] is None
        assert entry["approved_display_variants"] == []
    assert registry[("valuation:current", "fields.forward_pe")][
        "financial_quality_state"
    ] == "caution_usable"
    assert registry[("valuation:current", "fields.forward_pe")][
        "prose_allowed"
    ] is True
    assert registry[("valuation:current", "fields.price_to_book")][
        "prose_allowed"
    ] is True
    assert any("financial_quality_denied_fact_used" in error for error in errors)
    assert any("numbers_without_provenance" in error for error in errors)


def test_critical_financial_outlier_allows_number_free_specific_unknown(
    monkeypatch,
    tmp_path: Path,
) -> None:
    _settings(monkeypatch, tmp_path)
    with Session(_engine()) as session:
        _seed(session)
        assessment = session.exec(
            select(ThesisAssessment).where(
                ThesisAssessment.ticker == "PACKETUS",
                ThesisAssessment.assessment_date == RUN_DATE,
            )
        ).one()
        valuation = json.loads(assessment.valuation_snapshot)
        valuation.update(
            {
                "earnings_context_source": "preliminary_earnings",
                "earnings_context_is_preliminary": True,
                "latest_revenue": 79_318_700_000_000,
                "data_coverage": {
                    "reason_codes": ["preliminary_profitability_outlier"]
                },
            }
        )
        assessment.valuation_snapshot = json.dumps(valuation)
        session.add(assessment)
        session.commit()
        packet = build_ai_review_packet(session, RUN_DATE, "us")
        assert packet is not None
        output = _valid_output(packet)
        review = output["stock_reviews"][0]
        quality_fact = next(
            item["fact_id"]
            for item in packet["stocks"][0]["fact_catalog"]
            if item["fact_type"] == "financial_quality"
        )
        book_fact = next(
            item["fact_id"]
            for item in packet["stocks"][0]["fact_catalog"]
            if item["fact_id"] == "valuation:book"
        )
        review["facts_used"].extend([quality_fact, book_fact])
        review["business_earnings"] = {
            "text": (
                "잠정실적의 수익성 관계에 검증 경고가 있어 정량 해석을 "
                "보류하고 정식 재무의 매출·영업이익·현금흐름을 확인합니다."
            ),
            "fact_ids": [quality_fact],
        }
        review["valuation_analysis"]["fact_ids"] = [book_fact]

        _, errors = validate_ai_review_output(session, packet, output)

    assert not any("financial_quality_denied_fact_used" in error for error in errors)
    assert not any("business_earnings.text" in error for error in errors)


def test_mixed_valuation_fact_cannot_bypass_field_level_interpretation_fence(
    monkeypatch,
    tmp_path: Path,
) -> None:
    _settings(monkeypatch, tmp_path)
    with Session(_engine()) as session:
        _seed(session)
        packet = build_ai_review_packet(session, RUN_DATE, "us")
        assert packet is not None
        stock = packet["stocks"][0]
        aggregate = next(
            item for item in stock["fact_catalog"] if item["fact_id"] == "valuation:current"
        )
        aggregate["interpretation_eligible"] = False
        aggregate["interpretation_denial_reason"] = (
            "mixed_financial_lineage_requires_homogeneous_fact"
        )
        trailing = next(
            item
            for item in stock["fact_catalog"]
            if item["fact_id"] == "valuation:trailing_earnings"
        )
        trailing["prose_eligible"] = False
        trailing["interpretation_eligible"] = False
        book = next(
            item for item in stock["fact_catalog"] if item["fact_id"] == "valuation:book"
        )
        assert book["interpretation_eligible"] is True

        aggregate_output = _valid_output(packet)
        aggregate_review = AIDailyReviewOutput.model_validate(
            aggregate_output
        ).stock_reviews[0]
        aggregate_review.valuation_analysis.text = (
            "이익 배수가 높아 시장 기대가 매우 높습니다."
        )
        aggregate_errors = ai_review_service._validate_stock_review(
            aggregate_review, stock
        )

        denied_output = _valid_output(packet)
        denied_review = AIDailyReviewOutput.model_validate(denied_output).stock_reviews[0]
        denied_review.facts_used.append(trailing["fact_id"])
        denied_review.valuation_analysis.fact_ids = [trailing["fact_id"]]
        denied_review.valuation_analysis.text = (
            "낮은 이익 배수는 저평가를 뜻합니다."
        )
        denied_errors = ai_review_service._validate_stock_review(denied_review, stock)

        pbr = next(
            item
            for item in stock["numeric_registry"]
            if item["fact_id"] == "valuation:current"
            and item["field_path"] == "fields.price_to_book"
        )
        usage = f"{pbr['canonical_label']} {pbr['canonical_display_value']}"
        allowed_output = _valid_output(packet)
        allowed_data = allowed_output["stock_reviews"][0]
        allowed_data["facts_used"].extend([aggregate["fact_id"], book["fact_id"]])
        allowed_data["valuation_analysis"]["fact_ids"] = [book["fact_id"]]
        allowed_data["valuation_analysis"]["text"] = (
            f"{usage}는 확인된 장부가 배수입니다."
        )
        allowed_data["numeric_claims"].append(
            {
                "fact_id": pbr["fact_id"],
                "field_path": pbr["field_path"],
                "value": pbr["value"],
                "unit": pbr["unit"],
                "semantic_type": pbr["semantic_type"],
                "text_ref": "valuation_analysis.text",
                "usage": usage,
            }
        )
        allowed_review = AIDailyReviewOutput.model_validate(
            allowed_output
        ).stock_reviews[0]
        allowed_errors = ai_review_service._validate_stock_review(allowed_review, stock)

    assert any("financial_quality_denied_fact_used:valuation:current" in item for item in aggregate_errors)
    assert any(
        "financial_quality_denied_fact_used:valuation:trailing_earnings" in item
        for item in denied_errors
    )
    assert not any("financial_quality_denied_fact_used" in item for item in allowed_errors)


def test_market_hard_fails_zero_claims_with_four_eligible_anchors(
    monkeypatch,
    tmp_path: Path,
) -> None:
    _settings(monkeypatch, tmp_path)
    with Session(_engine()) as session:
        _seed(session)
        packet = build_ai_review_packet(session, RUN_DATE, "us")
        assert packet is not None
        packet["market_context"]["numeric_registry"] = [
            {
                "fact_id": f"market:test:{index}",
                "field_path": "fields.return_pct",
                "value": float(index),
                "unit": "pct",
                "semantic_type": "index_return_pct",
                "registered": True,
                "prose_allowed": True,
                "scope": "market",
            }
            for index in range(4)
        ]
        output = _valid_output(packet)
        output["market_review"]["numeric_claims"] = []
        _, errors = validate_ai_review_output(session, packet, output)

    assert "market_review:numeric_grounding_hard_fail" in errors


def test_fresh_night_futures_are_required_and_grounded_end_to_end(
    monkeypatch,
    tmp_path: Path,
) -> None:
    _settings(monkeypatch, tmp_path)
    with Session(_engine()) as session:
        _seed(session)
        _set_fresh_night_futures(
            session,
            "KRX_KOSPI200_NIGHT_FUT",
            "KRX_KOSDAQ150_NIGHT_FUT",
        )
        packet = build_ai_review_packet(session, RUN_DATE, "us")
        assert packet is not None
        context = packet["market_context"]
        required = context["required_market_fact_ids"]
        assert required == [
            "market:night_futures:1",
            "market:night_futures:2",
        ]
        assert all(
            item["market_packet_included"]
            and item["ai_fact_catalog_included"]
            and item["freshness"] == "fresh"
            for item in context["night_futures_audit"]["products"]
        )

        output = _valid_output(packet)
        market_review = output["market_review"]
        close_entries = [
            next(
                item
                for item in context["numeric_registry"]
                if item["fact_id"] == fact_id
                and item["semantic_type"] == "futures_close"
            )
            for fact_id in required
        ]
        usages = [
            f"{label} 야간선물 종가 {entry['approved_display_variants'][2]}"
            for label, entry in zip(("KOSPI200", "KOSDAQ150"), close_entries)
        ]
        market_review["facts_used"] = required
        market_review["core_judgment"] = {
            "text": "두 계약의 방향 차이는 한국 개장 전 가격 맥락으로만 봅니다.",
            "fact_ids": required,
        }
        market_review["important_changes"] = [
            {
                "text": f"{usages[0]}, {usages[1]}로 확인됐습니다.",
                "fact_ids": required,
            }
        ]
        market_review["market_context"] = {
            "text": "야간선물은 기업 투자 논리 변화가 아니라 개장 전 가격 신호입니다.",
            "fact_ids": required,
        }
        market_review["market_assumptions"]["fact_ids"] = required
        market_review["numeric_claims"] = [
            {
                "fact_id": entry["fact_id"],
                "field_path": entry["field_path"],
                "value": entry["value"],
                "unit": entry["unit"],
                "semantic_type": entry["semantic_type"],
                "text_ref": "important_changes[0].text",
                "usage": usage,
            }
            for entry, usage in zip(close_entries, usages)
        ]
        _, errors = validate_ai_review_output(session, packet, output)

    assert errors == []


def test_partial_or_missing_night_futures_do_not_block_market_packet(
    monkeypatch,
    tmp_path: Path,
) -> None:
    _settings(monkeypatch, tmp_path)
    with Session(_engine()) as session:
        _seed(session)
        _set_fresh_night_futures(session, "KRX_KOSPI200_NIGHT_FUT")
        partial = build_ai_review_packet(session, RUN_DATE, "us")
        assert partial is not None
        assert partial["market_context"]["required_market_fact_ids"] == [
            "market:night_futures:1"
        ]
        assert any(
            "KOSDAQ150" in item
            for item in partial["market_context"]["night_futures_cautions"]
        )

        _set_fresh_night_futures(session)
        missing = build_ai_review_packet(session, RUN_DATE, "us")
        assert missing is not None
        assert missing["market_context"]["required_market_fact_ids"] == []
        assert missing["ready_for_ai"] is True
        assert any(
            "최신 완료 세션 데이터를 확인하지 못해" in item
            for item in missing["market_context"]["night_futures_cautions"]
        )


def test_market_transmission_requires_exact_group_fact_and_prose_grounding(
    monkeypatch,
    tmp_path: Path,
) -> None:
    _settings(monkeypatch, tmp_path)
    with Session(_engine()) as session:
        _seed(session)
        packet = build_ai_review_packet(session, RUN_DATE, "us")
        assert packet is not None
        context = packet["market_context"]
        fact = {
            "fact_id": "market:relative:SOXX:SPY",
            "fact_type": "market_sector_relative",
            "as_of_date": RUN_DATE.isoformat(),
            "fields": {
                "subject": "SOXX",
                "subject_label": "반도체",
                "benchmark": "SPY",
                "benchmark_label": "S&P500",
                "relative_return_pct": 1.9,
                "source_fact_ids": ["market:sector:SOXX", "market:index:SPY"],
            },
        }
        context["fact_catalog"] = [fact]
        context["numeric_registry"] = ai_review_service._numeric_registry([fact])
        context["key_change_fact_ids"] = [fact["fact_id"]]
        context["portfolio_exposure_groups"] = [
            {"group_key": "memory", "label": "메모리", "tickers": ["PACKETUS"]}
        ]
        context["transmission_candidates"] = [
            {
                "portfolio_group": "memory",
                "market_fact_id": fact["fact_id"],
                "tickers": ["PACKETUS"],
                "channels": ["risk_appetite"],
            }
        ]
        output = _valid_output(packet)
        market_review = output["market_review"]
        market_review["facts_used"] = [fact["fact_id"]]
        market_review["important_changes"] = [
            {
                "text": "S&P500 대비 반도체 상대수익률 1.9%는 업종 선택적 강세를 보여줍니다.",
                "fact_ids": [fact["fact_id"]],
            }
        ]
        market_review["portfolio_transmission"] = [
            {
                "portfolio_group": "memory",
                "text": "메모리 가격환경에는 우호적이지만 주문과 마진 확인은 별개입니다.",
                "fact_ids": [fact["fact_id"]],
            }
        ]
        market_review["next_checks"] = [
            {
                "text": "반도체 상대강도가 다음 세션에도 이어지는지 확인합니다.",
                "fact_ids": [fact["fact_id"]],
            }
        ]
        market_review["numeric_claims"] = [
            {
                "fact_id": fact["fact_id"],
                "field_path": "fields.relative_return_pct",
                "value": 1.9,
                "unit": "pct",
                "semantic_type": "sector_relative_return_pct",
                "text_ref": "important_changes[0].text",
                "usage": "S&P500 대비 반도체 상대수익률 1.9%",
            }
        ]

        validated, errors = validate_ai_review_output(session, packet, output)
        assert validated is not None
        assert errors == []

        output["market_review"]["portfolio_transmission"][0][
            "portfolio_group"
        ] = "insurance"
        _, errors = validate_ai_review_output(session, packet, output)

    assert "market_review:portfolio_group_not_found:insurance" in errors
    assert any(
        error.startswith("market_review:portfolio_transmission_fact_mismatch:insurance")
        for error in errors
    )


def test_market_next_check_requires_a_specific_backend_fact(
    monkeypatch,
    tmp_path: Path,
) -> None:
    _settings(monkeypatch, tmp_path)
    with Session(_engine()) as session:
        _seed(session)
        packet = build_ai_review_packet(session, RUN_DATE, "us")
        assert packet is not None
        output = _valid_output(packet)
        output["market_review"]["next_checks"] = [
            {"text": "향후 시장 상황을 확인합니다.", "fact_ids": []}
        ]
        _, errors = validate_ai_review_output(session, packet, output)

    assert "market_review:next_check_without_fact:0" in errors
    assert "market_review:generic_next_check:0" in errors


def test_market_numeric_claim_cannot_reuse_stock_flow_semantic_scope(
    monkeypatch,
    tmp_path: Path,
) -> None:
    _settings(monkeypatch, tmp_path)
    with Session(_engine()) as session:
        _seed(session)
        packet = build_ai_review_packet(session, RUN_DATE, "us")
        assert packet is not None
        context = packet["market_context"]
        context["fact_catalog"] = [
            {
                "fact_id": "market:test:stock-flow",
                "fact_type": "positioning",
                "as_of_date": RUN_DATE.isoformat(),
                "fields": {"foreign_net_buy_qty": 100},
            }
        ]
        context["numeric_registry"] = ai_review_service._numeric_registry(
            context["fact_catalog"]
        )
        assert context["numeric_registry"][0]["semantic_type"] == "foreign_net_buy_qty"
        assert context["numeric_registry"][0]["scope"] == "stock"
        output = _valid_output(packet)
        review = output["market_review"]
        review["facts_used"] = ["market:test:stock-flow"]
        review["core_judgment"] = {
            "text": "외국인 순매수 100주를 시장 전체 수급처럼 사용했습니다.",
            "fact_ids": ["market:test:stock-flow"],
        }
        review["numeric_claims"] = [
            {
                "fact_id": "market:test:stock-flow",
                "field_path": "fields.foreign_net_buy_qty",
                "value": 100,
                "unit": "shares",
                "semantic_type": "foreign_net_buy_qty",
                "text_ref": "core_judgment.text",
                "usage": "외국인 순매수 100주",
            }
        ]
        _, errors = validate_ai_review_output(session, packet, output)

    assert any("numeric_semantic_scope_mismatch" in error for error in errors)


def test_market_quality_flags_generic_summary_and_missing_transmission(
    monkeypatch,
    tmp_path: Path,
) -> None:
    _settings(monkeypatch, tmp_path)
    with Session(_engine()) as session:
        _seed(session)
        packet = build_ai_review_packet(session, RUN_DATE, "us")
        assert packet is not None
        context = packet["market_context"]
        context["numeric_registry"] = [
            {
                "fact_id": "market:index:SPY",
                "field_path": "fields.return_pct",
                "value": 1.0,
                "unit": "pct",
                "semantic_type": "index_return_pct",
                "registered": True,
                "prose_allowed": True,
                "scope": "market",
            },
            {
                "fact_id": "market:oil:DCOILWTICO",
                "field_path": "fields.return_pct",
                "value": 2.0,
                "unit": "pct",
                "semantic_type": "oil_return_pct",
                "registered": True,
                "prose_allowed": True,
                "scope": "market",
            },
        ]
        context["key_change_fact_ids"] = ["market:oil:DCOILWTICO"]
        context["transmission_candidates"] = [
            {
                "portfolio_group": "general",
                "market_fact_id": "market:oil:DCOILWTICO",
            }
        ]
        output = AIDailyReviewOutput.model_validate(_valid_output(packet))
        output.market_review.core_judgment.text = "시장 신호가 혼재했습니다."
        report = ai_review_service.quantitative_grounding_report(packet, output)

    assert report["market"]["flags"] == [
        "insufficient_market_quantitative_grounding",
        "market_fact_without_transmission",
        "generic_market_summary",
    ]


def test_signed_supply_value_and_audit_only_denominator_are_fail_closed(
    monkeypatch,
    tmp_path: Path,
) -> None:
    _settings(monkeypatch, tmp_path)
    with Session(_engine()) as session:
        _seed(session)
        packet = build_ai_review_packet(session, RUN_DATE, "us")
        assert packet is not None
        stock = packet["stocks"][0]
        stock["fact_catalog"].append(
            {
                "fact_id": "positioning:signed",
                "fact_type": "positioning",
                "fields": {"foreign_net_buy_qty": -100},
            }
        )
        stock["numeric_registry"] = ai_review_service._numeric_registry(
            stock["fact_catalog"]
        )

        valid = _valid_output(packet)
        valid_review = valid["stock_reviews"][0]
        valid_review["facts_used"].append("positioning:signed")
        valid_review["supply_analysis"]["text"] = "외국인 순매도 -100주는 확인된 수급입니다."
        signed_claim = {
                "fact_id": "positioning:signed",
                "field_path": "fields.foreign_net_buy_qty",
                "value": -100,
                "unit": "shares",
                "semantic_type": "foreign_net_buy_qty",
                "text_ref": "supply_analysis.text",
                "usage": "외국인 순매도 -100주",
            }
        valid_review["numeric_claims"].append(signed_claim)
        _, valid_errors = validate_ai_review_output(session, packet, valid)

        absolute_sell = _valid_output(packet)
        absolute_sell_review = absolute_sell["stock_reviews"][0]
        absolute_sell_review["facts_used"].append("positioning:signed")
        absolute_sell_review["supply_analysis"]["text"] = (
            "외국인 순매도 100주는 확인된 수급입니다."
        )
        absolute_sell_review["numeric_claims"].append(
            {
                **signed_claim,
                "usage": "외국인 순매도 100주",
            }
        )
        _, absolute_sell_errors = validate_ai_review_output(
            session, packet, absolute_sell
        )

        wrong_direction = _valid_output(packet)
        wrong_direction_review = wrong_direction["stock_reviews"][0]
        wrong_direction_review["facts_used"].append("positioning:signed")
        wrong_direction_review["supply_analysis"]["text"] = (
            "외국인 순매수 100주는 확인된 수급입니다."
        )
        wrong_direction_review["numeric_claims"].append(
            {
                **signed_claim,
                "usage": "외국인 순매수 100주",
            }
        )
        _, wrong_direction_errors = validate_ai_review_output(
            session, packet, wrong_direction
        )

        capital = next(
            item
            for item in stock["fact_catalog"]
            if item["fact_type"] == "treasury_stock_transaction"
        )
        denied = _valid_output(packet)
        denied_review = denied["stock_reviews"][0]
        denied_review["facts_used"].append(capital["fact_id"])
        denied_review["core_judgment"]["text"] = "분모 주식 수 29,700,000주는 audit 전용입니다."
        denied_review["numeric_claims"].append(
            {
                "fact_id": capital["fact_id"],
                "field_path": "fields.share_denominator",
                "value": 29_700_000,
                "unit": "shares",
                "semantic_type": "share_denominator",
                "text_ref": "core_judgment.text",
                "usage": "분모 주식 수 29,700,000주",
            }
        )
        _, denied_errors = validate_ai_review_output(session, packet, denied)

        assert valid_errors == []
        assert absolute_sell_errors == []
        assert any(
            "numeric_usage_direction_mismatch" in error
            for error in wrong_direction_errors
        )
    assert any("numeric_semantic_not_supported" in error for error in denied_errors)


def test_representative_packet_numeric_registry_has_explicit_coverage(
    monkeypatch,
    tmp_path: Path,
) -> None:
    _settings(monkeypatch, tmp_path)
    with Session(_engine()) as session:
        _seed(session)
        packet = build_ai_review_packet(session, RUN_DATE, "us")
        assert packet is not None

    registries = [packet["market_context"]["numeric_registry"]] + [
        stock["numeric_registry"] for stock in packet["stocks"]
    ]
    unsupported = [
        item
        for registry in registries
        for item in registry
        if item["registered"] is not True
    ]
    denied = [
        item
        for registry in registries
        for item in registry
        if item["prose_allowed"] is not True
    ]

    assert unsupported == []
    assert {item["semantic_type"] for item in denied} == {"share_denominator"}


def test_v32_packet_waits_for_profile_and_numeric_activation_gates(
    monkeypatch,
    tmp_path: Path,
) -> None:
    _settings(monkeypatch, tmp_path)
    provenance = tmp_path / "company_profile_provenance" / "PACKETUS.json"
    provenance.unlink()
    with Session(_engine()) as session:
        _seed(session)
        packet = build_ai_review_packet(session, RUN_DATE, "us")
        blocked = write_ai_review_packet(session, RUN_DATE, "us")

    assert packet is not None
    assert packet["ready_for_ai"] is False
    assert packet["shadow_cohort"]["profile_gate"]["ready"] is False
    assert packet["shadow_cohort"]["numeric_semantic_gate"]["ready"] is True
    assert blocked.status == "not_ready"
    assert blocked.reason == "shadow_cohort_activation_gate_failed"


def test_v35_packet_records_structure_v2_shadow_cohort_metadata(
    monkeypatch,
    tmp_path: Path,
) -> None:
    _settings(monkeypatch, tmp_path)
    with Session(_engine()) as session:
        _seed(session)
        packet = build_ai_review_packet(session, RUN_DATE, "us")

    assert packet is not None
    assert packet["analysis_policy_version"] == "daily-review-v3.10"
    assert packet["structure_algorithm_version"] == "ohlcv-structure-v2"
    assert packet["ready_for_ai"] is True
    assert packet["shadow_cohort"] == {
        "policy_version": "daily-review-v3.10",
        "eligible": True,
        "profile_gate": {
            "active_total": 1,
            "complete_count": 1,
            "missing_count": 0,
            "unavailable_count": 0,
            "ready": True,
        },
        "numeric_semantic_gate": {
            "entry_count": 16,
            "registered_count": 16,
            "prose_allowed_count": 15,
            "prose_denied_count": 1,
            "unsupported": [],
            "ready": True,
        },
    }


def test_v32_scheduled_claim_preserves_but_skips_old_policy_packet(
    monkeypatch,
    tmp_path: Path,
) -> None:
    _settings(monkeypatch, tmp_path)
    with Session(_engine()) as session:
        _seed(session)
        old_packet = build_ai_review_packet(
            session,
            RUN_DATE,
            "us",
            generated_at=datetime(2026, 8, 14, 0, 0, tzinfo=UTC),
        )
        assert old_packet is not None

    old_packet["packet_id"] = "preserved-v31-packet"
    old_packet["analysis_policy_version"] = "daily-review-v3.1"
    inbox = tmp_path / "ai_review" / "inbox"
    inbox.mkdir(parents=True, exist_ok=True)
    path = inbox / "preserved-v31-packet.json"
    path.write_text(json.dumps(old_packet, default=str), encoding="utf-8")

    claim = claim_next_ai_review_packet(
        "us",
        owner="v32-primary",
        now=datetime(2026, 8, 14, 0, 1, tzinfo=UTC),
    )

    assert claim.status == "no_pending_packet"
    assert path.exists()


def test_industry_framework_router_handles_quality_fixtures() -> None:
    fixtures = (
        ("Memory semiconductor", "DRAM", "memory", "memory_valuation"),
        ("Insurance", "Reinsurance", "insurance", "insurance_reinsurance_valuation"),
        ("Software", "SaaS recurring revenue", "saas", "saas_recurring_revenue_valuation"),
        ("Construction", "EPC projects", "epc", "epc_construction_valuation"),
        ("Biotech", "Pre-profit drug development", "biotech", "biotech_valuation"),
    )
    for industry, business_model, key, framework in fixtures:
        routing = investment_framework_routing(
            industry,
            business_model,
            "verified thesis",
            has_earnings=True,
            preliminary_earnings=True,
            has_price_context=True,
            has_adr_basis_risk=True,
        )
        assert routing["industry_key"] == key
        assert framework in routing["required_frameworks"]
        assert "provisional_earnings" in routing["required_frameworks"]
        assert "adr_share_basis" in routing["required_frameworks"]


def test_structured_industry_priority_and_secondary_frameworks() -> None:
    fixtures = (
        (
            "Semiconductors",
            "GPU and memory devices",
            "AI cloud CAPEX beneficiary",
            "semiconductor_valuation",
            "hyperscaler_capex_transmission",
        ),
        (
            "Insurance",
            "Recurring premium revenue",
            "Digital distribution growth",
            "insurance_reinsurance_valuation",
            None,
        ),
        (
            "Construction / EPC",
            "Engineering projects",
            "Hyperscaler data-center projects",
            "epc_construction_valuation",
            "hyperscaler_capex_transmission",
        ),
        (
            "Banking",
            "Digital platform",
            "Platform engagement",
            "bank_valuation",
            None,
        ),
        (
            "Holding company",
            "Semiconductor subsidiaries",
            "Portfolio discount closes",
            "holding_company_valuation",
            "semiconductor_valuation",
        ),
        (
            "Biotech",
            "Recurring royalty income",
            "Royalty growth",
            "biotech_valuation",
            None,
        ),
    )
    for industry, business_model, thesis, primary, secondary in fixtures:
        routing = investment_framework_routing(
            industry,
            business_model,
            thesis,
            has_earnings=False,
            preliminary_earnings=False,
            has_price_context=False,
            has_adr_basis_risk=False,
        )
        detail = routing["industry_routing"]
        assert detail["primary_framework"] == primary
        assert detail["source"] == "structured_industry"
        assert detail["confidence"] == "high"
        if secondary:
            assert secondary in detail["secondary_frameworks"]
        if primary != "saas_recurring_revenue_valuation":
            assert "saas_recurring_revenue_valuation" not in detail["secondary_frameworks"]


def test_structured_subtype_dominance_and_ambiguous_fallback() -> None:
    memory = investment_framework_routing(
        "Semiconductors",
        "DRAM and NAND memory",
        "Cloud demand",
        has_earnings=False,
        preliminary_earnings=False,
        has_price_context=False,
        has_adr_basis_risk=False,
    )
    detail = memory["industry_routing"]
    assert detail["primary_framework"] == "memory_valuation"
    assert detail["source"] == "structured_business_model_subtype"
    assert detail["confidence"] == "high"

    dominant = investment_framework_routing(
        None,
        "Semiconductors 70%, cloud computing 30%",
        "Cloud theme",
        has_earnings=False,
        preliminary_earnings=False,
        has_price_context=False,
        has_adr_basis_risk=False,
    )
    assert dominant["industry_routing"]["primary_framework"] == (
        "semiconductor_valuation"
    )
    assert dominant["industry_routing"]["confidence"] == "medium"

    ambiguous = investment_framework_routing(
        None,
        "Semiconductors and cloud computing",
        "SaaS cloud thesis wording",
        has_earnings=False,
        preliminary_earnings=False,
        has_price_context=False,
        has_adr_basis_risk=False,
    )
    assert ambiguous["industry_key"] == "general"
    assert ambiguous["industry_routing"] == {
        "primary_framework": None,
        "secondary_frameworks": [],
        "source": "unclassified",
        "confidence": "low",
        "evidence": [],
    }


def test_incompatible_industry_framework_is_rejected(
    monkeypatch,
    tmp_path: Path,
) -> None:
    _settings(monkeypatch, tmp_path)
    with Session(_engine()) as session:
        _seed(session)
        packet = build_ai_review_packet(session, RUN_DATE, "us")
        assert packet is not None
        output = _valid_output(packet)
        output["stock_reviews"][0]["frameworks_used"] = ["saas_recurring_revenue_valuation"]
        _, errors = validate_ai_review_output(session, packet, output)

    assert any("framework_not_allowed:saas_recurring_revenue_valuation" in item for item in errors)
    assert any("industry_framework_missing:memory_valuation" in item for item in errors)


def test_low_confidence_routing_does_not_force_specialized_framework(
    monkeypatch,
    tmp_path: Path,
) -> None:
    _settings(monkeypatch, tmp_path)
    with Session(_engine()) as session:
        _seed(session)
        packet = build_ai_review_packet(session, RUN_DATE, "us")
        assert packet is not None
        routing = packet["stocks"][0]["knowledge_routing"]
        routing["industry_key"] = "general"
        routing["industry_routing"] = {
            "primary_framework": None,
            "secondary_frameworks": [],
            "source": "unclassified",
            "confidence": "low",
            "evidence": [],
        }
        routing["required_frameworks"] = list(ai_review_service._CORE_FRAMEWORKS)
        output = _valid_output(packet)
        output["stock_reviews"][0]["frameworks_used"] = [
            "market_expectations",
            "earnings_quality",
        ]
        routing["required_frameworks"].append("earnings_quality")
        _, errors = validate_ai_review_output(session, packet, output)

    assert not any("industry_framework_missing" in item for item in errors)
    assert errors == []


def test_shadow_comparison_flags_unsupported_quality_claims(
    monkeypatch,
    tmp_path: Path,
) -> None:
    _settings(monkeypatch, tmp_path)
    with Session(_engine()) as session:
        _seed(session)
        result = write_ai_review_packet(
            session,
            RUN_DATE,
            "us",
            generated_at=datetime(2026, 8, 14, 0, 0, tzinfo=UTC),
        )
        claim = claim_next_ai_review_packet(
            "us", owner="quality-fixture", now=datetime(2026, 8, 14, 0, 1, tzinfo=UTC)
        )
        packet = json.loads(Path(result.path).read_text(encoding="utf-8"))
        output = _valid_output(packet, claim_id=claim.claim_id)
        review = output["stock_reviews"][0]
        review["business_earnings"] = {
            "text": "Free cash flow improved even though the packet has no FCF fact.",
            "fact_ids": review["facts_used"],
        }
        review["core_judgment"]["text"] = "A low PER alone proves undervaluation."
        Path(claim.temp_output_path).write_text(json.dumps(output), encoding="utf-8")
        completed = finalize_ai_review_output(
            session, claim.packet_id, claim_id=claim.claim_id
        )
        comparison = json.loads(
            Path(completed.comparison_path).read_text(encoding="utf-8")
        )

    assert completed.status == "completed"
    flags = comparison["comparisons"][0]["guardrail_conflicts"]
    assert "unsupported_claim:free_cash_flow" in flags
    assert "memory_low_per_only_conclusion" in flags


def test_unknown_ticker_and_partial_output_are_rejected(monkeypatch, tmp_path: Path) -> None:
    _settings(monkeypatch, tmp_path)
    with Session(_engine()) as session:
        _seed(session)
        packet = build_ai_review_packet(session, RUN_DATE, "us")
        assert packet is not None
        output = _valid_output(packet)
        output["stock_reviews"][0]["ticker"] = "UNKNOWN"

        _, errors = validate_ai_review_output(session, packet, output)

    assert "ticker_set_mismatch" in errors


def test_skill_fixture_and_output_schema_are_present() -> None:
    skill_root = (
        Path(__file__).resolve().parents[1]
        / ".agents"
        / "skills"
        / "thesis-monitor-daily-review"
    )
    schema = json.loads(
        (skill_root / "references" / "output-schema.json").read_text(encoding="utf-8")
    )
    skill = (skill_root / "SKILL.md").read_text(encoding="utf-8")

    assert schema["properties"]["schema_version"] == {"const": "4"}
    assert "claim_id" in schema["required"]
    assert "knowledge_sha256" in schema["required"]
    numeric_claim = schema["$defs"]["numericClaim"]
    assert "semantic_type" in numeric_claim["required"]
    assert "text_ref" in numeric_claim["required"]
    assert "$thesis-monitor-daily-review" in skill
    assert "Do not browse the web" in skill
    assert "data/ai_review" in skill
    assert "knowledge-index.md" in skill
    assert "chart-knowledge-index.md" in skill
    assert "stock-chart-value-analysis-knowledge-v1.md" in skill
    assert "schema-4 reasoning sections" in skill
    assert "--claim-id" in skill
    market_review = schema["$defs"]["marketReview"]["properties"]
    assert market_review["important_changes"]["maxItems"] == 4
    assert market_review["portfolio_transmission"]["maxItems"] == 4
    assert market_review["next_checks"]["maxItems"] == 3
    assert market_review["unknowns"]["maxItems"] == 3
