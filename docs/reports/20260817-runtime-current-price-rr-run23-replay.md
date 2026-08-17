# Runtime Current-Price RR Run-23 Replay

## Replay Boundary

- Archive-only, read-only reconstruction
- Telegram sends: 0
- Pilot mutations: 0
- Database mutations: 0
- Source archive rewrites: 0

## Session Correction

2026-08-17 was not an XKRX trading session. The latest completed regular session was 2026-08-14, so the 2026-08-14 chart is fresh for this packet rather than stale.

## Ticker Results

| Ticker | Before | After | Current RR | Display | Fact | Numeric path |
|---|---|---|---:|---:|---|---|
| 000660 | UNAVAILABLE_BY_CONTRACT | UNAVAILABLE_BY_CONTRACT | N/A | N/A | no | no |
| 003690 | UNAVAILABLE_BY_CONTRACT | UNAVAILABLE_BY_CONTRACT | N/A | N/A | no | no |
| 005490 | BUG_MISSING_FACT | READY | 0.16778 | 0.17배 | yes | yes |
| 005930 | UNAVAILABLE_BY_CONTRACT | UNAVAILABLE_BY_CONTRACT | N/A | N/A | no | no |
| 010120 | BUG_MISSING_FACT | READY | 0.318131 | 0.32배 | yes | yes |
| 012450 | BUG_MISSING_FACT | READY | 0.152999 | 0.15배 | yes | yes |
| 086280 | BUG_MISSING_FACT | READY | 0.466189 | 0.47배 | yes | yes |

## Validator Replay

- RR missing-path errors in the immutable run-23 validation: 8
- RR missing-path errors after: 0
- Other current-contract replay errors after: 63
- The remaining replay errors are reported separately and are not treated as an RR repair failure.

## Result

The four calculated run-23 current-price RR values now have exact canonical Fact and numeric registry paths. Samsung Electronics, Korean Re, and SK hynix remain unavailable by contract and do not receive fabricated RR values.
