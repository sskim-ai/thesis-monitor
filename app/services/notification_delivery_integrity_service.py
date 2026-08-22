from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from datetime import date
from pathlib import Path

from sqlmodel import Session, select

from app.models.thesis import MonitorRun, NotificationDelivery
from app.services.notification_service import AI_ASSISTED_PILOT_METADATA_KEY


KR_DAILY_DIGEST_MARKER = "__DAILY_DIGEST_KR__"
KR_ORPHAN_TERMINAL_STATUS = "failed"
KR_ORPHAN_RECONCILIATION_REASON = "non_trading_day_orphan_no_packet"


class OrphanReconciliationError(RuntimeError):
    pass


@dataclass(frozen=True)
class KrOrphanIncident:
    run_id: int
    run_date: date
    packet_id: str
    expected_stock_count: int
    expected_digest_count: int = 1


def _payload(value: str) -> dict[str, object]:
    try:
        parsed = json.loads(value)
    except json.JSONDecodeError as exc:
        raise OrphanReconciliationError("invalid_delivery_payload") from exc
    if not isinstance(parsed, dict):
        raise OrphanReconciliationError("invalid_delivery_payload")
    return parsed


def _run_tickers(run: MonitorRun) -> list[str]:
    try:
        details = json.loads(run.details)
    except json.JSONDecodeError as exc:
        raise OrphanReconciliationError("invalid_monitor_run_details") from exc
    tickers = details.get("tickers") if isinstance(details, dict) else None
    if not isinstance(tickers, dict):
        raise OrphanReconciliationError("monitor_run_tickers_missing")
    return sorted(str(ticker) for ticker in tickers)


def _packet_artifacts(data_dir: Path, packet_id: str) -> list[str]:
    root = data_dir / "ai_review"
    if not root.exists():
        return []
    return sorted(
        str(path.relative_to(data_dir))
        for path in root.rglob(f"*{packet_id}*")
        if path.is_file()
    )


def _row_snapshot(delivery: NotificationDelivery) -> dict[str, object]:
    payload = _payload(delivery.payload)
    metadata = payload.get(AI_ASSISTED_PILOT_METADATA_KEY)
    packet_reference = (
        str(metadata.get("packet_id") or "")
        if isinstance(metadata, dict)
        else ""
    )
    return {
        "id": delivery.id,
        "ticker": delivery.ticker,
        "channel": delivery.channel,
        "status": delivery.status,
        "attempt_count": delivery.attempt_count,
        "last_error": delivery.last_error,
        "sent_at": delivery.sent_at.isoformat() if delivery.sent_at else None,
        "created_at": delivery.created_at.isoformat(),
        "payload_type": payload.get("type"),
        "payload_sha256": hashlib.sha256(
            delivery.payload.encode("utf-8")
        ).hexdigest(),
        "packet_reference": packet_reference or None,
    }


def inspect_kr_orphan_incident(
    session: Session,
    incident: KrOrphanIncident,
    *,
    data_dir: Path,
) -> dict[str, object]:
    run = session.get(MonitorRun, incident.run_id)
    if run is None:
        raise OrphanReconciliationError("monitor_run_missing")
    if (
        run.run_date != incident.run_date
        or run.run_type != "daily_kr"
        or run.status != "success"
    ):
        raise OrphanReconciliationError("monitor_run_identity_mismatch")

    stock_tickers = _run_tickers(run)
    if (
        len(stock_tickers) != incident.expected_stock_count
        or run.success_count != incident.expected_stock_count
        or run.failure_count != 0
    ):
        raise OrphanReconciliationError("stock_count_mismatch")
    expected_tickers = [KR_DAILY_DIGEST_MARKER, *stock_tickers]
    deliveries = list(
        session.exec(
            select(NotificationDelivery)
            .where(
                NotificationDelivery.assessment_date == incident.run_date,
                NotificationDelivery.channel == "telegram",
                NotificationDelivery.ticker.in_(expected_tickers),
            )
            .order_by(NotificationDelivery.id)
        ).all()
    )
    expected_total = incident.expected_stock_count + incident.expected_digest_count
    if len(deliveries) != expected_total:
        raise OrphanReconciliationError("delivery_count_mismatch")
    actual_tickers = sorted(delivery.ticker for delivery in deliveries)
    if actual_tickers != sorted(expected_tickers):
        raise OrphanReconciliationError("delivery_identity_mismatch")

    artifacts = _packet_artifacts(data_dir, incident.packet_id)
    if artifacts:
        raise OrphanReconciliationError("valid_packet_artifact_exists")
    snapshots = [_row_snapshot(delivery) for delivery in deliveries]
    if any(item["sent_at"] is not None for item in snapshots):
        raise OrphanReconciliationError("sent_at_present")
    if any(item["status"] == "sent" for item in snapshots):
        raise OrphanReconciliationError("already_sent_row_present")
    if any(item["packet_reference"] for item in snapshots):
        raise OrphanReconciliationError("packet_reference_present")

    statuses = {str(item["status"]) for item in snapshots}
    errors = {item["last_error"] for item in snapshots}
    if statuses == {"pending"}:
        state = "ready"
    elif statuses == {KR_ORPHAN_TERMINAL_STATUS} and errors == {
        KR_ORPHAN_RECONCILIATION_REASON
    }:
        state = "already_reconciled"
    else:
        raise OrphanReconciliationError("delivery_state_mismatch")
    return {
        "contract": "kr-orphan-delivery-reconciliation-v1",
        "state": state,
        "run_id": incident.run_id,
        "run_date": incident.run_date.isoformat(),
        "packet_id": incident.packet_id,
        "packet_artifact_count": 0,
        "expected_stock_count": incident.expected_stock_count,
        "expected_digest_count": incident.expected_digest_count,
        "target_row_count": len(snapshots),
        "rows": snapshots,
    }


def reconcile_kr_orphan_incident(
    session: Session,
    incident: KrOrphanIncident,
    *,
    data_dir: Path,
    apply: bool = False,
) -> dict[str, object]:
    before = inspect_kr_orphan_incident(session, incident, data_dir=data_dir)
    if before["state"] == "already_reconciled":
        return {**before, "result": "already_reconciled", "changed_count": 0}
    if not apply:
        return {**before, "result": "dry_run_ready", "changed_count": 0}

    row_ids = [int(row["id"]) for row in before["rows"]]
    deliveries = list(
        session.exec(
            select(NotificationDelivery).where(NotificationDelivery.id.in_(row_ids))
        ).all()
    )
    if len(deliveries) != len(row_ids):
        raise OrphanReconciliationError("delivery_count_changed_before_apply")
    for delivery in deliveries:
        if delivery.status != "pending" or delivery.sent_at is not None:
            raise OrphanReconciliationError("delivery_state_changed_before_apply")
        delivery.status = KR_ORPHAN_TERMINAL_STATUS
        delivery.last_error = KR_ORPHAN_RECONCILIATION_REASON
        session.add(delivery)
    session.commit()

    after = inspect_kr_orphan_incident(session, incident, data_dir=data_dir)
    if after["state"] != "already_reconciled":
        raise OrphanReconciliationError("post_apply_verification_failed")
    return {
        **after,
        "result": "reconciled",
        "changed_count": len(row_ids),
        "previous_status": "pending",
        "terminal_status": KR_ORPHAN_TERMINAL_STATUS,
        "reason": KR_ORPHAN_RECONCILIATION_REASON,
    }
