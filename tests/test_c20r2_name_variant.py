"""Focused synthetic inputs through the unchanged original snapshot builder."""
from copy import deepcopy
import json
import pytest
from tests.rev28_native_fixtures import native_input,security
from app.services.provider_native_valuation_snapshot import derive_provider_snapshots
from app.services.unified_snapshot_contract import encoded
from app.services.unified_run_artifacts import sha256_bytes

def alter(part,change):
    body=json.loads(part['raw']);change(body);part['raw']=encoded(body)
    part['receipt']['source_sha256']=sha256_bytes(part['raw'])

def setup(ticker='999999',registered='Registered Name',provider='Provider Name'):
    sec=security(ticker);sec['company_name']=registered;inputs=native_input(sec)
    alter(inputs,lambda b:b.update(stk_nm=provider))
    alter(inputs['identity_inputs']['list_pages'][0],lambda b:b['list'][0].update(name=provider))
    return sec,inputs

def derive(sec,inputs):return derive_provider_snapshots(inputs,security=sec,run_id='fictional-snapshot')

@pytest.mark.parametrize('ticker,registered,provider',[
    ('010120','LS일렉트릭','LS ELECTRIC'),('047810','한국항공우주산업','한국항공우주')])
def test_registered_variant_only_is_nonblocking(ticker,registered,provider):
    sec,inputs=setup(ticker,registered,provider)
    assert ''.join(c for c in registered.casefold() if c.isalnum()) != ''.join(c for c in provider.casefold() if c.isalnum())
    for row in derive(sec,inputs):
        assert row.display_eligible and row.value>0 and not row.overall_direction_use
        assert row.security_identity_receipt['name_diagnostics']==['REGISTERED_NAME_VARIANT_NONBLOCKING']

@pytest.mark.parametrize('case',['wrong_code','missing','duplicate','market','exchange','internal_name',
    'none','empty','space','punctuation','nonstring','raw_hash','alias_evidence','invalid_ratio'])
def test_original_guards_and_nonempty_provider_names(case):
    sec,inputs=setup();page=inputs['identity_inputs']['list_pages'][0]
    if case=='wrong_code':alter(inputs,lambda b:b.update(stk_cd='999998'))
    elif case=='missing':alter(page,lambda b:b.update(list=[]))
    elif case=='duplicate':alter(page,lambda b:b['list'].append(deepcopy(b['list'][0])))
    elif case=='market':alter(page,lambda b:b['list'][0].update(marketCode='10'))
    elif case=='exchange':alter(page,lambda b:b['list'][0].update(marketName='NASDAQ'))
    elif case=='internal_name':alter(inputs,lambda b:b.update(stk_nm='Other Provider Name'))
    elif case in ('none','empty','space','punctuation','nonstring'):
        value={'none':None,'empty':'','space':'  ','punctuation':'---...','nonstring':123}[case]
        alter(inputs,lambda b:b.update(stk_nm=value));alter(page,lambda b:b['list'][0].update(name=value))
    elif case=='raw_hash':inputs['raw']=b'{}'
    elif case=='alias_evidence':
        from app.services.reviewed_security_alias import ReviewedSecurityAliases
        reviews=[];owner=ReviewedSecurityAliases(lambda:{},lambda:reviews)
        reviews.append({'contract':'INVALID_EVIDENCE'})
        inputs['identity_inputs']['reviewed_alias_owner']=owner
    elif case=='invalid_ratio':alter(inputs,lambda b:b.update(per='0'))
    if case in ('raw_hash','alias_evidence'):
        with pytest.raises(ValueError):derive(sec,inputs)
    elif case=='invalid_ratio':
        per,pbr=derive(sec,inputs);assert not per.display_eligible and pbr.display_eligible
    else:assert all(not r.display_eligible and r.state=='UNAVAILABLE_SECURITY_IDENTITY' for r in derive(sec,inputs))

def test_unchanged_name_has_no_new_identity_keys():
    sec=security('999999');rows=derive(sec,native_input(sec))
    assert all(r.display_eligible and 'name_diagnostics' not in r.security_identity_receipt for r in rows)
