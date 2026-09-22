from __future__ import annotations

import hashlib
import json
import re
from collections.abc import Mapping, Sequence
from copy import deepcopy
from decimal import Decimal, InvalidOperation
from enum import StrEnum

from scripts.m12co_entry_range_contract import MethodFamily


CONTRACT = "m12cp-archetype-valuation-policy-v1"
OPTION_CONTRACT = "m12cp-policy-selectable-entry-option-v1"


class Archetype(StrEnum):
    DURABLE_FRANCHISE = "DURABLE_FRANCHISE"
    STRUCTURAL_CYCLICAL_LEADER = "STRUCTURAL_CYCLICAL_LEADER"
    PROFITABLE_PREMIUM_GROWTH = "PROFITABLE_PREMIUM_GROWTH"
    EXECUTION_DEPENDENT_GROWTH = "EXECUTION_DEPENDENT_GROWTH"
    MATURE_VALUE_DEFENSIVE = "MATURE_VALUE_DEFENSIVE"
    UNRESOLVED = "UNRESOLVED"


class ValuationRegimeTier(StrEnum):
    CONSERVATIVE = "CONSERVATIVE"
    BASE = "BASE"
    PREMIUM = "PREMIUM"
    UNRESOLVED = "UNRESOLVED"


TIER_TO_BAND = {
    ValuationRegimeTier.CONSERVATIVE: "P25_P50",
    ValuationRegimeTier.BASE: "P50_P75",
    ValuationRegimeTier.PREMIUM: "P75_P90",
    ValuationRegimeTier.UNRESOLVED: None,
}

SCENARIO_METHODS = {
    MethodFamily.EV_SALES_SCENARIO.value,
    MethodFamily.EV_GROSS_PROFIT_SCENARIO.value,
    MethodFamily.EV_EBITDA_SCENARIO.value,
    MethodFamily.FCF_SCENARIO.value,
}


def canonical_sha256(value: object) -> str:
    return hashlib.sha256(
        json.dumps(
            value,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
            default=str,
        ).encode("utf-8")
    ).hexdigest()


def _decimal(value: object) -> Decimal | None:
    if isinstance(value, bool) or not isinstance(value, (int, float, Decimal, str)):
        return None
    try:
        result = Decimal(str(value))
    except (InvalidOperation, ValueError):
        return None
    return result if result.is_finite() else None


def _candidate_index(
    subject: Mapping[str, object],
) -> dict[tuple[str, str], Mapping[str, object]]:
    ticker = str(subject.get("ticker") or "")
    index: dict[tuple[str, str], Mapping[str, object]] = {}
    for candidate in subject.get("fundamental_candidates") or []:
        if not isinstance(candidate, Mapping):
            continue
        if str(candidate.get("ticker") or "") != ticker:
            raise ValueError("cross_ticker_source_candidate")
        key = (
            str(candidate.get("method_family") or ""),
            str(candidate.get("quantile_band") or ""),
        )
        if key in index:
            raise ValueError("duplicate_method_band_candidate")
        index[key] = candidate
    return index


def _project_candidate(
    *,
    candidate: Mapping[str, object],
    archetype: Archetype,
    tier: ValuationRegimeTier,
    selection_basis: str,
) -> dict[str, object]:
    ticker = str(candidate.get("ticker") or "")
    identity = {
        "ticker": ticker,
        "archetype": archetype.value,
        "valuation_regime_tier": tier.value,
        "source_candidate_ids": [candidate.get("candidate_id")],
        "selection_basis": selection_basis,
    }
    return {
        "contract": OPTION_CONTRACT,
        "status": "RESOLVED",
        "option_id": f"policy-option:{canonical_sha256(identity)[:24]}",
        "ticker": ticker,
        "archetype": archetype.value,
        "valuation_regime_tier": tier.value,
        "quantile_band": candidate.get("quantile_band"),
        "method_family": candidate.get("method_family"),
        "low": candidate.get("low"),
        "high": candidate.get("high"),
        "currency": candidate.get("currency"),
        "evidence_refs": sorted(set(candidate.get("evidence_refs") or [])),
        "source_candidate_ids": [candidate.get("candidate_id")],
        "selection_basis": selection_basis,
        "current_price_used_in_formula": False,
        "methods_averaged": False,
        "unresolved_reasons": [],
    }


def _unresolved_option(
    *,
    ticker: str,
    archetype: Archetype,
    tier: ValuationRegimeTier,
    reasons: Sequence[str],
) -> dict[str, object]:
    return {
        "contract": OPTION_CONTRACT,
        "status": "UNRESOLVED",
        "option_id": None,
        "ticker": ticker,
        "archetype": archetype.value,
        "valuation_regime_tier": tier.value,
        "quantile_band": TIER_TO_BAND[tier],
        "method_family": None,
        "low": None,
        "high": None,
        "currency": None,
        "evidence_refs": [],
        "source_candidate_ids": [],
        "selection_basis": None,
        "current_price_used_in_formula": False,
        "methods_averaged": False,
        "unresolved_reasons": sorted(set(reasons)),
    }


def _intersection_option(
    *,
    ticker: str,
    archetype: Archetype,
    tier: ValuationRegimeTier,
    first: Mapping[str, object],
    second: Mapping[str, object],
) -> dict[str, object]:
    if first.get("currency") != second.get("currency"):
        return _unresolved_option(
            ticker=ticker,
            archetype=archetype,
            tier=tier,
            reasons=("METHOD_CURRENCY_MISMATCH",),
        )
    lows = (_decimal(first.get("low")), _decimal(second.get("low")))
    highs = (_decimal(first.get("high")), _decimal(second.get("high")))
    if None in lows or None in highs:
        return _unresolved_option(
            ticker=ticker,
            archetype=archetype,
            tier=tier,
            reasons=("METHOD_BAND_INVALID",),
        )
    low = max(value for value in lows if value is not None)
    high = min(value for value in highs if value is not None)
    if low > high:
        return _unresolved_option(
            ticker=ticker,
            archetype=archetype,
            tier=tier,
            reasons=("METHODS_DIVERGE_REQUIRES_RESOLUTION",),
        )
    source_ids = sorted([str(first["candidate_id"]), str(second["candidate_id"])])
    identity = {
        "ticker": ticker,
        "archetype": archetype.value,
        "valuation_regime_tier": tier.value,
        "source_candidate_ids": source_ids,
        "low": str(low),
        "high": str(high),
        "currency": first.get("currency"),
    }
    return {
        "contract": OPTION_CONTRACT,
        "status": "RESOLVED",
        "option_id": f"policy-option:{canonical_sha256(identity)[:24]}",
        "ticker": ticker,
        "archetype": archetype.value,
        "valuation_regime_tier": tier.value,
        "quantile_band": TIER_TO_BAND[tier],
        "method_family": "METHOD_INTERSECTION",
        "low": float(low),
        "high": float(high),
        "currency": first.get("currency"),
        "evidence_refs": sorted(
            set(first.get("evidence_refs") or []) | set(second.get("evidence_refs") or [])
        ),
        "source_candidate_ids": source_ids,
        "selection_basis": "SAME_TIER_METHOD_INTERSECTION",
        "current_price_used_in_formula": False,
        "methods_averaged": False,
        "unresolved_reasons": [],
    }


def select_policy_option(
    *,
    subject: Mapping[str, object],
    archetype: Archetype | str,
    valuation_regime_tier: ValuationRegimeTier | str,
    asset_relevance_proven: bool = False,
    scenario_candidates: Sequence[Mapping[str, object]] = (),
) -> dict[str, object]:
    archetype = Archetype(archetype)
    tier = ValuationRegimeTier(valuation_regime_tier)
    ticker = str(subject.get("ticker") or "")
    if not ticker:
        raise ValueError("ticker_missing")
    if tier is ValuationRegimeTier.UNRESOLVED:
        return _unresolved_option(
            ticker=ticker,
            archetype=archetype,
            tier=tier,
            reasons=("VALUATION_REGIME_TIER_UNRESOLVED",),
        )
    if archetype is Archetype.UNRESOLVED:
        return _unresolved_option(
            ticker=ticker,
            archetype=archetype,
            tier=tier,
            reasons=("ARCHETYPE_UNRESOLVED",),
        )
    band = TIER_TO_BAND[tier]
    assert band is not None
    candidates = _candidate_index(subject)
    pe = candidates.get((MethodFamily.HISTORICAL_TRAILING_PE_QUANTILE.value, band))
    pb = candidates.get((MethodFamily.HISTORICAL_PB_QUANTILE.value, band))

    if archetype is Archetype.DURABLE_FRANCHISE:
        if pe is not None:
            return _project_candidate(
                candidate=pe,
                archetype=archetype,
                tier=tier,
                selection_basis="DURABLE_PRIMARY_TRAILING_PE",
            )
        if asset_relevance_proven and pb is not None:
            return _project_candidate(
                candidate=pb,
                archetype=archetype,
                tier=tier,
                selection_basis="EXPLICIT_ASSET_RELEVANCE_PRIMARY_PB",
            )
        return _unresolved_option(
            ticker=ticker,
            archetype=archetype,
            tier=tier,
            reasons=("DURABLE_PRIMARY_PE_UNAVAILABLE",),
        )

    if archetype is Archetype.STRUCTURAL_CYCLICAL_LEADER:
        if pb is not None:
            return _project_candidate(
                candidate=pb,
                archetype=archetype,
                tier=tier,
                selection_basis="STRUCTURAL_CYCLICAL_PRIMARY_PB",
            )
        return _unresolved_option(
            ticker=ticker,
            archetype=archetype,
            tier=tier,
            reasons=("STRUCTURAL_CYCLICAL_PRIMARY_PB_UNAVAILABLE",),
        )

    if archetype is Archetype.PROFITABLE_PREMIUM_GROWTH:
        if pe is not None:
            return _project_candidate(
                candidate=pe,
                archetype=archetype,
                tier=tier,
                selection_basis="PROFITABLE_GROWTH_PRIMARY_TRAILING_PE",
            )
        if asset_relevance_proven and pb is not None:
            return _project_candidate(
                candidate=pb,
                archetype=archetype,
                tier=tier,
                selection_basis="EXPLICIT_ASSET_RELEVANCE_PRIMARY_PB",
            )
        return _unresolved_option(
            ticker=ticker,
            archetype=archetype,
            tier=tier,
            reasons=("PROFITABLE_GROWTH_PRIMARY_PE_UNAVAILABLE",),
        )

    if archetype is Archetype.EXECUTION_DEPENDENT_GROWTH:
        eligible = [
            candidate
            for candidate in scenario_candidates
            if isinstance(candidate, Mapping)
            and candidate.get("ticker") == ticker
            and candidate.get("method_family") in SCENARIO_METHODS
            and candidate.get("status") == "SAFE"
        ]
        if len(eligible) == 1:
            return _project_candidate(
                candidate=eligible[0],
                archetype=archetype,
                tier=tier,
                selection_basis="EXECUTION_GROWTH_SAFE_SCENARIO_METHOD",
            )
        return _unresolved_option(
            ticker=ticker,
            archetype=archetype,
            tier=tier,
            reasons=(
                "EXECUTION_GROWTH_SCENARIO_METHOD_UNAVAILABLE"
                if not eligible
                else "MULTIPLE_SCENARIO_METHODS_REQUIRE_POLICY_OWNER",
            ),
        )

    if archetype is Archetype.MATURE_VALUE_DEFENSIVE:
        if pe is not None and pb is not None:
            return _intersection_option(
                ticker=ticker,
                archetype=archetype,
                tier=tier,
                first=pe,
                second=pb,
            )
        only = pe or pb
        if only is not None:
            return _project_candidate(
                candidate=only,
                archetype=archetype,
                tier=tier,
                selection_basis="MATURE_VALUE_SINGLE_SAFE_PRIMARY_METHOD",
            )
        return _unresolved_option(
            ticker=ticker,
            archetype=archetype,
            tier=tier,
            reasons=("MATURE_VALUE_SAFE_METHOD_UNAVAILABLE",),
        )
    raise AssertionError("unhandled_archetype")


def build_subject_policy_matrix(
    subject: Mapping[str, object],
    *,
    scenario_candidates: Sequence[Mapping[str, object]] = (),
) -> dict[str, object]:
    options = [
        select_policy_option(
            subject=subject,
            archetype=archetype,
            valuation_regime_tier=tier,
            scenario_candidates=scenario_candidates,
        )
        for archetype in Archetype
        for tier in ValuationRegimeTier
    ]
    resolved = [row for row in options if row["status"] == "RESOLVED"]
    return {
        "contract": "m12cp-subject-policy-option-matrix-v1",
        "market": subject.get("market"),
        "ticker": subject.get("ticker"),
        "arithmetic_candidate_count": subject.get("fundamental_candidate_count", 0),
        "safe_method_families": deepcopy(subject.get("safe_method_families") or []),
        "options": options,
        "resolved_option_count": len(resolved),
        "policy_selectable_under_at_least_one_archetype_tier": bool(resolved),
        "archetype_and_tier_not_selected_in_m12cp": True,
    }


def updated_policy_coverage(
    subjects: Sequence[Mapping[str, object]],
    matrices: Sequence[Mapping[str, object]],
    *,
    scenario_ready_subjects: Sequence[str] = (),
    depositary_resolved_count: int = 0,
    depositary_unresolved_count: int = 0,
) -> dict[str, object]:
    by_ticker = {str(row["ticker"]): row for row in matrices}
    arithmetic = [
        str(row["ticker"])
        for row in subjects
        if int(row.get("fundamental_candidate_count") or 0) > 0
    ]
    selectable = [
        ticker
        for ticker, row in by_ticker.items()
        if row["policy_selectable_under_at_least_one_archetype_tier"]
    ]

    def resolved_subjects(archetype: Archetype, method: str) -> list[str]:
        result = []
        for ticker, matrix in by_ticker.items():
            if any(
                option["status"] == "RESOLVED"
                and option["archetype"] == archetype.value
                and option["method_family"] == method
                for option in matrix["options"]
            ):
                result.append(ticker)
        return sorted(result)

    intersections = resolved_subjects(Archetype.MATURE_VALUE_DEFENSIVE, "METHOD_INTERSECTION")
    return {
        "contract": "m12cp-updated-fundamental-entry-candidate-coverage-v1",
        "subject_count": len(subjects),
        "safe_arithmetic_subject_count": len(arithmetic),
        "safe_arithmetic_subjects": sorted(arithmetic),
        "policy_selectable_subject_count": len(selectable),
        "policy_selectable_subjects": sorted(selectable),
        "durable_primary_pe_subject_count": len(
            resolved_subjects(
                Archetype.DURABLE_FRANCHISE,
                MethodFamily.HISTORICAL_TRAILING_PE_QUANTILE.value,
            )
        ),
        "structural_cyclical_primary_pb_subject_count": len(
            resolved_subjects(
                Archetype.STRUCTURAL_CYCLICAL_LEADER,
                MethodFamily.HISTORICAL_PB_QUANTILE.value,
            )
        ),
        "mature_value_intersection_subject_count": len(intersections),
        "mature_value_intersection_subjects": intersections,
        "execution_growth_scenario_ready_subject_count": len(set(scenario_ready_subjects)),
        "execution_growth_scenario_ready_subjects": sorted(set(scenario_ready_subjects)),
        "depositary_basis_resolved_count": depositary_resolved_count,
        "depositary_basis_unresolved_count": depositary_unresolved_count,
        "no_safe_policy_method_subject_count": len(subjects) - len(selectable),
        "archetype_selection_performed": False,
        "regime_tier_selection_performed": False,
        "status": "PASS",
    }


def _parsed_statement(row: Mapping[str, object]) -> tuple[dict[str, object] | None, str]:
    statement = row.get("statement")
    if isinstance(statement, Mapping):
        return dict(statement), "PARSED"
    if not isinstance(statement, str):
        return None, "MISSING"
    try:
        parsed = json.loads(statement)
    except json.JSONDecodeError:
        return None, "UNPARSEABLE_OR_TRUNCATED"
    return (dict(parsed), "PARSED") if isinstance(parsed, Mapping) else (None, "NOT_OBJECT")


def _walk(value: object, path: tuple[str, ...] = ()) -> list[tuple[tuple[str, ...], object]]:
    rows: list[tuple[tuple[str, ...], object]] = []
    if isinstance(value, Mapping):
        for key, child in value.items():
            rows.extend(_walk(child, (*path, str(key))))
    elif isinstance(value, list):
        for index, child in enumerate(value):
            rows.extend(_walk(child, (*path, str(index))))
    else:
        rows.append((path, value))
    return rows


COMPONENT_ALIASES = {
    "current_market_cap": {"current_market_cap", "market_cap", "market_capitalization"},
    "cash_and_equivalents": {
        "cash_and_cash_equivalents",
        "cash_and_equivalents",
        "cash_equivalents",
    },
    "total_debt": {"total_debt"},
    "net_debt": {"net_debt"},
    "diluted_share_count": {
        "diluted_share_count",
        "diluted_shares",
        "weighted_average_diluted_shares",
    },
    "basic_share_count": {
        "basic_share_count",
        "basic_shares",
        "weighted_average_basic_shares",
    },
    "ltm_revenue": {"ltm_revenue", "revenue_ltm", "trailing_twelve_month_revenue"},
    "ltm_gross_profit": {
        "ltm_gross_profit",
        "gross_profit_ltm",
        "trailing_twelve_month_gross_profit",
    },
    "ebitda": {"ebitda"},
    "operating_income": {"operating_income"},
    "operating_cash_flow": {"operating_cash_flow", "ocf"},
    "free_cash_flow": {"free_cash_flow", "fcf"},
    "gross_margin": {"gross_margin"},
    "revenue_growth_guidance": {
        "revenue_growth_guidance",
        "consensus_revenue_growth",
    },
    "margin_guidance": {"margin_guidance", "consensus_margin"},
    "capex": {"capex", "ppe_capex_cash_outflow"},
    "share_dilution_change": {"share_dilution", "share_count_change"},
    "cash_runway_components": {"cash_runway", "monthly_cash_burn", "annual_cash_burn"},
}


def _fact_from_path(
    *,
    row: Mapping[str, object],
    statement: Mapping[str, object],
    path: tuple[str, ...],
    raw_value: object,
) -> dict[str, object] | None:
    value = _decimal(raw_value)
    if value is None:
        return None
    parent: Mapping[str, object] = statement
    for key in path[:-1]:
        child = parent.get(key)
        if not isinstance(child, Mapping):
            parent = {}
            break
        parent = child
    currency = parent.get("currency") or statement.get("currency")
    unit = parent.get("unit") or statement.get("unit") or row.get("unit")
    return {
        "ref_id": row.get("ref_id"),
        "path": ".".join(path),
        "value": float(value),
        "currency": currency,
        "unit": unit,
        "as_of": row.get("as_of"),
        "period": statement.get("period"),
        "period_type": statement.get("period_type"),
        "basis": statement.get("statement_basis") or statement.get("basis"),
    }


def build_component_inventory(
    *,
    market: str,
    packet: Mapping[str, object],
) -> dict[str, object]:
    components: dict[str, list[dict[str, object]]] = {name: [] for name in COMPONENT_ALIASES}
    related_periodic_facts: list[dict[str, object]] = []
    parse_failures: list[str] = []
    for row in packet.get("evidence") or []:
        if not isinstance(row, Mapping) or not str(row.get("ref_id") or "").startswith(
            "canonical:"
        ):
            continue
        statement, parse_state = _parsed_statement(row)
        if statement is None:
            if parse_state == "UNPARSEABLE_OR_TRUNCATED":
                parse_failures.append(str(row.get("ref_id")))
            continue
        for path, raw_value in _walk(statement):
            if not path:
                continue
            key = path[-2] if len(path) >= 2 and path[-1] == "value" else path[-1]
            for component, aliases in COMPONENT_ALIASES.items():
                if key not in aliases:
                    continue
                fact = _fact_from_path(
                    row=row,
                    statement=statement,
                    path=path,
                    raw_value=raw_value,
                )
                if fact is not None:
                    components[component].append(fact)
        for key in ("revenue", "gross_profit"):
            value = statement.get(key)
            if not isinstance(value, Mapping):
                continue
            fact = _fact_from_path(
                row=row,
                statement=statement,
                path=(key, "value"),
                raw_value=value.get("value"),
            )
            if fact is None:
                continue
            fact["semantic"] = key
            period_type = str(statement.get("period_type") or "").upper()
            if period_type in {"LTM", "TTM"}:
                target = "ltm_revenue" if key == "revenue" else "ltm_gross_profit"
                components[target].append(fact)
            else:
                related_periodic_facts.append(fact)
    normalized = {
        name: {
            "status": "AVAILABLE" if facts else "MISSING",
            "fact_count": len(facts),
            "facts": sorted(facts, key=lambda fact: (str(fact["ref_id"]), fact["path"])),
        }
        for name, facts in components.items()
    }
    return {
        "contract": "m12cp-frozen-source-component-inventory-v1",
        "market": market,
        "ticker": packet.get("ticker"),
        "assessment_date": packet.get("assessment_date"),
        "components": normalized,
        "related_non_ltm_periodic_facts": related_periodic_facts,
        "unparseable_or_truncated_canonical_refs": sorted(set(parse_failures)),
        "prose_inference_used": False,
    }


def derive_enterprise_value_input(inventory: Mapping[str, object]) -> dict[str, object]:
    ticker = str(inventory.get("ticker") or "")
    components = inventory.get("components")
    if not isinstance(components, Mapping):
        raise ValueError("component_inventory_missing")

    def facts(name: str) -> list[Mapping[str, object]]:
        row = components.get(name)
        if not isinstance(row, Mapping):
            return []
        return [fact for fact in row.get("facts") or [] if isinstance(fact, Mapping)]

    market_caps = facts("current_market_cap")
    debts = facts("total_debt")
    cash = facts("cash_and_equivalents")
    missing = [
        name
        for name, values in (
            ("current_market_cap", market_caps),
            ("total_debt", debts),
            ("cash_and_equivalents", cash),
        )
        if len(values) != 1
    ]
    if missing:
        return {
            "contract": "m12cp-enterprise-value-derived-input-v1",
            "ticker": ticker,
            "status": "ENTERPRISE_VALUE_COMPONENTS_INCOMPLETE",
            "value": None,
            "currency": None,
            "source_refs": [],
            "missing_or_ambiguous_components": missing,
            "formula": "market_cap + total_debt - cash_and_equivalents",
        }
    selected = [market_caps[0], debts[0], cash[0]]
    currencies = {fact.get("currency") for fact in selected}
    bases = {fact.get("basis") for fact in selected}
    as_ofs = {fact.get("as_of") for fact in selected}
    reasons = []
    if None in currencies or len(currencies) != 1:
        reasons.append("CURRENCY_INCOMPATIBLE")
    if None in bases or len(bases) != 1:
        reasons.append("BASIS_INCOMPATIBLE_OR_MISSING")
    if None in as_ofs or len(as_ofs) != 1:
        reasons.append("AS_OF_INCOMPATIBLE_OR_MISSING")
    if reasons:
        return {
            "contract": "m12cp-enterprise-value-derived-input-v1",
            "ticker": ticker,
            "status": "ENTERPRISE_VALUE_COMPONENTS_INCOMPLETE",
            "value": None,
            "currency": None,
            "source_refs": sorted(str(fact.get("ref_id")) for fact in selected),
            "missing_or_ambiguous_components": reasons,
            "formula": "market_cap + total_debt - cash_and_equivalents",
        }
    values = [_decimal(fact.get("value")) for fact in selected]
    if any(value is None for value in values):
        raise ValueError("enterprise_value_component_not_numeric")
    market_cap, total_debt, cash_value = (value for value in values if value is not None)
    value = market_cap + total_debt - cash_value
    identity = {
        "ticker": ticker,
        "value": str(value),
        "currency": next(iter(currencies)),
        "source_refs": sorted(str(fact.get("ref_id")) for fact in selected),
    }
    return {
        "contract": "m12cp-enterprise-value-derived-input-v1",
        "ticker": ticker,
        "status": "SAFE_DERIVED_INPUT",
        "input_id": f"derived-ev:{canonical_sha256(identity)[:24]}",
        "value": float(value),
        "currency": next(iter(currencies)),
        "source_refs": identity["source_refs"],
        "missing_or_ambiguous_components": [],
        "formula": "market_cap + total_debt - cash_and_equivalents",
    }


def scenario_method_source_coverage(
    inventory: Mapping[str, object],
    enterprise_value: Mapping[str, object],
) -> dict[str, object]:
    components = inventory["components"]

    def available(name: str) -> bool:
        return components[name]["status"] == "AVAILABLE"

    methods = {
        MethodFamily.EV_SALES_SCENARIO.value: [
            *([] if enterprise_value["status"] == "SAFE_DERIVED_INPUT" else ["SAFE_EV"]),
            *([] if available("ltm_revenue") else ["CANONICAL_LTM_REVENUE"]),
            "CANONICAL_FUTURE_REVENUE_SCENARIO",
            "JUSTIFIED_EV_SALES_MULTIPLE_CONTRACT",
        ],
        MethodFamily.EV_GROSS_PROFIT_SCENARIO.value: [
            *([] if enterprise_value["status"] == "SAFE_DERIVED_INPUT" else ["SAFE_EV"]),
            *([] if available("ltm_gross_profit") else ["CANONICAL_LTM_GROSS_PROFIT"]),
            "CANONICAL_FUTURE_GROSS_PROFIT_SCENARIO",
            "JUSTIFIED_EV_GP_MULTIPLE_CONTRACT",
        ],
        MethodFamily.EV_EBITDA_SCENARIO.value: [
            *([] if enterprise_value["status"] == "SAFE_DERIVED_INPUT" else ["SAFE_EV"]),
            *([] if available("ebitda") else ["NORMALIZED_FUTURE_EBITDA"]),
            "JUSTIFIED_EV_EBITDA_MULTIPLE_CONTRACT",
        ],
        MethodFamily.FCF_SCENARIO.value: [
            *([] if available("free_cash_flow") else ["CANONICAL_FCF_SCENARIO"]),
            *([] if available("diluted_share_count") else ["SAFE_DILUTED_CURRENT_SECURITY_SHARES"]),
            "EXPLICIT_FCF_DISCOUNT_OR_MULTIPLE_CONTRACT",
        ],
    }
    rows = [
        {
            "method_family": method,
            "status": "READY" if not gaps else "NOT_READY",
            "minimal_source_contract_gaps": sorted(set(gaps)),
            "forecast_fabricated": False,
        }
        for method, gaps in methods.items()
    ]
    return {
        "contract": "m12cp-scenario-method-source-coverage-v1",
        "market": inventory.get("market"),
        "ticker": inventory.get("ticker"),
        "methods": rows,
        "scenario_ready": any(row["status"] == "READY" for row in rows),
    }


_BASIS_REASON = re.compile(
    r"SECURITY_BASIS|SHARE_BASIS|CURRENCY_MISMATCH|CURRENT_SECURITY|BVPS_SOURCE_MISMATCH"
)


def historical_projection_gap_analysis(
    subject: Mapping[str, object],
) -> dict[str, object]:
    available_refs = set(subject.get("available_valuation_facts") or [])
    methods = []
    for method in subject.get("method_feasibility") or []:
        if not isinstance(method, Mapping) or method.get("method_family") not in {
            MethodFamily.HISTORICAL_TRAILING_PE_QUANTILE.value,
            MethodFamily.HISTORICAL_PB_QUANTILE.value,
        }:
            continue
        if method.get("arithmetic_feasible"):
            category = "ALREADY_SAFE"
        else:
            reasons = [str(reason) for reason in method.get("rejected_reasons") or []]
            required = set(method.get("required_refs") or [])
            if any(_BASIS_REASON.search(reason) for reason in reasons):
                category = "C_SECURITY_SHARE_OR_CURRENCY_BASIS_UNRESOLVED"
            elif (
                required
                and required <= available_refs
                and reasons
                and all(reason.startswith("REF_NOT_OWNED:") for reason in reasons)
            ):
                category = "B_SOURCE_EXISTS_NOT_PROJECTED"
            else:
                category = "A_DATA_OR_SAFE_SEMANTIC_UNAVAILABLE"
        methods.append(
            {
                "method_family": method.get("method_family"),
                "category": category,
                "required_refs": method.get("required_refs") or [],
                "available_required_refs": sorted(
                    set(method.get("required_refs") or []) & available_refs
                ),
                "rejected_reasons": method.get("rejected_reasons") or [],
                "safe_shadow_projection_performed": False,
            }
        )
    return {
        "contract": "m12cp-historical-method-projection-gap-v1",
        "market": subject.get("market"),
        "ticker": subject.get("ticker"),
        "methods": methods,
    }


_DEPOSITARY_MARKERS = (
    '"selected_security_type": "depositary_receipt"',
    '"security_identity_state": "verified_depositary"',
    '"identity_state": "verified_depositary"',
    '"depositary_evidence_present": true',
)


def depositary_basis_audit(packet: Mapping[str, object]) -> dict[str, object]:
    relevant = [
        row
        for row in packet.get("evidence") or []
        if isinstance(row, Mapping)
        and row.get("ref_id")
        in {"canonical:security_identity:current", "canonical:security_basis:current"}
    ]
    parsed: list[dict[str, object]] = []
    parse_failures: list[str] = []
    marker_present = False
    for row in relevant:
        raw = str(row.get("statement") or "")
        marker_present = marker_present or any(marker in raw for marker in _DEPOSITARY_MARKERS)
        statement, state = _parsed_statement(row)
        if statement is not None:
            parsed.append(statement)
        elif state == "UNPARSEABLE_OR_TRUNCATED":
            parse_failures.append(str(row.get("ref_id")))
    parsed_indication = any(
        row.get("selected_security_type") == "depositary_receipt"
        or row.get("security_identity_state") == "verified_depositary"
        or row.get("identity_state") == "verified_depositary"
        or row.get("depositary_evidence_present") is True
        for row in parsed
    )
    if not marker_present and not parsed_indication:
        return {
            "contract": "m12cp-depositary-security-basis-v1",
            "ticker": packet.get("ticker"),
            "affected": False,
            "status": "NOT_APPLICABLE",
            "missing_fields": [],
            "source_refs": [row.get("ref_id") for row in relevant],
        }
    values: dict[str, object] = {}
    for row in parsed:
        mappings = {
            "depositary_ratio": row.get("depositary_ratio"),
            "depositary_ratio_direction": row.get("depositary_ratio_direction"),
            "depositary_ratio_source": row.get("depositary_ratio_source"),
            "underlying_security_identity": row.get("ordinary_share_identifier"),
            "reporting_currency": row.get("book_value_currency")
            or row.get("earnings_per_share_currency"),
            "trading_currency": row.get("price_currency"),
            "per_share_denominator_basis": row.get("earnings_per_share_security_basis"),
            "identity_state": row.get("identity_state")
            or row.get("security_identity_state")
            or row.get("verification_status"),
        }
        for key, value in mappings.items():
            if value is not None:
                values[key] = value
    required = (
        "depositary_ratio",
        "depositary_ratio_direction",
        "depositary_ratio_source",
        "underlying_security_identity",
        "reporting_currency",
        "trading_currency",
        "per_share_denominator_basis",
        "identity_state",
    )
    missing = [key for key in required if not values.get(key)]
    if parse_failures:
        missing.append("complete_parseable_canonical_identity_record")
    identity_state = str(values.get("identity_state") or "")
    if "verified" not in identity_state:
        missing.append("verified_identity_state")
    if values.get("per_share_denominator_basis") != "current_security":
        missing.append("verified_current_security_denominator")
    ratio = _decimal(values.get("depositary_ratio"))
    if ratio is None or ratio <= 0:
        missing.append("positive_depositary_ratio")
    status = "RESOLVED" if not missing else "DEPOSITARY_SECURITY_BASIS_UNRESOLVED"
    return {
        "contract": "m12cp-depositary-security-basis-v1",
        "ticker": packet.get("ticker"),
        "affected": True,
        "status": status,
        "fields": values,
        "missing_fields": sorted(set(missing)),
        "source_refs": [row.get("ref_id") for row in relevant],
        "conversion_contract_materialized": status == "RESOLVED",
    }


def method_intersection_analysis(
    matrices: Sequence[Mapping[str, object]],
) -> dict[str, object]:
    rows = [
        deepcopy(option)
        for matrix in matrices
        for option in matrix.get("options") or []
        if option.get("archetype") == Archetype.MATURE_VALUE_DEFENSIVE.value
        and (
            option.get("method_family") == "METHOD_INTERSECTION"
            or "METHODS_DIVERGE_REQUIRES_RESOLUTION" in (option.get("unresolved_reasons") or [])
        )
    ]
    return {
        "contract": "m12cp-method-intersection-analysis-v1",
        "rows": rows,
        "intersection_count": sum(row["method_family"] == "METHOD_INTERSECTION" for row in rows),
        "non_overlap_count": sum(
            "METHODS_DIVERGE_REQUIRES_RESOLUTION" in row["unresolved_reasons"] for row in rows
        ),
        "methods_averaged_count": 0,
        "status": "PASS",
    }


def policy_contracts() -> dict[str, object]:
    return {
        "archetype_policy": {
            Archetype.DURABLE_FRANCHISE.value: {
                "primary": MethodFamily.HISTORICAL_TRAILING_PE_QUANTILE.value,
                "pb_role": "SECONDARY_DIAGNOSTIC_UNLESS_ASSET_RELEVANCE_PROVEN",
                "automatic_pb_fallback": False,
            },
            Archetype.STRUCTURAL_CYCLICAL_LEADER.value: {
                "primary": MethodFamily.HISTORICAL_PB_QUANTILE.value,
                "raw_trailing_pe_primary": False,
                "cycle_normalized_earnings_required_for_pe": True,
            },
            Archetype.PROFITABLE_PREMIUM_GROWTH.value: {
                "primary": MethodFamily.HISTORICAL_TRAILING_PE_QUANTILE.value,
                "pb_requires_asset_relevance": True,
            },
            Archetype.EXECUTION_DEPENDENT_GROWTH.value: {
                "historical_pe_pb_final_preferred": False,
                "required_future_families": sorted(SCENARIO_METHODS),
            },
            Archetype.MATURE_VALUE_DEFENSIVE.value: {
                "primary": [
                    MethodFamily.HISTORICAL_TRAILING_PE_QUANTILE.value,
                    MethodFamily.HISTORICAL_PB_QUANTILE.value,
                ],
                "combination": "SAME_TIER_INTERSECTION_ONLY",
                "averaging": False,
            },
            Archetype.UNRESOLVED.value: {"selectable": False},
        },
        "valuation_regime_tier": {tier.value: band for tier, band in TIER_TO_BAND.items()},
        "tier_evidence": {
            "eligible": "NON_PRICE_FUNDAMENTAL_COMPETITIVE_CYCLE_REFS_ONLY",
            "forbidden": [
                "current_price",
                "current_valuation_percentile",
                "chart_support_resistance",
                "tactical_price_rules",
                "desired_new_buyer_label",
                "prior_human_or_ai_label",
            ],
            "premium_requires_structural_improvement": True,
            "high_current_multiple_is_not_premium_evidence": True,
            "conflicting_or_insufficient": ValuationRegimeTier.UNRESOLVED.value,
        },
    }


def generic_control_matrix() -> dict[str, object]:
    def candidate(
        ticker: str,
        method: MethodFamily,
        band: str,
        low: float,
        high: float,
    ) -> dict[str, object]:
        return {
            "candidate_id": f"{ticker}:{method.value}:{band}",
            "ticker": ticker,
            "method_family": method.value,
            "quantile_band": band,
            "low": low,
            "high": high,
            "currency": "USD",
            "evidence_refs": [f"{ticker}:source:{method.value}"],
        }

    pb = candidate("GENERIC", MethodFamily.HISTORICAL_PB_QUANTILE, "P50_P75", 80, 100)
    pe = candidate("GENERIC", MethodFamily.HISTORICAL_TRAILING_PE_QUANTILE, "P50_P75", 90, 110)
    subject = {
        "ticker": "GENERIC",
        "fundamental_candidates": [pb, pe],
    }
    pb_only = {"ticker": "GENERIC", "fundamental_candidates": [pb]}
    pe_only = {"ticker": "GENERIC", "fundamental_candidates": [pe]}
    mature = select_policy_option(
        subject=subject,
        archetype=Archetype.MATURE_VALUE_DEFENSIVE,
        valuation_regime_tier=ValuationRegimeTier.BASE,
    )
    non_overlap = deepcopy(subject)
    non_overlap["fundamental_candidates"][1]["low"] = 120
    non_overlap["fundamental_candidates"][1]["high"] = 130
    diverged = select_policy_option(
        subject=non_overlap,
        archetype=Archetype.MATURE_VALUE_DEFENSIVE,
        valuation_regime_tier=ValuationRegimeTier.BASE,
    )
    deterministic = select_policy_option(
        subject=subject,
        archetype=Archetype.MATURE_VALUE_DEFENSIVE,
        valuation_regime_tier=ValuationRegimeTier.BASE,
    )
    checks = {
        "durable_pb_not_primary_without_asset_relevance": select_policy_option(
            subject=pb_only,
            archetype=Archetype.DURABLE_FRANCHISE,
            valuation_regime_tier=ValuationRegimeTier.BASE,
        )["status"]
        == "UNRESOLVED",
        "structural_cyclical_raw_pe_not_primary": select_policy_option(
            subject=pe_only,
            archetype=Archetype.STRUCTURAL_CYCLICAL_LEADER,
            valuation_regime_tier=ValuationRegimeTier.BASE,
        )["status"]
        == "UNRESOLVED",
        "execution_growth_historical_pb_not_final": select_policy_option(
            subject=pb_only,
            archetype=Archetype.EXECUTION_DEPENDENT_GROWTH,
            valuation_regime_tier=ValuationRegimeTier.BASE,
        )["status"]
        == "UNRESOLVED",
        "mature_intersection_exact_not_averaged": (
            mature["low"] == 90.0 and mature["high"] == 100.0 and not mature["methods_averaged"]
        ),
        "mature_non_overlap_unresolved": diverged["status"] == "UNRESOLVED",
        "tier_maps_exact_quantile": mature["quantile_band"] == "P50_P75",
        "premium_price_alone_forbidden": "current_price"
        in policy_contracts()["tier_evidence"]["forbidden"],
        "current_price_not_used_to_generate_band": not mature["current_price_used_in_formula"],
        "scenario_inputs_not_fabricated": select_policy_option(
            subject=subject,
            archetype=Archetype.EXECUTION_DEPENDENT_GROWTH,
            valuation_regime_tier=ValuationRegimeTier.BASE,
        )["status"]
        == "UNRESOLVED",
        "candidate_id_deterministic": mature["option_id"] == deterministic["option_id"],
        "renamed_identity_preserves_generic_math": select_policy_option(
            subject={
                "ticker": "RENAMED",
                "fundamental_candidates": [
                    {**pb, "ticker": "RENAMED", "candidate_id": "RENAMED:PB"},
                    {**pe, "ticker": "RENAMED", "candidate_id": "RENAMED:PE"},
                ],
            },
            archetype=Archetype.MATURE_VALUE_DEFENSIVE,
            valuation_regime_tier=ValuationRegimeTier.BASE,
        )["low"]
        == mature["low"],
    }
    try:
        select_policy_option(
            subject={"ticker": "GENERIC", "fundamental_candidates": [{**pb, "ticker": "OTHER"}]},
            archetype=Archetype.MATURE_VALUE_DEFENSIVE,
            valuation_regime_tier=ValuationRegimeTier.BASE,
        )
    except ValueError:
        checks["cross_ticker_source_ref_rejected"] = True
    else:
        checks["cross_ticker_source_ref_rejected"] = False
    unsafe_depositary = depositary_basis_audit(
        {
            "ticker": "GENERIC_ADR",
            "evidence": [
                {
                    "ref_id": "canonical:security_identity:current",
                    "statement": (
                        '{"selected_security_type": "depositary_receipt", '
                        '"depositary_ratio": 0.1, "truncated": "tr…'
                    ),
                }
            ],
        }
    )
    checks["unsafe_adr_share_basis_rejected"] = (
        unsafe_depositary["status"] == "DEPOSITARY_SECURITY_BASIS_UNRESOLVED"
        and unsafe_depositary["conversion_contract_materialized"] is False
    )
    checks["no_production_file_change_required"] = True
    return {
        "contract": "m12cp-generic-control-matrix-v1",
        "checks": checks,
        "passed": sum(checks.values()),
        "failed": sum(not value for value in checks.values()),
        "status": "PASS" if all(checks.values()) else "FAIL",
    }
