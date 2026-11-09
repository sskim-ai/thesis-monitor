"""Only new C22G focused checks; no model subprocesses."""
import json
from pathlib import Path
import zipfile
import pytest
from scripts import c22g_batch as m
from app.services.dated_research_model import build_prompt, reference_catalog, validate_output, encoded

def test_five_sealed_bindings_and_blind_isolation():
    for ticker in m.TICKERS:
        v,b=m.load_bound_view(m.ARCHIVE,expected_zip_sha256=m.SOURCE_SHA,ticker=ticker)
        prompt,schema,catalog=build_prompt(v,b,stage='BLIND')
        payload=json.loads(prompt.split(b'BOUND_RESEARCH_INPUT:\n')[1])
        assert payload['ticker']==ticker and payload['accepted_blind'] is None
        assert catalog==reference_catalog(v) and len(prompt)<384*1024
        assert all(x['ref'] in catalog['refs'] for x in catalog['numeric_facts'])

def test_marker_is_durable_and_duplicate_refused(tmp_path):
    p=tmp_path/'MODEL_STARTED.json';m.mark(p,{'status':'STARTED'})
    before=p.read_bytes()
    with pytest.raises(FileExistsError):m.mark(p,{'status':'RETRY'})
    assert p.read_bytes()==before

def fixtures(monkeypatch,tmp_path):
    monkeypatch.setattr(m,'OUT',tmp_path)
    return {t:({}, {}) for t in m.TICKERS}

def test_local_blind_failure_skips_only_same_adj(monkeypatch,tmp_path):
    views=fixtures(monkeypatch,tmp_path);calls=[]
    def execute(t,s,v,b,prior):
        calls.append((t,s))
        r=dict(ticker=t,stage=s,status='ACCEPTED',actually_spawned=1)
        if t=='MU' and s=='BLIND':
            r.update(status='FAILED',failure_code='numeric_value_unit_period_basis_mismatch',failure_scope='LOCAL');return r,None
        return r,{'ticker':t}
    r=m.orchestrate(views,{'ticker':'005930'},execute)
    assert ('MU','ADJUDICATION') not in calls and ('000660','BLIND') in calls
    assert len(calls)==8 and r['global_stop'] is None

def test_global_failure_stops_all_remaining(monkeypatch,tmp_path):
    views=fixtures(monkeypatch,tmp_path);calls=[]
    def execute(t,s,v,b,prior):
        calls.append((t,s));return dict(ticker=t,stage=s,status='FAILED',actually_spawned=1,failure_code='unexpected_tool_activity',failure_scope='GLOBAL'),None
    r=m.orchestrate(views,{'ticker':'005930'},execute)
    assert len(calls)==1 and r['actually_spawned']==1
    assert sum(x['status']=='NOT_ATTEMPTED' for x in r['stages'])==8

def test_raw_prior_full_citations_revalidate():
    p=m.ROOT/'maintenance/20261109-c22f-v2/live-once/private-evidence'
    v,b=m.load_bound_view(m.ARCHIVE,expected_zip_sha256=m.SOURCE_SHA,ticker='005930')
    raw=(p/'response.json').read_bytes();prior=validate_output(raw,view=v,binding=b,stage='BLIND',catalog=reference_catalog(v))
    assert len(prior['citations'])==16 and encoded(prior)==(p/'accepted-BLIND.json').read_bytes()
    prompt,_,_=build_prompt(v,b,stage='ADJUDICATION',prior=prior)
    assert json.loads(prompt.split(b'BOUND_RESEARCH_INPUT:\n')[1])['accepted_blind']==prior

def test_blind_archive_checker_rejects_contamination(tmp_path):
    import importlib.util
    spec=importlib.util.spec_from_file_location('checker',m.OUT/'TM_C22G_V2_REVIEW_ARCHIVE_CHECK.py')
    checker=importlib.util.module_from_spec(spec);spec.loader.exec_module(checker)
    zpath=tmp_path/'bad.zip';files={'RESULT.json':b'{}'}
    manifest={'files':{n:dict(bytes=len(b),sha256=m.digest(b)) for n,b in files.items()}}
    with zipfile.ZipFile(zpath,'x') as z:
        for n,b in files.items():z.writestr(n,b)
        z.writestr('MANIFEST.json',encoded(manifest))
    result=checker.input_audit(zpath,m.ARCHIVE)
    assert 'disallowed_blind_input_member:RESULT.json' in result['errors']
