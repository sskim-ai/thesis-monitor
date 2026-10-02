"""Synthetic availability/plumbing probe, never candidate or inference output."""
import argparse
from pathlib import Path

from scripts import r2b_r2_preflight as pre
from scripts import m12dr_fresh_blind_reproof as p
from scripts.r2b_r5_execution import Execution, add_limits
from scripts.sealed_cohort_offline_proof import network_guard


def run(prepared, output):
    network_guard()
    output.mkdir(parents=True,exist_ok=False)
    proof=Execution.__new__(Execution)
    proof.prepared=p.read(prepared)
    proof.gen='offline-r5-controller-probe-not-inference'
    proof.source_gen=next(iter(proof.prepared.values()))['initial_chain']['source_generation_id']
    proof.root=output
    proof.report=output/'report'
    proof.sealed=output/'sealed'
    proof.requests=proof.sealed/'requests'
    for name in ('cores','arows','brows','actx','bctx','chains','catalogs','subjects','caps','ranges','entries','stage_manifests'):
        setattr(proof,name,{})
    for t,d in proof.prepared.items():
        proof.chain(t)
        if d['mode']=='UNKNOWN_LIMIT':
            continue
        inp=d['core_input']
        raw={'claims':[dict(effect=o['effect'],text='Offline source capability probe.',evidence_refs=[o['source_ref']],
            observation_ids=[key],materiality='CONTEXT_ONLY') for key,o in inp['observed_propositions'].items()]}
        proof.cores[t]=pre.c.policy.materialize_core(t,raw,inp['metadata'],inp['authority'],inp['frozen_fact_fields'])
    a=proof.before_a()
    for request in a:
        spec={k:request[k] for k in ('market','batch','subjects')}
        evidence=proof.partition(spec)
        schema=p.read(Path(request['directory'])/'internal-semantic-schema.json')
        # Separate routing envelope leaves the accepted ordinary schema unchanged.
        base={**schema,'properties':{'classifications':schema['properties']['classifications']},'required':['classifications']}
        raw=pre.synthetic_shape_probe(base)
        rows,receipt=pre.owner.materialize_future_pass_a(raw,subjects=evidence,subject_contexts=proof.actx)
        p.require(receipt['status']=='PASS','offline_a_materialization')
        proof.arows.update({r['ticker']:r for r in rows})
    b=proof.before_b()
    for request in b:
        pre.schema_check(p.read(Path(request['directory'])/'internal-semantic-schema.json'))
    core_schemas=[]
    for spec in pre.owner._batch_topology():
        schema=add_limits(pre.c.schemas.core_schema({t:proof.prepared[t]['core_input'] for t in proof.partition(spec)}),
                          proof.prepared,spec['subjects'])
        core_schemas.append(pre.schema_check(schema))
    p.write(output/'summary.json',dict(status='PASS',model_calls=0,synthetic_only=True,
        inferred_candidates=0,core_schema_batches=len(core_schemas),a_requests=len(a),b_requests=len(b),
        ordinary_subjects=len(proof.cores),limited_subjects=sum(d['mode']=='UNKNOWN_LIMIT' for d in proof.prepared.values()),
        downstream_probes_not_model_outputs=True))
    print('Offline controller plumbing PASS; no inference',flush=True)


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--prepared',type=Path,required=True)
    parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args()
    run(args.prepared,args.output)
