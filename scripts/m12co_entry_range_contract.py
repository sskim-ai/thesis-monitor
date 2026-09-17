from __future__ import annotations

import json
import re
from collections.abc import Mapping, Sequence
from copy import deepcopy
from datetime import date
from decimal import Decimal, ROUND_HALF_EVEN
from enum import StrEnum

from scripts.m12cn_policy_contract import build_entry_catalog, canonical_sha256


CONTRACT = "m12co-fundamental-entry-candidate-builder-v1"
MATERIALIZATION_CONTRACT = "m12co-entry-selection-materialization-draft-v1"
MIN_HISTORY_OBSERVATIONS = 30
MIN_HISTORY_COVERAGE = Decimal("0.8")
MAX_HISTORY_LAG_DAYS = 14
QUANTILE_BANDS = (
    ("P25_P50", "percentile_25", "percentile_50"),
    ("P50_P75", "percentile_50", "percentile_75"),
    ("P75_P90", "percentile_75", "percentile_90"),
)


class FieldOwner(StrEnum):
    MODEL_JUDGMENT = "MODEL_JUDGMENT"
    DETERMINISTIC_CATALOG_PROJECTION = "DETERMINISTIC_CATALOG_PROJECTION"
    DETERMINISTIC_DERIVED_FIELD = "DETERMINISTIC_DERIVED_FIELD"
    MODEL_PROSE_WITH_HARD_NONNUMERIC_LIMITS = "MODEL_PROSE_WITH_HARD_NONNUMERIC_LIMITS"
    UNRESOLVED_REQUIRES_CHAT = "UNRESOLVED_REQUIRES_CHAT"


class MethodFamily(StrEnum):
    HISTORICAL_TRAILING_PE_QUANTILE = "HISTORICAL_TRAILING_PE_QUANTILE"
    HISTORICAL_PB_QUANTILE = "HISTORICAL_PB_QUANTILE"
    FORWARD_BOOK_HISTORICAL_PB = "FORWARD_BOOK_HISTORICAL_PB"
    FORWARD_EPS_HISTORICAL_TRAILING_PE = "FORWARD_EPS_HISTORICAL_TRAILING_PE"
    EV_SALES_SCENARIO = "EV_SALES_SCENARIO"
    EV_GROSS_PROFIT_SCENARIO = "EV_GROSS_PROFIT_SCENARIO"
    EV_EBITDA_SCENARIO = "EV_EBITDA_SCENARIO"
    FCF_SCENARIO = "FCF_SCENARIO"


def _statement(row: Mapping[str, object] | None) -> dict[str, object]:
    if not isinstance(row, Mapping):
        return {}
    value = row.get("statement")
    if isinstance(value, Mapping):
        return dict(value)
    if isinstance(value, str):
        try:
            parsed = json.loads(value)
        except json.JSONDecodeError:
            return {}
        if isinstance(parsed, dict):
            return parsed
    return {}


def _decimal(value: object) -> Decimal | None:
    if isinstance(value, bool) or not isinstance(value, (int, float, Decimal, str)):
        return None
    try:
        number = Decimal(str(value))
    except Exception:  # noqa: BLE001
        return None
    return number if number.is_finite() else None


def _amount(value: Decimal) -> float:
    return float(value.quantize(Decimal("0.000001"), rounding=ROUND_HALF_EVEN))


def _signed_distance(current: Decimal, low: Decimal, high: Decimal) -> float:
    if low <= current <= high:
        return 0.0
    boundary = low if current < low else high
    return _amount(((boundary - current) / current) * Decimal("100"))


def _evidence_rows(packet: Mapping[str, object]) -> dict[str, Mapping[str, object]]:
    return {
        str(row.get("ref_id") or ""): row
        for row in packet.get("evidence") or []
        if isinstance(row, Mapping) and row.get("ref_id")
    }


def _owned_refs(ownership: Mapping[str, object]) -> set[str]:
    refs = {
        str(ref)
        for group in ("core_ref_ids", "timing_ref_ids")
        for ref in ownership.get(group) or []
    }
    expectation = ownership.get("expectation_valuation")
    if isinstance(expectation, Mapping):
        refs.update(str(ref) for ref in expectation.get("valuation_refs") or [])
    return refs


def _history_check(
    *,
    row: Mapping[str, object] | None,
    statistics_key: str,
    metric: str,
    assessment_date: str,
) -> tuple[dict[str, object], list[str]]:
    reasons: list[str] = []
    statement = _statement(row)
    statistics = statement.get(statistics_key)
    if not isinstance(statistics, Mapping):
        return {}, [f"MISSING_{statistics_key.upper()}"]
    stats = dict(statistics)
    if stats.get("metric") != metric:
        reasons.append("HISTORY_METRIC_MISMATCH")
    if stats.get("history_quality") != "high":
        reasons.append("HISTORY_QUALITY_NOT_HIGH")
    observations = stats.get("deduplicated_observation_count")
    if not isinstance(observations, int) or observations < MIN_HISTORY_OBSERVATIONS:
        reasons.append("HISTORY_OBSERVATIONS_INSUFFICIENT")
    coverage = _decimal(stats.get("history_coverage_ratio"))
    if coverage is None or coverage < MIN_HISTORY_COVERAGE:
        reasons.append("HISTORY_COVERAGE_INSUFFICIENT")
    for _, low_key, high_key in QUANTILE_BANDS:
        low = _decimal(stats.get(low_key))
        high = _decimal(stats.get(high_key))
        if low is None or high is None or low <= 0 or high < low:
            reasons.append(f"INVALID_QUANTILE_PAIR:{low_key}:{high_key}")
    try:
        end = date.fromisoformat(str(stats.get("history_end_date")))
        cutoff = date.fromisoformat(assessment_date)
        lag = (cutoff - end).days
        if lag < 0 or lag > MAX_HISTORY_LAG_DAYS:
            reasons.append("HISTORY_AS_OF_NOT_ALIGNED")
    except ValueError:
        reasons.append("HISTORY_END_DATE_INVALID")
    return stats, sorted(set(reasons))


def _candidate(
    *,
    ticker: str,
    method_family: MethodFamily,
    band_name: str,
    denominator_name: str,
    denominator: Decimal,
    denominator_ref: str,
    low_multiple: Decimal,
    high_multiple: Decimal,
    history_ref: str,
    basis_refs: Sequence[str],
    currency: str,
    assumptions: Sequence[str],
    generally_meaningful_archetypes: Sequence[str],
    conditionally_meaningful_archetypes: Sequence[str],
    current_price: Mapping[str, object] | None,
) -> dict[str, object]:
    low = denominator * low_multiple
    high = denominator * high_multiple
    identity = {
        "ticker": ticker,
        "method_family": method_family.value,
        "method_version": "v1",
        "quantile_band": band_name,
        "denominator_name": denominator_name,
        "denominator": str(denominator),
        "low_multiple": str(low_multiple),
        "high_multiple": str(high_multiple),
        "currency": currency,
        "evidence_refs": sorted({denominator_ref, history_ref, *basis_refs}),
    }
    result: dict[str, object] = {
        "contract": CONTRACT,
        "candidate_id": f"fundamental:{canonical_sha256(identity)[:24]}",
        "ticker": ticker,
        "method_family": method_family.value,
        "method_version": "v1",
        "quantile_band": band_name,
        "low": _amount(low),
        "high": _amount(high),
        "currency": currency,
        "formula": f"{denominator_name} * historical_multiple_quantile",
        "formula_inputs": {
            "denominator_name": denominator_name,
            "denominator_value": float(denominator),
            "denominator_ref": denominator_ref,
            "multiple_low": float(low_multiple),
            "multiple_high": float(high_multiple),
            "history_ref": history_ref,
        },
        "evidence_refs": identity["evidence_refs"],
        "generally_meaningful_archetypes": list(generally_meaningful_archetypes),
        "conditionally_meaningful_archetypes": list(conditionally_meaningful_archetypes),
        "quality_state": "ARITHMETICALLY_SAFE_POLICY_SELECTION_REQUIRED",
        "assumptions": list(assumptions),
        "disqualifying_reasons": [],
        "entry_candidate_not_price_target": True,
        "current_price_context": None,
    }
    if isinstance(current_price, Mapping):
        current = _decimal(current_price.get("value"))
        if current is not None and current > 0 and current_price.get("currency") == currency:
            result["current_price_context"] = {
                "value": float(current),
                "currency": currency,
                "as_of": current_price.get("as_of"),
                "ref_id": current_price.get("ref_id"),
                "distance_to_band_pct": _signed_distance(current, low, high),
                "used_in_candidate_formula": False,
            }
    return result


def _pb_candidates(
    *,
    ticker: str,
    rows: Mapping[str, Mapping[str, object]],
    owned_refs: set[str],
    assessment_date: str,
    current_price: Mapping[str, object] | None,
) -> tuple[list[dict[str, object]], list[str], dict[str, object]]:
    required = {
        "canonical:valuation:book_quality",
        "canonical:valuation:book_value",
        "canonical:valuation:historical_pb",
    }
    reasons = [f"REF_NOT_OWNED:{ref}" for ref in sorted(required - owned_refs)]
    quality = _statement(rows.get("canonical:valuation:book_quality"))
    book = _statement(rows.get("canonical:valuation:book_value"))
    stats, history_reasons = _history_check(
        row=rows.get("canonical:valuation:historical_pb"),
        statistics_key="historical_pb_statistics",
        metric="price_to_book",
        assessment_date=assessment_date,
    )
    reasons.extend(history_reasons)
    bvps = _decimal(book.get("bvps"))
    quality_bvps = _decimal(quality.get("bvps"))
    if bvps is None or bvps <= 0:
        reasons.append("BVPS_NOT_POSITIVE")
    if quality_bvps is None or bvps is None or quality_bvps != bvps:
        reasons.append("BVPS_SOURCE_MISMATCH")
    if quality.get("status") != "passed":
        reasons.append("BOOK_QUALITY_NOT_PASSED")
    if quality.get("price_to_book_basis_status") != "directly_comparable":
        reasons.append("BOOK_BASIS_NOT_DIRECTLY_COMPARABLE")
    if quality.get("book_share_basis") != "current_security":
        reasons.append("BOOK_SHARE_BASIS_NOT_CURRENT_SECURITY")
    book_currency = quality.get("book_currency")
    price_currency = quality.get("price_currency")
    if not isinstance(book_currency, str) or not book_currency or book_currency != price_currency:
        reasons.append("BOOK_PRICE_CURRENCY_MISMATCH")
    if not isinstance(current_price, Mapping) or current_price.get("currency") != price_currency:
        reasons.append("CURRENT_PRICE_CURRENCY_MISMATCH")
    reasons = sorted(set(reasons))
    diagnostics = {
        "method_family": MethodFamily.HISTORICAL_PB_QUANTILE.value,
        "arithmetic_feasible": not reasons,
        "economically_suitable": "CHAT_POLICY_SELECTION_REQUIRED",
        "required_refs": sorted(required),
        "rejected_reasons": reasons,
    }
    if reasons or bvps is None or not isinstance(book_currency, str):
        return [], reasons, diagnostics
    candidates = []
    for band, low_key, high_key in QUANTILE_BANDS:
        candidates.append(
            _candidate(
                ticker=ticker,
                method_family=MethodFamily.HISTORICAL_PB_QUANTILE,
                band_name=band,
                denominator_name="positive_current_security_bvps",
                denominator=bvps,
                denominator_ref="canonical:valuation:book_value",
                low_multiple=Decimal(str(stats[low_key])),
                high_multiple=Decimal(str(stats[high_key])),
                history_ref="canonical:valuation:historical_pb",
                basis_refs=("canonical:valuation:book_quality",),
                currency=book_currency,
                assumptions=(
                    "positive directly comparable current-security BVPS",
                    "high-quality historical P/B distribution",
                    "historical percentile is descriptive, not normative fair value",
                ),
                generally_meaningful_archetypes=(
                    "STRUCTURAL_CYCLICAL_LEADER",
                    "MATURE_VALUE_DEFENSIVE",
                ),
                conditionally_meaningful_archetypes=(
                    "DURABLE_FRANCHISE",
                    "PROFITABLE_PREMIUM_GROWTH",
                    "EXECUTION_DEPENDENT_GROWTH",
                ),
                current_price=current_price,
            )
        )
    return candidates, [], diagnostics


def _pe_candidates(
    *,
    ticker: str,
    rows: Mapping[str, Mapping[str, object]],
    owned_refs: set[str],
    assessment_date: str,
    current_price: Mapping[str, object] | None,
) -> tuple[list[dict[str, object]], list[str], dict[str, object]]:
    required = {
        "canonical:valuation:trailing_earnings",
        "canonical:valuation:historical_pe",
        "canonical:valuation:multiple_relation",
    }
    reasons = [f"REF_NOT_OWNED:{ref}" for ref in sorted(required - owned_refs)]
    trailing = _statement(rows.get("canonical:valuation:trailing_earnings"))
    relation = _statement(rows.get("canonical:valuation:multiple_relation"))
    stats, history_reasons = _history_check(
        row=rows.get("canonical:valuation:historical_pe"),
        statistics_key="historical_pe_statistics",
        metric="trailing_pe",
        assessment_date=assessment_date,
    )
    reasons.extend(history_reasons)
    eps = _decimal(trailing.get("ttm_eps"))
    trailing_pe = _decimal(trailing.get("trailing_pe"))
    if eps is None or eps <= 0:
        reasons.append("TTM_EPS_NOT_POSITIVE")
    if trailing_pe is None or trailing_pe <= 0:
        reasons.append("TRAILING_PE_NOT_POSITIVE")
    safe_relation = (
        relation.get("basis_comparable") is True
        and relation.get("interpretation_eligibility") == "eligible"
        and relation.get("trailing_basis_status") == "directly_comparable"
        and relation.get("trailing_share_basis") == "current_security"
        and relation.get("security_basis") == "verified_non_depositary"
        and relation.get("currency_basis") == relation.get("price_currency")
    )
    if not safe_relation:
        reasons.append("TRAILING_EARNINGS_SECURITY_BASIS_UNRESOLVED")
    relation_pe = _decimal(relation.get("trailing_value"))
    if trailing_pe is None or relation_pe is None or trailing_pe != relation_pe:
        reasons.append("TRAILING_PE_RELATION_MISMATCH")
    currency = relation.get("currency_basis")
    current = _decimal(current_price.get("value")) if isinstance(current_price, Mapping) else None
    if (
        not isinstance(currency, str)
        or not currency
        or not isinstance(current_price, Mapping)
        or current_price.get("currency") != currency
    ):
        reasons.append("CURRENT_PRICE_CURRENCY_MISMATCH")
    if eps is not None and eps > 0 and current is not None and trailing_pe is not None:
        implied = (current / eps).quantize(Decimal("0.0001"), rounding=ROUND_HALF_EVEN)
        if implied != trailing_pe.quantize(Decimal("0.0001"), rounding=ROUND_HALF_EVEN):
            reasons.append("CURRENT_PRICE_EPS_MULTIPLE_IDENTITY_MISMATCH")
    reasons = sorted(set(reasons))
    diagnostics = {
        "method_family": MethodFamily.HISTORICAL_TRAILING_PE_QUANTILE.value,
        "arithmetic_feasible": not reasons,
        "economically_suitable": "CHAT_POLICY_SELECTION_REQUIRED",
        "required_refs": sorted(required),
        "rejected_reasons": reasons,
    }
    if reasons or eps is None or not isinstance(currency, str):
        return [], reasons, diagnostics
    candidates = []
    for band, low_key, high_key in QUANTILE_BANDS:
        candidates.append(
            _candidate(
                ticker=ticker,
                method_family=MethodFamily.HISTORICAL_TRAILING_PE_QUANTILE,
                band_name=band,
                denominator_name="positive_current_security_ttm_eps",
                denominator=eps,
                denominator_ref="canonical:valuation:trailing_earnings",
                low_multiple=Decimal(str(stats[low_key])),
                high_multiple=Decimal(str(stats[high_key])),
                history_ref="canonical:valuation:historical_pe",
                basis_refs=("canonical:valuation:multiple_relation",),
                currency=currency,
                assumptions=(
                    "positive directly comparable current-security TTM EPS",
                    "high-quality historical trailing-P/E distribution",
                    "historical percentile is descriptive, not normative fair value",
                ),
                generally_meaningful_archetypes=(
                    "DURABLE_FRANCHISE",
                    "PROFITABLE_PREMIUM_GROWTH",
                    "MATURE_VALUE_DEFENSIVE",
                ),
                conditionally_meaningful_archetypes=(
                    "STRUCTURAL_CYCLICAL_LEADER",
                    "EXECUTION_DEPENDENT_GROWTH",
                ),
                current_price=current_price,
            )
        )
    return candidates, [], diagnostics


def _key_inventory(rows: Mapping[str, Mapping[str, object]]) -> set[str]:
    keys: set[str] = set()

    def visit(value: object) -> None:
        if isinstance(value, Mapping):
            for key, child in value.items():
                keys.add(str(key).casefold())
                visit(child)
        elif isinstance(value, list):
            for child in value:
                visit(child)

    for ref, row in rows.items():
        if ref.startswith("canonical:"):
            visit(_statement(row))
    return keys


def _non_materialized_method_diagnostics(
    rows: Mapping[str, Mapping[str, object]],
) -> list[dict[str, object]]:
    inventory = _key_inventory(rows)
    forward_book = _statement(rows.get("canonical:valuation:modeled_forward_book"))
    forward_earnings = _statement(rows.get("canonical:valuation:consensus_forward_earnings"))
    if not forward_earnings:
        forward_earnings = _statement(rows.get("canonical:valuation:modeled_forward_earnings"))
    historical_pb = _statement(rows.get("canonical:valuation:historical_pb"))
    historical_pe = _statement(rows.get("canonical:valuation:historical_pe"))
    result = [
        {
            "method_family": MethodFamily.FORWARD_BOOK_HISTORICAL_PB.value,
            "arithmetic_feasible": bool(forward_book and historical_pb),
            "candidate_emitted": False,
            "rejected_reasons": (
                ["FORWARD_BOOK_HISTORICAL_PB_BASIS_UNRESOLVED"]
                if forward_book and historical_pb
                else ["MISSING_FORWARD_BOOK_OR_HISTORICAL_PB"]
            ),
        },
        {
            "method_family": MethodFamily.FORWARD_EPS_HISTORICAL_TRAILING_PE.value,
            "arithmetic_feasible": bool(forward_earnings.get("forward_eps") and historical_pe),
            "candidate_emitted": False,
            "rejected_reasons": (
                ["FORWARD_EPS_HISTORICAL_TRAILING_PE_BASIS_MISMATCH"]
                if forward_earnings.get("forward_eps") and historical_pe
                else ["MISSING_FORWARD_EPS_OR_HISTORICAL_PE"]
            ),
        },
    ]
    requirements = {
        MethodFamily.EV_SALES_SCENARIO: (
            {"enterprise_value", "revenue_scenario"},
            "MISSING_EV_AND_REVENUE_SCENARIO_INPUTS",
        ),
        MethodFamily.EV_GROSS_PROFIT_SCENARIO: (
            {"enterprise_value", "gross_profit_scenario"},
            "MISSING_EV_AND_GROSS_PROFIT_SCENARIO_INPUTS",
        ),
        MethodFamily.EV_EBITDA_SCENARIO: (
            {"enterprise_value", "normalized_future_ebitda"},
            "MISSING_EV_AND_NORMALIZED_EBITDA_INPUTS",
        ),
        MethodFamily.FCF_SCENARIO: (
            {"fcf_scenario", "diluted_share_count"},
            "MISSING_FCF_SCENARIO_AND_DILUTED_SHARE_INPUTS",
        ),
    }
    for family, (required, reason) in requirements.items():
        available = sorted(required & inventory)
        result.append(
            {
                "method_family": family.value,
                "arithmetic_feasible": required.issubset(inventory),
                "candidate_emitted": False,
                "available_required_fields": available,
                "missing_required_fields": sorted(required - inventory),
                "rejected_reasons": [reason],
            }
        )
    return result


def _method_disagreement(candidates: Sequence[Mapping[str, object]]) -> dict[str, object]:
    by_family: dict[str, dict[str, Mapping[str, object]]] = {}
    for candidate in candidates:
        by_family.setdefault(str(candidate["method_family"]), {})[
            str(candidate["quantile_band"])
        ] = candidate
    if not by_family:
        return {
            "status": "NO_SAFE_FUNDAMENTAL_METHOD",
            "magnitude": "NOT_APPLICABLE",
            "pairwise": [],
        }
    if len(by_family) == 1:
        return {
            "status": "SINGLE_METHOD_ONLY",
            "magnitude": "NOT_APPLICABLE",
            "pairwise": [],
        }
    families = sorted(by_family)
    left, right = families[:2]
    pairwise = []
    overlap_count = 0
    gap_ratios: list[Decimal] = []
    for band, _, _ in QUANTILE_BANDS:
        first = by_family[left].get(band)
        second = by_family[right].get(band)
        if first is None or second is None:
            continue
        first_low = Decimal(str(first["low"]))
        first_high = Decimal(str(first["high"]))
        second_low = Decimal(str(second["low"]))
        second_high = Decimal(str(second["high"]))
        overlap_low = max(first_low, second_low)
        overlap_high = min(first_high, second_high)
        overlaps = overlap_low <= overlap_high
        gap = (
            Decimal("0") if overlaps else max(first_low, second_low) - min(first_high, second_high)
        )
        narrower_width = min(first_high - first_low, second_high - second_low)
        gap_ratio = gap / narrower_width if narrower_width > 0 else Decimal("0")
        if overlaps:
            overlap_count += 1
        else:
            gap_ratios.append(gap_ratio)
        pairwise.append(
            {
                "quantile_band": band,
                "left_method": left,
                "right_method": right,
                "overlaps": overlaps,
                "overlap_low": _amount(overlap_low) if overlaps else None,
                "overlap_high": _amount(overlap_high) if overlaps else None,
                "gap": _amount(gap),
                "gap_to_narrower_band_width": _amount(gap_ratio),
            }
        )
    if overlap_count:
        magnitude = (
            "OVERLAP_ALL_MATCHED_BANDS"
            if overlap_count == len(pairwise)
            else "PARTIAL_MATCHED_BAND_OVERLAP"
        )
        status = "METHODS_OVERLAP"
    else:
        magnitude = (
            "NON_OVERLAP_GAP_AT_LEAST_ONE_NARROWER_BAND_WIDTH"
            if any(value >= 1 for value in gap_ratios)
            else "NON_OVERLAP_GAP_BELOW_ONE_NARROWER_BAND_WIDTH"
        )
        status = "METHODS_DIVERGE"
    return {"status": status, "magnitude": magnitude, "pairwise": pairwise}


def _historical_regime_diagnostics(
    *,
    rows: Mapping[str, Mapping[str, object]],
    ownership: Mapping[str, object],
    candidates: Sequence[Mapping[str, object]],
    disagreement: Mapping[str, object],
) -> dict[str, object]:
    methods: list[dict[str, object]] = []
    for family, ref_id, statistics_key in (
        (
            MethodFamily.HISTORICAL_TRAILING_PE_QUANTILE,
            "canonical:valuation:historical_pe",
            "historical_pe_statistics",
        ),
        (
            MethodFamily.HISTORICAL_PB_QUANTILE,
            "canonical:valuation:historical_pb",
            "historical_pb_statistics",
        ),
    ):
        statistics = _statement(rows.get(ref_id)).get(statistics_key)
        stats = dict(statistics) if isinstance(statistics, Mapping) else {}
        family_candidates = [row for row in candidates if row.get("method_family") == family.value]
        methods.append(
            {
                "method_family": family.value,
                "history_ref": ref_id if stats else None,
                "current_percentile": stats.get("current_percentile"),
                "current_multiple": stats.get("current_value"),
                "historical_quantiles": {
                    key: stats.get(key)
                    for key in (
                        "percentile_25",
                        "percentile_50",
                        "percentile_75",
                        "percentile_90",
                    )
                },
                "history_quality": stats.get("history_quality"),
                "deduplicated_observation_count": stats.get("deduplicated_observation_count"),
                "history_coverage_ratio": stats.get("history_coverage_ratio"),
                "history_start_date": stats.get("history_start_date"),
                "history_end_date": stats.get("history_end_date"),
                "premium_band_candidate_exists": any(
                    row.get("quantile_band") == "P75_P90" for row in family_candidates
                ),
            }
        )
    trailing = _statement(rows.get("canonical:valuation:trailing_earnings"))
    eps = _decimal(trailing.get("ttm_eps"))
    if eps is None:
        earnings_state = "UNAVAILABLE"
    elif eps > 0:
        earnings_state = "POSITIVE_TTM_EPS"
    elif eps == 0:
        earnings_state = "ZERO_TTM_EPS"
    else:
        earnings_state = "NEGATIVE_TTM_EPS"
    core_context_refs = sorted(
        str(ref)
        for ref in ownership.get("core_ref_ids") or []
        if str(ref) in rows and not str(ref).startswith("canonical:valuation:")
    )
    return {
        "historical_distribution_role": "DESCRIPTIVE_NOT_NORMATIVE_FAIR_VALUE",
        "ttm_eps_state": earnings_state,
        "ttm_eps_ref": ("canonical:valuation:trailing_earnings" if trailing else None),
        "structural_thesis_change": {
            "status": "NOT_DETERMINISTICALLY_CLASSIFIED",
            "available_core_context_refs": core_context_refs,
            "requires_chat_policy_selection": True,
        },
        "method_disagreement_status": disagreement["status"],
        "methods": methods,
    }


def build_subject_candidate_coverage(
    *,
    market: str,
    packet: Mapping[str, object],
    ownership: Mapping[str, object],
) -> dict[str, object]:
    ticker = str(packet.get("ticker") or "")
    assessment_date = str(packet.get("assessment_date") or "")
    rows = _evidence_rows(packet)
    refs = _owned_refs(ownership)
    r2_catalog = build_entry_catalog(packet, ownership)
    current_price = r2_catalog.get("current_price")
    pb_candidates, _, pb_diagnostics = _pb_candidates(
        ticker=ticker,
        rows=rows,
        owned_refs=refs,
        assessment_date=assessment_date,
        current_price=current_price if isinstance(current_price, Mapping) else None,
    )
    pe_candidates, _, pe_diagnostics = _pe_candidates(
        ticker=ticker,
        rows=rows,
        owned_refs=refs,
        assessment_date=assessment_date,
        current_price=current_price if isinstance(current_price, Mapping) else None,
    )
    candidates = sorted(
        [*pe_candidates, *pb_candidates],
        key=lambda row: (
            str(row["method_family"]),
            str(row["quantile_band"]),
            str(row["candidate_id"]),
        ),
    )
    method_diagnostics = [
        pe_diagnostics,
        pb_diagnostics,
        *_non_materialized_method_diagnostics(rows),
    ]
    disagreement = _method_disagreement(candidates)
    return {
        "contract": "m12co-subject-method-coverage-v1",
        "market": market,
        "ticker": ticker,
        "assessment_date": assessment_date,
        "available_valuation_facts": sorted(
            ref for ref in rows if ref.startswith("canonical:valuation:")
        ),
        "current_price": deepcopy(current_price),
        "tactical_candidates": deepcopy(r2_catalog.get("tactical_candidates") or []),
        "tactical_candidate_count": len(r2_catalog.get("tactical_candidates") or []),
        "fundamental_candidates": candidates,
        "fundamental_candidate_count": len(candidates),
        "safe_method_families": sorted({str(row["method_family"]) for row in candidates}),
        "method_feasibility": method_diagnostics,
        "method_disagreement": disagreement,
        "historical_regime_diagnostics": _historical_regime_diagnostics(
            rows=rows,
            ownership=ownership,
            candidates=candidates,
            disagreement=disagreement,
        ),
        "unresolved_policy": deepcopy(r2_catalog.get("unresolved_policy") or {}),
    }


def field_ownership_audit() -> dict[str, object]:
    rows = [
        ("entry_range.entry_range_status", FieldOwner.DETERMINISTIC_DERIVED_FIELD),
        ("entry_range.entry_option_id", FieldOwner.DETERMINISTIC_CATALOG_PROJECTION),
        ("entry_range.current_price", FieldOwner.DETERMINISTIC_CATALOG_PROJECTION),
        ("entry_range.current_price_as_of", FieldOwner.DETERMINISTIC_CATALOG_PROJECTION),
        ("entry_range.current_price_ref", FieldOwner.DETERMINISTIC_CATALOG_PROJECTION),
        ("entry_range.preferred_entry_low", FieldOwner.DETERMINISTIC_DERIVED_FIELD),
        ("entry_range.preferred_entry_high", FieldOwner.DETERMINISTIC_DERIVED_FIELD),
        ("entry_range.distance_to_band_pct", FieldOwner.DETERMINISTIC_DERIVED_FIELD),
        ("entry_range.fundamental_entry_band.status", FieldOwner.DETERMINISTIC_DERIVED_FIELD),
        (
            "entry_range.fundamental_entry_band.candidate_id",
            FieldOwner.DETERMINISTIC_CATALOG_PROJECTION,
        ),
        ("entry_range.fundamental_entry_band.low", FieldOwner.DETERMINISTIC_CATALOG_PROJECTION),
        ("entry_range.fundamental_entry_band.high", FieldOwner.DETERMINISTIC_CATALOG_PROJECTION),
        (
            "entry_range.fundamental_entry_band.currency",
            FieldOwner.DETERMINISTIC_CATALOG_PROJECTION,
        ),
        (
            "entry_range.fundamental_entry_band.evidence_refs",
            FieldOwner.DETERMINISTIC_CATALOG_PROJECTION,
        ),
        ("entry_range.tactical_entry_band.status", FieldOwner.DETERMINISTIC_DERIVED_FIELD),
        (
            "entry_range.tactical_entry_band.candidate_id",
            FieldOwner.DETERMINISTIC_CATALOG_PROJECTION,
        ),
        ("entry_range.tactical_entry_band.low", FieldOwner.DETERMINISTIC_CATALOG_PROJECTION),
        ("entry_range.tactical_entry_band.high", FieldOwner.DETERMINISTIC_CATALOG_PROJECTION),
        (
            "entry_range.tactical_entry_band.currency",
            FieldOwner.DETERMINISTIC_CATALOG_PROJECTION,
        ),
        (
            "entry_range.tactical_entry_band.evidence_refs",
            FieldOwner.DETERMINISTIC_CATALOG_PROJECTION,
        ),
        ("entry_range.method", FieldOwner.DETERMINISTIC_CATALOG_PROJECTION),
        ("entry_range.combination_rule", FieldOwner.DETERMINISTIC_DERIVED_FIELD),
        ("entry_range.valuation_basis_refs", FieldOwner.DETERMINISTIC_CATALOG_PROJECTION),
        ("entry_range.technical_basis_refs", FieldOwner.DETERMINISTIC_CATALOG_PROJECTION),
        ("entry_range.assumptions", FieldOwner.DETERMINISTIC_CATALOG_PROJECTION),
        ("entry_range.unresolved_inputs", FieldOwner.DETERMINISTIC_CATALOG_PROJECTION),
        (
            "entry_range.re_evaluate_conditions",
            FieldOwner.MODEL_PROSE_WITH_HARD_NONNUMERIC_LIMITS,
        ),
    ]
    draft_choices = [
        ("selection.fundamental_choice", FieldOwner.MODEL_JUDGMENT),
        ("selection.tactical_choice", FieldOwner.MODEL_JUDGMENT),
    ]
    output = [
        {
            "field": field,
            "owner": owner.value,
            "model_authors_final_value": owner
            in {FieldOwner.MODEL_JUDGMENT, FieldOwner.MODEL_PROSE_WITH_HARD_NONNUMERIC_LIMITS},
        }
        for field, owner in [*rows, *draft_choices]
    ]
    return {
        "contract": "m12co-entry-range-field-ownership-audit-v1",
        "current_entry_range_field_count": len(rows),
        "draft_selection_field_count": len(draft_choices),
        "duplicate_field_count": len(output) - len({row["field"] for row in output}),
        "fields": output,
        "status": "PASS",
    }


def _validate_re_evaluate_conditions(values: Sequence[str]) -> tuple[str, ...]:
    if len(values) > 3:
        raise ValueError("too_many_re_evaluate_conditions")
    result = []
    for value in values:
        text = str(value).strip()
        if not text or len(text) > 300:
            raise ValueError("re_evaluate_condition_length_invalid")
        if re.search(r"\d", text):
            raise ValueError("re_evaluate_condition_numeric_content_forbidden")
        result.append(text)
    return tuple(result)


def _null_band(status: str) -> dict[str, object]:
    return {
        "status": status,
        "candidate_id": None,
        "low": None,
        "high": None,
        "currency": None,
        "evidence_refs": [],
    }


def _project_band(candidate: Mapping[str, object]) -> dict[str, object]:
    return {
        "status": "RESOLVED",
        "candidate_id": candidate["candidate_id"],
        "low": candidate["low"],
        "high": candidate["high"],
        "currency": candidate["currency"],
        "evidence_refs": list(candidate["evidence_refs"]),
    }


def materialize_entry_range(
    *,
    ticker: str,
    new_buyer: str,
    catalog: Mapping[str, object],
    fundamental_choice: str | None,
    tactical_choice: str | None,
    re_evaluate_conditions: Sequence[str] = (),
) -> dict[str, object]:
    if str(catalog.get("ticker")) != ticker:
        raise ValueError("catalog_ticker_mismatch")
    prose = _validate_re_evaluate_conditions(re_evaluate_conditions)
    if new_buyer != "WAIT":
        if prose:
            raise ValueError("non_wait_re_evaluate_conditions_forbidden")
        if fundamental_choice not in {None, "NOT_APPLICABLE"} or tactical_choice not in {
            None,
            "NOT_APPLICABLE",
        }:
            raise ValueError("non_wait_candidate_injection_forbidden")
        return {
            "contract": MATERIALIZATION_CONTRACT,
            "entry_range_status": "NOT_APPLICABLE",
            "entry_option_id": None,
            "current_price": None,
            "current_price_as_of": None,
            "current_price_ref": None,
            "preferred_entry_low": None,
            "preferred_entry_high": None,
            "distance_to_band_pct": None,
            "fundamental_entry_band": _null_band("NOT_APPLICABLE"),
            "tactical_entry_band": _null_band("NOT_APPLICABLE"),
            "method": "NOT_APPLICABLE",
            "combination_rule": "NOT_APPLICABLE",
            "valuation_basis_refs": [],
            "technical_basis_refs": [],
            "assumptions": [],
            "unresolved_inputs": [],
            "re_evaluate_conditions": [],
        }
    fundamental = {
        str(row["candidate_id"]): row
        for row in catalog.get("fundamental_candidates") or []
        if isinstance(row, Mapping)
    }
    tactical = {
        str(row["candidate_id"]): row
        for row in catalog.get("tactical_candidates") or []
        if isinstance(row, Mapping)
    }
    if fundamental_choice != "UNRESOLVED" and fundamental_choice not in fundamental:
        raise ValueError("unknown_or_cross_ticker_fundamental_candidate")
    if tactical_choice != "UNRESOLVED" and tactical_choice not in tactical:
        raise ValueError("unknown_or_cross_ticker_tactical_candidate")
    if (
        fundamental_choice != "UNRESOLVED"
        and str(fundamental[fundamental_choice].get("ticker")) != ticker
    ):
        raise ValueError("cross_ticker_fundamental_candidate")
    current = catalog.get("current_price")
    if not isinstance(current, Mapping):
        raise ValueError("current_price_context_missing")
    unresolved_policy = catalog.get("unresolved_policy")
    if not isinstance(unresolved_policy, Mapping):
        raise ValueError("unresolved_policy_missing")
    unresolved: list[str] = []
    if fundamental_choice == "UNRESOLVED":
        fundamental_band = _null_band("UNRESOLVED")
        unresolved.append(str(unresolved_policy["fundamental_unresolved_reason"]))
        fundamental_row = None
    else:
        fundamental_row = fundamental[fundamental_choice]
        fundamental_band = _project_band(fundamental_row)
    if tactical_choice == "UNRESOLVED":
        tactical_band = _null_band("UNRESOLVED")
        unresolved.append(str(unresolved_policy["tactical_unresolved_reason"]))
        tactical_row = None
    else:
        tactical_row = tactical[tactical_choice]
        tactical_band = _project_band(tactical_row)
    if fundamental_row is None:
        preferred_low = preferred_high = distance = None
        method = "UNRESOLVED"
        combination = "UNRESOLVED"
        option_id = None
        valuation_refs: list[str] = []
        assumptions: list[str] = []
    else:
        preferred_low = Decimal(str(fundamental_row["low"]))
        preferred_high = Decimal(str(fundamental_row["high"]))
        combination = "FUNDAMENTAL_ONLY"
        if tactical_row is not None:
            if tactical_row["currency"] != fundamental_row["currency"]:
                raise ValueError("fundamental_tactical_currency_mismatch")
            overlap_low = max(preferred_low, Decimal(str(tactical_row["low"])))
            overlap_high = min(preferred_high, Decimal(str(tactical_row["high"])))
            if overlap_low <= overlap_high:
                preferred_low, preferred_high = overlap_low, overlap_high
                combination = "OVERLAP_INTERSECTION"
            else:
                combination = "FUNDAMENTAL_PRIMARY_NO_OVERLAP"
        current_value = Decimal(str(current["value"]))
        distance = _signed_distance(current_value, preferred_low, preferred_high)
        method = fundamental_row["method_family"]
        valuation_refs = list(fundamental_row["evidence_refs"])
        assumptions = list(fundamental_row["assumptions"])
        option_identity = {
            "ticker": ticker,
            "fundamental_candidate_id": fundamental_row["candidate_id"],
            "tactical_candidate_id": tactical_row["candidate_id"] if tactical_row else None,
            "combination_rule": combination,
        }
        option_id = f"option:{canonical_sha256(option_identity)[:24]}"
        preferred_low = _amount(preferred_low)
        preferred_high = _amount(preferred_high)
    return {
        "contract": MATERIALIZATION_CONTRACT,
        "entry_range_status": (
            "ENTRY_RANGE_RESOLVED" if fundamental_row is not None else "ENTRY_RANGE_UNRESOLVED"
        ),
        "entry_option_id": option_id,
        "current_price": current["value"],
        "current_price_as_of": current.get("as_of"),
        "current_price_ref": current.get("ref_id"),
        "preferred_entry_low": preferred_low,
        "preferred_entry_high": preferred_high,
        "distance_to_band_pct": distance,
        "fundamental_entry_band": fundamental_band,
        "tactical_entry_band": tactical_band,
        "method": method,
        "combination_rule": combination,
        "valuation_basis_refs": valuation_refs,
        "technical_basis_refs": (
            list(tactical_row["evidence_refs"]) if tactical_row is not None else []
        ),
        "assumptions": assumptions,
        "unresolved_inputs": unresolved,
        "re_evaluate_conditions": list(prose),
    }


def generic_materialization_control_matrix() -> dict[str, object]:
    fundamental = {
        "candidate_id": "fundamental:generic-a",
        "ticker": "GENERIC_A",
        "method_family": MethodFamily.HISTORICAL_PB_QUANTILE.value,
        "low": 80.0,
        "high": 100.0,
        "currency": "USD",
        "evidence_refs": ["valuation:book", "valuation:history"],
        "assumptions": ["generic source-owned assumption"],
    }
    tactical = {
        "candidate_id": "tactical:generic-a",
        "low": 90.0,
        "high": 110.0,
        "currency": "USD",
        "evidence_refs": ["technical:support"],
    }
    catalog = {
        "ticker": "GENERIC_A",
        "current_price": {
            "value": 120.0,
            "currency": "USD",
            "as_of": "2026-09-17",
            "ref_id": "price:current",
        },
        "fundamental_candidates": [fundamental],
        "tactical_candidates": [tactical],
        "unresolved_policy": {
            "fundamental_unresolved_reason": "no safe fundamental candidate",
            "tactical_unresolved_reason": "no safe tactical candidate",
        },
    }
    resolved = materialize_entry_range(
        ticker="GENERIC_A",
        new_buyer="WAIT",
        catalog=catalog,
        fundamental_choice="fundamental:generic-a",
        tactical_choice="tactical:generic-a",
        re_evaluate_conditions=("사업 조건이 달라질 때 재검토",),
    )
    unresolved = materialize_entry_range(
        ticker="GENERIC_A",
        new_buyer="WAIT",
        catalog=catalog,
        fundamental_choice="UNRESOLVED",
        tactical_choice="tactical:generic-a",
    )
    renamed_catalog = deepcopy(catalog)
    renamed_catalog["ticker"] = "RENAMED_GENERIC"
    renamed_fundamental = deepcopy(fundamental)
    renamed_fundamental["ticker"] = "RENAMED_GENERIC"
    renamed_catalog["fundamental_candidates"] = [renamed_fundamental]
    renamed = materialize_entry_range(
        ticker="RENAMED_GENERIC",
        new_buyer="WAIT",
        catalog=renamed_catalog,
        fundamental_choice="fundamental:generic-a",
        tactical_choice="UNRESOLVED",
    )
    checks = {
        "selected_candidate_materializes_exact_refs": resolved["valuation_basis_refs"]
        == fundamental["evidence_refs"],
        "selected_candidate_materializes_exact_numbers": (
            resolved["fundamental_entry_band"]["low"] == 80.0
            and resolved["fundamental_entry_band"]["high"] == 100.0
        ),
        "unresolved_fundamental_has_no_valuation_metadata": (
            unresolved["valuation_basis_refs"] == [] and unresolved["assumptions"] == []
        ),
        "tactical_does_not_become_fundamental": (
            unresolved["preferred_entry_low"] is None
            and unresolved["entry_range_status"] == "ENTRY_RANGE_UNRESOLVED"
        ),
        "renamed_generic_identity_behaves_identically": (
            renamed["fundamental_entry_band"] == resolved["fundamental_entry_band"]
            and renamed["valuation_basis_refs"] == resolved["valuation_basis_refs"]
        ),
    }
    negative_checks: dict[str, bool] = {}
    cases = {
        "nonexistent_candidate_fails_closed": {
            "ticker": "GENERIC_A",
            "new_buyer": "WAIT",
            "catalog": catalog,
            "fundamental_choice": "fundamental:missing",
            "tactical_choice": "UNRESOLVED",
        },
        "cross_ticker_catalog_fails_closed": {
            "ticker": "GENERIC_B",
            "new_buyer": "WAIT",
            "catalog": catalog,
            "fundamental_choice": "fundamental:generic-a",
            "tactical_choice": "UNRESOLVED",
        },
        "cross_ticker_candidate_fails_closed": {
            "ticker": "GENERIC_A",
            "new_buyer": "WAIT",
            "catalog": {
                **catalog,
                "fundamental_candidates": [{**fundamental, "ticker": "GENERIC_B"}],
            },
            "fundamental_choice": "fundamental:generic-a",
            "tactical_choice": "UNRESOLVED",
        },
        "tactical_as_fundamental_fails_closed": {
            "ticker": "GENERIC_A",
            "new_buyer": "WAIT",
            "catalog": catalog,
            "fundamental_choice": "tactical:generic-a",
            "tactical_choice": "UNRESOLVED",
        },
        "non_wait_candidate_injection_fails_closed": {
            "ticker": "GENERIC_A",
            "new_buyer": "ATTRACTIVE",
            "catalog": catalog,
            "fundamental_choice": "fundamental:generic-a",
            "tactical_choice": None,
        },
        "non_wait_prose_injection_fails_closed": {
            "ticker": "GENERIC_A",
            "new_buyer": "ATTRACTIVE",
            "catalog": catalog,
            "fundamental_choice": None,
            "tactical_choice": None,
            "re_evaluate_conditions": ("business conditions change",),
        },
    }
    for name, payload in cases.items():
        try:
            materialize_entry_range(**payload)
        except ValueError:
            negative_checks[name] = True
        else:
            negative_checks[name] = False
    checks.update(negative_checks)
    return {
        "contract": "m12co-generic-materialization-control-matrix-v1",
        "checks": checks,
        "status": "PASS" if all(checks.values()) else "FAIL",
    }


def valuation_method_source_contracts() -> dict[str, object]:
    return {
        "contract": "m12co-valuation-method-source-contracts-v1",
        "history_threshold_source": "app.services.semantic_decision_service.historical_valuation_selection",
        "history_thresholds": {
            "history_quality": "high",
            "minimum_deduplicated_observations": MIN_HISTORY_OBSERVATIONS,
            "minimum_coverage_ratio": float(MIN_HISTORY_COVERAGE),
            "maximum_history_lag_days": MAX_HISTORY_LAG_DAYS,
        },
        "methods": [
            {
                "method_family": MethodFamily.HISTORICAL_TRAILING_PE_QUANTILE.value,
                "formula": "positive current-security TTM EPS * historical trailing-P/E quantile",
                "required_refs": [
                    "canonical:valuation:trailing_earnings",
                    "canonical:valuation:historical_pe",
                    "canonical:valuation:multiple_relation",
                ],
                "basis_constraints": [
                    "directly comparable current-security trailing denominator",
                    "price and EPS currency equal",
                    "verified non-depositary security basis",
                ],
                "entry_candidate_not_price_target": True,
            },
            {
                "method_family": MethodFamily.HISTORICAL_PB_QUANTILE.value,
                "formula": "positive directly comparable current-security BVPS * historical P/B quantile",
                "required_refs": [
                    "canonical:valuation:book_value",
                    "canonical:valuation:book_quality",
                    "canonical:valuation:historical_pb",
                ],
                "basis_constraints": [
                    "book quality passed",
                    "current-security share basis",
                    "book and price currency equal",
                ],
                "entry_candidate_not_price_target": True,
            },
            {
                "method_family": MethodFamily.FORWARD_BOOK_HISTORICAL_PB.value,
                "formula": "forward BVPS * historical trailing-P/B quantile",
                "materialization_state": "BLOCKED_WITHOUT_EXPLICIT_BASIS_CONTRACT",
            },
            {
                "method_family": MethodFamily.FORWARD_EPS_HISTORICAL_TRAILING_PE.value,
                "formula": "forward EPS * historical trailing-P/E quantile",
                "materialization_state": "BLOCKED_WITHOUT_EXPLICIT_BASIS_CONTRACT",
            },
        ],
    }


def archetype_method_applicability_matrix() -> dict[str, object]:
    archetypes = (
        "DURABLE_FRANCHISE",
        "STRUCTURAL_CYCLICAL_LEADER",
        "PROFITABLE_PREMIUM_GROWTH",
        "EXECUTION_DEPENDENT_GROWTH",
        "MATURE_VALUE_DEFENSIVE",
        "UNRESOLVED",
    )
    policy = {
        MethodFamily.HISTORICAL_TRAILING_PE_QUANTILE.value: {
            "DURABLE_FRANCHISE": "CONDITIONAL_REGIME_REVIEW",
            "STRUCTURAL_CYCLICAL_LEADER": "CONDITIONAL_CYCLE_NORMALIZATION_REQUIRED",
            "PROFITABLE_PREMIUM_GROWTH": "CONDITIONAL_STRUCTURAL_RERATING_REVIEW",
            "EXECUTION_DEPENDENT_GROWTH": "CONDITIONAL_POSITIVE_NORMALIZED_EARNINGS_REQUIRED",
            "MATURE_VALUE_DEFENSIVE": "GENERALLY_MEANINGFUL",
            "UNRESOLVED": "CHAT_POLICY_REQUIRED",
        },
        MethodFamily.HISTORICAL_PB_QUANTILE.value: {
            "DURABLE_FRANCHISE": "CONDITIONAL_ASSET_RELEVANCE_REQUIRED",
            "STRUCTURAL_CYCLICAL_LEADER": "GENERALLY_MEANINGFUL_WITH_REGIME_CAUTION",
            "PROFITABLE_PREMIUM_GROWTH": "CONDITIONAL_INTANGIBLE_ECONOMICS_REVIEW",
            "EXECUTION_DEPENDENT_GROWTH": "CONDITIONAL_NOT_A_SUBSTITUTE_FOR_SCENARIO_VALUE",
            "MATURE_VALUE_DEFENSIVE": "GENERALLY_MEANINGFUL",
            "UNRESOLVED": "CHAT_POLICY_REQUIRED",
        },
        MethodFamily.FORWARD_BOOK_HISTORICAL_PB.value: dict.fromkeys(
            archetypes, "FORBIDDEN_UNTIL_BASIS_CONTRACT_EXISTS"
        ),
        MethodFamily.FORWARD_EPS_HISTORICAL_TRAILING_PE.value: dict.fromkeys(
            archetypes, "FORBIDDEN_UNTIL_BASIS_CONTRACT_EXISTS"
        ),
        MethodFamily.EV_SALES_SCENARIO.value: dict.fromkeys(
            archetypes, "CONDITIONAL_REQUIRES_CANONICAL_SCENARIO_INPUTS"
        ),
        MethodFamily.EV_GROSS_PROFIT_SCENARIO.value: dict.fromkeys(
            archetypes, "CONDITIONAL_REQUIRES_CANONICAL_SCENARIO_INPUTS"
        ),
        MethodFamily.EV_EBITDA_SCENARIO.value: dict.fromkeys(
            archetypes, "CONDITIONAL_REQUIRES_NORMALIZED_EBITDA"
        ),
        MethodFamily.FCF_SCENARIO.value: dict.fromkeys(
            archetypes, "CONDITIONAL_REQUIRES_FCF_SCENARIO_AND_DILUTED_SHARES"
        ),
    }
    return {
        "contract": "m12co-archetype-method-applicability-matrix-v1",
        "ticker_specific_rule_count": 0,
        "archetypes": list(archetypes),
        "methods": policy,
        "status": "PASS",
    }
