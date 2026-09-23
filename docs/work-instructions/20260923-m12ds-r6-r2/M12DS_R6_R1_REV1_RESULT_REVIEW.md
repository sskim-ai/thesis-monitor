# M12DS-R6-R1-REV1 Result Review

## Decision

`CORRECT_STOP — SOURCE AUTHORITY CLOSURE STILL REQUIRED`

The uploaded report ZIP is internally intact and its SHA-256 matches the sidecar:

`b90cb60e9d55082ec15a66d9a083edce53accad1b429ab3a5b7dfcecb5bd0dff`

Terminal:

`M12DS_R6_R1_INFORMATION_COVERAGE_INCOMPLETE`

No Market/Core/A/B calls were made, no new final messages were produced, and no
production mutation occurred. That was the correct behavior because the explicit
pre-model full-information gate was not satisfied.

## What is now proven

### 1. US OHLCV is not a stale-cache/parser problem

For 21/22 US symbols:
- HTTP 200;
- raw rows include 2026-09-18, 09-21, 09-22;
- parser normalizes 09-22 correctly;
- client fallback/cache is not used.

The blocker is narrower:

The latest 09-22 row exposes `cur_prc`, but the current source contract does not prove
that the latest row's value is the **settled regular-session close**.

Older rows can be proven FINAL because a later chart row exists. The latest row cannot.

Therefore it is correct to refuse:
- wall-clock inference;
- `current quote == completed close`;
- promotion of the old 09-04 DB row.

XLC is separately a real provider failure:
- HTTP 502
- response records an upstream Kiwoom token HTTP 429.

### 2. KR sector failure is not a parser/type bug

At the 2026-09-23 12:53 KST diagnostic cutoff:
- current KOSPI/KOSDAQ sector actions return current intraday values;
- target completed session is 2026-09-22;
- the current-only sector actions have no target-date parameter;
- the historical composite index proves the current snapshot is 09-23 intraday, not
  09-22 completed-session data.

Therefore the current/historical mismatch is a correct session-ownership stop.

The original morning ValueError is still not retroactively explained.

### 3. KR stock price-basis closure succeeded

All eight KR quote responses own `adjusted=true`.

The shared basis contract correctly represents:
- phase = INTRADAY
- adjustment = ADJUSTED
- legacy = adjusted_intraday

Basis validation:
`8/8 PASS`

This is not yet a full 8/8 message-capture proof because the market information gate
stopped before inference/capture.

### 4. Macro freshness is now fail-closed

Treasury 3Y/5Y/10Y/30Y are valid latest-published-with-lag factual rows under their
official publication metadata.

Some other FRED rows, including WTI in this diagnostic cutoff, remain
`STALE_UNEXPECTED` because an exact publication clock was not sufficiently owned.
They are correctly excluded from current-direction evidence.

For the user's information requirement, a later task should distinguish:
- current directional macro facts;
- clearly dated `latest available` informational rows that are not direction evidence.

### 5. Night D/W/M

No new live night call was made because the information gate stopped first.
The already-passing R6 implementation was left unchanged and its offline regressions pass.

## Validation

Final implementation:
`196b3f82f2a17fdb882339deda99490b7e0dbb60`

Full pytest:
- 5291 passed
- 63 existing skips
- 0 failed

Ruff / diff / knowledge / public-action:
PASS

P0:
0

P1:
2
- US settled regular-close authority
- KR completed-session sector authority

## Required next step

Do not weaken currentness/finality.

R6-R2 should first bind the source requirement to the **actual production send
schedule** for US and KR market messages.

Then:

1. US: inventory already configured/approved provider routes for an explicit settled
   regular-session close or completed daily-bar finality contract.
2. KR: determine whether production execution is post-close. If post-close, prove the
   current-only sector snapshot owns the just-completed session; if execution can be
   pre-close, an approved historical sector route is required.
3. Preserve the fixed KR adjusted-intraday price-basis contract.
4. Preserve night D/W/M and support/resistance.
5. Allow clearly dated latest-available macro informational rows without allowing them
   into current-direction evidence.
6. Only after the full information gate passes, run fresh Market/Core/A/B and capture
   24/24 messages.

No new external provider should be activated without user approval.
