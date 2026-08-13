from __future__ import annotations

import copy
import fcntl
import hashlib
import json
import os
from contextlib import contextmanager
from dataclasses import asdict, dataclass
from datetime import date, datetime, time
from pathlib import Path
from typing import Iterator, Literal
from zoneinfo import ZoneInfo

from sqlmodel import Session, select

from app.config import get_settings
from app.models.thesis import NotificationDelivery
from app.schemas.ai_review import AIDailyReviewOutput, AIMarketReview, AIStockReview
from app.services.notification_service import (
    AI_ASSISTED_PILOT_METADATA_KEY,
    TELEGRAM_DELIVERY_METADATA_KEY,
    TelegramNotifier,
    dispatch_pending_notifications,
)


KST = ZoneInfo("Asia/Seoul")
PILOT_MODE = "ai_assisted_single_delivery"
PILOT_VERSION = "ai-assisted-pilot-v1"
PILOT_MARKERS = {"us": "__DAILY_DIGEST__", "kr": "__DAILY_DIGEST_KR__"}
PilotMarket = Literal["us", "kr"]


@dataclass(frozen=True)
class PilotDeliveryResult:
    status: str
    market: str
    packet_id: str | None = None
    delivery_mode: str | None = None
    delivery_count: int = 0
    sent_count: int = 0
    pending_count: int = 0
    pilot_day: int | None = None
    reason: str | None = None

    def as_dict(self) -> dict[str, object]:
        return asdict(self)


def _pilot_root() -> Path:
    return Path(get_settings().data_dir) / "ai_review" / "pilot"


def _atomic_json(path: Path, payload: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temp = path.with_suffix(path.suffix + ".tmp")
    with temp.open("w", encoding="utf-8") as handle:
        json.dump(payload, handle, ensure_ascii=False, indent=2, default=str)
        handle.flush()
        os.fsync(handle.fileno())
    os.replace(temp, path)


@contextmanager
def _pilot_lock(key: str) -> Iterator[None]:
    digest = hashlib.sha256(key.encode("utf-8")).hexdigest()
    path = _pilot_root() / "locks" / f"{digest}.lock"
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a+b") as handle:
        fcntl.flock(handle.fileno(), fcntl.LOCK_EX)
        try:
            yield
        finally:
            fcntl.flock(handle.fileno(), fcntl.LOCK_UN)


def _read_json(path: Path) -> dict[str, object]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"Expected a JSON object: {path}")
    return value


def _pilot_state() -> dict[str, object]:
    path = _pilot_root() / "state.json"
    if not path.exists():
        return {
            "schema_version": "1",
            "pilot_version": PILOT_VERSION,
            "markets": {
                "us": {"successful_packet_ids": [], "successful_assessment_dates": []},
                "kr": {"successful_packet_ids": [], "successful_assessment_dates": []},
            },
            "sessions": {},
        }
    try:
        value = _read_json(path)
    except (ValueError, json.JSONDecodeError):
        return {
            "schema_version": "1",
            "pilot_version": PILOT_VERSION,
            "markets": {
                "us": {"successful_packet_ids": [], "successful_assessment_dates": []},
                "kr": {"successful_packet_ids": [], "successful_assessment_dates": []},
            },
            "sessions": {},
        }
    return value


def _write_pilot_state(state: dict[str, object]) -> None:
    _atomic_json(_pilot_root() / "state.json", state)


def _market_successes(state: dict[str, object], market: PilotMarket) -> list[str]:
    markets = state.get("markets")
    if not isinstance(markets, dict):
        return []
    item = markets.get(market)
    if not isinstance(item, dict):
        return []
    values = item.get("successful_packet_ids")
    return [str(value) for value in values] if isinstance(values, list) else []


def _market_success_dates(state: dict[str, object], market: PilotMarket) -> list[str]:
    markets = state.get("markets")
    if not isinstance(markets, dict):
        return []
    item = markets.get(market)
    if not isinstance(item, dict):
        return []
    values = item.get("successful_assessment_dates")
    return [str(value) for value in values] if isinstance(values, list) else []


def ai_assisted_pilot_active(market: PilotMarket) -> bool:
    settings = get_settings()
    if not settings.ai_review_pilot_enabled:
        return False
    with _pilot_lock("state"):
        return len(_market_success_dates(_pilot_state(), market)) < (
            settings.ai_review_pilot_target_success_days
        )


def _packet_path(packet_id: str) -> Path:
    return Path(get_settings().data_dir) / "ai_review" / "inbox" / f"{packet_id}.json"


def _output_path(packet_id: str) -> Path | None:
    candidates = sorted(
        (Path(get_settings().data_dir) / "ai_review" / "outbox").glob(
            f"{packet_id}--*.json"
        )
    )
    return candidates[-1] if candidates else None


def _packet_tickers(packet: dict[str, object]) -> list[str]:
    return [
        str(item["ticker"])
        for item in packet.get("stocks", [])
        if isinstance(item, dict) and item.get("ticker")
    ]


def _session_deliveries(
    session: Session,
    packet: dict[str, object],
) -> list[NotificationDelivery]:
    market = str(packet["market"])
    run_date = date.fromisoformat(str(packet["assessment_date"]))
    tickers = [*_packet_tickers(packet), PILOT_MARKERS[market]]
    channel = get_settings().notification_channel.strip().lower()
    return list(
        session.exec(
            select(NotificationDelivery)
            .where(
                NotificationDelivery.assessment_date == run_date,
                NotificationDelivery.channel == channel,
                NotificationDelivery.ticker.in_(tickers),
            )
            .order_by(NotificationDelivery.ticker)
        ).all()
    )


def _clean_deterministic_payload(payload: dict[str, object]) -> dict[str, object]:
    value = copy.deepcopy(payload)
    value.pop(AI_ASSISTED_PILOT_METADATA_KEY, None)
    value.pop(TELEGRAM_DELIVERY_METADATA_KEY, None)
    return value


def _pilot_metadata(payload: dict[str, object]) -> dict[str, object]:
    value = payload.get(AI_ASSISTED_PILOT_METADATA_KEY)
    return dict(value) if isinstance(value, dict) else {}


def _archive_directory(packet: dict[str, object]) -> Path:
    run_date = date.fromisoformat(str(packet["assessment_date"]))
    return (
        _pilot_root()
        / "history"
        / f"{run_date:%Y}"
        / f"{run_date:%m}"
        / str(packet["packet_id"])
    )


def _archive_messages(
    packet: dict[str, object],
    filename: str,
    messages: list[dict[str, object]],
) -> Path:
    path = _archive_directory(packet) / filename
    _atomic_json(path, {"packet_id": packet["packet_id"], "messages": messages})
    return path


def hold_ai_assisted_pilot_session(
    session: Session,
    packet_id: str,
    *,
    held_at: datetime | None = None,
) -> PilotDeliveryResult:
    packet = _read_json(_packet_path(packet_id))
    market = str(packet["market"])
    if market not in PILOT_MARKERS or not ai_assisted_pilot_active(market):
        return PilotDeliveryResult(status="not_active", market=market, packet_id=packet_id)
    now = (held_at or datetime.now(KST)).astimezone(KST)
    with _pilot_lock(packet_id):
        deliveries = _session_deliveries(session, packet)
        archived: list[dict[str, object]] = []
        held_ids: list[int] = []
        for delivery in deliveries:
            payload = json.loads(delivery.payload)
            if not isinstance(payload, dict):
                continue
            metadata = _pilot_metadata(payload)
            if metadata.get("packet_id") == packet_id and metadata.get("state") in {
                "held",
                "ai_assisted_pending",
                "ai_assisted_sent",
                "fallback_pending",
                "fallback_sent",
            }:
                if delivery.id is not None:
                    held_ids.append(delivery.id)
                continue
            telegram = payload.get(TELEGRAM_DELIVERY_METADATA_KEY)
            if (
                isinstance(telegram, dict)
                and int(telegram.get("next_chunk_index") or 0) > 0
            ):
                continue
            deterministic = _clean_deterministic_payload(payload)
            payload[AI_ASSISTED_PILOT_METADATA_KEY] = {
                "pilot_mode": PILOT_MODE,
                "pilot_version": PILOT_VERSION,
                "packet_id": packet_id,
                "market": market,
                "assessment_date": packet["assessment_date"],
                "state": "held",
                "fallback_eligible": True,
                "held_at": now.isoformat(),
                "deterministic_payload": deterministic,
            }
            delivery.payload = json.dumps(payload, ensure_ascii=False)
            delivery.status = "pending"
            delivery.sent_at = None
            session.add(delivery)
            if delivery.id is not None:
                held_ids.append(delivery.id)
            archived.append(
                {
                    "delivery_id": delivery.id,
                    "ticker": delivery.ticker,
                    "payload": deterministic,
                }
            )
        session.commit()
        archive_path = _archive_directory(packet) / "deterministic-messages.json"
        if archived or not archive_path.exists():
            _archive_messages(packet, "deterministic-messages.json", archived)
    return PilotDeliveryResult(
        status="held",
        market=market,
        packet_id=packet_id,
        delivery_mode="held",
        delivery_count=len(held_ids),
        pending_count=len(held_ids),
    )


def _bullets(values: list[str], empty: str | None = None) -> str:
    items = [f"• {value}" for value in values if value.strip()]
    if not items and empty:
        items.append(f"• {empty}")
    return "\n".join(items)


def _interpretations(review: AIMarketReview | AIStockReview) -> list[str]:
    return [item.text.strip() for item in review.interpretation if item.text.strip()]


def _deterministic_blocks(text: str) -> list[str]:
    return [block.strip() for block in text.split("\n\n") if block.strip()]


def _first_block(blocks: list[str], prefix: str) -> str | None:
    return next((block for block in blocks if block.startswith(prefix)), None)


def _render_ai_market_message(
    deterministic_text: str,
    review: AIMarketReview,
    *,
    market: str,
    pilot_day: int,
    target_days: int,
) -> str:
    market_label = "US" if market == "us" else "KR"
    interpretations = _bullets(_interpretations(review), "추가 해석이 없습니다.")
    unknowns = _bullets(review.unknowns)
    sections = [
        f"🤖 AI 보조 시장 점검 · {market_label} Pilot {pilot_day}/{target_days}",
        f"🎯 핵심 해석\n{review.summary.strip()}",
        f"🧩 투자적 의미\n{interpretations}",
    ]
    if unknowns:
        sections.append(f"⚠️ 확인 필요\n{unknowns}")
    sections.append(f"📋 검증된 시장 스냅샷\n{deterministic_text.strip()}")
    return "\n\n".join(sections)


def _render_ai_stock_message(
    deterministic_text: str,
    review: AIStockReview,
    *,
    market: str,
    pilot_day: int,
    target_days: int,
) -> str:
    market_label = "US" if market == "us" else "KR"
    blocks = _deterministic_blocks(deterministic_text)
    company = blocks[0] if blocks else f"🏢 {review.ticker}"
    official = _first_block(blocks, "투자 논리:") or "투자 논리: 확인 필요"
    fixed_context = [
        block
        for block in blocks
        if block.startswith(("구조적 위험:", "시장 기대:"))
    ]
    deterministic_details = [
        block
        for block in blocks
        if block.startswith(
            (
                "📌 초기 근거",
                "🔄 중요한 변화",
                "🚨 오늘 새 경고",
                "⚠️ 기존 경고",
                "👁 핵심 감시",
                "📍 오늘 접근한 조건",
                "💰 가격",
                "📊 수급",
                "📐 Valuation",
                "⚠️ 데이터 주의",
            )
        )
    ]
    sections = [
        f"🤖 AI 보조 종목 점검 · {market_label} Pilot {pilot_day}/{target_days}",
        "\n".join([company, official, *fixed_context]),
        f"🎯 핵심 해석\n{review.summary.strip()}",
    ]
    interpretations = _bullets(_interpretations(review), "추가 해석이 없습니다.")
    sections.append(f"🧩 투자적 의미\n{interpretations}")
    sections.extend(deterministic_details)
    sections.extend(
        [
            f"💡 보유 관점\n{review.holder_view.strip()}",
            f"🔎 신규 관찰자 관점\n{review.new_buyer_view.strip()}",
        ]
    )
    next_checks = _bullets(review.next_checks)
    if next_checks:
        sections.append(f"📌 다음 확인\n{next_checks}")
    if review.unknowns:
        sections.append(f"⚠️ 미확인 사항\n{_bullets(review.unknowns)}")
    return "\n\n".join(section for section in sections if section.strip())


def _pilot_day(market: PilotMarket) -> int:
    with _pilot_lock("state"):
        return len(_market_success_dates(_pilot_state(), market)) + 1


def _record_session(
    packet_id: str,
    market: PilotMarket,
    *,
    assessment_date: str,
    delivery_mode: str,
    sent: bool,
    now: datetime,
) -> int:
    with _pilot_lock("state"):
        state = _pilot_state()
        markets = state.setdefault("markets", {})
        market_state = markets.setdefault(
            market,
            {"successful_packet_ids": [], "successful_assessment_dates": []},
        )
        successes = market_state.setdefault("successful_packet_ids", [])
        if not isinstance(successes, list):
            successes = []
            market_state["successful_packet_ids"] = successes
        success_dates = market_state.setdefault("successful_assessment_dates", [])
        if not isinstance(success_dates, list):
            success_dates = []
            market_state["successful_assessment_dates"] = success_dates
        if sent and delivery_mode == "ai_assisted" and packet_id not in successes:
            successes.append(packet_id)
        if sent and delivery_mode == "ai_assisted" and assessment_date not in success_dates:
            success_dates.append(assessment_date)
        sessions = state.setdefault("sessions", {})
        sessions[packet_id] = {
            "market": market,
            "delivery_mode": delivery_mode,
            "sent": sent,
            "updated_at": now.astimezone(KST).isoformat(),
            "counted_as_ai_pilot_success": packet_id in successes,
        }
        _write_pilot_state(state)
        return (
            success_dates.index(assessment_date) + 1
            if assessment_date in success_dates
            else len(success_dates) + 1
        )


async def deliver_validated_ai_review(
    session: Session,
    packet_id: str,
    *,
    notifier: TelegramNotifier | None = None,
    allow_duplicate: bool = False,
    now: datetime | None = None,
) -> PilotDeliveryResult:
    packet = _read_json(_packet_path(packet_id))
    market = str(packet["market"])
    if market not in PILOT_MARKERS:
        return PilotDeliveryResult(status="invalid_market", market=market, packet_id=packet_id)
    if not get_settings().ai_review_pilot_enabled:
        return PilotDeliveryResult(status="not_active", market=market, packet_id=packet_id)
    output_path = _output_path(packet_id)
    if output_path is None:
        return PilotDeliveryResult(
            status="not_ready", market=market, packet_id=packet_id, reason="validated_output_missing"
        )
    output = AIDailyReviewOutput.model_validate(_read_json(output_path))
    current = (now or datetime.now(KST)).astimezone(KST)
    target_days = get_settings().ai_review_pilot_target_success_days
    pilot_day = min(_pilot_day(market), target_days)
    reviews = {item.ticker: item for item in output.stock_reviews}
    archive_dir = _archive_directory(packet)
    _atomic_json(archive_dir / "packet.json", packet)
    _atomic_json(archive_dir / "ai-review.json", output.model_dump(mode="json"))
    comparison_name = output_path.name.replace(".json", ".comparison.json")
    comparison_candidates = list(
        (Path(get_settings().data_dir) / "ai_review" / "history").glob(
            f"*/*/{comparison_name}"
        )
    )
    if comparison_candidates:
        _atomic_json(
            archive_dir / "comparison.json",
            _read_json(comparison_candidates[-1]),
        )

    with _pilot_lock(packet_id):
        deliveries = _session_deliveries(session, packet)
        prepared_ids: set[int] = set()
        deterministic_messages: list[dict[str, object]] = []
        final_messages: list[dict[str, object]] = []
        for delivery in deliveries:
            payload = json.loads(delivery.payload)
            if not isinstance(payload, dict):
                continue
            metadata = _pilot_metadata(payload)
            state = str(metadata.get("state") or "")
            deterministic = metadata.get("deterministic_payload")
            if not isinstance(deterministic, dict):
                deterministic = _clean_deterministic_payload(payload)
            deterministic_messages.append(
                {
                    "delivery_id": delivery.id,
                    "ticker": delivery.ticker,
                    "payload": deterministic,
                }
            )
            if state in {"fallback_pending", "fallback_sent"}:
                continue
            if state in {"ai_assisted_pending", "ai_assisted_sent"} and metadata.get(
                "packet_id"
            ) == packet_id:
                if delivery.id is not None:
                    prepared_ids.add(delivery.id)
                final_messages.append(
                    {
                        "delivery_id": delivery.id,
                        "ticker": delivery.ticker,
                        "logical_identity": metadata.get("delivery_identity"),
                        "text": str(payload.get("text") or ""),
                    }
                )
                continue
            if delivery.status == "sent" and not allow_duplicate:
                continue
            deterministic_text = str(deterministic.get("text") or "").strip()
            if delivery.ticker == PILOT_MARKERS[market]:
                text = _render_ai_market_message(
                    deterministic_text,
                    output.market_review,
                    market=market,
                    pilot_day=pilot_day,
                    target_days=target_days,
                )
                identity = f"{PILOT_VERSION}:{packet_id}:market"
                message_type = "ai_assisted_pilot_market"
            else:
                review = reviews.get(delivery.ticker)
                if review is None:
                    continue
                text = _render_ai_stock_message(
                    deterministic_text,
                    review,
                    market=market,
                    pilot_day=pilot_day,
                    target_days=target_days,
                )
                identity = f"{PILOT_VERSION}:{packet_id}:stock:{delivery.ticker}"
                message_type = "ai_assisted_pilot_stock"
            new_payload = copy.deepcopy(deterministic)
            new_payload["text"] = text
            new_payload["type"] = message_type
            new_payload["use_llm"] = False
            new_payload.pop(TELEGRAM_DELIVERY_METADATA_KEY, None)
            new_payload[AI_ASSISTED_PILOT_METADATA_KEY] = {
                "pilot_mode": PILOT_MODE,
                "pilot_version": PILOT_VERSION,
                "packet_id": packet_id,
                "market": market,
                "assessment_date": packet["assessment_date"],
                "state": "ai_assisted_pending",
                "fallback_eligible": False,
                "delivery_identity": identity,
                "deterministic_payload": deterministic,
                "prepared_at": current.isoformat(),
            }
            delivery.payload = json.dumps(new_payload, ensure_ascii=False)
            delivery.status = "pending"
            delivery.attempt_count = 0
            delivery.last_error = None
            delivery.sent_at = None
            session.add(delivery)
            if delivery.id is not None:
                prepared_ids.add(delivery.id)
            final_messages.append(
                {
                    "delivery_id": delivery.id,
                    "ticker": delivery.ticker,
                    "logical_identity": identity,
                    "text": text,
                }
            )
        session.commit()
        deterministic_archive = archive_dir / "deterministic-messages.json"
        if deterministic_messages or not deterministic_archive.exists():
            _archive_messages(
                packet,
                "deterministic-messages.json",
                deterministic_messages,
            )
        ai_archive = archive_dir / "ai-assisted-messages.json"
        if final_messages or not ai_archive.exists():
            _archive_messages(packet, "ai-assisted-messages.json", final_messages)
        _atomic_json(
            archive_dir / "validation-result.json",
            {
                "packet_id": packet_id,
                "status": "passed",
                "validated_output": str(output_path),
                "analysis_policy_version": output.analysis_policy_version,
                "knowledge_version": output.knowledge_version,
                "knowledge_sha256": output.knowledge_sha256,
            },
        )
        if not prepared_ids:
            return PilotDeliveryResult(
                status="archive_only",
                market=market,
                packet_id=packet_id,
                reason="fallback_or_existing_delivery_won",
            )
        await dispatch_pending_notifications(
            session,
            notifier=notifier,
            delivery_ids=prepared_ids,
        )
        sent_count = 0
        pending_count = 0
        for delivery in _session_deliveries(session, packet):
            if delivery.id not in prepared_ids:
                continue
            if delivery.status == "sent":
                sent_count += 1
            else:
                pending_count += 1
            payload = json.loads(delivery.payload)
            if isinstance(payload, dict):
                metadata = _pilot_metadata(payload)
                if metadata.get("packet_id") == packet_id:
                    metadata["state"] = (
                        "ai_assisted_sent"
                        if delivery.status == "sent"
                        else "ai_assisted_pending"
                    )
                    payload[AI_ASSISTED_PILOT_METADATA_KEY] = metadata
                    delivery.payload = json.dumps(payload, ensure_ascii=False)
                    session.add(delivery)
        session.commit()
        complete = bool(prepared_ids) and pending_count == 0
        recorded_day = _record_session(
            packet_id,
            market,
            assessment_date=str(packet["assessment_date"]),
            delivery_mode="ai_assisted",
            sent=complete,
            now=current,
        )
        _atomic_json(
            _archive_directory(packet) / "delivery-result.json",
            {
                "packet_id": packet_id,
                "delivery_mode": "ai_assisted",
                "status": "sent" if complete else "pending",
                "delivery_count": len(prepared_ids),
                "sent_count": sent_count,
                "pending_count": pending_count,
                "pilot_day": recorded_day if complete else pilot_day,
                "dispatched_at": current.isoformat() if complete else None,
            },
        )
    return PilotDeliveryResult(
        status="sent" if complete else "pending",
        market=market,
        packet_id=packet_id,
        delivery_mode="ai_assisted",
        delivery_count=len(prepared_ids),
        sent_count=sent_count,
        pending_count=pending_count,
        pilot_day=recorded_day if complete else pilot_day,
    )


def _fallback_deadline(run_date: date, market: PilotMarket) -> datetime:
    raw = (
        get_settings().ai_review_pilot_us_fallback_time
        if market == "us"
        else get_settings().ai_review_pilot_kr_fallback_time
    )
    hour, minute = (int(value) for value in raw.split(":", maxsplit=1))
    return datetime.combine(run_date, time(hour, minute), tzinfo=KST)


def _pending_pilot_packets(
    session: Session,
    market: PilotMarket,
    run_date: date,
) -> list[str]:
    channel = get_settings().notification_channel.strip().lower()
    values: list[str] = []
    deliveries = session.exec(
        select(NotificationDelivery).where(
            NotificationDelivery.assessment_date == run_date,
            NotificationDelivery.channel == channel,
            NotificationDelivery.status == "pending",
        )
    ).all()
    for delivery in deliveries:
        try:
            payload = json.loads(delivery.payload)
        except json.JSONDecodeError:
            continue
        metadata = _pilot_metadata(payload) if isinstance(payload, dict) else {}
        if metadata.get("market") == market and metadata.get("state") in {
            "held",
            "ai_assisted_pending",
            "fallback_pending",
        }:
            packet_id = str(metadata.get("packet_id") or "")
            if packet_id and packet_id not in values:
                values.append(packet_id)
    return values


async def _retry_fallback_delivery(
    session: Session,
    packet: dict[str, object],
    *,
    notifier: TelegramNotifier | None,
    current: datetime,
) -> PilotDeliveryResult:
    packet_id = str(packet["packet_id"])
    market = str(packet["market"])
    delivery_ids: set[int] = set()
    for delivery in _session_deliveries(session, packet):
        payload = json.loads(delivery.payload)
        metadata = _pilot_metadata(payload) if isinstance(payload, dict) else {}
        if metadata.get("state") == "fallback_pending" and delivery.id is not None:
            delivery_ids.add(delivery.id)
    await dispatch_pending_notifications(
        session,
        notifier=notifier,
        delivery_ids=delivery_ids,
    )
    sent_count = 0
    pending_count = 0
    for delivery in _session_deliveries(session, packet):
        if delivery.id not in delivery_ids:
            continue
        if delivery.status == "sent":
            sent_count += 1
        else:
            pending_count += 1
        payload = json.loads(delivery.payload)
        if isinstance(payload, dict):
            metadata = _pilot_metadata(payload)
            metadata["state"] = (
                "fallback_sent" if delivery.status == "sent" else "fallback_pending"
            )
            payload[AI_ASSISTED_PILOT_METADATA_KEY] = metadata
            delivery.payload = json.dumps(payload, ensure_ascii=False)
            session.add(delivery)
    session.commit()
    complete = bool(delivery_ids) and pending_count == 0
    _record_session(
        packet_id,
        market,
        assessment_date=str(packet["assessment_date"]),
        delivery_mode="deterministic_fallback",
        sent=complete,
        now=current,
    )
    _atomic_json(
        _archive_directory(packet) / "delivery-result.json",
        {
            "packet_id": packet_id,
            "delivery_mode": "deterministic_fallback",
            "status": "sent" if complete else "pending",
            "delivery_count": len(delivery_ids),
            "sent_count": sent_count,
            "pending_count": pending_count,
            "dispatched_at": current.isoformat() if complete else None,
        },
    )
    return PilotDeliveryResult(
        status="sent" if complete else "pending",
        market=market,
        packet_id=packet_id,
        delivery_mode="deterministic_fallback",
        delivery_count=len(delivery_ids),
        sent_count=sent_count,
        pending_count=pending_count,
    )


async def dispatch_due_deterministic_fallbacks(
    session: Session,
    *,
    market: PilotMarket,
    run_date: date,
    now: datetime | None = None,
    notifier: TelegramNotifier | None = None,
) -> list[PilotDeliveryResult]:
    current = (now or datetime.now(KST)).astimezone(KST)
    if current < _fallback_deadline(run_date, market):
        return [PilotDeliveryResult(status="before_deadline", market=market)]
    results: list[PilotDeliveryResult] = []
    for packet_id in _pending_pilot_packets(session, market, run_date):
        packet = _read_json(_packet_path(packet_id))
        session_states = {
            str(_pilot_metadata(payload).get("state") or "")
            for delivery in _session_deliveries(session, packet)
            if isinstance((payload := json.loads(delivery.payload)), dict)
        }
        if "fallback_pending" in session_states:
            with _pilot_lock(packet_id):
                results.append(
                    await _retry_fallback_delivery(
                        session,
                        packet,
                        notifier=notifier,
                        current=current,
                    )
                )
            continue
        if _output_path(packet_id) is not None:
            ai_result = await deliver_validated_ai_review(
                session,
                packet_id,
                notifier=notifier,
                now=current,
            )
            results.append(ai_result)
            if ai_result.status in {"sent", "pending"}:
                continue
        with _pilot_lock(packet_id):
            delivery_ids: set[int] = set()
            fallback_messages: list[dict[str, object]] = []
            for delivery in _session_deliveries(session, packet):
                payload = json.loads(delivery.payload)
                if not isinstance(payload, dict):
                    continue
                metadata = _pilot_metadata(payload)
                if metadata.get("state") != "held":
                    continue
                deterministic = metadata.get("deterministic_payload")
                if not isinstance(deterministic, dict):
                    continue
                fallback = copy.deepcopy(deterministic)
                fallback.pop(TELEGRAM_DELIVERY_METADATA_KEY, None)
                fallback[AI_ASSISTED_PILOT_METADATA_KEY] = {
                    **metadata,
                    "state": "fallback_pending",
                    "fallback_eligible": False,
                    "fallback_started_at": current.isoformat(),
                }
                delivery.payload = json.dumps(fallback, ensure_ascii=False)
                delivery.status = "pending"
                delivery.attempt_count = 0
                delivery.last_error = None
                delivery.sent_at = None
                session.add(delivery)
                if delivery.id is not None:
                    delivery_ids.add(delivery.id)
                fallback_messages.append(
                    {
                        "delivery_id": delivery.id,
                        "ticker": delivery.ticker,
                        "text": str(fallback.get("text") or ""),
                    }
                )
            session.commit()
            _archive_messages(packet, "fallback-messages.json", fallback_messages)
            await dispatch_pending_notifications(
                session,
                notifier=notifier,
                delivery_ids=delivery_ids,
            )
            sent_count = 0
            pending_count = 0
            for delivery in _session_deliveries(session, packet):
                if delivery.id not in delivery_ids:
                    continue
                if delivery.status == "sent":
                    sent_count += 1
                else:
                    pending_count += 1
                payload = json.loads(delivery.payload)
                if isinstance(payload, dict):
                    metadata = _pilot_metadata(payload)
                    metadata["state"] = (
                        "fallback_sent" if delivery.status == "sent" else "fallback_pending"
                    )
                    payload[AI_ASSISTED_PILOT_METADATA_KEY] = metadata
                    delivery.payload = json.dumps(payload, ensure_ascii=False)
                    session.add(delivery)
            session.commit()
            complete = bool(delivery_ids) and pending_count == 0
            _record_session(
                packet_id,
                market,
                assessment_date=str(packet["assessment_date"]),
                delivery_mode="deterministic_fallback",
                sent=complete,
                now=current,
            )
            _atomic_json(
                _archive_directory(packet) / "delivery-result.json",
                {
                    "packet_id": packet_id,
                    "delivery_mode": "deterministic_fallback",
                    "status": "sent" if complete else "pending",
                    "delivery_count": len(delivery_ids),
                    "sent_count": sent_count,
                    "pending_count": pending_count,
                    "dispatched_at": current.isoformat() if complete else None,
                },
            )
            results.append(
                PilotDeliveryResult(
                    status="sent" if complete else "pending",
                    market=market,
                    packet_id=packet_id,
                    delivery_mode="deterministic_fallback",
                    delivery_count=len(delivery_ids),
                    sent_count=sent_count,
                    pending_count=pending_count,
                )
            )
    return results or [PilotDeliveryResult(status="no_held_session", market=market)]
