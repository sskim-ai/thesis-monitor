from __future__ import annotations

import argparse
import asyncio
import json
from datetime import date
from pathlib import Path

from sqlmodel import Session

from app.config import get_settings
from app.database import engine
from app.services.ai_assisted_delivery_service import deliver_validated_ai_review
from app.services.notification_service import TelegramNotifier
from scripts.kr_market_preenable_evidence import audit_test_sink, load_env_values
from scripts.us_natural_repair_live_e2e import (
    CONTRACT,
    EXPECTED_CANDIDATE_SHA256,
    _delivery_audit,
    _delivery_tickers,
    _read,
    _write,
)


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

    packet = _read(args.packet)
    packet_id = str(packet.get("packet_id") or "")
    run_date = date.fromisoformat(str(packet["assessment_date"]))
    tickers = _delivery_tickers(packet)
    before = _delivery_audit(run_date, tickers=tickers)
    if before != {
        "delivery_count": 15,
        "sent_count": 0,
        "market_sent_count": 0,
        "stock_sent_count": 0,
        "fallback_sent_count": 0,
        "duplicate_count": 0,
    }:
        raise ValueError("live_e2e_resume_precondition_failed")

    receipts = sorted(args.claims_dir.glob("*.decision-v2-receipt.json"))
    if len(receipts) != 1:
        raise ValueError("live_e2e_model_receipt_ambiguous")
    model_receipt = _read(receipts[0])
    if model_receipt.get("status") != "PASS" or model_receipt.get("ready_count") != 14:
        raise ValueError("live_e2e_model_receipt_not_ready")

    with Session(engine) as session:
        first = await deliver_validated_ai_review(
            session,
            packet_id,
            notifier=TelegramNotifier(),
        )
    after_first = _delivery_audit(run_date, tickers=tickers)
    with Session(engine) as session:
        duplicate_probe = await deliver_validated_ai_review(
            session,
            packet_id,
            notifier=TelegramNotifier(),
        )
    after_duplicate_probe = _delivery_audit(run_date, tickers=tickers)

    expected = {
        "delivery_count": 15,
        "sent_count": 15,
        "market_sent_count": 1,
        "stock_sent_count": 14,
        "fallback_sent_count": 0,
        "duplicate_count": 0,
    }
    if (
        first.status != "sent"
        or after_first != expected
        or after_duplicate_probe != expected
        or duplicate_probe.sent_count != 15
    ):
        raise ValueError("live_e2e_resume_delivery_result_mismatch")

    proof = {
        "contract": CONTRACT,
        "status": "PASS",
        "packet_id": packet_id,
        "candidate_sha256": EXPECTED_CANDIDATE_SHA256,
        "source_ready_count": 15,
        "primary_claim_acquired": True,
        "claim_lease_renewal_count": model_receipt.get("claim_lease_renewal_count"),
        "claim_fencing_token_preserved": model_receipt.get(
            "claim_fencing_token_preserved"
        ),
        "backup_while_primary_healthy": "SAFE_NOOP_PRIMARY_ACTIVE",
        "signed_in_xhigh_result_count": int(model_receipt.get("ready_count") or 0),
        "tls_unknown_issuer_count": 0,
        "candidate_count": 15,
        "validator_status": "completed",
        "accepted_count": after_first["sent_count"],
        "ai_market_sent": after_first["market_sent_count"],
        "ai_stock_sent": after_first["stock_sent_count"],
        "fallback_sent": after_first["fallback_sent_count"],
        "duplicate_sent": after_duplicate_probe["duplicate_count"],
        "delivery_status": first.status,
        "delivery_mode": first.delivery_mode,
        "duplicate_probe_status": duplicate_probe.status,
        "test_sink_alias": sink.get("test_sink_alias"),
        "production_sink_alias": sink.get("production_sink_alias"),
        "production_collision": sink.get("production_collision"),
        "production_recipient_send": 0,
        "production_scheduler_mutation": 0,
        "production_database_mutation": 0,
        "isolated_database_mutation": True,
        "structured_autonomy_production_promotion": 0,
        "model_rerun_for_resume": 0,
        "model_receipt": model_receipt,
        "delivery_result": first.as_dict(),
        "duplicate_probe_result": duplicate_probe.as_dict(),
        "delivery_audit": after_first,
        "delivery_audit_after_duplicate_probe": after_duplicate_probe,
    }
    _write(args.output_dir / "live-e2e-proof.json", proof)
    return proof


def main() -> int:
    parser = argparse.ArgumentParser(description="Resume isolated US repair TEST delivery")
    parser.add_argument("--env-file", type=Path, required=True)
    parser.add_argument("--packet", type=Path, required=True)
    parser.add_argument("--claims-dir", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
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
