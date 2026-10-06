"""Source-owner fixtures, not historical reports or desired issuer decisions."""
from copy import deepcopy

import pytest

from app.services.provider_valuation_calibration_context import calibration_context
from app.services.unified_snapshot_contract import digest, encoded
from scripts import strict_blind_adapter as adapter
from scripts import strict_blind_contract as blind
from scripts import strict_blind_monitoring as monitoring
from scripts.newbuyer_b2_v2_coverage import SourceOwners
from scripts.r2b_r9_full_fresh_requalification import prepare_fresh_subject
from scripts.strict_blind_controller import StrictBlindController, ControllerError
from scripts.strict_blind_offline_proof import fixture, host_for
from tests.test_completed_price_state import unavailable_inputs
from tests.test_newbuyer_b2_v2_coverage import compose


def source_case(tmp_path, monkeypatch, *, kind="integrity", native=True):
    from scripts import r2b_r5_market_adapter
    inputs = unavailable_inputs(tmp_path / "source", "IBM", kind, native=native)
    generation = "FICTIONAL-UNAVAILABLE-BLIND"
    result = prepare_fresh_subject(inputs, execution_generation_id=generation)
    assert result["readiness"]["status"] == "PASS"
    stock = result["stock"]
    owner = SourceOwners(generation=stock["fresh_run_id"], stock=stock,
        security=inputs["financial_inputs"]["plan"]["security"],
        collection_receipt_sha256=digest("fictional-source-collection"))
    coverage = compose(owner)
    whole = dict(packets={"us": {"stocks": {stock["ticker"]: stock}}},
        authority_graph={"stocks": {stock["ticker"]: result["authority"]}},
        seed={"parent_run_id": stock["fresh_run_id"]}, authority_graph_sha256=digest(result["authority"]))
    # This subject-boundary test leaves unrelated market projection to its own suite.
    monkeypatch.setattr(r2b_r5_market_adapter, "project_sealed_market_context", lambda *a, **k: {})
    before = deepcopy(whole)
    native_source, selected = monitoring.from_sources(whole=whole,
        local_seeds={stock["ticker"]: inputs["technical_inputs"]["local_seed"]},
        valuation_contexts={stock["ticker"]: calibration_context(stock["valuation_view"])},
        generation=generation, coverage=coverage["coverage"], census=coverage["census"])
    assert whole == before and native_source["stocks"][stock["ticker"]] == stock
    return selected[stock["ticker"]], result, generation


def output(subject, audit):
    denied = audit["evaluability"]["evaluability_state"] == "ALL_RELEVANT_METRICS_UNUSABLE"
    values = dict(overall_direction="HOLD", new_buyer="WAIT", entry_timing="UNRESOLVED",
        holder="HOLDABLE", active_material_risk=False,
        valuation_evaluability=audit["evaluability"]["evaluability_state"],
        valuation_state="UNRESOLVED" if denied else "NEUTRAL")
    refs = {k: v[:1] for k, v in subject["axis_eligible_refs"].items()}
    refs["valuation_evaluability"] = (audit["evaluability"]["relevant_valuation_metric_refs"]
        if denied else audit["evaluability"]["usable_valuation_metric_refs"][:1])
    return dict(contract=blind.CONTRACT, **{k: subject[k] for k in
        ("generation", "source_generation_id", "ticker", "security_id")},
        subject_sha256=digest(subject), axes={k: dict(judgment=v, evidence_refs=refs[k],
            rationale="Fictional boundary probe only.", confidence="LOW") for k, v in values.items()})


@pytest.mark.parametrize("kind", ["integrity", "missing", "field_missing", "transport", "http", "provider_failed"])
@pytest.mark.parametrize("native", [False, True])
def test_typed_unavailable_price_preserves_independent_metrics(tmp_path, monkeypatch, kind, native):
    inp, original, generation = source_case(tmp_path, monkeypatch, kind=kind, native=native)
    state = original["stock"]["current_price_state"]
    assert original["prepared"]["subject"]["current_price"] is None
    assert inp["current_price"]["value"] is None and inp["current_price"]["ref_id"] is None
    assert inp["current_price"]["price_state_ref"] == state["receipt_sha256"]
    assert inp["current_price"]["availability"] == state["state"]
    subject, audit = blind.project_subject(inp, generation=generation)
    assert not audit["timing_options"] and not subject["tactical_candidates"]
    assert audit["evaluability"]["evaluability_state"] == (
        "EVALUABLE" if native else "ALL_RELEVANT_METRICS_UNUSABLE")
    raw = output(subject, audit)
    assert blind.validate_output(raw, subject, audit)["status"] == "PASS"
    raw["axes"]["entry_timing"]["judgment"] = "FAVORABLE_NOW"
    failed = blind.validate_output(raw, subject, audit)
    assert failed["status"] == "FAIL" and not failed["retryable"]
    assert "TIMING_WITHOUT_OWNED_RANGE_RELATION" in failed["errors"]


def test_available_price_assembly_bytes_unchanged(tmp_path, monkeypatch):
    inp, original, _ = source_case(tmp_path, monkeypatch, kind="available")
    assert encoded(inp["current_price"]) == encoded(original["prepared"]["subject"]["current_price"])


@pytest.mark.parametrize("bad", ["receipt", "context", "ticker", "numeric"])
def test_shared_missing_price_binding_remains_fail_closed(tmp_path, monkeypatch, bad):
    from app.services.unavailable_price_valuation import shadow_request_context
    _, original, _ = source_case(tmp_path, monkeypatch)
    stock, context = deepcopy(original["stock"]), deepcopy(original["prepared"]["subject"])
    if bad == "receipt":
        stock["current_price_state"]["receipt_sha256"] = "0" * 64
    elif bad == "context":
        stock["packet"]["stocks"][0]["current_price_context"]["price_state"] = {}
    elif bad == "ticker":
        context["ticker"] = "WRONG_SECURITY"
    else:
        context["current_price"] = {"value": 100}
    with pytest.raises(ValueError, match="unavailable_price_input_mismatch"):
        shadow_request_context(context, stock)


def test_unavailable_source_blind_controller_raw_seal_and_isolation(tmp_path, monkeypatch):
    inp, _, generation = source_case(tmp_path, monkeypatch)
    old, _, code = fixture(tmp_path / "host", subjects=[inp["ticker"]])
    c = StrictBlindController.create(tmp_path / "controller", generation=generation,
        plan=old.contract["plan"], host_preparation=old.contract["host_preparation"],
        declared_host_transitions=["CODEX_SANDBOX"],
        code_files=[code, __file__, adapter.__file__, blind.__file__, monitoring.__file__])
    adapter.register(c)
    c.seal_pre_source(adapter.authorities(c.contract["plan"], dict(slots=c.contract["plan"]["source_slots"])))
    c.admit_source("source-one", simulated=True)
    source = dict(generation=generation, blind_inputs={inp["ticker"]: inp})
    c.seal_source(source, dict(status="PASS", generation=generation, source_sha256=digest(source)))
    c.seal_blind_package(blind.package(source), validate_source_only=blind.validate_package)
    request = adapter.build_requests(c)[0]
    c.seal_requests("BLIND", [request])
    validation = adapter.BlindValidation(request, inp)
    raw = output(validation.subject, validation.audit)
    host, context, _ = host_for(c, request)
    result = c.attempt("BLIND", request, host=host, context=context,
        transport=lambda payload: encoded(raw), provider_validate=validation.provider,
        semantic_validate=validation.semantic, simulated=True)
    assert result["status"] == "PASS"
    c.seal_stage("BLIND")
    with pytest.raises(ControllerError, match="FORBIDDEN_CONTEXT_READ"):
        c.view("AI", ["outputs_BLIND"])
    assert not c.data["strict_run_started"]
