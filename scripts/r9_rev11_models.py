"""Fresh-only official model adapter. Existing Core/A/B contracts are unchanged."""
import argparse
import asyncio
import shutil
from pathlib import Path

from app.services.current_fresh_valuation import CurrentValuationView
from app.services.cross_market_decision_engine_service import DecisionEvidencePacket
from app.services.detailed_stock_message_service import build_detailed_plan, build_unknown_plan, final_detailed_audit
from app.services.accepted_decision_v2_service import render_accepted_v2_production
from app.services.unified_snapshot_contract import digest
from scripts import r2b_r2_preflight as pre
from scripts import m12dr_fresh_blind_reproof as p
from scripts import m12ds_launch_context as launch
from scripts import m12ds_r4_r4_market as market_owner
from scripts.r2b_r5_execution import Execution, add_limits, STAGES
from scripts.r2b_r5_market_adapter import project_sealed_market_context
from scripts.r2b_r9_full_fresh_requalification import prepare_fresh_subject
from scripts.r9_offline_stage_replay import replay_market
from scripts.r9_rev11_replay import replay_twice
from scripts.r9_rev11_live import POLICY
from scripts.m12ds_r4_r1_accepted_capture import stock_plan
from scripts.m12ds_r4_offline_capture import capture_payload

c, owner = pre.c, pre.owner


class FreshExecution(Execution):
    DETAILED_PRESENTATION = True
    # Match REV10 detailed capture; the older typed path expects legacy packets.
    TYPED_PRESENTATION = False

    def __init__(self, root, sources):
        self.root, self.sources = root, sources
        self.report, self.sealed = root/'report', root/'sealed'
        self.requests = self.sealed/'requests'
        self.ledger = []
        self.cores, self.arows, self.brows, self.markets = {}, {}, {}, {}
        self.chains, self.catalogs, self.subjects, self.caps = {}, {}, {}, {}
        self.ranges, self.entries, self.actx, self.bctx = {}, {}, {}, {}
        self.stage_manifests = {}
        self.limits = {s:{} for s in STAGES}
        self.source_frozen = p.read(sources/'r9-rev11-final-provider-plan.json')
        self.source_gen = self.gen = self.source_frozen['generation_id']
        self.frozen = p.read(self.report/'execution-freeze.json') if (self.report/'execution-freeze.json').exists() else None
        self.prepared, self.fresh_stocks, self.stock_inputs, self.projected = {}, {}, {}, {}
        if self.frozen:
            self.prepared = p.read(root/'inputs/prepared.json')
            self.fresh_stocks = p.read(root/'inputs/stocks.json')
            self.projected = p.read(root/'inputs/markets.json')
            self.locals = p.read(root/'inputs/locals.json')

    def verify(self):
        p.require(self.frozen is not None, 'fresh_model_freeze_required')
        p.require(p.read(self.report/'execution-freeze.json')==self.frozen, 'model_freeze_drift')
        p.require(p.git_state(p.REPO)==self.frozen['controller'] and p.code_manifest()==self.frozen['code'], 'code_drift')
        p.require(p.git_state(p.OPERATING)==self.frozen['operating'], 'operating_drift')
        p.require(p.manifest(self.root/'inputs')==self.frozen['inputs'], 'fresh_model_input_drift')
        p.require(p.manifest(self.sources)==self.frozen['sources'], 'fresh_source_corpus_drift')
        p.require(p.sha(self.report/'host-context.json')==self.frozen['host_context_sha256'], 'host_context_drift')
        p.require(p.sha(launch.INSTRUCTION/'m12ds-launch-context-parity-contract.json')==self.frozen['launch_contract_sha256'], 'launch_contract_drift')
        p.require(shutil.disk_usage(self.root).free>=10*1024**3,'disk_budget_blocked')
        p.transport.validate_binding(p.binding(),str(p.BIN))
        for stage, sha in self.stage_manifests.items():
            path=self.sealed/(stage+'-request-freeze.json')
            p.require(p.sha(path)==sha and p.manifest(self.requests/stage)==p.read(path)['files'], 'stage_request_drift')
        p.require(sum(r['attempts'] for r in self.ledger)<=26, 'official_call_budget')

    def prepare(self):
        from scripts.sealed_cohort_offline_proof import network_guard
        network_guard()
        p.require(self.frozen is None and not self.requests.exists(), 'new_model_generation_required')
        qualified=p.read(self.sources/'source-qualification.json')
        p.require(qualified['status']=='PASS', 'whole_fresh_source_not_qualified')
        args,whole,receipt=replay_twice(self.sources,self.source_frozen,p.read(self.sources/'acquisition-outcome.json'),POLICY)
        p.require(receipt['first_sha256']==qualified['first_sha256'], 'source_qualification_drift')
        from scripts.r9_rev11_market_qualification import qualify_markets
        coverage=qualify_markets(whole)
        p.require(all(r['status']=='PASS' for r in coverage.values()),'mandatory_market_source_partial')
        self.whole=whole
        self.locals={}
        for t, item in args['stock_inputs'].items():
            inputs=item['fresh_financial_binding']
            result=prepare_fresh_subject(inputs,execution_generation_id=self.gen)
            p.require(result['readiness']['status']=='PASS', 'fresh_stock_model_preflight:'+t)
            self.prepared[t],self.fresh_stocks[t]=result['prepared'],result['stock']
            self.locals[t]=inputs['technical_inputs']['local_seed']
        for market in ('us','kr'):
            self.projected[market]=project_sealed_market_context(whole['packets'][market],whole['seed'],whole['authority_graph'],
                expected_authority_sha256=whole['authority_graph_sha256'])
        for name,value in [('prepared',self.prepared),('stocks',self.fresh_stocks),('markets',self.projected),('locals',self.locals),('whole',whole)]:
            p.write(self.root/'inputs'/(name+'.json'),value)
        requests={'market':[],'core':[]}
        for market in ('us','kr'):
            ctx=self.projected[market]['context']
            requests['market'].append(self.capture('market',dict(market=market,batch=1,subjects=[]),ctx,
                market_owner.market_schema(ctx),market_owner.PROMPT))
        for spec in owner._batch_topology():
            contexts={}
            for t in spec['subjects']:
                self.chain(t)
                data=self.prepared[t]
                contexts[t]=self.limit_context(t) if data['mode']=='UNKNOWN_LIMIT' else {**data['core_input'],'authority':self.chains[t]['authority']}
            evidence=self.partition(spec)
            schema=add_limits(c.schemas.core_schema({t:contexts[t] for t in evidence}),self.prepared,spec['subjects'])
            requests['core'].append(self.capture('core',spec,contexts,schema,c.schemas.CORE_PROMPT+'\n'+c.LIMIT_PROMPT))
        for stage, rows in requests.items():
            self.freeze_stage(stage,rows)
        p.write(self.sealed/'initial-requests.json',requests)
        p.write(self.report/'host-context.json',launch.context_receipt())
        self.frozen=dict(generation_id=self.gen,source_generation_id=self.source_gen,controller=p.git_state(p.REPO),
            operating=p.git_state(p.OPERATING),code=p.code_manifest(),inputs=p.manifest(self.root/'inputs'),sources=p.manifest(self.sources),
            stage_manifests=self.stage_manifests,initial_request_manifest_sha256=p.sha(self.sealed/'initial-requests.json'),
            host_context_sha256=p.sha(self.report/'host-context.json'),
            launch_contract_sha256=p.sha(launch.INSTRUCTION/'m12ds-launch-context-parity-contract.json'),
            model='gpt-5.6-sol',effort='xhigh',timeout_seconds=1200,retries=0,fallback=0,judge=0,provider_refresh=0,
            transport_policy='EXISTING_OFFICIAL_SHADOW_CONTRACT_UNCHANGED',max_calls=26,
            fresh_source_replay=receipt,independent_assessment_content_read=False,production_side_effects=0)
        p.require(not self.frozen['controller']['status'],'clean_model_code_required')
        p.write(self.report/'execution-freeze.json',self.frozen)
        self.verify()

    def render(self):
        from scripts.sealed_cohort_offline_proof import network_guard
        self.verify()
        network_guard()
        whole=p.read(self.root/'inputs/whole.json')
        output=self.root/'messages'
        output.mkdir(exist_ok=False)
        captures={}
        for market in ('us','kr'):
            captures['MARKET_'+market.upper()]=replay_market(whole,market,self.markets[market])['capture']
        for ticker,stock in self.fresh_stocks.items():
            ep=DecisionEvidencePacket.model_validate(stock['evidence_packet'])
            valuation=CurrentValuationView.model_validate(stock['valuation_view'])
            if self.prepared[ticker]['mode']=='UNKNOWN_LIMIT':
                plan=build_unknown_plan(source_stock=stock,source_authority=self.prepared[ticker]['source_authority'],
                    local_seed=self.locals[ticker],decision=self.limits['pass-b'][ticker],execution_generation_id=self.gen,valuation=valuation)
            else:
                plan=build_detailed_plan(packet=ep,accepted=stock_plan(self,ticker,ep),source_stock=stock,
                    core=self.cores[ticker],pass_a=self.arows[ticker],valuation=valuation)
            rendered=render_accepted_v2_production(ep,plan)
            p.require(rendered.validation.valid,'fresh_detailed_validation:'+ticker)
            audit=final_detailed_audit(rendered.text,ep,plan)
            p.require(audit['status']=='PASS','fresh_detailed_audit:'+ticker)
            key=stock['market']+'-'+ticker
            captures[key]=asyncio.run(capture_payload(dict(type='stock_review',market=stock['market'],ticker=ticker,text=rendered.text,use_llm=False)))
            p.write(output/'bindings'/(key+'.json'),dict(plan=plan.model_dump(mode='json'),audit=audit))
        p.require(len(captures)==24,'exact24_required')
        rows=[]
        for key,receipt in captures.items():
            p.require(receipt['production_sends']==0 and receipt['network_requests']==0,'delivery_not_disabled')
            (output/(key+'.txt')).write_text(receipt['prepared_text'])
            p.write(output/'receipts'/(key+'.json'),receipt)
            rows.append(dict(message=key,sha256=receipt['prepared_text_sha256']))
        (output/'ALL_MESSAGES.md').write_text('\n\n'.join('## '+k+'\n\n'+r['prepared_text'] for k,r in captures.items()))
        p.write(output/'manifest.json',dict(generation_id=self.gen,source_generation_id=self.source_gen,messages=rows,
            total=24,source_sha256=digest(whole),production_sends=0))


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('mode',choices=['prepare','run'])
    parser.add_argument('--root',type=Path,required=True)
    parser.add_argument('--sources',type=Path,required=True)
    args=parser.parse_args()
    proof=FreshExecution(args.root,args.sources)
    getattr(proof,args.mode)()


if __name__=='__main__':
    main()
