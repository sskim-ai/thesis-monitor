import pytest

from scripts.r9_phase_a_gate import root_gate, code_fingerprints, GATES


def test_absent_proof_cannot_qualify_dispatch():
    receipt, artifacts = root_gate()
    assert receipt['dispatch_allowed'] is False
    assert receipt['status'] == 'R2B_R9_REV10_PREFLIGHT_CONTRACT_GAP'
    assert set(receipt['blockers']) == set(GATES)
    assert artifacts == {}


@pytest.mark.parametrize('proof,error', [
    ({'status': 'PASS'}, 'exact_replay_inputs'),
    ({'whole_source_inputs': {}, 'stock_outputs': {}, 'market_outputs': {}, 'code_fingerprints': {}}, 'code_policy_schema_drift'),
])
def test_status_and_stale_hash_cannot_qualify_dispatch(proof, error):
    with pytest.raises(ValueError, match=error):
        root_gate(proof)


def test_fingerprints_cover_transitive_policy_schema():
    fingerprints = code_fingerprints()
    assert 'scripts/r2b_r2_contract.py' in fingerprints
    assert 'app/services/fresh_event_carrier.py' in fingerprints
    assert 'app/services/fresh_valuation_capability.py' in fingerprints
