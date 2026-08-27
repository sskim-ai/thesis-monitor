# 2026-08-27 US Morning Evidence Utilization

## Materiality Classification

| Fact | Packet | AI review | Final digest | Classification |
|---|---|---|---|---|
| SPY | present/current | absent | absent | MESSAGE_OMITTED_MATERIAL_LOSS |
| QQQ | present/current | absent | absent | MESSAGE_OMITTED_MATERIAL_LOSS |
| IWM | present/current | absent | absent | MESSAGE_OMITTED_MATERIAL_LOSS |
| SOXX | present/current | absent | absent | MESSAGE_OMITTED_MATERIAL_LOSS |
| RSP | present/current | absent | absent | MESSAGE_OMITTED_MATERIAL_LOSS |
| XLI leader | present/current | absent | absent | MESSAGE_OMITTED_MATERIAL_LOSS |
| XLV laggard | present/current | absent | absent | MESSAGE_OMITTED_MATERIAL_LOSS |
| Nasdaq breadth state | unavailable | missing stated in long AI review | absent | MESSAGE_OMITTED_SAFE |
| 10Y nominal | present, 8/25 | used | absent | MESSAGE_OMITTED_SAFE |
| 10Y real | present, 8/25 | used | used/date-labeled | MESSAGE_USED |
| VIX | present, 8/25 | absent | absent | MESSAGE_OMITTED_SAFE |
| WTI | present, 8/25 | used | absent | MESSAGE_OMITTED_SAFE |
| USD/KRW | lagging/reference | absent | absent | MESSAGE_OMITTED_SAFE |

The digest does not need every available field. The defect is the complete loss of the completed-session market cross-section: all five required core ETF/style facts and both material sector extremes disappeared, while an older-dated macro observation became the only exact market fact delivered.

## Root Cause Boundary

Acquisition, temporal normalization, numeric registration, and packet persistence all passed. The loss happened in downstream market evidence selection/rendering. The deterministic fallback shares the omission, so switching routes would not have restored it.

```text
US_MARKET_DIGEST_MATERIAL_INFORMATION_LOSS = 7
OPEN_MATERIAL_P1 = us_current_session_market_evidence_omitted_from_natural_digest
```

This is a bounded consumption/rendering repair candidate. No repair is made in this review.
