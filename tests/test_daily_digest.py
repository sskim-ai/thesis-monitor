import json
from datetime import date, datetime, timezone

import httpx
import pytest
from sqlmodel import Session, select

from app.database import engine, init_db
from app.macro.regime import assess_macro_regime
from app.models.macro import MacroBriefing, MacroObservation, ThesisMacroImpact
from app.models.thesis import InvestmentThesis, MonitorRun, NotificationDelivery, ThesisAssessment
from app.models.watchlist import WatchlistItem
from app.services.daily_digest import build_daily_digest
from app.services.daily_digest_renderer import render_daily_digest
from app.services.notification_service import (
    TelegramNotifier,
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
        assert all(company_name in first for _ticker, company_name in TICKERS)
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
        assert "중요 변화 없음" in payload["text"]
        assert "오늘 투자 논리를 바꿀 신규 확정 사실은 확인되지 않았습니다." in payload["text"]
        assert "🚨 오늘 새 경고" in payload["text"]
        assert "⚠️ 아직 해결되지 않은 기존 경고" in payload["text"]


def test_queued_daily_digest_omits_duplicate_stock_detail_section() -> None:
    init_db()
    run_date = date(2038, 8, 13)
    with Session(engine) as session:
        _seed_digest(session, run_date, suffix="S")

        delivery = queue_daily_digest_notification(session, run_date)

        assert delivery is not None
        payload = json.loads(delivery.payload)
        assert "🏢 오늘 종목 점검" in payload["text"]
        assert "🔎 오늘 상세 점검" not in payload["text"]


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
