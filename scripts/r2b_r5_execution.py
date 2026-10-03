"""Frozen, fail-stop local Monitoring-AI controller; no acquisition or delivery.

R2B UNKNOWN_LIMIT uses its existing typed contract in each batch. Ordinary
subjects keep the accepted Core/A/B owners. Dependent requests are frozen only
after the preceding stage is validated; availability probes are never outputs.
"""
import argparse
from copy import deepcopy
from datetime import datetime, timezone
import json
from pathlib import Path
import shutil
import sys
import traceback

from app.services.unified_snapshot_contract import digest
from scripts import r2b_r2_preflight as pre
from scripts import r2b_r4_preflight as r4
from scripts import m12dr_fresh_blind_reproof as p
from scripts import m12ds_launch_context as launch
from scripts.m12ds_same_blind_reproof import Reproof as OfficialLaunch
from scripts.m12ds_r2_shadow_reproof import Reproof as CaptureOwner
from scripts import m12ds_r4_r4_market as market_owner
from scripts.m12ds_r2_ranges import materialize_ranges

c, owner = pre.c, pre.owner
STAGES = ('market', 'core', 'pass-a', 'pass-b')
MAX_CALLS = dict(zip(STAGES, (2, 8, 8, 8), strict=True))


def add_limits(schema, inputs, specs):
    """Compose existing limitation schema without changing ordinary row schemas."""
    schema = deepcopy(schema)
    limits = {t: c.unknown_schema(inputs[t]['recovery']) for t in specs
              if inputs[t]['mode'] == 'UNKNOWN_LIMIT'}
    if limits:
        schema['properties']['limits'] = c.schemas.obj(limits)
        schema['required'].append('limits')
    return schema


class Execution(OfficialLaunch):
    POLICY = c.policy
    capture = CaptureOwner.capture
    receipt = p.Reproof.receipt
    args = p.Reproof.args
    TYPED_PRESENTATION = True
    MARKET_SCOPES = ('us', 'kr')
    SUBJECT_COUNT = 22
    CALL_LIMITS = MAX_CALLS
    SUCCESS_TERMINAL = 'R2B_R5_MONITORING_AI_24_MESSAGE_PASS_READY_FOR_BLIND_COMPARISON'

    def batch_topology(self):
        return owner._batch_topology()

    def __init__(self, root):
        self.root = root
        self.report, self.sealed = root/'report', root/'sealed'
        self.requests = self.sealed/'requests'
        self.ledger = []
        self.cores, self.arows, self.brows, self.markets = {}, {}, {}, {}
        self.chains, self.catalogs, self.subjects, self.caps = {}, {}, {}, {}
        self.ranges, self.entries, self.actx, self.bctx = {}, {}, {}, {}
        self.prepared = p.read(root/'inputs/stock/prepared-inputs.json')
        self.projected = {m: p.read(root/f'inputs/market/{m}-projection.json') for m in ('us','kr')}
        self.source_gen = next(iter(self.prepared.values()))['initial_chain']['source_generation_id']
        self.stage_manifests = {}
        self.limits = {s: {} for s in STAGES}
        self.frozen = p.read(root/'report/execution-freeze.json') if (root/'report/execution-freeze.json').exists() else None
        self.gen = self.frozen['generation_id'] if self.frozen else '20260928-r2b-r5-'+datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')

    def partition(self, spec):
        return [t for t in spec['subjects'] if self.prepared[t]['mode']=='EVIDENCE_BASED']

    def chain(self, t, atomic=()):
        data = self.prepared[t]
        cat, sub, chain = pre.subject_inputs(data['view'], data['source_authority'], data['view_receipt'],
                                            generation=self.gen, atomic=atomic)
        self.catalogs[t], self.subjects[t], self.chains[t] = cat, sub, chain

    def limit_context(self, t):
        return dict(ticker=t, decision_mode='UNKNOWN_LIMIT', recovery=self.prepared[t]['recovery'],
                    source_view_receipt=self.prepared[t]['view_receipt'])

    def valuation_context(self, ticker):
        return None

    def newbuyer_shadow_requests(self, settings):
        """Explicit artifact-only entry point; never part of run()/delivery."""
        if not settings.newbuyer_qualified_valuation_shadow:
            return {}
        from scripts.newbuyer_b2_shadow import build_request
        return {ticker: build_request(settings=settings, context=self.bctx[ticker],
                    accepted=accepted, core=self.cores[ticker], pass_a=self.arows[ticker],
                    source_generation_id=self.source_gen)
                for ticker, accepted in self.brows.items()}

    def freeze_stage(self, stage, requests):
        path = self.sealed/(stage+'-request-freeze.json')
        p.require(not path.exists(), 'stage_already_frozen')
        p.write(path, dict(generation_id=self.gen, requests=requests, files=p.manifest(self.requests/stage)))
        self.stage_manifests[stage] = p.sha(path)

    def verify(self):
        p.require(self.frozen is not None, 'whole_binding_not_issued')
        p.require(p.read(self.report/'execution-freeze.json') == self.frozen, 'binding_changed')
        p.require(p.git_state(p.REPO) == self.frozen['controller'] and p.code_manifest()==self.frozen['code'], 'code_drift')
        p.require(p.git_state(p.OPERATING)==self.frozen['operating'], 'operating_drift')
        p.require(p.manifest(self.root/'inputs')==self.frozen['inputs'], 'sealed_input_drift')
        p.require(p.sha(self.root/'validation/validation.json')==self.frozen['validation_sha256'], 'validation_drift')
        p.require(p.sha(self.report/'host-context.json')==self.frozen['host_context_sha256'], 'host_context_drift')
        p.require(p.sha(launch.INSTRUCTION/'m12ds-launch-context-parity-contract.json')==
                  self.frozen['launch_contract_sha256'], 'launch_contract_drift')
        p.require(shutil.disk_usage(self.root).free >= 10*1024**3, 'disk_budget_blocked')
        p.transport.validate_binding(p.binding(),str(p.BIN))
        for stage, expected in self.stage_manifests.items():
            path = self.sealed/(stage+'-request-freeze.json')
            p.require(p.sha(path)==expected and p.manifest(self.requests/stage)==p.read(path)['files'], 'request_drift')
        p.require(sum(r['attempts'] for r in self.ledger)<=26, 'call_budget_exceeded')

    def prepare(self):
        p.require(self.frozen is None and not self.requests.exists(), 'fresh_freeze_required')
        stock = p.read(self.root/'inputs/stock/summary.json')
        market = p.read(self.root/'inputs/market/summary.json')
        p.require(stock['stage_ready']==dict(Core=22,A=22,B=22) and market['Market']==2 and market['status']=='PASS', 'preflight_gap')
        p.require(stock['quality_supplement_sha256']==r4.SUPPLEMENT_SHA and stock['stored_price_rule_versions_pass']==20
                  and stock['model_visible_time_unclassified']==0 and stock['quality_owner_gaps']==0, 'stock_contract_drift')
        r4.verify_receipt((self.root/'inputs/neutral-v2.json').read_bytes())
        p.require(p.read(self.root/'inputs/market/market-blind-view-materiality-audit.json')['status']=='PASS', 'blind_material_change')
        p.require(p.read(self.root/'validation/validation.json')['status']=='PASS', 'validation_failed')
        p.require(not p.git_state(p.REPO)['status'], 'clean_code_required')
        host = launch.context_receipt()
        p.require(host['state_access']['effective_open_readwrite_without_write'], 'host_launch_unready')
        p.write(self.report/'host-context.json',host)
        requests = {s: [] for s in ('market','core')}
        for m in ('us','kr'):
            projected = self.projected[m]
            p.require(projected['receipt']['numeric_alias_binding']['status']=='PASS', 'alias_gap')
            requests['market'].append(self.capture('market',dict(market=m,batch=1,subjects=[]),
                projected['context'], projected['schema'], market_owner.PROMPT))
        for spec in self.batch_topology():
            contexts = {}
            for t in spec['subjects']:
                self.chain(t)
                data = self.prepared[t]
                if data['mode']=='UNKNOWN_LIMIT':
                    contexts[t] = self.limit_context(t)
                else:
                    contexts[t] = {**data['core_input'], 'authority':self.chains[t]['authority']}
            evidence = self.partition(spec)
            schema = add_limits(c.schemas.core_schema({t:contexts[t] for t in evidence}),self.prepared,spec['subjects'])
            requests['core'].append(self.capture('core',spec,contexts,schema,c.schemas.CORE_PROMPT+'\n'+c.LIMIT_PROMPT))
        for stage, values in requests.items():
            self.freeze_stage(stage, values)
        p.write(self.sealed/'initial-requests.json',requests)
        self.frozen = dict(status='ISSUED_WHOLE_COHORT_READY', generation_id=self.gen,
            source_generation_id=self.source_gen, source_hashes=stock['source_hashes'],
            blind_fairness='PASS_V2', neutral_receipt_sha256=r4.RECEIPT_SHA, quality_supplement_sha256=r4.SUPPLEMENT_SHA,
            controller=p.git_state(p.REPO), operating=p.git_state(p.OPERATING), code=p.code_manifest(),
            inputs=p.manifest(self.root/'inputs'), validation_sha256=p.sha(self.root/'validation/validation.json'),
            stage_manifests=self.stage_manifests, initial_request_manifest_sha256=p.sha(self.sealed/'initial-requests.json'),
            host_context_sha256=p.sha(self.report/'host-context.json'), frozen_at=p.now(),
            launch_contract_sha256=p.sha(launch.INSTRUCTION/'m12ds-launch-context-parity-contract.json'),
            model='gpt-5.6-sol', effort='xhigh', timeout_seconds=1200, max_calls=MAX_CALLS,
            retries=0, repair=0, fallback=0, judge=0, provider_refresh=0,
            decision_modes={t:d['mode'] for t,d in self.prepared.items()},
            market_context_hashes={m:digest(v['context']) for m,v in self.projected.items()},
            stock_source_input_hashes={t:digest(d) for t,d in self.prepared.items()},
            downstream_requests='A/B are dependent on newly validated upstream outputs; freeze each exact request before its stage. Offline probes are NOT model outputs.',
            policy_contract='unchanged R4/R2B schemas/validators/renderer', independent_assessment_content_read=False)
        p.write(self.report/'execution-freeze.json',self.frozen)
        self.verify()
        print(json.dumps(dict(status=self.frozen['status'],generation_id=self.gen,model_calls=0)),flush=True)

    def validate_limits(self, raw, stage, spec, dest):
        expected = {t for t in spec['subjects'] if self.prepared[t]['mode']=='UNKNOWN_LIMIT'}
        p.require(set(raw.get('limits',{}))==expected, 'limit_subject_set')
        for t in expected:
            cap = {k:[] for k in c.DIRECTION_BUCKETS}
            self.receipt(dest/(t+'-limit-validation.json'),c.validate_unknown(raw['limits'][t],mode='UNKNOWN_LIMIT',
                recovery=self.prepared[t]['recovery'],capability=cap))
            self.limits[stage][t] = raw['limits'][t]

    def core(self, spec, request):
        raw, dest = self.invoke('core',spec,request)
        self.validate_limits(raw,'core',spec,dest)
        inputs = p.read(Path(request['directory'])/'subject-context.json')
        accepted = {t:c.policy.materialize_core(t,raw['cores'][t],inputs[t]['metadata'],inputs[t]['authority'],
                    inputs[t]['frozen_fact_fields']) for t in self.partition(spec)}
        p.write(dest/'accepted.json',accepted)
        self.cores.update(accepted)

    def before_a(self):
        requests = []
        for spec in self.batch_topology():
            evidence = self.partition(spec)
            contexts = {}
            for t in spec['subjects']:
                if t not in evidence:
                    contexts[t]=self.limit_context(t)
                    continue
                self.chain(t,self.cores[t]['atomic_claims'])
                d = self.prepared[t]
                gate=pre.a_input(d['view'],self.catalogs[t],self.subjects[t],self.chains[t],d['source_authority'])
                self.receipt(self.sealed/'pre-a'/f'{t}.json',gate['receipt'])
                self.actx[t]=contexts[t]=gate['model_context']
            schema=owner.future_pass_a_batch_schema(subjects=evidence,subject_contexts=self.actx,
                source_use_inputs={t:dict(catalog=self.catalogs[t],chain=self.chains[t],
                    source_metadata=self.subjects[t]['decision_evidence'],source_generation_id=self.source_gen,
                    execution_generation_id=self.gen) for t in evidence})
            requests.append(self.capture('pass-a',spec,contexts,add_limits(schema,self.prepared,spec['subjects']),
                owner.future_pass_a_prompt_template()+'\n'+c.LIMIT_PROMPT))
        self.freeze_stage('pass-a',requests)
        return requests

    def pass_a(self,spec,request):
        raw,dest=self.invoke('pass-a',spec,request)
        self.validate_limits(raw,'pass-a',spec,dest)
        evidence=self.partition(spec)
        output={'classifications':raw['classifications']}
        rows,receipt=owner.materialize_future_pass_a(output,subjects=evidence,subject_contexts=self.actx)
        self.receipt(dest/'materialization.json',receipt)
        identity=dict(generation_id=self.gen,packet_id=f"r2b-r5-{spec['market']}-{spec['batch']}",
            market=spec['market'],assessment_date=self.projected[spec['market']]['packet']['assessment_date'])
        envelope=owner.PassABatchOutput.model_validate(dict(contract='m12cq-pass-a-archetype-regime-v1',**identity,classifications=rows))
        args=self.args(evidence)
        args['source_catalogs']=args.pop('catalogs')
        self.receipt(dest/'semantic.json',owner.validate_pass_a_batch(envelope,expected_identity=identity,
            subject_contexts=self.actx,**args))
        self.receipt(dest/'leakage.json',owner.pass_a_output_leak_scan(output))
        p.write(dest/'accepted.json',rows)
        self.arows.update({r['ticker']:r for r in rows})

    def before_b(self):
        requests=[]
        for spec in self.batch_topology():
            contexts,schemas={},{}
            for t in spec['subjects']:
                if self.prepared[t]['mode']=='UNKNOWN_LIMIT':
                    contexts[t]=self.limit_context(t)
                    continue
                cap=c.policy.axis_capability(self.cores[t],self.chains[t],self.catalogs[t],self.subjects[t]['decision_evidence'])
                ctx,entries,valuation=pre.b_input(self.prepared[t]['view'],self.catalogs[t],self.subjects[t],self.chains[t],self.arows[t],cap)
                ctx['r2_core_effects']=self.cores[t]['effects']
                self.caps[t],self.ranges[t],self.entries[t]=cap,valuation,entries
                self.bctx[t]=contexts[t]=ctx
                schemas[t]=c.decision_schema('EVIDENCE_BASED',cap,valuation,entries,{})
                snapshot_context = self.valuation_context(t)
                if snapshot_context is not None:
                    from app.services.provider_valuation_calibration_context import with_axis_refs
                    ctx['valuation_context'] = snapshot_context
                    schemas[t] = with_axis_refs(schemas[t], snapshot_context)
            schema=add_limits(c.schemas.obj({'decisions':c.schemas.obj(schemas)}),self.prepared,spec['subjects'])
            from app.services.provider_valuation_calibration_context import context_prompt
            extra = '\n' + context_prompt(contexts) if any('valuation_context' in ctx for ctx in contexts.values()) else ''
            requests.append(self.capture('pass-b',spec,contexts,schema,c.schemas.B_PROMPT+'\n'+c.LIMIT_PROMPT+extra))
        self.freeze_stage('pass-b',requests)
        return requests

    def pass_b(self,spec,request):
        raw,dest=self.invoke('pass-b',spec,request)
        self.validate_limits(raw,'pass-b',spec,dest)
        accepted={}
        for t in self.partition(spec):
            snapshot_context = self.valuation_context(t)
            if snapshot_context is not None:
                from app.services.provider_valuation_calibration_context import validate_calibration_output
                audit = validate_calibration_output(raw['decisions'][t], snapshot_context)
                self.receipt(dest/(t+'-valuation-use.json'), audit)
            cap=c.policy.axis_capability(self.cores[t],self.chains[t],self.catalogs[t],self.subjects[t]['decision_evidence'])
            p.require(cap==self.caps[t],'capability_drift')
            row,receipt=c.validate_decision(raw['decisions'][t],mode='EVIDENCE_BASED',cap=cap,valuation=self.ranges[t],recovery={})
            self.receipt(dest/(t+'-policy-validation.json'),receipt)
            self.entries[t]=materialize_ranges(self.ranges[t],self.entries[t],row['tactical_choice'])
            accepted[t]=row
        p.write(dest/'accepted.json',accepted)
        self.brows.update(accepted)

    def market(self,spec,request):
        raw,dest=self.invoke('market',spec,request)
        self.receipt(dest/'semantic.json',market_owner.validate_market(raw,self.projected[spec['market']]['context']))
        p.write(dest/'accepted.json',raw)
        self.markets[spec['market']]=raw

    def bounded(self,stage,spec,request):
        limits=getattr(self,'CALL_LIMITS',MAX_CALLS)
        p.require(sum(r['attempts'] for r in self.ledger if r['stage']==stage)<limits[stage], 'stage_call_budget')
        self.ledger.append(dict(stage=stage,**spec,attempts=0,status='NOT_STARTED'))
        try:
            getattr(self,stage.replace('-','_'))(spec,request)
            self.ledger[-1]['status']='PASS'
        except Exception as exc:
            self.ledger[-1].update(status='FAIL',failure_type=type(exc).__name__,failure_code=str(exc))
            raise
        finally:
            self.publish()

    def run(self):
        p.require(not (self.report/'model-structural-ledger.json').exists(),'one_execution_only')
        self.stage_manifests=dict(self.frozen['stage_manifests'])
        stage='market'
        terminal='MARKET_MODEL_FAILURE'
        try:
            self.verify()
            initial=p.read(self.sealed/'initial-requests.json')
            p.require(p.sha(self.sealed/'initial-requests.json')==self.frozen['initial_request_manifest_sha256'],'initial_request_drift')
            for stage in STAGES:
                requests=initial[stage] if stage in initial else self.before_a() if stage=='pass-a' else self.before_b()
                for request in requests:
                    self.bounded(stage,{k:request[k] for k in ('market','batch','subjects')},request)
                accepted=self.markets if stage=='market' else self.cores if stage=='core' else self.arows if stage=='pass-a' else self.brows
                p.require(len(accepted)+len(self.limits[stage])==(len(self.MARKET_SCOPES) if stage=='market' else self.SUBJECT_COUNT),'stage_incomplete')
                p.write(self.sealed/(stage+'-output-freeze.json'),dict(generation_id=self.gen,accepted=accepted,limits=self.limits[stage],
                    call_files=p.manifest(self.sealed/'calls'/stage)))
            stage='render'
            self.render()
            terminal=self.SUCCESS_TERMINAL
        except Exception as exc:
            terminal=dict(market='MARKET_MODEL_FAILURE',core='CORE_MODEL_FAILURE',**{'pass-a':'A_MODEL_FAILURE','pass-b':'B_MODEL_FAILURE',
                'render':'RENDER_VALIDATION_FAILURE'})[stage]
            p.write(self.sealed/'failure.json',dict(stage=stage,type=type(exc).__name__,error=str(exc),traceback=traceback.format_exc()))
        finally:
            p.write(self.report/'execution-complete.json',dict(terminal=terminal,generation_id=self.gen,
                calls={s:sum(r['attempts'] for r in self.ledger if r['stage']==s) for s in STAGES},
                accepted=dict(Market=len(self.markets),Core=len(self.cores),A=len(self.arows),B=len(self.brows)),
                accepted_limits={s:len(v) for s,v in self.limits.items()},
                messages=len(list((self.root/'messages').glob('*.txt'))),
                independent_assessment_content_read=False,reveal_gate='CLOSED_UNTIL_RESULT_SEAL',
                provider_refresh=0,production_side_effects=0,retry=0))
            self.publish()

    def render(self):
        from scripts.r2b_r5_render import capture
        capture(self)


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('mode',choices=('prepare','run'))
    parser.add_argument('--root',type=Path,required=True)
    args=parser.parse_args()
    audit=pre.SourceReadAudit([], [Path('/tmp/codex-remote-attachments'),
        Path.home()/'Library/Mobile Documents/com~apple~CloudDocs',p.OPERATING/'data'])
    sys.addaudithook(audit)
    proof=Execution(args.root)
    try:
        getattr(proof,args.mode)()
    finally:
        p.write(args.root/'report'/('read-audit-'+args.mode+'.json'),audit.receipt())


if __name__=='__main__':
    main()
