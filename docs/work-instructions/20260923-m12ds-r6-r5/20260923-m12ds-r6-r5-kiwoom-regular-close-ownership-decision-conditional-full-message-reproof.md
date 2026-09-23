# Thesis Monitor — M12DS-R6-R5 Kiwoom Regular-Close Ownership Decision + Conditional Full Message Reproof

**Suggested work-instruction filename:**  
`20260923-m12ds-r6-r5-kiwoom-regular-close-ownership-decision-conditional-full-message-reproof.md`

**Suggested result bundle:**  
`thesis-monitor-20260923-m12ds-r6-r5-kiwoom-regular-close-ownership-decision-conditional-full-message-reproof-report.zip`

**Required review bundle on full success:**  
`m12ds-r6-r5-rendered-message-review.zip` + `.sha256`

**Task ID:** `M12DS-R6-R5-20260923`

---

## 0. Objective

R6-R4 resolved the field semantics but discovered evidence that the latest same-date
Kiwoom daily-row close is not reproducibly final at the production cutoff.

Facts:

- `usa06012` is officially `미국주식 일 차트`.
- row-local `cur_prc` is officially `현재가(종가)`.
- correct exchange routes are known for 22/22.
- current/previous daily pairs exist 22/22.
- same 2026-09-22 row:
  - O/H/L unchanged 22/22;
  - close changed 19/22 between two acquisition paths/times.
- actual 08:05-era raw per-symbol receipts are missing.
- KR post-close sector authority is already PASS.

R6-R5 must make a **final Kiwoom ownership decision**.

Do not continue repeating generic finality probes after this task.

Use the existing Kiwoom `usa20100` current-quote endpoint only as a bounded read-only
qualification context.

If an exact Kiwoom owner for the just-completed regular close is proven, integrate that
owner and continue to the full 24-message R6 proof.

If no such owner is proven, stop with an explicit external-source requirement. Do not
weaken finality.

No Alpha Vantage.
No new external provider.
No main merge.

---

## 1. Baseline

Use `m12ds-r6-r5-baseline.json`.

Continue from:

`33bb3cb666bd0063aba9444afe7d5f062fefac62`

R6-R4 report SHA-256:

`7c0e70b7a09232130a4988b7797c80ab92d1010a390610e90071d6f5e2717920`

Preserve:
- 22/22 routing;
- official daily-row close semantic;
- same-date variance evidence;
- KR post-close PASS;
- all existing R6 renderer/source contracts.

---

# Phase A — explain the prior close drift without overclaiming

## 2. Reconcile acquisition contexts

For the 22 same-date comparisons, record:

- prior gateway response acquisition timestamp;
- later direct Kiwoom acquisition timestamp;
- route identity;
- request basis;
- row date;
- O/H/L/C;
- raw/gateway hashes available;
- running gateway/code SHA if reconstructable.

Do not assert upstream mutation because the prior upstream wire is missing.

Classify the discrepancy only as:

`PRODUCTION_ROUTE_SAME_DATE_CLOSE_NOT_REPRODUCIBLY_FINAL`

unless stronger evidence is obtained.

This classification alone is sufficient to deny the old latest-row owner.

---

# Phase B — bounded `usa20100` qualification

## 3. Authorization

The user authorizes a bounded read-only use of the existing Kiwoom endpoint:

`usa20100 — 미국주식 현재가 종목정보`

for **qualification only**.

This is not a new provider.

Do not wire it into production until its exact semantics are proven.

---

## 4. Fields to inspect

Official fields include:

- `cur_prc` = 현재가
- `base_close_pric` = 전일종가
- `pre_open_pric`
- `pre_high_pric`
- `pre_low_pric`
- exchange code / symbol identity
- return/delta fields

For selected probes preserve:
- actual timestamp KST/UTC/ET;
- exchange route;
- raw response SHA;
- all relevant fields.

No credentials in artifacts.

---

## 5. Historical-finalized cross-check

During the current pre-market/next-day context, use `usa20100.base_close_pric` only as a
qualification reference.

Compare it against:
- the now-historical `usa06012` close for the immediately prior completed regular
  session.

Require:
- same symbol;
- same session date ownership;
- compatible raw/adjusted basis or an explicit basis-reconciliation reason.

If exact relation is not owned, do not call it parity.

This test answers:
> Which observed value is consistent with Kiwoom's own previous regular close once the
> session has rolled?

---

# Phase C — actual production-cutoff observation

## 6. Target window

Configured US source windows:

- 08:05 KST
- 08:10 KST
- 08:15 KST
- 08:20 KST

At each actual configured observation minute, collect the **full canonical universe** using
the already frozen exchange-routing map.

For a bounded diagnostic subset (at minimum SPY plus representative NASDAQ/NYSE sector
symbols), also collect `usa20100`.

Do not enable production schedulers.

Manual read-only observer only.

---

## 7. At-cutoff facts to preserve

For every `usa06012` symbol:

- request start/end;
- row date;
- row O/H/L/C;
- previous row close/date;
- basis;
- raw hash.

For quote subset:

- current price;
- base_close_pric;
- previous O/H/L;
- raw hash.

Also record:
- target completed session from XNYS calendar;
- after-hours state.

---

## 8. Later finalized comparison

The at-cutoff target-date daily row must later be compared with the same date after it has
become a historical row.

This comparison may use:
- the next pre-market/day observation;
- but only as qualification evidence.

Production must not depend on next-day lookahead.

Required per symbol:
- cutoff close;
- later historical close;
- exact equality flag.

A production regular-close owner must have a rule that does not require later information
to operate, while this delayed check validates that rule.

---

# Phase D — determine whether Kiwoom has a production-time owner

## 9. Candidate owner 1: `usa06012` latest dated row

PASS only if:
- target row at cutoff equals later historical finalized close;
- full required universe qualifies;
- no cross-symbol exceptions;
- result is reproducible.

R6-R4's 19/22 prior drift is negative evidence and must remain in the audit.

One successful day cannot erase prior observed drift unless the prior discrepancy is
independently explained as a non-equivalent acquisition path/version.

---

## 10. Candidate owner 2: `usa20100.base_close_pric`

Do not assume `전일종가` means the just-completed same-day regular close during after-hours.

At the 08:05 KST after-hours cutoff, prove which exchange session `base_close_pric`
actually owns.

Possible outcomes:

### A
It refers to the target just-completed regular session and matches later historical
`usa06012` close.

Then it may qualify as the production-time regular-close owner.

### B
It refers to the session before the target (one-day lag).

Then it is not usable for the current market message.

No label reinterpretation.

---

## 11. Final Kiwoom decision

Exactly one of:

### `KIWOOM_REGULAR_CLOSE_OWNER_PASS`
An existing Kiwoom field/contract owns the just-completed regular-session close at the
production cutoff for the complete required universe.

### `KIWOOM_REGULAR_CLOSE_OWNER_NOT_AVAILABLE`
No tested existing Kiwoom route can provide the target regular close at the production
cutoff without ambiguity/lookahead.

### `KIWOOM_REGULAR_CLOSE_OWNER_UNRESOLVED`
Only if evidence collection itself failed for a bounded technical reason.

Do not repeat finality work indefinitely after a conclusive NOT_AVAILABLE.

---

# Phase E — if Kiwoom PASS

## 12. Bind one typed owner

Create:

`us-regular-session-close-kiwoom-v2`

with:
- exact API/field;
- session date;
- close;
- previous session/close;
- basis;
- provider/exchange;
- raw hash;
- finality contract.

Only the qualified field is promoted.

No global `cur_prc` mapping.

---

## 13. Full US market universe

Require:
- SPY / QQQ / IWM;
- full sector ETF universe;
- same target session;
- same basis;
- deterministic TOP3/BOTTOM3.

No stale fallback.

---

# Phase F — if Kiwoom NOT AVAILABLE

## 14. Stop and report source requirement

Return:

`M12DS_R6_R5_US_REGULAR_CLOSE_EXTERNAL_SOURCE_REQUIRED`

Include:
- why usa06012 latest row is unsafe;
- what usa20100 owns;
- production cutoff;
- exact required semantic:
  `just-completed regular-session settled close + previous same-basis close`;
- required universe;
- no provider recommendation promoted automatically.

No Market/Core/A/B.

No 24-message success claim.

A subsequent task may compare external provider options only after user authorization.

---

# Phase G — carry already-closed contracts

## 15. KR post-close

Carry `kr-post-close-sector-session-v1` as qualified.

For the final fresh generation, recollect current values under the same contract.

---

## 16. KR stock basis

Preserve:
`adjusted_intraday = INTRADAY + ADJUSTED`

Fresh final capture must validate 8/8.

---

## 17. Night futures

Preserve official KRX:
- daily;
- weekly in-progress;
- month-to-date;
- expected/elapsed counts;
- final-message E2E.

---

## 18. Price structure

Preserve distinct:
- fundamental range;
- support;
- resistance;
- tactical watch zone.

---

## 19. Macro latest-available display

Preserve:
- current facts for direction evidence;
- clearly dated `최신 확인값` informational rows with no direction refs.

---

# Phase H — full reproof only after Kiwoom PASS

## 20. Fresh information gate

Require:
- US close owner + full universe;
- US sector ranking;
- KR completed-sector ranking;
- KR8 quote basis;
- macro display;
- night D/W/M.

No model call before full gate.

---

## 21. Fresh Market/Core/A/B

Run:
- Market 2/2
- Core 22/22
- A 22/22
- B 22/22

Transport:
- 600 seconds per attempt
- first + up to 2 byte-identical transient retries
- max 3 attempts
- no semantic/schema/source/security retry
- no source refresh between attempts
- no offline substitution

---

## 22. Exact 24-message capture

Require:
- MARKET_US
- MARKET_KR
- 22 stocks

`24/24`

with:
- US indices/sectors;
- Treasury 3/5/10/30Y;
- WTI latest/current labeling;
- KR sector blocks;
- stock support/resistance;
- tactical/fundamental separation;
- night D/W/M.

---

## 23. Validation

Before full reproof:
- focused PASS
- full pytest clean-env PASS
- Ruff PASS
- diff PASS
- no new skips/xfails

Production mutations remain zero.

---

## 24. Full success

`M12DS_R6_R5_KIWOOM_CLOSE_OWNER_24_MESSAGE_PASS_READY_FOR_HUMAN_REVIEW`

---

## 25. Stop states

- `M12DS_R6_R5_KIWOOM_CROSS_CONTEXT_PROOF_FAILED`
- `M12DS_R6_R5_CUTOFF_OBSERVATION_PENDING`
- `M12DS_R6_R5_KIWOOM_REGULAR_CLOSE_OWNER_UNRESOLVED`
- `M12DS_R6_R5_US_REGULAR_CLOSE_EXTERNAL_SOURCE_REQUIRED`
- `M12DS_R6_R5_INFORMATION_COVERAGE_INCOMPLETE`
- `M12DS_R6_R5_CURRENT_INFERENCE_INCOMPLETE`
- `M12DS_R6_R5_MESSAGE_CAPTURE_INCOMPLETE`
- `M12DS_R6_R5_LOCAL_VALIDATION_FAILED`

No new provider in this task.

---

## 26. After success

If 24 messages are human-approved:
1. bounded R6 integration to main;
2. then M12DT onboarding.

If external source is required:
return to Chat for explicit provider authorization before any provider integration.
