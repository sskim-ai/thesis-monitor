"""One foreground cycle; only incomplete collection can enter another source attempt."""

from __future__ import annotations

import asyncio
from dataclasses import dataclass
from datetime import date, datetime, time, timedelta
import fcntl
import json
from pathlib import Path
import traceback
from typing import Protocol
from zoneinfo import ZoneInfo

from app.services.market_session import _exchange_calendar
from app.services.unified_run_artifacts import (
    copy_verified, durable_json, load_json, sanitized, seal_failure_bundle, sha256_bytes,
)
from app.services.unified_snapshot_contract import (
    CONTRACT, STAGES, Collection, SnapshotPolicy, StageResult, digest, encoded,
    validate_collection, validate_delivery, validate_render, validate_stage,
)


KST = ZoneInfo("Asia/Seoul")
NY = ZoneInfo("America/New_York")
TIMES = {"us": (time(8, 10), time(8, 15), time(8, 20)),
         "kr": (time(16), time(16, 5), time(16, 10))}


def scheduled_slots(market: str, day: date) -> tuple[datetime, ...]:
    return tuple(datetime.combine(day, t, KST) for t in TIMES[market])


def target_session(market: str, scheduled: datetime) -> date | None:
    """No weekday fallback and no repeated old session on the next closed day."""
    calendar = _exchange_calendar("XNYS" if market == "us" else "XKRX")
    day = scheduled.astimezone(NY if market == "us" else KST).date()
    if not calendar.is_session(day):
        return None
    session = calendar.date_to_session(day)
    close = calendar.session_close(session).to_pydatetime()
    return day if close <= scheduled else None


class Clock:
    def now(self) -> datetime:
        return datetime.now(KST)

    async def until(self, when: datetime) -> None:
        while self.now() < when:
            await asyncio.sleep(min(60, (when - self.now()).total_seconds()))


class PipelinePorts(Protocol):
    """Adapters retain existing source/AI/renderer validators, not new policy."""

    async def policy(self, market: str, session: date, run_id: str) -> SnapshotPolicy: ...
    async def collect(self, request: dict, directory: Path) -> Collection: ...
    async def stage(self, request: dict, directory: Path) -> StageResult: ...
    async def notify_failure(self, payload: dict) -> dict: ...


@dataclass(frozen=True)
class RunConfiguration:
    root: Path
    debug_destination: Path | None
    repo_commit: str
    scheduler_identity: str
    adapter_fingerprint: str
    stage_timeout_seconds: int = 1200
    collection_timeout_seconds: int = 1200
    notification_timeout_seconds: int = 30
    secrets: tuple[str, ...] = ()

    def public(self) -> dict:
        return {"contract": CONTRACT, "repo_commit": self.repo_commit,
                "scheduler_identity": self.scheduler_identity,
                "adapter_fingerprint": self.adapter_fingerprint,
                "stage_timeout_seconds": self.stage_timeout_seconds,
                "collection_timeout_seconds": self.collection_timeout_seconds,
                "notification_timeout_seconds": self.notification_timeout_seconds,
                "debug_destination_configured": self.debug_destination is not None,
                "model_attempts_per_role": 1, "external_reference_calls_allowed": 0}


class UnifiedMarketRun:
    def __init__(self, config: RunConfiguration, ports: PipelinePorts, *, clock: Clock | None = None):
        self.config, self.ports, self.clock = config, ports, clock or Clock()
        if min(config.stage_timeout_seconds, config.collection_timeout_seconds,
               config.notification_timeout_seconds) <= 0:
            raise ValueError("positive_timeout_required")

    async def run(self, market: str, day: date) -> dict:
        slots = scheduled_slots(market, day)
        # Durable cycle identity prevents retries, process restarts and duplicate schedulers
        # from generating a second normal delivery for the same market/date.
        run_id = f"snapshot-{market}-{day.isoformat()}"
        directory = self.config.root / run_id
        directory.mkdir(parents=True, exist_ok=True, mode=0o700)
        with (directory / "cycle.lock").open("a") as lock:
            try:
                fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
            except BlockingIOError:
                return {"run_id": run_id, "status": "ALREADY_RUNNING", "normal_messages_sent": False}
            if (directory / "terminal.json").exists():
                return load_json(directory / "terminal.json")
            state = {"run_id": run_id, "market": market, "scheduled_at": slots[0].isoformat(),
                     "status": "STARTED", "stage": "PREFLIGHT", "transitions": [], "attempts": [],
                     "stage_receipts": [], "snapshot_sha256": None, "normal_messages_sent": False,
                     "configuration": self.config.public(), "error_chain": [],
                     "configuration_sha256": digest(self.config.public())}
            if (directory / "state.json").exists():
                state = load_json(directory / "state.json")
                state["recovery"] = "INTERRUPTED_CYCLE_NO_AUTOMATIC_REPLAY"
                return await self._fail(directory, state, "interrupted_cycle_requires_review")

            def transition(stage: str) -> None:
                state["stage"] = stage
                state["transitions"].append({"stage": stage, "at": self.clock.now().isoformat()})
                durable_json(directory / "state.json", state)

            transition("SESSION_GATE")
            try:
                session = target_session(market, slots[0])
                if session is None:
                    transition("MARKET_CLOSED_SKIP")
                    state.update(status="SKIPPED", reason="NO_ELIGIBLE_EXCHANGE_SESSION")
                    durable_json(directory / "terminal.json", state, exclusive=True)
                    return state
                state["target_session"] = session.isoformat()
                transition("PREFLIGHT")
                if self.config.debug_destination is None or not self.config.debug_destination.is_dir():
                    raise ValueError("configured_debug_destination_unavailable")
                policy = await asyncio.wait_for(self.ports.policy(market, session, run_id),
                                                self.config.collection_timeout_seconds)
                if policy.market != market:
                    raise ValueError("policy_market_mismatch")
                policy_value = policy.model_dump(mode="json")
                durable_json(directory / "policy.json", policy_value, exclusive=True)
                policy_hash = digest(policy_value)
                frozen = None
                for index, slot in enumerate(slots):
                    end = slots[index + 1] if index + 1 < len(slots) else slot + timedelta(minutes=5)
                    # Missed windows are recorded, never replayed in a burst. An attempt
                    # started within its window may finish later under its own timeout.
                    if self.clock.now() >= end:
                        state["attempts"].append({"slot": slot.isoformat(), "status": "WINDOW_MISSED"})
                        transition("WINDOW_MISSED")
                        continue
                    transition("WAIT_INITIAL" if index == 0 else f"WAIT_RETRY_{index}")
                    await self.clock.until(slot)
                    if self.clock.now() >= end:
                        state["attempts"].append({"slot": slot.isoformat(), "status": "WINDOW_MISSED"})
                        transition("WINDOW_MISSED")
                        continue
                    attempt_id = f"{run_id}-attempt-{index + 1}"
                    attempt_dir = directory / attempt_id
                    attempt_dir.mkdir(mode=0o700)
                    started = self.clock.now()
                    request = {"contract": CONTRACT, "run_id": run_id, "attempt_id": attempt_id,
                               "market": market, "target_session": session.isoformat(),
                               "started_at": started.isoformat(), "policy": policy_value,
                               "policy_sha256": policy_hash, "finality_claim": "NOT_CLAIMED",
                               "semantics": "QUERY_TIME_SNAPSHOT"}
                    durable_json(attempt_dir / "request.json", request, exclusive=True)
                    transition("COLLECT_INITIAL" if index == 0 else f"COLLECT_RETRY_{index}")
                    receipt = {"attempt_id": attempt_id, "slot": slot.isoformat(),
                               "started_at": started.isoformat(), "status": "INCOMPLETE"}
                    # Persist intent before provider execution so cancellation is auditable.
                    state["attempts"].append(receipt)
                    durable_json(directory / "state.json", state)
                    try:
                        result = await asyncio.wait_for(self.ports.collect(request, attempt_dir),
                                                        self.config.collection_timeout_seconds)
                        errors = validate_collection(result, policy=policy, run_id=run_id,
                                                     attempt_id=attempt_id, started_at=started,
                                                     now=self.clock.now())
                        receipt.update(errors=errors, source_receipts=[r.model_dump(mode="json")
                                       for r in result.receipts], validators=[v.model_dump(mode="json")
                                       for v in result.validators], packet_sha256=digest(result.packet))
                        durable_json(attempt_dir / "collection.json", result.model_dump(mode="json"),
                                     exclusive=True)
                        if not errors:
                            receipt["status"] = "ELIGIBLE"
                            frozen = {"contract": CONTRACT, "run_id": run_id, "policy_sha256": policy_hash,
                                      "collection": result.model_dump(mode="json")}
                    except OSError:
                        raise
                    except Exception as exc:
                        receipt.update(errors=["collection_exception"], error_type=type(exc).__name__)
                        state["error_chain"].extend(self._error(exc))
                    receipt["completed_at"] = self.clock.now().isoformat()
                    durable_json(attempt_dir / "receipt.json", sanitized(receipt, self.config.secrets))
                    durable_json(directory / "state.json", state)
                    if frozen is not None:
                        break
                if frozen is None:
                    raise ValueError("no_complete_collection_within_bounded_windows")
                snapshot_path = directory / "snapshot.json"
                durable_json(snapshot_path, frozen, exclusive=True)
                state["snapshot_sha256"] = digest(frozen)
                transition("SNAPSHOT_READY")
                outputs = {}
                for stage in STAGES:
                    transition(stage)
                    if (digest(load_json(snapshot_path)) != state["snapshot_sha256"]
                            or digest(load_json(directory / "policy.json")) != policy_hash):
                        raise ValueError("frozen_snapshot_or_policy_changed")
                    request = {"contract": CONTRACT, "run_id": run_id, "stage": stage,
                               "snapshot_sha256": state["snapshot_sha256"], "snapshot": frozen,
                               "inputs": outputs, "configuration_sha256": state["configuration_sha256"]}
                    stage_dir = directory / stage.lower()
                    durable_json(stage_dir / "request.json", request, exclusive=True)
                    state["stage_receipts"].append({"stage": stage, "request_sha256": digest(request),
                                                    "status": "STARTED"})
                    if stage == "DELIVER":
                        # An interrupted HTTP send cannot be proven unsent. Never resend it.
                        state["normal_messages_sent"] = "UNKNOWN"
                    durable_json(directory / "state.json", state)
                    result = await asyncio.wait_for(
                        self.ports.stage(json.loads(encoded(request)), stage_dir),
                        self.config.stage_timeout_seconds)
                    durable_json(stage_dir / "response.json", result.model_dump(mode="json"), exclusive=True)
                    state["stage_receipts"][-1].update(response_sha256=digest(result.model_dump(mode="json")),
                                                       status=result.status, errors=result.errors)
                    validate_stage(result, request)
                    if stage == "RENDER":
                        validate_render(result.output, policy, state["snapshot_sha256"])
                    if stage == "DELIVER":
                        state["delivery_receipt"] = result.output
                        validate_delivery(result.output, policy)
                    if digest(load_json(snapshot_path)) != state["snapshot_sha256"]:
                        raise ValueError("snapshot_changed_during_stage")
                    outputs[stage] = result.model_dump(mode="json")
                    if stage == "DELIVER":
                        state["normal_messages_sent"] = result.output.get("normal_messages_sent", "UNKNOWN")
                        state["delivery_receipt"] = result.output
                transition("DONE")
                state["status"] = "SUCCESS"
                durable_json(directory / "terminal.json", sanitized(state, self.config.secrets), exclusive=True)
                return state
            except (Exception, asyncio.CancelledError) as exc:
                state["error_chain"].extend(self._error(exc))
                known_codes = {
                    "configured_debug_destination_unavailable", "policy_market_mismatch",
                    "no_complete_collection_within_bounded_windows", "frozen_snapshot_or_policy_changed",
                    "snapshot_changed_during_stage", "stage_snapshot_or_request_binding_mismatch",
                    "stage_validation_failed", "unsupported_finality_claim", "render_message_coverage_mismatch",
                    "empty_rendered_message", "render_snapshot_mismatch", "unsupported_finality_wording",
                    "delivery_receipt_incomplete_or_uncertain", "unified_production_adapter_not_qualified",
                }
                code = str(exc) if str(exc) in known_codes else type(exc).__name__
                return await self._fail(directory, state, code)

    @staticmethod
    def _error(exc: BaseException) -> list[dict]:
        # Exception strings and locals may contain provider URLs/credentials.
        rows, seen = [], set()
        while exc is not None and id(exc) not in seen:
            seen.add(id(exc))
            rows.append({"type": type(exc).__name__, "frames": [
                {"file": Path(f.filename).name, "function": f.name, "line": f.lineno}
                for f in traceback.extract_tb(exc.__traceback__)]})
            exc = exc.__cause__ or exc.__context__
        return rows

    async def _fail(self, directory: Path, state: dict, code: str) -> dict:
        state.update(status="FAILED", failed_stage=state["stage"], failure_code=code)
        state["transitions"].append({"stage": "FAILURE_FINALIZE", "at": self.clock.now().isoformat()})
        payload = {"kind": "MONITORING_OPERATIONAL_FAILURE", "market": state["market"],
                   "run_id": state["run_id"], "scheduled_at": state["scheduled_at"],
                   "failed_stage": state["failed_stage"], "failure_code": code,
                   "attempt_count": sum("attempt_id" in r for r in state["attempts"]),
                   "normal_messages_sent": state["normal_messages_sent"],
                   "debug_bundle_upload_status": "PENDING_LOCAL_COPY",
                   "debug_bundle": state["run_id"] + "-debug.zip"}
        state["failure_notification"] = {"status": "SEND_INTENT_RECORDED", "payload": payload}
        durable_json(directory / "state.json", sanitized(state, self.config.secrets))
        if not (directory / "failure-notification-intent.json").exists():
            durable_json(directory / "failure-notification-intent.json", payload, exclusive=True)
            try:
                result = await asyncio.wait_for(self.ports.notify_failure(payload),
                                                self.config.notification_timeout_seconds)
                state["failure_notification"].update(status="RETURNED", receipt=result)
            except Exception as exc:
                state["failure_notification"].update(status="FAILED", error_type=type(exc).__name__)
        else:
            state["failure_notification"]["status"] = "PRIOR_SEND_INTENT_NO_RESEND"
        durable_json(directory / "state.json", sanitized(state, self.config.secrets))
        try:
            bundle = directory / f"{state['run_id']}-debug.zip"
            if not bundle.exists():
                bundle = seal_failure_bundle(directory, state, secrets=self.config.secrets)
            expected = bundle.with_suffix(".zip.sha256").read_text().split()[0]
            if expected != sha256_bytes(bundle.read_bytes()):
                raise ValueError("sealed_debug_bundle_changed")
            if self.config.debug_destination is None:
                raise ValueError("configured_debug_destination_unavailable")
            state["debug_upload"] = copy_verified(bundle, self.config.debug_destination)
            copy_verified(bundle.with_suffix(".zip.sha256"), self.config.debug_destination)
        except Exception as exc:
            state["debug_upload"] = {"status": "FAILED", "error_type": type(exc).__name__}
        durable_json(directory / "upload-receipt.json", state["debug_upload"])
        durable_json(directory / "terminal.json", sanitized(state, self.config.secrets), exclusive=True)
        return state
