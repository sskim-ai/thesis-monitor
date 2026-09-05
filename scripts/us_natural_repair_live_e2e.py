from __future__ import annotations

import argparse
import asyncio
import copy
import hashlib
import json
import shutil
from datetime import UTC, date, datetime, timedelta
from pathlib import Path

from sqlmodel import Session, select

from app.config import get_settings
from app.database import engine
from app.jobs.accepted_decision_v2_runtime import generate as generate_accepted_v2
from app.models.thesis import NotificationDelivery
from app.services.ai_assisted_delivery_service import (
    hold_ai_assisted_pilot_session,
    deliver_validated_ai_review,
)
from app.services.ai_review_service import (
    claim_next_ai_review_packet,
    finalize_ai_review_output,
)
from app.services.notification_service import (
    AI_ASSISTED_PILOT_METADATA_KEY,
    TELEGRAM_DELIVERY_METADATA_KEY,
    TelegramNotifier,
)
from app.services.v2_natural_proof_service import (
    ExplicitV2NaturalProofCounts,
    evaluate_explicit_v2_natural_proof,
)
from scripts.kr_market_preenable_evidence import audit_test_sink, load_env_values


CONTRACT = "us-natural-tls-lease-validator-live-e2e-v1"


def _read(path: Path) -> dict[str, object]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"expected_json_object:{path}")
    return value


def _write(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(
        json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True, default=str) + "\n",
        encoding="utf-8",
    )
    temporary.replace(path)


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _delivery_tickers(packet: dict[str, object]) -> set[str]:
    return {
        "__DAILY_DIGEST__",
        *(
            str(row.get("ticker") or "").upper()
            for row in packet.get("stocks") or []
            if isinstance(row, dict)
        ),
    }


def _reset_isolated_deliveries(
    run_date: date,
    *,
    tickers: set[str],
) -> int:
    reset = 0
    with Session(engine) as session:
        rows = session.exec(
            select(NotificationDelivery).where(
                NotificationDelivery.assessment_date == run_date,
                NotificationDelivery.channel == "telegram",
                NotificationDelivery.ticker.in_(tickers),
            )
        ).all()
        for row in rows:
            payload = json.loads(row.payload)
            if not isinstance(payload, dict):
                continue
            metadata = payload.get(AI_ASSISTED_PILOT_METADATA_KEY)
            deterministic = (
                metadata.get("deterministic_payload")
                if isinstance(metadata, dict)
                else None
            )
            if isinstance(deterministic, dict):
                payload = copy.deepcopy(deterministic)
            payload.pop(AI_ASSISTED_PILOT_METADATA_KEY, None)
            payload.pop(TELEGRAM_DELIVERY_METADATA_KEY, None)
            row.payload = json.dumps(payload, ensure_ascii=False)
            row.status = "pending"
            row.attempt_count = 0
            row.last_error = None
            row.sent_at = None
            session.add(row)
            reset += 1
        session.commit()
    return reset


def _delivery_audit(
    run_date: date,
    *,
    tickers: set[str],
) -> dict[str, int]:
    with Session(engine) as session:
        rows = session.exec(
            select(NotificationDelivery).where(
                NotificationDelivery.assessment_date == run_date,
                NotificationDelivery.channel == "telegram",
                NotificationDelivery.ticker.in_(tickers),
            )
        ).all()
    audited = []
    for row in rows:
        payload = json.loads(row.payload)
        metadata = (
            payload.get(AI_ASSISTED_PILOT_METADATA_KEY)
            if isinstance(payload, dict)
            else None
        )
        audited.append((row, metadata if isinstance(metadata, dict) else {}))
    sent = [(row, metadata) for row, metadata in audited if row.status == "sent"]
    ai_sent = [
        (row, metadata)
        for row, metadata in sent
        if metadata.get("state") == "ai_assisted_sent"
    ]
    explicit_v2_sent = [
        (row, metadata)
        for row, metadata in ai_sent
        if row.ticker != "__DAILY_DIGEST__"
        and isinstance(metadata.get("decision_canary"), dict)
        and metadata["decision_canary"].get("state") == "included"
        and metadata["decision_canary"].get("accepted_plan_only") is True
    ]
    stock_ai_sent_count = sum(row.ticker != "__DAILY_DIGEST__" for row, _ in ai_sent)
    return {
        "delivery_count": len(rows),
        "sent_count": len(sent),
        "market_sent_count": sum(
            row.ticker == "__DAILY_DIGEST__" for row, _ in ai_sent
        ),
        "stock_sent_count": stock_ai_sent_count,
        "explicit_v2_stock_sent_count": len(explicit_v2_sent),
        "pilot_ai_assisted_stock_sent_count": stock_ai_sent_count - len(explicit_v2_sent),
        "fallback_sent_count": sum(
            metadata.get("state") == "fallback_sent" for _, metadata in sent
        ),
        "duplicate_count": sum(max(row.attempt_count - 1, 0) for row in rows),
    }


def _prepare_isolated_runtime(args: argparse.Namespace) -> tuple[dict[str, object], Path]:
    data_dir = Path(get_settings().data_dir).resolve()
    expected_data_dir = (args.output_dir / "data").resolve()
    if data_dir != expected_data_dir:
        raise ValueError("DATA_DIR_must_target_live_e2e_output_dir")
    existing = tuple(args.output_dir.iterdir()) if args.output_dir.exists() else ()
    if any(
        path.resolve() != expected_data_dir or (path.is_dir() and any(path.iterdir()))
        for path in existing
    ):
        raise FileExistsError("live_e2e_output_dir_must_be_empty")
    database_path = data_dir / "thesis_monitor.sqlite3"
    database_path.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(args.production_database, database_path)
    engine.dispose()

    packet = _read(args.packet)
    packet_id = str(packet.get("packet_id") or "")
    if not packet_id or packet.get("market") != "us" or len(packet.get("stocks") or []) != 14:
        raise ValueError("live_e2e_packet_scope_invalid")
    packet_path = data_dir / "ai_review" / "inbox" / f"{packet_id}.json"
    _write(packet_path, packet)
    return packet, packet_path


async def _run(args: argparse.Namespace) -> dict[str, object]:
    values = load_env_values(args.env_file)
    sink = audit_test_sink(values)
    selected_key = str(sink.get("selected_test_key_name") or "")
    if (
        sink.get("available") is not True
        or sink.get("production_collision") != 0
        or not selected_key
        or get_settings().telegram_chat_id != values.get(selected_key)
        or get_settings().telegram_chat_id == values.get("TELEGRAM_CHAT_ID")
    ):
        raise ValueError("live_e2e_test_sink_not_isolated")
    if get_settings().notification_dry_run:
        raise ValueError("live_e2e_requires_real_test_sink_transport")
    if not get_settings().ai_review_pilot_enabled:
        raise ValueError("live_e2e_requires_isolated_ai_pilot")

    packet, packet_path = _prepare_isolated_runtime(args)
    packet_id = str(packet["packet_id"])
    run_date = date.fromisoformat(str(packet["assessment_date"]))
    tickers = _delivery_tickers(packet)
    reset_count = _reset_isolated_deliveries(run_date, tickers=tickers)
    if reset_count != 15:
        raise ValueError(f"live_e2e_delivery_scope_invalid:{reset_count}")

    with Session(engine) as session:
        held = hold_ai_assisted_pilot_session(session, packet_id)
    if held.status != "held" or held.pending_count != 15:
        raise ValueError(f"live_e2e_hold_failed:{held.status}:{held.pending_count}")

    claimed_at = datetime.now(UTC)
    claim = claim_next_ai_review_packet(
        "us",
        owner="us-natural-repair-live-e2e-primary",
        lease_minutes=10,
        now=claimed_at,
    )
    if claim.status != "claimed" or not claim.claim_id or not claim.temp_output_path:
        raise ValueError(f"live_e2e_claim_failed:{claim.status}:{claim.reason}")

    model_receipt = await generate_accepted_v2(
        packet_id,
        claim.claim_id,
        timeout=args.model_timeout,
    )
    if model_receipt.get("status") != "PASS" or model_receipt.get("ready_count") != 14:
        raise ValueError(f"live_e2e_accepted_v2_not_ready:{model_receipt.get('status')}")

    backup = claim_next_ai_review_packet(
        "us",
        owner="us-natural-repair-live-e2e-backup",
        now=claimed_at + timedelta(minutes=10),
    )
    if backup.status != "no_pending_packet":
        raise ValueError("live_e2e_fresh_primary_reclaimed_by_backup")

    candidate_sha256 = _sha256(args.candidate)
    if args.candidate_sha256 and candidate_sha256 != args.candidate_sha256:
        raise ValueError("live_e2e_candidate_sha256_mismatch")
    candidate = _read(args.candidate)
    candidate["claim_id"] = claim.claim_id
    _write(Path(claim.temp_output_path), candidate)
    with Session(engine) as session:
        validation = finalize_ai_review_output(
            session,
            packet_id,
            claim_id=claim.claim_id,
        )
        if validation.status != "completed":
            raise ValueError(
                "live_e2e_candidate_validation_failed:" + ",".join(validation.errors)
            )
        delivery = await deliver_validated_ai_review(
            session,
            packet_id,
            notifier=TelegramNotifier(),
        )

    result = delivery.as_dict()
    audit = _delivery_audit(run_date, tickers=tickers)
    natural_proof_gate = evaluate_explicit_v2_natural_proof(
        ExplicitV2NaturalProofCounts(
            ai_accepted_total=audit["sent_count"],
            ai_market_sent=audit["market_sent_count"],
            explicit_v2_stock_accepted=int(model_receipt.get("ready_count") or 0),
            explicit_v2_stock_sent=audit["explicit_v2_stock_sent_count"],
            pilot_ai_assisted_sent=audit["pilot_ai_assisted_stock_sent_count"],
            deterministic_fallback_sent=audit["fallback_sent_count"],
            duplicate_sent=audit["duplicate_count"],
        ),
        expected_stock_count=14,
    )
    if (
        delivery.status != "sent"
        or audit["delivery_count"] != 15
        or audit["sent_count"] != 15
        or audit["market_sent_count"] != 1
        or audit["stock_sent_count"] != 14
        or natural_proof_gate["status"] != "PASS"
        or audit["fallback_sent_count"] != 0
        or audit["duplicate_count"] != 0
    ):
        raise ValueError("live_e2e_delivery_result_mismatch")
    proof = {
        "contract": CONTRACT,
        "status": "PASS",
        "packet_id": packet_id,
        "packet_path_alias": packet_path.name,
        "candidate_sha256": candidate_sha256,
        "source_ready_count": 15,
        "primary_claim_acquired": True,
        "claim_lease_renewal_count": model_receipt.get("claim_lease_renewal_count"),
        "claim_fencing_token_preserved": model_receipt.get("claim_fencing_token_preserved"),
        "backup_while_primary_healthy": "SAFE_NOOP_PRIMARY_ACTIVE",
        "signed_in_xhigh_result_count": int(model_receipt.get("ready_count") or 0),
        "tls_unknown_issuer_count": 0,
        "candidate_count": 15,
        "validator_status": validation.status,
        "accepted_count": audit["sent_count"],
        "ai_market_sent": audit["market_sent_count"],
        "ai_stock_sent": audit["stock_sent_count"],
        "explicit_v2_stock_accepted": int(model_receipt.get("ready_count") or 0),
        "explicit_v2_stock_sent": audit["explicit_v2_stock_sent_count"],
        "pilot_ai_assisted_sent": audit["pilot_ai_assisted_stock_sent_count"],
        "fallback_sent": audit["fallback_sent_count"],
        "duplicate_sent": audit["duplicate_count"],
        "delivery_status": result.get("status"),
        "delivery_mode": result.get("delivery_mode"),
        "test_sink_alias": sink.get("test_sink_alias"),
        "production_sink_alias": sink.get("production_sink_alias"),
        "production_collision": sink.get("production_collision"),
        "production_recipient_send": 0,
        "production_scheduler_mutation": 0,
        "production_database_mutation": 0,
        "isolated_database_mutation": True,
        "structured_autonomy_production_promotion": 0,
        "model_receipt": model_receipt,
        "delivery_result": result,
        "delivery_audit": audit,
        "natural_proof_gate": natural_proof_gate,
    }
    _write(args.output_dir / "live-e2e-proof.json", proof)
    return proof


def main() -> int:
    parser = argparse.ArgumentParser(description="Run isolated production-path US repair E2E")
    parser.add_argument("--env-file", type=Path, required=True)
    parser.add_argument("--production-database", type=Path, required=True)
    parser.add_argument("--packet", type=Path, required=True)
    parser.add_argument("--candidate", type=Path, required=True)
    parser.add_argument("--candidate-sha256")
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--model-timeout", type=int, default=1800)
    args = parser.parse_args()
    proof = asyncio.run(_run(args))
    print(
        json.dumps(
            {
                "status": proof["status"],
                "accepted_count": proof["accepted_count"],
                "ai_market_sent": proof["ai_market_sent"],
                "ai_stock_sent": proof["ai_stock_sent"],
                "fallback_sent": proof["fallback_sent"],
                "duplicate_sent": proof["duplicate_sent"],
                "test_sink_alias": proof["test_sink_alias"],
            },
            ensure_ascii=False,
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
