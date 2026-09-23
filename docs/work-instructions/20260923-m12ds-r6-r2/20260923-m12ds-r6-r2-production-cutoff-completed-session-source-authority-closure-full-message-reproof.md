# Thesis Monitor — M12DS-R6-R2 Production-Cutoff Completed-Session Source Authority Closure + Full 24-Message Reproof

**Suggested work-instruction filename:**
`20260923-m12ds-r6-r2-production-cutoff-completed-session-source-authority-closure-full-message-reproof.md`

**Suggested result bundle:**
`thesis-monitor-20260923-m12ds-r6-r2-production-cutoff-completed-session-source-authority-closure-full-message-reproof-report.zip`

**Required review bundle on success:**
`m12ds-r6-r2-rendered-message-review.zip` + `.sha256`

**Task ID:** `M12DS-R6-R2-20260923`

---

## 0. Objective

R6-R1-REV1 correctly stopped before model inference.

It proved the remaining blockers are not generic parser failures:

### US
Current 2026-09-22 raw daily rows exist for 21/22 symbols, but the latest row lacks an
owned **settled regular-session close/finality** semantic.

### KR
At the 2026-09-23 12:53 KST diagnostic cutoff, the sector actions are current-only and
therefore own 2026-09-23 intraday state, while the requested completed session is
2026-09-22.

### Already fixed
The KR eight-stock price-basis vocabulary is now correctly typed as:

`INTRADAY + ADJUSTED`

and validates 8/8.

R6-R2 binds source authority to the actual production execution cutoff, closes the
completed-session source contracts without weakening currentness, then runs the first
fresh full-information 24-message reproof.

Do not change investment judgment policy.

Do not merge main in R6-R2.

---

## 1. Frozen baseline

Use `m12ds-r6-r2-baseline.json`.

Operating main remains:

`2097645892e30d84aba435416f98e7f9545a87fa`

Continue from the validated R6-R1-REV1 task branch final:

`196b3f82f2a17fdb882339deda99490b7e0dbb60`

R6-R1-REV1 report SHA-256:

`b90cb60e9d55082ec15a66d9a083edce53accad1b429ab3a5b7dfcecb5bd0dff`

Full validation:
- 5291 PASS
- 63 existing skips
- 0 failures

No model output from R6-R1-REV1 may be invented; model calls were 0.

---

# Workstream A — own the real production cutoff

## 2. Resolve production schedules before source design

Read the actual repository scheduler/config owners for:

- US market message execution;
- KR market message execution;
- source collection cutoffs used by those messages.

Record:
- timezone;
- scheduled local time;
- exchange-local equivalent;
- intended completed-session date;
- whether execution occurs pre-open / intraday / post-close;
- backup/fallback schedule if it can produce the same message.

Do not infer the production cutoff from the current diagnostic wall clock.

Create:

`production-market-cutoff-receipt.json`

The source contract must be satisfiable at the real scheduled cutoff, not only in an
ad-hoc later test window.

If schedule/config ownership is ambiguous:
stop with

`M12DS_R6_R2_PRODUCTION_CUTOFF_UNRESOLVED`.

---

# Workstream B — US settled regular-session close authority

## 3. Existing finding

For 21 successful US OHLCV symbols:
- HTTP 200;
- rows include 09-18, 09-21, 09-22;
- 09-18 and 09-21 are final because a later row exists;
- latest 09-22 exposes `cur_prc`;
- source contract does not prove `cur_prc` is the settled regular-session close.

Do not weaken this finding.

XLC separately had:
- HTTP 502;
- upstream token 429.

---

## 4. Inventory already configured/approved US routes

Before adding any provider, inventory existing repository/provider routes that are
already configured and read-only.

Search for an exact semantic owner for:

`SETTLED_REGULAR_SESSION_CLOSE`

or an equivalent documented completed daily-bar close.

For each candidate route record:

- provider;
- action/endpoint;
- security universe coverage;
- field name;
- session-date semantics;
- whether after-hours trading contaminates the field;
- whether the field is explicitly regular-session close;
- availability at the actual production cutoff;
- source documentation/schema/test owner;
- raw-response SHA in a bounded live probe.

A route is acceptable only if its semantics are provable without relying on a future row
that would not exist at the production cutoff.

### Allowed proof classes

1. Explicit provider field documented as regular-session settled close.
2. Historical/daily endpoint whose documented row semantics make the target bar a
   completed daily close at the cutoff.
3. Already-approved read-only route exposing previous/regular close with exact session
   ownership.

### Forbidden proof classes

- wall-clock passage alone;
- current quote silently equals close;
- `cur_prc` relabeled without source semantics;
- use of next-session lookahead unavailable at the production send time;
- stale DB row promoted as current.

---

## 5. Existing-provider route repair

If an already configured/approved route owns the exact close:

create one typed receipt:

`us-regular-session-close-v1`

binding:
- symbol;
- provider/action;
- exchange session date;
- settled close;
- previous settled close where needed;
- finality state;
- raw source SHA;
- source contract/version.

Use that owner for:
- SPY / QQQ / IWM;
- canonical US sector universe;
- style/breadth market rows where the same semantic applies.

Do not alter stock-level technical history semantics unnecessarily.

### XLC

Use the user's standing retry policy for the real provider request:

- 600 seconds per attempt;
- max 3 attempts total;
- retries only byte-identical transient transport/process failures.

HTTP 429/502 may qualify only through the existing typed transient classification.

If XLC remains unavailable, a complete `TOP3/BOTTOM3` sector ranking cannot silently
pretend the canonical universe is complete.

Return exact missing-universe evidence.

---

## 6. If no existing route can prove settled close

Do not activate a new external provider.

Return:

`M12DS_R6_R2_US_SETTLED_CLOSE_ROUTE_REQUIRES_USER_AUTHORIZATION`

with:
- routes inspected;
- why each fails;
- exact semantic needed;
- any configured-but-not-yet-authorized candidate route separately identified.

Do not run Market/Core/A/B.

---

# Workstream C — KR completed-session sector authority

## 7. Bind the route to actual KR production timing

The 12:53 KST diagnostic cannot use current-only sector actions for 09-22 because the
09-23 session is still live.

The correct production contract depends on the actual scheduler.

### Case A — production message executes after KRX close

A current-only sector action may own the just-completed same-day session only if all are
proven:

1. official exchange calendar/session state = CLOSED;
2. response collected after the owned close cutoff;
3. provider action semantics own the current market/sector state;
4. current composite KOSPI/KOSDAQ values match the same-date historical completed index
   owner within exact documented representation/rounding semantics;
5. sector response date/session can be deterministically bound to that same completed
   session.

Create:

`kr-post-close-sector-session-v1`

Do not use intraday data collected before close.

### Case B — production message can execute before KRX close

Then previous completed-session sectors require an approved historical/target-date sector
route.

Inventory already configured Kiwoom/KRX routes.

An acceptable route must own:
- target session date;
- sector taxonomy;
- sector return/level;
- KOSPI vs KOSDAQ venue;
- completed-session finality.

If no approved route exists:

`M12DS_R6_R2_KR_HISTORICAL_SECTOR_ROUTE_REQUIRES_USER_AUTHORIZATION`

Do not make the current-only intraday TR impersonate the previous day.

---

## 8. KR sector deterministic rankings

Once session ownership is proven:

- same-session only;
- KOSPI and KOSDAQ taxonomy remain separate unless an existing explicit cross-venue owner
  says otherwise;
- deterministic TOP3/BOTTOM3;
- exact numeric returns;
- stable tie-break;
- no model-generated ranking.

Before model calls prove the final renderer can emit the factual blocks.

---

# Workstream D — preserve KR current-price basis closure

## 9. Promote the locally proven basis contract into the fresh proof

Preserve:

- `phase = INTRADAY`
- `adjustment = ADJUSTED`
- legacy mapping `adjusted_intraday`

for all eight current KR quotes when the source owns adjusted=true.

Producer, validator, renderer and capture must consume the same typed owner.

Required full fresh proof:
- 8/8 KR stock final messages pass the quote/as-of/basis boundary.

Do not count the R6-R1 basis-only 8/8 validation as a fresh message proof.

---

# Workstream E — macro information display versus direction evidence

## 10. Keep current-direction evidence strict

No lagged or publication-uncertain macro row may become supporting/contradicting evidence
for the current market direction.

Preserve the fail-closed directional contract.

---

## 11. User-visible latest-available informational rows

The user explicitly wants WTI and Treasury tenors visible.

Separate two concepts:

### Current directional facts
Only source-owned current facts.

### Latest available informational facts
A clearly labeled factual row may be rendered even when it is not current-direction
eligible, if:
- the source row itself is authentic;
- its observation date is owned;
- the value is typed/provenanced;
- the message labels it as `latest available`, `latest published`, or equivalent;
- the observation date is shown;
- it is excluded from model direction refs.

This is display-only. It is not source-currentness widening.

For example an older WTI row may appear as:

`WTI 최신 확인값 (기준 2026-09-15): ... · 현재 시장방향 판단에는 미사용`

if and only if the source row/value/date are valid.

Do not call an unexpectedly stale observation current.

Treasury 3Y/5Y/10Y/30Y latest-published-with-lag rows remain visible with their dates.

---

# Workstream F — preserve already-successful R6 features

## 12. Night futures

Do not regress:
- KOSPI200 daily;
- KOSPI200 weekly in-progress;
- KOSPI200 month-to-date official KRX history;
- KOSDAQ150 same;
- elapsed/expected session counts;
- exact message E2E.

Recalculate month/week coverage for the new run date; do not hardcode historical 16/16.

Official KRX remains authority.
Kiwoom remains cross-check only.

---

## 13. Stock technical levels

Preserve:
- technical support;
- technical resistance;
- tactical watch zone;
- fundamental entry range;

as four distinct concepts.

No technical/tactical range may be renamed fair value.

---

# Workstream G — pre-model full information gate

## 14. Required source coverage

Before any model call require:

### US
- canonical major indices own the latest completed-session settled close;
- full canonical sector ranking universe owns the same session;
- no stale-row promotion;
- breadth may remain `PUBLICATION_PENDING` if the upstream publication is honestly not
  available, but must be explicitly separated from the index/sector coverage result.

### KR
- completed-session sector owner appropriate to the actual production cutoff;
- deterministic venue-specific TOP3/BOTTOM3;
- 8/8 typed quote contexts;
- all existing financial/source gates.

### Macro
- Treasury display contract;
- WTI/latest-available display contract;
- directional eligibility separately audited.

### Night
- typed D/W/M context available under existing contract.

If any mandatory user-facing block lacks source authority:
no model calls.

---

# Workstream H — fresh production-equivalent proof

## 15. Fresh source generation

After code/source-contract freeze, start a NEW fresh generation.

Do not reuse diagnostic live values as the final current source snapshot.

Freeze:
- source packets;
- production cutoff;
- source authority receipts;
- request bytes;
- code SHA.

---

## 16. Fresh Market/Core/A/B

Run:

- Market 2/2
- Core 22/22
- A 22/22
- B 22/22

using the user-approved standing transport policy:

- model `gpt-5.6-sol`
- xhigh
- 600 seconds per process attempt
- first attempt + up to 2 byte-identical transient retries
- maximum 3 attempts total per logical request
- no 4th attempt
- no semantic/schema/source-use/policy/security/identity retry
- no source refresh between retries
- no offline substitution.

---

## 17. Exact 24-message capture

Capture at the real final outbound boundary with sends disabled.

Expected:
- MARKET_US
- MARKET_KR
- 22 stock messages

Total:

`24/24`

### MARKET_US must show
when source-owned:
- major indices;
- sector TOP3/BOTTOM3;
- Treasury 3Y/5Y/10Y/30Y;
- WTI latest-available/current label with date;
- market interpretation;
- KRX night D/W/M next-session context.

### MARKET_KR
- completed-session indices/breadth/flows;
- completed-session sector TOP3/BOTTOM3;
- no intraday/completed mixing.

### All stocks
- Overall / New Buyer / Holder;
- price as-of;
- fundamental range if valid;
- support if valid;
- resistance if valid;
- tactical watch zone if valid.

---

## 18. Mandatory review bundle

Create:

`m12ds-r6-r2-rendered-message-review.zip`

Include:
- exact 24 texts;
- production-cutoff receipt;
- US settled-close authority audit;
- KR completed-sector authority audit;
- macro display/direction separation audit;
- KR 8/8 price-basis capture audit;
- US/KR sector ranking audit;
- night D/W/M E2E;
- production isolation;
- full tests/lint.

---

## 19. Validation

Before final live proof:
- focused tests PASS;
- full pytest PASS;
- Ruff PASS;
- diff check PASS;
- no new skip/xfail.

After exact capture:
- production DB/WAL unchanged;
- send/recipient intent 0;
- scheduler mutation 0;
- broker action 0.

No main merge/push/deploy.

---

## 20. Full-success terminal

`M12DS_R6_R2_COMPLETED_SESSION_AUTHORITY_24_MESSAGE_PASS_READY_FOR_HUMAN_REVIEW`

Requires:
- actual production cutoff owned;
- US settled-close authority complete;
- US sector TOP3/BOTTOM3 complete;
- KR completed-session sector authority complete;
- KR sector TOP3/BOTTOM3 complete;
- KR stock 8/8 final messages;
- macro information/currentness labels correct;
- night D/W/M PASS;
- total messages 24/24;
- full validation PASS;
- production mutations 0.

---

## 21. Stop terminals

- `M12DS_R6_R2_PRODUCTION_CUTOFF_UNRESOLVED`
- `M12DS_R6_R2_US_SETTLED_CLOSE_ROUTE_REQUIRES_USER_AUTHORIZATION`
- `M12DS_R6_R2_US_SETTLED_CLOSE_SOURCE_FAILED`
- `M12DS_R6_R2_KR_HISTORICAL_SECTOR_ROUTE_REQUIRES_USER_AUTHORIZATION`
- `M12DS_R6_R2_KR_COMPLETED_SECTOR_SOURCE_FAILED`
- `M12DS_R6_R2_INFORMATION_COVERAGE_INCOMPLETE`
- `M12DS_R6_R2_CURRENT_INFERENCE_INCOMPLETE`
- `M12DS_R6_R2_MESSAGE_CAPTURE_INCOMPLETE`
- `M12DS_R6_R2_NIGHT_REGRESSION`
- `M12DS_R6_R2_LOCAL_VALIDATION_FAILED`
- `M12DS_R6_R2_JUDGMENT_POLICY_SCOPE_EXPANSION_REQUIRES_CHAT`

Do not weaken finality/currentness to avoid a stop.

---

## 22. After human approval

After exact messages are reviewed and accepted:

1. bounded R6 main integration + remote CI/replay;
2. then:
   `M12DT_NEW_TICKER_ONBOARDING_GATE`.
