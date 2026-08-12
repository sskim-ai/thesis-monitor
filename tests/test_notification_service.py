import json
from datetime import date, datetime, timezone
from types import SimpleNamespace

import httpx
import pytest
from sqlalchemy.pool import StaticPool
from sqlmodel import SQLModel, Session, create_engine

from app.config import get_settings
from app.models.thesis import NotificationDelivery
from app.services.notification_service import (
    TelegramNotifier,
    _macro_report,
    _message_for_assessment,
    _notification_channel,
    _notifier_for_channel,
    _should_requeue_sent_delivery,
    dispatch_pending_notifications,
)


def _compact_assessment(**overrides):
    values = {
        "ticker": "000660",
        "assessment_date": "2026-08-11",
        "thesis_version": 1,
        "status": "no_material_change",
        "business_thesis_change": "no_material_change",
        "score": 0,
        "confidence": 0.8,
        "summary": "변화 없음",
        "new_buyer_view": "확인",
        "holder_view": "확인",
        "price_view": "지지구간 위 · 확인가 아래",
        "risk_level": "normal",
        "structural_risk_level": "elevated",
        "assessment_state": "final",
        "market_session": "closed",
        "evidence": "[]",
        "confirmed_facts": "[]",
        "background_confirmed_facts": "[]",
        "inferred_implications": "[]",
        "unknowns": "[]",
        "confirmed_warnings": "[]",
        "new_warnings": "[]",
        "open_warnings": '["유상증자 이후 희석 효과 확인 필요"]',
        "open_confirmed_warnings": '["유상증자 이후 희석 효과 확인 필요"]',
        "persistent_watch_risks": '["HBM4 수율", "CAPEX 대비 FCF", "HBM ASP", "후순위 위험"]',
        "warning_states": "[]",
        "watch_items": "[]",
        "earnings_estimate_impact": "unchanged",
        "market_expectation_assessment": "{}",
        "price_context": json.dumps(
            {
                "decision": {
                    "current_price": 1_425_000,
                    "currency": "KRW",
                    "price_basis": "close",
                    "current_position": "지지구간 위 · 확인가 아래",
                    "new_observer_checks": [
                        {"label": "지지", "price_low": 1_397_000, "price_high": 1_420_000},
                        {"label": "상향 확인", "price": 1_550_000},
                    ],
                    "holder_checks": [{"label": "재점검", "price": 1_320_000}],
                }
            },
            ensure_ascii=False,
        ),
        "new_buyer_price_view": "중복 설명",
        "holder_price_view": "중복 설명",
        "valuation_context": '{"impact":"neutral","summary":"신규 근거 없음"}',
        "valuation_snapshot": json.dumps(
            {
                "current_price": 1_425_000,
                "currency": "KRW",
                "trailing_pe": 13.5,
                "trailing_pe_status": "value",
                "ttm_eps": 105_555.56,
                "price_to_book": 6.1,
                "price_to_book_status": "value",
                "bvps": 233_606.56,
                "forward_pe": 11.8,
                "forward_pe_status": "value",
                "forward_eps": 120_762.71,
                "forward_price_to_book_status": "unavailable",
                "valuation_relative_position": "premium",
                "valuation_relative_position_reason": "PBR이 과거 범위 상단입니다.",
                "historical_pe_statistics": {"historical_median": 10.8, "current_percentile": 62, "observation_count": 100},
                "historical_pb_statistics": {"historical_median": 1.7, "current_percentile": 92, "observation_count": 100},
                "consensus_status": "unavailable",
                "data_coverage": {
                    "price_quality": "fresh",
                    "event_quality": "fresh",
                    "financial_quality": "full",
                    "full_financial_freshness": "current",
                    "preliminary_financial_freshness": "current",
                    "consensus_quality": "unavailable",
                    "historical_valuation_quality": "high",
                    "forward_valuation_quality": "partial",
                    "reason_codes": [],
                },
            },
            ensure_ascii=False,
        ),
        "thesis_snapshot": '{"base_thesis":"HBM4 수익성과 FCF 전환이 핵심입니다."}',
    }
    values.update(overrides)
    return SimpleNamespace(**values)


def test_compact_user_report_hides_internal_metadata_and_empty_sections() -> None:
    message = _message_for_assessment(_compact_assessment())

    for hidden in (
        "정식 재무 기준:",
        "정식 재무 공시일:",
        "잠정실적 공시일:",
        "TTM 기준:",
        "PER 분모:",
        "PBR 분모:",
        "cycle_adjusted",
        "FY1 common equity roll-forward",
        "provider 없음",
        "Consensus: 자료 없음",
        "가격 fresh",
        "정식 재무 full/current",
        "현재 상태: closed",
        "이익 추정치 영향: unchanged",
        "오늘 충족된 조건: 없음",
        "🚨 오늘 새 경고",
    ):
        assert hidden not in message
    assert "투자 논리: 유지 · 오늘 중요한 신규 변화 없음" in message
    assert "⚠️ 기존 경고" in message
    assert "📐 Valuation" in message
    assert "PER = 현재가 ÷ TTM EPS = 1,425,000원 ÷ 105,555.56원 = 13.5배" in message
    assert "fPBR" not in message
    assert "⚠️ 데이터 주의" not in message


def test_korean_supply_section_is_between_price_and_valuation() -> None:
    assessment = _compact_assessment()
    price_context = json.loads(assessment.price_context)
    price_context["supply"] = {
        "available": True,
        "as_of_date": "2026-08-12",
        "foreign_net_buy_qty": -153_000,
        "institution_net_buy_qty": 205_000,
        "individual_net_buy_qty": 0,
        "confidence": "high",
        "validation_status": "validated",
    }
    assessment.price_context = json.dumps(price_context)

    message = _message_for_assessment(assessment)

    assert message.index("💰 가격") < message.index("📊 수급") < message.index("📐 Valuation")


def test_us_report_omits_supply_section() -> None:
    assessment = _compact_assessment(ticker="GOOGL")
    price_context = json.loads(assessment.price_context)
    price_context["supply"] = {
        "available": True,
        "as_of_date": "2026-08-11",
        "foreign_net_buy_qty": 10,
    }
    assessment.price_context = json.dumps(price_context)

    assert "📊 수급" not in _message_for_assessment(assessment)


def test_provider_only_forward_multiple_is_not_reverse_engineered() -> None:
    assessment = _compact_assessment()
    snapshot = json.loads(assessment.valuation_snapshot)
    snapshot["forward_eps"] = None
    snapshot["forward_pe"] = 19.3
    snapshot["forward_pe_status"] = "value"
    assessment.valuation_snapshot = json.dumps(snapshot)

    message = _message_for_assessment(assessment)

    assert "fPER: 19.3배" in message
    assert "현재가 ÷ 예상 EPS" not in message


def test_data_caution_only_renders_for_material_quality_problem() -> None:
    normal = _compact_assessment()
    assert "⚠️ 데이터 주의" not in _message_for_assessment(normal)

    snapshot = json.loads(normal.valuation_snapshot)
    snapshot["consensus_status"] = "conflicting"
    snapshot["consensus_disagreement"] = True
    normal.valuation_snapshot = json.dumps(snapshot)
    assert "⚠️ 데이터 주의" in _message_for_assessment(normal)


def test_neutral_valuation_delta_is_hidden_but_relative_position_remains() -> None:
    message = _message_for_assessment(_compact_assessment())

    assert "현재 Valuation:\n부담 구간" in message
    assert "Valuation: 중립" not in message
    assert "오늘 Valuation 변화" not in message


def test_non_neutral_valuation_delta_uses_change_label() -> None:
    assessment = _compact_assessment(
        valuation_context=json.dumps(
            {"impact": "compression", "summary": "할인율 부담이 높아졌습니다."},
            ensure_ascii=False,
        )
    )

    message = _message_for_assessment(assessment)

    assert "현재 Valuation:\n부담 구간" in message
    assert "오늘 Valuation 변화: 압축" in message
    assert "오늘 Valuation 영향" not in message


def test_basis_conflict_renders_judgment_hold_and_natural_caution() -> None:
    assessment = _compact_assessment()
    snapshot = json.loads(assessment.valuation_snapshot)
    snapshot.update(
        {
            "trailing_pe": None,
            "trailing_pe_status": "conflict",
            "trailing_pe_basis_conflict": True,
        }
    )
    assessment.valuation_snapshot = json.dumps(snapshot, ensure_ascii=False)

    message = _message_for_assessment(assessment)

    assert "PER: 판단 보류" in message
    assert "PER 계산의 이익 기준이 서로 충돌" in message
    assert "basis_conflict" not in message


def test_preliminary_period_mapping_failure_has_specific_caution() -> None:
    assessment = _compact_assessment()
    snapshot = json.loads(assessment.valuation_snapshot)
    snapshot["data_coverage"]["preliminary_financial_quality"] = "validation_failed"
    snapshot["data_coverage"]["reason_codes"] = [
        "preliminary_validation_failed",
        "preliminary_period_mapping_failed",
    ]
    assessment.valuation_snapshot = json.dumps(snapshot, ensure_ascii=False)

    message = _message_for_assessment(assessment)

    assert "최근 잠정실적의 기간 매핑을 검증하지 못해" in message
    assert "잠정실적 숫자 검증이 완료되지 않아" not in message


def test_assessment_notification_uses_investment_rationale_label() -> None:
    assessment = SimpleNamespace(
        ticker="000660",
        assessment_date="2026-08-07",
        thesis_version=1,
        status="strengthened",
        score=40,
        confidence=0.8,
        summary="새 근거가 현재 투자 논리를 강화했습니다.",
        new_buyer_view="가격을 확인합니다.",
        holder_view="근거를 확인하며 보유 논리를 유지합니다.",
        price_view="가격 범위 중간입니다.",
        risk_level="watch",
        evidence="[]",
        price_context="{}",
        valuation_context=json.dumps(
            {
                "impact": "compression",
                "summary": "새 근거가 멀티플 압축 조건과 연결됩니다.",
            },
            ensure_ascii=False,
        ),
        thesis_snapshot='{"base_thesis":"HBM 수요가 이익을 지지합니다."}',
    )

    message = _message_for_assessment(assessment)

    assert message.startswith("🏢 000660(000660)")
    assert "🎯 핵심" in message
    assert "💰 가격" in message
    assert "📐 Valuation" in message
    assert "fPBR" not in message
    assert "Thesis" not in message


def test_krx_provisional_message_names_korean_market() -> None:
    assessment = SimpleNamespace(
        ticker="005930",
        assessment_date="2026-08-11",
        thesis_version=1,
        status="no_material_change",
        business_thesis_change="no_material_change",
        confidence=0.8,
        score=0,
        summary="변화 없음",
        new_buyer_view="확인",
        holder_view="확인",
        price_view="장중",
        risk_level="normal",
        structural_risk_level="normal",
        assessment_state="provisional",
        market_session="open",
        evidence="[]",
        price_context="{}",
        valuation_context='{"impact":"neutral"}',
        valuation_snapshot="{}",
        thesis_snapshot='{"base_thesis":"반도체 이익을 점검합니다."}',
    )

    message = _message_for_assessment(assessment)

    assert "현재 장중 데이터로 가격 판단은 잠정입니다." in message
    assert "현재 상태: open" not in message


def test_morning_delivery_requeues_only_messages_sent_before_cutoff() -> None:
    cutoff = datetime(2026, 8, 10, 22, 45, tzinfo=timezone.utc)
    delivery = NotificationDelivery(
        ticker="__DAILY_DIGEST__",
        assessment_date=date(2026, 8, 11),
        channel="telegram",
        status="sent",
        sent_at=datetime(2026, 8, 10, 17, 0),
    )

    assert _should_requeue_sent_delivery(delivery, cutoff) is True

    delivery.sent_at = datetime(2026, 8, 10, 22, 50)
    assert _should_requeue_sent_delivery(delivery, cutoff) is False


def test_macro_report_explains_axes_confidence_and_friendly_series_names() -> None:
    briefing = SimpleNamespace(
        briefing_date="2030-01-02",
        as_of="2030-01-02T08:00:00+09:00",
        headline="mixed",
        market_summary=json.dumps(
            {
                "items": ["S&P +0.4%", "Nasdaq +0.8%", "VIX -4.2%"],
                "observations": [
                    {"series_code": "SPY", "change_pct": 0.4},
                    {"series_code": "QQQ", "change_pct": 0.8},
                    {"series_code": "SOXX", "change_pct": 0.7},
                    {"series_code": "VIXCLS", "change_pct": -4.2},
                    {"series_code": "DFII10", "change_value": 0.02},
                ],
            },
            ensure_ascii=False,
        ),
        regime_summary=json.dumps(
            {
                "label": "mixed",
                "summary": "성장 +0, 물가 +0, 유동성 +0, 금융여건 +0, 위험선호 +1, 이익 +0",
                "confidence": 0.9,
            },
            ensure_ascii=False,
        ),
        macro_theses=json.dumps(
            [
                {
                    "thesis_key": "us_soft_landing_disinflation",
                    "title": "미국 연착륙과 점진적 디스인플레이션",
                    "status": "strengthening",
                    "confidence": 0.85,
                }
            ],
            ensure_ascii=False,
        ),
        ticker_impacts="[]",
        today_calendar="[]",
        data_quality=json.dumps(
            [
                {
                    "series_code": "DTWEXBGS",
                    "quality_status": "stale",
                    "observed_at": "2029-12-20",
                }
            ],
            ensure_ascii=False,
        ),
    )

    report, _context = _macro_report(briefing)

    assert "6축 점수" not in report
    assert "위험선호 +1" not in report
    assert "🧭 현재 시장 상황" in report
    assert "• 위험선호:" in report
    assert "성장 급락과 물가 재가속" in report
    assert "미 달러지수(광의)(DTWEXBGS)" in report
    assert "당일 방향 판단에는 사용하지 않습니다" in report


def test_notification_channel_defaults_to_telegram(monkeypatch) -> None:
    monkeypatch.delenv("NOTIFICATION_CHANNEL", raising=False)
    get_settings.cache_clear()
    try:
        assert _notification_channel() == "telegram"
    finally:
        get_settings.cache_clear()


def test_notification_channel_accepts_only_telegram(monkeypatch) -> None:
    monkeypatch.setenv("NOTIFICATION_CHANNEL", "telegram")
    get_settings.cache_clear()
    assert _notification_channel() == "telegram"

    monkeypatch.setenv("NOTIFICATION_CHANNEL", "kakao_self")
    get_settings.cache_clear()
    try:
        with pytest.raises(RuntimeError, match="Unsupported notification channel"):
            _notification_channel()
    finally:
        monkeypatch.setenv("NOTIFICATION_CHANNEL", "telegram")
        get_settings.cache_clear()


def test_notifier_factory_supports_telegram_only() -> None:
    assert isinstance(_notifier_for_channel("telegram"), TelegramNotifier)
    with pytest.raises(RuntimeError, match="Unsupported notification channel"):
        _notifier_for_channel("kakao_self")


def test_notification_delivery_defaults_to_telegram() -> None:
    delivery = NotificationDelivery(
        ticker="DEFAULT-CHANNEL",
        assessment_date=date(2045, 1, 1),
        payload="{}",
    )

    assert delivery.channel == "telegram"


@pytest.mark.anyio
async def test_telegram_dispatch_ignores_legacy_channel_rows() -> None:
    class RecordingNotifier:
        def __init__(self) -> None:
            self.payloads: list[dict[str, object]] = []

        async def send(self, payload: dict[str, object]) -> str:
            self.payloads.append(payload)
            return "sent"

    isolated_engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    SQLModel.metadata.create_all(isolated_engine)
    with Session(isolated_engine) as session:
        telegram = NotificationDelivery(
            ticker="TELEGRAM-PENDING",
            assessment_date=date(2045, 1, 2),
            channel="telegram",
            status="pending",
            payload=json.dumps({"text": "Telegram"}),
        )
        legacy = NotificationDelivery(
            ticker="LEGACY-PENDING",
            assessment_date=date(2045, 1, 2),
            channel="kakao_self",
            status="pending",
            payload=json.dumps({"text": "Legacy"}),
        )
        session.add(telegram)
        session.add(legacy)
        session.commit()
        notifier = RecordingNotifier()

        await dispatch_pending_notifications(session, notifier=notifier)
        session.refresh(telegram)
        session.refresh(legacy)

        assert telegram.status == "sent"
        assert telegram.attempt_count == 1
        assert legacy.status == "pending"
        assert legacy.attempt_count == 0
        assert notifier.payloads == [{"text": "Telegram"}]


@pytest.mark.anyio
async def test_telegram_notifier_sends_generated_report_as_section_chunks() -> None:
    sent_chunks: list[str] = []

    class StubNarrativeGenerator:
        async def generate(self, context: dict[str, object], fallback: str) -> str:
            assert context == {"analysis_type": "macro"}
            assert fallback == "기본 분석"
            return "🌍 시장환경 점검\n\n" + "• 시장 변화와 투자 의미를 연결합니다. " * 25

    def handler(request: httpx.Request) -> httpx.Response:
        assert request.url.host == "api.telegram.org"
        assert request.url.path.endswith("/sendMessage")
        payload = json.loads(request.content)
        assert payload["chat_id"] == "135988"
        assert payload["disable_web_page_preview"] is True
        sent_chunks.append(payload["text"])
        return httpx.Response(200, json={"ok": True, "result": {"message_id": 1}})

    notifier = TelegramNotifier(
        transport=httpx.MockTransport(handler),
        narrative_generator=StubNarrativeGenerator(),
    )
    notifier.settings = notifier.settings.model_copy(
        update={
            "notification_dry_run": False,
            "telegram_bot_token": "bot-token",
            "telegram_chat_id": "135988",
            "telegram_message_max_chars": 300,
            "telegram_retry_base_seconds": 0,
        }
    )

    result = await notifier.send(
        {
            "text": "기본 분석",
            "presentation": "long_text",
            "use_llm": True,
            "analysis_context": {"analysis_type": "macro"},
        }
    )

    assert result == "sent"
    assert len(sent_chunks) >= 2
    assert all(len(chunk) <= 310 for chunk in sent_chunks)
    assert sent_chunks[0].startswith("[1/")


@pytest.mark.anyio
async def test_telegram_notifier_retries_temporary_server_error() -> None:
    calls = 0

    def handler(_request: httpx.Request) -> httpx.Response:
        nonlocal calls
        calls += 1
        if calls == 1:
            return httpx.Response(503, json={"ok": False, "description": "temporary"})
        return httpx.Response(200, json={"ok": True, "result": {"message_id": 2}})

    notifier = TelegramNotifier(transport=httpx.MockTransport(handler))
    notifier.settings = notifier.settings.model_copy(
        update={
            "notification_dry_run": False,
            "telegram_bot_token": "bot-token",
            "telegram_chat_id": "135988",
            "telegram_retry_attempts": 2,
            "telegram_retry_base_seconds": 0,
        }
    )

    assert await notifier.send({"text": "전송 테스트"}) == "sent"
    assert calls == 2
