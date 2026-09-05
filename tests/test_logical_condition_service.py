from __future__ import annotations

import pytest
from pydantic import ValidationError

from app.services.logical_condition_service import (
    ClaimLogicalCondition,
    ClaimLogicalComposite,
    ClaimLogicalLeaf,
    LogicalCoverageMode,
    LogicalOperator,
    LogicalSeverity,
    SourceLogicalCondition,
    SourceLogicalComposite,
    SourceLogicalLeaf,
    CheckpointMetric,
    logical_condition_errors,
    source_checkpoint_metric_refs,
    source_claim_expression,
    source_logical_condition,
)


def _source(operator: LogicalOperator = LogicalOperator.ANY_OF) -> SourceLogicalCondition:
    return SourceLogicalCondition(
        subject="GENERIC",
        generation_id="packet-1",
        source_condition_ref="K1",
        severity=LogicalSeverity.INVALIDATION_CANDIDATE,
        expression=SourceLogicalComposite(
            condition_id="K1",
            type=operator,
            children=(
                SourceLogicalLeaf(condition_id="K1A"),
                SourceLogicalLeaf(condition_id="K1B"),
            ),
        ),
    )


def _claim(
    operator: LogicalOperator,
    *,
    refs: tuple[str, ...] = ("K1A", "K1B"),
    coverage: LogicalCoverageMode = LogicalCoverageMode.FULL,
) -> ClaimLogicalCondition:
    expression = (
        ClaimLogicalLeaf(leaf_ref=refs[0])
        if operator == LogicalOperator.LEAF
        else ClaimLogicalComposite(
            type=operator,
            children=tuple(
                ClaimLogicalLeaf(leaf_ref=ref)
                for ref in refs
            ),
        )
    )
    return ClaimLogicalCondition(
        source_condition_ref="K1",
        coverage_mode=coverage,
        severity=LogicalSeverity.INVALIDATION_CANDIDATE,
        expression=expression,
    )


def _errors(source: SourceLogicalCondition, claim: ClaimLogicalCondition | None) -> tuple[str, ...]:
    return logical_condition_errors(
        subject="GENERIC",
        generation_id="packet-1",
        source_conditions=(source,),
        claim=claim,
    )


def test_source_adapter_owns_explicit_or_before_writer() -> None:
    source = source_logical_condition(
        subject="GENERIC",
        generation_id="packet-1",
        evidence_ref="risk-1",
        statement="고객계약 취소 또는 반복적인 준공 실패",
        severity=LogicalSeverity.INVALIDATION_CANDIDATE,
    )

    assert source.expression.type == LogicalOperator.ANY_OF
    assert len(source.expression.children) == 2
    assert "또는" not in (source.expression.children[0].statement or "")


def test_source_metric_aliases_are_exact_and_do_not_parse_future_grammar() -> None:
    assert source_checkpoint_metric_refs(
        "영업현금흐름이 개선되고 잉여현금흐름을 점검"
    ) == (CheckpointMetric.OCF, CheckpointMetric.FCF)
    assert source_checkpoint_metric_refs("CAPEX 증가를 점검") == ()

    source = source_logical_condition(
        subject="GENERIC",
        generation_id="packet-1",
        evidence_ref="cash-flow-1",
        statement="영업현금흐름이 개선",
        severity=LogicalSeverity.STRENGTHENING,
    )
    assert source.metric_refs == (CheckpointMetric.OCF,)


def test_full_any_of_to_all_of_is_rejected_without_reading_prose() -> None:
    assert _errors(_source(), _claim(LogicalOperator.ALL_OF)) == (
        "logical_condition_full_semantic_mismatch",
    )


def test_full_all_of_to_any_of_is_rejected() -> None:
    assert _errors(
        _source(LogicalOperator.ALL_OF),
        _claim(LogicalOperator.ANY_OF),
    ) == ("logical_condition_full_semantic_mismatch",)


def test_full_claim_cannot_delete_branch() -> None:
    assert _errors(_source(), _claim(LogicalOperator.LEAF, refs=("K1A",))) == (
        "logical_condition_full_semantic_mismatch",
    )


def test_non_exhaustive_example_may_reference_one_source_branch() -> None:
    assert _errors(
        _source(),
        _claim(
            LogicalOperator.LEAF,
            refs=("K1A",),
            coverage=LogicalCoverageMode.NON_EXHAUSTIVE_EXAMPLE,
        ),
    ) == ()


def test_full_source_expression_round_trip_is_valid() -> None:
    source = _source()
    claim = ClaimLogicalCondition(
        source_condition_ref="K1",
        coverage_mode=LogicalCoverageMode.FULL,
        severity=source.severity,
        expression=source_claim_expression(source.expression),
    )
    assert _errors(source, claim) == ()


def test_cross_condition_branch_and_severity_mutation_are_rejected() -> None:
    claim = _claim(LogicalOperator.ANY_OF, refs=("K1A", "OTHER"))
    claim = claim.model_copy(update={"severity": LogicalSeverity.WEAKENING})
    assert set(_errors(_source(), claim)) == {
        "logical_condition_severity_mutation",
        "logical_condition_cross_condition_branch",
        "logical_condition_full_semantic_mismatch",
    }


def test_subject_and_generation_are_part_of_source_identity() -> None:
    source = _source().model_copy(update={"subject": "OTHER"})
    assert _errors(source, _claim(LogicalOperator.ANY_OF)) == (
        "logical_condition_owner_mismatch",
    )


def _claim_document(expression: object) -> dict[str, object]:
    return {
        "source_condition_ref": "K1",
        "coverage_mode": "FULL",
        "severity": "INVALIDATION_CANDIDATE",
        "expression": expression,
    }


def test_claim_schema_is_a_discriminated_union() -> None:
    expression = ClaimLogicalCondition.model_json_schema()["properties"]["expression"]

    assert expression["discriminator"]["propertyName"] == "type"
    assert set(expression["discriminator"]["mapping"]) == {"LEAF", "ANY_OF", "ALL_OF"}


def test_leaf_requires_leaf_ref_and_forbids_children() -> None:
    parsed = ClaimLogicalCondition.model_validate(
        _claim_document({"type": "LEAF", "leaf_ref": "K1A"})
    )
    assert isinstance(parsed.expression, ClaimLogicalLeaf)

    with pytest.raises(ValidationError) as exc_info:
        ClaimLogicalCondition.model_validate(
            _claim_document(
                {
                    "type": "LEAF",
                    "leaf_ref": "K1A",
                    "children": [{"type": "LEAF", "leaf_ref": "K1B"}],
                }
            )
        )
    assert "children" in str(exc_info.value)


@pytest.mark.parametrize("operator", ("ANY_OF", "ALL_OF"))
def test_composite_requires_children_and_forbids_leaf_ref(operator: str) -> None:
    valid = ClaimLogicalCondition.model_validate(
        _claim_document(
            {
                "type": operator,
                "children": [
                    {"type": "LEAF", "leaf_ref": "K1A"},
                    {"type": "LEAF", "leaf_ref": "K1B"},
                ],
            }
        )
    )
    assert isinstance(valid.expression, ClaimLogicalComposite)

    with pytest.raises(ValidationError):
        ClaimLogicalCondition.model_validate(
            _claim_document({"type": operator, "leaf_ref": "K1A"})
        )
