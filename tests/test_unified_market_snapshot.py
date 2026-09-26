from __future__ import annotations

import asyncio
from copy import deepcopy
from datetime import date, datetime, timedelta
import json
import zipfile

import pytest

from app.jobs.unified_market_snapshot import run_selected
from app.services import unified_market_run as runtime
from app.services.unified_run_artifacts import copy_verified, durable_bytes, sanitized
from app.services.unified_snapshot_contract import (
    STAGES, Collection, Role, SnapshotPolicy, SourceReceipt, StageResult, ValidatorReceipt,
    digest, validate_collection,
)


class FakeClock(runtime.Clock):
    def __init__(self, market="us", day=date(2026, 9, 23)):
        self.current = runtime.scheduled_slots(market, day)[0]
        self.waits = []

    def now(self):
        return self.current

    async def until(self, when):
        self.waits.append(when)
        self.current = max(when, self.current)


class FixturePorts:
    """Orchestration-only fake; never evidence of real source/model qualification."""

    def __init__(self, clock, failed_attempts=0, fail_stage=None):
        self.clock = clock
        self.failed_attempts = failed_attempts
        self.fail_stage = fail_stage
        self.collections, self.stages, self.notifications = [], [], []
        self.tamper = None
        self.stage_tamper = None
        self.notify_error = False
        self.universe = tuple(f"FICTIONAL-{n:02}" for n in range(22))

    async def policy(self, market, session, run_id):
        all_subjects = tuple(f"FICTIONAL-{n:02}" for n in range(22))
        self.universe = all_subjects[:14] if market == "us" else all_subjects[14:]
        self.frozen_policy = SnapshotPolicy(
            market=market, subjects=self.universe,
            universe_owner_sha256=digest(self.universe),
            message_ids=("market", *self.universe),
            validator_contracts=("existing-source-validator-fixture-v1",),
            roles=tuple(Role(key=t, symbol=t, provider="fixture", route="daily-query",
                             packet_pointer=f"/stocks/{i}/quote", session_date=session,
                             basis="adjusted", ohlc=True) for i, t in enumerate(self.universe)),
        )
        return self.frozen_policy

    async def collect(self, request, directory):
        self.collections.append(deepcopy(request))
        attempt = len(self.collections)
        packet = {"stocks": [{"ticker": t, "quote": {
            "open": 100 + attempt, "high": 104 + attempt,
            "low": 98 + attempt, "close": 102 + attempt,
        }} for t in self.universe]}
        result = Collection(
            run_id=request["run_id"], attempt_id=request["attempt_id"], market=request["market"],
            started_at=self.clock.now(), completed_at=self.clock.now(), packet=packet,
            policy_sha256=request["policy_sha256"],
            receipts=tuple(SourceReceipt(
                role=t, attempt_id=request["attempt_id"], provider="fixture", route="daily-query",
                symbol=t, session_date=date.fromisoformat(request["target_session"]), basis="adjusted",
                observed_at=self.clock.now(), raw_sha256=digest({"raw": t, "attempt": attempt}),
                normalized_sha256=digest(packet["stocks"][i]["quote"]), status="PASS",
            ) for i, t in enumerate(self.universe)),
            validators=(ValidatorReceipt(contract="existing-source-validator-fixture-v1",
                                         packet_sha256=digest(packet), status="PASS"),),
        )
        values = result.model_dump(mode="json")
        if attempt <= self.failed_attempts:
            values["receipts"].pop()
        if self.tamper:
            self.tamper(values)
        return Collection.model_validate(values)

    async def stage(self, request, directory):
        self.stages.append(deepcopy(request))
        stage = request["stage"]
        output = {"fixture": True}
        if stage == "RENDER":
            output = {"finality_claim": "NOT_CLAIMED", "messages": [
                {"message_id": key, "text": "Query-time snapshot; no finality claimed.",
                 "snapshot_sha256": request["snapshot_sha256"]}
                for key in self.frozen_policy.message_ids]}
        if stage == "DELIVER":
            output = {"normal_messages_sent": True, "receipts": [
                {"message_id": key, "status": "SENT"} for key in self.frozen_policy.message_ids]}
        result = StageResult(run_id=request["run_id"], snapshot_sha256=request["snapshot_sha256"],
                             request_sha256=digest(request), stage=stage,
                             status="FAIL" if self.fail_stage == stage else "PASS", output=output,
                             errors=("fixture_failure",) if self.fail_stage == stage else ())
        if self.stage_tamper:
            result = self.stage_tamper(result, request, directory)
        return result

    async def notify_failure(self, payload):
        self.notifications.append(deepcopy(payload))
        if self.notify_error:
            raise RuntimeError("token=private-value")
        return {"status": "FIXTURE_NOT_SENT"}


def setup(tmp_path, market="us", failed_attempts=0, fail_stage=None, day=date(2026, 9, 23)):
    destination = tmp_path / "cloud"
    destination.mkdir()
    clock = FakeClock(market, day)
    ports = FixturePorts(clock, failed_attempts, fail_stage)
    config = runtime.RunConfiguration(
        root=tmp_path / "runs", debug_destination=destination, repo_commit="fixture",
        scheduler_identity="fixture-single-" + market, adapter_fingerprint="fixture-only",
        secrets=("private-value",),
    )
    return runtime.UnifiedMarketRun(config, ports, clock=clock), ports, clock


def execute(engine, market="us", day=date(2026, 9, 23)):
    return asyncio.run(engine.run(market, day))


@pytest.mark.parametrize("market", ["us", "kr"])
@pytest.mark.parametrize("failed_attempts", [0, 1, 2])
def test_first_whole_eligible_attempt_wins(tmp_path, market, failed_attempts):
    engine, ports, clock = setup(tmp_path, market, failed_attempts)
    result = execute(engine, market)
    assert result["status"] == "SUCCESS"
    assert len(ports.collections) == failed_attempts + 1
    assert [r["stage"] for r in ports.stages] == list(STAGES)
    assert ports.notifications == []
    assert len({r["snapshot_sha256"] for r in ports.stages}) == 1
    assert len({r["run_id"] for r in ports.stages}) == 1
    assert clock.waits == list(runtime.scheduled_slots(market, date(2026, 9, 23)))[:failed_attempts + 1]
    for stage in ports.stages:
        snapshot = stage["snapshot"]["collection"]
        assert snapshot["attempt_id"].endswith(str(failed_attempts + 1))
        assert snapshot["packet"]["stocks"][0]["quote"]["close"] == 103 + failed_attempts
        assert snapshot["semantics"] == "QUERY_TIME_SNAPSHOT"
        assert snapshot["finality_claim"] == "NOT_CLAIMED"


@pytest.mark.parametrize("market", ["us", "kr"])
def test_three_incomplete_no_ai_sealed_failure_and_copy(tmp_path, market):
    engine, ports, _ = setup(tmp_path, market, failed_attempts=3)
    result = execute(engine, market)
    assert result["status"] == "FAILED"
    assert len(ports.collections) == 3
    assert ports.stages == []
    assert len(ports.notifications) == 1
    assert ports.notifications[0]["normal_messages_sent"] is False
    assert result["debug_upload"]["status"] == "LOCAL_COPY_HASH_VERIFIED"
    assert result["debug_upload"]["remote_sync"] == "NOT_VERIFIED"
    local = next(engine.config.root.glob("*/*-debug.zip"))
    remote = engine.config.debug_destination / local.name
    assert remote.read_bytes() == local.read_bytes()
    with zipfile.ZipFile(local) as z:
        summary = json.loads(z.read("summary.json"))
        assert len(summary["attempts"]) == 3
        assert summary["attempts"][0]["errors"]
        assert json.loads(z.read("secret-scan.json"))["status"] == "PASS"
        assert "packet" not in summary["attempts"][0]


@pytest.mark.parametrize("stage", STAGES)
def test_downstream_failure_never_recollects(tmp_path, stage):
    engine, ports, _ = setup(tmp_path, fail_stage=stage)
    result = execute(engine)
    assert result["status"] == "FAILED"
    assert result["failed_stage"] == stage
    assert len(ports.collections) == 1
    assert len(ports.stages) == STAGES.index(stage) + 1
    assert len(ports.notifications) == 1
    assert result["normal_messages_sent"] == ("UNKNOWN" if stage == "DELIVER" else False)


@pytest.mark.parametrize("market,day", [
    ("kr", date(2026, 9, 25)), ("us", date(2026, 9, 8)),
    ("us", date(2026, 9, 27)), ("kr", date(2026, 9, 26)),
])
def test_holiday_no_collection_models_render_send_or_alert(tmp_path, market, day):
    engine, ports, _ = setup(tmp_path, market, day=day)
    result = execute(engine, market, day)
    assert result["status"] == "SKIPPED"
    assert ports.collections == ports.stages == ports.notifications == []


def test_saturday_kst_is_valid_completed_friday_us_session():
    scheduled = runtime.scheduled_slots("us", date(2026, 9, 26))[0]
    assert runtime.target_session("us", scheduled) == date(2026, 9, 25)


def test_dual_market_fixture_has_configured_24_messages_without_hardcoding_runner(tmp_path):
    engine, ports, _ = setup(tmp_path)
    results = asyncio.run(run_selected("all", engine, date(2026, 9, 23)))
    assert [r["status"] for r in results] == ["SUCCESS", "SUCCESS"]
    deliveries = [s for s in ports.stages if s["stage"] == "DELIVER"]
    assert [len(r["inputs"]["RENDER"]["output"]["messages"]) for r in deliveries] == [15, 9]
    assert sum(len(r["snapshot"]["collection"]["packet"]["stocks"]) for r in deliveries) == 22


def test_all_market_kr_holiday_does_not_suppress_us(tmp_path):
    engine, ports, _ = setup(tmp_path, day=date(2026, 9, 25))
    results = asyncio.run(run_selected("all", engine, date(2026, 9, 25)))
    assert [r["status"] for r in results] == ["SUCCESS", "SKIPPED"]
    assert {r["market"] for r in ports.collections} == {"us"}


@pytest.mark.parametrize("fault,expected", [
    ("stale_run", "collection_identity_mismatch"),
    ("mixed_attempt", "source_identity_date_basis_invalid:FICTIONAL-00"),
    ("future_row", "source_identity_date_basis_invalid:FICTIONAL-00"),
    ("old_row", "source_identity_date_basis_invalid:FICTIONAL-00"),
    ("wrong_basis", "source_identity_date_basis_invalid:FICTIONAL-00"),
    ("wrong_route", "source_identity_date_basis_invalid:FICTIONAL-00"),
    ("wrong_symbol", "source_identity_date_basis_invalid:FICTIONAL-00"),
    ("missing_symbol", "production_universe_incomplete"),
    ("duplicate_symbol", "production_universe_incomplete"),
    ("invalid_ohlc", "required_source_fields_invalid:FICTIONAL-00"),
    ("null_close", "required_source_fields_invalid:FICTIONAL-00"),
    ("old_receipt", "source_time_outside_attempt:FICTIONAL-00"),
    ("wrong_hash", "normalized_source_binding_mismatch:FICTIONAL-00"),
    ("missing_validator", "source_validator_coverage_mismatch"),
    ("failed_validator", "source_validation_failed:existing-source-validator-fixture-v1"),
    ("wrong_policy", "collection_policy_mismatch"),
    ("provider_error", "required_source_error"),
])
def test_source_negatives_fail_closed(tmp_path, fault, expected):
    engine, ports, _ = setup(tmp_path)

    def tamper(v):
        receipt = v["receipts"][0]
        if fault == "stale_run":
            v["run_id"] = "yesterday"
        elif fault == "mixed_attempt":
            receipt["attempt_id"] = "other-attempt"
        elif fault == "future_row":
            receipt["session_date"] = "2099-01-01"
        elif fault == "old_row":
            receipt["session_date"] = "2020-01-01"
        elif fault in {"wrong_basis", "wrong_route", "wrong_symbol"}:
            receipt[fault[6:]] = "wrong"
        elif fault == "missing_symbol":
            v["packet"]["stocks"].pop()
        elif fault == "duplicate_symbol":
            v["packet"]["stocks"].append(v["packet"]["stocks"][0])
        elif fault == "invalid_ohlc":
            v["packet"]["stocks"][0]["quote"]["high"] = 0
        elif fault == "null_close":
            v["packet"]["stocks"][0]["quote"]["close"] = None
        elif fault == "old_receipt":
            receipt["observed_at"] = "2020-01-01T00:00:00+00:00"
        elif fault == "wrong_hash":
            receipt["normalized_sha256"] = "a" * 64
        elif fault == "missing_validator":
            v["validators"] = []
        elif fault == "failed_validator":
            v["validators"][0]["status"] = "FAIL"
        elif fault == "wrong_policy":
            v["policy_sha256"] = "a" * 64
        elif fault == "provider_error":
            v["source_errors"] = ["provider_unavailable"]
    ports.tamper = tamper
    result = execute(engine)
    assert result["status"] == "FAILED"
    assert all(expected in row["errors"] for row in result["attempts"])
    assert ports.stages == []


@pytest.mark.parametrize("field", ["run_id", "snapshot_sha256", "request_sha256"])
def test_layer_binding_mismatch_terminal(tmp_path, field):
    engine, ports, _ = setup(tmp_path)
    ports.stage_tamper = lambda result, *_: result.model_copy(update={field: "wrong"})
    result = execute(engine)
    assert result["status"] == "FAILED"
    assert len(ports.collections) == len(ports.stages) == 1


def test_snapshot_on_disk_mutation_is_detected(tmp_path):
    engine, ports, _ = setup(tmp_path)

    def corrupt(result, request, directory):
        path = directory.parent / "snapshot.json"
        path.write_text("{}")
        return result
    ports.stage_tamper = corrupt
    result = execute(engine)
    assert result["status"] == "FAILED"
    assert result["failed_stage"] == "MARKET"
    assert not any(r["stage"] == "DELIVER" for r in ports.stages)


def test_mutating_returned_source_cannot_rewrite_frozen_data(tmp_path):
    engine, ports, _ = setup(tmp_path)
    first = execute(engine)
    path = next(engine.config.root.glob("*/snapshot.json"))
    before = path.read_bytes()
    ports.stages[0]["snapshot"]["collection"]["packet"]["stocks"][0]["quote"]["close"] = 999
    assert path.read_bytes() == before
    assert execute(engine) == json.loads(json.dumps(first))
    assert len(ports.collections) == 1


def test_restart_with_delivery_intent_never_resends_normal_messages(tmp_path):
    engine, ports, _ = setup(tmp_path)
    result = execute(engine)
    directory = engine.config.root / result["run_id"]
    (directory / "terminal.json").unlink()
    before = len(ports.stages)
    result = execute(engine)
    assert result["status"] == "FAILED"
    assert result["recovery"] == "INTERRUPTED_CYCLE_NO_AUTOMATIC_REPLAY"
    assert len(ports.stages) == before


def test_concurrent_cycle_has_single_owner(tmp_path):
    engine, ports, _ = setup(tmp_path)
    original = ports.collect

    async def scenario():
        entered, release = asyncio.Event(), asyncio.Event()

        async def delayed(request, directory):
            entered.set()
            await release.wait()
            return await original(request, directory)
        ports.collect = delayed
        first = asyncio.create_task(engine.run("us", date(2026, 9, 23)))
        await entered.wait()
        duplicate = await engine.run("us", date(2026, 9, 23))
        assert duplicate["status"] == "ALREADY_RUNNING"
        release.set()
        assert (await first)["status"] == "SUCCESS"
    asyncio.run(scenario())
    assert len(ports.collections) == 1


def test_late_resume_uses_allowed_slot_without_burst(tmp_path):
    engine, ports, clock = setup(tmp_path)
    clock.current += timedelta(minutes=6)
    result = execute(engine)
    assert result["status"] == "SUCCESS"
    assert result["attempts"][0]["status"] == "WINDOW_MISSED"
    assert ports.collections[0]["attempt_id"].endswith("attempt-2")


def test_after_final_window_no_provider_call(tmp_path):
    engine, ports, clock = setup(tmp_path)
    clock.current += timedelta(minutes=15)
    result = execute(engine)
    assert result["status"] == "FAILED"
    assert ports.collections == ports.stages == []


def test_notification_failure_still_sealed_and_uploaded(tmp_path):
    engine, ports, _ = setup(tmp_path, failed_attempts=3)
    ports.notify_error = True
    result = execute(engine)
    assert result["debug_upload"]["status"] == "LOCAL_COPY_HASH_VERIFIED"
    path = next(engine.config.root.glob("*/*-debug.zip"))
    with zipfile.ZipFile(path) as z:
        raw = z.read("summary.json")
        assert b"private-value" not in raw
        assert json.loads(raw)["failure_notification"]["status"] == "FAILED"


def test_unavailable_cloud_fails_visibly_and_retains_local_zip(tmp_path):
    engine, ports, _ = setup(tmp_path)
    engine.config.debug_destination.rmdir()
    result = execute(engine)
    assert result["debug_upload"]["status"] == "FAILED"
    assert list(engine.config.root.glob("*/*-debug.zip"))
    assert ports.collections == []


def test_atomic_copy_never_overwrites_conflicting_archive(tmp_path):
    source, destination = tmp_path / "report.zip", tmp_path / "cloud"
    destination.mkdir()
    durable_bytes(source, b"archive-one", exclusive=True)
    copy_verified(source, destination)
    source.write_bytes(b"archive-two")
    with pytest.raises(ValueError, match="immutable_debug_destination_conflict"):
        copy_verified(source, destination)
    assert (destination / source.name).read_bytes() == b"archive-one"


def test_debug_redaction():
    value = {"telegram_chat_id": "12345", "url": "https://provider/?api_key=bad&ok=yes",
             "error": "Bearer private-token", "detail": "custom-secret"}
    safe = json.dumps(sanitized(value, ("custom-secret",)))
    assert all(s not in safe for s in ("12345", "=bad", "private-token", "custom-secret"))


@pytest.mark.parametrize("fault", ["finality", "message_missing", "empty_text", "wrong_snapshot", "wording"])
def test_render_contract_rejects_missing_or_unsupported_message(tmp_path, fault):
    engine, ports, _ = setup(tmp_path)

    def corrupt(result, request, directory):
        if result.stage != "RENDER":
            return result
        output = deepcopy(result.output)
        if fault == "finality":
            output["finality_claim"] = "OFFICIAL"
        elif fault == "message_missing":
            output["messages"].pop()
        elif fault == "empty_text":
            output["messages"][0]["text"] = ""
        elif fault == "wrong_snapshot":
            output["messages"][0]["snapshot_sha256"] = "wrong"
        else:
            output["messages"][0]["text"] = "Official final close"
        return result.model_copy(update={"output": output})
    ports.stage_tamper = corrupt
    result = execute(engine)
    assert result["status"] == "FAILED"
    assert result["failed_stage"] == "RENDER"
    assert not any(s["stage"] == "DELIVER" for s in ports.stages)


def test_missing_delivery_receipt_not_success(tmp_path):
    engine, ports, _ = setup(tmp_path)
    ports.stage_tamper = lambda result, *_: (result.model_copy(update={"output": {}})
                                          if result.stage == "DELIVER" else result)
    result = execute(engine)
    assert result["status"] == "FAILED"
    assert result["normal_messages_sent"] == "UNKNOWN"


def test_schema_rejects_unallowed_provider_and_unknown_basis():
    args = dict(key="a", symbol="a", provider="Alpha_Vantage", route="daily", packet_pointer="/a",
                session_date=None, basis="raw")
    with pytest.raises(ValueError, match="provider_not_authorized"):
        Role(**args)
    args.update(provider="fixture", basis="unknown")
    with pytest.raises(ValueError, match="explicit_basis_required"):
        Role(**args)


def test_timezone_naive_is_not_verified(tmp_path):
    engine, ports, clock = setup(tmp_path)

    async def scenario():
        policy = await ports.policy("us", date(2026, 9, 22), "id")
        request = dict(run_id="id", attempt_id="id-1", market="us", target_session="2026-09-22",
                       policy_sha256=digest(policy.model_dump(mode="json")))
        result = await ports.collect(request, tmp_path)
        result = result.model_copy(update={"started_at": datetime(2026, 9, 23)})
        errors = validate_collection(result, policy=policy, run_id="id", attempt_id="id-1",
                                     started_at=clock.now(), now=clock.now())
        assert "timezone_required" in errors
    asyncio.run(scenario())


def test_scheduler_plan_is_single_entry_and_inactive():
    from pathlib import Path
    from app.services.unified_scheduler_plan import migration_plan, RETIRED_AGENTS, RETIRED_AUTOMATIONS

    plan = migration_plan(Path("/deployment"), Path("/deployment/.venv/bin/python"),
                          host_timezone="Asia/Seoul")
    assert plan["activation_allowed"] is False
    assert len(plan["new_agents"]) == 2
    assert [p["StartCalendarInterval"] for p in plan["new_agents"]] == [
        {"Hour": 8, "Minute": 10}, {"Hour": 16, "Minute": 0}]
    assert all(p["Disabled"] for p in plan["new_agents"])
    assert len(RETIRED_AUTOMATIONS) == len(RETIRED_AGENTS) == 4
    assert not any("backup" in json.dumps(p) for p in plan["new_agents"])
    assert "onboarding_reconciler" in plan["preserve"]
    with pytest.raises(ValueError, match="verified_kst_host"):
        migration_plan(Path("/deployment"), Path("/python"), host_timezone="UTC")


def test_sleep_overrun_does_not_start_missed_attempt(tmp_path):
    engine, ports, clock = setup(tmp_path)

    async def late(when):
        clock.current = when + timedelta(minutes=6)
    clock.until = late
    result = execute(engine)
    assert result["status"] == "FAILED"
    assert ports.collections == []


def test_collection_overrun_skips_elapsed_retry_slots(tmp_path):
    engine, ports, clock = setup(tmp_path, failed_attempts=1)
    original = ports.collect

    async def slow(request, directory):
        result = await original(request, directory)
        if len(ports.collections) == 1:
            clock.current += timedelta(minutes=11)
        return result
    ports.collect = slow
    result = execute(engine)
    assert result["status"] == "SUCCESS"
    assert len(ports.collections) == 2
    assert ports.collections[-1]["attempt_id"].endswith("attempt-3")
    assert result["attempts"][1]["status"] == "WINDOW_MISSED"


def test_source_os_error_is_not_a_recollection_trigger(tmp_path):
    engine, ports, _ = setup(tmp_path)

    async def no_disk(request, directory):
        ports.collections.append(request)
        raise OSError("no space left; password=private-value")
    ports.collect = no_disk
    result = execute(engine)
    assert result["status"] == "FAILED"
    assert len(ports.collections) == 1


def test_invalid_calendar_fails_closed_not_weekday_fallback(tmp_path, monkeypatch):
    engine, ports, _ = setup(tmp_path)

    def bad(*args):
        raise ValueError("calendar unavailable")
    monkeypatch.setattr(runtime, "_exchange_calendar", bad)
    result = execute(engine)
    assert result["status"] == "FAILED"
    assert result["failed_stage"] == "SESSION_GATE"
    assert not ports.collections


def test_runtime_defaults_off_and_no_unqualified_fallback(tmp_path, monkeypatch, capsys):
    from app.config import Settings
    from app.jobs import unified_market_snapshot as job

    settings = Settings(_env_file=None)
    assert settings.unified_snapshot_enabled is False
    monkeypatch.setattr(job, "get_settings", lambda: settings)
    monkeypatch.setattr("sys.argv", ["job", "--market", "us"])
    asyncio.run(job.main())
    assert json.loads(capsys.readouterr().out)["status"] == "DISABLED"
    with pytest.raises(RuntimeError, match="adapter_not_qualified"):
        asyncio.run(job.load_adapter(settings).policy("us", date(2026, 9, 22), "id"))


def test_stage_timeout_cancels_owned_work_and_does_not_recollect(tmp_path):
    from dataclasses import replace

    engine, ports, _ = setup(tmp_path)
    engine.config = replace(engine.config, stage_timeout_seconds=0.01)
    canceled = []

    async def stalled(request, directory):
        try:
            await asyncio.sleep(60)
        finally:
            canceled.append(request["stage"])
    ports.stage = stalled
    result = execute(engine)
    assert result["status"] == "FAILED"
    assert result["failure_code"] == "TimeoutError"
    assert canceled == ["MARKET"]
    assert len(ports.collections) == 1


def test_owned_interruption_is_terminal_not_collection_retry(tmp_path):
    engine, ports, _ = setup(tmp_path)

    async def interrupted(request, directory):
        ports.collections.append(request)
        raise asyncio.CancelledError()
    ports.collect = interrupted
    result = execute(engine)
    assert result["status"] == "FAILED"
    assert result["failure_code"] == "CancelledError"
    assert len(ports.collections) == 1
    assert result["debug_upload"]["status"] == "LOCAL_COPY_HASH_VERIFIED"


def test_policy_is_frozen_between_layers(tmp_path):
    engine, ports, _ = setup(tmp_path)

    def mutate(result, request, directory):
        (directory.parent / "policy.json").write_text("{}")
        return result
    ports.stage_tamper = mutate
    result = execute(engine)
    assert result["status"] == "FAILED"
    assert result["failure_code"] == "frozen_snapshot_or_policy_changed"
    assert len(ports.stages) == 1


def test_duplicate_failed_cycle_does_not_notify_again(tmp_path):
    engine, ports, _ = setup(tmp_path, failed_attempts=3)
    first = execute(engine)
    second = execute(engine)
    assert second["run_id"] == first["run_id"]
    assert len(ports.notifications) == 1
    assert len(ports.collections) == 3
