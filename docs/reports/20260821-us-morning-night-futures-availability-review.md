# 2026-08-21 US Morning Night-Futures Availability Review

## 1. Morning summary impact

US packet `2026-08-21-us-run-30-5a3b7c1c4390` was generated at `08:20:05.452305 KST`. The latest completed NIGHT pair was not ready, so `night_futures=[]` in the market context and the actual digest stated that Korean night futures were excluded. No stale values were rendered.

Result:

```text
NIGHT_FUTURES_LATEST_AVAILABILITY = UNAVAILABLE_AT_DEADLINE
NIGHT_FUTURES_FAIL_CLOSED_SAFETY = PASS
```

## 2. Expected latest session

The morning gate recorded `expected_session=2026-08-21`. This is correct under `night-futures-session-basis-v1`: NIGHT `BAS_DD=2026-08-21` denotes the session from `2026-08-20 18:00` to `2026-08-21 06:00`, paired with preceding eligible XKRX DAY `2026-08-20`. The expected-date logic did not confuse wall-clock date with the preceding DAY basis.

## 3. Exact retry timeline

| Time KST | Attempt | Expected NIGHT | Provider result | Rows | Candidate products | Ready | Error | Classification |
|---|---:|---|---|---:|---:|---:|---|---|
| `08:06:30.294808` | 1 | `2026-08-21` | HTTP/raw not retained; no ready products | unknown | unknown | 0 | none | expected session unavailable |
| query time not retained; scheduler `08:10:05.483` | 2 | `2026-08-21` | HTTP/raw not retained; no ready products | unknown | unknown | 0 | none | expected session unavailable |
| query time not retained; scheduler `08:15:02.463` | 3 | `2026-08-21` | HTTP/raw not retained; no ready products | unknown | unknown | 0 | none | expected session unavailable |
| `08:20:05.452305` | 4 | `2026-08-21` | expected date empty; older dates present | expected `0`; `8/20=385`; `8/19=385` | 2 stale | 0 | none | stale pair suppressed |

LaunchAgent start/inactive pairs were `08:05:04.589/08:06:31.735`, `08:10:05.483/08:10:10.762`, `08:15:02.463/08:15:06.109`, and `08:20:04.688/08:20:09.663`. The retained gate metadata reports `retry_count=4`, `last_error=null`, and `deadline_reached=true`. No inferred query timestamps are used.

## 4. Raw provider availability

The final stored provider/date evidence shows:

- `2026-08-21`: row count `0`
- `2026-08-20`: row count `385`, verified KOSPI200 and KOSDAQ150 contracts
- `2026-08-19`: row count `385`, but not the expected current pair

Per-attempt HTTP status, empty-body SHA, and exact raw response were not archived. Therefore they remain `UNKNOWN_NOT_RETAINED`; `last_error=null` is not converted into an inferred HTTP status.

## 5. Session-date semantics

The session-basis contract, Phase 8.5.4.2 calendar traversal, existing tests, and naturally stored pair identities agree:

```text
NIGHT BAS_DD = overnight session end date
NIGHT 2026-08-21 -> preceding eligible DAY 2026-08-20
NIGHT 2026-08-20 -> preceding eligible DAY 2026-08-19
```

Verdict: `EXPECTED_SESSION_DATE_BASIS_MISMATCH` is **not** present.

## 6. Phase 8.5.4.2 regression controls

| Control | Result |
|---|---|
| Same-BAS_DD DAY/NIGHT pairing | PASS |
| Calendar-day subtraction | PASS |
| XKRX holiday/weekend traversal | PASS |
| Future DAY pairing | PASS |
| Wrong preceding eligible DAY | PASS |
| Instrument mismatch | PASS for stale pair |
| Contract/maturity mismatch | PASS for stale pair |
| Provider raw-change conflict ignored | PASS for stale pair |
| Current expected pair canonicalization | `NOT_REACHED` because rows were unavailable |

## 7. Stale prior pair

| Product | NIGHT / DAY | Contract | NIGHT | DAY | Change | Provider check |
|---|---|---|---:|---:|---:|---|
| KOSPI200 | `2026-08-20 / 2026-08-19` | `A0169000`, `2026-09` | `1040.35` | `1016.25` | `+24.10`, `+2.37146371%` | match |
| KOSDAQ150 | `2026-08-20 / 2026-08-19` | `A0669000`, `2026-09` | `1460.10` | `1433.00` | `+27.10`, `+1.89113747%` | match |

Night source SHA: `deec12e278599752379a792518e313df6678c11bc8b9c4cab9d63de99cafc753`; DAY reference SHA: `98488c8819932b8b330f366c0ef8c9a5d8e54556e97b701a00a47e5375f89ae1`.

The pair is internally valid but stale relative to expected NIGHT `2026-08-21`; user-visible suppression was correct.

## 8. Later publication evidence

No later natural artifact proves when NIGHT `2026-08-21` first became available.

```text
FIRST_PROVIDER_AVAILABILITY_TIME = UNKNOWN
```

A later live query was not made and would not have proved first availability.

## 9. Root cause classification

- `EXPECTED_NO_LATEST_SESSION`: confirmed at the deadline.
- `TELEMETRY_CAPTURE_GAP`: attempt-level raw metadata and post-deadline natural availability were not retained.
- `UNKNOWN_INSUFFICIENT_EVIDENCE`: exact provider publication cause/time cannot be established.

`PROVIDER_PUBLICATION_DELAY` remains plausible but is not promoted to confirmed fact. Parser, calendar traversal, contract rollover, and provider-change conflict defects were not found.

## 10. Deadline adequacy

`DEADLINE_UNPROVEN`.

The expected session was absent by `08:20` on both August 20 and August 21, which materially reduces morning context. However, no post-deadline natural capture establishes when either session first appeared, so the evidence cannot prove that a later fixed deadline would solve the problem without affecting the morning SLA.

## 11. Fail-closed safety

PASS. The runtime did not substitute the prior pair, relabel a wrong session, fabricate a pair, or expose last-known values as current. The actual digest included an explicit omission warning.

## 12. Stale internal-item risk

`LOW`. Stale observations remain available for audit, but all current rendering paths use `summarize_night_futures` with hard freshness/session gates, and the market-intelligence registry excludes the night series. No reachable user-visible leakage path was found.

## 13. Severity

- P0: `0`
- P1: `1` isolated availability/telemetry issue: two consecutive morning deadlines lacked the expected latest session, materially degrading context while safety remained intact
- P2: `1` optional hardening for retained stale internal items; current user-visible leakage risk is LOW

This P1 is isolated from the zero-runtime-diff Phase 9.1 working-capital chain and does not make its promotion unsafe.

## 14. One bounded repair recommendation

Create a separate **Night-Futures Natural Publication-Time Telemetry & Attempt Archive v1** task. It should retain each natural attempt's timestamp, HTTP/result metadata, response SHA/date inventory, candidate/ready products, and one bounded post-deadline natural observation. Do not change deadline or session semantics until that evidence exists.

## Evidence

- `data/ai_review/pilot/history/2026/08/2026-08-21-us-run-30-5a3b7c1c4390/packet.json` SHA `d52e6545692c26769862b33a3632ab36bd4add8b3ea1fbc205c4f1ae089543f1`
- `market-context.json` SHA `5d4c6162db49be7901d58067a606ab964df7469c576b66b08e92c840bce089fe`
- `deterministic-messages.json` SHA `e266bafd6d8fce38cf7a86d1e6cec3b1213337ef4e74875ad2ee88279962f78c`
- `data/macro/briefings/2026-08-21.json`
- Unified LaunchAgent logs and retained `daily.out` lines 65-68
- Machine-readable timeline: `docs/reports/20260821-us-morning-night-futures-timeline.json`
