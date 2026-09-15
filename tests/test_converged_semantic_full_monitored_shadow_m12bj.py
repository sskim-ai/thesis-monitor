from __future__ import annotations

from scripts import converged_semantic_full_monitored_shadow_m12bj as runner


def test_m12bj_report_contract_is_complete_and_unique() -> None:
    assert len(runner.REPORT_SLUGS) == 82
    assert len(set(runner.REPORT_SLUGS)) == 82
    assert runner.NUMBERS["repository-provenance"] == 1
    assert runner.NUMBERS["program-completion"] == 82


def test_m12bj_model_and_fictional_reuse_are_frozen() -> None:
    assert runner.MODEL == "gpt-5.6-sol"
    assert runner.EFFORT == "xhigh"
    assert runner.M12BD_GENERATION_ID == (
        "20260911-m12ai-fictional-20260913T113957Z-07ac29f97bc6"
    )
    assert runner.SEMANTIC_ORCHESTRATOR_CONTRACT == (
        "directional-core-semantic-audit-v1"
    )


def test_m12bj_active_universe_count_is_not_hard_coded() -> None:
    assert runner._unique_tickers(("A", "B"), subject="fixture") == ("A", "B")


def test_m12bj_raw_artifacts_are_outside_repository_package_inventory() -> None:
    paths = {str(path) for path in runner.artifact_files()}

    assert str(runner.LOCAL_RAW_ROOT) not in paths
    assert not any("model-calls" in path for path in paths)
    assert not any(path.endswith("prompt.txt") for path in paths)
    assert not any(path.endswith("output.raw.json") for path in paths)


def test_m12bj_topology_uses_four_subject_contexts() -> None:
    assert len(runner.m12bg.capability._batches(tuple("ABCDEFGH"))) == 2
    assert len(runner.m12bg.capability._batches(tuple("ABCDEFGHIJKLMNOPQRSTUV"))) == 6


def test_m12bj_disabled_runtime_flags_accept_json_zero_and_boolean_false() -> None:
    assert runner._disabled_flag(0)
    assert runner._disabled_flag(False)
    assert not runner._disabled_flag(1)
    assert not runner._disabled_flag(True)
    assert not runner._disabled_flag(None)


def test_m12bj_frozen_hash_check_uses_the_manifest_paths(tmp_path) -> None:
    path = tmp_path / "frozen.txt"
    path.write_text("frozen")
    state = {"code_hashes": {str(path): runner.file_sha256(path)}}

    assert runner._frozen_code_hashes_match(state)
    path.write_text("changed")
    assert not runner._frozen_code_hashes_match(state)


def test_m12bj_only_known_legacy_duplicate_exit_is_diagnostic() -> None:
    assert runner._legacy_finalization_exit_is_diagnostic(
        SystemExit("M12AZ_SHADOW_HARD_ACCEPTANCE_FAILURE")
    )
    assert not runner._legacy_finalization_exit_is_diagnostic(
        SystemExit("M12BJ_SHADOW_HARD_ACCEPTANCE_FAILURE")
    )
