"""Five changed-boundary tests only; no model or financial service execution."""
from copy import deepcopy
import json
import os
from pathlib import Path
import zipfile

import pytest
from app.services.dated_research_model import (AXES, build_prompt, digest, encoded,
    load_bound_view, reference_catalog, validate_output)

ARCHIVE=Path(os.environ['C22E_C22D_ZIP'])
SHA='9d503cf07d0904ef98427c67ce1310873c23f930ff2d30318d987c89303c9338'


def candidate(view,binding,catalog):
    ref=next(iter(catalog['refs']))
    result=dict(ticker=view['ticker'],input_digest=binding['research_view_sha256'],as_of=view['as_of'],stage='BLIND',
        thesis_comparison='NOT_COMPARED_TO_REGISTERED_THESIS',what_changes_mind=['New evidence contradicts the hypothesis.'],
        uncertainty=['Independent market expectations not verified.'],adjudication_change_reason='NOT_APPLICABLE_BLIND',
        NO_SEND=True,Strict_NATIVE_STAGE_READY=False,citations=[])
    states=('BUY','ATTRACTIVE','HOLDABLE','HYPOTHESIS','UNKNOWN','POTENTIAL_EXPOSURE','MIXED','MIXED')
    for axis,state in zip(AXES,states):
        result[axis]=dict(state=state,confidence='LOW',statement='Synthetic contract test only, not AI investment analysis.',refs=[ref])
    for fact in catalog['numeric_facts'][:2]:
        result['overall']['refs'].append(fact['ref'])
        result['citations'].append(dict(axis='overall',**fact))
    return result


def test_actual_sealed_bytes_not_only_hash_shape(tmp_path):
    view,binding=load_bound_view(ARCHIVE,expected_zip_sha256=SHA,ticker='005930')
    assert binding['byte_binding_verified']
    with pytest.raises(ValueError,match='sealed_zip_bytes_mismatch'):
        load_bound_view(ARCHIVE,expected_zip_sha256='0'*64,ticker='005930')
    # Even a self-consistent replacement manifest cannot sever original bytes -> research provenance.
    modified=tmp_path/'bad.zip'
    with zipfile.ZipFile(ARCHIVE) as source,zipfile.ZipFile(modified,'w') as target:
        manifest=json.loads(source.read('MANIFEST.json'));name='ORIGINAL_INPUTS/005930.json'
        packet=json.loads(source.read(name));packet['economic']['as_of']='2000-01-01';raw=encoded(packet)
        manifest['files'][name]=dict(bytes=len(raw),sha256=digest(raw))
        for member in source.namelist():
            target.writestr(member,encoded(manifest) if member=='MANIFEST.json' else raw if member==name else source.read(member))
    with pytest.raises(ValueError,match='original_bytes_to_view_provenance_mismatch'):
        load_bound_view(modified,expected_zip_sha256=digest(modified.read_bytes()),ticker='005930')


def test_two_real_prompts_blind_isolated_and_under_budget():
    from scripts.dated_economic_model import command, validate_native_retry_configuration
    with pytest.raises(ValueError,match='ZERO_RETRY_NOT_VERIFIED'):
        validate_native_retry_configuration()
    argv=command(Path('/existing/codex'),root=Path('/isolated'),schema=Path('/schema'),output=Path('/output'))
    assert not any('model_providers.openai' in arg for arg in argv)
    assert '--sandbox' in argv and 'read-only' in argv and 'gpt-6.1-sol' in argv
    for ticker in ('005930','MU'):
        view,binding=load_bound_view(ARCHIVE,expected_zip_sha256=SHA,ticker=ticker)
        prompt,schema,catalog=build_prompt(view,binding,stage='BLIND')
        payload=json.loads(prompt.split(b'BOUND_RESEARCH_INPUT:\n')[1])
        assert payload['accepted_blind'] is None and payload['stage']=='BLIND'
        assert len(prompt)<=384*1024 and schema['properties']['input_digest']['const']==binding['research_view_sha256']
        assert view['verified_mechanism_count']==0 and catalog['numeric_facts']
        if ticker=='MU':assert b'FISCAL_WEEK_COUNT_DIFFERENCE' in prompt


def test_exact_numeric_period_refs_and_no_fact_promotion():
    view,binding=load_bound_view(ARCHIVE,expected_zip_sha256=SHA,ticker='005930');catalog=reference_catalog(view)
    result=candidate(view,binding,catalog)
    validate_output(encoded(result),view=view,binding=binding,stage='BLIND',catalog=catalog)
    for field,value in [('value',-999),('period','2000-01-01'),('unit','FAKE'),('ref','not-original')]:
        bad=deepcopy(result);bad['citations'][0][field]=value
        with pytest.raises(ValueError):validate_output(encoded(bad),view=view,binding=binding,stage='BLIND',catalog=catalog)
    for axis,state in [('business_mechanism','FACT'),('market_expectations','FACT'),('structural_risk','OBSERVED_RISK')]:
        bad=deepcopy(result);bad[axis]['state']=state
        with pytest.raises(ValueError):validate_output(encoded(bad),view=view,binding=binding,stage='BLIND',catalog=catalog)


def test_adj_requires_valid_blind_and_no_wait_for_unknown():
    view,binding=load_bound_view(ARCHIVE,expected_zip_sha256=SHA,ticker='MU');catalog=reference_catalog(view)
    result=candidate(view,binding,catalog)
    assert result['market_expectations']['state']=='UNKNOWN'
    accepted=validate_output(encoded(result),view=view,binding=binding,stage='BLIND',catalog=catalog)
    assert accepted['newbuyer']['state']=='ATTRACTIVE'
    prompt,_,_=build_prompt(view,binding,stage='ADJUDICATION',prior=accepted)
    assert json.loads(prompt.split(b'BOUND_RESEARCH_INPUT:\n')[1])['accepted_blind']==accepted
    with pytest.raises(ValueError):build_prompt(view,binding,stage='ADJUDICATION')
    bad=deepcopy(accepted);bad['input_digest']='0'*64
    with pytest.raises(Exception):build_prompt(view,binding,stage='ADJUDICATION',prior=bad)


def test_native_and_sr_exact_citations_without_owner_upgrade():
    view,binding=load_bound_view(ARCHIVE,expected_zip_sha256=SHA,ticker='005930');catalog=reference_catalog(view)
    native=[n for n in catalog['numeric_facts'] if n['ref'].startswith('native:')]
    sr=[n for n in catalog['numeric_facts'] if n['ref'].startswith(('v3-zone:','dated-structure:'))]
    assert native and sr and any(n['unit'] is None for n in native)
    result=candidate(view,binding,catalog)
    for fact in (native[0],sr[0]):
        result['technical_price_structure']['refs'].append(fact['ref'])
        result['citations'].append(dict(axis='technical_price_structure',**fact))
    accepted=validate_output(encoded(result),view=view,binding=binding,stage='BLIND',catalog=catalog)
    assert accepted['Strict_NATIVE_STAGE_READY'] is False and accepted['NO_SEND'] is True
