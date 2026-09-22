from pathlib import Path

import pytest

from scripts.m12dc_r3_worker_boundary_offline import (
    native_prefix,
    read_outcome,
    request_artifacts,
    worker_plan,
)


@pytest.mark.parametrize(
    "code,stdout,stderr,expected",
    [
        (0, b"canary", b"", "EXACT_BYTES_RETURNED"),
        (1, b"", b"cat: Permission denied", "OS_PERMISSION_DENIED"),
        (1, b"", b"cat: Operation not permitted", "OS_PERMISSION_DENIED"),
        (1, b"", b"No such file or directory", "INCONCLUSIVE_PROCESS_OR_READ_FAILURE"),
        (134, b"", b"Operation not permitted", "INCONCLUSIVE_PROCESS_OR_READ_FAILURE"),
        (None, b"", b"timeout", "INCONCLUSIVE_PROCESS_OR_READ_FAILURE"),
        (1, b"canary", b"Permission denied", "INCONCLUSIVE_PROCESS_OR_READ_FAILURE"),
        (0, b"wrong", b"", "INCONCLUSIVE_PROCESS_OR_READ_FAILURE"),
    ],
)
def test_denial_not_inferred_from_missing_or_abort(code, stdout, stderr, expected):
    assert read_outcome(code, stdout, stderr, b"canary") == expected


def layout(tmp_path):
    paths = [tmp_path / name for name in ("batch", "private", "home", "controller")]
    for path in paths:
        path.mkdir()
    return paths


def test_profile_plan_is_not_an_executable_adapter(tmp_path):
    batch, private, home, controller = layout(tmp_path)
    plan = worker_plan(batch, private, home, [controller])
    assert plan["executable"] is False
    assert plan["launch_denial"]
    assert plan["environment"]["TMPDIR"] == str(private)
    assert "network={enabled=false}" in plan["native_prefix"][5]


def test_cannot_treat_controller_data_under_scratch_as_private(tmp_path):
    batch, private, home, _ = layout(tmp_path)
    old = private / "old.txt"
    old.write_text("synthetic")
    with pytest.raises(ValueError, match="controller_data_inside_worker_root"):
        worker_plan(batch, private, home, [old])


def test_symlink_exclusion_uses_real_target(tmp_path):
    batch, private, home, controller = layout(tmp_path)
    real = private / "old.txt"
    real.write_text("synthetic")
    link = controller / "escape"
    link.symlink_to(real)
    with pytest.raises(ValueError, match="controller_data_inside_worker_root"):
        worker_plan(batch, private, home, [link])


def test_batch_and_tmp_must_be_disjoint(tmp_path):
    batch, _, home, controller = layout(tmp_path)
    with pytest.raises(ValueError, match="disjoint"):
        worker_plan(batch, batch, home, [controller])


def test_native_policy_quotes_paths(tmp_path):
    result = native_prefix("bounded", tmp_path, {str(tmp_path / 'space " quote'): "read"})
    assert result[2:4] == ["-P", "bounded"]
    assert '\\" quote' in result[5]
    assert result[-1] == "--"


def test_synthetic_preparation_contains_no_financial_policy(tmp_path):
    result = request_artifacts(tmp_path)
    assert result["positive_local_schema"] == "PASS"
    assert result["negative_local_schema"] == "REJECTED"
    assert result["financial_definitions_added"] == []
    assert len(result["files"]) == 3
    assert all(len(h) == 64 for h in result["files"].values())


def test_no_production_executable_change():
    import inspect
    from app.jobs.accepted_decision_v2_runtime import _invoke_signed_in_codex

    parameters = inspect.signature(_invoke_signed_in_codex).parameters
    assert "cwd" in parameters
    assert not {"permissions", "tools", "env"}.intersection(parameters)
    assert Path(inspect.getfile(_invoke_signed_in_codex)).name == "accepted_decision_v2_runtime.py"


def test_actual_callsite_capture_never_launches_cli(tmp_path):
    from scripts.m12dc_r3_worker_boundary_offline import capture_existing_invocation

    batch, private, home, controller = layout(tmp_path)
    request = request_artifacts(batch)
    plan = worker_plan(batch, private, home, [controller])
    result = capture_existing_invocation(
        Path(__file__).resolve().parents[1], controller, batch, plan["environment"]
    )
    assert result["native_exec_launched"] is False
    assert result["actual_isolated_invoke_path_bound"] is False
    assert result["environment_injected_at_stub_only"] is True
    capture = result["captured"]
    assert capture["stdin_sha256"] == request["files"]["prompt.txt"]
    assert capture["schema_sha256"] == request["files"]["provider-wire-schema.json"]
    assert capture["argv"][capture["argv"].index("--sandbox") + 1] == "read-only"
    assert not (controller / "never-output.json").exists()


def test_all_frozen_owner_paths_exist():
    from scripts.m12dc_r3_worker_boundary_offline import OWNER_PATHS

    root = Path(__file__).resolve().parents[1]
    assert all((root / name).is_file() for name in OWNER_PATHS)
