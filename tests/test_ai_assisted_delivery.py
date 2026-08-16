import json
from datetime import date, datetime
from pathlib import Path
from zoneinfo import ZoneInfo

import pytest
from sqlalchemy.pool import StaticPool
from sqlmodel import SQLModel, Session, create_engine, select

import app.services.ai_assisted_delivery_service as delivery_service
from app.config import get_settings
from app.models.thesis import NotificationDelivery
from app.schemas.ai_review import AIMarketReview, AIStockReview
from app.services.ai_assisted_delivery_service import (
    _render_ai_market_message,
    _render_ai_stock_message,
    ai_assisted_pilot_active,
    deliver_validated_ai_review,
    dispatch_due_deterministic_fallbacks,
    hold_ai_assisted_pilot_session,
    record_ai_validation_rejection,
    retry_pending_ai_assisted_deliveries,
)
from app.services.notification_service import (
    AI_ASSISTED_PILOT_METADATA_KEY,
    dispatch_pending_notifications,
    queue_daily_digest_notification,
)


KST = ZoneInfo("Asia/Seoul")
RUN_DATE = date(2026, 8, 14)
PACKET_ID = "2026-08-14-kr-run-1-pilot"


class RecordingNotifier:
    def __init__(self, *, fail: bool = False) -> None:
        self.fail = fail
        self.payloads: list[dict[str, object]] = []

    async def send(self, payload: dict[str, object]) -> str:
        self.payloads.append(payload)
        if self.fail:
            raise RuntimeError("scripted outage")
        return "sent"


def _engine():
    value = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    SQLModel.metadata.create_all(value)
    return value


def _settings(monkeypatch, tmp_path: Path):
    settings = get_settings().model_copy(
        update={
            "data_dir": str(tmp_path),
            "notification_channel": "telegram",
            "notification_dry_run": False,
            "ai_review_mode": "shadow",
            "ai_review_pilot_enabled": True,
            "ai_review_pilot_target_success_days": 5,
            "ai_review_pilot_us_fallback_time": "08:40",
            "ai_review_pilot_kr_fallback_time": "17:10",
        }
    )
    monkeypatch.setattr(
        "app.services.ai_assisted_delivery_service.get_settings", lambda: settings
    )
    monkeypatch.setattr("app.services.notification_service.get_settings", lambda: settings)
    return settings


def _packet() -> dict[str, object]:
    return {
        "schema_version": "1",
        "output_schema_version": "4",
        "analysis_policy_version": "daily-review-v3.7",
        "knowledge": {"version": "3.0", "sha256": "knowledge-sha"},
        "chart_knowledge": {"version": "1.0", "sha256": "chart-knowledge-sha"},
        "packet_id": PACKET_ID,
        "market": "kr",
        "assessment_date": RUN_DATE.isoformat(),
        "market_context": {
            "portfolio_exposure_groups": [
                {
                    "group_key": "semiconductor",
                    "label": "반도체",
                    "tickers": ["PILOT"],
                }
            ]
        },
        "stocks": [{"ticker": "PILOT", "thesis_version": 1}],
    }


def _output() -> dict[str, object]:
    return {
        "schema_version": "4",
        "packet_id": PACKET_ID,
        "claim_id": "claim-1",
        "analysis_policy_version": "daily-review-v3.7",
        "knowledge_version": "3.0",
        "knowledge_sha256": "knowledge-sha",
        "chart_knowledge_version": "1.0",
        "chart_knowledge_sha256": "chart-knowledge-sha",
        "market": "kr",
        "assessment_date": RUN_DATE.isoformat(),
        "market_review": {
            "facts_used": [],
            "frameworks_used": ["macro_transmission"],
            "core_judgment": {"text": "검증된 시장 맥락은 혼재 상태입니다.", "fact_ids": []},
            "important_changes": [
                {"text": "시장 신호는 기업 펀더멘털과 분리해 봐야 합니다.", "fact_ids": []}
            ],
            "market_context": {"text": "시장 환경은 혼재 상태입니다.", "fact_ids": []},
            "market_assumptions": {"text": "추가 확정 근거를 기다립니다.", "fact_ids": []},
            "portfolio_transmission": [
                {
                    "portfolio_group": "semiconductor",
                    "text": "업종 가격 강도는 가격환경에 우호적이지만 실적 확인은 별개입니다.",
                    "fact_ids": ["market:sector:SOXX"],
                }
            ],
            "next_checks": [
                {
                    "text": "다음 세션에서 업종 상대강도의 지속 여부를 확인합니다.",
                    "fact_ids": ["market:sector:SOXX"],
                }
            ],
            "numeric_claims": [],
            "unknowns": ["다음 거래일 방향은 미확인입니다."],
        },
        "stock_reviews": [
            {
                "ticker": "PILOT",
                "thesis_version": 1,
                "ai_thesis_assessment": "weakened",
                "earnings_estimate_view": "unchanged",
                "valuation_view": "neutral",
                "facts_used": [],
                "frameworks_used": ["market_expectations"],
                "core_judgment": {"text": "공식 상태를 바꿀 확정 근거는 아직 부족합니다.", "fact_ids": []},
                "business_earnings": {"text": "추가 약화 여부는 다음 실적에서 확인해야 합니다.", "fact_ids": []},
                "price_positioning": {
                    "text": "현재 가격 신호는 사업 논리와 분리합니다.",
                    "new_observer_view": "기업의 질과 진입 가격을 나누어 봅니다.",
                    "holder_view": "가격 확인 조건을 계속 추적합니다.",
                    "fact_ids": []
                },
                "supply_analysis": {"text": "수급만으로 공식 상태를 바꾸지 않습니다.", "fact_ids": []},
                "valuation_analysis": {"text": "Valuation은 별도 판단 층위입니다.", "fact_ids": []},
                "numeric_claims": [],
                "unknowns": ["다음 분기 마진은 미확인입니다."],
                "priority_watch": ["확정된 경고와 실행 지표"],
                "next_checks": ["다음 분기 영업이익률"],
                "confidence": 0.8,
            }
        ],
    }


def _write_artifacts(tmp_path: Path, *, output: bool = True) -> None:
    inbox = tmp_path / "ai_review" / "inbox"
    outbox = tmp_path / "ai_review" / "outbox"
    inbox.mkdir(parents=True)
    outbox.mkdir(parents=True)
    (inbox / f"{PACKET_ID}.json").write_text(
        json.dumps(_packet(), ensure_ascii=False), encoding="utf-8"
    )
    if output:
        (outbox / f"{PACKET_ID}--daily-review-v3.7--knowledge.json").write_text(
            json.dumps(_output(), ensure_ascii=False), encoding="utf-8"
        )


def test_stock_renderer_preserves_validated_user_text_without_semantic_rewrite() -> None:
    review_value = _output()["stock_reviews"][0]
    review_value["business_earnings"]["text"] = (
        "앵커 투자자와 앵커 테넌트는 서로 다른 사업 요소입니다."
    )
    review_value["valuation_analysis"]["text"] = "업계 앵커 역할은 평가 기준과 다릅니다."
    review_value["priority_watch"] = ["앵커 고객 유지율"]
    review = AIStockReview.model_validate(review_value)

    rendered = _render_ai_stock_message(
        "🏢 Pilot Corp(PILOT)\n\n투자 논리: 유지",
        review,
        market="kr",
        pilot_day=1,
        target_days=5,
    )

    assert "앵커 투자자와 앵커 테넌트는 서로 다른 사업 요소입니다." in rendered
    assert "업계 앵커 역할은 평가 기준과 다릅니다." in rendered
    assert "• 앵커 고객 유지율" in rendered
    assert "기준 투자자" not in rendered
    assert "기준 테넌트" not in rendered


@pytest.mark.parametrize(
    ("market", "expected", "forbidden"),
    [
        ("kr", "📊 수급", "📊 거래량·포지셔닝"),
        ("us", "📊 거래량·포지셔닝", "📊 수급"),
    ],
)
def test_stock_renderer_uses_market_specific_positioning_heading(
    market: str,
    expected: str,
    forbidden: str,
) -> None:
    review = AIStockReview.model_validate(_output()["stock_reviews"][0])

    rendered = _render_ai_stock_message(
        "🏢 Pilot Corp(PILOT)\n\n투자 논리: 유지",
        review,
        market=market,
        pilot_day=1,
        target_days=5,
    )

    assert expected in rendered
    assert forbidden not in rendered


def _seed_deliveries(session: Session, *, status: str = "pending") -> None:
    session.add(
        NotificationDelivery(
            ticker="__DAILY_DIGEST_KR__",
            assessment_date=RUN_DATE,
            channel="telegram",
            status=status,
            payload=json.dumps(
                {
                    "text": (
                        "🇰🇷 한국 종목 장마감 점검 · 2026-08-14\n현재 환경: 혼합\n\n"
                        "⚠️ 데이터 주의\n• 광의 달러지수: stale"
                    ),
                    "type": "daily_monitoring_digest",
                    "market_scope": "kr",
                },
                ensure_ascii=False,
            ),
        )
    )
    session.add(
        NotificationDelivery(
            ticker="PILOT",
            assessment_date=RUN_DATE,
            channel="telegram",
            status=status,
            payload=json.dumps(
                {
                    "text": (
                        "🏢 Pilot Corp(PILOT)\n\n"
                        "투자 논리: 유지 · 오늘 중요한 신규 변화 없음\n\n"
                        "구조적 위험: 보통\n\n시장 기대: 균형\n\n"
                        "🎯 핵심\n기존 논리를 유지합니다.\n\n"
                        "💰 가격\n현재가: $100 · 2026-08-14 종가\n\n"
                        "📐 Valuation\n현재 Valuation: 판단 자료 부족\n"
                        "해석: 검증된 배수가 부족합니다."
                    ),
                    "type": "daily_stock_analysis",
                    "ticker": "PILOT",
                    "status": "no_material_change",
                },
                ensure_ascii=False,
            ),
        )
    )
    session.commit()


@pytest.mark.anyio
async def test_ai_pass_sends_only_one_ai_assisted_set(monkeypatch, tmp_path: Path) -> None:
    _settings(monkeypatch, tmp_path)
    _write_artifacts(tmp_path)
    notifier = RecordingNotifier()
    with Session(_engine()) as session:
        _seed_deliveries(session)
        held = hold_ai_assisted_pilot_session(session, PACKET_ID)
        await dispatch_pending_notifications(session, notifier=notifier)
        result = await deliver_validated_ai_review(
            session, PACKET_ID, notifier=notifier
        )
        duplicate = await deliver_validated_ai_review(
            session, PACKET_ID, notifier=notifier
        )
        deliveries = session.exec(select(NotificationDelivery)).all()

    assert held.status == "held"
    assert result.status == "sent"
    assert duplicate.status == "sent"
    assert len(notifier.payloads) == 2
    assert {item["type"] for item in notifier.payloads} == {
        "ai_assisted_pilot_market",
        "ai_assisted_pilot_stock",
    }
    stock = next(item for item in notifier.payloads if item["type"].endswith("stock"))
    stock_text = str(stock["text"])
    assert "투자 논리: 유지" in stock_text
    assert "AI 투자 논리: 약화" not in stock_text
    assert "🎯 핵심 판단" in stock_text
    assert "📈 사업·실적" in stock_text
    assert "💰 가격·포지셔닝" in stock_text
    assert "📊 수급" in stock_text
    assert "📐 Valuation" in stock_text
    assert "• 신규 관찰자:" in stock_text
    assert "• 보유자:" in stock_text
    assert "현재가: $100" not in stock_text
    assert "frameworks_used" not in stock_text
    assert "chart_state" not in stock_text
    assert "claim_id" not in stock_text
    assert "numeric_claims" not in stock_text
    market_message = next(
        item for item in notifier.payloads if item["type"].endswith("market")
    )
    market_text = str(market_message["text"])
    assert "🎯 오늘 시장 한 줄" in market_text
    assert "🧭 시장 구조" in market_text
    assert "🔗 모니터링 종목에 미치는 영향" in market_text
    assert "반도체:" in market_text
    assert "📌 다음 확인" in market_text
    assert "시장 가정" not in market_text
    assert "추가 확정 근거를 기다립니다" not in market_text
    assert market_text.count("⚠️ 데이터 주의") == 1
    assert "stale" not in market_text
    assert all(item.status == "sent" for item in deliveries)
    archive = tmp_path / "ai_review" / "pilot" / "history" / "2026" / "08" / PACKET_ID
    assert (archive / "deterministic-messages.json").exists()
    assert (archive / "ai-assisted-messages.json").exists()
    assert (archive / "delivery-result.json").exists()
    assert (archive / "chart-context.json").exists()
    assert (archive / "chart-transition.json").exists()
    assert (archive / "quantitative-grounding-report.json").exists()
    assert (archive / "market-context.json").exists()
    assert (archive / "market-review.json").exists()
    assert (archive / "market-numeric-claims.json").exists()
    assert (archive / "portfolio-transmission.json").exists()
    completion = json.loads((archive / "archive-complete.json").read_text())
    assert completion["packet_id"] == PACKET_ID
    assert completion["validator_status"] == "passed"
    assert completion["delivery_status"] == "sent"
    assert {item["filename"] for item in completion["artifacts"]} == set(
        delivery_service.AI_SUCCESS_REQUIRED_ARTIFACTS
    )
    assert len(json.loads((archive / "deterministic-messages.json").read_text())["messages"]) == 2
    assert len(json.loads((archive / "ai-assisted-messages.json").read_text())["messages"]) == 2


@pytest.mark.anyio
@pytest.mark.parametrize("failed_filename", ["delivery-result.json", "archive-complete.json"])
async def test_ai_pilot_count_waits_for_archive_completion_and_recovers_without_resend(
    monkeypatch,
    tmp_path: Path,
    failed_filename: str,
) -> None:
    _settings(monkeypatch, tmp_path)
    _write_artifacts(tmp_path)
    sent = RecordingNotifier()
    recovery = RecordingNotifier()
    original_atomic_json = delivery_service._atomic_json
    failed = False

    def fail_once(path: Path, payload: object) -> None:
        nonlocal failed
        if path.name == failed_filename and not failed:
            failed = True
            raise OSError(f"scripted {failed_filename} failure")
        original_atomic_json(path, payload)

    monkeypatch.setattr(delivery_service, "_atomic_json", fail_once)
    with Session(_engine()) as session:
        _seed_deliveries(session)
        hold_ai_assisted_pilot_session(session, PACKET_ID)
        with pytest.raises(OSError, match="scripted"):
            await deliver_validated_ai_review(session, PACKET_ID, notifier=sent)

        state_path = tmp_path / "ai_review" / "pilot" / "state-v3.json"
        if state_path.exists():
            state = json.loads(state_path.read_text())
            assert state["markets"]["kr"]["successful_packet_ids"] == []

        monkeypatch.setattr(delivery_service, "_atomic_json", original_atomic_json)
        recovered = await retry_pending_ai_assisted_deliveries(
            session,
            market="kr",
            run_date=RUN_DATE,
            now=datetime(2026, 8, 14, 16, 25, tzinfo=KST),
            notifier=recovery,
        )
        duplicate = await retry_pending_ai_assisted_deliveries(
            session,
            market="kr",
            run_date=RUN_DATE,
            now=datetime(2026, 8, 14, 16, 30, tzinfo=KST),
            notifier=recovery,
        )

    assert len(sent.payloads) == 2
    assert recovery.payloads == []
    assert recovered[-1].status == "sent"
    assert duplicate[-1].status == "no_pending_ai_delivery"
    state = json.loads(state_path.read_text())
    assert state["markets"]["kr"]["successful_packet_ids"] == [PACKET_ID]
    assert state["markets"]["kr"]["successful_assessment_dates"] == [
        RUN_DATE.isoformat()
    ]
    archive = tmp_path / "ai_review" / "pilot" / "history" / "2026" / "08" / PACKET_ID
    assert (archive / "archive-complete.json").exists()
    retry = json.loads((archive / "delivery-retry-state.json").read_text())
    assert retry["archive_completion_recovery"] is True
    assert retry["telegram_resent"] is False
    assert retry["analysis_rerun"] is False
    assert retry["renderer_rerun"] is False


@pytest.mark.anyio
async def test_missing_required_archive_after_delivery_does_not_count(
    monkeypatch,
    tmp_path: Path,
) -> None:
    _settings(monkeypatch, tmp_path)
    _write_artifacts(tmp_path)
    sent = RecordingNotifier()
    recovery = RecordingNotifier()
    original_dispatch = delivery_service.dispatch_pending_notifications

    async def dispatch_then_remove_archive(*args, **kwargs) -> None:
        await original_dispatch(*args, **kwargs)
        archive = (
            tmp_path
            / "ai_review"
            / "pilot"
            / "history"
            / "2026"
            / "08"
            / PACKET_ID
            / "ai-review.json"
        )
        archive.unlink()

    monkeypatch.setattr(
        delivery_service,
        "dispatch_pending_notifications",
        dispatch_then_remove_archive,
    )
    with Session(_engine()) as session:
        _seed_deliveries(session)
        hold_ai_assisted_pilot_session(session, PACKET_ID)
        with pytest.raises(FileNotFoundError):
            await deliver_validated_ai_review(session, PACKET_ID, notifier=sent)

        state_path = tmp_path / "ai_review" / "pilot" / "state-v3.json"
        assert not state_path.exists()
        monkeypatch.setattr(
            delivery_service,
            "dispatch_pending_notifications",
            original_dispatch,
        )
        recovered = await retry_pending_ai_assisted_deliveries(
            session,
            market="kr",
            run_date=RUN_DATE,
            notifier=recovery,
        )

    assert recovered[-1].status == "sent"
    assert len(sent.payloads) == 2
    assert recovery.payloads == []
    state = json.loads(state_path.read_text())
    assert state["markets"]["kr"]["successful_packet_ids"] == [PACKET_ID]


@pytest.mark.anyio
async def test_old_policy_output_is_not_eligible_for_pilot_v2_delivery(
    monkeypatch, tmp_path: Path
) -> None:
    _settings(monkeypatch, tmp_path)
    _write_artifacts(tmp_path, output=False)
    old_output = _output()
    old_output["schema_version"] = "3"
    old_output["analysis_policy_version"] = "daily-review-v3.5"
    outbox = tmp_path / "ai_review" / "outbox"
    (outbox / f"{PACKET_ID}--daily-review-v3.5--knowledge.json").write_text(
        json.dumps(old_output, ensure_ascii=False), encoding="utf-8"
    )
    notifier = RecordingNotifier()
    with Session(_engine()) as session:
        _seed_deliveries(session)
        hold_ai_assisted_pilot_session(session, PACKET_ID)
        result = await deliver_validated_ai_review(
            session, PACKET_ID, notifier=notifier
        )

    assert result.status == "not_ready"
    assert notifier.payloads == []


@pytest.mark.anyio
async def test_fallback_sends_only_deterministic_and_late_ai_is_archive_only(
    monkeypatch, tmp_path: Path
) -> None:
    _settings(monkeypatch, tmp_path)
    _write_artifacts(tmp_path, output=False)
    fallback_notifier = RecordingNotifier()
    late_notifier = RecordingNotifier()
    with Session(_engine()) as session:
        _seed_deliveries(session)
        hold_ai_assisted_pilot_session(session, PACKET_ID)
        results = await dispatch_due_deterministic_fallbacks(
            session,
            market="kr",
            run_date=RUN_DATE,
            now=datetime(2026, 8, 14, 17, 10, tzinfo=KST),
            notifier=fallback_notifier,
        )
        outbox = tmp_path / "ai_review" / "outbox"
        (outbox / f"{PACKET_ID}--daily-review-v3.7--knowledge.json").write_text(
            json.dumps(_output(), ensure_ascii=False), encoding="utf-8"
        )
        late = await deliver_validated_ai_review(
            session, PACKET_ID, notifier=late_notifier
        )

    assert results[-1].delivery_mode == "deterministic_fallback"
    assert results[-1].status == "sent"
    assert len(fallback_notifier.payloads) == 2
    assert all(not str(item["type"]).startswith("ai_assisted") for item in fallback_notifier.payloads)
    assert late.status == "archive_only"
    assert late_notifier.payloads == []


@pytest.mark.anyio
async def test_validation_reject_preserves_deadline_fallback_and_does_not_count_pilot(
    monkeypatch,
    tmp_path: Path,
) -> None:
    _settings(monkeypatch, tmp_path)
    _write_artifacts(tmp_path, output=False)
    notifier = RecordingNotifier()
    with Session(_engine()) as session:
        _seed_deliveries(session)
        hold_ai_assisted_pilot_session(session, PACKET_ID)
        recorded = record_ai_validation_rejection(
            session,
            PACKET_ID,
            errors=("PILOT:numbers_without_provenance:valuation_analysis.text:0.59",),
            rejected_at=datetime(2026, 8, 14, 16, 20, tzinfo=KST),
        )
        held = session.exec(
            select(NotificationDelivery).where(NotificationDelivery.ticker == "PILOT")
        ).one()
        metadata = json.loads(held.payload)[AI_ASSISTED_PILOT_METADATA_KEY]
        results = await dispatch_due_deterministic_fallbacks(
            session,
            market="kr",
            run_date=RUN_DATE,
            now=datetime(2026, 8, 14, 17, 10, tzinfo=KST),
            notifier=notifier,
        )

    assert recorded.status == "fallback_preserved"
    assert metadata["state"] == "held"
    assert metadata["fallback_eligible"] is True
    assert metadata["ai_validation_state"] == "rejected"
    assert results[-1].delivery_mode == "deterministic_fallback"
    assert results[-1].status == "sent"
    assert len(notifier.payloads) == 2
    state = json.loads((tmp_path / "ai_review" / "pilot" / "state-v3.json").read_text())
    assert state["markets"]["kr"]["successful_packet_ids"] == []


@pytest.mark.anyio
async def test_fallback_network_failure_retries_same_persisted_payload(
    monkeypatch,
    tmp_path: Path,
) -> None:
    _settings(monkeypatch, tmp_path)
    _write_artifacts(tmp_path, output=False)
    failed = RecordingNotifier(fail=True)
    recovered = RecordingNotifier()
    with Session(_engine()) as session:
        _seed_deliveries(session)
        hold_ai_assisted_pilot_session(session, PACKET_ID)
        first = await dispatch_due_deterministic_fallbacks(
            session,
            market="kr",
            run_date=RUN_DATE,
            now=datetime(2026, 8, 14, 17, 10, tzinfo=KST),
            notifier=failed,
        )
        second = await dispatch_due_deterministic_fallbacks(
            session,
            market="kr",
            run_date=RUN_DATE,
            now=datetime(2026, 8, 14, 17, 15, tzinfo=KST),
            notifier=recovered,
        )

    assert first[-1].status == "pending"
    assert first[-1].delivery_mode == "deterministic_fallback"
    assert second[-1].status == "sent"
    assert second[-1].delivery_mode == "deterministic_fallback"
    assert [item["text"] for item in recovered.payloads] == [
        item["text"] for item in failed.payloads
    ]
    retry = json.loads(
        (
            tmp_path
            / "ai_review"
            / "pilot"
            / "history"
            / "2026"
            / "08"
            / PACKET_ID
            / "fallback-delivery-retry-state.json"
        ).read_text()
    )
    assert retry["retry_count"] == 1
    assert retry["analysis_rerun"] is False
    assert retry["packet_regenerated"] is False
    assert retry["payload_reformatted"] is False


@pytest.mark.anyio
async def test_fallback_network_retry_is_bounded(
    monkeypatch,
    tmp_path: Path,
) -> None:
    _settings(monkeypatch, tmp_path)
    _write_artifacts(tmp_path, output=False)
    failed = RecordingNotifier(fail=True)
    recovered = RecordingNotifier()
    with Session(_engine()) as session:
        _seed_deliveries(session)
        hold_ai_assisted_pilot_session(session, PACKET_ID)
        initial = await dispatch_due_deterministic_fallbacks(
            session,
            market="kr",
            run_date=RUN_DATE,
            now=datetime(2026, 8, 14, 17, 10, tzinfo=KST),
            notifier=failed,
        )
        retries = [
            await dispatch_due_deterministic_fallbacks(
                session,
                market="kr",
                run_date=RUN_DATE,
                now=datetime(2026, 8, 14, 17, minute, tzinfo=KST),
                notifier=failed,
            )
            for minute in (15, 20, 25)
        ]
        exhausted = await dispatch_due_deterministic_fallbacks(
            session,
            market="kr",
            run_date=RUN_DATE,
            now=datetime(2026, 8, 14, 17, 30, tzinfo=KST),
            notifier=recovered,
        )

    assert initial[-1].status == "pending"
    assert [result[-1].status for result in retries] == ["pending"] * 3
    assert exhausted[-1].status == "retry_exhausted"
    assert exhausted[-1].reason == "persisted_delivery_retry_limit_reached"
    assert recovered.payloads == []
    retry = json.loads(
        (
            tmp_path
            / "ai_review"
            / "pilot"
            / "history"
            / "2026"
            / "08"
            / PACKET_ID
            / "fallback-delivery-retry-state.json"
        ).read_text()
    )
    assert retry["retry_count"] == 3


@pytest.mark.anyio
async def test_ai_delivery_failure_retries_ai_without_deterministic_mix(
    monkeypatch, tmp_path: Path
) -> None:
    _settings(monkeypatch, tmp_path)
    _write_artifacts(tmp_path)
    failed = RecordingNotifier(fail=True)
    recovered = RecordingNotifier()
    with Session(_engine()) as session:
        _seed_deliveries(session)
        hold_ai_assisted_pilot_session(session, PACKET_ID)
        first = await deliver_validated_ai_review(session, PACKET_ID, notifier=failed)
        state_path = tmp_path / "ai_review" / "pilot" / "state-v3.json"
        assert not state_path.exists()
        fallback = await dispatch_due_deterministic_fallbacks(
            session,
            market="kr",
            run_date=RUN_DATE,
            now=datetime(2026, 8, 14, 17, 10, tzinfo=KST),
            notifier=recovered,
        )
        second = await deliver_validated_ai_review(
            session, PACKET_ID, notifier=recovered
        )

    assert first.status == "pending"
    assert fallback[-1].status == "sent"
    assert fallback[-1].delivery_mode == "ai_assisted"
    assert second.status == "sent"
    assert len(recovered.payloads) == 2
    assert all(str(item["type"]).startswith("ai_assisted") for item in recovered.payloads)


@pytest.mark.anyio
async def test_persisted_delivery_retry_reuses_final_text_without_reanalysis(
    monkeypatch,
    tmp_path: Path,
) -> None:
    _settings(monkeypatch, tmp_path)
    _write_artifacts(tmp_path)
    failed = RecordingNotifier(fail=True)
    recovered = RecordingNotifier()
    with Session(_engine()) as session:
        _seed_deliveries(session)
        hold_ai_assisted_pilot_session(session, PACKET_ID)
        first = await deliver_validated_ai_review(session, PACKET_ID, notifier=failed)
        retries = await retry_pending_ai_assisted_deliveries(
            session,
            market="kr",
            run_date=RUN_DATE,
            now=datetime(2026, 8, 14, 16, 22, tzinfo=KST),
            notifier=recovered,
        )

    assert first.status == "pending"
    assert retries[-1].status == "sent"
    assert [item["text"] for item in recovered.payloads] == [
        item["text"] for item in failed.payloads
    ]
    retry_state = (
        tmp_path
        / "ai_review"
        / "pilot"
        / "history"
        / "2026"
        / "08"
        / PACKET_ID
        / "delivery-retry-state.json"
    )
    payload = json.loads(retry_state.read_text())
    assert payload["retry_count"] == 1
    assert payload["analysis_rerun"] is False
    assert payload["packet_regenerated"] is False


@pytest.mark.anyio
async def test_explicit_duplicate_exception_allows_sent_session_once(
    monkeypatch, tmp_path: Path
) -> None:
    _settings(monkeypatch, tmp_path)
    _write_artifacts(tmp_path)
    notifier = RecordingNotifier()
    with Session(_engine()) as session:
        _seed_deliveries(session, status="sent")
        blocked = await deliver_validated_ai_review(session, PACKET_ID, notifier=notifier)
        allowed = await deliver_validated_ai_review(
            session,
            PACKET_ID,
            notifier=notifier,
            allow_duplicate=True,
        )
        rerun = await deliver_validated_ai_review(
            session,
            PACKET_ID,
            notifier=notifier,
            allow_duplicate=True,
        )

    assert blocked.status == "archive_only"
    assert allowed.status == "sent"
    assert rerun.status == "sent"
    assert len(notifier.payloads) == 2


@pytest.mark.anyio
async def test_runtime_quality_gate_rejects_ai_and_preserves_single_fallback(
    monkeypatch,
    tmp_path: Path,
) -> None:
    _settings(monkeypatch, tmp_path)
    _write_artifacts(tmp_path)
    output_path = next((tmp_path / "ai_review" / "outbox").glob("*.json"))
    output = json.loads(output_path.read_text(encoding="utf-8"))
    stock = output["stock_reviews"][0]
    stock["price_positioning"]["holder_view"] = stock["price_positioning"][
        "new_observer_view"
    ]
    output_path.write_text(json.dumps(output, ensure_ascii=False), encoding="utf-8")
    ai_notifier = RecordingNotifier()
    fallback_notifier = RecordingNotifier()

    with Session(_engine()) as session:
        _seed_deliveries(session)
        hold_ai_assisted_pilot_session(session, PACKET_ID)
        rejected = await deliver_validated_ai_review(
            session, PACKET_ID, notifier=ai_notifier
        )
        fallback = await dispatch_due_deterministic_fallbacks(
            session,
            market="kr",
            run_date=RUN_DATE,
            now=datetime(2026, 8, 14, 17, 10, tzinfo=KST),
            notifier=fallback_notifier,
        )

    assert rejected.status == "quality_rejected"
    assert ai_notifier.payloads == []
    assert fallback[-1].status == "sent"
    assert len(fallback_notifier.payloads) == 2
    state = json.loads(
        (tmp_path / "ai_review" / "pilot" / "state-v3.json").read_text()
    )
    assert state["markets"]["kr"]["successful_packet_ids"] == []


@pytest.mark.anyio
async def test_persisted_retry_rejects_payload_tampering_against_quality_receipt(
    monkeypatch,
    tmp_path: Path,
) -> None:
    _settings(monkeypatch, tmp_path)
    _write_artifacts(tmp_path)
    failed = RecordingNotifier(fail=True)
    retry_notifier = RecordingNotifier()

    with Session(_engine()) as session:
        _seed_deliveries(session)
        hold_ai_assisted_pilot_session(session, PACKET_ID)
        first = await deliver_validated_ai_review(session, PACKET_ID, notifier=failed)
        delivery = session.exec(
            select(NotificationDelivery).where(NotificationDelivery.ticker == "PILOT")
        ).one()
        payload = json.loads(delivery.payload)
        payload["text"] = f"{payload['text']} tampered"
        delivery.payload = json.dumps(payload, ensure_ascii=False)
        session.add(delivery)
        session.commit()
        retry = await deliver_validated_ai_review(
            session, PACKET_ID, notifier=retry_notifier
        )

    assert first.status == "pending"
    assert retry.status == "quality_receipt_invalid"
    assert retry_notifier.payloads == []


def test_pilot_v3_stops_market_after_five_successful_packets(
    monkeypatch, tmp_path: Path
) -> None:
    _settings(monkeypatch, tmp_path)
    state = {
        "schema_version": "1",
        "pilot_version": "ai-assisted-pilot-v3",
        "markets": {
            "us": {"successful_packet_ids": [], "successful_assessment_dates": []},
            "kr": {
                "successful_packet_ids": [f"packet-{index}" for index in range(5)],
                "successful_assessment_dates": [f"2026-08-{index + 1:02d}" for index in range(5)],
            },
        },
        "sessions": {},
    }
    path = tmp_path / "ai_review" / "pilot" / "state-v3.json"
    path.parent.mkdir(parents=True)
    path.write_text(json.dumps(state), encoding="utf-8")

    assert ai_assisted_pilot_active("kr") is False
    assert ai_assisted_pilot_active("us") is True


def test_us_market_renderer_v3_integrates_night_futures_without_duplication() -> None:
    raw_review = _output()["market_review"]
    raw_review["facts_used"].append("market:night_futures:1")
    raw_review["important_changes"].append(
        {
            "text": "KOSPI200 야간선물은 431.25pt로 한국 개장 전 약세 신호입니다.",
            "fact_ids": ["market:night_futures:1"],
        }
    )
    review = AIMarketReview.model_validate(raw_review)
    deterministic = (
        "🇺🇸 미국시장 점검\n현재 환경: 선택적 강세\n\n"
        "🌙 한국 야간선물\n• KOSPI200 야간선물 종가 431.25pt · +0.67%\n\n"
        "🧭 시장 상황\n기존 deterministic 전체 블록\n\n"
        "⚠️ 데이터 주의\n• 달러지수 지연"
    )
    text = _render_ai_market_message(
        deterministic,
        review,
        market_context={
            "required_market_fact_ids": ["market:night_futures:1"],
            "portfolio_exposure_groups": [
                {"group_key": "semiconductor", "label": "반도체"}
            ]
        },
        market="us",
        pilot_day=1,
        target_days=5,
    )

    assert "🤖 AI 보조 미국시장 점검 · US Pilot 1/5" in text
    assert "🌙 한국 개장 전 신호" in text
    assert "🎯 오늘 시장 한 줄" in text
    assert "📈 실제 변화" in text
    assert "🧭 시장 구조" in text
    assert "🔗 모니터링 종목에 미치는 영향" in text
    assert "📌 다음 확인" in text
    assert "⚠️ 데이터 주의" in text
    assert text.count("🌙 한국 개장 전 신호") == 1
    assert "기존 deterministic 전체 블록" not in text
    assert "추가 확정 근거를 기다립니다" not in text


@pytest.mark.anyio
async def test_hold_is_scoped_and_internal_metadata_is_not_sent(
    monkeypatch, tmp_path: Path
) -> None:
    _settings(monkeypatch, tmp_path)
    _write_artifacts(tmp_path)
    notifier = RecordingNotifier()
    with Session(_engine()) as session:
        _seed_deliveries(session)
        session.add(
            NotificationDelivery(
                ticker="UNRELATED",
                assessment_date=RUN_DATE,
                channel="telegram",
                status="pending",
                payload=json.dumps({"text": "운영 경고", "type": "operational_warning"}),
            )
        )
        session.commit()
        hold_ai_assisted_pilot_session(session, PACKET_ID)
        await dispatch_pending_notifications(session, notifier=notifier)
        held = session.exec(
            select(NotificationDelivery).where(NotificationDelivery.ticker == "PILOT")
        ).one()

    assert [item["type"] for item in notifier.payloads] == ["operational_warning"]
    payload = json.loads(held.payload)
    assert payload[AI_ASSISTED_PILOT_METADATA_KEY]["state"] == "held"
    assert AI_ASSISTED_PILOT_METADATA_KEY not in str(notifier.payloads[0]["text"])


def test_monitor_retry_does_not_overwrite_pilot_owned_digest(
    monkeypatch, tmp_path: Path
) -> None:
    _settings(monkeypatch, tmp_path)
    _write_artifacts(tmp_path)
    monkeypatch.setattr(
        "app.services.notification_service.build_daily_digest", lambda *args, **kwargs: object()
    )
    monkeypatch.setattr(
        "app.services.notification_service.render_daily_digest",
        lambda *args, **kwargs: "new deterministic render",
    )
    with Session(_engine()) as session:
        _seed_deliveries(session)
        hold_ai_assisted_pilot_session(session, PACKET_ID)
        before = session.exec(
            select(NotificationDelivery).where(
                NotificationDelivery.ticker == "__DAILY_DIGEST_KR__"
            )
        ).one()
        held_payload = before.payload
        queue_daily_digest_notification(session, RUN_DATE, market_scope="kr")
        session.refresh(before)

    assert before.payload == held_payload
