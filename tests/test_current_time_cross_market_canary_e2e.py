import json

from scripts.current_time_cross_market_canary_e2e import (
    _market_quality,
    _render_current_kr_market,
    _stock_quality,
)


def _kr_market_fixture(tmp_path):
    archive = {
        "responses": [
            {
                "api_id": "ka20003",
                "request": {"inds_cd": "001"},
                "payload": {
                    "all_inds_idex": [
                        {"stk_nm": "화학", "flu_rt": "+3.83"},
                        {"stk_nm": "섬유/의류", "flu_rt": "+3.09"},
                        {"stk_nm": "음식료/담배", "flu_rt": "+2.68"},
                        {"stk_nm": "전기/전자", "flu_rt": "-3.19"},
                        {"stk_nm": "전기/가스", "flu_rt": "-3.06"},
                        {"stk_nm": "제약", "flu_rt": "-3.01"},
                    ]
                },
            },
            {
                "api_id": "ka20003",
                "request": {"inds_cd": "101"},
                "payload": {
                    "all_inds_idex": [
                        {"stk_nm": "KOSDAQ 100", "flu_rt": "-0.23"},
                        {"stk_nm": "KOSDAQ MID 300", "flu_rt": "+0.44"},
                        {"stk_nm": "KOSDAQ SMALL", "flu_rt": "+0.58"},
                        {"stk_nm": "유통", "flu_rt": "+3.09"},
                        {"stk_nm": "제약", "flu_rt": "+2.05"},
                        {"stk_nm": "IT 서비스", "flu_rt": "+1.81"},
                        {"stk_nm": "기계/장비", "flu_rt": "-1.66"},
                        {"stk_nm": "전기/전자", "flu_rt": "-1.51"},
                        {"stk_nm": "코스닥 중견기업", "flu_rt": "-0.84"},
                        {"stk_nm": "비금속", "flu_rt": "-0.81"},
                    ]
                },
            },
        ]
    }
    archive_path = tmp_path / "kr-market-archive.json"
    archive_path.write_text(json.dumps(archive), encoding="utf-8")
    breadth = {
        "advance_count": 10,
        "decline_count": 5,
        "unchanged_count": 1,
        "ad_ratio": 2.0,
    }
    flows = [
        {"market": market, "actor": actor, "net_buy_amount": value}
        for market in ("KOSPI", "KOSDAQ")
        for actor, value in (
            ("foreign", -1_000_000_000_000),
            ("institution", -200_000_000_000),
            ("retail", 300_000_000_000),
        )
    ]
    return {
        "session_date": "2026-08-28",
        "archive_path": str(archive_path),
        "indices": [
            {"symbol": "KOSPI", "close": 6788.88, "return_pct": -1.79},
            {"symbol": "KOSDAQ", "close": 838.41, "return_pct": 0.09},
        ],
        "breadth_by_scope": [
            {"scope": "KOSPI", "breadth": breadth},
            {"scope": "KOSDAQ", "breadth": breadth},
        ],
        "market_flows": flows,
        "size_context": [
            {"sector": "대형주", "return_pct": -2.04},
            {"sector": "중형주", "return_pct": 1.05},
            {"sector": "소형주", "return_pct": 1.23},
        ],
    }


def test_fresh_kr_market_renderer_keeps_required_blocks_and_real_sectors(tmp_path):
    message = _render_current_kr_market(_kr_market_fixture(tmp_path))

    assert _market_quality("KR_MARKET", message) == []
    assert "KOSPI 6,788.88 · -1.79%" in message
    assert "KOSDAQ 838.41 · +0.09%" in message
    assert "코스닥 중견기업" not in message
    assert "비금속 -0.81%" in message
    assert "보조 시장환경" not in message


def test_market_quality_rejects_price_structure():
    message = "\n".join(
        (
            "🇰🇷 한국시장 마감",
            "📈 주요 지수",
            "🔎 시장 내부",
            "💰 투자자 수급",
            "📊 규모/스타일",
            "🏭 업종 강세 TOP3",
            "📉 업종 약세 TOP3",
            "가격 구조",
        )
    )

    assert "forbidden:가격 구조" in _market_quality("KR_MARKET", message)


def test_stock_quality_separates_reasoning_confidence_timing_and_polarity():
    message = "\n".join(
        (
            "AI 종합 판단: HOLD",
            "추론등급: 매우 높음",
            "판단 확신도: 중간",
            "단기 타이밍: 중립",
            "✅ BUY 쪽 근거:",
            "⚠️ SELL 쪽 근거:",
            "🔼 상향 조건:",
            "🔽 하향 조건:",
        )
    )

    assert _stock_quality(message, "HOLD") == []
