from __future__ import annotations

import json

from scripts.phase9_1c_shadow_consumption import generate


def _payload() -> dict[str, object]:
    return generate()


def test_phase9_1c_generation_is_deterministic() -> None:
    first = _payload()
    second = _payload()

    assert json.dumps(first, sort_keys=True) == json.dumps(second, sort_keys=True)


def test_phase9_1c_selects_only_current_formal_material_relations() -> None:
    payload = _payload()
    selected = [
        row for row in payload["subjects"] if row["context"]["shadow_used"]
    ]

    assert payload["active_universe_count"] == 20
    assert len(selected) == 7
    assert payload["usage_counts"] == {
        "INVENTORY_RELATION": 5,
        "TRADE_AR_RELATION": 2,
    }
    assert all(
        row["context"]["freshness_state"] == "CURRENT_FORMAL"
        for row in selected
    )
    assert all(len(row["context"]["selected_relations"]) == 1 for row in selected)


def test_phase9_1c_preserves_semantics_and_lineage() -> None:
    payload = _payload()
    for row in payload["subjects"]:
        selected = row["context"]["selected_relations"]
        if not row["context"]["shadow_used"]:
            continue
        relation = selected[0]
        assert len(relation["input_fact_ids"]) == 6
        assert relation["balance_metric"] in {
            "inventory",
            "trade_accounts_receivable",
        }
        assert "accounts_receivable_broad" != relation["balance_metric"]
        assert "accounts_payable_broad" != relation["balance_metric"]
        assert row["validation_errors"] == []


def test_phase9_1c_tsm_lagging_and_insurance_negative_controls() -> None:
    payload = _payload()
    by_ticker = {row["ticker"]: row for row in payload["subjects"]}

    assert (
        by_ticker["TSM"]["context"]["freshness_state"]
        == "FORMAL_LAGGING_PROVISIONAL"
    )
    assert by_ticker["TSM"]["context"]["shadow_used"] is False
    assert by_ticker["003690"]["context"]["usage_mode"] == "NOT_APPLICABLE"
    assert by_ticker["003690"]["reasoning"] is None


def test_phase9_1c_numeric_binding_quality_and_unknowns_pass() -> None:
    payload = _payload()

    assert payload["numeric_binding"] == {
        "automatic": 7,
        "manual": 0,
        "rejected": 0,
        "unresolved": 0,
        "relation_arithmetic_errors": 0,
    }
    assert payload["quality_receipt"]["status"] == "PASS"
    assert payload["unknown_resolution"]["contradictions"] == 0
    assert payload["human_quality"].get("DEGRADED", 0) == 0
    assert payload["readiness"]["phase_9_1d_ready"] is True


def test_phase9_1c_does_not_mutate_user_visible_contracts() -> None:
    payload = _payload()

    assert set(payload["mutations"].values()) == {0}
    assert payload["readiness"]["runtime_user_visible_diff"] == 0
    assert payload["readiness"]["working_capital_user_visible"] == "NOT_ENABLED"
    assert (
        payload["readiness"]["phase_9_0e_mode"]
        == "SELECTIVE_CURRENT_FORMAL_FULL_FCF"
    )
    assert set(payload["readiness"]["advanced_ratios"].values()) == {"DEFER"}
