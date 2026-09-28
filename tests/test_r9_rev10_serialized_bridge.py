import json

from app.services.bounded_financial_stock_owner import assemble
from app.services.fresh_financial_stock_owner import fresh_stock_baseline
from app.services.unified_snapshot_contract import digest, encoded
from tests.rev8_source_fixtures import fresh_inputs


def test_fresh_bridge_source_owner_hash_survives_sorted_json(tmp_path):
    source = fresh_inputs(tmp_path, '000660')
    baseline = fresh_stock_baseline(source['technical_inputs'])
    inputs = dict(local_seed=source['technical_inputs']['local_seed'], **source['financial_inputs'])
    before = assemble(baseline=baseline, **inputs)
    after = assemble(baseline=json.loads(encoded(baseline)), **inputs)
    assert before['status'] == after['status'] == 'PASS'
    assert digest(before) == digest(after)
    assert before == after
