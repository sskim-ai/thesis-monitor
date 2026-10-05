"""Opt-in strict-blind orchestration. No provider, model, or production entry point.

Economic builders/validators remain caller-owned frozen code. This controller owns
admission, immutable receipts, and declared input views, not OS process isolation.
"""
from __future__ import annotations

from copy import deepcopy
from dataclasses import asdict
from enum import StrEnum
import inspect
import json
from pathlib import Path

from app.services.unified_run_artifacts import durable_bytes, durable_json, sha256_bytes
from app.services.unified_snapshot_contract import digest, encoded
from scripts import qualified_official_launch_context as native
from scripts import scoped_attempt_failure as failure

SERIALIZATION = "canonical-json-utf8-sorted-v1"
STATES = (
    "PREFLIGHT", "PRE_SOURCE_AUTHORITIES_SEALED", "SOURCE_COLLECTION",
    "SOURCE_COLLECTION_SEALED", "BLIND_PACKAGE_SEALED", "BLIND_JUDGMENT_EXECUTION",
    "BLIND_JUDGMENTS_SEALED", "UPSTREAM_EXECUTION", "UPSTREAM_AUTHORITY_SEALED",
    "B2_REQUESTS_SEALED", "B2_EXECUTION", "B2_OUTPUTS_SEALED", "REVEAL_COMPARISON", "COMPLETE",
)
MODEL_STAGES = ("BLIND", "MARKET", "CORE", "A", "B", "B2")
MARKET_CONTRACTS = {"US": "US14_NATIVE_MARKET_CAPTURE", "KR": "KR8_NATIVE_MARKET_CAPTURE"}
NATIVE_MARKET_FILES = (
    "us14_models.py", "rev46_kr_models.py", "kr8_fy1_models.py", "r9_rev11_models.py",
    "m12ds_r2_shadow_reproof.py", "m12ds_r4_r4_market.py", "m12ds_r4_r1_market.py",
    "m12ds_r3_market.py", "m12ds_r2_market.py",
)
AUTHORITIES = frozenset({"blind_rubric", "blind_schema", "blind_prompt", "comparison",
    "acceptance", "blind_controller_policy", "monitoring_controller_policy",
    "execution_plan", "source_dag"})
BLIND_KINDS = frozenset({"source", "blind_package", "blind_rubric", "blind_schema",
                        "blind_prompt", "comparison", "acceptance", "blind_request_view"})
AI_KINDS = frozenset({"source", "owner", "upstream", "ai_contract", "ai_request_view"})


class Mode(StrEnum):
    CLEAN_START = "CLEAN_START"
    RESUME = "RESUME_AFTER_RETRYABLE_EXECUTION_FAILURE"


class RequestScope(StrEnum):
    MARKET = "MARKET_SCOPED"
    SUBJECT = "SUBJECT_SCOPED"


class ControllerError(ValueError):
    pass


def require(condition, code):
    if not condition:
        raise ControllerError(code)


def canonical(value):
    """Use the existing persisted JSON serializer, never Python container equality."""
    def check(item):
        if isinstance(item, dict):
            require(all(isinstance(k, str) for k in item), "NON_JSON_OBJECT_KEY")
            for child in item.values():
                check(child)
        elif isinstance(item, (list, tuple)):
            for child in item:
                check(child)
    check(value)
    return json.loads(encoded(value))


def validate_scope(*, stage, scope, market, subjects, native_market_contract):
    require(stage in MODEL_STAGES and market in MARKET_CONTRACTS, "REQUEST_SCOPE_OR_MARKET_GAP")
    require(isinstance(subjects, (list, tuple)), "SUBJECT_SEQUENCE_REQUIRED")
    if stage == "MARKET":
        require(scope == RequestScope.MARKET and not subjects, "MARKET_SCOPE_OR_FAKE_SUBJECT")
        require(native_market_contract == MARKET_CONTRACTS[market], "NATIVE_MARKET_CONTRACT_MISMATCH")
    else:
        require(scope == RequestScope.SUBJECT and subjects and native_market_contract is None,
                "SUBJECT_SCOPE_REQUIRED")
        require(all(isinstance(t, str) and t for t in subjects)
                and len(set(subjects)) == len(subjects), "SUBJECT_IDENTITY_GAP")


def request_identity(*, generation, stage, scope, market, native_market_contract,
                     logical_id, subjects, batch, payload,
                     prompt_sha256, schema_sha256, policy_sha256, context_refs):
    require(stage in MODEL_STAGES and generation and logical_id,
            "REQUEST_IDENTITY_INCOMPLETE")
    validate_scope(stage=stage, scope=scope, market=market, subjects=subjects,
                   native_market_contract=native_market_contract)
    if stage == "MARKET":
        require(payload.get("input", {}).get("market") == market, "MARKET_PAYLOAD_IDENTITY_MISMATCH")
    value = canonical(dict(serialization=SERIALIZATION, generation=generation, stage=stage,
        scope=scope, market=market, native_market_contract=native_market_contract,
        logical_id=logical_id, subjects=subjects, batch=batch, payload=payload,
        request_sha256=sha256_bytes(encoded(payload)), prompt_sha256=prompt_sha256,
        schema_sha256=schema_sha256, policy_sha256=policy_sha256, context_refs=context_refs))
    require(all(len(value[k]) == 64 for k in
                ("prompt_sha256", "schema_sha256", "policy_sha256")), "CONTRACT_DIGEST_MISSING")
    return value


def qualify_host(*, declared_transitions, **inputs):
    """Native owner remains authoritative; a difference is never required."""
    require(set(declared_transitions) <= native.ALLOWED_TRANSITION, "DENIED_HOST_TRANSITION")
    try:
        result = native.QualifiedOfficialModelLaunchContext.qualify(**inputs)
    except (native.LaunchQualificationError, KeyError, TypeError, ValueError) as exc:
        raise ControllerError("DENIED_HOST_TRANSITION_OR_PROVENANCE") from exc
    require(set(result.transition_differences) <= set(declared_transitions),
            "DENIED_HOST_TRANSITION")
    return result, ("QUALIFIED_ALLOWED_TRANSITION" if result.transition_differences else "QUALIFIED")


class StrictBlindController:
    """Single writer, append-only journal. Resume only a recorded retryable attempt.

    Model adapters must consume materialized views, not the private journal root.
    A future live runner must separately prove its process/tool surface isolation.
    """

    @classmethod
    def create(cls, root, *, generation, plan, code_files, host_preparation,
               declared_host_transitions=(), offline=True):
        root = Path(root)
        require(not root.exists(), "CLEAN_ROOT_REQUIRED")
        plan = canonical(plan)
        require(set(plan) == {"stages", "source_slots", "model", "effort", "timeout_seconds",
                             "retries", "caps"}, "PLAN_UNKNOWN_OR_RESULT_DEPENDENT_POLICY")
        require(set(plan["stages"]) == set(MODEL_STAGES), "CAUSAL_STAGE_PLAN_REQUIRED")
        require(plan["model"] == "gpt-5.6-sol" and plan["effort"] == "xhigh",
                "FROZEN_MODEL_POLICY_REQUIRED")
        require(plan["timeout_seconds"] == 600 and plan["retries"] == 2,
                "REV59_EXECUTION_POLICY_REQUIRED")
        require(plan["caps"].get("BLIND") == plan["caps"].get("B2") == 30
                and set(plan["caps"]) == set(MODEL_STAGES)
                and all(isinstance(v, int) and v > 0 for v in plan["caps"].values()),
                "PHYSICAL_CAP_REQUIRED")
        ids = []
        for stage, slots in plan["stages"].items():
            require(bool(slots), "EMPTY_STAGE_PLAN")
            for slot in slots:
                require(set(slot) == {"logical_id", "subjects", "batch", "scope", "market",
                                     "native_market_contract"},
                        "TICKER_EXCEPTION_OR_SLOT_GAP")
                validate_scope(stage=stage, **{k: slot[k] for k in
                    ("scope", "market", "subjects", "native_market_contract")})
                ids.append(slot["logical_id"])
        require(len(ids) == len(set(ids)), "DUPLICATE_LOGICAL_ID")
        require(plan["source_slots"] and len(set(plan["source_slots"])) == len(plan["source_slots"]),
                "SOURCE_PLAN_GAP")
        require(set(declared_host_transitions) <= native.ALLOWED_TRANSITION,
                "DENIED_HOST_TRANSITION")
        require(bool(code_files) and bool(host_preparation), "PREPARATION_PROVENANCE_MISSING")
        frozen_files = [*code_files, __file__, native.__file__, failure.__file__,
                        *(Path(__file__).with_name(name) for name in NATIVE_MARKET_FILES)]
        files = {str(Path(p).resolve()): sha256_bytes(Path(p).read_bytes()) for p in frozen_files}
        value = dict(generation=generation, plan=plan, code=files, offline=offline,
            serialization=SERIALIZATION, host_preparation=canonical(host_preparation),
            declared_host_transitions=list(declared_host_transitions))
        durable_json(root / "contract.json", value, exclusive=True)
        obj = cls.__new__(cls)
        obj.root, obj.contract = root.resolve(), canonical(value)
        obj.contract_sha = digest(obj.contract)
        obj.data = dict(mode=Mode.CLEAN_START, state="PREFLIGHT", strict_run_started=False,
            simulated_boundary_started=False, artifacts={}, requests={}, outputs={}, attempts={},
            source_slots=[], adapters={}, views={}, halted=False, active_attempt=None, resume_receipt=None)
        obj.previous, obj.sequence = None, 0
        obj._record("CREATE_CLEAN_GENERATION")
        return obj

    @classmethod
    def resume(cls, root, *, expected_contract_sha256, failed_receipt_sha256):
        require(bool(failed_receipt_sha256), "RESUME_FAILURE_RECEIPT_REQUIRED")
        obj = cls.__new__(cls)
        obj.root = Path(root).resolve()
        obj.contract = json.loads((obj.root / "contract.json").read_bytes())
        obj.contract_sha = digest(obj.contract)
        require(obj.contract_sha == expected_contract_sha256, "RESUME_CONTRACT_DRIFT")
        paths = sorted((obj.root / "journal").glob("*.json"))
        require(bool(paths), "RESUME_LEDGER_REQUIRED")
        previous = None
        for index, path in enumerate(paths):
            row = json.loads(path.read_bytes())
            require(path.name == f"{index:06d}.json" and row["sequence"] == index
                    and row["previous"] == previous and row["contract_sha256"] == obj.contract_sha,
                    "RESUME_JOURNAL_INTEGRITY_GAP")
            previous = digest(row)
        obj.data, obj.previous, obj.sequence = row["data"], previous, len(paths)
        obj._guard()
        receipts = [r for values in obj.data["attempts"].values() for r in values]
        require(bool(receipts), "RESUME_LEDGER_REQUIRED")
        latest = max(receipts, key=lambda r: r["sequence"])
        require(latest["receipt_sha256"] == failed_receipt_sha256
                and latest["retry_eligible"] and latest["failure_class"] == failure.TRANSPORT
                and not obj.data["halted"] and obj.data["active_attempt"] is None,
                "RESUME_NOT_RETRYABLE")
        obj.data["mode"] = Mode.RESUME
        obj.data["resume_receipt"] = failed_receipt_sha256
        obj._record("RESUME_SAME_FROZEN_RETRY")
        return obj

    @property
    def generation(self):
        return self.contract["generation"]

    @property
    def state(self):
        return self.data["state"]

    def _guard(self):
        require(digest(json.loads((self.root / "contract.json").read_bytes())) == self.contract_sha
                == digest(self.contract), "CONTRACT_DRIFT")
        require(not self.data["halted"], "TERMINAL_FAIL_STOP")
        for path, expected in self.contract["code"].items():
            require(sha256_bytes(Path(path).read_bytes()) == expected, "FROZEN_CODE_DRIFT")
        for row in self.data["artifacts"].values():
            path = self.root / row["path"]
            require(not path.is_symlink() and path.resolve().is_relative_to(self.root)
                    and sha256_bytes(path.read_bytes()) == row["sha256"], "SEALED_ARTIFACT_DRIFT")
        for rows in self.data["attempts"].values():
            for row in rows:
                path = self.root / row["raw_path"]
                require(not path.is_symlink() and path.resolve().is_relative_to(self.root)
                        and sha256_bytes(path.read_bytes()) == row["raw_response_sha256"],
                        "RAW_OUTPUT_DRIFT")
        for root, expected in self.data["views"].items():
            path = Path(root) / "context.json"
            require(not path.is_symlink() and sha256_bytes(path.read_bytes()) == expected,
                    "DECLARED_VIEW_DRIFT")
        if self.sequence:
            last = json.loads((self.root / "journal" / f"{self.sequence-1:06d}.json").read_bytes())
            require(digest(last) == self.previous and digest(last["data"]) == digest(self.data),
                    "MEMORY_OR_JOURNAL_DRIFT")

    def _record(self, event):
        row = dict(sequence=self.sequence, previous=self.previous, event=event,
                   contract_sha256=self.contract_sha, data=self.data)
        durable_json(self.root / "journal" / f"{self.sequence:06d}.json", row, exclusive=True)
        self.previous, self.sequence = digest(row), self.sequence + 1

    def _advance(self, state):
        require(STATES.index(state) == STATES.index(self.state) + 1, "ILLEGAL_STATE_TRANSITION")
        self.data["state"] = state

    def _seal(self, name, kind, value, parents=()):
        require(name not in self.data["artifacts"] and name.replace("_", "").isalnum(),
                "ARTIFACT_RESEAL_OR_INVALID_NAME")
        require(all(p in self.data["artifacts"] for p in parents), "MISSING_LINEAGE")
        body = encoded(dict(generation=self.generation, kind=kind, value=value,
                            parents={p: self.data["artifacts"][p]["sha256"] for p in parents}))
        path = f"artifacts/{name}.json"
        durable_bytes(self.root / path, body, exclusive=True)
        self.data["artifacts"][name] = dict(path=path, kind=kind, sha256=sha256_bytes(body),
                                            parents=list(parents))
        return self.data["artifacts"][name]["sha256"]

    def register_adapter(self, name, code_path, *, function_name=None):
        self._guard()
        require(self.state == "PREFLIGHT" and not self.data["strict_run_started"]
                and not self.data["simulated_boundary_started"], "ADAPTER_REGISTRATION_CLOSED")
        path = str(Path(code_path).resolve())
        require(path in self.contract["code"] and name not in self.data["adapters"],
                "UNFROZEN_ADAPTER")
        self.data["adapters"][name] = dict(path=path, function_name=function_name)
        self._record("REGISTER_DECLARED_ADAPTER")

    def seal_pre_source(self, authorities):
        self._guard()
        require(self.state == "PREFLIGHT" and set(authorities) == AUTHORITIES,
                "PRE_PROVIDER_AUTHORITIES_INCOMPLETE")
        require(canonical(authorities["execution_plan"]) == self.contract["plan"], "PLAN_DRIFT")
        require(authorities["source_dag"]["slots"] == self.contract["plan"]["source_slots"],
                "SOURCE_DAG_DRIFT")
        for name, value in authorities.items():
            require(bool(value), "EMPTY_PRE_PROVIDER_AUTHORITY")
            self._seal(name, name, value)
        self._advance("PRE_SOURCE_AUTHORITIES_SEALED")
        self._record("PRE_SOURCE_AUTHORITIES_SEALED")

    def admit_source(self, slot, *, simulated=False):
        self._guard()
        require(simulated == self.contract["offline"], "OFFLINE_EXTERNAL_DISPATCH_DENIED")
        require(self.state in {"PRE_SOURCE_AUTHORITIES_SEALED", "SOURCE_COLLECTION"},
                "SOURCE_COLLECTION_CLOSED")
        require(slot in self.contract["plan"]["source_slots"] and slot not in self.data["source_slots"],
                "UNPLANNED_OR_DUPLICATE_SOURCE")
        if self.state == "PRE_SOURCE_AUTHORITIES_SEALED":
            self._advance("SOURCE_COLLECTION")
        self.data["simulated_boundary_started" if simulated else "strict_run_started"] = True
        self.data["source_slots"].append(slot)
        self._record("SIMULATED_SOURCE_ADMISSION" if simulated else "SOURCE_CALL_ADMITTED")

    def seal_source(self, source, owner_receipt):
        self._guard()
        require(self.state == "SOURCE_COLLECTION" and
                set(self.data["source_slots"]) == set(self.contract["plan"]["source_slots"]),
                "SOURCE_COLLECTION_INCOMPLETE")
        require(source["generation"] == owner_receipt["generation"] == self.generation
                and owner_receipt["status"] == "PASS" and owner_receipt["source_sha256"] == digest(source),
                "OWNER_GATE_OR_GENERATION_GAP")
        self._seal("source", "source", source)
        self._seal("owner", "owner", owner_receipt, ("source",))
        self._advance("SOURCE_COLLECTION_SEALED")
        self._record("SOURCE_COLLECTION_SEALED")

    def seal_blind_package(self, package, *, validate_source_only):
        self._guard()
        require(self.state == "SOURCE_COLLECTION_SEALED", "BLIND_PACKAGE_OUT_OF_ORDER")
        source = self._value("source")
        self._callback_identity(validate_source_only)
        # The existing provenance-allowlist exporter owns content validation.
        require(validate_source_only(package, source) is True, "BLIND_CONTAMINATION")
        require(package["generation"] == self.generation, "BLIND_GENERATION_DRIFT")
        self._seal("blind_package", "blind_package", package, ("source",))
        self._advance("BLIND_PACKAGE_SEALED")
        self._record("BLIND_PACKAGE_SEALED")

    def _value(self, name):
        return json.loads((self.root / self.data["artifacts"][name]["path"]).read_bytes())["value"]

    def _callback_identity(self, callback):
        try:
            path = str(Path(inspect.getsourcefile(callback)).resolve())
            identity = dict(path=path, qualname=callback.__qualname__,
                            line=callback.__code__.co_firstlineno)
        except (TypeError, AttributeError) as exc:
            raise ControllerError("UNFROZEN_CALLBACK") from exc
        require(path in self.contract["code"], "UNFROZEN_CALLBACK")
        return dict(identity, source_sha256=self.contract["code"][path])

    def view(self, audience, names):
        self._guard()
        allowed = BLIND_KINDS if audience == "BLIND" else AI_KINDS if audience == "AI" else set()
        require(bool(allowed) and bool(names), "UNKNOWN_OR_EMPTY_VIEW")
        if audience == "AI":
            require("BLIND" in self.data["outputs"], "AI_CONTEXT_BEFORE_BLIND_SEAL")
        def visit(name):
            row = self.data["artifacts"].get(name)
            require(row is not None and row["kind"] in allowed, "FORBIDDEN_CONTEXT_READ")
            for parent in row["parents"]:
                visit(parent)
        for name in names:
            if audience == "BLIND":
                require(self.data["artifacts"].get(name, {}).get("kind") != "source",
                        "BLIND_REQUIRES_ALLOWLIST_PACKAGE")
            visit(name)
        return {name: self._value(name) for name in names}

    def materialize_view(self, audience, names, destination):
        value = self.view(audience, names)
        destination = Path(destination).absolute()
        require(not destination.exists() and not destination.resolve().is_relative_to(self.root)
                and not self.root.is_relative_to(destination.resolve()), "WORKSPACE_ROOT_OVERLAP")
        require(not any(destination.resolve().is_relative_to(Path(p))
                        or Path(p).is_relative_to(destination.resolve())
                        for p in self.data["views"]), "WORKSPACE_ROOT_OVERLAP")
        require(not any(p.is_symlink() for p in [destination, *destination.parents]), "VIEW_SYMLINK")
        durable_json(destination / "context.json", value, exclusive=True)
        self.data["views"][str(destination)] = sha256_bytes((destination/"context.json").read_bytes())
        self._record("MATERIALIZE_DECLARED_VIEW")
        return dict(audience=audience, root=str(destination), context_sha256=digest(value),
                    artifacts={n: self.data["artifacts"][n]["sha256"] for n in names},
                    process_sandbox_qualification="REQUIRED_SEPARATELY_FOR_LIVE")

    def blind_seal_receipt(self):
        self._guard()
        require("BLIND" in self.data["outputs"], "BLIND_NOT_SEALED")
        return dict(sealed=True, sha256=self.data["outputs"]["BLIND"])

    def _admit_stage(self, stage):
        require(stage in MODEL_STAGES, "UNKNOWN_STAGE")
        require(stage not in self.data["outputs"], "STAGE_ALREADY_SEALED")
        index = MODEL_STAGES.index(stage)
        require(all(p in self.data["outputs"] for p in MODEL_STAGES[:index]),
                "PREREQUISITE_OUTPUT_MISSING")
        valid = {"BLIND": {"BLIND_PACKAGE_SEALED", "BLIND_JUDGMENT_EXECUTION"},
                 "B2": {"UPSTREAM_AUTHORITY_SEALED", "B2_REQUESTS_SEALED", "B2_EXECUTION"}}
        require(self.state in valid.get(stage, {"BLIND_JUDGMENTS_SEALED", "UPSTREAM_EXECUTION"}),
                "STAGE_STATE_MISMATCH")

    def project_request(self, stage, slot_index, *, parents, adapter, builder):
        """Bind a predeclared domain builder's native payload without wrapping it."""
        self._guard()
        self._admit_stage(stage)
        require(stage not in self.data["requests"], "REQUEST_SET_ALREADY_SEALED")
        declared = self.data["adapters"].get(adapter)
        require(declared and declared["function_name"] == builder.__qualname__
                and str(Path(inspect.getsourcefile(builder)).resolve()) == declared["path"],
                "UNDECLARED_PROJECTION_ADAPTER")
        audience = "BLIND" if stage == "BLIND" else "AI"
        inputs = self.view(audience, parents)
        self._callback_identity(builder)
        payload = canonical(builder(deepcopy(inputs)))
        require(set(payload) == {"prompt", "response_schema", "input"}, "NATIVE_PAYLOAD_SHAPE")
        name = f"view_{stage}_{slot_index}"
        kind = "blind_request_view" if stage == "BLIND" else "ai_request_view"
        self._seal(name, kind, payload, parents)
        self._record("SEAL_NATIVE_PROJECTED_PAYLOAD")
        slot = self.contract["plan"]["stages"][stage][slot_index]
        policy = "blind_controller_policy" if stage == "BLIND" else "monitoring_controller_policy"
        return request_identity(generation=self.generation, stage=stage,
            scope=slot["scope"], market=slot["market"], native_market_contract=slot["native_market_contract"],
            logical_id=slot["logical_id"], subjects=slot["subjects"], batch=slot["batch"], payload=payload,
            prompt_sha256=digest(payload["prompt"]), schema_sha256=digest(payload["response_schema"]),
            policy_sha256=self.data["artifacts"][policy]["sha256"],
            context_refs={name: self.data["artifacts"][name]["sha256"]})

    def seal_requests(self, stage, requests):
        self._guard()
        self._admit_stage(stage)
        require(stage not in self.data["requests"], "REQUEST_SET_ALREADY_SEALED")
        slots = self.contract["plan"]["stages"][stage]
        requests = canonical(requests)
        require(len(requests) == len(slots), "REQUEST_COHORT_INCOMPLETE")
        for request, slot in zip(requests, slots, strict=True):
            self._check_request(request, stage)
            require({k: request[k] for k in slot} == slot, "REQUEST_SLOT_MISMATCH")
            context = self.view("BLIND" if stage == "BLIND" else "AI", list(request["context_refs"]))
            require(all(self.data["artifacts"][n]["sha256"] == h
                        for n, h in request["context_refs"].items()), "CONTEXT_REF_DRIFT")
            payload = request["payload"]
            native_view = len(context) == 1 and all(
                self.data["artifacts"][n]["kind"] in {"blind_request_view", "ai_request_view"}
                for n in context)
            require(set(payload) == {"prompt", "response_schema", "input"}
                    and (payload == next(iter(context.values())) if native_view
                         else payload["input"] == context), "UNDECLARED_MODEL_CONTEXT")
            require(digest(payload["prompt"]) == request["prompt_sha256"]
                    and digest(payload["response_schema"]) == request["schema_sha256"],
                    "PROMPT_SCHEMA_BINDING_GAP")
            policy = "blind_controller_policy" if stage == "BLIND" else "monitoring_controller_policy"
            require(request["policy_sha256"] == self.data["artifacts"][policy]["sha256"],
                    "REQUEST_POLICY_DRIFT")
        sha = self._seal(f"requests_{stage}", "private_request", requests)
        self.data["requests"][stage] = sha
        if stage == "BLIND":
            self._advance("BLIND_JUDGMENT_EXECUTION")
        elif stage == "MARKET":
            self._advance("UPSTREAM_EXECUTION")
        elif stage == "B2":
            self._advance("B2_REQUESTS_SEALED")
        self._record(f"SEAL_REQUESTS_{stage}")
        return sha

    def _check_request(self, request, stage):
        require(request["generation"] == self.generation and request["stage"] == stage,
                "REQUEST_GENERATION_OR_STAGE_MISMATCH")
        validate_scope(stage=stage, **{k: request.get(k) for k in
            ("scope", "market", "subjects", "native_market_contract")})
        if stage == "MARKET":
            require(request["payload"].get("input", {}).get("market") == request["market"],
                    "MARKET_PAYLOAD_IDENTITY_MISMATCH")
        require(request["serialization"] == SERIALIZATION
                and request["request_sha256"] == sha256_bytes(encoded(request["payload"])),
                "REQUEST_CANONICAL_SHA_MISMATCH")

    def authorize(self, stage, request, *, host, context):
        self._guard()
        self._admit_stage(stage)
        self._check_request(request, stage)
        require(stage in self.data["requests"], "UNSEALED_REQUEST_SET")
        selected = self._value(f"requests_{stage}")
        require(digest(request) in {digest(r) for r in selected}, "REQUEST_NOT_FROZEN")
        require(isinstance(host, native.QualifiedOfficialModelLaunchContext), "NATIVE_HOST_REQUIRED")
        require(set(host.transition_differences) <= set(self.contract["declared_host_transitions"]),
                "DENIED_HOST_TRANSITION")
        require(host.preparation_sha256 == native.digest(self.contract["host_preparation"]),
                "HOST_PREPARATION_DRIFT")
        identity = asdict(host.identity)
        policy = self.contract["plan"]
        require(identity["source_generation_id"] == self.generation
                and identity["request_freeze_sha256"] == digest(request)
                and identity["whole_source_sha256"] == self.data["artifacts"]["source"]["sha256"]
                and identity["source_only_zip_sha256"] == self.data["artifacts"]["blind_package"]["sha256"],
                "HOST_REQUEST_BINDING_GAP")
        require(identity["implementation_sha"] == digest(self.contract["code"])
                and identity["qualification_sha256"] == self.contract_sha
                and identity["prompt_schema_sha256"] == digest(
                    {k: request[k] for k in ("prompt_sha256", "schema_sha256", "policy_sha256")})
                and all(identity[k] in self.contract["code"].values()
                        for k in ("executable_sha256", "launcher_sha256")),
                "HOST_CODE_OR_CONTRACT_BINDING_GAP")
        require(all(identity[k] == policy[k] for k in ("model", "effort", "timeout_seconds", "retries"))
                and identity["max_calls"] == 10, "HOST_EXECUTION_POLICY_DRIFT")
        host.verify(context=context, identity=host.identity, preparation_sha256=host.preparation_sha256,
                    freeze_sha256=host.sha256)
        auth = dict(mode=self.data["mode"], generation=self.generation, stage=stage,
            scope=request["scope"], market=request["market"],
            native_market_contract=request["native_market_contract"],
            sealed_request_set_sha256=self.data["requests"][stage], canonical_request_sha256=digest(request),
            request_sha256=request["request_sha256"], serialization=SERIALIZATION,
            logical_id=request["logical_id"], subjects=request["subjects"], batch=request["batch"],
            contract_sha256=self.contract_sha, model=policy["model"], effort=policy["effort"],
            timeout_seconds=policy["timeout_seconds"], retries=policy["retries"], cap=policy["caps"][stage],
            native_host_scope="ONE_LOGICAL_REQUEST", native_host_cap=10,
            host_receipt=host.receipt(), prerequisite_seals={n: r["sha256"] for n, r in
                self.data["artifacts"].items() if r["kind"] not in {"attempt", "private_request"}},
            production_replacement=False, delivery=False, persistence=False)
        if self.data["mode"] == Mode.RESUME:
            auth["failed_receipt_sha256"] = self.data["resume_receipt"]
        return canonical(auth)

    def attempt(self, stage, request, *, host, context, transport, provider_validate,
                semantic_validate, simulated=False):
        require(simulated == self.contract["offline"], "OFFLINE_EXTERNAL_DISPATCH_DENIED")
        auth = self.authorize(stage, request, host=host, context=context)
        callbacks = {name: self._callback_identity(callback) for name, callback in (
            ("transport", transport), ("provider_validate", provider_validate),
            ("semantic_validate", semantic_validate))}
        auth["callbacks"] = callbacks
        require(self.data["active_attempt"] is None, "INCOMPLETE_ATTEMPT_FAIL_STOP")
        previous = self.data["attempts"].get(request["logical_id"], [])
        if previous:
            require(previous[-1]["retry_eligible"], "NONRETRYABLE_OR_SUCCESSFUL_REQUEST")
            require(previous[-1]["callback_sha256"] == digest(callbacks),
                    "RETRY_CALLBACK_DRIFT")
        require(len(previous) <= auth["retries"], "REQUEST_RETRY_CAP")
        stage_count = sum(len(rows) for rows in self.data["attempts"].values()
                          if rows and rows[0]["stage"] == stage)
        require(stage_count < auth["cap"], "PHYSICAL_STAGE_CAP")
        # Fixed order prevents successful-subject resampling and selective skipping.
        selected = self._value(f"requests_{stage}")
        pending = next((r for r in selected if not self.data["attempts"].get(r["logical_id"])
                        or self.data["attempts"][r["logical_id"]][-1]["status"] != "PASS"), None)
        require(pending and digest(pending) == digest(request), "REQUEST_ORDER_MISMATCH")
        name = f"attempt_{stage}_{stage_count}"
        self._seal(name + "_authorization", "attempt", auth)
        self.data["active_attempt"] = name
        if stage == "B2" and self.state == "B2_REQUESTS_SEALED":
            self._advance("B2_EXECUTION")
        self._record("ATTEMPT_ADMITTED")
        raw, transport_error = b"", None
        try:
            raw = transport(encoded(request["payload"]))
            require(isinstance(raw, bytes), "TRANSPORT_MUST_RETURN_BYTES")
        except Exception as exc:
            transport_error = exc
            if not isinstance(raw, bytes):
                raw = b""
        durable_bytes(self.root / "raw" / (name + ".bin"), raw, exclusive=True)
        receipt = dict(stage=stage, logical_id=request["logical_id"], sequence=self.sequence,
            attempt=len(previous)+1, canonical_request_sha256=digest(request),
            callback_sha256=digest(callbacks),
            raw_response_sha256=sha256_bytes(raw), raw_path=f"raw/{name}.bin",
            provider_schema_status="NOT_EVALUATED", local_semantic_status="NOT_EVALUATED",
            status="FAIL", failure_class=None, retry_eligible=False)
        # Seal raw capture before parsing or invoking either validator.
        self._seal(name + "_raw", "attempt", receipt)
        self._record("RAW_DURABLE_BEFORE_VALIDATION")
        output, exc = None, transport_error
        if exc is None:
            try:
                try:
                    output = json.loads(raw)
                except (ValueError, UnicodeError) as error:
                    raise failure.ResponseFormFailure("MALFORMED_RESPONSE") from error
                if provider_validate(output) is not True:
                    raise failure.ResponseFormFailure("PROVIDER_SCHEMA_REJECT")
                receipt["provider_schema_status"] = "PASS"
                try:
                    if semantic_validate(output) is not True:
                        raise ValueError("LOCAL_SEMANTIC_REJECT")
                except failure.ResponseFormFailure as error:
                    # A form exception raised after schema PASS cannot resample a judgment.
                    raise ValueError("LOCAL_SEMANTIC_REJECT") from error
                receipt["local_semantic_status"] = "PASS"
                receipt["status"] = "PASS"
            except Exception as error:
                exc = error
        if exc is not None:
            category, retry = failure.classify(exc, receipt)
            receipt.update(failure_class=category, retry_eligible=retry, error_type=type(exc).__name__)
            if category == failure.SEMANTIC:
                receipt["local_semantic_status"] = "FAIL"
            if not retry:
                self.data["halted"] = True
        sha = self._seal(name + "_result", "attempt", dict(receipt, output=output))
        receipt["receipt_sha256"] = sha
        self.data["attempts"].setdefault(request["logical_id"], []).append(receipt)
        self.data["active_attempt"] = None
        self._record("ATTEMPT_VALIDATED")
        return deepcopy(receipt)

    def seal_stage(self, stage):
        self._guard()
        self._admit_stage(stage)
        require(stage in self.data["requests"], "REQUESTS_NOT_SEALED")
        results = []
        for request in self._value(f"requests_{stage}"):
            rows = self.data["attempts"].get(request["logical_id"], [])
            require(rows and rows[-1]["status"] == "PASS", "ACCEPTED_OUTPUT_COHORT_INCOMPLETE")
            row = rows[-1]
            require(sha256_bytes((self.root/row["raw_path"]).read_bytes()) == row["raw_response_sha256"],
                    "RAW_OUTPUT_DRIFT")
            results.append(dict(logical_id=request["logical_id"], subjects=request["subjects"],
                scope=request["scope"], market=request["market"],
                native_market_contract=request["native_market_contract"],
                canonical_request_sha256=digest(request), receipt_sha256=row["receipt_sha256"],
                raw_response_sha256=row["raw_response_sha256"],
                output=json.loads((self.root/row["raw_path"]).read_bytes())))
        kind = "blind_output" if stage == "BLIND" else "ai_output" if stage == "B2" else "upstream"
        # Output lineage intentionally excludes blind content from AI dependencies.
        parents = ("source",) + tuple(f"outputs_{p}" for p in MODEL_STAGES[1:MODEL_STAGES.index(stage)]
                                      if p in self.data["outputs"])
        self.data["outputs"][stage] = self._seal(f"outputs_{stage}", kind, results, parents)
        if stage == "BLIND":
            self._advance("BLIND_JUDGMENTS_SEALED")
        elif stage == "B":
            self._advance("UPSTREAM_AUTHORITY_SEALED")
        elif stage == "B2":
            self._advance("B2_OUTPUTS_SEALED")
        self._record(f"SEAL_OUTPUTS_{stage}")

    def reveal(self):
        self._guard()
        require(self.state == "B2_OUTPUTS_SEALED" and all(s in self.data["outputs"]
                for s in MODEL_STAGES), "EARLY_REVEAL_DENIED")
        self._advance("REVEAL_COMPARISON")
        self._record("REVEAL_BOTH_SEALED")
        return {stage: self._value(f"outputs_{stage}") for stage in MODEL_STAGES}

    def complete(self, comparison, *, validate_comparison):
        self._guard()
        require(self.state == "REVEAL_COMPARISON", "COMPARISON_BEFORE_REVEAL")
        self._callback_identity(validate_comparison)
        require(validate_comparison(comparison, self._value("comparison"), self._value("acceptance"))
                is True, "PRESEALED_COMPARISON_CONTRACT_REJECT")
        self._seal("comparison_result", "comparison_result", comparison,
                   ("comparison", "acceptance", "outputs_BLIND", "outputs_B2"))
        self._advance("COMPLETE")
        self._record("COMPLETE")

    def receipt(self):
        self._guard()
        return dict(generation=self.generation, mode=self.data["mode"], state=self.state,
            strict_run_started=self.data["strict_run_started"], offline=self.contract["offline"],
            journal_sha256=self.previous, contract_sha256=self.contract_sha,
            artifact_seals=deepcopy(self.data["artifacts"]), outputs=deepcopy(self.data["outputs"]))
