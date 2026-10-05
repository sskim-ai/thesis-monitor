"""Synthetic-only complete controller exercise, not investment/model qualification."""
from __future__ import annotations

from copy import deepcopy
from dataclasses import asdict
import json
from pathlib import Path

from app.services.unified_run_artifacts import durable_json
from app.services.unified_snapshot_contract import digest, encoded
from scripts import qualified_official_launch_context as native
from scripts.strict_blind_controller import (
    AUTHORITIES, MARKET_CONTRACTS, MODEL_STAGES, RequestScope, StrictBlindController,
    qualify_host, request_identity,
)


def fixture(root, *, extra_code_files=(), generation="SYNTHETIC-OFFLINE-ONLY", subjects=None,
            market_slots=None):
    root = Path(root)
    code = root / "synthetic-frozen-adapter.txt"
    code.parent.mkdir(parents=True, exist_ok=True)
    code.write_bytes(b"synthetic no external execution\n")
    stages = {stage: [dict(logical_id=f"fixture:{stage}:one", subjects=subjects or ["SYN_A", "SYN_B"],
                         batch=1, scope=RequestScope.SUBJECT, market="US", native_market_contract=None)]
              for stage in MODEL_STAGES}
    stages["MARKET"] = market_slots or [dict(logical_id="fixture:MARKET:US", subjects=[], batch=1,
        scope=RequestScope.MARKET, market="US", native_market_contract=MARKET_CONTRACTS["US"])]
    plan = dict(stages=stages, source_slots=["source-one"], model="gpt-5.6-sol", effort="xhigh",
                timeout_seconds=600, retries=2, caps={stage: 30 for stage in MODEL_STAGES})
    environment = {"CODEX_SANDBOX": {"present": True, "sha256": digest("native")},
                   "SSL_CERT_FILE": {"present": False, "sha256": None}}
    preparation = dict(uid=1, gid=2, state_access=dict(uid=1, gid=2, mode="600", path_sha256="state"),
                       home_access={"path_sha256": "home"}, codex_home_access={"path_sha256": "codex"},
                       safe_environment=environment)
    controller = StrictBlindController.create(root/"controller", generation=generation,
        plan=plan, code_files=[code, Path(__file__), Path(__file__).with_name("strict_blind_controller.py"),
                              *extra_code_files],
        host_preparation=preparation, declared_host_transitions=["CODEX_SANDBOX"])
    controller.register_adapter("synthetic_market", __file__, function_name="synthetic_market_projection")
    authorities = {name: {"fixture_only": True, "authority": name} for name in AUTHORITIES}
    authorities["execution_plan"] = plan
    authorities["source_dag"] = {"slots": plan["source_slots"]}
    return controller, authorities, code


def source_phase(controller, authorities, code):
    controller.register_adapter("synthetic", code)
    controller.seal_pre_source(authorities)
    controller.admit_source("source-one", simulated=True)
    source = dict(generation=controller.generation, facts=[dict(ref="synthetic-fact", value=7)])
    controller.seal_source(source, dict(generation=controller.generation, status="PASS",
        source_sha256=digest(source), owner_metric_evaluability="SYNTHETIC_GATE_ONLY"))
    controller.seal_blind_package(source, validate_source_only=lambda p, s: p == s)


def synthetic_market_projection(view):
    return dict(prompt="Synthetic lifecycle receipt only; no economic judgment.",
        response_schema={"type": "object", "required": ["synthetic"]}, input=dict(market="US", source=view))


def requests_for(controller, stage):
    if stage == "MARKET":
        return [controller.project_request(stage, 0, parents=["source", "owner"],
            adapter="synthetic_market", builder=synthetic_market_projection)]
    names = ["blind_package", "blind_rubric", "blind_schema", "blind_prompt", "comparison", "acceptance"]
    if stage != "BLIND":
        names = ["source", "owner"] + [f"outputs_{s}" for s in MODEL_STAGES[1:MODEL_STAGES.index(stage)]]
    view = controller.view("BLIND" if stage == "BLIND" else "AI", names)
    payload = dict(prompt="Synthetic lifecycle receipt only; no economic judgment.",
                   response_schema={"type": "object", "required": ["synthetic"]}, input=view)
    policy = "blind_controller_policy" if stage == "BLIND" else "monitoring_controller_policy"
    return [request_identity(generation=controller.generation, stage=stage,
        scope=slot["scope"], market=slot["market"], native_market_contract=slot["native_market_contract"],
        logical_id=slot["logical_id"], subjects=tuple(slot["subjects"]), batch=slot["batch"], payload=payload,
        prompt_sha256=digest(payload["prompt"]), schema_sha256=digest(payload["response_schema"]),
        policy_sha256=controller.data["artifacts"][policy]["sha256"],
        context_refs={n: controller.data["artifacts"][n]["sha256"] for n in names})
        for slot in controller.contract["plan"]["stages"][stage]]


def host_inputs(controller, request, *, transition=False):
    """All host evidence is synthetic; no official state or CLI is opened."""
    code_hash = next(iter(controller.contract["code"].values()))
    identity = native.LaunchIdentity(implementation_sha=digest(controller.contract["code"]),
        source_generation_id=controller.generation,
        whole_source_sha256=controller.data["artifacts"]["source"]["sha256"],
        source_only_zip_sha256=controller.data["artifacts"]["blind_package"]["sha256"],
        request_freeze_sha256=digest(request),
        prompt_schema_sha256=digest({k: request[k] for k in
            ("prompt_sha256", "schema_sha256", "policy_sha256")}),
        executable_sha256=code_hash, launcher_sha256=code_hash,
        qualification_sha256=controller.contract_sha, cwd_sha256=digest("synthetic-cwd"),
        timeout_seconds=600, max_calls=10, retries=2)
    preparation = deepcopy(controller.contract["host_preparation"])
    env = deepcopy(preparation["safe_environment"])
    if transition:
        env["CODEX_SANDBOX"] = {"present": False, "sha256": None}
    context = dict(at="SYNTHETIC-TIME", pid=123, uid=1, gid=2, home_sha256="home",
        codex_home_sha256="codex", state_path_sha256="state", state_owner_mode=[1, 2, 0o600],
        safe_environment=env, cwd_sha256=identity.cwd_sha256, state_read_ready=True,
        state_probe_write_calls=0, state_permissions_modified=False)
    return dict(identity=identity, expected_identity=identity, preparation=preparation,
        preparation_sha256=native.digest(preparation), actual_preparation_sha256=native.digest(preparation),
        context=context, entry_environment=deepcopy(env),
        state_evidence=native.StateWriteEvidence("PARENT_AND_OFFICIAL_CHILD", 0, 0,
            digest("synthetic-state-proof-not-live"), code_hash, code_hash),
        binding_verified=True, provider_calls=0, secret_scan_passed=True)


def host_for(controller, request, *, transition=False):
    inputs = host_inputs(controller, request, transition=transition)
    host, status = qualify_host(declared_transitions=controller.contract["declared_host_transitions"],
                                **inputs)
    return host, inputs["context"], status


def run_stage(controller, stage, *, transition=False):
    requests = requests_for(controller, stage)
    controller.seal_requests(stage, requests)
    rows = []
    for request in requests:
        host, context, status = host_for(controller, request, transition=transition)
        auth = controller.authorize(stage, request, host=host, context=context)
        validation_order = []
        def provider(output):
            captures = [p for p in (controller.root/"artifacts").glob("*_raw.json")]
            assert captures and list((controller.root/"raw").glob("*.bin"))
            validation_order.append("PROVIDER_SCHEMA_AFTER_DURABLE_RAW")
            return output == {"synthetic": stage}
        def semantic(output):
            assert validation_order == ["PROVIDER_SCHEMA_AFTER_DURABLE_RAW"]
            validation_order.append("LOCAL_SEMANTIC_AFTER_PROVIDER_SCHEMA")
            return True
        receipt = controller.attempt(stage, request, host=host, context=context,
            transport=lambda payload: encoded({"synthetic": stage}),
            provider_validate=provider, semantic_validate=semantic, simulated=True)
        auth = controller._value(f"attempt_{stage}_{len(rows)}_authorization")
        rows.append(dict(authorization=auth, host_status=status, host_identity=asdict(host.identity),
                         attempt=receipt, validation_order=validation_order))
    controller.seal_stage(stage)
    return rows


def full_proof(root):
    root = Path(root)
    controller, authorities, code = fixture(root)
    source_phase(controller, authorities, code)
    blind_view = controller.materialize_view("BLIND", ["blind_package", "blind_rubric", "blind_schema",
        "blind_prompt", "comparison", "acceptance"], root/"blind-workspace")
    stages = {}
    for stage in MODEL_STAGES:
        stages[stage] = run_stage(controller, stage)
    ai_view = controller.materialize_view("AI", ["source", "owner", "outputs_B"], root/"ai-workspace")
    revealed = controller.reveal()
    controller.complete(dict(synthetic=True, compared_stages=list(revealed)),
        validate_comparison=lambda result, comparison, acceptance: bool(result["synthetic"]
            and comparison["fixture_only"] and acceptance["fixture_only"]))
    events = [json.loads(p.read_bytes()) for p in sorted((controller.root/"journal").glob("*.json"))]
    states = list(dict.fromkeys(r["data"]["state"] for r in events))
    result = dict(status="PASS", scope="SYNTHETIC_OFFLINE_LIFECYCLE_NOT_LIVE_QUALIFICATION",
        controller=controller.receipt(), states=states, stages=stages,
        isolation=dict(blind=blind_view, ai=ai_view, distinct_roots=True,
                       blind_content_not_in_ai_view=True, OS_sandbox_claimed=False),
        no_historical_failed_ledger_dependency=True, source_provider_model_calls=0,
        official_cli_calls=0, production_side_effects=0)
    durable_json(root/"clean-start-e2e-dry-run.json", result, exclusive=True)
    return result


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("destination", type=Path)
    args = parser.parse_args()
    from scripts.sealed_cohort_offline_proof import network_guard
    network_guard()
    print(full_proof(args.destination)["status"])
