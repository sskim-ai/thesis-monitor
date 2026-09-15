from scripts import fictional_case_fcf_prospective_scope_m12au as runner


def test_report_sequence_matches_work_instruction() -> None:
    assert len(runner.SLUGS) == 134
    assert runner.SLUGS[10] == "fic-fin-01-case-check-architecture-decision"
    assert runner.SLUGS[43] == "new-fictional-model-call-gate"
    assert runner.SLUGS[76] == "fictional-shadow-gate-decision"
    assert runner.SLUGS[85] == "shadow-model-call-gate"
    assert runner.SLUGS[134] == "program-completion"


def test_runtime_contract_is_frozen() -> None:
    assert runner.MODEL == "gpt-5.6-sol"
    assert runner.EFFORT == "xhigh"
    assert runner.TIMEOUT_SECONDS == 1800
    assert runner.EXPECTED_FICTIONAL_CALLS == 12
    assert runner.EXPECTED_FICTIONAL_ROWS == 24
    assert runner.EXPECTED_SHADOW_CALLS == 18
    assert runner.EXPECTED_ACTIVE_COUNT == 22


def test_model_facing_semantic_surfaces_are_unchanged() -> None:
    audit = runner._semantic_surface_hashes()
    assert audit["status"] == "PASS"
    assert audit["decision"] == "NO_MODEL_FACING_SEMANTIC_CHANGE"
    assert audit["total_semantic_change_count"] == 0
