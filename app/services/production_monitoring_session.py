"""Current-cycle session delegating domain work to the accepted canonical owners.

Legacy controller construction, dispatch, resume and historical-file verification
are deliberately not inherited. Only named domain builder/validator methods are
used, with this session owning their input/output filesystem and dispatch.
"""
from copy import deepcopy
import json
from pathlib import Path
from types import SimpleNamespace

from app.services.provider_valuation_calibration_context import require_direction_isolation
from app.services.unavailable_price_valuation import shadow_request_context
from app.services.unified_run_artifacts import durable_bytes, durable_json
from app.services.unified_snapshot_contract import digest
from app.services.unified_stock_acquisition import UNIVERSE
from app.services import canonical_monitoring_domain as domain
from app.services import new_buyer_input_owner as b1
from app.services import new_buyer_request_owner as b2

STAGE_NAMES = {"MARKET": "market", "CORE": "core", "A": "pass-a", "B": "pass-b"}


class ProductionMonitoringSession:
    POLICY = domain.c.policy
    DETAILED_PRESENTATION = True
    TYPED_PRESENTATION = False
    partition = domain.CanonicalMonitoringDomain.partition
    chain = domain.CanonicalMonitoringDomain.chain
    limit_context = domain.CanonicalMonitoringDomain.limit_context
    args = domain.CanonicalMonitoringDomain.args
    validate_limits = domain.CanonicalMonitoringDomain.validate_limits
    before_a = domain.CanonicalMonitoringDomain.before_a
    before_b = domain.CanonicalMonitoringDomain.before_b

    def __init__(self, root, *, market, generation_id, source, source_generation_id=None,
                 authority_native_v2=False, native_owner_parent=None, native_parent_scope=None):
        if type(authority_native_v2) is not bool:
            raise ValueError("EXPLICIT_NATIVE_SESSION_GATE_REQUIRED")
        if not authority_native_v2 and (native_owner_parent is not None or native_parent_scope is not None):
            raise ValueError("NATIVE_PARENT_REQUIRES_EXPLICIT_GATE")
        self._native_owner_parent = None
        self._native_parent_scope = None
        if authority_native_v2:
            from app.services.native_owner_session import BackendOwnerParent
            if not isinstance(native_owner_parent, BackendOwnerParent) or not isinstance(native_parent_scope, dict):
                raise ValueError("BACKEND_PARENT_CAPABILITY_REQUIRED")
            if (native_parent_scope.get("market"), native_parent_scope.get("generation_id"),
                    native_parent_scope.get("source_generation_id")) != (market, generation_id, source_generation_id or generation_id):
                raise ValueError("NATIVE_SESSION_GENERATION_MISMATCH")
            native_owner_parent.verify_scope(**native_parent_scope)
            self._native_owner_parent = native_owner_parent
            self._native_parent_scope = dict(native_parent_scope)
        self.root = Path(root)
        self.report, self.sealed = self.root / "report", self.root / "sealed"
        self.requests = self.sealed / "requests"
        self.market = market
        self.gen, self.source_gen = generation_id, source_generation_id or generation_id
        self.source = deepcopy(source)
        self.prepared, self.fresh_stocks, self.projected = (deepcopy(source[k]) for k in ("prepared", "stocks", "markets"))
        if source["source_generation_id"] != self.source_gen or set(self.projected) != {market}:
            raise ValueError("production_monitoring_generation_or_market_drift")
        if set(self.prepared) != set(UNIVERSE[market]) or set(self.fresh_stocks) != set(self.prepared):
            raise ValueError("production_monitoring_current_cohort_gap")
        for ticker, row in self.prepared.items():
            if (row["mode"] != "EVIDENCE_BASED"
                    or row["initial_chain"]["source_generation_id"] != self.source_gen
                    or row["initial_chain"]["execution_generation_id"] != generation_id
                    or self.fresh_stocks[ticker]["fresh_run_id"] != self.source_gen
                    or row["view_receipt"]["raw_source_sha256"] != digest(self.fresh_stocks[ticker])):
                raise ValueError("production_monitoring_subject_authority_gap")
        for name in ("cores", "arows", "brows", "markets", "chains", "catalogs", "subjects", "caps", "ranges", "entries", "actx", "bctx"):
            setattr(self, name, {})
        self.limits = {stage: {} for stage in STAGE_NAMES.values()}
        self.stage_manifests, self.captured, self._accepted_batches = {}, {}, set()
        self._pending_output = None

    def native_owner(self):
        if self._native_owner_parent is None:
            raise ValueError("NATIVE_SESSION_FEATURE_DISABLED")
        self._native_owner_parent.verify_scope(**self._native_parent_scope)
        return self._native_owner_parent

    def native_context_prompt(self, invocation_id, receipt):
        return self.native_owner().context_prompt(invocation_id, receipt)

    def native_reported_economic_claim(self, invocation_id, receipt, packet):
        """Opt-in role evidence, never promoted to a complete accepted Core."""
        return self.native_owner().reported_economic_claim(invocation_id, receipt, packet)

    def native_economic_candidate(self, invocation_id, receipt, candidate, *, packet=None):
        owner = self.native_owner()
        result = owner.economic_candidate(invocation_id, receipt, candidate)
        if packet is not None:
            owner.verify_packet(invocation_id, receipt, candidate, packet)
        return result

    def batch_topology(self):
        rows = [row for row in domain.owner._batch_topology() if row["market"] == self.market]
        if sorted(t for row in rows for t in row["subjects"]) != sorted(UNIVERSE[self.market]):
            raise ValueError("production_canonical_batch_topology_drift")
        return deepcopy(rows)

    def valuation_context(self, ticker):
        return deepcopy(self.source["valuation_contexts"][ticker])

    def receipt(self, path, value):
        durable_json(path, value, exclusive=True)
        if value.get("status") != "PASS":
            raise ValueError("production_canonical_semantic_reject")

    def freeze_stage(self, stage, requests):
        value = {"generation_id": self.gen, "requests": requests}
        durable_json(self.sealed / (stage + "-request-freeze.json"), value, exclusive=True)
        self.stage_manifests[stage] = digest(value)

    def capture(self, stage_name, spec, context, schema, prompt):
        expected = [] if stage_name == "market" else next(
            (s["subjects"] for s in self.batch_topology() if s["batch"] == spec["batch"]), None)
        if spec["market"] != self.market or spec["subjects"] != expected:
            raise ValueError("production_request_subject_scope")
        if stage_name in {"core", "pass-a"}:
            require_direction_isolation(context)
            require_direction_isolation(schema)
        if stage_name == "pass-b" and any(context[t].get("valuation_context") != self.valuation_context(t) for t in expected):
            raise ValueError("production_pass_b_valuation_visibility_drift")
        wire, projection = domain.owner.project_provider_wire_schema(schema)
        scan = domain.owner.scan_provider_structured_output_schema(wire)
        if scan["status"] != "PASS":
            raise ValueError("production_provider_wire_schema_gap")
        destination = self.requests / stage_name / self.market / f"batch-{spec['batch']:02d}"
        payload = dict(prompt=prompt + "\nFROZEN_CONTEXT:\n" + json.dumps(context, ensure_ascii=False, sort_keys=True) + "\n",
                       input=deepcopy(context), response_schema=wire)
        for name, value in (("subject-context", context), ("internal-semantic-schema", schema),
                            ("provider-wire-schema", wire), ("provider-wire-projection", projection), ("provider-dialect-scan", scan)):
            durable_json(destination / (name + ".json"), value, exclusive=True)
        durable_bytes(destination / "prompt.txt", payload["prompt"].encode(), exclusive=True)
        request = {"directory": str(destination), **spec, "stage": stage_name,
            "execution_generation_id": self.gen, "source_generation_id": self.source_gen,
            "payload": payload, "payload_sha256": digest(payload), "internal_schema_sha256": digest(schema)}
        durable_json(destination / "request-receipt.json", request, exclusive=True)
        return request

    def build(self, stage):
        if stage not in STAGE_NAMES or stage in self.captured:
            raise ValueError("production_request_rebuild_or_unknown_stage")
        previous = list(STAGE_NAMES)[:list(STAGE_NAMES).index(stage)]
        if any(name not in self.captured or any((name, r["batch"]) not in self._accepted_batches for r in self.captured[name]) for name in previous):
            raise ValueError("production_upstream_stage_incomplete")
        if stage == "MARKET":
            ctx = self.projected[self.market]["context"]
            rows = [self.capture("market", dict(market=self.market, batch=1, subjects=[]), ctx,
                domain.market_owner.market_schema(ctx), domain.market_owner.PROMPT)]
        elif stage == "CORE":
            rows = []
            for spec in self.batch_topology():
                contexts = {}
                for ticker in spec["subjects"]:
                    self.chain(ticker)
                    contexts[ticker] = {**self.prepared[ticker]["core_input"], "authority": self.chains[ticker]["authority"]}
                rows.append(self.capture("core", spec, contexts, domain.c.schemas.core_schema(contexts),
                    domain.c.schemas.CORE_PROMPT + "\n" + domain.c.LIMIT_PROMPT))
        else:
            rows = self.before_a() if stage == "A" else self.before_b()
        self.captured[stage] = deepcopy(rows)
        return rows

    def invoke(self, stage, spec, request):
        expected_stage, expected_spec, expected_request, output, destination = self._pending_output
        if (stage, spec, request) != (expected_stage, expected_spec, expected_request):
            raise ValueError("production_canonical_accept_scope")
        return deepcopy(output), destination

    def accept(self, stage, request, output):
        if request not in self.captured.get(stage, ()) or (stage, request["batch"]) in self._accepted_batches:
            raise ValueError("production_response_scope_or_duplicate")
        destination = Path(request["directory"])
        schema = json.loads((destination / "internal-semantic-schema.json").read_bytes())
        if (digest(schema) != request["internal_schema_sha256"]
                or digest(request["payload"]) != request["payload_sha256"]
                or json.loads((destination / "subject-context.json").read_bytes()) != request["payload"]["input"]
                or domain.owner.validate_json_schema(output, schema)):
            raise ValueError("production_internal_schema_or_request_drift")
        spec = {k: request[k] for k in ("market", "batch", "subjects")}
        validated = self.sealed / "validated" / stage / str(request["batch"])
        self._pending_output = (STAGE_NAMES[stage], spec, request, output, validated)
        try:
            getattr(domain.CanonicalMonitoringDomain, STAGE_NAMES[stage].replace("-", "_"))(self, spec, request)
        finally:
            self._pending_output = None
        self._accepted_batches.add((stage, request["batch"]))

    def b2_request(self, ticker):
        if set(self.brows) != set(UNIVERSE[self.market]):
            raise ValueError("production_b2_requires_complete_b")
        first = b1.build_request(settings=SimpleNamespace(newbuyer_qualified_valuation_shadow=True),
            context=shadow_request_context(self.bctx[ticker], self.fresh_stocks[ticker]),
            accepted=self.brows[ticker], core=self.cores[ticker], pass_a=self.arows[ticker], source_generation_id=self.source_gen)
        subject = first["subject"]
        legacy = []
        for ref in subject["capability"]["confidence"] + subject["capability"]["quality"]:
            claim = next(r for r in subject["frozen_business_claims"] if r["claim_ref"] == ref)
            effect = self.cores[ticker]["effects"][ref]
            legacy.append(dict(ticker=ticker, claim_ref=ref, effect=effect["effect"],
                existing_materiality=effect["materiality"], legacy_claim_sha256=digest(claim)))
        coverage, census = self.source["coverage"], self.source["census"]
        return b2.build_request(enabled=True, v1_request=first, coverage=coverage, census=census,
            coverage_sha=coverage["receipt_sha256"], census_sha=census["receipt_sha256"], legacy_records=legacy)
