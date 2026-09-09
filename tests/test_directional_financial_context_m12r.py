from __future__ import annotations

from scripts import directional_financial_context_m12 as m12
from scripts import directional_financial_context_m12r as m12r


def test_m12r_scope_reuses_frozen_m12_runtime_and_topology() -> None:
    assert m12.MODEL == "gpt-5.6-sol"
    assert m12.EFFORT == "xhigh"
    assert m12.TIMEOUT_SECONDS == 1800
    assert m12.SUBJECTS_PER_CONTEXT == 4
    assert m12.CONTEXT_COUNT == 2
    assert m12.REPETITION_COUNT == 3
    assert m12.EXPECTED_MODEL_CALLS == 6


def test_m12r_positive_and_negative_period_fixtures_are_closed() -> None:
    positive = m12r._positive_fixture_report()
    negative = m12r._negative_fixture_report()

    assert positive["fixture_count"] == 6
    assert positive["pass_count"] == 6
    assert positive["status"] == "PASS"
    assert negative["fixture_count"] >= 7
    assert negative["rejected_count"] == negative["fixture_count"]
    assert negative["status"] == "PASS"


def test_generation_normalization_changes_identity_only() -> None:
    left = {
        "generation_id": "old-generation",
        "nested": ["prefix:old-generation", {"value": 3}],
    }
    right = {
        "generation_id": "new-generation",
        "nested": ["prefix:new-generation", {"value": 3}],
    }

    assert m12r._normalized_json_sha(
        left, "old-generation"
    ) == m12r._normalized_json_sha(right, "new-generation")
