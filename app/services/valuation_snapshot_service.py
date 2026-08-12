import json
import math
from dataclasses import dataclass
from datetime import date, datetime, timedelta, timezone
from statistics import median

import httpx
from sqlmodel import Session, select

from app.config import Settings, get_settings
from app.models.financial import CapitalReturnHistory, DividendHistory, FinancialSnapshot
from app.models.security import (
    ConsensusEstimate,
    ProviderResponseCache,
    SecurityMaster,
    ShareCountObservation,
)
from app.models.watchlist import WatchlistItem
from app.models.thesis import InvestmentThesis
from app.schemas.thesis import (
    PriceContext,
    ValuationRelativePosition,
    ValuationSnapshot,
)
from app.services.historical_valuation_service import (
    HistoricalValuationService,
    filing_date,
    financial_period_end,
)
from app.services.alpha_vantage_service import AlphaVantageService
from app.services.data_coverage_service import DataCoverageService
from app.services.dividend_history_service import DividendHistoryService
from app.services.financial_freshness_service import FinancialFreshnessService
from app.services.financial_validation import financial_snapshot_is_usable
from app.services.provider_telemetry_service import ProviderTelemetryService
from app.services.sec_financial_snapshot_service import SecFinancialSnapshotService


def _positive_number(value: object) -> float | None:
    if not isinstance(value, (int, float)):
        return None
    number = float(value)
    return round(number, 4) if math.isfinite(number) and number > 0 else None


def _currency(exchange: str | None, ticker: str) -> str:
    if (exchange or "").upper() in {"KRX", "KOSPI", "KOSDAQ"} or ticker.isdigit():
        return "KRW"
    return "USD"


def _supports_finnhub(exchange: str | None, ticker: str) -> bool:
    return (
        (exchange or "").upper() in {"NASDAQ", "NYSE", "AMEX"}
        and ticker.isascii()
        and ticker.isalpha()
    )


def _date_value(value: object) -> date | None:
    if not isinstance(value, str) or not value:
        return None
    try:
        return date.fromisoformat(value[:10])
    except ValueError:
        return None


def _json_dict(value: str | None) -> dict[str, object]:
    try:
        parsed = json.loads(value or "{}")
    except json.JSONDecodeError:
        return {}
    return parsed if isinstance(parsed, dict) else {}


def _valid_quarters(rows: list[FinancialSnapshot]) -> list[FinancialSnapshot]:
    unique: dict[tuple[int | None, str | None], FinancialSnapshot] = {}
    for row in sorted(rows, key=lambda item: item.reported_date or date.min):
        if row.financial_statement_basis_warning or row.margin_quality_review:
            continue
        if row.period_type not in {"Q1", "H1", "Q3", "FY"}:
            continue
        if row.revenue is None and row.net_income is None and row.diluted_eps is None:
            continue
        unique[(row.fiscal_year, row.period_type)] = row
    return sorted(
        unique.values(),
        key=lambda item: (financial_period_end(item) or date.min, filing_date(item) or date.min),
    )


def _stored_list(value: str | None) -> list[str]:
    try:
        parsed = json.loads(value or "[]")
    except json.JSONDecodeError:
        return []
    return [str(item) for item in parsed] if isinstance(parsed, list) else []


def _quarter_key(row: FinancialSnapshot) -> date | None:
    return financial_period_end(row)


def _preliminary_is_earnings_context_usable(row: FinancialSnapshot) -> bool:
    if row.snapshot_type != "preliminary_earnings":
        return True
    raw_fields = _json_dict_list(row.raw_financial_fields)
    parse_methods = {
        str(field.get("parse_method")) for field in raw_fields if field.get("parse_method")
    }
    filed = filing_date(row)
    common_requirements = (
        bool(row.source_filing_id)
        and row.financial_period_end is not None
        and filed is not None
        and row.financial_period_end <= filed
        and not _stored_list(row.financial_hard_errors)
        and not row.financial_statement_basis_warning
        and not row.margin_quality_review
    )
    provider = (row.provider or "").lower()
    if provider == "opendart":
        return (
            common_requirements
            and row.currency == "KRW"
            and bool(row.unit_scale and row.unit_scale > 0)
            and bool({"html_semantic_table", "structured_filing"} & parse_methods)
            and row.revenue is not None
            and row.operating_income is not None
        )
    if provider == "sec_foreign_filing":
        return (
            common_requirements
            and bool(row.currency)
            and bool(row.unit_scale and row.unit_scale > 0)
            and row.reporting_period_confidence in {"high", "medium"}
            and "sec_foreign_release" in parse_methods
            and any(value is not None for value in (row.revenue, row.operating_income))
        )
    return False


def _preliminary_is_earnings_usable(row: FinancialSnapshot) -> bool:
    """Compatibility alias for callers using the former predicate name."""
    return _preliminary_is_earnings_context_usable(row)


def _json_dict_list(value: str | None) -> list[dict[str, object]]:
    try:
        parsed = json.loads(value or "[]")
    except json.JSONDecodeError:
        return []
    if not isinstance(parsed, list):
        return []
    return [item for item in parsed if isinstance(item, dict)]


def _earnings_quarters(rows: list[FinancialSnapshot]) -> list[FinancialSnapshot]:
    """Select one validated earnings record per actual fiscal quarter."""
    selected: dict[date, FinancialSnapshot] = {}
    for row in sorted(
        rows,
        key=lambda item: (financial_period_end(item) or date.min, filing_date(item) or date.min),
    ):
        key = _quarter_key(row)
        if key is None or row.snapshot_type not in {"full_statement", "preliminary_earnings"}:
            continue
        if _stored_list(row.financial_hard_errors):
            continue
        if row.financial_statement_basis_warning or row.margin_quality_review:
            continue
        if (
            row.snapshot_type == "preliminary_earnings"
            and not _preliminary_is_earnings_context_usable(row)
        ):
            continue
        if all(
            value is None
            for value in (
                row.revenue,
                row.operating_income,
                row.common_net_income,
                row.owners_parent_net_income,
                row.basic_eps,
                row.diluted_eps,
            )
        ):
            continue
        current = selected.get(key)
        if current is None:
            selected[key] = row
            continue
        current_priority = 2 if current.snapshot_type == "full_statement" else 1
        row_priority = 2 if row.snapshot_type == "full_statement" else 1
        if row_priority > current_priority or (
            row_priority == current_priority
            and (filing_date(row) or date.min) >= (filing_date(current) or date.min)
        ):
            selected[key] = row
    return [selected[key] for key in sorted(selected)]


def _latest_official_shares(
    rows: list[FinancialSnapshot], as_of: date | None
) -> tuple[float | None, str | None]:
    candidates = [
        row
        for row in rows
        if row.snapshot_type == "full_statement"
        and (as_of is None or (filing_date(row) is not None and filing_date(row) <= as_of))
        and (row.diluted_shares or row.common_shares_outstanding)
    ]
    if not candidates:
        return None, None
    latest = max(candidates, key=lambda row: filing_date(row) or date.min)
    if latest.diluted_shares and latest.diluted_shares > 0:
        return float(latest.diluted_shares), "latest_official_diluted_shares"
    if latest.common_shares_outstanding and latest.common_shares_outstanding > 0:
        return float(latest.common_shares_outstanding), "latest_official_common_shares"
    return None, None


def _basic_eps_is_reliable(row: FinancialSnapshot) -> bool:
    if row.basic_eps is None:
        return False
    if row.diluted_shares and row.common_shares_outstanding:
        return abs(row.diluted_shares / row.common_shares_outstanding - 1) <= 0.01
    return not row.dilution_notes and not row.stock_based_compensation


@dataclass(frozen=True)
class EarningsTtmResult:
    eps: float | None
    common_income: float | None
    method: str | None
    quarters: tuple[FinancialSnapshot, ...]
    quarter_eps: tuple[float | None, ...]
    share_basis: tuple[str | None, ...]
    eps_currency: tuple[str | None, ...] = ()
    eps_security_basis: tuple[str | None, ...] = ()

    @property
    def contains_preliminary(self) -> bool:
        return any(row.snapshot_type == "preliminary_earnings" for row in self.quarters)


def _field_metadata_record(
    row: FinancialSnapshot,
    *field_names: str,
) -> dict[str, object] | None:
    matches = [
        item
        for item in _json_dict_list(row.raw_financial_fields)
        if str(item.get("field") or "") in field_names
    ]
    return next(
        (item for item in matches if item.get("selected_for_valuation") is True),
        matches[0] if matches else None,
    )


def _field_metadata(
    row: FinancialSnapshot,
    *field_names: str,
) -> tuple[str | None, str]:
    item = _field_metadata_record(row, *field_names)
    if item is not None:
        currency = str(item.get("currency") or "").upper() or None
        security_basis = str(item.get("security_basis") or "unknown")
        return currency, security_basis
    return None, "unknown"


def _quarter_eps(
    row: FinancialSnapshot,
    rows: list[FinancialSnapshot],
) -> tuple[float | None, str | None, str | None, str]:
    if row.diluted_eps is not None:
        currency, security_basis = _field_metadata(row, "diluted_eps", "eps")
        return (
            float(row.diluted_eps),
            "reported_diluted_eps",
            currency,
            security_basis,
        )
    if _basic_eps_is_reliable(row):
        currency, security_basis = _field_metadata(row, "basic_eps", "eps")
        return float(row.basic_eps), "reported_basic_eps", currency, security_basis
    common_income = row.common_net_income or row.owners_parent_net_income
    if common_income is None:
        return None, None, None, "unknown"
    shares = row.diluted_shares or row.common_shares_outstanding
    basis = "snapshot_diluted_shares" if row.diluted_shares else "snapshot_common_shares"
    share_field = "diluted_shares" if row.diluted_shares else "common_shares_outstanding"
    _share_currency, security_basis = _field_metadata(row, share_field)
    if not shares or shares <= 0:
        shares, basis = _latest_official_shares(rows, filing_date(row))
        security_basis = "unknown"
    if not shares or shares <= 0:
        return None, None, None, "unknown"
    return float(common_income) / float(shares), basis, row.currency, security_basis


def _ttm_earnings(rows: list[FinancialSnapshot]) -> EarningsTtmResult:
    quarters = _earnings_quarters(rows)[-4:]
    if len(quarters) < 4:
        return EarningsTtmResult(None, None, None, tuple(quarters), tuple(), tuple())
    keys = [_quarter_key(row) for row in quarters]
    if any(key is None for key in keys) or any(
        not 60 <= (keys[index] - keys[index - 1]).days <= 120
        for index in range(1, len(keys))
        if keys[index] is not None and keys[index - 1] is not None
    ):
        return EarningsTtmResult(None, None, None, tuple(quarters), tuple(), tuple())
    resolved = [_quarter_eps(row, rows) for row in quarters]
    eps_values = [item[0] for item in resolved]
    share_basis = [item[1] for item in resolved]
    eps_currency = [item[2] for item in resolved]
    eps_security_basis = [item[3] for item in resolved]
    common_incomes = [row.common_net_income or row.owners_parent_net_income for row in quarters]
    common_income = (
        sum(float(value) for value in common_incomes if value is not None)
        if all(value is not None for value in common_incomes)
        else None
    )
    if not all(value is not None for value in eps_values):
        return EarningsTtmResult(
            None,
            common_income,
            None,
            tuple(quarters),
            tuple(eps_values),
            tuple(share_basis),
            tuple(eps_currency),
            tuple(eps_security_basis),
        )
    method = (
        "TTM EPS including official preliminary earnings"
        if any(row.snapshot_type == "preliminary_earnings" for row in quarters)
        else "TTM diluted EPS"
        if all(basis == "reported_diluted_eps" for basis in share_basis)
        else "TTM official EPS"
    )
    return EarningsTtmResult(
        sum(float(value) for value in eps_values if value is not None),
        common_income,
        method,
        tuple(quarters),
        tuple(eps_values),
        tuple(share_basis),
        tuple(eps_currency),
        tuple(eps_security_basis),
    )


def _ttm_denominators(
    rows: list[FinancialSnapshot],
) -> tuple[float | None, float | None, str | None]:
    result = _ttm_earnings(rows)
    return result.eps, result.common_income, result.method


def _modeled_fy1_income(
    quarters: list[FinancialSnapshot],
    *,
    minimum: int,
    settings: Settings,
    ticker: str,
) -> tuple[float | None, str | None]:
    if len(quarters) < minimum:
        return None, None
    recent = quarters[-minimum:]
    if any(row.revenue is None or row.common_net_income is None for row in recent):
        return None, None
    current_revenue = sum(float(row.revenue) for row in recent[-4:] if row.revenue is not None)
    prior_revenue = sum(float(row.revenue) for row in recent[-8:-4] if row.revenue is not None)
    if current_revenue <= 0 or prior_revenue <= 0:
        return None, None
    growth = max(
        settings.valuation_model_growth_floor,
        min(settings.valuation_model_growth_cap, current_revenue / prior_revenue - 1),
    )
    margins = [
        float(row.common_net_income) / float(row.revenue)
        for row in recent
        if row.common_net_income is not None and row.revenue not in {None, 0}
    ]
    if len(margins) < minimum:
        return None, None
    latest_ttm_margin = sum(float(row.common_net_income) for row in recent[-4:]) / current_revenue
    normalized_margin = median(margins)
    method = "normalized_net_margin"
    if ticker in {"000660", "MU"}:
        modeled_margin = normalized_margin
        method = "cycle_adjusted"
    else:
        modeled_margin = latest_ttm_margin * 0.6 + normalized_margin * 0.4
    return current_revenue * (1 + growth) * float(modeled_margin), method


def _latest_balance(rows: list[FinancialSnapshot]) -> FinancialSnapshot | None:
    return next(
        (
            row
            for row in sorted(rows, key=lambda item: item.reported_date or date.min, reverse=True)
            if row.snapshot_type == "full_statement"
            and (row.common_equity or row.owners_parent_equity)
            and row.common_shares_outstanding
            and not row.financial_statement_basis_warning
        ),
        None,
    )


@dataclass(frozen=True)
class MultipleBasis:
    metric: str
    horizon: str
    accounting_basis: str = "unknown"
    earnings_attribution: str = "unknown"
    share_basis: str = "unknown"
    security_basis: str = "unknown"
    currency: str = "unknown"
    denominator_period: str | None = None
    denominator_as_of: str | None = None
    source: str = "unknown"


@dataclass(frozen=True)
class PerShareBasisContext:
    issuer_type: str = "unknown"
    security_type: str = "common_stock"
    is_depositary_security: bool = False
    price_currency: str | None = None
    financial_currency: str | None = None
    adr_ratio: float | None = None
    adr_ratio_source: str | None = None
    adr_ratio_direction: str = "ordinary_shares_per_adr"
    identity_warning: str | None = None


@dataclass(frozen=True)
class PerShareValueResult:
    value: float | None
    status: str
    reason: str
    currency: str | None = None
    security_basis: str = "unknown"
    ratio_used: float | None = None


def _is_depositary_security(
    issuer_type: str,
    security_type: str,
    adr_identifier: str | None,
) -> bool:
    normalized_security = security_type.strip().lower().replace("-", "_").replace(" ", "_")
    normalized_issuer = issuer_type.strip().lower()
    depositary_security_type = normalized_security in {
        "adr",
        "ads",
        "depositary_receipt",
        "depositary_security",
        "american_depositary_receipt",
        "american_depositary_share",
    }
    return (
        normalized_issuer == "adr"
        or bool(adr_identifier)
        or depositary_security_type
        and normalized_issuer not in {"domestic_us", "krx"}
    )


def _resolve_per_share_basis_context(
    watchlist_item: WatchlistItem | None,
    security_master: SecurityMaster | None,
    *,
    price_currency: str | None,
    financial_currency: str | None,
) -> PerShareBasisContext:
    watchlist_issuer = watchlist_item.issuer_type if watchlist_item else None
    security_issuer = security_master.issuer_type if security_master else None
    issuer_type = watchlist_issuer or security_issuer or "unknown"
    security_type = security_master.security_type if security_master else "common_stock"
    ratios = [
        value
        for value in (
            watchlist_item.adr_ratio if watchlist_item else None,
            security_master.adr_ratio if security_master else None,
        )
        if value is not None and value > 0
    ]
    identity_warning = None
    if watchlist_issuer and security_issuer and watchlist_issuer != security_issuer:
        identity_warning = "issuer_type_conflict"
    if len(ratios) == 2 and not math.isclose(ratios[0], ratios[1], rel_tol=1e-6):
        identity_warning = "adr_ratio_conflict"
    ratio = ratios[0] if ratios and identity_warning != "adr_ratio_conflict" else None
    ratio_source = (
        "watchlist"
        if watchlist_item and watchlist_item.adr_ratio == ratio
        else security_master.adr_ratio_source
        if security_master and security_master.adr_ratio == ratio
        else None
    )
    return PerShareBasisContext(
        issuer_type=issuer_type,
        security_type=security_type,
        is_depositary_security=(
            _is_depositary_security(
                issuer_type,
                security_type,
                security_master.adr_identifier if security_master else None,
            )
            or bool(
                watchlist_item
                and watchlist_item.adr_ratio
                and watchlist_item.ordinary_share_identifier
            )
        ),
        price_currency=price_currency,
        financial_currency=financial_currency,
        adr_ratio=ratio,
        adr_ratio_source=ratio_source,
        identity_warning=identity_warning,
    )


def _normalize_per_share_value(
    value: float | None,
    *,
    value_currency: str | None,
    security_basis: str,
    context: PerShareBasisContext,
) -> PerShareValueResult:
    if value is None:
        return PerShareValueResult(None, "insufficient_metadata", "denominator_missing")
    if context.identity_warning:
        return PerShareValueResult(
            None,
            "insufficient_metadata",
            context.identity_warning,
            security_basis=security_basis,
        )
    price_currency = (context.price_currency or "").upper()
    denominator_currency = (value_currency or "").upper()
    if context.is_depositary_security:
        if not denominator_currency:
            return PerShareValueResult(
                None,
                "insufficient_metadata",
                "denominator_currency_unknown",
                security_basis=security_basis,
            )
        if not price_currency or denominator_currency != price_currency:
            return PerShareValueResult(
                None,
                "currency_mismatch",
                "price_and_denominator_currency_mismatch",
                currency=denominator_currency,
                security_basis=security_basis,
            )
        if security_basis in {"depositary_security", "current_security"}:
            return PerShareValueResult(
                value,
                "directly_comparable",
                "same_currency_current_security",
                denominator_currency,
                "current_security",
            )
        if security_basis == "ordinary_share":
            if context.adr_ratio is None:
                return PerShareValueResult(
                    None,
                    "missing_adr_ratio",
                    "ordinary_shares_per_adr_unknown",
                    denominator_currency,
                    security_basis,
                )
            return PerShareValueResult(
                value * context.adr_ratio,
                "normalized_to_current_security",
                "ordinary_share_scaled_by_ordinary_shares_per_adr",
                denominator_currency,
                "current_security",
                context.adr_ratio,
            )
        return PerShareValueResult(
            None,
            "security_basis_mismatch",
            "denominator_security_basis_unknown",
            denominator_currency,
            security_basis,
        )
    if (
        context.issuer_type == "foreign_private_issuer"
        and denominator_currency
        and price_currency
        and denominator_currency != price_currency
    ):
        return PerShareValueResult(
            None,
            "currency_mismatch",
            "price_and_denominator_currency_mismatch",
            denominator_currency,
            security_basis,
        )
    return PerShareValueResult(
        value,
        "directly_comparable",
        "non_depositary_current_security",
        denominator_currency or context.price_currency,
        "current_security",
    )


def _normalize_ttm_eps(
    result: EarningsTtmResult,
    context: PerShareBasisContext,
) -> PerShareValueResult:
    if result.eps is None or len(result.quarter_eps) != 4:
        return PerShareValueResult(None, "insufficient_metadata", "ttm_eps_unavailable")
    normalized: list[float] = []
    statuses: list[str] = []
    ratio_used: float | None = None
    currency: str | None = None
    for index, value in enumerate(result.quarter_eps):
        item = _normalize_per_share_value(
            value,
            value_currency=(
                result.eps_currency[index] if index < len(result.eps_currency) else None
            ),
            security_basis=(
                result.eps_security_basis[index]
                if index < len(result.eps_security_basis)
                else "unknown"
            ),
            context=context,
        )
        if item.value is None:
            return item
        normalized.append(item.value)
        statuses.append(item.status)
        ratio_used = item.ratio_used or ratio_used
        currency = item.currency or currency
    status = (
        "normalized_to_current_security"
        if "normalized_to_current_security" in statuses
        else "directly_comparable"
    )
    return PerShareValueResult(
        sum(normalized),
        status,
        "ttm_quarters_share_same_normalized_basis",
        currency,
        "current_security",
        ratio_used,
    )


@dataclass(frozen=True)
class BasisComparison:
    status: str
    reason: str


_UNKNOWN_BASIS_VALUES = {"", "unknown", "provider_defined", "provider-defined", "unavailable"}


def _basis_value_known(value: str | None) -> bool:
    return (value or "").strip().lower() not in _UNKNOWN_BASIS_VALUES


def determine_basis_comparability(
    provider: MultipleBasis | None,
    derived: MultipleBasis | None,
) -> BasisComparison:
    if provider is None or derived is None:
        return BasisComparison("insufficient_metadata", "basis_metadata_missing")
    if provider.metric != derived.metric:
        return BasisComparison("not_comparable", "metric_mismatch")
    dimensions = (
        ("horizon", provider.horizon, derived.horizon),
        ("accounting_basis", provider.accounting_basis, derived.accounting_basis),
        (
            "earnings_attribution",
            provider.earnings_attribution,
            derived.earnings_attribution,
        ),
        ("share_basis", provider.share_basis, derived.share_basis),
        ("security_basis", provider.security_basis, derived.security_basis),
        ("currency", provider.currency, derived.currency),
    )
    unknown_dimensions = [
        name
        for name, provider_value, derived_value in dimensions
        if not _basis_value_known(provider_value) or not _basis_value_known(derived_value)
    ]
    mismatches = [
        name
        for name, provider_value, derived_value in dimensions
        if _basis_value_known(provider_value)
        and _basis_value_known(derived_value)
        and provider_value.strip().lower() != derived_value.strip().lower()
    ]
    if mismatches:
        return BasisComparison("not_comparable", f"{mismatches[0]}_mismatch")
    if unknown_dimensions:
        return BasisComparison("insufficient_metadata", f"{unknown_dimensions[0]}_unknown")
    return BasisComparison("comparable", "same_normalized_basis")


def _official_pe_basis(snapshot: ValuationSnapshot) -> MultipleBasis:
    return MultipleBasis(
        metric="pe",
        horizon="TTM",
        accounting_basis="GAAP",
        earnings_attribution="owners_parent_common",
        share_basis="diluted",
        security_basis=(
            "current_security"
            if snapshot.trailing_pe_basis_status
            in {"directly_comparable", "normalized_to_current_security"}
            else "unknown"
        ),
        currency=snapshot.eps_currency or "unknown",
        denominator_period=snapshot.trailing_pe_denominator_period_end,
        source="official_financials",
    )


def _official_pb_basis(snapshot: ValuationSnapshot) -> MultipleBasis:
    return MultipleBasis(
        metric="pb",
        horizon="latest_reported",
        accounting_basis="GAAP",
        earnings_attribution="owners_parent_common_equity",
        share_basis="common_outstanding",
        security_basis=(
            "current_security"
            if snapshot.price_to_book_basis_status
            in {"directly_comparable", "normalized_to_current_security"}
            else "unknown"
        ),
        currency=snapshot.book_currency or "unknown",
        denominator_period=snapshot.pbr_denominator_period_end,
        source="official_financials",
    )


def _provider_multiple_basis(
    metric: str,
    horizon: str,
    currency: str,
    source: str,
) -> MultipleBasis:
    return MultipleBasis(
        metric=metric,
        horizon=horizon,
        currency=currency,
        source=source,
    )


def _relative_position(
    snapshot: ValuationSnapshot,
    framework: dict[str, object],
) -> tuple[ValuationRelativePosition, str | None]:
    method = str(framework.get("primary_method", "")).lower()
    metric = (
        "price_to_book" if any(term in method for term in ("p/b", "pbr", "roe")) else "forward_pe"
    )
    value = getattr(snapshot, metric)
    if value is None and metric == "forward_pe":
        metric = "trailing_pe"
        value = snapshot.trailing_pe
    ranges = framework.get("historical_multiple_range") or framework.get("peer_multiple_range")
    if not isinstance(ranges, dict) or value is None:
        return ValuationRelativePosition.unknown, None
    low = ranges.get(f"{metric}_low", ranges.get("low"))
    high = ranges.get(f"{metric}_high", ranges.get("high"))
    if not isinstance(low, (int, float)) or not isinstance(high, (int, float)) or low >= high:
        return ValuationRelativePosition.unknown, None
    midpoint = (float(low) + float(high)) / 2
    if value < float(low):
        position = ValuationRelativePosition.discounted
    elif value < midpoint:
        position = ValuationRelativePosition.somewhat_discounted
    elif value <= float(high):
        position = ValuationRelativePosition.neutral
    elif value <= float(high) * 1.2:
        position = ValuationRelativePosition.somewhat_premium
    else:
        position = ValuationRelativePosition.premium
    return position, f"{metric} 비교 범위 {float(low):.1f}~{float(high):.1f}배"


class ValuationSnapshotService:
    def __init__(self, transport: httpx.AsyncBaseTransport | None = None) -> None:
        self.settings = get_settings()
        self.transport = transport
        self.history_service = HistoricalValuationService()
        self.sec_financial_service = SecFinancialSnapshotService(transport=transport)
        self.dividend_service = DividendHistoryService()
        self.coverage_service = DataCoverageService()
        self.freshness_service = FinancialFreshnessService()
        self.alpha_vantage_service = AlphaVantageService(transport=transport)
        self.telemetry = ProviderTelemetryService()

    def _financial_rows(
        self,
        session: Session | None,
        ticker: str,
    ) -> list[FinancialSnapshot]:
        if session is None:
            return []
        rows = list(
            session.exec(
                select(FinancialSnapshot)
                .where(FinancialSnapshot.ticker == ticker)
                .order_by(FinancialSnapshot.reported_date)
            ).all()
        )
        return [row for row in rows if financial_snapshot_is_usable(row)]

    def _apply_financial_metadata(
        self, snapshot: ValuationSnapshot, rows: list[FinancialSnapshot]
    ) -> None:
        if not rows:
            return
        latest_row = max(
            rows,
            key=lambda row: (financial_period_end(row) or date.min, filing_date(row) or date.min),
        )
        period_end = financial_period_end(latest_row)
        filed = filing_date(latest_row)
        snapshot.financial_period_end = period_end.isoformat() if period_end else None
        snapshot.filing_date = filed.isoformat() if filed else None
        snapshot.financials_as_of = snapshot.financial_period_end
        quarters = _earnings_quarters(rows)[-4:]
        if len(quarters) == 4:
            start = financial_period_end(quarters[0])
            end = financial_period_end(quarters[-1])
            snapshot.ttm_period_start = start.isoformat() if start else None
            snapshot.ttm_period_end = end.isoformat() if end else None
            snapshot.ttm_source_filings = [
                filed.isoformat() for row in quarters if (filed := filing_date(row)) is not None
            ]

    def _apply_earnings_context(
        self,
        snapshot: ValuationSnapshot,
        rows: list[FinancialSnapshot],
        result: EarningsTtmResult,
    ) -> None:
        quarters = list(result.quarters)
        if not quarters:
            return
        latest = quarters[-1]
        latest_period = financial_period_end(latest)
        snapshot.latest_earnings_period = latest_period.isoformat() if latest_period else None
        snapshot.financial_currency = latest.currency
        snapshot.earnings_context_source = latest.snapshot_type
        snapshot.earnings_context_is_preliminary = latest.snapshot_type == "preliminary_earnings"
        snapshot.latest_revenue = latest.revenue
        snapshot.latest_operating_income = latest.operating_income
        snapshot.earnings_context_usable = any(
            value is not None
            for value in (latest.revenue, latest.operating_income, latest.net_income)
        )
        snapshot.eps_per_usable = result.eps is not None
        snapshot.ttm_contains_preliminary = result.contains_preliminary and snapshot.eps_per_usable
        snapshot.preliminary_quarter_count = (
            sum(row.snapshot_type == "preliminary_earnings" for row in quarters)
            if snapshot.eps_per_usable
            else 0
        )
        snapshot.earnings_basis = result.method
        snapshot.share_basis = (
            ";".join(dict.fromkeys(item for item in result.share_basis if item)) or None
        )
        snapshot.earnings_quarter_series = [
            {
                "period": (
                    financial_period_end(row).isoformat() if financial_period_end(row) else None
                ),
                "source": row.snapshot_type,
                "filing": filing_date(row).isoformat() if filing_date(row) else None,
                "eps": result.quarter_eps[index] if index < len(result.quarter_eps) else None,
                "share_basis": result.share_basis[index]
                if index < len(result.share_basis)
                else None,
                "eps_currency": result.eps_currency[index]
                if index < len(result.eps_currency)
                else None,
                "eps_security_basis": result.eps_security_basis[index]
                if index < len(result.eps_security_basis)
                else "unknown",
                "reported_diluted_eps": row.diluted_eps,
                "reported_eps_currency": (
                    (_field_metadata_record(row, "diluted_eps", "eps") or {}).get("currency")
                ),
                "reported_eps_security_basis": (
                    (_field_metadata_record(row, "diluted_eps", "eps") or {}).get("security_basis")
                ),
                "revenue": row.revenue,
                "operating_income": row.operating_income,
                "net_income": row.net_income,
                "common_net_income": row.common_net_income,
                "owners_parent_net_income": row.owners_parent_net_income,
                "net_income_concept": (
                    (_field_metadata_record(row, "net_income") or {}).get("concept")
                ),
                "owners_parent_income_concept": (
                    (_field_metadata_record(row, "owners_parent_net_income") or {}).get("concept")
                ),
                "common_income_concept": (
                    (_field_metadata_record(row, "common_net_income") or {}).get("concept")
                ),
                "operating_income_source": row.operating_income_basis,
                "eps_representation": (
                    (_field_metadata_record(row, "diluted_eps", "eps") or {}).get(
                        "representation_type"
                    )
                ),
                "eps_alternate_count": sum(
                    item.get("field") == "diluted_eps_alternate"
                    for item in _json_dict_list(row.raw_financial_fields)
                ),
                "context_usable": any(
                    value is not None
                    for value in (row.revenue, row.operating_income, row.net_income)
                ),
                "eps_usable": (
                    result.quarter_eps[index] is not None
                    if index < len(result.quarter_eps)
                    else False
                ),
            }
            for index, row in enumerate(quarters)
        ]
        if latest.operating_margin is not None:
            snapshot.latest_operating_margin = float(latest.operating_margin)
        elif latest.revenue not in {None, 0} and latest.operating_income is not None:
            snapshot.latest_operating_margin = round(
                float(latest.operating_income) / float(latest.revenue) * 100, 4
            )

        latest_key = _quarter_key(latest)
        by_key = {_quarter_key(row): row for row in _earnings_quarters(rows)}
        prior = None
        prior_year = None
        if latest_key is not None:
            previous = [
                (key, row) for key, row in by_key.items() if key is not None and key < latest_key
            ]
            if previous:
                prior_key, prior = max(previous, key=lambda item: item[0])
                if not 60 <= (latest_key - prior_key).days <= 120:
                    prior = None
            prior_year = next(
                (
                    row
                    for key, row in by_key.items()
                    if key is not None and 330 <= (latest_key - key).days <= 400
                ),
                None,
            )

        def growth(current: float | None, comparison: float | None) -> float | None:
            if current is None or comparison in {None, 0}:
                return None
            return round((float(current) / float(comparison) - 1) * 100, 4)

        if prior is not None:
            snapshot.latest_revenue_qoq = growth(latest.revenue, prior.revenue)
            snapshot.latest_operating_income_qoq = growth(
                latest.operating_income, prior.operating_income
            )
            if (
                snapshot.latest_operating_margin is not None
                and prior.revenue not in {None, 0}
                and prior.operating_income is not None
            ):
                prior_margin = float(prior.operating_income) / float(prior.revenue) * 100
                snapshot.latest_operating_margin_delta_qoq = round(
                    snapshot.latest_operating_margin - prior_margin, 4
                )
        if prior_year is not None:
            snapshot.latest_revenue_yoy = growth(latest.revenue, prior_year.revenue)
            snapshot.latest_operating_income_yoy = growth(
                latest.operating_income, prior_year.operating_income
            )

    def _apply_derived_trailing(
        self,
        snapshot: ValuationSnapshot,
        rows: list[FinancialSnapshot],
        basis_context: PerShareBasisContext | None = None,
    ) -> tuple[float | None, float | None]:
        if snapshot.current_price is None:
            return None, None
        basis_context = basis_context or PerShareBasisContext(
            price_currency=snapshot.currency,
            financial_currency=next((row.currency for row in reversed(rows) if row.currency), None),
        )
        ttm_result = _ttm_earnings(rows)
        normalized_ttm = _normalize_ttm_eps(ttm_result, basis_context)
        ttm_eps, pe_method = normalized_ttm.value, ttm_result.method
        snapshot.raw_ttm_eps = ttm_result.eps
        snapshot.trailing_pe_basis_status = normalized_ttm.status
        snapshot.eps_currency = normalized_ttm.currency
        snapshot.eps_security_basis = normalized_ttm.security_basis
        snapshot.adr_ratio_used = normalized_ttm.ratio_used
        ttm_rows = list(ttm_result.quarters)
        if len(ttm_rows) == 4:
            ttm_end = financial_period_end(ttm_rows[-1])
            ttm_filed = max(
                (filing_date(row) for row in ttm_rows if filing_date(row)),
                default=None,
            )
            snapshot.trailing_pe_denominator_period_end = ttm_end.isoformat() if ttm_end else None
            snapshot.trailing_pe_denominator_filing_date = (
                ttm_filed.isoformat() if ttm_filed else None
            )
        derived_pe: float | None = None
        snapshot.ttm_eps = ttm_eps
        if ttm_eps is not None and ttm_eps <= 0:
            snapshot.trailing_pe = None
            snapshot.trailing_pe_status = "not_meaningful"
            snapshot.trailing_pe_source = "derived_trailing"
            snapshot.trailing_pe_method = pe_method
            snapshot.trailing_valuation_confidence = max(
                snapshot.trailing_valuation_confidence, 0.85
            )
        elif ttm_eps:
            derived_pe = round(snapshot.current_price / ttm_eps, 4)
            snapshot.trailing_pe = derived_pe
            snapshot.trailing_pe_status = "value"
            snapshot.trailing_pe_source = "derived_trailing"
            snapshot.trailing_pe_method = pe_method
            snapshot.trailing_valuation_confidence = 0.85

        balance = _latest_balance(rows)
        derived_pb: float | None = None
        if balance is not None and snapshot.current_price is not None:
            balance_period = financial_period_end(balance)
            balance_filed = filing_date(balance)
            snapshot.pbr_denominator_period_end = (
                balance_period.isoformat() if balance_period else None
            )
            snapshot.pbr_denominator_filing_date = (
                balance_filed.isoformat() if balance_filed else None
            )
            equity = balance.common_equity or balance.owners_parent_equity
            shares = balance.common_shares_outstanding
            if equity is not None and shares and shares > 0:
                raw_bvps = equity / shares
                snapshot.raw_bvps = raw_bvps
                _share_currency, share_security_basis = _field_metadata(
                    balance, "common_shares_outstanding", "diluted_shares"
                )
                normalized_bvps = _normalize_per_share_value(
                    raw_bvps,
                    value_currency=balance.currency,
                    security_basis=share_security_basis,
                    context=basis_context,
                )
                bvps = normalized_bvps.value
                snapshot.bvps = bvps
                snapshot.book_currency = normalized_bvps.currency
                snapshot.share_count_security_basis = normalized_bvps.security_basis
                snapshot.price_to_book_basis_status = normalized_bvps.status
                snapshot.adr_ratio_used = normalized_bvps.ratio_used or snapshot.adr_ratio_used
                if bvps is not None and bvps > 0:
                    derived_pb = round(snapshot.current_price / bvps, 4)
                    if snapshot.price_to_book_status != "value":
                        snapshot.price_to_book = derived_pb
                        snapshot.price_to_book_status = "value"
                        snapshot.price_to_book_source = "derived_trailing"
                        snapshot.price_to_book_method = (
                            "latest owners-parent common equity / current common shares"
                        )
                        snapshot.trailing_valuation_confidence = max(
                            snapshot.trailing_valuation_confidence, 0.85
                        )
        self._apply_financial_metadata(snapshot, rows)
        self._apply_earnings_context(snapshot, rows, ttm_result)
        snapshot.eps_per_usable = ttm_eps is not None
        snapshot.ttm_contains_preliminary = (
            ttm_result.contains_preliminary and snapshot.eps_per_usable
        )
        if ttm_eps is None:
            snapshot.preliminary_quarter_count = 0
        return derived_pe, derived_pb

    def _forecast_dividends(
        self,
        rows: list[FinancialSnapshot],
        fy1_income: float,
        framework: dict[str, object],
        history: list[DividendHistory] | None = None,
    ) -> tuple[float | None, str | None, str, str | None]:
        policy = framework.get("official_dividend_forecast")
        if isinstance(policy, (int, float)) and float(policy) >= 0:
            return float(policy), "official_policy", "high", "회사 공식 배당정책"
        announced = framework.get("announced_common_dividend")
        if isinstance(announced, (int, float)) and float(announced) >= 0:
            return float(announced), "announced_dividend", "high", "발표된 보통주 배당"
        usable_history = [row for row in (history or []) if row.total_dividend is not None]
        payout_history = [
            row.payout_ratio for row in usable_history[-3:] if row.payout_ratio is not None
        ]
        if len(payout_history) >= 3:
            payout = max(0.0, min(1.0, median(float(value) for value in payout_history)))
            return (
                fy1_income * payout,
                "median_3y_payout_ratio",
                "medium",
                f"최근 3년 중앙 지급률 {payout:.1%}",
            )
        if len(usable_history) >= 3:
            return (
                median(float(row.total_dividend) for row in usable_history[-3:]),
                "median_3y_dividend",
                "medium",
                "최근 3년 총배당 중앙값",
            )
        if usable_history:
            return (
                float(usable_history[-1].total_dividend),
                "latest_dividend",
                "low",
                "최근 총배당 유지",
            )
        annual = [
            row
            for row in _valid_quarters(rows)
            if row.period_type == "FY"
            and (row.common_dividends is not None or row.dividends is not None)
        ]
        payouts = [
            float(row.common_dividends if row.common_dividends is not None else row.dividends)
            / float(row.common_net_income or row.owners_parent_net_income)
            for row in annual[-3:]
            if (row.common_net_income or row.owners_parent_net_income or 0) > 0
        ]
        if len(payouts) >= 3:
            payout = max(0.0, min(1.0, median(payouts)))
            return (
                fy1_income * payout,
                "median_3y_payout_ratio",
                "medium",
                f"최근 3년 중앙 지급률 {payout:.1%}",
            )
        dividend_totals = [
            float(row.common_dividends if row.common_dividends is not None else row.dividends)
            for row in annual[-3:]
        ]
        if len(dividend_totals) >= 3:
            return median(dividend_totals), "median_3y_dividend", "medium", "최근 3년 총배당 중앙값"
        if dividend_totals:
            return dividend_totals[-1], "latest_dividend", "low", "최근 총배당 유지"
        return None, None, "unavailable", None

    def _forecast_buybacks(
        self,
        rows: list[FinancialSnapshot],
        framework: dict[str, object],
        ticker: str,
        history: list[CapitalReturnHistory] | None = None,
    ) -> tuple[float | None, str | None, str, str | None]:
        announced = framework.get("announced_buyback")
        if isinstance(announced, (int, float)) and float(announced) >= 0:
            return float(announced), "announced_authorization", "high", "발표된 자사주 매입"
        actual = [row.actual_amount for row in (history or []) if row.actual_amount is not None]
        if actual:
            return (
                median(max(0.0, float(value)) for value in actual[-3:]),
                "historical_normalized_buyback",
                "medium",
                "최근 연간 자사주 매입 중앙값",
            )
        annual = [
            row
            for row in _valid_quarters(rows)
            if row.period_type == "FY" and row.buybacks is not None
        ]
        if annual:
            values = [max(0.0, float(row.buybacks or 0)) for row in annual[-3:]]
            return (
                median(values),
                "historical_normalized_buyback",
                "medium",
                "최근 연간 자사주 매입 중앙값",
            )
        if ticker in {"GOOGL", "IBM", "TSLA"}:
            return None, None, "unavailable", "정기 자사주 매입 영향 자료 부족"
        return 0.0, "no_material_buyback_data", "low", "확인된 중요 자사주 매입 없음"

    def _apply_forward_model(
        self,
        snapshot: ValuationSnapshot,
        rows: list[FinancialSnapshot],
        ticker: str,
        framework: dict[str, object],
        dividend_history: list[DividendHistory] | None = None,
        capital_returns: list[CapitalReturnHistory] | None = None,
        basis_context: PerShareBasisContext | None = None,
    ) -> None:
        if snapshot.current_price is None:
            return
        method = str(framework.get("primary_method", "")).lower()
        if ticker in {"RXRX", "WRD"} or any(
            term in method
            for term in ("risk-adjusted npv", "unit economics", "sotp", "sum-of-the-parts")
        ):
            if ticker in {"RXRX", "WRD"} and any(
                (row.common_net_income or row.owners_parent_net_income or 0) < 0
                for row in _earnings_quarters(rows)[-4:]
            ):
                snapshot.forward_pe_status = "not_meaningful"
                snapshot.forward_pe_source = "modeled_forward"
            return
        full_quarters = _valid_quarters(rows)
        quarters = _earnings_quarters(rows)
        minimum = self.settings.valuation_model_min_quarters
        if len(quarters) < minimum:
            return
        recent = quarters[-minimum:]
        basis_context = basis_context or PerShareBasisContext(
            price_currency=snapshot.currency,
            financial_currency=next((row.currency for row in reversed(rows) if row.currency), None),
        )
        share_row = next(
            (
                row
                for row in reversed(recent)
                if row.diluted_shares or row.common_shares_outstanding
            ),
            None,
        )
        shares = (
            share_row.diluted_shares or share_row.common_shares_outstanding if share_row else None
        )
        if not shares or shares <= 0:
            return
        is_insurance = ticker == "003690" or any(term in method for term in ("p/b", "pbr", "roe"))
        consensus_fy1_income = (
            snapshot.forward_eps * shares
            if snapshot.forward_eps is not None
            and snapshot.forward_eps > 0
            and not basis_context.is_depositary_security
            else None
        )
        book_fy1_income: float | None = None
        if consensus_fy1_income is not None:
            fy1_income = consensus_fy1_income
            book_fy1_income = fy1_income
            forecast_method = "consensus_forward_eps"
        elif is_insurance:
            balance = _latest_balance(rows)
            equity = (balance.common_equity or balance.owners_parent_equity) if balance else None
            if not equity or equity <= 0:
                return
            roe_values: list[float] = []
            for row in recent:
                row_equity = row.common_equity or row.owners_parent_equity
                if not row_equity or row_equity <= 0:
                    continue
                if row.common_net_income is not None:
                    roe_values.append(float(row.common_net_income) * 4 / float(row_equity))
                elif row.diluted_eps is not None and row.common_shares_outstanding:
                    bvps = float(row_equity) / float(row.common_shares_outstanding)
                    if bvps > 0:
                        roe_values.append(float(row.diluted_eps) * 4 / bvps)
            if not roe_values:
                return
            fy1_income = equity * median(roe_values)
            book_fy1_income = fy1_income
            forecast_method = "normalized_roe"
        else:
            modeled = _modeled_fy1_income(
                quarters,
                minimum=minimum,
                settings=self.settings,
                ticker=ticker,
            )
            fy1_income, forecast_method = modeled
            if fy1_income is None or forecast_method is None:
                return
            if any(row.snapshot_type == "preliminary_earnings" for row in recent):
                book_fy1_income, _book_method = _modeled_fy1_income(
                    full_quarters,
                    minimum=minimum,
                    settings=self.settings,
                    ticker=ticker,
                )
            else:
                book_fy1_income = fy1_income
        if fy1_income <= 0:
            if snapshot.forward_pe_status != "value":
                snapshot.forward_pe_status = "not_meaningful"
                snapshot.forward_pe_source = "modeled_forward"
                snapshot.forecast_method = forecast_method
            return
        raw_fy1_eps = fy1_income / shares
        share_field = (
            "diluted_shares"
            if share_row and share_row.diluted_shares
            else "common_shares_outstanding"
        )
        _share_currency, share_security_basis = (
            _field_metadata(
                share_row,
                share_field,
                "common_shares_outstanding",
                "diluted_shares",
            )
            if share_row
            else (None, "unknown")
        )
        normalized_fy1_eps = _normalize_per_share_value(
            raw_fy1_eps,
            value_currency=share_row.currency if share_row else None,
            security_basis=share_security_basis,
            context=basis_context,
        )
        fy1_eps = normalized_fy1_eps.value
        snapshot.forward_pe_basis_status = normalized_fy1_eps.status
        if (
            fy1_eps is not None
            and snapshot.forward_pe_status != "value"
            and not snapshot.forward_pe_basis_conflict
        ):
            snapshot.forward_eps = fy1_eps
            snapshot.forward_pe = round(snapshot.current_price / fy1_eps, 4)
            snapshot.forward_pe_status = "value"
            snapshot.forward_pe_source = "modeled_forward"
            snapshot.forward_pe_method = forecast_method
            snapshot.forward_basis = "FY1"
            snapshot.forward_pe_input_period = "FY1"
            snapshot.forecast_method = forecast_method
            snapshot.forward_valuation_confidence = 0.55

        balance = _latest_balance(rows)
        if balance is not None and book_fy1_income is not None:
            equity = balance.common_equity or balance.owners_parent_equity
            common_shares = balance.common_shares_outstanding
            if equity and common_shares and equity > 0 and common_shares > 0:
                expected_dividends, dividend_method, dividend_quality, dividend_assumption = (
                    self._forecast_dividends(rows, book_fy1_income, framework, dividend_history)
                )
                expected_buybacks, buyback_method, buyback_quality, buyback_assumption = (
                    self._forecast_buybacks(rows, framework, ticker, capital_returns)
                )
                snapshot.dividend_forecast_method = dividend_method
                snapshot.dividend_forecast_quality = dividend_quality
                snapshot.dividend_assumption = dividend_assumption
                snapshot.buyback_forecast_method = buyback_method
                snapshot.buyback_assumption_quality = buyback_quality
                snapshot.buyback_assumption = buyback_assumption
                if expected_dividends is None:
                    snapshot.warnings.append(
                        "배당정책·과거 지급 이력이 부족해 내부 추정 fPBR을 계산하지 않았습니다."
                    )
                    return
                if expected_buybacks is None:
                    snapshot.warnings.append(
                        "중요 자사주 매입 가정을 신뢰성 있게 만들 수 없어 내부 추정 fPBR을 계산하지 않았습니다."
                    )
                    return
                issuance = (
                    median(
                        [
                            float(row.equity_issuance)
                            for row in recent
                            if row.equity_issuance is not None
                        ]
                    )
                    if any(row.equity_issuance is not None for row in recent)
                    else 0.0
                )
                oci = (
                    median(
                        [
                            float(row.other_comprehensive_income)
                            for row in recent
                            if row.other_comprehensive_income is not None
                        ]
                    )
                    if any(row.other_comprehensive_income is not None for row in recent)
                    else 0.0
                )
                fy1_equity = (
                    equity
                    + book_fy1_income
                    - expected_dividends
                    - expected_buybacks
                    + issuance
                    + oci
                )
                if fy1_equity > 0:
                    raw_forward_bvps = fy1_equity / common_shares
                    _share_currency, balance_share_basis = _field_metadata(
                        balance, "common_shares_outstanding"
                    )
                    normalized_forward_bvps = _normalize_per_share_value(
                        raw_forward_bvps,
                        value_currency=balance.currency,
                        security_basis=balance_share_basis,
                        context=basis_context,
                    )
                    snapshot.forward_price_to_book_basis_status = normalized_forward_bvps.status
                    snapshot.forward_bvps = normalized_forward_bvps.value
                    if snapshot.forward_bvps is None:
                        return
                    snapshot.forward_price_to_book = round(
                        snapshot.current_price / snapshot.forward_bvps, 4
                    )
                    snapshot.forward_price_to_book_status = "value"
                    snapshot.forward_price_to_book_source = "modeled_forward"
                    snapshot.forward_price_to_book_method = (
                        "FY1 common equity roll-forward"
                        f"; income={forecast_method}"
                        f"; dividend={dividend_method}"
                        f"; buyback={buyback_method}"
                    )
                    snapshot.forward_book_basis = "FY1"
                    snapshot.forward_pb_input_period = "FY1"

    def _cross_check(
        self,
        snapshot: ValuationSnapshot,
        provider_pe: float | None,
        provider_pb: float | None,
        derived_pe: float | None,
        derived_pb: float | None,
        *,
        provider_pe_basis: MultipleBasis | None = None,
        provider_pb_basis: MultipleBasis | None = None,
        derived_pe_basis: MultipleBasis | None = None,
        derived_pb_basis: MultipleBasis | None = None,
    ) -> None:
        threshold = self.settings.valuation_discrepancy_threshold_pct / 100
        if provider_pe is not None:
            snapshot.provider_trailing_pe = provider_pe
        if derived_pe is not None:
            snapshot.derived_trailing_pe = derived_pe
        if provider_pb is not None:
            snapshot.provider_price_to_book = provider_pb
        if derived_pb is not None:
            snapshot.derived_price_to_book = derived_pb

        pe_comparison = determine_basis_comparability(
            provider_pe_basis,
            derived_pe_basis
            or (_official_pe_basis(snapshot) if snapshot.ttm_eps is not None else None),
        )
        if provider_pe is not None:
            snapshot.trailing_pe_comparability = pe_comparison.status
            snapshot.trailing_pe_comparability_reason = pe_comparison.reason
        pe_structural_conflict = (
            pe_comparison.status == "comparable"
            and provider_pe is not None
            and provider_pe > 0
            and snapshot.ttm_eps is not None
            and snapshot.ttm_eps <= 0
        )
        pe_discrepancy = (
            pe_comparison.status == "comparable"
            and provider_pe is not None
            and provider_pe > 0
            and derived_pe is not None
            and derived_pe > 0
            and abs(provider_pe / derived_pe - 1) > threshold
        )
        if pe_structural_conflict or pe_discrepancy:
            if pe_structural_conflict:
                snapshot.trailing_pe_comparability = "structural_conflict"
                snapshot.trailing_pe_comparability_reason = (
                    "same_basis_positive_multiple_with_nonpositive_denominator"
                )
            snapshot.trailing_pe_basis_conflict = True
            if "trailing_pe" not in snapshot.multiple_basis_conflicts:
                snapshot.multiple_basis_conflicts.append("trailing_pe")
            snapshot.trailing_pe = None
            snapshot.trailing_pe_status = "not_meaningful" if pe_structural_conflict else "conflict"
            snapshot.trailing_valuation_confidence = min(
                snapshot.trailing_valuation_confidence, 0.35
            )
            if pe_discrepancy:
                snapshot.valuation_discrepancy_warning = True
            warning = (
                "외부 PER와 자체 TTM 이익 기준이 구조적으로 충돌합니다."
                if pe_structural_conflict
                else "외부 PER와 자체 계산 PER 차이가 커 분모·주식수·기준일 확인이 필요합니다."
            )
            if warning not in snapshot.warnings:
                snapshot.warnings.append(warning)
        elif derived_pe is not None and derived_pe > 0:
            snapshot.trailing_pe = derived_pe
            snapshot.trailing_pe_status = "value"
            snapshot.trailing_pe_source = "derived_trailing"
        elif snapshot.ttm_eps is not None and snapshot.ttm_eps <= 0:
            snapshot.trailing_pe = None
            snapshot.trailing_pe_status = "not_meaningful"
            snapshot.trailing_pe_source = "derived_trailing"

        pb_comparison = determine_basis_comparability(
            provider_pb_basis,
            derived_pb_basis
            or (_official_pb_basis(snapshot) if snapshot.bvps is not None else None),
        )
        if provider_pb is not None:
            snapshot.price_to_book_comparability = pb_comparison.status
            snapshot.price_to_book_comparability_reason = pb_comparison.reason
        pb_structural_conflict = (
            pb_comparison.status == "comparable"
            and provider_pb is not None
            and provider_pb > 0
            and snapshot.bvps is not None
            and snapshot.bvps <= 0
        )
        pb_discrepancy = (
            pb_comparison.status == "comparable"
            and provider_pb is not None
            and provider_pb > 0
            and derived_pb is not None
            and derived_pb > 0
            and abs(provider_pb / derived_pb - 1) > threshold
        )
        if pb_structural_conflict or pb_discrepancy:
            if pb_structural_conflict:
                snapshot.price_to_book_comparability = "structural_conflict"
                snapshot.price_to_book_comparability_reason = (
                    "same_basis_positive_multiple_with_nonpositive_denominator"
                )
            snapshot.price_to_book_basis_conflict = True
            if "price_to_book" not in snapshot.multiple_basis_conflicts:
                snapshot.multiple_basis_conflicts.append("price_to_book")
            snapshot.price_to_book = None
            snapshot.price_to_book_status = "conflict"
            snapshot.trailing_valuation_confidence = min(
                snapshot.trailing_valuation_confidence, 0.35
            )
            if pb_discrepancy:
                snapshot.valuation_discrepancy_warning = True
            warning = (
                "외부 PBR과 자체 장부가치 기준이 구조적으로 충돌합니다."
                if pb_structural_conflict
                else "외부 PBR과 자체 계산 PBR 차이가 커 자본·주식수 기준 확인이 필요합니다."
            )
            if warning not in snapshot.warnings:
                snapshot.warnings.append(warning)
        elif derived_pb is not None and derived_pb > 0:
            snapshot.price_to_book = derived_pb
            snapshot.price_to_book_status = "value"
            snapshot.price_to_book_source = "derived_trailing"

    def _cross_check_forward(
        self,
        snapshot: ValuationSnapshot,
        *,
        provider_pe: float | None = None,
        derived_pe: float | None = None,
        provider_pb: float | None = None,
        derived_pb: float | None = None,
        provider_pe_basis: MultipleBasis | None = None,
        derived_pe_basis: MultipleBasis | None = None,
        provider_pb_basis: MultipleBasis | None = None,
        derived_pb_basis: MultipleBasis | None = None,
    ) -> None:
        threshold = self.settings.valuation_discrepancy_threshold_pct / 100
        if derived_pe is not None:
            snapshot.derived_forward_pe = derived_pe
        if provider_pb is not None:
            snapshot.provider_forward_price_to_book = provider_pb
        if derived_pb is not None:
            snapshot.derived_forward_price_to_book = derived_pb

        pe_comparison = determine_basis_comparability(provider_pe_basis, derived_pe_basis)
        if provider_pe is not None:
            snapshot.forward_pe_comparability = pe_comparison.status
            snapshot.forward_pe_comparability_reason = pe_comparison.reason
        pe_conflict = (
            pe_comparison.status == "comparable"
            and provider_pe is not None
            and provider_pe > 0
            and (
                (snapshot.forward_eps is not None and snapshot.forward_eps <= 0)
                or (
                    derived_pe is not None
                    and derived_pe > 0
                    and abs(provider_pe / derived_pe - 1) > threshold
                )
            )
        )
        pe_difference = (
            abs(provider_pe / derived_pe - 1)
            if provider_pe is not None
            and provider_pe > 0
            and derived_pe is not None
            and derived_pe > 0
            else None
        )
        if pe_difference is not None:
            snapshot.forward_pe_reference_difference_pct = round(pe_difference * 100, 4)
        if (
            pe_difference is not None
            and pe_difference > threshold
            and pe_comparison.status in {"insufficient_metadata", "not_comparable"}
        ):
            snapshot.forward_pe_reference_caution = True
            snapshot.forward_pe_reference_caution_reason = pe_comparison.reason
        if pe_conflict:
            if snapshot.forward_eps is not None and snapshot.forward_eps <= 0:
                snapshot.forward_pe_comparability = "structural_conflict"
                snapshot.forward_pe_comparability_reason = (
                    "same_basis_positive_multiple_with_nonpositive_denominator"
                )
            snapshot.forward_pe_basis_conflict = True
            snapshot.valuation_discrepancy_warning = True
            if "forward_pe" not in snapshot.multiple_basis_conflicts:
                snapshot.multiple_basis_conflicts.append("forward_pe")
            snapshot.forward_pe = None
            snapshot.forward_pe_status = "conflict"
            snapshot.forward_valuation_confidence = min(snapshot.forward_valuation_confidence, 0.35)
            warning = "외부 fPER와 확인 가능한 예상 EPS 기준이 충돌합니다."
            if warning not in snapshot.warnings:
                snapshot.warnings.append(warning)

        pb_comparison = determine_basis_comparability(provider_pb_basis, derived_pb_basis)
        if provider_pb is not None:
            snapshot.forward_price_to_book_comparability = pb_comparison.status
            snapshot.forward_price_to_book_comparability_reason = pb_comparison.reason
        pb_conflict = (
            pb_comparison.status == "comparable"
            and provider_pb is not None
            and provider_pb > 0
            and (
                (snapshot.forward_bvps is not None and snapshot.forward_bvps <= 0)
                or (
                    derived_pb is not None
                    and derived_pb > 0
                    and abs(provider_pb / derived_pb - 1) > threshold
                )
            )
        )
        if pb_conflict:
            if snapshot.forward_bvps is not None and snapshot.forward_bvps <= 0:
                snapshot.forward_price_to_book_comparability = "structural_conflict"
                snapshot.forward_price_to_book_comparability_reason = (
                    "same_basis_positive_multiple_with_nonpositive_denominator"
                )
            snapshot.forward_price_to_book_basis_conflict = True
            snapshot.valuation_discrepancy_warning = True
            if "forward_price_to_book" not in snapshot.multiple_basis_conflicts:
                snapshot.multiple_basis_conflicts.append("forward_price_to_book")
            snapshot.forward_price_to_book = None
            snapshot.forward_price_to_book_status = "conflict"
            snapshot.forward_valuation_confidence = min(snapshot.forward_valuation_confidence, 0.35)
            warning = "외부 fPBR과 확인 가능한 예상 BVPS 기준이 충돌합니다."
            if warning not in snapshot.warnings:
                snapshot.warnings.append(warning)

    async def fetch(
        self,
        ticker: str,
        exchange: str | None,
        price_context: PriceContext,
        as_of: datetime | None = None,
        *,
        session: Session | None = None,
        thesis: InvestmentThesis | None = None,
    ) -> ValuationSnapshot:
        now = as_of or datetime.now(timezone.utc)
        price_decision = price_context.decision
        daily_price = price_context.periods.get("daily")
        current_price = price_decision.current_price or (
            daily_price.latest_close if daily_price else None
        )
        exchange_trade_date = (
            price_decision.exchange_trade_date
            or price_decision.price_as_of
            or (daily_price.latest_date if daily_price else None)
        )
        snapshot = ValuationSnapshot(
            current_price=current_price,
            currency=_currency(exchange, ticker),
            price_as_of=exchange_trade_date,
            exchange_trade_date=exchange_trade_date,
            latest_completed_regular_session_date=(
                price_decision.latest_completed_regular_session_date
            ),
            price_observed_at=price_decision.price_observed_at,
            price_observed_timezone=price_decision.price_observed_timezone,
            price_basis=price_decision.price_basis
            or ("close" if exchange_trade_date else "unavailable"),
            provider="ohlcv-analyst",
            valuation_data_as_of=now.date().isoformat(),
            valuation_calculated_at=now.isoformat(),
        )
        watchlist_item: WatchlistItem | None = None
        security_master: SecurityMaster | None = None
        foreign_cache_metadata_missing = False
        if session is not None:
            watchlist_item = session.exec(
                select(WatchlistItem).where(WatchlistItem.ticker == ticker)
            ).first()
            security_master = session.exec(
                select(SecurityMaster).where(SecurityMaster.ticker == ticker)
            ).first()
            identity_context = _resolve_per_share_basis_context(
                watchlist_item,
                security_master,
                price_currency=snapshot.currency,
                financial_currency=None,
            )
            if (
                identity_context.issuer_type in {"adr", "foreign_private_issuer"}
                or identity_context.is_depositary_security
            ):
                foreign_cache = session.exec(
                    select(ProviderResponseCache).where(
                        ProviderResponseCache.provider == "sec_edgar",
                        ProviderResponseCache.ticker == ticker,
                        ProviderResponseCache.data_type == "foreign_6k_exhibits",
                    )
                ).first()
                foreign_payload = _json_dict(foreign_cache.payload) if foreign_cache else {}
                foreign_cache_metadata_missing = "latest_filing_parse_result" not in foreign_payload
        rows = self._financial_rows(session, ticker)
        foreign_preliminary_reparse_required = any(
            row.snapshot_type == "preliminary_earnings"
            and (row.provider or "").lower() == "sec_foreign_filing"
            and not _preliminary_is_earnings_context_usable(row)
            for row in rows
        )
        if (
            session is not None
            and _supports_finnhub(exchange, ticker)
            and self.settings.sec_user_agent
            and (
                len(rows) < self.settings.valuation_model_min_quarters
                or max((filing_date(row) or date.min for row in rows), default=date.min)
                < now.date() - timedelta(days=75)
                or foreign_cache_metadata_missing
                or foreign_preliminary_reparse_required
            )
        ):
            try:
                await self.sec_financial_service.refresh(
                    session, ticker, self.settings.sec_user_agent
                )
                rows = self._financial_rows(session, ticker)
            except (httpx.HTTPError, TypeError, ValueError):
                pass
        latest_financial_currency = next(
            (row.currency for row in reversed(_earnings_quarters(rows)) if row.currency),
            None,
        )
        basis_context = _resolve_per_share_basis_context(
            watchlist_item,
            security_master,
            price_currency=snapshot.currency,
            financial_currency=latest_financial_currency,
        )
        snapshot.resolved_issuer_type = basis_context.issuer_type
        snapshot.resolved_security_type = basis_context.security_type
        snapshot.is_depositary_security = basis_context.is_depositary_security
        snapshot.resolved_adr_ratio = basis_context.adr_ratio
        snapshot.adr_ratio_source = basis_context.adr_ratio_source
        snapshot.adr_ratio_direction = (
            basis_context.adr_ratio_direction if basis_context.is_depositary_security else None
        )
        dividend_history: list[DividendHistory] = []
        capital_returns: list[CapitalReturnHistory] = []
        if session is not None:
            dividend_history = self.dividend_service.sync_financial_snapshots(session, ticker, rows)
            capital_returns = self.dividend_service.sync_capital_returns(session, ticker, rows)
        provider_pe: float | None = None
        provider_pb: float | None = None
        alpha_metrics: dict[str, float | None] = {}

        if _supports_finnhub(exchange, ticker) and self.settings.finnhub_api_key:
            finnhub_started = datetime.now(timezone.utc)
            try:
                async with httpx.AsyncClient(
                    base_url="https://finnhub.io/api/v1",
                    timeout=self.settings.valuation_provider_timeout_seconds,
                    transport=self.transport,
                ) as client:
                    response = await client.get(
                        "/stock/metric",
                        params={
                            "symbol": ticker,
                            "metric": "all",
                            "token": self.settings.finnhub_api_key,
                        },
                    )
                    response.raise_for_status()
                    payload = response.json()
                metrics = payload.get("metric", {}) if isinstance(payload, dict) else {}
                if isinstance(metrics, dict) and metrics:
                    eps_ttm = metrics.get("epsTTM")
                    provider_pe = _positive_number(metrics.get("peTTM"))
                    if provider_pe is not None:
                        snapshot.trailing_pe = provider_pe
                        snapshot.trailing_pe_status = "value"
                        snapshot.trailing_pe_source = "provider"
                        snapshot.trailing_pe_method = "Finnhub peTTM"
                        snapshot.trailing_valuation_confidence = 0.75
                    elif isinstance(eps_ttm, (int, float)) and float(eps_ttm) <= 0:
                        snapshot.trailing_pe_status = "not_meaningful"
                        snapshot.trailing_pe_source = "provider"
                    snapshot.forward_pe = _positive_number(metrics.get("forwardPE"))
                    if snapshot.forward_pe is not None:
                        snapshot.provider_forward_pe = snapshot.forward_pe
                        snapshot.forward_pe_comparability = "insufficient_metadata"
                        snapshot.forward_pe_comparability_reason = (
                            "derived_forward_denominator_unavailable"
                        )
                        snapshot.forward_pe_status = "value"
                        snapshot.forward_pe_source = "consensus_forward"
                        snapshot.forward_pe_method = "Finnhub forwardPE"
                        snapshot.forward_basis = "provider-defined forward consensus"
                        snapshot.forward_pe_input_period = "provider-defined forward consensus"
                        snapshot.forward_valuation_confidence = 0.7
                        snapshot.estimate_provider = "finnhub"
                        snapshot.estimate_period = "provider-defined forward consensus"
                        snapshot.consensus_status = "partial"
                        if session is not None:
                            estimate = session.exec(
                                select(ConsensusEstimate).where(
                                    ConsensusEstimate.ticker == ticker,
                                    ConsensusEstimate.provider == "finnhub",
                                    ConsensusEstimate.estimate_period
                                    == "provider-defined forward consensus",
                                )
                            ).first() or ConsensusEstimate(
                                ticker=ticker,
                                provider="finnhub",
                                estimate_as_of=now,
                                estimate_period="provider-defined forward consensus",
                            )
                            estimate.estimate_as_of = now
                            estimate.metric = "forward_pe"
                            estimate.basis = "provider-defined"
                            estimate.value = snapshot.forward_pe
                            estimate.quality = "partial"
                            estimate.coverage_status = "partial"
                            estimate.raw_reference = "Finnhub stock metric forwardPE"
                            session.add(estimate)
                    provider_pb = _positive_number(
                        metrics.get("pbQuarterly") or metrics.get("pbAnnual")
                    )
                    if provider_pb is not None:
                        snapshot.price_to_book = provider_pb
                        snapshot.price_to_book_status = "value"
                        snapshot.price_to_book_source = "provider"
                        snapshot.price_to_book_method = "Finnhub reported P/B"
                    snapshot.provider = "ohlcv-analyst + finnhub"
                    denominator_date = _date_value(
                        payload.get("metricAsOf") or payload.get("asOfDate")
                    )
                    snapshot.denominator_as_of = (
                        denominator_date.isoformat() if denominator_date else None
                    )
                    if denominator_date is None:
                        snapshot.quality = "partial"
                        snapshot.warnings.append(
                            "Finnhub 배수 분모의 정확한 추정 기준일이 제공되지 않아 freshness를 부분 확인으로 표시합니다."
                        )
                    elif (
                        now.date() - denominator_date
                    ).days > self.settings.valuation_snapshot_max_age_days:
                        snapshot.quality = "stale"
                        snapshot.warnings.append(
                            "Valuation 배수 분모 기준일이 오래되어 최신 주가·실적을 완전히 반영하지 않을 수 있습니다."
                        )
                    else:
                        snapshot.quality = "fresh"
                    if session is not None:
                        self.telemetry.record(
                            session,
                            provider="finnhub",
                            endpoint="stock_metric",
                            ticker=ticker,
                            started_at=finnhub_started,
                            status="success",
                        )
                else:
                    snapshot.warnings.append(
                        "Finnhub에서 사용 가능한 Valuation 배수를 반환하지 않았습니다."
                    )
                    if session is not None:
                        self.telemetry.record(
                            session,
                            provider="finnhub",
                            endpoint="stock_metric",
                            ticker=ticker,
                            started_at=finnhub_started,
                            status="partial",
                            error_type="EmptyProviderPayload",
                            error_reason="valuation_metrics_unavailable",
                        )
            except (httpx.HTTPError, TypeError, ValueError) as exc:
                snapshot.warnings.append(f"Finnhub 배수 조회 실패: {type(exc).__name__}")
                if session is not None:
                    self.telemetry.record(
                        session,
                        provider="finnhub",
                        endpoint="stock_metric",
                        ticker=ticker,
                        started_at=finnhub_started,
                        status="failed",
                        error_type=type(exc).__name__,
                        error_code=(
                            str(exc.response.status_code)
                            if isinstance(exc, httpx.HTTPStatusError)
                            else None
                        ),
                        error_reason="valuation_metric_fetch_failed",
                    )
        elif _supports_finnhub(exchange, ticker):
            snapshot.warnings.append("Finnhub API key가 없어 Valuation 배수를 수집하지 못했습니다.")

        if (
            session is not None
            and _supports_finnhub(exchange, ticker)
            and self.settings.alpha_vantage_api_key
        ):
            existing_alpha_estimate = session.exec(
                select(ConsensusEstimate).where(
                    ConsensusEstimate.ticker == ticker,
                    ConsensusEstimate.provider == "alpha_vantage",
                )
            ).first()
            existing_alpha_shares = session.exec(
                select(ShareCountObservation).where(
                    ShareCountObservation.ticker == ticker,
                    ShareCountObservation.provider == "alpha_vantage",
                )
            ).first()
            official_shares_available = any(
                row.diluted_shares or row.common_shares_outstanding for row in rows
            )
            derived_pe_available = len(_valid_quarters(rows)) >= 4
            derived_pb_available = _latest_balance(rows) is not None
            alpha_functions: list[str] = []
            if snapshot.forward_pe_status != "value" and existing_alpha_estimate is None:
                alpha_functions.append("EARNINGS_ESTIMATES")
            if not official_shares_available and existing_alpha_shares is None:
                alpha_functions.append("SHARES_OUTSTANDING")
            if (provider_pe is None and not derived_pe_available) or (
                provider_pb is None and not derived_pb_available
            ):
                alpha_functions.append("OVERVIEW")
            if not dividend_history:
                alpha_functions.append("DIVIDENDS")
            if alpha_functions:
                alpha_bundle = await self.alpha_vantage_service.collect(
                    session,
                    ticker,
                    functions=tuple(dict.fromkeys(alpha_functions)),
                )
                alpha_metrics = self.alpha_vantage_service.overview_metrics(alpha_bundle)
                if alpha_bundle.warnings:
                    snapshot.warnings.append(
                        "Alpha Vantage 일부 보조 데이터가 제공되지 않아 사용 가능한 항목만 교차검증했습니다."
                    )

        alpha_estimate: ConsensusEstimate | None = None
        alpha_shares: ShareCountObservation | None = None
        if session is not None:
            alpha_estimate = session.exec(
                select(ConsensusEstimate)
                .where(
                    ConsensusEstimate.ticker == ticker,
                    ConsensusEstimate.provider == "alpha_vantage",
                )
                .order_by(ConsensusEstimate.estimate_period)
            ).first()
            alpha_shares = session.exec(
                select(ShareCountObservation)
                .where(
                    ShareCountObservation.ticker == ticker,
                    ShareCountObservation.provider == "alpha_vantage",
                )
                .order_by(ShareCountObservation.observed_at.desc())
            ).first()
        if alpha_estimate and alpha_estimate.estimate_mean is not None:
            alpha_eps = alpha_estimate.estimate_mean
            if snapshot.estimate_provider is None:
                snapshot.estimate_provider = "alpha_vantage"
                snapshot.estimate_as_of = alpha_estimate.estimate_as_of.isoformat()
                snapshot.estimate_period = alpha_estimate.estimate_period
                snapshot.estimate_mean = alpha_eps
                snapshot.estimate_high = alpha_estimate.estimate_high
                snapshot.estimate_low = alpha_estimate.estimate_low
                snapshot.estimate_analyst_count = alpha_estimate.analyst_count
                snapshot.estimate_revision_direction = alpha_estimate.revision_direction
                snapshot.consensus_status = alpha_estimate.coverage_status
            if snapshot.current_price and not basis_context.is_depositary_security:
                alpha_forward_pe = snapshot.current_price / alpha_eps if alpha_eps > 0 else None
                provider_forward_pe = (
                    snapshot.forward_pe
                    if snapshot.forward_pe_status == "value"
                    and snapshot.forward_pe_source == "consensus_forward"
                    and snapshot.forward_pe_method == "Finnhub forwardPE"
                    else None
                )
                if provider_forward_pe is not None:
                    snapshot.forward_eps = alpha_eps
                    snapshot.forward_pe_input_period = alpha_estimate.estimate_period
                    self._cross_check_forward(
                        snapshot,
                        provider_pe=provider_forward_pe,
                        derived_pe=alpha_forward_pe,
                        provider_pe_basis=_provider_multiple_basis(
                            "pe",
                            "provider_defined",
                            snapshot.currency,
                            "finnhub",
                        ),
                        derived_pe_basis=MultipleBasis(
                            metric="pe",
                            horizon="FY1",
                            accounting_basis="unknown",
                            earnings_attribution="common_eps",
                            share_basis="unknown",
                            security_basis="current_security",
                            currency=snapshot.currency,
                            denominator_period=alpha_estimate.estimate_period,
                            source="alpha_vantage",
                        ),
                    )
                elif alpha_forward_pe is not None and snapshot.forward_pe_status != "value":
                    snapshot.forward_eps = alpha_eps
                    snapshot.forward_pe = round(alpha_forward_pe, 4)
                    snapshot.forward_pe_status = "value"
                    snapshot.forward_pe_source = "consensus_forward"
                    snapshot.forward_pe_method = "Alpha Vantage analyst EPS estimate"
                    snapshot.forward_basis = alpha_estimate.estimate_period
                    snapshot.forward_pe_input_period = alpha_estimate.estimate_period
                    snapshot.forward_valuation_confidence = 0.65
                    snapshot.consensus_status = alpha_estimate.coverage_status
                if (
                    provider_forward_pe is not None
                    and alpha_forward_pe is not None
                    and snapshot.forward_pe_comparability == "comparable"
                ):
                    discrepancy = abs(provider_forward_pe / alpha_forward_pe - 1)
                    if discrepancy > self.settings.alpha_vantage_consensus_discrepancy_pct / 100:
                        snapshot.consensus_disagreement = True
                        snapshot.forward_valuation_confidence *= 0.7
                        snapshot.warnings.append(
                            "Finnhub와 Alpha Vantage의 forward EPS 추정치 차이가 커 신뢰도를 낮췄습니다."
                        )
                        snapshot.consensus_status = "conflicting"

        derived_pe, derived_pb = self._apply_derived_trailing(snapshot, rows, basis_context)
        unsafe_basis_statuses = {
            "insufficient_metadata",
            "currency_mismatch",
            "security_basis_mismatch",
            "missing_adr_ratio",
        }
        if basis_context.is_depositary_security and {
            snapshot.trailing_pe_basis_status,
            snapshot.price_to_book_basis_status,
        }.intersection(unsafe_basis_statuses):
            snapshot.valuation_calculation_warning = True
            if "currency_mismatch" in {
                snapshot.trailing_pe_basis_status,
                snapshot.price_to_book_basis_status,
            }:
                snapshot.warnings.append(
                    "가격 통화와 주당 재무 기준 통화가 달라 자체 PER/PBR 계산을 보류합니다."
                )
            else:
                snapshot.warnings.append(
                    "ADR/외국 상장주식의 주당 기준을 확인하지 못해 자체 PER/PBR 계산을 보류합니다."
                )
        if alpha_shares and rows:
            official_shares = next(
                (
                    row.diluted_shares or row.common_shares_outstanding
                    for row in reversed(rows)
                    if row.diluted_shares or row.common_shares_outstanding
                ),
                None,
            )
            cross_check_shares = alpha_shares.diluted_shares or alpha_shares.basic_shares
            if official_shares and cross_check_shares:
                share_difference = abs(cross_check_shares / official_shares - 1)
                if share_difference > self.settings.alpha_vantage_share_discrepancy_pct / 100:
                    snapshot.share_count_discrepancy_warning = True
                    snapshot.trailing_valuation_confidence *= 0.7
                    snapshot.warnings.append(
                        "공식 재무제표와 Alpha Vantage 주식 수 차이가 커 주당 배수 신뢰도를 낮췄습니다."
                    )
        framework = _json_dict(thesis.valuation_framework if thesis else None)
        self._apply_forward_model(
            snapshot,
            rows,
            ticker,
            framework,
            dividend_history,
            capital_returns,
            basis_context,
        )
        if (
            basis_context.is_depositary_security
            and snapshot.forward_pe_status == "value"
            and snapshot.forward_pe_source == "consensus_forward"
            and snapshot.forward_eps is None
        ):
            snapshot.forward_pe_basis_status = "insufficient_metadata"
        self._cross_check(
            snapshot,
            provider_pe,
            provider_pb,
            derived_pe,
            derived_pb,
            provider_pe_basis=(
                _provider_multiple_basis("pe", "TTM", snapshot.currency, "finnhub")
                if provider_pe is not None
                else None
            ),
            provider_pb_basis=(
                _provider_multiple_basis("pb", "latest_reported", snapshot.currency, "finnhub")
                if provider_pb is not None
                else None
            ),
        )
        self._cross_check(
            snapshot,
            alpha_metrics.get("trailing_pe"),
            alpha_metrics.get("price_to_book"),
            derived_pe,
            derived_pb,
            provider_pe_basis=(
                _provider_multiple_basis("pe", "TTM", snapshot.currency, "alpha_vantage")
                if alpha_metrics.get("trailing_pe") is not None
                else None
            ),
            provider_pb_basis=(
                _provider_multiple_basis(
                    "pb", "latest_reported", snapshot.currency, "alpha_vantage"
                )
                if alpha_metrics.get("price_to_book") is not None
                else None
            ),
        )
        historical_allowed = not basis_context.is_depositary_security
        snapshot.historical_per_share_basis_status = (
            "directly_comparable" if historical_allowed else "historical_per_share_basis_unverified"
        )
        if session is not None and historical_allowed:
            observations = self.history_service.update_cache(
                session,
                ticker,
                price_context.valuation_history or price_context.daily_history,
                rows,
            )
            self.history_service.apply(snapshot, observations, framework, ticker)
        elif not historical_allowed:
            snapshot.historical_pe_statistics = None
            snapshot.historical_pb_statistics = None
            snapshot.valuation_relative_position = ValuationRelativePosition.unknown
            snapshot.valuation_relative_position_confidence = "low"
            snapshot.valuation_relative_position_reason = "ADR의 시점별 주식 변환 비율과 통화 기준이 확인되지 않아 역사적 per-share 배수 비교를 보류합니다."
            snapshot.valuation_relative_position_reason_codes = [
                "historical_per_share_basis_unverified"
            ]
        if (
            snapshot.valuation_relative_position == ValuationRelativePosition.unknown
            and historical_allowed
        ):
            relative, basis = _relative_position(snapshot, framework)
            if relative != ValuationRelativePosition.unknown:
                snapshot.valuation_relative_position = relative
                snapshot.valuation_relative_basis = basis
                snapshot.valuation_relative_position_confidence = "low"
                snapshot.valuation_relative_position_reason = (
                    "저장된 peer 또는 역사적 범위를 참고했습니다."
                )

        if snapshot.multiple_basis_conflicts:
            snapshot.valuation_signal_conflict = True
            snapshot.valuation_relative_position_confidence = "low"
            if "multiple_basis_conflict" not in snapshot.valuation_relative_position_reason_codes:
                snapshot.valuation_relative_position_reason_codes.append("multiple_basis_conflict")

        if rows and snapshot.provider == "ohlcv-analyst":
            snapshot.provider = "ohlcv-analyst + financial-statements"
        if snapshot.quality == "unavailable":
            if any(
                status in {"value", "not_meaningful"}
                for status in (
                    snapshot.trailing_pe_status,
                    snapshot.forward_pe_status,
                    snapshot.price_to_book_status,
                    snapshot.forward_price_to_book_status,
                )
            ):
                snapshot.quality = "partial"
            elif snapshot.current_price is not None:
                snapshot.quality = "partial"
        if not _supports_finnhub(exchange, ticker) and not rows:
            snapshot.warnings.append(
                "현재 연결된 재무 데이터로 신뢰 가능한 PER/PBR 분모를 만들 수 없어 자료 없음으로 표시합니다."
            )
        if snapshot.filing_date:
            financial_date = _date_value(snapshot.filing_date)
            if (
                financial_date
                and (now.date() - financial_date).days
                > self.settings.valuation_financial_max_age_days
            ):
                snapshot.quality = "stale"
                snapshot.warnings.append(
                    "재무 분모 기준일이 오래되어 Valuation 판단 강도를 낮춥니다."
                )
        if (
            snapshot.forward_pe_status == "value"
            and snapshot.forward_pe_source == "consensus_forward"
            and snapshot.consensus_status == "unavailable"
        ):
            snapshot.consensus_status = "partial"
            if snapshot.estimate_provider is None:
                snapshot.estimate_provider = "provider_metadata_partial"
        if session is not None:
            freshness = self.freshness_service.assess(session, ticker)
            snapshot.financial_refresh_required = freshness.refresh_required
            snapshot.latest_material_financial_event_date = (
                freshness.latest_material_event_date.isoformat()
                if freshness.latest_material_event_date
                else None
            )
            snapshot.financial_freshness = freshness.status
            snapshot.latest_full_financial_period = (
                freshness.latest_full_period.isoformat() if freshness.latest_full_period else None
            )
            snapshot.latest_preliminary_financial_period = (
                freshness.latest_preliminary_period.isoformat()
                if freshness.latest_preliminary_period
                else None
            )
            snapshot.latest_preliminary_context_period = (
                snapshot.latest_preliminary_financial_period
            )
            snapshot.latest_full_filing_date = (
                freshness.latest_full_filing_date.isoformat()
                if freshness.latest_full_filing_date
                else None
            )
            snapshot.latest_preliminary_filing_date = (
                freshness.latest_preliminary_filing_date.isoformat()
                if freshness.latest_preliminary_filing_date
                else None
            )
            snapshot.latest_guidance_date = (
                freshness.latest_guidance_date.isoformat()
                if freshness.latest_guidance_date
                else None
            )
            snapshot.financial_refresh_result = freshness.refresh_result
            snapshot.financial_refresh_reason = freshness.refresh_reason
            snapshot.financial_refresh_trigger_event_id = freshness.refresh_trigger_event_id
            if freshness.refresh_required:
                snapshot.quality = "stale"
                snapshot.forward_valuation_confidence *= 0.5
                snapshot.trailing_valuation_confidence *= 0.7
                snapshot.warnings.append(
                    "최근 실적 발표는 확인됐지만 Valuation 재무 snapshot이 최신 분기로 갱신되지 않았습니다."
                )
            elif freshness.status == "refresh_due":
                if snapshot.quality == "fresh":
                    snapshot.quality = "partial"
                snapshot.forward_valuation_confidence *= 0.7
                snapshot.trailing_valuation_confidence *= 0.8
                snapshot.warnings.append(
                    "정식 재무 보고 주기가 경과했고 이후 material 실적 이벤트가 있어 재무 갱신 여부를 확인 중입니다."
                )
            elif freshness.status == "preliminary_only":
                if snapshot.quality == "fresh":
                    snapshot.quality = "partial"
                latest_preliminary = next(
                    (
                        row
                        for row in rows
                        if row.snapshot_type == "preliminary_earnings"
                        and row.financial_period_end == freshness.latest_preliminary_period
                    ),
                    None,
                )
                if latest_preliminary and latest_preliminary.financial_statement_basis_warning:
                    snapshot.warnings.append(
                        "최신 잠정실적 공시는 확인했지만 파싱된 숫자의 단위·기간 검증에 실패해 매출·이익 및 Valuation 계산에는 반영하지 않았습니다."
                    )
                else:
                    snapshot.warnings.append(
                        "매출·영업이익은 최신 잠정실적까지 확인했지만 현금흐름·재무상태표 배수는 직전 정식 재무제표 기준입니다."
                    )
            if freshness.full_financial_freshness == "stale":
                if snapshot.quality == "fresh":
                    snapshot.quality = "partial"
                snapshot.trailing_valuation_confidence *= 0.7
                snapshot.forward_valuation_confidence *= 0.8
                snapshot.warnings.append(
                    "정식 재무제표는 존재하지만 reporting cadence 기준으로 오래되어 현재 배수 신뢰도를 낮췄습니다."
                )
            if freshness.status == "foreign_filing_partial":
                if snapshot.quality == "fresh":
                    snapshot.quality = "partial"
                snapshot.trailing_valuation_confidence *= 0.6
                snapshot.forward_valuation_confidence *= 0.6
                snapshot.warnings.append(
                    "더 최신 foreign filing의 재무표 자동 구조화가 완료되지 않아 Valuation 신뢰도를 낮췄습니다."
                )
            snapshot.current_multiple_confidence = snapshot.trailing_valuation_confidence
            snapshot.forward_multiple_confidence = snapshot.forward_valuation_confidence
            if (
                freshness.refresh_required
                or snapshot.consensus_disagreement
                or snapshot.share_count_discrepancy_warning
                or bool(snapshot.multiple_basis_conflicts)
            ):
                if snapshot.valuation_relative_position_confidence == "high":
                    snapshot.valuation_relative_position_confidence = "medium"
                if snapshot.consensus_disagreement or snapshot.share_count_discrepancy_warning:
                    snapshot.valuation_relative_position_confidence = "low"
                if snapshot.multiple_basis_conflicts:
                    snapshot.valuation_relative_position_confidence = "low"
            if (
                freshness.full_financial_freshness == "stale"
                or freshness.status == "foreign_filing_partial"
            ):
                if snapshot.valuation_relative_position_confidence == "high":
                    snapshot.valuation_relative_position_confidence = "medium"
                elif snapshot.valuation_relative_position_confidence == "medium":
                    snapshot.valuation_relative_position_confidence = "low"
            if (
                freshness.refresh_required
                and snapshot.current_multiple_confidence < 0.4
                and snapshot.forward_multiple_confidence < 0.4
            ):
                snapshot.valuation_relative_position = ValuationRelativePosition.unknown
                snapshot.valuation_relative_position_reason = "최근 material 실적 이후 정식 재무 분모가 갱신되지 않아 현재 Valuation 위치 판단을 보류합니다."
                snapshot.valuation_relative_position_reason_codes.append(
                    "stale_financial_after_material_event"
                )
            snapshot.data_coverage = self.coverage_service.build(session, ticker, snapshot)
        return snapshot
