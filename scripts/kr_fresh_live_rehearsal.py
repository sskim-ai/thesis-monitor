from __future__ import annotations

import argparse
import asyncio
import hashlib
import json
import os
from collections import Counter
from datetime import date, datetime, timezone
from pathlib import Path
from zoneinfo import ZoneInfo

from sqlalchemy import delete
from sqlmodel import Session, select

from app.config import get_settings
from app.database import engine, init_db
from app.jobs.monitor_daily import _producer_target_payload
from app.macro.kr_close import run_kr_close_market_briefing
from app.models.security import ProviderCallTelemetry, SecurityMaster
from app.models.thesis import MonitorRun, NotificationDelivery
from app.models.watchlist import WatchlistItem
from app.services.ai_assisted_delivery_service import hold_ai_assisted_pilot_session
from app.services.ai_review_service import try_write_ai_review_packet
from app.services.daily_monitor_service import (
    _item_market_scope,
    queue_daily_monitor_notifications,
    run_daily_monitor,
)
from app.services.notification_service import AI_ASSISTED_PILOT_METADATA_KEY
from app.services.xkrx_role_target_service import resolve_xkrx_role_target


KST = ZoneInfo("Asia/Seoul")
DIGEST_MARKER = "__DAILY_DIGEST_KR__"
RUN_TYPE = "MANUAL_LIVE_REHEARSAL_NO_DELIVERY"


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run an isolated KR live rehearsal without delivery")
    parser.add_argument("--rehearsal-id", required=True)
    parser.add_argument("--cutoff-kst", required=True)
    parser.add_argument("--output-dir", required=True, type=Path)
    parser.add_argument("--base-sha", required=True)
    return parser


def _atomic_json(path: Path, payload: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f".{path.name}.{os.getpid()}.tmp")
    temporary.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True, default=str) + "\n",
        encoding="utf-8",
    )
    os.replace(temporary, path)


def _read_json(path: Path) -> dict[str, object]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"expected JSON object: {path}")
    return value


def _provider_snapshot(session: Session) -> dict[tuple[str, str, str], tuple[int, int, int]]:
    return {
        (row.provider, row.endpoint, row.ticker): (
            row.success_count,
            row.failure_count,
            row.skip_count,
        )
        for row in session.exec(select(ProviderCallTelemetry)).all()
    }


def _provider_delta(
    session: Session,
    before: dict[tuple[str, str, str], tuple[int, int, int]],
    started_at: datetime,
) -> list[dict[str, object]]:
    started_at_utc = started_at.astimezone(timezone.utc).replace(tzinfo=None)
    rows: list[dict[str, object]] = []
    for row in session.exec(select(ProviderCallTelemetry)).all():
        key = (row.provider, row.endpoint, row.ticker)
        previous = before.get(key, (0, 0, 0))
        success_delta = row.success_count - previous[0]
        failure_delta = row.failure_count - previous[1]
        skip_delta = row.skip_count - previous[2]
        if not any((success_delta, failure_delta, skip_delta)):
            continue
        rows.append(
            {
                "provider": row.provider,
                "endpoint": row.endpoint,
                "ticker": row.ticker,
                "status": row.status,
                "attempted_at": row.attempted_at,
                "finished_at": row.finished_at,
                "success_delta": success_delta,
                "failure_delta": failure_delta,
                "skip_delta": skip_delta,
                "after_rehearsal_start": row.attempted_at >= started_at_utc,
            }
        )
    return sorted(rows, key=lambda item: (str(item["provider"]), str(item["ticker"])))


def _active_kr_tickers(session: Session) -> list[str]:
    securities = {
        row.ticker: row
        for row in session.exec(select(SecurityMaster)).all()
    }
    tickers: list[str] = []
    for item in session.exec(
        select(WatchlistItem).where(WatchlistItem.active.is_(True)).order_by(WatchlistItem.ticker)
    ).all():
        security = securities.get(item.ticker)
        exchange = item.exchange or (security.exchange if security else None)
        if _item_market_scope(session, item) == "kr" and exchange:
            tickers.append(item.ticker)
    return tickers


def _isolated_intent_stage(session: Session, run_date: date, tickers: list[str]) -> None:
    identities = [DIGEST_MARKER, *tickers]
    session.exec(
        delete(NotificationDelivery).where(
            NotificationDelivery.assessment_date == run_date,
            NotificationDelivery.ticker.in_(identities),
        )
    )
    session.commit()


def _delivery_bundle(
    session: Session,
    run_date: date,
    packet_id: str,
    intent_ids: set[int],
) -> tuple[list[dict[str, object]], dict[str, object]]:
    deliveries = list(
        session.exec(
            select(NotificationDelivery)
            .where(NotificationDelivery.id.in_(intent_ids))
            .order_by(NotificationDelivery.id)
        ).all()
    )
    messages: list[dict[str, object]] = []
    packet_refs: list[str] = []
    identities: list[str] = []
    sent_count = 0
    for delivery in deliveries:
        payload = json.loads(delivery.payload)
        if not isinstance(payload, dict):
            raise ValueError("rehearsal delivery payload must be an object")
        metadata = payload.get(AI_ASSISTED_PILOT_METADATA_KEY)
        if not isinstance(metadata, dict):
            raise ValueError("packet-bound rehearsal metadata missing")
        deterministic = metadata.get("deterministic_payload")
        if not isinstance(deterministic, dict):
            raise ValueError("deterministic fallback payload missing")
        packet_ref = str(metadata.get("packet_id") or "")
        packet_refs.append(packet_ref)
        identity = str(delivery.ticker)
        identities.append(identity)
        sent_count += int(delivery.sent_at is not None or delivery.status == "sent")
        messages.append(
            {
                "intent_id": delivery.id,
                "ticker": delivery.ticker,
                "packet_id": packet_ref,
                "state": metadata.get("state"),
                "fallback_eligible": metadata.get("fallback_eligible"),
                "payload": deterministic,
            }
        )
    duplicates = sum(count - 1 for count in Counter(identities).values() if count > 1)
    orphans = sum(packet_ref != packet_id for packet_ref in packet_refs)
    audit = {
        "packet_id": packet_id,
        "intent_count": len(deliveries),
        "digest_count": identities.count(DIGEST_MARKER),
        "stock_count": len(deliveries) - identities.count(DIGEST_MARKER),
        "duplicate_intents": duplicates,
        "orphan_intents": orphans,
        "sent_count": sent_count,
        "all_fallback_eligible": all(
            item["fallback_eligible"] is True for item in messages
        ),
    }
    return messages, audit


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


async def _run() -> None:
    args = _parser().parse_args()
    cutoff = datetime.fromisoformat(args.cutoff_kst).astimezone(KST)
    run_date = date.fromisoformat(cutoff.date().isoformat())
    settings = get_settings()
    data_root = Path(settings.data_dir).resolve()
    database_url = settings.database_url
    if "kr-live-rehearsal" not in args.rehearsal_id:
        raise ValueError("rehearsal identity is not namespaced")
    if not str(data_root).startswith(
        ("/tmp/thesis-monitor-kr-rehearsal-", "/private/tmp/thesis-monitor-kr-rehearsal-")
    ):
        raise ValueError("rehearsal data directory must be isolated under /tmp")
    if "/tmp/thesis-monitor-kr-rehearsal-" not in database_url:
        raise ValueError("rehearsal database must be isolated under /tmp")
    if settings.notification_dry_run is not True:
        raise ValueError("NOTIFICATION_DRY_RUN must be true")

    target = resolve_xkrx_role_target(cutoff, "kr_daily_production")
    if not target.observation_eligible or target.target_xkrx_business_date != run_date:
        raise ValueError(target.skip_reason or "REHEARSAL_NOT_ELIGIBLE")

    init_db()
    started_at = datetime.now(KST)
    with Session(engine) as session:
        tickers = _active_kr_tickers(session)
        telemetry_before = _provider_snapshot(session)
        db_counts_before = {
            "notification_rows": len(session.exec(select(NotificationDelivery)).all()),
            "run_rows": len(session.exec(select(MonitorRun)).all()),
        }
        close_result = await run_kr_close_market_briefing(
            session,
            run_date,
            queue_notifications=False,
            dispatch_notifications=False,
        )
        analysis = await run_daily_monitor(
            session,
            run_date=run_date,
            force=True,
            queue_notifications=False,
            dispatch_notifications=False,
            market_scope="kr",
            as_of=cutoff,
        )
        packet_result = try_write_ai_review_packet(
            session,
            run_date,
            "kr",
            generated_at=cutoff,
        )
        if packet_result.status not in {"created", "already_exists"}:
            raise ValueError(f"packet persistence failed: {packet_result.reason}")
        if not packet_result.packet_id or not packet_result.path:
            raise ValueError("packet persistence returned no identity/path")
        packet_path = Path(packet_result.path)
        packet = _read_json(packet_path)
        natural_packet_id = "2026-08-24-kr-run-36-b82af21dfde3"
        if packet_result.packet_id == natural_packet_id:
            raise ValueError("rehearsal packet collided with immutable natural packet")

        _isolated_intent_stage(session, run_date, tickers)
        intent_ids = queue_daily_monitor_notifications(
            session,
            run_date,
            "kr",
            packet_id=packet_result.packet_id,
        )
        hold = hold_ai_assisted_pilot_session(
            session,
            packet_result.packet_id,
            held_at=cutoff,
        )
        messages, intent_audit = _delivery_bundle(
            session,
            run_date,
            packet_result.packet_id,
            intent_ids,
        )
        provider_rows = _provider_delta(session, telemetry_before, started_at)
        provider_summary: dict[str, dict[str, int]] = {}
        for row in provider_rows:
            summary = provider_summary.setdefault(
                str(row["provider"]),
                {"success": 0, "failure": 0, "skip": 0},
            )
            summary["success"] += int(row["success_delta"])
            summary["failure"] += int(row["failure_delta"])
            summary["skip"] += int(row["skip_delta"])
        output = {
            "contract": "kr-fresh-live-rehearsal-no-delivery-v1",
            "rehearsal_id": args.rehearsal_id,
            "run_type": RUN_TYPE,
            "created_at_kst": started_at,
            "cutoff_at_kst": cutoff,
            "base_sha": args.base_sha,
            "market": "kr",
            "target_xkrx_date": target.target_xkrx_business_date,
            "source_mode": "fresh_read_only",
            "delivery_mode": "disabled",
            "producer_role_target": _producer_target_payload(target),
            "active_kr_universe": tickers,
            "analysis": analysis.model_dump(mode="json"),
            "kr_close_market": close_result.model_dump(mode="json"),
            "packet": {
                "status": packet_result.status,
                "packet_id": packet_result.packet_id,
                "path": str(packet_path),
                "sha256": _sha256(packet_path),
                "ready_for_ai": packet.get("ready_for_ai"),
                "shadow_cohort": packet.get("shadow_cohort"),
                "production_packet_persistence": packet.get(
                    "production_packet_persistence"
                ),
            },
            "hold": hold.as_dict(),
            "intent_audit": intent_audit,
            "provider_summary": provider_summary,
            "provider_rows": provider_rows,
            "db_counts_before": db_counts_before,
            "production_writes": 0,
            "telegram_send": 0,
            "scheduled_task_run": 0,
        }
        args.output_dir.mkdir(parents=True, exist_ok=True)
        _atomic_json(args.output_dir / "rehearsal-result.json", output)
        _atomic_json(
            args.output_dir / "deterministic-fallback-bundle.json",
            {
                "rehearsal_id": args.rehearsal_id,
                "watermark": "MANUAL LIVE REHEARSAL - NOT SENT",
                "packet_id": packet_result.packet_id,
                "messages": messages,
                "audit": intent_audit,
            },
        )
        _atomic_json(args.output_dir / "fresh-packet.json", packet)
        print(json.dumps(output, ensure_ascii=False, indent=2, default=str))


def main() -> None:
    asyncio.run(_run())


if __name__ == "__main__":
    main()
