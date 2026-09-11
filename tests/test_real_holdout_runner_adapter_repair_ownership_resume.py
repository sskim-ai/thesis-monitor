import inspect
from pathlib import Path

import pytest

from scripts import model_transport_revalidation_ownership_continuation as transport
from scripts import real_holdout_runner_adapter_repair_ownership_resume as resume
from scripts import synthetic_canary_fixture_repair_ownership_resume as previous
from scripts import uskr22_structured_autonomy_shadow as engine


def runner_kwargs(codex_bin: str) -> dict[str, object]:
    return {
        "codex_bin": codex_bin,
        "prompt": Path("prompt.txt"),
        "output": Path("output.json"),
        "log": Path("output.log"),
        "schema": Path("schema.json"),
        "cwd": Path("work"),
        "timeout": 1800,
        "state_namespace": "TEST_NAMESPACE",
    }


def test_canonical_adapter_remains_strict_about_runner_owned_codex_bin() -> None:
    signature = inspect.signature(transport.ContinuationTransportAdapter.invoke)

    with pytest.raises(TypeError, match="codex_bin"):
        signature.bind(object(), **runner_kwargs("/usr/bin/true"))

    assert "codex_bin" not in resume.canonical_adapter_keys()


def test_runner_bridge_consumes_only_verified_codex_binary() -> None:
    spy = resume.BindingSpyAdapter("/usr/bin/true")

    normalized = resume.normalize_real_runner_kwargs(spy, runner_kwargs("/usr/bin/true"))

    assert set(normalized) == set(resume.runner_supplied_keys()) - {"codex_bin"}
    inspect.signature(transport.ContinuationTransportAdapter.invoke).bind(spy, **normalized)


def test_runner_bridge_rejects_codex_binary_identity_mismatch() -> None:
    spy = resume.BindingSpyAdapter("/usr/bin/true")

    with pytest.raises(ValueError, match="runner_adapter_codex_binary_mismatch"):
        resume.normalize_real_runner_kwargs(spy, runner_kwargs("/usr/bin/false"))


def test_runner_bridge_dispatches_canonical_shape_and_restores_engine() -> None:
    spy = resume.BindingSpyAdapter("/usr/bin/true")
    original = engine._invoke_signed_in_codex

    with pytest.raises(resume.BindingPreflightComplete):
        with resume.real_holdout_runner_bridge(spy):
            engine._invoke_signed_in_codex(**runner_kwargs("/usr/bin/true"))

    assert engine._invoke_signed_in_codex is original
    assert len(spy.calls) == 1
    assert set(spy.calls[0]) == set(resume.runner_supplied_keys()) - {"codex_bin"}


def test_model_input_manifest_keeps_prompt_and_schema_namespaces(tmp_path: Path) -> None:
    prompts = tmp_path / "prompts"
    schemas = tmp_path / "schemas"
    prompts.mkdir()
    schemas.mkdir()
    (prompts / "batch-01.txt").write_text("prompt", encoding="utf-8")
    (schemas / "batch-01.txt").write_text("schema", encoding="utf-8")

    manifest = resume.model_input_manifest(tmp_path)

    assert set(manifest) == {"prompts/batch-01.txt", "schemas/batch-01.txt"}
    assert manifest["prompts/batch-01.txt"] != manifest["schemas/batch-01.txt"]


def test_transport_change_is_bounded_to_context_namespace_allocation() -> None:
    current = previous.transport_hashes(Path.cwd())
    unchanged = set(current) - {
        "continuation_harness_file",
        "continuation_transport_adapter",
    }

    assert all(
        current[key] == previous.EXPECTED_TRANSPORT_HASHES[key] for key in unchanged
    )
    assert current["continuation_harness_file"] != previous.EXPECTED_TRANSPORT_HASHES[
        "continuation_harness_file"
    ]
    assert current["continuation_transport_adapter"] != previous.EXPECTED_TRANSPORT_HASHES[
        "continuation_transport_adapter"
    ]
    assert resume.root_cause_document()["status"] == "PASS"
