from __future__ import annotations

from scripts import canonical_acceptance_persistence_design_m12bm as design


def test_required_report_inventory_is_exact() -> None:
    assert len(design.REPORT_SLUGS) == 74
    assert len(set(design.REPORT_SLUGS)) == 74
    assert design.NUMBERS["repository-provenance"] == 1
    assert design.NUMBERS["canonical-acceptance-receipt-v1-spec"] == 9
    assert design.NUMBERS["program-completion"] == 74


def test_latest_m12bl_bundle_integrity_is_independently_reproducible() -> None:
    result = design.verify_latest_result()

    assert result["zip_sha256"] == design.LATEST_RESULT_SHA256
    assert result["indexed_payload_count"] == 83
    assert result["zip_entry_count"] == 84
    assert result["missing_count"] == 0
    assert result["extra_count"] == 0
    assert result["hash_mismatch_count"] == 0
    assert result["size_mismatch_count"] == 0
    assert result["crc_failure"] is None
    assert result["secret_scan_failure_count"] == 0


def test_receipt_has_exactly_twenty_five_fields_and_one_trusted_issuer() -> None:
    receipt = design.build_example_receipt()

    assert tuple(receipt) == design.RECEIPT_FIELDS
    assert len(receipt) == 25
    assert len(design.TRUSTED_ISSUERS) == 1
    assert design.verify_receipt(receipt) == ()


def test_acceptance_identity_is_stable_but_envelope_time_remains_auditable() -> None:
    first = design.build_example_receipt(accepted_at="2026-09-14T08:00:00+00:00")
    replay = design.build_example_receipt(accepted_at="2026-09-14T08:05:00+00:00")

    assert first["acceptance_id"] == replay["acceptance_id"]
    assert first["receipt_hash"] != replay["receipt_hash"]
    assert design.verify_receipt(first) == ()
    assert design.verify_receipt(replay) == ()


def test_receipt_tampering_is_detected_without_semantic_rerun() -> None:
    receipt = design.build_example_receipt()
    receipt["final_composed_candidate_hash"] = "e" * 64

    errors = design.verify_receipt(receipt)

    assert "acceptance_id_mismatch" in errors
    assert "receipt_hash_mismatch" in errors


def test_receipt_rejects_untrusted_issuer_and_naive_timestamp() -> None:
    receipt = design.build_example_receipt()
    receipt["trusted_issuer_id"] = "external_request"
    receipt["effective_at"] = "2026-09-07T12:00:00"
    receipt["acceptance_id"] = design.expected_acceptance_id(receipt)
    receipt["receipt_hash"] = design.expected_receipt_hash(receipt)

    errors = design.verify_receipt(receipt)

    assert "untrusted_receipt_issuer" in errors
    assert "timezone_aware_timestamp_required:effective_at" in errors


def test_total_order_is_timezone_safe_and_not_acceptance_time_ordered() -> None:
    older = design.build_example_receipt(accepted_at="2026-09-14T09:00:00+00:00")
    newer = design.build_example_receipt(accepted_at="2026-09-14T07:00:00+00:00")
    newer["generation_generated_at"] = "2026-09-14T03:47:39+00:00"
    newer["generation_id"] = "20260914-newer-generation"
    newer["acceptance_id"] = design.expected_acceptance_id(newer)
    newer["receipt_hash"] = design.expected_receipt_hash(newer)

    assert design.ordering_key(newer) > design.ordering_key(older)
    assert newer["accepted_at"] < older["accepted_at"]


def test_warning_state_machine_is_acceptance_observation_driven() -> None:
    assert design.warning_transition(None, "CONFIRMED") == ("open", True)
    assert design.warning_transition("open", "CONFIRMED") == ("open", False)
    assert design.warning_transition("open", "WORSENED") == ("escalated", True)
    assert design.warning_transition("escalated", "RECOVERED") == ("resolved", True)
    assert design.warning_transition("resolved", "WORSENED") == ("open", True)
    assert design.warning_transition("open", "UNRESOLVED") == ("open", False)


def test_option_c_and_source_domain_firewall_are_explicit() -> None:
    selected = [row for row in design.schema_options() if row["decision"] == "SELECT"]
    registry = design.source_registry_schema()

    assert [row["option"] for row in selected] == ["C_NEW_IMMUTABLE_ACCEPTED_V2_AND_CURRENT_STATE"]
    assert registry["pre_v2_backfill"] == "LEGACY_UNVERIFIED"
    assert "MANUAL_USER_AUTHORED" in registry["future_manual_write"]


def test_frozen_positive_and_negative_fixture_contracts_are_complete() -> None:
    rows = design.load_m12bj_positive_rows()
    fixtures = design.fixture_specs(rows)

    assert len(rows) == 22
    assert {row["generation_id"] for row in rows} == {design.M12BJ_GENERATION_ID}
    assert fixtures["m12bj_positive"]["future_expected"]["receipt_verify_pass"] == 22
    assert fixtures["historical_negative"]["fixture_count"] == 16
    assert fixtures["historical_negative"]["expected_canonical_rows"] == 0
    assert len(fixtures["transaction_failures"]) == 7
    assert len(fixtures["concurrency"]) == 3


def test_implementation_map_is_bounded_and_semantics_remain_frozen() -> None:
    rows = design.implementation_change_map()

    assert rows
    assert all(row["semantic_behavior_changed"] is False for row in rows)
    assert all(row["model_facing_behavior_changed"] is False for row in rows)
    assert all(row["production_side_effect_path_changed"] is False for row in rows)
    assert any(row["database_schema_changed"] is True for row in rows)


def test_artifact_inventory_excludes_raw_model_material() -> None:
    paths = {str(path) for path in design.artifact_files()}

    assert not any("model-calls" in path for path in paths)
    assert not any(path.endswith("prompt.txt") for path in paths)
    assert not any(path.endswith("output.raw.json") for path in paths)
    assert not any(path.endswith("transport.log") for path in paths)
