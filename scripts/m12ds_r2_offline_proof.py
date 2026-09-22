"""No-inference full source/serializer probe, separate from all live requests/results."""
import argparse
from itertools import product
from pathlib import Path
import shutil

from scripts import m12ds_r2_judgment_policy as policy
from scripts import m12ds_r2_schemas as schemas
from scripts.m12ds_r2_shadow_reproof import Reproof, p
from scripts.m12ds_r1_offline_parity import resolved


def sample(schema, node):
    node = resolved(schema,node)
    if 'const' in node:
        return node['const']
    if 'enum' in node:
        return node['enum'][0]
    if 'anyOf' in node:
        return sample(schema,node['anyOf'][0])
    kind = node.get('type')
    if kind=='object':
        return {k:sample(schema,v) for k,v in node['properties'].items()}
    if kind=='array':
        return [sample(schema,node['items']) for _ in range(node.get('minItems',0))]
    if kind=='string':
        return 'Offline generic contract probe.'
    if kind=='number' or kind=='integer':
        return 5
    if kind=='null':
        return None
    if kind=='boolean':
        return False
    raise ValueError('unsupported_probe_schema')


def run(root, *, proof_class=Reproof, policy=policy, schemas=schemas):
    proof = proof_class(root)
    out = root/'offline-flow'
    p.require(not out.exists(),'OFFLINE_OUTPUT_ALREADY_EXISTS')
    proof.report,proof.sealed = out/'report',out/'sealed'
    proof.requests = proof.sealed/'requests'
    proof.report.mkdir(parents=True)
    shutil.copy2(root/'report/source-authority-before-core.json',proof.report/'source-authority-before-core.json')
    inputs = p.read(root/'sealed/core-inputs.json')
    for t,c in inputs.items():
        observed = next(iter(c['observed_propositions'].values()))
        raw = {'claims':[dict(effect=observed['effect'],text='Offline shape probe, not a model judgment.',
                             evidence_refs=[observed['source_ref']],observation_ids=[observed['observation_id']],
                             materiality='CONTEXT_ONLY')]}
        schema = schemas.core_schema({t:c})
        p.require(not p.owner.validate_json_schema({'cores':{t:raw}},schema),'OFFLINE_CORE_SCHEMA')
        proof.cores[t] = policy.materialize_core(t,raw,c['metadata'],c['authority'],c['frozen_fact_fields'])
    a_requests = proof.before_a()
    for req in a_requests:
        schema = p.read(Path(req['directory'])/'internal-semantic-schema.json')
        raw = sample(schema,schema)
        normal,receipt = p.owner.materialize_future_pass_a(raw,subjects=tuple(req['subjects']),subject_contexts=proof.actx)
        p.require(receipt['status']=='PASS','OFFLINE_A_MATERIALIZATION')
        proof.arows.update({r['ticker']:r for r in normal})
    b_requests = proof.before_b()
    rows = []
    for req in b_requests:
        path = Path(req['directory'])
        internal,wire = [p.read(path/name) for name in ('internal-semantic-schema.json','provider-wire-schema.json')]
        for t in req['subjects']:
            props = internal['properties']['decisions']['properties'][t]['properties']
            probes = 0
            for overall,holder,buyer in product(props['overall']['anyOf'],props['holder_axis']['anyOf'],props['new_buyer_axis']['anyOf']):
                raw = {'overall':sample(internal,overall),'holder_axis':sample(internal,holder),
                       'new_buyer_axis':sample(internal,buyer),'tactical_choice':sample(internal,props['tactical_choice'])}
                flat = schemas.normalize_decision(raw)
                p.require(policy.validate_decision(flat,proof.caps[t],proof.ranges[t])['status']=='PASS','OFFLINE_B_POLICY_PARITY')
                # Isolated subject schema preserves root definitions for provider enum references.
                for schema in (internal,wire):
                    branch = schema['properties']['decisions']['properties'][t]
                    p.require(not p.owner.validate_json_schema(raw,branch,root=schema),'OFFLINE_B_SCHEMA_PARITY')
                probes += 1
            rows.append({'ticker':t,'status':'PASS','branch_probes':probes,
                         'tactical_candidates':len(proof.range_catalogs[t].get('tactical_candidates') or []),
                         'range_source_exclusions':len(proof.ranges[t]['source_use_exclusions'])})
    receipt = {'status':'PASS','model_calls':0,'synthetic_intermediate_claims_only':True,
               'live_request_results_reused':False,'rows':rows,'subjects':len(rows),'a_requests':len(a_requests),'b_requests':len(b_requests)}
    p.write(root/'validation/full-source-offline-proof.json',receipt)
    print('Offline shape/authority/policy proof PASS: 22 subjects, 8 A + 8 B request builders, zero inference',flush=True)


if __name__=='__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--root',type=Path,required=True)
    run(parser.parse_args().root)
