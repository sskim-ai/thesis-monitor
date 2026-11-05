"""C7 retry override uses the real compiler; fixtures confer no live authority."""
from pathlib import Path
import asyncio
import json

import httpx

import pytest

from app.services.production_source_plan import build_request_plan, admit_request_plan
from tests.test_production_source_plan import current_plan


@pytest.mark.parametrize("market", ["kr", "us"])
def test_zero_retry_flows_through_original_production_compiler(market):
    args, kis, legacy = current_plan(market)
    assert any(d.transient_retry_max == 2 for d in legacy["plan"].descriptors)
    args["transient_retry_max"] = 0
    result = build_request_plan(market=market, run_id="production-fixture",
        attempt_id="production-fixture-attempt-1", compiler_args=args, kis_plan=kis)
    assert result["plan"].descriptors
    assert all(d.transient_retry_max == 0 and d.max_transport_attempts == 1
        for d in result["plan"].descriptors)
    for financial in result["candidate"]["financial_plans"].values():
        assert financial["maximum_retries_per_request"] == 0
        assert financial["maximum_attempts_per_request"] == 1
        assert financial["maximum_HTTP_attempts"] == financial["maximum_logical_requests"]
    admission = admit_request_plan(result["plan"], compiler_args=args, kis_plan=kis,
        config_identities=args["config_identities"],
        credential_presence={**dict.fromkeys(args["config_identities"], True), "kis": True},
        repository_root=Path(__file__).resolve().parents[1])
    assert admission["status"] == "PASS", admission
    args.pop("transient_retry_max")
    changed = admit_request_plan(result["plan"], compiler_args=args, kis_plan=kis,
        config_identities=args["config_identities"],
        credential_presence={**dict.fromkeys(args["config_identities"], True), "kis": True},
        repository_root=Path(__file__).resolve().parents[1])
    assert "canonical_plan_replay_mismatch" in changed["gaps"]


@pytest.mark.parametrize("invalid", [True, False, -1, 3, 0.0, "0"])
def test_invalid_run_retry_policy_rejected_before_dispatch(invalid):
    args, kis, _ = current_plan("us")
    args["transient_retry_max"] = invalid
    with pytest.raises(ValueError, match="finite_transient_retry_policy_required"):
        build_request_plan(market="us", run_id="production-fixture",
            attempt_id="production-fixture-attempt-1", compiler_args=args, kis_plan=kis)


@pytest.mark.parametrize("market", ["kr", "us"])
def test_omitted_override_keeps_original_compiler_bytes(market):
    args, kis, original = current_plan(market)
    args["transient_retry_max"] = None
    rebuilt = build_request_plan(market=market, run_id="production-fixture",
        attempt_id="production-fixture-attempt-1", compiler_args=args, kis_plan=kis)
    assert rebuilt["plan"].descriptors == original["plan"].descriptors
    assert rebuilt["candidate"] == original["candidate"]


@pytest.mark.parametrize("failure", [500, 401, 403, 429, "connect"])
def test_actual_dispatch_executor_sends_once_with_zero_retry(tmp_path, failure):
    from app.services.production_source_dispatch import ProductionSourceDispatcher
    from app.services.sealed_fresh_dispatch import SourceSafetyStop
    args, kis, _ = current_plan("us")
    args["transient_retry_max"] = 0
    result = build_request_plan(market="us", run_id="production-fixture",
        attempt_id="production-fixture-attempt-1", compiler_args=args, kis_plan=kis)
    plan = result["plan"]
    dispatcher = ProductionSourceDispatcher(plan=plan, root=tmp_path/"dispatch",
        compiler_args=args, kis_plan=kis, config_identities=args["config_identities"],
        credential_presence={**dict.fromkeys(args["config_identities"], True), "kis": True},
        repository_root=Path(__file__).resolve().parents[1])
    descriptor = next(d for d in plan.descriptors if d.provider == "fred")
    wire = json.loads(descriptor.request_json)
    request = httpx.Request(wire["method"], wire["url"], headers=wire["headers"], content=wire["body"])
    calls = []
    def respond(req):
        calls.append(req)
        if failure == "connect":
            raise httpx.ConnectError("synthetic network failure", request=req)
        return httpx.Response(failure, json={"error": "synthetic"})
    def normalize(raw):
        raise AssertionError("failed source must not normalize")
    normalize.identity = (descriptor.normalizer, descriptor.owner_sha256)
    async def run():
        async with httpx.MockTransport(respond) as transport:
            try:
                await dispatcher.execute(descriptor.logical_request_id, request,
                    transport=transport, normalize=normalize)
            except SourceSafetyStop:
                assert failure in (401, 403)
    asyncio.run(run())
    assert len(calls) == 1
    final = json.loads((tmp_path/"dispatch"/"receipts"/descriptor.logical_request_id/"final.json").read_bytes())
    assert len(final["attempts"]) == 1 and final["status"] != "PASS"
