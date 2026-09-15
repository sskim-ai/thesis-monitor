from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from decimal import Decimal, InvalidOperation
import hashlib
from typing import Iterable, Mapping

from app.services.cash_flow_capital_efficiency_service import FinancialFact, Metric
from app.services.official_cash_flow_service import (
    CanonicalizationBatch,
    OfficialFilingOccurrence,
    canonicalize_official_occurrences,
)
from app.services.opendart_financial_recovery_service import (
    FIELD_SPECS,
    FieldSpec,
    Filing,
    select_field_occurrence,
)
from app.services.opendart_xbrl_service import XbrlFact, reconcile_xbrl_duration_fact


CONTRACT_VERSION = "source-class-financial-mapping-v1"

_PPE_ACCOUNT_ID = (
    "ifrs-full_purchaseofpropertyplantandequipmentclassifiedasinvestingactivities"
)
_PPE_SPEC = FieldSpec(
    logical_field="ppe_capex_cash_outflow",
    account_ids=(_PPE_ACCOUNT_ID,),
    account_aliases=(),
    statement_types=("CF",),
    xbrl_period_required=True,
)
_FISCAL_PERIOD_BY_REPORT_CODE = {
    "11013": "Q1",
    "11012": "Q2",
    "11014": "Q3",
    "11011": "FY",
}


@dataclass(frozen=True)
class OpenDartCanonicalPromotionBatch:
    facts: tuple[FinancialFact, ...]
    denials: tuple[dict[str, str], ...]
    source_candidates: int
    exact_duplicates_suppressed: int
    conflicts: int


def _decimal(value: object) -> Decimal | None:
    try:
        parsed = Decimal(str(value or "").replace(",", "").strip())
    except (InvalidOperation, ValueError):
        return None
    return parsed if parsed.is_finite() else None


def _candidate_id(filing: Filing, metric: Metric, semantic: str) -> str:
    identity = "|".join(
        ("opendart", filing.corp_code, filing.receipt_no, metric.value, semantic)
    )
    return f"opendart-candidate:{hashlib.sha256(identity.encode()).hexdigest()[:24]}"


def _denial(
    filing: Filing,
    metric: Metric,
    semantic: str,
    reason: str,
) -> dict[str, str]:
    return {
        "source_occurrence_id": _candidate_id(filing, metric, semantic),
        "source_semantic": semantic,
        "reason": reason,
    }


def _canonical_occurrence(
    filing: Filing,
    rows_by_basis: Mapping[str, list[dict[str, object]]],
    facts: tuple[XbrlFact, ...],
    *,
    metric: Metric,
    spec: FieldSpec,
    raw_payload_sha256: str,
) -> tuple[OfficialFilingOccurrence | None, dict[str, str] | None, int]:
    selection = select_field_occurrence(rows_by_basis, spec)
    semantic = (
        str(selection.candidates[0].get("account_id") or "")
        if selection.candidates
        else spec.account_ids[0]
    )
    semantic = semantic.replace("_", ":", 1)
    if not selection.candidates:
        return None, _denial(filing, metric, semantic, selection.reason or "source_row_missing"), 0
    if len(selection.candidates) != 1:
        return None, _denial(filing, metric, semantic, "multiple_source_occurrences"), len(selection.candidates)

    row = selection.candidates[0]
    account_id = str(row.get("account_id") or "")
    value = _decimal(row.get(spec.source_column))
    currency = str(row.get("currency") or "").upper()
    statement_basis = "consolidated" if selection.basis == "CFS" else "separate"
    source_identity = (
        str(row.get("rcept_no") or "") == filing.receipt_no
        and str(row.get("reprt_code") or "") == filing.report_code
        and str(row.get("bsns_year") or "") == str(filing.business_year)
        and str(row.get("corp_code") or "") == filing.corp_code
    )
    if not source_identity:
        return None, _denial(filing, metric, semantic, "filing_identity_mismatch"), 1
    if not account_id or value is None:
        return None, _denial(filing, metric, semantic, "source_amount_or_semantic_missing"), 1
    if currency != "KRW":
        return None, _denial(filing, metric, semantic, "unsupported_financial_currency"), 1

    match = reconcile_xbrl_duration_fact(
        facts,
        taxonomy_element=account_id.split("_", maxsplit=1)[-1],
        value=value,
        unit_ref="KRW",
        statement_basis=statement_basis,
        entity_identifier=filing.corp_code,
    )
    if match is None:
        return None, _denial(filing, metric, semantic, "exact_xbrl_context_unresolved"), 1

    fiscal_period = _FISCAL_PERIOD_BY_REPORT_CODE.get(filing.report_code)
    if fiscal_period is None:
        return None, _denial(filing, metric, semantic, "formal_report_code_unsupported"), 1
    namespace, tag = account_id.split("_", maxsplit=1)
    return (
        OfficialFilingOccurrence(
            issuer_id=f"opendart:{filing.corp_code}",
            value=value,
            currency=currency,
            unit=str(match.unit_ref or ""),
            period_start=match.context.period_start,
            period_end=match.context.period_end,
            fiscal_year=filing.business_year,
            fiscal_period=fiscal_period,
            source_provider="opendart_xbrl",
            source_document_id=filing.receipt_no,
            source_document_type=filing.report_code,
            filing_date=filing.receipt_date,
            namespace=namespace,
            tag=tag,
            raw_payload_sha256=raw_payload_sha256,
            entity_scope="issuer_level",
            statement_basis=statement_basis,
            frame=match.context_ref,
        ),
        None,
        1,
    )


def promote_opendart_cash_flow_facts(
    filing: Filing,
    rows_by_basis: Mapping[str, list[dict[str, object]]],
    xbrl_facts: Iterable[XbrlFact],
    *,
    raw_payload_sha256: str,
    as_of_date: date,
) -> OpenDartCanonicalPromotionBatch:
    """Promote only exact, unique OpenDART OCF and PPE duration occurrences."""
    facts = tuple(xbrl_facts)
    occurrences: list[OfficialFilingOccurrence] = []
    denials: list[dict[str, str]] = []
    candidate_count = 0
    for metric, spec in (
        (Metric.OCF, FIELD_SPECS["operating_cash_flow"]),
        (Metric.CAPEX, _PPE_SPEC),
    ):
        occurrence, denial, candidates = _canonical_occurrence(
            filing,
            rows_by_basis,
            facts,
            metric=metric,
            spec=spec,
            raw_payload_sha256=raw_payload_sha256,
        )
        candidate_count += candidates
        if occurrence is not None:
            occurrences.append(occurrence)
        if denial is not None:
            denials.append(denial)

    canonical: CanonicalizationBatch = canonicalize_official_occurrences(
        occurrences,
        as_of_date=as_of_date,
    )
    return OpenDartCanonicalPromotionBatch(
        facts=canonical.facts,
        denials=tuple([*denials, *canonical.denials]),
        source_candidates=candidate_count,
        exact_duplicates_suppressed=canonical.exact_duplicates_suppressed,
        conflicts=canonical.conflicts,
    )
