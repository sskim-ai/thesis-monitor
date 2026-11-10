"""Consumer-boundary tests on already sealed outputs; no inference or source collection."""
from copy import deepcopy
import importlib.util
import json
from pathlib import Path
import pytest
from app.services.dated_research_model import digest,encoded
from app.services.dated_split_research_consumer import build_message,render_message,validate_message

@pytest.fixture(scope='module')
def cases():
    path=Path(__file__).resolve().parents[3]/'maintenance/20261110-c22k-v2/inputs.py'
    spec=importlib.util.spec_from_file_location('c22k_inputs',path);mod=importlib.util.module_from_spec(spec);spec.loader.exec_module(mod)
    return mod.load_cases()[0]

@pytest.fixture(scope='module')
def messages(cases):
    return {t:build_message(**c) for t,c in cases.items()}

def test_five_real_messages_json_markdown_values_and_two_axes(messages):
    assert len(messages)==5
    for m in messages.values():
        text=render_message(m);assert json.loads(encoded(m))==m
        for axis in m['split_panel']['axes'].values():assert axis['state'] in text
        for c in m['split_panel']['citations']:assert str(c['value']) in text and c['source_sha256'] in text
        assert m['new_overall_or_holder_issued'] is False and m['NO_SEND'] is True

def test_wrong_view_or_time_join_rejected(cases):
    for key,value in [('input_digest','0'*64),('as_of','2026-11-05T00:00:00+00:00')]:
        c=deepcopy(cases['MU']);p=json.loads(c['prior_raw']);p[key]=value;c['prior_raw']=encoded(p)
        c['sealed_hashes']['prior']=digest(c['prior_raw']);c['prior_receipt']['accepted_sha256']=digest(c['prior_raw'])
        with pytest.raises(ValueError,match='different_research'):build_message(**c)

def test_source_member_and_no_send_denials(cases,messages):
    c=deepcopy(cases['MU']);c['sealed_hashes']['split']='0'*64
    with pytest.raises(ValueError,match='sealed_member'):build_message(**c)
    m=deepcopy(messages['MU']);m['NO_SEND']=False
    with pytest.raises(ValueError,match='scope'):validate_message(m,view=json.loads(cases['MU']['preview_raw'])['source_view'])

def test_mu_positive_and_kai_negative_not_forced_to_wait(messages):
    assert messages['MU']['split_panel']['axes']['newbuyer_fundamental_attractiveness']['state']=='ATTRACTIVE'
    assert messages['MU']['split_panel']['axes']['newbuyer_entry_timing']['state']=='UNFAVORABLE'
    assert messages['047810']['split_panel']['axes']['newbuyer_fundamental_attractiveness']['state']=='UNATTRACTIVE'
    assert any(f['field']=='financial.operating_income' for f in messages['047810']['financial'])

def test_corz_neutral_does_not_hide_risk_or_pbr_conflict(messages):
    m=messages['CORZ'];assert m['split_panel']['axes']['newbuyer_fundamental_attractiveness']['state']=='NEUTRAL'
    assert any('PBR_VS_NEGATIVE' in w for w in m['warnings'])
    assert m['structural_risk']['meaning']=='UNASSESSED_SENTINEL_NOT_RISK_ABSENT'

def test_legacy_holder_separate_not_actual_and_missing_metrics_positive(messages):
    for m in messages.values():
        assert m['prior_panel']['scope']=='PRIOR_C22G_ADJ_RESEARCH_ONLY'
        assert m['prior_panel']['actual_holdings_or_private_thesis_used'] is False
    assert 'FY1_EPS' in messages['005930']['missing_metrics']
    assert 'PER' in messages['CORZ']['missing_metrics']
    assert 'fPER' not in messages['MU']['missing_metrics']

def test_temporal_retrospective_original_contracts_and_week_difference(messages):
    for m in messages.values():
        for v in m['valuations']:
            assert v['PIT_available_at_cutoff'] is False
            assert v['temporal']['historical_information_cutoff']==m['as_of']
            assert v['original_contract'] and v['original_use_limits']['overall_direction_use'] is False
    periods=[r['fiscal_comparability'] for r in messages['MU']['financial'] if r['fiscal_comparability']]
    assert any(p['current_weeks']==53 and p['prior_weeks']==52 for p in periods)
    assert any(r['anomaly_cautions'] for r in messages['000660']['financial'])

def test_report_only_four_entry_warnings(messages):
    flag='newbuyer_entry_timing:FREE_PROSE_NUMERIC_COVERAGE_NOT_PROVEN'
    assert sum(flag in m['quality_report']['flags'] for m in messages.values())==4
    assert all(m['quality_report']['report_only'] for m in messages.values())

def test_projection_source_number_period_and_sentinel_tampering(cases,messages):
    view=json.loads(cases['MU']['preview_raw'])['source_view']
    for key,value in [('value','999999'),('unit','WRONG'),('period','1900-01-01'),('source_sha256','0'*64)]:
        m=deepcopy(messages['MU']);m['split_panel']['citations'][0][key]=value
        with pytest.raises(ValueError):validate_message(m,view=view)
    m=deepcopy(messages['MU']);m['structural_risk']['meaning']='NO_RISK'
    with pytest.raises(ValueError,match='sentinel'):validate_message(m,view=view)
    m=deepcopy(messages['MU']);m['financial'][0]['observations'][0]['value']='123'
    with pytest.raises(ValueError):validate_message(m,view=view)
    m=deepcopy(messages['MU']);m['valuations'][0]['PIT_available_at_cutoff']=True
    with pytest.raises(ValueError,match='temporal'):validate_message(m,view=view)

def test_new_prose_has_no_unchecked_digits_and_current_scope_denied(messages,cases):
    for m in messages.values():
        for a in m['split_panel']['axes'].values():
            for item in [a['statement'],*a['pro'],*a['con']]:
                if item['text']:assert not any(x.isdigit() for x in item['text'])
    m=deepcopy(messages['MU']);m['research_mode']='POINT_IN_TIME'
    with pytest.raises(ValueError,match='scope'):validate_message(m,view=json.loads(cases['MU']['preview_raw'])['source_view'])
