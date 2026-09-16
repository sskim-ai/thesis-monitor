from __future__ import annotations

import pytest

from scripts.m12cg_r3_proof_harness import (
    FAIL,
    NOT_PROVEN,
    PASS,
    aggregate_fixture_rows,
    evaluate_expected_exception,
    exact_node_coverage,
)


SHA = "a" * 64


def _row(
    *,
    fixture_id: str = "P01",
    variant_id: str = "P01:test",
    assertion_result: str = PASS,
) -> dict[str, object]:
    return {
        "fixture_id": fixture_id,
        "variant_id": variant_id,
        "assertion_result": assertion_result,
        "expected_result": "PASS",
        "observed_result": {"valid": True},
        "denominator": 1,
        "evidence": [{"node_id": "tests/test_example.py::test_example"}],
        "source_sha256": SHA,
        "runtime_sha256": SHA,
    }


@pytest.mark.parametrize(
    ("rows", "fixtures", "variants"),
    [
        ([], ("P01",), ("P01:test",)),
        ([None], ("P01",), ("P01:test",)),
        ([_row(), _row()], ("P01",), ("P01:test",)),
        ([_row(assertion_result="SKIPPED")], ("P01",), ("P01:test",)),
        ([_row(assertion_result="NOT_RUN")], ("P01",), ("P01:test",)),
    ],
)
def test_aggregate_never_passes_empty_duplicate_null_skip_or_not_run(
    rows: list[dict[str, object] | None],
    fixtures: tuple[str, ...],
    variants: tuple[str, ...],
) -> None:
    result = aggregate_fixture_rows(
        rows,
        required_fixture_ids=fixtures,
        required_variant_ids=variants,
    )

    assert result["status"] != PASS


def test_aggregate_reports_not_proven_for_known_pending_child() -> None:
    result = aggregate_fixture_rows(
        [_row(assertion_result=NOT_PROVEN)],
        required_fixture_ids=("P01",),
        required_variant_ids=("P01:test",),
    )

    assert result["status"] == NOT_PROVEN


def test_aggregate_rejects_missing_required_sibling_variant() -> None:
    result = aggregate_fixture_rows(
        [_row()],
        required_fixture_ids=("P01",),
        required_variant_ids=("P01:test", "P01:test[sibling]"),
    )

    assert result["status"] == FAIL
    assert "missing_variant:P01:test[sibling]" in result["errors"]


def test_aggregate_rejects_zero_denominator_and_missing_evidence() -> None:
    row = _row()
    row["denominator"] = 0
    row["evidence"] = []

    result = aggregate_fixture_rows(
        [row],
        required_fixture_ids=("P01",),
        required_variant_ids=("P01:test",),
    )

    assert result["status"] == FAIL
    assert "missing_or_zero_denominator:P01:P01:test" in result["errors"]
    assert "missing_evidence:P01:P01:test" in result["errors"]


def test_aggregate_accepts_complete_all_pass_control() -> None:
    rows = [
        _row(fixture_id="P01", variant_id="P01:a"),
        _row(fixture_id="P02", variant_id="P02:b"),
    ]

    result = aggregate_fixture_rows(
        rows,
        required_fixture_ids=("P01", "P02"),
        required_variant_ids=("P01:a", "P02:b"),
    )

    assert result["status"] == PASS
    assert result["proven_variant_count"] == 2


def test_not_applicable_requires_approved_owner_and_equivalent_evidence() -> None:
    row = _row(assertion_result="NOT_APPLICABLE")
    rejected = aggregate_fixture_rows(
        [row],
        required_fixture_ids=("P01",),
        required_variant_ids=("P01:test",),
    )
    row["approved_disposition"] = True
    row["equivalent_evidence"] = [{"owner": "native-artifact"}]
    accepted = aggregate_fixture_rows(
        [row],
        required_fixture_ids=("P01",),
        required_variant_ids=("P01:test",),
    )

    assert rejected["status"] == FAIL
    assert accepted["status"] == PASS


def test_exact_node_coverage_requires_every_exact_parameter_variant() -> None:
    nodes = [{"node_id": "tests/test_x.py::test_x[a]", "status": PASS}]

    result = exact_node_coverage(
        nodes,
        ("tests/test_x.py::test_x[a]", "tests/test_x.py::test_x[b]"),
    )

    assert result["status"] == FAIL
    assert result["missing_node_ids"] == ["tests/test_x.py::test_x[b]"]


def test_expected_exception_requires_exact_type_and_code() -> None:
    def intended() -> None:
        raise ValueError("intended_code")

    def unrelated() -> None:
        raise TypeError("intended_code")

    intended_result = evaluate_expected_exception(
        intended,
        expected_type=ValueError,
        expected_code="intended_code",
    )
    unrelated_result = evaluate_expected_exception(
        unrelated,
        expected_type=ValueError,
        expected_code="intended_code",
    )

    assert intended_result["status"] == PASS
    assert unrelated_result["status"] == FAIL
