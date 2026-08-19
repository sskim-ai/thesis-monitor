# Night Futures Holiday Traversal Audit

Observed: `2026-08-19 KST`

## Historical Holiday Pair

XKRX calendar evidence:

| Date | Session |
|---|---|
| 2026-08-18 | yes |
| 2026-08-17 | no |
| 2026-08-16 | no |
| 2026-08-15 | no |
| 2026-08-14 | yes |

The authoritative predecessor of 2026-08-18 is therefore 2026-08-14.

| Instrument | NIGHT | Contract | Selected DAY | DAY price | NIGHT price | Derived | Provider audit |
|---|---|---|---|---:|---:|---:|---:|
| KOSPI200 | 2026-08-18 | `A0169000` | 2026-08-14 | 1098.90 | 1094.95 | -3.95 / -0.35945036% | -3.95, match |
| KOSDAQ150 | 2026-08-18 | `A0669000` | 2026-08-14 | 1487.50 | 1477.30 | -10.20 / -0.68571429% | -10.20, match |

NIGHT payload SHA256:
`2c6b0d1d66ca52c84f484b846fd89454931c2d97ba80eb07342b5982340d28a0`

DAY payload SHA256:
`49dad52cf69264c1ec9de80c0d3bd9af6fc8d5649b4b55edc1145ffafbe5c15c`

## Ordinary-Session Control

| Instrument | NIGHT | Selected DAY | Contract | Derived | Provider audit |
|---|---|---|---|---:|---:|
| KOSPI200 | 2026-08-14 | 2026-08-13 | `A0169000` | +21.70 / +2.02104871% | +21.70, match |
| KOSDAQ150 | 2026-08-14 | 2026-08-13 | `A0669000` | +12.30 / +0.82% | +12.30, match |

## Negative Controls

| Control | Result |
|---|---|
| 2026-08-18 NIGHT -> 2026-08-18 DAY | rejected |
| future DAY row only | rejected |
| weekend / 2026-08-17 holiday | skipped by XKRX calendar |
| multi-day closure | latest prior XKRX session selected |
| different contract/maturity | unavailable, no older reconnect |
| missing/zero reference | unavailable |
| provider raw change conflict | unavailable |
| expected current NIGHT empty | older valid pair remains stale |

## Current Readiness

The read-only live probe queried 2026-08-19 back through 2026-08-14. The 2026-08-19 response still
contained zero rows. Both instruments therefore remain `PROVIDER_DATA_PENDING` for current
exposure. The 2026-08-18 historical pair is now reconstructable, but its freshness is `stale` against
the expected 2026-08-19 session and it is suppressed from user-visible output.

| Instrument | Historical pair | Current status | Current display |
|---|---|---|---|
| KOSPI200 | PASS | `PROVIDER_DATA_PENDING` | suppressed |
| KOSDAQ150 | PASS | `PROVIDER_DATA_PENDING` | suppressed |

Historical proof and current readiness are deliberately separate.
