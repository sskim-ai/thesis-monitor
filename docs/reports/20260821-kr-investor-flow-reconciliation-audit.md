# 2026-08-21 KR Investor-Flow Reconciliation Audit

Authoritative machine-readable evidence:
`20260821-kr-investor-flow-reconciliation.json`.

## Result

| Measure | Result |
|---|---:|
| Active KR tickers | 7 |
| Audited windows | 21 |
| Complete canonical windows | 21 |
| Full top-level net equal to zero | 21 |
| Institution diagnostic difference equal to zero | 21 |
| Material omitted-flow windows | 21 |
| Unsupported exclusive attribution before | 2 |
| Unsupported exclusive attribution after | 0 |
| Residual-derived participant | 0 |

The visible-three net is diagnostic only. In every observed window, named other-corporation and
domestic-foreign source fields supplied the offset. The implementation never names that offset from
arithmetic alone.

Five tickers had exact packet-versus-later-source equality. Samsung Electronics and Hanwha
Aerospace had later same-date provider occurrence corrections; the audit preserves both values and
does not rewrite run-31. Runtime canonicalization always combines participants from one response
occurrence.

Provider aggregate was unavailable, so the status is `complete_without_provider_total`, not a
fabricated aggregate validation. Optional aggregate exact-match and conflict paths are covered by
unit tests.
