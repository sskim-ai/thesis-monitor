from __future__ import annotations

import pytest

from app.services.free_analyst_production_integration_service import (
    build_production_candidate,
)
from app.services.kr_market_digest_quality_service import (
    KrDigestSelectionState,
    build_kr_market_digest_plan,
)
from app.services.market_evidence_utilization_validator_service import (
    validate_kr_market_evidence_utilization,
)


OLD_RUN42_MESSAGE = """🤖 AI 보조 한국시장 마감 · KR Pilot 4/5

🎯 판단
KOSPI와 KOSDAQ의 지수 방향과 시장 폭이 엇갈려 국내 장을 하나의 방향으로 묶기 어렵습니다.

🔎 핵심 근거
외국인은 양 시장에서 순매수했습니다. 기관은 양 시장에서 순매수했습니다. 개인은 양 시장에서 순매도했습니다.

📌 다음 확인
• 양 시장의 상승·하락 종목 분포와 외국인·기관의 시장별 수급 방향이 함께 유지되는지 확인합니다.
"""


def _context() -> dict[str, object]:
    session = "2026-08-27"
    return {
        "contract_version": "market-context-adapter-v1",
        "market": "KR",
        "assessment_date": session,
        "session_date": session,
        "as_of": "2026-08-27T16:06:11+09:00",
        "cutoff": "2026-08-27T17:05:35+09:00",
        "indices": [
            {
                "symbol": symbol,
                "name": symbol,
                "close": close,
                "return_pct": return_pct,
                "basis": "official_or_provider_index",
                "as_of_date": session,
                "source_ref": f"index:{symbol}",
            }
            for symbol, close, return_pct in (
                ("KOSPI", 6912.37, 1.53),
                ("KOSDAQ", 837.65, 1.30),
            )
        ],
        "breadth": {
            "availability": "AVAILABLE",
            "advancers": 1157,
            "decliners": 1333,
            "unchanged": 146,
            "eligible_count": 2636,
            "breadth_ratio": 0.4647,
            "source_refs": ["breadth:all"],
        },
        "breadth_by_scope": [
            {
                "scope": scope,
                "breadth": {
                    "availability": "AVAILABLE",
                    "advancers": advance,
                    "decliners": decline,
                    "unchanged": unchanged,
                    "eligible_count": advance + decline + unchanged,
                    "breadth_ratio": advance / (advance + decline),
                    "source_refs": [f"breadth:{scope}"],
                },
            }
            for scope, advance, decline, unchanged in (
                ("KOSPI", 317, 539, 50),
                ("KOSDAQ", 840, 794, 96),
            )
        ],
        "size_context": [
            {
                "name": name,
                "return_pct": value,
                "basis": "official_size_index",
                "as_of_date": session,
                "source_ref": f"size:KOSPI:{name}",
            }
            for name, value in (
                ("대형주", 1.66),
                ("중형주", 0.22),
                ("소형주", -0.13),
            )
        ],
        "sectors": [
            {
                "name": name,
                "return_pct": value,
                "basis": "actual_sector_breadth",
                "source_ref": f"sector:{scope}:{name}",
                "market_scope": scope,
                "listed_count": listed,
            }
            for scope, name, value, listed in (
                ("KOSDAQ", "KOSDAQ 100", 1.94, 100),
                ("KOSDAQ", "KOSDAQ MID 300", 0.76, 299),
                ("KOSDAQ", "KOSDAQ SMALL", 0.44, 1341),
                ("KOSPI", "전기/전자", 2.62, 81),
                ("KOSPI", "유통", -2.36, 62),
                ("KOSPI", "화학", 0.18, 123),
                ("KOSDAQ", "금융", 3.21, 101),
                ("KOSDAQ", "오락/문화", -1.29, 53),
                ("KOSDAQ", "금속", 0.35, 65),
            )
        ],
        "market_flows": [
            {
                "participant": actor,
                "net_flow": amount,
                "unit": "KRW",
                "scope": scope,
                "as_of_date": session,
                "source_ref": f"flow:{scope}:{actor}",
            }
            for scope, actor, amount in (
                ("KOSPI", "foreign", 668_800_000_000),
                ("KOSPI", "institution", 540_300_000_000),
                ("KOSPI", "retail", -2_793_400_000_000),
                ("KOSDAQ", "foreign", 94_200_000_000),
                ("KOSDAQ", "institution", 61_200_000_000),
                ("KOSDAQ", "retail", -156_600_000_000),
            )
        ],
        "concentration": [],
        "deterministic_relations": [],
        "session_context": {
            "role": "after_hours",
            "assessment_state": "final",
            "market_date": session,
            "latest_completed_regular_session_date": session,
            "timezone": "Asia/Seoul",
            "provider_publication_state": "PROVIDER_COMPLETE",
        },
        "data_gaps": [],
    }


def _fallback_text(context: dict[str, object]) -> str:
    plan = build_kr_market_digest_plan(context)
    return "\n".join(claim.text for claim in plan.claims())


def test_run42_plan_selects_all_size_rows_and_sector_extremes() -> None:
    plan = build_kr_market_digest_plan(_context())

    assert plan.size_style_state == KrDigestSelectionState.SELECTED_REQUIRED
    assert plan.sector_extremes_state == KrDigestSelectionState.SELECTED_REQUIRED
    assert plan.size_context is not None
    assert plan.sector_context is not None
    assert (
        "KOSPI 대형 +1.66% · 중형 +0.22% · 소형 -0.13%"
        in plan.size_context.text
    )
    assert "KOSDAQ100 +1.94% · MID300 +0.76% · SMALL +0.44%" in plan.size_context.text
    assert "업종 상대 강세: KOSPI 전기·전자 +2.62% · KOSDAQ 금융 +3.21%" in plan.sector_context.text
    assert "업종 상대 약세: KOSPI 유통 -2.36% · KOSDAQ 오락·문화 -1.29%" in plan.sector_context.text
    assert "leader" not in plan.sector_context.text.casefold()
    assert "laggard" not in plan.sector_context.text.casefold()


def test_incomplete_size_market_is_omitted_without_fabrication() -> None:
    context = _context()
    context["size_context"] = context["size_context"][:2]

    plan = build_kr_market_digest_plan(context)

    assert plan.size_style_state == KrDigestSelectionState.SELECTED_REQUIRED
    assert plan.size_context is not None
    assert "KOSPI 대형" not in plan.size_context.text
    assert "KOSDAQ100 +1.94%" in plan.size_context.text


def test_wrong_session_size_rows_are_not_carried_forward() -> None:
    context = _context()
    for item in context["size_context"]:
        item["as_of_date"] = "2026-08-26"
    context["sectors"] = [
        item
        for item in context["sectors"]
        if not str(item["name"]).startswith("KOSDAQ ")
    ]

    plan = build_kr_market_digest_plan(context)

    assert plan.size_context is None
    assert plan.size_style_state == KrDigestSelectionState.WRONG_SESSION


@pytest.mark.parametrize(
    ("strongest", "weakest"),
    [((2.0, 1.0), (0.8, 0.2)), ((-0.2, -1.0), (-0.3, -1.5))],
)
def test_sector_labels_remain_relative_for_same_sign_markets(
    strongest: tuple[float, float],
    weakest: tuple[float, float],
) -> None:
    context = _context()
    sectors = [
        item
        for item in context["sectors"]
        if not str(item["name"]).startswith("KOSDAQ ")
    ]
    for item in sectors:
        if item["name"] in {"전기/전자", "금융"}:
            item["return_pct"] = strongest[0 if item["market_scope"] == "KOSPI" else 1]
        elif item["name"] in {"유통", "오락/문화"}:
            item["return_pct"] = weakest[0 if item["market_scope"] == "KOSPI" else 1]
        else:
            high = strongest[0 if item["market_scope"] == "KOSPI" else 1]
            low = weakest[0 if item["market_scope"] == "KOSPI" else 1]
            item["return_pct"] = (high + low) / 2
    context["sectors"] = sectors

    claim = build_kr_market_digest_plan(context).sector_context

    assert claim is not None
    assert "업종 상대 강세" in claim.text
    assert "업종 상대 약세" in claim.text


def test_one_sector_market_unavailable_renders_only_safe_market() -> None:
    context = _context()
    context["sectors"] = [
        item for item in context["sectors"] if item["market_scope"] == "KOSPI"
    ]

    plan = build_kr_market_digest_plan(context)

    assert plan.sector_extremes_state == KrDigestSelectionState.SELECTED_REQUIRED
    assert plan.sector_context is not None
    assert "KOSPI 전기·전자 +2.62%" in plan.sector_context.text
    assert "KOSDAQ 금융" not in plan.sector_context.text


def test_stale_completed_session_disables_required_slots() -> None:
    context = _context()
    context["session_context"]["latest_completed_regular_session_date"] = "2026-08-26"

    plan = build_kr_market_digest_plan(context)

    assert plan.richness.status is False
    assert plan.size_style_state == KrDigestSelectionState.SOURCE_UNAVAILABLE
    assert plan.sector_extremes_state == KrDigestSelectionState.SOURCE_UNAVAILABLE
    assert plan.size_context is None
    assert plan.sector_context is None


def test_old_run42_message_fails_new_required_consumption_policy() -> None:
    plan = build_kr_market_digest_plan(_context())

    result = validate_kr_market_evidence_utilization(
        plan,
        rendered_text=OLD_RUN42_MESSAGE,
    )

    assert result.status == "FAIL"
    assert result.counters["SIZE_STYLE_AVAILABLE_BUT_OMITTED"] == 1
    assert result.counters["SECTOR_EXTREMES_AVAILABLE_BUT_OMITTED"] == 1


def test_repaired_ai_and_fallback_consume_the_same_required_plan() -> None:
    context = _context()
    fallback = _fallback_text(context)
    candidate = build_production_candidate(
        OLD_RUN42_MESSAGE,
        deterministic_text=fallback,
        message_key="market:run42-size-sector-replay",
        market="kr",
        packet_owner="packet:run42",
        is_market_digest=True,
        market_context={"adapter_context": context},
    )

    assert candidate.eligible is True
    assert candidate.quality_v2 is not None
    assert candidate.quality_v2["kr_market_digest"]["utilization"]["status"] == "PASS"
    for marker in (
        "KOSPI 대형 +1.66% · 중형 +0.22% · 소형 -0.13%",
        "KOSDAQ100 +1.94% · MID300 +0.76% · SMALL +0.44%",
        "업종 상대 강세: KOSPI 전기·전자 +2.62% · KOSDAQ 금융 +3.21%",
        "업종 상대 약세: KOSPI 유통 -2.36% · KOSDAQ 오락·문화 -1.29%",
    ):
        assert marker in fallback
        assert marker in candidate.candidate_text
    assert "미국 반도체" not in candidate.candidate_text
