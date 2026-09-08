from __future__ import annotations

import hashlib
import json
from collections.abc import Iterable, Mapping, Sequence
from decimal import Decimal

from app.services.cash_flow_capital_efficiency_service import (
    FactType,
    FinancialFact,
    Metric,
)
from app.services.fact_consumer_scope_service import (
    FactConsumer,
    with_fact_consumer_scopes,
)


CONTRACT_VERSION = "canonical-financial-lineage-projection-v1"
LINEAGE_FIELD = "canonical_financial_lineage"
SUPPORT_ONLY_FIELD = "financial_context_support_only"

_FACT_TYPE_BY_METRIC = {
    Metric.OCF: "cash_flow_ocf",
    Metric.CAPEX: "cash_flow_ppe_capex",
    Metric.FCF: "cash_flow_fcf_ppe",
    Metric.CASH_AND_CASH_EQUIVALENTS: "balance_sheet_cash_and_cash_equivalents",
    Metric.CASH_AND_RESTRICTED_CASH: "balance_sheet_cash_and_restricted_cash",
    Metric.RESTRICTED_CASH_CURRENT: "balance_sheet_restricted_cash_current",
    Metric.RESTRICTED_CASH_NONCURRENT: "balance_sheet_restricted_cash_noncurrent",
    Metric.SHORT_TERM_BORROWINGS: "balance_sheet_short_term_borrowings",
    Metric.CURRENT_PORTION_LONG_TERM_DEBT: (
        "balance_sheet_current_portion_long_term_debt"
    ),
    Metric.CURRENT_INTEREST_BEARING_DEBT: (
        "balance_sheet_current_interest_bearing_debt"
    ),
    Metric.LONG_TERM_BORROWINGS: "balance_sheet_long_term_borrowings",
    Metric.BONDS_PAYABLE_CURRENT: "balance_sheet_bonds_payable_current",
    Metric.BONDS_PAYABLE_NONCURRENT: "balance_sheet_bonds_payable_noncurrent",
    Metric.NOTES_PAYABLE_CURRENT: "balance_sheet_notes_payable_current",
    Metric.NOTES_PAYABLE_NONCURRENT: "balance_sheet_notes_payable_noncurrent",
    Metric.CONVERTIBLE_DEBT_CURRENT: "balance_sheet_convertible_debt_current",
    Metric.CONVERTIBLE_DEBT_NONCURRENT: (
        "balance_sheet_convertible_debt_noncurrent"
    ),
    Metric.LEASE_LIABILITIES_CURRENT: "balance_sheet_lease_liabilities_current",
    Metric.LEASE_LIABILITIES_NONCURRENT: (
        "balance_sheet_lease_liabilities_noncurrent"
    ),
    Metric.INTEREST_BEARING_DEBT_TOTAL: (
        "balance_sheet_interest_bearing_debt_total"
    ),
    Metric.NET_DEBT: "balance_sheet_net_debt",
    Metric.INVENTORY: "balance_sheet_inventory",
    Metric.INVENTORY_COMPONENT: "balance_sheet_inventory_component",
    Metric.TRADE_AR: "balance_sheet_trade_receivables",
    Metric.BROAD_AR: "balance_sheet_broad_receivables_context",
    Metric.TRADE_AP: "balance_sheet_trade_payables",
    Metric.BROAD_AP: "balance_sheet_broad_payables_context",
    Metric.CURRENT_ASSETS: "balance_sheet_current_assets",
    Metric.CURRENT_LIABILITIES: "balance_sheet_current_liabilities",
    Metric.CONTRACT_ASSETS: "balance_sheet_contract_assets_context",
    Metric.CONTRACT_LIABILITIES: "balance_sheet_contract_liabilities_context",
    Metric.BALANCE_DELTA: "balance_sheet_working_capital_balance_delta",
}

_CASH_FLOW_METRICS = frozenset({Metric.OCF, Metric.CAPEX, Metric.FCF})


def _canonical_bytes(value: object) -> bytes:
    return json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
        default=str,
    ).encode("utf-8")


def _numeric_value(value: Decimal) -> int | float:
    return int(value) if value == value.to_integral_value() else float(value)


def canonical_lineage_projection(fact: FinancialFact) -> dict[str, object]:
    """Project existing canonical lineage without deriving or repairing it."""
    payload: dict[str, object] = {
        "contract": CONTRACT_VERSION,
        "fact_id": fact.fact_id,
        "metric": fact.metric.value,
        "value": str(fact.value),
        "currency": fact.currency,
        "period_start": (
            None
            if fact.period.period_type.value == "POINT_IN_TIME"
            else fact.period.start.isoformat()
        ),
        "period_end": fact.period.end.isoformat(),
        "period_type": fact.period.period_type.value,
        "fiscal_year": fact.period.fiscal_year,
        "fiscal_quarter": fact.period.fiscal_quarter,
        "entity_scope": fact.entity_scope,
        "statement_basis": fact.statement_basis,
        "capex_scope": fact.capex_scope.value if fact.capex_scope else None,
        "canonical_fact_type": fact.fact_type.value,
        "reported_or_derived": fact.reported_or_derived,
        "issuer_id": fact.issuer_id,
        "unit": fact.unit,
        "unit_scale": 1,
        "semantic_mapping": fact.semantic_mapping,
        "derivation_formula": fact.derivation_formula,
        "derivation_version": fact.derivation_version,
        "ordered_input_fact_ids": list(fact.input_fact_ids),
        "ordered_input_source_refs": [
            f"stock.fact_catalog.{fact_id}" for fact_id in fact.input_fact_ids
        ],
        "source_provider": fact.source_provider,
        "source_document_id": fact.source_document_id,
        "source_document_type": fact.source_document_type,
        "filing_date": fact.filing_date.isoformat(),
        "source_occurrence_id": fact.source_occurrence_id,
        "source_semantic": fact.source_semantic,
        "raw_payload_sha256": fact.raw_payload_sha256,
    }
    if fact.balance_scope is not None:
        payload["balance_scope"] = fact.balance_scope
    if fact.net_gross_scope is not None:
        payload["net_gross_scope"] = fact.net_gross_scope
    if fact.comparison_kind is not None:
        payload["comparison_kind"] = fact.comparison_kind
    payload["lineage_sha256"] = lineage_projection_digest(payload)
    return payload


def lineage_projection_digest(payload: Mapping[str, object]) -> str:
    identity = dict(payload)
    identity.pop("lineage_sha256", None)
    return hashlib.sha256(_canonical_bytes(identity)).hexdigest()


def lineage_projection_is_complete(fact: FinancialFact) -> bool:
    if fact.fact_type == FactType.REPORTED:
        return not fact.input_fact_ids
    return bool(
        fact.derivation_formula
        and fact.derivation_version
        and fact.input_fact_ids
    )


def projection_closure(
    facts: Iterable[FinancialFact],
    *,
    selected_fact_ids: Sequence[str],
    prior_fact_ids: Sequence[str] = (),
) -> tuple[FinancialFact, ...]:
    """Return the exact canonical prior/input closure, deduplicated by fact ID."""
    grouped: dict[str, list[FinancialFact]] = {}
    for fact in facts:
        grouped.setdefault(fact.fact_id, []).append(fact)
    by_id = {
        fact_id: values[0]
        for fact_id, values in grouped.items()
        if all(item == values[0] for item in values)
    }
    queue = list(dict.fromkeys([*selected_fact_ids, *prior_fact_ids]))
    selected: dict[str, FinancialFact] = {}
    while queue:
        fact_id = queue.pop(0)
        fact = by_id.get(fact_id)
        if fact is None or fact_id in selected:
            continue
        selected[fact_id] = fact
        queue.extend(
            input_id
            for input_id in fact.input_fact_ids
            if input_id not in selected
        )
    return tuple(selected[fact_id] for fact_id in sorted(selected))


def _fact_catalog_entry(
    fact: FinancialFact,
    *,
    context_id: str | None,
    support_only: bool,
) -> dict[str, object]:
    row: dict[str, object] = {
        "fact_id": fact.fact_id,
        "fact_type": _FACT_TYPE_BY_METRIC[fact.metric],
        "as_of_date": fact.period.end.isoformat(),
        "source": (
            "canonical_cash_flow_fact"
            if fact.metric in _CASH_FLOW_METRICS
            else "canonical_financial_fact"
        ),
        "fields": {
            "value": _numeric_value(fact.value),
            "currency": fact.currency,
            "period_start": (
                None
                if fact.period.period_type.value == "POINT_IN_TIME"
                else fact.period.start.isoformat()
            ),
            "period_end": fact.period.end.isoformat(),
            "period_type": fact.period.period_type.value,
            "fiscal_year": str(fact.period.fiscal_year),
            "fiscal_quarter": (
                str(fact.period.fiscal_quarter)
                if fact.period.fiscal_quarter is not None
                else None
            ),
            "entity_scope": fact.entity_scope,
            "statement_basis": fact.statement_basis,
            "capex_scope": fact.capex_scope.value if fact.capex_scope else None,
            "input_fact_ids": list(fact.input_fact_ids),
            "cash_flow_user_visible_context_id": context_id,
        },
        LINEAGE_FIELD: canonical_lineage_projection(fact),
        SUPPORT_ONLY_FIELD: support_only,
        "prose_eligible": not support_only,
        "interpretation_eligible": not support_only,
        "numeric_registry_eligible": not support_only,
    }
    fields = row["fields"]
    assert isinstance(fields, dict)
    if fact.balance_scope is not None:
        fields["balance_scope"] = fact.balance_scope
    if fact.net_gross_scope is not None:
        fields["net_gross_scope"] = fact.net_gross_scope
    if fact.comparison_kind is not None:
        fields["comparison_kind"] = fact.comparison_kind
    if support_only:
        return with_fact_consumer_scopes(
            row,
            (FactConsumer.ARCHIVE_ONLY,),
            user_visible=False,
        )
    return row


def project_financial_fact_catalog(
    visible_facts: Sequence[FinancialFact],
    *,
    context_id: str | None,
    lineage_facts: Sequence[FinancialFact] = (),
) -> list[dict[str, object]]:
    """Project visible facts plus non-consuming support rows for the adapter."""
    visible_by_id = {fact.fact_id: fact for fact in visible_facts}
    support_by_id = {
        fact.fact_id: fact
        for fact in lineage_facts
        if fact.fact_id not in visible_by_id
    }
    rows = [
        _fact_catalog_entry(
            fact,
            context_id=context_id,
            support_only=False,
        )
        for fact in visible_facts
    ]
    rows.extend(
        _fact_catalog_entry(
            support_by_id[fact_id],
            context_id=context_id,
            support_only=True,
        )
        for fact_id in sorted(support_by_id)
    )
    return rows


def adapter_projection_rows(
    all_rows: Sequence[Mapping[str, object]],
    visible_rows: Sequence[Mapping[str, object]],
) -> list[dict[str, object]]:
    """Expose only explicit archive support rows to the internal adapter lookup."""
    output = [dict(row) for row in visible_rows]
    seen = {str(row.get("fact_id") or "") for row in output}
    for row in all_rows:
        fact_id = str(row.get("fact_id") or "")
        if (
            fact_id
            and fact_id not in seen
            and row.get(SUPPORT_ONLY_FIELD) is True
            and row.get("consumer_scopes") == [FactConsumer.ARCHIVE_ONLY.value]
            and row.get("source")
            in {"canonical_cash_flow_fact", "canonical_financial_fact"}
        ):
            output.append(dict(row))
            seen.add(fact_id)
    return output
