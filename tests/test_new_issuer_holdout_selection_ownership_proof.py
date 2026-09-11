from __future__ import annotations

import asyncio
import hashlib
import json
from pathlib import Path

import pytest

from app.services.direction_timing_ownership_service import DirectionalUnknown
from scripts import new_issuer_holdout_selection_ownership_proof as proof
from scripts import synthetic_canary_fixture_repair_ownership_resume as synthetic


def _write_json(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value), encoding="utf-8")


def _write_identity_templates(prompt: Path, schema: Path) -> None:
    identity = {
        "contract": proof.CORE_OUTPUT_CONTRACT,
        "packet_id": "generation",
        "tickers": ["TEST"],
    }
    prompt.write_text(
        "IDENTITY:\n" + json.dumps(identity, separators=(",", ":")) + "\n",
        encoding="utf-8",
    )
    _write_json(
        schema,
        {
            "type": "object",
            "properties": {
                "contract": {"const": proof.CORE_OUTPUT_CONTRACT},
                "packet_id": {"const": "generation"},
                "candidates": {
                    "type": "array",
                    "items": {
                        "anyOf": [
                            {
                                "type": "object",
                                "properties": {"ticker": {"const": "TEST"}},
                            }
                        ]
                    },
                },
            },
        },
    )


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


def test_core_partial_audit_rejects_historical_neon_unknown_field_shape() -> None:
    owned = synthetic.fictional_owned("SYNTHETIC_NEON_CAPTURE", market="us")
    core = synthetic.fixture_core(owned)
    earnings = f"fictional:{core.ticker}:earnings"
    business = f"fictional:{core.ticker}:business"
    historical_shape = DirectionalUnknown(
        summary=(
            "과거 손실은 부정 근거지만 공식 실적의 현재성이 낮아 "
            "후속 공시 확인이 필요하다."
        ),
        evidence_refs=(earnings, business),
        treatment="CONFIRMATION_REQUIRED",
        directional_negative_basis=(earnings,),
    )
    captured_derivative = core.model_copy(
        update={"unknown_treatments": (historical_shape,)}
    )

    result = proof.core_partial_audit(
        (captured_derivative,), {captured_derivative.ticker: owned}
    )

    row = result["rows"][0]
    assert result["status"] == "FAIL"
    assert row["errors"] == ["unknown_nonnegative_has_directional_basis"]
    assert row["unknown_treatment_consistency_issues"][0]["field_path"] == (
        "unknown_treatments[0].directional_negative_basis"
    )


def test_core_partial_audit_preserves_negative_fact_and_separate_unknown() -> None:
    owned = synthetic.fictional_owned("SYNTHETIC_NEGATIVE_FACT", market="us")
    core = synthetic.fixture_core(owned)
    earnings = f"fictional:{core.ticker}:earnings"
    unknown = f"fictional:{core.ticker}:unknown"
    candidate = core.model_copy(
        update={
            "unknown_treatments": (
                DirectionalUnknown(
                    summary="확인된 손실은 방향성 부정 근거입니다.",
                    evidence_refs=(earnings,),
                    treatment="DIRECTIONAL_NEGATIVE",
                    directional_negative_basis=(earnings,),
                ),
                DirectionalUnknown(
                    summary="향후 실행은 후속 확인이 필요합니다.",
                    evidence_refs=(unknown,),
                    treatment="CONFIRMATION_REQUIRED",
                    directional_negative_basis=(),
                ),
            )
        }
    )

    result = proof.core_partial_audit((candidate,), {candidate.ticker: owned})

    assert result["status"] == "PASS"
    assert result["rows"][0]["unknown_treatment_consistency_failure_count"] == 0


def test_core_partial_audit_rejects_missing_only_as_directional_negative() -> None:
    owned = synthetic.fictional_owned("SYNTHETIC_MISSING_NEGATIVE", market="us")
    core = synthetic.fixture_core(owned)
    unknown = f"fictional:{core.ticker}:unknown"
    candidate = core.model_copy(
        update={
            "unknown_treatments": (
                DirectionalUnknown(
                    summary="자료 부재만 확인됩니다.",
                    evidence_refs=(unknown,),
                    treatment="DIRECTIONAL_NEGATIVE",
                    directional_negative_basis=(unknown,),
                ),
            )
        }
    )

    result = proof.core_partial_audit((candidate,), {candidate.ticker: owned})

    assert result["status"] == "FAIL"
    assert result["rows"][0]["errors"] == [
        "unknown_directional_negative_without_non_unknown_evidence"
    ]


def test_execute_run_stops_before_timing_after_invalid_core(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    owned = synthetic.fictional_owned("SYNTHETIC_EARLY_STOP", market="us")
    core = synthetic.fixture_core(owned)
    earnings = f"fictional:{core.ticker}:earnings"
    invalid = core.model_copy(
        update={
            "unknown_treatments": (
                DirectionalUnknown(
                    summary="현재 확인이 필요합니다.",
                    evidence_refs=(earnings,),
                    treatment="CONFIRMATION_REQUIRED",
                    directional_negative_basis=(earnings,),
                ),
            )
        }
    )
    output_root = tmp_path / "offline-injected-run"
    calls: list[tuple[str, int]] = []

    class NeverNetworkAdapter:
        def invoke(self, **kwargs: object) -> dict[str, object]:
            raise AssertionError("offline early-stop proof must not call transport")

    def inject_captured_core(**kwargs: object) -> tuple[dict[str, object], Path]:
        stage = str(kwargs["stage"])
        batch_number = int(kwargs["batch_number"])
        calls.append((stage, batch_number))
        if len(calls) != 1 or stage != "DIRECTIONAL_CORE":
            raise AssertionError("no context may follow the invalid Core")
        context = proof.context_directory(output_root, "a", stage, batch_number)
        context.mkdir(parents=True)
        output = context / "output.raw.json"
        _write_json(output, {"candidates": [invalid.model_dump(mode="json")]})
        manifest = {
            "contract": "offline-captured-context-v1",
            "per_context_partial_semantic_audit_status": "NOT_MEASURED",
        }
        _write_json(context / "context_manifest.json", manifest)
        return manifest, output

    monkeypatch.setattr(proof, "invoke_model_context", inject_captured_core)
    monkeypatch.setattr(proof.runtime_identity, "load_binding", lambda path: object())
    monkeypatch.setattr(
        proof.runtime_identity,
        "validate_output_identity",
        lambda value, binding: {"status": "PASS"},
    )
    monkeypatch.setattr(
        proof.frozen,
        "_resolve_batch_candidates",
        lambda raw, **kwargs: ((invalid,), {}),
    )
    state = {
        "program_generation_id": "offline-generation",
        "directional_context_count": 0,
        "price_timing_context_count": 0,
        "renderer_context_count": 0,
        "per_context_semantic_failure_count": 0,
    }
    args = type("Args", (), {"output_root": output_root})()

    with pytest.raises(
        proof.SemanticStop,
        match="core_partial_semantic_audit_failed:a:1",
    ):
        proof.execute_run(
            args=args,
            state=state,
            adapter=NeverNetworkAdapter(),
            run="a",
            cohort=(invalid.ticker,),
            contexts={},
            evidence={},
            owned={invalid.ticker: owned},
            core_aliases={},
            timing_aliases={},
            price_maps={},
            stocks={},
        )

    assert calls == [("DIRECTIONAL_CORE", 1)]
    assert state["directional_context_count"] == 1
    assert state["price_timing_context_count"] == 0
    assert state["renderer_context_count"] == 0
    assert state["per_context_semantic_failure_count"] == 1
    assert not (output_root / "model-contexts/A/PRICE_TIMING").exists()


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
    assert len(proof.PROOF_NAMES) == 60
    assert proof.PROOF_NAMES[4] == "05-dual-market-source-coverage-policy"
    assert proof.PROOF_NAMES[59] == "60-program-completion"


def test_market_evaluation_uses_precommitted_reserve_until_target(monkeypatch) -> None:
    async def fake_evaluate(identity, *, as_of, cache_dir):
        ticker = str(identity["ticker"])
        eligible = ticker in {"B", "C"}
        row = {
            "ticker": ticker,
            "market": "us",
            "issuer_id": f"issuer-{ticker}",
            "issuer_key": f"issuer-{ticker}",
            "evidence_families": [
                "IDENTITY_SECURITY",
                "EARNINGS_FINANCIAL_CURRENT",
                "VALUATION_SAFE",
            ],
            "source_provenance": [],
            "sufficiency_status": "SUFFICIENT_FOR_DIRECTIONAL_JUDGMENT",
            "directional_model_eligible": eligible,
            "missing_required_families": [] if eligible else ["BUSINESS_CURRENT"],
            "preflight_status": "ASSEMBLED" if eligible else "SOURCE_INSUFFICIENT",
            "provider_audit": {
                "profile_successes": 1,
                "companyfacts_successes": 1,
            },
        }
        result = object() if eligible else None
        if eligible:
            row.update(
                {
                    "base_status": "ASSEMBLED",
                    "packet_sha256": f"packet-{ticker}",
                    "validation_errors": [],
                }
            )
        return row, result

    monkeypatch.setattr(proof, "evaluate_candidate", fake_evaluate)
    rows = [
        {"ticker": ticker, "company_name": ticker, "market": "us"}
        for ticker in ("A", "B", "C", "D")
    ]

    selected, audit_rows = asyncio.run(
        proof.evaluate_market_candidates(
            market="us",
            rows=rows,
            target=2,
            as_of=proof.datetime(2026, 9, 7, tzinfo=proof.UTC),
            cache_dir=Path("unused"),
            selected_issuer_keys=set(),
        )
    )

    assert len(selected) == 2
    assert [row["ticker"] for row in audit_rows] == ["A", "B", "C"]
    assert audit_rows[0]["price_context_status"] == "NOT_ATTEMPTED_SOURCE_GATE"
    assert audit_rows[2]["primary_or_reserve"] == "RESERVE"


def test_dual_market_summary_preserves_other_market_result_after_us_failure() -> None:
    us = {
        "target_count": 4,
        "attempted_count": 5,
        "source_sufficient_count": 2,
        "source_insufficient_count": 3,
        "pipeline_coverage_gap_count": 2,
        "source_absence_count": 1,
        "unknown_failure_count": 0,
        "source_target_status": "FAIL",
        "rows": [
            {
                "eligible_for_final_holdout": False,
                "failure_reason_codes": ["NORMALIZATION_OR_MAPPING_GAP"],
            }
        ],
    }
    kr = {
        "target_count": 12,
        "attempted_count": 12,
        "source_sufficient_count": 12,
        "source_insufficient_count": 0,
        "pipeline_coverage_gap_count": 0,
        "source_absence_count": 0,
        "unknown_failure_count": 0,
        "source_target_status": "PASS",
        "rows": [],
    }

    result = proof.dual_market_summary(us, kr)

    assert result["dual_market_source_status"] == "US_FAIL_KR_PASS"
    assert result["kr_attempted"] == 12
    assert result["market_failure_did_not_abort_other_market_diagnostic"] == 1
    assert result["real_holdout_model_calls_while_source_target_failed"] == 0


def test_raw_regulatory_tags_classify_unmapped_bank_domain_as_pipeline_gap(
    tmp_path: Path,
) -> None:
    _write_json(
        tmp_path / "sec_companyfacts" / "BANK.json",
        {
            "facts": {
                "us-gaap": {
                    "CapitalRequiredForCapitalAdequacyToRiskWeightedAssets": {}
                }
            }
        },
    )
    row = {
        "ticker": "BANK",
        "market": "us",
        "issuer_id": "0000001",
        "issuer_key": "issuer-bank",
        "market_sequence": 1,
        "initial_or_reserve": "INITIAL",
        "evidence_families": [
            "IDENTITY_SECURITY",
            "EARNINGS_FINANCIAL_CURRENT",
        ],
        "missing_required_families": [
            "REGULATORY_CAPITAL_CURRENTORSECTOR_OPERATING_CURRENT"
        ],
        "sufficiency_status": "SUFFICIENT_FOR_LIMITED_RESEARCH_ONLY",
        "preflight_status": "SOURCE_INSUFFICIENT",
        "directional_model_eligible": False,
        "provider_audit": {
            "profile_successes": 1,
            "companyfacts_successes": 1,
        },
    }

    result = proof.candidate_coverage_row(
        row,
        None,
        identity={"company_name": "Bank"},
        cache_dir=tmp_path,
    )

    assert result["failure_class"] == "PIPELINE_COVERAGE_GAP"
    assert "NORMALIZATION_OR_MAPPING_GAP" in result["failure_reason_codes"]
    assert result["true_source_absence_suspected"] is False


def test_nested_provider_audit_keeps_eligible_candidate_free_of_failure_codes(
    tmp_path: Path,
) -> None:
    row = {
        "ticker": "PASS",
        "market": "us",
        "issuer_id": "0000002",
        "issuer_key": "issuer-pass",
        "market_sequence": 1,
        "initial_or_reserve": "INITIAL",
        "evidence_families": [
            "IDENTITY_SECURITY",
            "BUSINESS_CURRENT",
            "EARNINGS_FINANCIAL_CURRENT",
        ],
        "missing_required_families": [],
        "sufficiency_status": "SUFFICIENT_FOR_DIRECTIONAL_JUDGMENT",
        "preflight_status": "SUFFICIENT_FOR_DIRECTIONAL_JUDGMENT",
        "directional_model_eligible": True,
        "base_status": "ASSEMBLED",
        "packet_sha256": "packet",
        "provider_audit": {
            "fundamental": {
                "profile_successes": 1,
                "companyfacts_successes": 1,
            },
            "base": {"ohlcv": "success"},
        },
        "selected": True,
    }

    result = proof.candidate_coverage_row(
        row,
        object(),
        identity={"company_name": "Pass"},
        cache_dir=tmp_path,
    )

    assert result["official_profile_status"] == "PASS"
    assert result["filing_or_official_financial_status"] == "PASS"
    assert result["failure_reason_codes"] == []
    assert proof._provider_metric(result, "profile_successes") == 1


def test_model_context_is_invoked_once_and_preserved_before_return(
    tmp_path: Path,
) -> None:
    output_root = tmp_path / "output"
    receipt_root = output_root / "transport-receipts"
    prompt = tmp_path / "prompt.txt"
    schema = tmp_path / "schema.json"
    _write_identity_templates(prompt, schema)
    proof.write_json(
        output_root / "source-lock.json",
        {
            "source_lock_sha256": "lock",
            "packet_sha256": {"TEST": "packet"},
            "market_by_ticker": {"TEST": "us"},
        },
    )

    class FakeAdapter:
        model_call_count = 0
        continuation_generation = "generation"

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
                        "generation_id": "generation",
                        "invocation_id": invocation_id,
                        "stage": str(kwargs["stage"]),
                        "batch_id": str(kwargs["batch_id"]),
                        "subject_count": int(kwargs["subject_count"]),
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


def _context_args(tmp_path: Path):
    output_root = tmp_path / "output"
    proof.write_json(
        output_root / "source-lock.json",
        {
            "source_lock_sha256": "lock",
            "packet_sha256": {"TEST": "packet"},
            "market_by_ticker": {"TEST": "us"},
        },
    )
    prompt = tmp_path / "prompt.txt"
    schema = tmp_path / "schema.json"
    _write_identity_templates(prompt, schema)
    args = type(
        "Args",
        (),
        {"output_root": output_root, "timeout": proof.TIMEOUT_SECONDS},
    )()
    state = {
        "program_generation_id": "generation",
        "source_lock_sha256": "lock",
        "model_invocation_count": 0,
        "context_evidence_preservation_failure_count": 0,
        "context_preservation_secondary_failure_count": 0,
        "transport_timeout_count": 0,
        "historical_stall_pattern_recurred": 0,
    }
    return args, state, prompt, schema


def test_prespawn_failure_preserves_root_without_requiring_receipt(
    tmp_path: Path,
) -> None:
    args, state, prompt, schema = _context_args(tmp_path)
    root_error = synthetic.LiveWorkloadObservationUnavailable("observer denied")

    class FakeAdapter:
        model_call_count = 0
        continuation_generation = "generation"
        receipt_root = args.output_root / "receipts"

        def invoke(self, **kwargs: object) -> dict[str, object]:
            lifecycle = {
                "failure_stage": "PRE_SPAWN",
                "spawn_started": 0,
                "transport_receipt_expected": 0,
                "transport_receipt_created": 0,
                "root_exception_masked": 0,
            }
            setattr(root_error, "transport_lifecycle", lifecycle)
            raise root_error

        def lifecycle_for(self, invocation_id: str) -> dict[str, object]:
            return dict(root_error.transport_lifecycle)

    with pytest.raises(
        synthetic.LiveWorkloadObservationUnavailable, match="observer denied"
    ):
        proof.invoke_model_context(
            args=args,
            state=state,
            adapter=FakeAdapter(),
            run="first",
            stage="DIRECTIONAL_CORE",
            batch_number=1,
            subjects=("TEST",),
            sequence_position=1,
            prompt_source=prompt,
            schema_source=schema,
        )

    context = args.output_root / "model-contexts/FIRST/DIRECTIONAL_CORE/batch-01"
    failure = proof.read_json(context / "pre-spawn-failure.json")
    manifest = proof.read_json(context / "context_manifest.json")
    assert failure["spawn_started"] == 0
    assert failure["transport_receipt_expected"] == 0
    assert failure["transport_receipt_created"] == 0
    assert failure["root_exception_masked"] == 0
    assert manifest["context_evidence_preservation_status"] == "PASS"
    assert state["context_preservation_secondary_failure_count"] == 0


def test_postspawn_missing_receipt_remains_detectable(tmp_path: Path) -> None:
    args, state, prompt, schema = _context_args(tmp_path)

    class FakeAdapter:
        model_call_count = 1
        continuation_generation = "generation"
        receipt_root = args.output_root / "receipts"

        def invoke(self, **kwargs: object) -> dict[str, object]:
            Path(str(kwargs["output"])).write_text("{}\n", encoding="utf-8")
            return {}

    with pytest.raises(ValueError, match="POST_SPAWN_RECEIPT_MISSING"):
        proof.invoke_model_context(
            args=args,
            state=state,
            adapter=FakeAdapter(),
            run="first",
            stage="DIRECTIONAL_CORE",
            batch_number=1,
            subjects=("TEST",),
            sequence_position=1,
            prompt_source=prompt,
            schema_source=schema,
        )


def test_runtime_identity_mismatch_blocks_adapter_before_spawn(tmp_path: Path) -> None:
    args, state, prompt, schema = _context_args(tmp_path)

    class NeverCalledAdapter:
        model_call_count = 0
        continuation_generation = "wrong-generation"
        receipt_root = args.output_root / "receipts"
        called = False

        def invoke(self, **kwargs: object) -> dict[str, object]:
            self.called = True
            raise AssertionError("adapter must not be called")

        def lifecycle_for(self, invocation_id: str) -> dict[str, object]:
            return {}

    adapter = NeverCalledAdapter()
    with pytest.raises(
        proof.runtime_identity.PreSpawnRuntimeIdentityBindingMismatch,
        match="adapter_generation_id",
    ):
        proof.invoke_model_context(
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

    context = args.output_root / "model-contexts/FIRST/DIRECTIONAL_CORE/batch-01"
    preflight = proof.read_json(context / "actual-request-identity-preflight.json")
    failure = proof.read_json(context / "pre-spawn-failure.json")
    assert adapter.called is False
    assert adapter.model_call_count == 0
    assert preflight["status"] == "FAIL"
    assert preflight["spawn_started"] == 0
    assert failure["failure_stage"] == "PRE_SPAWN_IDENTITY_GATE"
    assert failure["root_exception_masked"] == 0
