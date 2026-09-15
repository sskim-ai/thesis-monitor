from __future__ import annotations

import json
from collections.abc import Mapping, Sequence
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from pathlib import Path
import tempfile

from sqlalchemy import Connection, Engine, insert, select, update
from sqlalchemy.exc import IntegrityError

from app.models.accepted_assessment import (
    accepted_assessment_v2,
    canonical_acceptance_receipt_v1,
    monitoring_current_state_v2,
    notification_outbox_v2,
    warning_state_v2,
    warning_transition_v2,
)
from app.schemas.accepted_assessment_v2 import (
    CanonicalAcceptanceReceiptV1,
    CanonicalWarningObservationV1,
    DailySummaryNotificationV1,
    MaterialTransitionNotificationV1,
    NotificationEventKind,
    PersistenceApplicationResult,
    PersistenceEligibility,
    SourceEvidenceSnapshotIdentity,
    TrustedFinalizationResult,
    WarningObservationValue,
)
from app.services.canonical_acceptance_receipt_service import (
    ACCEPTED_ASSESSMENT_CONTRACT,
    acceptance_id_for,
    accepted_payload_dict,
    canonical_json,
    canonical_sha256,
    issue_canonical_acceptance_receipt,
    normalize_utc,
    verify_canonical_acceptance_receipt,
)
from app.services.direction_timing_ownership_service import DirectionalCoreCandidate


TOTAL_ORDER_CONTRACT = "accepted-assessment-total-order-v1"
APPLICATION_TRANSACTION_CONTRACT = "accepted-assessment-application-transaction-v2"
WARNING_IDENTITY_CONTRACT = "warning-identity-v2"
WARNING_TRANSITION_CONTRACT = "warning-transition-v2"
OUTBOX_CONTRACT = "notification-outbox-v2"
CURRENT_STATE_CAS_MAX_ATTEMPTS = 3


class PersistenceV2Error(RuntimeError):
    pass


class PersistenceV2IntegrityError(PersistenceV2Error):
    pass


class PersistenceV2LocalGateError(PersistenceV2Error):
    pass


def require_local_ephemeral_engine(engine: Engine, *, explicitly_enabled: bool) -> None:
    if not explicitly_enabled:
        raise PersistenceV2LocalGateError("persistence_v2_local_gate_disabled")
    if engine.dialect.name != "sqlite":
        raise PersistenceV2LocalGateError("persistence_v2_local_sqlite_required")
    database = engine.url.database
    if database in {None, "", ":memory:"}:
        return
    database_path = Path(database).expanduser().resolve()
    temporary_root = Path(tempfile.gettempdir()).resolve()
    if not database_path.is_relative_to(temporary_root):
        raise PersistenceV2LocalGateError("persistence_v2_ephemeral_path_required")


def _utc(value: datetime) -> datetime:
    if value.tzinfo is None:
        return value.replace(tzinfo=UTC)
    return value.astimezone(UTC)


def _now() -> datetime:
    return datetime.now(UTC)


def _json_value(value: str) -> object:
    return json.loads(value)


def _receipt_row(receipt: CanonicalAcceptanceReceiptV1) -> dict[str, object]:
    value = receipt.model_dump(mode="python")
    value["source_evidence_snapshot_identity"] = canonical_json(
        receipt.source_evidence_snapshot_identity.model_dump(mode="json")
    )
    value["quarantine_reason_codes"] = canonical_json(list(receipt.quarantine_reason_codes))
    return value


def receipt_from_row(row: Mapping[str, object]) -> CanonicalAcceptanceReceiptV1:
    return CanonicalAcceptanceReceiptV1.model_validate(
        {
            **dict(row),
            "generation_generated_at": _utc(row["generation_generated_at"]),
            "effective_at": _utc(row["effective_at"]),
            "accepted_at": _utc(row["accepted_at"]),
            "source_evidence_snapshot_identity": SourceEvidenceSnapshotIdentity.model_validate(
                _json_value(str(row["source_evidence_snapshot_identity"]))
            ),
            "quarantine_reason_codes": tuple(
                _json_value(str(row["quarantine_reason_codes"]))
            ),
        }
    )


def total_ordering_key(
    *,
    effective_at: datetime,
    generation_generated_at: datetime,
    generation_id: str,
    acceptance_id: str,
) -> tuple[datetime, datetime, str, str]:
    return (
        normalize_utc(effective_at, field="effective_at"),
        normalize_utc(generation_generated_at, field="generation_generated_at"),
        generation_id,
        acceptance_id,
    )


def ordering_key_json(key: tuple[datetime, datetime, str, str]) -> str:
    return canonical_json(
        {
            "contract": TOTAL_ORDER_CONTRACT,
            "effective_at_utc": key[0].isoformat(timespec="microseconds").replace("+00:00", "Z"),
            "generation_generated_at_utc": key[1]
            .isoformat(timespec="microseconds")
            .replace("+00:00", "Z"),
            "generation_id": key[2],
            "acceptance_id": key[3],
        }
    )


_EXTRACT_FIELDS: dict[str, str] = {
    "business_thesis_context_json": "business_thesis_context",
    "earnings_estimate_context_json": "earnings_estimate_context",
    "market_expectation_context_json": "market_expectation_context",
    "valuation_context_json": "valuation_context",
    "risk_context_json": "risk_context",
    "sector_interpretation_json": "sector_interpretation",
    "buy_drivers_json": "buy_drivers",
    "sell_drivers_json": "sell_drivers",
    "dominant_evidence_json": "dominant_evidence",
    "uncertainty_limit_json": "uncertainty_limit",
    "core_judgment_json": "core_investment_judgment",
    "structured_unknowns_json": "unknown_treatments",
    "material_anchor_refs_json": "material_directional_anchor_basis",
    "new_buyer_json": "fundamental_new_buyer",
    "holder_json": "fundamental_holder",
    "reevaluation_up_json": "business_reevaluation_up",
    "reevaluation_down_json": "business_reevaluation_down",
}


def accepted_assessment_row(
    result: TrustedFinalizationResult,
    receipt: CanonicalAcceptanceReceiptV1,
) -> dict[str, object]:
    payload = accepted_payload_dict(result)
    payload_json = canonical_json(payload)
    payload_hash = canonical_sha256(payload)
    if payload_hash != receipt.final_composed_candidate_hash:
        raise PersistenceV2IntegrityError("accepted_payload_receipt_hash_mismatch")
    key = total_ordering_key(
        effective_at=result.effective_at,
        generation_generated_at=result.generation_generated_at,
        generation_id=result.generation_id,
        acceptance_id=receipt.acceptance_id,
    )
    security_json = canonical_json(result.security_basis_provenance)
    row: dict[str, object] = {
        "acceptance_id": receipt.acceptance_id,
        "schema_contract_version": ACCEPTED_ASSESSMENT_CONTRACT,
        "source_domain": "CANONICAL_MODEL_ACCEPTED",
        "ticker": result.ticker,
        "thesis_version": result.thesis_version,
        "assessment_date": result.assessment_date,
        "effective_at_utc": key[0],
        "generation_generated_at_utc": key[1],
        "generation_id": result.generation_id,
        "ordering_key_json": ordering_key_json(key),
        "overall_direction": payload["overall_direction"],
        "directional_balance_buy": Decimal(str(payload["directional_balance"]["buy"])),
        "directional_balance_sell": Decimal(str(payload["directional_balance"]["sell"])),
        "hold_lean": payload["hold_lean"],
        "directional_confidence": payload["directional_confidence"],
        "canonical_business_delta": payload["business_thesis_change"],
        "canonical_payload_contract_version": result.accepted_payload_contract_version,
        "canonical_payload_json": payload_json,
        "canonical_payload_sha256": payload_hash,
        "security_basis_provenance_json": security_json,
        "security_basis_provenance_sha256": canonical_sha256(
            result.security_basis_provenance
        ),
    }
    for column, field in _EXTRACT_FIELDS.items():
        row[column] = canonical_json(payload[field])
    validate_extract_consistency(row)
    return row


def validate_extract_consistency(row: Mapping[str, object]) -> None:
    try:
        payload = _json_value(str(row["canonical_payload_json"]))
    except (KeyError, json.JSONDecodeError) as exc:
        raise PersistenceV2IntegrityError("canonical_payload_json_invalid") from exc
    if not isinstance(payload, dict):
        raise PersistenceV2IntegrityError("canonical_payload_object_required")
    if canonical_sha256(payload) != row.get("canonical_payload_sha256"):
        raise PersistenceV2IntegrityError("canonical_payload_sha256_mismatch")
    try:
        DirectionalCoreCandidate.model_validate(payload)
    except Exception as exc:
        raise PersistenceV2IntegrityError("canonical_payload_contract_invalid") from exc
    scalar_checks = {
        "overall_direction": payload.get("overall_direction"),
        "hold_lean": payload.get("hold_lean"),
        "directional_confidence": payload.get("directional_confidence"),
        "canonical_business_delta": payload.get("business_thesis_change"),
    }
    for column, expected in scalar_checks.items():
        if row.get(column) != expected:
            raise PersistenceV2IntegrityError(f"accepted_extract_mismatch:{column}")
    balance = payload.get("directional_balance")
    if not isinstance(balance, dict):
        raise PersistenceV2IntegrityError("accepted_directional_balance_invalid")
    for column, field in (
        ("directional_balance_buy", "buy"),
        ("directional_balance_sell", "sell"),
    ):
        if Decimal(str(row.get(column))) != Decimal(str(balance.get(field))):
            raise PersistenceV2IntegrityError(f"accepted_extract_mismatch:{column}")
    for column, field in _EXTRACT_FIELDS.items():
        try:
            actual = _json_value(str(row[column]))
        except (KeyError, json.JSONDecodeError) as exc:
            raise PersistenceV2IntegrityError(f"accepted_extract_invalid:{column}") from exc
        if actual != payload.get(field):
            raise PersistenceV2IntegrityError(f"accepted_extract_mismatch:{column}")
    security = _json_value(str(row["security_basis_provenance_json"]))
    if canonical_sha256(security) != row.get("security_basis_provenance_sha256"):
        raise PersistenceV2IntegrityError("security_basis_provenance_hash_mismatch")


def _allowed_evidence_refs(payload: object) -> frozenset[str]:
    refs: set[str] = set()

    def walk(value: object, *, key: str | None = None) -> None:
        if isinstance(value, Mapping):
            for child_key, child in value.items():
                walk(child, key=str(child_key))
            return
        if isinstance(value, Sequence) and not isinstance(value, (str, bytes)):
            if key and (key.endswith("refs") or key.endswith("basis")):
                refs.update(str(item) for item in value if isinstance(item, str))
            for child in value:
                walk(child)

    walk(payload)
    return frozenset(refs)


def warning_identity(
    *,
    ticker: str,
    thesis_version: int,
    observation: CanonicalWarningObservationV1,
) -> str:
    return canonical_sha256(
        {
            "domain": WARNING_IDENTITY_CONTRACT,
            "ticker": ticker,
            "thesis_version": thesis_version,
            "warning_type": observation.warning_type,
            "condition_contract_version": observation.condition_contract_version,
            "condition_identity": observation.condition_identity,
        }
    )


def warning_transition_id(
    *,
    identity: str,
    episode: int,
    from_state: str | None,
    to_state: str,
    acceptance_id: str,
    transition_reason_version: str,
) -> str:
    return canonical_sha256(
        {
            "domain": WARNING_TRANSITION_CONTRACT,
            "warning_identity": identity,
            "episode": episode,
            "from_state": from_state,
            "to_state": to_state,
            "triggering_acceptance_id": acceptance_id,
            "transition_reason_version": transition_reason_version,
        }
    )


def _next_warning_state(
    current: str | None,
    observation: WarningObservationValue,
    episode: int,
) -> tuple[str | None, int, bool]:
    if current is None:
        if observation in {WarningObservationValue.CONFIRMED, WarningObservationValue.WORSENED}:
            return "open", 1, True
        return None, 0, False
    if current == "open":
        if observation == WarningObservationValue.WORSENED:
            return "escalated", episode, True
        if observation == WarningObservationValue.RECOVERED:
            return "resolved", episode, True
        return current, episode, False
    if current == "escalated":
        if observation == WarningObservationValue.RECOVERED:
            return "resolved", episode, True
        return current, episode, False
    if current == "resolved":
        if observation in {WarningObservationValue.CONFIRMED, WarningObservationValue.WORSENED}:
            return "open", episode + 1, True
        return current, episode, False
    raise PersistenceV2IntegrityError(f"unknown_warning_state:{current}")


def _outbox_identity(
    *,
    source_event_id: str,
    channel: str,
    payload_contract_version: str,
    payload_sha256: str,
) -> str:
    return canonical_sha256(
        {
            "domain": "notification-outbox-event-v2",
            "source_event_id": source_event_id,
            "channel": channel,
            "payload_contract_version": payload_contract_version,
            "payload_sha256": payload_sha256,
        }
    )


def _insert_outbox(
    connection: Connection,
    *,
    event_kind: NotificationEventKind,
    source_event_id: str,
    acceptance_id: str,
    channel: str,
    payload_contract_version: str,
    payload: Mapping[str, object],
    now: datetime,
) -> str:
    payload_json = canonical_json(dict(payload))
    payload_hash = canonical_sha256(dict(payload))
    event_id = _outbox_identity(
        source_event_id=source_event_id,
        channel=channel,
        payload_contract_version=payload_contract_version,
        payload_sha256=payload_hash,
    )
    existing = connection.execute(
        select(notification_outbox_v2).where(
            notification_outbox_v2.c.source_event_id == source_event_id,
            notification_outbox_v2.c.channel == channel,
            notification_outbox_v2.c.payload_contract_version == payload_contract_version,
        )
    ).mappings().first()
    if existing is not None:
        if (
            existing["outbox_event_id"] != event_id
            or existing["payload_json"] != payload_json
            or existing["acceptance_id"] != acceptance_id
            or existing["event_kind"] != event_kind.value
        ):
            raise PersistenceV2IntegrityError("outbox_semantic_identity_conflict")
        return str(existing["outbox_event_id"])
    connection.execute(
        insert(notification_outbox_v2).values(
            outbox_event_id=event_id,
            event_kind=event_kind.value,
            source_event_id=source_event_id,
            acceptance_id=acceptance_id,
            channel=channel,
            payload_contract_version=payload_contract_version,
            payload_json=payload_json,
            payload_sha256=payload_hash,
            status="pending",
            attempt_count=0,
            next_attempt_at_utc=now,
            last_error_code=None,
            sent_at_utc=None,
            created_at_utc=now,
        )
    )
    return event_id


class CanonicalAssessmentPersistenceV2:
    def __init__(self, engine: Engine, *, allow_local_ephemeral: bool = False) -> None:
        require_local_ephemeral_engine(engine, explicitly_enabled=allow_local_ephemeral)
        self.engine = engine

    def apply(
        self,
        result: TrustedFinalizationResult,
        *,
        warning_observations: Sequence[CanonicalWarningObservationV1] = (),
        daily_notification: DailySummaryNotificationV1 | None = None,
        material_notification: MaterialTransitionNotificationV1 | None = None,
        accepted_at: datetime | None = None,
        failure_injection: str | None = None,
    ) -> PersistenceApplicationResult:
        if not isinstance(result, TrustedFinalizationResult):
            return PersistenceApplicationResult(
                eligibility=PersistenceEligibility.REJECTED_INVALID_RECEIPT,
                acceptance_id=None,
                receipt_hash=None,
                history_inserted=False,
                current_advanced=False,
                warning_transition_ids=(),
                outbox_event_ids=(),
                denial_reason="trusted_finalization_result_type_required",
            )
        candidate_id = acceptance_id_for(result)
        payload = accepted_payload_dict(result)
        allowed_refs = _allowed_evidence_refs(payload)
        for observation in warning_observations:
            if not isinstance(observation, CanonicalWarningObservationV1):
                raise PersistenceV2IntegrityError("trusted_warning_observation_type_required")
            if not set(observation.evidence_refs).issubset(allowed_refs):
                raise PersistenceV2IntegrityError("warning_evidence_outside_accepted_payload")

        now = normalize_utc(accepted_at or _now(), field="accepted_at")
        connection = self.engine.connect()
        try:
            connection.exec_driver_sql("BEGIN IMMEDIATE")
            existing_row = connection.execute(
                select(canonical_acceptance_receipt_v1).where(
                    canonical_acceptance_receipt_v1.c.acceptance_id == candidate_id
                )
            ).mappings().first()
            existing_receipt = receipt_from_row(existing_row) if existing_row is not None else None
            receipt = issue_canonical_acceptance_receipt(
                result,
                accepted_at=now,
                existing_receipt=existing_receipt,
            )
            verification = verify_canonical_acceptance_receipt(
                receipt,
                trusted_result=result,
                accepted_payload=payload,
            )
            if not verification.valid:
                connection.rollback()
                return PersistenceApplicationResult(
                    eligibility=verification.eligibility,
                    acceptance_id=receipt.acceptance_id,
                    receipt_hash=receipt.receipt_hash,
                    history_inserted=False,
                    current_advanced=False,
                    warning_transition_ids=(),
                    outbox_event_ids=(),
                    denial_reason=";".join(verification.errors),
                )

            slot = connection.execute(
                select(canonical_acceptance_receipt_v1.c.acceptance_id).where(
                    canonical_acceptance_receipt_v1.c.trusted_issuer_id
                    == receipt.trusted_issuer_id,
                    canonical_acceptance_receipt_v1.c.generation_id == receipt.generation_id,
                    canonical_acceptance_receipt_v1.c.ticker == receipt.ticker,
                )
            ).scalar_one_or_none()
            if slot is not None and slot != receipt.acceptance_id:
                raise PersistenceV2IntegrityError("generation_ticker_receipt_conflict")

            expected_history = accepted_assessment_row(result, receipt)
            existing_history = connection.execute(
                select(accepted_assessment_v2).where(
                    accepted_assessment_v2.c.acceptance_id == receipt.acceptance_id
                )
            ).mappings().first()
            if existing_history is not None:
                self._verify_existing_history(existing_history, expected_history)
                connection.commit()
                return PersistenceApplicationResult(
                    eligibility=PersistenceEligibility.IDEMPOTENT_ALREADY_APPLIED,
                    acceptance_id=receipt.acceptance_id,
                    receipt_hash=receipt.receipt_hash,
                    history_inserted=False,
                    current_advanced=False,
                    warning_transition_ids=(),
                    outbox_event_ids=(),
                )

            if existing_receipt is None:
                connection.execute(insert(canonical_acceptance_receipt_v1).values(**_receipt_row(receipt)))
            if failure_injection == "history_insert":
                raise PersistenceV2Error("injected_history_insert_failure")
            connection.execute(insert(accepted_assessment_v2).values(**expected_history))
            history_inserted = True

            current_advanced = self._advance_current_state(
                connection,
                result=result,
                receipt=receipt,
                now=now,
            )
            if failure_injection == "current_state_cas":
                raise PersistenceV2Error("injected_current_state_cas_failure")
            if not current_advanced:
                connection.commit()
                return PersistenceApplicationResult(
                    eligibility=PersistenceEligibility.REJECTED_STALE,
                    acceptance_id=receipt.acceptance_id,
                    receipt_hash=receipt.receipt_hash,
                    history_inserted=history_inserted,
                    current_advanced=False,
                    warning_transition_ids=(),
                    outbox_event_ids=(),
                    denial_reason="accepted_assessment_total_order_stale",
                )

            transition_ids = self._apply_warning_observations(
                connection,
                result=result,
                receipt=receipt,
                observations=warning_observations,
                now=now,
            )
            if failure_injection == "warning_transition":
                raise PersistenceV2Error("injected_warning_transition_failure")

            outbox_ids: list[str] = []
            if daily_notification is not None:
                source_id = canonical_sha256(
                    {
                        "domain": "daily-summary-source-event-v2",
                        "schedule_run_id": daily_notification.schedule_run_id,
                        "ticker": result.ticker,
                        "acceptance_id": receipt.acceptance_id,
                        "channel": daily_notification.channel,
                        "payload_contract_version": (
                            daily_notification.payload_contract_version
                        ),
                    }
                )
                outbox_ids.append(
                    _insert_outbox(
                        connection,
                        event_kind=NotificationEventKind.DAILY_SUMMARY_NOTIFICATION,
                        source_event_id=source_id,
                        acceptance_id=receipt.acceptance_id,
                        channel=daily_notification.channel,
                        payload_contract_version=daily_notification.payload_contract_version,
                        payload=daily_notification.payload,
                        now=now,
                    )
                )
            if material_notification is not None:
                for transition_id in transition_ids:
                    outbox_ids.append(
                        _insert_outbox(
                            connection,
                            event_kind=(
                                NotificationEventKind.MATERIAL_STATE_TRANSITION_NOTIFICATION
                            ),
                            source_event_id=transition_id,
                            acceptance_id=receipt.acceptance_id,
                            channel=material_notification.channel,
                            payload_contract_version=(
                                material_notification.payload_contract_version
                            ),
                            payload={
                                **material_notification.payload,
                                "warning_transition_id": transition_id,
                            },
                            now=now,
                        )
                    )
            if failure_injection == "outbox_insert":
                raise PersistenceV2Error("injected_outbox_insert_failure")
            connection.commit()
            if failure_injection == "after_commit_before_send":
                raise PersistenceV2Error("injected_after_commit_before_send_failure")
            return PersistenceApplicationResult(
                eligibility=PersistenceEligibility.ELIGIBLE_CANONICAL,
                acceptance_id=receipt.acceptance_id,
                receipt_hash=receipt.receipt_hash,
                history_inserted=True,
                current_advanced=True,
                warning_transition_ids=tuple(transition_ids),
                outbox_event_ids=tuple(outbox_ids),
            )
        except Exception:
            if connection.in_transaction():
                connection.rollback()
            raise
        finally:
            connection.close()

    @staticmethod
    def _verify_existing_history(
        existing: Mapping[str, object],
        expected: Mapping[str, object],
    ) -> None:
        for key, expected_value in expected.items():
            actual = existing[key]
            if isinstance(expected_value, datetime):
                if _utc(actual) != _utc(expected_value):
                    raise PersistenceV2IntegrityError(f"immutable_history_conflict:{key}")
            elif isinstance(expected_value, Decimal):
                if Decimal(str(actual)) != expected_value:
                    raise PersistenceV2IntegrityError(f"immutable_history_conflict:{key}")
            elif actual != expected_value:
                raise PersistenceV2IntegrityError(f"immutable_history_conflict:{key}")
        validate_extract_consistency(existing)

    @staticmethod
    def _advance_current_state(
        connection: Connection,
        *,
        result: TrustedFinalizationResult,
        receipt: CanonicalAcceptanceReceiptV1,
        now: datetime,
    ) -> bool:
        incoming = total_ordering_key(
            effective_at=result.effective_at,
            generation_generated_at=result.generation_generated_at,
            generation_id=result.generation_id,
            acceptance_id=receipt.acceptance_id,
        )
        values = {
            "latest_acceptance_id": receipt.acceptance_id,
            "latest_effective_at_utc": incoming[0],
            "latest_generation_generated_at_utc": incoming[1],
            "latest_generation_id": incoming[2],
            "latest_ordering_acceptance_id": incoming[3],
            "latest_assessment_date": result.assessment_date,
            "latest_thesis_version": result.thesis_version,
            "updated_at_utc": now,
        }
        for _attempt in range(CURRENT_STATE_CAS_MAX_ATTEMPTS):
            current = connection.execute(
                select(monitoring_current_state_v2).where(
                    monitoring_current_state_v2.c.ticker == result.ticker
                )
            ).mappings().first()
            if current is None:
                try:
                    connection.execute(
                        insert(monitoring_current_state_v2).values(
                            ticker=result.ticker,
                            row_version=1,
                            **values,
                        )
                    )
                    return True
                except IntegrityError:
                    continue

            current_key = total_ordering_key(
                effective_at=_utc(current["latest_effective_at_utc"]),
                generation_generated_at=_utc(
                    current["latest_generation_generated_at_utc"]
                ),
                generation_id=str(current["latest_generation_id"]),
                acceptance_id=str(current["latest_ordering_acceptance_id"]),
            )
            if incoming <= current_key:
                return False
            row_version = int(current["row_version"])
            changed = connection.execute(
                update(monitoring_current_state_v2)
                .where(
                    monitoring_current_state_v2.c.ticker == result.ticker,
                    monitoring_current_state_v2.c.row_version == row_version,
                    monitoring_current_state_v2.c.latest_acceptance_id
                    == current["latest_acceptance_id"],
                    monitoring_current_state_v2.c.latest_effective_at_utc
                    == current["latest_effective_at_utc"],
                    monitoring_current_state_v2.c.latest_generation_generated_at_utc
                    == current["latest_generation_generated_at_utc"],
                    monitoring_current_state_v2.c.latest_generation_id
                    == current["latest_generation_id"],
                    monitoring_current_state_v2.c.latest_ordering_acceptance_id
                    == current["latest_ordering_acceptance_id"],
                )
                .values(row_version=row_version + 1, **values)
            ).rowcount
            if changed == 1:
                return True
        raise PersistenceV2IntegrityError("current_state_cas_retry_exhausted")

    @staticmethod
    def _apply_warning_observations(
        connection: Connection,
        *,
        result: TrustedFinalizationResult,
        receipt: CanonicalAcceptanceReceiptV1,
        observations: Sequence[CanonicalWarningObservationV1],
        now: datetime,
    ) -> list[str]:
        key = total_ordering_key(
            effective_at=result.effective_at,
            generation_generated_at=result.generation_generated_at,
            generation_id=result.generation_id,
            acceptance_id=receipt.acceptance_id,
        )
        key_json = ordering_key_json(key)
        transitions: list[str] = []
        for observation in observations:
            identity = warning_identity(
                ticker=result.ticker,
                thesis_version=result.thesis_version,
                observation=observation,
            )
            state = connection.execute(
                select(warning_state_v2).where(
                    warning_state_v2.c.warning_identity == identity
                )
            ).mappings().first()
            if state is not None:
                state_key_payload = _json_value(str(state["latest_ordering_key_json"]))
                state_key = (
                    datetime.fromisoformat(
                        str(state_key_payload["effective_at_utc"]).replace("Z", "+00:00")
                    ),
                    datetime.fromisoformat(
                        str(state_key_payload["generation_generated_at_utc"]).replace(
                            "Z", "+00:00"
                        )
                    ),
                    str(state_key_payload["generation_id"]),
                    str(state_key_payload["acceptance_id"]),
                )
                if key <= state_key:
                    continue
            current_name = str(state["state"]) if state is not None else None
            current_episode = int(state["episode"]) if state is not None else 0
            next_name, episode, material = _next_warning_state(
                current_name,
                observation.observation,
                current_episode,
            )
            if next_name is None:
                continue
            state_values = {
                "ticker": result.ticker,
                "thesis_version": result.thesis_version,
                "warning_type": observation.warning_type,
                "condition_contract_version": observation.condition_contract_version,
                "condition_identity": observation.condition_identity,
                "state": next_name,
                "episode": episode,
                "latest_observation_acceptance_id": receipt.acceptance_id,
                "latest_ordering_key_json": key_json,
            }
            if state is None:
                connection.execute(
                    insert(warning_state_v2).values(
                        warning_identity=identity,
                        latest_transition_id=None,
                        row_version=1,
                        **state_values,
                    )
                )
                row_version = 1
            else:
                row_version = int(state["row_version"])
                changed = connection.execute(
                    update(warning_state_v2)
                    .where(
                        warning_state_v2.c.warning_identity == identity,
                        warning_state_v2.c.row_version == row_version,
                    )
                    .values(row_version=row_version + 1, **state_values)
                ).rowcount
                if changed != 1:
                    raise PersistenceV2IntegrityError("warning_state_cas_conflict")
                row_version += 1
            if not material:
                continue
            transition_id = warning_transition_id(
                identity=identity,
                episode=episode,
                from_state=current_name,
                to_state=next_name,
                acceptance_id=receipt.acceptance_id,
                transition_reason_version=observation.transition_reason_version,
            )
            connection.execute(
                insert(warning_transition_v2).values(
                    warning_transition_id=transition_id,
                    warning_identity=identity,
                    episode=episode,
                    from_state=current_name,
                    to_state=next_name,
                    triggering_acceptance_id=receipt.acceptance_id,
                    observation_json=canonical_json(observation.model_dump(mode="json")),
                    transition_reason_version=observation.transition_reason_version,
                    created_at_utc=now,
                )
            )
            connection.execute(
                update(warning_state_v2)
                .where(
                    warning_state_v2.c.warning_identity == identity,
                    warning_state_v2.c.row_version == row_version,
                )
                .values(latest_transition_id=transition_id)
            )
            transitions.append(transition_id)
        return transitions


class FakeOutboxSender:
    def __init__(self, *, fail: bool = False) -> None:
        self.fail = fail
        self.sent_event_ids: list[str] = []

    def __call__(self, event: Mapping[str, object]) -> None:
        if self.fail:
            raise RuntimeError("fake_sender_failure")
        self.sent_event_ids.append(str(event["outbox_event_id"]))


def dispatch_pending_outbox(
    engine: Engine,
    sender: FakeOutboxSender,
    *,
    allow_local_ephemeral: bool = False,
    max_attempts: int = 3,
    now: datetime | None = None,
) -> dict[str, int]:
    require_local_ephemeral_engine(engine, explicitly_enabled=allow_local_ephemeral)
    if not isinstance(sender, FakeOutboxSender):
        raise PersistenceV2LocalGateError("fake_sender_instance_required")
    at = normalize_utc(now or _now(), field="outbox_dispatch_time")
    with engine.begin() as connection:
        rows = connection.execute(
            select(notification_outbox_v2).where(
                notification_outbox_v2.c.status.in_(("pending", "retry")),
                notification_outbox_v2.c.next_attempt_at_utc <= at,
            )
        ).mappings().all()
    sent = retried = dead = 0
    for row in rows:
        event_id = str(row["outbox_event_id"])
        try:
            sender(dict(row))
        except Exception:
            attempts = int(row["attempt_count"]) + 1
            status = "dead_letter" if attempts >= max_attempts else "retry"
            with engine.begin() as connection:
                connection.execute(
                    update(notification_outbox_v2)
                    .where(notification_outbox_v2.c.outbox_event_id == event_id)
                    .values(
                        status=status,
                        attempt_count=attempts,
                        next_attempt_at_utc=at + timedelta(minutes=min(attempts, 5)),
                        last_error_code="FAKE_SEND_FAILURE",
                    )
                )
            dead += int(status == "dead_letter")
            retried += int(status == "retry")
            continue
        with engine.begin() as connection:
            connection.execute(
                update(notification_outbox_v2)
                .where(notification_outbox_v2.c.outbox_event_id == event_id)
                .values(
                    status="sent",
                    attempt_count=int(row["attempt_count"]) + 1,
                    sent_at_utc=at,
                    last_error_code=None,
                )
            )
        sent += 1
    return {"sent": sent, "retry": retried, "dead_letter": dead}
