# KR Pre-Enable Market Digest Plan

Packet `2026-08-27-kr-run-42-5d8d23e6fbd6` reuses the shared `kr-market-digest-quality-v1` plan. The plan keeps index and
breadth judgment first, aggregate participant flow second, then the six size/style returns and four
bounded sector extrema. Global context is not retained in the AI candidate.

```json
{
  "contract": "kr-market-digest-quality-v1",
  "richness": {
    "contract": "kr-market-digest-quality-v1",
    "status": true,
    "completed_session": true,
    "kospi_kosdaq_indices": true,
    "kospi_kosdaq_breadth": true,
    "supporting_local_context": [
      "market_wide_participant_flow",
      "size_style_context",
      "sector_context"
    ],
    "reasons": []
  },
  "judgment": {
    "role": "judgment",
    "text": "KOSPI와 KOSDAQ의 지수 방향과 시장 폭이 엇갈려 국내 장을 하나의 방향으로 묶기 어렵습니다.",
    "priority": "P1_KR_LOCAL_MARKET_STRUCTURE",
    "source_refs": [
      "kiwoom:ka20001:KOSPI:2026-08-27",
      "kiwoom:ka20001:KOSDAQ:2026-08-27",
      "cross-section:KIWOOM_REST:breadth:KOSPI",
      "cross-section:KIWOOM_REST:breadth:KOSDAQ"
    ]
  },
  "interpretation": {
    "role": "interpretation",
    "text": "외국인은 양 시장에서 순매수했습니다. 기관은 양 시장에서 순매수했습니다. 개인은 양 시장에서 순매도했습니다.",
    "priority": "P2_KR_LOCAL_MARKET_FLOW",
    "source_refs": [
      "kiwoom:ka10051:KOSPI:foreign:2026-08-27",
      "kiwoom:ka10051:KOSPI:institution:2026-08-27",
      "kiwoom:ka10051:KOSPI:retail:2026-08-27",
      "kiwoom:ka10051:KOSDAQ:foreign:2026-08-27",
      "kiwoom:ka10051:KOSDAQ:institution:2026-08-27",
      "kiwoom:ka10051:KOSDAQ:retail:2026-08-27"
    ]
  },
  "size_context": {
    "role": "size_context",
    "text": "규모별: KOSPI 대형 +1.66% · 중형 +0.22% · 소형 -0.13%; KOSDAQ100 +1.94% · MID300 +0.76% · SMALL +0.44%.",
    "priority": "P1_KR_LOCAL_MARKET_STRUCTURE",
    "source_refs": [
      "kiwoom:ka20003:KOSPI:002:2026-08-27",
      "kiwoom:ka20003:KOSPI:003:2026-08-27",
      "kiwoom:ka20003:KOSPI:004:2026-08-27",
      "kiwoom:ka20003:KOSDAQ:138:2026-08-27",
      "kiwoom:ka20003:KOSDAQ:139:2026-08-27",
      "kiwoom:ka20003:KOSDAQ:140:2026-08-27"
    ]
  },
  "sector_context": {
    "role": "sector_context",
    "text": "업종 상대 강세: KOSPI 전기·전자 +2.62% · KOSDAQ 금융 +3.21%. 업종 상대 약세: KOSPI 유통 -2.36% · KOSDAQ 오락·문화 -1.29%.",
    "priority": "P3_KR_LOCAL_STOCK_CROSS_SECTION",
    "source_refs": [
      "kiwoom:ka20003:KOSPI:013:2026-08-27",
      "kiwoom:ka20003:KOSPI:016:2026-08-27",
      "kiwoom:ka20003:KOSDAQ:111:2026-08-27",
      "kiwoom:ka20003:KOSDAQ:141:2026-08-27"
    ]
  },
  "next_check": {
    "role": "next_check",
    "text": "양 시장의 상승·하락 종목 분포와 외국인·기관의 시장별 수급 방향이 함께 유지되는지 확인합니다.",
    "priority": "P2_KR_LOCAL_MARKET_FLOW",
    "source_refs": [
      "kiwoom:ka20001:KOSPI:2026-08-27",
      "kiwoom:ka20001:KOSDAQ:2026-08-27",
      "cross-section:KIWOOM_REST:breadth:KOSPI",
      "cross-section:KIWOOM_REST:breadth:KOSDAQ",
      "kiwoom:ka10051:KOSPI:foreign:2026-08-27",
      "kiwoom:ka10051:KOSPI:institution:2026-08-27",
      "kiwoom:ka10051:KOSPI:retail:2026-08-27",
      "kiwoom:ka10051:KOSDAQ:foreign:2026-08-27",
      "kiwoom:ka10051:KOSDAQ:institution:2026-08-27",
      "kiwoom:ka10051:KOSDAQ:retail:2026-08-27"
    ]
  },
  "size_style_state": "SELECTED_REQUIRED",
  "sector_extremes_state": "SELECTED_REQUIRED",
  "global_context_retained": false,
  "global_context_reason": "no_material_global_contradiction_required",
  "concentration_scopes_used": []
}
```

`KR_LOCAL_FIRST_PLAN = PASS`
