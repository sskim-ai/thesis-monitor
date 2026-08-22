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
from app.services.delta_first_rendering_service import DeltaFirstRenderPlan
from app.services.ai_reasoning_quality_service import (
    runtime_message_quality_receipt,
    verify_runtime_message_quality_receipt,
)
from app.services.ai_review_service import quantitative_grounding_report
from app.services.notification_service import (
    AI_ASSISTED_PILOT_METADATA_KEY,
    TELEGRAM_DELIVERY_METADATA_KEY,
    TelegramNotifier,
    dispatch_pending_notifications,
)


KST = ZoneInfo("Asia/Seoul")
PILOT_MODE = "ai_assisted_single_delivery"
PILOT_VERSION = "ai-assisted-pilot-v3"
PILOT_RENDERER_VERSION = "ai-assisted-pilot-renderer-v3"
AI_ARCHIVE_CONTRACT_VERSION = "ai-assisted-archive-v2"
AI_ARTIFACT_MANIFEST_VERSION = "runtime-quality-receipt-v2"
PILOT_MARKERS = {"us": "__DAILY_DIGEST__", "kr": "__DAILY_DIGEST_KR__"}
MAX_PERSISTED_DELIVERY_RETRIES = 3
PilotMarket = Literal["us", "kr"]

AI_SUCCESS_REQUIRED_ARTIFACTS = (
    "packet.json",
    "ai-review.json",
    "market-context.json",
    "market-review.json",
    "market-numeric-claims.json",
    "portfolio-transmission.json",
    "chart-context.json",
    "chart-transition.json",
    "quantitative-grounding-report.json",
    "deterministic-messages.json",
    "ai-assisted-messages.json",
    "message-quality-receipt.json",
    "validation-result.json",
    "delivery-result.json",
)


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


def _pilot_state_path() -> Path:
    return _pilot_root() / "state-v3.json"


def _pilot_state() -> dict[str, object]:
    path = _pilot_state_path()
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
    _atomic_json(_pilot_state_path(), state)


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


def _output_path(packet: dict[str, object]) -> Path | None:
    packet_id = str(packet["packet_id"])
    knowledge = packet.get("knowledge")
    chart_knowledge = packet.get("chart_knowledge")
    expected = {
        "packet_id": packet_id,
        "schema_version": str(packet.get("output_schema_version") or "4"),
        "analysis_policy_version": str(packet.get("analysis_policy_version") or ""),
        "knowledge_version": str(
            knowledge.get("version") if isinstance(knowledge, dict) else ""
        ),
        "knowledge_sha256": str(
            knowledge.get("sha256") if isinstance(knowledge, dict) else ""
        ),
        "chart_knowledge_version": str(
            chart_knowledge.get("version")
            if isinstance(chart_knowledge, dict)
            else ""
        ),
        "chart_knowledge_sha256": str(
            chart_knowledge.get("sha256")
            if isinstance(chart_knowledge, dict)
            else ""
        ),
    }
    candidates = sorted(
        (Path(get_settings().data_dir) / "ai_review" / "outbox").glob(
            f"{packet_id}--*.json"
        ),
        reverse=True,
    )
    for candidate in candidates:
        try:
            value = _read_json(candidate)
        except (OSError, ValueError, json.JSONDecodeError):
            continue
        if all(str(value.get(key) or "") == wanted for key, wanted in expected.items()):
            return candidate
    return None


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


def _payload_cash_flow_context(payload: dict[str, object]) -> dict[str, object]:
    analysis = payload.get("analysis_context")
    if not isinstance(analysis, dict):
        return {}
    value = analysis.get("cash_flow_user_visible")
    return dict(value) if isinstance(value, dict) else {}


def _packet_cash_flow_context(
    packet: dict[str, object], ticker: str
) -> dict[str, object]:
    for stock in packet.get("stocks", []):
        if not isinstance(stock, dict) or str(stock.get("ticker")) != ticker:
            continue
        value = stock.get("cash_flow_user_visible")
        return dict(value) if isinstance(value, dict) else {}
    return {}


def _payload_working_capital_context(payload: dict[str, object]) -> dict[str, object]:
    analysis = payload.get("analysis_context")
    if not isinstance(analysis, dict):
        return {}
    value = analysis.get("working_capital_user_visible")
    return dict(value) if isinstance(value, dict) else {}


def _align_working_capital_packet_id(
    payload: dict[str, object], packet_id: str
) -> None:
    analysis = payload.get("analysis_context")
    if not isinstance(analysis, dict):
        return
    context = analysis.get("working_capital_user_visible")
    if isinstance(context, dict):
        context["packet_id"] = packet_id


def _packet_working_capital_context(
    packet: dict[str, object], ticker: str
) -> dict[str, object]:
    for stock in packet.get("stocks", []):
        if not isinstance(stock, dict) or str(stock.get("ticker")) != ticker:
            continue
        value = stock.get("working_capital_user_visible")
        return dict(value) if isinstance(value, dict) else {}
    return {}


def _working_capital_delivery_metadata(
    packet: dict[str, object], ticker: str, deterministic: dict[str, object]
) -> dict[str, object]:
    packet_context = _packet_working_capital_context(packet, ticker)
    fallback_context = _payload_working_capital_context(deterministic)
    if packet_context or fallback_context:
        parity_fields = (
            "working_capital_user_visible_context_id",
            "packet_id",
            "metric_family",
            "semantic_scope",
            "balance_date",
            "relation_id",
            "relation_family",
            "direction",
            "display_value",
            "selected_fact_ids",
            "resolved_unknowns",
            "suppression_reasons",
            "user_visible_enabled",
        )
        if any(packet_context.get(key) != fallback_context.get(key) for key in parity_fields):
            raise ValueError(f"working_capital_ai_fallback_context_mismatch:{ticker}")
    source = packet_context or fallback_context
    return {
        "working_capital_user_visible_mode": source.get("feature_mode", "OFF"),
        "working_capital_user_visible_context_id": source.get(
            "working_capital_user_visible_context_id"
        ),
        "working_capital_user_visible_enabled": (
            source.get("user_visible_enabled") is True
        ),
        "working_capital_fact_ids": list(source.get("selected_fact_ids") or []),
        "working_capital_relation_id": source.get("relation_id"),
        "working_capital_metric_family": source.get("metric_family"),
    }


def _cash_flow_delivery_metadata(
    packet: dict[str, object], ticker: str, deterministic: dict[str, object]
) -> dict[str, object]:
    packet_context = _packet_cash_flow_context(packet, ticker)
    fallback_context = _payload_cash_flow_context(deterministic)
    if packet_context or fallback_context:
        parity_fields = (
            "cash_flow_user_visible_context_id",
            "selection_state",
            "selection_reason",
            "display_reason",
            "evidence_signature",
            "primary_fact_ref",
            "primary_period",
            "financial_currency",
            "freshness_state",
            "suppressed_baseline_claim_ids",
            "user_visible_enabled",
        )
        if any(packet_context.get(key) != fallback_context.get(key) for key in parity_fields):
            raise ValueError(f"cash_flow_ai_fallback_context_mismatch:{ticker}")
    source = packet_context or fallback_context
    return {
        "cash_flow_user_visible_mode": source.get("rollout_mode", "OFF"),
        "cash_flow_user_visible_context_id": source.get(
            "cash_flow_user_visible_context_id"
        ),
        "cash_flow_user_visible_enabled": source.get("user_visible_enabled") is True,
        "cash_flow_fact_ids": [
            source[key]
            for key in ("ocf_fact_ref", "ppe_capex_fact_ref", "fcf_fact_ref")
            if source.get(key)
        ],
        "cash_flow_suppressed_baseline_claim_ids": list(
            source.get("suppressed_baseline_claim_ids") or []
        ),
    }


def _cash_flow_run_metadata(packet: dict[str, object]) -> dict[str, object]:
    contexts = [
        item.get("cash_flow_user_visible")
        for item in packet.get("stocks", [])
        if isinstance(item, dict)
        and isinstance(item.get("cash_flow_user_visible"), dict)
    ]
    selected = [
        item
        for item in contexts
        if isinstance(item, dict) and item.get("user_visible_enabled") is True
    ]
    mode = str(contexts[0].get("rollout_mode") or "OFF") if contexts else "OFF"
    return {
        "cash_flow_user_visible_mode": mode,
        "cash_flow_selected_count": len(selected),
        "cash_flow_selected_tickers": [
            str(item.get("ticker") or "")
            for item in packet.get("stocks", [])
            if isinstance(item, dict)
            and isinstance(item.get("cash_flow_user_visible"), dict)
            and item["cash_flow_user_visible"].get("user_visible_enabled") is True
        ],
        "cash_flow_context_ids": [
            item["cash_flow_user_visible_context_id"]
            for item in selected
            if item.get("cash_flow_user_visible_context_id")
        ],
        "cash_flow_fact_ids_used": sorted(
            {
                str(item[key])
                for item in selected
                for key in ("ocf_fact_ref", "ppe_capex_fact_ref", "fcf_fact_ref")
                if item.get(key)
            }
        ),
        "cash_flow_suppressed_count": sum(
            isinstance(item, dict) and item.get("user_visible_enabled") is not True
            for item in contexts
        ),
    }


def _working_capital_run_metadata(packet: dict[str, object]) -> dict[str, object]:
    contexts = [
        item.get("working_capital_user_visible")
        for item in packet.get("stocks", [])
        if isinstance(item, dict)
        and isinstance(item.get("working_capital_user_visible"), dict)
    ]
    selected = [
        item
        for item in contexts
        if isinstance(item, dict) and item.get("user_visible_enabled") is True
    ]
    mode = str(selected[0].get("feature_mode") or "OFF") if selected else "OFF"
    return {
        "working_capital_user_visible_mode": mode,
        "working_capital_selected_count": len(selected),
        "working_capital_context_ids": [
            item["working_capital_user_visible_context_id"]
            for item in selected
            if item.get("working_capital_user_visible_context_id")
        ],
        "working_capital_fact_ids": sorted(
            {
                str(fact_id)
                for item in selected
                for fact_id in item.get("selected_fact_ids") or ()
            }
        ),
        "working_capital_metric_families": sorted(
            {str(item.get("metric_family")) for item in selected}
        ),
    }


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


def _file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _verified_ai_archive_artifacts(packet: dict[str, object]) -> list[dict[str, str]]:
    packet_id = str(packet["packet_id"])
    archive_dir = _archive_directory(packet)
    artifacts: list[dict[str, str]] = []
    for filename in AI_SUCCESS_REQUIRED_ARTIFACTS:
        path = archive_dir / filename
        value = json.loads(path.read_text(encoding="utf-8"))
        if isinstance(value, dict):
            archived_packet_id = value.get("packet_id")
            if archived_packet_id is not None and str(archived_packet_id) != packet_id:
                raise ValueError(f"Archive packet mismatch: {filename}")
        artifacts.append({"filename": filename, "sha256": _file_sha256(path)})
    delivery = _read_json(archive_dir / "delivery-result.json")
    if (
        delivery.get("delivery_mode") != "ai_assisted"
        or delivery.get("status") != "sent"
        or int(delivery.get("pending_count") or 0) != 0
        or int(delivery.get("sent_count") or 0)
        != int(delivery.get("delivery_count") or 0)
    ):
        raise ValueError("AI delivery archive is not complete")
    validation = _read_json(archive_dir / "validation-result.json")
    if validation.get("status") != "passed":
        raise ValueError("AI validation archive is not passed")
    receipt = _read_json(archive_dir / "message-quality-receipt.json")
    receipt_sha256 = _file_sha256(archive_dir / "message-quality-receipt.json")
    output = AIDailyReviewOutput.model_validate(_read_json(archive_dir / "ai-review.json"))
    archived_messages = _read_json(archive_dir / "ai-assisted-messages.json").get(
        "messages"
    )
    if not isinstance(archived_messages, list) or not verify_runtime_message_quality_receipt(
        receipt,
        _read_json(archive_dir / "packet.json"),
        output,
        [item for item in archived_messages if isinstance(item, dict)],
    ):
        raise ValueError("AI message quality receipt does not match archived payload")
    if (
        delivery.get("message_quality_receipt_sha256") != receipt_sha256
        or delivery.get("rendered_payload_set_sha256")
        != receipt.get("rendered_payload_set_sha256")
    ):
        raise ValueError("AI delivery archive receipt integrity mismatch")
    return artifacts


def _verified_legacy_archive_artifacts(
    packet: dict[str, object],
    marker: dict[str, object],
) -> list[dict[str, str]]:
    packet_id = str(packet["packet_id"])
    archive_dir = _archive_directory(packet)
    manifest = marker.get("artifacts")
    if not isinstance(manifest, list) or not manifest:
        raise ValueError("Legacy archive artifact manifest is unavailable")
    verified: list[dict[str, str]] = []
    for item in manifest:
        if not isinstance(item, dict):
            raise ValueError("Legacy archive artifact entry is invalid")
        filename = str(item.get("filename") or "")
        expected = str(item.get("sha256") or "")
        if not filename or not expected:
            raise ValueError("Legacy archive artifact identity is invalid")
        path = archive_dir / filename
        if not path.exists() or _file_sha256(path) != expected:
            raise ValueError(f"Legacy archive artifact mismatch: {filename}")
        value = json.loads(path.read_text(encoding="utf-8"))
        if (
            isinstance(value, dict)
            and value.get("packet_id") is not None
            and str(value.get("packet_id")) != packet_id
        ):
            raise ValueError(f"Legacy archive packet mismatch: {filename}")
        verified.append({"filename": filename, "sha256": expected})
    delivery = _read_json(archive_dir / "delivery-result.json")
    validation = _read_json(archive_dir / "validation-result.json")
    if (
        delivery.get("delivery_mode") != "ai_assisted"
        or delivery.get("status") != "sent"
        or int(delivery.get("pending_count") or 0) != 0
        or validation.get("status") != "passed"
    ):
        raise ValueError("Legacy AI archive is not complete")
    return verified


def _write_ai_archive_completion_marker(
    packet: dict[str, object],
    output: AIDailyReviewOutput,
    *,
    completed_at: datetime,
) -> dict[str, object]:
    archive_dir = _archive_directory(packet)
    marker_path = archive_dir / "archive-complete.json"
    marker = {
        "packet_id": packet["packet_id"],
        "archive_contract_version": AI_ARCHIVE_CONTRACT_VERSION,
        "required_artifact_manifest_version": AI_ARTIFACT_MANIFEST_VERSION,
        "runtime_quality_gate_version": "runtime-message-quality-v1",
        "pilot_version": PILOT_VERSION,
        "renderer_version": PILOT_RENDERER_VERSION,
        "analysis_policy_version": output.analysis_policy_version,
        "schema_version": output.schema_version,
        "validator_status": "passed",
        "delivery_status": "sent",
        "artifacts": _verified_ai_archive_artifacts(packet),
        "completed_at": completed_at.isoformat(),
    }
    _atomic_json(marker_path, marker)
    persisted = _read_json(marker_path)
    if (
        persisted.get("packet_id") != packet["packet_id"]
        or persisted.get("validator_status") != "passed"
        or persisted.get("delivery_status") != "sent"
        or persisted.get("artifacts") != marker["artifacts"]
    ):
        raise ValueError("AI archive completion marker verification failed")
    return persisted


def _ai_archive_complete(packet: dict[str, object]) -> bool:
    marker_path = _archive_directory(packet) / "archive-complete.json"
    if not marker_path.exists():
        return False
    try:
        marker = _read_json(marker_path)
        artifacts = (
            _verified_ai_archive_artifacts(packet)
            if marker.get("archive_contract_version")
            == AI_ARCHIVE_CONTRACT_VERSION
            else _verified_legacy_archive_artifacts(packet, marker)
        )
    except (OSError, ValueError, json.JSONDecodeError):
        return False
    return bool(
        marker.get("packet_id") == packet["packet_id"]
        and marker.get("validator_status") == "passed"
        and marker.get("delivery_status") == "sent"
        and marker.get("artifacts") == artifacts
    )


def _persisted_quality_integrity_errors(
    deliveries: list[NotificationDelivery],
    packet_id: str,
    receipt_path: Path,
    receipt: dict[str, object],
) -> list[str]:
    if not receipt_path.exists():
        return ["quality_receipt_file_missing"]
    actual_receipt_sha = _file_sha256(receipt_path)
    rendered_sha = str(receipt.get("rendered_payload_set_sha256") or "")
    errors: list[str] = []
    matched = 0
    receipt_shas: set[str] = set()
    rendered_shas: set[str] = set()
    for delivery in deliveries:
        try:
            payload = json.loads(delivery.payload)
        except json.JSONDecodeError:
            continue
        if not isinstance(payload, dict):
            continue
        metadata = _pilot_metadata(payload)
        if metadata.get("packet_id") != packet_id or metadata.get("state") not in {
            "ai_assisted_pending",
            "ai_assisted_sent",
        }:
            continue
        matched += 1
        metadata_receipt_sha = str(
            metadata.get("message_quality_receipt_sha256") or ""
        )
        metadata_rendered_sha = str(
            metadata.get("rendered_payload_set_sha256") or ""
        )
        receipt_shas.add(metadata_receipt_sha)
        rendered_shas.add(metadata_rendered_sha)
        if metadata_receipt_sha != actual_receipt_sha:
            errors.append("delivery_receipt_file_sha_mismatch")
        if metadata_rendered_sha != rendered_sha:
            errors.append("delivery_rendered_payload_set_sha_mismatch")
    if matched == 0:
        errors.append("persisted_ai_delivery_metadata_missing")
    if len(receipt_shas) != 1:
        errors.append("delivery_receipt_sha_not_uniform")
    if len(rendered_shas) != 1:
        errors.append("delivery_rendered_payload_sha_not_uniform")
    return list(dict.fromkeys(errors))


def _hold_quality_integrity_rejection(
    session: Session,
    packet: dict[str, object],
    deliveries: list[NotificationDelivery],
    *,
    reason: str,
    rejected_at: datetime,
) -> dict[str, object]:
    packet_id = str(packet["packet_id"])
    held_count = 0
    sent_count = 0
    matched_deliveries: list[tuple[NotificationDelivery, dict[str, object]]] = []
    for delivery in deliveries:
        try:
            payload = json.loads(delivery.payload)
        except json.JSONDecodeError:
            continue
        if not isinstance(payload, dict):
            continue
        metadata = _pilot_metadata(payload)
        if metadata.get("packet_id") != packet_id:
            continue
        matched_deliveries.append((delivery, payload))
        if delivery.status == "sent" or metadata.get("state") == "ai_assisted_sent":
            sent_count += 1
    partial_delivery = sent_count > 0
    integrity_state = (
        "post_partial_delivery_rejected" if partial_delivery else "rejected"
    )
    for delivery, payload in matched_deliveries:
        metadata = _pilot_metadata(payload)
        already_sent = (
            delivery.status == "sent" or metadata.get("state") == "ai_assisted_sent"
        )
        if partial_delivery:
            if not already_sent:
                metadata["state"] = "partial_integrity_rejected"
                metadata["fallback_eligible"] = False
            metadata["manual_intervention_required"] = True
        else:
            metadata["state"] = "held"
            metadata["fallback_eligible"] = True
        metadata["quality_integrity_state"] = integrity_state
        metadata["quality_integrity_reason"] = reason
        metadata["quality_integrity_rejected_at"] = rejected_at.isoformat()
        payload[AI_ASSISTED_PILOT_METADATA_KEY] = metadata
        delivery.payload = json.dumps(payload, ensure_ascii=False)
        if not already_sent:
            delivery.status = "pending"
        session.add(delivery)
        if not already_sent and not partial_delivery:
            held_count += 1
    session.commit()
    _atomic_json(
        _archive_directory(packet) / "quality-receipt-integrity-error.json",
        {
            "packet_id": packet_id,
            "status": integrity_state,
            "reason": reason,
            "integrity_failure_timing": (
                "post_partial_delivery" if partial_delivery else "pre_send"
            ),
            "ai_sent_count": sent_count,
            "rejected_ai_sent": sent_count > 0,
            "held_count": held_count,
            "fallback_eligible": not partial_delivery and held_count > 0,
            "manual_intervention_required": partial_delivery,
            "full_deterministic_fallback_recorded": False,
            "analysis_rerun": False,
            "packet_regenerated": False,
            "binder_rerun": False,
            "validator_rerun": False,
            "renderer_rerun": False,
            "recorded_at": rejected_at.isoformat(),
        },
    )
    return {
        "integrity_state": integrity_state,
        "partial_delivery": partial_delivery,
        "sent_count": sent_count,
        "held_count": held_count,
        "fallback_eligible": not partial_delivery and held_count > 0,
    }


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
            _align_working_capital_packet_id(deterministic, packet_id)
            payload[AI_ASSISTED_PILOT_METADATA_KEY] = {
                "pilot_mode": PILOT_MODE,
                "pilot_version": PILOT_VERSION,
                "renderer_version": PILOT_RENDERER_VERSION,
                "packet_id": packet_id,
                "market": market,
                "assessment_date": packet["assessment_date"],
                "state": "held",
                "fallback_eligible": True,
                "held_at": now.isoformat(),
                "deterministic_payload": deterministic,
                **_cash_flow_delivery_metadata(
                    packet, delivery.ticker, deterministic
                ),
                **_working_capital_delivery_metadata(
                    packet, delivery.ticker, deterministic
                ),
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


def record_ai_validation_rejection(
    session: Session,
    packet_id: str,
    *,
    errors: tuple[str, ...] | list[str],
    rejected_at: datetime | None = None,
) -> PilotDeliveryResult:
    """Preserve deterministic fallback eligibility after an AI final reject."""
    packet = _read_json(_packet_path(packet_id))
    market = str(packet["market"])
    current = (rejected_at or datetime.now(KST)).astimezone(KST)
    held_count = 0
    with _pilot_lock(packet_id):
        for delivery in _session_deliveries(session, packet):
            try:
                payload = json.loads(delivery.payload)
            except json.JSONDecodeError:
                continue
            if not isinstance(payload, dict):
                continue
            metadata = _pilot_metadata(payload)
            if (
                metadata.get("packet_id") != packet_id
                or metadata.get("state") != "held"
            ):
                continue
            metadata["fallback_eligible"] = True
            metadata["ai_validation_state"] = "rejected"
            metadata["ai_validation_rejected_at"] = current.isoformat()
            metadata["ai_validation_errors"] = list(errors)
            payload[AI_ASSISTED_PILOT_METADATA_KEY] = metadata
            delivery.payload = json.dumps(payload, ensure_ascii=False)
            session.add(delivery)
            held_count += 1
        session.commit()
        _atomic_json(
            _archive_directory(packet) / "validation-result.json",
            {
                "packet_id": packet_id,
                "status": "rejected",
                "errors": list(errors),
                "rejected_ai_sent": False,
                "fallback_eligibility_preserved": held_count > 0,
                "recorded_at": current.isoformat(),
            },
        )
    return PilotDeliveryResult(
        status="fallback_preserved" if held_count else "no_held_session",
        market=market,
        packet_id=packet_id,
        delivery_mode="held",
        pending_count=held_count,
        reason="ai_validation_rejected",
    )


def _bullets(values: list[str], empty: str | None = None) -> str:
    items = [f"• {value}" for value in values if value.strip()]
    if not items and empty:
        items.append(f"• {empty}")
    return "\n".join(items)


def _deterministic_blocks(text: str) -> list[str]:
    return [block.strip() for block in text.split("\n\n") if block.strip()]


def _first_block(blocks: list[str], prefix: str) -> str | None:
    return next((block for block in blocks if block.startswith(prefix)), None)


def _render_ai_market_message(
    deterministic_text: str,
    review: AIMarketReview,
    *,
    market_context: dict[str, object],
    market: str,
    pilot_day: int,
    target_days: int,
) -> str:
    market_label = "US" if market == "us" else "KR"
    title = "미국시장 점검" if market == "us" else "한국시장 마감"
    unknowns = _bullets(review.unknowns)
    required_market_fact_ids = {
        str(item) for item in market_context.get("required_market_fact_ids", [])
    }
    night_changes = [
        item
        for item in review.important_changes
        if set(item.fact_ids) & required_market_fact_ids
    ]
    changes = _bullets(
        [
            item.text.strip()
            for item in review.important_changes
            if item.text.strip() and item not in night_changes
        ]
    )
    group_labels = {
        str(item.get("group_key")): str(item.get("label") or item.get("group_key"))
        for item in market_context.get("portfolio_exposure_groups", [])
        if isinstance(item, dict) and item.get("group_key")
    }
    transmissions = _bullets(
        [
            f"{group_labels.get(item.portfolio_group, item.portfolio_group)}: "
            f"{item.text.strip()}"
            for item in review.portfolio_transmission
            if item.text.strip()
        ]
    )
    next_checks = _bullets(
        [item.text.strip() for item in review.next_checks if item.text.strip()]
    )
    blocks = _deterministic_blocks(deterministic_text)
    cautions = _first_block(blocks, "⚠️ 데이터 주의")
    sections = [
        f"🤖 AI 보조 {title} · {market_label} Pilot {pilot_day}/{target_days}",
        f"🎯 오늘 시장 한 줄\n{review.core_judgment.text.strip()}",
    ]
    if changes:
        sections.append(f"📈 실제 변화\n{changes}")
    if market == "us":
        rendered_night_changes = _bullets(
            [item.text.strip() for item in night_changes if item.text.strip()]
        )
        night_cautions = _bullets(
            [
                str(item)
                for item in market_context.get("night_futures_cautions", [])
                if str(item).strip()
            ]
        )
        if rendered_night_changes:
            sections.append(f"🌙 한국 개장 전 신호\n{rendered_night_changes}")
        elif night_cautions:
            sections.append(f"🌙 한국 개장 전 신호\n{night_cautions}")
    sections.append(f"🧭 시장 구조\n{review.market_context.text.strip()}")
    if transmissions:
        sections.append(f"🔗 모니터링 종목에 미치는 영향\n{transmissions}")
    if next_checks:
        sections.append(f"📌 다음 확인\n{next_checks}")
    fallback_caution = (
        "• 일부 시장 데이터의 최신성이 부족해 "
        "관련 판단 강도를 낮춥니다."
        if cautions
        else ""
    )
    caution_parts = (
        [unknowns] if unknowns else ([fallback_caution] if fallback_caution else [])
    )
    if caution_parts:
        normalized_cautions = [
            part.removeprefix("⚠️ 데이터 주의\n") for part in caution_parts
        ]
        caution_text = "\n".join(normalized_cautions)
        sections.append(f"⚠️ 데이터 주의\n{caution_text}")
    return "\n\n".join(sections)


def _render_ai_stock_message(
    deterministic_text: str,
    review: AIStockReview,
    *,
    market: str,
    pilot_day: int,
    target_days: int,
    render_plan: DeltaFirstRenderPlan | None = None,
) -> str:
    market_label = "US" if market == "us" else "KR"
    positioning_heading = "📊 거래량·포지셔닝" if market == "us" else "📊 수급"
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
                "🚨 오늘 새 경고",
                "⚠️ 기존 경고",
                "⚠️ 데이터 주의",
            )
        )
    ]
    standard_sections = [
        f"🤖 AI 보조 종목 점검 · {market_label} Pilot {pilot_day}/{target_days}",
        "\n".join([company, official, *fixed_context]),
        f"🎯 핵심 판단\n{review.core_judgment.text.strip()}",
        f"📈 사업·실적\n{review.business_earnings.text.strip()}",
        (
            "💰 가격·포지셔닝\n"
            f"{review.price_positioning.text.strip()}\n"
            f"• 신규 관찰자: {review.price_positioning.new_observer_view.strip()}\n"
            f"• 보유자: {review.price_positioning.holder_view.strip()}"
        ),
        f"{positioning_heading}\n{review.supply_analysis.text.strip()}",
        f"📐 Valuation\n{review.valuation_analysis.text.strip()}",
    ]
    if render_plan is None:
        sections = standard_sections
        sections.extend(deterministic_details)
        priority_watch = _bullets(review.priority_watch)
        if priority_watch:
            sections.append(f"👁 핵심 감시\n{priority_watch}")
        next_checks = _bullets(review.next_checks)
        if next_checks:
            sections.append(f"📌 다음 확인\n{next_checks}")
        if review.unknowns:
            sections.append(f"⚠️ 미확인\n{_bullets(review.unknowns)}")
        return "\n\n".join(section for section in sections if section.strip())

    header = standard_sections[0]
    adaptive_context = [company, official, *fixed_context]
    if render_plan.material_delta != "none":
        adaptive_context.append(f"오늘 관찰 변화: {render_plan.today_change_label}")
    context = "\n".join(adaptive_context)
    adaptive_sections = {
        "core": standard_sections[2],
        "business": standard_sections[3],
        "price": standard_sections[4],
        "supply": standard_sections[5],
        "valuation": standard_sections[6],
        "warnings": "\n\n".join(deterministic_details),
        "priority_watch": (
            f"👁 핵심 감시\n{_bullets(review.priority_watch)}"
            if review.priority_watch
            else ""
        ),
        "next": (
            f"📌 다음 확인\n{_bullets(review.next_checks)}"
            if review.next_checks
            else ""
        ),
        "unknown": (
            f"⚠️ 미확인\n{_bullets(review.unknowns)}" if review.unknowns else ""
        ),
    }
    sections = [
        header,
        context,
        *(adaptive_sections.get(name, "") for name in render_plan.section_order),
    ]
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
    if sent and delivery_mode == "ai_assisted":
        packet = _read_json(_packet_path(packet_id))
        if not _ai_archive_complete(packet):
            raise ValueError("Pilot success requires a verified archive completion marker")
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
    output_path = _output_path(packet)
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
    _atomic_json(archive_dir / "market-context.json", packet.get("market_context", {}))
    _atomic_json(
        archive_dir / "market-review.json",
        output.market_review.model_dump(mode="json"),
    )
    _atomic_json(
        archive_dir / "market-numeric-claims.json",
        [item.model_dump(mode="json") for item in output.market_review.numeric_claims],
    )
    night_audit = copy.deepcopy(
        packet.get("market_context", {}).get("night_futures_audit", {})
        if isinstance(packet.get("market_context"), dict)
        else {}
    )
    if isinstance(night_audit, dict):
        products = night_audit.get("products", [])
        used_fact_ids = set(output.market_review.facts_used)
        claimed_fact_ids = {
            item.fact_id for item in output.market_review.numeric_claims
        }
        for product in (products if isinstance(products, list) else []):
            if not isinstance(product, dict):
                continue
            fact_id = str(product.get("fact_id") or "")
            product["ai_facts_used"] = fact_id in used_fact_ids
            product["numeric_claim_included"] = fact_id in claimed_fact_ids
            product["rendered_in_telegram"] = False
    _atomic_json(
        archive_dir / "portfolio-transmission.json",
        [
            item.model_dump(mode="json")
            for item in output.market_review.portfolio_transmission
        ],
    )
    _atomic_json(
        archive_dir / "chart-context.json",
        {
            "packet_id": packet_id,
            "stocks": [
                {
                    "ticker": item.get("ticker"),
                    "chart_context": item.get("chart_context", {}),
                }
                for item in packet.get("stocks", [])
                if isinstance(item, dict)
            ],
        },
    )
    _atomic_json(
        archive_dir / "chart-transition.json",
        {
            "packet_id": packet_id,
            "stocks": [
                {
                    "ticker": item.get("ticker"),
                    "price_transition": (
                        item.get("chart_context", {}).get("price_transition", {})
                        if isinstance(item.get("chart_context"), dict)
                        else {}
                    ),
                }
                for item in packet.get("stocks", [])
                if isinstance(item, dict)
            ],
        },
    )
    _atomic_json(
        archive_dir / "quantitative-grounding-report.json",
        quantitative_grounding_report(packet, output),
    )
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
        if any(
            _pilot_metadata(payload).get("quality_integrity_state")
            in {"rejected", "post_partial_delivery_rejected"}
            for delivery in deliveries
            if isinstance((payload := json.loads(delivery.payload)), dict)
        ):
            return PilotDeliveryResult(
                status="quality_receipt_invalid",
                market=market,
                packet_id=packet_id,
                delivery_mode=(
                    "partial_integrity"
                    if any(
                        _pilot_metadata(payload).get("quality_integrity_state")
                        == "post_partial_delivery_rejected"
                        for delivery in deliveries
                        if isinstance(
                            (payload := json.loads(delivery.payload)), dict
                        )
                    )
                    else "held"
                ),
                pending_count=sum(delivery.status == "pending" for delivery in deliveries),
                reason="quality_integrity_rejected_requires_fallback",
            )
        prepared_ids: set[int] = set()
        prepared_payloads: list[tuple[NotificationDelivery, dict[str, object]]] = []
        reused_persisted_payload = False
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
                reused_persisted_payload = True
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
                    market_context=(
                        packet.get("market_context")
                        if isinstance(packet.get("market_context"), dict)
                        else {}
                    ),
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
                "renderer_version": PILOT_RENDERER_VERSION,
                "packet_id": packet_id,
                "market": market,
                "assessment_date": packet["assessment_date"],
                "state": "ai_assisted_pending",
                "fallback_eligible": False,
                "delivery_identity": identity,
                "deterministic_payload": deterministic,
                "prepared_at": current.isoformat(),
                "persisted_delivery_retry_count": 0,
                **_cash_flow_delivery_metadata(
                    packet, delivery.ticker, deterministic
                ),
            }
            prepared_payloads.append((delivery, new_payload))
            if delivery.id is not None:
                prepared_ids.add(delivery.id)
            final_messages.append(
                {
                    "delivery_id": delivery.id,
                    "ticker": delivery.ticker,
                    "logical_identity": identity,
                    "text": text,
                    "cash_flow_user_visible_context_id": _packet_cash_flow_context(
                        packet, delivery.ticker
                    ).get("cash_flow_user_visible_context_id"),
                    "working_capital_user_visible_context_id": (
                        _packet_working_capital_context(packet, delivery.ticker).get(
                            "working_capital_user_visible_context_id"
                        )
                    ),
                }
            )
        ticker_order = {
            ticker: index for index, ticker in enumerate(_packet_tickers(packet), start=1)
        }
        final_messages.sort(
            key=lambda item: (
                0
                if item.get("ticker") == PILOT_MARKERS[market]
                else ticker_order.get(str(item.get("ticker") or ""), 10_000)
            )
        )
        deterministic_archive = archive_dir / "deterministic-messages.json"
        if deterministic_messages or not deterministic_archive.exists():
            _archive_messages(
                packet,
                "deterministic-messages.json",
                deterministic_messages,
            )
        if not prepared_ids:
            return PilotDeliveryResult(
                status="archive_only",
                market=market,
                packet_id=packet_id,
                reason="fallback_or_existing_delivery_won",
            )
        receipt_path = archive_dir / "message-quality-receipt.json"
        if reused_persisted_payload:
            try:
                receipt = _read_json(receipt_path)
            except (OSError, ValueError, json.JSONDecodeError):
                _hold_quality_integrity_rejection(
                    session,
                    packet,
                    deliveries,
                    reason="persisted_quality_receipt_missing",
                    rejected_at=current,
                )
                return PilotDeliveryResult(
                    status="quality_receipt_invalid",
                    market=market,
                    packet_id=packet_id,
                    delivery_mode="held",
                    pending_count=len(prepared_ids),
                    reason="persisted_quality_receipt_missing",
                )
            receipt_valid = verify_runtime_message_quality_receipt(
                receipt,
                packet,
                output,
                final_messages,
            )
            integrity_errors = _persisted_quality_integrity_errors(
                deliveries,
                packet_id,
                receipt_path,
                receipt,
            )
            receipt_valid = bool(receipt_valid and not integrity_errors)
        else:
            receipt = runtime_message_quality_receipt(
                packet,
                output,
                final_messages,
                checked_at=current,
            )
            receipt_valid = verify_runtime_message_quality_receipt(
                receipt,
                packet,
                output,
                final_messages,
            )
            _atomic_json(receipt_path, receipt)
        if reused_persisted_payload and not receipt_valid:
            reason = (
                ",".join(integrity_errors)
                if integrity_errors
                else "persisted_payload_or_receipt_content_mismatch"
            )
            rejection = _hold_quality_integrity_rejection(
                session,
                packet,
                deliveries,
                reason=reason,
                rejected_at=current,
            )
            return PilotDeliveryResult(
                status="quality_receipt_invalid",
                market=market,
                packet_id=packet_id,
                delivery_mode=(
                    "partial_integrity"
                    if rejection["partial_delivery"]
                    else "held"
                ),
                sent_count=int(rejection["sent_count"]),
                pending_count=int(rejection["held_count"]),
                reason=reason,
            )
        if not receipt_valid:
            for delivery in deliveries:
                try:
                    payload = json.loads(delivery.payload)
                except json.JSONDecodeError:
                    continue
                if not isinstance(payload, dict):
                    continue
                metadata = _pilot_metadata(payload)
                if metadata.get("packet_id") != packet_id:
                    continue
                metadata["state"] = "held"
                metadata["fallback_eligible"] = True
                metadata["ai_validation_state"] = "quality_rejected"
                metadata["message_quality_receipt_sha256"] = _file_sha256(
                    receipt_path
                )
                payload[AI_ASSISTED_PILOT_METADATA_KEY] = metadata
                delivery.payload = json.dumps(payload, ensure_ascii=False)
                session.add(delivery)
            session.commit()
            _archive_messages(
                packet,
                "quality-rejected-ai-messages.json",
                final_messages,
            )
            _atomic_json(
                archive_dir / "validation-result.json",
                {
                    "packet_id": packet_id,
                    "status": "quality_rejected",
                    "errors": receipt.get("errors", []),
                    "rejected_ai_sent": False,
                    "fallback_eligibility_preserved": True,
                    "recorded_at": current.isoformat(),
                },
            )
            return PilotDeliveryResult(
                status="quality_rejected",
                market=market,
                packet_id=packet_id,
                delivery_mode="held",
                pending_count=len(prepared_ids),
                reason="runtime_message_quality_gate_failed",
            )
        receipt_sha256 = _file_sha256(receipt_path)
        for delivery, new_payload in prepared_payloads:
            metadata = _pilot_metadata(new_payload)
            metadata["message_quality_receipt_sha256"] = receipt_sha256
            metadata["rendered_payload_set_sha256"] = receipt.get(
                "rendered_payload_set_sha256"
            )
            new_payload[AI_ASSISTED_PILOT_METADATA_KEY] = metadata
            delivery.payload = json.dumps(new_payload, ensure_ascii=False)
            delivery.status = "pending"
            delivery.attempt_count = 0
            delivery.last_error = None
            delivery.sent_at = None
            session.add(delivery)
        session.commit()
        persisted_integrity_errors = _persisted_quality_integrity_errors(
            deliveries,
            packet_id,
            receipt_path,
            receipt,
        )
        if persisted_integrity_errors:
            rejection = _hold_quality_integrity_rejection(
                session,
                packet,
                deliveries,
                reason=",".join(persisted_integrity_errors),
                rejected_at=current,
            )
            return PilotDeliveryResult(
                status="quality_receipt_invalid",
                market=market,
                packet_id=packet_id,
                delivery_mode=(
                    "partial_integrity"
                    if rejection["partial_delivery"]
                    else "held"
                ),
                sent_count=int(rejection["sent_count"]),
                pending_count=int(rejection["held_count"]),
                reason="persisted_quality_metadata_mismatch",
            )
        ai_archive = archive_dir / "ai-assisted-messages.json"
        if final_messages or not ai_archive.exists():
            _archive_messages(packet, "ai-assisted-messages.json", final_messages)
        if isinstance(night_audit, dict):
            market_text = next(
                (
                    str(item.get("text") or "")
                    for item in final_messages
                    if item.get("ticker") == PILOT_MARKERS[market]
                ),
                "",
            )
            products = night_audit.get("products", [])
            for product in (products if isinstance(products, list) else []):
                if not isinstance(product, dict):
                    continue
                fact_id = str(product.get("fact_id") or "")
                usages = [
                    item.usage
                    for item in output.market_review.numeric_claims
                    if item.fact_id == fact_id
                ]
                product["rendered_in_telegram"] = bool(
                    usages and all(usage in market_text for usage in usages)
                )
            _atomic_json(archive_dir / "night-futures-audit.json", night_audit)
        _atomic_json(
            archive_dir / "validation-result.json",
            {
                "packet_id": packet_id,
                "status": "passed",
                "validated_output": str(output_path),
                "analysis_policy_version": output.analysis_policy_version,
                "knowledge_version": output.knowledge_version,
                "knowledge_sha256": output.knowledge_sha256,
                "chart_knowledge_version": output.chart_knowledge_version,
                "chart_knowledge_sha256": output.chart_knowledge_sha256,
                "renderer_version": PILOT_RENDERER_VERSION,
                **_cash_flow_run_metadata(packet),
                **_working_capital_run_metadata(packet),
            },
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
        delivery_result = {
            "packet_id": packet_id,
            "delivery_mode": "ai_assisted",
            "status": "sent" if complete else "pending",
            "delivery_count": len(prepared_ids),
            "sent_count": sent_count,
            "pending_count": pending_count,
            "pilot_day": pilot_day,
            "message_quality_receipt_sha256": receipt_sha256,
            "rendered_payload_set_sha256": receipt.get(
                "rendered_payload_set_sha256"
            ),
            "dispatched_at": current.isoformat() if complete else None,
            **_cash_flow_run_metadata(packet),
            **_working_capital_run_metadata(packet),
        }
        _atomic_json(_archive_directory(packet) / "delivery-result.json", delivery_result)
        recorded_day = pilot_day
        if complete:
            _write_ai_archive_completion_marker(
                packet,
                output,
                completed_at=current,
            )
            recorded_day = _record_session(
                packet_id,
                market,
                assessment_date=str(packet["assessment_date"]),
                delivery_mode="ai_assisted",
                sent=True,
                now=current,
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
        )
    ).all()
    for delivery in deliveries:
        try:
            payload = json.loads(delivery.payload)
        except json.JSONDecodeError:
            continue
        metadata = _pilot_metadata(payload) if isinstance(payload, dict) else {}
        if metadata.get("market") != market:
            continue
        if metadata.get("quality_integrity_state") == "post_partial_delivery_rejected":
            continue
        state = str(metadata.get("state") or "")
        packet_id = str(metadata.get("packet_id") or "")
        if not packet_id:
            continue
        retryable = delivery.status == "pending" and state in {
            "held",
            "ai_assisted_pending",
            "fallback_pending",
        }
        if state == "ai_assisted_sent":
            packet_path = _packet_path(packet_id)
            if packet_path.exists():
                packet = _read_json(packet_path)
                retryable = not _ai_archive_complete(packet) or packet_id not in (
                    _market_successes(_pilot_state(), market)
                )
        if retryable and packet_id not in values:
            values.append(packet_id)
    return values


async def retry_pending_ai_assisted_deliveries(
    session: Session,
    *,
    market: PilotMarket,
    run_date: date,
    now: datetime | None = None,
    notifier: TelegramNotifier | None = None,
) -> list[PilotDeliveryResult]:
    """Retry finalized AI messages without rerunning analysis or rendering."""
    current = (now or datetime.now(KST)).astimezone(KST)
    results: list[PilotDeliveryResult] = []
    for packet_id in _pending_pilot_packets(session, market, run_date):
        packet = _read_json(_packet_path(packet_id))
        retryable: list[NotificationDelivery] = []
        archive_recovery = False
        retry_count = 0
        with _pilot_lock(packet_id):
            for delivery in _session_deliveries(session, packet):
                payload = json.loads(delivery.payload)
                metadata = _pilot_metadata(payload) if isinstance(payload, dict) else {}
                if (
                    delivery.status == "sent"
                    and metadata.get("packet_id") == packet_id
                    and metadata.get("state") == "ai_assisted_sent"
                ):
                    archive_recovery = True
                    continue
                if delivery.status != "pending":
                    continue
                if (
                    metadata.get("packet_id") != packet_id
                    or metadata.get("state") != "ai_assisted_pending"
                ):
                    continue
                retryable.append(delivery)
                retry_count = max(
                    retry_count,
                    int(metadata.get("persisted_delivery_retry_count") or 0),
                )
            if not retryable and not archive_recovery:
                continue
            retry_path = _archive_directory(packet) / "delivery-retry-state.json"
            if archive_recovery and not retryable and retry_path.exists():
                retry_count = int(_read_json(retry_path).get("retry_count") or 0)
            if retry_count >= MAX_PERSISTED_DELIVERY_RETRIES:
                results.append(
                    PilotDeliveryResult(
                        status="retry_exhausted",
                        market=market,
                        packet_id=packet_id,
                        delivery_mode="ai_assisted",
                        pending_count=len(retryable),
                        reason="persisted_delivery_retry_limit_reached",
                    )
                )
                continue
            next_retry = retry_count + 1
            for delivery in retryable:
                payload = json.loads(delivery.payload)
                metadata = _pilot_metadata(payload)
                metadata["persisted_delivery_retry_count"] = next_retry
                metadata["persisted_delivery_last_retry_at"] = current.isoformat()
                payload[AI_ASSISTED_PILOT_METADATA_KEY] = metadata
                delivery.payload = json.dumps(payload, ensure_ascii=False)
                session.add(delivery)
            session.commit()
        result = await deliver_validated_ai_review(
            session,
            packet_id,
            notifier=notifier,
            now=current,
        )
        _atomic_json(
            _archive_directory(packet) / "delivery-retry-state.json",
            {
                "packet_id": packet_id,
                "retry_count": next_retry,
                "retry_at": current.isoformat(),
                "status": result.status,
                "sent_count": result.sent_count,
                "pending_count": result.pending_count,
                "analysis_rerun": False,
                "packet_regenerated": False,
                "renderer_rerun": False,
                "telegram_resent": False if archive_recovery and not retryable else None,
                "archive_completion_recovery": archive_recovery and not retryable,
            },
        )
        results.append(result)
    return results or [PilotDeliveryResult(status="no_pending_ai_delivery", market=market)]


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
    retry_path = _archive_directory(packet) / "fallback-delivery-retry-state.json"
    retry_state = _read_json(retry_path) if retry_path.exists() else {}
    retry_count = int(retry_state.get("retry_count") or 0)
    if retry_count >= MAX_PERSISTED_DELIVERY_RETRIES:
        return PilotDeliveryResult(
            status="retry_exhausted",
            market=market,
            packet_id=packet_id,
            delivery_mode="deterministic_fallback",
            pending_count=len(delivery_ids),
            reason="persisted_delivery_retry_limit_reached",
        )
    next_retry = retry_count + 1
    _atomic_json(
        retry_path,
        {
            "packet_id": packet_id,
            "retry_count": next_retry,
            "retry_at": current.isoformat(),
            "status": "dispatching",
            "sent_count": 0,
            "pending_count": len(delivery_ids),
            "analysis_rerun": False,
            "packet_regenerated": False,
            "payload_reformatted": False,
        },
    )
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
            **_cash_flow_run_metadata(packet),
            **_working_capital_run_metadata(packet),
        },
    )
    _atomic_json(
        retry_path,
        {
            "packet_id": packet_id,
            "retry_count": next_retry,
            "retry_at": current.isoformat(),
            "status": "sent" if complete else "pending",
            "sent_count": sent_count,
            "pending_count": pending_count,
            "analysis_rerun": False,
            "packet_regenerated": False,
            "payload_reformatted": False,
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
    partial_packet_ids: set[str] = set()
    channel = get_settings().notification_channel.strip().lower()
    for delivery in session.exec(
        select(NotificationDelivery).where(
            NotificationDelivery.assessment_date == run_date,
            NotificationDelivery.channel == channel,
        )
    ).all():
        try:
            payload = json.loads(delivery.payload)
        except json.JSONDecodeError:
            continue
        metadata = _pilot_metadata(payload) if isinstance(payload, dict) else {}
        if (
            metadata.get("market") == market
            and metadata.get("quality_integrity_state")
            == "post_partial_delivery_rejected"
            and metadata.get("packet_id")
        ):
            partial_packet_ids.add(str(metadata["packet_id"]))
    results: list[PilotDeliveryResult] = [
        PilotDeliveryResult(
            status="partial_integrity_manual_intervention",
            market=market,
            packet_id=packet_id,
            delivery_mode="partial_integrity",
            reason="post_partial_delivery_receipt_integrity_failure",
        )
        for packet_id in sorted(partial_packet_ids)
    ]
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
        if _output_path(packet) is not None:
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
                        "cash_flow_user_visible_context_id": metadata.get(
                            "cash_flow_user_visible_context_id"
                        ),
                        "working_capital_user_visible_context_id": metadata.get(
                            "working_capital_user_visible_context_id"
                        ),
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
                    **_cash_flow_run_metadata(packet),
                    **_working_capital_run_metadata(packet),
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
