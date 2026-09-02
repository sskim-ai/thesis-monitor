# US Treasury Observation Pair

Read-only official FRED extraction was bounded to the run-51 point-in-time window. The latest safe date is `2026-08-31`; the immediately previous non-missing same-series date is `2026-08-28`.

| Series | Current | Previous | Delta |
| --- | ---: | ---: | ---: |
| `DGS3` | 4.40% | 4.41% | -1bp |
| `DGS5` | 4.49% | 4.48% | +1bp |
| `DGS10` | 4.75% | 4.73% | +2bp |
| `DGS30` | 5.25% | 5.22% | +3bp |

All deltas satisfy `(current - previous) * 100` within display precision. The section header says `08/31 관측`; it never says `오늘`. The raw public CSV SHA-256 is recorded in the machine-readable fixture.

`UST_OBSERVATION_PAIR_VALID = PASS`

`LAGGED_UST_DATA_LABELED_SAME_DAY = 0`

`UST_DELTA_RENDERED_AS_PERCENT_RETURN = 0`
