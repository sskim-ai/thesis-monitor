import json
import re
from dataclasses import dataclass, field

from app.models.event import Event
from app.models.financial import FinancialSnapshot


UNIT_MULTIPLIERS = {
    "krw": ("KRW", 1.0),
    "thousand krw": ("KRW", 1_000.0),
    "million krw": ("KRW", 1_000_000.0),
    "100 million krw": ("KRW", 100_000_000.0),
    "billion krw": ("KRW", 1_000_000_000.0),
    "trillion krw": ("KRW", 1_000_000_000_000.0),
    "usd": ("USD", 1.0),
    "thousand usd": ("USD", 1_000.0),
    "million usd": ("USD", 1_000_000.0),
    "billion usd": ("USD", 1_000_000_000.0),
}
VALID_PERIOD_SCOPES = {"quarter", "half-year", "ytd", "annual", "single-quarter", "cumulative"}
FINANCIAL_FACT_PREFIXES = (
    "opendart financial fact:",
    "opendart financial cumulative fact:",
)


@dataclass(frozen=True)
class NormalizedFinancialNumber:
    value: float
    currency: str
    source_unit: str


@dataclass
class FinancialValidationResult:
    valid: bool = True
    hard_errors: list[str] = field(default_factory=list)
    soft_outliers: list[str] = field(default_factory=list)

    @property
    def warnings(self) -> list[str]:
        """Compatibility view for callers that still display all findings."""
        return [*self.hard_errors, *self.soft_outliers]


@dataclass(frozen=True)
class StandaloneQuarter:
    value: float | None
    method: str
    valid: bool


def validate_snapshot_period_chronology(snapshot: FinancialSnapshot) -> bool:
    period_end = snapshot.financial_period_end or snapshot.financials_as_of
    filing_date = snapshot.filing_date or snapshot.reported_date
    if period_end is None or filing_date is None or period_end <= filing_date:
        snapshot.period_mapping_validation_failed = False
        return True
    snapshot.period_mapping_validation_failed = True
    snapshot.financial_statement_basis_warning = True
    hard_errors = _list(snapshot.financial_hard_errors or "[]")
    _append(hard_errors, "financial_period_after_filing_date")
    snapshot.financial_hard_errors = json.dumps(hard_errors)
    warning = (
        "financial period end is after filing date; snapshot is quarantined from "
        "current context and valuation inputs"
    )
    existing_warnings = snapshot.quality_warnings or ""
    while f"; {warning}" in existing_warnings:
        existing_warnings = existing_warnings.replace(f"; {warning}", "", 1)
    if warning not in existing_warnings:
        existing_warnings = "; ".join(
            item for item in (existing_warnings, warning) if item
        )
    snapshot.quality_warnings = existing_warnings
    return False


def financial_snapshot_is_usable(snapshot: FinancialSnapshot) -> bool:
    return (
        not snapshot.period_mapping_validation_failed
        and validate_snapshot_period_chronology(snapshot)
    )


def normalize_standalone_quarter(
    cumulative_value: float | None,
    prior_cumulative_value: float | None,
    period_scope: str,
) -> StandaloneQuarter:
    """Convert a DART cumulative amount to a standalone quarter without guessing."""
    if cumulative_value is None:
        return StandaloneQuarter(None, "missing", False)
    if period_scope in {"single-quarter", "quarter"}:
        return StandaloneQuarter(cumulative_value, "reported_single_quarter", True)
    if period_scope not in {"half-year", "ytd", "annual", "cumulative"}:
        return StandaloneQuarter(None, "unsupported_period_scope", False)
    if prior_cumulative_value is None:
        return StandaloneQuarter(None, "missing_prior_cumulative", False)
    return StandaloneQuarter(
        cumulative_value - prior_cumulative_value,
        "cumulative_less_prior_cumulative",
        True,
    )


def normalize_financial_number(value: float, unit: str) -> NormalizedFinancialNumber | None:
    normalized_unit = re.sub(r"\s+", " ", unit.strip().lower())
    definition = UNIT_MULTIPLIERS.get(normalized_unit)
    if definition is None:
        return None
    currency, multiplier = definition
    return NormalizedFinancialNumber(value=value * multiplier, currency=currency, source_unit=unit)


def _list(value: str) -> list[str]:
    try:
        parsed = json.loads(value)
    except json.JSONDecodeError:
        return []
    return [str(item) for item in parsed] if isinstance(parsed, list) else []


def _append(items: list[str], value: str) -> None:
    if value not in items:
        items.append(value)


def _basis_value(fact: str, key: str) -> str | None:
    match = re.search(rf"{re.escape(key)}=([^;)]*)", fact)
    return match.group(1).strip() if match else None


def _is_financial_company(event: Event) -> bool:
    text = f"{event.company_name or ''} {event.title}".lower()
    return any(term in text for term in ("은행", "보험", "증권", "금융", "bank", "insurance"))


def _fact_amount(facts: list[str], labels: tuple[str, ...]) -> float | None:
    for fact in facts:
        if not any(label in fact for label in labels):
            continue
        match = re.search(r"=\s*([-\d,.]+)\s+KRW\b", fact, re.IGNORECASE)
        if match:
            return float(match.group(1).replace(",", ""))
    return None


def _official_financial_source(event: Event) -> bool:
    return event.provider in {"opendart", "sec_edgar", "company_ir"} or (
        event.claim_actor_type in {"company_official_filing", "company_management"}
    )


def _raw_field_mapping_errors(event: Event) -> list[str]:
    if event.document_type != "preliminary_earnings":
        return []
    try:
        fields = json.loads(event.raw_financial_fields or "[]")
    except json.JSONDecodeError:
        return ["raw_financial_fields_invalid"]
    if not isinstance(fields, list) or not fields:
        return ["preliminary_semantic_mapping_unavailable"]
    methods = {
        str(item.get("parse_method"))
        for item in fields
        if isinstance(item, dict) and item.get("parse_method")
    }
    errors: list[str] = []
    if len(methods) > 1:
        errors.append("mixed_parser_basis")
    supported_units = {"원", "천원", "백만원", "억원"}
    if any(
        isinstance(item, dict)
        and item.get("raw_unit") not in supported_units
        for item in fields
    ):
        errors.append("unsupported_preliminary_unit")
    selected = [
        item
        for item in fields
        if isinstance(item, dict)
        and item.get("raw_period") == "single_quarter"
        and item.get("raw_label")
        in {"매출액", "영업이익", "당기순이익", "지배주주순이익"}
    ]
    if any("증감률" in str(item.get("raw_column_header") or "") for item in selected):
        errors.append("percentage_cell_selected_as_amount")
    return errors


def validate_event_financials(
    event: Event,
    operating_margin_upper_bound: float = 60.0,
) -> FinancialValidationResult:
    facts = _list(event.confirmed_facts)
    financial_facts = [
        fact for fact in facts if fact.lower().startswith(FINANCIAL_FACT_PREFIXES)
    ]
    if not financial_facts:
        return FinancialValidationResult()

    result = FinancialValidationResult()
    if event.document_type == "preliminary_earnings" and event.reporting_period_end is None:
        result.hard_errors.append("reporting_period_unavailable")
    bases = {
        (
            _basis_value(fact, "fs_div"),
            _basis_value(fact, "sj_div"),
            _basis_value(fact, "thstrm_nm"),
            _basis_value(fact, "period_scope"),
        )
        for fact in financial_facts
        if any(label in fact for label in ("매출액", "수익(매출액)", "영업수익", "영업이익"))
    }
    scopes = {basis[3] for basis in bases if basis[3]}
    if any(scope not in VALID_PERIOD_SCOPES for scope in scopes):
        result.hard_errors.append("unsupported_financial_period_scope")
    if len({basis[:3] for basis in bases}) > 1 or len(scopes) > 1:
        result.hard_errors.append("inconsistent_statement_or_period_basis")

    for fact in financial_facts:
        if not re.search(r"=\s*[-\d,.]+\s+KRW\b", fact, re.IGNORECASE):
            result.hard_errors.append("unsupported_financial_amount_unit")
            break

    for error in _raw_field_mapping_errors(event):
        _append(result.hard_errors, error)

    revenue = (
        event.revenue
        if event.revenue is not None
        else _fact_amount(financial_facts, ("매출액", "수익(매출액)", "영업수익"))
    )
    operating_income = (
        event.operating_income
        if event.operating_income is not None
        else _fact_amount(financial_facts, ("영업이익",))
    )
    net_income = (
        event.net_income
        if event.net_income is not None
        else _fact_amount(financial_facts, ("지배주주순이익", "당기순이익"))
    )
    margin = event.operating_margin
    if margin is None and revenue not in {None, 0} and operating_income is not None:
        margin = operating_income / revenue * 100
    if revenue is not None and revenue <= 0:
        result.hard_errors.append("non_positive_revenue")
    if (
        revenue not in {None, 0}
        and operating_income is not None
        and abs(operating_income) > abs(revenue)
        and not _is_financial_company(event)
    ):
        result.soft_outliers.append("operating_income_exceeds_revenue")
    if (
        revenue not in {None, 0}
        and net_income is not None
        and abs(net_income) > abs(revenue)
        and not _is_financial_company(event)
    ):
        result.soft_outliers.append("net_income_exceeds_revenue")
    if margin is not None and not _is_financial_company(event):
        if margin > operating_margin_upper_bound or margin < -100:
            result.soft_outliers.append("unusually_high_or_low_operating_margin")
        if revenue not in {None, 0} and operating_income is not None:
            derived = operating_income / revenue * 100
            if event.operating_margin is not None and abs(derived - margin) > 1.0:
                result.hard_errors.append("reported_and_derived_margin_mismatch")

    if (
        revenue not in {None, 0}
        and net_income is not None
        and abs(net_income / revenue) > 1
        and "net_income_exceeds_revenue" not in result.soft_outliers
    ):
        result.soft_outliers.append("unusually_high_or_low_net_margin")

    if result.soft_outliers and not _official_financial_source(event):
        result.hard_errors.append("outlier_not_verified_by_official_source")

    event.financial_hard_errors = json.dumps(result.hard_errors)
    event.financial_soft_outliers = json.dumps(result.soft_outliers)

    if not result.hard_errors:
        return result

    result.valid = False
    event.financial_statement_basis_warning = True
    event.margin_quality_review = True
    event.revenue = None
    event.operating_income = None
    event.net_income = None
    event.operating_margin = None
    event.yoy_growth = None
    event.qoq_growth = None
    event.confirmed_facts = json.dumps(
        [fact for fact in facts if not fact.lower().startswith(FINANCIAL_FACT_PREFIXES)],
        ensure_ascii=False,
    )
    implications = [
        item
        for item in _list(event.inferred_implications)
        if not any(
            phrase in item.lower()
            for phrase in (
                "reported revenue fact parsed",
                "reported operating profit fact parsed",
                "implied operating margin",
                "revenue basis metadata",
                "operating profit basis metadata",
                "revenue changed",
                "operating income changed",
                "operating margin changed",
            )
        )
    ]
    unknowns = _list(event.unknowns)
    for error in result.hard_errors:
        _append(unknowns, f"Financial validation hard error: {error}")
    _append(
        unknowns,
        "실적 발표는 확인됐으나 현재 파싱된 숫자의 단위 또는 기간 검증이 필요합니다.",
    )
    event.inferred_implications = json.dumps(implications, ensure_ascii=False)
    event.unknowns = json.dumps(unknowns, ensure_ascii=False)
    return result
