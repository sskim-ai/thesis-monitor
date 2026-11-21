"""Concrete current-cycle source backend; canonical owners remain authoritative."""
import asyncio
from datetime import datetime
from pathlib import Path
import time

from app.services.production_kis_sources import replay_current_kis
from app.services.production_source_configuration import ProductionSourceConfiguration
from app.services.production_source_consumer import consumer_collection, consumer_policy
from app.services.production_source_context import POLICY, credential_binding, freeze_current_context
from app.services.production_source_projection import coverage_from_owned_sources, monitoring_source, replay_source_owners
from app.services.production_source_seal import read, seal_collection, verify_collection_seal
from app.services.production_source_transport import NativeProductionSourceTransport
from app.services.canonical_source_replay import market_inputs, require_captured_phase
from app.services.unified_run_artifacts import durable_json, sha256_bytes
from app.services.unified_snapshot_contract import digest

ROOT = Path(__file__).resolve().parents[2]


def runtime_code_identity():
    # Include uncommitted implementation during offline qualification. A final
    # commit does not authorize any different source bytes after admission.
    files = {}
    for directory in ("app", "scripts"):
        for suffix in ("*.py", "*.json"):
            for path in sorted((ROOT / directory).rglob(suffix)):
                if path.is_symlink():
                    raise ValueError("production_code_symlink_denied")
                files[str(path.relative_to(ROOT))] = sha256_bytes(path.read_bytes())
    path = ROOT / "docs/operations/UNIFIED_ACQUISITION_CLASSES.json"
    files[str(path.relative_to(ROOT))] = sha256_bytes(path.read_bytes())
    return digest(files)


class CanonicalProductionSourceBackend:
    def __init__(self, *, settings, configuration, implementation_sha, clock, transport=None,
                 context_factory=freeze_current_context,run_ledger=None,registration_owner=None,source_policy=None):
        self.settings = settings
        self.configuration = ProductionSourceConfiguration.model_validate(configuration)
        self.implementation_sha = implementation_sha
        self.clock = clock
        self.transport = transport or NativeProductionSourceTransport(settings,run_ledger=run_ledger,
            registration_owner=registration_owner,source_policy=source_policy)
        self.context_factory = context_factory
        self.code_identity = runtime_code_identity()
        self.configuration_identity = digest(dict(configuration=self.configuration.identity,
            code=self.code_identity, settings=settings.model_dump(mode="json")))
        self.policies = {}
        self.admitted = {}

    def guard(self):
        if runtime_code_identity() != self.code_identity or digest(dict(configuration=self.configuration.identity,
                code=self.code_identity, settings=self.settings.model_dump(mode="json"))) != self.configuration_identity:
            raise ValueError("production_source_code_or_configuration_drift")

    async def policy(self, market, session, run_id):
        self.guard()
        credential_binding(self.settings, market)
        policy = consumer_policy(market=market, session=session, code_config_sha256=self.configuration_identity)
        if run_id in self.policies:
            raise ValueError("production_source_policy_already_frozen")
        self.policies[run_id] = policy
        return policy

    def project(self, root, frozen, outcome, kis_plan, seal, request, finished_at):
        verify_collection_seal(root, seal, frozen)
        self.guard()
        kis_view = replay_current_kis(root, frozen, outcome, kis_plan) if kis_plan is not None else None
        args, whole = replay_source_owners(root, frozen, outcome, POLICY,
                                          runtime_policy_sha256=request["policy_sha256"])
        coverage = coverage_from_owned_sources(root, frozen, whole,
            collection_seal_sha256=seal["receipt_sha256"], kis_plan=kis_plan, kis_view=kis_view,
            kis_root=root / "kis" if kis_plan is not None else None)
        monitoring = monitoring_source(args=args, whole=whole, frozen=frozen, coverage=coverage,
                                       kis_plan=kis_plan, kis_view=kis_view)
        result = consumer_collection(request=request, policy=self.policies[request["run_id"]],
            whole=whole, monitoring=monitoring, seal=seal, finished_at=finished_at)
        verify_collection_seal(root, seal, frozen)
        return result, dict(whole_source_sha256=digest(whole), coverage_sha256=digest(coverage),
            monitoring_input_sha256=digest(monitoring), code_identity=self.code_identity,
            source_collection_seal_sha256=seal["receipt_sha256"], canonical_replay_count=2,
            qualified_projection=True, current_generation=request["attempt_id"])

    async def collect(self, request, directory):
        self.guard()
        policy = self.policies[request["run_id"]]
        if request["policy_sha256"] != digest(policy.model_dump(mode="json")):
            raise ValueError("production_source_runtime_policy_drift")
        root = Path(directory).resolve() / "source"
        deadline = time.monotonic() + 600
        frozen, compiler, kis_plan, credentials = self.context_factory(request=request, directory=root,
            settings=self.settings, configuration=self.configuration, implementation_sha=self.implementation_sha)
        try:
            outcome = await self.transport.collect(root=root, frozen=frozen, compiler=compiler,
                kis_plan=kis_plan, credentials=credentials, deadline=deadline)
        finally:
            for values in credentials.values():
                values.clear()
            credentials.clear()
        # The canonical aggregate owner materializes its deterministic receipt.
        # Finish that step before the immutable corpus inventory is sealed.
        require_captured_phase(root, frozen, outcome, 'stocks')
        market_inputs(root, frozen, outcome, POLICY)
        seal = seal_collection(root, seal_path=Path(directory) / "source-seal.json", frozen=frozen, outcome=outcome)
        finished_at = self.clock.now()
        if finished_at < datetime.fromisoformat(request["started_at"]):
            raise ValueError("production_source_clock_regressed")
        # Canonical offline replay owns nested event loops and performs no live
        # requests. No transport may execute after collection seal.
        result, replay = await asyncio.to_thread(self.project, root, frozen, outcome, kis_plan, seal, request, finished_at)
        durable_json(Path(directory) / "source-owner-replay.json", replay, exclusive=True)
        identity = (request["run_id"], request["attempt_id"])
        if identity in self.admitted:
            raise ValueError("production_source_generation_already_admitted")
        self.admitted[identity] = dict(root=root, frozen=frozen, seal=seal, replay=replay,
            collection_sha256=digest(result.model_dump(mode="json")))
        return result

    def verify(self, collection):
        self.guard()
        saved = self.admitted.get((collection.run_id, collection.attempt_id))
        if saved is None or digest(collection.model_dump(mode="json")) != saved["collection_sha256"]:
            raise ValueError("production_source_not_current_admitted_generation")
        verify_collection_seal(saved["root"], saved["seal"], saved["frozen"])
        receipt = read(saved["root"].parent / "source-owner-replay.json")
        if receipt != saved["replay"] or not receipt["qualified_projection"]:
            raise ValueError("production_source_owner_receipt_drift")
        return receipt
