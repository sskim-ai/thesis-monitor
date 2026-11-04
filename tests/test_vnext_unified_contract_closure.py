"""Cross-field contrasts. Synthetic mechanics, never real issuer acceptance."""
from copy import deepcopy
import pytest
from test_vnext_unified_judgment import fixture, check
from app.services import vnext_unified_judgment as m


def test_absent_risk_requires_empty_reason_without_repair():
    p,v,r=fixture()
    assert check(p,v,r)['decision']['newbuyer_fundamental']=='ATTRACTIVE'
    v['active_material_risk_reason']='No active risk is established; absence of risk is also unproven.'
    before=deepcopy(v)
    with pytest.raises(ValueError,match='^unified_risk_without_evidence$'):check(p,v,r)
    assert v==before


def test_present_risk_needs_reason_and_retains_avoid():
    p,v,r=fixture()
    p['base']['evidence'][0]['data']['fields']['structural_risk_verified']=True
    v['economic_drivers_negative']=deepcopy(v['economic_drivers_positive'])
    v['business']='MIXED';v['active_material_risk_refs']=['business']
    with pytest.raises(ValueError,match='unified_unbound_action'):check(p,v,r)
    v['active_material_risk_reason']='Admitted current structural impairment remains material.'
    assert check(p,v,r)['decision']['newbuyer_fundamental']=='AVOID'


@pytest.mark.parametrize('change,error',[
    ('empty_driver','unified_empty_driver'),
    ('business','unified_business_driver_binding'),
    ('lineage','unified_driver_lineage_double_count'),
    ('quality','unified_evidence_use_denied'),
    ('veto','unified_confidence_veto_binding'),
    ('valuation_refs','unified_valuation_source_missing'),
    ('valuation_confidence','unified_axis_confidence'),
    ('holder_economic','unified_holder_economic_basis'),
    ('holder_adverse','unified_holder_adverse_basis'),
    ('newbuyer_confidence','unified_newbuyer_confidence'),
])
def test_single_cross_field_rejection(change,error):
    p,v,r=fixture();check(p,v,r)
    if change=='empty_driver':v['economic_drivers_positive'][0]['refs']=[]
    if change=='business':v['business']='MIXED'
    if change=='lineage':v['economic_drivers_positive']*=2
    if change=='quality':v['business_quality_denials']=['business']
    if change=='veto':v['confidence_veto_refs']=['business']
    if change=='valuation_refs':v['valuation']['refs']=[]
    if change=='valuation_confidence':v['valuation']['confidence']='NOT_SEPARATELY_ISSUED'
    if change=='holder_economic':v['holder_virtual']['refs']=[];v['holder_virtual']['stance']='REVIEW';v['holder_virtual']['confidence']='MEDIUM'
    if change=='holder_adverse':v['holder_virtual']['refs']=['business'];v['holder_virtual']['stance']='REDUCE';v['holder_virtual']['confidence']='MEDIUM'
    if change=='newbuyer_confidence':v['newbuyer_confidence']='NOT_SEPARATELY_ISSUED'
    with pytest.raises(ValueError,match='^'+error+'$'):check(p,v,r)


def test_unissued_valuation_is_not_neutral_or_confident_newbuyer():
    p,v,r=fixture();v['valuation']['judgment']='NOT_ISSUED'
    v['valuation']['confidence']='NOT_SEPARATELY_ISSUED'
    v['newbuyer_confidence']='NOT_SEPARATELY_ISSUED'
    assert check(p,v,r)['decision']['newbuyer_fundamental']=='NOT_ISSUED'


def test_prompt_schema_share_conditions_not_new_output_structure():
    p,v,r=fixture();packet=m.build_bundle(p,registry=r)
    text=m.prompt(packet,'BLIND',knowledge={},registry=r)
    schema=m.schema(security_id=v['security_id'])
    for field,rule in m.FIELD_RULES.items():
        assert rule in text and schema['properties'][field]['description']==rule
    assert schema['$defs']['TechnicalReview']['properties']['security_id']['const']==v['security_id']
    assert set(schema['properties'])==set(v)
    assert m.CONTRACT=='UNIFIED_JUDGMENT_V1' and not m.ENABLED_BY_DEFAULT
