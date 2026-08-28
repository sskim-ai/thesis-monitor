# 2026-08-29 US Macro Temporal Context

| Series | Value | Change | Observation | Temporal role | Today eligible | Source |
| --- | --- | --- | --- | --- | --- | --- |
| DGS10 | 4.67 percent | +1bp | 2026-08-27 | CURRENT_OBSERVATION | True | fred |
| DFII10 | 2.34 percent | +0bp | 2026-08-27 | CURRENT_OBSERVATION | True | fred |
| T10YIE | 2.31 percent | -2bp | 2026-08-28 | CURRENT_OBSERVATION | True | fred |
| BAMLH0A0HYM2 | 2.63 percent | -4bp | 2026-08-27 | CURRENT_OBSERVATION | True | fred |
| VIXCLS | 14.51 index | -4.60% | 2026-08-27 | CURRENT_OBSERVATION | True | fred |
| DCOILWTICO | 83.9 usd_per_barrel | -2.98% | 2026-08-25 | REFERENCE_LAGGING | False | fred |
| USDKRW | 1372.5 원 | -0.61% | 2026-08-28 | REFERENCE_LAGGING | False | ecos |
| DTWEXBGS | 118.0628 index | -0.71% | 2026-08-21 | REFERENCE_LAGGING | False | fred |

`MACRO_SELECTED_FACTS = []`. Current DGS10, DFII10, T10YIE, high-yield spread, and VIX observations were retained in evidence but none passed the existing additional-materiality selector. WTI, broad dollar, and USD/KRW remained reference-lagging. The user-facing macro section was safely omitted.
