from __future__ import annotations

import json
import hashlib
from pathlib import Path

from scripts import new_issuer_holdout_selection_ownership_proof as proof
from scripts import synthetic_canary_fixture_repair_ownership_resume as synthetic


def _write_json(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value), encoding="utf-8")


def test_exposure_registry_uses_real_outputs_and_deduplicates_share_classes(
    tmp_path: Path,
) -> None:
    _write_json(
        tmp_path / "20260906-one" / "first.json",
        {
            "contract": "uskr22-structured-autonomy-run-v1",
            "program_generation_id": "generation-one",
            "run": "first",
            "candidate_count": 2,
            "candidates": [{"ticker": "GOOG"}, {"ticker": "ABC"}],
            "batch_invocations": [
                {"batch": 1, "tickers": ["GOOG", "ABC"]},
            ],
        },
    )
    _write_json(
        tmp_path / "20260906-two" / "first.json",
        {
            "contract": "uskr22-structured-autonomy-run-v1",
            "program_generation_id": "generation-two",
            "run": "first",
            "candidate_count": 1,
            "candidates": [{"ticker": "GOOGL"}],
        },
    )
    _write_json(
        tmp_path / "20260906-source-only" / "selection.json",
        {
            "contract": "final-unseen-cohort-selection-v1",
            "candidate_count": 1,
            "rows": [{"ticker": "NEVER_CALLED"}],
        },
    )
    universe = [
        {"ticker": "GOOG", "company_name": "Alphabet Inc", "market": "us"},
        {"ticker": "GOOGL", "company_name": "Alphabet Inc Class A", "market": "us"},
        {"ticker": "ABC", "company_name": "ABC Corp", "market": "us"},
    ]

    result = proof.build_exposure_registry(tmp_path, universe)

    assert result["status"] == "PASS"
    assert result["registry_count"] == 2
    alphabet = next(
        row for row in result["rows"] if row["canonical_issuer_key"] == "us:alphabet"
    )
    assert alphabet["tickers"] == ["GOOG", "GOOGL"]
    assert "NEVER_CALLED" not in proof.exposure_tickers(result)


def test_market_ranking_is_deterministic_and_sector_stratified() -> None:
    rows = [
        {"ticker": "A", "market": "kr", "sector": "one"},
        {"ticker": "B", "market": "kr", "sector": "one"},
        {"ticker": "C", "market": "kr", "sector": "two"},
        {"ticker": "D", "market": "us", "sector": "one"},
    ]

    first = proof.ranked_market_candidates(rows, "kr")
    second = proof.ranked_market_candidates(list(reversed(rows)), "kr")

    assert [row["ticker"] for row in first] == [row["ticker"] for row in second]
    assert {row["ticker"] for row in first[:2]} != {"A", "B"}


def test_core_partial_audit_accepts_frozen_synthetic_core() -> None:
    owned = synthetic.fictional_owned("SYNTHETIC_NEW_HOLDOUT", market="us")
    core = synthetic.fixture_core(owned)

    result = proof.core_partial_audit((core,), {core.ticker: owned})

    assert result["status"] == "PASS"
    assert result["timing_renderer_gates"] == "NOT_MEASURED"
    assert result["rows"][0]["directional_core_price_technical_refs"] == 0
    assert result["rows"][0]["directional_core_supply_refs"] == 0


def test_secret_scan_blocks_token_shapes_without_echoing_values(tmp_path: Path) -> None:
    clean = tmp_path / "clean.txt"
    blocked = tmp_path / "blocked.txt"
    clean.write_text("canonical issuer evidence", encoding="utf-8")
    blocked.write_text(
        "Authorization: Bearer abcdefghijklmnopqrstuvwxyz123456",
        encoding="utf-8",
    )

    clean_result = proof.scan_secrets((clean,))
    blocked_result = proof.scan_secrets((blocked,))

    assert clean_result["secret_scan_status"] == "PASS"
    assert blocked_result["secret_scan_status"] == "FAIL"
    assert blocked_result["secret_exposure_count"] == 1


def test_experiment_constants_preserve_frozen_runtime_contract() -> None:
    assert proof.MODEL == "gpt-5.6-sol"
    assert proof.EFFORT == "xhigh"
    assert proof.TIMEOUT_SECONDS == 1800
    assert proof.TIMEOUT_OWNER_COUNT == 1
    assert proof.BATCH_SEMANTICS == "MODEL_CONTEXT_COUPLED"
    assert (proof.TARGET_US, proof.TARGET_KR, proof.TARGET_TOTAL) == (4, 12, 16)
    assert len(proof.PROOF_NAMES) == 52


def test_model_context_is_invoked_once_and_preserved_before_return(
    tmp_path: Path,
) -> None:
    output_root = tmp_path / "output"
    receipt_root = output_root / "transport-receipts"
    prompt = tmp_path / "prompt.txt"
    schema = tmp_path / "schema.json"
    prompt.write_text("IDENTITY:\n{}\n", encoding="utf-8")
    schema.write_text("{}\n", encoding="utf-8")
    proof.write_json(
        output_root / "source-lock.json",
        {"packet_sha256": {"TEST": "packet"}},
    )

    class FakeAdapter:
        model_call_count = 0

        def __init__(self) -> None:
            self.receipt_root = receipt_root

        def invoke(self, **kwargs: object) -> dict[str, object]:
            self.model_call_count += 1
            invocation_id = str(kwargs["invocation_id"])
            output_path = Path(str(kwargs["output"]))
            log_path = Path(str(kwargs["log"]))
            output_path.write_text("{}\n", encoding="utf-8")
            log_path.write_text("transport\n", encoding="utf-8")
            receipt = self.receipt_root / (
                hashlib.sha256(invocation_id.encode()).hexdigest()[:16] + ".json"
            )
            receipt.parent.mkdir(parents=True, exist_ok=True)
            receipt.write_text(
                json.dumps(
                    {
                        "model": proof.MODEL,
                        "reasoning_effort": proof.EFFORT,
                        "configured_timeout_seconds": proof.TIMEOUT_SECONDS,
                        "timeout_owner_count": 1,
                        "transport_metadata": {
                            "runtime_state_namespace_hash": "namespace"
                        },
                        "input_bytes": 12,
                        "status": "PASS",
                        "elapsed_to_exit_seconds": 1.0,
                        "stdout_bytes": 3,
                        "stderr_bytes": 0,
                        "output_bytes": 3,
                        "exit_code": 0,
                        "output_parsed": True,
                        "termination_initiator": "NONE",
                        "child_cleanup_status": "NOT_NEEDED",
                        "orphan_model_process_count": 0,
                    }
                ),
                encoding="utf-8",
            )
            receipt.with_suffix(".stdout.log").write_text("{}\n", encoding="utf-8")
            receipt.with_suffix(".stderr.log").write_bytes(b"")
            return proof.read_json(receipt)

    state = {
        "program_generation_id": "generation",
        "source_lock_sha256": "lock",
        "model_invocation_count": 0,
        "context_evidence_preservation_failure_count": 0,
        "transport_timeout_count": 0,
        "historical_stall_pattern_recurred": 0,
    }
    args = type(
        "Args",
        (),
        {"output_root": output_root, "timeout": proof.TIMEOUT_SECONDS},
    )()
    adapter = FakeAdapter()

    manifest, output = proof.invoke_model_context(
        args=args,
        state=state,
        adapter=adapter,
        run="first",
        stage="DIRECTIONAL_CORE",
        batch_number=1,
        subjects=("TEST",),
        sequence_position=1,
        prompt_source=prompt,
        schema_source=schema,
    )

    assert adapter.model_call_count == 1
    assert state["model_invocation_count"] == 1
    assert output.is_file()
    assert manifest["context_evidence_preservation_status"] == "PASS"
    assert (output.parent / "transport_receipt.json").is_file()
