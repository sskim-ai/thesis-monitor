from __future__ import annotations

from scripts import business_delta_unchanged_negation_scope_m12as as program


def test_required_report_sequence_is_complete() -> None:
    assert len(program.SLUGS) == 103
    assert program.SLUGS[1] == "repository-provenance"
    assert program.SLUGS[50] == "new-shadow-model-call-gate"
    assert program.SLUGS[103] == "program-completion"


def test_authoritative_m12ar_identity_is_frozen() -> None:
    assert program.M12AR_BUNDLE_SHA256 == (
        "97b94a2cfd2deb7bfcfa74508eba16815d2dff74f287886545a9e3970db09456"
    )
    assert program.M12AR_INDEXED_PAYLOADS == 294
    assert program.M12AR_ZIP_ENTRIES == 295
    assert program.M12AR_GENERATION_ID == ("20260911-m12ai-shadow-20260912T075624Z-ffbc08645051")


def test_fixture_audit_has_zero_false_results() -> None:
    result = program._fixture_audit()
    assert result["status"] == "PASS"
    assert result["fixture_count"] == 15
    assert result["false_reject_count"] == 0
    assert result["false_accept_count"] == 0


def test_model_facing_semantic_hashes_are_unchanged() -> None:
    result = program._semantic_hash_audit()
    unchanged = {"prompt", "schema", "evidence_projection", "two_stage"}
    assert all(result[key]["status"] == "PASS" for key in unchanged)
    assert all(result[key]["semantic_change_count"] == 0 for key in unchanged)

    # M12AT intentionally composes configured-signal ownership into these two views.
    assert result["business_delta_view"]["semantic_change_count"] == 1
    assert result["expectation_view"]["semantic_change_count"] == 1
    assert [row["path"] for row in result["expectation_view"]["rows"]] == [
        "app/services/market_expectation_evidence_service.py"
    ]


def test_shadow_topology_is_one_attempt_without_reruns() -> None:
    assert program.MODEL == "gpt-5.6-sol"
    assert program.EFFORT == "xhigh"
    assert program.TIMEOUT_SECONDS == 1800
    assert program.EXPECTED_CONTEXT_COUNT == 6
    assert program.EXPECTED_SHADOW_CALLS == 18
