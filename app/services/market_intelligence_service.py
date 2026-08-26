from __future__ import annotations

from collections import defaultdict
from datetime import date, datetime, timezone
from typing import Iterable

from app.macro.temporal import rehydrate_legacy_market_summary
from app.models.macro import MacroBriefing
from app.services.market_cross_section_service import MarketCrossSection


USABLE_QUALITY = {"fresh", "revised"}

_SERIES = {
    "SPY": ("indices", "market_index", "S&P500"),
    "QQQ": ("indices", "market_index", "Nasdaq"),
    "IWM": ("indices", "market_index", "Russell 2000"),
    "RSP": ("style_size", "market_style", "S&P500 동일가중"),
    "SOXX": ("sectors", "market_sector", "반도체"),
    "XLB": ("sectors", "market_sector", "소재"),
    "XLC": ("sectors", "market_sector", "커뮤니케이션 서비스"),
    "XLE": ("sectors", "market_sector", "에너지"),
    "XLF": ("sectors", "market_sector", "금융"),
    "XLI": ("sectors", "market_sector", "산업재"),
    "XLK": ("sectors", "market_sector", "정보기술"),
    "XLP": ("sectors", "market_sector", "필수소비재"),
    "XLRE": ("sectors", "market_sector", "부동산"),
    "XLU": ("sectors", "market_sector", "유틸리티"),
    "XLV": ("sectors", "market_sector", "헬스케어"),
    "XLY": ("sectors", "market_sector", "경기소비재"),
    "DGS10": ("rates", "market_nominal_yield", "미국 10년물 금리"),
    "DFII10": ("rates", "market_real_yield", "미국 10년물 실질금리"),
    "T10YIE": ("rates", "market_breakeven_inflation", "미국 기대인플레이션"),
    "BAMLH0A0HYM2": ("credit", "market_credit_spread", "미국 하이일드 신용스프레드"),
    "DTWEXBGS": ("liquidity", "market_dollar_index", "미 달러지수(광의)"),
    "USDKRW": ("fx", "market_fx", "원/달러 환율"),
    "DCOILWTICO": ("commodities", "market_oil", "WTI 유가"),
    "VIXCLS": ("risk_signals", "market_volatility", "VIX"),
}

_EXPECTED_SERIES = {
    "indices": {"SPY", "QQQ", "IWM"},
    "style_size": {"RSP"},
    "sectors": {
        "SOXX",
        "XLB",
        "XLC",
        "XLE",
        "XLF",
        "XLI",
        "XLK",
        "XLP",
        "XLRE",
        "XLU",
        "XLV",
        "XLY",
    },
    "rates": {"DGS10", "DFII10", "T10YIE"},
    "credit": {"BAMLH0A0HYM2"},
    "liquidity": {"DTWEXBGS"},
    "fx": {"USDKRW"},
    "commodities": {"DCOILWTICO"},
    "risk_signals": {"VIXCLS"},
}

_SELECTION_THRESHOLDS = {
    ("SPY", "return_pct"): 1.0,
    ("QQQ:SPY", "relative_return_pct"): 0.4,
    ("SOXX:SPY", "relative_return_pct"): 0.5,
    ("DGS10", "change_bp"): 5.0,
    ("DFII10", "change_bp"): 3.0,
    ("VIXCLS", "return_pct"): 5.0,
    ("USDKRW", "change_pct"): 0.7,
    ("DCOILWTICO", "return_pct"): 2.0,
}

_GROUP_LABELS = {
    "semiconductor": "반도체",
    "memory": "메모리",
    "automotive": "자동차",
    "bank": "은행",
    "insurance": "보험·재보험",
    "shipping": "운송·물류",
    "holding_company": "지주회사",
    "consumer": "소비재",
    "epc_construction": "EPC·건설",
    "saas_recurring": "SaaS·구독",
    "cloud_platform": "클라우드·플랫폼",
    "biotech": "바이오",
    "robotaxi_preprofit": "로보택시·이익 전 단계",
    "general": "기타·일반",
}


def _briefing_as_of(briefing: MacroBriefing) -> datetime:
    for raw_value in (
        getattr(briefing, "as_of", None),
        getattr(briefing, "created_at", None),
        getattr(briefing, "briefing_date", None),
    ):
        value: datetime | None = None
        if isinstance(raw_value, datetime):
            value = raw_value
        elif isinstance(raw_value, date):
            value = datetime.combine(raw_value, datetime.min.time())
        elif raw_value:
            try:
                value = datetime.fromisoformat(str(raw_value).replace("Z", "+00:00"))
            except ValueError:
                continue
        if value is not None:
            return value if value.tzinfo is not None else value.replace(tzinfo=timezone.utc)
    raise ValueError("macro briefing is missing a usable as-of identity")


def _market_summary_view(
    briefing: MacroBriefing | None,
    previous_briefing: MacroBriefing | None,
) -> dict[str, object]:
    if briefing is None:
        return {}
    return rehydrate_legacy_market_summary(
        briefing.market_summary,
        previous_briefing.market_summary if previous_briefing is not None else None,
        as_of=_briefing_as_of(briefing),
        previous_cutoff=(
            _briefing_as_of(previous_briefing)
            if previous_briefing is not None
            else None
        ),
    )


def _observations(market_summary: dict[str, object]) -> dict[str, dict[str, object]]:
    values = market_summary.get("observations", [])
    if not isinstance(values, list):
        return {}
    return {
        str(item["series_code"]): item
        for item in values
        if isinstance(item, dict) and item.get("series_code")
    }


def _number(item: dict[str, object], key: str) -> float | None:
    value = item.get(key)
    return float(value) if isinstance(value, (int, float)) else None


def _fact_id(series_code: str) -> str:
    fact_type = _SERIES[series_code][1]
    category = fact_type.removeprefix("market_")
    return f"market:{category}:{series_code}"


def _observation_fact(
    series_code: str,
    item: dict[str, object],
    run_date: date,
) -> dict[str, object]:
    _category, fact_type, label = _SERIES[series_code]
    value = _number(item, "value")
    change_pct = _number(item, "change_pct")
    change_value = _number(item, "change_value")
    fields: dict[str, object] = {
        "series_code": series_code,
        "label": label,
        "quality": str(item.get("quality_status") or "fresh"),
        "observed_at": str(item.get("observed_at") or run_date),
    }
    temporal = item.get("temporal")
    if isinstance(temporal, dict):
        fields.update(
            {
                "temporal_contract": "macro-digest-temporal-eligibility-v1",
                "temporal_role": str(
                    temporal.get("temporal_role") or "REFERENCE_LAGGING"
                ),
                "today_signal_eligible": bool(
                    temporal.get("today_signal_eligible", False)
                ),
                "important_change_eligible": bool(
                    temporal.get("important_change_eligible", False)
                ),
                "temporal_reason": str(temporal.get("reason") or ""),
                "structured_state": str(
                    temporal.get("structured_state")
                    or (
                        "CURRENT_DIRECTIONAL"
                        if change_pct is not None or change_value is not None
                        else "CURRENT_LEVEL_ONLY"
                    )
                ),
            }
        )
    else:
        fields.update(
            {
                "temporal_role": "CURRENT_OBSERVATION",
                "today_signal_eligible": True,
                "important_change_eligible": True,
                "structured_state": (
                    "CURRENT_DIRECTIONAL"
                    if change_pct is not None or change_value is not None
                    else "CURRENT_LEVEL_ONLY"
                ),
            }
        )
    if item.get("market_session"):
        fields["market_session"] = str(item["market_session"])

    if fact_type in {"market_index", "market_sector", "market_style"}:
        if value is not None and fact_type in {"market_sector", "market_style"}:
            fields["level"] = value
        if change_pct is not None:
            fields["return_pct"] = change_pct
    elif fact_type in {
        "market_nominal_yield",
        "market_real_yield",
        "market_breakeven_inflation",
        "market_credit_spread",
    }:
        if value is not None:
            fields["level_pct"] = value
        if change_value is not None:
            fields["change_bp"] = change_value * 100.0
    elif fact_type == "market_fx":
        if value is not None:
            fields["value"] = value
        if change_pct is not None:
            fields["change_pct"] = change_pct
    elif fact_type == "market_oil":
        if value is not None:
            fields["price_usd_per_barrel"] = value
        if change_pct is not None:
            fields["return_pct"] = change_pct
    elif fact_type == "market_volatility":
        if value is not None:
            fields["level"] = value
        if change_pct is not None:
            fields["return_pct"] = change_pct
    elif fact_type == "market_dollar_index":
        if value is not None:
            fields["level"] = value
        if change_pct is not None:
            fields["return_pct"] = change_pct

    return {
        "fact_id": _fact_id(series_code),
        "fact_type": fact_type,
        "as_of_date": str(item.get("observed_at") or run_date).split(" ", 1)[0],
        "source": "verified_macro_briefing",
        "fields": fields,
    }


def _relative_fact(
    subject: str,
    benchmark: str,
    facts_by_series: dict[str, dict[str, object]],
) -> dict[str, object] | None:
    subject_fact = facts_by_series.get(subject)
    benchmark_fact = facts_by_series.get(benchmark)
    if subject_fact is None or benchmark_fact is None:
        return None
    subject_fields = subject_fact["fields"]
    benchmark_fields = benchmark_fact["fields"]
    if not isinstance(subject_fields, dict) or not isinstance(benchmark_fields, dict):
        return None
    subject_return = _number(subject_fields, "return_pct")
    benchmark_return = _number(benchmark_fields, "return_pct")
    if subject_return is None or benchmark_return is None:
        return None
    same_temporal_role = subject_fields.get("temporal_role") == benchmark_fields.get(
        "temporal_role"
    )
    same_date = subject_fact.get("as_of_date") == benchmark_fact.get("as_of_date")
    today_eligible = bool(
        same_temporal_role
        and same_date
        and subject_fields.get("today_signal_eligible") is True
        and benchmark_fields.get("today_signal_eligible") is True
    )
    if subject_fact.get("fact_type") == "market_sector":
        fact_type = "market_sector_relative"
    elif subject_fact.get("fact_type") == "market_style":
        fact_type = "market_style_relative"
    else:
        fact_type = "market_growth_relative"
    return {
        "fact_id": f"market:relative:{subject}:{benchmark}",
        "fact_type": fact_type,
        "as_of_date": subject_fact["as_of_date"],
        "source": "deterministic_market_relative_performance",
        "fields": {
            "subject": subject,
            "subject_label": subject_fields["label"],
            "benchmark": benchmark,
            "benchmark_label": benchmark_fields["label"],
            "relative_return_pct": subject_return - benchmark_return,
            "source_fact_ids": [subject_fact["fact_id"], benchmark_fact["fact_id"]],
            "temporal_role": (
                subject_fields.get("temporal_role")
                if same_temporal_role and same_date
                else "REFERENCE_LAGGING"
            ),
            "today_signal_eligible": today_eligible,
            "important_change_eligible": bool(
                same_temporal_role
                and same_date
                and subject_fields.get("important_change_eligible") is True
                and benchmark_fields.get("important_change_eligible") is True
            ),
        },
    }


def _coverage(
    observations: dict[str, dict[str, object]],
    market: str,
) -> tuple[dict[str, dict[str, object]], list[str]]:
    coverage: dict[str, dict[str, object]] = {}
    unknowns = [
        "시장 breadth는 backend packet에 제공되지 않았습니다.",
        "시장 전체 투자주체 수급은 backend packet에 제공되지 않았습니다.",
    ]
    for category, expected in _EXPECTED_SERIES.items():
        present = {
            code
            for code in expected
            if code in observations
            and str(observations[code].get("quality_status") or "fresh")
            in USABLE_QUALITY
        }
        status = "available" if present == expected else "partial" if present else "unavailable"
        coverage[category] = {
            "status": status,
            "available_series": sorted(present),
            "missing_series": sorted(expected - present),
        }
    if market == "kr":
        coverage["indices"]["role"] = "overnight_cross_asset_context"
        coverage["sectors"]["role"] = "overnight_cross_asset_context"
        coverage["style_size"]["role"] = "overnight_cross_asset_context"
        coverage["local_market_indices"] = {
            "status": "unavailable",
            "reason": "kr_local_index_not_provided_by_backend",
        }
        unknowns.append(
            "한국 현물 지수는 packet에 없어 미국 지수와 반도체 가격은 전일 해외 맥락으로만 사용합니다."
        )
    else:
        coverage["indices"]["role"] = "local_market_proxy"
        coverage["sectors"]["role"] = "local_sector_proxy"
        coverage["style_size"]["role"] = "local_style_proxy"
        coverage["local_market_indices"] = {
            "status": coverage["indices"]["status"],
            "available_series": coverage["indices"]["available_series"],
        }
    coverage["breadth"] = {
        "status": "unavailable",
        "reason": "not_provided_by_backend",
    }
    coverage["market_flows"] = {
        "status": "unavailable",
        "reason": "not_provided_by_backend",
    }
    stale = sorted(
        code
        for code, item in observations.items()
        if code in _SERIES
        and str(item.get("quality_status") or "fresh") not in USABLE_QUALITY
    )
    if stale:
        unknowns.append(
            "최신성이 부족해 핵심 판단에서 제외한 시장 지표: " + ", ".join(stale)
        )
    return coverage, unknowns


def _selected_change_fact_ids(
    facts: list[dict[str, object]],
) -> list[str]:
    by_id = {str(fact["fact_id"]): fact for fact in facts}
    candidates = (
        ("SPY", "return_pct", "market:index:SPY"),
        ("QQQ:SPY", "relative_return_pct", "market:relative:QQQ:SPY"),
        ("SOXX:SPY", "relative_return_pct", "market:relative:SOXX:SPY"),
        ("DGS10", "change_bp", "market:nominal_yield:DGS10"),
        ("DFII10", "change_bp", "market:real_yield:DFII10"),
        ("VIXCLS", "return_pct", "market:volatility:VIXCLS"),
        ("USDKRW", "change_pct", "market:fx:USDKRW"),
        ("DCOILWTICO", "return_pct", "market:oil:DCOILWTICO"),
    )
    ranked: list[tuple[float, str]] = []
    for series, field, fact_id in candidates:
        fact = by_id.get(fact_id)
        if fact is None or not isinstance(fact.get("fields"), dict):
            continue
        if fact["fields"].get("today_signal_eligible") is not True:
            continue
        value = _number(fact["fields"], field)
        threshold = _SELECTION_THRESHOLDS.get((series, field))
        if value is None or threshold is None or abs(value) < threshold:
            continue
        ranked.append((abs(value) / threshold, fact_id))
    ranked.sort(key=lambda item: (-item[0], item[1]))
    return [fact_id for _score, fact_id in ranked[:4]]


def _group_key(stock: dict[str, object]) -> str:
    profile = stock.get("company_profile")
    if isinstance(profile, dict) and profile.get("taxonomy_key"):
        return str(profile["taxonomy_key"])
    routing = stock.get("knowledge_routing")
    if isinstance(routing, dict):
        value = str(routing.get("industry_key") or "")
        if value and value != "general":
            return value
    return "general"


def _portfolio_transmission(
    stocks: list[dict[str, object]],
    impacts: Iterable[dict[str, object]],
    facts: list[dict[str, object]],
) -> tuple[list[dict[str, object]], list[dict[str, object]], dict[str, list[dict[str, object]]]]:
    fact_ids_by_series = {
        str(fields["series_code"]): str(fact["fact_id"])
        for fact in facts
        if isinstance((fields := fact.get("fields")), dict)
        and fields.get("series_code")
        and fields.get("today_signal_eligible") is True
    }
    fact_ids = {str(fact["fact_id"]) for fact in facts}
    stock_groups = {str(stock["ticker"]): _group_key(stock) for stock in stocks}
    group_members: dict[str, list[str]] = defaultdict(list)
    for ticker, group in stock_groups.items():
        group_members[group].append(ticker)

    groups = [
        {
            "group_key": group,
            "label": _GROUP_LABELS.get(group, group.replace("_", " ")),
            "tickers": sorted(tickers),
            "classification_source": "verified_company_profile",
        }
        for group, tickers in sorted(group_members.items())
    ]

    stock_links: dict[str, list[dict[str, object]]] = defaultdict(list)
    for impact in impacts:
        ticker = str(impact.get("ticker") or "")
        if ticker not in stock_groups:
            continue
        evidence = impact.get("evidence")
        if not isinstance(evidence, list):
            continue
        for item in evidence:
            if not isinstance(item, dict):
                continue
            fact_id = fact_ids_by_series.get(str(item.get("series_code") or ""))
            exposure = item.get("exposure")
            if fact_id is None or not isinstance(exposure, dict):
                continue
            stock_links[ticker].append(
                {
                    "fact_id": fact_id,
                    "factor": str(exposure.get("factor") or item.get("factor") or ""),
                    "channel": str(exposure.get("channel") or item.get("channel") or ""),
                    "direction": str(item.get("direction") or "neutral"),
                    "condition": str(exposure.get("condition") or ""),
                    "horizon": str(exposure.get("horizon") or ""),
                    "materiality": str(item.get("materiality") or "unknown"),
                    "earnings_link_validated": bool(item.get("earnings_link_validated")),
                    "valuation_context_eligible": bool(
                        item.get("eligible_for_valuation_context")
                    ),
                    "not_fundamental_confirmation": True,
                }
            )

    sector_relative = "market:relative:SOXX:SPY"
    sector_relative_fact = next(
        (item for item in facts if item.get("fact_id") == sector_relative),
        None,
    )
    sector_relative_fields = (
        sector_relative_fact.get("fields")
        if isinstance(sector_relative_fact, dict)
        and isinstance(sector_relative_fact.get("fields"), dict)
        else {}
    )
    if sector_relative in fact_ids and sector_relative_fields.get("today_signal_eligible") is True:
        for ticker, group in stock_groups.items():
            if group not in {"semiconductor", "memory"}:
                continue
            stock_links[ticker].append(
                {
                    "fact_id": sector_relative,
                    "factor": "semiconductor_relative_performance",
                    "channel": "risk_appetite",
                    "direction": "context",
                    "condition": "업종 가격 강도는 실제 주문·마진 확인과 분리",
                    "horizon": "단기",
                    "materiality": "market_context",
                    "earnings_link_validated": False,
                    "valuation_context_eligible": False,
                    "not_fundamental_confirmation": True,
                }
            )

    combined: dict[tuple[str, str], dict[str, object]] = {}
    for ticker, links in stock_links.items():
        group = stock_groups[ticker]
        for link in links:
            key = (group, str(link["fact_id"]))
            item = combined.setdefault(
                key,
                {
                    "portfolio_group": group,
                    "market_fact_id": link["fact_id"],
                    "tickers": [],
                    "channels": [],
                    "directions": [],
                    "conditions": [],
                    "not_fundamental_confirmation": True,
                },
            )
            item["tickers"].append(ticker)
            if link["channel"]:
                item["channels"].append(link["channel"])
            if link["direction"]:
                item["directions"].append(link["direction"])
            if link["condition"]:
                item["conditions"].append(link["condition"])

    candidates = []
    for item in combined.values():
        for key in ("tickers", "channels", "directions", "conditions"):
            item[key] = sorted(set(item[key]))
        candidates.append(item)
    candidates.sort(key=lambda item: (str(item["portfolio_group"]), str(item["market_fact_id"])))
    return groups, candidates, {ticker: links for ticker, links in stock_links.items()}


def build_market_intelligence(
    briefing: MacroBriefing | None,
    run_date: date,
    stocks: list[dict[str, object]],
    impacts: Iterable[dict[str, object]],
    *,
    market: str,
    cross_section: MarketCrossSection | None = None,
    previous_briefing: MacroBriefing | None = None,
) -> dict[str, object]:
    market_summary = _market_summary_view(briefing, previous_briefing)
    observations = _observations(market_summary)
    facts_by_series = {
        code: _observation_fact(code, item, run_date)
        for code, item in observations.items()
        if code in _SERIES
        and str(item.get("quality_status") or "fresh") in USABLE_QUALITY
    }
    facts = list(facts_by_series.values())
    for subject, benchmark in (
        ("QQQ", "SPY"),
        ("SOXX", "SPY"),
        ("RSP", "SPY"),
        ("XLE", "XLF"),
    ):
        relative = _relative_fact(subject, benchmark, facts_by_series)
        if relative is not None:
            facts.append(relative)
    cross_section_facts: list[dict[str, object]] = []
    if (
        cross_section is not None
        and cross_section.market.lower() == market.lower()
        and cross_section.session_date == run_date
        and cross_section.quality.freshness == "fresh"
    ):
        for index in cross_section.indices:
            cross_section_facts.append(
                {
                    "fact_id": f"market:cross-section:index:{index.symbol}",
                    "fact_type": "market_cross_section_index",
                    "as_of_date": run_date.isoformat(),
                    "source": cross_section.quality.provider,
                    "fields": {
                        "symbol": index.symbol,
                        "label": index.label,
                        "close": index.close,
                        "return_pct": index.return_pct,
                    },
                }
            )
        if cross_section.breadth is not None:
            breadth = cross_section.breadth
            cross_section_facts.extend(
                [
                    {
                        "fact_id": f"market:breadth:{market}:counts",
                        "fact_type": "market_breadth_counts",
                        "as_of_date": run_date.isoformat(),
                        "source": cross_section.quality.provider,
                        "fields": {
                            "eligible_count": breadth.eligible_count,
                            "advance_count": breadth.advance_count,
                            "decline_count": breadth.decline_count,
                            "unchanged_count": breadth.unchanged_count,
                        },
                    },
                    {
                        "fact_id": f"market:breadth:{market}:returns",
                        "fact_type": "market_breadth_returns",
                        "as_of_date": run_date.isoformat(),
                        "source": cross_section.quality.provider,
                        "fields": {
                            "advance_ratio_pct": (
                                breadth.advance_ratio * 100
                                if breadth.advance_ratio is not None
                                else None
                            ),
                            "ad_ratio": breadth.ad_ratio,
                            "median_return_pct": breadth.median_return_pct,
                            "equal_weight_return_pct": breadth.equal_weight_return_pct,
                            "positive_return_pct": breadth.positive_return_pct,
                            "negative_return_pct": breadth.negative_return_pct,
                        },
                    },
                ]
            )
            for scoped in cross_section.breadth_by_scope:
                scoped_breadth = scoped.breadth
                cross_section_facts.extend(
                    [
                        {
                            "fact_id": (
                                f"market:breadth:{market}:{scoped.scope}:counts"
                            ),
                            "fact_type": "market_breadth_counts",
                            "as_of_date": run_date.isoformat(),
                            "source": cross_section.quality.provider,
                            "fields": {
                                "market_scope": scoped.scope,
                                "eligible_count": scoped_breadth.eligible_count,
                                "advance_count": scoped_breadth.advance_count,
                                "decline_count": scoped_breadth.decline_count,
                                "unchanged_count": scoped_breadth.unchanged_count,
                            },
                        },
                        {
                            "fact_id": (
                                f"market:breadth:{market}:{scoped.scope}:returns"
                            ),
                            "fact_type": "market_breadth_returns",
                            "as_of_date": run_date.isoformat(),
                            "source": cross_section.quality.provider,
                            "fields": {
                                "market_scope": scoped.scope,
                                "advance_ratio_pct": (
                                    scoped_breadth.advance_ratio * 100
                                    if scoped_breadth.advance_ratio is not None
                                    else None
                                ),
                                "ad_ratio": scoped_breadth.ad_ratio,
                                "median_return_pct": (
                                    scoped_breadth.median_return_pct
                                ),
                                "equal_weight_return_pct": (
                                    scoped_breadth.equal_weight_return_pct
                                ),
                                "positive_return_pct": (
                                    scoped_breadth.positive_return_pct
                                ),
                                "negative_return_pct": (
                                    scoped_breadth.negative_return_pct
                                ),
                            },
                        },
                    ]
                )
            safe_volume = (
                breadth.total_trading_volume
                if cross_section.quality.volume_semantics == "raw_reported_shares"
                else None
            )
            safe_value = (
                breadth.total_trading_value
                if cross_section.quality.trading_value_semantics == "official_reported"
                else None
            )
            if safe_volume is not None or safe_value is not None:
                cross_section_facts.append(
                    {
                        "fact_id": f"market:breadth:{market}:activity",
                        "fact_type": "market_breadth_activity",
                        "as_of_date": run_date.isoformat(),
                        "source": cross_section.quality.provider,
                        "fields": {
                            "total_trading_volume": safe_volume,
                            "total_trading_value": safe_value,
                            "currency": "USD" if market.lower() == "us" else "KRW",
                        },
                    }
                )
        if cross_section.concentration.get("concentration_gap_pct") is not None:
            cross_section_facts.append(
                {
                    "fact_id": f"market:concentration:{market}",
                    "fact_type": "market_concentration",
                    "as_of_date": run_date.isoformat(),
                    "source": cross_section.quality.provider,
                    "fields": {
                        "metric_role": cross_section.concentration.get("metric_role"),
                        "proxy_symbol": cross_section.concentration.get("proxy_symbol"),
                        "concentration_gap_pct": cross_section.concentration[
                            "concentration_gap_pct"
                        ],
                    },
                }
            )
        flow_concentration = cross_section.concentration.get("relations")
        if isinstance(flow_concentration, list):
            for relation in flow_concentration:
                if not isinstance(relation, dict):
                    continue
                market_scope = str(relation.get("market") or "")
                actor = str(relation.get("actor") or "")
                if not market_scope or not actor:
                    continue
                cross_section_facts.append(
                    {
                        "fact_id": (
                            f"market:flow-concentration:{market_scope}:{actor}"
                        ),
                        "fact_type": "market_flow_concentration",
                        "as_of_date": run_date.isoformat(),
                        "source": cross_section.quality.provider,
                        "fields": relation,
                    }
                )
        for sector in cross_section.sectors:
            cross_section_facts.append(
                {
                    "fact_id": f"market:cross-section:sector:{sector.taxonomy}:{sector.sector}",
                    "fact_type": "market_cross_section_sector",
                    "as_of_date": run_date.isoformat(),
                    "source": cross_section.quality.provider,
                    "fields": {
                        **sector.model_dump(mode="json", exclude={"advance_ratio"}),
                        "advance_ratio_pct": (
                            sector.advance_ratio * 100
                            if sector.advance_ratio is not None
                            else None
                        ),
                    },
                }
            )
        for flow in cross_section.market_flows:
            cross_section_facts.append(
                {
                    "fact_id": f"market:flow:{market}:{flow.market}:{flow.actor}",
                    "fact_type": "market_flow",
                    "as_of_date": run_date.isoformat(),
                    "source": cross_section.quality.provider,
                    "fields": {
                        "actor": flow.actor,
                        "net_buy_amount": flow.net_buy_amount,
                        "currency": flow.currency,
                        "market_scope": flow.market,
                        "exchange_basis": flow.exchange_basis,
                        "source_ref": flow.source_ref,
                    },
                }
            )
        facts.extend(cross_section_facts)
    facts.sort(key=lambda item: str(item["fact_id"]))

    coverage, unknowns = _coverage(observations, market)
    if cross_section_facts:
        if cross_section.breadth is not None:
            coverage["breadth"] = {
                "status": "available",
                "provider": cross_section.quality.provider,
                "universe_version": cross_section.quality.universe_version,
            }
            unknowns = [item for item in unknowns if not item.startswith("시장 breadth")]
        if cross_section.market_flows:
            coverage["market_flows"] = {
                "status": "available",
                "provider": cross_section.quality.provider,
            }
            unknowns = [
                item for item in unknowns if not item.startswith("시장 전체 투자주체")
            ]
        if cross_section.indices and market.lower() == "kr":
            coverage["local_market_indices"] = {
                "status": "available",
                "provider": cross_section.quality.provider,
                "available_series": [item.symbol for item in cross_section.indices],
            }
    groups, transmissions, stock_transmissions = _portfolio_transmission(
        stocks, impacts, facts
    )
    current_fact_ids = sorted(
        str(item["fact_id"])
        for item in facts
        if isinstance(item.get("fields"), dict)
        and item["fields"].get("today_signal_eligible") is True
    )
    prior_fact_ids = sorted(
        str(item["fact_id"])
        for item in facts
        if isinstance(item.get("fields"), dict)
        and item["fields"].get("temporal_role") == "PRIOR_MARKET_SESSION"
    )
    reference_fact_ids = sorted(
        str(item["fact_id"])
        for item in facts
        if isinstance(item.get("fields"), dict)
        and item["fields"].get("temporal_role")
        in {"REFERENCE_LAGGING", "STALE_FOR_DAILY_SIGNAL", "UNAVAILABLE"}
    )
    return {
        "macro_temporal_eligibility": market_summary.get(
            "temporal_eligibility", {}
        ),
        "fact_catalog": facts,
        "key_change_fact_ids": _selected_change_fact_ids(facts),
        "current_observation_fact_ids": current_fact_ids,
        "prior_market_session_fact_ids": prior_fact_ids,
        "reference_fact_ids": reference_fact_ids,
        "coverage": coverage,
        "portfolio_exposure_groups": groups,
        "transmission_candidates": transmissions,
        "stock_transmissions": stock_transmissions,
        "unknowns": unknowns,
    }
