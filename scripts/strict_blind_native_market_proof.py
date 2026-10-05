"""Offline native US/KR Market integration proof. No provider/model dispatch."""
from copy import deepcopy
import json
from pathlib import Path
from tempfile import TemporaryDirectory

from app.services.unified_run_artifacts import durable_json
from app.services.unified_snapshot_contract import digest, encoded
from scripts import m12ds_r4_r4_market as market_owner
from scripts.r9_rev11_models import owner
from scripts.rev46_kr_models import Rev46Kr8Execution
from scripts.us14_models import Us14Execution
from scripts.strict_blind_controller import MARKET_CONTRACTS, RequestScope
from scripts.strict_blind_offline_proof import fixture, host_for, run_stage


def packet(market):
    # Invented, empty source: absence is explicit, never a live market assertion.
    return dict(market=market.lower(), assessment_date="2026-01-02",
        market_context=dict(fact_catalog=[], adapter_context={},
                            session=dict(latest_completed_regular_session_date="2026-01-02")))


def capture(root, market, context, generation):
    cls = Us14Execution if market == "US" else Rev46Kr8Execution
    execution = cls.__new__(cls)
    execution.requests = Path(root)
    execution.gen = execution.source_gen = generation
    receipt = execution.capture("market", dict(market=market.lower(), batch=1, subjects=[]),
        deepcopy(context), market_owner.market_schema(context), market_owner.PROMPT)
    path = Path(receipt["directory"])
    payload = dict(prompt=(path/"prompt.txt").read_text(), input=json.loads((path/"subject-context.json").read_bytes()),
                   response_schema=json.loads((path/"provider-wire-schema.json").read_bytes()))
    return payload, receipt


def projected_market(view, market):
    source = view["source"]
    context = market_owner.market_context(source["markets"][market])
    with TemporaryDirectory(prefix="strict-native-market-") as root:
        return capture(root, market, context, source["generation"])[0]


def us_market_payload(view):
    return projected_market(view, "US")


def kr_market_payload(view):
    return projected_market(view, "KR")


def native_prepared(root, *, extra_code_files=()):
    slots = [dict(logical_id=f"native:MARKET:{market}", subjects=[], batch=1,
        scope=RequestScope.MARKET, market=market, native_market_contract=MARKET_CONTRACTS[market])
        for market in ("US", "KR")]
    controller, authorities, code = fixture(root, extra_code_files=[__file__, *extra_code_files],
        market_slots=slots)
    for market, builder in (("US", us_market_payload), ("KR", kr_market_payload)):
        controller.register_adapter(market, __file__, function_name=builder.__qualname__)
    controller.register_adapter("synthetic", code)
    controller.seal_pre_source(authorities)
    controller.admit_source("source-one", simulated=True)
    source = dict(generation=controller.generation, markets={m: packet(m) for m in ("US", "KR")})
    controller.seal_source(source, dict(generation=controller.generation, source_sha256=digest(source), status="PASS"))
    controller.seal_blind_package(source, validate_source_only=lambda p, s: p == s)
    return controller


def market_requests(controller):
    return [controller.project_request("MARKET", index, parents=["source"], adapter=market, builder=builder)
        for index, (market, builder) in enumerate((("US", us_market_payload), ("KR", kr_market_payload)))]


def response(market):
    return dict(market=market, regime="DATA_INSUFFICIENT", confidence="LOW",
        breadth_state="Unavailable", leadership="Unavailable", flows_or_participation="Unavailable",
        rates_or_macro_context="Unavailable", supporting_refs=[], contradicting_refs=[])


def full_native_proof(root):
    root = Path(root)
    controller = native_prepared(root)
    blind_view = controller.materialize_view("BLIND", ["blind_package"], root/"blind-workspace")
    run_stage(controller, "BLIND")
    requests = market_requests(controller)
    controller.seal_requests("MARKET", requests)
    reports = []
    for request in requests:
        market = request["market"]
        context = market_owner.market_context(packet(market))
        native, capture_receipt = capture(root/"native-baseline"/market, market, context, controller.generation)
        assert encoded(native) == encoded(request["payload"])
        assert digest(native) == request["request_sha256"]
        host, host_context, _ = host_for(controller, request)
        detached = json.loads(encoded(request))
        detached["subjects"] = tuple(detached["subjects"])
        authorization = controller.authorize("MARKET", detached, host=host, context=host_context)
        order = []

        def simulated_transport(body):
            assert body == encoded(native)
            return encoded(response(market))

        def provider_validate(output):
            latest = json.loads(sorted((controller.root/"journal").glob("*.json"))[-1].read_bytes())
            assert latest["event"] == "RAW_DURABLE_BEFORE_VALIDATION"
            assert encoded(output) in [p.read_bytes() for p in (controller.root/"raw").glob("*.bin")]
            order.append("PROVIDER_SCHEMA_AFTER_DURABLE_RAW")
            return not owner.validate_json_schema(output, native["response_schema"])

        def semantic_validate(output):
            assert order == ["PROVIDER_SCHEMA_AFTER_DURABLE_RAW"]
            order.append("NATIVE_LOCAL_SEMANTICS_AFTER_PROVIDER_SCHEMA")
            return (not owner.validate_json_schema(output, market_owner.market_schema(context))
                    and market_owner.validate_market(output, context)["status"] == "PASS")

        receipt = controller.attempt("MARKET", detached, host=host, context=host_context,
            transport=simulated_transport, provider_validate=provider_validate,
            semantic_validate=semantic_validate, simulated=True)
        assert receipt["status"] == "PASS"
        report = dict(status="PASS", market=market, subjects=[], scope=RequestScope.MARKET,
            native_contract=MARKET_CONTRACTS[market], native_capture=capture_receipt,
            native_payload_sha256=digest(native), controller_payload_sha256=request["request_sha256"],
            canonical_envelope_sha256=digest(request), bytes_unchanged=True, fake_subject=False,
            authorization=authorization, raw_first_validation_order=order, attempt=receipt,
            historical_failed_ledger_required=False, live_host_qualification=False,
            native_provider_and_semantic_validators=True)
        reports.append(report)
    controller.seal_stage("MARKET")
    for stage in ("CORE", "A", "B", "B2"):
        run_stage(controller, stage)
    ai_view = controller.materialize_view("AI", ["source", "outputs_B"], root/"ai-workspace")
    revealed = controller.reveal()
    controller.complete(dict(synthetic=True, stages=list(revealed)),
        validate_comparison=lambda result, comparison, acceptance: bool(result["synthetic"]
            and comparison["fixture_only"] and acceptance["fixture_only"]))
    for report in reports:
        report["output_seal_unlocked_core_and_remaining_stages"] = controller.state == "COMPLETE"
        durable_json(root/f"native-{report['market'].lower()}-market-controller-parity.json", report, exclusive=True)
    events = [json.loads(p.read_bytes()) for p in sorted((controller.root/"journal").glob("*.json"))]
    proof = dict(status="PASS", scope="NATIVE_MARKET_OFFLINE_SYNTHETIC_SOURCE_AND_RESPONSE_ONLY",
        controller=controller.receipt(), states=list(dict.fromkeys(e["data"]["state"] for e in events)),
        markets=reports, isolation=dict(blind=blind_view, ai=ai_view, OS_sandbox_claimed=False),
        source_provider_model_calls=0, official_cli_calls=0, production_side_effects=0)
    durable_json(root/"native-clean-start-e2e-dry-run.json", proof, exclusive=True)
    return proof


if __name__ == "__main__":
    import argparse
    from scripts.sealed_cohort_offline_proof import network_guard
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("destination", type=Path)
    args = parser.parse_args()
    network_guard()
    print(full_native_proof(args.destination)["status"])
