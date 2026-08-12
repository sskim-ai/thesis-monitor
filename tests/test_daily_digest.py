import json
from datetime import date, datetime, timezone

import httpx
import pytest
from sqlalchemy.pool import StaticPool
from sqlmodel import SQLModel, Session, create_engine, select

from app.database import engine, init_db
from app.macro.regime import assess_macro_regime
from app.models.macro import MacroBriefing, MacroObservation, ThesisMacroImpact
from app.models.thesis import InvestmentThesis, MonitorRun, NotificationDelivery, ThesisAssessment
from app.models.watchlist import WatchlistItem
from app.services.daily_digest import build_daily_digest
from app.services.daily_digest_renderer import render_daily_digest
from app.services.notification_service import (
    TelegramNotifier,
    _supply_report,
    dispatch_pending_notifications,
    queue_daily_digest_notification,
    queue_daily_stock_notification,
    queue_notification,
)


TICKERS = [
    ("000660D", "SK하이닉스"),
    ("003690D", "코리안리"),
    ("005490D", "POSCO홀딩스"),
    ("005930D", "삼성전자"),
    ("086280D", "현대글로비스"),
    ("CRCLD", "Circle"),
    ("GOOGLD", "Alphabet"),
    ("IBMD", "IBM"),
    ("MUD", "Micron"),
    ("RXRXD", "Recursion"),
    ("SNDKD", "SanDisk"),
    ("TSLAD", "Tesla"),
    ("TSMD", "TSMC"),
    ("WRDD", "WeRide"),
]


def _briefing(run_date: date) -> MacroBriefing:
    observations = [
        {
            "series_code": "SPY",
            "change_pct": 1.2,
            "quality_status": "fresh",
        },
        {
            "series_code": "QQQ",
            "change_pct": 1.8,
            "quality_status": "fresh",
        },
        {
            "series_code": "SOXX",
            "change_pct": 2.1,
            "quality_status": "fresh",
        },
        {
            "series_code": "DFII10",
            "change_value": 0.06,
            "quality_status": "fresh",
        },
        {
            "series_code": "VIXCLS",
            "change_pct": -6.0,
            "quality_status": "fresh",
        },
        {
            "series_code": "DTWEXBGS",
            "change_pct": 2.0,
            "quality_status": "stale",
        },
    ]
    return MacroBriefing(
        briefing_date=run_date,
        briefing_type="morning",
        as_of=datetime.combine(run_date, datetime.min.time(), tzinfo=timezone.utc),
        headline="mixed",
        market_summary=json.dumps({"items": [], "observations": observations}),
        regime_summary=json.dumps(
            {
                "label": "mixed",
                "confidence": 0.75,
                "growth_momentum": 0,
                "inflation_pressure": 0,
                "liquidity_condition": 0,
                "financial_conditions": -1,
                "risk_appetite": 1,
                "earnings_momentum": 0,
            }
        ),
        today_calendar="[]",
        macro_theses=json.dumps(
            [
                {
                    "thesis_key": "fed_policy_path",
                    "title": "연준 정책경로와 장기 실질금리",
                    "status": "intact",
                    "daily_signal": -1,
                }
            ],
            ensure_ascii=False,
        ),
        ticker_impacts="[]",
        data_quality=json.dumps(
            [
                {
                    "series_code": "DTWEXBGS",
                    "quality_status": "stale",
                    "observed_at": "2038-01-01",
                }
            ]
        ),
        kakao_text="unused",
        status="ready",
        dedupe_key=f"digest-test:{run_date}",
    )


def _kr_close_briefing(run_date: date) -> MacroBriefing:
    return MacroBriefing(
        briefing_date=run_date,
        briefing_type="kr_close",
        as_of=datetime.combine(run_date, datetime.min.time(), tzinfo=timezone.utc),
        headline="한국 장마감 환율 점검",
        market_summary=json.dumps(
            {
                "fx": [
                    {
                        "series_code": "USDKRW_KR_CLOSE",
                        "value": 1417.4,
                        "change_value": 7.1,
                        "change_pct": 0.5035,
                        "quality_status": "fresh",
                    },
                    {
                        "series_code": "JPYKRW100_KR_CLOSE",
                        "value": 886.9,
                        "change_value": -2.8,
                        "change_pct": -0.3147,
                        "quality_status": "fresh",
                    },
                    {
                        "series_code": "EURKRW_KR_CLOSE",
                        "value": 1634.7,
                        "change_value": 5.4,
                        "change_pct": 0.3314,
                        "quality_status": "fresh",
                    },
                ]
            }
        ),
        data_quality="[]",
        kakao_text="unused",
        status="ready",
        dedupe_key=f"digest-kr-close-test:{run_date}",
    )


def _seed_digest(
    session: Session,
    run_date: date,
    suffix: str = "",
) -> list[ThesisAssessment]:
    session.add(_briefing(run_date))
    assessments: list[ThesisAssessment] = []
    statuses = {
        "000660D": "strengthened",
        "TSLAD": "weakened",
        "WRDD": "invalidation_candidate",
    }
    valuations = {
        "000660D": "mixed",
        "TSLAD": "compression",
        "TSMD": "expansion",
    }
    for base_ticker, company_name in TICKERS:
        ticker = f"{base_ticker}{suffix}"
        status = statuses.get(base_ticker, "no_material_change")
        valuation = valuations.get(base_ticker, "neutral")
        session.add(WatchlistItem(ticker=ticker, company_name=company_name))
        session.add(
            InvestmentThesis(
                ticker=ticker,
                version=1,
                core_thesis=f"{company_name}의 사업 성장과 현금흐름을 확인합니다.",
                validation_metrics=json.dumps(
                    ["매출 성장", "영업이익률", "영업현금흐름", "FCF", "ROIC"],
                    ensure_ascii=False,
                ),
                weaken_signals=json.dumps(["FCF 악화"], ensure_ascii=False),
                invalidation_signals=json.dumps(["구조적 수요 붕괴"], ensure_ascii=False),
                market_expectations=json.dumps(
                    {"level": "very_high" if base_ticker == "000660D" else "balanced"}
                ),
                valuation_framework=json.dumps({"primary_method": "forward P/E"}),
            )
        )
        assessment = ThesisAssessment(
            ticker=ticker,
            thesis_version=1,
            assessment_date=run_date,
            status=status,
            business_thesis_change=status,
            valuation_change=valuation,
            earnings_estimate_impact="up" if base_ticker == "000660D" else "unknown",
            score=30 if status == "strengthened" else -30 if status != "no_material_change" else 0,
            confidence=0.8 if status != "no_material_change" else 0.0,
            summary="구조화된 근거를 기준으로 일일 평가를 완료했습니다.",
            new_buyer_view="시장 기대와 추가 실적 확인을 우선합니다.",
            holder_view="핵심 검증 지표의 지속 여부를 관리합니다.",
            price_view="가격 판단은 별도 기준으로 확인합니다.",
            risk_level="watch",
            evidence="[]",
            confirmed_facts="[]",
            inferred_implications="[]",
            unknowns="[]",
            market_expectation_assessment="{}",
            price_context="{}",
            valuation_context=json.dumps({"impact": valuation}),
            thesis_snapshot="{}",
        )
        session.add(assessment)
        assessments.append(assessment)
    session.add(
        ThesisMacroImpact(
            ticker=f"000660D{suffix}",
            thesis_version=1,
            assessment_date=run_date,
            direction="mixed",
            magnitude=3,
            channels='["discount_rate"]',
            earnings_effect="neutral",
            valuation_effect="weaken",
            rationale="실질금리 전달 경로",
            evidence=json.dumps(
                [
                    {
                        "series_code": "DFII10",
                        "contribution": -12,
                        "exposure": {"channel": "discount_rate"},
                    }
                ]
            ),
        )
    )
    session.commit()
    return assessments


def test_fourteen_stock_digest_is_deterministic_and_hides_axis_scores() -> None:
    init_db()
    run_date = date(2038, 8, 10)
    with Session(engine) as session:
        _seed_digest(session, run_date)
        digest = build_daily_digest(session, run_date)
        first = render_daily_digest(digest)
        second = render_daily_digest(build_daily_digest(session, run_date))

        assert first == second
        assert "전체 14개 종목 평가 완료" in first
        assert "6축 점수" not in first
        assert "성장 +0" not in first
        assert "유지 · 신규 데이터 없음" in first
        assert "미 달러지수(광의): stale" in first
        assert "오늘 글로벌 유동성 방향은 판단을 유보" in first
        assert [item.ticker for item in digest.portfolio.focus_tickers[:3]] == [
            "WRDD",
            "TSLAD",
            "000660D",
        ]


def test_daily_digest_and_material_alert_are_queued_separately() -> None:
    init_db()
    run_date = date(2038, 8, 11)
    with Session(engine) as session:
        assessments = _seed_digest(session, run_date, suffix="Q")
        digest_delivery = queue_daily_digest_notification(session, run_date)
        material = next(item for item in assessments if item.ticker == "000660DQ")
        queue_notification(session, material)
        queue_notification(session, material)
        session.commit()

        assert digest_delivery is not None
        deliveries = session.exec(
            select(NotificationDelivery).where(NotificationDelivery.assessment_date == run_date)
        ).all()
        assert {item.ticker for item in deliveries} == {"__DAILY_DIGEST__", "000660DQ"}
        digest_payload = json.loads(digest_delivery.payload)
        assert digest_payload["use_llm"] is False
        assert digest_payload["type"] == "daily_monitoring_digest"


def test_daily_stock_analysis_is_queued_without_material_change() -> None:
    init_db()
    run_date = date(2038, 8, 12)
    with Session(engine) as session:
        assessments = _seed_digest(session, run_date, suffix="M")
        neutral = next(
            item for item in assessments if item.business_thesis_change == "no_material_change"
        )

        delivery = queue_daily_stock_notification(session, neutral)
        session.commit()

        payload = json.loads(delivery.payload)
        assert payload["type"] == "daily_stock_analysis"
        assert payload["ticker"] == neutral.ticker
        assert "오늘 중요한 신규 변화 없음" in payload["text"]
        assert "오늘 투자 논리를 바꿀 신규 확정 사실은 확인되지 않았습니다." not in payload["text"]
        assert "🚨 오늘 새 경고" not in payload["text"]
        assert "⚠️ 기존 경고" not in payload["text"]


def test_queued_daily_digest_omits_duplicate_stock_detail_section() -> None:
    init_db()
    run_date = date(2038, 8, 13)
    with Session(engine) as session:
        _seed_digest(session, run_date, suffix="S")

        delivery = queue_daily_digest_notification(session, run_date)

        assert delivery is not None
        payload = json.loads(delivery.payload)
        assert "📊 14종목 상태" in payload["text"]
        assert "🔎 오늘 상세 점검" not in payload["text"]


def test_market_scoped_digest_uses_separate_keys_and_portfolios() -> None:
    init_db()
    run_date = date(2038, 8, 14)
    with Session(engine) as session:
        assessments = _seed_digest(session, run_date, suffix="X")
        for assessment in assessments:
            item = session.exec(
                select(WatchlistItem).where(WatchlistItem.ticker == assessment.ticker)
            ).one()
            item.exchange = "KRX" if item.company_name in {
                "SK하이닉스", "코리안리", "POSCO홀딩스", "삼성전자", "현대글로비스"
            } else "NASDAQ"
        session.add(_kr_close_briefing(run_date))
        session.commit()

        us_delivery = queue_daily_digest_notification(session, run_date, market_scope="us")
        kr_delivery = queue_daily_digest_notification(session, run_date, market_scope="kr")

        assert us_delivery is not None
        assert kr_delivery is not None
        assert us_delivery.ticker == "__DAILY_DIGEST__"
        assert kr_delivery.ticker == "__DAILY_DIGEST_KR__"
        us_payload = json.loads(us_delivery.payload)
        kr_payload = json.loads(kr_delivery.payload)
        assert us_payload["market_scope"] == "us"
        assert kr_payload["market_scope"] == "kr"
        assert "🌎 미국 종목 점검" in us_payload["text"]
        assert "전체 9개 종목 평가 완료" in us_payload["text"]
        assert "💱 환율" not in us_payload["text"]
        assert "🇰🇷 한국 종목 장마감 점검" in kr_payload["text"]
        assert "🇰🇷 한국 시장환경 점검" not in kr_payload["text"]
        assert "💱 환율" in kr_payload["text"]
        assert "원/달러 1,417.4원 · +7.1원 (+0.50%)" in kr_payload["text"]
        assert "원/100엔 886.9원 · -2.8원 (-0.31%)" in kr_payload["text"]
        assert "원/유로 1,634.7원 · +5.4원 (+0.33%)" in kr_payload["text"]
        assert kr_payload["text"].index("💱 환율") < kr_payload["text"].index(
            "현재 환경:"
        )
        assert "전체 5개 종목 평가 완료" in kr_payload["text"]


@pytest.mark.anyio
async def test_dispatcher_sends_only_selected_delivery_ids() -> None:
    class RecordingNotifier:
        def __init__(self) -> None:
            self.payloads: list[dict[str, object]] = []

        async def send(self, payload: dict[str, object]) -> str:
            self.payloads.append(payload)
            return "sent"

    init_db()
    run_date = date(2038, 8, 15)
    with Session(engine) as session:
        us_delivery = NotificationDelivery(
            ticker="US-SCOPED",
            assessment_date=run_date,
            channel="telegram",
            status="pending",
            payload=json.dumps({"text": "US"}),
        )
        kr_delivery = NotificationDelivery(
            ticker="KR-SCOPED",
            assessment_date=run_date,
            channel="telegram",
            status="pending",
            payload=json.dumps({"text": "KR"}),
        )
        session.add(us_delivery)
        session.add(kr_delivery)
        session.commit()
        notifier = RecordingNotifier()

        await dispatch_pending_notifications(
            session, notifier=notifier, delivery_ids={us_delivery.id}
        )
        session.refresh(us_delivery)
        session.refresh(kr_delivery)

        assert us_delivery.status == "sent"
        assert kr_delivery.status == "pending"
        assert notifier.payloads == [{"text": "US"}]


@pytest.mark.anyio
async def test_kr_digest_is_dispatched_before_older_stock_delivery() -> None:
    class RecordingNotifier:
        def __init__(self) -> None:
            self.types: list[str] = []

        async def send(self, payload: dict[str, object]) -> str:
            self.types.append(str(payload["type"]))
            return "sent"

    isolated_engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    SQLModel.metadata.create_all(isolated_engine)
    run_date = date(2038, 8, 15)
    with Session(isolated_engine) as session:
        stock = NotificationDelivery(
            ticker="005930",
            assessment_date=run_date,
            channel="telegram",
            status="pending",
            payload=json.dumps({"text": "stock", "type": "daily_stock_analysis"}),
            created_at=datetime(2038, 8, 15, 7, 0, tzinfo=timezone.utc),
        )
        digest = NotificationDelivery(
            ticker="__DAILY_DIGEST_KR__",
            assessment_date=run_date,
            channel="telegram",
            status="pending",
            payload=json.dumps({"text": "digest", "type": "daily_monitoring_digest"}),
            created_at=datetime(2038, 8, 15, 7, 1, tzinfo=timezone.utc),
        )
        session.add_all([stock, digest])
        session.commit()
        notifier = RecordingNotifier()

        await dispatch_pending_notifications(
            session,
            notifier=notifier,
            delivery_ids={stock.id, digest.id},
        )

    assert notifier.types == ["daily_monitoring_digest", "daily_stock_analysis"]


@pytest.mark.anyio
@pytest.mark.parametrize(
    ("digest_status", "stock_status", "expected_texts"),
    [
        ("sent", "sent", []),
        ("pending", "sent", ["digest"]),
        ("sent", "pending", ["stock"]),
        ("pending", "pending", ["digest", "stock"]),
    ],
)
async def test_delivery_retry_sends_only_pending_rows(
    digest_status: str,
    stock_status: str,
    expected_texts: list[str],
) -> None:
    class RecordingNotifier:
        def __init__(self) -> None:
            self.texts: list[str] = []

        async def send(self, payload: dict[str, object]) -> str:
            self.texts.append(str(payload["text"]))
            return "sent"

    isolated_engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    SQLModel.metadata.create_all(isolated_engine)
    with Session(isolated_engine) as session:
        digest = NotificationDelivery(
            ticker="__DAILY_DIGEST_KR__",
            assessment_date=date(2044, 8, 15),
            channel="telegram",
            status=digest_status,
            payload=json.dumps({"text": "digest"}),
            attempt_count=2,
        )
        stock = NotificationDelivery(
            ticker="005930",
            assessment_date=date(2044, 8, 15),
            channel="telegram",
            status=stock_status,
            payload=json.dumps({"text": "stock"}),
            attempt_count=3,
        )
        session.add(digest)
        session.add(stock)
        session.commit()
        notifier = RecordingNotifier()

        await dispatch_pending_notifications(
            session,
            notifier=notifier,
            delivery_ids={digest.id, stock.id},
        )
        session.refresh(digest)
        session.refresh(stock)

        assert notifier.texts == expected_texts
        assert digest.attempt_count == 2 + (digest_status == "pending")
        assert stock.attempt_count == 3 + (stock_status == "pending")


def test_samsung_supply_renderer_is_compact_and_uses_actual_as_of_date() -> None:
    rendered = _supply_report(
        {
            "supply": {
                "available": True,
                "as_of_date": "2026-08-12",
                "foreign_net_buy_qty": -153_000,
                "institution_net_buy_qty": 205_000,
                "individual_net_buy_qty": 0,
                "foreign_net_buy_qty_5": -6_981_054,
                "institution_net_buy_qty_5": -34_386,
                "individual_net_buy_qty_5": 5_829_492,
                "foreign_net_buy_qty_20": -8_108_432,
                "institution_net_buy_qty_20": -11_716_549,
                "individual_net_buy_qty_20": 18_403_424,
                "foreign_holding_qty": 2_724_356_859,
                "foreign_holding_ratio": 46.6,
                "score": 29,
                "quality": "distribution",
                "primary_signal": "foreign_exit_retail_absorption",
                "confidence": "high",
                "validation_status": "validated",
            }
        }
    )

    assert rendered is not None
    assert "📊 수급 · 8/12 기준" in rendered
    assert "외국인 -15.3만주 · 기관 +20.5만주 · 개인 0주" in rendered
    assert "외국인 -698.1만주 · 기관 -3.4만주 · 개인 +582.9만주" in rendered
    assert "외국인 -810.8만주 · 기관 -1,171.7만주 · 개인 +1,840.3만주" in rendered
    assert "외국인 보유: 27.24억주 · 46.6%" in rendered
    assert "수급 점수: 29 · 분산/매도 우위 · 외국인 이탈·개인 흡수" in rendered


def test_low_confidence_supply_hides_unmapped_summary_enum() -> None:
    rendered = _supply_report(
        {
            "supply": {
                "available": True,
                "as_of_date": "2026-08-11",
                "foreign_net_buy_qty": -10,
                "quality": "new_unknown_quality",
                "primary_signal": "new_unknown_signal",
                "confidence": "low",
                "validation_status": "failed",
            }
        }
    )

    assert rendered is not None
    assert "📊 수급 · 8/11 기준" in rendered
    assert "외국인 -10주" in rendered
    assert "참고 수준" in rendered
    assert "new_unknown" not in rendered


@pytest.mark.anyio
async def test_default_telegram_path_never_calls_narrative_generator() -> None:
    class FailIfCalled:
        async def generate(self, context: dict[str, object], fallback: str) -> str:
            raise AssertionError("LLM generator must not run")

    sent: list[str] = []

    def handler(request: httpx.Request) -> httpx.Response:
        sent.append(json.loads(request.content)["text"])
        return httpx.Response(200, json={"ok": True, "result": {"message_id": 1}})

    notifier = TelegramNotifier(
        transport=httpx.MockTransport(handler),
        narrative_generator=FailIfCalled(),
    )
    notifier.settings = notifier.settings.model_copy(
        update={
            "notification_dry_run": False,
            "telegram_bot_token": "bot-token",
            "telegram_chat_id": "chat-id",
        }
    )
    result = await notifier.send(
        {
            "text": "결정론적 일일 분석",
            "presentation": "long_text",
            "use_llm": False,
        }
    )
    assert result == "sent"
    assert sent == ["결정론적 일일 분석"]


def test_stale_observation_is_not_used_for_regime_direction() -> None:
    init_db()
    run_date = date(2045, 1, 2)
    with Session(engine) as session:
        session.add(
            MacroObservation(
                dedupe_key="stale-dollar-2045",
                series_code="DTWEXBGS",
                category="fx",
                provider="test",
                observed_at=datetime(2045, 1, 2, tzinfo=timezone.utc),
                value=130,
                previous_value=120,
                change_value=10,
                change_pct=8.3,
                source_url="https://example.com/dollar",
                quality_status="stale",
            )
        )
        session.commit()
        regime = assess_macro_regime(session, run_date)

        assert regime.liquidity_condition == 0
        assert regime.confidence < 0.9


def test_digest_is_still_built_when_macro_briefing_failed() -> None:
    init_db()
    run_date = date(2050, 1, 2)
    with Session(engine) as session:
        session.add(
            MonitorRun(
                run_date=run_date,
                run_type="daily",
                status="failed",
                ticker_count=14,
                success_count=0,
                failure_count=14,
            )
        )
        session.commit()

        digest = build_daily_digest(session, run_date)
        report = render_daily_digest(digest)

        assert digest.macro.regime_label == "판단 보류"
        assert "시장환경 브리핑 생성 실패" in report
        assert "종목 일일 평가 0/14건 완료" in report
