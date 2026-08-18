from __future__ import annotations

import math
import json
import re
from collections import defaultdict
from dataclasses import dataclass
from datetime import date
from statistics import mean, median
from typing import Callable, Iterable, Mapping

from sqlmodel import Session, select

from app.models.company import Company
from app.models.security import SecurityMaster
from app.models.thesis import ThesisAssessment
from app.services.security_identity_service import (
    TIER_A_AUTHORITATIVE,
    TIER_B_DETERMINISTIC_REFERENCE,
    TIER_C_EXPLICIT_LOCAL,
    identity_source_tier,
)


PEER_SECTOR_VALUATION_CONTRACT = "peer-sector-valuation-v1"
PEER_GROUP_VERSION = "verified-profile-peers-v2"
PEER_PROVIDER = "validated_active_monitoring_assessments"
MINIMUM_PEER_SAMPLE = 3
HIGH_QUALITY_PEER_SAMPLE = 5

_COMPARABLE_BASIS = {"directly_comparable", "normalized_to_current_security"}
_RELIABLE_IDENTITY_TIERS = {
    TIER_A_AUTHORITATIVE,
    TIER_B_DETERMINISTIC_REFERENCE,
    TIER_C_EXPLICIT_LOCAL,
}
_UNSUITABLE_FRAMEWORKS = {
    "biotech",
    "biotechnology",
    "drug_discovery",
    "hpc_crypto_infrastructure",
    "holding_company",
    "life_sciences",
    "pharmaceutical",
    "pharmaceuticals",
    "saas",
}
_IDENTITY_CONFLICT = re.compile(r"conflict|mismatch|inconsistent|불일치|상충", re.I)


@dataclass(frozen=True)
class MetricSpec:
    key: str
    value_field: str
    status_field: str
    basis_field: str
    denominator_field: str
    denominator_period_field: str
    denominator_filing_field: str | None
    source_field: str
    required_source: str | None = None


_METRIC_SPECS = (
    MetricSpec(
        key="trailing_pe",
        value_field="trailing_pe",
        status_field="trailing_pe_status",
        basis_field="trailing_pe_basis_status",
        denominator_field="ttm_eps",
        denominator_period_field="trailing_pe_denominator_period_end",
        denominator_filing_field="trailing_pe_denominator_filing_date",
        source_field="trailing_pe_source",
    ),
    MetricSpec(
        key="price_to_book",
        value_field="price_to_book",
        status_field="price_to_book_status",
        basis_field="price_to_book_basis_status",
        denominator_field="bvps",
        denominator_period_field="pbr_denominator_period_end",
        denominator_filing_field="pbr_denominator_filing_date",
        source_field="price_to_book_source",
    ),
    MetricSpec(
        key="forward_pe_consensus",
        value_field="forward_pe",
        status_field="forward_pe_status",
        basis_field="forward_pe_basis_status",
        denominator_field="forward_eps",
        denominator_period_field="forward_pe_input_period",
        denominator_filing_field=None,
        source_field="forward_pe_source",
        required_source="consensus_forward",
    ),
    MetricSpec(
        key="forward_pe_modeled",
        value_field="forward_pe",
        status_field="forward_pe_status",
        basis_field="forward_pe_basis_status",
        denominator_field="forward_eps",
        denominator_period_field="forward_pe_input_period",
        denominator_filing_field=None,
        source_field="forward_pe_source",
        required_source="modeled_forward",
    ),
    MetricSpec(
        key="forward_price_to_book_consensus",
        value_field="forward_price_to_book",
        status_field="forward_price_to_book_status",
        basis_field="forward_price_to_book_basis_status",
        denominator_field="forward_bvps",
        denominator_period_field="forward_pb_input_period",
        denominator_filing_field=None,
        source_field="forward_price_to_book_source",
        required_source="consensus_forward",
    ),
    MetricSpec(
        key="forward_price_to_book_modeled",
        value_field="forward_price_to_book",
        status_field="forward_price_to_book_status",
        basis_field="forward_price_to_book_basis_status",
        denominator_field="forward_bvps",
        denominator_period_field="forward_pb_input_period",
        denominator_filing_field=None,
        source_field="forward_price_to_book_source",
        required_source="modeled_forward",
    ),
)


def _dict(value: object) -> dict[str, object]:
    if isinstance(value, dict):
        return value
    if not isinstance(value, str):
        return {}
    try:
        parsed = json.loads(value or "{}")
    except json.JSONDecodeError:
        return {}
    return parsed if isinstance(parsed, dict) else {}


def _number(value: object) -> float | None:
    if isinstance(value, (int, float)) and not isinstance(value, bool):
        number = float(value)
        return number if math.isfinite(number) else None
    return None


def _normalized(value: object) -> str | None:
    text = re.sub(r"[^a-z0-9]+", "_", str(value or "").strip().lower()).strip("_")
    return text or None


def _market(company: Company) -> str:
    if company.ticker.isdigit() or (company.exchange or "").upper() == "KRX":
        return "kr"
    return "us"


def _percentile(values: list[float], fraction: float) -> float:
    ordered = sorted(values)
    position = (len(ordered) - 1) * fraction
    lower = math.floor(position)
    upper = math.ceil(position)
    if lower == upper:
        return round(ordered[lower], 4)
    weight = position - lower
    return round(ordered[lower] * (1 - weight) + ordered[upper] * weight, 4)


def _cross_section_percentile(values: list[float], company_value: float) -> float:
    below = sum(value < company_value for value in values)
    equal = sum(value == company_value for value in values)
    return round((below + 0.5 * equal) / len(values) * 100, 4)


def _profile(
    company: Company,
    *,
    profile_reader: Callable[[str, object], dict[str, object] | None],
    data_dir: object,
) -> dict[str, str | None]:
    provenance = profile_reader(company.ticker, data_dir) or {}
    quality = str(provenance.get("quality") or "unavailable")
    if quality != "verified":
        return {
            "quality": quality,
            "taxonomy": None,
            "sub_industry": None,
            "industry": None,
            "sector": None,
        }
    industry = provenance.get("industry") or company.industry
    sector = provenance.get("sector") or company.sector
    official_description = provenance.get("official_industry_description")
    sub_industry = (
        _normalized(official_description)
        if official_description and _normalized(official_description) != _normalized(industry)
        else None
    )
    return {
        "quality": quality,
        "taxonomy": _normalized(provenance.get("taxonomy_key")),
        "sub_industry": sub_industry,
        "industry": _normalized(industry),
        "sector": _normalized(sector),
    }


def _framework(profile: Mapping[str, str | None]) -> str:
    taxonomy = str(profile.get("taxonomy") or "")
    industry = str(profile.get("industry") or "")
    combined = f"{taxonomy}_{industry}"
    if any(token in combined for token in ("biotech", "pharmaceutical", "life_science")):
        return "biotech"
    if "insurance" in combined or "reinsurance" in combined:
        return "insurance"
    if any(token in combined for token in ("steel", "material")):
        return "steel_materials"
    if any(token in combined for token in ("shipping", "transport", "logistics")):
        return "transport_logistics"
    if "automotive" in combined:
        return "automotive"
    if "holding" in combined:
        return "holding_company"
    if "saas" in combined:
        return "saas"
    if any(token in combined for token in ("hpc", "crypto_infrastructure")):
        return "hpc_crypto_infrastructure"
    if "semiconductor" in combined:
        return "semiconductor"
    return "general"


def _interpretation_contract(framework: str) -> dict[str, object]:
    contracts = {
        "semiconductor": (
            "cycle_normalized_earnings_and_cash_conversion",
            ["asp_or_utilization", "product_mix", "capex", "free_cash_flow"],
        ),
        "insurance": (
            "pbr_requires_returns_and_capital_context",
            ["roe", "capital_adequacy", "underwriting_quality"],
        ),
        "transport_logistics": (
            "mid_cycle_margin_and_cash_conversion",
            ["freight_or_contract_mix", "fuel_cost", "operating_cash_flow"],
        ),
        "steel_materials": (
            "cycle_normalized_earnings_and_book_value",
            ["spread", "inventory", "normalized_margin", "operating_cash_flow"],
        ),
        "automotive": (
            "volume_mix_margin_and_free_cash_flow",
            ["volume", "asp_or_mix", "incentives", "free_cash_flow"],
        ),
        "biotech": (
            "peer_valuation_not_meaningful",
            ["cash_runway", "milestone_probability", "dilution"],
        ),
        "hpc_crypto_infrastructure": (
            "generic_multiple_not_primary",
            ["capacity", "power_economics", "contracts", "capex", "dilution"],
        ),
        "saas": (
            "per_pbr_not_primary_without_growth_metric",
            ["arr", "nrr", "gross_margin", "free_cash_flow"],
        ),
        "holding_company": (
            "nav_sotp_required",
            ["subsidiary_value", "ownership", "net_debt", "holding_discount"],
        ),
        "general": (
            "relative_multiple_is_context_not_verdict",
            ["earnings_quality", "cash_conversion", "balance_sheet"],
        ),
    }
    rule, required_drivers = contracts[framework]
    return {
        "framework": framework,
        "rule": rule,
        "required_drivers": required_drivers,
        "automatic_cheap_or_expensive_verdict": False,
    }


def _metric_allowed(metric: str, framework: str) -> tuple[bool, str | None]:
    if framework in _UNSUITABLE_FRAMEWORKS:
        return False, "industry_metric_not_meaningful"
    if metric.startswith("forward_price_to_book") and framework not in {
        "insurance",
        "steel_materials",
        "semiconductor",
        "transport_logistics",
        "automotive",
    }:
        return False, "industry_metric_not_primary"
    return True, None


def evaluate_metric_value(
    snapshot: Mapping[str, object],
    spec: MetricSpec,
    *,
    expected_price_as_of: str,
) -> tuple[float | None, str | None, list[str]]:
    basis_conflict = snapshot.get(f"{spec.value_field}_basis_conflict") is True
    conflict_fields = snapshot.get("multiple_basis_conflicts")
    if basis_conflict or (
        isinstance(conflict_fields, list) and spec.value_field in conflict_fields
    ):
        return None, "provider_conflict", []
    denominator = _number(snapshot.get(spec.denominator_field))
    if denominator is None or denominator <= 0:
        reason = (
            "negative_eps"
            if spec.denominator_field in {"ttm_eps", "forward_eps"}
            and denominator is not None
            else "negative_equity"
            if spec.denominator_field in {"bvps", "forward_bvps"}
            and denominator is not None
            else f"missing_{spec.denominator_field}"
        )
        return None, reason, []
    value = _number(snapshot.get(spec.value_field))
    if value is None or value <= 0:
        return None, "metric_unavailable_or_non_positive", []
    if str(snapshot.get(spec.status_field) or "") != "value":
        return None, "metric_status_not_value", []
    if str(snapshot.get(spec.basis_field) or "") not in _COMPARABLE_BASIS:
        return None, "security_basis_unknown", []
    if spec.required_source and snapshot.get(spec.source_field) != spec.required_source:
        return None, "forward_basis_mismatch", []
    price_as_of = str(snapshot.get("price_as_of") or "")[:10]
    if not price_as_of or price_as_of != expected_price_as_of:
        return None, "stale_metric", []
    if spec.denominator_filing_field:
        filing_date = str(snapshot.get(spec.denominator_filing_field) or "")[:10]
        if filing_date and filing_date > expected_price_as_of:
            return None, "future_denominator_filing", []
    cautions: list[str] = []
    if not snapshot.get(spec.denominator_period_field):
        cautions.append("denominator_period_partial")
    return value, None, cautions


def _period_compatibility(subject_period: object, candidate_period: object) -> str:
    subject = str(subject_period or "").strip()
    candidate = str(candidate_period or "").strip()
    if not subject or not candidate:
        return "partial"
    if subject == candidate:
        return "exact"
    try:
        subject_date = date.fromisoformat(subject[:10])
        candidate_date = date.fromisoformat(candidate[:10])
    except ValueError:
        return "mismatch"
    return "caution" if abs((subject_date - candidate_date).days) <= 120 else "mismatch"


def _issuer_identity(security: SecurityMaster | None, ticker: str) -> dict[str, object]:
    if security is None:
        return {
            "issuer_id": f"ticker:{ticker}",
            "security_id": f"ticker:{ticker}",
            "identity_tier": "unavailable",
            "issuer_dedup_reliable": False,
        }
    tier = identity_source_tier(security.identity_provider, security.identity_quality)
    reliable = tier in _RELIABLE_IDENTITY_TIERS
    warnings = security.identity_warnings
    if isinstance(warnings, str):
        try:
            parsed_warnings = json.loads(warnings or "[]")
        except json.JSONDecodeError:
            parsed_warnings = [warnings]
    else:
        parsed_warnings = warnings
    warning_items = parsed_warnings if isinstance(parsed_warnings, list) else []
    warning_text = " ".join(str(item) for item in warning_items)
    return {
        "issuer_id": (
            security.canonical_company_id if reliable else f"ticker:{security.ticker}"
        ),
        "security_id": security.canonical_security_id,
        "identity_tier": tier,
        "issuer_dedup_reliable": reliable,
        "security_type": security.security_type,
        "issuer_type": security.issuer_type,
        "adr_ratio": security.adr_ratio,
        "identity_conflict": bool(_IDENTITY_CONFLICT.search(warning_text)),
    }


def _select_group(
    subject: str,
    companies: Mapping[str, Company],
    profiles: Mapping[str, Mapping[str, str | None]],
) -> tuple[str | None, str | None, list[str]]:
    company = companies[subject]
    market = _market(company)
    profile = profiles[subject]
    for basis in ("taxonomy", "sub_industry", "industry", "sector"):
        value = profile.get(basis)
        if not value:
            continue
        matches = sorted(
            ticker
            for ticker, candidate in companies.items()
            if ticker != subject
            and _market(candidate) == market
            and profiles[ticker].get("quality") == "verified"
            and profiles[ticker].get(basis) == value
        )
        if len(matches) >= MINIMUM_PEER_SAMPLE:
            return basis, value, matches
    return None, None, []


def _deduplicate_issuers(
    tickers: list[str], identities: Mapping[str, Mapping[str, object]]
) -> tuple[list[str], dict[str, str]]:
    grouped: dict[str, list[str]] = defaultdict(list)
    for ticker in tickers:
        grouped[str(identities[ticker]["issuer_id"])].append(ticker)
    kept: list[str] = []
    excluded: dict[str, str] = {}
    for issuer_tickers in grouped.values():
        ordered = sorted(issuer_tickers)
        kept.append(ordered[0])
        for ticker in ordered[1:]:
            excluded[ticker] = "same_issuer_duplicate"
    return sorted(kept), excluded


def _quality(sample_count: int, group_basis: str) -> str:
    if sample_count < MINIMUM_PEER_SAMPLE or group_basis == "sector":
        return "LOW"
    return "HIGH" if sample_count >= HIGH_QUALITY_PEER_SAMPLE else "MEDIUM"


def _metric_state(
    *,
    spec: MetricSpec,
    subject: str,
    candidate_tickers: list[str],
    duplicate_exclusions: Mapping[str, str],
    snapshots: Mapping[str, Mapping[str, object]],
    profiles: Mapping[str, Mapping[str, str | None]],
    identities: Mapping[str, Mapping[str, object]],
    group_basis: str,
    expected_price_as_of: str,
    framework: str,
) -> tuple[dict[str, object], dict[str, object]]:
    allowed, unavailable_reason = _metric_allowed(spec.key, framework)
    if not allowed:
        return (
            {"available": False, "sample_count": 0, "reason": unavailable_reason},
            {"included": [], "excluded": []},
        )
    if identities[subject].get("identity_conflict") is True:
        return (
            {
                "available": False,
                "sample_count": 0,
                "reason": "security_identity_conflict",
            },
            {"included": [], "excluded": []},
        )
    subject_value, subject_reason, subject_cautions = evaluate_metric_value(
        snapshots[subject], spec, expected_price_as_of=expected_price_as_of
    )
    subject_period = snapshots[subject].get(spec.denominator_period_field)
    included: list[dict[str, object]] = []
    excluded: list[dict[str, object]] = []
    values: list[float] = []
    for ticker in candidate_tickers:
        if ticker in duplicate_exclusions:
            excluded.append(
                {
                    "ticker": ticker,
                    "issuer_id": identities[ticker]["issuer_id"],
                    "reason": duplicate_exclusions[ticker],
                }
            )
            continue
        if identities[ticker].get("identity_conflict") is True:
            excluded.append(
                {
                    "ticker": ticker,
                    "issuer_id": identities[ticker]["issuer_id"],
                    "reason": "security_identity_conflict",
                }
            )
            continue
        value, reason, cautions = evaluate_metric_value(
            snapshots[ticker], spec, expected_price_as_of=expected_price_as_of
        )
        if value is None:
            excluded.append(
                {
                    "ticker": ticker,
                    "issuer_id": identities[ticker]["issuer_id"],
                    "reason": reason or "metric_unavailable",
                }
            )
            continue
        period_status = _period_compatibility(
            subject_period, snapshots[ticker].get(spec.denominator_period_field)
        )
        if period_status == "mismatch":
            excluded.append(
                {
                    "ticker": ticker,
                    "issuer_id": identities[ticker]["issuer_id"],
                    "reason": "period_mismatch",
                }
            )
            continue
        if period_status in {"partial", "caution"}:
            cautions.append(f"period_{period_status}")
        values.append(value)
        included.append(
            {
                "ticker": ticker,
                "issuer_id": identities[ticker]["issuer_id"],
                "security_id": identities[ticker]["security_id"],
                "identity_tier": identities[ticker]["identity_tier"],
                "issuer_dedup_reliable": identities[ticker][
                    "issuer_dedup_reliable"
                ],
                "taxonomy": profiles[ticker].get("taxonomy"),
                "industry": profiles[ticker].get("industry"),
                "metric": spec.key,
                "value": round(value, 4),
                "as_of": expected_price_as_of,
                "source": snapshots[ticker].get(spec.source_field),
                "basis": snapshots[ticker].get(spec.basis_field),
                "denominator_period": snapshots[ticker].get(
                    spec.denominator_period_field
                ),
                "eligibility": "CAUTION" if cautions else "ELIGIBLE",
                "cautions": cautions,
            }
        )
    quality = _quality(len(values), group_basis)
    if subject_value is None:
        return (
            {
                "available": False,
                "sample_count": len(values),
                "quality": quality,
                "reason": subject_reason,
            },
            {"included": included, "excluded": excluded},
        )
    if len(values) < MINIMUM_PEER_SAMPLE:
        return (
            {
                "available": False,
                "sample_count": len(values),
                "quality": quality,
                "reason": "insufficient_comparable_metric_sample",
            },
            {"included": included, "excluded": excluded},
        )
    peer_median = float(median(values))
    stats = {
        "company_value": round(subject_value, 4),
        "median": round(peer_median, 4),
        "mean": round(mean(values), 4),
        "percentile_25": _percentile(values, 0.25),
        "percentile_75": _percentile(values, 0.75),
        "iqr": round(_percentile(values, 0.75) - _percentile(values, 0.25), 4),
        "minimum": round(min(values), 4),
        "maximum": round(max(values), 4),
        "sample_count": len(values),
        "company_relative_multiple": round(subject_value / peer_median, 4),
        "company_vs_median_pct": round((subject_value / peer_median - 1) * 100, 4),
        "company_cross_section_percentile": _cross_section_percentile(
            [*values, subject_value], subject_value
        ),
        "quality": quality,
        "subject_cautions": subject_cautions,
    }
    if quality == "LOW":
        return (
            {
                "available": False,
                "audit_available": True,
                "reason": "broad_fallback_low_quality",
                **stats,
            },
            {"included": included, "excluded": excluded},
        )
    return ({"available": True, **stats}, {"included": included, "excluded": excluded})


def build_peer_valuation_states(
    session: Session,
    assessments: Iterable[ThesisAssessment],
    assessment_date: date,
    *,
    profile_reader: Callable[[str, object], dict[str, object] | None],
    data_dir: object,
) -> dict[str, dict[str, object]]:
    rows = list(assessments)
    tickers = {row.ticker for row in rows}
    companies = {
        item.ticker: item
        for item in session.exec(select(Company).where(Company.ticker.in_(tickers))).all()
    }
    securities = {
        item.ticker: item
        for item in session.exec(
            select(SecurityMaster).where(SecurityMaster.ticker.in_(tickers))
        ).all()
    }
    snapshots = {row.ticker: _dict(row.valuation_snapshot) for row in rows}
    profiles = {
        ticker: _profile(
            company,
            profile_reader=profile_reader,
            data_dir=data_dir,
        )
        for ticker, company in companies.items()
    }
    identities = {
        ticker: _issuer_identity(securities.get(ticker), ticker) for ticker in companies
    }
    results: dict[str, dict[str, object]] = {}
    for row in rows:
        company = companies.get(row.ticker)
        profile = profiles.get(row.ticker, {})
        if company is None or profile.get("quality") != "verified":
            results[row.ticker] = {
                "available": False,
                "reason": "verified_company_profile_unavailable",
                "provider": PEER_PROVIDER,
                "contract": PEER_SECTOR_VALUATION_CONTRACT,
            }
            continue
        expected_price_as_of = str(snapshots[row.ticker].get("price_as_of") or "")[:10]
        if not expected_price_as_of:
            results[row.ticker] = {
                "available": False,
                "reason": "subject_price_as_of_unavailable",
                "provider": PEER_PROVIDER,
                "contract": PEER_SECTOR_VALUATION_CONTRACT,
            }
            continue
        group_basis, group_value, candidates = _select_group(
            row.ticker, companies, profiles
        )
        if group_basis is None or group_value is None:
            results[row.ticker] = {
                "available": False,
                "reason": "insufficient_verified_peer_universe",
                "provider": PEER_PROVIDER,
                "contract": PEER_SECTOR_VALUATION_CONTRACT,
                "minimum_sample": MINIMUM_PEER_SAMPLE,
                "profile_quality": profile.get("quality"),
            }
            continue
        unique_candidates, duplicate_exclusions = _deduplicate_issuers(
            candidates, identities
        )
        framework = _framework(profile)
        metrics: dict[str, object] = {}
        audit: dict[str, object] = {
            "candidate_tickers": candidates,
            "issuer_deduplicated_tickers": unique_candidates,
            "duplicate_issuer_exclusions": duplicate_exclusions,
            "metrics": {},
        }
        for spec in _METRIC_SPECS:
            metric, metric_audit = _metric_state(
                spec=spec,
                subject=row.ticker,
                candidate_tickers=candidates,
                duplicate_exclusions=duplicate_exclusions,
                snapshots=snapshots,
                profiles=profiles,
                identities=identities,
                group_basis=group_basis,
                expected_price_as_of=expected_price_as_of,
                framework=framework,
            )
            metrics[spec.key] = metric
            audit["metrics"][spec.key] = metric_audit  # type: ignore[index]
        available_metrics = [
            metric
            for metric in metrics.values()
            if isinstance(metric, dict) and metric.get("available") is True
        ]
        quality_order = {"LOW": 0, "MEDIUM": 1, "HIGH": 2}
        sample_quality = max(
            (str(metric.get("quality")) for metric in available_metrics),
            key=lambda quality: quality_order.get(quality, -1),
            default="LOW",
        )
        results[row.ticker] = {
            "available": bool(available_metrics),
            "assessment_date": assessment_date.isoformat(),
            "as_of_date": expected_price_as_of,
            "provider": PEER_PROVIDER,
            "contract": PEER_SECTOR_VALUATION_CONTRACT,
            "peer_scope": "limited_active_monitoring_universe",
            "peer_group": f"{_market(company)}_{group_basis}_{group_value}",
            "peer_group_version": PEER_GROUP_VERSION,
            "group_basis": group_basis,
            "group_value": group_value,
            "minimum_sample": MINIMUM_PEER_SAMPLE,
            "sample_quality": sample_quality,
            "framework": framework,
            "interpretation_contract": _interpretation_contract(framework),
            "metrics": metrics,
            "audit": audit,
        }
    return results
