"""Synthetic supplemental wiring, not real KIS economic authority."""
from copy import deepcopy
import pytest
from test_vnext_unified_judgment import fixture
from app.services import vnext_unified_judgment as m
from app.services.vnext_optional_fy1_research import attach


class SyntheticOwner:
    def __init__(self, security):
        self.security = security
        self.revoked = False

    def snapshots(self, *, security, cutoff):
        if self.revoked or security != self.security:
            raise ValueError('synthetic_owner_revoked_or_wrong_security')
        return [dict(metric='FY1_EPS',value='27.5',unit='KRW_PER_SHARE',
            retrieval_timestamp='2026-01-01T00:00:00+00:00',estimate_date='2025-12-30',
            period='2026.12E',fiscal_inventory_as_of='2025-12-01',source_generation='synthetic',
            lineage_sha256='a'*64,policy_version='synthetic-test-only')]


def case():
    p,v,r=fixture()
    owner=SyntheticOwner(deepcopy(p['base']['public_security']))
    p=attach(p['base'],numeric_owner=owner)
    kw=dict(registry=r,dated_numeric_context=True,numeric_owner=owner)
    return p,v,r,owner,kw


def test_optional_context_default_off_and_no_new_decision_axis():
    p,v,r,owner,kw=case()
    old=m.build_bundle(p,registry=r)
    assert 'dated_numeric_context' not in old
    packet=m.build_bundle(p,**kw)
    assert packet['admissibility']==old['admissibility']
    assert packet['valuation_facts']==old['valuation_facts']
    assert packet['dated_numeric_context']['economic_refs']==[]
    assert packet['dated_numeric_context']['current_qualified'] is False
    assert m.validate_and_render(v,packet,economic_loader=lambda:p,**kw)['decision']['newbuyer_fundamental']=='ATTRACTIVE'
    text=m.prompt(packet,'BLIND',knowledge={},registry=r)
    assert '27.5' in text and '2025-12-01' in text
    assert 'not evidence refs for any decision axis' in text


@pytest.mark.parametrize('change',['value','period','source','identity','revoked','no_owner','no_opt_in'])
def test_context_rebinds_original_owner_on_each_validation(change):
    p,v,r,owner,kw=case();packet=m.build_bundle(p,**kw)
    if change=='identity':p['base']['public_security']['ticker']='WRONG'
    elif change=='revoked':owner.revoked=True
    elif change=='no_owner':kw['numeric_owner']=None
    elif change=='no_opt_in':kw['dated_numeric_context']=False
    else:p['numeric_reference_catalog'][0][{'value':'value','period':'forecast_period','source':'source_generation'}[change]]='CHANGED'
    with pytest.raises(ValueError):m.validate_and_render(v,packet,economic_loader=lambda:p,**kw)


@pytest.mark.parametrize('axis',['driver','valuation','holder','overall'])
def test_supplemental_ref_cannot_become_economic_ref(axis):
    p,v,r,owner,kw=case();packet=m.build_bundle(p,**kw)
    ref=packet['dated_numeric_context']['numbers'][0]['catalog_id']
    if axis=='driver':v['economic_drivers_positive'][0]['refs']=[ref]
    else:v[{'valuation':'valuation','holder':'holder_virtual','overall':'overall'}[axis]]['refs']=[ref]
    with pytest.raises(ValueError):m.validate_and_render(v,packet,economic_loader=lambda:p,**kw)
