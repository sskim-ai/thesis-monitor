from __future__ import annotations

import hashlib
import re
from enum import StrEnum
from typing import Iterable

from pydantic import BaseModel, ConfigDict, Field, model_validator


CONTRACT_VERSION = "source-owned-logical-condition-v1"


class FrozenModel(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)


class LogicalOperator(StrEnum):
    LEAF = "LEAF"
    ANY_OF = "ANY_OF"
    ALL_OF = "ALL_OF"


class LogicalCoverageMode(StrEnum):
    FULL = "FULL"
    NON_EXHAUSTIVE_EXAMPLE = "NON_EXHAUSTIVE_EXAMPLE"
    PARTIAL = "PARTIAL"


class LogicalSeverity(StrEnum):
    STRENGTHENING = "STRENGTHENING"
    WEAKENING = "WEAKENING"
    INVALIDATION_CANDIDATE = "INVALIDATION_CANDIDATE"


class SourceLogicalExpression(FrozenModel):
    condition_id: str = Field(min_length=1)
    type: LogicalOperator
    statement: str | None = None
    children: tuple[SourceLogicalExpression, ...] = ()

    @model_validator(mode="after")
    def validate_shape(self) -> SourceLogicalExpression:
        if self.type == LogicalOperator.LEAF and self.children:
            raise ValueError("logical_leaf_cannot_have_children")
        if self.type != LogicalOperator.LEAF and len(self.children) < 2:
            raise ValueError("logical_composite_requires_two_children")
        return self


class SourceLogicalCondition(FrozenModel):
    contract: str = CONTRACT_VERSION
    subject: str = Field(min_length=1)
    generation_id: str = Field(min_length=1)
    source_condition_ref: str = Field(min_length=1)
    severity: LogicalSeverity
    expression: SourceLogicalExpression

    @model_validator(mode="after")
    def validate_root_identity(self) -> SourceLogicalCondition:
        if self.source_condition_ref != self.expression.condition_id:
            raise ValueError("logical_source_root_identity_mismatch")
        return self


class ClaimLogicalExpression(FrozenModel):
    type: LogicalOperator
    condition_ref: str | None = None
    children: tuple[ClaimLogicalExpression, ...] = ()

    @model_validator(mode="after")
    def validate_shape(self) -> ClaimLogicalExpression:
        if self.type == LogicalOperator.LEAF:
            if not self.condition_ref or self.children:
                raise ValueError("logical_claim_leaf_shape_invalid")
        elif self.condition_ref is not None or len(self.children) < 2:
            raise ValueError("logical_claim_composite_shape_invalid")
        return self


class ClaimLogicalCondition(FrozenModel):
    source_condition_ref: str = Field(min_length=1)
    coverage_mode: LogicalCoverageMode
    severity: LogicalSeverity
    expression: ClaimLogicalExpression


_SOURCE_ANY_OF = re.compile(r"\s+(?:또는|OR)\s+", re.IGNORECASE)


def _stable_id(prefix: str, *parts: object) -> str:
    material = "|".join(str(part) for part in parts)
    return f"{prefix}:" + hashlib.sha256(material.encode()).hexdigest()[:20]


def source_logical_condition(
    *,
    subject: str,
    generation_id: str,
    evidence_ref: str,
    statement: str,
    severity: LogicalSeverity,
) -> SourceLogicalCondition:
    """Structure an authoritative source condition before it reaches the writer.

    The source adapter recognizes only the explicit disjunction needed by the
    stored thesis contract. Output prose is never parsed by this module.
    """

    compact = " ".join(statement.split())
    branches = tuple(part.strip() for part in _SOURCE_ANY_OF.split(compact) if part.strip())
    root_id = _stable_id("logical-condition", subject, generation_id, evidence_ref)
    if len(branches) <= 1:
        expression = SourceLogicalExpression(
            condition_id=root_id,
            type=LogicalOperator.LEAF,
            statement=compact,
        )
    else:
        expression = SourceLogicalExpression(
            condition_id=root_id,
            type=LogicalOperator.ANY_OF,
            children=tuple(
                SourceLogicalExpression(
                    condition_id=_stable_id(root_id, index, branch),
                    type=LogicalOperator.LEAF,
                    statement=branch,
                )
                for index, branch in enumerate(branches, start=1)
            ),
        )
    return SourceLogicalCondition(
        subject=subject,
        generation_id=generation_id,
        source_condition_ref=root_id,
        severity=severity,
        expression=expression,
    )


def source_claim_expression(expression: SourceLogicalExpression) -> ClaimLogicalExpression:
    if expression.type == LogicalOperator.LEAF:
        return ClaimLogicalExpression(
            type=LogicalOperator.LEAF,
            condition_ref=expression.condition_id,
        )
    return ClaimLogicalExpression(
        type=expression.type,
        children=tuple(source_claim_expression(child) for child in expression.children),
    )


def _leaf_refs(expression: ClaimLogicalExpression) -> tuple[str, ...]:
    if expression.type == LogicalOperator.LEAF:
        return (expression.condition_ref,) if expression.condition_ref else ()
    return tuple(ref for child in expression.children for ref in _leaf_refs(child))


def _source_leaf_refs(expression: SourceLogicalExpression) -> tuple[str, ...]:
    if expression.type == LogicalOperator.LEAF:
        return (expression.condition_id,)
    return tuple(ref for child in expression.children for ref in _source_leaf_refs(child))


def _signature(expression: ClaimLogicalExpression) -> tuple[object, ...]:
    if expression.type == LogicalOperator.LEAF:
        return (LogicalOperator.LEAF, expression.condition_ref)
    return (
        expression.type,
        tuple(sorted((_signature(child) for child in expression.children), key=str)),
    )


def _source_signature(expression: SourceLogicalExpression) -> tuple[object, ...]:
    if expression.type == LogicalOperator.LEAF:
        return (LogicalOperator.LEAF, expression.condition_id)
    return (
        expression.type,
        tuple(sorted((_source_signature(child) for child in expression.children), key=str)),
    )


def logical_condition_errors(
    *,
    subject: str,
    generation_id: str,
    source_conditions: Iterable[SourceLogicalCondition],
    claim: ClaimLogicalCondition | None,
) -> tuple[str, ...]:
    source_values = tuple(source_conditions)
    sources = {
        item.source_condition_ref: item
        for item in source_values
        if item.subject == subject and item.generation_id == generation_id
    }
    if source_values and not sources:
        return ("logical_condition_owner_mismatch",)
    if not sources:
        return ()
    if claim is None:
        return ("logical_condition_metadata_missing",)
    source = sources.get(claim.source_condition_ref)
    if source is None:
        return ("logical_condition_source_ref_unknown",)
    errors: list[str] = []
    if claim.severity != source.severity:
        errors.append("logical_condition_severity_mutation")
    source_refs = set(_source_leaf_refs(source.expression))
    claim_refs = _leaf_refs(claim.expression)
    if not claim_refs or len(claim_refs) != len(set(claim_refs)):
        errors.append("logical_condition_branch_identity_invalid")
    elif not set(claim_refs).issubset(source_refs):
        errors.append("logical_condition_cross_condition_branch")

    if claim.coverage_mode == LogicalCoverageMode.FULL:
        if _signature(claim.expression) != _source_signature(source.expression):
            errors.append("logical_condition_full_semantic_mismatch")
    elif claim.coverage_mode == LogicalCoverageMode.NON_EXHAUSTIVE_EXAMPLE:
        if claim.expression.type != LogicalOperator.LEAF or len(claim_refs) != 1:
            errors.append("logical_condition_example_must_reference_one_branch")
    elif set(claim_refs) == source_refs:
        errors.append("logical_condition_partial_claims_full_coverage")
    return tuple(dict.fromkeys(errors))
