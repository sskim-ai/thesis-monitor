# Thesis Monitor — M12DS-R6-R5A Actual 08:05 Cutoff Observation

**Suggested filename:**  
`20260924-m12ds-r6-r5a-actual-us-cutoff-observation.md`

**Suggested result bundle:**  
`thesis-monitor-20260924-m12ds-r6-r5a-actual-us-cutoff-observation-report.zip`

## 0. Purpose

R6-R5 correctly ended at:

`M12DS_R6_R5_CUTOFF_OBSERVATION_PENDING`

The final Kiwoom ownership decision remains intentionally null.

This task performs only the actual configured US source-window observation for
2026-09-24 KST, targeting the completed US regular session of 2026-09-23.

No model calls.
No Market/Core/A/B.
No message rendering.
No production send.
No scheduler registration.
No new provider.

## 1. Frozen baseline

R6-R5 final local SHA:

`1da19d245e84b6643a7139f8177f72acd46a16fe`

Operating main:

`2097645892e30d84aba435416f98e7f9545a87fa`

Observer route SHA:

`c3020384e933286760e33d03a627b26cd662753a4cb3f5c893b111d36b9a8c7e`

Observer plan SHA:

`018c17edb00fd78181ae3f3627785b678dd854dc11689c7c1fd5b14290930f8f`

Do not modify the route or request plan.

## 2. Launch-time gate

This instruction is valid only when started in time for the actual configured window:

- 08:05 KST
- 08:10 KST
- 08:15 KST
- 08:20 KST

Preferred start: 08:03–08:04 KST.

If started after the final owned window:
stop:

`M12DS_R6_R5A_CUTOFF_WINDOW_MISSED`

Do not backfill with a later observation.

If started too early, bounded synchronous waiting until the first configured minute is
allowed. Do not create a daemon, launchd job, cron job, automation or detached process.

## 3. Target session

Use XNYS exchange calendar.

Target must be the immediately preceding completed regular session.

Expected for this run:

`2026-09-23`

Verify dynamically. Do not hardcode acceptance solely from this expected date.

## 4. Requests

Use the exact frozen observer plan.

At each owned cutoff collect:

### Full canonical universe
`usa06012`, adjusted daily row, all 22 frozen symbols.

### Qualification subset
For:
- SPY
- SOXX
- XLC

also collect:
- `usa06012` raw
- `usa20100` quote context

Do not add symbols or calls.

Do not use Alpha Vantage.

## 5. Per-cutoff receipt

For every request preserve:

- actual start/end KST/UTC/ET;
- symbol;
- exchange route;
- API id;
- request hash;
- HTTP/provider status;
- raw response SHA;
- target row date;
- target row O/H/L/C;
- previous dated row close;
- raw/adjusted basis;
- quote current price;
- quote `base_close_pric`;
- quote previous O/H/L where applicable.

Credentials must not be retained.

## 6. Window ownership

A response counts for a cutoff only if the actual acquisition begins within the frozen
minute ownership rule already implemented by the observer.

Missed windows are:

`MISSED`

They must never be populated from another timestamp.

## 7. Early-stop behavior

Do not stop merely because the full22 target row is present.

All four configured windows are useful for testing whether the latest daily row mutates
during the after-hours period.

Therefore collect every configured window that is actually reached during this single
bounded run.

No retry outside the frozen provider observer contract.

## 8. Required output

Create a cutoff receipt containing:

- target session;
- per-window full22 availability;
- per-symbol close values at each window;
- close-change matrix 08:05→08:10→08:15→08:20;
- O/H/L change matrix;
- SPY/SOXX/XLC `base_close_pric` relation at each window;
- full universe missing/failure list;
- raw hashes;
- actual timestamps.

Classify only:

- `CUTOFF_OBSERVATION_COMPLETE`
- `CUTOFF_OBSERVATION_PARTIAL`
- `CUTOFF_WINDOW_MISSED`
- `TECHNICAL_COLLECTION_FAILURE`

Do NOT yet declare:
- `KIWOOM_REGULAR_CLOSE_OWNER_PASS`
- `EXTERNAL_SOURCE_REQUIRED`

unless an already-frozen R6-R5 rule explicitly permits that conclusion without the later
historical comparison. Default is to defer final ownership.

## 9. Later comparison handoff

Freeze the exact target-date values captured at cutoff.

Prepare but do not execute a later comparison request.

The next task will compare the frozen cutoff row/base-close values with the same
2026-09-23 session after it is a historical/finalized row in the next premarket/day
context.

No production algorithm may depend on that future value.

## 10. Safety

Must remain zero:

- model calls
- source-provider expansion
- Alpha Vantage calls
- Telegram/send
- recipient intent
- DB decision/warning writes
- scheduler mutation
- broker action
- merge/push/deploy

Do not enable paused/disabled production jobs.

## 11. Terminal

Preferred:

`M12DS_R6_R5A_ACTUAL_CUTOFF_OBSERVATION_COMPLETE`

Return the structural report and SHA to Chat.
