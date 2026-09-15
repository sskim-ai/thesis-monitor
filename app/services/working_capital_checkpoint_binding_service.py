from __future__ import annotations

from collections.abc import Mapping, Sequence
import re

from pydantic import Field

from app.services.cross_market_decision_engine_service import FrozenModel


CONTRACT_VERSION = "working-capital-checkpoint-typed-ref-binding-v1"
VIEW_CONTRACT_VERSION = "working-capital-checkpoint-binding-view-v1"

# This is the existing checkpoint surface from
# directional_financial_context_m12g._CHECKPOINT_PATH_MARKERS.
CHECKPOINT_FIELDS = (
    "core_investment_judgment",
    "dominant_evidence",
    "risk_context",
    "business_reevaluation_up",
    "business_reevaluation_down",
    "fundamental_new_buyer.confirmation_business_condition",
    "fundamental_holder.business_invalidation_condition",
    "buy_drivers",
    "sell_drivers",
)

# Stage 2 owns the two fundamental stance conditions. Keeping their fully
# qualified names out of the default model view preserves the Stage 1 boundary;
# each stage receives only the checkpoint fields it can write.
MODEL_CHECKPOINT_FIELDS = tuple(
    field for field in CHECKPOINT_FIELDS if not field.startswith("fundamental_")
)
STAGE2_MODEL_CHECKPOINT_FIELDS = tuple(
    field for field in CHECKPOINT_FIELDS if field.startswith("fundamental_")
)

_METRIC_CUES = {
    "inventory": re.compile(
        r"(?:재고)|(?<![A-Za-z0-9_])(?:inventory|inventories)(?![A-Za-z0-9_])",
        re.IGNORECASE,
    ),
    "trade_accounts_receivable": re.compile(
        r"(?:매출채권)|(?<![A-Za-z0-9_])(?:trade\s+(?:accounts?\s+)?receivables?|"
        r"accounts?\s+receivables?|receivables?)(?![A-Za-z0-9_])",
        re.IGNORECASE,
    ),
    "trade_accounts_payable": re.compile(
        r"(?:매입채무)|(?<![A-Za-z0-9_])(?:trade\s+(?:accounts?\s+)?payables?|"
        r"accounts?\s+payables?|payables?)(?![A-Za-z0-9_])",
        re.IGNORECASE,
    ),
}
_GENERIC_WORKING_CAPITAL_CUE = re.compile(
    r"(?:운전자본)|(?<![A-Za-z0-9_])working(?:\s+|-)capital(?![A-Za-z0-9_])",
    re.IGNORECASE,
)


class WorkingCapitalCheckpointBindingItem(FrozenModel):
    alias: str
    canonical_ref: str | None = None
    metric: str
    evidence_kind: str
    comparison_kind: str | None = None
    period_type: str | None = None


class WorkingCapitalCheckpointBindingView(FrozenModel):
    contract: str = VIEW_CONTRACT_VERSION
    ticker: str
    selected_working_capital_items: tuple[
        WorkingCapitalCheckpointBindingItem, ...
    ] = ()
    metric_to_typed_aliases: dict[str, tuple[str, ...]] = Field(
        default_factory=dict
    )
    metric_to_canonical_refs: dict[str, tuple[str, ...]] = Field(
        default_factory=dict
    )
    checkpoint_fields: tuple[str, ...] = CHECKPOINT_FIELDS

    def model_context(
        self,
        *,
        checkpoint_fields: Sequence[str] = MODEL_CHECKPOINT_FIELDS,
    ) -> dict[str, object]:
        projected_fields = tuple(checkpoint_fields)
        unsupported = sorted(set(projected_fields) - set(CHECKPOINT_FIELDS))
        if unsupported:
            raise ValueError(
                f"unsupported_working_capital_checkpoint_fields:{unsupported}"
            )
        return {
            "contract": self.contract,
            "selected_working_capital_items": [
                {
                    "alias": item.alias,
                    "metric": item.metric,
                    "evidence_kind": item.evidence_kind,
                    "comparison_kind": item.comparison_kind,
                    "period_type": item.period_type,
                }
                for item in self.selected_working_capital_items
            ],
            "metric_to_typed_aliases": {
                metric: list(aliases)
                for metric, aliases in self.metric_to_typed_aliases.items()
            },
            "checkpoint_fields": list(projected_fields),
        }

    def stage2_model_context(self) -> dict[str, object]:
        return self.model_context(
            checkpoint_fields=STAGE2_MODEL_CHECKPOINT_FIELDS,
        )


def build_working_capital_checkpoint_binding_view(
    *,
    ticker: str,
    context: Mapping[str, object],
    alias_to_canonical_ref: Mapping[str, str] | None = None,
) -> WorkingCapitalCheckpointBindingView:
    financial = context.get("financial_decision_context")
    if not isinstance(financial, Mapping):
        return WorkingCapitalCheckpointBindingView(ticker=ticker)
    raw_items = financial.get("evidence_items")
    if not isinstance(raw_items, Sequence) or isinstance(raw_items, (str, bytes)):
        return WorkingCapitalCheckpointBindingView(ticker=ticker)

    canonical = alias_to_canonical_ref or {}
    items: list[WorkingCapitalCheckpointBindingItem] = []
    for raw in raw_items:
        if not isinstance(raw, Mapping):
            continue
        metric = str(raw.get("metric") or "")
        if metric not in _METRIC_CUES:
            continue
        alias = str(raw.get("evidence_id") or "")
        if not alias:
            continue
        comparison = raw.get("comparison")
        period = raw.get("period")
        items.append(
            WorkingCapitalCheckpointBindingItem(
                alias=alias,
                canonical_ref=canonical.get(alias),
                metric=metric,
                evidence_kind="TYPED_FINANCIAL",
                comparison_kind=(
                    str(comparison.get("kind"))
                    if isinstance(comparison, Mapping) and comparison.get("kind")
                    else None
                ),
                period_type=(
                    str(period.get("type"))
                    if isinstance(period, Mapping) and period.get("type")
                    else None
                ),
            )
        )

    items.sort(key=lambda item: (item.metric, item.alias))
    aliases: dict[str, list[str]] = {}
    canonical_refs: dict[str, list[str]] = {}
    for item in items:
        aliases.setdefault(item.metric, []).append(item.alias)
        if item.canonical_ref is not None:
            canonical_refs.setdefault(item.metric, []).append(item.canonical_ref)
    return WorkingCapitalCheckpointBindingView(
        ticker=ticker,
        selected_working_capital_items=tuple(items),
        metric_to_typed_aliases={
            metric: tuple(sorted(values)) for metric, values in sorted(aliases.items())
        },
        metric_to_canonical_refs={
            metric: tuple(sorted(values))
            for metric, values in sorted(canonical_refs.items())
        },
    )


def attach_working_capital_checkpoint_binding_view(
    context: Mapping[str, object],
    view: WorkingCapitalCheckpointBindingView,
) -> dict[str, object]:
    result = dict(context)
    if view.selected_working_capital_items:
        result["working_capital_checkpoint_binding"] = view.model_context()
    return result


def _claim_rows(value: object, path: str = "") -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    if isinstance(value, Mapping):
        text = value.get("text")
        refs = value.get("evidence_refs")
        if (
            isinstance(text, str)
            and isinstance(refs, Sequence)
            and not isinstance(refs, (str, bytes))
        ):
            rows.append(
                {
                    "path": path,
                    "text": text,
                    "evidence_refs": tuple(str(ref) for ref in refs),
                }
            )
        for condition_key, refs_key in (
            (
                "confirmation_business_condition",
                "confirmation_business_condition_refs",
            ),
            (
                "business_invalidation_condition",
                "business_invalidation_condition_refs",
            ),
        ):
            condition = value.get(condition_key)
            condition_refs = value.get(refs_key)
            if (
                isinstance(condition, str)
                and isinstance(condition_refs, Sequence)
                and not isinstance(condition_refs, (str, bytes))
            ):
                condition_path = f"{path}.{condition_key}" if path else condition_key
                rows.append(
                    {
                        "path": condition_path,
                        "text": condition,
                        "evidence_refs": tuple(
                            str(ref) for ref in condition_refs
                        ),
                    }
                )
        for key, child in value.items():
            child_path = f"{path}.{key}" if path else str(key)
            rows.extend(_claim_rows(child, child_path))
    elif isinstance(value, Sequence) and not isinstance(value, (str, bytes)):
        for index, child in enumerate(value):
            rows.extend(_claim_rows(child, f"{path}[{index}]"))
    return rows


def working_capital_metrics_in_text(text: str) -> tuple[str, ...]:
    return tuple(
        metric for metric, pattern in _METRIC_CUES.items() if pattern.search(text)
    )


def _is_checkpoint_path(path: str) -> bool:
    return any(marker in path for marker in CHECKPOINT_FIELDS)


def validate_working_capital_checkpoint_bindings(
    candidate: object,
    view: WorkingCapitalCheckpointBindingView,
) -> dict[str, object]:
    payload = (
        candidate.model_dump(mode="json")
        if hasattr(candidate, "model_dump")
        else candidate
    )
    selected_metrics = set(view.metric_to_typed_aliases)
    identity_by_metric = {
        metric: set(view.metric_to_typed_aliases.get(metric, ()))
        | set(view.metric_to_canonical_refs.get(metric, ()))
        for metric in selected_metrics
    }
    all_typed_identities = set().union(*identity_by_metric.values()) if identity_by_metric else set()
    rows: list[dict[str, object]] = []
    for claim in _claim_rows(payload):
        path = str(claim["path"])
        if not _is_checkpoint_path(path):
            continue
        text = str(claim["text"])
        detected_metrics = set(working_capital_metrics_in_text(text))
        required_metrics = detected_metrics & selected_metrics
        generic = bool(_GENERIC_WORKING_CAPITAL_CUE.search(text))
        if not required_metrics and not (generic and selected_metrics):
            continue
        refs = set(claim["evidence_refs"])
        directly_bound = refs & all_typed_identities
        missing_metrics = {
            metric
            for metric in required_metrics
            if not refs.intersection(identity_by_metric[metric])
        }
        generic_grounded = bool(directly_bound) if generic and not required_metrics else True
        grounded = not missing_metrics and generic_grounded
        required_aliases = {
            alias
            for metric in required_metrics
            for alias in view.metric_to_typed_aliases.get(metric, ())
        }
        if generic and not required_metrics:
            required_aliases = {
                alias
                for aliases in view.metric_to_typed_aliases.values()
                for alias in aliases
            }
        narrative_refs = refs - all_typed_identities
        rows.append(
            {
                "ticker": view.ticker,
                "checkpoint_field": path,
                "claim_text": text,
                "metric_cues_detected": sorted(detected_metrics),
                "generic_working_capital_cue": generic,
                "required_metrics": sorted(required_metrics),
                "required_typed_aliases": sorted(required_aliases),
                "actual_claim_refs": sorted(refs),
                "typed_refs_directly_bound": sorted(directly_bound),
                "narrative_refs_directly_bound": sorted(narrative_refs),
                "missing_metrics": sorted(missing_metrics),
                "claim_grounded": grounded,
                "metric_specific_mismatch": bool(missing_metrics and directly_bound),
                "narrative_only_substitution": bool(
                    not grounded and narrative_refs and not directly_bound
                ),
                "validation_result": "PASS" if grounded else "FAIL",
            }
        )

    failures = [row for row in rows if not row["claim_grounded"]]
    errors = (
        ("working_capital_checkpoint_typed_ref_binding_failure",)
        if failures
        else ()
    )
    return {
        "contract": CONTRACT_VERSION,
        "view_contract": view.contract,
        "ticker": view.ticker,
        "selected_working_capital_metrics": sorted(selected_metrics),
        "selected_typed_aliases": sorted(
            alias
            for aliases in view.metric_to_typed_aliases.values()
            for alias in aliases
        ),
        "checkpoint_fields": list(view.checkpoint_fields),
        "working_capital_checkpoint_count": len(rows),
        "grounded_working_capital_checkpoint_count": len(rows) - len(failures),
        "working_capital_grounding_failure_count": len(failures),
        "metric_specific_ref_mismatch_count": sum(
            bool(row["metric_specific_mismatch"]) for row in rows
        ),
        "narrative_only_substitution_count": sum(
            bool(row["narrative_only_substitution"]) for row in rows
        ),
        "unsafe_working_capital_auto_direction_count": 0,
        "errors": list(errors),
        "rows": rows,
        "valid": not failures,
        "status": "PASS" if not failures else "FAIL",
    }
