"""Default-OFF prepared-source research entry. No acquisition or notification ports.

Per-market children retain their original run/source/time identities. Only the
final manifest joins them; neither a master ID nor a hash grants source rights.
"""
import asyncio
from dataclasses import dataclass
import fcntl
from pathlib import Path
import re
from types import SimpleNamespace

from app.services.model_execution_plan import ModelExecutionPlan
from app.services.production_model_profile import SolHighCallBudget
from app.services.production_model_transport import OfficialProductionModelTransport
from app.services.production_monitoring_session import ProductionMonitoringSession
from app.services.production_runtime_bridge import ProductionRuntimeBridgeV1
from app.services.unified_run_artifacts import SECRET_KEY, durable_json, load_json
from app.services.unified_runtime_v2 import CONTRACT, STAGES, validate_stage_v2
from app.services.unified_snapshot_contract import digest
from app.services.vnext_execution_profile import SOL_HIGH_V1

TERMINAL = 'RESEARCH_NO_SEND_RENDER_TERMINAL'
RESEARCH_STAGES = STAGES[:-1]


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
        return dict(market=self.market, run_id=c.run_id, source_generation=c.source_generation,
            assessment_date=c.assessment_date, effective_at=c.effective_at, cutoff=c.cutoff,
            cohort_sha256=c.sha256, plan_sha256=self.plan.sha256,
            source_relationship_sha256=digest(self.owner.relationship(self.market)),
            consumed_source_sha256=digest(self.owner.source(self.market)),
            message_ids=['MARKET_'+self.market.upper(), *c.market_subjects[self.market]])


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
    return dict(stage=stage, planned_calls=calls, per_call_seconds=600,
        overhead_seconds=30, total_seconds=600*calls+30, retries=0)


class PreparedResearchBridge(ProductionRuntimeBridgeV1):
    def __init__(self, *, child, settings, model, clock):
        child.verify()
        if (model.call_budget.plan != child.plan or model.cohort_source_owner is not child.owner
                or model.call_budget.journal is None):
            raise ValueError('research_persistent_budget_and_original_owner_required')
        self.child = child
        self.child_binding = child.binding()
        super().__init__(settings=settings, sources=None, model=model, delivery=None, clock=clock,
            execution_profile=SOL_HIGH_V1)
        model.bind_cycle(market=child.market, run_id=child.plan.cohort.run_id)

    def snapshot(self):
        self.child.verify()
        if self.child.binding() != self.child_binding:
            raise ValueError('research_child_source_drift')
        c = self.child.plan.cohort
        return dict(contract='prepared-scoped-research-snapshot-v1', child_binding=self.child_binding,
            collection=dict(market=self.child.market, monitoring_input=self.child.owner.source(self.child.market),
                production_envelope=dict(generation_id=c.run_id, subjects=list(c.market_subjects[self.child.market]))))

    def _session(self, request, directory):
        expected = self.snapshot()
        if (request['snapshot'] != expected or request['snapshot_sha256'] != digest(expected)
                or request['run_id'] != self.child.plan.cohort.run_id):
            raise ValueError('research_child_snapshot_binding_mismatch')
        c = self.child.plan.cohort
        session = ProductionMonitoringSession(directory/'canonical', market=self.child.market,
            generation_id=c.run_id, source=expected['collection']['monitoring_input'],
            source_generation_id=c.source_generation, frozen_cohort=c, cohort_source_owner=self.child.owner)
        self._restore_upstream(session, request)
        return session, SimpleNamespace(production_envelope=SimpleNamespace(subjects=c.market_subjects[self.child.market]))

    async def policy(self, *args, **kwargs):
        raise ValueError('research_prepared_source_only_no_collection')

    async def collect(self, *args, **kwargs):
        raise ValueError('research_prepared_source_only_no_collection')

    async def notify_failure(self, payload):
        return dict(status='LOCAL_ONLY_NO_SEND', external_attempts=0)


def build_research_no_send_adapter(*, enabled=False, child, settings, binding, runtime_root,
                                   journal_path, approved_max_invocations, approved_plan_sha256, clock):
    if enabled is not True:
        raise ValueError('research_no_send_factory_disabled')
    child.verify()
    expected_journal = Path(runtime_root)/'invocation-ledger'/child.plan.cohort.run_id/'events.jsonl'
    if Path(journal_path).absolute() != expected_journal.absolute():
        raise ValueError('research_fixed_cycle_journal_required')
    budget = SolHighCallBudget(plan=child.plan, approved_max_invocations=approved_max_invocations,
        approved_plan_sha256=approved_plan_sha256, journal_path=journal_path)
    secrets = tuple(v.get_secret_value() if hasattr(v,'get_secret_value') else str(v)
        for k,v in settings.model_dump().items() if v and SECRET_KEY.search(k))
    model = OfficialProductionModelTransport(binding=binding, runtime_root=runtime_root,
        execution_profile=SOL_HIGH_V1, call_budget=budget, cohort_source_owner=child.owner, secrets=secrets)
    return PreparedResearchBridge(child=child, settings=settings, model=model, clock=clock)


async def run_prepared_research(bridge, *, root, enabled=False):
    if enabled is not True or type(bridge) is not PreparedResearchBridge:
        raise ValueError('explicit_prepared_research_entry_required')
    path = Path(root)/bridge.child.plan.cohort.run_id
    if any(p.is_symlink() for p in (path, *path.parents)):
        raise ValueError('research_cycle_symlink')
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
        try:
            if (path/'intent.json').exists():
                raise ValueError('interrupted_research_cycle_no_automatic_replay')
            durable_json(path/'intent.json',state,exclusive=True)
            snapshot = bridge.snapshot()
            outputs = {}
            for stage in RESEARCH_STAGES:
                bound = stage_deadline(bridge.child.plan, stage)
                request = dict(contract=CONTRACT, run_id=bridge.child.plan.cohort.run_id, stage=stage,
                    snapshot_sha256=digest(snapshot), snapshot=snapshot, inputs=dict(outputs),
                    configuration_sha256=digest(dict(purpose=TERMINAL, child_binding=bridge.child_binding)))
                directory = path/stage.lower()
                durable_json(directory/'request.json',request,exclusive=True)
                state['stage_receipts'].append(dict(stage=stage,deadline=bound,status='INTENT'))
                durable_json(path/'state.json',state)
                result = await asyncio.wait_for(bridge.stage(request,directory), bound['total_seconds'])
                validate_stage_v2(result,request)
                value = result.model_dump(mode='json')
                durable_json(directory/'response.json',value,exclusive=True)
                state['stage_receipts'][-1].update(status='PASS',response_sha256=digest(value))
                outputs[stage] = value
            messages = outputs['RENDER']['output']['messages']
            if (sorted(m['message_id'] for m in messages) != sorted(bridge.child_binding['message_ids'])
                    or digest(messages) != outputs['VALIDATE']['output']['content_sha256']
                    or set(bridge.model.call_budget.accepted) != {s.slot_id for s in bridge.child.plan.slots}
                    or any(m.get('NO_SEND') is not True or not m.get('text') for m in messages)):
                raise ValueError('research_render_coverage_or_content_drift')
            state.update(status=TERMINAL,messages=messages,messages_sha256=digest(messages))
        except (Exception, asyncio.CancelledError) as exc:
            from app.services.unified_market_run import UnifiedMarketRun
            state.update(status='FAILED_NO_SEND',error_chain=UnifiedMarketRun._error(exc))
            try:
                bridge.model.call_budget.stop()
            except Exception as ledger_error:
                state['ledger_failure'] = UnifiedMarketRun._error(ledger_error)
        durable_json(path/'terminal.json',state,exclusive=True)
        return state
