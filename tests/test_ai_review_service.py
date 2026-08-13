import json
from datetime import UTC, date, datetime, timedelta
from pathlib import Path

from sqlalchemy.pool import StaticPool
from sqlmodel import SQLModel, Session, create_engine, select

from app.config import get_settings
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
    validate_ai_review_output,
    write_ai_review_packet,
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
        thesis_snapshot=json.dumps({"assessment_mode": "daily_delta"}),
    )


def _seed(session: Session) -> None:
    ticker = "PACKETUS"
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


def _valid_output(packet: dict[str, object]) -> dict[str, object]:
    stock = packet["stocks"][0]
    facts = stock["fact_catalog"]
    market_facts = packet["market_context"]["fact_catalog"]
    return {
        "schema_version": "1",
        "packet_id": packet["packet_id"],
        "analysis_policy_version": packet["analysis_policy_version"],
        "market": packet["market"],
        "assessment_date": packet["assessment_date"],
        "market_review": {
            "facts_used": [market_facts[0]["fact_id"]] if market_facts else [],
            "interpretation": ["The verified market inputs do not establish a new regime."],
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
                "interpretation": ["The verified order supports the existing demand thesis."],
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
    assert packet["stocks"][0]["previous_assessment"]["assessment_date"] == "2026-08-13"
    assert packet["stocks"][0]["valuation"]["historical_comparison_withheld"] is True
    assert "historical_pe_statistics" not in packet["stocks"][0]["valuation"]
    rendered = json.dumps(packet, ensure_ascii=False)
    for token in ("OpenDART", "fs_div", "provider=", "unit=KRW", "raw_fact"):
        assert token not in rendered


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
            json.dumps(_valid_output(packet), ensure_ascii=False), encoding="utf-8"
        )
        assert not Path(claim.final_output_path).exists()
        completed = finalize_ai_review_output(
            session,
            packet_result.packet_id,
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
    assert recovered.status == "claimed"
    assert recovered.packet_id == first.packet_id
    claim_data = json.loads(Path(recovered.claim_path).read_text(encoding="utf-8"))
    assert claim_data["owner"] == "backup"


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
            json.dumps(_valid_output(packet), ensure_ascii=False), encoding="utf-8"
        )
        completed = finalize_ai_review_output(session, claim.packet_id)
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
        assert any("numbers_not_in_packet:999" in item for item in errors)

        modeled_as_consensus = _valid_output(packet)
        modeled_as_consensus["stock_reviews"][0]["summary"] = "시장 컨센서스 EPS가 반영됐습니다."
        _, errors = validate_ai_review_output(session, packet, modeled_as_consensus)
        assert any("modeled_forward_called_consensus" in item for item in errors)

        invalid_history = _valid_output(packet)
        invalid_history["stock_reviews"][0]["summary"] = "과거 배수 기준으로 저평가입니다."
        _, errors = validate_ai_review_output(session, packet, invalid_history)
        assert any("invalid_historical_comparison_used" in item for item in errors)


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

    assert schema["properties"]["schema_version"] == {"const": "1"}
    assert "$thesis-monitor-daily-review" in skill
    assert "Do not browse the web" in skill
    assert "data/ai_review" in skill
