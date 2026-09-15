from __future__ import annotations

from scripts import financial_context_output_grounding_m12a as m12a


def test_option_a_projects_selected_typed_refs_into_one_evidence_index() -> None:
    state = m12a._fictional_state()

    prototype = m12a.option_a_prototype(state, "FIC-FIN-06")

    rows = prototype["prototype_representation"]["evidence"]
    typed = [row for row in rows if row["evidence_kind"] == "TYPED_FINANCIAL"]
    aliases = [row["alias"] for row in rows]
    assert prototype["selected_typed_count"] == 2
    assert prototype["first_class_typed_count"] == 2
    assert prototype["duplicate_alias_count"] == 0
    assert set(aliases) == {entry.alias for entry in state.catalogs["FIC-FIN-06"].entries}
    assert {row["label"] for row in typed} == {
        "inventory",
        "trade_accounts_receivable",
    }
    assert all(not row["statement"].startswith("{") for row in typed)
    assert prototype["output_schema_change_required"] is False


def test_option_a_neutral_statements_preserve_period_and_comparison() -> None:
    state = m12a._fictional_state()
    prototype = m12a.option_a_prototype(state, "FIC-FIN-06")

    statements = {
        row["label"]: row["statement"]
        for row in prototype["prototype_representation"]["evidence"]
        if row["evidence_kind"] == "TYPED_FINANCIAL"
    }

    assert statements["inventory"] == (
        "inventory is higher than the prior year-end balance."
    )
    assert statements["trade_accounts_receivable"] == (
        "trade accounts receivable is higher than the prior year-end balance."
    )
    assert not any(
        verdict in " ".join(statements.values()).lower()
        for verdict in ("bullish", "bearish", "dangerous", "deterioration")
    )


def test_option_a_does_not_project_unselected_raw_financial_facts() -> None:
    state = m12a._fictional_state()
    ticker = "FIC-FIN-02"
    prototype = m12a.option_a_prototype(state, ticker)
    selected = {
        item.evidence_id for item in m12a._selected_items(state.owned[ticker])
    }
    typed_canonical = {
        prototype["lineage_map"][row["alias"]]["canonical_ref"]
        for row in prototype["prototype_representation"]["evidence"]
        if row["evidence_kind"] == "TYPED_FINANCIAL"
    }

    assert typed_canonical == selected
    assert prototype["unselected_typed_projection_count"] == 0


def test_option_b_does_not_invent_lineage_from_matching_words() -> None:
    state = m12a._fictional_state()

    prototype = m12a.option_b_prototype(state, "FIC-FIN-06")

    assert prototype["audit_only_text_topic_matches_not_lineage"]
    assert prototype["lineage_map"] == {}
    assert prototype["valid_narrative_lineage_count"] == 0
    assert all(
        row["backing_financial_refs"] == []
        for row in prototype["prototype_representation"]["evidence"]
    )
    assert prototype["status"] == "BLOCKING"


def test_option_c_is_explicit_schema_cost_not_retroactive_success() -> None:
    state = m12a._fictional_state()

    prototype = m12a.option_c_prototype(state, "FIC-FIN-06")
    replay = m12a._old_fic06_replay(state)

    schema = prototype["prototype_representation"]["candidate_schema_fragment"]
    assert "material_financial_evidence_refs" in schema
    assert prototype["output_schema_change_required"] is True
    assert replay["option_c"]["result"] == "LEGACY_NOT_APPLICABLE"


def test_old_fic_fin_06_remains_failed_under_input_architectures() -> None:
    replay = m12a._old_fic06_replay(m12a._fictional_state())

    assert replay["option_a"]["result"] == "FAIL"
    assert replay["option_b"]["result"] == "FAIL"
    assert replay["historically_cited_typed_refs"] == []
    assert replay["historical_failure_preserved"] is True


def test_corrected_fixture_is_representable_without_becoming_model_result() -> None:
    comparison = m12a._corrected_comparison(m12a._fictional_state())

    assert comparison["fixture_is_model_result"] is False
    assert comparison["options"]["A"]["result"] == "PASS"
    assert comparison["options"]["B"]["result"] == "PASS"
    assert comparison["options"]["C"]["result"] == "PASS_REPRESENTABLE"
    assert len(comparison["used_typed_refs"]) == 2


def test_preserved_history_exposes_repeated_split_surface_risk() -> None:
    history = m12a._history_audit(m12a._fictional_state())

    assert history["aggregate_completed_subject_count"] == 20
    assert history["aggregate_selected_typed_financial_ref_count"] == 41
    assert history["aggregate_typed_financial_ref_used_count"] == 33
    assert history["aggregate_narrative_substitution_failure_count"] == 2
    assert history["finding"] == (
        "SPLIT_SURFACE_RISK_RECURRED_IN_M12R_AND_M12G_FIC_FIN_06"
    )


def test_duplicate_audit_never_upgrades_similarity_to_lineage() -> None:
    audit = m12a._duplicate_audit(m12a._fictional_state())

    assert audit["selected_typed_financial_count"] == 15
    assert audit["narrative_duplicate_selected_item_count"] == 8
    assert audit["unique_narrative_duplicate_ref_count"] == 4
    assert audit["valid_lineage_count"] == 0
    assert audit["method"]["topic_matching_may_create_lineage"] is False
    assert all(row["valid_lineage_refs"] == [] for row in audit["rows"])


def test_current_flow_places_split_at_model_input_projection() -> None:
    flow = m12a._current_flow()

    assert flow["split_created_at"] == (
        "scripts/directional_core_price_timing_holdout.py::_owned_context"
    )
    assert flow["status"] == "PASS"
    alias_step = next(row for row in flow["steps"] if row["step"] == "stage alias catalog")
    assert alias_step["one_alias_namespace"] is True
    assert alias_step["validator_can_resolve"] is True
