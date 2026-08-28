# 2026-08-29 US Morning Review Summary

| Item | Result |
| --- | --- |
| US target session | 2026-08-28 |
| SPY | -0.23% |
| QQQ | -0.65% |
| IWM | -1.35% |
| SOXX | -3.20% |
| RSP | -0.34% |
| Participation/style | 동일가중도 같은 방향으로 하락했지만 SPY보다 0.12%p 약했고, QQQ와 IWM도 SPY를 하회해 대형주 방어가 상대적으로 나았던 혼합·좁은 참여였습니다. RSP는 참여 스타일 프록시이며 공식 거래소 breadth가 아닙니다. |
| Semiconductor relative | RELATIVE_WEAKNESS (-2.9724pp vs SPY) |
| Top 3 sectors | XLC +1.42%, XLY +1.15%, XLE +0.63% |
| Bottom 3 sectors | XLK -1.55%, XLU -1.04%, XLI -0.93% |
| Nasdaq breadth | PUBLICATION_PENDING; latest official 2026-08-26 |
| KOSPI200 night | NOT_READY; omitted |
| KOSDAQ150 night | NOT_READY; omitted |
| Macro selected | none |
| Natural run | FOUND; run 45; parity PASS |

## Final Gates

```json
{
  "AI_CALCULATED_INDEX_RETURN": 0,
  "AI_DERIVED_SECTOR_RANKING": 0,
  "AI_FALLBACK_INDEX_NUMERIC_PARITY": "PASS",
  "AI_FALLBACK_NIGHT_FUTURES_PARITY": "PASS",
  "AI_FALLBACK_SECTOR_NUMERIC_PARITY": "PASS",
  "AI_FALLBACK_TEMPORAL_PARITY": "PASS",
  "EXECUTION_TIME_KST": "2026-08-29T08:27:23+09:00",
  "EXPECTED_NIGHT_FUTURES_SESSION": "2026-08-29",
  "GENERIC_NO_CHANGE_MACRO_SECTION_VISIBLE": 0,
  "IWM": "-1.35%",
  "IWM_CURRENT": "PASS",
  "KOSDAQ150_NIGHT_FUTURES": "UNAVAILABLE",
  "KOSDAQ150_NIGHT_FUTURES_STATE": "NOT_READY",
  "KOSPI200_NIGHT_FUTURES": "UNAVAILABLE",
  "KOSPI200_NIGHT_FUTURES_STATE": "NOT_READY",
  "LATEST_COMPLETED_US_SESSION": "2026-08-28",
  "LATEST_COMPLETED_US_SESSION_RESOLVED": "PASS",
  "MACRO_SELECTED_FACTS": [],
  "MALFORMED_ZERO_CHANGE_KOREAN": 0,
  "NASDAQ_BREADTH_SOURCE_SESSION": "2026-08-26",
  "NASDAQ_BREADTH_STATE": "PUBLICATION_PENDING",
  "NATURAL_US_MORNING_MESSAGE_EVIDENCE_PARITY": "PASS",
  "NATURAL_US_MORNING_PACKET_ID": "2026-08-29-us-run-45-0e9c491532df",
  "NATURAL_US_MORNING_RUN": "FOUND",
  "NATURAL_US_MORNING_RUN_ID": 45,
  "NEXT_ACTION": "BOUNDED_REPAIR",
  "NIGHT_FUTURES_CANONICAL_GATE_USED": "PASS",
  "NIGHT_FUTURES_SESSION_MAPPING": "PASS",
  "NYSE_BREADTH": "UNAVAILABLE",
  "OPEN_MATERIAL_P1": 1,
  "OPEN_P0": 0,
  "PARTICIPATION_STYLE_SUMMARY": "동일가중도 같은 방향으로 하락했지만 SPY보다 0.12%p 약했고, QQQ와 IWM도 SPY를 하회해 대형주 방어가 상대적으로 나았던 혼합·좁은 참여였습니다. RSP는 참여 스타일 프록시이며 공식 거래소 breadth가 아닙니다.",
  "QQQ": "-0.65%",
  "QQQ_CURRENT": "PASS",
  "RAW_SUMMARY_NIGHT_FUTURES_BYPASS": 0,
  "RSP": "-0.34%",
  "RSP_CURRENT": "PASS",
  "SECTOR_CURRENT_SESSION_COUNT": 11,
  "SECTOR_TOP3_STRONG": [
    "XLC +1.42%",
    "XLY +1.15%",
    "XLE +0.63%"
  ],
  "SECTOR_TOP3_WEAK": [
    "XLK -1.55%",
    "XLU -1.04%",
    "XLI -0.93%"
  ],
  "SEMICONDUCTOR_RELATIVE_SPREAD_VS_SPY": "-2.9724pp",
  "SEMICONDUCTOR_RELATIVE_STATE": "RELATIVE_WEAKNESS",
  "SOXX": "-3.20%",
  "SOXX_CURRENT": "PASS",
  "SPY": "-0.23%",
  "SPY_CURRENT": "PASS",
  "STALE_MACRO_AS_CURRENT": 0,
  "STALE_NASDAQ_BREADTH_AS_CURRENT": 0,
  "STALE_NIGHT_FUTURES_VISIBLE": 0,
  "US_MORNING_DATA_REVIEW": "PARTIAL_SAFE"
}
```

The review is `PARTIAL_SAFE`: hard market-data, temporal-safety, renderer, and natural-message parity gates pass. One material P1 remains in the rejected full-stock AI candidate and requires a separate bounded repair; production delivery already completed safely through the deterministic route.
