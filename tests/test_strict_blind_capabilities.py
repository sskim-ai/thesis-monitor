"""Source-ontology counterfactuals; no historic answers or ticker targets."""
from copy import deepcopy
import json

import pytest

from app.services.unified_snapshot_contract import digest, encoded
from scripts import strict_blind_contract as b
from scripts import strict_blind_adapter as adapter
from scripts.m12da_source_use_contract import canonical_sha256, canonical_source_metadata_sha256
from scripts.strict_blind_controller import StrictBlindController
from scripts.strict_blind_offline_proof import fixture, host_for
from tests.strict_blind_fixtures import source_inputs, response


def accounting_loss(inp):
    result = deepcopy(inp)
    row = result['metadata'][0]
    fields = json.loads(row['statement'])
    fields.update(current_value=-10, prior_comparable_value=-20)
    row['statement'] = json.dumps(fields)
    owner = next(r for r in result['authority']['authority_records'] if r['ref_id'] == row['ref_id'])
    owner['source_metadata_sha256'] = digest(row)
    result['authority']['source_metadata_sha256'] = canonical_source_metadata_sha256(result['metadata'])
    result['authority'].pop('authority_manifest_sha256')
    result['authority']['authority_manifest_sha256'] = canonical_sha256(result['authority'])
    result['source_sha256'] = digest(result['metadata'])
    return result


@pytest.mark.parametrize('state', ['WAIT_FOR_ZONE', 'FAVORABLE_NOW'])
def test_relation_complete_binding_and_wire_parity(tmp_path, state):
    inp = source_inputs(tmp_path, timing=state)
    subject, audit = b.project_subject(inp, generation='GENERIC-NEW')
    relation = subject['capabilities']['timing_relations'][0]
    assert relation['state'] == state
    assert relation['required_evidence_refs'] == ['source:price', 'source:zone']
    assert relation['security_id'] == inp['security_id']
    assert relation['source_generation_id'] == inp['source_generation_id']
    assert relation['source_input_sha256'] == digest(inp)
    assert relation['ref_sha256'] == {r: subject['evidence'][r]['source_sha256']
        for r in relation['required_evidence_refs']}
    assert relation['relation_id'] == 'owned-timing:' + digest({k: v for k, v in relation.items() if k != 'relation_id'})
    raw = response(subject, audit, timing=state)
    assert b.validate_output(raw, subject, audit)['status'] == 'PASS'
    wire = b.payload(subject)[0]['response_schema']
    assert not b.validate_json_schema(raw, wire)
    raw['axes']['entry_timing']['evidence_refs'].reverse()
    assert b.validate_output(raw, subject, audit)['status'] == 'PASS'


@pytest.mark.parametrize('refs', [['source:technical'], ['source:zone'], ['source:price'],
    ['canonical:chart:daily', 'source:technical'], ['source:price', 'source:zone', 'source:technical']])
def test_missing_support_price_or_unowned_extra_relation_fails(tmp_path, refs):
    subject, audit = b.project_subject(source_inputs(tmp_path), generation='NEW')
    raw = response(subject, audit)
    raw['axes']['entry_timing']['evidence_refs'] = refs
    assert b.validate_output(raw, subject, audit)['status'] == 'FAIL'
    assert b.validate_json_schema(raw, b.payload(subject)[0]['response_schema'])
    assert 'TIMING_WITHOUT_OWNED_RANGE_RELATION' in b._validate_axes(raw['axes'], subject, audit)['errors']


def test_risk_reward_does_not_grant_favorable_now(tmp_path):
    subject, audit = b.project_subject(source_inputs(tmp_path), generation='NEW')
    raw = response(subject, audit, timing='FAVORABLE_NOW')
    assert {r['state'] for r in subject['capabilities']['timing_relations']} == {'WAIT_FOR_ZONE'}
    assert b.validate_output(raw, subject, audit)['status'] == 'FAIL'
    assert b.validate_json_schema(raw, b.payload(subject)[0]['response_schema'])


def test_narrowing_loss_is_absolute_context_not_material_risk(tmp_path):
    inp = accounting_loss(source_inputs(tmp_path))
    before = digest(inp)
    subject, audit = b.project_subject(inp, generation='NEW')
    cap = subject['capabilities']
    assert cap['risk']['improvement_refs'] == ['source:business']
    assert not cap['risk']['adverse_refs'] and cap['risk']['no_adverse_capability']
    loss, = cap['absolute_level_context']
    assert loss['value'] == '-10' and loss['period']['period_type'] == 'QTD'
    assert loss['binding']['security_id'] == inp['security_id']
    assert loss['binding']['source_sha256'] == inp['source_sha256']
    assert loss['permitted_use'] == 'CONTEXT_ONLY' and not loss['grants_active_material_risk']
    raw = response(subject, audit)
    assert b.validate_output(raw, subject, audit)['status'] == 'PASS'
    raw['axes']['active_material_risk']['judgment'] = True
    raw['axes']['holder']['judgment'] = 'REVIEW'
    raw['axes']['new_buyer']['judgment'] = 'AVOID'
    assert b.validate_output(raw, subject, audit)['status'] == 'FAIL'
    assert 'ACTIVE_RISK_WITHOUT_ADVERSE_FACT' in b._validate_axes(raw['axes'], subject, audit)['errors']
    assert digest(inp) == before


@pytest.mark.parametrize('bound', [False, True])
def test_canonical_flat_period_requires_fact_binding(tmp_path, bound):
    inp = accounting_loss(source_inputs(tmp_path))
    subject, audit = b.project_subject(inp, generation='NEW')
    observations = deepcopy(audit['observations'])
    row = next(iter(observations.values()))
    period = row['financial_scope'].pop('current_period')
    row['financial_scope'].update(period_start=period['start'], period_end=period['end'],
        period_type=period['period_type'], currency=period['currency'], issuer_id='FICTIONAL-ISSUER',
        statement_basis=period['statement_basis'])
    row['fact_binding'] = {'fields': deepcopy(row['financial_scope']), 'fact_sha256': digest('fictional')} if bound else None
    cap = b._capabilities(inp, 'NEW', observations, [], subject['evidence'])
    assert len(cap['absolute_level_context']) == int(bound)
    assert not cap['risk']['adverse_refs']
    if bound:
        assert cap['absolute_level_context'][0]['period']['issuer_id'] == 'FICTIONAL-ISSUER'


@pytest.mark.parametrize('risk', [False, True])
def test_holder_review_has_no_independent_watch_permission(tmp_path, risk):
    subject, audit = b.project_subject(source_inputs(tmp_path, risk=risk), generation='NEW')
    raw = response(subject, audit, risk=risk)
    assert b.validate_output(raw, subject, audit)['status'] == 'PASS'
    raw['axes']['holder']['judgment'] = 'REVIEW'
    raw['axes']['active_material_risk']['judgment'] = False
    assert b.validate_output(raw, subject, audit)['status'] == 'FAIL'
    assert 'HOLDER_MATERIAL_RISK_AXIS_MISMATCH' in b._validate_axes(raw['axes'], subject, audit)['errors']
    raw['axes']['active_material_risk']['judgment'] = True
    raw['axes']['holder']['judgment'] = 'REDUCE'
    assert b.validate_output(raw, subject, audit)['status'] == 'FAIL'


def test_capability_not_attractiveness_or_timing_override(tmp_path):
    subject, audit = b.project_subject(source_inputs(tmp_path), generation='NEW')
    for valuation in ('SUPPORTIVE', 'NEUTRAL', 'BURDENSOME'):
        raw = response(subject, audit, valuation=valuation)
        assert b.validate_output(raw, subject, audit)['status'] == 'PASS'
    raw = response(subject, audit)
    raw['axes']['new_buyer']['judgment'] = 'WAIT'
    assert 'TIMING_OR_CONFIDENCE_OVERWROTE_FUNDAMENTAL' in b.validate_output(raw, subject, audit)['errors']


def test_generation_binding_capability_tamper_and_declared_schema(tmp_path):
    inp = source_inputs(tmp_path)
    source = dict(generation='NEW', blind_inputs={inp['ticker']: inp})
    package = b.package(source)
    package['subjects'][inp['ticker']]['capabilities']['timing_relations'][0]['security_id'] = 'OTHER'
    assert not b.validate_package(package, source)
    subject, audit = b.project_subject(inp, generation='NEW')
    raw = response(subject, audit)
    raw['generation'] = 'OLD'
    assert b.validate_output(raw, subject, audit)['status'] == 'FAIL'
    view = dict(blind_package=b.package(source), blind_rubric=b.RUBRIC,
        blind_prompt=b.PROMPT, blind_schema=adapter.schema_authority())
    view['blind_schema']['capabilities']['holder_review'] = 'watch is enough'
    with pytest.raises(ValueError, match='CAPABILITY_SCHEMA_DRIFT'):
        adapter.BlindSubjectAdapter(inp['ticker']).build(view)


def test_22_independent_blind_fixture_scenarios_seal_without_live_io(tmp_path, monkeypatch):
    import socket
    monkeypatch.setattr(socket, 'create_connection', lambda *a, **kw: pytest.fail('live I/O'))
    base = source_inputs(tmp_path/'fixture')
    inputs = {}
    kinds = []
    for index in range(22):
        # Keep each fixture's valuation identity intact in an independent scenario.
        kind = index % 4
        kinds.append(kind)
        inputs[index] = accounting_loss(deepcopy(base)) if kind == 3 else source_inputs(
            tmp_path/f'source-{index}', risk=kind == 2, timing='FAVORABLE_NOW' if kind == 1 else 'WAIT_FOR_ZONE')
    receipts = []
    for index, inp in inputs.items():
        generation = f'FICTIONAL-CAPABILITY-{index}'
        host, _, code = fixture(tmp_path/f'host-{index}', subjects=[inp['ticker']])
        controller = StrictBlindController.create(tmp_path/f'controller-{index}', generation=generation,
            plan=host.contract['plan'], code_files=[code, __file__, b.__file__, adapter.__file__],
            host_preparation=host.contract['host_preparation'], declared_host_transitions=['CODEX_SANDBOX'])
        adapter.register(controller)
        controller.seal_pre_source(adapter.authorities(controller.contract['plan'], dict(slots=['source-one'])))
        controller.admit_source('source-one', simulated=True)
        source = dict(generation=generation, blind_inputs={inp['ticker']: inp})
        controller.seal_source(source, dict(status='PASS', generation=generation, source_sha256=digest(source)))
        controller.seal_blind_package(b.package(source), validate_source_only=b.validate_package)
        request, = adapter.build_requests(controller)
        controller.seal_requests('BLIND', [request])
        validation = adapter.BlindValidation(request, inp)
        raw = response(validation.subject, validation.audit, risk=kinds[index] == 2,
            timing='FAVORABLE_NOW' if kinds[index] == 1 else 'WAIT_FOR_ZONE')
        context, probe, _ = host_for(controller, request)
        receipt = controller.attempt('BLIND', request, host=context, context=probe,
            transport=lambda payload: encoded(raw), provider_validate=validation.provider,
            semantic_validate=validation.semantic, simulated=True)
        assert receipt['status'] == 'PASS'
        controller.seal_stage('BLIND')
        receipts.append(receipt)
    assert len(receipts) == 22 and set(kinds) == {0, 1, 2, 3}
