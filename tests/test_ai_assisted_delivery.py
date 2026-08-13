import json
from datetime import date, datetime
from pathlib import Path
from zoneinfo import ZoneInfo

import pytest
from sqlalchemy.pool import StaticPool
from sqlmodel import SQLModel, Session, create_engine, select

from app.config import get_settings
from app.models.thesis import NotificationDelivery
from app.services.ai_assisted_delivery_service import (
    ai_assisted_pilot_active,
    deliver_validated_ai_review,
    dispatch_due_deterministic_fallbacks,
    hold_ai_assisted_pilot_session,
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
            "ai_review_pilot_us_fallback_time": "09:45",
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
        "analysis_policy_version": "daily-review-v3.2",
        "knowledge": {"version": "3.0", "sha256": "knowledge-sha"},
        "packet_id": PACKET_ID,
        "market": "kr",
        "assessment_date": RUN_DATE.isoformat(),
        "stocks": [{"ticker": "PILOT", "thesis_version": 1}],
    }


def _output() -> dict[str, object]:
    return {
        "schema_version": "2",
        "packet_id": PACKET_ID,
        "claim_id": "claim-1",
        "analysis_policy_version": "daily-review-v3.2",
        "knowledge_version": "3.0",
        "knowledge_sha256": "knowledge-sha",
        "market": "kr",
        "assessment_date": RUN_DATE.isoformat(),
        "market_review": {
            "facts_used": [],
            "frameworks_used": ["macro_transmission"],
            "interpretation": [
                {"text": "시장 신호는 기업 펀더멘털과 분리해 봐야 합니다.", "fact_ids": []}
            ],
            "numeric_claims": [],
            "unknowns": ["다음 거래일 방향은 미확인입니다."],
            "summary": "검증된 시장 맥락은 혼재 상태입니다.",
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
                "interpretation": [
                    {"text": "추가 약화 여부는 다음 실적에서 확인해야 합니다.", "fact_ids": []}
                ],
                "numeric_claims": [],
                "unknowns": ["다음 분기 마진은 미확인입니다."],
                "summary": "공식 상태를 바꿀 확정 근거는 아직 부족합니다.",
                "holder_view": "확정된 경고와 실행 지표를 계속 확인합니다.",
                "new_buyer_view": "기업의 질과 진입 가격을 나누어 봅니다.",
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
        (outbox / f"{PACKET_ID}--daily-review-v3.2--knowledge.json").write_text(
            json.dumps(_output(), ensure_ascii=False), encoding="utf-8"
        )


def _seed_deliveries(session: Session, *, status: str = "pending") -> None:
    session.add(
        NotificationDelivery(
            ticker="__DAILY_DIGEST_KR__",
            assessment_date=RUN_DATE,
            channel="telegram",
            status=status,
            payload=json.dumps(
                {
                    "text": "🇰🇷 한국 종목 장마감 점검 · 2026-08-14\n현재 환경: 혼합",
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
    assert "투자 논리: 유지" in str(stock["text"])
    assert "AI 투자 논리: 약화" not in str(stock["text"])
    assert all(item.status == "sent" for item in deliveries)
    archive = tmp_path / "ai_review" / "pilot" / "history" / "2026" / "08" / PACKET_ID
    assert (archive / "deterministic-messages.json").exists()
    assert (archive / "ai-assisted-messages.json").exists()
    assert (archive / "delivery-result.json").exists()


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
        (outbox / f"{PACKET_ID}--daily-review-v3.2--knowledge.json").write_text(
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


def test_pilot_stops_market_after_five_successful_packets(monkeypatch, tmp_path: Path) -> None:
    _settings(monkeypatch, tmp_path)
    state = {
        "schema_version": "1",
        "pilot_version": "ai-assisted-pilot-v1",
        "markets": {
            "us": {"successful_packet_ids": [], "successful_assessment_dates": []},
            "kr": {
                "successful_packet_ids": [f"packet-{index}" for index in range(5)],
                "successful_assessment_dates": [f"2026-08-{index + 1:02d}" for index in range(5)],
            },
        },
        "sessions": {},
    }
    path = tmp_path / "ai_review" / "pilot" / "state.json"
    path.parent.mkdir(parents=True)
    path.write_text(json.dumps(state), encoding="utf-8")

    assert ai_assisted_pilot_active("kr") is False
    assert ai_assisted_pilot_active("us") is True


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
