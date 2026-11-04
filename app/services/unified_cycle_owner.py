"""Pinned backend cycle provenance, separate from completed exchange prices.

The freeze pin is an independently owned backend input, never a model/caller
claim. A JSON hash cannot prove a historical write or scheduled execution.
Only a live handle loaded by that backend may amend the legacy cycle denial.
No production writer, schedule or stored row is changed by this module.
"""

from __future__ import annotations

from copy import deepcopy
from datetime import date, datetime
import hashlib
import json
from importlib.metadata import version
from pathlib import Path
from typing import Literal
from weakref import WeakKeyDictionary

from pydantic import AwareDatetime, BaseModel, ConfigDict, Field

from app.services.market_session import NEW_YORK, SEOUL, _exchange_calendar
from app.services.unified_snapshot_contract import digest

LEGACY_DENIAL = "first_eligible_cycle_to_session_authority_required"
CONTRACT = "class-c-cycle-run-session-owner-v1"
_ROOT = Path(__file__).resolve().parents[2]
_MODULES = (
    "app/services/onboarding_reconciler_service.py",
    "app/services/onboarding_readiness_service.py",
    "app/services/unified_runtime_v2.py",
    "app/services/unified_market_run.py",
    "app/services/market_session.py",
)
_TABLES = {"watchlistitem", "securitymaster", "investmentthesis", "company"}


def policy_fingerprints():
    return {p: hashlib.sha256((_ROOT / p).read_bytes()).hexdigest() for p in _MODULES}


class Strict(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)


class CycleEvent(Strict):
    ticker: str = Field(min_length=1)
    security_id: str = Field(min_length=1)
    thesis_version: int = Field(ge=1)
    record_hashes: dict[str, str]
    original_cycle: date
    mode: Literal["RECONCILER_DEFAULT", "RECONCILER_EXPLICIT_OVERRIDE"]
    writer_at: AwareDatetime
    explicit_override: date | None = None
    original_writer_event_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")


class CycleFreeze(Strict):
    contract: Literal["class-c-cycle-run-session-owner-v1"] = CONTRACT
    generation_id: str = Field(min_length=1)
    source_generation_id: str = Field(min_length=1)
    source_export_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    source_projection_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    identity_policy_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    calendar_version: str = Field(min_length=1)
    target_session: date
    source_cutoff: AwareDatetime
    market: Literal["kr", "us"]
    cutoff: AwareDatetime
    scheduled_at: AwareDatetime
    scheduled_run_event_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    policy_fingerprints: dict[str, str]
    events: tuple[CycleEvent, ...]


class CycleOwner:
    """Opaque process-local capability. Public JSON cannot recreate this handle."""

    __slots__ = ("__weakref__",)


_OWNERS: WeakKeyDictionary = WeakKeyDictionary()


def load_pinned_cycle_owner(
    raw: bytes,
    *,
    expected_sha256: str,
    source_rows: bytes,
    source_generation_id: str,
    execution_generation_id: str,
    policy,
) -> CycleOwner:
    """Called only with a trusted freeze pin for original write AND run events.

    The backend must establish event custody independently before calling this
    function. It does not discover historical authority from current SQL rows.
    Synthetic test freezes remain synthetic; no operating producer is enabled.
    """
    if hashlib.sha256(raw).hexdigest() != expected_sha256:
        raise ValueError("cycle_independent_freeze_pin_mismatch")
    freeze = CycleFreeze.model_validate_json(raw)
    if (freeze.source_generation_id, freeze.generation_id) != (
        source_generation_id,
        execution_generation_id,
    ):
        raise ValueError("cycle_source_or_execution_generation_mismatch")
    if hashlib.sha256(source_rows).hexdigest() != freeze.source_export_sha256:
        raise ValueError("cycle_original_export_digest_mismatch")
    if freeze.calendar_version != version("exchange-calendars"):
        raise ValueError("cycle_calendar_version_mismatch")
    if freeze.identity_policy_sha256 != digest(sorted(policy.allowed_providers)):
        raise ValueError("cycle_identity_policy_mismatch")
    if freeze.policy_fingerprints != policy_fingerprints():
        raise ValueError("cycle_writer_or_selector_version_unproven")
    if freeze.source_cutoff != freeze.cutoff:
        raise ValueError("cycle_source_asof_mismatch")
    from app.services.minimal_class_c_export import project_authorized_rows

    projection = project_authorized_rows(
        json.loads(source_rows),
        market=freeze.market,
        session_key=freeze.target_session.isoformat(),
        cutoff=freeze.source_cutoff,
        policy=policy,
    )
    if digest(projection) != freeze.source_projection_sha256:
        raise ValueError("cycle_authenticated_projection_mismatch")
    if len({e.ticker for e in freeze.events}) != len(freeze.events):
        raise ValueError("cycle_duplicate_subject_event")
    for event in freeze.events:
        if set(event.record_hashes) != _TABLES or any(
            len(v) != 64 or any(c not in "0123456789abcdef" for c in v)
            for v in event.record_hashes.values()
        ):
            raise ValueError("cycle_four_original_record_bindings_required")
        if event.writer_at > freeze.source_cutoff:
            raise ValueError("cycle_writer_after_source_cutoff")
        from app.services.onboarding_reconciler_service import _next_cycle_date

        if event.mode == "RECONCILER_DEFAULT":
            if event.explicit_override is not None or event.original_cycle != _next_cycle_date(
                freeze.market, event.writer_at
            ):
                raise ValueError("cycle_default_writer_mismatch")
        elif event.explicit_override != event.original_cycle:
            raise ValueError("cycle_explicit_override_unproven")
    handle = CycleOwner()
    # Keep immutable serialized bytes, not references to caller dictionaries.
    _OWNERS[handle] = (freeze.model_dump_json(), expected_sha256, json.dumps(projection))
    return handle


def _state(owner):
    if type(owner) is not CycleOwner or owner not in _OWNERS:
        raise ValueError("cycle_live_backend_owner_required")
    frozen, pin, projection = _OWNERS[owner]
    value = CycleFreeze.model_validate_json(frozen)
    if value.policy_fingerprints != policy_fingerprints():
        raise ValueError("cycle_policy_changed_since_issuance")
    if value.calendar_version != version("exchange-calendars"):
        raise ValueError("cycle_calendar_changed_since_issuance")
    return value, pin, json.loads(projection)


def require_generation(owner, generation_id):
    freeze, _, _ = _state(owner)
    if freeze.generation_id != generation_id:
        raise ValueError("cycle_execution_generation_mismatch")


def revoke_cycle_owner(owner):
    _state(owner)
    del _OWNERS[owner]


def _clock(freeze, target):
    from app.services.unified_runtime_v2 import scheduled_slots
    from app.services.unified_market_run import target_session

    local = freeze.scheduled_at.astimezone(SEOUL)
    if freeze.scheduled_at not in scheduled_slots(freeze.market, local.date()):
        raise ValueError("cycle_scheduled_slot_not_owned")
    if freeze.scheduled_at > freeze.cutoff:
        raise ValueError("cycle_scheduled_after_cutoff")
    name = "XNYS" if freeze.market == "us" else "XKRX"
    zone = NEW_YORK if freeze.market == "us" else SEOUL
    try:
        cal = _exchange_calendar(name)
        selected = cal.date_to_session(freeze.cutoff.astimezone(zone).date(), direction="previous")
        if cal.session_close(selected).to_pydatetime() > freeze.cutoff:
            selected = cal.previous_session(selected)
        if (
            selected.date() != target
            or target_session(freeze.market, freeze.scheduled_at) != target
        ):
            raise ValueError("cycle_completed_session_mismatch")
        prior = cal.previous_session(selected)
        return dict(
            calendar=name,
            calendar_version=version("exchange-calendars"),
            target=target.isoformat(),
            prior=prior.date().isoformat(),
            completed_close=cal.session_close(selected).to_pydatetime().isoformat(),
            prior_close=cal.session_close(prior).to_pydatetime().isoformat(),
        )
    except (ValueError, IndexError, TypeError) as exc:
        raise ValueError("cycle_exchange_calendar_or_scheduled_run_unproven") from exc


def apply_cycle_owner(document: dict, *, original: dict, owner: CycleOwner) -> dict:
    """Amend only the cycle denial; all other original owner gates stay intact.

    Replay authenticates full-row hashes from the pinned original projection
    and compares fresh selection semantics. It does not re-create omitted
    Watchlist fields or pretend their ORM defaults were original source data.
    """
    freeze, pin, authenticated = _state(owner)
    if any(
        original.get(k) != authenticated.get(k)
        for k in ("universe", "owner_fingerprints", "market", "cutoff", "session")
    ):
        raise ValueError("cycle_authenticated_selection_mismatch")
    if set(original["roles"]) != set(authenticated["roles"]) or any(
        original["roles"][k]["records"] != authenticated["roles"][k]["records"]
        for k in authenticated["roles"]
    ):
        raise ValueError("cycle_authenticated_original_records_mismatch")
    if (document["market"], datetime.fromisoformat(document["cutoff"])) != (
        freeze.market,
        freeze.cutoff,
    ):
        raise ValueError("cycle_market_cutoff_mismatch")
    if (original["market"], original["cutoff"], original["session"]) != (
        document["market"],
        document["cutoff"],
        document["session"],
    ):
        raise ValueError("cycle_original_projection_mismatch")
    clock = _clock(freeze, date.fromisoformat(document["session"]))
    by_subject = {}
    for role, component in original["roles"].items():
        if component["version"] != digest(component["records"]):
            raise ValueError("cycle_original_role_digest_mismatch")
        current = document["roles"][role]["records"]

        def semantic(records):
            return [{k: r[k] for k in ("table", "record_id", "record")} for r in records]

        if semantic(current) != semantic(component["records"]):
            raise ValueError("cycle_replayed_selection_changed")
        for record in component["records"]:
            table = record["table"]
            subject = by_subject.setdefault(record["record"]["ticker"], {})
            if table in subject:
                raise ValueError("cycle_duplicate_original_record")
            subject[table] = record
    events = {e.ticker: e for e in freeze.events}
    approved, denied = [], []
    for ticker in document["universe"]["eligible_subjects"]:
        rows, event = by_subject.get(ticker, {}), events.get(ticker)
        reason = None
        if event is None:
            reason = "cycle_original_writer_provenance_missing"
        elif set(rows) != _TABLES or any(
            rows[t]["original_record_sha256"] != event.record_hashes[t] for t in _TABLES
        ):
            reason = "cycle_original_record_binding_mismatch"
        else:
            watch, security, thesis = [
                rows[t]["record"] for t in ("watchlistitem", "securitymaster", "investmentthesis")
            ]
            if (
                security["canonical_security_id"],
                thesis["version"],
                watch["first_eligible_session"],
            ) != (event.security_id, event.thesis_version, event.original_cycle.isoformat()):
                reason = "cycle_security_thesis_or_original_date_mismatch"
            elif not all(
                watch.get(k) is True
                for k in ("active", "monitoring_requested", "production_eligible")
            ):
                reason = "cycle_subject_not_active"
            elif watch["onboarding_state"] != "ACTIVE" or thesis["status"] != "active":
                reason = "cycle_owner_role_lost"
            elif not watch["activated_at"]:
                reason = "cycle_activation_authority_missing"
            else:
                from datetime import timezone

                activation = datetime.fromisoformat(watch["activated_at"])
                if activation.tzinfo is None:
                    activation = activation.replace(tzinfo=timezone.utc)
                if activation > freeze.cutoff:
                    reason = "cycle_activation_after_cutoff"
                elif event.original_cycle > freeze.cutoff.astimezone(SEOUL).date():
                    reason = "cycle_not_reached_at_run_cutoff"
        if reason:
            denied.append(dict(role="universe", ticker=ticker, reason=reason))
        else:
            approved.append(ticker)
    result = deepcopy(document)
    # A caller cannot erase another owner's denial while amending the cycle.
    result["denials"] = []
    for denial in [*authenticated["denials"], *document["denials"]]:
        if denial["reason"] == LEGACY_DENIAL and denial["ticker"] in approved:
            continue
        if denial not in result["denials"]:
            result["denials"].append(deepcopy(denial))
    result["denials"].extend(denied)
    for role in result["roles"]:
        if role != "universe":
            result["roles"][role]["eligible"] = (
                authenticated["roles"][role]["eligible"]
                and document["roles"][role]["eligible"]
                and not any(d["role"] == role for d in result["denials"])
            )
    result["roles"]["universe"]["eligible"] = bool(approved) and not any(
        d["role"] == "universe" for d in result["denials"]
    )
    result["cycle_owner_receipt"] = dict(
        contract=CONTRACT,
        freeze_sha256=pin,
        source_export_sha256=freeze.source_export_sha256,
        source_generation_id=freeze.source_generation_id,
        generation_id=freeze.generation_id,
        scheduled_run_event_sha256=freeze.scheduled_run_event_sha256,
        scheduled_at=freeze.scheduled_at.isoformat(),
        membership_as_of="FROZEN_RUN_CUTOFF",
        calendar=clock,
        approved=approved,
        denied=denied,
        scope="RUN_MEMBERSHIP_ONLY_NOT_D01_D02",
    )
    return result
