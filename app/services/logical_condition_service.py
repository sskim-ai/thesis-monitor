from __future__ import annotations

import hashlib
import re
from enum import StrEnum
from typing import Annotated, Iterable, Literal, TypeAlias

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


class CheckpointMetric(StrEnum):
    OCF = "OCF"
    PPE_CAPEX = "PPE_CAPEX"
    FCF = "FCF"
    ROIC = "ROIC"
    CCC = "CCC"
    DSO = "DSO"
    DPO = "DPO"


_CHECKPOINT_METRIC = re.compile(
    r"(?<![A-Za-z0-9_])(?P<metric>ROIC|CCC|DSO|DPO|OCF|FCF|PPE[ _-]?CAPEX)"
    r"(?![A-Za-z0-9_])",
    re.IGNORECASE,
)


def checkpoint_metric_refs(value: str) -> tuple[CheckpointMetric, ...]:
    normalized = {
        match.group("metric").upper().replace(" ", "_").replace("-", "_")
        for match in _CHECKPOINT_METRIC.finditer(value)
    }
    return tuple(metric for metric in CheckpointMetric if metric.value in normalized)


class SourceLogicalLeaf(FrozenModel):
    condition_id: str = Field(min_length=1)
    type: Literal[LogicalOperator.LEAF] = LogicalOperator.LEAF
    statement: str | None = None


class SourceLogicalComposite(FrozenModel):
    condition_id: str = Field(min_length=1)
    type: Literal[LogicalOperator.ANY_OF, LogicalOperator.ALL_OF]
    children: tuple[SourceLogicalExpression, ...] = Field(min_length=2)


SourceLogicalExpression: TypeAlias = Annotated[
    SourceLogicalLeaf | SourceLogicalComposite,
    Field(discriminator="type"),
]


class SourceLogicalCondition(FrozenModel):
    contract: str = CONTRACT_VERSION
    subject: str = Field(min_length=1)
    generation_id: str = Field(min_length=1)
    source_condition_ref: str = Field(min_length=1)
    severity: LogicalSeverity
    metric_refs: tuple[CheckpointMetric, ...] = ()
    expression: SourceLogicalExpression

    @model_validator(mode="after")
    def validate_root_identity(self) -> SourceLogicalCondition:
        if self.source_condition_ref != self.expression.condition_id:
            raise ValueError("logical_source_root_identity_mismatch")
        return self


class ClaimLogicalLeaf(FrozenModel):
    type: Literal[LogicalOperator.LEAF] = LogicalOperator.LEAF
    leaf_ref: str = Field(min_length=1)


class ClaimLogicalComposite(FrozenModel):
    type: Literal[LogicalOperator.ANY_OF, LogicalOperator.ALL_OF]
    children: tuple[ClaimLogicalExpression, ...] = Field(min_length=2)


ClaimLogicalExpression: TypeAlias = Annotated[
    ClaimLogicalLeaf | ClaimLogicalComposite,
    Field(discriminator="type"),
]


SourceLogicalComposite.model_rebuild(
    _types_namespace={"SourceLogicalExpression": SourceLogicalExpression}
)
ClaimLogicalComposite.model_rebuild(
    _types_namespace={"ClaimLogicalExpression": ClaimLogicalExpression}
)


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
        expression: SourceLogicalExpression = SourceLogicalLeaf(
            condition_id=root_id,
            statement=compact,
        )
    else:
        expression = SourceLogicalComposite(
            condition_id=root_id,
            type=LogicalOperator.ANY_OF,
            children=tuple(
                SourceLogicalLeaf(
                    condition_id=_stable_id(root_id, index, branch),
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
        metric_refs=checkpoint_metric_refs(compact),
        expression=expression,
    )


def source_claim_expression(expression: SourceLogicalExpression) -> ClaimLogicalExpression:
    if expression.type == LogicalOperator.LEAF:
        return ClaimLogicalLeaf(leaf_ref=expression.condition_id)
    return ClaimLogicalComposite(
        type=expression.type,
        children=tuple(source_claim_expression(child) for child in expression.children),
    )


def _leaf_refs(expression: ClaimLogicalExpression) -> tuple[str, ...]:
    if expression.type == LogicalOperator.LEAF:
        return (expression.leaf_ref,)
    return tuple(ref for child in expression.children for ref in _leaf_refs(child))


def _source_leaf_refs(expression: SourceLogicalExpression) -> tuple[str, ...]:
    if expression.type == LogicalOperator.LEAF:
        return (expression.condition_id,)
    return tuple(ref for child in expression.children for ref in _source_leaf_refs(child))


def _signature(expression: ClaimLogicalExpression) -> tuple[object, ...]:
    if expression.type == LogicalOperator.LEAF:
        return (LogicalOperator.LEAF, expression.leaf_ref)
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


def logical_expression_is_composite(expression: SourceLogicalExpression) -> bool:
    return isinstance(expression, SourceLogicalComposite)
