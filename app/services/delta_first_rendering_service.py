from __future__ import annotations

import copy
from dataclasses import dataclass
from typing import Iterable

from app.services.numeric_provenance_service import TYPED_VALUATION_CONTRACT
from app.services.numeric_semantic_registry import build_numeric_registry
from app.services.industry_reasoning_service import (
    INDUSTRY_REASONING_CONTRACT,
    INDUSTRY_REASONING_REFERENCE_FIELD,
    build_industry_reasoning_plan,
)
from app.services.semantic_decision_service import (
    SEMANTIC_CLAIM_REFERENCE_FIELD,
    SEMANTIC_SCOPE_CONTRACT,
    VALUATION_CONTEXT_REFERENCE_FIELD,
    assign_listed_security_valuation_scope,
    build_valuation_context_selection,
    financial_cross_field_coherence_report,
    historical_valuation_selection,
    select_decision_material_delta,
)


DELTA_FIRST_RENDERING_CONTRACT = "delta-first-rendering-v1"
RECOVERY_FACT_PREFIX = "earnings:recovery:"


@dataclass(frozen=True)
class DeltaFirstRenderPlan:
    contract: str
    material_delta: str
    today_change_label: str
    section_order: tuple[str, ...]
    suppressed_sections: tuple[str, ...]
    suppression_reasons: dict[str, str]
    decision_selection: dict[str, object]

    def as_dict(self) -> dict[str, object]:
        return {
            "contract": self.contract,
            "material_delta": self.material_delta,
            "today_change_label": self.today_change_label,
            "section_order": list(self.section_order),
            "suppressed_sections": list(self.suppressed_sections),
            "suppression_reasons": dict(self.suppression_reasons),
            "decision_selection": dict(self.decision_selection),
        }


def build_delta_first_render_plan(
    stock: dict[str, object],
    *,
    financial_available: bool,
) -> DeltaFirstRenderPlan:
    selection = select_decision_material_delta(
        stock,
        financial_available=financial_available,
    )
    material_delta = selection.selected_primary
    today_change = {
        "earnings_or_thesis": "사업·실적 판단 근거 변화",
        "valuation": "가치평가 구간 변화",
        "price_structure": "가격 구조 전환",
        "risk_reward": "현재가 손익비 변화",
        "supply": "수급 시간축 엇갈림",
        "none": "중요 변화 없음",
    }.get(material_delta, "검증된 판단 근거 변화")

    if material_delta == "price_structure":
        section_order = (
            "price",
            "core",
            "supply",
            "valuation",
            "warnings",
            "next",
            "unknown",
        )
    elif material_delta == "supply":
        section_order = (
            "supply",
            "core",
            "price",
            "valuation",
            "warnings",
            "next",
            "unknown",
        )
    elif financial_available:
        section_order = (
            "core",
            "price",
            "supply",
            "valuation",
            "warnings",
            "next",
            "unknown",
        )
    else:
        section_order = (
            "core",
            "valuation",
            "price",
            "supply",
            "warnings",
            "next",
            "unknown",
        )
    return DeltaFirstRenderPlan(
        contract=DELTA_FIRST_RENDERING_CONTRACT,
        material_delta=material_delta,
        today_change_label=today_change,
        section_order=section_order,
        suppressed_sections=("business", "priority_watch"),
        suppression_reasons={
            "business": "decision_relevant_financial_facts_integrated_into_core",
            "priority_watch": "overlaps_with_next_confirmation_and_unknown",
        },
        decision_selection=selection.as_dict(),
    )


def financial_recovery_fact(
    ticker: str,
    recovered: dict[str, object],
) -> dict[str, object] | None:
    fields = _mapping(recovered.get("fields"))
    earnings: dict[str, object] = {
        "financial_period_required": True,
        "field_period_labels": {},
        "field_statement_basis": {},
    }
    quality: dict[str, object] = {}
    for source_name, target_name, period_key in (
        ("revenue", "revenue", "latest_revenue"),
        ("operating_income", "operating_income", "latest_operating_income"),
        ("net_income", "net_income", "latest_net_income"),
    ):
        source = _mapping(fields.get(source_name))
        lineage = _mapping(source.get("lineage"))
        if source.get("status") != "verified_usable" or not lineage:
            continue
        earnings[target_name] = {
            "value": source.get("value"),
            "currency": lineage.get("currency"),
        }
        _add_period_basis(earnings, quality, period_key, target_name, lineage)

    margin = _mapping(fields.get("operating_margin"))
    operating = _mapping(_mapping(fields.get("operating_income")).get("lineage"))
    if margin.get("status") == "verified_usable" and operating:
        earnings["operating_margin_pct"] = margin.get("value")
        _add_period_basis(
            earnings,
            quality,
            "latest_operating_margin",
            "operating_margin_pct",
            operating,
        )

    for source_name, target_name, period_key in (
        ("revenue", "revenue_yoy_pct", "latest_revenue_yoy"),
        (
            "operating_income",
            "operating_income_yoy_pct",
            "latest_operating_income_yoy",
        ),
        ("net_income", "net_income_yoy_pct", "latest_net_income_yoy"),
    ):
        source = _mapping(fields.get(source_name))
        yoy = _mapping(source.get("yoy"))
        lineage = _mapping(source.get("lineage"))
        if (
            source.get("status") != "verified_usable"
            or yoy.get("status") != "verified_usable"
            or not lineage
        ):
            continue
        earnings[target_name] = yoy.get("value")
        _add_period_basis(
            earnings,
            quality,
            period_key,
            target_name,
            lineage,
        )

    if not quality:
        return None
    return {
        "fact_id": f"{RECOVERY_FACT_PREFIX}{ticker}",
        "fact_type": "earnings",
        "fields": earnings,
        "field_quality": quality,
        "interpretation_eligible": True,
        "source_contract": "financial-lineage-v2",
    }


def prepare_delta_first_packet(
    source_packet: dict[str, object],
    recoveries: dict[str, object],
    tickers: Iterable[str],
    *,
    packet_id: str,
) -> dict[str, object]:
    selected = set(tickers)
    packet = copy.deepcopy(source_packet)
    packet["packet_id"] = packet_id
    stocks: list[dict[str, object]] = []
    for value in packet.get("stocks", []):
        if not isinstance(value, dict) or str(value.get("ticker") or "") not in selected:
            continue
        stock = value
        ticker = str(stock["ticker"])
        recovery = _mapping(recoveries.get(ticker))
        fact = financial_recovery_fact(ticker, recovery) if recovery else None
        catalog = [
            item
            for item in stock.get("fact_catalog", [])
            if isinstance(item, dict)
            and not str(item.get("fact_id") or "").startswith(RECOVERY_FACT_PREFIX)
        ]
        for item in catalog:
            fact_id = str(item.get("fact_id") or "")
            if fact_id == "chart:structure:risk_reward:current_price":
                item["fact_type"] = "chart_risk_reward_current_price"
                _mapping(item.get("fields"))["rr_basis"] = "current_price"
            elif fact_id == "chart:structure:risk_reward:support_entry":
                item["fact_type"] = "chart_risk_reward_support_entry"
                _mapping(item.get("fields"))["rr_basis"] = "support_entry"
        assign_listed_security_valuation_scope(catalog)
        if fact is not None:
            catalog.append(fact)
        stock["fact_catalog"] = catalog
        stock["numeric_registry"] = build_numeric_registry(catalog)
        stock["typed_valuation_interpretation_contract"] = TYPED_VALUATION_CONTRACT
        stock["semantic_scope_contract"] = SEMANTIC_SCOPE_CONTRACT
        stock["industry_reasoning_contract"] = INDUSTRY_REASONING_CONTRACT
        stock["denied_semantic_families"] = _denied_semantic_families(
            stock,
            recovery,
        )
        stocks.append(stock)
    packet["stocks"] = stocks
    return packet


def build_delta_first_stock_draft(
    stock: dict[str, object],
    original_review: dict[str, object],
    recovery: dict[str, object],
) -> tuple[dict[str, object], dict[str, object]]:
    ticker = str(stock.get("ticker") or "")
    registry = {
        (str(item.get("fact_id") or ""), str(item.get("field_path") or "")): item
        for item in stock.get("numeric_registry", [])
        if isinstance(item, dict)
        and item.get("registered") is True
        and item.get("prose_allowed") is True
    }
    references: list[dict[str, object]] = []
    semantic_claim_refs: list[dict[str, object]] = []
    fact_ids_by_section: dict[str, set[str]] = {
        name: set()
        for name in ("core", "business", "price", "supply", "valuation")
    }

    def numeric(
        text_ref: str,
        fact_id: str,
        field_path: str,
        *,
        role: str = "value",
        postposition: str | None = None,
    ) -> str | None:
        if (fact_id, field_path) not in registry:
            return None
        ref_id = f"d{len(references) + 1}"
        item: dict[str, object] = {
            "ref_id": ref_id,
            "fact_id": fact_id,
            "field_path": field_path,
            "text_ref": text_ref,
            "role": role,
        }
        if postposition:
            item["postposition"] = postposition
        references.append(item)
        section = text_ref.split(".", maxsplit=1)[0]
        section = "price" if section == "price_positioning" else section
        section = "supply" if section == "supply_analysis" else section
        section = "valuation" if section == "valuation_analysis" else section
        section = "core" if section == "core_judgment" else section
        section = "business" if section == "business_earnings" else section
        if section in fact_ids_by_section:
            fact_ids_by_section[section].add(fact_id)
        return f"{{{{numeric:{ref_id}}}}}"

    industry_plan = build_industry_reasoning_plan(stock)
    profile = _reasoning_profile(stock)
    recovery_fact_id = f"{RECOVERY_FACT_PREFIX}{ticker}"
    financial_available = any(
        (recovery_fact_id, path) in registry
        for path in (
            "fields.revenue.value",
            "fields.operating_income.value",
            "fields.net_income.value",
        )
    )
    core_text = _financial_core_text(
        profile,
        recovery,
        recovery_fact_id,
        numeric,
    )
    business_text = _financial_detail_text(
        profile,
        recovery_fact_id,
        numeric,
    )
    if not financial_available:
        quality_facts = _financial_quality_facts(stock)
        fact_ids_by_section["core"].update(quality_facts)
        fact_ids_by_section["business"].update(quality_facts)
        if quality_facts:
            semantic_claim_refs.append(
                {
                    "ref_id": "financial_denial_explanation",
                    "text_ref": "core_judgment.text",
                    "exact_text_span": (
                        "공식 손익 수치는 품질 충돌 때문에 이번 판단에 "
                        "사용하지 않습니다."
                    ),
                    "claim_type": "denial_explanation",
                    "economic_scope": "company",
                    "supporting_fact_ids": [sorted(quality_facts)[0]],
                    "semantic_families": ["earnings"],
                }
            )

    price_text, observer_text, holder_text = _price_texts(
        profile,
        stock,
        numeric,
    )
    supply_text = _supply_text(profile, stock, numeric)
    (
        valuation_text,
        historical_valuation,
        valuation_context,
        valuation_context_span,
    ) = _valuation_text(
        profile,
        recovery,
        stock,
        numeric,
    )
    valuation_reference_paths = {
        str(item.get("field_path") or "")
        for item in references
        if str(item.get("text_ref") or "").startswith("valuation_analysis")
    }
    fact_ids_by_section["valuation"].discard("valuation:current")
    if "fields.trailing_pe" in valuation_reference_paths:
        fact_ids_by_section["valuation"].add("valuation:trailing_earnings")
    if "fields.price_to_book" in valuation_reference_paths:
        fact_ids_by_section["valuation"].add("valuation:book")
    selected_historical = historical_valuation.get("selected")
    if isinstance(selected_historical, dict):
        fact_ids_by_section["valuation"].add(
            str(selected_historical.get("fact_id") or "")
        )
    valuation_interpretation_refs = _valuation_interpretation_refs(
        profile,
        references,
        selected_historical,
    )

    unknown = _profile_unknown(profile, financial_available)
    next_check = _profile_next_check(
        profile,
        financial_available,
        recovery_fact_id,
        numeric,
    )
    valid_fact_ids = {
        str(item.get("fact_id") or "")
        for item in stock.get("fact_catalog", [])
        if isinstance(item, dict)
    }
    facts_used = sorted(
        {
            fact_id
            for values in fact_ids_by_section.values()
            for fact_id in values
            if fact_id in valid_fact_ids
        }
        | {
            str(item.get("fact_id") or "")
            for item in references
            if str(item.get("fact_id") or "") in valid_fact_ids
        }
    )
    frameworks = [str(item) for item in original_review.get("frameworks_used", [])]
    primary = str(
        _mapping(_mapping(stock.get("knowledge_routing")).get("industry_routing")).get(
            "primary_framework"
        )
        or ""
    )
    if primary and primary not in frameworks:
        frameworks.append(primary)

    industry_reasoning_refs: list[dict[str, object]] = []
    missing_family = _unknown_required_family(
        profile,
        industry_plan.missing_drivers,
    )
    if missing_family:
        industry_reasoning_refs.append(
            {
                "ref_id": "industry_missing_driver",
                "text_ref": "unknowns[0]",
                "exact_text_span": unknown,
                "claim_type": "missing_driver_unknown",
                "primary_framework": industry_plan.primary_framework,
                "supporting_fact_ids": [],
                "required_fact_families": [missing_family],
            }
        )
    valuation_boundary = _valuation_boundary_span(profile, valuation_text)
    valuation_support = sorted(fact_ids_by_section["valuation"])
    if valuation_boundary and valuation_support:
        industry_reasoning_refs.append(
            {
                "ref_id": "industry_valuation_boundary",
                "text_ref": "valuation_analysis.text",
                "exact_text_span": valuation_boundary,
                "claim_type": "valuation_boundary",
                "primary_framework": industry_plan.primary_framework,
                "supporting_fact_ids": valuation_support,
                "required_fact_families": [],
            }
        )
    valuation_relation = _valuation_relation_span(profile, valuation_text)
    if valuation_relation and valuation_support:
        industry_reasoning_refs.append(
            {
                "ref_id": "industry_valuation_relation",
                "text_ref": "valuation_analysis.text",
                "exact_text_span": valuation_relation,
                "claim_type": "valuation_boundary",
                "primary_framework": industry_plan.primary_framework,
                "supporting_fact_ids": valuation_support,
                "required_fact_families": [],
            }
        )

    draft = {
        "ticker": ticker,
        "thesis_version": original_review.get("thesis_version"),
        "ai_thesis_assessment": original_review.get("ai_thesis_assessment"),
        "earnings_estimate_view": original_review.get("earnings_estimate_view"),
        "valuation_view": original_review.get("valuation_view"),
        "facts_used": facts_used,
        "frameworks_used": frameworks,
        "core_judgment": {
            "text": core_text,
            "fact_ids": sorted(fact_ids_by_section["core"]),
        },
        "business_earnings": {
            "text": business_text,
            "fact_ids": sorted(fact_ids_by_section["business"]),
        },
        "price_positioning": {
            "text": price_text,
            "new_observer_view": observer_text,
            "holder_view": holder_text,
            "fact_ids": sorted(fact_ids_by_section["price"]),
        },
        "supply_analysis": {
            "text": supply_text,
            "fact_ids": sorted(fact_ids_by_section["supply"]),
        },
        "valuation_analysis": {
            "text": valuation_text,
            "fact_ids": sorted(fact_ids_by_section["valuation"]),
        },
        "numeric_claims": [],
        "numeric_fact_refs": references,
        "valuation_interpretation_refs": valuation_interpretation_refs,
        VALUATION_CONTEXT_REFERENCE_FIELD: {
            **valuation_context,
            "text_ref": "valuation_analysis.text",
            "exact_text_span": valuation_context_span,
        },
        SEMANTIC_CLAIM_REFERENCE_FIELD: semantic_claim_refs,
        INDUSTRY_REASONING_REFERENCE_FIELD: industry_reasoning_refs,
        "unknowns": [unknown],
        "priority_watch": list(original_review.get("priority_watch", []))[:2],
        "next_checks": [next_check],
        "confidence": original_review.get("confidence", 0.75),
    }
    available_sections = [
        "core",
        "business",
        "price",
        "supply",
        "valuation",
        "priority_watch",
        "next",
        "unknown",
    ]
    plan = build_delta_first_render_plan(
        stock,
        financial_available=financial_available,
    )
    audit = {
        "ticker": ticker,
        "profile": profile,
        "financial_available": financial_available,
        "available_sections": available_sections,
        "selected_sections": list(plan.section_order),
        "suppressed_sections": list(plan.suppressed_sections),
        "suppression_reasons": plan.suppression_reasons,
        "eligible_fact_counts": _eligible_fact_counts(stock, recovery_fact_id),
        "used_fact_counts": _used_fact_counts(references, plan.section_order),
        "core_investment_claim_count": _sentence_count(core_text),
        "plan": plan.as_dict(),
        "decision_hierarchy": plan.decision_selection,
        "historical_valuation": historical_valuation,
        "valuation_context": valuation_context,
        "financial_cross_field_coherence": financial_cross_field_coherence_report(
            recovery
        ),
        "industry_reasoning": build_industry_reasoning_plan(
            stock,
            facts_used=facts_used,
        ).as_dict(),
    }
    return draft, audit


def _financial_core_text(
    profile: str,
    recovery: dict[str, object],
    fact_id: str,
    numeric: object,
) -> str:
    fields = _mapping(recovery.get("fields"))
    revenue_yoy = numeric(
        "core_judgment.text", fact_id, "fields.revenue_yoy_pct"
    )
    operating_yoy = numeric(
        "core_judgment.text", fact_id, "fields.operating_income_yoy_pct"
    )
    margin = numeric(
        "core_judgment.text", fact_id, "fields.operating_margin_pct"
    )
    if revenue_yoy and operating_yoy:
        revenue_value = _number(_mapping(_mapping(fields.get("revenue")).get("yoy")).get("value"))
        operating_value = _number(
            _mapping(_mapping(fields.get("operating_income")).get("yoy")).get("value")
        )
        if revenue_value is not None and operating_value is not None and revenue_value * operating_value < 0:
            relation = (
                f"{revenue_yoy}, {operating_yoy}로 외형과 영업이익 방향이 엇갈렸습니다."
            )
        else:
            relation = (
                f"{revenue_yoy}, {operating_yoy}로 외형과 영업이익이 같은 방향으로 움직였습니다."
            )
        if margin:
            relation += f" {margin}입니다."
        return f"{_profile_opening(profile)} {relation} {_profile_meaning(profile)}"
    if operating_yoy:
        return (
            f"{_profile_opening(profile)} {operating_yoy}로 영업이익 방향은 확인됩니다. "
            f"{_profile_meaning(profile)}"
        )
    return (
        f"{_profile_opening(profile)} 공식 손익 수치는 품질 충돌 때문에 이번 판단에 "
        "사용하지 않습니다. 따라서 현재 판단은 PBR, 가격구조, 수급과 독립적으로 "
        "확인 가능한 사업 지표에 한정합니다."
    )


def _financial_detail_text(
    profile: str,
    fact_id: str,
    numeric: object,
) -> str:
    values = [
        numeric("business_earnings.text", fact_id, path)
        for path in (
            "fields.revenue.value",
            "fields.operating_income.value",
            "fields.operating_margin_pct",
        )
    ]
    values = [value for value in values if value]
    if not values:
        return (
            "공식 손익 수치의 품질 충돌이 해소되지 않아 금액과 성장률을 표시하지 "
            "않습니다. 독립적으로 검증된 가격·장부가치 근거와 분리해 봅니다."
        )
    return (
        f"{', '.join(values)}로 {_profile_detail_relation(profile)}. "
        f"{_profile_detail_caution(profile)}"
    )


def _price_texts(
    profile: str,
    stock: dict[str, object],
    numeric: object,
) -> tuple[str, str, str]:
    grounding = _mapping(stock.get("state_grounding_requirements"))
    requirements = [
        item for item in grounding.get("price", []) if isinstance(item, dict)
    ]
    current: str | None = None
    support: tuple[str, str] | None = None
    resistance: tuple[str, str] | None = None
    rr: str | None = None
    for requirement in requirements:
        fact_id = str(requirement.get("fact_id") or "")
        paths = [str(item) for item in requirement.get("field_paths", [])]
        if fact_id == "price:current" and paths:
            current = numeric("price_positioning.text", fact_id, paths[0])
        elif "nearest_supports" in fact_id and len(paths) >= 2:
            lower = numeric(
                "price_positioning.text", fact_id, paths[0], role="lower"
            )
            upper = numeric(
                "price_positioning.text", fact_id, paths[1], role="upper"
            )
            if lower and upper:
                support = (lower, upper)
        elif "nearest_resistance" in fact_id and len(paths) >= 2:
            lower = numeric(
                "price_positioning.text", fact_id, paths[0], role="lower"
            )
            upper = numeric(
                "price_positioning.text", fact_id, paths[1], role="upper"
            )
            if lower and upper:
                resistance = (lower, upper)
        elif "risk_reward:current_price" in fact_id and paths:
            rr = numeric("price_positioning.text", fact_id, paths[0])

    parts = [f"{current}입니다." if current else "현재 가격은 확인되지 않습니다."]
    parts.append(
        f"가까운 지지는 {support[0]}부터 {support[1]}까지입니다."
        if support
        else "현재 구조에서 적격 동적 지지는 확인되지 않았습니다."
    )
    parts.append(
        f"가까운 저항은 {resistance[0]}부터 {resistance[1]}까지입니다."
        if resistance
        else "현재 구조에서 적격 동적 저항은 확인되지 않았습니다."
    )
    if rr:
        parts.append(
            f"{rr}입니다. 가까운 저항 대비 하방 무효화 폭이 더 커 신규 추격의 "
            "가격 비대칭은 불리합니다."
        )
        observer_rr = numeric(
            "price_positioning.new_observer_view",
            "chart:structure:risk_reward:current_price",
            "fields.ratio",
        )
        observer = (
            f"{observer_rr}입니다. 신규 관찰자는 추격보다 지지 접근이나 실적 근거의 "
            "추가 확인을 우선합니다."
        )
    else:
        unavailable_reason = (
            "손익비 구성에 필요한 적격 지지가 없어"
            if resistance and not support
            else "가까운 목표로 쓸 적격 저항이 없어"
            if support and not resistance
            else "지지와 저항이 함께 확인되지 않아"
        )
        parts.append(
            f"{unavailable_reason} 현재가 기준 손익비는 보류하며 "
            f"{_profile_price_focus(profile)}을 먼저 봅니다."
        )
        observer = (
            f"신규 관찰자는 {_profile_entry_condition(profile)} 전까지 확인 가격만으로 "
            "진입 근거를 만들지 않습니다."
        )
    holder = (
        f"보유자는 신규 진입 조건과 분리해 {_profile_holder_condition(profile)}을 "
        "우선 점검합니다."
    )
    return " ".join(parts), observer, holder


def _supply_text(
    profile: str,
    stock: dict[str, object],
    numeric: object,
) -> str:
    positioning_id = next(
        (
            str(item.get("fact_id") or "")
            for item in stock.get("fact_catalog", [])
            if isinstance(item, dict) and item.get("fact_type") == "positioning"
        ),
        "",
    )
    paths = (
        ("foreign_net_buy_qty", "institution_net_buy_qty"),
        ("foreign_net_buy_qty_5", "institution_net_buy_qty_5"),
        ("foreign_net_buy_qty_20", "institution_net_buy_qty_20"),
    )
    lines: list[str] = []
    for foreign_path, institution_path in paths:
        foreign = numeric(
            "supply_analysis.text", positioning_id, f"fields.{foreign_path}"
        )
        institution = numeric(
            "supply_analysis.text", positioning_id, f"fields.{institution_path}"
        )
        if foreign and institution:
            lines.append(f"{foreign}, {institution}.")
    if not lines:
        return "검증된 투자주체별 수급 수치가 없어 방향을 추정하지 않습니다."
    relation = (
        _profile_supply_divergence(profile)
        if _supply_signs_diverge(stock, positioning_id)
        else _profile_supply_alignment(profile)
    )
    return "\n".join(lines) + f"\n{relation}"


def _valuation_text(
    profile: str,
    recovery: dict[str, object],
    stock: dict[str, object],
    numeric: object,
) -> tuple[str, dict[str, object], dict[str, object], str]:
    denied_earnings = any(
        _mapping(_mapping(recovery.get("fields")).get(field)).get("status") == "denied"
        for field in ("revenue", "operating_income", "net_income")
    )
    values: dict[str, str] = {}
    if not denied_earnings:
        pe = numeric(
            "valuation_analysis.text", "valuation:current", "fields.trailing_pe"
        )
        if pe:
            values["pe"] = pe
    pbr = numeric(
        "valuation_analysis.text", "valuation:current", "fields.price_to_book"
    )
    if pbr:
        values["pbr"] = pbr
    historical = historical_valuation_selection(
        stock,
        denied_earnings=denied_earnings,
    )
    if not values:
        context = build_valuation_context_selection(
            stock,
            historical,
            current_used=False,
            history_used=False,
        )
        context_span = (
            "현재 회사 전체 배수가 확인되지 않아 가치평가 해석을 제한합니다."
        )
        return context_span, historical, context.as_dict(), context_span
    statements = []
    if "pe" in values:
        statements.append(
            f"{_company_valuation_prefix(profile, 'pe')} {values['pe']}입니다."
        )
    if "pbr" in values:
        statements.append(
            f"{_company_valuation_prefix(profile, 'pbr')} {values['pbr']}입니다."
        )
    relation = _profile_valuation_relation(profile, values)
    if relation:
        statements.append(relation)
    selected = historical.get("selected")
    history_used = False
    if isinstance(selected, dict):
        metric = str(selected.get("metric") or "")
        percentile = numeric(
            "valuation_analysis.text",
            "valuation:current",
            str(selected.get("field_path") or ""),
        )
        if percentile:
            history_used = True
            label = "PER" if metric == "pe" else "PBR"
            direction = (
                "대부분보다 높은 구간"
                if float(selected.get("percentile") or 0.0) >= 50.0
                else "대부분보다 낮은 구간"
            )
            statements.append(
                f"회사 전체 {label}의 자체 역사 위치는 {percentile}입니다. 이는 현재 "
                f"{label}이 비교 가능한 과거 관측치 {direction}이라는 뜻입니다."
            )
    context = build_valuation_context_selection(
        stock,
        historical,
        current_used=True,
        history_used=history_used,
    )
    context_span = _valuation_context_wording(profile, context.as_dict())
    return (
        f"{' '.join(statements)} {_profile_valuation_context(profile)} {context_span}",
        historical,
        context.as_dict(),
        context_span,
    )


def _valuation_interpretation_refs(
    profile: str,
    references: list[dict[str, object]],
    selected_historical: object,
) -> list[dict[str, object]]:
    output: list[dict[str, object]] = []
    for item in references:
        if item.get("text_ref") != "valuation_analysis.text":
            continue
        field_path = str(item.get("field_path") or "")
        if field_path == "fields.trailing_pe":
            metric = "pe"
            fact_id = "valuation:trailing_earnings"
            exact_span = (
                f"{_company_valuation_prefix(profile, 'pe')} "
                f"{{{{numeric:{item['ref_id']}}}}}입니다."
            )
        elif field_path == "fields.price_to_book":
            metric = "pbr"
            fact_id = "valuation:book"
            exact_span = (
                f"{_company_valuation_prefix(profile, 'pbr')} "
                f"{{{{numeric:{item['ref_id']}}}}}입니다."
            )
        elif field_path in {
            "fields.historical_pe_statistics.current_percentile",
            "fields.historical_pb_statistics.current_percentile",
        } and isinstance(selected_historical, dict):
            metric = str(selected_historical.get("metric") or "")
            label = "PER" if metric == "pe" else "PBR"
            direction = (
                "대부분보다 높은 구간"
                if float(selected_historical.get("percentile") or 0.0) >= 50.0
                else "대부분보다 낮은 구간"
            )
            output.append(
                {
                    "ref_id": f"valuation_historical_{metric}",
                    "interpretation_type": "historical",
                    "metric": metric,
                    "fact_id": str(selected_historical.get("fact_id") or ""),
                    "text_ref": "valuation_analysis.text",
                    "exact_text_span": (
                        f"회사 전체 {label}의 자체 역사 위치는 "
                        f"{{{{numeric:{item['ref_id']}}}}}입니다. 이는 현재 {label}이 "
                        f"비교 가능한 과거 관측치 {direction}이라는 뜻입니다."
                    ),
                    "comparison_numeric_ref_ids": [str(item["ref_id"])],
                    "basis_status": "verified",
                    "source_type": "canonical_history",
                    "direction": "high" if direction.endswith("높은 구간") else "low",
                    "economic_scope": "listed_security",
                }
            )
            continue
        else:
            continue
        output.append(
            {
                "ref_id": f"valuation_{metric}",
                "interpretation_type": "absolute",
                "metric": metric,
                "fact_id": fact_id,
                "text_ref": "valuation_analysis.text",
                "exact_text_span": exact_span,
                "comparison_numeric_ref_ids": [str(item["ref_id"])],
                "basis_status": "verified",
                "source_type": "canonical",
                "direction": "neutral",
                "economic_scope": "listed_security",
            }
        )
    return output


def _add_period_basis(
    earnings: dict[str, object],
    quality: dict[str, object],
    period_key: str,
    field_name: str,
    lineage: dict[str, object],
) -> None:
    period_labels = _mapping(earnings.get("field_period_labels"))
    period_labels[period_key] = _period_label(lineage)
    earnings["field_period_labels"] = period_labels
    basis = _mapping(earnings.get("field_statement_basis"))
    basis[period_key] = {
        "state": lineage.get("statement_basis_state"),
        "basis": lineage.get("statement_basis"),
    }
    earnings["field_statement_basis"] = basis
    path = (
        f"fields.{field_name}.value"
        if field_name in {"revenue", "operating_income", "net_income"}
        else f"fields.{field_name}"
    )
    quality[path] = {
        "state": "verified_usable",
        "prose_eligible": True,
        "source_filing_identifier": lineage.get("source_filing"),
        "source_row_identity": lineage.get("source_row_identity"),
        "amount_period_type": lineage.get("amount_period_type"),
        "amount_period_start": lineage.get("amount_period_start"),
        "amount_period_end": lineage.get("amount_period_end"),
        "statement_basis_state": lineage.get("statement_basis_state"),
    }


def _period_label(lineage: dict[str, object]) -> str:
    end = str(lineage.get("amount_period_end") or "")
    year = end[:4] if len(end) >= 4 else "기간 미상"
    month = int(end[5:7]) if len(end) >= 7 else 0
    scope = str(lineage.get("amount_period_type") or "")
    if scope == "single_quarter" and month:
        period = f"{year}년 {(month - 1) // 3 + 1}분기"
    elif scope == "year_to_date_cumulative" and month == 6:
        period = f"{year}년 상반기 누적"
    elif scope == "point_in_time" and month:
        period = f"{year}년 {month}월 말"
    elif scope == "annual":
        period = f"{year}년 연간"
    else:
        period = "검증된 기간"
    basis = (
        "연결 기준"
        if lineage.get("statement_basis_state") == "verified_consolidated"
        else "별도 기준"
        if lineage.get("statement_basis_state") == "verified_separate"
        else ""
    )
    return " ".join(item for item in (period, basis) if item)


def _reasoning_profile(stock: dict[str, object]) -> str:
    framework = build_industry_reasoning_plan(stock).primary_framework
    return {
        "memory": "semiconductor",
        "semiconductor": "semiconductor",
        "semiconductor_foundry": "semiconductor",
        "insurance": "insurance",
        "transport_logistics": "shipping",
        "steel_materials": "cyclical_materials",
    }.get(framework, "general")


def _profile_opening(profile: str) -> str:
    return {
        "semiconductor": "메모리·HBM 실행 논리 자체는 바뀌지 않았습니다.",
        "insurance": "재보험 언더라이팅과 자본관리 논리는 유지됩니다.",
        "shipping": "완성차 운송과 물류 성장 논리는 유지됩니다.",
        "cyclical_materials": "철강·소재 회복 논리를 바꿀 새 사건은 없습니다.",
        "general": "현재 사업 논리를 바꿀 새 사건은 없습니다.",
    }[profile]


def _profile_meaning(profile: str) -> str:
    return {
        "semiconductor": "사업별 기여도와 HBM 실행, 재고·현금흐름이 없어 전사 실적만으로 원인을 단정하지 않습니다.",
        "insurance": "합산비율·대형재해 손실·자본적정성이 없어 이익 증가의 반복 가능성은 아직 확인되지 않았습니다.",
        "shipping": "운임·연료비·계약 믹스와 현금전환이 없어 외형 변화의 질은 아직 확인되지 않았습니다.",
        "cyclical_materials": "철강 스프레드·소재 손익과 현금전환이 없어 사이클상 위치는 아직 확인되지 않았습니다.",
        "general": "부문별 기여도와 현금전환이 없어 전사 숫자만으로 원인을 단정하지 않습니다.",
    }[profile]


def _profile_detail_caution(profile: str) -> str:
    return {
        "semiconductor": "연결 기준 전사 숫자이며 반도체·모바일·디스플레이별 기여도는 확인되지 않았습니다.",
        "insurance": "제조업식 이익률 대신 합산비율·손해율·투자손익과 자본적정성 확인이 필요합니다.",
        "shipping": "운임·연료비·계약 믹스와 영업현금흐름이 없어 수익성 변화의 원인은 분해되지 않습니다.",
        "cyclical_materials": "철강 스프레드와 소재 부문 손익, 운전자본·설비투자가 없어 회복의 질은 열려 있습니다.",
        "general": "부문별 실적과 영업현금흐름이 없어 증가 원인의 지속성은 열려 있습니다.",
    }[profile]


def _profile_detail_relation(profile: str) -> str:
    return {
        "semiconductor": "전사 연결 실적의 규모와 수익성을 확인할 수 있습니다",
        "insurance": "재보험사의 현재 이익 규모를 확인할 수 있습니다",
        "shipping": "물류 사업의 외형과 현재 수익성을 함께 확인할 수 있습니다",
        "cyclical_materials": "철강·소재 혼합 사업의 외형과 현재 수익성을 확인할 수 있습니다",
        "general": "현재 연결 실적의 규모와 수익성을 확인할 수 있습니다",
    }[profile]


def _profile_entry_condition(profile: str) -> str:
    return {
        "semiconductor": "동적 지지와 HBM 실행 근거가 함께 형성되기",
        "insurance": "동적 지지와 보험 수익성 지표가 함께 확인되기",
        "shipping": "동적 지지와 물류 수익성 근거가 함께 확인되기",
        "cyclical_materials": "동적 지지와 사이클 회복 근거가 함께 확인되기",
        "general": "동적 지지와 실적 지속성 근거가 함께 확인되기",
    }[profile]


def _profile_price_focus(profile: str) -> str:
    return {
        "semiconductor": "동적 지지 형성과 HBM 실행",
        "insurance": "월봉 지지와 보험 수익성",
        "shipping": "동적 지지와 물류 마진",
        "cyclical_materials": "동적 지지와 철강·소재 현금전환",
        "general": "동적 지지와 실적 지속성",
    }[profile]


def _profile_holder_condition(profile: str) -> str:
    return {
        "semiconductor": "HBM 실행과 재고·현금흐름",
        "insurance": "지지 유지와 합산비율·자본적정성",
        "shipping": "지지 유지와 운임·마진·현금전환",
        "cyclical_materials": "지지 유지와 철강·소재 현금전환",
        "general": "지지 유지와 다음 실적의 수익성",
    }[profile]


def _profile_supply_divergence(profile: str) -> str:
    return {
        "semiconductor": "세 시간축의 매매 방향이 엇갈려 메모리 실행 근거와 분리해 봅니다.",
        "insurance": "투자주체별 시간축이 엇갈려 재보험 수익성의 확인 근거로 사용하지 않습니다.",
        "shipping": "단기와 중기 매매 방향이 달라 물류 실적의 질을 확인하는 근거로 승격하지 않습니다.",
        "cyclical_materials": "기간별 매매 방향이 엇갈려 철강·소재 사이클 회복 근거와 분리합니다.",
        "general": "기간별 투자주체 흐름이 엇갈려 사업 논리와 분리해 해석합니다.",
    }[profile]


def _profile_supply_alignment(profile: str) -> str:
    return {
        "semiconductor": "세 시간축의 매매 수치는 HBM 실행이 아니라 가격 참여의 맥락으로만 봅니다.",
        "insurance": "세 시간축의 매매 수치는 언더라이팅 개선을 증명하지 않으므로 별도 맥락으로 봅니다.",
        "shipping": "세 시간축의 매매 수치는 운임·마진 변화와 분리해 봅니다.",
        "cyclical_materials": "세 시간축의 매매 수치는 철강·소재 이익 회복과 분리해 봅니다.",
        "general": "세 시간축의 매매 수치는 사업 논리와 분리해 봅니다.",
    }[profile]


def _profile_valuation_context(profile: str) -> str:
    return {
        "semiconductor": "이 배수는 HBM 실행과 재고·현금흐름의 확인과 함께 봐야 합니다.",
        "insurance": "보험업 배수는 합산비율·자기자본이익률·자본적정성과 함께 봐야 합니다.",
        "shipping": "운송업 배수는 운임·물량보다 마진과 현금전환의 지속성과 함께 봐야 합니다.",
        "cyclical_materials": "철강·소재 배수는 정상화 이익과 현금전환의 지속성과 함께 봐야 합니다.",
        "general": "현재 배수는 수익성과 현금전환의 지속성과 함께 봐야 합니다.",
    }[profile]


def _profile_valuation_relation(profile: str, values: dict[str, str]) -> str | None:
    if profile == "cyclical_materials" and {"pe", "pbr"}.issubset(values):
        return (
            "이익배수와 장부가 배수가 서로 다른 신호를 주므로 PBR 하나만으로 "
            "가치평가 결론을 내리지 않습니다."
        )
    if profile == "insurance" and "pbr" in values:
        return (
            "장부가 배수는 자기자본이익률과 자본적정성이 없어 현재 숫자만으로 "
            "가치평가 결론을 내리지 않습니다."
        )
    return None


def _valuation_context_wording(
    profile: str,
    context: dict[str, object],
) -> str:
    context_class = str(context.get("valuation_context_class") or "")
    historical_status = str(context.get("historical_status") or "unavailable")
    peer_status = str(context.get("peer_status") or "unavailable")
    if context_class == "CURRENT_PLUS_HISTORY_PLUS_PEER":
        return (
            "이번 평가는 회사 전체 현재 배수와 자체 역사 위치, 같은 시점의 "
            "동종기업 비교를 함께 봅니다."
        )
    if context_class == "CURRENT_PLUS_HISTORY":
        if peer_status == "available":
            return (
                "이번 평가는 회사 전체 현재 배수와 자체 역사 위치를 중심으로 "
                "봅니다."
            )
        return {
            "semiconductor": (
                "같은 시점의 동종기업 비교값은 없어 회사 전체 현재 배수와 "
                "자체 역사 위치를 함께 봅니다."
            ),
            "insurance": (
                "동종기업의 같은 시점 비교값은 없어 회사 전체 현재 배수와 "
                "자체 역사 위치를 판단 근거로 사용합니다."
            ),
            "shipping": (
                "동종기업의 같은 시점 비교값은 없어 회사 전체 현재 배수와 "
                "자체 역사 위치를 중심으로 판단합니다."
            ),
            "cyclical_materials": (
                "같은 시점의 동종기업 비교값 없이 회사 전체 현재 배수와 "
                "자체 역사 위치를 함께 봅니다."
            ),
            "general": (
                "같은 시점의 동종기업 비교값은 없어 이번 평가는 회사 전체 현재 "
                "배수와 자체 역사 위치를 중심으로 봅니다."
            ),
        }[profile]
    if context_class == "CURRENT_PLUS_PEER":
        if historical_status == "unsafe":
            return (
                "자체 역사 비교는 기준 일치 문제로 사용하지 않고 회사 전체 현재 "
                "배수와 같은 시점의 동종기업 비교를 중심으로 봅니다."
            )
        return (
            "이번 평가는 회사 전체 현재 배수와 같은 시점의 동종기업 비교를 "
            "중심으로 봅니다."
        )
    if context_class == "CURRENT_ONLY":
        if historical_status in {"unsafe", "unavailable"}:
            return (
                "동종기업 비교값과 안전한 자체 역사 비교값이 없어 이번 평가는 "
                "회사 전체 현재 배수에 한정합니다."
            )
        return (
            "같은 시점의 동종기업 비교값은 없으며 이번 판단에는 회사 전체 현재 "
            "배수를 중심으로 봅니다."
        )
    return "현재 회사 전체 배수가 확인되지 않아 가치평가 해석을 제한합니다."


def _company_valuation_prefix(profile: str, metric: str) -> str:
    if metric == "pe":
        return {
            "semiconductor": "상장주식 기준 회사 전체 이익 배수는",
            "insurance": "재보험사 전체의 이익 기준 값은",
            "shipping": "상장회사 전체의 이익 기준 값은",
            "cyclical_materials": "연결 회사 전체의 이익 기준 값은",
            "general": "회사 전체의 이익 기준 값은",
        }[profile]
    return {
        "semiconductor": "상장주식 기준 회사 전체 장부가 배수는",
        "insurance": "재보험사 전체의 장부가 기준 값은",
        "shipping": "상장회사 전체의 장부가 기준 값은",
        "cyclical_materials": "연결 회사 전체의 장부가 기준 값은",
        "general": "회사 전체의 장부가 기준 값은",
    }[profile]


def _profile_unknown(profile: str, financial_available: bool) -> str:
    if not financial_available:
        if profile == "semiconductor":
            return (
                "HBM 고객별 출하·수율과 재고·설비투자 이후 현금흐름이 "
                "확인되지 않았습니다."
            )
        return "검증된 영업현금흐름과 업종 핵심 실행 지표가 확인되지 않았습니다."
    return {
        "semiconductor": "사업부별 이익 기여도와 영업현금흐름·설비투자가 없어 전사 실적 개선의 현금 회수 여부는 확인되지 않았습니다.",
        "insurance": "합산비율·대형재해 손실·투자수익률과 자본적정성이 없어 영업이익 증가의 질은 확인되지 않았습니다.",
        "shipping": "운임·연료비 전가·계약 믹스와 영업현금흐름이 없어 매출과 이익 방향이 엇갈린 원인은 확인되지 않았습니다.",
        "cyclical_materials": "철강 스프레드·소재 부문 손익과 영업현금흐름·설비투자가 없어 현재 이익의 사이클상 위치는 확인되지 않았습니다.",
        "general": "부문별 이익 기여도와 영업현금흐름이 없어 전사 실적 변화의 지속성은 확인되지 않았습니다.",
    }[profile]


def _profile_next_check(
    profile: str,
    financial_available: bool,
    recovery_fact_id: str,
    numeric: object,
) -> str:
    if not financial_available:
        if profile == "semiconductor":
            return "HBM 출하·수율과 재고·설비투자 이후 현금흐름이 검증되기 전에는 장부가치 배수만으로 투자 논리를 강화하지 않습니다."
        return "업종 핵심 실행 지표와 영업현금흐름이 검증되기 전에는 현재 배수만으로 투자 논리를 강화하지 않습니다."
    if profile == "shipping":
        current_margin = numeric(
            "next_checks[0]",
            recovery_fact_id,
            "fields.operating_margin_pct",
        )
        if current_margin:
            return (
                f"다음 분기 수익성이 {current_margin}보다 더 낮아지면 외형 성장의 "
                "이익 전환이 약해진 것으로 봅니다."
            )
    return {
        "semiconductor": "다음 공시에서 사업부별 이익과 영업현금흐름이 함께 개선돼야 전사 실적 증가를 지속 가능한 변화로 봅니다.",
        "insurance": "다음 갱신의 합산비율과 대형재해 손실, 자본적정성이 함께 개선돼야 이익 증가의 반복 가능성을 높게 봅니다.",
        "shipping": "다음 분기 운임·연료비 전가와 영업이익률이 함께 개선돼야 외형 성장을 질 높은 성장으로 봅니다.",
        "cyclical_materials": "철강·소재 부문 마진과 영업현금흐름이 함께 개선돼야 현재 이익 증가를 사이클 회복 이상의 변화로 봅니다.",
        "general": "다음 분기 이익률과 영업현금흐름이 함께 개선돼야 현재 실적 변화를 지속 가능한 변화로 봅니다.",
    }[profile]


def _unknown_required_family(
    profile: str,
    missing_drivers: tuple[str, ...],
) -> str | None:
    preferences = {
        "semiconductor": ("inventory", "capex", "free_cash_flow"),
        "insurance": ("combined_ratio", "capital_adequacy", "roe"),
        "shipping": ("freight_rate", "contract_mix", "operating_cash_flow"),
        "cyclical_materials": ("spread", "inventory", "operating_cash_flow"),
        "general": ("operating_cash_flow", "balance_sheet"),
    }[profile]
    return next((item for item in preferences if item in missing_drivers), None)


def _valuation_boundary_span(profile: str, text: str) -> str | None:
    candidates = {
        "semiconductor": (
            "이 배수는 HBM 실행과 재고·현금흐름의 확인과 함께 봐야 합니다."
        ),
        "insurance": (
            "보험업 배수는 합산비율·자기자본이익률·자본적정성과 함께 봐야 합니다."
        ),
        "shipping": (
            "운송업 배수는 운임·물량보다 마진과 현금전환의 지속성과 함께 봐야 합니다."
        ),
        "cyclical_materials": (
            "철강·소재 배수는 정상화 이익과 현금전환의 지속성과 함께 봐야 합니다."
        ),
        "general": "현재 배수는 수익성과 현금전환의 지속성과 함께 봐야 합니다.",
    }
    candidate = candidates[profile]
    return candidate if candidate in text else None


def _valuation_relation_span(profile: str, text: str) -> str | None:
    candidate = _profile_valuation_relation(profile, {"pe": "", "pbr": ""})
    return candidate if candidate and candidate in text else None


def _financial_quality_facts(stock: dict[str, object]) -> set[str]:
    return {
        str(item.get("fact_id") or "")
        for item in stock.get("fact_catalog", [])
        if isinstance(item, dict) and item.get("fact_type") == "financial_quality"
    }


def _denied_semantic_families(
    stock: dict[str, object],
    recovery: dict[str, object],
) -> list[str]:
    families: set[str] = set()
    fields = _mapping(recovery.get("fields"))
    if _mapping(fields.get("revenue")).get("status") == "denied":
        families.add("revenue")
    if _mapping(fields.get("operating_income")).get("status") == "denied":
        families.update({"operating_income", "margin"})
    if _mapping(fields.get("net_income")).get("status") == "denied":
        families.update({"earnings", "pe"})
    denied_quality = any(
        str(_mapping(item.get("fields")).get("state") or "") == "denied"
        for item in stock.get("fact_catalog", [])
        if isinstance(item, dict) and item.get("fact_type") == "financial_quality"
    )
    if denied_quality:
        families.update(
            {"earnings", "revenue", "operating_income", "margin", "pe"}
        )
    return sorted(families)


def _supply_signs_diverge(stock: dict[str, object], fact_id: str) -> bool:
    registry = {
        str(item.get("field_path") or ""): _number(item.get("value"))
        for item in stock.get("numeric_registry", [])
        if isinstance(item, dict) and str(item.get("fact_id") or "") == fact_id
    }
    values = [
        registry.get(f"fields.{actor}{suffix}")
        for suffix in ("", "_5", "_20")
        for actor in ("foreign_net_buy_qty", "institution_net_buy_qty")
    ]
    signs = {1 if value > 0 else -1 if value < 0 else 0 for value in values if value is not None}
    return len(signs - {0}) > 1


def _eligible_fact_counts(stock: dict[str, object], recovery_fact_id: str) -> dict[str, int]:
    categories = {"financial": 0, "price": 0, "supply": 0, "valuation": 0}
    price_requirements = {
        (str(requirement.get("fact_id") or ""), str(path))
        for requirement in _mapping(stock.get("state_grounding_requirements")).get(
            "price", []
        )
        if isinstance(requirement, dict)
        for path in requirement.get("field_paths", [])
    }
    valuation_semantics = {
        "trailing_pe",
        "price_to_book",
        "historical_pe_percentile",
        "historical_pb_percentile",
    }
    for item in stock.get("numeric_registry", []):
        if not isinstance(item, dict) or item.get("prose_allowed") is not True:
            continue
        fact_id = str(item.get("fact_id") or "")
        semantic = str(item.get("semantic_type") or "")
        if fact_id == recovery_fact_id:
            categories["financial"] += 1
        elif (fact_id, str(item.get("field_path") or "")) in price_requirements:
            categories["price"] += 1
        elif semantic.startswith(("foreign_net_buy", "institution_net_buy")):
            categories["supply"] += 1
        elif fact_id.startswith("valuation:") and semantic in valuation_semantics:
            categories["valuation"] += 1
    return categories


def _used_fact_counts(
    references: list[dict[str, object]],
    selected_sections: tuple[str, ...],
) -> dict[str, int]:
    categories: dict[str, set[tuple[str, str]]] = {
        "financial": set(),
        "price": set(),
        "supply": set(),
        "valuation": set(),
    }
    for item in references:
        fact_id = str(item.get("fact_id") or "")
        field_path = str(item.get("field_path") or "")
        text_ref = str(item.get("text_ref") or "")
        section = (
            "core"
            if text_ref.startswith("core_judgment")
            else "business"
            if text_ref.startswith("business_earnings")
            else "price"
            if text_ref.startswith("price_positioning")
            else "supply"
            if text_ref.startswith("supply_analysis")
            else "valuation"
            if text_ref.startswith("valuation_analysis")
            else ""
        )
        if section not in selected_sections:
            continue
        key = (fact_id, field_path)
        if fact_id.startswith(RECOVERY_FACT_PREFIX):
            categories["financial"].add(key)
        elif section == "price":
            categories["price"].add(key)
        elif section == "supply":
            categories["supply"].add(key)
        elif section == "valuation":
            categories["valuation"].add(key)
    return {name: len(values) for name, values in categories.items()}


def _sentence_count(value: str) -> int:
    return sum(bool(item.strip()) for item in value.replace("!", ".").split("."))


def _number(value: object) -> float | None:
    if isinstance(value, (int, float)) and not isinstance(value, bool):
        return float(value)
    return None


def _mapping(value: object) -> dict[str, object]:
    return value if isinstance(value, dict) else {}
