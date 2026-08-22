# Night-Futures Natural Publication Proof

## Expected session basis

`EXPECTED_SESSION_BASIS = PASS`

For the 2026-08-22 morning cycle, `night-futures-session-basis-v1` correctly expected NIGHT `2026-08-22` with preceding eligible XKRX DAY `2026-08-21`. Both products used September 2026 contracts: KOSPI200 `A0169000` and KOSDAQ150 `A0669000`.

## Production attempts

| Role | Time KST | HTTP | Returned dates | Raw / parsed | Candidates / ready | Per-product result | Terminal |
|---|---|---|---|---:|---:|---|---|
| attempt 1 | 08:06:27..08:06:28 | 200 | 2026-08-20, 2026-08-21 | 770 / 16 | 0 / 0 | both NOT_READY; returned NIGHT 08-21; expected absent | STALE_PRIOR_SESSION_PRESENT |
| attempt 2 | 08:10:07..08:10:08 | 200 | 2026-08-20, 2026-08-21 | 770 / 16 | 0 / 0 | same | STALE_PRIOR_SESSION_PRESENT |
| attempt 3 | 08:15:04..08:15:06 | 200 | 2026-08-20, 2026-08-21 | 770 / 16 | 0 / 0 | same | STALE_PRIOR_SESSION_PRESENT |
| attempt 4 | 08:20:05..08:20:07 | 200 | 2026-08-20, 2026-08-21 | 770 / 16 | 0 / 0 | same | STALE_PRIOR_SESSION_PRESENT |

Every attempt queried 08-22 (0 rows), 08-21 (385), and 08-20 (385). Parser and canonicalization were PASS. The common normalized raw SHA was `0c157d7abfc2a65a140cf0756b5b13745106e8168b8a364717416ede84e8d02e`; individual payload SHAs are in the JSON companion report. Provider-change cross-check was globally PASS, while expected-product cross-check remained NOT_OBSERVED because the expected session was absent. Production mutation and user-visible integration were both false.

## Natural observers

The LaunchAgent ran twice and exited 0, but both jobs returned:

```json
{"production_effect":0,"provider_calls":0,"reason":"not_normal_xkrx_session","status":"SKIPPED"}
```

- 08:45 observer: actual file birth `2026-08-22 08:45:05 KST`; no provider call, no archive attempt.
- 09:15 observer: log modification `2026-08-22 09:15:06 KST`; no provider call, no archive attempt.
- Root cause: the observer checks `is_exchange_session_date("XKRX", current.date())` before deriving the latest completed NIGHT session. Saturday morning is rejected even though Friday's NIGHT session is identified by Saturday's NIGHT BAS_DD.
- First observed availability interval for both products: `UNKNOWN_WITHIN_HORIZON`.

## Verdicts

`NIGHT_FUTURES_TELEMETRY_GAP = FAIL`

The production attempt archive is complete, but the required post-deadline observer evidence was not captured. This is a material P1 telemetry-plumbing failure, not a market-data correctness P0.

`DEADLINE_VERDICT = DEADLINE_UNPROVEN`

`FAIL_CLOSED_SAFETY = PASS`

`STALE_INTERNAL_ITEM_RISK = LOW`

The stale 08-21 pair remained internally visible as explicitly stale evidence, but was not promoted as the expected 08-22 pair. The actual market digest said the latest completed session could not be confirmed and excluded night futures from the opening signal. No wrong session pair, contract mismatch, fabricated current value, or unsafe user-visible output was found.
