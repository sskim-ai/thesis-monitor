from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from typing import Iterable, Mapping

from app.services.cash_flow_capital_efficiency_service import (
    EligibilityStatus,
    FactType,
    FinancialFact,
    Metric,
    PeriodType,
    derive_fcf,
    derive_qtd_from_ytd,
    derive_ttm,
    q1_ytd_as_qtd,
)
from app.services.official_cash_flow_service import (
    CanonicalizationBatch,
    canonicalize_sec_companyfacts,
)


DERIVATION_FISCAL_YEAR_LOOKBACK = 2


@dataclass(frozen=True)
class CashFlowCoreSnapshot:
    status: EligibilityStatus
    facts: tuple[FinancialFact, ...]
    latest_fcf: FinancialFact | None
    latest_qtd_fcf: FinancialFact | None
    latest_ttm_fcf: FinancialFact | None
    denial_reasons: tuple[str, ...]
    cautions: tuple[str, ...]
    source_audit: dict[str, object]


def _fact_sort_key(fact: FinancialFact) -> tuple[object, ...]:
    return (
        fact.period.end,
        fact.period.start,
        fact.filing_date,
        fact.fact_id,
    )


def _latest(values: Iterable[FinancialFact]) -> FinancialFact | None:
    facts = list(values)
    return max(facts, key=_fact_sort_key) if facts else None


def _same_period_source_key(fact: FinancialFact) -> tuple[object, ...]:
    return (
        fact.issuer_id,
        fact.period,
        fact.currency,
        fact.unit,
        fact.entity_scope,
        fact.statement_basis,
        fact.source_document_id,
    )


def _period_derivations(reported: tuple[FinancialFact, ...]) -> tuple[FinancialFact, ...]:
    derived: dict[str, FinancialFact] = {}
    by_metric: dict[Metric, list[FinancialFact]] = {Metric.OCF: [], Metric.CAPEX: []}
    for fact in reported:
        if fact.metric in by_metric:
            by_metric[fact.metric].append(fact)

    for facts in by_metric.values():
        for current in facts:
            if current.period.period_type != PeriodType.YTD:
                continue
            quarter = current.period.fiscal_quarter
            if quarter == 1:
                decision = q1_ytd_as_qtd(current)
                if decision.fact is not None:
                    derived[decision.fact.fact_id] = decision.fact
            elif quarter in {2, 3}:
                prior = _latest(
                    item
                    for item in facts
                    if item.period.period_type == PeriodType.YTD
                    and item.period.fiscal_year == current.period.fiscal_year
                    and item.period.fiscal_quarter == quarter - 1
                    and item.period.start == current.period.start
                )
                if prior is not None:
                    decision = derive_qtd_from_ytd(current, prior)
                    if decision.fact is not None:
                        derived[decision.fact.fact_id] = decision.fact

            prior_fy = _latest(
                item
                for item in facts
                if item.period.period_type == PeriodType.FY
                and item.period.fiscal_year == current.period.fiscal_year - 1
            )
            prior_comparable = _latest(
                item
                for item in facts
                if item.period.period_type == PeriodType.YTD
                and item.period.fiscal_year == current.period.fiscal_year - 1
                and item.period.fiscal_quarter == quarter
            )
            if prior_fy is not None and prior_comparable is not None:
                decision = derive_ttm(prior_fy, current, prior_comparable)
                if decision.fact is not None:
                    derived[decision.fact.fact_id] = decision.fact
    return tuple(sorted(derived.values(), key=_fact_sort_key))


def _recent_derivation_window(
    reported: tuple[FinancialFact, ...],
) -> tuple[FinancialFact, ...]:
    if not reported:
        return ()
    latest_fiscal_year = max(item.period.fiscal_year for item in reported)
    minimum_fiscal_year = latest_fiscal_year - DERIVATION_FISCAL_YEAR_LOOKBACK
    return tuple(
        item for item in reported if item.period.fiscal_year >= minimum_fiscal_year
    )


def _fcf_derivations(facts: tuple[FinancialFact, ...]) -> tuple[FinancialFact, ...]:
    ocf_by_key: dict[tuple[object, ...], FinancialFact] = {}
    capex_by_key: dict[tuple[object, ...], FinancialFact] = {}
    for fact in facts:
        if fact.metric == Metric.OCF:
            ocf_by_key[_same_period_source_key(fact)] = fact
        elif fact.metric == Metric.CAPEX:
            capex_by_key[_same_period_source_key(fact)] = fact
    output: list[FinancialFact] = []
    for key in sorted(ocf_by_key.keys() & capex_by_key.keys(), key=str):
        decision = derive_fcf(ocf_by_key[key], capex_by_key[key])
        if decision.fact is not None:
            output.append(decision.fact)
    return tuple(sorted(output, key=_fact_sort_key))


def _snapshot_from_batch(batch: CanonicalizationBatch) -> CashFlowCoreSnapshot:
    reported = _recent_derivation_window(batch.facts)
    period_facts = _period_derivations(reported)
    all_inputs = tuple(sorted((*reported, *period_facts), key=_fact_sort_key))
    fcf_facts = _fcf_derivations(all_inputs)
    all_facts = tuple(sorted((*all_inputs, *fcf_facts), key=_fact_sort_key))
    latest_fcf = _latest(
        item
        for item in fcf_facts
        if item.period.period_type in {PeriodType.YTD, PeriodType.FY}
        and all(
            source.fact_type == FactType.REPORTED
            for source in all_inputs
            if source.fact_id in item.input_fact_ids
        )
    )
    latest_qtd = _latest(
        item for item in fcf_facts if item.period.period_type == PeriodType.QTD
    )
    latest_ttm = _latest(
        item for item in fcf_facts if item.period.period_type == PeriodType.TTM
    )
    ocf_exists = any(item.metric == Metric.OCF for item in batch.facts)
    capex_exists = any(item.metric == Metric.CAPEX for item in batch.facts)
    reasons: list[str] = []
    if not ocf_exists:
        reasons.append("missing_ocf")
    if not capex_exists:
        reasons.append("missing_ppe_capex")
    if latest_fcf is None:
        reasons.append("compatible_ocf_capex_pair_missing")
    if latest_fcf is not None:
        status = EligibilityStatus.ELIGIBLE
    elif ocf_exists or capex_exists:
        status = EligibilityStatus.PARTIAL
    else:
        status = EligibilityStatus.BLOCKED
    cautions = tuple(
        sorted({caution for fact in all_facts for caution in fact.cautions})
    )
    return CashFlowCoreSnapshot(
        status=status,
        facts=all_facts,
        latest_fcf=latest_fcf,
        latest_qtd_fcf=latest_qtd,
        latest_ttm_fcf=latest_ttm,
        denial_reasons=tuple(reasons),
        cautions=cautions,
        source_audit={
            "extracted_occurrences": batch.extracted_occurrences,
            "canonical_reported_facts": len(batch.facts),
            "derivation_window_reported_facts": len(reported),
            "derivation_fiscal_year_lookback": DERIVATION_FISCAL_YEAR_LOOKBACK,
            "derived_period_facts": len(period_facts),
            "derived_fcf_facts": len(fcf_facts),
            "exact_duplicates_suppressed": batch.exact_duplicates_suppressed,
            "source_conflicts": batch.conflicts,
            "source_denials": list(batch.denials),
        },
    )


def build_sec_cash_flow_core(
    payload: Mapping[str, object],
    *,
    raw_payload_sha256: str,
    as_of_date: date,
    financial_type: str,
) -> CashFlowCoreSnapshot:
    if financial_type == "financial":
        return CashFlowCoreSnapshot(
            status=EligibilityStatus.NOT_APPLICABLE,
            facts=(),
            latest_fcf=None,
            latest_qtd_fcf=None,
            latest_ttm_fcf=None,
            denial_reasons=("financial_industry_not_applicable",),
            cautions=(),
            source_audit={"source_processing_skipped": "industry_applicability_gate"},
        )
    batch = canonicalize_sec_companyfacts(
        payload,
        raw_payload_sha256=raw_payload_sha256,
        as_of_date=as_of_date,
    )
    return _snapshot_from_batch(batch)


def blocked_cash_flow_core(
    reason: str,
    *,
    partial: bool = False,
    not_applicable: bool = False,
    source_audit: dict[str, object] | None = None,
) -> CashFlowCoreSnapshot:
    status = EligibilityStatus.BLOCKED
    if partial:
        status = EligibilityStatus.PARTIAL
    if not_applicable:
        status = EligibilityStatus.NOT_APPLICABLE
    return CashFlowCoreSnapshot(
        status=status,
        facts=(),
        latest_fcf=None,
        latest_qtd_fcf=None,
        latest_ttm_fcf=None,
        denial_reasons=(reason,),
        cautions=(),
        source_audit=source_audit or {},
    )


def fact_to_dict(fact: FinancialFact) -> dict[str, object]:
    return {
        "fact_id": fact.fact_id,
        "issuer_id": fact.issuer_id,
        "metric": fact.metric.value,
        "value": str(fact.value),
        "currency": fact.currency,
        "unit": fact.unit,
        "fact_type": fact.fact_type.value,
        "reported_or_derived": fact.reported_or_derived,
        "period_start": fact.period.start.isoformat(),
        "period_end": fact.period.end.isoformat(),
        "period_type": fact.period.period_type.value,
        "fiscal_year": fact.period.fiscal_year,
        "fiscal_quarter": fact.period.fiscal_quarter,
        "duration_days": fact.period.duration_days,
        "entity_scope": fact.entity_scope,
        "statement_basis": fact.statement_basis,
        "source_provider": fact.source_provider,
        "source_document_id": fact.source_document_id,
        "source_document_type": fact.source_document_type,
        "filing_date": fact.filing_date.isoformat(),
        "source_occurrence_id": fact.source_occurrence_id,
        "source_semantic": fact.source_semantic,
        "raw_payload_sha256": fact.raw_payload_sha256,
        "source_reported_value": (
            str(fact.source_reported_value)
            if fact.source_reported_value is not None
            else None
        ),
        "source_reported_unit": fact.source_reported_unit,
        "source_sign": fact.source_sign,
        "normalization_transform": fact.normalization_transform,
        "capex_scope": fact.capex_scope.value if fact.capex_scope else None,
        "derivation_formula": fact.derivation_formula,
        "derivation_version": fact.derivation_version,
        "input_fact_ids": list(fact.input_fact_ids),
        "quality": fact.quality,
        "eligibility": fact.eligibility.value,
        "denial_reason": fact.denial_reason,
        "cautions": list(fact.cautions),
        "as_of_date": fact.as_of_date.isoformat() if fact.as_of_date else None,
    }


def snapshot_to_dict(snapshot: CashFlowCoreSnapshot) -> dict[str, object]:
    return {
        "status": snapshot.status.value,
        "latest_fcf_fact_id": (
            snapshot.latest_fcf.fact_id if snapshot.latest_fcf else None
        ),
        "latest_qtd_fcf_fact_id": (
            snapshot.latest_qtd_fcf.fact_id if snapshot.latest_qtd_fcf else None
        ),
        "latest_ttm_fcf_fact_id": (
            snapshot.latest_ttm_fcf.fact_id if snapshot.latest_ttm_fcf else None
        ),
        "denial_reasons": list(snapshot.denial_reasons),
        "cautions": list(snapshot.cautions),
        "source_audit": snapshot.source_audit,
        "facts": [fact_to_dict(item) for item in snapshot.facts],
    }
