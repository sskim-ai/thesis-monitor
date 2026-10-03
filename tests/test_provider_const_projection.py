"""Offline provider-wire parity, not a live provider acceptance certificate."""
from copy import deepcopy
from decimal import Decimal
import json
from pathlib import Path

import pytest

from scripts.m12cs_r1_provider_schema import (
    infer_const_json_type, project_provider_wire_schema, scan_provider_structured_output_schema,
)
from scripts.websocket_timeout_runtime_review_first_a_closeout import validate_json_schema
from scripts.newbuyer_b2_shadow_failure import request_schema_rejection


def obj(properties):
    return dict(type='object',properties=properties,required=list(properties),additionalProperties=False)


def project(node):
    schema,receipt=project_provider_wire_schema(obj(dict(value=node)))
    assert scan_provider_structured_output_schema(schema)['status']=='PASS'
    return schema['properties']['value'],receipt


@pytest.mark.parametrize('value,kind', [('WAIT','string'),(True,'boolean'),(False,'boolean'),
    (7,'integer'),(1.5,'number'),(None,'null')])
def test_primitive_const_matrix(value,kind):
    assert infer_const_json_type(value)==kind
    for node in ({'const':value},{'const':value,'type':kind}):
        before=deepcopy(node)
        wire,_=project(node)
        assert wire=={'const':value,'type':kind} and node==before
    with pytest.raises(ValueError,match='provider_const_type_mismatch'):
        project(dict(const=value,type='array'))


@pytest.mark.parametrize('value', [float('nan'),float('inf'),float('-inf'),{'x':float('inf')}])
def test_nonfinite_constants_fail_closed(value):
    with pytest.raises(ValueError,match='provider_const_nonfinite_number'):
        project(dict(const=value))
    scan=scan_provider_structured_output_schema(obj(dict(v=dict(const=value,type='number'))))
    assert any(e.startswith('const_nonfinite_number:') for e in scan['errors'])


@pytest.mark.parametrize('value', [Decimal('1.0'),(1,2),{1:'key'},set(),object()])
def test_python_only_values_rejected(value):
    with pytest.raises(ValueError,match='provider_const_unsupported'):
        project(dict(const=value))


def test_recursive_value_and_bool_integer_mismatch():
    value=[]
    value.append(value)
    with pytest.raises(ValueError,match='provider_const_unsupported'):
        project(dict(const=value))
    with pytest.raises(ValueError,match='provider_const_type_mismatch'):
        project(dict(const=True,type='integer'))
    assert project(dict(const=1,type='number'))[0]['type']=='number'


def test_compatible_constraints_preserved_conflicts_rejected():
    node=dict(const='WAIT',pattern='^WAIT$',minLength=4,maxLength=4,enum=['WAIT'])
    assert project(node)[0]==dict(node,type='string')
    for bad in (dict(const='WAIT',minLength=5),dict(const=4,maximum=3),
                dict(const='WAIT',enum=['BUY']),dict(const=4,multipleOf=3),
                dict(const='abc',format='email')):
        with pytest.raises(ValueError,match='provider_const_constraint'):
            project(bad)


def test_object_const_lowering_is_strict_and_local_order_stays_exact():
    value=dict(state='WAIT_FOR_ZONE',selected='candidate-x',evidence_refs=['ref-a','ref-b'])
    local=dict(const=value)
    wire,receipt=project(local)
    assert wire['type']=='object' and wire['required']==list(value)
    assert wire['additionalProperties'] is False and 'const' not in wire
    assert wire['properties']['state']==dict(type='string',const='WAIT_FOR_ZONE')
    assert receipt['const_lowering']['counts']['object']==1
    assert not validate_json_schema(value,wire) and not validate_json_schema(value,local)
    for bad in ({'selected':'candidate-x','evidence_refs':['ref-a','ref-b']},
                {**value,'extra':True},{**value,'state':'OTHER'}):
        assert validate_json_schema(bad,wire)
    reordered={**value,'evidence_refs':['ref-b','ref-a']}
    duplicate={**value,'evidence_refs':['ref-a','ref-a']}
    assert not validate_json_schema(reordered,wire)
    assert validate_json_schema(reordered,local) and validate_json_schema(duplicate,local)


@pytest.mark.parametrize('values', [[],['a'],['a','b']])
def test_ref_array_const_lowering(values):
    local=obj(dict(new_buyer_shadow=obj(dict(active_risk_refs=dict(const=values)))))
    wire,receipt=project_provider_wire_schema(local)
    assert scan_provider_structured_output_schema(wire)['status']=='PASS'
    node=wire['properties']['new_buyer_shadow']['properties']['active_risk_refs']
    assert node['type']=='array' and node['items']['type']=='string'
    assert node['minItems']==node['maxItems']==len(values)
    assert receipt['const_lowering']['counts']['array']==1


@pytest.mark.parametrize('values,kind', [([1,2],'integer'),([1,2.5],'number'),
    ([True,False],'boolean'),([None,None],'null')])
def test_nonempty_homogeneous_primitive_arrays(values,kind):
    wire,_=project(dict(const=values))
    assert wire['items']['type']==kind and wire['minItems']==wire['maxItems']==2


def test_empty_array_requires_exact_owner_or_explicit_item_type():
    for schema in (obj(dict(evidence_refs=dict(const=[]))),obj(dict(unrelated=obj(
            dict(active_risk_refs=dict(const=[])))))):
        with pytest.raises(ValueError,match='provider_empty_const_array_item_type_unowned'):
            project_provider_wire_schema(schema)
    assert project(dict(const=[],items=dict(type='integer')))[0]['items']==dict(type='integer')
    bad=obj(dict(new_buyer_shadow=obj(dict(active_risk_refs=dict(const=[],items={})))))
    with pytest.raises(ValueError,match='provider_const_constraint_review_required'):
        project_provider_wire_schema(bad)


@pytest.mark.parametrize('value', [[1,'a'],[True,1],[{'x':1}],[['a']]])
def test_complex_array_fail_closed(value):
    with pytest.raises(ValueError,match='provider_complex_const_array_review_required'):
        project(dict(const=value))


@pytest.mark.parametrize('node', [dict(const='x'),dict(type='integer',const=True),
    dict(type='array'),dict(type='array',items={}),dict(type='array',items=dict(const='x')),
    dict(type='object'),dict(properties={'x':dict(type='string')}),
    dict(type='object',properties={'x':dict(type='string')},required=[],additionalProperties=False),
    dict(type='object',properties={},required=[],additionalProperties=True),
    dict(type='string',items=dict(const='x')),dict(type='string',items=dict(type='string')),
    dict(anyOf={'const':'x'}),dict(type='string',**{'$defs':[]}),
    dict(anyOf=[dict(const='x')]),dict(type='object',properties={},required=[],additionalProperties=False,
        **{'$defs':{'bad':dict(const='x')}})])
def test_scanner_rejects_missing_types_and_unclosed_nested_shapes(node):
    assert scan_provider_structured_output_schema(obj(dict(v=node)))['status']=='FAIL'


def test_schema_walker_never_modifies_constant_payload_as_schema():
    wire,_=project(dict(const={'properties':'literal','uniqueItems':True,'type':'data'}))
    assert wire['properties']['uniqueItems']==dict(type='boolean',const=True)
    assert wire['properties']['type']==dict(type='string',const='data')


def test_exact_rev53_corz_wire_fixture():
    path=Path(__file__).parent/'fixtures/rev53_corz_provider_wire_schema.json'
    old=json.loads(path.read_bytes())
    before=deepcopy(old)
    scan=scan_provider_structured_output_schema(old)
    assert scan['status']=='FAIL'
    assert 'const_type_missing:$.properties.new_buyer_shadow.anyOf[0].properties.contract' in scan['errors']
    wire,_=project_provider_wire_schema(old)
    assert scan_provider_structured_output_schema(wire)['status']=='PASS'
    assert wire['properties']['new_buyer_shadow']['anyOf'][0]['properties']['contract']=={
        'type':'string','const':'newbuyer-qualified-valuation-context-v1'}
    assert old==before


def event(status=400,code='invalid_json_schema',kind='error'):
    body=dict(status=status,error=dict(type='invalid_request_error',code=code,
        message="schema must have a 'type' key"))
    if kind=='error':
        return json.dumps(dict(type=kind,message=json.dumps(body))).encode()
    return json.dumps(dict(type=kind,error=dict(message=json.dumps(body)))).encode()


@pytest.mark.parametrize('kind',['error','turn.failed'])
def test_exact_request_schema_rejection(kind):
    assert request_schema_rejection(event(kind=kind))==dict(
        failure_kind='REQUEST_SCHEMA_PROVIDER_REJECTED',retry_eligible=False,
        http_status=400,provider_error_code='invalid_json_schema')


@pytest.mark.parametrize('payload',[event(status=401),event(status=429),event(status=503),
    event(code='invalid_api_key'),event(code='output_schema_mismatch'),b'timeout',
    json.dumps(dict(type='item.completed',item={'text':event().decode()})).encode()])
def test_request_classifier_never_conflates_auth_transport_or_output(payload):
    assert request_schema_rejection(payload) is None
