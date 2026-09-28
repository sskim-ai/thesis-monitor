from datetime import timedelta

import pytest

from scripts.r2b_r9_full_fresh_requalification import prepare_fresh_subject
from scripts.r9_offline_stage_replay import replay_stages
from tests.rev8_source_fixtures import fresh_inputs
from tests.rev10_source_fixtures import wire_clock
from tests.rev10_stage_fixtures import synthetic_outputs
from tests.test_unified_stock_acquisition import plan as plan_fixture


@pytest.mark.parametrize('ticker,options', [
    ('CORZ', {}), ('TSM', {}), ('005930', {}), ('003690', {'insurance': True}),
    ('CORZ', {'conflict': True}), ('005930', {'denied_quality': True}),
])
def test_normal_archetype_actual_stages_and_sender(tmp_path, ticker, options):
    start = plan_fixture.__wrapped__().frozen_at
    with wire_clock(start + timedelta(seconds=4)):
        inputs = fresh_inputs(tmp_path, ticker, **options)
    result = prepare_fresh_subject(inputs, execution_generation_id='synthetic-rev10')
    if options.get('denied_quality'):
        assert result['stock']['quality_view']['receipt']['state'] == 'denied'
    raw = synthetic_outputs(result, 'synthetic-rev10', inputs['technical_inputs']['local_seed'])
    proof = replay_stages(result, 'synthetic-rev10', raw)
    assert proof['status'] == 'PASS'
    assert proof['capture']['production_sends'] == proof['capture']['network_requests'] == 0
    assert proof['capture']['prepared_text_sha256']
