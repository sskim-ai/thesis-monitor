# 2026-08-25 KR Macro Temporal Natural Review

| Metric | Observation date | Eligibility as-of | Temporal role | Important change | Today signal | Actual wording |
| --- | --- | --- | --- | --- | --- | --- |
| SOXX | 2026-08-24 | 2026-08-24T23:05:03.509538+00:00 | CURRENT_OBSERVATION | True | True | 반도체가 S&P500을 2.4%p 밑돌았습니다. |
| QQQ | 2026-08-24 | 2026-08-24T23:05:03.509538+00:00 | CURRENT_OBSERVATION | True | True | Nasdaq이 S&P500을 0.7%p 밑돌아 성장주 주도력이 약했습니다. |
| DFII10 | 2026-08-21 | 2026-08-24T23:05:03.509538+00:00 | CURRENT_OBSERVATION | True | True | 미국 실질금리가 +5bp 움직였습니다. |

All three macro changes actually rendered in the digest were `CURRENT_OBSERVATION` and newly
eligible since the previous briefing. Reference-only `USDKRW` and lagging oil facts did not create an
important-change/today-signal claim.

- False-current claims: `0`
- Legacy missing metadata defaulted current: `0`
- Reference-only today signals: `0`
- `MACRO_TEMPORAL_KR_NATURAL = LIVE_PASS`
