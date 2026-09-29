"""Exact fiscal-calendar provenance, with no investment-number authority."""

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, StrictInt

from app.services.issuer_fiscal_week_policy import annual_comparability
from app.services.unified_snapshot_contract import digest

NUMERIC_FIELDS = frozenset(
    {"current_fiscal_year", "prior_fiscal_year", "current_weeks", "prior_weeks"}
)


class FiscalComparabilityMetadata(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)
    contract: Literal["ISSUER_DECLARED_52_53_WEEK_ANNUAL_COMPARABLE"]
    current_fiscal_year: StrictInt = Field(ge=1000, le=9999)
    prior_fiscal_year: StrictInt = Field(ge=1000, le=9999)
    current_weeks: Literal[52, 53]
    prior_weeks: Literal[52, 53]
    quality_reason_codes: list[Literal["FISCAL_WEEK_COUNT_DIFFERENCE"]]
    policy_receipt_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    value_adjustment: None


def validate_metadata(fact):
    fields = fact["fields"]
    value = fields["fiscal_comparability"]
    if any(type(value.get(k)) is not int for k in NUMERIC_FIELDS):
        raise ValueError("fiscal_metadata_exact_integer_required")
    typed = FiscalComparabilityMetadata.model_validate(value).model_dump()
    dependency = fact["field_dependency_receipts"]
    policy = fact["fiscal_metadata_policy"]
    if fact["fact_type"] != "earnings_comparison" or fields["period_type"] != "annual":
        raise ValueError("fiscal_metadata_not_comparison_provenance")
    tuples, sources = [], []
    for role, amount, start, end in (
        ("current", "current_value", "period_start", "period_end"),
        ("comparison", "prior_comparable_value", "prior_period_start", "prior_period_end"),
    ):
        row = dependency[role]["lineage"]
        if (
            fields[amount] != row["amount"]
            or fields[start] != row["amount_period_start"]
            or fields[end] != row["amount_period_end"]
            or fields["metric"] != dependency["metric"]
            or fields["issuer_id"] != f"CIK:{int(row['issuer_cik']):010d}"
            or fields["source_receipt"] != row["receipt"]
        ):
            raise ValueError("fiscal_metadata_source_relation_mismatch")
        sources.append(row["source_row_identity"])
        tuples.append(
            dict(
                issuer=row["issuer_cik"],
                metric=dependency["metric"],
                semantic=row["taxonomy"] + ":" + row["concept"],
                statement_basis=row["statement_basis"],
                currency=row["currency"],
                unit=row["currency"],
                unit_scale=1,
                formal_state="FORMAL",
                period_role="ANNUAL",
                period_start=row["amount_period_start"],
                period_end=row["amount_period_end"],
                source_document_id=row["receipt"],
            )
        )
    if (
        not all(sources)
        or fields["source_occurrences"] != sources
        or typed != dependency["fiscal_comparability"]
        or typed != annual_comparability(*tuples, policy)
    ):
        raise ValueError("fiscal_metadata_policy_or_occurrence_mismatch")
    return dict(
        source_fact_ref=fact["fact_id"],
        policy_receipt_sha256=policy["receipt_sha256"],
        source_relation_sha256=digest(dependency),
        source_occurrence_refs=sources,
    )
