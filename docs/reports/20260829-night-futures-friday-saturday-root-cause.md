# Night Futures Friday-to-Saturday Root Cause

## Decision

`NIGHT_FUTURES_ROOT_CAUSE = UPSTREAM_NOT_PUBLISHED`

The official KRX `fut_bydd_trd` endpoint uses `BAS_DD` as the night-session end business date. The 2026-08-28 night rows reconcile exactly to the 2026-08-27 regular close, while the required Friday-night-to-Saturday economic session would need `BAS_DD=2026-08-29`. The official endpoint returned HTTP 200 with zero rows for that date.

| Contract | Night BAS_DD | Reference DAY | Derived | Provider | Match |
| --- | --- | --- | --- | --- | --- |
| A0669000 | 20260828 | 20260827 | 11.6 | 11.6 | True |
| A0169000 | 20260828 | 20260827 | -8.0 | -8.0 | True |

This is not a normalizer defect and changing the expected date to Friday would relabel the Thursday-night-to-Friday session as current. The existing fail-closed omission remains correct.
