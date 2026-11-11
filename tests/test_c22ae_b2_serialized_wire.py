"""Saved original requests retain exact payload SHA and closed schema meaning."""
from copy import deepcopy
import json
import pytest

from app.services import new_buyer_request_owner as owner
from app.services.unified_snapshot_contract import digest
from scripts.kis_eps_wire_calibration import sealed
from tests.test_production_b2_execution import request_and_auth,body


def test_original_b2_survives_sorted_json_without_changing_raw_request_or_economics():
    request,auth,_=request_and_auth(timing='WAIT_FOR_ZONE')
    saved=json.loads(json.dumps(request,sort_keys=True))
    before=deepcopy(saved)
    assert owner.provider_payload(saved,expected_request_sha256=auth.request_sha256)==request['provider_request']
    assert owner.validate_result(json.loads(body(request)),saved,expected_request_sha256=auth.request_sha256)['status']=='PASS'
    assert saved==before
    with pytest.raises(ValueError):owner.provider_payload(saved,expected_request_sha256='0'*64)


@pytest.mark.parametrize('mutation',['remove_required','duplicate_required','change_const'])
def test_orderless_required_does_not_allow_schema_semantic_changes(mutation):
    request,_,_=request_and_auth(timing='WAIT_FOR_ZONE')
    def find(node,key):
        if isinstance(node,dict):
            if key in node:return node
            for value in node.values():
                result=find(value,key)
                if result is not None:return result
        elif isinstance(node,list):
            for value in node:
                result=find(value,key)
                if result is not None:return result
    wire=request['provider_request']['response_schema']
    if mutation=='remove_required':find(wire,'required')['required'].pop()
    elif mutation=='duplicate_required':
        row=find(wire,'required');row['required'].append(row['required'][0])
    else:find(wire,'const')['const']='OFFLINE_FORGED_CONST'
    request['request_sha256']=digest(request['provider_request'])
    request=sealed({k:v for k,v in request.items() if k!='receipt_sha256'})
    with pytest.raises(ValueError):owner.provider_payload(request,expected_request_sha256=request['request_sha256'])


def test_required_word_inside_const_data_is_not_treated_as_a_schema_keyword():
    a={'type':'object','properties':{'required':{'const':{'required':['b','a']}}},'required':['required']}
    b=deepcopy(a);b['properties']['required']['const']['required'].reverse()
    assert owner._required_order_only(a)!=owner._required_order_only(b)
    assert owner._required_order_only(a)==a
