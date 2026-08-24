# Shadow Investor-Flow Registry Negative Controls

| Control | Result |
|---|---|
| Exact 30 reconciliation paths per stock | PASS |
| Actor identity preserved | PASS |
| 1d/5d/20d window identity preserved | PASS |
| Reconciliation prose eligibility | 0 |
| Binder accepts audit-only field as prose | 0 |
| Newly appearing unknown path | fail-closed |
| Wildcard/blanket registration | 0 |
| Residual-derived participant attribution | 0 |

The AI claim gate was not relaxed. The registry repair only changes known reconciliation fields from
unsupported to registered non-prose evidence; unknown paths continue to block shadow readiness.
