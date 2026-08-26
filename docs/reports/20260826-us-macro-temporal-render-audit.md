# 2026-08-26 US Macro Temporal Render Audit

| Series | Observation | Role | Today-signal eligible | Replay behavior |
|---|---|---|---|---|
| DGS10 | 2026-08-24 | `CURRENT_OBSERVATION` by official release occurrence | true | if selected, prefix `공식 관측(8/24)` |
| DFII10 | 2026-08-24 | `CURRENT_OBSERVATION` by official release occurrence | true | if selected, prefix `공식 관측(8/24)` |
| VIXCLS | 2026-08-24 | `CURRENT_OBSERVATION` by official release occurrence | true | if selected, prefix `공식 관측(8/24)` |
| DCOILWTICO | 2026-08-18 | `REFERENCE_LAGGING` | false | suppressed from important changes |

Every rendered change is sourced from an observation carrying date, temporal role, and eligibility. Market-session prior items retain `직전 거래일(M/D)`; release-bound changes now retain `공식 관측(M/D)`. No value is called “today” solely because it was newly retrieved.

```text
PRIOR_VIX_AS_TODAY = 0
PRIOR_YIELD_AS_TODAY = 0
LAGGING_WTI_AS_TODAY = 0
STALE_MACRO_AS_CURRENT = 0
AI_FALLBACK_TEMPORAL_POLICY_DIVERGENCE = 0
```
