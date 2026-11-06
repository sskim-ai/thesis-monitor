"""Typed fresh evidence, not changing registration flags or Native authority."""
from datetime import datetime,timezone
from app.services import prospective_class_c_owner as owner
from app.services.fresh_registered_identity import FreshRegisteredIdentityReader,FreshIdentityObservation
from test_c10r_identity_discovery import discovery_capture
from test_minimal_class_c_export import POLICY
import pytest


class SyntheticReader(FreshRegisteredIdentityReader):
    def __init__(self):self.at=datetime.now(timezone.utc);self.change=None
    def read(self, original):
        current=original.model_copy(deep=True)
        if self.change=='flags':current.identity_quality='verified'
        if self.change=='security':current.canonical_security_id='OTHER'
        if self.change=='ratio':current.adr_ratio=50
        if self.change=='ordinary':current.ordinary_share_identifier='OTHER'
        if self.change=='class':current.security_type='common_stock'
        return FreshIdentityObservation(current.model_dump_json(),
            'mock' if self.change=='provider' else 'sec_official_identity',self.at,'a'*64,'b'*64,
            'NOT_ADMITTED' if self.change=='status' else 'QUALIFIED_EXACT_SECURITY')


def test_fresh_original_identity_allows_source_intake_without_flag_changes(tmp_path):
    approval,capture,_,_=discovery_capture(tmp_path,mutation="UPDATE securitymaster SET identity_quality='missing'")
    reader=SyntheticReader()
    handle,receipt=owner.issue_source_intake_owner(approval=approval,capture=capture,market='us',
        generation_id='SYNTHETIC_FRESH',policy=POLICY,fresh_identity_reader=reader)
    assert receipt['subjects']['NEWUS']['registered_source_intake_eligible']
    identities,*_=owner.source_intake_snapshot(handle,generation_id='SYNTHETIC_FRESH',subjects=('NEWUS',),policy=POLICY)
    assert identities['NEWUS']['identity_quality']=='missing'
    assert not receipt['source_or_economic_authority'] and not receipt['production_seed_qualified']
    reader.change='status'
    with pytest.raises(ValueError):owner.require_source_intake(handle,generation_id='SYNTHETIC_FRESH',ticker='NEWUS')


@pytest.mark.parametrize('change',['flags','security','provider','status','serialized','ratio','ordinary'])
def test_fresh_identity_does_not_accept_relabelled_registration_or_json(tmp_path,change):
    approval,capture,_,_=discovery_capture(tmp_path)
    reader=SyntheticReader();reader.change=change
    if change=='serialized':reader={'classification':'QUALIFIED_EXACT_SECURITY'}
    with pytest.raises(ValueError):
        owner.issue_source_intake_owner(approval=approval,capture=capture,market='us',
            generation_id='SYNTHETIC_FRESH',policy=POLICY,fresh_identity_reader=reader)
def test_research_append_uses_live_intake_not_synthetic_active(tmp_path):
    from test_c9_intake_bridge import prepared,POLICY
    from app.services.vnext_research_store import ResearchStore
    from app.services import prospective_class_c_owner as grants
    _,_,handle,_,_=prepared(tmp_path)
    store=ResearchStore(tmp_path/'research.sqlite3')
    from datetime import datetime,timezone
    cutoff=datetime.now(timezone.utc).isoformat()
    store.start_run('C10R_TEST',cutoff)
    h=store.capture('C10R_TEST','TEST_ONLY','original',b'{}',dict(captured_at=cutoff))
    kw=dict(registration_owner=handle,registration_generation='C8_TEST',registration_policy=POLICY)
    payload=dict(strict_native=False,reason='TEST_ONLY_NO_ECONOMIC_GRANT')
    store.observation('C10R_TEST','NEWUS','financial.revenue','NOT_ATTEMPTED',h,payload,**kw)
    with store.connect() as c:assert c.execute('SELECT COUNT(*) FROM watchlistitem').fetchone()==(0,)
    grants.revoke_source_intake(handle)
    with pytest.raises(ValueError):store.observation('C10R_TEST','NEWUS','financial.revenue','NOT_ATTEMPTED',h,payload,**kw)
    with pytest.raises(ValueError):store.observation('C10R_TEST','NEWUS','financial.revenue','NOT_ATTEMPTED',h,payload)
