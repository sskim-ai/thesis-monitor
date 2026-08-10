import json
import re
from dataclasses import dataclass, field

from app.models.event import Event


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
FINANCIAL_FACT_PREFIX = "opendart financial fact:"


@dataclass(frozen=True)
class NormalizedFinancialNumber:
    value: float
    currency: str
    source_unit: str


@dataclass
class FinancialValidationResult:
    valid: bool = True
    warnings: list[str] = field(default_factory=list)


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


def validate_event_financials(
    event: Event,
    operating_margin_upper_bound: float = 60.0,
) -> FinancialValidationResult:
    facts = _list(event.confirmed_facts)
    financial_facts = [fact for fact in facts if fact.lower().startswith(FINANCIAL_FACT_PREFIX)]
    if not financial_facts:
        return FinancialValidationResult()

    result = FinancialValidationResult()
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
        result.warnings.append("Financial period scope is missing or unsupported.")
    if len({basis[:3] for basis in bases}) > 1 or len(scopes) > 1:
        result.warnings.append("Revenue and operating income use inconsistent statement or period bases.")

    for fact in financial_facts:
        if not re.search(r"=\s*[-\d,.]+\s+KRW\b", fact, re.IGNORECASE):
            result.warnings.append("Financial amount unit is not explicitly supported.")
            break

    revenue = event.revenue
    operating_income = event.operating_income
    margin = event.operating_margin
    if revenue is not None and revenue <= 0:
        result.warnings.append("Revenue is non-positive, so ratio validation is unavailable.")
    if (
        revenue not in {None, 0}
        and operating_income is not None
        and abs(operating_income) > abs(revenue)
        and not _is_financial_company(event)
    ):
        result.warnings.append("Absolute operating income exceeds revenue.")
    if margin is not None and not _is_financial_company(event):
        if margin > operating_margin_upper_bound or margin < -100:
            result.warnings.append("Operating margin is outside the configured sanity range.")
        if revenue not in {None, 0} and operating_income is not None:
            derived = operating_income / revenue * 100
            if abs(derived - margin) > 1.0:
                result.warnings.append("Reported and derived operating margins do not reconcile.")

    if not result.warnings:
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
        [fact for fact in facts if not fact.lower().startswith(FINANCIAL_FACT_PREFIX)],
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
    for warning in result.warnings:
        _append(unknowns, f"Financial validation warning: {warning}")
    _append(
        unknowns,
        "실적 발표는 확인됐으나 현재 파싱된 숫자의 단위 또는 기간 검증이 필요합니다.",
    )
    event.inferred_implications = json.dumps(implications, ensure_ascii=False)
    event.unknowns = json.dumps(unknowns, ensure_ascii=False)
    return result
