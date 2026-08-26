import json
from datetime import date, datetime, timezone

from app.macro.temporal import (
    CURRENT_OBSERVATION,
    PRIOR_MARKET_SESSION,
    REFERENCE_LAGGING,
    STALE_FOR_DAILY_SIGNAL,
    UNAVAILABLE,
    build_temporal_context,
    rehydrate_legacy_market_summary,
)
from app.models.macro import MacroBriefing
from app.schemas.ai_review import AIMarketReview
from app.services.ai_review_service import _macro_temporal_semantic_errors
from app.services.daily_digest import interpret_macro_briefing
from app.services.market_intelligence_service import build_market_intelligence
from app.services.market_session import us_market_session


def _row(
    code: str,
    observed_at: str,
    *,
    change_pct: float | None = None,
    change_value: float | None = None,
    quality: str = "fresh",
) -> dict[str, object]:
    return {
        "series_code": code,
        "observed_at": observed_at,
        "retrieved_at": "2026-08-23T23:05:00+00:00",
        "quality_status": quality,
        "frequency": "daily",
        "change_pct": change_pct,
        "change_value": change_value,
        "value": 100.0,
    }


def _summary(*rows: dict[str, object]) -> dict[str, object]:
    return {"observations": list(rows)}


def _briefing(
    summary: dict[str, object],
    temporal: dict[str, object],
) -> MacroBriefing:
    observations = {
        str(item["series_code"]): dict(item)
        for item in summary["observations"]
        if isinstance(item, dict)
    }
    decisions = temporal["decisions"]
    for code, item in observations.items():
        item["temporal"] = decisions[code]
    return MacroBriefing(
        briefing_date=date(2026, 8, 24),
        briefing_type="morning",
        as_of=datetime(2026, 8, 23, 23, 5, tzinfo=timezone.utc),
        headline="mixed",
        market_summary=json.dumps(
            {
                "observations": list(observations.values()),
                "temporal_eligibility": temporal,
            }
        ),
        regime_summary=json.dumps(
            {
                "label": "mixed",
                "confidence": 0.8,
                "growth_momentum": -1,
                "inflation_pressure": 1,
                "liquidity_condition": 0,
                "financial_conditions": -1,
                "risk_appetite": -2,
                "earnings_momentum": -1,
            }
        ),
        macro_theses=json.dumps(
            [
                {
                    "thesis_key": "fed_policy_path",
                    "title": "연준 정책경로",
                    "status": "intact",
                    "today_signal": "negative",
                    "today_signal_strength": "weak",
                }
            ]
        ),
        today_calendar="[]",
        ticker_impacts="[]",
        data_quality="[]",
        kakao_text="unused",
        status="ready",
        dedupe_key="macro-temporal-test",
    )


def _legacy_briefing(
    summary: dict[str, object],
    *,
    briefing_date: date,
    as_of: datetime,
    key: str,
) -> MacroBriefing:
    return MacroBriefing(
        briefing_date=briefing_date,
        briefing_type="morning",
        as_of=as_of,
        headline="legacy",
        market_summary=json.dumps(summary),
        regime_summary=json.dumps(
            {
                "label": "mixed",
                "confidence": 0.8,
                "growth_momentum": -1,
                "inflation_pressure": 1,
                "liquidity_condition": 0,
                "financial_conditions": -1,
                "risk_appetite": -2,
                "earnings_momentum": -1,
            }
        ),
        macro_theses=json.dumps(
            [
                {
                    "thesis_key": "oil_supply_shock",
                    "title": "유가와 공급충격",
                    "status": "intact",
                    "today_signal": "negative",
                    "today_signal_strength": "weak",
                }
            ]
        ),
        today_calendar="[]",
        ticker_impacts="[]",
        data_quality="[]",
        kakao_text="unused",
        status="ready",
        dedupe_key=key,
    )


def test_weekend_repeated_observations_are_not_today_signals() -> None:
    current = _summary(
        _row("SPY", "2026-08-21T20:00:00+00:00", change_pct=-1.0),
        _row("DGS10", "2026-08-20T00:00:00+00:00", change_value=0.06),
        _row("VIXCLS", "2026-08-20T00:00:00+00:00", change_pct=7.5),
        _row("USDKRW", "2026-08-23T00:00:00+00:00", change_pct=0.8),
    )
    previous = _summary(
        _row("SPY", "2026-08-21T20:00:00+00:00", change_pct=-1.0),
        _row("DGS10", "2026-08-20T00:00:00+00:00", change_value=0.06),
        _row("VIXCLS", "2026-08-20T00:00:00+00:00", change_pct=7.5),
        _row("USDKRW", "2026-08-22T00:00:00+00:00", change_pct=0.8),
    )

    context = build_temporal_context(
        current,
        previous,
        as_of=datetime(2026, 8, 23, 23, 5, tzinfo=timezone.utc),
    )

    decisions = context["decisions"]
    assert decisions["SPY"]["temporal_role"] == PRIOR_MARKET_SESSION
    assert decisions["DGS10"]["temporal_role"] == REFERENCE_LAGGING
    assert decisions["VIXCLS"]["temporal_role"] == REFERENCE_LAGGING
    assert decisions["USDKRW"]["temporal_role"] == REFERENCE_LAGGING
    assert context["current_series"] == []
    assert set(context["daily_axes"].values()) == {0}

    macro = interpret_macro_briefing(_briefing(current, context))
    assert macro.one_line_heading == "현재 한 줄"
    assert macro.changes_heading == "직전 거래일 맥락"
    assert "새 일일 거시 관측이 없어" in macro.one_line
    assert all("VIX" not in item for item in macro.key_changes)
    assert all("원/달러" not in item for item in macro.key_changes)
    assert macro.key_changes
    assert "직전 거래일" in macro.key_changes[0]
    assert all("현재 신호: 중립" in item for item in macro.market_assumptions)


def test_closed_session_allows_new_official_release() -> None:
    current = _summary(
        _row("DGS10", "2026-08-21T00:00:00+00:00", change_value=-0.07),
    )
    previous = _summary(
        _row("DGS10", "2026-08-20T00:00:00+00:00", change_value=0.01),
    )
    context = build_temporal_context(
        current,
        previous,
        as_of=datetime(2026, 8, 23, 23, 5, tzinfo=timezone.utc),
    )
    decision = context["decisions"]["DGS10"]
    assert decision["temporal_role"] == CURRENT_OBSERVATION
    assert decision["today_signal_eligible"] is True
    assert context["daily_axes"]["financial_conditions"] == 0


def test_normal_after_close_session_marks_new_prices_current() -> None:
    current = _summary(
        _row("SPY", "2026-08-24T20:00:00+00:00", change_pct=1.2),
        _row("QQQ", "2026-08-24T20:00:00+00:00", change_pct=1.5),
    )
    previous = _summary(
        _row("SPY", "2026-08-21T20:00:00+00:00", change_pct=-0.5),
        _row("QQQ", "2026-08-21T20:00:00+00:00", change_pct=-0.6),
    )
    context = build_temporal_context(
        current,
        previous,
        as_of=datetime(2026, 8, 25, 1, 0, tzinfo=timezone.utc),
    )
    assert context["decisions"]["SPY"]["temporal_role"] == CURRENT_OBSERVATION
    assert context["decisions"]["QQQ"]["temporal_role"] == CURRENT_OBSERVATION
    assert context["daily_axes"]["risk_appetite"] == 2


def test_current_rsp_level_without_return_stays_level_only() -> None:
    current = _summary(_row("RSP", "2026-08-24T20:00:00+00:00"))
    context = build_temporal_context(
        current,
        {},
        as_of=datetime(2026, 8, 25, 1, 0, tzinfo=timezone.utc),
    )

    decision = context["decisions"]["RSP"]
    assert decision["temporal_role"] == CURRENT_OBSERVATION
    assert decision["structured_state"] == "CURRENT_LEVEL_ONLY"
    assert decision["today_signal_eligible"] is False
    assert decision["important_change_eligible"] is False
    assert context["current_series"] == []
    assert context["current_level_only_series"] == ["RSP"]


def test_release_observation_change_renders_source_date_not_today() -> None:
    current = _summary(
        _row("DGS10", "2026-08-24T00:00:00+00:00", change_value=0.06),
    )
    previous = _summary(
        _row("DGS10", "2026-08-21T00:00:00+00:00", change_value=0.01),
    )
    context = build_temporal_context(
        current,
        previous,
        as_of=datetime(2026, 8, 25, 23, 5, tzinfo=timezone.utc),
    )
    macro = interpret_macro_briefing(_briefing(current, context))

    assert any(item.startswith("공식 관측(8/24)") for item in macro.key_changes)
    assert all("오늘 미국 10년물" not in item for item in macro.key_changes)


def test_us_sector_dispersion_uses_only_directional_same_session_facts() -> None:
    current = _summary(
        _row("XLE", "2026-08-24T20:00:00+00:00", change_pct=-1.6638),
        _row("XLF", "2026-08-24T20:00:00+00:00", change_pct=0.1546),
        _row("RSP", "2026-08-24T20:00:00+00:00"),
    )
    context = build_temporal_context(
        current,
        {},
        as_of=datetime(2026, 8, 25, 1, 0, tzinfo=timezone.utc),
    )
    briefing = _briefing(current, context)
    macro = interpret_macro_briefing(briefing)

    assert any("에너지 -1.7%, 금융 +0.2%" in item for item in macro.key_changes)
    assert all("RSP" not in item and "동일가중" not in item for item in macro.key_changes)


def test_old_session_and_bad_quality_fail_closed() -> None:
    current = _summary(
        _row("SPY", "2026-08-20T20:00:00+00:00", change_pct=2.0),
        _row("DGS10", "2026-08-21T00:00:00+00:00", change_value=0.2, quality="stale"),
    )
    context = build_temporal_context(
        current,
        {},
        as_of=datetime(2026, 8, 23, 23, 5, tzinfo=timezone.utc),
    )
    assert context["decisions"]["SPY"]["temporal_role"] == STALE_FOR_DAILY_SIGNAL
    assert context["decisions"]["DGS10"]["temporal_role"] == STALE_FOR_DAILY_SIGNAL


def test_lagging_release_is_source_unavailable_for_current_structured_context() -> None:
    current = _summary(
        _row("DCOILWTICO", "2026-08-18T00:00:00+00:00", change_pct=2.0),
    )
    previous = _summary(
        _row("DCOILWTICO", "2026-08-18T00:00:00+00:00", change_pct=2.0),
    )
    context = build_temporal_context(
        current,
        previous,
        as_of=datetime(2026, 8, 25, 23, 5, tzinfo=timezone.utc),
    )

    decision = context["decisions"]["DCOILWTICO"]
    assert decision["temporal_role"] == REFERENCE_LAGGING
    assert decision["structured_state"] == "SOURCE_UNAVAILABLE"
    assert decision["today_signal_eligible"] is False


def test_market_intelligence_selects_only_current_change_facts() -> None:
    current = _summary(
        _row("SPY", "2026-08-21T20:00:00+00:00", change_pct=-1.2),
        _row("DGS10", "2026-08-21T00:00:00+00:00", change_value=0.07),
        _row("VIXCLS", "2026-08-20T00:00:00+00:00", change_pct=7.5),
    )
    previous = _summary(
        _row("SPY", "2026-08-21T20:00:00+00:00", change_pct=-1.2),
        _row("DGS10", "2026-08-20T00:00:00+00:00", change_value=0.01),
        _row("VIXCLS", "2026-08-20T00:00:00+00:00", change_pct=7.5),
    )
    temporal = build_temporal_context(
        current,
        previous,
        as_of=datetime(2026, 8, 23, 23, 5, tzinfo=timezone.utc),
    )
    briefing = _briefing(current, temporal)
    result = build_market_intelligence(briefing, date(2026, 8, 24), [], [], market="us")

    assert result["key_change_fact_ids"] == ["market:nominal_yield:DGS10"]
    assert "market:index:SPY" in result["prior_market_session_fact_ids"]
    assert "market:volatility:VIXCLS" in result["reference_fact_ids"]


def test_holiday_and_mixed_timing_are_classified_per_series() -> None:
    current = _summary(
        _row("SPY", "2026-09-04T20:00:00+00:00", change_pct=-0.8),
        _row("VIXCLS", "2026-09-07T00:00:00+00:00", change_pct=6.0),
        _row("DCOILWTICO", "2026-09-03T00:00:00+00:00", change_pct=2.5),
    )
    previous = _summary(
        _row("SPY", "2026-09-04T20:00:00+00:00", change_pct=-0.8),
        _row("VIXCLS", "2026-09-04T00:00:00+00:00", change_pct=-2.0),
        _row("DCOILWTICO", "2026-09-03T00:00:00+00:00", change_pct=2.5),
    )
    context = build_temporal_context(
        current,
        previous,
        as_of=datetime(2026, 9, 7, 23, 0, tzinfo=timezone.utc),
    )
    decisions = context["decisions"]
    assert decisions["SPY"]["temporal_role"] == PRIOR_MARKET_SESSION
    assert decisions["VIXCLS"]["temporal_role"] == CURRENT_OBSERVATION
    assert decisions["DCOILWTICO"]["temporal_role"] == REFERENCE_LAGGING
    assert context["daily_axes"]["risk_appetite"] == -1
    assert context["daily_axes"]["inflation_pressure"] == 0


def test_early_close_uses_authoritative_session_close() -> None:
    state = us_market_session(datetime(2026, 11, 27, 19, 0, tzinfo=timezone.utc))
    assert state.session == "after_hours"
    assert state.latest_completed_regular_session_date == date(2026, 11, 27)

    context = build_temporal_context(
        _summary(_row("SPY", "2026-11-27T18:00:00+00:00", change_pct=0.9)),
        _summary(_row("SPY", "2026-11-25T21:00:00+00:00", change_pct=-0.3)),
        as_of=datetime(2026, 11, 27, 19, 0, tzinfo=timezone.utc),
    )
    assert context["decisions"]["SPY"]["temporal_role"] == CURRENT_OBSERVATION


def test_same_period_official_revision_is_current() -> None:
    current = _row("DGS10", "2026-08-20T00:00:00+00:00", change_value=0.03, quality="revised")
    current["value"] = 4.68
    previous = _row("DGS10", "2026-08-20T00:00:00+00:00", change_value=0.04)
    previous["value"] = 4.69
    context = build_temporal_context(
        _summary(current),
        _summary(previous),
        as_of=datetime(2026, 8, 23, 23, 5, tzinfo=timezone.utc),
    )
    assert context["decisions"]["DGS10"]["temporal_role"] == CURRENT_OBSERVATION


def test_legacy_missing_temporal_metadata_rehydrates_without_mutation() -> None:
    current = _summary(
        _row("SPY", "2026-08-21T20:00:00+00:00", change_pct=-1.0),
        _row("VIXCLS", "2026-08-20T00:00:00+00:00", change_pct=7.5),
    )
    previous = _summary(
        _row("SPY", "2026-08-21T20:00:00+00:00", change_pct=-1.0),
        _row("VIXCLS", "2026-08-20T00:00:00+00:00", change_pct=7.5),
    )
    original = json.loads(json.dumps(current))

    view = rehydrate_legacy_market_summary(
        current,
        previous,
        as_of=datetime(2026, 8, 23, 23, 5, tzinfo=timezone.utc),
        previous_cutoff=datetime(2026, 8, 22, 23, 5, tzinfo=timezone.utc),
    )

    decisions = view["temporal_eligibility"]["decisions"]
    assert decisions["SPY"]["temporal_role"] == PRIOR_MARKET_SESSION
    assert decisions["VIXCLS"]["temporal_role"] == REFERENCE_LAGGING
    assert view["temporal_eligibility"]["compatibility_contract"] == (
        "macro-temporal-legacy-rehydration-v1"
    )
    assert current == original


def test_legacy_new_release_requires_observation_and_retrieval_after_cutoff() -> None:
    release = _row(
        "DGS10",
        "2026-08-24T00:00:00+00:00",
        change_value=-0.07,
    )
    release["retrieved_at"] = "2026-08-24T13:00:00+00:00"
    view = rehydrate_legacy_market_summary(
        _summary(release),
        {},
        as_of=datetime(2026, 8, 24, 14, 0, tzinfo=timezone.utc),
        previous_cutoff=datetime(2026, 8, 23, 23, 5, tzinfo=timezone.utc),
    )
    assert view["temporal_eligibility"]["decisions"]["DGS10"][
        "temporal_role"
    ] == CURRENT_OBSERVATION


def test_legacy_insufficient_identity_never_defaults_current() -> None:
    missing = _row("VIXCLS", "", change_pct=7.5)
    view = rehydrate_legacy_market_summary(
        _summary(missing),
        {},
        as_of=datetime(2026, 8, 23, 23, 5, tzinfo=timezone.utc),
    )
    decision = view["temporal_eligibility"]["decisions"]["VIXCLS"]
    assert decision["temporal_role"] == UNAVAILABLE
    assert decision["today_signal_eligible"] is False


def test_legacy_daily_digest_and_market_intelligence_share_temporal_view() -> None:
    current = _summary(
        _row("SPY", "2026-08-21T20:00:00+00:00", change_pct=-1.2),
        _row("VIXCLS", "2026-08-20T00:00:00+00:00", change_pct=7.5),
    )
    previous = _summary(
        _row("SPY", "2026-08-21T20:00:00+00:00", change_pct=-1.2),
        _row("VIXCLS", "2026-08-20T00:00:00+00:00", change_pct=7.5),
    )
    previous_briefing = _legacy_briefing(
        previous,
        briefing_date=date(2026, 8, 23),
        as_of=datetime(2026, 8, 22, 23, 5, tzinfo=timezone.utc),
        key="legacy-previous",
    )
    current_briefing = _legacy_briefing(
        current,
        briefing_date=date(2026, 8, 24),
        as_of=datetime(2026, 8, 23, 23, 5, tzinfo=timezone.utc),
        key="legacy-current",
    )

    macro = interpret_macro_briefing(current_briefing, previous_briefing)
    intelligence = build_market_intelligence(
        current_briefing,
        date(2026, 8, 24),
        [],
        [],
        market="kr",
        previous_briefing=previous_briefing,
    )

    assert macro.has_current_observation is False
    assert all("VIX" not in item for item in macro.key_changes)
    assert intelligence["current_observation_fact_ids"] == []
    assert "market:index:SPY" in intelligence["prior_market_session_fact_ids"]
    assert "market:volatility:VIXCLS" in intelligence["reference_fact_ids"]


def _market_review(change_text: str, fact_id: str) -> AIMarketReview:
    return AIMarketReview.model_validate(
        {
            "facts_used": [fact_id],
            "frameworks_used": [],
            "core_judgment": {"text": "시장 상태를 참고합니다.", "fact_ids": [fact_id]},
            "important_changes": [{"text": change_text, "fact_ids": [fact_id]}],
            "market_context": {"text": "시장 상태를 참고합니다.", "fact_ids": [fact_id]},
            "market_assumptions": {"text": "가정은 유지합니다.", "fact_ids": [fact_id]},
            "portfolio_transmission": [],
            "next_checks": [],
            "numeric_claims": [],
            "unknowns": [],
        }
    )


def _validator_context(role: str) -> dict[str, object]:
    return {
        "macro_temporal_eligibility": {
            "contract": "macro-digest-temporal-eligibility-v1"
        },
        "fact_catalog": [
            {
                "fact_id": "market:volatility:VIXCLS",
                "fields": {"temporal_role": role},
            }
        ],
    }


def test_semantic_validator_rejects_reference_as_today_change() -> None:
    errors = _macro_temporal_semantic_errors(
        _validator_context(REFERENCE_LAGGING),
        _market_review(
            "오늘 VIX가 7.5% 움직여 위험회피가 커졌습니다.",
            "market:volatility:VIXCLS",
        ),
    )
    assert "market_review:temporal_reference_used_as_important_change:0" in errors
    assert any(item.startswith("market_review:stale_or_prior_as_current:") for item in errors)


def test_semantic_validator_allows_explicit_prior_session_wording() -> None:
    errors = _macro_temporal_semantic_errors(
        _validator_context(PRIOR_MARKET_SESSION),
        _market_review(
            "직전 거래일 기준 VIX 변화를 참고합니다.",
            "market:volatility:VIXCLS",
        ),
    )
    assert errors == []
