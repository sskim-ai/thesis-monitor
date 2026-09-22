from __future__ import annotations

import argparse
import asyncio
import hashlib
import json
import re
import socket
import tempfile
import threading
import time
from collections.abc import Mapping, Sequence
from copy import deepcopy
from dataclasses import dataclass, replace
from datetime import UTC, date, datetime
from pathlib import Path
from types import TracebackType
from typing import Any
from unittest.mock import patch

from pydantic import ValidationError
from sqlalchemy.pool import StaticPool
from sqlmodel import SQLModel, Session, create_engine, select

import app.services.accepted_decision_v2_runtime_service as accepted_runtime
import app.services.accepted_decision_v2_service as accepted_service
import app.services.ai_assisted_delivery_service as delivery_service
import app.services.notification_service as notification_service
from app.config import Settings, get_settings
from app.models.thesis import NotificationDelivery
from app.services.accepted_decision_v2_runtime_service import (
    STAGE2_MATURITY_AS_OF_MATERIALIZATION_CONTRACT,
    STAGE2_MODEL_OUTPUT_CONTRACT,
    AcceptedV2ProductionArtifact,
    AcceptedV2ProductionArtifactV2,
    AcceptedV2ProductionContext,
    accepted_v2_production_paths,
    build_accepted_v2_production_context,
    load_accepted_v2_production_artifact,
    load_accepted_v2_state,
    materialize_accepted_v2_stage2_output,
    validate_accepted_v2_production_output,
)
from app.services.accepted_decision_v2_service import (
    AcceptedDecisionPlan,
    resolve_accepted_v2_decision,
    validate_accepted_v2_decision,
)
from app.services.notification_service import AI_ASSISTED_PILOT_METADATA_KEY


KST_ISO = "+09:00"
VALIDATED_AT = datetime(2026, 9, 16, tzinfo=UTC)


def canonical_bytes(value: object) -> bytes:
    return json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
        default=str,
    ).encode("utf-8")


def pretty_bytes(value: object) -> bytes:
    return (
        json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True, default=str)
        + "\n"
    ).encode("utf-8")


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def sha256_file(path: Path) -> str:
    return sha256_bytes(path.read_bytes())


def write_json(root: Path, relative: str, value: object) -> Path:
    path = root / relative
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(pretty_bytes(value))
    return path


def subset_raw(raw: Mapping[str, object], ticker: str) -> dict[str, object]:
    payload = deepcopy(dict(raw))
    for field_name in ("fundamental_cores", "candidates", "adjudications"):
        rows = payload.get(field_name)
        if isinstance(rows, list):
            payload[field_name] = [
                row
                for row in rows
                if isinstance(row, Mapping) and str(row.get("ticker")) == ticker
            ]
    return payload


def stage2_raw_without_runtime_fields(raw: Mapping[str, object]) -> dict[str, object]:
    payload = deepcopy(dict(raw))
    payload["contract"] = STAGE2_MODEL_OUTPUT_CONTRACT
    candidates = payload.get("candidates")
    if isinstance(candidates, list):
        for candidate in candidates:
            if not isinstance(candidate, dict):
                continue
            rows = candidate.get("driver_maturity")
            if not isinstance(rows, list):
                continue
            for row in rows:
                if isinstance(row, dict):
                    row.pop("as_of", None)
                    row.pop("provenance_status", None)
    return payload


def find_source_root(bundle_root: Path, phase_fragment: str) -> Path:
    matches = [
        path
        for path in bundle_root.iterdir()
        if path.is_dir() and phase_fragment in path.name
    ]
    if len(matches) != 1:
        raise ValueError(f"source_root_not_unique:{phase_fragment}:{len(matches)}")
    return matches[0]


def source_batch_for_ticker(raw_root: Path, ticker: str) -> tuple[Path, dict[str, object]]:
    for path in sorted(raw_root.glob("batch-*.output.json")):
        payload = json.loads(path.read_text(encoding="utf-8"))
        candidates = payload.get("candidates") if isinstance(payload, Mapping) else None
        if isinstance(candidates, list) and any(
            isinstance(row, Mapping) and str(row.get("ticker")) == ticker
            for row in candidates
        ):
            return path, dict(payload)
    raise ValueError(f"source_batch_not_found:{ticker}")


def settings_for(root: Path, *, max_chars: int = 3500) -> Settings:
    return get_settings().model_copy(
        update={
            "data_dir": str(root),
            "notification_channel": "telegram",
            "notification_recipient_class": "test",
            "notification_dry_run": False,
            "telegram_bot_token": "offline-test-token",
            "telegram_chat_id": "offline-test-recipient",
            "telegram_test_chat_id": "offline-test-recipient",
            "telegram_message_max_chars": max_chars,
            "telegram_retry_attempts": 1,
            "telegram_retry_base_seconds": 0.0,
            "ai_review_mode": "shadow",
            "ai_review_pilot_enabled": True,
            "ai_review_pilot_target_success_days": 5,
            "visible_stock_decision_engine": "v2_accepted",
            "v2_production_enabled": True,
            "v2_full_monitored_stock_coverage_target": True,
            "v1_decision_rollback_available": True,
            "free_analyst_adaptive_enabled": False,
            "free_analyst_adaptive_mode": "current",
        }
    )


def daily_packet(
    context: AcceptedV2ProductionContext,
    ticker: str,
    *,
    source_label: str,
) -> dict[str, object]:
    evidence_packet = next(row for row in context.evidence_packets if row.ticker == ticker)
    identity_state = "unknown"
    identity_ref = None
    for evidence in evidence_packet.evidence:
        if evidence.ref_id != "canonical:security_basis:current":
            continue
        try:
            statement = json.loads(evidence.statement)
        except (TypeError, ValueError, json.JSONDecodeError):
            match = re.search(
                r'"security_identity_state"\s*:\s*"([^"]+)"',
                evidence.statement,
            )
            if match is not None:
                identity_state = match.group(1)
                identity_ref = evidence.ref_id
            break
        if isinstance(statement, Mapping):
            identity_state = str(statement.get("security_identity_state") or "unknown")
            identity_ref = evidence.ref_id
        break
    return {
        "schema_version": "1",
        "output_schema_version": "4",
        "analysis_policy_version": "daily-review-v3.7",
        "knowledge": {"version": "3.0", "sha256": "offline-knowledge-sha"},
        "chart_knowledge": {"version": "1.0", "sha256": "offline-chart-sha"},
        "packet_id": context.packet_id,
        "source_monitor_run_id": f"m12cg-r3-{source_label}",
        "market": context.market,
        "assessment_date": context.assessment_date,
        "market_context": {
            "portfolio_exposure_groups": [
                {
                    "group_key": "offline-proof",
                    "label": "offline proof",
                    "tickers": [ticker],
                }
            ]
        },
        "stocks": [
            {
                "ticker": ticker,
                "thesis_version": 1,
                "valuation": {
                    "security_identity_state": identity_state,
                    "security_identity_source_ref": identity_ref,
                },
            }
        ],
    }


def daily_output(packet: Mapping[str, object], ticker: str, claim_id: str) -> dict[str, object]:
    packet_id = str(packet["packet_id"])
    market = str(packet["market"])
    assessment_date = str(packet["assessment_date"])
    return {
        "schema_version": "4",
        "packet_id": packet_id,
        "claim_id": claim_id,
        "analysis_policy_version": "daily-review-v3.7",
        "knowledge_version": "3.0",
        "knowledge_sha256": "offline-knowledge-sha",
        "chart_knowledge_version": "1.0",
        "chart_knowledge_sha256": "offline-chart-sha",
        "market": market,
        "assessment_date": assessment_date,
        "market_review": {
            "facts_used": [],
            "frameworks_used": ["macro_transmission"],
            "core_judgment": {
                "text": "검증된 시장 맥락은 혼재 상태입니다.",
                "fact_ids": [],
            },
            "important_changes": [
                {
                    "text": "시장 신호는 기업 펀더멘털과 분리해 봐야 합니다.",
                    "fact_ids": [],
                }
            ],
            "market_context": {
                "text": "시장 환경은 혼재 상태입니다.",
                "fact_ids": [],
            },
            "market_assumptions": {
                "text": "추가 확정 근거를 기다립니다.",
                "fact_ids": [],
            },
            "portfolio_transmission": [
                {
                    "portfolio_group": "offline-proof",
                    "text": "시장 가격과 기업 실적의 연결은 별도로 검증합니다.",
                    "fact_ids": [],
                }
            ],
            "next_checks": [
                {
                    "text": "다음 공식 자료에서 사업 지표를 확인합니다.",
                    "fact_ids": [],
                }
            ],
            "numeric_claims": [],
            "unknowns": ["다음 거래일 방향은 미확인입니다."],
        },
        "stock_reviews": [
            {
                "ticker": ticker,
                "thesis_version": 1,
                "ai_thesis_assessment": "no_material_change",
                "earnings_estimate_view": "unchanged",
                "valuation_view": "neutral",
                "facts_used": [],
                "frameworks_used": ["market_expectations"],
                "core_judgment": {
                    "text": "공식 상태를 바꿀 확정 근거는 아직 부족합니다.",
                    "fact_ids": [],
                },
                "business_earnings": {
                    "text": "다음 공식 실적에서 사업 진전을 확인해야 합니다.",
                    "fact_ids": [],
                },
                "price_positioning": {
                    "text": "현재 가격 신호는 사업 논리와 분리합니다.",
                    "new_observer_view": "기업의 질과 진입 가격을 나누어 봅니다.",
                    "holder_view": "가격 확인 조건을 계속 추적합니다.",
                    "fact_ids": [],
                },
                "supply_analysis": {
                    "text": "거래량 변화는 공식 사업 지표와 분리해 확인합니다.",
                    "fact_ids": [],
                },
                "valuation_analysis": {
                    "text": "Valuation은 별도 판단 층위입니다.",
                    "fact_ids": [],
                },
                "numeric_claims": [],
                "unknowns": ["다음 분기 사업 지표는 미확인입니다."],
                "priority_watch": ["확정된 사업 지표"],
                "next_checks": ["다음 공식 실적"],
                "confidence": 0.8,
            }
        ],
    }


@dataclass(frozen=True)
class NativeFixture:
    name: str
    ticker: str
    packet: dict[str, object]
    output: dict[str, object]
    artifact: AcceptedV2ProductionArtifact | AcceptedV2ProductionArtifactV2
    context: AcceptedV2ProductionContext
    raw_output: dict[str, object]
    normalized_output: object
    source_paths: dict[str, str]
    source_hashes: dict[str, str]
    transformations: dict[str, object]


def build_fixture(
    *,
    source_root: Path,
    ticker: str,
    settings: Settings,
    source_label: str,
    fixture_name: str | None = None,
    packet_id_override: str | None = None,
    assessment_date_override: str | None = None,
    historical: bool = False,
    legacy_normalization: bool = False,
) -> NativeFixture:
    raw_root = source_root / "raw" / "reproof-no-repair" / "us"
    context_path = raw_root / "context.json"
    source_context = AcceptedV2ProductionContext.model_validate_json(
        context_path.read_text(encoding="utf-8")
    )
    original_evidence_packet = next(
        row for row in source_context.evidence_packets if row.ticker == ticker
    )
    batch_path, raw = source_batch_for_ticker(raw_root, ticker)
    if historical:
        raw = stage2_raw_without_runtime_fields(raw)
    packet = daily_packet(source_context, ticker, source_label=source_label)
    if packet_id_override is not None:
        packet["packet_id"] = packet_id_override
    if assessment_date_override is not None:
        packet["assessment_date"] = assessment_date_override
    evidence_packet = original_evidence_packet.model_copy(
        update={
            "packet_id": str(packet["packet_id"]),
            "assessment_date": str(packet["assessment_date"]),
        }
    )
    context = build_accepted_v2_production_context(
        packet=packet,
        claim_id=source_context.claim_id,
        evidence_packets=(evidence_packet,),
        prepared_at=VALIDATED_AT,
        settings=settings,
    )
    one_raw = subset_raw(raw, ticker)
    if packet_id_override is not None:
        one_raw["packet_id"] = packet_id_override
    if assessment_date_override is not None:
        one_raw["assessment_date"] = assessment_date_override
    normalized_contract = (
        STAGE2_MATURITY_AS_OF_MATERIALIZATION_CONTRACT
        if legacy_normalization
        else accepted_runtime.STAGE2_MATURITY_PROVENANCE_MATERIALIZATION_CONTRACT
    )
    normalized = materialize_accepted_v2_stage2_output(
        context,
        one_raw,
        normalized_contract=normalized_contract,
    )
    artifact = validate_accepted_v2_production_output(
        context,
        normalized,
        validated_at=VALIDATED_AT,
    )
    output = daily_output(packet, ticker, context.claim_id)
    return NativeFixture(
        name=fixture_name or source_label,
        ticker=ticker,
        packet=packet,
        output=output,
        artifact=artifact,
        context=context,
        raw_output=one_raw,
        normalized_output=normalized,
        source_paths={
            "source_bundle_scope": "M12CB" if historical else "M12CE",
            "context": context_path.relative_to(source_root).as_posix(),
            "batch": batch_path.relative_to(source_root).as_posix(),
        },
        source_hashes={
            "context": sha256_file(context_path),
            "batch": sha256_file(batch_path),
            "packet": sha256_bytes(canonical_bytes(packet)),
            "raw_subset": sha256_bytes(canonical_bytes(one_raw)),
            "normalized": sha256_bytes(
                canonical_bytes(normalized.model_dump(mode="json"))
            ),
            "artifact": sha256_bytes(
                canonical_bytes(artifact.model_dump(mode="json"))
            ),
        },
        transformations={
            "projection": "CANONICAL_SUBSET_REGENERATED_THROUGH_EXISTING_APIS",
            "ticker_filter": ticker,
            "historical_runtime_field_materialization": historical,
            "legacy_normalization_contract": legacy_normalization,
            "packet_id_projection": (
                {
                    "from": source_context.packet_id,
                    "to": packet_id_override,
                    "evidence_identity_updated_consistently": True,
                }
                if packet_id_override is not None
                else None
            ),
            "assessment_date_projection": (
                {
                    "from": source_context.assessment_date,
                    "to": assessment_date_override,
                    "evidence_identity_updated_consistently": True,
                }
                if assessment_date_override is not None
                else None
            ),
            "financial_or_decision_semantics_modified": False,
        },
    )


def output_path_for(root: Path, fixture: NativeFixture) -> Path:
    return (
        root
        / "ai_review"
        / "outbox"
        / f"{fixture.packet['packet_id']}--daily-review-v3.7--knowledge.json"
    )


def install_fixture(
    root: Path,
    fixture: NativeFixture,
    *,
    artifact_payload: Mapping[str, object] | None = None,
    receipt_payload: Mapping[str, object] | None = None,
) -> dict[str, Path]:
    inbox = root / "ai_review" / "inbox"
    outbox = root / "ai_review" / "outbox"
    inbox.mkdir(parents=True, exist_ok=True)
    outbox.mkdir(parents=True, exist_ok=True)
    packet_path = inbox / f"{fixture.packet['packet_id']}.json"
    packet_path.write_bytes(pretty_bytes(fixture.packet))
    output_path = output_path_for(root, fixture)
    output_path.write_bytes(pretty_bytes(fixture.output))
    paths = accepted_v2_production_paths(
        output_path,
        claim_id=str(fixture.output["claim_id"]),
    )
    payload = artifact_payload or fixture.artifact.model_dump(mode="json")
    paths["final"].write_bytes(pretty_bytes(payload))
    if receipt_payload is not None:
        paths["receipt"].parent.mkdir(parents=True, exist_ok=True)
        paths["receipt"].write_bytes(pretty_bytes(receipt_payload))
    return {"packet": packet_path, "output": output_path, **paths}


def engine_memory():
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    SQLModel.metadata.create_all(engine)
    return engine


def seed_deliveries(session: Session, fixture: NativeFixture, *, include_market: bool = True) -> None:
    assessment_date = date.fromisoformat(str(fixture.packet["assessment_date"]))
    if include_market:
        session.add(
            NotificationDelivery(
                ticker=delivery_service.PILOT_MARKERS[str(fixture.packet["market"])],
                assessment_date=assessment_date,
                channel="telegram",
                status="pending",
                payload=json.dumps(
                    {
                        "text": "시장 점검\n현재 환경: 혼합",
                        "type": "daily_monitoring_digest",
                        "market_scope": fixture.packet["market"],
                    },
                    ensure_ascii=False,
                ),
            )
        )
    session.add(
        NotificationDelivery(
            ticker=fixture.ticker,
            assessment_date=assessment_date,
            channel="telegram",
            status="pending",
            payload=json.dumps(
                {
                    "text": (
                        f"{fixture.ticker}\n\n투자 논리: 유지\n\n"
                        "핵심 판단: 기존 논리를 유지합니다.\n\n"
                        "가격: 현재 가격은 별도 확인합니다."
                    ),
                    "type": "daily_stock_analysis",
                    "ticker": fixture.ticker,
                    "status": "no_material_change",
                },
                ensure_ascii=False,
            ),
        )
    )
    session.commit()


class CaptureNotifier:
    def __init__(self, *, fail_calls: Sequence[int] = ()) -> None:
        self.fail_calls = set(fail_calls)
        self.attempted: list[dict[str, object]] = []
        self.sent: list[dict[str, object]] = []

    async def send(self, payload: dict[str, object]) -> str:
        copied = deepcopy(payload)
        self.attempted.append(copied)
        if len(self.attempted) in self.fail_calls:
            raise RuntimeError("m12cg_r3_scripted_transport_failure")
        self.sent.append(copied)
        return "sent"


class SimulatedProcessCrash(BaseException):
    pass


class ChunkCaptureNotifier(notification_service.TelegramNotifier):
    def __init__(
        self,
        settings: Settings,
        *,
        fail_calls: Sequence[int] = (),
        crash_after_success_calls: Sequence[int] = (),
    ) -> None:
        self.settings = settings
        self.transport = None
        self.narrative_generator = None
        self.fail_calls = set(fail_calls)
        self.crash_after_success_calls = set(crash_after_success_calls)
        self.attempted_chunks: list[str] = []
        self.sent_chunks: list[str] = []

    async def send_chunk(self, text: str) -> notification_service.TelegramChunkResult:
        self.attempted_chunks.append(text)
        call = len(self.attempted_chunks)
        if call in self.fail_calls:
            raise notification_service.TelegramDeliveryError(
                "m12cg_r3_scripted_chunk_failure"
            )
        self.sent_chunks.append(text)
        if call in self.crash_after_success_calls:
            raise SimulatedProcessCrash("m12cg_r3_simulated_post_send_process_crash")
        return notification_service.TelegramChunkResult(message_id=call)


class NetworkDeny:
    def __init__(self) -> None:
        self.blocked_attempts: list[str] = []
        self._patches: list[Any] = []

    def _blocked_create(self, address: object, *args: object, **kwargs: object) -> None:
        self.blocked_attempts.append(f"create_connection:{address!r}")
        raise RuntimeError("m12cg_r3_network_denied")

    def _blocked_connect(
        self,
        sock: socket.socket,
        address: object,
    ) -> None:
        del sock
        self.blocked_attempts.append(f"socket_connect:{address!r}")
        raise RuntimeError("m12cg_r3_network_denied")

    def __enter__(self) -> NetworkDeny:
        self._patches = [
            patch("socket.create_connection", self._blocked_create),
            patch.object(socket.socket, "connect", self._blocked_connect),
        ]
        for item in self._patches:
            item.start()
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        traceback: TracebackType | None,
    ) -> None:
        del exc_type, exc, traceback
        for item in reversed(self._patches):
            item.stop()

    def deliberate_probe(self) -> str:
        try:
            socket.create_connection(("offline.invalid", 443))
        except RuntimeError as exc:
            return str(exc)
        return "NETWORK_GUARD_FAILED"


def delivery_rows(session: Session) -> list[dict[str, object]]:
    rows = session.exec(select(NotificationDelivery).order_by(NotificationDelivery.id)).all()
    return [
        {
            "id": row.id,
            "ticker": row.ticker,
            "assessment_date": row.assessment_date.isoformat(),
            "status": row.status,
            "attempt_count": row.attempt_count,
            "last_error": row.last_error,
            "sent_at": row.sent_at.isoformat() if row.sent_at else None,
            "payload_sha256": sha256_bytes(row.payload.encode("utf-8")),
            "payload": json.loads(row.payload),
        }
        for row in rows
    ]


def state_snapshot(settings: Settings) -> dict[str, object] | None:
    state = load_accepted_v2_state(settings=settings)
    return state.model_dump(mode="json") if state is not None else None


def state_sha256(state: Mapping[str, object] | None) -> str | None:
    return sha256_bytes(canonical_bytes(state)) if state is not None else None


def decision_metadata_rows(snapshot: Mapping[str, object]) -> list[dict[str, object]]:
    result: list[dict[str, object]] = []
    for row in snapshot.get("deliveries", []):
        if not isinstance(row, Mapping):
            continue
        payload = row.get("payload")
        if not isinstance(payload, Mapping):
            continue
        metadata = payload.get(AI_ASSISTED_PILOT_METADATA_KEY)
        if not isinstance(metadata, Mapping):
            continue
        decision = metadata.get("decision_canary")
        result.append(
            {
                "ticker": row.get("ticker"),
                "delivery_status": row.get("status"),
                "pilot_state": metadata.get("state"),
                "decision_state": (
                    decision.get("state") if isinstance(decision, Mapping) else None
                ),
                "suppression_reason": (
                    decision.get("suppression_reason")
                    if isinstance(decision, Mapping)
                    else None
                ),
                "accepted_plan_only": (
                    decision.get("accepted_plan_only")
                    if isinstance(decision, Mapping)
                    else None
                ),
            }
        )
    return result


def sink_rows(notifier: CaptureNotifier) -> list[dict[str, object]]:
    return [
        {
            "index": index,
            "ticker": row.get("ticker"),
            "type": row.get("type"),
            "text_sha256": sha256_bytes(str(row.get("text") or "").encode("utf-8")),
            "text": row.get("text"),
        }
        for index, row in enumerate(notifier.sent, start=1)
    ]


def archived_quality_receipts(root: Path) -> list[dict[str, object]]:
    receipts = []
    for path in sorted(root.rglob("message-quality-receipt.json")):
        receipts.append(
            {
                "path": path.relative_to(root).as_posix(),
                "sha256": sha256_file(path),
                "payload": json.loads(path.read_text(encoding="utf-8")),
            }
        )
    return receipts


def archived_named_payloads(root: Path, name: str) -> list[dict[str, object]]:
    payloads = []
    for path in sorted(root.rglob(name)):
        payloads.append(
            {
                "path": path.relative_to(root).as_posix(),
                "sha256": sha256_file(path),
                "payload": json.loads(path.read_text(encoding="utf-8")),
            }
        )
    return payloads


async def execute_delivery(
    *,
    session: Session,
    fixture: NativeFixture,
    settings: Settings,
    notifier: CaptureNotifier,
    now: datetime = VALIDATED_AT,
) -> dict[str, object]:
    with (
        patch.object(delivery_service, "get_settings", lambda: settings),
        patch.object(notification_service, "get_settings", lambda: settings),
        patch.object(accepted_runtime, "get_settings", lambda: settings),
    ):
        held = delivery_service.hold_ai_assisted_pilot_session(
            session,
            str(fixture.packet["packet_id"]),
        )
        result = await delivery_service.deliver_validated_ai_review(
            session,
            str(fixture.packet["packet_id"]),
            notifier=notifier,  # type: ignore[arg-type]
            now=now,
        )
    return {
        "hold": held.as_dict(),
        "result": result.as_dict(),
        "deliveries": delivery_rows(session),
        "state": state_snapshot(settings),
        "sink": sink_rows(notifier),
        "attempted_sink_count": len(notifier.attempted),
        "successful_sink_count": len(notifier.sent),
    }


async def execute_chunk_delivery(
    *,
    session: Session,
    fixture: NativeFixture,
    settings: Settings,
    notifier: ChunkCaptureNotifier,
    now: datetime = VALIDATED_AT,
) -> dict[str, object]:
    with (
        patch.object(delivery_service, "get_settings", lambda: settings),
        patch.object(notification_service, "get_settings", lambda: settings),
        patch.object(accepted_runtime, "get_settings", lambda: settings),
    ):
        held = delivery_service.hold_ai_assisted_pilot_session(
            session,
            str(fixture.packet["packet_id"]),
        )
        result = await delivery_service.deliver_validated_ai_review(
            session,
            str(fixture.packet["packet_id"]),
            notifier=notifier,
            now=now,
        )
    return {
        "hold": held.as_dict(),
        "result": result.as_dict(),
        "deliveries": delivery_rows(session),
        "state": state_snapshot(settings),
        "attempted_chunks": list(notifier.attempted_chunks),
        "sent_chunks": list(notifier.sent_chunks),
    }


def export_fixture(out: Path, fixture: NativeFixture) -> dict[str, object]:
    prefix = f"payloads/native-fixtures/{fixture.name}"
    files = {
        "packet": write_json(out, f"{prefix}/packet.json", fixture.packet),
        "ai_output": write_json(out, f"{prefix}/ai-output.json", fixture.output),
        "raw_stage2": write_json(out, f"{prefix}/raw-stage2.json", fixture.raw_output),
        "normalized_stage2": write_json(
            out,
            f"{prefix}/normalized-stage2.json",
            fixture.normalized_output.model_dump(mode="json"),
        ),
        "artifact": write_json(
            out,
            f"{prefix}/accepted-artifact.json",
            fixture.artifact.model_dump(mode="json"),
        ),
    }
    return {
        "fixture_name": fixture.name,
        "ticker": fixture.ticker,
        "source_paths": fixture.source_paths,
        "source_hashes": fixture.source_hashes,
        "transformations": fixture.transformations,
        "exported_files": {
            key: {
                "path": path.relative_to(out).as_posix(),
                "size": path.stat().st_size,
                "sha256": sha256_file(path),
            }
            for key, path in files.items()
        },
    }


def exception_observation(exc: Exception) -> dict[str, object]:
    if isinstance(exc, ValidationError):
        errors = exc.errors(include_url=False)
        return {
            "exception_type": type(exc).__name__,
            "exception_code": str(errors[0].get("type")) if errors else "validation_error",
            "exception_message": str(exc),
            "validation_errors": errors,
        }
    return {
        "exception_type": type(exc).__name__,
        "exception_code": str(exc),
        "exception_message": str(exc),
        "validation_errors": [],
    }


def direct_load_observation(
    path: Path,
    *,
    fixture: NativeFixture,
) -> dict[str, object]:
    try:
        artifact = load_accepted_v2_production_artifact(
            path,
            packet=fixture.packet,
            claim_id=str(fixture.output["claim_id"]),
        )
    except Exception as exc:
        return {"status": "REJECTED", **exception_observation(exc)}
    return {
        "status": "ACCEPTED",
        "contract": artifact.contract,
        "artifact_sha256": sha256_bytes(
            canonical_bytes(artifact.model_dump(mode="json"))
        ),
    }


def artifact_payload(fixture: NativeFixture) -> dict[str, object]:
    return deepcopy(fixture.artifact.model_dump(mode="json"))


def accepted_semantic_sha256(fixture: NativeFixture) -> str:
    plans = []
    for row in fixture.artifact.accepted_plans:
        payload = row.model_dump(mode="json")
        for field_name in (
            "accepted_decision_id",
            "accepted_evidence_fingerprint",
            "candidate_decision_id",
            "candidate_evidence_fingerprint",
        ):
            payload.pop(field_name, None)
        plans.append(payload)
    blocks = []
    for row in fixture.artifact.blocks:
        payload = row.model_dump(mode="json")
        payload.pop("accepted_decision_id", None)
        blocks.append(payload)
    return sha256_bytes(
        canonical_bytes(
            {
                "accepted_plans": plans,
                "blocks": blocks,
            }
        )
    )


def mutate_artifact_payload(
    fixture: NativeFixture,
    variant: str,
) -> tuple[dict[str, object], dict[str, object]]:
    payload = artifact_payload(fixture)
    before = deepcopy(payload)
    pointer: str
    if variant == "wrong_packet":
        pointer = "/packet_id"
        payload["packet_id"] = "wrong-packet"
    elif variant == "wrong_claim":
        pointer = "/claim_id"
        payload["claim_id"] = "wrong-claim"
    elif variant == "wrong_market":
        pointer = "/market"
        payload["market"] = "kr"
    elif variant == "wrong_date":
        pointer = "/assessment_date"
        payload["assessment_date"] = "2026-09-14"
    elif variant == "wrong_subject":
        pointer = "/selected_subjects/0"
        payload["selected_subjects"][0] = "WRONG"  # type: ignore[index]
    elif variant == "wrong_source_hash":
        pointer = "/source_packet_sha256"
        payload["source_packet_sha256"] = "0" * 64
    elif variant == "candidate_mutation":
        pointer = "/candidates/0/confidence"
        payload["candidates"][0]["confidence"] = "LOW"  # type: ignore[index]
    elif variant == "accepted_plan_mutation":
        pointer = "/accepted_plans/0/accepted_reason/text"
        payload["accepted_plans"][0]["accepted_reason"]["text"] += " 변조"  # type: ignore[index]
    elif variant == "block_mutation":
        pointer = "/blocks/0/text"
        payload["blocks"][0]["text"] += "\n변조"  # type: ignore[index]
    elif variant == "plan_status_not_ready":
        pointer = "/accepted_plans/0/status"
        payload["accepted_plans"][0]["status"] = "NOT_READY"  # type: ignore[index]
    elif variant == "artifact_status_invalid":
        pointer = "/status"
        payload["status"] = "INVALID"
    elif variant == "contract_version_invalid":
        pointer = "/contract"
        payload["contract"] = "v2-accepted-production-artifact-v999"
    else:
        raise ValueError(f"unknown_artifact_mutation:{variant}")
    return payload, {
        "variant": variant,
        "json_pointer": pointer,
        "before_sha256": sha256_bytes(canonical_bytes(before)),
        "after_sha256": sha256_bytes(canonical_bytes(payload)),
    }


def claim_rows(plan: AcceptedDecisionPlan) -> list[dict[str, object]]:
    rows: list[tuple[str, object]] = [
        ("/accepted_balance_summary", plan.accepted_balance_summary),
        ("/accepted_reason/text", plan.accepted_reason),
        ("/accepted_confirmation_cost_basis/text", plan.accepted_confirmation_cost_basis),
        ("/accepted_upgrade_condition/text", plan.accepted_upgrade_condition),
        ("/accepted_downgrade_condition/text", plan.accepted_downgrade_condition),
    ]
    rows.extend(
        (f"/accepted_buy_drivers/{index}/text", claim)
        for index, claim in enumerate(plan.accepted_buy_drivers)
    )
    rows.extend(
        (f"/accepted_sell_drivers/{index}/text", claim)
        for index, claim in enumerate(plan.accepted_sell_drivers)
    )
    rows.append(
        (
            "/accepted_new_buyer_axis/reason/text",
            plan.accepted_new_buyer_axis.reason if plan.accepted_new_buyer_axis else None,
        )
    )
    rows.append(
        (
            "/accepted_holder_axis/reason/text",
            plan.accepted_holder_axis.reason if plan.accepted_holder_axis else None,
        )
    )
    result: list[dict[str, object]] = []
    for pointer, value in rows:
        if value is None:
            continue
        if isinstance(value, str):
            text = value
            refs: list[str] = []
        else:
            text = str(value.text)
            refs = list(value.evidence_refs)
        matches = [
            {
                "substring": match.group(0),
                "span": [match.start(), match.end()],
            }
            for match in accepted_service._EXACT_NUMBER.finditer(text)
        ]
        result.append(
            {
                "json_pointer": pointer,
                "text": text,
                "evidence_refs": refs,
                "exact_number_matches": matches,
            }
        )
    return result


def numeric_owner_trace(m12ce_root: Path, out: Path) -> dict[str, object]:
    raw_root = m12ce_root / "raw" / "reproof-no-repair" / "us"
    context_path = raw_root / "context.json"
    context = AcceptedV2ProductionContext.model_validate_json(
        context_path.read_text(encoding="utf-8")
    )
    batch_path, raw = source_batch_for_ticker(raw_root, "GOOGL")
    results = []
    for ticker in ("GOOGL", "HUT"):
        selected = {ticker}
        one_context = context.model_copy(
            update={
                "selected_subjects": (ticker,),
                "evidence_packets": tuple(
                    row for row in context.evidence_packets if row.ticker in selected
                ),
                "evidence_ownership": tuple(
                    row for row in context.evidence_ownership if row.ticker in selected
                ),
                "prior_accepted": tuple(
                    row for row in context.prior_accepted if row.ticker in selected
                ),
            }
        )
        one_raw = subset_raw(raw, ticker)
        normalized = materialize_accepted_v2_stage2_output(one_context, one_raw)
        candidate = normalized.candidates[0]
        core = normalized.fundamental_cores[0]
        packet = one_context.evidence_packets[0]
        prior = {row.ticker: row for row in one_context.prior_accepted}
        baseline = prior.get(ticker)
        adjudications = {row.ticker: row for row in normalized.adjudications}
        material_disagreement = bool(
            baseline is not None
            and accepted_runtime.requires_directional_balance_adjudication(
                prior_decision=baseline.accepted_decision,
                prior_balance=baseline.accepted_directional_balance,
                prior_evidence_sha256=baseline.evidence_sha256,
                candidate_decision=candidate.decision,
                candidate_balance=candidate.directional_balance,
                current_evidence_sha256=packet.evidence_sha256,
            )
        )
        plan = resolve_accepted_v2_decision(
            packet,
            candidate,
            v1_decision=baseline.accepted_decision if baseline else candidate.decision,
            v1_directional_balance=(
                baseline.accepted_directional_balance if baseline else None
            ),
            v1_buy_drivers=baseline.accepted_buy_drivers if baseline else (),
            v1_sell_drivers=baseline.accepted_sell_drivers if baseline else (),
            v1_balance_summary=baseline.accepted_balance_summary if baseline else None,
            material_disagreement=material_disagreement,
            adjudication=adjudications.get(ticker),
        )
        validation = validate_accepted_v2_decision(packet, plan)
        rows = claim_rows(plan)
        evidence = {row.ref_id: row for row in packet.evidence}
        numeric_rows = []
        for row in rows:
            if not row["exact_number_matches"]:
                continue
            refs = [str(ref_id) for ref_id in row["evidence_refs"]]
            numeric_rows.append(
                {
                    **row,
                    "source_evidence_rows": [
                        evidence[ref_id].model_dump(mode="json")
                        for ref_id in refs
                        if ref_id in evidence
                    ],
                    "validator_registry_values_compared": [],
                    "validator_registry_comparison_count": 0,
                    "origin": "FROZEN_FUNDAMENTAL_CORE_COPIED_BY_STAGE2",
                }
            )
        core_identity = {
            "directional_balance": candidate.directional_balance == core.directional_balance,
            "buy_drivers": candidate.buy_drivers == core.buy_drivers,
            "sell_drivers": candidate.sell_drivers == core.sell_drivers,
            "balance_summary": candidate.balance_summary == core.balance_summary,
            "fundamental_core_sha256": candidate.fundamental_core_sha256,
            "expected_fundamental_core_sha256": (
                accepted_runtime.accepted_v2_fundamental_core_sha256(core)
            ),
        }
        payloads = {
            "context": write_json(
                out,
                f"payloads/numeric-trace/{ticker}.context.json",
                one_context.model_dump(mode="json"),
            ),
            "raw": write_json(
                out,
                f"payloads/numeric-trace/{ticker}.raw.json",
                one_raw,
            ),
            "normalized": write_json(
                out,
                f"payloads/numeric-trace/{ticker}.normalized.json",
                normalized.model_dump(mode="json"),
            ),
            "core": write_json(
                out,
                f"payloads/numeric-trace/{ticker}.core.json",
                core.model_dump(mode="json"),
            ),
            "candidate": write_json(
                out,
                f"payloads/numeric-trace/{ticker}.candidate.json",
                candidate.model_dump(mode="json"),
            ),
            "accepted_plan": write_json(
                out,
                f"payloads/numeric-trace/{ticker}.accepted-plan.json",
                plan.model_dump(mode="json"),
            ),
        }
        try:
            validate_accepted_v2_production_output(
                one_context,
                normalized,
                validated_at=VALIDATED_AT,
            )
            finalization = {"result": "UNEXPECTED_PASS", "error": None}
        except Exception as exc:
            finalization = {
                "result": "EXPECTED_REPRODUCED_FAILURE",
                "error_type": type(exc).__name__,
                "error": str(exc),
            }
        results.append(
            {
                "ticker": ticker,
                "source_context_sha256": sha256_file(context_path),
                "source_batch_sha256": sha256_file(batch_path),
                "packet_evidence_sha256": packet.evidence_sha256,
                "raw_subset_sha256": sha256_bytes(canonical_bytes(one_raw)),
                "normalized_output_sha256": sha256_bytes(
                    canonical_bytes(normalized.model_dump(mode="json"))
                ),
                "prior_state": baseline.model_dump(mode="json") if baseline else None,
                "prior_state_sha256": (
                    sha256_bytes(canonical_bytes(baseline.model_dump(mode="json")))
                    if baseline
                    else None
                ),
                "stage2_validation": "PASS",
                "plan_status": plan.status,
                "accepted_source": plan.accepted_source,
                "accepted_plan_validation": validation.model_dump(mode="json"),
                "numeric_claims": numeric_rows,
                "numeric_match_count": sum(
                    len(row["exact_number_matches"]) for row in numeric_rows
                ),
                "core_identity": core_identity,
                "rejected_predicate": {
                    "owner": "accepted_decision_v2_service.validate_accepted_v2_decision",
                    "regex_owner": "accepted_decision_v2_service._EXACT_NUMBER",
                    "predicate": "_EXACT_NUMBER.search(claim.text)",
                    "registry_lookup_performed": False,
                    "evaluated_result": True,
                    "emitted_error": "adjudication_introduced_unregistered_numeric",
                },
                "classification": "FROZEN_CORE_REVALIDATION_SCOPE_FALSE_POSITIVE",
                "finalization": finalization,
                "payloads": {
                    name: {
                        "path": path.relative_to(out).as_posix(),
                        "sha256": sha256_file(path),
                    }
                    for name, path in payloads.items()
                },
            }
        )
    return {
        "contract": "m12cg-r3-googl-hut-numeric-owner-trace-v1",
        "source_bundle_scope": "M12CE",
        "source_context": context_path.relative_to(m12ce_root).as_posix(),
        "source_batch": batch_path.relative_to(m12ce_root).as_posix(),
        "trace_complete_count": sum(
            row["numeric_match_count"] > 0
            and row["finalization"]["result"] == "EXPECTED_REPRODUCED_FAILURE"
            for row in results
        ),
        "runtime_repair_applied": False,
        "numeric_runtime_repair_required": True,
        "results": results,
        "status": (
            "PASS_DIAGNOSIS_RUNTIME_REPAIR_REQUIRED"
            if len(results) == 2
            and all(row["numeric_match_count"] > 0 for row in results)
            else "NOT_PROVEN"
        ),
    }


async def positive_and_reentry_cases(
    *,
    fixtures: Mapping[str, NativeFixture],
    out: Path,
) -> tuple[list[dict[str, object]], dict[str, object]]:
    cases: list[dict[str, object]] = []
    network = NetworkDeny()
    with network:
        deliberate = network.deliberate_probe()
        for case_id, fixture_name in (
            ("D01", "corz-concrete-v2"),
            ("D02", "skhy-symbolic-v2"),
            ("D03", "skhy-mixed-m12cd-v2"),
        ):
            fixture = fixtures[fixture_name]
            with tempfile.TemporaryDirectory(prefix=f"m12cg-r3-{case_id.lower()}-") as value:
                root = Path(value)
                settings = settings_for(root)
                paths = install_fixture(root, fixture)
                notifier = CaptureNotifier()
                with Session(engine_memory()) as session:
                    seed_deliveries(session, fixture)
                    first = await execute_delivery(
                        session=session,
                        fixture=fixture,
                        settings=settings,
                        notifier=notifier,
                    )
                    repeat = None
                    if case_id == "D01":
                        repeat = await execute_delivery(
                            session=session,
                            fixture=fixture,
                            settings=settings,
                            notifier=notifier,
                        )
                state = first["state"]
                artifact_candidate = fixture.artifact.candidates[0]
                maturity_rows = [
                    row.model_dump(mode="json")
                    for row in artifact_candidate.driver_maturity
                ]
                expected_sink = 2
                row = {
                    "case_id": case_id,
                    "variant_id": {
                        "D01": "D01-eligible-matched-concrete-artifact",
                        "D02": "D02-symbolic-only-limitation",
                        "D03": "D03-mixed-provenance-concrete-max",
                    }[case_id],
                    "fixture": fixture_name,
                    "route_entrypoint": (
                        "ai_assisted_delivery_service.deliver_validated_ai_review"
                    ),
                    "packet_sha256": fixture.source_hashes["packet"],
                    "artifact_sha256": fixture.source_hashes["artifact"],
                    "claim_id": fixture.artifact.claim_id,
                    "artifact_contract": fixture.artifact.contract,
                    "first": first,
                    "repeat": repeat,
                    "maturity_rows": maturity_rows,
                    "source_paths": fixture.source_paths,
                    "installed_paths": {
                        key: path.relative_to(root).as_posix()
                        for key, path in paths.items()
                    },
                    "quality_receipts": archived_quality_receipts(root),
                    "combined_quality_rejections": archived_named_payloads(
                        root, "decision-v2-combined-quality-rejection.json"
                    ),
                    "status": (
                        "PASS"
                        if first["result"]["status"] == "sent"
                        and first["successful_sink_count"] == expected_sink
                        and state is not None
                        and (
                            repeat is None
                            or repeat["successful_sink_count"] == expected_sink
                        )
                        else "FAIL"
                    ),
                }
                if case_id == "D02":
                    symbolic = [
                        maturity
                        for maturity in maturity_rows
                        if maturity.get("provenance_status")
                        == "SYMBOLIC_ONLY_NO_CONCRETE_DATE"
                    ]
                    row["symbolic_limit_preserved"] = (
                        len(maturity_rows) == 5
                        and len(symbolic) == 1
                        and symbolic[0].get("as_of") is None
                    )
                    if not row["symbolic_limit_preserved"]:
                        row["status"] = "FAIL"
                if case_id == "D03":
                    mixed = [
                        maturity
                        for maturity in maturity_rows
                        if maturity.get("provenance_status")
                        == "CONCRETE_WITH_SYMBOLIC_REFS"
                    ]
                    row["mixed_provenance_preserved"] = (
                        len(mixed) == 2
                        and all(maturity.get("as_of") == "2026-09-15" for maturity in mixed)
                    )
                    if not row["mixed_provenance_preserved"]:
                        row["status"] = "FAIL"
                cases.append(row)
                if case_id == "D01" and repeat is not None:
                    first_state_sha = state_sha256(first["state"])
                    repeat_state_sha = state_sha256(repeat["state"])
                    cases.append(
                        {
                            "case_id": "D04",
                            "variant_id": "D04-repeat-same-logical-event-after-success",
                            "fixture": fixture_name,
                            "first": first,
                            "repeat": repeat,
                            "sink_count_before_repeat": first["successful_sink_count"],
                            "sink_count_after_repeat": repeat["successful_sink_count"],
                            "state_sha256_before_repeat": first_state_sha,
                            "state_sha256_after_repeat": repeat_state_sha,
                            "delivery_attempt_counts_after_repeat": [
                                item["attempt_count"] for item in repeat["deliveries"]
                            ],
                            "status": (
                                "PASS"
                                if first["successful_sink_count"] == 2
                                and repeat["successful_sink_count"] == 2
                                and first_state_sha == repeat_state_sha
                                and all(
                                    item["attempt_count"] == 1
                                    for item in repeat["deliveries"]
                                )
                                else "FAIL"
                            ),
                        }
                    )

        failure_fixture = fixtures["corz-concrete-v2"]
        with tempfile.TemporaryDirectory(prefix="m12cg-r3-d06-d07-") as value:
            root = Path(value)
            settings = settings_for(root)
            install_fixture(root, failure_fixture)
            failing = CaptureNotifier(fail_calls=(1, 2))
            succeeding = CaptureNotifier()
            with Session(engine_memory()) as session:
                seed_deliveries(session, failure_fixture)
                failed = await execute_delivery(
                    session=session,
                    fixture=failure_fixture,
                    settings=settings,
                    notifier=failing,
                )
                after_failure_state = state_snapshot(settings)
                recovered = await execute_delivery(
                    session=session,
                    fixture=failure_fixture,
                    settings=settings,
                    notifier=succeeding,
                )
            failure_ok = (
                failed["result"]["status"] == "pending"
                and after_failure_state is None
                and all(row["status"] == "pending" for row in failed["deliveries"])
            )
            recovery_ok = (
                recovered["result"]["status"] == "sent"
                and recovered["state"] is not None
                and recovered["successful_sink_count"] == 2
            )
            cases.extend(
                (
                    {
                        "case_id": "D06",
                        "variant_id": "D06-transport-failure-before-success",
                        "fixture": failure_fixture.name,
                        "failed_attempt": failed,
                        "accepted_state_after_failure": after_failure_state,
                        "quality_receipts": archived_quality_receipts(root),
                        "status": "PASS" if failure_ok else "FAIL",
                    },
                    {
                        "case_id": "D07",
                        "variant_id": "D07-failure-reentry-same-event",
                        "fixture": failure_fixture.name,
                        "failed_attempt": failed,
                        "reentry": recovered,
                        "status": "PASS" if recovery_ok else "FAIL",
                    },
                )
            )
    isolation = {
        "contract": "m12cg-r3-test-isolation-network-denial-v1",
        "temporary_roots_only": True,
        "synthetic_recipient_only": True,
        "external_transport_replaced_with_in_process_sink": True,
        "deliberate_probe_result": deliberate,
        "blocked_attempts": network.blocked_attempts,
        "network_attempts_blocked": len(network.blocked_attempts),
        "production_credentials_read": False,
        "production_sends": 0,
        "production_intents": 0,
        "status": (
            "PASS" if deliberate == "m12cg_r3_network_denied" else "FAIL"
        ),
    }
    write_json(out, "audits/test-isolation-and-network-denial-proof.json", isolation)
    return cases, isolation


async def new_independent_event_case(
    *,
    first_fixture: NativeFixture,
    new_fixture: NativeFixture,
) -> dict[str, object]:
    with tempfile.TemporaryDirectory(prefix="m12cg-r3-d05-") as value:
        root = Path(value)
        settings = settings_for(root)
        notifier = CaptureNotifier()
        engine = engine_memory()
        install_fixture(root, first_fixture)
        with Session(engine) as session:
            seed_deliveries(session, first_fixture)
            first = await execute_delivery(
                session=session,
                fixture=first_fixture,
                settings=settings,
                notifier=notifier,
            )
            install_fixture(root, new_fixture)
            seed_deliveries(session, new_fixture)
            second = await execute_delivery(
                session=session,
                fixture=new_fixture,
                settings=settings,
                notifier=notifier,
            )
        first_date = str(first_fixture.packet["assessment_date"])
        new_date = str(new_fixture.packet["assessment_date"])
        first_ids = {
            str(row["payload"].get(AI_ASSISTED_PILOT_METADATA_KEY, {}).get(
                "delivery_generation_id"
            ))
            for row in first["deliveries"]
            if row["assessment_date"] == first_date
        }
        second_ids = {
            str(row["payload"].get(AI_ASSISTED_PILOT_METADATA_KEY, {}).get(
                "delivery_generation_id"
            ))
            for row in second["deliveries"]
            if row["assessment_date"] == new_date
        }
        passed = (
            first["result"]["status"] == "sent"
            and second["result"]["status"] == "sent"
            and first["successful_sink_count"] == 2
            and second["successful_sink_count"] == 4
            and first_fixture.packet["packet_id"] != new_fixture.packet["packet_id"]
            and first_fixture.packet["assessment_date"]
            != new_fixture.packet["assessment_date"]
            and first_ids.isdisjoint(second_ids)
            and second["state"] is not None
        )
        return {
            "case_id": "D05",
            "variant_id": "D05-new-independent-packet-and-business-date",
            "first_fixture": first_fixture.name,
            "new_fixture": new_fixture.name,
            "first": first,
            "new_event": second,
            "first_delivery_generation_ids": sorted(first_ids),
            "new_delivery_generation_ids": sorted(second_ids),
            "sink_count_after_first": first["successful_sink_count"],
            "sink_count_after_new_event": second["successful_sink_count"],
            "status": "PASS" if passed else "FAIL",
        }


async def negative_binding_cases(
    *,
    fixture: NativeFixture,
    out: Path,
) -> list[dict[str, object]]:
    case_variants = {
        "D10": (
            "wrong_packet",
            "wrong_claim",
            "wrong_market",
            "wrong_date",
            "wrong_subject",
            "wrong_source_hash",
        ),
        "D11": (
            "candidate_mutation",
            "accepted_plan_mutation",
            "block_mutation",
            "plan_status_not_ready",
            "artifact_status_invalid",
            "contract_version_invalid",
        ),
    }
    expected_codes = {
        "wrong_packet": "v2_production_artifact_freshness_or_scope_mismatch",
        "wrong_claim": "v2_production_artifact_freshness_or_scope_mismatch",
        "wrong_market": "v2_production_artifact_freshness_or_scope_mismatch",
        "wrong_date": "v2_production_artifact_freshness_or_scope_mismatch",
        "wrong_subject": "v2_production_artifact_freshness_or_scope_mismatch",
        "wrong_source_hash": "v2_production_artifact_freshness_or_scope_mismatch",
        "accepted_plan_mutation": "v2_production_artifact_block_mismatch",
        "block_mutation": "v2_production_artifact_block_mismatch",
        "plan_status_not_ready": "v2_production_not_ready_block_visible",
        "artifact_status_invalid": "literal_error",
        "contract_version_invalid": "unsupported_accepted_v2_artifact_contract",
    }
    cases: list[dict[str, object]] = []
    for case_id, variants in case_variants.items():
        for variant in variants:
            mutated, transformation = mutate_artifact_payload(fixture, variant)
            prefix = f"payloads/native-negative/{case_id.lower()}-{variant}"
            before_path = write_json(
                out,
                f"{prefix}/before.json",
                fixture.artifact.model_dump(mode="json"),
            )
            after_path = write_json(out, f"{prefix}/after.json", mutated)
            with tempfile.TemporaryDirectory(
                prefix=f"m12cg-r3-{case_id.lower()}-{variant}-"
            ) as value:
                root = Path(value)
                settings = settings_for(root)
                paths = install_fixture(root, fixture, artifact_payload=mutated)
                direct = direct_load_observation(paths["final"], fixture=fixture)
                notifier = CaptureNotifier()
                with Session(engine_memory()) as session:
                    seed_deliveries(session, fixture)
                    routed = await execute_delivery(
                        session=session,
                        fixture=fixture,
                        settings=settings,
                        notifier=notifier,
                    )
                decision_rows = decision_metadata_rows(routed)
                stock_text = next(
                    (
                        str(row.get("text") or "")
                        for row in routed["sink"]
                        if row.get("ticker") == fixture.ticker
                    ),
                    "",
                )
                if variant == "candidate_mutation":
                    semantic_authority_unchanged = (
                        mutated["accepted_plans"]
                        == fixture.artifact.model_dump(mode="json")["accepted_plans"]
                        and mutated["blocks"]
                        == fixture.artifact.model_dump(mode="json")["blocks"]
                    )
                    passed = (
                        direct["status"] == "ACCEPTED"
                        and routed["result"]["status"] == "sent"
                        and routed["state"] is not None
                        and fixture.artifact.blocks[0].text in stock_text
                        and semantic_authority_unchanged
                    )
                    disposition = (
                        "NON_AUTHORITATIVE_CANDIDATE_FIELD_NO_ACCEPTED_SEMANTIC_EFFECT"
                    )
                    expected = "ACCEPTED_WITH_UNCHANGED_PLAN_AND_BLOCK_AUTHORITY"
                else:
                    expected_code = expected_codes[variant]
                    direct_matches = (
                        direct["status"] == "REJECTED"
                        and direct.get("exception_code") == expected_code
                    )
                    suppressed = any(
                        row.get("decision_state") == "V2_DECISION_SUPPRESSED_SAFE"
                        for row in decision_rows
                    )
                    passed = (
                        direct_matches
                        and routed["result"]["status"] == "sent"
                        and routed["state"] is None
                        and fixture.artifact.blocks[0].text not in stock_text
                        and suppressed
                    )
                    disposition = "AUTHORITATIVE_ARTIFACT_REJECTED_BASE_AI_SAFE_FALLBACK"
                    expected = f"REJECTED:{expected_code}"
                cases.append(
                    {
                        "case_id": case_id,
                        "variant_id": f"{case_id}-{variant}",
                        "fixture": fixture.name,
                        "transformation": transformation,
                        "before": {
                            "path": before_path.relative_to(out).as_posix(),
                            "sha256": sha256_file(before_path),
                        },
                        "after": {
                            "path": after_path.relative_to(out).as_posix(),
                            "sha256": sha256_file(after_path),
                        },
                        "direct_loader": direct,
                        "native_route": routed,
                        "decision_metadata": decision_rows,
                        "invalid_block_reached_sink": (
                            fixture.artifact.blocks[0].text in stock_text
                            if variant != "candidate_mutation"
                            else False
                        ),
                        "accepted_state_advanced": routed["state"] is not None,
                        "expected_result": expected,
                        "disposition": disposition,
                        "status": "PASS" if passed else "FAIL",
                    }
                )
    return cases


async def version_continuity_cases(
    *,
    legacy: NativeFixture,
    current: NativeFixture,
    out: Path,
) -> list[dict[str, object]]:
    with tempfile.TemporaryDirectory(prefix="m12cg-r3-d08-d09-") as value:
        root = Path(value)
        settings = settings_for(root)
        legacy_paths = install_fixture(root, legacy)
        preserved_legacy = root / "versioned-artifacts" / "accepted-v1.json"
        preserved_legacy.parent.mkdir(parents=True, exist_ok=True)
        preserved_legacy.write_bytes(legacy_paths["final"].read_bytes())
        legacy_hash_before = sha256_file(preserved_legacy)
        legacy_direct = direct_load_observation(preserved_legacy, fixture=legacy)
        notifier = CaptureNotifier()
        with Session(engine_memory()) as session:
            seed_deliveries(session, legacy)
            first = await execute_delivery(
                session=session,
                fixture=legacy,
                settings=settings,
                notifier=notifier,
            )
            current_paths = install_fixture(root, current)
            current_direct = direct_load_observation(
                current_paths["final"], fixture=current
            )
            repeated = await execute_delivery(
                session=session,
                fixture=current,
                settings=settings,
                notifier=notifier,
            )
        legacy_hash_after = sha256_file(preserved_legacy)
        packet_identity_equal = legacy.packet == current.packet
        accepted_semantics_equal = (
            accepted_semantic_sha256(legacy) == accepted_semantic_sha256(current)
        )
        no_duplicate = (
            first["successful_sink_count"] == 2
            and repeated["successful_sink_count"] == 2
            and all(row["attempt_count"] == 1 for row in repeated["deliveries"])
        )
        d08_pass = (
            packet_identity_equal
            and accepted_semantics_equal
            and legacy.artifact.contract != current.artifact.contract
            and first["result"]["status"] == "sent"
            and repeated["result"]["status"] == "sent"
            and no_duplicate
            and first["state"] is not None
            and repeated["state"] is not None
        )
        d09_pass = (
            legacy_direct["status"] == "ACCEPTED"
            and current_direct["status"] == "ACCEPTED"
            and legacy_hash_before == legacy_hash_after
            and legacy.artifact.contract == "v2-accepted-production-artifact-v1"
            and current.artifact.contract == "v2-accepted-production-artifact-v2"
        )
        exported_legacy = write_json(
            out,
            "payloads/version-continuity/accepted-v1.json",
            legacy.artifact.model_dump(mode="json"),
        )
        exported_current = write_json(
            out,
            "payloads/version-continuity/accepted-v2.json",
            current.artifact.model_dump(mode="json"),
        )
        shared = {
            "logical_event_packet_sha256": legacy.source_hashes["packet"],
            "legacy_artifact_sha256": legacy.source_hashes["artifact"],
            "current_artifact_sha256": current.source_hashes["artifact"],
            "legacy_contract": legacy.artifact.contract,
            "current_contract": current.artifact.contract,
            "accepted_semantics_legacy_sha256": accepted_semantic_sha256(legacy),
            "accepted_semantics_current_sha256": accepted_semantic_sha256(current),
            "packet_identity_equal": packet_identity_equal,
            "accepted_semantics_equal": accepted_semantics_equal,
            "first": first,
            "repeat_after_version_change": repeated,
            "sink_count_before": first["successful_sink_count"],
            "sink_count_after": repeated["successful_sink_count"],
            "state_sha256_before": state_sha256(first["state"]),
            "state_sha256_after": state_sha256(repeated["state"]),
        }
        return [
            {
                "case_id": "D08",
                "variant_id": "D08-metadata-only-v1-to-v2-same-event",
                **shared,
                "unintended_duplicate": not no_duplicate,
                "semantic_delta": not accepted_semantics_equal,
                "status": "PASS" if d08_pass else "FAIL",
            },
            {
                "case_id": "D09",
                "variant_id": "D09-legacy-new-coexistence",
                **shared,
                "legacy_direct_loader": legacy_direct,
                "current_direct_loader": current_direct,
                "legacy_preserved_sha256_before": legacy_hash_before,
                "legacy_preserved_sha256_after": legacy_hash_after,
                "exported_artifacts": {
                    "legacy": {
                        "path": exported_legacy.relative_to(out).as_posix(),
                        "sha256": sha256_file(exported_legacy),
                    },
                    "current": {
                        "path": exported_current.relative_to(out).as_posix(),
                        "sha256": sha256_file(exported_current),
                    },
                },
                "status": "PASS" if d09_pass else "FAIL",
            },
        ]


async def sidecar_and_authority_cases(
    *,
    fixture: NativeFixture,
    swapped_fixture: NativeFixture,
    out: Path,
) -> list[dict[str, object]]:
    cases: list[dict[str, object]] = []
    sidecar_variants = (
        ("missing", None, None),
        (
            "forged",
            {
                "contract": "v2-accepted-production-receipt-v1",
                "status": "PASS",
                "packet_id": "forged-packet",
                "artifact_sha256": "f" * 64,
            },
            None,
        ),
        (
            "forged_cannot_elevate_invalid_artifact",
            {
                "contract": "v2-accepted-production-receipt-v1",
                "status": "PASS",
                "packet_id": fixture.packet["packet_id"],
                "artifact_sha256": fixture.source_hashes["artifact"],
            },
            "wrong_source_hash",
        ),
    )
    for variant, receipt, mutation in sidecar_variants:
        payload = artifact_payload(fixture)
        transformation = None
        if mutation is not None:
            payload, transformation = mutate_artifact_payload(fixture, mutation)
        with tempfile.TemporaryDirectory(prefix=f"m12cg-r3-d12-{variant}-") as value:
            root = Path(value)
            settings = settings_for(root)
            paths = install_fixture(
                root,
                fixture,
                artifact_payload=payload,
                receipt_payload=receipt,
            )
            direct = direct_load_observation(paths["final"], fixture=fixture)
            notifier = CaptureNotifier()
            with Session(engine_memory()) as session:
                seed_deliveries(session, fixture)
                routed = await execute_delivery(
                    session=session,
                    fixture=fixture,
                    settings=settings,
                    notifier=notifier,
                )
            decision_rows = decision_metadata_rows(routed)
            if mutation is None:
                passed = (
                    direct["status"] == "ACCEPTED"
                    and routed["result"]["status"] == "sent"
                    and routed["state"] is not None
                )
                disposition = "DIAGNOSTIC_SIDECAR_NOT_CONSUMED_BY_NATIVE_LOADER"
            else:
                passed = (
                    direct["status"] == "REJECTED"
                    and routed["state"] is None
                    and any(
                        row.get("decision_state") == "V2_DECISION_SUPPRESSED_SAFE"
                        for row in decision_rows
                    )
                )
                disposition = "DIAGNOSTIC_SIDECAR_CANNOT_ELEVATE_INVALID_ARTIFACT"
            cases.append(
                {
                    "case_id": "D12",
                    "variant_id": f"D12-{variant}",
                    "receipt_present": paths["receipt"].exists(),
                    "receipt_payload": receipt,
                    "artifact_transformation": transformation,
                    "direct_loader": direct,
                    "native_route": routed,
                    "decision_metadata": decision_rows,
                    "disposition": disposition,
                    "status": "PASS" if passed else "FAIL",
                }
            )

    with tempfile.TemporaryDirectory(prefix="m12cg-r3-d13-receipt-") as value:
        root = Path(value)
        settings = settings_for(root)
        install_fixture(root, fixture)
        failing = CaptureNotifier(fail_calls=(1, 2))
        succeeding = CaptureNotifier()
        engine = engine_memory()
        with Session(engine) as session:
            seed_deliveries(session, fixture)
            pending = await execute_delivery(
                session=session,
                fixture=fixture,
                settings=settings,
                notifier=failing,
            )
            receipt_path = next(root.rglob("message-quality-receipt.json"))
            receipt_before = json.loads(receipt_path.read_text(encoding="utf-8"))
            receipt_before_sha = sha256_file(receipt_path)
            tampered_receipt = deepcopy(receipt_before)
            tampered_receipt["rendered_payload_set_sha256"] = "0" * 64
            receipt_path.write_bytes(pretty_bytes(tampered_receipt))
            receipt_after_sha = sha256_file(receipt_path)
            rejected = await execute_delivery(
                session=session,
                fixture=fixture,
                settings=settings,
                notifier=succeeding,
            )
        receipt_pass = (
            pending["result"]["status"] == "pending"
            and rejected["result"]["status"] == "quality_receipt_invalid"
            and rejected["successful_sink_count"] == 0
            and rejected["state"] is None
            and receipt_before_sha != receipt_after_sha
        )
        before_path = write_json(
            out,
            "payloads/authority-negative/runtime-quality-receipt-before.json",
            receipt_before,
        )
        after_path = write_json(
            out,
            "payloads/authority-negative/runtime-quality-receipt-after.json",
            tampered_receipt,
        )
        cases.append(
            {
                "case_id": "D13",
                "variant_id": "D13-runtime-message-quality-receipt-tamper",
                "authoritative_owner": "runtime-message-quality-receipt-v2",
                "pending_before_tamper": pending,
                "reentry_after_tamper": rejected,
                "before": {
                    "path": before_path.relative_to(out).as_posix(),
                    "sha256": sha256_file(before_path),
                },
                "after": {
                    "path": after_path.relative_to(out).as_posix(),
                    "sha256": sha256_file(after_path),
                },
                "status": "PASS" if receipt_pass else "FAIL",
            }
        )

    with tempfile.TemporaryDirectory(prefix="m12cg-r3-d13-artifact-") as value:
        root = Path(value)
        settings = settings_for(root)
        swapped_payload = artifact_payload(swapped_fixture)
        paths = install_fixture(root, fixture, artifact_payload=swapped_payload)
        direct = direct_load_observation(paths["final"], fixture=fixture)
        notifier = CaptureNotifier()
        with Session(engine_memory()) as session:
            seed_deliveries(session, fixture)
            routed = await execute_delivery(
                session=session,
                fixture=fixture,
                settings=settings,
                notifier=notifier,
            )
        decision_rows = decision_metadata_rows(routed)
        artifact_pass = (
            direct["status"] == "REJECTED"
            and direct.get("exception_code")
            == "v2_production_artifact_freshness_or_scope_mismatch"
            and routed["state"] is None
            and any(
                row.get("decision_state") == "V2_DECISION_SUPPRESSED_SAFE"
                for row in decision_rows
            )
        )
        cases.append(
            {
                "case_id": "D13",
                "variant_id": "D13-authoritative-artifact-swap",
                "authoritative_owner": "load_accepted_v2_production_artifact",
                "installed_fixture": fixture.name,
                "swapped_artifact_fixture": swapped_fixture.name,
                "swapped_artifact_sha256": sha256_bytes(
                    canonical_bytes(swapped_payload)
                ),
                "direct_loader": direct,
                "native_route": routed,
                "decision_metadata": decision_rows,
                "status": "PASS" if artifact_pass else "FAIL",
            }
        )
    return cases


def telegram_cursor_rows(snapshot: Mapping[str, object]) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    for delivery in snapshot.get("deliveries", []):
        if not isinstance(delivery, Mapping):
            continue
        payload = delivery.get("payload")
        if not isinstance(payload, Mapping):
            continue
        metadata = payload.get(notification_service.TELEGRAM_DELIVERY_METADATA_KEY)
        if not isinstance(metadata, Mapping):
            continue
        rows.append(
            {
                "ticker": delivery.get("ticker"),
                "delivery_status": delivery.get("status"),
                "chunk_count": metadata.get("chunk_count"),
                "next_chunk_index": metadata.get("next_chunk_index"),
                "content_sha256": metadata.get("content_sha256"),
                "source_sha256": metadata.get("source_sha256"),
            }
        )
    return rows


def chunk_test_fixture(fixture: NativeFixture) -> NativeFixture:
    output = deepcopy(fixture.output)
    market_review = output["market_review"]
    assert isinstance(market_review, dict)
    core = market_review["core_judgment"]
    assert isinstance(core, dict)
    core["text"] = (
        "오프라인 chunk cursor 검증을 위해 시장 문맥의 길이만 확장했습니다. "
        + "성장, 물가, 금리, 유동성, 위험선호, 실적 기대의 상호작용을 구분해 확인합니다. "
        * 18
    )
    return replace(
        fixture,
        name=f"{fixture.name}-chunked-market",
        output=output,
        transformations={
            **fixture.transformations,
            "market_message_length_only_extension": True,
            "stock_or_accepted_decision_semantics_modified": False,
        },
    )


async def chunk_crash_overlap_cases(
    *,
    fixture: NativeFixture,
) -> list[dict[str, object]]:
    cases: list[dict[str, object]] = []
    fixture = chunk_test_fixture(fixture)
    with tempfile.TemporaryDirectory(prefix="m12cg-r3-d14-partial-") as value:
        root = Path(value)
        settings = settings_for(root, max_chars=1000)
        install_fixture(root, fixture)
        partial_notifier = ChunkCaptureNotifier(settings, fail_calls=(2,))
        recovery_notifier = ChunkCaptureNotifier(settings)
        engine = engine_memory()
        with Session(engine) as session:
            seed_deliveries(session, fixture)
            partial = await execute_chunk_delivery(
                session=session,
                fixture=fixture,
                settings=settings,
                notifier=partial_notifier,
            )
            cursors_after_partial = telegram_cursor_rows(partial)
            recovered = await execute_chunk_delivery(
                session=session,
                fixture=fixture,
                settings=settings,
                notifier=recovery_notifier,
            )
            cursors_after_recovery = telegram_cursor_rows(recovered)
        first_successful_chunk = (
            partial_notifier.sent_chunks[0] if partial_notifier.sent_chunks else None
        )
        cursor_resume_pass = (
            partial["result"]["status"] == "pending"
            and partial["state"] is None
            and any(row.get("next_chunk_index") == 1 for row in cursors_after_partial)
            and recovered["result"]["status"] == "sent"
            and recovered["state"] is not None
            and first_successful_chunk is not None
            and first_successful_chunk not in recovery_notifier.sent_chunks
            and all(
                row.get("next_chunk_index") == row.get("chunk_count")
                for row in cursors_after_recovery
            )
        )
        cases.append(
            {
                "case_id": "D14",
                "variant_id": "D14-chunk-partial-failure-cursor-resume",
                "partial": partial,
                "recovered": recovered,
                "cursors_after_partial": cursors_after_partial,
                "cursors_after_recovery": cursors_after_recovery,
                "first_successful_chunk_repeated": (
                    first_successful_chunk in recovery_notifier.sent_chunks
                    if first_successful_chunk is not None
                    else None
                ),
                "delivery_guarantee": "CURSOR_RESUME_AFTER_COMMITTED_CHUNK",
                "status": "PASS" if cursor_resume_pass else "FAIL",
            }
        )

    with tempfile.TemporaryDirectory(prefix="m12cg-r3-d14-crash-") as value:
        root = Path(value)
        settings = settings_for(root, max_chars=1000)
        install_fixture(root, fixture)
        crash_notifier = ChunkCaptureNotifier(
            settings,
            crash_after_success_calls=(1,),
        )
        recovery_notifier = ChunkCaptureNotifier(settings)
        engine = engine_memory()
        crash_observation: dict[str, object]
        with Session(engine) as session:
            seed_deliveries(session, fixture)
            try:
                await execute_chunk_delivery(
                    session=session,
                    fixture=fixture,
                    settings=settings,
                    notifier=crash_notifier,
                )
            except SimulatedProcessCrash as exc:
                session.rollback()
                crash_observation = {
                    "exception_type": type(exc).__name__,
                    "exception_code": str(exc),
                    "deliveries": delivery_rows(session),
                    "state": state_snapshot(settings),
                    "attempted_chunks": list(crash_notifier.attempted_chunks),
                    "sent_chunks": list(crash_notifier.sent_chunks),
                }
            else:
                crash_observation = {
                    "exception_type": None,
                    "exception_code": None,
                    "deliveries": delivery_rows(session),
                    "state": state_snapshot(settings),
                    "attempted_chunks": list(crash_notifier.attempted_chunks),
                    "sent_chunks": list(crash_notifier.sent_chunks),
                }
        with Session(engine) as session:
            recovered = await execute_chunk_delivery(
                session=session,
                fixture=fixture,
                settings=settings,
                notifier=recovery_notifier,
            )
        sent_before_crash = crash_observation["sent_chunks"]
        first_chunk = (
            sent_before_crash[0]
            if isinstance(sent_before_crash, list) and sent_before_crash
            else None
        )
        duplicate_after_crash = bool(
            first_chunk is not None and first_chunk in recovery_notifier.sent_chunks
        )
        crash_pass = (
            crash_observation["exception_type"] == "SimulatedProcessCrash"
            and crash_observation["state"] is None
            and recovered["result"]["status"] == "sent"
            and recovered["state"] is not None
            and duplicate_after_crash
        )
        cases.append(
            {
                "case_id": "D14",
                "variant_id": "D14-post-send-pre-cursor-crash-window",
                "crash": crash_observation,
                "recovered": recovered,
                "first_chunk_repeated_after_crash": duplicate_after_crash,
                "delivery_guarantee": (
                    "AT_LEAST_ONCE_CRASH_WINDOW_OBSERVED_NO_EXACTLY_ONCE_CLAIM"
                ),
                "status": "PASS" if crash_pass else "FAIL",
            }
        )

    with tempfile.TemporaryDirectory(prefix="m12cg-r3-d14-overlap-") as value:
        root = Path(value)
        settings = settings_for(root)
        install_fixture(root, fixture)
        notifier = CaptureNotifier()
        engine = engine_memory()
        acquired = threading.Event()
        release = threading.Event()

        def hold_native_lock() -> None:
            with delivery_service._pilot_lock(str(fixture.packet["packet_id"])):
                acquired.set()
                release.wait(timeout=5.0)

        with Session(engine) as session:
            seed_deliveries(session, fixture)
            with patch.object(delivery_service, "get_settings", lambda: settings):
                holder = threading.Thread(target=hold_native_lock, daemon=True)
                holder.start()
                lock_acquired = acquired.wait(timeout=2.0)
                timer = threading.Timer(0.2, release.set)
                timer.start()
                started = time.monotonic()
                routed = await execute_delivery(
                    session=session,
                    fixture=fixture,
                    settings=settings,
                    notifier=notifier,
                )
                elapsed = time.monotonic() - started
                timer.cancel()
                release.set()
                holder.join(timeout=2.0)
        overlap_pass = (
            lock_acquired
            and not holder.is_alive()
            and elapsed >= 0.15
            and routed["result"]["status"] == "sent"
            and routed["successful_sink_count"] == 2
            and routed["state"] is not None
        )
        cases.append(
            {
                "case_id": "D14",
                "variant_id": "D14-overlapping-claim-native-lock-serialization",
                "lock_owner": "ai_assisted_delivery_service._pilot_lock(packet_id)",
                "lock_acquired_before_delivery": lock_acquired,
                "delivery_wait_seconds": elapsed,
                "holder_completed": not holder.is_alive(),
                "native_route": routed,
                "delivery_guarantee": "SERIALIZED_BY_PACKET_ID_FLOCK",
                "status": "PASS" if overlap_pass else "FAIL",
            }
        )
    return cases


async def run_probe(args: argparse.Namespace) -> None:
    out = args.output_dir.resolve()
    out.mkdir(parents=True, exist_ok=True)
    m12ce_root = find_source_root(args.m12ce_bundle_root.resolve(), "m12ce-new-full22")
    m12cb_root = find_source_root(
        args.m12cb_bundle_root.resolve(),
        "stage2-frozen-core-claim-language",
    )
    with tempfile.TemporaryDirectory(prefix="m12cg-r3-fixture-state-") as fixture_state:
        fixture_settings = settings_for(Path(fixture_state))
        fixtures = {
            "corz-concrete-v2": build_fixture(
                source_root=m12ce_root,
                ticker="CORZ",
                settings=fixture_settings,
                source_label="corz-concrete-v2",
            ),
            "corz-concrete-v1": build_fixture(
                source_root=m12ce_root,
                ticker="CORZ",
                settings=fixture_settings,
                source_label="corz-concrete-v1",
                legacy_normalization=True,
            ),
            "corz-version-event-v2": build_fixture(
                source_root=m12ce_root,
                ticker="CORZ",
                settings=fixture_settings,
                source_label="corz-version-event",
                fixture_name="corz-version-event-v2",
            ),
            "corz-version-event-v1": build_fixture(
                source_root=m12ce_root,
                ticker="CORZ",
                settings=fixture_settings,
                source_label="corz-version-event",
                fixture_name="corz-version-event-v1",
                legacy_normalization=True,
            ),
            "corz-independent-event-v2": build_fixture(
                source_root=m12ce_root,
                ticker="CORZ",
                settings=fixture_settings,
                source_label="corz-independent-event",
                fixture_name="corz-independent-event-v2",
                packet_id_override="m12cg-r3-independent-us-event",
                assessment_date_override="2026-09-16",
            ),
            "cpng-independent-v2": build_fixture(
                source_root=m12ce_root,
                ticker="CPNG",
                settings=fixture_settings,
                source_label="cpng-independent-v2",
            ),
            "skhy-symbolic-v2": build_fixture(
                source_root=m12ce_root,
                ticker="SKHY",
                settings=fixture_settings,
                source_label="skhy-symbolic-v2",
            ),
            "skhy-mixed-m12cd-v2": build_fixture(
                source_root=m12cb_root,
                ticker="SKHY",
                settings=fixture_settings,
                source_label="skhy-mixed-m12cd-v2",
                historical=True,
            ),
        }
    fixture_manifest = {
        "contract": "m12cg-r3-native-fixture-source-transformation-v1",
        "projection_policy": (
            "SYNTHETIC_GENERIC_CANONICAL_SUBSET_REGENERATED_THROUGH_EXISTING_APIS"
        ),
        "original_whole_batch_coverage_claimed": False,
        "fixtures": [export_fixture(out, fixture) for fixture in fixtures.values()],
    }
    write_json(
        out,
        "audits/native-fixture-source-and-transformation-manifest.json",
        fixture_manifest,
    )
    numeric = numeric_owner_trace(m12ce_root, out)
    write_json(
        out,
        "audits/googl-hut-numeric-token-claim-ref-owner-trace.json",
        numeric,
    )
    cases, isolation = await positive_and_reentry_cases(fixtures=fixtures, out=out)
    cases.append(
        await new_independent_event_case(
            first_fixture=fixtures["corz-concrete-v2"],
            new_fixture=fixtures["corz-independent-event-v2"],
        )
    )
    cases.extend(
        await version_continuity_cases(
            legacy=fixtures["corz-version-event-v1"],
            current=fixtures["corz-version-event-v2"],
            out=out,
        )
    )
    cases.extend(
        await negative_binding_cases(
            fixture=fixtures["corz-concrete-v2"],
            out=out,
        )
    )
    cases.extend(
        await sidecar_and_authority_cases(
            fixture=fixtures["corz-concrete-v2"],
            swapped_fixture=fixtures["cpng-independent-v2"],
            out=out,
        )
    )
    cases.extend(
        await chunk_crash_overlap_cases(
            fixture=fixtures["corz-concrete-v2"],
        )
    )
    case_failures = [
        f"{row['case_id']}:{row.get('variant_id') or row.get('fixture')}"
        for row in cases
        if row.get("status") != "PASS"
    ]
    write_json(
        out,
        "audits/native-delivery-case-matrix.json",
        {
            "contract": "m12cg-r3-native-delivery-case-matrix-v1",
            "required_case_ids": [f"D{index:02d}" for index in range(1, 15)],
            "observed_case_ids": sorted({str(row["case_id"]) for row in cases}),
            "case_variant_count": len(cases),
            "failed_variants": case_failures,
            "cases": cases,
            "status": "PASS" if not case_failures else "FAIL",
        },
    )
    result = {
        "contract": "m12cg-r3-native-probe-v1",
        "numeric": numeric,
        "cases": cases,
        "isolation": isolation,
        "fixture_manifest": fixture_manifest,
        "native_case_failures": case_failures,
        "native_offline_proof_status": "PASS" if not case_failures else "FAIL",
        "status": (
            "FAIL"
            if case_failures
            else (
                "PARTIAL"
                if numeric["numeric_runtime_repair_required"]
                else "PASS"
            )
        ),
    }
    write_json(out, args.result_name, result)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--m12ce-bundle-root", type=Path, required=True)
    parser.add_argument("--m12cb-bundle-root", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--result-name", default="audits/native-probe-result.json")
    args = parser.parse_args()
    asyncio.run(run_probe(args))


if __name__ == "__main__":
    main()
