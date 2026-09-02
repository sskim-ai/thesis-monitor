from __future__ import annotations

from app.services.us_full_message_service import (
    preserve_us_full_message_layout,
    render_us_full_market_message,
)
from app.services.us_market_digest_plan_service import build_us_market_digest_plan


def _fact(
    symbol: str,
    fact_type: str,
    value: float,
    *,
    label: str,
) -> dict[str, object]:
    return {
        "fact_id": f"market:{fact_type.removeprefix('market_')}:{symbol}",
        "fact_type": fact_type,
        "as_of_date": "2026-08-27",
        "fields": {
            "series_code": symbol,
            "label": label,
            "return_pct": value,
            "temporal_role": "CURRENT_OBSERVATION",
            "today_signal_eligible": True,
            "structured_state": "CURRENT_DIRECTIONAL",
        },
    }


def _context() -> dict[str, object]:
    facts = [
        _fact("SPY", "market_index", 0.6553, label="S&P500"),
        _fact("QQQ", "market_index", 1.3692, label="Nasdaq"),
        _fact("IWM", "market_index", 0.2944, label="Russell 2000"),
        _fact("SOXX", "market_sector", 1.9461, label="반도체"),
        _fact("RSP", "market_style", -0.2972, label="S&P500 동일가중"),
        _fact("XLK", "market_sector", 3.1558, label="정보기술"),
        _fact("XLP", "market_sector", -1.3794, label="필수소비재"),
    ]
    context: dict[str, object] = {"fact_catalog": facts, "key_change_fact_ids": []}
    context["us_market_digest_plan"] = build_us_market_digest_plan(context).to_dict()
    return context


def _macro_fact(
    symbol: str,
    fact_type: str,
    value: float,
    *,
    label: str,
    field: str,
    temporal_role: str = "CURRENT_OBSERVATION",
    as_of_date: str = "2026-08-27",
) -> dict[str, object]:
    return {
        "fact_id": f"market:{fact_type.removeprefix('market_')}:{symbol}",
        "fact_type": fact_type,
        "as_of_date": as_of_date,
        "fields": {
            "series_code": symbol,
            "label": label,
            field: value,
            "temporal_role": temporal_role,
            "today_signal_eligible": temporal_role == "CURRENT_OBSERVATION",
            "structured_state": temporal_role,
        },
    }


def _select_stored_macro(
    context: dict[str, object],
    fact: dict[str, object],
) -> None:
    context["fact_catalog"].append(fact)
    items = list(context["us_market_digest_plan"]["items"])
    items[-1] = {
        "slot": "MACRO_CONTEXT",
        "priority": 5,
        "claim_text": "legacy prose is not trusted",
        "materiality": "specific neutral macro selected by the upstream policy",
        "evidence_refs": [fact["fact_id"]],
        "numeric_refs": [],
        "temporal_roles": [fact["fields"]["temporal_role"]],
        "observation_dates": [fact["as_of_date"]],
        "omission_reason": "SELECTED",
        "required_consumption": False,
    }
    context["us_market_digest_plan"]["items"] = items


def test_full_message_owns_index_and_sector_numbers_in_fixed_order() -> None:
    rendered = render_us_full_market_message(_context())

    assert rendered.status == "PASS"
    assert rendered.section_order == (
        "HEADER",
        "INDEX_BLOCK",
        "MARKET_INTERNAL",
        "NEXT_CHECK",
    )
    assert rendered.text.startswith("🇺🇸 미국시장 마감\n\n📈 주요 지수")
    for line in (
        "• SPY +0.66%",
        "• QQQ +1.37%",
        "• IWM +0.29%",
        "• SOXX +1.95%",
        "• RSP -0.30%",
        "• 업종 강세: 정보기술 +3.16%",
        "• 업종 약세: 필수소비재 -1.38%",
    ):
        assert rendered.text.count(line) == 1
    assert rendered.text.index("📈 주요 지수") < rendered.text.index("🔎 시장 내부")
    assert rendered.text.index("🔎 시장 내부") < rendered.text.index("📌 다음 확인")
    assert "반도체 SOXX가 SPY를 크게 웃돌아" in rendered.text
    assert "소형주 IWM" not in rendered.text


def test_current_close_renders_material_iwm_soxx_without_overloading_roles() -> None:
    context = _context()
    current_returns = {
        "SPY": -0.2269,
        "QQQ": -0.6490,
        "IWM": -1.3542,
        "SOXX": -3.1993,
        "RSP": -0.3432,
        "XLK": -1.55,
        "XLP": -0.20,
    }
    for fact in context["fact_catalog"]:
        series = fact["fields"]["series_code"]
        if series in current_returns:
            fact["fields"]["return_pct"] = current_returns[series]
    context["us_market_digest_plan"] = build_us_market_digest_plan(context).to_dict()

    rendered = render_us_full_market_message(context)

    assert rendered.status == "PASS"
    assert rendered.text.count("소형주 IWM도 SPY보다 약해 위험선호는 제한적이었습니다.") == 1
    assert (
        rendered.text.count("반도체 SOXX가 SPY를 크게 밑돌아 반도체 상대약세가 두드러졌습니다.")
        == 1
    )
    assert "동일가중 S&P500은 하락해" in rendered.text
    assert "breadth" not in rendered.text
    assert rendered.text.count("• 업종 강세:") == 1
    assert rendered.text.count("• 업종 약세:") == 1


def test_full_message_renders_verified_night_returns_without_levels() -> None:
    context = _context()
    context["night_futures"] = [
        {
            "fact_id": "market:night_futures:1",
            "field_path": "fields.change_pct",
            "state": "CURRENT_DIRECTIONAL",
            "series_code": "KRX_KOSPI200_NIGHT_FUT",
            "change_pct": 0.67,
        },
        {
            "fact_id": "market:night_futures:2",
            "field_path": "fields.change_pct",
            "state": "CURRENT_DIRECTIONAL",
            "series_code": "KRX_KOSDAQ150_NIGHT_FUT",
            "change_pct": -0.28,
        },
    ]

    rendered = render_us_full_market_message(context)

    assert rendered.status == "PASS"
    assert "🌙 한국 야간선물\n• KOSPI200 야간선물 +0.67%" in rendered.text
    assert "• KOSDAQ150 야간선물 -0.28%" in rendered.text
    assert rendered.night_fact_ids == (
        "market:night_futures:1",
        "market:night_futures:2",
    )


def _timeframe(
    series: str,
    contract: str,
    timeframe: str,
    *,
    open_: float,
    high: float,
    low: float,
    close: float,
    return_pct: float,
) -> dict[str, object]:
    suffix = timeframe.lower()
    status = "FINAL" if timeframe == "DAILY" else "IN_PROGRESS"
    return {
        "contract": "krx-night-same-contract-dwm-v1",
        "fact_id": f"market:night_futures:{suffix}:{series}:{contract}:2026-09-01",
        "instrument_root": "KOSPI200" if "KOSPI" in series else "KOSDAQ150",
        "series_code": series,
        "contract_code": contract,
        "contract_maturity": "2026-09",
        "timeframe": timeframe,
        "bar_start_date": "2026-09-01",
        "reference_date": "2026-09-01",
        "open": open_,
        "high": high,
        "low": low,
        "close": close,
        "status": status,
        "quality": "VALID",
        "expected_dates": ["2026-09-01"],
        "included_dates": ["2026-09-01"],
        "missing_dates": [],
        "future_expected_dates": [] if status == "FINAL" else ["2026-09-02"],
        "aggregation_start_date": "2026-09-01",
        "gap_value": open_ - (close - 1.0) if timeframe == "DAILY" else None,
        "gap_pct": (
            (open_ - (close - 1.0)) / (close - 1.0) * 100
            if timeframe == "DAILY"
            else None
        ),
        "gap_baseline_date": "2026-08-31" if timeframe == "DAILY" else None,
        "gap_baseline_close": close - 1.0 if timeframe == "DAILY" else None,
        "gap_baseline_semantic": (
            "night_open_minus_validated_preceding_regular_day_close"
            if timeframe == "DAILY"
            else None
        ),
        "change_value": 1.0,
        "return_pct": return_pct,
        "return_baseline_date": "2026-08-31",
        "return_baseline_close": close - 1.0,
        "return_baseline_semantic": "verified_same_contract_baseline",
        "source_fact_ids": [f"source:{series}:{timeframe}"],
        "source_raw_sha256": ["a" * 64],
        "source_fingerprints": ["b" * 64],
    }


def _dwm_row(
    series: str,
    contract: str,
    values: tuple[float, float, float, float],
) -> dict[str, object]:
    open_, high, low, close = values
    frames = {
        "contract": "krx-night-same-contract-dwm-v1",
        "instrument_root": "KOSPI200" if "KOSPI" in series else "KOSDAQ150",
        "series_code": series,
        "contract_code": contract,
        "contract_maturity": "2026-09",
        "reference_date": "2026-09-01",
        "daily": _timeframe(
            series,
            contract,
            "DAILY",
            open_=open_,
            high=high,
            low=low,
            close=close,
            return_pct=-0.31,
        ),
        "weekly": _timeframe(
            series,
            contract,
            "WEEKLY",
            open_=open_ + 1,
            high=high + 10,
            low=low,
            close=close,
            return_pct=-1.60,
        ),
        "monthly": _timeframe(
            series,
            contract,
            "MONTHLY",
            open_=open_,
            high=high,
            low=low,
            close=close,
            return_pct=0.03,
        ),
    }
    return {
        "fact_id": (
            "market:night_futures:1"
            if series == "KRX_KOSPI200_NIGHT_FUT"
            else "market:night_futures:2"
        ),
        "field_path": "fields.change_pct",
        "state": "CURRENT_DIRECTIONAL",
        "series_code": series,
        "change_pct": -0.31,
        "contract_code": contract,
        "session_date": "2026-09-01",
        "night_timeframes": frames,
    }


def test_full_message_renders_two_same_contract_daily_weekly_monthly_blocks() -> None:
    context = _context()
    context["night_futures"] = [
        _dwm_row(
            "KRX_KOSPI200_NIGHT_FUT",
            "A0169000",
            (1067.0, 1072.45, 1053.8, 1064.5),
        ),
        _dwm_row(
            "KRX_KOSDAQ150_NIGHT_FUT",
            "A0669000",
            (1440.0, 1447.0, 1415.5, 1432.8),
        ),
    ]

    rendered = render_us_full_market_message(context)

    assert rendered.status == "PASS"
    assert rendered.text.count("- 일봉:") == 2
    assert rendered.text.count("- 주봉(진행중):") == 2
    assert rendered.text.count("- 월봉(진행중):") == 2
    assert "KOSPI200 최근월물 (202609)" in rendered.text
    assert "🌙 한국 야간선물 · 기준 09/01" in rendered.text
    assert "시가 1,067.00 · 종가 1,064.50 · 갭 +0.33% · 등락 -0.31%" in rendered.text
    assert "H 1,072.45" not in rendered.text
    assert "L 1,053.80" not in rendered.text
    assert len(rendered.night_fact_ids) == 6


def test_real_yield_is_not_the_primary_user_facing_rate_block() -> None:
    context = _context()
    context["fact_catalog"].append(
        {
            "fact_id": "market:real_yield:DFII10",
            "fact_type": "market_real_yield",
            "as_of_date": "2026-08-31",
            "fields": {
                "series_code": "DFII10",
                "label": "미국 10년물 실질금리",
                "level_pct": 2.44,
                "previous_level_pct": 2.42,
                "previous_observation_date": "2026-08-28",
                "change_pp": 0.02,
                "change_bp": 2.0,
                "temporal_role": "CURRENT_OBSERVATION",
                "today_signal_eligible": True,
                "structured_state": "CURRENT_DIRECTIONAL",
            },
        }
    )

    rendered = render_us_full_market_message(context)

    assert rendered.status == "PASS"
    assert "미 10년 실질금리" not in rendered.text
    assert "🌐 미국 국채금리" not in rendered.text


def test_nominal_treasury_curve_uses_same_series_observation_pairs() -> None:
    context = _context()
    values = {
        "DGS3": (3.72, 3.74),
        "DGS5": (3.84, 3.83),
        "DGS10": (4.21, 4.17),
        "DGS30": (4.86, 4.80),
    }
    for series, (current, previous) in values.items():
        context["fact_catalog"].append(
            {
                "fact_id": f"market:nominal_yield:{series}",
                "fact_type": "market_nominal_yield",
                "as_of_date": "2026-09-01",
                "fields": {
                    "series_code": series,
                    "label": f"미국 {series.removeprefix('DGS')}년물 금리",
                    "level_pct": current,
                    "previous_level_pct": previous,
                    "previous_observation_date": "2026-08-31",
                    "change_bp": (current - previous) * 100,
                    "temporal_role": "CURRENT_OBSERVATION",
                    "today_signal_eligible": True,
                    "structured_state": "CURRENT_DIRECTIONAL",
                },
            }
        )

    rendered = render_us_full_market_message(context)

    assert rendered.status == "PASS"
    assert "🌐 미국 국채금리 · 09/01 관측" in rendered.text
    for line in (
        "• 3년: 3.72% · -2bp",
        "• 5년: 3.84% · +1bp",
        "• 10년: 4.21% · +4bp",
        "• 30년: 4.86% · +6bp",
    ):
        assert line in rendered.text
    assert len(rendered.treasury_fact_ids) == 4


def test_treasury_curve_reports_exact_partial_pair_cause() -> None:
    context = _context()
    context["fact_catalog"].append(
        {
            "fact_id": "market:nominal_yield:DGS10",
            "fact_type": "market_nominal_yield",
            "as_of_date": "2026-09-01",
            "fields": {
                "series_code": "DGS10",
                "label": "미국 10년물 금리",
                "level_pct": 4.21,
                "change_bp": 4.0,
            },
        }
    )

    rendered = render_us_full_market_message(context)

    assert "• 3년: 공식 관측 없음" in rendered.text
    assert "• 5년: 공식 관측 없음" in rendered.text
    assert "• 10년: 직전 유효 관측쌍 불충분" in rendered.text
    assert "• 30년: 공식 관측 없음" in rendered.text


def test_full_message_suppresses_noncanonical_night_futures_sidecar() -> None:
    context = _context()
    context["night_futures"] = [
        {
            "fact_id": "legacy:night-futures",
            "series_code": "KRX_KOSPI200_NIGHT_FUT",
            "change_pct": 9.99,
        }
    ]

    rendered = render_us_full_market_message(context)

    assert rendered.status == "PASS"
    assert "🌙 한국 야간선물" not in rendered.text
    assert rendered.night_fact_ids == ()


def test_incomplete_index_tuple_fails_closed_for_new_layout() -> None:
    context = _context()
    context["fact_catalog"] = [
        row for row in context["fact_catalog"] if row["fields"]["series_code"] != "RSP"
    ]
    context["us_market_digest_plan"] = build_us_market_digest_plan(context).to_dict()

    rendered = render_us_full_market_message(context)

    assert rendered.status == "FAIL"
    assert "missing_current_index_return:RSP" in rendered.validation_errors


def test_adaptive_output_can_only_replace_bounded_next_check() -> None:
    deterministic = render_us_full_market_message(_context()).text
    candidate = """🤖 분석

🎯 판단
다른 요약입니다.

📌 다음 확인
• 다음 세션의 참여 폭을 확인합니다.
"""

    preserved = preserve_us_full_message_layout(
        candidate,
        deterministic_text=deterministic,
    )

    assert preserved.startswith("🇺🇸 미국시장 마감")
    assert "• SPY +0.66%" in preserved
    assert "• 다음 세션의 참여 폭을 확인합니다." in preserved
    assert "다른 요약입니다" not in preserved


def test_relative_equity_fact_is_not_promoted_to_macro_slot() -> None:
    context = _context()
    relative = {
        "fact_id": "market:relative:SOXX:SPY",
        "fact_type": "market_relative",
        "as_of_date": "2026-08-27",
        "fields": {
            "series_code": "SOXX_SPY",
            "temporal_role": "CURRENT_OBSERVATION",
            "today_signal_eligible": True,
            "structured_state": "CURRENT_DIRECTIONAL",
        },
    }
    context["fact_catalog"].append(relative)
    context["key_change_fact_ids"] = [relative["fact_id"]]

    plan = build_us_market_digest_plan(context)
    macro = plan.items[-1]

    assert macro.slot.value == "MACRO_CONTEXT"
    assert macro.selected is False
    assert macro.evidence_refs == ()


def test_legacy_stored_plan_cannot_reuse_relative_equity_as_macro() -> None:
    context = _context()
    relative = {
        "fact_id": "market:relative:SOXX:SPY",
        "fact_type": "market_sector_relative",
        "as_of_date": "2026-08-27",
        "fields": {
            "series_code": "SOXX_SPY",
            "temporal_role": "CURRENT_OBSERVATION",
            "today_signal_eligible": True,
            "structured_state": "CURRENT_DIRECTIONAL",
        },
    }
    context["fact_catalog"].append(relative)
    items = list(context["us_market_digest_plan"]["items"])
    items[-1] = {
        "slot": "MACRO_CONTEXT",
        "priority": 5,
        "claim_text": "보조 거시 맥락에서는 거시 지표가 변화 없음했습니다.",
        "materiality": "legacy invalid ownership",
        "evidence_refs": [relative["fact_id"]],
        "numeric_refs": [],
        "temporal_roles": ["CURRENT_OBSERVATION"],
        "observation_dates": ["2026-08-27"],
        "omission_reason": "SELECTED",
        "required_consumption": False,
    }
    context["us_market_digest_plan"]["items"] = items

    rendered = render_us_full_market_message(context)

    assert rendered.status == "PASS"
    assert "🌐 보조 시장환경" not in rendered.text
    assert "변화 없음했습니다" not in rendered.text


def test_generic_zero_change_macro_is_omitted_by_plan() -> None:
    context = _context()
    fact = _macro_fact(
        "DGS10",
        "market_nominal_yield",
        0.0,
        label="미국 10년물 금리",
        field="change_bp",
    )
    context["fact_catalog"].append(fact)
    context["key_change_fact_ids"] = [fact["fact_id"]]
    context["us_market_digest_plan"] = build_us_market_digest_plan(context).to_dict()

    rendered = render_us_full_market_message(context)

    assert rendered.status == "PASS"
    assert "🌐 보조 시장환경" not in rendered.text


def test_incomplete_nominal_yield_moves_to_primary_curve_block() -> None:
    context = _context()
    fact = _macro_fact(
        "DGS10",
        "market_nominal_yield",
        0.0,
        label="미국 10년물 금리",
        field="change_bp",
    )
    _select_stored_macro(context, fact)

    rendered = render_us_full_market_message(context)

    assert "🌐 미국 국채금리" in rendered.text
    assert "• 10년: 직전 유효 관측쌍 불충분" in rendered.text
    assert "🌐 보조 시장환경" not in rendered.text
    assert "변화 없음했습니다" not in rendered.text


def test_specific_neutral_vix_uses_grammar_safe_claim() -> None:
    context = _context()
    fact = _macro_fact(
        "VIXCLS",
        "market_volatility",
        0.0,
        label="VIX",
        field="return_pct",
    )
    _select_stored_macro(context, fact)

    rendered = render_us_full_market_message(context)

    assert "VIX는 전 세션과 큰 변화가 없었습니다." in rendered.text


def test_lagging_nominal_yield_is_not_labeled_same_day() -> None:
    context = _context()
    fact = _macro_fact(
        "DGS10",
        "market_nominal_yield",
        0.0,
        label="미국 10년물 금리",
        field="change_bp",
        temporal_role="PRIOR_MARKET_SESSION",
        as_of_date="2026-08-26",
    )
    _select_stored_macro(context, fact)

    rendered = render_us_full_market_message(context)

    assert "• 10년: 직전 유효 관측쌍 불충분" in rendered.text
    assert "오늘" not in rendered.text


def test_lagging_zero_change_wti_is_omitted_by_plan() -> None:
    context = _context()
    fact = _macro_fact(
        "DCOILWTICO",
        "market_oil",
        0.0,
        label="WTI 유가",
        field="return_pct",
        temporal_role="REFERENCE_LAGGING",
        as_of_date="2026-08-25",
    )
    context["fact_catalog"].append(fact)
    context["key_change_fact_ids"] = [fact["fact_id"]]
    context["us_market_digest_plan"] = build_us_market_digest_plan(context).to_dict()

    rendered = render_us_full_market_message(context)

    assert "🌐 보조 시장환경" not in rendered.text
