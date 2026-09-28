"""Schema-conforming fictional outputs, not expected investment decisions."""
from copy import deepcopy

from scripts import r2b_r2_preflight as pre
from scripts.r9_offline_stage_replay import core_inputs, a_inputs
from tests.test_r9_rev9_context_only import unknown_decision


def synthetic_outputs(result, generation, local):
    if result['prepared']['mode'] == 'UNKNOWN_LIMIT':
        row = unknown_decision(result['prepared'])
        return dict(core=deepcopy(row), a=deepcopy(row), b=deepcopy(row), local_seed=local)
    obs = result['prepared']['core_input']['observed_propositions']
    core = dict(claims=[dict(effect=o['effect'], text='Synthetic source interpretation.',
        evidence_refs=[o['source_ref']], observation_ids=[key], materiality='CONTEXT_ONLY')
        for key, o in list(obs.items())[:8]])
    state = core_inputs(result, generation, core)
    a = pre.synthetic_shape_probe(state['a_schema'])
    state = a_inputs(result, state, a)
    b_schema = deepcopy(state['b_schema'])
    # Select an available schema branch, not a ticker-specific target label.
    branches = b_schema['properties']['overall']['anyOf']
    owned = [branch for branch in branches if branch['properties']['supporting_refs']['minItems']]
    if owned:
        b_schema['properties']['overall']['anyOf'] = owned
    b = pre.synthetic_shape_probe(b_schema)
    return dict(core=core, a=a, b=b)
