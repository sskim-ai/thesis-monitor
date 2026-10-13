"""Operational v2 envelope. The v1 and economic owner contracts remain intact."""
from datetime import date, datetime, time
from typing import Any, Literal
from zoneinfo import ZoneInfo

from app.services.unified_snapshot_contract import (
    ContractModel, SnapshotPolicy, digest, validate_stage,
)

CONTRACT = "unified-query-time-snapshot-v2"
STAGES = ("MARKET", "CORE", "A", "B", "B2", "VALIDATE", "RENDER", "DELIVER")
TIMES = {"us": (time(8, 10), time(8, 15), time(8, 20)),
         "kr": (time(16, 10), time(16, 15), time(16, 20))}


def scheduled_slots(market: str, day: date) -> tuple[datetime, ...]:
    return tuple(datetime.combine(day, value, ZoneInfo("Asia/Seoul")) for value in TIMES[market])


class StageResultV2(ContractModel):
    runtime_contract: Literal["unified-query-time-snapshot-v2"] = CONTRACT
    run_id: str
    generation_id: str
    snapshot_sha256: str
    request_sha256: str
    stage: Literal["MARKET", "CORE", "A", "B", "B2", "VALIDATE", "RENDER", "DELIVER"]
    status: Literal["PASS", "FAIL"]
    output: dict[str, Any]
    errors: tuple[str, ...] = ()


def validate_stage_v2(result: StageResultV2, request: dict) -> None:
    validate_stage(result, request)
    expected = request["snapshot"]["collection"]["production_envelope"]["generation_id"]
    if (result.runtime_contract != CONTRACT or request["contract"] != CONTRACT
            or result.generation_id != expected):
        raise ValueError("runtime_v2_generation_mismatch")
    prior = STAGES[:STAGES.index(result.stage)]
    if set(request["inputs"]) != set(prior):
        raise ValueError("runtime_v2_required_stage_omitted_or_reordered")
    for stage in prior:
        upstream = request["inputs"][stage]
        if (upstream["runtime_contract"] != CONTRACT or upstream["generation_id"] != expected
                or upstream["snapshot_sha256"] != result.snapshot_sha256
                or upstream["run_id"] != result.run_id or upstream["status"] != "PASS"
                or upstream["errors"]):
            raise ValueError("runtime_v2_upstream_binding_mismatch")


def validate_delivery_v2(output: dict, policy: SnapshotPolicy, request: dict) -> None:
    rows = output.get("receipts", [])
    dry = output.get("mode") == "DRY_RUN"
    expected_status = "DRY_RUN_NOT_SENT" if dry else "SENT"
    if (output.get("mode") not in {"DRY_RUN", "LIVE_AUTHORIZED"}
            or sorted(r.get("message_id", "") for r in rows) != sorted(policy.message_ids)
            or output.get("normal_messages_sent") is not (not dry)
            or any(r.get("status") != expected_status for r in rows)):
        raise ValueError("delivery_receipt_incomplete_or_uncertain")
    for row in rows:
        identity = {key: row[key] for key in (
            "run_id", "generation_id", "message_id", "destination_fingerprint", "content_sha256")}
        if row.get("dedup_sha256") != digest(identity):
            raise ValueError("runtime_v2_delivery_dedup_mismatch")
        messages = {m["message_id"]: m for m in request["inputs"]["RENDER"]["output"]["messages"]}
        if (row["run_id"] != request["run_id"]
                or row["generation_id"] != request["snapshot"]["collection"]["production_envelope"]["generation_id"]
                or row["content_sha256"] != digest(messages[row["message_id"]]["text"])
                or not row["destination_fingerprint"]):
            raise ValueError("runtime_v2_delivery_content_binding")
