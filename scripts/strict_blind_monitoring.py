"""Clean-start adapters around unchanged native Market/Core/A/B and B2 owners.

Only request capture and validation are called. Legacy execution/continuation
methods are never used; dispatch and stage seals belong to StrictBlindController.
"""
from copy import deepcopy
import json
from pathlib import Path
from tempfile import TemporaryDirectory
from types import MethodType, SimpleNamespace

from app.services.unified_snapshot_contract import digest
from app.services.unavailable_price_valuation import shadow_request_context
from scripts import r2b_r5_execution as native
from scripts import strict_blind_contract as blind
from scripts import newbuyer_b2_v2_shadow as b2
from scripts import newbuyer_b2_shadow as b1
from scripts import newbuyer_b2_contract as b1_contract
from scripts.strict_blind_controller import canonical
from scripts.rev46_kr_models import Rev46Kr8Execution
from scripts.us14_models import Us14Execution

STAGES = {"MARKET": "market", "CORE": "core", "A": "pass-a", "B": "pass-b"}


def from_sources(*, whole, local_seeds, valuation_contexts, generation, coverage, census):
    """Rebuild source-use inputs before models. Never load historical accepted state."""
    from scripts.fresh_source_only_export import source_only_fresh_stock
    from scripts.r2b_r2_preflight import preflight_subject
    from scripts.r2b_r5_market_adapter import project_sealed_market_context
    prepared, stocks, blind_inputs = {}, {}, {}
    for market, packet in whole["packets"].items():
        for ticker, stock in packet["stocks"].items():
            authority = whole["authority_graph"]["stocks"][ticker]
            source_only_fresh_stock(stock, authority)
            readiness, data = preflight_subject(stock, authority, local_seeds[ticker],
                generation=generation, cutoff=stock["packet"]["generated_at"])
            blind.require(readiness["status"] == "PASS" and data["mode"] == "EVIDENCE_BASED",
                "STRICT_NATIVE_SOURCE_PREFLIGHT_GAP:" + ticker)
            prepared[ticker], stocks[ticker] = data, deepcopy(stock)
            sub = data["subject"]
            blind_inputs[ticker] = dict(ticker=ticker, market=market.upper(),
                security_id=valuation_contexts[ticker]["security_id"], source_generation_id=stock["fresh_run_id"],
                source_sha256=digest(stock), metadata=deepcopy(sub["decision_evidence"]),
                authority=deepcopy(data["initial_chain"]["authority"]),
                frozen_fact_fields=native.c.policy.frozen_fact_fields(stock["packet"], ticker, sub["decision_evidence"]),
                valuation_context=deepcopy(valuation_contexts[ticker]), coverage=deepcopy(coverage), census=deepcopy(census),
                current_price=deepcopy(shadow_request_context(sub, stock)["current_price"]),
                tactical_candidates=deepcopy(sub["tactical_candidates"]))
    markets = {market: project_sealed_market_context(packet, whole["seed"], whole["authority_graph"],
        expected_authority_sha256=whole["authority_graph_sha256"]) for market, packet in whole["packets"].items()}
    return dict(prepared=prepared, stocks=stocks, markets=markets, valuation_contexts=deepcopy(valuation_contexts),
        source_generation_id=whole["seed"]["parent_run_id"], coverage=deepcopy(coverage), census=deepcopy(census),
        whole_source_sha256=digest(whole)), blind_inputs


def _valuation(self, ticker):
    return deepcopy(self.strict_valuation_contexts[ticker])


def _captured_payload(request):
    path = Path(request["directory"])
    return dict(prompt=(path / "prompt.txt").read_text(),
        input=json.loads((path / "subject-context.json").read_bytes()),
        response_schema=json.loads((path / "provider-wire-schema.json").read_bytes()))


class NativeSession:
    def __init__(self, root, *, market, generation, source):
        cls = Us14Execution if market == "US" else Rev46Kr8Execution
        self.execution = e = cls.__new__(cls)
        e.root = Path(root)
        e.report, e.sealed = e.root / "report", e.root / "sealed"
        e.requests = e.sealed / "requests"
        e.gen, e.source_gen = generation, source["source_generation_id"]
        e.source_frozen = {"provider_native_valuation": True}
        e.active_batches = None
        e.prepared, e.fresh_stocks, e.projected = (deepcopy(source[k]) for k in ("prepared", "stocks", "markets"))
        e.strict_valuation_contexts = deepcopy(source["valuation_contexts"])
        e.valuation_context = MethodType(_valuation, e)
        for name in ("cores", "arows", "brows", "markets", "chains", "catalogs", "subjects",
                     "caps", "ranges", "entries", "actx", "bctx", "stage_manifests"):
            setattr(e, name, {})
        e.limits = {s: {} for s in native.STAGES}
        e.ledger = []
        self.market, self.source, self.captured = market, source, {}
        blind.require(set(e.prepared) == {t for s in e.full_topology() for t in s["subjects"]},
            "STRICT_NATIVE_FULL_COHORT_REQUIRED")
        blind.require(all(d["mode"] == "EVIDENCE_BASED" for d in e.prepared.values()),
            "STRICT_NATIVE_UNKNOWN_B2_DEPENDENCY")
        for ticker, data in e.prepared.items():
            blind.require(data["initial_chain"]["source_generation_id"] == e.source_gen
                and data["initial_chain"]["execution_generation_id"] == generation
                and data["view_receipt"]["raw_source_sha256"] == digest(e.fresh_stocks[ticker]),
                "STRICT_NATIVE_GENERATION_OR_SOURCE_DRIFT")

    def capture(self, stage):
        blind.require(stage not in self.captured, "STRICT_NATIVE_REQUEST_REBUILD")
        e = self.execution
        if stage == "MARKET":
            context = e.projected[self.market.lower()]["context"]
            rows = [e.capture("market", dict(market=self.market.lower(), batch=1, subjects=[]), context,
                native.market_owner.market_schema(context), native.market_owner.PROMPT)]
        elif stage == "CORE":
            rows = []
            for spec in e.batch_topology():
                contexts = {}
                for ticker in spec["subjects"]:
                    e.chain(ticker)
                    contexts[ticker] = {**e.prepared[ticker]["core_input"], "authority": e.chains[ticker]["authority"]}
                rows.append(e.capture("core", spec, contexts, native.c.schemas.core_schema(contexts),
                    native.c.schemas.CORE_PROMPT + "\n" + native.c.LIMIT_PROMPT))
        else:
            rows = e.before_a() if stage == "A" else e.before_b()
        self.captured[stage] = rows
        return rows

    def accept(self, stage, request, output):
        e = self.execution
        path = Path(request["directory"])
        schema = json.loads((path / "internal-semantic-schema.json").read_bytes())
        blind.require(not native.owner.validate_json_schema(output, schema), "STRICT_NATIVE_INTERNAL_SCHEMA")
        destination = e.sealed / "validated" / stage / str(request["batch"])
        destination.mkdir(parents=True, exist_ok=False)
        expected_spec = {k: request[k] for k in ("market", "batch", "subjects")}

        def frozen_output(instance, requested_stage, spec, original):
            blind.require(requested_stage == STAGES[stage] and spec == expected_spec and original == request,
                "STRICT_NATIVE_ACCEPT_SCOPE")
            return deepcopy(output), destination

        # Existing domain methods invoke only this detached, already raw-sealed output.
        e.invoke = MethodType(frozen_output, e)
        getattr(native.Execution, STAGES[stage].replace("-", "_"))(e, expected_spec, request)

    def replay(self, stage, view):
        for prior in list(STAGES)[:list(STAGES).index(stage)] if stage in STAGES else list(STAGES):
            requests = self.capture(prior)
            results = [r for r in view["outputs_" + prior] if r["market"] == self.market]
            blind.require(len(results) == len(requests), "STRICT_NATIVE_UPSTREAM_COHORT_GAP")
            for request, result in zip(requests, results, strict=True):
                blind.require(canonical(request["subjects"]) == canonical(result["subjects"]),
                    "STRICT_NATIVE_UPSTREAM_SUBJECT_DRIFT")
                self.accept(prior, request, result["output"])

    def b2_request(self, ticker):
        e = self.execution
        v1 = b1.build_request(settings=SimpleNamespace(newbuyer_qualified_valuation_shadow=True),
            context=shadow_request_context(e.bctx[ticker], e.fresh_stocks[ticker]), accepted=e.brows[ticker],
            core=e.cores[ticker], pass_a=e.arows[ticker], source_generation_id=e.source_gen)
        sub = v1["subject"]
        legacy = []
        for ref in sub["capability"]["confidence"] + sub["capability"]["quality"]:
            claim = next(r for r in sub["frozen_business_claims"] if r["claim_ref"] == ref)
            effect = e.cores[ticker]["effects"][ref]
            legacy.append(dict(ticker=ticker, claim_ref=ref, effect=effect["effect"],
                existing_materiality=effect["materiality"], legacy_claim_sha256=digest(claim)))
        coverage, census = self.source["coverage"], self.source["census"]
        request = b2.build_request(enabled=True, v1_request=v1, coverage=coverage, census=census,
            coverage_sha=coverage["receipt_sha256"], census_sha=census["receipt_sha256"], legacy_records=legacy)
        return request, v1


class MonitoringAdapter:
    def __init__(self, stage, market, batch, ticker=None):
        self.stage, self.market, self.batch, self.ticker = stage, market, batch, ticker

    def _session(self, view, root):
        prior = list(STAGES)[:list(STAGES).index(self.stage)] if self.stage in STAGES else list(STAGES)
        names = ["source"] + ["outputs_" + s for s in prior]
        blind.require(set(view) == set(names), "STRICT_NATIVE_UNDECLARED_VIEW")
        session = NativeSession(root, market=self.market, generation=view["source"]["generation"],
            source=view["source"]["monitoring_inputs"][self.market])
        session.replay(self.stage, view)
        return session

    def build(self, view):
        with TemporaryDirectory(prefix="strict-native-request-") as root:
            session = self._session(view, root)
            if self.stage == "B2":
                request, _ = session.b2_request(self.ticker)
                return b2.provider_payload(request, expected_request_sha256=request["request_sha256"])
            request = next(r for r in session.capture(self.stage) if r["batch"] == self.batch)
            return _captured_payload(request)

    def validate(self, view, output):
        with TemporaryDirectory(prefix="strict-native-validation-") as root:
            session = self._session(view, root)
            if self.stage == "B2":
                request, _ = session.b2_request(self.ticker)
                return b2.validate_result(output, request, expected_request_sha256=request["request_sha256"])["status"] == "PASS"
            request = next(r for r in session.capture(self.stage) if r["batch"] == self.batch)
            session.accept(self.stage, request, output)
            return True


def register(controller):
    controller.register_adapter("monitoring_native", __file__, function_name=MonitoringAdapter.build.__qualname__)


def requests(controller, stage):
    prior = list(STAGES)[:list(STAGES).index(stage)] if stage in STAGES else list(STAGES)
    parents = ["source"] + ["outputs_" + s for s in prior]
    rows = []
    for index, slot in enumerate(controller.contract["plan"]["stages"][stage]):
        adapter = MonitoringAdapter(stage, slot["market"], slot["batch"],
            slot["subjects"][0] if stage == "B2" else None)
        rows.append(controller.project_request(stage, index, parents=parents,
            adapter="monitoring_native", builder=adapter.build))
    return rows


class NativeValidation:
    def __init__(self, request, view):
        self.request, self.view = deepcopy(request), deepcopy(view)
        self.adapter = MonitoringAdapter(request["stage"], request["market"], request["batch"],
            request["subjects"][0] if request["stage"] == "B2" else None)
        blind.require(self.adapter.build(self.view) == request["payload"], "STRICT_NATIVE_PAYLOAD_DRIFT")

    def provider(self, output):
        return not b1_contract.validate_json_schema(output, self.request["payload"]["response_schema"])

    def semantic(self, output):
        return self.adapter.validate(self.view, output)
