"""Native request construction and scoped identity, entirely offline."""
from copy import deepcopy
import json
from pathlib import Path

import pytest

from scripts.strict_blind_controller import (
    ControllerError, MARKET_CONTRACTS, MODEL_STAGES, RequestScope, STATES,
    StrictBlindController, digest, encoded, request_identity,
)
from scripts.strict_blind_native_market_proof import (
    capture, full_native_proof, market_requests, native_prepared, packet, market_owner, response, owner,
)
from scripts.strict_blind_offline_proof import fixture, host_for, run_stage


@pytest.fixture
def markets(tmp_path):
    c = native_prepared(tmp_path, extra_code_files=[__file__])
    run_stage(c, "BLIND")
    requests = market_requests(c)
    c.seal_requests("MARKET", requests)
    return c, requests


def test_native_both_market_lifecycle(tmp_path, monkeypatch):
    import socket
    import subprocess
    def deny(*args, **kwargs):
        pytest.fail("External operation in offline native parity proof")
    monkeypatch.setattr(socket, "socket", deny)
    monkeypatch.setattr(subprocess, "Popen", deny)
    proof = full_native_proof(tmp_path)
    assert proof["states"] == list(STATES)
    assert not proof["controller"]["strict_run_started"]
    assert proof["controller"]["state"] == "COMPLETE"
    assert all(row["bytes_unchanged"] and row["output_seal_unlocked_core_and_remaining_stages"]
               for row in proof["markets"])


@pytest.mark.parametrize("index", [0, 1], ids=["US", "KR"])
def test_market_detached_identity_no_fake_subject(markets, index):
    c, requests = markets
    request = requests[index]
    host, ctx, _ = host_for(c, request)
    detached = json.loads(encoded(request))
    detached["subjects"] = ()
    auth = c.authorize("MARKET", detached, host=host, context=ctx)
    assert auth["scope"] == RequestScope.MARKET and auth["subjects"] == []
    assert auth["market"] == request["market"] and "failed_receipt_sha256" not in auth
    assert digest(detached) == digest(request)


@pytest.mark.parametrize("index", [0, 1], ids=["US", "KR"])
@pytest.mark.parametrize("change", ["market", "generation", "stage", "bytes", "contract", "subjects", "scope"])
def test_wrong_market_generation_stage_bytes_reject(markets, index, change):
    c, requests = markets
    request = requests[index]
    host, ctx, _ = host_for(c, request)
    bad = deepcopy(request)
    if change == "market":
        bad["market"] = "KR" if request["market"] == "US" else "US"
        bad["native_market_contract"] = MARKET_CONTRACTS[bad["market"]]
    elif change == "bytes":
        bad["payload"]["prompt"] += " drift"
        bad["request_sha256"] = digest(bad["payload"])
    else:
        key, value = {"generation": ("generation", "wrong"), "stage": ("stage", "CORE"),
            "contract": ("native_market_contract", "unregistered"), "subjects": ("subjects", ["FAKE_MARKET"]),
            "scope": ("scope", RequestScope.SUBJECT)}[change]
        bad[key] = value
    with pytest.raises(ControllerError):
        c.authorize("MARKET", bad, host=host, context=ctx)


@pytest.mark.parametrize("stage", [s for s in MODEL_STAGES if s != "MARKET"])
def test_subject_scoped_stages_reject_empty_plan_and_identity(tmp_path, stage):
    c, _, code = fixture(tmp_path)
    plan = deepcopy(c.contract["plan"])
    plan["stages"][stage][0]["subjects"] = []
    with pytest.raises(ControllerError, match="SUBJECT_SCOPE_REQUIRED"):
        StrictBlindController.create(tmp_path/"bad", generation="new", plan=plan,
            code_files=[code], host_preparation=c.contract["host_preparation"])
    with pytest.raises(ControllerError, match="SUBJECT_SCOPE_REQUIRED"):
        request_identity(generation="new", stage=stage, **plan["stages"][stage][0], payload={},
            prompt_sha256="0"*64, schema_sha256="0"*64, policy_sha256="0"*64, context_refs={})


@pytest.mark.parametrize("market", ["US", "KR"])
@pytest.mark.parametrize("kind", ["fake_subject", "wrong_scope", "wrong_contract", "unknown_market"])
def test_invalid_market_plan_fails_before_root_created(tmp_path, market, kind):
    c, _, code = fixture(tmp_path)
    plan = deepcopy(c.contract["plan"])
    row = plan["stages"]["MARKET"][0]
    row.update(market=market, native_market_contract=MARKET_CONTRACTS[market])
    key, value = {"fake_subject": ("subjects", ["MARKET"]), "wrong_scope": ("scope", RequestScope.SUBJECT),
        "wrong_contract": ("native_market_contract", "other"), "unknown_market": ("market", "JP")}[kind]
    row[key] = value
    with pytest.raises(ControllerError):
        StrictBlindController.create(tmp_path/"bad", generation="new", plan=plan,
            code_files=[code], host_preparation=c.contract["host_preparation"])
    assert not (tmp_path/"bad").exists()


@pytest.mark.parametrize("market", ["US", "KR"])
def test_native_validators_reject_wrong_market_and_unsupported_refs(tmp_path, market):
    context = market_owner.market_context(packet(market))
    payload, _ = capture(tmp_path/market, market, context, "synthetic")
    row = response(market)
    assert not owner.validate_json_schema(row, payload["response_schema"])
    assert market_owner.validate_market(row, context)["status"] == "PASS"
    row["market"] = "KR" if market == "US" else "US"
    assert owner.validate_json_schema(row, payload["response_schema"])
    assert market_owner.validate_market(row, context)["status"] == "FAIL"
    row = response(market)
    row["supporting_refs"] = ["not_in_source"]
    assert owner.validate_json_schema(row, payload["response_schema"])
    assert market_owner.validate_market(row, context)["status"] == "FAIL"


def test_native_market_files_in_frozen_contract(markets):
    from scripts.strict_blind_controller import NATIVE_MARKET_FILES
    c, _ = markets
    assert set(NATIVE_MARKET_FILES) <= {Path(p).name for p in c.contract["code"]}
