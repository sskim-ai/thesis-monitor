"""Concrete current-cycle source backend; canonical owners remain authoritative."""
import asyncio
from datetime import datetime, timedelta, timezone
import math
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


async def _source_sync(function, /, *args, on_cancel=None, **kwargs):
    # A cancelled caller must not leave Source writes/handles behind in a thread.
    task = asyncio.create_task(asyncio.to_thread(function, *args, **kwargs))
    try:
        return await asyncio.shield(task)
    except asyncio.CancelledError:
        while not task.done():
            try:
                await asyncio.shield(task)
            except asyncio.CancelledError:
                continue
            except Exception:
                break
        if not task.cancelled():
            error = task.exception()
            if error is None and on_cancel is not None:
                on_cancel(task.result())
        raise


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
    @staticmethod
    async def prepare_registered(*, settings, registration_owner, run_ledger, root, frozen, compiler,
                                 credentials, policy, deadline, kis_plan=None, retained_sec=None,
                                 execution_generation=None, mixed_limitations=False, transport=None,
                                 manual_no_send=False, manual_source_seconds=None,
                                 routine_us_no_send_source_seconds=None):
        """Shared selected Source-only boundary; registration and plan stay original."""
        from app.services import prospective_class_c_owner as registration
        from app.services.selected_source_plan import SelectedRequestPlan, SelectedStockPlan, SCOPE
        from app.services.selected_source_preparation import prepare_child

        if frozen.get('scope') != SCOPE or run_ledger is None:
            raise ValueError('production_registered_selected_plan_required')
        routine = routine_us_no_send_source_seconds is not None
        if routine and (manual_source_seconds is not None or manual_no_send is not False
                or type(routine_us_no_send_source_seconds) is not int
                or not 600 <= routine_us_no_send_source_seconds <= 1800):
            raise ValueError('registered_routine_source_budget_invalid')
        registration.require_generation(registration_owner, frozen['generation_id'],
            purpose=registration.ROUTINE_SCOPE if routine else registration.SCOPE)
        plan = SelectedRequestPlan.model_validate(frozen['plan'])
        if (run_ledger.state()['plans'].get(plan.market) != plan.plan_sha256
                or frozen.get('shared_run_ledger') != run_ledger.worker_binding()):
            raise ValueError('production_registered_plan_ledger_mismatch')
        root = Path(root)
        if read(root/'production-frozen-source-plan.json') != frozen:
            raise ValueError('production_registered_sealed_plan_mismatch')
        ceiling = 600
        authority_expires = None
        if routine:
            decision = registration._approval(run_ledger.approval)
            _, owner_receipt = registration._state(registration_owner)
            run_ledger._external()
            identity = run_ledger.identity
            stock = SelectedStockPlan.model_validate(frozen['stock_plan'])
            child = run_ledger.selected_child(plan.market)
            maximum = identity.get('wallclock_seconds_max')
            if (plan.market != 'us' or frozen.get('execution_purpose') != registration.ROUTINE_SCOPE
                    or plan.purpose != registration.ROUTINE_SCOPE or identity.get('send') is not False
                    or identity.get('onboarding') or type(maximum) is not int or maximum <= 0
                    or decision.routine_us_no_send_source_seconds != routine_us_no_send_source_seconds
                    or identity.get('routine_us_no_send_source_seconds') != routine_us_no_send_source_seconds
                    or owner_receipt.get('routine_us_no_send_source_seconds') != routine_us_no_send_source_seconds
                    or plan.routine_us_no_send_source_seconds != routine_us_no_send_source_seconds
                    or stock.routine_us_no_send_source_seconds != routine_us_no_send_source_seconds
                    or owner_receipt['approval_sha256'] != identity['approval_sha256']
                    or digest(decision.model_dump(mode='json')) != identity['approval_sha256']
                    or identity['expires_at'] != decision.expires_at.isoformat()
                    or owner_receipt['market'] != plan.market or stock.market != plan.market
                    or plan.generation_id != frozen['generation_id'] or stock.run_id != plan.generation_id
                    or owner_receipt['source_generation_id'] != plan.generation_id
                    or child['generation'] != plan.generation_id or tuple(child['subjects']) != plan.subjects
                    or stock.subjects != plan.subjects or set(owner_receipt['bindings']) != set(plan.subjects)
                    or frozen.get('registration_receipt_sha256') != digest(owner_receipt)
                    or plan.stock_plan_sha256 != digest(stock.model_dump(mode='json'))
                    or stock.frozen_at.isoformat() != owner_receipt['cutoff']
                    or stock.universe_sha256 != digest(dict(market=plan.market, subjects=stock.subjects,
                        registration_sha256=digest(owner_receipt)))):
                raise ValueError('registered_routine_source_budget_not_approved')
            authority_expires = min(decision.expires_at, datetime.fromisoformat(owner_receipt['expires_at']),
                datetime.fromisoformat(identity['authorized_at'])+timedelta(seconds=maximum))
            ceiling = routine_us_no_send_source_seconds
        if manual_source_seconds is not None:
            if (manual_no_send is not True or type(manual_source_seconds) is not int
                    or not 600 <= manual_source_seconds <= 1800 or plan.market != 'us'):
                raise ValueError('registered_manual_source_budget_invalid')
            decision = registration._approval(run_ledger.approval)
            _, owner_receipt = registration._state(registration_owner)
            run_ledger._external()
            identity = run_ledger.identity
            maximum = identity.get('wallclock_seconds_max')
            if (decision.manual_no_send_source_seconds != manual_source_seconds
                    or owner_receipt['approval_sha256'] != identity['approval_sha256']
                    or digest(decision.model_dump(mode='json')) != identity['approval_sha256']
                    or owner_receipt['purpose'] != registration.SCOPE
                    or identity['children'][plan.market]['generation'] != plan.generation_id
                    or type(maximum) is not int or maximum < manual_source_seconds
                    or identity.get('onboarding') or identity['max_models'] < 1):
                raise ValueError('registered_manual_source_budget_not_approved')
            expires = min(decision.expires_at, datetime.fromisoformat(owner_receipt['expires_at']),
                datetime.fromisoformat(identity['authorized_at']) + timedelta(seconds=maximum))
            if (expires - datetime.now(timezone.utc)).total_seconds() < manual_source_seconds:
                raise ValueError('registered_manual_source_budget_exceeds_authority_window')
            ceiling = manual_source_seconds
        began = time.monotonic()
        if (type(deadline) not in (int, float) or not math.isfinite(deadline)
                or manual_source_seconds is not None and deadline > began + ceiling):
            raise ValueError('registered_source_deadline_outside_budget')
        effective_deadline = min(deadline, began + ceiling)
        if authority_expires is not None:
            effective_deadline = min(effective_deadline,
                began + (authority_expires-datetime.now(timezone.utc)).total_seconds())
        remaining = effective_deadline - began
        if remaining <= 0:
            raise TimeoutError('source_deadline_exceeded')
        collector = transport or NativeProductionSourceTransport(settings, run_ledger=run_ledger,
            registration_owner=registration_owner, source_policy=policy)
        budget = dict(ceiling_seconds=ceiling,
            manual_no_send=manual_source_seconds is not None, monotonic_deadline=effective_deadline,
            original_approval_sha256=run_ledger.identity['approval_sha256'])
        if routine:
            budget.update(purpose=registration.ROUTINE_SCOPE,
                routine_us_no_send_source_seconds=ceiling, authority_expires_at=authority_expires.isoformat(),
                plan_sha256=plan.plan_sha256, generation_id=plan.generation_id)
        durable_json(root.parent/'source-time-budget.json', budget, exclusive=True)
        terminal = 'FAILED_OR_CANCELLED'
        try:
            outcome = await asyncio.wait_for(collector.collect(root=root, frozen=frozen, compiler=compiler,
                kis_plan=kis_plan, credentials=credentials, deadline=effective_deadline,
                retained_sec=retained_sec), max(0, effective_deadline-time.monotonic()))
            terminal = 'COLLECTOR_RETURNED_REQUIRES_SOURCE_ADMISSION'
        finally:
            durable_json(root.parent/'source-time-result.json', dict(status=terminal,
                elapsed_seconds=time.monotonic()-began, ceiling_seconds=ceiling,
                monotonic_deadline=effective_deadline,
                note='Cancellation cleanup may finish after the collection deadline; no new requests allowed'),
                exclusive=True)
        run_ledger.source_captured(plan.market)
        require_captured_phase(root, frozen, outcome, 'stocks')
        market_inputs(root, frozen, outcome, policy)
        seal = await _source_sync(seal_collection, root,
            seal_path=root.parent/'source-seal.json', frozen=frozen, outcome=outcome)
        verify_collection_seal(root, seal, frozen)
        child, proof = await _source_sync(prepare_child, root=root, frozen=frozen, outcome=outcome,
            policy=policy, registration_owner=registration_owner, kis_plan=kis_plan, enabled=True,
            execution_generation=execution_generation, mixed_limitations=mixed_limitations,
            on_cancel=lambda result: result[0].owner.close())
        try:
            child.verify()
            child.plan.validate()
            run_ledger.source_owned(child)
        except BaseException:
            child.owner.close()
            raise
        return child, proof

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
        seal = await _source_sync(seal_collection, root,
            seal_path=Path(directory) / "source-seal.json", frozen=frozen, outcome=outcome)
        finished_at = self.clock.now()
        if finished_at < datetime.fromisoformat(request["started_at"]):
            raise ValueError("production_source_clock_regressed")
        # Canonical offline replay owns nested event loops and performs no live
        # requests. No transport may execute after collection seal.
        result, replay = await _source_sync(self.project, root, frozen, outcome, kis_plan, seal, request, finished_at)
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
