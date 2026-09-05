from __future__ import annotations

from app.services.logical_condition_service import (
    ClaimLogicalCondition,
    ClaimLogicalExpression,
    LogicalCoverageMode,
    LogicalOperator,
    LogicalSeverity,
    SourceLogicalCondition,
    SourceLogicalExpression,
    logical_condition_errors,
    source_claim_expression,
    source_logical_condition,
)


def _source(operator: LogicalOperator = LogicalOperator.ANY_OF) -> SourceLogicalCondition:
    return SourceLogicalCondition(
        subject="GENERIC",
        generation_id="packet-1",
        source_condition_ref="K1",
        severity=LogicalSeverity.INVALIDATION_CANDIDATE,
        expression=SourceLogicalExpression(
            condition_id="K1",
            type=operator,
            children=(
                SourceLogicalExpression(condition_id="K1A", type=LogicalOperator.LEAF),
                SourceLogicalExpression(condition_id="K1B", type=LogicalOperator.LEAF),
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
        ClaimLogicalExpression(type=LogicalOperator.LEAF, condition_ref=refs[0])
        if operator == LogicalOperator.LEAF
        else ClaimLogicalExpression(
            type=operator,
            children=tuple(
                ClaimLogicalExpression(type=LogicalOperator.LEAF, condition_ref=ref)
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
