# 2026-08-28 US Morning Macro Temporal Audit

| Series | Value | Backend change | Observation | Temporal role | Today eligible | Final digest |
|---|---:|---:|---|---|---|---|
| DGS10 | 4.66% | +2 bp | 2026-08-26 | `CURRENT_OBSERVATION` | yes | omitted |
| DFII10 | 2.34% | +2 bp | 2026-08-26 | `CURRENT_OBSERVATION` | yes | omitted |
| VIXCLS | 15.21 | -1.5534% | 2026-08-26 | `CURRENT_OBSERVATION` | yes | omitted |
| DCOILWTICO | $83.90 | -2.9833% | 2026-08-25 | `REFERENCE_LAGGING` | no | omitted |
| USDKRW | 1380.9 | -0.2816% | 2026-08-27 | `REFERENCE_LAGGING` | no | omitted |
| DTWEXBGS | 118.0628 | -0.7065% | 2026-08-21 | `REFERENCE_LAGGING` | no | omitted |

The AI review used DFII10 only as structured portfolio context and did not render it in the final market digest. WTI, USD/KRW, and the broad dollar index were denied current-direction ownership by the temporal contract. The deterministic fallback retained only bounded macro context; it did not phrase lagging WTI, FX, or dollar data as today's move.

```text
MACRO_TEMPORAL_BOUNDARY = PASS
SUMMARY_ITEM_WITHOUT_TEMPORAL_BINDING = 0
PRIOR_YIELD_AS_TODAY = 0
PRIOR_VIX_AS_TODAY = 0
LAGGING_WTI_AS_TODAY = 0
FX_SESSION_BASIS_CONFLICT = 0
STALE_MACRO_AS_CURRENT = 0
TEMPORAL_LANGUAGE_WITHOUT_CURRENT_EVIDENCE = 0
```
