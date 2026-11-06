"""New live components do not bypass the original full-Parent boundary."""
import pytest
from app.services.market_component_handoff import required_original_parents,_project_complete,project_original_parent
from app.services.production_source_binding import ProductionSourceRunBinding

@pytest.mark.parametrize('market',['kr','us'])
def test_missing_full_parent_inputs_remain_typed_denial(market):
    result=required_original_parents(None,None,None,market)
    assert result.MarketParent=='NOT_ISSUED'
    assert result.missing==('packet','binding','authority_graph')

@pytest.mark.parametrize('market',['kr','us'])
def test_component_json_cannot_substitute_for_required_parent_graph(market):
    result=_project_complete(packet={'market':market},binding={'market':market},graph={'markets':{}},
        market=market,component_sha256='0'*64,value_sha256='1'*64,
        generation_id='SYNTHETIC',expected_authority_sha256='2'*64)
    assert result.MarketParent=='NOT_ISSUED'
    assert 'binding.parent_run_id' in result.missing
    assert 'graph.class_c' in result.missing
    if market=='us':assert 'original_KRX_night_availability_and_receipts' in result.missing

def test_serialized_component_does_not_restore_handoff():
    with pytest.raises(ValueError,match='unissued_component'):
        project_original_parent({},packet={},binding={},graph={},expected_authority_sha256='0'*64)

def test_pending_research_purpose_is_not_a_production_binding():
    with pytest.raises(ValueError) as caught:
        ProductionSourceRunBinding.model_validate({'execution_purpose':'PENDING_MARKET_COMPONENT_SOURCE_ONLY'})
    assert any(e['loc']==('execution_purpose',) and e['type']=='literal_error' for e in caught.value.errors())
