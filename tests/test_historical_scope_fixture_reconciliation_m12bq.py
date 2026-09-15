from __future__ import annotations

import copy

from scripts import financial_exclusion_expectation_m12u as m12u
from scripts import first_class_typed_financial_evidence_m12b as m12b
from scripts import sol_restoration_m12w as m12w


M12BP_AUTHORIZED_CHANGE_PATHS = {
    "app/services/coldstart_fundamental_enrichment_service.py",
    "app/services/company_profile_service.py",
    "app/services/opendart_financial_recovery_service.py",
    "tests/test_coldstart_fundamental_enrichment_service.py",
    "tests/test_company_profile_service.py",
    "tests/test_opendart_financial_recovery_service.py",
}


def _m12b_scope_is_valid(frozen: dict[str, dict[str, object]]) -> bool:
    approved_changed_surfaces = {
        "calibration",
        "financial_validator",
        "core_prompt",
        "output_schema",
        "source_sufficiency",
    }
    return all(
        row["status"] == "PASS"
        for name, row in frozen.items()
        if name not in approved_changed_surfaces
    )


def test_m12u_allows_exact_m12bp_paths_and_rejects_unrelated_fake_path(
    tmp_path, monkeypatch
) -> None:
    baseline = m12u.read(m12u.BASELINE)
    fake_path = "app/services/m12bq_unrelated_fake.py"
    baseline["files"][fake_path] = "0" * 64
    original_read = m12u.read

    def read_with_fake(path):
        if path == m12u.BASELINE:
            return copy.deepcopy(baseline)
        return original_read(path)

    monkeypatch.setattr(m12u, "read", read_with_fake)
    result = m12u.scope_audit()

    assert not M12BP_AUTHORIZED_CHANGE_PATHS & set(result["unexpected_file_changes"])
    assert fake_path in result["unexpected_file_changes"]
    assert result["status"] == "FAIL"


def test_m12w_allows_exact_m12bp_paths_and_preserves_unexpected_path_rejection() -> None:
    result = m12w.freeze()

    assert not M12BP_AUTHORIZED_CHANGE_PATHS & set(result["changed_existing_paths"])
    assert "app/services/financial_framework_claim_service.py" in result[
        "changed_existing_paths"
    ]
    assert result["status"] == "FAIL"


def test_m12b_allows_only_named_surface_and_rejects_unrelated_surface_change() -> None:
    frozen = m12b._frozen_surfaces()
    assert _m12b_scope_is_valid(frozen)

    unexpected = copy.deepcopy(frozen)
    unexpected["renderer"]["status"] = "FAIL"
    assert not _m12b_scope_is_valid(unexpected)
