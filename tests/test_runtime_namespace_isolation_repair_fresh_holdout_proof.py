from __future__ import annotations

import hashlib
from pathlib import Path

import pytest

from app.services.codex_runtime_state_service import CodexRuntimeIsolationCollision
from scripts import model_transport_revalidation_ownership_continuation as transport
from scripts import new_issuer_holdout_selection_ownership_proof as runner
from scripts import runtime_namespace_isolation_repair_fresh_holdout_proof as proof
from scripts import uskr22_structured_autonomy_shadow as engine


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _auth_source(tmp_path: Path) -> Path:
    source = tmp_path / "auth.json"
    source.write_text("{}\n", encoding="utf-8")
    source.chmod(0o600)
    return source


def test_actual_adapter_allocation_is_unique_for_full_32_context_shape(
    tmp_path: Path, monkeypatch
) -> None:
    monkeypatch.setattr(transport, "cli_version", lambda _binary: "test-cli")
    adapter = transport.ContinuationTransportAdapter(
        continuation_generation="fresh-generation",
        receipt_root=tmp_path / "receipts",
        codex_bin="/usr/bin/true",
        runtime_state_root=tmp_path / "runtime-state",
    )
    auth_source = _auth_source(tmp_path)
    input_root = tmp_path / "inputs"
    input_root.mkdir()
    inputs = []
    for name, value in (
        ("prompt.txt", "prompt\n"),
        ("schema.json", '{"type":"object"}\n'),
        ("packet.json", '{"ticker":"TEST"}\n'),
    ):
        path = input_root / name
        path.write_text(value, encoding="utf-8")
        inputs.append(path)
    before = {path.name: _sha256(path) for path in inputs}

    identities = []
    for run in ("first", "a", "b", "c"):
        for stage in ("DIRECTIONAL_CORE", "PRICE_TIMING"):
            for batch in range(1, 5):
                invocation_id = f"fresh-generation:{run}:{stage}:{batch:02d}"
                with engine.isolated_model_working_directory(
                    run=f"{run}-{stage.lower()}", batch=batch
                ) as working_directory:
                    _, identity = adapter.prepare_execution_isolation(
                        state_namespace=f"FRESH_PROOF_{run.upper()}_{stage}",
                        invocation_id=invocation_id,
                        working_directory=working_directory,
                        auth_source=auth_source,
                    )
                identities.append(identity)

    assert len(identities) == 32
    assert len({row.invocation_id for row in identities}) == 32
    assert len({row.runtime_state_namespace_hash for row in identities}) == 32
    assert len({row.working_directory_identity for row in identities}) == 32
    assert adapter.isolation_registry.claim_count == 32
    assert adapter.isolation_registry.distinct_namespace_count == 32
    assert adapter.isolation_registry.distinct_working_directory_count == 32
    assert adapter.model_call_count == 0
    assert {path.name: _sha256(path) for path in inputs} == before
    assert transport.MODEL == "gpt-5.6-sol"
    assert transport.EFFORT == "xhigh"
    assert runner.TIMEOUT_SECONDS == 1800
    assert runner.CONTEXT_SIZE == 4


def test_same_generation_diff_run_stage_and_batch_get_distinct_namespaces(
    tmp_path: Path, monkeypatch
) -> None:
    monkeypatch.setattr(transport, "cli_version", lambda _binary: "test-cli")
    adapter = transport.ContinuationTransportAdapter(
        continuation_generation="same-generation",
        receipt_root=tmp_path / "receipts",
        codex_bin="/usr/bin/true",
        runtime_state_root=tmp_path / "runtime-state",
    )
    auth_source = _auth_source(tmp_path)
    rows = []
    for index, invocation_id in enumerate(
        (
            "same-generation:first:DIRECTIONAL_CORE:01",
            "same-generation:first:DIRECTIONAL_CORE:02",
            "same-generation:first:PRICE_TIMING:01",
            "same-generation:a:DIRECTIONAL_CORE:01",
        )
    ):
        working_directory = tmp_path / f"work-{index}"
        working_directory.mkdir()
        _, identity = adapter.prepare_execution_isolation(
            state_namespace="SAME_LOGICAL_GENERATION",
            invocation_id=invocation_id,
            working_directory=working_directory,
            auth_source=auth_source,
        )
        rows.append(identity)

    assert len({row.runtime_state_namespace_hash for row in rows}) == len(rows)
    assert all(row.execution_isolation_valid for row in rows)


def test_runtime_namespace_collision_stops_before_network_or_model(
    tmp_path: Path, monkeypatch
) -> None:
    monkeypatch.setattr(transport, "cli_version", lambda _binary: "test-cli")
    network_probe_calls = 0

    def forbidden_network_probe() -> None:
        nonlocal network_probe_calls
        network_probe_calls += 1
        raise AssertionError("network probe must not run after an isolation collision")

    monkeypatch.setattr(transport, "probe_codex_network_readiness", forbidden_network_probe)
    adapter = transport.ContinuationTransportAdapter(
        continuation_generation="same-generation",
        receipt_root=tmp_path / "receipts",
        codex_bin="/usr/bin/true",
        runtime_state_root=tmp_path / "runtime-state",
    )
    auth_source = _auth_source(tmp_path)
    claimed_workdir = tmp_path / "claimed-workdir"
    claimed_workdir.mkdir()
    adapter.prepare_execution_isolation(
        state_namespace="SAME_LOGICAL_GENERATION",
        invocation_id="same-generation:first:DIRECTIONAL_CORE:01",
        working_directory=claimed_workdir,
        auth_source=auth_source,
    )
    context_dir = tmp_path / "context"
    context_dir.mkdir()
    prompt = context_dir / "prompt.txt"
    schema = context_dir / "schema.json"
    prompt.write_text("prompt\n", encoding="utf-8")
    schema.write_text('{"type":"object"}\n', encoding="utf-8")

    with pytest.raises(CodexRuntimeIsolationCollision, match="RUNTIME_NAMESPACE_COLLISION"):
        adapter.invoke(
            prompt=prompt,
            output=context_dir / "output.raw.json",
            log=context_dir / "transport.log",
            schema=schema,
            cwd=tmp_path / "unused-workdir",
            timeout=1800,
            state_namespace="SAME_LOGICAL_GENERATION",
            invocation_id="same-generation:first:DIRECTIONAL_CORE:01",
            stage="DIRECTIONAL_CORE",
            batch_id="01",
            subject_count=4,
        )

    assert network_probe_calls == 0
    assert adapter.model_call_count == 0
    preflight = transport.read_json(context_dir / "runtime-isolation-preflight.json")
    assert preflight["spawn_started"] == 0
    assert preflight["status"] == "RUNTIME_NAMESPACE_COLLISION"


def test_partial_exposure_cohort_is_fully_retired_from_fresh_candidates(
    monkeypatch,
) -> None:
    monkeypatch.setattr(proof, "PREVIOUS_EXCLUSION_COUNT", 1)
    monkeypatch.setattr(proof, "UPDATED_EXCLUSION_COUNT", 17)
    prior = {
        "rows": [
            {
                "canonical_issuer_key": "prior:issuer",
                "security_aliases": ["PRIOR"],
            }
        ],
        "all_excluded_issuer_keys": ["prior:issuer"],
    }
    cohort_rows = [
        {
            "display_symbol": ticker,
            "canonical_issuer_key": f"issuer:{ticker}",
            "market": "kr" if ticker.isdigit() else "us",
        }
        for ticker in proof.LATEST_COHORT
    ]
    reserve_rows = [
        {
            "display_symbol": f"US{index}",
            "canonical_issuer_key": f"reserve:us:{index}",
            "market": "us",
        }
        for index in range(4)
    ] + [
        {
            "display_symbol": f"9{index:05d}",
            "canonical_issuer_key": f"reserve:kr:{index}",
            "market": "kr",
        }
        for index in range(12)
    ]

    registry = proof.expand_exclusion_registry(
        prior,
        [*cohort_rows, *reserve_rows],
        runtime_generation_id="historical-runtime-generation",
    )
    identities = proof.filter_candidate_identities(
        {
            "us": [
                row
                for row in [*cohort_rows, *reserve_rows]
                if row["market"] == "us"
            ],
            "kr": [
                row
                for row in [*cohort_rows, *reserve_rows]
                if row["market"] == "kr"
            ],
        },
        registry,
    )

    appended = [
        row
        for row in registry["rows"]
        if row["canonical_issuer_key"] != "prior:issuer"
    ]
    assert len(appended) == 16
    assert sum(row["actual_output_exposure"] for row in appended) == 8
    assert all(row["whole_cohort_retired"] for row in appended)
    assert not (
        set(proof.LATEST_COHORT)
        & {
            row["display_symbol"]
            for market in ("us", "kr")
            for row in identities[market]
        }
    )
