"""Shared Market/Core/A/B builder and validator methods, without dispatch."""
from copy import deepcopy
from pathlib import Path
from app.services import canonical_monitoring_io as p
from app.services import canonical_monitoring_input as pre
from app.services import canonical_monitoring_owner as owner
from scripts import r2b_r2_contract as c
from scripts import m12ds_r4_r4_market as market_owner
from scripts.m12ds_r2_ranges import materialize_ranges

def add_limits(schema, inputs, specs):
    """Compose existing limitation schema without changing ordinary row schemas."""
    schema = deepcopy(schema)
    limits = {t: c.unknown_schema(inputs[t]['recovery']) for t in specs
              if inputs[t]['mode'] == 'UNKNOWN_LIMIT'}
    if limits:
        schema['properties']['limits'] = c.schemas.obj(limits)
        schema['required'].append('limits')
    return schema

class CanonicalMonitoringDomain:

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

    def args(self, subjects):
        return dict(subjects=tuple(subjects), catalogs=self.catalogs,
                    source_use_views={t: self.chains[t]["projection"] for t in subjects},
                    source_use_bindings={t: self.chains[t]["binding"] for t in subjects},
                    source_use_expectations={t: self.chains[t]["expectation"] for t in subjects},
                    source_metadata_by_ticker={t: self.subjects[t]["decision_evidence"] for t in subjects},
                    source_generation_id=self.source_gen, execution_generation_id=self.gen, require_source_use=True)
