from __future__ import annotations

import hashlib
import re
from dataclasses import dataclass
from typing import Iterable


INDUSTRY_REASONING_CONTRACT = "industry-specific-reasoning-v1"
INDUSTRY_REASONING_REFERENCE_FIELD = "industry_reasoning_refs"

SUPPORTED_FRAMEWORKS = {
    "memory",
    "semiconductor",
    "semiconductor_foundry",
    "insurance",
    "transport_logistics",
    "steel_materials",
    "automotive",
    "biotech",
    "hpc_crypto_infrastructure",
    "epc_construction",
    "saas",
    "holding_company",
    "general",
}

_ROUTING_KEY_MAP = {
    "memory": "memory",
    "semiconductor": "semiconductor",
    "semiconductor_foundry": "semiconductor_foundry",
    "insurance": "insurance",
    "shipping": "transport_logistics",
    "transport_logistics": "transport_logistics",
    "steel_materials": "steel_materials",
    "automotive": "automotive",
    "biotech": "biotech",
    "hpc_crypto_infrastructure": "hpc_crypto_infrastructure",
    "epc": "epc_construction",
    "epc_construction": "epc_construction",
    "saas": "saas",
    "holding_company": "holding_company",
    "general": "general",
}

_VERIFIED_INDUSTRY_PATTERNS = (
    ("steel_materials", re.compile(r"steel|metals?|materials?|철강|소재", re.I)),
    (
        "transport_logistics",
        re.compile(r"transport|logistics|shipping|운송|물류|해운", re.I),
    ),
    ("insurance", re.compile(r"insurance|reinsurance|보험|재보험", re.I)),
    ("automotive", re.compile(r"automotive|automobile|자동차|완성차", re.I)),
    ("biotech", re.compile(r"biotech|biopharma|pharmaceutical|바이오|신약", re.I)),
    ("epc_construction", re.compile(r"\bepc\b|construction|건설|플랜트", re.I)),
    ("holding_company", re.compile(r"holding company|지주", re.I)),
    ("semiconductor", re.compile(r"semiconductor|반도체", re.I)),
)

_FRAMEWORK_DRIVERS = {
    "memory": (
        "asp",
        "shipment",
        "premium_mix",
        "yield",
        "inventory",
        "capex",
        "free_cash_flow",
    ),
    "semiconductor": (
        "segment_contribution",
        "utilization",
        "product_mix",
        "capex",
        "free_cash_flow",
    ),
    "semiconductor_foundry": (
        "utilization",
        "wafer_pricing",
        "node_mix",
        "advanced_packaging",
        "capex",
        "free_cash_flow",
    ),
    "insurance": (
        "loss_ratio",
        "combined_ratio",
        "investment_yield",
        "roe",
        "capital_adequacy",
    ),
    "transport_logistics": (
        "volume",
        "freight_rate",
        "fuel_cost",
        "contract_mix",
        "working_capital",
        "operating_cash_flow",
    ),
    "steel_materials": (
        "spread",
        "raw_material_cost",
        "capacity_utilization",
        "inventory",
        "normalized_earnings",
        "operating_cash_flow",
    ),
    "automotive": (
        "volume",
        "asp",
        "product_mix",
        "incentives",
        "capex",
        "free_cash_flow",
    ),
    "biotech": (
        "cash_runway",
        "cash_burn",
        "clinical_milestone",
        "probability_of_success",
        "licensing",
        "dilution",
    ),
    "hpc_crypto_infrastructure": (
        "power_capacity",
        "power_cost",
        "utilization",
        "customer_contract",
        "capex",
        "financing_need",
    ),
    "epc_construction": (
        "orders",
        "backlog",
        "project_mix",
        "project_margin",
        "working_capital",
    ),
    "saas": (
        "arr",
        "nrr",
        "gross_margin",
        "operating_leverage",
        "free_cash_flow",
    ),
    "holding_company": (
        "subsidiary_value",
        "ownership",
        "net_debt",
        "holding_discount",
        "capital_allocation",
    ),
    "general": (
        "revenue",
        "operating_margin",
        "operating_cash_flow",
        "balance_sheet",
    ),
}

_CAUSAL_CHAINS = {
    "memory": ("pricing_and_mix", "margin", "inventory_and_capex", "free_cash_flow", "mid_cycle_value"),
    "semiconductor": ("product_and_segment_mix", "margin", "capex", "cash_conversion", "company_value"),
    "semiconductor_foundry": ("utilization_and_node_mix", "margin", "capex", "cash_conversion", "roic"),
    "insurance": ("underwriting_and_investment", "earnings", "roe", "capital", "pbr_and_distribution"),
    "transport_logistics": ("volume_rate_and_cost", "revenue", "margin", "working_capital", "cash_conversion"),
    "steel_materials": ("spread_and_utilization", "margin", "normalized_earnings", "cash_conversion", "cycle_value"),
    "automotive": ("volume_price_and_mix", "margin", "capex", "free_cash_flow", "execution_value"),
    "biotech": ("cash_and_burn", "runway", "milestone_probability", "financing", "risk_adjusted_value"),
    "hpc_crypto_infrastructure": ("contracted_power_and_utilization", "revenue", "margin", "capex_and_financing", "cash_flow_and_dilution"),
    "epc_construction": ("orders_and_backlog", "revenue_recognition", "project_margin", "working_capital", "cash_conversion"),
    "saas": ("arr_and_nrr", "gross_margin", "operating_leverage", "free_cash_flow", "growth_quality_value"),
    "holding_company": ("subsidiary_value_and_ownership", "net_debt", "capital_allocation", "holding_discount", "nav"),
    "general": ("revenue", "margin", "cash_flow", "balance_sheet", "valuation_and_risk"),
}

_DECISION_FOCUS = {
    "memory": ("cycle_position_and_normalized_value", "asp_mix_supply_discipline", "asp_inventory_capex_and_fcf"),
    "semiconductor": ("segment_evidence_and_entry_value", "segment_execution_and_cash_conversion", "segment_margin_capex_and_fcf"),
    "semiconductor_foundry": ("utilization_margin_and_entry_value", "node_mix_execution_and_capex", "utilization_pricing_margin_and_fcf"),
    "insurance": ("roe_capital_and_entry_value", "underwriting_persistence_and_capital", "combined_ratio_roe_and_capital"),
    "transport_logistics": ("margin_recovery_rr_and_value", "margin_and_cash_conversion", "rate_mix_margin_and_ocf"),
    "steel_materials": ("cycle_normalization_and_value", "spread_margin_and_cash_conversion", "spread_inventory_margin_and_ocf"),
    "automotive": ("margin_fcf_and_option_expectation", "mix_incentive_and_execution", "volume_mix_margin_and_fcf"),
    "biotech": ("runway_milestone_and_dilution", "milestone_execution_and_runway", "milestone_cash_burn_and_financing"),
    "hpc_crypto_infrastructure": ("contracted_capacity_and_financing", "commissioning_cash_flow_and_dilution", "capacity_contract_capex_and_funding"),
    "epc_construction": ("backlog_quality_and_entry_value", "project_margin_and_working_capital", "backlog_margin_and_cash_conversion"),
    "saas": ("retention_growth_and_fcf", "retention_and_operating_leverage", "arr_nrr_margin_and_fcf"),
    "holding_company": ("nav_discount_and_capital_allocation", "subsidiary_value_and_net_debt", "nav_debt_and_shareholder_return"),
    "general": ("verified_earnings_cash_and_entry_value", "earnings_persistence_and_risk", "margin_cash_flow_and_balance_sheet"),
}

_FACT_FAMILY_MARKERS = {
    "revenue": ("revenue", "sales"),
    "operating_income": ("operating_income", "operating_profit"),
    "operating_margin": ("operating_margin",),
    "inventory": ("inventory",),
    "operating_cash_flow": ("operating_cash_flow", "cash_from_operations"),
    "free_cash_flow": ("free_cash_flow", "fcf"),
    "capex": ("capex", "capital_expenditure"),
    "roe": ("return_on_equity", "roe"),
    "arr": ("annual_recurring_revenue", "arr"),
    "nrr": ("net_revenue_retention", "nrr"),
    "project_margin": ("project_margin", "contract_margin"),
    "orders": ("orders", "order_value"),
    "backlog": ("backlog",),
    "cash_runway": ("cash_runway",),
    "cash_burn": ("cash_burn",),
    "dilution": ("dilution", "diluted_share"),
    "price": ("current_price",),
    "risk_reward": ("risk_reward", "rr_basis"),
    "pbr": ("price_to_book", "historical_pb"),
    "pe": ("trailing_pe", "forward_pe", "historical_pe"),
}

_CHEAP_LANGUAGE = re.compile(r"cheap|undervalu|저평가|싸다|싼\s*구간", re.I)
_LOW_PE_LANGUAGE = re.compile(r"(?:low|낮은).{0,18}(?:per|이익\s*배수)", re.I)
_LOW_PBR_LANGUAGE = re.compile(r"(?:low|낮은).{0,18}(?:pbr|장부가|장부가치)", re.I)
_PER_LANGUAGE = re.compile(r"(?<![A-Za-z])per(?![A-Za-z])|이익\s*배수", re.I)
_PEER_VERDICT_LEAP = re.compile(
    r"(?:peer|동종업계|비교군).{0,60}(?:discount|할인|premium|프리미엄)"
    r".{0,35}(?:cheap|저평가|overvalued|고평가|비싸)",
    re.I,
)
_ORDER_MARGIN_LEAP = re.compile(
    r"(?:수주|order).{0,45}(?:마진|margin|수익성).{0,15}(?:개선|상승|확대|improv|increase)",
    re.I,
)
_THEME_REVENUE_LEAP = re.compile(
    r"(?:hyperscaler|하이퍼스케일러|cloud\s*capex|클라우드\s*capex).{0,55}"
    r"(?:회사|기업|매출|revenue).{0,20}(?:확정|증가|성장|반영|confirm|increase|grow)",
    re.I,
)
_GENERIC_UNKNOWN = re.compile(
    r"^(?:추가\s*확인이\s*필요(?:합니다)?|확인이\s*필요(?:합니다)?|unknown)\.?$",
    re.I,
)


@dataclass(frozen=True)
class IndustryReasoningPlan:
    contract: str
    primary_framework: str
    secondary_contexts: tuple[str, ...]
    confidence: str
    source: str
    evidence: tuple[str, ...]
    available_fact_families: tuple[str, ...]
    selected_operating_facts: tuple[str, ...]
    missing_drivers: tuple[str, ...]
    valuation_framework: str
    causal_chain: tuple[str, ...]
    observer_focus: str
    holder_focus: str
    next_confirmation: str

    def as_dict(self) -> dict[str, object]:
        return {
            "contract": self.contract,
            "primary_framework": self.primary_framework,
            "secondary_contexts": list(self.secondary_contexts),
            "confidence": self.confidence,
            "source": self.source,
            "evidence": list(self.evidence),
            "available_fact_families": list(self.available_fact_families),
            "selected_operating_facts": list(self.selected_operating_facts),
            "missing_drivers": list(self.missing_drivers),
            "valuation_framework": self.valuation_framework,
            "causal_chain": list(self.causal_chain),
            "observer_focus": self.observer_focus,
            "holder_focus": self.holder_focus,
            "next_confirmation": self.next_confirmation,
        }


def build_industry_reasoning_plan(
    stock: dict[str, object],
    *,
    facts_used: Iterable[str] = (),
) -> IndustryReasoningPlan:
    routing = _mapping(stock.get("knowledge_routing"))
    industry_routing = _mapping(routing.get("industry_routing"))
    routed_key = str(routing.get("industry_key") or "general")
    framework = _ROUTING_KEY_MAP.get(routed_key, "general")
    confidence = str(industry_routing.get("confidence") or "low")
    source = str(industry_routing.get("source") or "unclassified")
    evidence = tuple(
        str(item)
        for item in industry_routing.get("evidence", [])
        if isinstance(item, str)
    )

    profile = _mapping(stock.get("company_profile"))
    if framework == "general" and profile.get("quality") == "verified":
        verified_text = " ".join(
            str(stock.get(field) or "") for field in ("industry", "sector")
        )
        inferred = next(
            (
                candidate
                for candidate, pattern in _VERIFIED_INDUSTRY_PATTERNS
                if pattern.search(verified_text)
            ),
            None,
        )
        if inferred is not None:
            framework = inferred
            confidence = "high" if stock.get("industry") else "medium"
            source = "verified_company_industry"
            evidence = (f"company.industry={stock.get('industry')}",)

    if framework not in SUPPORTED_FRAMEWORKS:
        framework = "general"
        confidence = "low"
        source = "unsupported_route_fallback"
        evidence = ()

    secondary = tuple(
        dict.fromkeys(
            str(item)
            for item in industry_routing.get("secondary_frameworks", [])
            if isinstance(item, str)
        )
    )
    available = available_fact_families(stock)
    used = set(str(item) for item in facts_used)
    selected = tuple(
        sorted(
            family
            for family in available
            if _family_has_used_fact(stock, family, used)
        )
    )
    missing = tuple(
        driver
        for driver in _FRAMEWORK_DRIVERS[framework]
        if driver not in available
    )
    observer_focus, holder_focus, next_confirmation = _DECISION_FOCUS[framework]
    return IndustryReasoningPlan(
        contract=INDUSTRY_REASONING_CONTRACT,
        primary_framework=framework,
        secondary_contexts=secondary,
        confidence=confidence,
        source=source,
        evidence=evidence,
        available_fact_families=tuple(sorted(available)),
        selected_operating_facts=selected,
        missing_drivers=missing,
        valuation_framework=_valuation_framework(framework),
        causal_chain=_CAUSAL_CHAINS[framework],
        observer_focus=observer_focus,
        holder_focus=holder_focus,
        next_confirmation=next_confirmation,
    )


def available_fact_families(stock: dict[str, object]) -> set[str]:
    families: set[str] = set()
    for fact in stock.get("fact_catalog", []):
        if not isinstance(fact, dict) or _fact_denied(fact):
            continue
        searchable = " ".join(
            (
                str(fact.get("fact_id") or ""),
                str(fact.get("fact_type") or ""),
                " ".join(_nested_keys(_mapping(fact.get("fields")))),
            )
        ).casefold()
        for family, markers in _FACT_FAMILY_MARKERS.items():
            if any(_marker_present(searchable, marker) for marker in markers):
                families.add(family)
    return families


def _marker_present(searchable: str, marker: str) -> bool:
    return bool(
        re.search(
            rf"(?<![a-z0-9]){re.escape(marker.casefold())}(?![a-z0-9])",
            searchable,
        )
    )


def industry_reasoning_reference_errors(
    review: dict[str, object],
    stock: dict[str, object],
    *,
    prefix: str,
) -> tuple[list[str], list[dict[str, object]]]:
    values = review.pop(INDUSTRY_REASONING_REFERENCE_FIELD, [])
    if stock.get("industry_reasoning_contract") != INDUSTRY_REASONING_CONTRACT:
        return [f"{prefix}:industry_reasoning_contract_unsupported"], []
    if not isinstance(values, list):
        return [f"{prefix}:industry_reasoning_refs_not_list"], []

    facts = {
        str(item.get("fact_id") or ""): item
        for item in stock.get("fact_catalog", [])
        if isinstance(item, dict) and item.get("fact_id")
    }
    facts_used = {
        str(item) for item in review.get("facts_used", [])
    } if isinstance(review.get("facts_used"), list) else set()
    plan = build_industry_reasoning_plan(stock, facts_used=facts_used)
    errors: list[str] = []
    accepted: list[dict[str, object]] = []
    seen: set[str] = set()
    for index, item in enumerate(values):
        if not isinstance(item, dict):
            errors.append(f"{prefix}:industry_reasoning_ref_not_object:{index}")
            continue
        ref_id = str(item.get("ref_id") or "")
        text_ref = str(item.get("text_ref") or "")
        exact_span = _normalize(str(item.get("exact_text_span") or ""))
        claim_type = str(item.get("claim_type") or "")
        framework = str(item.get("primary_framework") or "")
        supporting = {
            str(value) for value in item.get("supporting_fact_ids", [])
        } if isinstance(item.get("supporting_fact_ids"), list) else set()
        required = {
            str(value) for value in item.get("required_fact_families", [])
        } if isinstance(item.get("required_fact_families"), list) else set()
        if not ref_id or ref_id in seen:
            errors.append(f"{prefix}:industry_reasoning_ref_invalid_id:{ref_id or index}")
            continue
        seen.add(ref_id)
        target = _normalize(_text_value(review, text_ref))
        if not exact_span or target.count(exact_span) != 1:
            errors.append(f"{prefix}:industry_reasoning_span_not_unique:{ref_id}")
            continue
        if framework != plan.primary_framework:
            errors.append(f"{prefix}:industry_reasoning_framework_mismatch:{ref_id}")
            continue
        if supporting and (
            not supporting.issubset(facts)
            or not supporting.issubset(facts_used)
            or any(_fact_denied(facts[fact_id]) for fact_id in supporting)
        ):
            errors.append(f"{prefix}:industry_reasoning_fact_not_grounded:{ref_id}")
            continue
        if claim_type == "verified_causal_interpretation":
            if not supporting or not required.issubset(plan.available_fact_families):
                errors.append(f"{prefix}:industry_reasoning_missing_middle_fact:{ref_id}")
                continue
        elif claim_type == "missing_driver_unknown":
            if not required or required.intersection(plan.available_fact_families):
                errors.append(f"{prefix}:industry_reasoning_unknown_not_missing:{ref_id}")
                continue
        elif claim_type not in {"valuation_boundary", "attribution_boundary"}:
            errors.append(f"{prefix}:industry_reasoning_claim_type_invalid:{ref_id}")
            continue
        accepted.append(
            {
                "ref_id": ref_id,
                "text_ref": text_ref,
                "exact_text_span": exact_span,
                "normalized_span_sha256": hashlib.sha256(
                    exact_span.encode("utf-8")
                ).hexdigest(),
                "claim_type": claim_type,
                "primary_framework": framework,
                "supporting_fact_ids": sorted(supporting),
                "required_fact_families": sorted(required),
            }
        )
    return list(dict.fromkeys(errors)), accepted


def industry_reasoning_guardrail_flags(
    review: object,
    stock: dict[str, object],
) -> list[str]:
    plan = build_industry_reasoning_plan(
        stock,
        facts_used=getattr(review, "facts_used", ()),
    )
    text = "\n".join(_review_texts(review))
    lowered = text.casefold()
    available = set(plan.available_fact_families)
    flags: list[str] = []
    if plan.primary_framework == "memory" and _LOW_PE_LANGUAGE.search(text) and _CHEAP_LANGUAGE.search(text):
        flags.append("industry_reasoning:memory_low_trailing_pe_only")
    if plan.primary_framework == "insurance" and _LOW_PBR_LANGUAGE.search(text) and _CHEAP_LANGUAGE.search(text):
        if not {"roe", "capital_adequacy"}.intersection(available):
            flags.append("industry_reasoning:insurance_low_pbr_without_returns_or_capital")
    if plan.primary_framework == "biotech" and _PER_LANGUAGE.search(text) and _CHEAP_LANGUAGE.search(text):
        flags.append("industry_reasoning:biotech_per_cheap")
    if _PEER_VERDICT_LEAP.search(text):
        flags.append("industry_reasoning:peer_relative_multiple_used_as_verdict")
    if plan.primary_framework == "epc_construction" and _ORDER_MARGIN_LEAP.search(text):
        if "project_margin" not in available:
            flags.append("industry_reasoning:epc_order_to_margin_leap")
    if _THEME_REVENUE_LEAP.search(text) and not {"revenue", "customer_contract"}.intersection(available):
        flags.append("industry_reasoning:theme_promoted_to_company_revenue")
    if plan.primary_framework == "insurance" and re.search(r"\b(?:arr|nrr)\b", lowered):
        flags.append("industry_reasoning:insurance_saas_metric_mismatch")
    for unknown in getattr(review, "unknowns", ()):  # type: ignore[union-attr]
        if isinstance(unknown, str) and _GENERIC_UNKNOWN.fullmatch(unknown.strip()):
            flags.append("industry_reasoning:generic_unknown")
    return list(dict.fromkeys(flags))


def _valuation_framework(framework: str) -> str:
    return {
        "memory": "normalized_earnings_pbr_and_cash_conversion",
        "semiconductor": "company_level_multiple_with_segment_attribution_boundary",
        "semiconductor_foundry": "utilization_margin_cash_conversion_and_roic",
        "insurance": "roe_capital_underwriting_and_pbr",
        "transport_logistics": "mid_cycle_margin_cash_conversion_and_valuation",
        "steel_materials": "normalized_earnings_pbr_and_cash_conversion",
        "automotive": "margin_free_cash_flow_and_execution_option_value",
        "biotech": "cash_runway_risk_adjusted_pipeline_and_dilution",
        "hpc_crypto_infrastructure": "contracted_capacity_capex_financing_and_dilution",
        "epc_construction": "backlog_margin_working_capital_and_cash_conversion",
        "saas": "recurring_revenue_quality_operating_leverage_and_fcf",
        "holding_company": "nav_ownership_net_debt_and_capital_allocation",
        "general": "revenue_margin_cash_balance_sheet_and_valuation",
    }[framework]


def _family_has_used_fact(
    stock: dict[str, object],
    family: str,
    facts_used: set[str],
) -> bool:
    if not facts_used:
        return False
    markers = _FACT_FAMILY_MARKERS.get(family, ())
    for fact in stock.get("fact_catalog", []):
        if not isinstance(fact, dict) or str(fact.get("fact_id") or "") not in facts_used:
            continue
        searchable = " ".join(
            (
                str(fact.get("fact_id") or ""),
                str(fact.get("fact_type") or ""),
                " ".join(_nested_keys(_mapping(fact.get("fields")))),
            )
        ).casefold()
        if any(marker.casefold() in searchable for marker in markers):
            return True
    return False


def _fact_denied(fact: dict[str, object]) -> bool:
    if fact.get("interpretation_eligible") is False:
        return True
    fields = _mapping(fact.get("fields"))
    if str(fields.get("state") or "") == "denied":
        return True
    quality = fact.get("field_quality")
    return bool(
        isinstance(quality, dict)
        and quality
        and all(
            isinstance(value, dict) and value.get("state") == "denied"
            for value in quality.values()
        )
    )


def _nested_keys(value: dict[str, object], prefix: str = "") -> list[str]:
    output: list[str] = []
    for key, item in value.items():
        path = f"{prefix}.{key}" if prefix else key
        output.append(path)
        if isinstance(item, dict):
            output.extend(_nested_keys(item, path))
    return output


def _review_texts(review: object) -> list[str]:
    output: list[str] = []
    for name in (
        "core_judgment",
        "business_earnings",
        "price_positioning",
        "supply_analysis",
        "valuation_analysis",
    ):
        section = getattr(review, name, None)
        for field in ("text", "new_observer_view", "holder_view"):
            value = getattr(section, field, None)
            if isinstance(value, str):
                output.append(value)
    for name in ("unknowns", "priority_watch", "next_checks"):
        values = getattr(review, name, ())
        output.extend(str(value) for value in values if isinstance(value, str))
    return output


def _text_value(review: dict[str, object], text_ref: str) -> str:
    node: object = review
    for part in text_ref.split("."):
        match = re.fullmatch(r"([A-Za-z_][A-Za-z0-9_]*)(?:\[([0-9]+)\])?", part)
        if match is None or not isinstance(node, dict):
            return ""
        key, raw_index = match.groups()
        node = node.get(key)
        if raw_index is not None:
            if not isinstance(node, list) or int(raw_index) >= len(node):
                return ""
            node = node[int(raw_index)]
    return node if isinstance(node, str) else ""


def _normalize(value: str) -> str:
    return " ".join(value.split())


def _mapping(value: object) -> dict[str, object]:
    return value if isinstance(value, dict) else {}
