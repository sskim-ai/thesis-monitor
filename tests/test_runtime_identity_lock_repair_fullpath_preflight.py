from __future__ import annotations

from pathlib import Path

from scripts import runtime_identity_lock_repair_fullpath_preflight as proof


def test_model_free_rehearsal_exercises_fresh_and_resume_full_path(
    tmp_path: Path,
) -> None:
    result = proof.model_free_rehearsal(tmp_path / "model-free")

    assert result["status"] == "PASS"
    assert result["whole_path_model_free_rehearsal_status"] == "PASS"
    assert result["simulated_invocation_count"] == 64
    assert result["model_free_real_model_call_count"] == 0
    assert result["fresh"]["runtime_generation_id"] != result["resumed"][
        "runtime_generation_id"
    ]
    for suite in (result["fresh"], result["resumed"]):
        assert suite["status"] == "PASS"
        assert suite["actual_request_preflight_count"] == 32
        assert suite["actual_request_preflight_failures"] == 0
        assert suite["receipt_identity_failure_count"] == 0
        assert suite["output_identity_failure_count"] == 0
        assert suite["renderer_context_count"] == 16
