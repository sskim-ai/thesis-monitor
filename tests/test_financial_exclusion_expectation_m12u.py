from __future__ import annotations

import copy
import json
from pathlib import Path

import pytest

from app.services.directional_balance_service import directional_balance_ordinal_calibration_prompt
from app.services.financial_framework_claim_service import (
    FrameworkClaimKind,
    financial_framework_claims,
)
from scripts import financial_exclusion_expectation_m12u as u
from tests.test_financial_exclusion_m12f import net_debt_ref, validate

FIXTURES = json.loads(Path("fixtures/financial_exclusion_expectation_m12u.json").read_text())


@pytest.mark.parametrize("text", FIXTURES["positive"])
def test_nominal_exclusion_is_not_metric_application(text):
    claims = financial_framework_claims(text)
    assert claims and all(c.kind == FrameworkClaimKind.EXPLICIT_EXCLUSION for c in claims)
    assert validate(text).valid


@pytest.mark.parametrize("text", FIXTURES["negative"])
def test_mixed_unrelated_conditional_or_ambiguous_claim_remains_blocked(text):
    assert not validate(text).valid


@pytest.mark.parametrize("field", ["core_investment_judgment", "sell_drivers", "dominant_evidence"])
def test_exclusion_does_not_immunize_other_fields(field):
    claim = {"text": "운전자본 악화로 부정 판단을 강화한다.", "evidence_refs": []}
    extra = {field: [claim] if field == "sell_drivers" else claim}
    assert not validate(FIXTURES["positive"][1], extra=extra).valid


def test_exclusion_does_not_immunize_industrial_anchor():
    ref = net_debt_ref()
    assert not validate(
        FIXTURES["positive"][1],
        refs=(ref,),
        extra={"material_directional_anchor_basis": [ref.ref_id]},
    ).valid


def test_scope_is_portable_and_only_approved_surfaces_changed():
    from scripts import business_delta_alias_balance_confidence_m12z as z

    result = u.scope_audit()
    assert result["status"] == "FAIL"
    assert [key for key, value in result["checks"].items() if not value] == [
        "unrelated_files_unchanged",
        "one_appended_paragraph",
        "helper_unrelated_ast_unchanged",
    ]
    assert result["unexpected_file_changes"] == [
        "app/services/directional_financial_context_service.py"
    ]
    before = u.e.prompt_value(u.read(u.BASELINE)["approved_module_before"][u.BALANCE])
    after = z.without_m12z_prompt(result["after_prompt"])
    assert after.startswith(before + "\n\n")
    assert "\n\n" not in after.removeprefix(before).strip()


@pytest.mark.parametrize("case", FIXTURES["leverage"], ids=lambda c: c["id"])
def test_frozen_qualitative_ordinal_examples(case):
    assert u.e.tie_fixture(case["supportable_buy_buckets"]) == case["selected_buy"]
    assert case["facts"] and case["limitation"]
    assert not {"ticker", "weight", "score", "points"} & case.keys()


def test_conditional_and_independent_expectations_are_distinct():
    cases = {c["id"]: c for c in FIXTURES["leverage"]}
    assert cases["LEV-MKT-01"]["selected_buy"] == cases["LEV-MKT-03"]["selected_buy"]
    assert cases["LEV-MKT-02"]["selected_buy"] < cases["LEV-MKT-01"]["selected_buy"]
    assert cases["LEV-MKT-04"]["classification"] == "NOT_ADDITIONAL_NEGATIVE_CORROBORATION"
    assert cases["LEV-MKT-05"]["selected_buy"] < 6
    assert cases["LEV-MKT-06"]["classification"] == "INDEPENDENT_MARKET_EXPECTATION_AXIS"


def test_one_generic_prompt_clarification_preserves_prior_text():
    from scripts import business_delta_alias_balance_confidence_m12z as z

    before = u.read(u.BASELINE)["approved_module_before"][u.BALANCE]
    prompt = z.without_m12z_prompt(directional_balance_ordinal_calibration_prompt())
    assert prompt.startswith(u.e.prompt_value(before) + "\n\n")
    addition = prompt[len(u.e.prompt_value(before)) :].strip()
    assert "\n\n" not in addition
    assert "Source-category independence is not economic independence" in addition
    assert "conditional on the same materially unresolved" in addition
    assert "Confirmed financing stress" in addition
    assert "not source categories or reference counts" in addition
    assert "FIC-FIN" not in addition and "LEV-MKT" not in addition


def test_target_is_read_from_frozen_review_not_overridden_by_old_audit():
    root = u.read(u.ROOT)
    row = {"ticker": "FIC-FIN-05", "core": {"directional_balance": {"buy": 4}}}
    assert u.calibration_audit(row, root)["status"] == "FAIL"
    copy_root = copy.deepcopy(root)
    copy_root["expectation"]["all_target_buys"]["FIC-FIN-05"] = 4
    assert u.calibration_audit(row, copy_root)["status"] == "PASS"
    assert u.read(u.ROOT) == root


def test_original_m12t_row_remains_failed_and_new_offline_exclusion_passes(monkeypatch):
    # Committed historical rows, not a machine-local ZIP dependency in hosted CI.
    directory = Path(
        "docs/reports/20260910-bounded-astra-transport-timeout-review-new-full-fictional-canary"
    )
    original = [
        row
        for name in ("34-run-1-context-01.json", "35-run-1-context-02.json")
        for row in json.loads((directory / name).read_text())["rows"]
    ]
    monkeypatch.setattr(u, "preserved_rows", lambda: copy.deepcopy(original))
    replay = u.offline_replay()
    row = next(r for r in replay["rows"] if r["ticker"] == "FIC-FIN-08")
    assert row["status"] == "PASS"
    assert replay["original_exclusion_errors"] == ["financial_sector_generic_reasoning"]
    assert replay["original_rows_unchanged"]
    assert replay["old_leverage_calibration"]["status"] == "FAIL"


def test_runtime_delegates_unchanged_without_retry(tmp_path, monkeypatch):
    from scripts import astra_transport_m12t as t

    monkeypatch.setattr(u, "OUTPUT", tmp_path)
    u.write(tmp_path / "phase-a-receipt.json", {"status": "FAIL"})
    with pytest.raises(ValueError, match="phase_a_not_passed"):
        u.run()
    assert (t.m12.TIMEOUT_SECONDS, t.m12.SUBJECTS_PER_CONTEXT, t.m12.REPETITION_COUNT) == (
        1800,
        4,
        3,
    )


def test_required_artifact_names_are_complete_and_unique():
    assert set(u.SLUGS) == set(range(1, 80))
    assert len(set(u.SLUGS.values())) == 79
