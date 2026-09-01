from __future__ import annotations

from collections.abc import Sequence
from datetime import date
from enum import StrEnum

from pydantic import BaseModel, ConfigDict


CONTRACT_VERSION = "technical-feature-dependency-registry-v1"


class DependencyKind(StrEnum):
    FINITE = "FINITE"
    RECURSIVE_FULL_HISTORY = "RECURSIVE_FULL_HISTORY"


class DependencyClassification(StrEnum):
    SAFE = "SAFE"
    SAFE_INDEPENDENT_OF_BAD_ROW = "SAFE_INDEPENDENT_OF_BAD_ROW"
    SAFE_AFTER_PROVEN_WARMUP = "SAFE_AFTER_PROVEN_WARMUP"
    UNSAFE_DEPENDS_ON_BAD_ROW = "UNSAFE_DEPENDS_ON_BAD_ROW"
    UNAVAILABLE_OTHER_REASON = "UNAVAILABLE_OTHER_REASON"


class FrozenModel(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")


class FeatureDependencyRule(FrozenModel):
    semantic_family: str
    dependency_kind: DependencyKind
    required_bars_source: str
    recursive_initialization: str | None = None


class FeatureDependencyAssessment(FrozenModel):
    contract: str = CONTRACT_VERSION
    semantic: str
    dependency_kind: DependencyKind
    classification: DependencyClassification
    required_bars: int
    dependency_start: str | None = None
    dependency_end: str | None = None
    dependency_bar_count: int = 0
    blocking_invalid_dates: tuple[str, ...] = ()


_RECURSIVE_PREFIXES = (
    "ema_",
    "macd_",
    "rsi_",
    "atr_",
    "adx_",
    "plus_di_",
    "minus_di_",
)
_RECURSIVE_EXACT = frozenset({"dmi_state", "obv"})


def dependency_rule(semantic: str) -> FeatureDependencyRule:
    if semantic in _RECURSIVE_EXACT or semantic.startswith(_RECURSIVE_PREFIXES):
        return FeatureDependencyRule(
            semantic_family=semantic,
            dependency_kind=DependencyKind.RECURSIVE_FULL_HISTORY,
            required_bars_source="all normalized history used by the existing seeded recursion",
            recursive_initialization="existing SMA seed followed by EMA/Wilder/cumulative recursion",
        )
    return FeatureDependencyRule(
        semantic_family=semantic,
        dependency_kind=DependencyKind.FINITE,
        required_bars_source="TechnicalFeatureFact.minimum_history",
    )


def assess_feature_dependency(
    *,
    semantic: str,
    minimum_history: int,
    row_dates: Sequence[date],
    invalid_dates: Sequence[date],
) -> FeatureDependencyAssessment:
    rule = dependency_rule(semantic)
    if not row_dates or len(row_dates) < minimum_history:
        return FeatureDependencyAssessment(
            semantic=semantic,
            dependency_kind=rule.dependency_kind,
            classification=DependencyClassification.UNAVAILABLE_OTHER_REASON,
            required_bars=minimum_history,
        )
    start_index = (
        0
        if rule.dependency_kind == DependencyKind.RECURSIVE_FULL_HISTORY
        else len(row_dates) - minimum_history
    )
    start = row_dates[start_index]
    end = row_dates[-1]
    blocked = tuple(
        sorted({value.isoformat() for value in invalid_dates if start <= value <= end})
    )
    if blocked:
        classification = DependencyClassification.UNSAFE_DEPENDS_ON_BAD_ROW
    elif invalid_dates:
        classification = DependencyClassification.SAFE_INDEPENDENT_OF_BAD_ROW
    else:
        classification = DependencyClassification.SAFE
    return FeatureDependencyAssessment(
        semantic=semantic,
        dependency_kind=rule.dependency_kind,
        classification=classification,
        required_bars=minimum_history,
        dependency_start=start.isoformat(),
        dependency_end=end.isoformat(),
        dependency_bar_count=len(row_dates) - start_index,
        blocking_invalid_dates=blocked,
    )


def dependency_registry() -> tuple[FeatureDependencyRule, ...]:
    return (
        FeatureDependencyRule(
            semantic_family="close/returns/range/drawdown/SMA/ROC/stochastic/Bollinger/volume ratio/CMF/MFI/Donchian",
            dependency_kind=DependencyKind.FINITE,
            required_bars_source="TechnicalFeatureFact.minimum_history",
        ),
        FeatureDependencyRule(
            semantic_family="EMA/MACD",
            dependency_kind=DependencyKind.RECURSIVE_FULL_HISTORY,
            required_bars_source="all normalized history",
            recursive_initialization="SMA seed followed by recursive EMA",
        ),
        FeatureDependencyRule(
            semantic_family="RSI/ATR/ADX/DMI",
            dependency_kind=DependencyKind.RECURSIVE_FULL_HISTORY,
            required_bars_source="all normalized history",
            recursive_initialization="Wilder seed and smoothing",
        ),
        FeatureDependencyRule(
            semantic_family="OBV",
            dependency_kind=DependencyKind.RECURSIVE_FULL_HISTORY,
            required_bars_source="all normalized history",
            recursive_initialization="cumulative signed volume",
        ),
    )
