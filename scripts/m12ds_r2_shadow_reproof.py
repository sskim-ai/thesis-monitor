"""Same-source fresh R2 market/Core/A/B: bounded, frozen, local shadow only."""
import argparse
from collections import Counter
from datetime import datetime, timezone
import json
from pathlib import Path
import shutil
import traceback

from scripts import m12dr_fresh_blind_reproof as p
from scripts.m12ds_same_blind_reproof import Reproof as LaunchReproof
from scripts import m12ds_r2_judgment_policy as policy
from scripts import m12ds_r2_schemas as schemas
from scripts import m12ds_r2_market as market_owner
from scripts.m12ds_r2_ranges import valuation_policy, materialize_ranges, eligible_range_inputs
from scripts.m12dj_source_authority_preflight import preflight_current_pass_a_cohort
from scripts.m12cq_two_pass_contract import build_pass_b_subject_context, validate_pass_b_transformation
from scripts.m12ds_r1_offline_parity import audit as a_parity

BASE = Path('/Users/sskim/Documents/Codex/Reports/20260922-m12ds-r1-axis-parity')
INSTRUCTIONS = p.REPO / 'docs/work-instructions/20260922-m12ds-r2'
SUCCESS = 'M12DS_R2_JUDGMENT_POLICY_CALIBRATION_FRESH_CORE_AB_PASS_READY_FOR_CHAT'


def stage(root):
    baseline = p.read(INSTRUCTIONS / 'm12ds-r2-baseline.json')['accepted_m12ds_r1']
    for name, digest in (
        ('thesis-monitor-20260922-m12ds-r1-pass-a-axis-specific-source-use-schema-parity-same-blind-fresh-a8-b8-report.zip', baseline['structural_report_zip_sha256']),
        ('m12ds-r1-monitoring-ai-sealed-results.zip', baseline['sealed_ai_zip_sha256'])):
        p.require(p.sha(BASE.parents[1] / name) == digest, 'R1_ARCHIVE_HASH_MISMATCH')
    p.require(not root.exists(), 'NEW_ROOT_REQUIRED')
    for name in ('source','snapshot'):
        shutil.copytree(BASE / name, root / name)
    for name in ('source-coverage.json','source-input-binding.json','quality-receipts.json','issuer-business-projection.json',
                 'blind-leakage-audit.json','host-context.json','launch-parity.json'):
        (root / 'report').mkdir(exist_ok=True)
        shutil.copy2(BASE / 'report' / name, root / 'report' / name)
    for name in ('m12dr-live-data-blind-pack.zip','m12dr-live-data-blind-pack.zip.sha256'):
        shutil.copy2(BASE / name, root / name)
    p.require(p.sha(root / 'm12dr-live-data-blind-pack.zip') == baseline['blind_pack_sha256'], 'BLIND_MISMATCH')
    p.write(root / 'report/preparation.json', {'generation_id':'20260922-m12ds-r2-' + datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ'),
        'blind_sha256':baseline['blind_pack_sha256'], 'old_outputs_read':False, 'source_refetch':0,
        'baseline_sha256':p.sha(INSTRUCTIONS / 'm12ds-r2-baseline.json')})


class Reproof(LaunchReproof):
    POLICY = policy
    SCHEMAS = schemas
    MARKET_OWNER = market_owner
    INSTRUCTIONS = INSTRUCTIONS
    PREFIX = 'M12DS_R2'
    SUCCESS = SUCCESS

    def __init__(self, root):
        p.Reproof.__init__(self, root)
        self.gen = p.read(self.report / 'preparation.json')['generation_id']
        self.frozen = p.read(self.report / 'execution-freeze.json') if (self.report / 'execution-freeze.json').exists() else None
        self.markets, self.core_inputs, self.ranges, self.core_policy = {}, {}, {}, {}
        self.range_catalogs = {}
        self.requests_root = self.requests
        self.stage_manifests = {}

    def verify(self):
        p.Reproof.verify(self)
        if p.manifest(self.INSTRUCTIONS) != self.frozen['instructions']:
            raise p.SystemicFailure('M12DS_R2_INSTRUCTION_DRIFT')
        for stage_name, expected in self.frozen['request_files'].items():
            if p.manifest(self.requests / stage_name) != expected:
                raise p.SystemicFailure('M12DS_R2_FROZEN_REQUEST_DRIFT')
        for name, digest in self.stage_manifests.items():
            path = self.sealed / (name + '-request-freeze.json')
            if p.sha(path) != digest or p.manifest(self.requests / name) != p.read(path)['files']:
                raise p.SystemicFailure('M12DS_R2_DYNAMIC_REQUEST_DRIFT')
        if p.sha(self.root / 'validation/receipt.json') != self.frozen['validation_sha256']:
            raise p.SystemicFailure('M12DS_R2_OFFLINE_PROOF_DRIFT')
        for name, digest in self.frozen['initial_manifests'].items():
            if p.sha(self.root / name) != digest:
                raise p.SystemicFailure('M12DS_R2_INITIAL_MANIFEST_DRIFT')

    def capture(self, stage_name, spec, context, schema, prompt):
        dest = self.requests / stage_name / spec['market'] / f"batch-{spec['batch']:02d}"
        p.require(not dest.exists(), 'REQUEST_IMMUTABILITY')
        wire, projection = p.owner.project_provider_wire_schema(schema)
        scan = p.owner.scan_provider_structured_output_schema(wire)
        p.require(scan['status'] == 'PASS', 'WIRE_DIALECT_FAILURE')
        p.write(dest / 'subject-context.json', context)
        p.write(dest / 'internal-semantic-schema.json', schema)
        p.write(dest / 'provider-wire-schema.json', wire)
        p.write(dest / 'provider-wire-projection.json', projection)
        p.write(dest / 'provider-dialect-scan.json', scan)
        (dest / 'prompt.txt').write_text(prompt + '\nFROZEN_CONTEXT:\n' + json.dumps(context, ensure_ascii=False, sort_keys=True) + '\n')
        receipt = {'directory':str(dest), **spec, 'stage':stage_name, 'execution_generation_id':self.gen,
            'source_generation_id':self.source_gen, 'context_sha256':p.owner.canonical_sha256(context),
            'files':p.manifest(dest), 'model':'gpt-5.6-sol', 'effort':'xhigh', 'timeout_seconds':1200,
            'attempt_limit':1, 'retries':0, 'status':'PASS'}
        p.write(dest / 'request-receipt.json', receipt)
        return receipt

    def prepare(self):
        core_requests, market_requests, source_readiness = [], [], []
        for spec in p.owner._batch_topology():
            for ticker in spec['subjects']:
                self.chain(ticker, spec['market'], [])
                owned = next(r for r in self.contexts[spec['market']].evidence_ownership if r.ticker == ticker)
                metadata = [r for r in self.subjects[ticker]['decision_evidence'] if r['ref_id'] in owned.core_ref_ids]
                authority = self.authorities[ticker]['authority']
                fields = self.POLICY.frozen_fact_fields(self.packets[spec['market']],ticker,metadata)
                obs = self.POLICY.observations(metadata, authority, fields)
                self.core_inputs[ticker] = dict(ticker=ticker, metadata=metadata, authority=authority,
                                                frozen_fact_fields=fields, observed_propositions=obs, source_generation_id=self.source_gen)
                source_readiness.append({'ticker':ticker, 'observed_propositions':len(obs), 'status':'PASS' if obs else 'BLOCKED'})
            inputs = {t:self.core_inputs[t] for t in spec['subjects']}
            core_requests.append(self.capture('core', spec, inputs, self.SCHEMAS.core_schema(inputs), self.SCHEMAS.CORE_PROMPT))
        p.write(self.report / 'observed-source-preflight.json', {'rows':source_readiness, 'model_calls':0})
        p.require(all(r['status']=='PASS' for r in source_readiness), 'M12DS_R2_FRESH_CORE_DIRECTIONAL_ENTITLEMENT_INCOMPLETE')
        for market in ('us','kr'):
            context = self.MARKET_OWNER.market_context(self.packets[market])
            spec = {'market':market,'batch':1,'subjects':[]}
            market_requests.append(self.capture('market', spec, context, self.MARKET_OWNER.market_schema(context), self.MARKET_OWNER.PROMPT))
        p.write(self.sealed / 'initial-requests.json', {'core':core_requests,'market':market_requests})
        p.write(self.sealed / 'core-inputs.json', self.core_inputs)
        p.write(self.report / 'source-authority-before-core.json', {t:{r['ref_id']:{k:r[k] for k in ('allowed_uses','prohibited_uses','authority_state')}
            for r in a['authority']['authority_records']} for t,a in self.authorities.items()})
        print('R2 preparation PASS: same-source 22, market2/Core8 captured; model calls=0', flush=True)

    def freeze(self):
        p.require(not p.git_state(p.REPO)['status'], 'CLEAN_COMMIT_REQUIRED')
        p.require(not (self.report / 'execution-freeze.json').exists(), 'ALREADY_FROZEN')
        p.require(all(r['status']=='PASS' for r in p.read(self.root / 'validation/receipt.json').values()), 'OFFLINE_PROOF_REQUIRED')
        self.frozen = dict(controller=p.git_state(p.REPO), operating=p.git_state(p.OPERATING), code=p.code_manifest(),
            source=p.manifest(self.root/'source'), snapshot=p.manifest(self.snapshot), instructions=p.manifest(self.INSTRUCTIONS),
            blind_zip_sha256=p.read(self.report/'preparation.json')['blind_sha256'],
            generation_id=self.gen, source_generation_id=self.source_gen, frozen_at=p.now(),
            request_files={s:p.manifest(self.requests/s) for s in ('core','market')},
            validation_sha256=p.sha(self.root/'validation/receipt.json'), model='gpt-5.6-sol', effort='xhigh',
            initial_manifests={name:p.sha(self.root/name) for name in (
                'sealed/initial-requests.json','sealed/core-inputs.json','report/source-authority-before-core.json','report/preparation.json')},
            timeout_seconds=1200, max_calls={'market':2,'core':8,'pass-a':8,'pass-b':8}, retry=0, fallback=0, judge=0)
        p.write(self.report/'execution-freeze.json', self.frozen)
        self.verify()
        print('R2 code/config/input freeze PASS', flush=True)

    def core(self, spec, request):
        raw, dest = self.invoke('core',spec,request)
        inputs = p.read(Path(request['directory'])/'subject-context.json')
        accepted = {t:self.POLICY.materialize_core(t, raw['cores'][t], inputs[t]['metadata'], inputs[t]['authority'],inputs[t]['frozen_fact_fields']) for t in spec['subjects']}
        self.receipt(dest/'core-policy-validation.json', {'status':'PASS','subjects':spec['subjects'],'source_authority_widened':False})
        p.write(dest/'accepted-core.json', accepted)
        self.cores.update(accepted)

    def before_a(self):
        inputs, receipts = [], []
        previous = p.read(self.report/'source-authority-before-core.json')
        for spec in p.owner._batch_topology():
            for ticker in spec['subjects']:
                self.chain(ticker, spec['market'], self.cores[ticker]['atomic_claims'])
                actual = {r['ref_id']:{k:r[k] for k in ('allowed_uses','prohibited_uses','authority_state')}
                    for r in self.authorities[ticker]['authority']['authority_records']}
                p.require(actual==previous[ticker], 'RAW_SOURCE_AUTHORITY_CHANGED')
                chain = self.chains[ticker]
                cap = self.POLICY.axis_capability(self.cores[ticker],chain,self.catalogs[ticker],self.subjects[ticker]['decision_evidence'])
                self.core_policy[ticker] = cap
                receipts.append({'ticker':ticker,'directional_entitlement_count':len(cap['positive'])+len(cap['negative']),
                                 'confidence_excluded':len(cap['confidence']), 'raw_authority_unchanged':True})
                inputs.append(dict(ticker=ticker, source_generation_id=self.source_gen, execution_generation_id=self.gen,
                    catalog=self.catalogs[ticker], source_packet=self.subjects[ticker], authority=chain['authority'],
                    projection=chain['projection'], binding=chain['binding'], expectation=chain['expectation'],
                    prohibited_pass_a_source_refs=self.authorities[ticker]['pass_a_visibility_exclusions']))
        gate = preflight_current_pass_a_cohort(inputs,expected_subjects=p.owner._expected_tickers())
        p.write(self.sealed/'before-a-preflight.json',gate)
        p.write(self.report/'future-b-entitlement.json',{'rows':receipts,'status':'PASS' if gate['status']=='PASS' and all(r['directional_entitlement_count'] for r in receipts) else 'FAIL'})
        p.require(gate['status']=='PASS' and all(r['directional_entitlement_count'] for r in receipts),'M12DS_R2_FRESH_CORE_DIRECTIONAL_ENTITLEMENT_INCOMPLETE')
        self.actx = gate['model_contexts']
        requests = [p.owner._request_capture(root=self.requests,stage='pass-a',**spec,contexts=self.actx,
            catalogs=self.catalogs,chains=self.chains,generation_id=self.gen,fixture_only=False,
            raw_source_metadata_by_ticker={t:self.subjects[t]['decision_evidence'] for t in spec['subjects']}) for spec in p.owner._batch_topology()]
        parity = a_parity(self,requests)
        p.write(self.report/'pass-a-parity.json',parity)
        p.require(parity['status']=='PASS','A_SCHEMA_PARITY_FAILED')
        self.freeze_stage('pass-a',requests)
        return requests

    def freeze_stage(self, stage_name, requests):
        path = self.sealed/(stage_name+'-request-freeze.json')
        p.require(not path.exists(), 'STAGE_ALREADY_FROZEN')
        p.write(path, {'requests':requests,'files':p.manifest(self.requests/stage_name)})
        self.stage_manifests[stage_name] = p.sha(path)

    def before_b(self):
        rows, requests = [], []
        for spec in p.owner._batch_topology():
            for t in spec['subjects']:
                chain, raw = self.chains[t], self.subjects[t]['decision_evidence']
                range_subject, range_catalog, exclusions = eligible_range_inputs(self.subjects[t],self.catalogs[t]['entry_catalog'],chain)
                valuation = valuation_policy(range_subject,self.arows[t],self.typed[t]['security_valuation_basis'])
                valuation['source_use_exclusions'] = exclusions
                self.range_catalogs[t] = range_catalog
                self.ranges[t], self.options[t] = valuation, valuation['option']
                common = dict(catalog=self.catalogs[t],source_use_view=chain['projection'],source_use_binding=chain['binding'],
                    source_use_expectation=chain['expectation'],source_generation_id=self.source_gen,execution_generation_id=self.gen)
                ctx = build_pass_b_subject_context(context=p.owner.m12db._source_context(t,self.subjects[t]),ticker=t,
                    pass_a=self.arows[t],policy_option=self.options[t],require_source_use=True,**common)
                transform = validate_pass_b_transformation(context=ctx,raw_source_metadata=raw,**common)
                p.require(transform['status']=='PASS','M12DO_RAW_EMITTED_FAILED')
                emitted = {r['ref_id']:r for r in ctx['decision_evidence']}
                p.require(all(emitted.get(r['ref_id'],{}).get('logical_condition')==r['logical_condition']
                    for r in raw if r.get('logical_condition')), 'LOGICAL_CONDITION_LOST')
                cap = self.POLICY.axis_capability(self.cores[t],chain,self.catalogs[t],raw)
                p.require(cap==self.core_policy[t],'CORE_EFFECT_CAPABILITY_DRIFT')
                ctx.update(r2_policy_capability=cap,r2_valuation=valuation,r2_core_effects=self.cores[t]['effects'],
                           r2_eligible_range_catalog=range_catalog)
                self.bctx[t],self.caps[t] = ctx,cap
                rows.append({'ticker':t,'status':'PASS','transformation_sha256':p.owner.canonical_sha256(transform),
                             'final_context_sha256':p.owner.canonical_sha256(ctx),'capability_sha256':p.owner.canonical_sha256(cap)})
            schema = self.SCHEMAS.obj({'decisions':self.SCHEMAS.obj({t:self.SCHEMAS.decision_schema(self.caps[t],self.ranges[t],self.range_catalogs[t]) for t in spec['subjects']})})
            requests.append(self.capture('pass-b',spec,{t:self.bctx[t] for t in spec['subjects']},schema,self.SCHEMAS.B_PROMPT))
        p.write(self.report/'offline-preb-closure.json',{'status':'PASS','subjects':rows,'requests':len(requests)})
        self.freeze_stage('pass-b',requests)
        p.write(self.sealed/'deterministic-materialization.json',self.ranges)
        return requests

    def pass_b(self,spec,request):
        raw,dest = self.invoke('pass-b',spec,request)
        decisions, entries, audits = {},{},{}
        for t in spec['subjects']:
            cap = self.POLICY.axis_capability(self.cores[t],self.chains[t],self.catalogs[t],self.subjects[t]['decision_evidence'])
            p.require(cap==self.caps[t],'CAPABILITY_BINDING_DRIFT')
            row = self.SCHEMAS.normalize_decision(raw['decisions'][t])
            self.receipt(dest/(t+'-policy-validation.json'),self.POLICY.validate_decision(row,cap,self.ranges[t]))
            entries[t] = materialize_ranges(self.ranges[t],self.range_catalogs[t],row['tactical_choice'])
            decisions[t] = row
            audits[t] = self.POLICY.policy_audit(row,cap,self.ranges[t])
        p.write(dest/'accepted.json',{'decisions':decisions,'entries':entries,'policy_audits':audits})
        self.brows.update(decisions)
        self.entries.update(entries)

    def market(self,spec,request):
        raw,dest = self.invoke('market',spec,request)
        context = p.read(Path(request['directory'])/'subject-context.json')
        self.receipt(dest/'market-validation.json',self.MARKET_OWNER.validate_market(raw,context))
        self.markets[spec['market']] = raw
        p.write(dest/'accepted.json',raw)

    def bounded(self,stage,spec,callback):
        # New policy errors are local validation failures; systemic errors retain the host guard.
        def validated():
            try:
                callback()
            except p.SystemicFailure:
                raise
            except ValueError as exc:
                raise p.BatchFailure(str(exc)) from exc
        return super().bounded(stage,spec,validated)

    def run(self):
        p.require(not (self.report/'model-structural-ledger.json').exists(),'ONE_EXECUTION_ONLY')
        terminal,failure,stage_name = self.PREFIX+'_RUNTIME_OR_SECURITY_STOP',None,'market'
        try:
            self.verify()
            requests = p.read(self.sealed/'initial-requests.json')
            for request in requests['market']:
                spec = {k:request[k] for k in ('market','batch','subjects')}
                self.bounded('market',spec,lambda spec=spec,request=request:self.market(spec,request))
            p.require(len(self.markets)==2,'MARKET_EXPORT_INCOMPLETE')
            stage_name = 'core'
            for spec,request in zip(p.owner._batch_topology(),requests['core'],strict=True):
                self.bounded('core',spec,lambda spec=spec,request=request:self.core(spec,request))
            p.require(len(self.cores)==22,'FRESH_CORE_INCOMPLETE')
            p.write(self.sealed/'fresh-core-freeze.json',{'generation_id':self.gen,'cores':self.cores})
            stage_name = 'entitlement'
            a_requests = self.before_a()
            stage_name = 'pass-a'
            for spec,request in zip(p.owner._batch_topology(),a_requests,strict=True):
                self.bounded('pass-a',spec,lambda spec=spec,request=request:self.pass_a(spec,request))
            p.require(len(self.arows)==22,'A_INCOMPLETE')
            p.write(self.sealed/'fresh-a-freeze.json',self.arows)
            stage_name = 'pre-b'
            b_requests = self.before_b()
            stage_name = 'pass-b'
            for spec,request in zip(p.owner._batch_topology(),b_requests,strict=True):
                self.bounded('pass-b',spec,lambda spec=spec,request=request:self.pass_b(spec,request))
            p.require(len(self.brows)==22,'B_INCOMPLETE')
            self.verify()
            p.write(self.sealed/'final-results.json',{'generation_id':self.gen,'source_generation_id':self.source_gen,
                'market_judgments':self.markets,'decisions':self.brows,'ranges':self.entries,
                'valuation_audit':self.ranges,'claim_effects':{t:c['effects'] for t,c in self.cores.items()},
                'axis_policy_audits':{t:self.POLICY.policy_audit(r,self.caps[t],self.ranges[t]) for t,r in self.brows.items()},
                'diagnostic_only_distributions':{axis:dict(Counter(r[axis] for r in self.brows.values())) for axis in ('overall_direction','new_buyer','holder')}})
            terminal = self.SUCCESS
        except p.SystemicFailure as exc:
            failure = str(exc)
            p.write(self.sealed/'systemic-failure.json',{'details':traceback.format_exc()})
        except Exception as exc:
            failure = str(exc)
            terminal = {'market':'M12DS_R2_MARKET_EXPORT_INCOMPLETE','core':'M12DS_R2_FRESH_CORE_COMPLETED_WITH_BATCH_LOCAL_FAILURES',
                'entitlement':'M12DS_R2_FRESH_CORE_DIRECTIONAL_ENTITLEMENT_INCOMPLETE','pass-a':'M12DS_R2_PASS_A_COMPLETED_WITH_BATCH_LOCAL_FAILURES',
                'pre-b':'M12DS_R2_OFFLINE_PREB_CLOSURE_FAILED','pass-b':'M12DS_R2_PASS_B_COMPLETED_WITH_BATCH_LOCAL_FAILURES'}[stage_name]
            terminal = terminal.replace('M12DS_R2',self.PREFIX,1)
            p.write(self.sealed/'gate-failure.json',{'details':traceback.format_exc()})
        finally:
            p.write(self.report/'execution-complete.json',{'terminal':terminal,'failure_code':failure,'generation_id':self.gen,
                'source_generation_id':self.source_gen,'market_accepted':len(self.markets),'core_accepted':len(self.cores),
                'a_accepted':len(self.arows),'b_accepted':len(self.brows),
                'calls':{s:sum(r['attempts'] for r in self.ledger if r['stage']==s) for s in ('market','core','pass-a','pass-b')},
                'retries':sum(max(r['attempts']-1,0) for r in self.ledger),'fallback':0,'judge':0,'completed_at':p.now(),'comparison':'NOT_PERFORMED','production_ready':False,
                'source_only_inference_certified':False})
            self.publish()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('mode',choices=('stage','prepare','freeze','run'))
    parser.add_argument('--root',type=Path,required=True)
    args = parser.parse_args()
    stage(args.root) if args.mode=='stage' else getattr(Reproof(args.root),args.mode)()


if __name__ == '__main__':
    main()
