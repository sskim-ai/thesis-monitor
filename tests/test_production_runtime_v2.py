"""Runtime contract probes, not a claim of full production adapter qualification."""
import asyncio
from datetime import date, timedelta
from dataclasses import replace
from pathlib import Path

import pytest

from app.services import unified_market_run as runtime
from app.services import unified_runtime_v2 as v2
from app.services.production_source_execution import (
    ProductionCollection, ProductionRoleResolution, ProductionSourceExecutionEnvelopeV1,
    ProductionSourceRole, build_production_policy,
)
from app.services.unified_snapshot_contract import Role, SourceReceipt, ValidatorReceipt, digest
from app.services.unified_stock_acquisition import UNIVERSE
from app.services.unified_scheduler_plan import migration_plan
from tests.test_unified_market_snapshot import FakeClock

DAY = date(2026, 9, 23)


class RuntimePorts:
    def __init__(self, clock, failures=0, overrun=False, night="AVAILABLE", fail_stage=None):
        self.clock, self.failures, self.overrun = clock, failures, overrun
        self.night, self.fail_stage = night, fail_stage
        self.calls, self.stages, self.notifications = [], [], []

    async def policy(self, market, session, run_id):
        roles = [ProductionSourceRole(role=Role(key=t, symbol=t, provider="kiwoom",
            route="usa20590" if market == "us" else "ka10081", session_date=session,
            basis="completed_regular_close", packet_pointer=f"/stocks/{i}/quote", numeric_fields=("close",)),
            owner_contract="synthetic-canonical-close-v1", purpose="COMPLETED_CLOSE", required=True)
            for i, t in enumerate(UNIVERSE[market])]
        roles.append(ProductionSourceRole(role=Role(key="night", symbol="KOSPI200", provider="krx_night_futures",
            route="fut_bydd_trd", session_date=session, basis="night_session", packet_pointer="/night"),
            owner_contract="synthetic-optional-owner-v1", purpose="NIGHT", required=False))
        families = [('TECHNICAL', 'kiwoom', 'usa06012' if market == 'us' else 'ka10081'),
                    ('FINANCIAL', 'sec_edgar' if market == 'us' else 'opendart', 'companyfacts' if market == 'us' else 'financial'),
                    ('BUSINESS', 'sec_edgar' if market == 'us' else 'opendart', 'filing' if market == 'us' else 'document'),
                    ('VALUATION', 'finnhub' if market == 'us' else 'kis', 'metric' if market == 'us' else '/uapi/domestic-stock/v1/quotations/estimate-perform')]
        for ticker in UNIVERSE[market]:
            for purpose, provider, route in families:
                roles.append(ProductionSourceRole(role=Role(key=ticker+':'+purpose, symbol=ticker,
                    provider=provider, route=route, session_date=None, basis='synthetic-family', packet_pointer='/context'),
                    owner_contract='synthetic-family-owner-v1', purpose=purpose, required=True))
        roles.append(ProductionSourceRole(role=Role(key='market', symbol='MARKET', provider='kiwoom', route='ka20001',
            session_date=None, basis='synthetic-market', packet_pointer='/context'), owner_contract='synthetic-market-v1', purpose='MARKET', required=True))
        self.bound_policy = build_production_policy(market=market, subjects=UNIVERSE[market],
            source_roles=roles, code_config_sha256=digest("synthetic-config"))
        return self.bound_policy

    async def collect(self, request, directory):
        self.calls.append(request)
        policy = self.bound_policy
        started = self.clock.now()
        if self.overrun and len(self.calls) == 1:
            self.clock.current += timedelta(minutes=6)
        packet = {"stocks": [{"ticker": t, "quote": {"close": 100}} for t in policy.subjects],
                  "context": {"close": 100},
                  "night": {"value": 100} if self.night == "AVAILABLE" else None}
        receipts, rows = [], []
        for spec in policy.source_roles:
            role = spec.role
            value = packet["night"] if role.key == "night" else {"close": 100}
            raw_hash = digest([role.key, request["attempt_id"]])
            available = value is not None
            state = "AVAILABLE" if available else "TYPED_UNAVAILABLE"
            owner = dict(contract=spec.owner_contract, generation_id=request["attempt_id"], role=role.key,
                raw_receipt_sha256=raw_hash, normalized_sha256=digest(value), state=state,
                current_eligible_count=int(available))
            provenance = dict(generation_id=request["attempt_id"], attempt_id=request["attempt_id"],
                role=role.key, target_session=request["target_session"], raw_receipt_sha256=raw_hash)
            rows.append(ProductionRoleResolution(role_key=role.key, provider=role.provider, route=role.route,
                owner_contract=spec.owner_contract, state=state, raw_receipt_sha256=raw_hash,
                normalized_sha256=digest(value), owner_result_sha256=digest(owner), provenance_sha256=digest(provenance),
                observed_at=self.clock.now(), current_eligible_count=int(available),
                reason_codes=() if available else ("NO_CURRENT_FINAL_ROW",), value=value, owner_result=owner, provenance=provenance))
            receipts.append(SourceReceipt(role=role.key, attempt_id=request["attempt_id"], provider=role.provider,
                route=role.route, symbol=role.symbol, session_date=role.session_date, basis=role.basis,
                observed_at=self.clock.now(), raw_sha256=raw_hash, normalized_sha256=digest(value), status="PASS"))
        envelope = ProductionSourceExecutionEnvelopeV1(market=request["market"], run_id=request["run_id"],
            attempt_id=request["attempt_id"], generation_id=request["attempt_id"], subjects=policy.subjects,
            source_policy_sha256=request["policy_sha256"], code_config_sha256=policy.code_config_sha256,
            started_at=started, completed_at=self.clock.now(), target_session=request["target_session"],
            required_roles=tuple(r.role.key for r in policy.source_roles if r.required), optional_roles=("night",),
            resolutions=tuple(rows), packet_sha256=digest(packet))
        if len(self.calls) <= self.failures:
            receipts.pop(0)
        return ProductionCollection(run_id=request["run_id"], attempt_id=request["attempt_id"],
            market=request["market"], started_at=started, completed_at=self.clock.now(), packet=packet,
            receipts=tuple(receipts), validators=tuple(ValidatorReceipt(contract=k, packet_sha256=digest(packet), status="PASS")
                for k in policy.validator_contracts), policy_sha256=request["policy_sha256"], production_envelope=envelope)

    async def stage(self, request, directory):
        self.stages.append(request["stage"])
        generation = request["snapshot"]["collection"]["production_envelope"]["generation_id"]
        output = {"fixture_only": True}
        if request["stage"] == "RENDER":
            output = dict(finality_claim="NOT_CLAIMED", messages=[dict(message_id=k, text="Offline query-time fixture.",
                snapshot_sha256=request["snapshot_sha256"], generation_id=generation) for k in self.bound_policy.message_ids])
        if request["stage"] == "DELIVER":
            from app.services.production_delivery import ProductionDelivery
            delivery = ProductionDelivery(root=directory / "outbox", fingerprint=digest("synthetic-destination"),
                                          dry_run=True, live_authorized=False, notifier=None)
            output = await delivery.deliver(run_id=request["run_id"], generation_id=generation,
                messages=request["inputs"]["RENDER"]["output"]["messages"])
        return v2.StageResultV2(run_id=request["run_id"], generation_id=generation, snapshot_sha256=request["snapshot_sha256"],
            request_sha256=digest(request), stage=request["stage"], status="FAIL" if request["stage"] == self.fail_stage else "PASS", output=output)

    async def notify_failure(self, payload):
        self.notifications.append(payload)
        return {"status": "DRY_RUN_NOT_SENT"}


def setup(tmp_path, market, **kwargs):
    destination = tmp_path / "icloud-fixture"
    destination.mkdir()
    clock = FakeClock(market)
    clock.current = v2.scheduled_slots(market, DAY)[0]
    ports = RuntimePorts(clock, **kwargs)
    config = runtime.RunConfiguration(root=tmp_path / "runs", debug_destination=destination,
        repo_commit="synthetic", scheduler_identity="synthetic", adapter_fingerprint="RUNTIME_TEST_NOT_QUALIFIED",
        runtime_contract=v2.CONTRACT, stage_timeout_seconds=600, collection_timeout_seconds=600)
    return runtime.UnifiedMarketRun(config, ports, clock=clock), ports


@pytest.mark.parametrize("market", ("us", "kr"))
@pytest.mark.parametrize("failures", (0, 1, 2))
def test_v2_first_eligible_attempt_and_explicit_b2(tmp_path, market, failures):
    engine, ports = setup(tmp_path, market, failures=failures)
    result = asyncio.run(engine.run(market, DAY))
    assert result["status"] == "SUCCESS", result["error_chain"]
    assert len(ports.calls) == failures + 1
    assert ports.stages == list(v2.STAGES)
    assert not result["normal_messages_sent"]
    assert asyncio.run(engine.run(market, DAY)) == result
    assert len(ports.calls) == failures + 1


@pytest.mark.parametrize("market", ("us", "kr"))
def test_overrun_blocks_crossed_slot_and_waits_for_third(tmp_path, market):
    engine, ports = setup(tmp_path, market, failures=1, overrun=True)
    result = asyncio.run(engine.run(market, DAY))
    assert result["status"] == "SUCCESS"
    assert len(ports.calls) == 2
    assert ports.calls[1]["attempt_id"].endswith("attempt-3")
    assert result["attempts"][1]["status"] == "WINDOW_MISSED"


@pytest.mark.parametrize("market", ("us", "kr"))
def test_three_failed_collections_one_failure_and_truthful_local_copy(tmp_path, market):
    engine, ports = setup(tmp_path, market, failures=3)
    result = asyncio.run(engine.run(market, DAY))
    assert result["status"] == "FAILED"
    assert len(ports.notifications) == 1 and not ports.stages
    assert result["debug_upload"]["status"] == "LOCAL_ICLOUD_CONTAINER_VERIFIED"
    assert result["debug_upload"]["remote_sync"] == "NOT_VERIFIED"


@pytest.mark.parametrize("market", ("us", "kr"))
def test_optional_unavailable_continues(tmp_path, market):
    engine, ports = setup(tmp_path, market, night="UNAVAILABLE")
    result = asyncio.run(engine.run(market, DAY))
    assert result["status"] == "SUCCESS"
    assert ports.stages == list(v2.STAGES)


@pytest.mark.parametrize("market", ("us", "kr"))
def test_b2_failure_never_reaches_render_or_deliver(tmp_path, market):
    engine, ports = setup(tmp_path, market, fail_stage="B2")
    result = asyncio.run(engine.run(market, DAY))
    assert result["status"] == "FAILED"
    assert ports.stages == ["MARKET", "CORE", "A", "B", "B2"]


def test_v1_scheduler_preserved_and_v2_future_plan_only():
    args = (Path("/synthetic/checkout"), Path("/synthetic/python"))
    before = migration_plan(*args, host_timezone="Asia/Seoul")
    after = migration_plan(*args, host_timezone="Asia/Seoul", runtime_version=2)
    assert before["new_agents"][1]["StartCalendarInterval"]["Minute"] == 0
    assert after["new_agents"][1]["StartCalendarInterval"]["Minute"] == 10
    assert after["status"] == "NOT_APPLIED" and not after["activation_allowed"]
    assert all(a["Disabled"] for a in after["new_agents"])


def test_v2_timeout_contract(tmp_path):
    engine, ports = setup(tmp_path, "us")
    with pytest.raises(ValueError, match="600_second"):
        runtime.UnifiedMarketRun(replace(engine.config, stage_timeout_seconds=1200), ports)
