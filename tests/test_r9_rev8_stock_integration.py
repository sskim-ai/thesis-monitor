import pytest

from app.services.fresh_financial_stock_owner import assemble_fresh_stock
from app.services.unified_stock_acquisition import UNIVERSE
from tests.rev8_source_fixtures import fresh_inputs


@pytest.mark.parametrize('ticker', [t for subjects in UNIVERSE.values() for t in subjects])
def test_all22_direct_source_owner_integration(tmp_path, ticker):
    inputs = fresh_inputs(tmp_path, ticker)
    first = assemble_fresh_stock(**inputs)
    assert first == assemble_fresh_stock(**inputs)
    assert first['status'] == 'PASS', first['mandatory_missing']
    assert first['valuation_view']['ticker'] == ticker
    assert first['fresh_run_id'] == inputs['technical_inputs']['plan'].run_id
    assert first['quality_view']['receipt']['directional_use_allowed'] is False
    assert first['complete_source_adapter_qualified'] is False


@pytest.mark.parametrize('ticker', [t for subjects in UNIVERSE.values() for t in subjects])
def test_fresh_stock_reaches_existing_core_a_b_preflight(tmp_path, ticker):
    from scripts.r2b_r9_full_fresh_requalification import prepare_fresh_subject
    result = prepare_fresh_subject(fresh_inputs(tmp_path, ticker), execution_generation_id='synthetic-model-input-only')
    assert result['readiness']['status'] == 'PASS', result['readiness']
    assert all(result['readiness'][stage] == 'PASS' for stage in ('Core', 'A', 'B'))
    assert result['readiness']['offline_availability_probes_only'] is True


def test_current_only_source_reaches_unknown_limit_without_fake_quality(tmp_path):
    from scripts.r2b_r9_full_fresh_requalification import prepare_fresh_subject
    inputs = fresh_inputs(tmp_path, 'CORZ', current_only=True)
    result = prepare_fresh_subject(inputs, execution_generation_id='synthetic-no-dispatch')
    assert result['readiness']['status'] == 'PASS'
    assert result['prepared']['mode'] == 'UNKNOWN_LIMIT'
    assert result['stock']['quality_view']['fact'] is None
