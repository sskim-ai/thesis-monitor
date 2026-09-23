# M12DS-R6-R4 Result Review

## Decision

`NOT_READY_FOR_FULL_MESSAGE_REPROOF`

R6-R4 correctly stopped at:

`M12DS_R6_R4_KIWOOM_FINALITY_UNRESOLVED`

Report ZIP SHA-256:

`7c0e70b7a09232130a4988b7797c80ab92d1010a390610e90071d6f5e2717920`

## What is now closed

- Correct Kiwoom exchange routing recovered for 22/22 canonical US symbols.
- `usa06012` official schema is confirmed as `미국주식 일 차트`.
- Inside that dated daily-row context:
  `cur_prc = 현재가(종가)` is the row close semantic.
- 22/22 current and previous dated rows are extractable under the same adjusted basis.
- KR post-close sector ownership remains PASS.
- Focused/full/Ruff/diff validation all PASS.
- Production mutations and model calls remain zero.

## The important new evidence

The same 2026-09-22 daily row was observed at two different acquisition times.

Across 22 symbols:
- Open/High/Low exact parity: 22/22
- Close exact parity: only 3/22
- Close changed: 19/22

Examples:
- SPY: 774.12 -> 773.38
- QQQ: 747.35 -> 747.46
- SOXX: 569.64 -> 572.78

The later direct Kiwoom responses were captured around 2026-09-23 17:19 KST
(~04:19 ET pre-market). The prior gateway responses were captured earlier from the
same logical route and adjusted basis.

The prior upstream wire body is not preserved, so the exact cause of the difference
cannot be asserted. Candidate explanations include:
- latest-row extended-hours/current-price behavior;
- overnight provider correction;
- gateway/acquisition-version difference.

But for production safety one conclusion is sufficient:

> A latest same-date `usa06012` row observed after the regular close is not yet a
> reproducible `SETTLED_REGULAR_SESSION_CLOSE` owner at the 08:05 KST production cutoff.

The field is a daily-row close; the unresolved point is the latest row's finality.

## Why another generic cutoff observer alone is not enough

A future 08:05 observer can prove availability, but availability alone does not solve
finality.

R6-R4 already observed historical same-date close drift. A new 08:05 row must be tied
to an independent regular-close reference or later finalized historical row before it
can be qualified.

## Useful existing Kiwoom cross-context field

Official `usa20100` (`미국주식 현재가 종목정보`) contains:

- `cur_prc` = current price
- `base_close_pric` = 전일종가
- previous O/H/L fields

This route is useful as an **independent qualification reference**, but it is not yet
proven to expose the just-completed same-day regular close during 08:05 KST after-hours.

The next task should inspect this exact behavior rather than assume it.

## Recommended next step

R6-R5 should perform a bounded Kiwoom-only close-ownership decision:

1. use `usa20100` as a read-only cross-context qualification source;
2. compare its `base_close_pric` against finalized historical `usa06012` rows;
3. during the actual 08:05/10/15/20 KST window record:
   - `usa06012` target-date row;
   - `usa20100 cur_prc`;
   - `usa20100 base_close_pric`;
4. later compare the 08:05 target row to the same date after it becomes historical;
5. determine whether any Kiwoom field owns the just-completed regular close at the
   production cutoff.

Possible results:

### A. Kiwoom exact owner found
Bind it and proceed to full R6 fresh 24-message proof.

### B. No Kiwoom exact owner
Stop with an explicit external settled-close source requirement. Do not continue
cycling on `usa06012` finality.

Alpha Vantage remains excluded under the current account limit.

KR post-close authority should remain carried as PASS.

No new external provider or schedule change is authorized in this task.
