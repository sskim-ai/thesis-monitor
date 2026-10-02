from copy import deepcopy

import pytest

from app.services.auxiliary_issuer_financial_owner import AuxiliaryIssuerDependency, assemble_issuer
from app.services.bounded_financial_stock_owner import assemble, _issuer_business_facts
from app.services.unified_snapshot_contract import digest
from scripts.r2b_r9_full_fresh_requalification import prepare_fresh_subject
from tests.rev9_source_fixtures import bridge_inputs


def fixture(root):
    target, source = bridge_inputs(root)
    bridge = target['financial_inputs']['issuer_business']
    plan = source['financial_inputs']['plan']
    dep = AuxiliaryIssuerDependency(run_id=plan['run_id'], cutoff=plan['cutoff'],
        source_plan_sha256=digest(plan), official_identity_sha256=digest(bridge['official_identity']))
    inputs = dict(source['financial_inputs'], dependency=dep.model_dump(mode='json'))
    return target, inputs


def test_auxiliary_comparisons_equal_legacy_without_kr_technical_baseline(tmp_path):
    target, inputs = fixture(tmp_path)
    bridge = target['financial_inputs']['issuer_business']
    legacy = assemble(**bridge['source_inputs'])
    result = assemble_issuer(**inputs, target_plan=target['financial_inputs']['plan'])
    assert result['status'] == 'PASS'
    assert result['comparative_facts'] == [f for f in legacy['packet']['stocks'][0]['fact_catalog']
        if 'canonical:'+f['fact_id'] in legacy['comparative_fact_refs']]
    assert not {'packet', 'price', 'technical_inputs', 'local_seed', 'baseline'} & result.keys()
    bridge.update(source_inputs=inputs, source_result_sha256=digest(result))
    proof = prepare_fresh_subject(target, execution_generation_id='synthetic-us14')
    assert proof['stock']['status'] == proof['readiness']['status'] == 'PASS'
    b = proof['stock']['issuer_business_bridge']
    assert b['ISSUER_BUSINESS_EVIDENCE_ELIGIBLE']
    assert not b['security_valuation_transfer']
    assert proof['stock']['valuation_view']['ticker'] == 'SKHY'
    assert proof['stock']['valuation_view']['currency'] == 'USD'


@pytest.mark.parametrize('mutation', ['generation', 'prior-receipt', 'target', 'technical', 'official'])
def test_auxiliary_identity_generation_and_scope_fail_closed(tmp_path, mutation):
    target, inputs = fixture(tmp_path)
    if mutation == 'generation':
        inputs['dependency']['run_id'] = 'prior'
    elif mutation == 'prior-receipt':
        inputs['receipts'][0]['started_at'] = '2001-01-01T00:00:00+00:00'
    elif mutation == 'target':
        target['financial_inputs']['plan'] = deepcopy(target['financial_inputs']['plan'])
        target['financial_inputs']['plan']['ticker'] = 'IBM'
    elif mutation == 'technical':
        inputs['dependency']['technical_eligible'] = True
    else:
        inputs['dependency']['official_identity_sha256'] = '0'*64
        bridge = target['financial_inputs']['issuer_business']
        bridge.update(source_inputs=inputs)
        with pytest.raises(ValueError, match='auxiliary'):
            _issuer_business_facts(target['financial_inputs']['plan'], bridge)
        return
    with pytest.raises(ValueError):
        assemble_issuer(**inputs, target_plan=target['financial_inputs']['plan'])


def test_auxiliary_rejects_even_supplied_price_baseline(tmp_path):
    target, inputs = fixture(tmp_path)
    with pytest.raises(TypeError):
        assemble_issuer(**inputs, target_plan=target['financial_inputs']['plan'], baseline={})
