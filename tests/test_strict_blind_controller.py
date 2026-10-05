"""Offline orchestration controls. No actual issuer data, labels, or external calls."""
from copy import deepcopy
from dataclasses import replace
import json

import pytest

from app.services.unified_snapshot_contract import digest, encoded
from scripts import scoped_attempt_failure as failure
from scripts.strict_blind_controller import (
    ControllerError, Mode, STATES, StrictBlindController, canonical, qualify_host,
)
from scripts.strict_blind_offline_proof import (
    fixture, full_proof, host_for, host_inputs, requests_for, run_stage, source_phase,
)


@pytest.fixture
def prepared(tmp_path):
    controller, authorities, code = fixture(tmp_path, extra_code_files=[__file__])
    source_phase(controller, authorities, code)
    return controller


@pytest.fixture
def blind(prepared):
    request = requests_for(prepared, "BLIND")[0]
    prepared.seal_requests("BLIND", [request])
    host, context, _ = host_for(prepared, request)
    return prepared, request, host, context


def attempt(blind, **changes):
    controller, request, host, context = blind
    kwargs = dict(host=host, context=context, transport=lambda p: b'{"synthetic":true}',
                  provider_validate=lambda v: True, semantic_validate=lambda v: True, simulated=True)
    kwargs.update(changes)
    return controller.attempt("BLIND", request, **kwargs)


def test_01_tuple_list_canonical_authorization(blind):
    c, request, host, context = blind
    native = deepcopy(request)
    native["subjects"] = tuple(native["subjects"])
    assert digest(native) == digest(request)
    assert c.authorize("BLIND", native, host=host, context=context) == c.authorize(
        "BLIND", json.loads(encoded(request)), host=host, context=context)


@pytest.mark.parametrize("mutation", ["claimed_hash", "same_id_changed_bytes"])
def test_02_changed_sha_or_same_id_changed_bytes_rejected(blind, mutation):
    c, request, host, context = blind
    altered = deepcopy(request)
    if mutation == "claimed_hash":
        altered["request_sha256"] = "0" * 64
    else:
        altered["payload"]["prompt"] += " changed"
        altered["request_sha256"] = digest(altered["payload"])
    with pytest.raises(ControllerError, match="REQUEST_CANONICAL_SHA_MISMATCH|REQUEST_NOT_FROZEN"):
        c.authorize("BLIND", altered, host=host, context=context)


@pytest.mark.parametrize("key,value", [("generation", "WRONG"), ("stage", "B2")], ids=["03", "04"])
def test_wrong_generation_stage_reject(blind, key, value):
    c, request, host, context = blind
    altered = {**request, key: value}
    with pytest.raises(ControllerError, match="REQUEST_GENERATION_OR_STAGE"):
        c.authorize("BLIND", altered, host=host, context=context)


def test_05_clean_without_failure_allowed(blind):
    c, request, host, context = blind
    auth = c.authorize("BLIND", request, host=host, context=context)
    assert auth["mode"] == Mode.CLEAN_START
    assert "failed_receipt_sha256" not in auth
    assert not list(c.root.rglob("*continuation*"))
    assert not list(c.root.rglob("*failed*"))


def test_06_clean_history_requirement_is_not_a_supported_input(tmp_path):
    with pytest.raises(TypeError, match="failed_ledger"):
        StrictBlindController.create(tmp_path/"bad", generation="new", plan={}, code_files=[],
                                     host_preparation={}, failed_ledger="historical")


def test_07_resume_without_failure_rejects(prepared):
    with pytest.raises(ControllerError, match="RESUME_FAILURE_RECEIPT_REQUIRED"):
        StrictBlindController.resume(prepared.root, expected_contract_sha256=prepared.contract_sha,
                                     failed_receipt_sha256=None)
    with pytest.raises(ControllerError, match="RESUME_LEDGER_REQUIRED"):
        StrictBlindController.resume(prepared.root, expected_contract_sha256=prepared.contract_sha,
                                     failed_receipt_sha256="not-present")


@pytest.mark.parametrize("transition,expected", [(False, "QUALIFIED"), (True, "QUALIFIED_ALLOWED_TRANSITION")],
                         ids=["08", "09"])
def test_native_host_unchanged_and_declared_transition(blind, transition, expected):
    c, request, _, _ = blind
    host, context, status = host_for(c, request, transition=transition)
    assert status == expected
    assert c.authorize("BLIND", request, host=host, context=context)["host_receipt"]["status"] == "PASS"


@pytest.mark.parametrize("case", ["undeclared", "disallowed", "missing_provenance"])
def test_10_host_unapproved_or_missing_provenance_rejects(blind, case):
    c, request, _, _ = blind
    inputs = host_inputs(c, request, transition=True)
    allowed = ["CODEX_SANDBOX"]
    if case == "undeclared":
        allowed = []
    elif case == "disallowed":
        inputs["context"]["safe_environment"]["SSL_CERT_FILE"] = {"present": True, "sha256": "drift"}
        inputs["entry_environment"] = inputs["context"]["safe_environment"]
    else:
        inputs["state_evidence"] = replace(inputs["state_evidence"], proof_sha256=None)
    with pytest.raises(ControllerError, match="DENIED_HOST_TRANSITION"):
        qualify_host(declared_transitions=allowed, **inputs)


def test_11_blind_cannot_read_ai_output(prepared):
    run_stage(prepared, "BLIND")
    run_stage(prepared, "MARKET")
    with pytest.raises(ControllerError, match="FORBIDDEN_CONTEXT_READ"):
        prepared.view("BLIND", ["outputs_MARKET"])


def test_12_ai_cannot_read_blind_content(prepared):
    run_stage(prepared, "BLIND")
    with pytest.raises(ControllerError, match="FORBIDDEN_CONTEXT_READ"):
        prepared.view("AI", ["outputs_BLIND"])
    assert set(prepared.blind_seal_receipt()) == {"sealed", "sha256"}


def test_13_source_call_after_source_seal_reject(prepared):
    with pytest.raises(ControllerError, match="SOURCE_COLLECTION_CLOSED"):
        prepared.admit_source("source-one", simulated=True)


def test_14_blind_rerun_after_seal_reject(blind):
    c, request, host, context = blind
    attempt(blind)
    c.seal_stage("BLIND")
    with pytest.raises(ControllerError, match="STAGE_ALREADY_SEALED"):
        c.authorize("BLIND", request, host=host, context=context)


def test_15_b2_rerun_after_seal_reject(prepared):
    for stage in ("BLIND", "MARKET", "CORE", "A", "B", "B2"):
        run_stage(prepared, stage)
    with pytest.raises(ControllerError, match="STAGE_ALREADY_SEALED"):
        prepared.seal_requests("B2", [])


def test_16_early_reveal_rejects(prepared):
    with pytest.raises(ControllerError, match="EARLY_REVEAL"):
        prepared.reveal()
    run_stage(prepared, "BLIND")
    with pytest.raises(ControllerError, match="EARLY_REVEAL"):
        prepared.reveal()


@pytest.mark.parametrize("stage", ["BLIND", "MARKET", "CORE", "A", "B", "B2"])
def test_17_schema_valid_semantic_reject_never_retryable(prepared, stage):
    from scripts.strict_blind_controller import MODEL_STAGES
    for prior in MODEL_STAGES[:MODEL_STAGES.index(stage)]:
        run_stage(prepared, prior)
    request = requests_for(prepared, stage)[0]
    prepared.seal_requests(stage, [request])
    host, context, _ = host_for(prepared, request)
    kwargs = dict(host=host, context=context, transport=lambda p: b'{}',
                  provider_validate=lambda v: True, semantic_validate=lambda v: False, simulated=True)
    receipt = prepared.attempt(stage, request, **kwargs)
    assert receipt["failure_class"] == failure.SEMANTIC and not receipt["retry_eligible"]
    with pytest.raises(ControllerError, match="TERMINAL_FAIL_STOP"):
        prepared.attempt(stage, request, **kwargs)


def test_18_adapter_registration_after_boundary_rejects(prepared):
    assert prepared.data["simulated_boundary_started"] and not prepared.data["strict_run_started"]
    with pytest.raises(ControllerError, match="ADAPTER_REGISTRATION_CLOSED"):
        prepared.register_adapter("late", __file__)


def test_19_result_dependent_continuation_rejects(prepared):
    prepared.contract["plan"]["continuation_exception"] = "observed-result"
    with pytest.raises(ControllerError, match="CONTRACT_DRIFT"):
        prepared.receipt()


def test_20_ticker_specific_exception_rejects(tmp_path):
    c, _, code = fixture(tmp_path)
    plan = deepcopy(c.contract["plan"])
    plan["stages"]["BLIND"][0]["ticker_exception"] = True
    with pytest.raises(ControllerError, match="TICKER_EXCEPTION"):
        StrictBlindController.create(tmp_path/"other", generation="another", plan=plan,
            code_files=[code], host_preparation=c.contract["host_preparation"])


def test_full_clean_start_lifecycle_zero_external_calls(tmp_path, monkeypatch):
    import socket
    import subprocess
    def deny(*args, **kwargs):
        pytest.fail("External process or network call in offline proof")
    monkeypatch.setattr(socket, "socket", deny)
    monkeypatch.setattr(subprocess, "Popen", deny)
    result = full_proof(tmp_path)
    assert result["states"] == list(STATES)
    assert result["controller"]["state"] == "COMPLETE"
    assert result["source_provider_model_calls"] == 0
    assert not result["controller"]["strict_run_started"]
    assert result["no_historical_failed_ledger_dependency"]
    ai = json.loads((tmp_path/"ai-workspace/context.json").read_bytes())
    assert "outputs_BLIND" not in encoded(ai).decode()


def test_real_retry_receipt_can_resume_same_request_only(blind):
    c, request, host, context = blind
    responses = iter([b'{malformed', b'{"synthetic":true}'])
    def transport(payload):
        return next(responses)
    receipt = attempt(blind, transport=transport)
    assert receipt["failure_class"] == failure.TRANSPORT and receipt["retry_eligible"]
    resumed = StrictBlindController.resume(c.root, expected_contract_sha256=c.contract_sha,
                                           failed_receipt_sha256=receipt["receipt_sha256"])
    assert resumed.data["mode"] == Mode.RESUME
    assert resumed.authorize("BLIND", request, host=host, context=context)["failed_receipt_sha256"]
    assert attempt((resumed, request, host, context), transport=transport)["status"] == "PASS"
    resumed.seal_stage("BLIND")


@pytest.mark.parametrize("kind", ["json", "schema", "transport"])
def test_only_existing_form_transport_taxonomy_retries(blind, kind):
    def transport(payload):
        raise failure.ResponseFormFailure("TIMEOUT")
    changes = dict(transport=lambda p: b'bad') if kind == "json" else (
        dict(provider_validate=lambda p: False) if kind == "schema" else dict(transport=transport))
    for _ in range(3):
        assert attempt(blind, **changes)["retry_eligible"]
    with pytest.raises(ControllerError, match="REQUEST_RETRY_CAP"):
        attempt(blind, **changes)


def test_unexpected_harness_failure_no_retry(blind):
    def broken(payload):
        raise RuntimeError("harness")
    receipt = attempt(blind, transport=broken)
    assert receipt["failure_class"] == failure.SYSTEMIC and not receipt["retry_eligible"]


def test_semantic_callback_cannot_launder_form_retry(blind):
    def invalid(value):
        raise failure.ResponseFormFailure("semantic mislabeled as form")
    receipt = attempt(blind, semantic_validate=invalid)
    assert receipt["provider_schema_status"] == "PASS"
    assert receipt["failure_class"] == failure.SEMANTIC and not receipt["retry_eligible"]


def test_raw_first_durable_before_any_validator(blind):
    c = blind[0]
    order = []
    def provider(value):
        assert len(list((c.root/"raw").glob("*.bin"))) == 1
        assert len(list((c.root/"artifacts").glob("*_raw.json"))) == 1
        assert json.loads(sorted((c.root/"journal").glob("*.json"))[-1].read_bytes())["event"] == "RAW_DURABLE_BEFORE_VALIDATION"
        order.append("provider")
        return True
    def semantic(value):
        assert order == ["provider"]
        order.append("semantic")
        return True
    assert attempt(blind, provider_validate=provider, semantic_validate=semantic)["status"] == "PASS"
    assert order == ["provider", "semantic"]


@pytest.mark.parametrize("target", ["contract", "artifact", "code", "memory", "journal"])
def test_frozen_inputs_and_state_drift_reject(prepared, target):
    c = prepared
    if target == "contract":
        (c.root/"contract.json").write_bytes(b'{}')
    elif target == "artifact":
        (c.root/"artifacts/source.json").write_bytes(b'{}')
    elif target == "code":
        path = c.root.parent/"synthetic-frozen-adapter.txt"
        assert path.is_relative_to(c.root.parent)
        path.write_bytes(b'drift')
    elif target == "memory":
        c.data["state"] = "PREFLIGHT"
    else:
        path = sorted((c.root/"journal").glob("*.json"))[-1]
        value = json.loads(path.read_bytes())
        value["event"] = "changed"
        path.write_bytes(encoded(value))
    with pytest.raises(ControllerError, match="DRIFT"):
        c.receipt()


def test_unapproved_extra_context_rejects(prepared):
    request = requests_for(prepared, "BLIND")[0]
    request["payload"]["input"]["hidden_ai"] = {"judgment": "target"}
    request["request_sha256"] = digest(request["payload"])
    with pytest.raises(ControllerError, match="UNDECLARED_MODEL_CONTEXT"):
        prepared.seal_requests("BLIND", [request])


def test_isolation_transitive_paths_and_no_nested_roots(prepared, tmp_path):
    c = prepared
    c.materialize_view("BLIND", ["blind_package"], tmp_path/"blind")
    with pytest.raises(ControllerError, match="AI_CONTEXT_BEFORE_BLIND_SEAL"):
        c.view("AI", ["source"])
    with pytest.raises(ControllerError, match="BLIND_REQUIRES_ALLOWLIST_PACKAGE"):
        c.view("BLIND", ["source"])
    run_stage(c, "BLIND")
    with pytest.raises(ControllerError, match="WORKSPACE_ROOT_OVERLAP"):
        c.materialize_view("AI", ["source"], tmp_path/"blind/nested")
    with pytest.raises(ControllerError, match="WORKSPACE_ROOT_OVERLAP"):
        c.materialize_view("AI", ["source"], c.root/"nested")
    (tmp_path/"link").symlink_to(tmp_path/"blind", target_is_directory=True)
    with pytest.raises(ControllerError, match="VIEW_SYMLINK|WORKSPACE_ROOT_OVERLAP"):
        c.materialize_view("AI", ["source"], tmp_path/"link/nested")


def test_source_cannot_start_without_every_authority(tmp_path):
    c, authorities, _ = fixture(tmp_path)
    with pytest.raises(ControllerError, match="SOURCE_COLLECTION_CLOSED"):
        c.admit_source("source-one", simulated=True)
    del authorities["acceptance"]
    with pytest.raises(ControllerError, match="PRE_PROVIDER_AUTHORITIES_INCOMPLETE"):
        c.seal_pre_source(authorities)


def test_offline_mode_cannot_admit_external_source_or_model(blind):
    c, request, host, context = blind
    with pytest.raises(ControllerError, match="OFFLINE_EXTERNAL_DISPATCH_DENIED"):
        c.admit_source("source-one")
    with pytest.raises(ControllerError, match="OFFLINE_EXTERNAL_DISPATCH_DENIED"):
        c.attempt("BLIND", request, host=host, context=context, transport=lambda p: pytest.fail(),
                  provider_validate=lambda v: True, semantic_validate=lambda v: True)


def test_missing_causal_stage_and_backwards_transition_reject(prepared):
    with pytest.raises(ControllerError, match="PREREQUISITE_OUTPUT_MISSING"):
        prepared.seal_requests("B2", [])
    with pytest.raises(ControllerError, match="ILLEGAL_STATE_TRANSITION"):
        prepared._advance("PREFLIGHT")


def test_valid_request_requires_matching_native_host_identity(blind):
    c, request, host, context = blind
    altered = replace(host, identity=replace(host.identity, source_generation_id="wrong"))
    with pytest.raises(ControllerError, match="HOST_REQUEST_BINDING_GAP"):
        c.authorize("BLIND", request, host=altered, context=context)
    with pytest.raises(ControllerError, match="NATIVE_HOST_REQUIRED"):
        c.authorize("BLIND", request, host={"status": "PASS"}, context=context)


def test_non_json_keys_nan_and_aliasing_reject():
    with pytest.raises(ControllerError, match="NON_JSON_OBJECT_KEY"):
        canonical({1: "bad"})
    with pytest.raises(ValueError):
        canonical({"bad": float("nan")})
    value = {"nested": [1, 2]}
    clone = canonical(value)
    clone["nested"].clear()
    assert value["nested"] == [1, 2]


def native_b2_projection(view):
    from scripts import newbuyer_b2_v2_shadow as b2
    inputs = view["outputs_B"][0]["output"]["native_b2_inputs"]
    request = b2.build_request(**inputs)
    return b2.provider_payload(request, expected_request_sha256=request["request_sha256"])


def test_existing_b2_native_payload_is_byte_preserved(tmp_path):
    from scripts import newbuyer_b2_v2_shadow as b2
    from tests.test_newbuyer_b2_v2 import inputs
    synthetic = inputs()
    subject = synthetic["v1_request"]["subject"]
    c, authorities, code = fixture(tmp_path, extra_code_files=[__file__, b2.__file__],
        generation=subject["source_generation_id"], subjects=[subject["ticker"]])
    c.register_adapter("native_b2", __file__, function_name="native_b2_projection")
    source_phase(c, authorities, code)
    for stage in ("BLIND", "MARKET", "CORE", "A"):
        run_stage(c, stage)
    request = requests_for(c, "B")[0]
    c.seal_requests("B", [request])
    host, context, _ = host_for(c, request)
    native_request = b2.build_request(**synthetic)
    native = b2.provider_payload(native_request, expected_request_sha256=native_request["request_sha256"])
    c.attempt("B", request, host=host, context=context, simulated=True,
        transport=lambda p: encoded({"native_b2_inputs": synthetic}),
        provider_validate=lambda v: True, semantic_validate=lambda v: True)
    c.seal_stage("B")
    projected = c.project_request("B2", 0, parents=["outputs_B"],
                                  adapter="native_b2", builder=native_b2_projection)
    assert encoded(projected["payload"]) == encoded(native)
    c.seal_requests("B2", [projected])
    host, context, _ = host_for(c, projected)
    assert c.authorize("B2", projected, host=host, context=context)
    assert "LEGACY CONFIDENCE PROSE" not in encoded(projected["payload"]).decode()
    with pytest.raises(ControllerError, match="FORBIDDEN_CONTEXT_READ"):
        c.view("BLIND", ["view_B2_0"])


@pytest.mark.parametrize("role", ["transport", "provider_validate", "semantic_validate"])
def test_dispatch_callbacks_must_belong_to_predeclared_frozen_code(blind, role):
    namespace = {}
    exec(compile("def undeclared(value): return True", "unfrozen_adapter.py", "exec"), namespace)
    with pytest.raises(ControllerError, match="UNFROZEN_CALLBACK"):
        attempt(blind, **{role: namespace["undeclared"]})
    assert not blind[0].data["attempts"] and blind[0].data["active_attempt"] is None


def test_retry_cannot_switch_even_between_preexisting_callback_functions(blind):
    def first(payload):
        return b'bad'
    def replacement(payload):
        return b'{}'
    assert attempt(blind, transport=first)["retry_eligible"]
    with pytest.raises(ControllerError, match="RETRY_CALLBACK_DRIFT"):
        attempt(blind, transport=replacement)
