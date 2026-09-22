from __future__ import annotations

import json
from pathlib import Path

import pytest

from app.services.accepted_decision_v2_runtime_service import (
    STAGE2_MODEL_OUTPUT_CONTRACT,
)
from scripts.m12ch_full22_reproof import (
    ReproofFailure,
    call_key,
    exact_ref_errors,
    stage2_raw_contract_audit,
)


def _write_json(path: Path, value: object) -> None:
    path.write_text(json.dumps(value), encoding="utf-8")


def test_call_key_accepts_only_planned_core_and_stage2_outputs() -> None:
    assert call_key(Path("/tmp/us/core-batch-03.output.json")) == (
        "us",
        "FUNDAMENTAL_CORE",
        3,
    )
    assert call_key(Path("/tmp/kr/batch-02.output.json")) == (
        "kr",
        "PRICE_TIMING",
        2,
    )

    with pytest.raises(ReproofFailure, match="forbidden_or_unknown_model_call"):
        call_key(Path("/tmp/us/batch-01.CORZ.repair.output.json"))


def test_stage2_raw_contract_rejects_model_authored_provenance(tmp_path: Path) -> None:
    safe = tmp_path / "safe.json"
    _write_json(
        safe,
        {
            "contract": STAGE2_MODEL_OUTPUT_CONTRACT,
            "candidates": [{"ticker": "CORZ", "driver_maturity": [{"driver": "x"}]}],
        },
    )
    assert stage2_raw_contract_audit(safe)["status"] == "PASS"

    unsafe = tmp_path / "unsafe.json"
    _write_json(
        unsafe,
        {
            "contract": STAGE2_MODEL_OUTPUT_CONTRACT,
            "candidates": [
                {
                    "ticker": "CORZ",
                    "driver_maturity": [
                        {
                            "driver": "x",
                            "as_of": "2026-09-15",
                            "provenance_status": "CONCRETE_ONLY",
                        }
                    ],
                }
            ],
        },
    )
    audit = stage2_raw_contract_audit(unsafe)
    assert audit["status"] == "FAIL"
    assert audit["model_authored_as_of_count"] == 1
    assert audit["model_authored_provenance_status_count"] == 1


def test_exact_ref_errors_distinguishes_evidence_and_atomic_claim_refs(
    tmp_path: Path,
) -> None:
    output = tmp_path / "output.json"
    catalog = tmp_path / "catalog.json"
    _write_json(
        output,
        {
            "evidence_refs": ["evidence:ok"],
            "supporting_claim_refs": ["core-claim:ok"],
            "source_condition_ref": "source:ok",
            "leaf_ref": "leaf:ok",
        },
    )
    _write_json(
        catalog,
        {
            "allowed_refs": ["evidence:ok"],
            "allowed_maturity_claim_refs": ["core-claim:ok"],
            "allowed_source_condition_refs": ["source:ok"],
            "allowed_leaf_refs": ["leaf:ok"],
        },
    )
    assert exact_ref_errors(output, catalog) == []

    _write_json(
        output,
        {
            "evidence_refs": ["evidence:ok"],
            "supporting_claim_refs": ["core-claim:invented"],
        },
    )
    errors = exact_ref_errors(output, catalog)
    assert errors == [
        {
            "path": "$.supporting_claim_refs[0]",
            "kind": "supporting_claim_refs",
            "ref": "core-claim:invented",
        }
    ]
