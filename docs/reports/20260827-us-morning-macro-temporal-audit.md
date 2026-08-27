# 2026-08-27 US Morning Macro Temporal Audit

## Canonical Macro Facts

`CURRENT_OBSERVATION` means a newly available official occurrence at packet cutoff; it does not silently rewrite the observation date to the target equity session.

| Fact | Value / change | Observation | Temporal role | Today signal | Delivered use |
|---|---|---|---|---|---|
| US 10Y nominal | 4.64%, -6bp | 2026-08-25 | CURRENT_OBSERVATION | yes | omitted safely |
| US 10Y real | 2.32%, -6bp | 2026-08-25 | CURRENT_OBSERVATION | yes | used with explicit `(8/25)` |
| VIX | 15.45, -2.5237% | 2026-08-25 | CURRENT_OBSERVATION | yes | omitted safely |
| WTI | $83.90, -2.9833% | 2026-08-25 | CURRENT_OBSERVATION | yes | omitted safely |
| USD/KRW | 1384.8, -0.0938% | 2026-08-26 | REFERENCE_LAGGING | no | omitted safely |
| Broad dollar | 118.0628, -0.7065% | 2026-08-21 | REFERENCE_LAGGING | no | omitted safely |
| 10Y breakeven | 2.32%, 0bp | 2026-08-26 | CURRENT_OBSERVATION | yes | omitted safely |
| HY spread | 2.70%, +1bp | 2026-08-25 | CURRENT_OBSERVATION | yes | omitted safely |

Every packet summary item resolves an observation date, temporal role, and `today_signal_eligible` state. The exact delivery's only macro numeric is explicitly date-qualified. It contains no “today VIX,” “today oil,” or FX session-equivalence claim.

```text
MACRO_TEMPORAL_BOUNDARY = PASS
SUMMARY_ITEM_WITHOUT_TEMPORAL_BINDING = 0
PRIOR_YIELD_AS_TODAY = 0
STALE_YIELD_AS_CURRENT = 0
PRIOR_VIX_AS_TODAY = 0
STALE_VIX_AS_CURRENT = 0
LAGGING_WTI_AS_TODAY = 0
STALE_OIL_CAUSAL_CLAIM = 0
FX_SESSION_BASIS_CONFLICT = 0
STALE_MACRO_AS_CURRENT = 0
TEMPORAL_LANGUAGE_WITHOUT_CURRENT_EVIDENCE = 0
```
