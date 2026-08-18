from __future__ import annotations

import math
import re
from collections import defaultdict
from datetime import date
from typing import Iterable, Mapping

from app.services.peer_sector_valuation_service import (
    HIGH_QUALITY_PEER_SAMPLE,
    MINIMUM_PEER_SAMPLE,
    calculate_peer_statistics,
    evaluate_metric_value,
    metric_allowed,
    metric_spec,
)


FREE_PEER_PROVIDER_POLICY = "FREE_ONLY"
FREE_SOURCE_PEER_CONTRACT = "free-source-current-peer-v1"
FREE_SOURCE_PEER_GROUP_VERSION = "verified-profile-peers-v2"
MAX_DENOMINATOR_AGE_DAYS = 180

_PROFILE_LEVELS = ("taxonomy", "sub_industry", "industry", "sector")
_COMMON_SECURITY_TYPES = {"common_stock", "common stock", "ordinary_share"}
_SAFE_PER_SHARE_BASIS = {
    "current_security",
    "provider_security_per_share",
    "directly_comparable",
}
_ALLOWED_FREE_SOURCES = {
    "existing_canonical",
    "finnhub_free_basic_financials",
    "opendart_existing_financials",
}
_NOT_MEANINGFUL_FRAMEWORKS = {
    "biotech",
    "hpc_crypto_infrastructure",
    "holding_company",
    "saas",
}
_COMPARISON_SCOPE_LABELS = {
    "automotive": "자동차",
    "insurance": "보험",
    "memory": "메모리",
    "semiconductor": "반도체",
    "steel_materials": "철강·소재",
    "transport_logistics": "운송·물류",
}


def _normalized(value: object) -> str | None:
    text = re.sub(r"[^a-z0-9]+", "_", str(value or "").strip().lower()).strip("_")
    return text or None


def _number(value: object) -> float | None:
    if isinstance(value, (int, float)) and not isinstance(value, bool):
        number = float(value)
        return number if math.isfinite(number) else None
    return None


def _date(value: object) -> date | None:
    try:
        return date.fromisoformat(str(value or "")[:10])
    except ValueError:
        return None


def _identity_exclusion(candidate: Mapping[str, object]) -> str | None:
    if candidate.get("identity_conflict") is True:
        return "security_identity_conflict"
    if candidate.get("issuer_dedup_reliable") is not True:
        return "issuer_identity_unknown"
    if candidate.get("is_depositary_security") is True:
        return "adr_basis_conflict"
    security_type = _normalized(candidate.get("security_type"))
    if security_type not in {_normalized(value) for value in _COMMON_SECURITY_TYPES}:
        return "non_common_security"
    return None


def select_free_peer_candidates(
    subject: Mapping[str, object],
    candidates: Iterable[Mapping[str, object]],
) -> dict[str, object]:
    """Separate economic candidates from security-eligible issuer-deduped peers."""
    subject_ticker = str(subject.get("ticker") or "")
    subject_market = str(subject.get("market") or "")
    rows = [dict(item) for item in candidates]
    profile_matches: dict[str, list[dict[str, object]]] = {}
    for level in _PROFILE_LEVELS:
        expected = _normalized(subject.get(level))
        if expected is None:
            continue
        profile_matches[level] = [
            item
            for item in rows
            if str(item.get("ticker") or "") != subject_ticker
            and str(item.get("market") or "") == subject_market
            and item.get("profile_quality") == "verified"
            and _normalized(item.get(level)) == expected
        ]

    selected_level = next(
        (
            level
            for level in _PROFILE_LEVELS
            if len(profile_matches.get(level, [])) >= MINIMUM_PEER_SAMPLE
        ),
        next(
            (level for level in _PROFILE_LEVELS if profile_matches.get(level)),
            None,
        ),
    )
    selected = profile_matches.get(selected_level or "", [])
    excluded: list[dict[str, object]] = []
    by_issuer: dict[str, list[dict[str, object]]] = defaultdict(list)
    subject_issuer = str(subject.get("issuer_id") or "")
    for item in selected:
        reason = _identity_exclusion(item)
        issuer_id = str(item.get("issuer_id") or "")
        if reason is None and subject_issuer and issuer_id == subject_issuer:
            reason = "subject_issuer"
        if reason is not None:
            excluded.append({"ticker": item.get("ticker"), "reason": reason})
            continue
        by_issuer[issuer_id].append(item)

    eligible: list[dict[str, object]] = []
    for issuer_rows in by_issuer.values():
        ordered = sorted(issuer_rows, key=lambda item: str(item.get("ticker") or ""))
        eligible.append(ordered[0])
        for duplicate in ordered[1:]:
            excluded.append(
                {"ticker": duplicate.get("ticker"), "reason": "same_issuer_duplicate"}
            )

    selected_value = subject.get(selected_level) if selected_level else None
    return {
        "group_basis": selected_level,
        "group_value": selected_value,
        "candidate_count": len(selected),
        "same_market_count": sum(
            str(item.get("market") or "") == subject_market for item in rows
        ),
        "issuer_deduplicated_count": len(eligible),
        "candidates": sorted(selected, key=lambda item: str(item.get("ticker") or "")),
        "eligible_candidates": sorted(
            eligible, key=lambda item: str(item.get("ticker") or "")
        ),
        "excluded": sorted(
            excluded, key=lambda item: (str(item.get("ticker") or ""), str(item["reason"]))
        ),
    }


def derive_free_current_metric(
    fact: Mapping[str, object],
    metric: str,
    *,
    target_session: str,
) -> tuple[float | None, str | None, dict[str, object]]:
    """Derive PER/PBR only from a current price and a positive per-security denominator."""
    if not fact:
        return None, "free_current_valuation_unavailable", {}
    source = str(fact.get("source") or "")
    if source not in _ALLOWED_FREE_SOURCES or fact.get("source_entitlement") != "free_existing":
        return None, "source_not_allowed", {}
    if fact.get("identity_safe") is not True:
        return None, "security_basis_unknown", {}
    if fact.get("provider_conflict") is True:
        return None, "provider_conflict", {}
    if fact.get("financial_quality_denied") is True:
        return None, "financial_quality_denied", {}
    if str(fact.get("price_as_of") or "")[:10] != target_session:
        return None, "session_mismatch", {}
    price = _number(fact.get("price"))
    if price is None or price <= 0:
        return None, "price_unavailable", {}

    if metric == "trailing_pe":
        denominator_field = "ttm_eps"
        period_field = "ttm_eps_period_end"
        basis_field = "eps_security_basis"
        currency_field = "eps_currency"
        negative_reason = "negative_eps"
    elif metric == "price_to_book":
        denominator_field = "bvps"
        period_field = "bvps_period_end"
        basis_field = "bvps_security_basis"
        currency_field = "bvps_currency"
        negative_reason = "negative_equity"
    else:
        raise ValueError(f"unsupported free peer metric: {metric}")

    denominator = _number(fact.get(denominator_field))
    if denominator is None:
        return None, f"missing_{denominator_field}", {}
    if denominator <= 0:
        return None, negative_reason, {}
    if _normalized(fact.get(basis_field)) not in {
        _normalized(value) for value in _SAFE_PER_SHARE_BASIS
    }:
        return None, "security_basis_unknown", {}
    price_currency = str(fact.get("price_currency") or "").upper()
    denominator_currency = str(fact.get(currency_field) or "").upper()
    if not price_currency or price_currency != denominator_currency:
        return None, "currency_mismatch", {}
    period_end = _date(fact.get(period_field))
    session_date = _date(target_session)
    if period_end is None or session_date is None:
        return None, "denominator_period_unknown", {}
    age_days = (session_date - period_end).days
    if age_days < 0:
        return None, "future_denominator_period", {}
    if age_days > MAX_DENOMINATOR_AGE_DAYS:
        return None, "stale_denominator", {}

    value = round(price / denominator, 4)
    return (
        value,
        None,
        {
            "source": source,
            "price": price,
            "price_as_of": target_session,
            "price_currency": price_currency,
            "denominator_field": denominator_field,
            "denominator": denominator,
            "denominator_period_end": period_end.isoformat(),
            "denominator_currency": denominator_currency,
            "security_basis": fact.get(basis_field),
            "calculation": f"price/{denominator_field}",
        },
    )


def _sample_quality(sample_count: int, group_basis: object) -> str:
    if sample_count < MINIMUM_PEER_SAMPLE or group_basis == "sector":
        return "LOW"
    return "HIGH" if sample_count >= HIGH_QUALITY_PEER_SAMPLE else "MEDIUM"


def _display_metric(framework: str, metrics: Mapping[str, object]) -> str | None:
    preference = (
        ("price_to_book", "trailing_pe")
        if framework in {"insurance", "memory", "steel_materials"}
        else ("trailing_pe", "price_to_book")
    )
    return next(
        (
            metric
            for metric in preference
            if isinstance(metrics.get(metric), dict)
            and metrics[metric].get("available") is True
        ),
        None,
    )


def _comparison_scope_label(state: Mapping[str, object]) -> str:
    selection = state.get("selection")
    group_value = (
        _normalized(selection.get("group_value"))
        if isinstance(selection, Mapping)
        else None
    )
    framework = _normalized(state.get("framework"))
    return _COMPARISON_SCOPE_LABELS.get(
        group_value or "",
        _COMPARISON_SCOPE_LABELS.get(framework or "", "산업"),
    )


def build_free_source_peer_state(
    subject: Mapping[str, object],
    candidates: Iterable[Mapping[str, object]],
    subject_snapshot: Mapping[str, object],
    candidate_facts: Mapping[str, Mapping[str, object]],
    *,
    target_session: str,
) -> dict[str, object]:
    selection = select_free_peer_candidates(subject, candidates)
    framework = str(subject.get("framework") or "general")
    if framework in _NOT_MEANINGFUL_FRAMEWORKS:
        return {
            "available": False,
            "coverage_state": "NOT_MEANINGFUL",
            "reason": "industry_metric_not_meaningful",
            "provider_policy": FREE_PEER_PROVIDER_POLICY,
            "contract": FREE_SOURCE_PEER_CONTRACT,
            "peer_group_version": FREE_SOURCE_PEER_GROUP_VERSION,
            "framework": framework,
            "selection": selection,
            "metrics": {},
        }
    if subject.get("identity_safe") is not True:
        return {
            "available": False,
            "coverage_state": "SUPPRESSED",
            "reason": "subject_security_basis_unsafe",
            "provider_policy": FREE_PEER_PROVIDER_POLICY,
            "contract": FREE_SOURCE_PEER_CONTRACT,
            "peer_group_version": FREE_SOURCE_PEER_GROUP_VERSION,
            "framework": framework,
            "selection": selection,
            "metrics": {},
        }

    metrics: dict[str, object] = {}
    audit: dict[str, object] = {}
    for metric in ("trailing_pe", "price_to_book"):
        allowed, reason = metric_allowed(metric, framework)
        if not allowed:
            metrics[metric] = {"available": False, "reason": reason, "sample_count": 0}
            audit[metric] = {"included": [], "excluded": []}
            continue
        subject_value, subject_reason, subject_cautions = evaluate_metric_value(
            subject_snapshot,
            metric_spec(metric),
            expected_price_as_of=target_session,
        )
        included: list[dict[str, object]] = []
        excluded: list[dict[str, object]] = []
        values: list[float] = []
        for candidate in selection["eligible_candidates"]:
            ticker = str(candidate.get("ticker") or "")
            value, exclusion, lineage = derive_free_current_metric(
                candidate_facts.get(ticker, {}), metric, target_session=target_session
            )
            if value is None:
                excluded.append({"ticker": ticker, "reason": exclusion})
                continue
            values.append(value)
            included.append(
                {
                    "ticker": ticker,
                    "issuer_id": candidate.get("issuer_id"),
                    "security_id": candidate.get("security_id"),
                    "value": value,
                    "eligibility": "ELIGIBLE",
                    "lineage": lineage,
                }
            )
        quality = _sample_quality(len(values), selection.get("group_basis"))
        if subject_value is None:
            metrics[metric] = {
                "available": False,
                "reason": subject_reason,
                "sample_count": len(values),
                "quality": quality,
            }
        elif len(values) < MINIMUM_PEER_SAMPLE:
            metrics[metric] = {
                "available": False,
                "reason": "insufficient_comparable_metric_sample",
                "sample_count": len(values),
                "quality": quality,
            }
        else:
            statistics = calculate_peer_statistics(
                subject_value,
                values,
                quality=quality,
                subject_cautions=subject_cautions,
            )
            if quality == "LOW":
                metrics[metric] = {
                    "available": False,
                    "audit_available": True,
                    "reason": "broad_fallback_low_quality",
                    **statistics,
                }
            else:
                metrics[metric] = {"available": True, **statistics}
        audit[metric] = {"included": included, "excluded": excluded}

    available_metrics = [
        value
        for value in metrics.values()
        if isinstance(value, dict) and value.get("available") is True
    ]
    display_metric = _display_metric(framework, metrics)
    display_value = metrics.get(display_metric) if display_metric else None
    sample_quality = (
        str(display_value.get("quality"))
        if isinstance(display_value, dict)
        else "LOW"
    )
    coverage_state = sample_quality if available_metrics else (
        "LOW" if selection.get("candidate_count") else "SUPPRESSED"
    )
    peer_fields: dict[str, object] = {
        "contract": FREE_SOURCE_PEER_CONTRACT,
        "peer_scope": "free_source_current_cross_section",
        "peer_group_version": FREE_SOURCE_PEER_GROUP_VERSION,
        "group_basis": selection.get("group_basis"),
        "group_value": selection.get("group_value"),
        "sample_quality": sample_quality,
        "display_metric": display_metric,
        "framework": framework,
    }
    numeric_provenance: list[dict[str, object]] = []
    for metric, prefix, semantic_prefix in (
        ("trailing_pe", "pe", "peer_pe"),
        ("price_to_book", "pb", "peer_pb"),
    ):
        value = metrics.get(metric)
        if not isinstance(value, dict) or value.get("available") is not True:
            continue
        for source, target in (
            ("median", f"{prefix}_median"),
            ("mean", f"{prefix}_mean"),
            ("percentile_25", f"{prefix}_percentile_25"),
            ("percentile_75", f"{prefix}_percentile_75"),
            ("sample_count", f"{prefix}_sample_count"),
            ("company_relative_multiple", f"company_{prefix}_relative_multiple"),
            ("company_vs_median_pct", f"company_{prefix}_vs_median_pct"),
            (
                "company_cross_section_percentile",
                f"company_{prefix}_cross_section_percentile",
            ),
        ):
            if value.get(source) is not None:
                peer_fields[target] = value[source]
        semantic_by_source = {
            "company_value": metric,
            "median": f"{semantic_prefix}_multiple",
            "sample_count": "peer_sample_count",
            "company_vs_median_pct": f"{semantic_prefix}_relative_pct",
        }
        for source, semantic in semantic_by_source.items():
            numeric_provenance.append(
                {
                    "fact_id": (
                        "valuation:current"
                        if source == "company_value"
                        else "valuation:peer"
                    ),
                    "field_path": (
                        f"fields.{metric}"
                        if source == "company_value"
                        else f"fields.{prefix}_{source}"
                        if source in {"median", "sample_count"}
                        else f"fields.company_{prefix}_vs_median_pct"
                    ),
                    "raw": value[source],
                    "unit": (
                        "count"
                        if source == "sample_count"
                        else "pct"
                        if source == "company_vs_median_pct"
                        else "x"
                    ),
                    "semantic_type": semantic,
                    "text_ref": "valuation.peer_context",
                    "usage": "rendered_exact_value",
                }
            )
    return {
        "available": bool(available_metrics),
        "coverage_state": coverage_state,
        "provider_policy": FREE_PEER_PROVIDER_POLICY,
        "contract": FREE_SOURCE_PEER_CONTRACT,
        "peer_group_version": FREE_SOURCE_PEER_GROUP_VERSION,
        "as_of_date": target_session,
        "framework": framework,
        "sample_quality": sample_quality,
        "display_metric": display_metric,
        "selection": selection,
        "metrics": metrics,
        "audit": audit,
        "canonical_fact": {
            "fact_id": "valuation:peer",
            "fact_type": "peer_valuation",
            "as_of_date": target_session,
            "source": "free_source_current_peer_assembly",
            "fields": peer_fields,
        }
        if available_metrics
        else None,
        "numeric_provenance": numeric_provenance,
    }


def render_free_peer_context(state: Mapping[str, object]) -> str | None:
    if state.get("available") is not True:
        return None
    metrics = state.get("metrics")
    if not isinstance(metrics, dict):
        return None
    configured_metric = str(state.get("display_metric") or "")
    metric_key = (
        configured_metric
        if isinstance(metrics.get(configured_metric), dict)
        and metrics[configured_metric].get("available") is True
        else None
    )
    if metric_key is None:
        return None
    metric = metrics[metric_key]
    label = "PBR" if metric_key == "price_to_book" else "PER"
    company_value = metric["company_value"]
    peer_median = metric["median"]
    sample_count = metric["sample_count"]
    difference = metric["company_vs_median_pct"]
    relation = "높지만" if float(difference) >= 0 else "낮지만"
    relative_label = "프리미엄" if float(difference) >= 0 else "할인"
    scope_label = _comparison_scope_label(state)
    framework = str(state.get("framework") or "general")
    caution = {
        "memory": "메모리 사이클·마진·현금흐름 차이를 함께 봐야 합니다.",
        "semiconductor": "제품 믹스·마진·설비투자 이후 현금흐름 차이를 함께 봐야 합니다.",
        "insurance": "ROE·자본적정성 차이 확인 전에는 할인 여부만으로 결론 내리지 않습니다.",
        "steel_materials": "사이클 정상화 이익과 현금전환 차이를 함께 봐야 합니다.",
        "transport_logistics": "운임·물량·중기 마진과 현금전환 차이를 함께 봐야 합니다.",
    }.get(framework)
    caution_suffix = f" {caution}" if caution else ""
    return (
        f"동일 {scope_label} 분류에서 {label} 비교가 가능한 {sample_count}개 상장사 "
        f"중앙값은 {peer_median:.2f}배입니다. 현재 {label} {company_value:.2f}배는 "
        f"이 기초 비교군보다 {abs(float(difference)):.1f}% {relation}, 사업모델·성장 "
        f"기대가 달라 직접 동종기업 {relative_label} 해석에는 한계가 있습니다."
        f"{caution_suffix}"
    )
