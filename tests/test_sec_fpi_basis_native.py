"""Synthetic full original producer/consumer route, not real issuer admission."""
import asyncio
from datetime import timedelta

import httpx
import pytest

from app.services.bounded_financial_acquisition import make_plan,BoundedReader,collect
from app.services.fresh_financial_stock_owner import assemble_fresh_stock
from app.services.cross_market_decision_engine_service import build_decision_evidence_packet
from app.services.direction_timing_ownership_service import build_owned_evidence_packet
from app.services.sec_fpi_statement_basis_owner import POLICY
from tests.rev8_source_fixtures import fresh_inputs
from tests.rev10_source_fixtures import wire_clock
from tests.test_unified_stock_acquisition import plan as plan_fixture
from test_reported_business_native_projection import window
from test_sec_foreign_statement_scope import statement
from test_bounded_financial_acquisition import filing,submission


@pytest.fixture
def source(tmp_path):
    plan=plan_fixture.__wrapped__()
    with wire_clock(plan.frozen_at+timedelta(seconds=4)):
        inputs=fresh_inputs(tmp_path/'base','TSM',verified_identity=True,financial_scale=1_000_000,plan=plan)
    security=inputs['financial_inputs']['plan']['security']
    fp=make_plan(security,market='us',cutoff=plan.frozen_at,run_id=plan.run_id,
        all_subjects_fresh=True,exact_financial_owner=True)
    f={**filing('6-K'),'accessionNumber':'0000001234-26-000001'}
    def respond(request):
        if '/submissions/' in str(request.url):return httpx.Response(200,json={**submission([f]),'cik':1234})
        if '/companyfacts/' in str(request.url):return httpx.Response(200,json={'cik':1234})
        if str(request.url).endswith('index.json'):return httpx.Response(200,json={'directory':{'item':[]}})
        return httpx.Response(200,text=statement('Consolidated',extra='<tr><td>Operating income</td><td>30</td><td>20</td></tr>')+
            statement('Separate','999','888',extra='<tr><td>Operating income</td><td>300</td><td>200</td></tr>'))
    reader=BoundedReader(fp,tmp_path/'financial',transport=httpx.MockTransport(respond))
    with wire_clock(plan.frozen_at+timedelta(seconds=5)):acq=asyncio.run(collect(reader))
    inputs['financial_inputs']=dict(plan=fp,acquisition=acq,directory=tmp_path/'financial',receipts=reader.receipts,
        field_semantics=True,statement_basis_policy=POLICY,basis_execution_generation=plan.run_id)
    return {**inputs,'reported_comparison_business':True,'source_window':window(plan)}


def test_actual_fresh_owner_and_native_consumer_with_basis(source,record_property):
    result=assemble_fresh_stock(**source)
    assert result['status']=='PASS'
    stock=result['packet']['stocks'][0]
    evidence=build_decision_evidence_packet(packet=result['packet'],stock=stock)
    owned=build_owned_evidence_packet(evidence,stock=stock)
    assert len(result['comparative_fact_refs'])==2 and set(result['comparative_fact_refs'])<=owned.core_refs
    projection=result['projection']
    assert projection['statement_basis_owner']['documents'][0]['selected_basis']=='consolidated'
    assert result['selected_financial_owner']['selected_projection_sha256']
    record_property('ng40_consumer',dict(scope='SYNTHETIC_OFFLINE_ONLY',status='PASS',
        comparative_refs=result['comparative_fact_refs'],owner=result['selected_financial_owner'],
        policy=projection['statement_basis_owner']['policy'],model_calls=0,real_READY=0))


@pytest.mark.parametrize('change',['execution','policy','raw','double_owner'])
def test_original_native_boundary_rejects_invalid_basis_inputs(source,change):
    fin=source['financial_inputs']
    if change=='execution':fin['basis_execution_generation']='old-policy-generation'
    elif change=='policy':fin['statement_basis_policy']='caller-policy'
    elif change=='raw':
        r=next(r for r in fin['receipts'] if r.get('artifact') and r['stage']=='document')
        p=fin['directory']/r['artifact'];p.write_bytes(p.read_bytes()+b' ')
    else:fin['issuer_business']={'unissued':True}
    with pytest.raises(ValueError):assemble_fresh_stock(**source)
