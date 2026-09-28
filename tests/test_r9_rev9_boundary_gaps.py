import pytest

from app.services.fresh_financial_stock_owner import assemble_fresh_stock
from app.services.unified_full_source_cohort import FreshFullSourceRunSeed, compose_full_source
from scripts.r2b_r9_full_fresh_requalification import load_stock_inputs
from tests.test_unified_live_source_cohort import seed
from tests.rev8_source_fixtures import fresh_inputs
from tests.rev9_source_fixtures import write_descriptor


@pytest.mark.parametrize('context,metadata', [(None, None), ({}, None), (None, {})])
def test_fresh_aggregate_requires_current_context_and_code_ownership(context, metadata):
    fresh = FreshFullSourceRunSeed(**seed().model_dump(), fresh_stock_owner_set_sha256='a'*64)
    with pytest.raises(ValueError, match='fresh_complete_context_and_code_inventory_required'):
        compose_full_source(seed=fresh, market_inputs={}, stock_inputs={}, authority_inputs={},
            version_set={}, optional_denials={}, issuer_bridge={},
            fresh_context_inputs=context, composition_metadata=metadata)


def test_unimplemented_event_input_cannot_claim_fresh_parity(tmp_path):
    inputs = fresh_inputs(tmp_path / 'raw', 'CORZ', current_only=True)
    descriptor = write_descriptor(tmp_path, inputs)
    descriptor['event_source'] = {}
    with pytest.raises(ValueError, match='descriptor_shape'):
        load_stock_inputs(tmp_path, descriptor, inputs['technical_inputs']['plan'])
    inputs['technical_inputs']['event_source'] = {}
    with pytest.raises(ValueError, match='fresh_stock_no_parent_mutable_input'):
        assemble_fresh_stock(**inputs)
