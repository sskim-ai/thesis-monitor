from copy import deepcopy
from pathlib import Path

import pytest

from scripts import r2b_r4_preflight as gate


def receipt_bytes():
    return (Path(__file__).resolve().parents[1] / 'docs/work-instructions/20260928-r2b-r4'
            / 'thesis-monitor-20260928-INDEPENDENT_FREEZE_RECEIPT_V2.json').read_bytes()


def test_exact_neutral_receipt_is_only_an_attestation_not_verdict_read():
    result = gate.verify_receipt(receipt_bytes())
    assert result['status'] == 'PASS_V2'
    assert not result['independent_content_read']
    assert result['assessment_content_hashes_not_independently_read']


def test_changed_neutral_receipt_fails_closed():
    with pytest.raises(ValueError, match='neutral_v2_receipt_hash_mismatch'):
        gate.verify_receipt(receipt_bytes() + b' ')


@pytest.mark.parametrize('market', ['us', 'kr'])
def test_unified_component_is_not_an_implicitly_qualified_market_context(market):
    packet = dict(market=market, market_sources={'component': {'value': {}}}, stocks={})
    before = deepcopy(packet)
    result = gate.market_preflight(packet)
    assert result['status'] == 'BLOCKED'
    assert result['missing_input_field'] == 'market_context'
    assert not result['synthesized_market_context']
    assert packet == before
