from __future__ import annotations

from scripts import production_integration_persistence_review_m12bl as runner


def test_report_contract_preserves_optional_migration_gap() -> None:
    assert len(runner.REPORT_SLUGS) == 67
    assert len(set(runner.REPORT_SLUGS)) == 67
    assert runner.NUMBERS["repository-provenance"] == 1
    assert runner.NUMBERS["local-migration-upgrade-replay"] == 50
    assert 51 not in set(runner.NUMBERS.values())
    assert runner.NUMBERS["production-db-no-mutation-proof"] == 52
    assert runner.NUMBERS["program-completion"] == 68


def test_authoritative_latest_result_inventory_is_intact() -> None:
    result = runner.verify_latest_result()

    assert result["zip_sha256"] == runner.LATEST_RESULT_SHA256
    assert result["indexed_payload_count"] == 45
    assert result["zip_entry_count"] == 46
    assert result["missing_count"] == 0
    assert result["extra_count"] == 0
    assert result["hash_mismatch_count"] == 0
    assert result["size_mismatch_count"] == 0


def test_frozen_m12bj_fixture_identity_and_acceptance_are_preserved() -> None:
    rows = runner.load_m12bj_fixture_manifest()

    assert len(rows) == 22
    assert len({row["ticker"] for row in rows}) == 22
    assert {row["generation_id"] for row in rows} == {runner.M12BJ_GENERATION_ID}
    assert {row["canonical_semantic_status"] for row in rows} == {"PASS"}
    assert {row["final_composition_status"] for row in rows} == {"PASS"}
    assert {row["persistence_eligible"] for row in rows} == {False}
    assert all(len(str(row["packet_sha256"])) == 64 for row in rows)
    assert all(len(str(row["core_sha256"])) == 64 for row in rows)
    assert all(len(str(row["stance_sha256"])) == 64 for row in rows)


def test_persistence_mapping_and_provenance_gaps_are_explicit() -> None:
    provenance = runner.provenance_coverage()
    mapping = runner.assessment_mapping_matrix()

    proof_critical_missing = [
        row
        for row in provenance
        if row["classification"] == "MISSING_AND_PROOF_CRITICAL"
    ]
    lossy = [
        row
        for row in mapping
        if row["classification"] in {"LOSSY", "MISSING", "INVALID_ENUM_MAPPING"}
    ]

    assert len(provenance) == 14
    assert len(proof_critical_missing) == 10
    assert len(mapping) == 15
    assert len(lossy) == 12
    assert any(
        row["concept"] == "business_thesis_change"
        and row["classification"] == "INVALID_ENUM_MAPPING"
        for row in mapping
    )


def test_ephemeral_harness_exposes_fail_open_and_stale_paths() -> None:
    result = runner.run_ephemeral_harness()

    assert result["production_database_used"] is False
    assert result["production_notification_queue_writes"] == 0
    assert result["production_sends"] == 0
    assert result["missing_semantic_receipt_persisted"] is True
    assert result["failed_semantic_receipt_candidate_persisted"] is False
    assert result["failed_semantic_receipt_fields_ignored"] == []
    assert result["failed_semantic_receipt_fields_rejected"] is True
    assert result["ordinary_manual_old_row_persisted"] is True
    assert result["duplicate_same_date_idempotent_row_count"] is True
    assert result["stale_watchlist_overwrite_observed"] is True
    assert result["accepted_v2_state"]["stale_overwrite_observed"] is True
    assert result["warning_id_stable"] is True
    assert result["same_date_warning_replay_idempotent"] is False
    assert result["first_warning_status"] == "open"
    assert result["same_date_repeat_warning_status"] == "escalated"
    assert result["notification_duplicate_suppressed"] is True
    assert result["stale_notification_row_possible"] is True
    assert result["transaction_rollback_effective"] is True


def test_ephemeral_harness_keeps_ticker_and_date_edges_visible() -> None:
    result = runner.run_ephemeral_harness()

    assert result["ticker_normalization"]["000660"] == "000660"
    assert result["ticker_normalization"]["660"] == "660"
    assert result["ticker_normalization"]["005930"] == "005930"
    assert result["ticker_normalization"]["5930"] == "5930"
    assert result["ticker_normalization"]["ibm"] == "IBM"
    assert result["numeric_ticker_input_rejected"] is True
    assert result["read_path_dates"] == ["2026-09-14", "2026-09-13"]
    assert result["read_path_orders_by_persisted_date"] is True


def test_post_acceptance_scan_has_no_competing_production_semantic_engine() -> None:
    result = runner.semantic_rederivation_scan()

    assert result["proof_critical_post_acceptance_semantic_rederivation_count"] == 0
    assert "absence" in result["important_limit"]


def test_artifact_inventory_excludes_raw_model_material() -> None:
    paths = {str(path) for path in runner.artifact_files()}

    assert not any("model-calls" in path for path in paths)
    assert not any(path.endswith("prompt.txt") for path in paths)
    assert not any(path.endswith("output.raw.json") for path in paths)
    assert not any(path.endswith("transport.log") for path in paths)
