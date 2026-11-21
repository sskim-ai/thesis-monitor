"""Default-OFF prepared-source research entry. No acquisition or notification ports.

Per-market children retain their original run/source/time identities. Only the
final manifest joins them; neither a master ID nor a hash grants source rights.
"""
import asyncio
from contextvars import ContextVar
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
import fcntl
import json
import os
from pathlib import Path
import re

from app.services.model_execution_plan import ModelExecutionPlan
from app.services.production_model_profile import SolHighCallBudget
from app.services.production_model_transport import OfficialProductionModelTransport
from app.services.production_runtime_bridge import ProductionRuntimeBridgeV1
from app.services.research_artifact_budget import ArtifactCapacityError, ResearchArtifactBudget, artifact_scope, artifact_stage
from app.services.research_request_storage import save_stage_request
from app.services.unified_run_artifacts import SECRET_KEY, durable_json, load_json
from app.services.unified_runtime_v2 import CONTRACT, STAGES, validate_stage_v2
from app.services.unified_snapshot_contract import ContractModel, digest
from app.services.vnext_execution_profile import SOL_HIGH_V1

TERMINAL = 'RENDER_VERIFIED_NO_SEND'
PARTIAL = 'RENDER_VERIFIED_PARTIAL_NO_SEND'
RESEARCH_STAGES = STAGES[:-1]
MODEL_STAGES = frozenset({'MARKET', 'CORE', 'A', 'B', 'B2'})
FINALIZATION_STAGES = frozenset({'VALIDATE', 'RENDER'})
FINALIZATION_LOCAL_SECONDS = 600
_stage_timer = ContextVar('prepared_research_stage_timer', default=None)


class PreparedResearchEnvelope(ContractModel):
    """Typed serialization of the already owner-verified snapshot, not a grant."""
    generation_id: str
    subjects: tuple[str, ...]


@dataclass(frozen=True)
class MarketResearchChild:
    plan: ModelExecutionPlan
    owner: object

    def verify(self):
        self.plan.validate()
        if self.plan.topology != 'CANONICAL_PRODUCTION' or len(self.plan.cohort.market_subjects) != 1:
            raise ValueError('research_single_market_canonical_child_required')
        if (not re.fullmatch(r'[A-Za-z0-9_.:-]+',self.plan.cohort.run_id)
                or self.plan.cohort.run_id in ('.','..')):
            raise ValueError('research_child_run_path_invalid')
        self.plan.cohort.verify_source_owner(self.owner)

    @property
    def market(self):
        return next(iter(self.plan.cohort.market_subjects))

    def binding(self):
        self.verify()
        c = self.plan.cohort
        binding = dict(market=self.market, run_id=c.run_id, source_generation=c.source_generation,
            assessment_date=c.assessment_date, effective_at=c.effective_at, cutoff=c.cutoff,
            cohort_sha256=c.sha256, plan_sha256=self.plan.sha256,
            source_relationship_sha256=digest(self.owner.relationship(self.market)),
            consumed_source_sha256=digest(self.owner.source(self.market)),
            message_ids=['MARKET_'+self.market.upper(), *c.market_subjects[self.market]])
        if c.limitation_subjects:
            binding['limitation_subjects'] = list(c.limitation_subjects)
        return binding


@dataclass(frozen=True)
class MasterFourPanelManifest:
    parent_id: str
    children: tuple[MarketResearchChild, ...]

    def binding(self):
        rows = [c.binding() for c in self.children]
        if (not self.parent_id or sorted(r['market'] for r in rows) != ['kr','us']
                or any(len(r['message_ids']) != 2 for r in rows)
                or len({r['run_id'] for r in rows}) != 2):
            raise ValueError('four_panel_distinct_market_children_required')
        return dict(contract='master-four-panel-manifest-v1', parent_id=self.parent_id,
            children=sorted(rows,key=lambda r:r['market']), purpose=TERMINAL)

    def combine(self, results):
        binding = self.binding()
        if set(results) != {'us','kr'}:
            raise ValueError('four_panel_child_results_incomplete')
        messages = []
        for child in binding['children']:
            result = results[child['market']]
            rows = result.get('messages', [])
            if (result.get('status') != TERMINAL or result.get('child_binding') != child
                    or result.get('normal_messages_sent') is not False
                    or sorted(r['message_id'] for r in rows) != sorted(child['message_ids'])
                    or digest(rows) != result.get('messages_sha256')
                    or [r.get('stage') for r in result.get('stage_receipts', [])] != list(RESEARCH_STAGES)
                    or any(r.get('status') != 'PASS' for r in result['stage_receipts'])
                    or any(m.get('NO_SEND') is not True for m in rows)):
                raise ValueError('four_panel_original_child_terminal_required')
            messages.extend(rows)
        return dict(status=TERMINAL, manifest=binding, manifest_sha256=digest(binding),
            children_sha256={m:digest(r) for m,r in results.items()}, messages=messages,
            messages_sha256=digest(messages), normal_messages_sent=False, failure_notifications_sent=False)


def stage_deadline(plan, stage):
    plan.validate()
    if stage not in RESEARCH_STAGES:
        raise ValueError('research_stage_not_allowed')
    calls = sum(s.stage == stage for s in plan.slots)
    # Both finalization stages restore and render the entire accepted cohort.
    total = FINALIZATION_LOCAL_SECONDS if stage in FINALIZATION_STAGES else 600*calls+30
    return dict(stage=stage, planned_calls=calls, per_call_seconds=600,
        overhead_seconds=30, total_seconds=total, retries=0)


def _split_stage_deadline(bound, multi_batch_local_seconds):
    stage = bound['stage']
    result = dict(bound, local_seconds=None if stage in MODEL_STAGES else FINALIZATION_LOCAL_SECONDS,
        scope=('MODEL_LOCAL_UNLIMITED_CAMPAIGN_AND_PER_CALL_CAPPED' if stage in MODEL_STAGES
            else 'SEPARATE_LOCAL_AND_WORKER_CAMPAIGN_CAPPED'))
    del result['total_seconds']
    return result


class _StageTimer:
    """Bound workers and finalization locally; all phases retain the campaign cap."""
    def __init__(self, deadline, loop, campaign_end, retry_cap=0):
        self.deadline, self.loop, self.campaign_end = deadline, loop, campaign_end
        self.local_seconds = self.worker_seconds = 0.0
        self.phase, self.began, self.calls = 'local', loop.time(), 0
        limit = deadline['local_seconds']
        self.timeout = asyncio.timeout_at(campaign_end if limit is None else min(self.began+limit,campaign_end))
        self.retry_cap = retry_cap

    def check(self):
        now = self.loop.time()
        if now >= self.campaign_end:
            raise TimeoutError('research_campaign_deadline')
        if self.timeout.when() is not None and now >= self.timeout.when():
            raise TimeoutError('research_'+self.phase+'_deadline')

    def switch(self, phase):
        self.check()
        now = self.loop.time()
        if phase == 'worker':
            self.local_seconds += now-self.began
            self.calls += 1
            if self.calls > self.deadline['planned_calls']+self.retry_cap:
                raise ValueError('research_stage_worker_count_exceeded')
            remaining = self.deadline['per_call_seconds']+self.deadline['overhead_seconds']
        else:
            self.worker_seconds += now-self.began
            limit = self.deadline['local_seconds']
            remaining = None if limit is None else limit-self.local_seconds
        self.phase, self.began = phase, now
        self.timeout.reschedule(self.campaign_end if remaining is None else min(now+remaining,self.campaign_end))
        self.check()

    def receipt(self):
        elapsed = self.loop.time()-self.began
        return dict(local_seconds=round(self.local_seconds+(elapsed if self.phase=='local' else 0),3),
            worker_seconds=round(self.worker_seconds+(elapsed if self.phase=='worker' else 0),3),
            worker_windows=self.calls, final_phase=self.phase)


def current_stage_timer():
    return _stage_timer.get()


def _first_failure(exc, stage):
    failure = dict(type=type(exc).__name__[:80], code='RESEARCH_STAGE_FAILED', stage=stage,
        at=datetime.now(timezone.utc).isoformat())
    if isinstance(exc, ArtifactCapacityError):
        receipt = exc.receipt
        code = receipt.get('code', '')
        if re.fullmatch(r'RESEARCH_[A-Z_]{1,80}', code):
            failure['code'] = code
        failure['storage'] = {k: receipt[k] for k in ('current_bytes', 'projected_bytes', 'cap_bytes')
            if type(receipt.get(k)) is int}
    return failure


def _persist_first_failure(path, state):
    """Only this bounded, payload-free receipt may bypass the artifact free guard."""
    directory = None
    pending = False
    try:
        raw = json.dumps(state['first_failure'], sort_keys=True, separators=(',', ':')).encode()+b'\n'
        if len(raw) > 4096:
            raise ValueError('research_first_failure_receipt_too_large')
        directory = os.open(path, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)
        fd = os.open('.first-failure.pending', os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW,
            0o600, dir_fd=directory)
        pending = True
        with os.fdopen(fd, 'wb') as stream:
            stream.write(raw)
            stream.flush()
            os.fsync(stream.fileno())
        os.link('.first-failure.pending', 'first-failure.json', src_dir_fd=directory,
            dst_dir_fd=directory, follow_symlinks=False)
        os.fsync(directory)
        state['first_failure_receipt'] = dict(status='PERSISTED', bytes=len(raw))
    except Exception as error:
        state['first_failure_receipt'] = dict(status='UNAVAILABLE', type=type(error).__name__,
            errno=error.errno if isinstance(error, OSError) else None)
    finally:
        if directory is not None:
            if pending:
                try:
                    os.unlink('.first-failure.pending', dir_fd=directory)
                except OSError:
                    pass
            try:
                os.close(directory)
            except OSError:
                pass


class PreparedResearchBridge(ProductionRuntimeBridgeV1):
    def __init__(self, *, child, settings, model, clock, retained_kr_ecos_body=None):
        child.verify()
        if (model.call_budget.plan != child.plan or model.cohort_source_owner is not child.owner
                or model.call_budget.journal is None):
            raise ValueError('research_persistent_budget_and_original_owner_required')
        if retained_kr_ecos_body is not None and (child.market != 'kr' or model.call_budget.market_origin is None):
            raise ValueError('research_retained_kr_display_requires_market_origin')
        self._retained_kr_ecos_body = retained_kr_ecos_body
        self.child = child
        self.child_binding = child.binding()
        super().__init__(settings=settings, sources=None, model=model, delivery=None, clock=clock,
            execution_profile=SOL_HIGH_V1)
        model.bind_cycle(market=child.market, run_id=child.plan.cohort.run_id)

    def _render_market(self, session):
        if self._retained_kr_ecos_body is None:
            return super()._render_market(session)
        from app.services.production_message_renderer import market_message
        from app.services.production_source_context import POLICY

        return market_message(session,sector_taxonomy_version='sector-universe-user-confirmed-v2',
            ecos_fx_body=self._retained_kr_ecos_body,fx_source_policy=POLICY)

    def snapshot(self):
        self.child.verify()
        if self.child.binding() != self.child_binding:
            raise ValueError('research_child_source_drift')
        c = self.child.plan.cohort
        return dict(contract='prepared-scoped-research-snapshot-v1', child_binding=self.child_binding,
            collection=dict(market=self.child.market, monitoring_input=self.child.owner.source(self.child.market),
                production_envelope=dict(generation_id=c.run_id, subjects=list(c.market_subjects[self.child.market]))))

    async def policy(self, *args, **kwargs):
        raise ValueError('research_prepared_source_only_no_collection')

    async def collect(self, *args, **kwargs):
        raise ValueError('research_prepared_source_only_no_collection')

    async def notify_failure(self, payload):
        return dict(status='LOCAL_ONLY_NO_SEND', external_attempts=0)


def build_research_no_send_adapter(*, enabled=False, child, settings, binding, runtime_root,
                                   journal_path, approved_max_invocations, approved_plan_sha256, clock, run_ledger=None,
                                   market_origin=None, artifact_budget=None, retained_kr_ecos_body=None,
                                   timeout_retry_cap=0, b2_retry_policy=None):
    if enabled is not True:
        raise ValueError('research_no_send_factory_disabled')
    child.verify()
    expected_journal = Path(runtime_root)/'invocation-ledger'/child.plan.cohort.run_id/'events.jsonl'
    if Path(journal_path).absolute() != expected_journal.absolute():
        raise ValueError('research_fixed_cycle_journal_required')
    with artifact_scope(artifact_budget):
        budget = SolHighCallBudget(plan=child.plan, approved_max_invocations=approved_max_invocations,
            approved_plan_sha256=approved_plan_sha256, journal_path=journal_path, run_ledger=run_ledger,
            market_origin=market_origin, timeout_retry_cap=timeout_retry_cap, b2_retry_policy=b2_retry_policy)
    secrets = tuple(v.get_secret_value() if hasattr(v,'get_secret_value') else str(v)
        for k,v in settings.model_dump().items() if v and SECRET_KEY.search(k))
    model = OfficialProductionModelTransport(binding=binding, runtime_root=runtime_root,
        execution_profile=SOL_HIGH_V1, call_budget=budget, cohort_source_owner=child.owner, secrets=secrets)
    bridge = PreparedResearchBridge(child=child, settings=settings, model=model, clock=clock,
        retained_kr_ecos_body=retained_kr_ecos_body)
    bridge.artifact_budget = artifact_budget
    return bridge


async def run_prepared_research(bridge, *, root, enabled=False, local_output_rejection=False,
                                split_model_timing=False, multi_batch_local_seconds=600):
    if enabled is not True or type(bridge) is not PreparedResearchBridge:
        raise ValueError('explicit_prepared_research_entry_required')
    if (type(multi_batch_local_seconds) is not int or not 600 <= multi_batch_local_seconds <= 900
            or (multi_batch_local_seconds != 600 and split_model_timing is not True)):
        raise ValueError('research_multi_batch_local_limit_not_allowed')
    campaign_end = None
    if getattr(bridge.model.call_budget,'retry_enabled',False) and split_model_timing is not True:
        raise ValueError('research_timeout_retry_requires_campaign_timer')
    if split_model_timing is True:
        ledger = bridge.model.call_budget.run_ledger
        if type(bridge.model) is not OfficialProductionModelTransport or ledger is None:
            raise ValueError('split_model_timing_requires_original_ledger_and_transport')
        maximum = ledger.identity['wallclock_seconds_max']
        expires = min(datetime.fromisoformat(ledger.identity['expires_at']),
            datetime.fromisoformat(ledger.identity['authorized_at'])+timedelta(seconds=maximum))
        campaign_end = asyncio.get_running_loop().time()+(expires-datetime.now(timezone.utc)).total_seconds()
    path = Path(root)/bridge.child.plan.cohort.run_id
    if any(p.is_symlink() for p in (path, *path.parents)):
        raise ValueError('research_cycle_symlink')
    budget = getattr(bridge, 'artifact_budget', None)
    if budget is None:
        roots = {path: 'result'}
        runtime = getattr(bridge.model, 'runtime_root', None)
        if runtime is not None:
            roots[runtime] = 'scratch'
        journal = bridge.model.call_budget.journal
        if journal is not None:
            roots[journal.path] = 'result'
        ledger = getattr(bridge.model.call_budget, 'run_ledger', None)
        if ledger is not None:
            roots[ledger.path] = 'result'
        budget = ResearchArtifactBudget(roots=roots)
    with artifact_scope(budget):
        return await _run(bridge, path, local_output_rejection=local_output_rejection,
            artifacts=budget, campaign_end=campaign_end, multi_batch_local_seconds=multi_batch_local_seconds)


async def _run(bridge, path, *, local_output_rejection, artifacts, campaign_end=None, multi_batch_local_seconds=600):
    path.mkdir(parents=True, exist_ok=True, mode=0o700)
    with (path/'cycle.lock').open('a') as lock:
        try:
            fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            return dict(status='ALREADY_RUNNING', normal_messages_sent=False)
        if (path/'terminal.json').exists():
            return load_json(path/'terminal.json')
        state = dict(status='STARTED', child_binding=bridge.child_binding, stage_receipts=[],
            normal_messages_sent=False, failure_notifications_sent=False)
        stage = 'INITIALIZE'
        try:
            if (path/'intent.json').exists():
                raise ValueError('interrupted_research_cycle_no_automatic_replay')
            durable_json(path/'intent.json',state,exclusive=True)
            snapshot = bridge.snapshot()
            snapshot_pin = digest(snapshot)
            outputs = {}
            for stage in RESEARCH_STAGES:
                with artifact_stage(stage):
                    bound = stage_deadline(bridge.child.plan, stage)
                    if campaign_end is not None:
                        bound = _split_stage_deadline(bound, multi_batch_local_seconds)
                        retry_cap = getattr(bridge.model.call_budget,'timeout_retry_cap',0)
                        if retry_cap and bound['planned_calls']:
                            bound['campaign_timeout_retry_cap'] = retry_cap
                        if getattr(bridge.model.call_budget,'b2_retry_policy',None) and stage == 'B2':
                            bound['b2_retry_policy'] = bridge.model.call_budget.b2_retry_policy
                        if stage == 'MARKET':
                            from app.services.model_timeout_retry import market_timeout_retry_cap
                            if market_timeout_retry_cap(getattr(bridge.model.call_budget,'b2_retry_policy',None)):
                                bound['market_timeout_retry_cap'] = 1
                    request = dict(contract=CONTRACT, run_id=bridge.child.plan.cohort.run_id, stage=stage,
                        snapshot_sha256=snapshot_pin, snapshot=snapshot, inputs=dict(outputs),
                        configuration_sha256=digest(dict(purpose=TERMINAL, child_binding=bridge.child_binding)))
                    directory = path/stage.lower()
                    saved = save_stage_request(path, request)
                    state['stage_receipts'].append(dict(stage=stage,deadline=bound,status='INTENT',**saved))
                    durable_json(path/'state.json',state)
                    if campaign_end is None:
                        result = await asyncio.wait_for(bridge.stage(request,directory), bound['total_seconds'])
                    else:
                        receipt = state['stage_receipts'][-1]
                        loop = asyncio.get_running_loop()
                        allowance = (bridge.model.call_budget.retry_capacity
                            if getattr(bridge.model.call_budget,'b2_retry_policy',None) and stage == 'B2'
                            else bound.get('market_timeout_retry_cap',getattr(bridge.model.call_budget,'timeout_retry_cap',0)))
                        timer = _StageTimer(bound,loop,campaign_end, allowance)
                        token = _stage_timer.set(timer)
                        try:
                            async with timer.timeout:
                                timer.check()
                                result = await bridge.stage(request,directory)
                                timer.check()
                        finally:
                            _stage_timer.reset(token)
                            receipt['timing'] = timer.receipt()
                    validate_stage_v2(result,request)
                    value = result.model_dump(mode='json')
                    durable_json(directory/'response.json',value,exclusive=True)
                    state['stage_receipts'][-1].update(status='PASS',response_sha256=digest(value))
                    outputs[stage] = value
            if campaign_end is not None and asyncio.get_running_loop().time() >= campaign_end:
                raise TimeoutError('research_campaign_deadline')
            messages = outputs['RENDER']['output']['messages']
            calls = bridge.model.call_budget
            inherited = set(calls.inherited)
            accepted = set(calls.accepted)
            omitted = outputs['B2']['output'].get('unissued',{})
            exhausted = getattr(calls,'exhausted',set())
            if (omitted and not getattr(calls,'retry_enabled',False)
                    or sorted(m['message_id'] for m in messages) != sorted(set(bridge.child_binding['message_ids'])-set(omitted))
                    or digest(messages) != outputs['VALIDATE']['output']['content_sha256']
                    or exhausted != {v['slot_id'] for v in omitted.values()}
                    or accepted != {s.slot_id for s in bridge.child.plan.slots}-exhausted
                    or calls.used & inherited or accepted != (calls.used-exhausted) | inherited
                    or any(m.get('NO_SEND') is not True or not m.get('text') for m in messages)):
                raise ValueError('research_render_coverage_or_content_drift')
            if getattr(calls,'retry_enabled',False):
                from app.services.model_invocation_journal import read_invocation_journal
                from app.services.model_timeout_retry import verify_render_partition

                verify_render_partition(messages=messages, subjects=bridge.child.plan.cohort.market_subjects['us'],
                    slots=bridge.child.plan.slots, b2=outputs['B2']['output'],
                    journal=read_invocation_journal(calls.journal.path.read_bytes(), calls.journal.identity),
                    accepted_content_sha256=outputs['VALIDATE']['output']['content_sha256'],plan=bridge.child.plan)
            state.update(status=PARTIAL if omitted else TERMINAL,messages=messages,messages_sha256=digest(messages))
            if bridge.child.plan.cohort.limitation_subjects:
                from app.services.model_execution_plan import verify_mixed_render

                receipts = outputs['RENDER']['output']['limitation_receipts']
                if receipts != outputs['VALIDATE']['output']['limitation_receipts']:
                    raise ValueError('research_limitation_validate_render_drift')
                verify_mixed_render(bridge.child.plan, messages, receipts)
                state['limitation_receipts'] = receipts
            if omitted:
                state.update(unissued=omitted, expected_message_count=len(bridge.child_binding['message_ids']))
            state['model_acceptances'] = calls.state()
            state['storage_inventory'] = artifacts.measure()
        except (Exception, asyncio.CancelledError) as exc:
            from app.services.unified_market_run import UnifiedMarketRun
            state.update(status='FAILED_NO_SEND',error_chain=UnifiedMarketRun._error(exc),
                first_failure=_first_failure(exc, stage))
            for key in ('messages', 'messages_sha256', 'limitation_receipts'):
                state.pop(key, None)
            if isinstance(exc, ArtifactCapacityError):
                state['storage_failure'] = exc.receipt
            try:
                from app.services.canonical_monitoring_io import BatchFailure
                from app.services.production_b2_execution import SemanticReject
                # Only an explicit canonical-output failure is child-local.
                # Transport, authentication, boundary and ledger errors stay global.
                local=(local_output_rejection is True and (isinstance(exc,(BatchFailure,SemanticReject))
                    or type(exc) is ValueError and str(exc)=='production_canonical_semantic_reject'))
                bridge.model.call_budget.stop(global_stop=not local)
            except Exception as ledger_error:
                state['ledger_failure'] = UnifiedMarketRun._error(ledger_error)
            _persist_first_failure(path, state)
        try:
            durable_json(path/'terminal.json',state,exclusive=True)
        except (ArtifactCapacityError, OSError) as exc:
            from app.services.unified_market_run import UnifiedMarketRun
            state.update(status='FAILED_NO_SEND', terminal_write_blocked=(exc.receipt
                if isinstance(exc, ArtifactCapacityError) else dict(type=type(exc).__name__, errno=exc.errno)))
            if 'first_failure' not in state:
                state.update(first_failure=_first_failure(exc, stage), error_chain=UnifiedMarketRun._error(exc))
                _persist_first_failure(path, state)
                try:
                    bridge.model.call_budget.stop(global_stop=True)
                except Exception as ledger_error:
                    state['ledger_failure'] = UnifiedMarketRun._error(ledger_error)
            for key in ('messages', 'messages_sha256', 'limitation_receipts'):
                state.pop(key, None)
        return state
