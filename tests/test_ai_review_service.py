import hashlib
import json
import threading
from concurrent.futures import ThreadPoolExecutor
from datetime import UTC, date, datetime, timedelta
from pathlib import Path

from sqlalchemy.pool import StaticPool
from sqlmodel import SQLModel, Session, create_engine, select

import app.services.ai_review_service as ai_review_service
from app.config import get_settings
from app.models.company import Company
from app.models.macro import MacroBriefing
from app.models.thesis import (
    InvestmentThesis,
    MonitorRun,
    NotificationDelivery,
    ThesisAssessment,
)
from app.models.watchlist import WatchlistItem
from app.services.ai_review_service import (
    build_ai_review_packet,
    claim_next_ai_review_packet,
    finalize_ai_review_output,
    investment_framework_routing,
    knowledge_manifest,
    validate_ai_review_output,
    write_ai_review_packet,
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
                "price_as_of": assessment_date.isoformat(),
                "latest_earnings_period": "2026-06-30",
                "latest_revenue": 500.0,
                "latest_operating_income": 50.0,
                "latest_operating_margin": 10.0,
                "trailing_pe": 20.0,
                "price_to_book": 3.0,
                "forward_pe": 18.0,
                "forward_eps": 5.5,
                "forward_pe_source": "modeled_forward",
                "forecast_method": "normalized_roe",
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


def _valid_output(
    packet: dict[str, object],
    *,
    claim_id: str = "fixture-claim",
) -> dict[str, object]:
    stock = packet["stocks"][0]
    facts = stock["fact_catalog"]
    market_facts = packet["market_context"]["fact_catalog"]
    return {
        "schema_version": "2",
        "packet_id": packet["packet_id"],
        "claim_id": claim_id,
        "analysis_policy_version": packet["analysis_policy_version"],
        "knowledge_version": packet["knowledge"]["version"],
        "knowledge_sha256": packet["knowledge"]["sha256"],
        "market": packet["market"],
        "assessment_date": packet["assessment_date"],
        "market_review": {
            "facts_used": [market_facts[0]["fact_id"]] if market_facts else [],
            "frameworks_used": ["macro_transmission"],
            "interpretation": [
                {
                    "text": "The verified market inputs do not establish a new regime.",
                    "fact_ids": [market_facts[0]["fact_id"]] if market_facts else [],
                }
            ],
            "numeric_claims": [],
            "unknowns": ["Direction remains uncertain."],
            "summary": "Keep the market context separate from company fundamentals.",
        },
        "stock_reviews": [
            {
                "ticker": stock["ticker"],
                "thesis_version": stock["thesis_version"],
                "ai_thesis_assessment": "no_material_change",
                "earnings_estimate_view": "unchanged",
                "valuation_view": "neutral",
                "facts_used": [facts[0]["fact_id"]],
                "frameworks_used": ["memory_valuation", "market_expectations"],
                "interpretation": [
                    {
                        "text": "The verified order supports the existing demand thesis.",
                        "fact_ids": [facts[0]["fact_id"]],
                    }
                ],
                "numeric_claims": [],
                "unknowns": ["Delivery timing remains unknown."],
                "summary": "The evidence is supportive but does not require a status change.",
                "holder_view": "Track execution and margin delivery.",
                "new_buyer_view": "Separate company quality from entry valuation.",
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
        hallucination["stock_reviews"][0]["summary"] = "Revenue reached 999 billion."
        _, errors = validate_ai_review_output(session, packet, hallucination)
        assert any(
            "numbers_without_provenance:summary:999" in item for item in errors
        )

        modeled_as_consensus = _valid_output(packet)
        modeled_as_consensus["stock_reviews"][0]["summary"] = "시장 컨센서스 EPS가 반영됐습니다."
        _, errors = validate_ai_review_output(session, packet, modeled_as_consensus)
        assert any("modeled_forward_called_consensus" in item for item in errors)

        invalid_history = _valid_output(packet)
        invalid_history["stock_reviews"][0]["summary"] = "과거 배수 기준으로 저평가입니다."
        _, errors = validate_ai_review_output(session, packet, invalid_history)
        assert any("invalid_historical_comparison_used" in item for item in errors)

        knowledge_mismatch = _valid_output(packet)
        knowledge_mismatch["knowledge_sha256"] = "0" * 64
        _, errors = validate_ai_review_output(session, packet, knowledge_mismatch)
        assert "identity_mismatch:knowledge_sha256" in errors


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
        review["interpretation"].append(
            {
                "text": "영업이익률 10%는 현재 수익성의 확인된 기준입니다.",
                "fact_ids": [earnings["fact_id"]],
            }
        )
        review["numeric_claims"].append(
            {
                "fact_id": earnings["fact_id"],
                "field_path": "fields.operating_margin_pct",
                "value": 10.0,
                "unit": "pct",
                "semantic_type": "operating_margin",
                "text_ref": "interpretation[1].text",
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
        krw_review["facts_used"] = [contract["fact_id"]]
        krw_review["interpretation"] = [
            {
                "text": "계약금액 3,190억원은 확인된 수주 규모입니다.",
                "fact_ids": [contract["fact_id"]],
            }
        ]
        krw_review["numeric_claims"] = [
            {
                "fact_id": contract["fact_id"],
                "field_path": "fields.contract_amount.value",
                "value": 318_964_597_910,
                "unit": "KRW",
                "semantic_type": "contract_amount",
                "text_ref": "interpretation[0].text",
                "usage": "계약금액 3,190억원",
            }
        ]
        _, errors = validate_ai_review_output(session, packet, krw)
        assert errors == []

        wrong_semantic = _valid_output(packet)
        wrong_review = wrong_semantic["stock_reviews"][0]
        wrong_review["facts_used"] = ["price:current"]
        wrong_review["interpretation"] = [
            {
                "text": "매출 성장률은 100 USD입니다.",
                "fact_ids": ["price:current"],
            }
        ]
        wrong_review["numeric_claims"] = [
            {
                "fact_id": "price:current",
                "field_path": "fields.current_price",
                "value": 100,
                "unit": "USD",
                "semantic_type": "share_price",
                "text_ref": "interpretation[0].text",
                "usage": "매출 성장률 100 USD",
            }
        ]
        _, errors = validate_ai_review_output(session, packet, wrong_semantic)
        assert any("numeric_usage_semantic_mismatch" in item for item in errors)

        unsupported_derived = _valid_output(packet)
        unsupported_derived["stock_reviews"][0]["summary"] = "추정 성장률은 55%입니다."
        _, errors = validate_ai_review_output(session, packet, unsupported_derived)
        assert any(
            "numbers_without_provenance:summary:55" in item for item in errors
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
        review["facts_used"] = [capital["fact_id"]]
        review["interpretation"] = [
            {
                "text": "처분 주식 비율 약 0.11%는 소규모입니다.",
                "fact_ids": [capital["fact_id"]],
            }
        ]
        review["numeric_claims"] = [
            {
                "fact_id": capital["fact_id"],
                "field_path": "fields.share_ratio_pct",
                "value": 0.1095,
                "unit": "pct",
                "semantic_type": "share_ratio",
                "text_ref": "interpretation[0].text",
                "usage": "처분 주식 비율 약 0.11%",
            }
        ]
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
        review["summary"] = "매출 성장률은 100%입니다."
        review["holder_view"] = "현재가 100 USD에서는 실행 가격을 분리해 봅니다."
        review["numeric_claims"] = [
            {
                "fact_id": "price:current",
                "field_path": "fields.current_price",
                "value": 100,
                "unit": "USD",
                "semantic_type": "share_price",
                "text_ref": "holder_view",
                "usage": "현재가 100 USD",
            }
        ]
        _, errors = validate_ai_review_output(session, packet, output)

    assert any(
        "numbers_without_provenance:summary:100" in error for error in errors
    )
    assert not any(
        "numbers_without_provenance:holder_view:100" in error for error in errors
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
        review["summary"] = "현재가 100 USD는 확인된 가격입니다."
        review["numeric_claims"] = [
            {
                "fact_id": "price:current",
                "field_path": "fields.current_price",
                "value": 100,
                "unit": "USD",
                "semantic_type": "revenue_yoy",
                "text_ref": "holder_view",
                "usage": "현재가 100 USD",
            }
        ]
        _, errors = validate_ai_review_output(session, packet, output)

    assert any("numeric_semantic_type_mismatch" in error for error in errors)
    assert any("numeric_usage_not_in_text_ref" in error for error in errors)
    assert any("numbers_without_provenance:summary:100" in error for error in errors)


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
        review["summary"] = "처분 주식 비율 약 0.2%는 소규모입니다."
        review["numeric_claims"] = [
            {
                "fact_id": capital["fact_id"],
                "field_path": "fields.share_ratio_pct",
                "value": 0.1095,
                "unit": "pct",
                "semantic_type": "share_ratio",
                "text_ref": "summary",
                "usage": "처분 주식 비율 약 0.2%",
            }
        ]
        _, errors = validate_ai_review_output(session, packet, output)

    assert any("numeric_usage_value_mismatch" in error for error in errors)
    assert any("numbers_without_provenance:summary:0.2" in error for error in errors)


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
        market_review["summary"] = "2026년 2분기 기준 시장 등락률은 -3.17%입니다."
        market_review["numeric_claims"] = [
            {
                "fact_id": "market:test:return",
                "field_path": "fields.percent_change",
                "value": -3.17,
                "unit": "pct",
                "semantic_type": "percent_change",
                "text_ref": "summary",
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
        market_review["summary"] = "시장 등락률은 +0.67%였습니다."
        market_review["numeric_claims"] = [
            {
                "fact_id": "market:test:positive-return",
                "field_path": "fields.percent_change",
                "value": 0.67,
                "unit": "pct",
                "semantic_type": "percent_change",
                "text_ref": "summary",
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
        review["summary"] = "현재 PER 20배는 확인됐지만 순이익률 10%는 제공되지 않았습니다."
        review["numeric_claims"] = [
            {
                "fact_id": "valuation:current",
                "field_path": "fields.trailing_pe",
                "value": 20,
                "unit": "x",
                "semantic_type": "trailing_pe",
                "text_ref": "summary",
                "usage": "현재 PER 20배",
            }
        ]
        _, errors = validate_ai_review_output(session, packet, output)

    assert not any("summary:20" in error for error in errors)
    assert any("numbers_without_provenance:summary:10" in error for error in errors)


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
        review["summary"] = "핵심 요인 2가지를 봤지만 계약 수량 100개는 근거가 없습니다."
        review["numeric_claims"] = []
        _, errors = validate_ai_review_output(session, packet, output)

    assert not any("summary:2" in error for error in errors)
    assert any("numbers_without_provenance:summary:100" in error for error in errors)


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


def test_knowledge_v3_policy_identity_starts_new_shadow_cohort() -> None:
    assert ai_review_service.ANALYSIS_POLICY_VERSION == "daily-review-v3.1"
    manifest = knowledge_manifest()
    assert manifest["version"] == "3.0"
    assert manifest["sha256"] == (
        "559ad45e4dd86cb0aec9bb09b51a5dc816bf323e8c2b4fd050cf28960a5a9d18"
    )


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
        review["interpretation"] = [
            {
                "text": "Free cash flow improved even though the packet has no FCF fact.",
                "fact_ids": review["facts_used"],
            }
        ]
        review["summary"] = "A low PER alone proves undervaluation."
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

    assert schema["properties"]["schema_version"] == {"const": "2"}
    assert "claim_id" in schema["required"]
    assert "knowledge_sha256" in schema["required"]
    numeric_claim = schema["$defs"]["numericClaim"]
    assert "semantic_type" in numeric_claim["required"]
    assert "text_ref" in numeric_claim["required"]
    assert "$thesis-monitor-daily-review" in skill
    assert "Do not browse the web" in skill
    assert "data/ai_review" in skill
    assert "knowledge-index.md" in skill
    assert "--claim-id" in skill
