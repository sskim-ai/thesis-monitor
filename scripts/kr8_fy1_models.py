"""KR8-only fresh official-model proof, separate from all22 and production."""
import asyncio
from dataclasses import asdict
from pathlib import Path
import sys

from app.services.current_fresh_valuation import CurrentValuationView
from app.services.cross_market_decision_engine_service import DecisionEvidencePacket
from app.services.detailed_stock_message_service import build_detailed_plan, build_unknown_plan
from app.services.accepted_decision_v2_service import render_accepted_v2_production
from app.services.kr_forward_valuation_context import KrForwardValuationView, calibration_context
from app.services.kr_forward_valuation_message import build_plan, audit
from app.services.unified_snapshot_contract import digest
from app.services.unified_run_artifacts import durable_json
from scripts import qualified_official_launch_context as q
from scripts import m12dr_fresh_blind_reproof as p
from scripts.r9_rev11_models import FreshExecution, owner
from scripts.kr8_kis_integration import SUBJECTS
from scripts.kr8_source_scope import require_kr8_plan
from scripts.m12ds_r4_r1_accepted_capture import stock_plan
from scripts.m12ds_r4_offline_capture import capture_payload
from scripts.r9_offline_stage_replay import replay_market

AUTHORITY=p.REPO/'docs/work-instructions/20260930-rev31-c1-state-ownership-clarification.md'


class Kr8Execution(FreshExecution):
    MARKET_SCOPES=('kr',)
    SUBJECT_COUNT=8
    CALL_LIMITS={'market':1,'core':3,'pass-a':3,'pass-b':3}
    SUCCESS_TERMINAL='R2B_R9_REV40_R1_KR8_FULL_FRESH_CURRENT_FY1_FPER_8_MESSAGE_PASS_READY_FOR_REVIEW'

    def __init__(self, root, sources, kis_root, kis_view, kis_plan, source_only):
        super().__init__(root,sources)
        require_kr8_plan(self.source_frozen)
        self.kis_root,self.kis_view_path,self.kis_plan_path,self.source_only=map(Path,(kis_root,kis_view,kis_plan,source_only))
        self.kis_view,self.kis_plan=p.read(self.kis_view_path),p.read(self.kis_plan_path)
        p.require(self.kis_view['generation_id']==self.source_gen==self.kis_plan['generation_id'],'KR8_KIS_GENERATION_GAP')
        p.require(self.kis_view['scope']=='KR8_ONLY' and len(self.kis_view['rows'])==8 and
            {r['security_code'] for r in self.kis_view['rows']}==set(SUBJECTS),'KR8_KIS_COHORT_GAP')
        p.require(self.kis_view['rows_sha256']==digest(self.kis_view['rows']),'KR8_KIS_VIEW_HASH_GAP')
        self.qualified=None
        self.names=q.inventory_names()
        self.entry_environment=q.environment(self.names)
        self.guard=q.ManualMutationGuard([p.OPERATING,Path.home()/'.codex',self.sources,self.kis_root,
            self.kis_view_path,self.kis_plan_path,self.source_only,Path.home()/'Library/LaunchAgents'])

    def batch_topology(self):
        rows=[r for r in owner._batch_topology() if r['market']=='kr']
        p.require(len(rows)==3 and sorted(t for r in rows for t in r['subjects'])==list(SUBJECTS),
            'KR8_BATCH_TOPOLOGY_GAP')
        return rows

    def forward_view(self,ticker):
        row=next(r for r in self.kis_view['rows'] if r['security_code']==ticker)
        return KrForwardValuationView(native=CurrentValuationView.model_validate(self.fresh_stocks[ticker]['valuation_view']),
            kis=row,as_of=self.kis_plan['as_of'],fresh_plan_sha256=self.kis_plan['receipt_sha256'],
            source_corpus_sha256=digest(self.kis_view))

    def valuation_context(self,ticker):
        p.require(ticker in SUBJECTS,'KR8_FOREIGN_VALUATION_CONTEXT')
        return calibration_context(self.forward_view(ticker))

    def capture(self,stage_name,spec,context,schema,prompt):
        p.require(spec['market']=='kr','KR8_US_REQUEST_FORBIDDEN')
        expected=[] if stage_name=='market' else next(
            (r['subjects'] for r in self.batch_topology() if r['batch']==spec['batch']),None)
        p.require(expected==spec['subjects'],'KR8_REQUEST_SUBJECT_SCOPE')
        return super().capture(stage_name,spec,context,schema,prompt)

    def freeze_extra(self):
        return dict(scope='KR8_ONLY',kis_sources=p.manifest(self.kis_root),
            kis_view_sha256=p.sha(self.kis_view_path),kis_plan_sha256=p.sha(self.kis_plan_path),
            source_only_zip_sha256=p.sha(self.source_only),maintenance_authorization_sha256=p.sha(AUTHORITY))

    def prepare(self):
        # The source-only artifact is externally sealed before requests/model launch.
        p.require(self.source_only.is_file(),'KR8_SOURCE_ONLY_SEAL_REQUIRED')
        super().prepare()
        contexts={t:self.valuation_context(t) for t in SUBJECTS}
        durable_json(self.report/'valuation-visibility-preflight.json',dict(status='PASS',
            scope='KR8_ONLY',core_contexts_frozen_without_valuation=True,
            pass_a_capture_guard='require_direction_isolation',
            expected_pass_b_contexts=contexts,overall_direction_use=False),exclusive=True)

    def verify(self):
        super().verify()
        require_kr8_plan(self.source_frozen)
        p.require(self.frozen['scope']=='KR8_ONLY' and self.frozen['max_calls']==10,'KR8_MODEL_BUDGET_SCOPE')
        p.require(set(self.prepared)==set(SUBJECTS) and set(self.projected)=={'kr'},'KR8_MODEL_INPUT_SCOPE')
        p.require(self.freeze_extra()=={k:self.frozen[k] for k in self.freeze_extra()},'KR8_SOURCE_OR_AUTHORITY_DRIFT')
        p.require(self.guard.blocked_attempts==0,'KR8_MANUAL_MUTATION_ATTEMPT')
        p.require(sum(r['attempts'] for r in self.ledger)<=10,'KR8_CALL_BUDGET')
        p.require(all(r['market']=='kr' and set(r['subjects'])<=set(SUBJECTS) for r in self.ledger),'KR8_CALL_SCOPE')

    def identity(self):
        return q.LaunchIdentity(implementation_sha=self.frozen['controller']['head'],source_generation_id=self.source_gen,
            whole_source_sha256=self.frozen['fresh_source_replay']['first_sha256'],
            source_only_zip_sha256=self.frozen['source_only_zip_sha256'],
            request_freeze_sha256=p.sha(self.report/'execution-freeze.json'),
            prompt_schema_sha256=q.digest(p.read(self.sealed/'initial-requests.json')),
            executable_sha256=p.binding().executable_sha256,
            launcher_sha256=p.sha(p.REPO/'app/services/official_codex_shadow_transport_service.py'),
            qualification_sha256=p.binding().qualification_sha256,cwd_sha256=q.legacy.digest(str(p.REPO)))

    def current_launch_context(self):
        return q.capture_context(self.names)

    def qualify_host(self,secret_scan):
        self.verify()
        context=self.current_launch_context()
        evidence=q.StateWriteEvidence('CONTROLLER_ONLY_OFFICIAL_MAINTENANCE_AUTHORIZED',0,0,
            q.digest(context),p.binding().executable_sha256,
            p.sha(p.REPO/'app/services/official_codex_shadow_transport_service.py'),p.sha(AUTHORITY))
        identity=self.identity()
        qualified=q.QualifiedOfficialModelLaunchContext.qualify(identity=identity,expected_identity=identity,
            preparation=p.read(self.report/'host-context.json'),preparation_sha256=self.frozen['host_context_sha256'],
            actual_preparation_sha256=p.sha(self.report/'host-context.json'),context=context,
            entry_environment=self.entry_environment,state_evidence=evidence,binding_verified=True,
            provider_calls=0,secret_scan_passed=secret_scan(dict(context=context,identity=asdict(identity),evidence=asdict(evidence))),
            expected_maintenance_authorization_sha256=self.frozen['maintenance_authorization_sha256'])
        durable_json(self.report/'qualified-actual-host.json',qualified.receipt(),exclusive=True)
        freeze=dict(contract=q.CONTRACT,authority_sha256=qualified.sha256,
            receipt_file_sha256=p.sha(self.report/'qualified-actual-host.json'),qualified_at=p.now(),
            native_internal_maintenance='AUTHORIZED_NOT_MEASURED_AS_ZERO',direct_db_write_calls=0,
            permission_mutations=0,source_only_sha256=p.sha(self.source_only))
        durable_json(self.report/'official-model-execution-context-freeze.json',freeze,exclusive=True)
        self.qualified=qualified
        self.context_freeze_sha=p.sha(self.report/'official-model-execution-context-freeze.json')

    def authorize_launch_context(self,context):
        p.require(self.qualified is not None,'KR8_QUALIFIED_HOST_REQUIRED')
        self.verify()
        freeze=p.read(self.report/'official-model-execution-context-freeze.json')
        p.require(p.sha(self.report/'official-model-execution-context-freeze.json')==self.context_freeze_sha,
            'KR8_CONTEXT_FREEZE_DRIFT')
        p.require(p.sha(self.report/'qualified-actual-host.json')==freeze['receipt_file_sha256'],'KR8_HOST_RECEIPT_DRIFT')
        receipt=self.qualified.verify(context=context,identity=self.identity(),
            preparation_sha256=p.sha(self.report/'host-context.json'),freeze_sha256=freeze['authority_sha256'])
        durable_json(self.report/'per-call-contexts'/f'{len(self.ledger):02d}.json',receipt,exclusive=True)

    def run_qualified(self,secret_scan):
        self.guard.roots+=tuple(path.resolve() for path in [self.root/'inputs',self.report/'execution-freeze.json',
            self.report/'host-context.json',self.sealed/'initial-requests.json',self.requests/'core',self.requests/'market'])
        sys.addaudithook(self.guard)
        self.qualify_host(secret_scan)
        self.guard.roots+=tuple((self.report/name).resolve() for name in [
            'qualified-actual-host.json','official-model-execution-context-freeze.json'])
        super().run()
        durable_json(self.report/'direct-mutation-guard.json',dict(blocked_attempts=self.guard.blocked_attempts,
            direct_db_writes=0,permission_mutations=0,native_internal_state_management='AUTHORIZED_CLI_OWNED'),exclusive=True)

    def render(self):
        from scripts.sealed_cohort_offline_proof import network_guard
        self.verify()
        network_guard()
        output=self.root/'messages'
        output.mkdir(exist_ok=False)
        whole=p.read(self.root/'inputs/whole.json')
        support=replay_market(whole,'kr',self.markets['kr'])['capture']
        p.write(output/'supporting-market-kr.json',support)
        records=[]
        for ticker in SUBJECTS:
            source=self.fresh_stocks[ticker]
            packet=DecisionEvidencePacket.model_validate(source['evidence_packet'])
            valuation=CurrentValuationView.model_validate(source['valuation_view'])
            if self.prepared[ticker]['mode']=='UNKNOWN_LIMIT':
                base=build_unknown_plan(source_stock=source,source_authority=self.prepared[ticker]['source_authority'],
                    local_seed=self.locals[ticker],decision=self.limits['pass-b'][ticker],
                    execution_generation_id=self.gen,valuation=valuation)
            else:
                base=build_detailed_plan(packet=packet,accepted=stock_plan(self,ticker,packet),source_stock=source,
                    core=self.cores[ticker],pass_a=self.arows[ticker],valuation=valuation)
            plan=build_plan(packet,base,self.forward_view(ticker))
            rendered=render_accepted_v2_production(packet,plan)
            p.require(rendered.validation.valid,'KR8_RENDER_VALIDATION:'+ticker)
            checked=audit(rendered.text,packet,plan)
            receipt=asyncio.run(capture_payload(dict(type='stock_review',market='kr',ticker=ticker,
                text=rendered.text,use_llm=False)))
            p.require(receipt['production_sends']==0 and receipt['network_requests']==0,'KR8_DELIVERY_NOT_DISABLED')
            (output/(ticker+'.txt')).write_text(receipt['prepared_text'])
            p.write(output/'bindings'/(ticker+'.json'),dict(plan=plan.model_dump(mode='json'),audit=checked))
            p.write(output/'receipts'/(ticker+'.json'),receipt)
            records.append(dict(ticker=ticker,sha256=receipt['prepared_text_sha256']))
        p.require(len(records)==8,'KR8_EXACT_STOCK_MESSAGES_REQUIRED')
        p.write(output/'manifest.json',dict(scope='KR8_ONLY',generation_id=self.gen,
            source_generation_id=self.source_gen,stock_messages=records,stock_message_count=8,
            supporting_market_count=1,US_MESSAGES=0,production_sends=0))
