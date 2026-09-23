# Thesis Monitor — M12DS-R6-R1-REV1 Market Source Diagnostics + KR Price-Basis Closure + Full 24-Message Reproof

**Suggested work-instruction filename:**  
`20260923-m12ds-r6-r1-rev1-market-source-diagnostics-kr-price-basis-closure-full-message-reproof.md`

**Suggested result bundle:**  
`thesis-monitor-20260923-m12ds-r6-r1-rev1-market-source-diagnostics-kr-price-basis-closure-full-message-reproof-report.zip`

**Required review bundle on success:**  
`m12ds-r6-r1-rendered-message-review.zip` + `.sha256`

**Task ID:** `M12DS-R6-R1-REV1-20260923`

---

## 0. Objective

Two independent fresh R6 runs both completed:

- Market 2/2
- Core 22/22
- A 22/22
- B 22/22

and both reproduced the same partial information coverage and the same final-message
count:

`16/24`

This rules out a one-off model failure.

Already closed:
- Treasury 3Y/5Y/10Y/30Y user-facing display;
- WTI user-facing display;
- stock technical support/resistance for captured US subjects;
- official KRX night daily;
- official KRX night weekly in-progress rendering;
- official KRX night month-to-date backfill;
- night final-message E2E.

Remaining systematic blockers:

1. US SPY/QQQ/IWM and sector/style current bars do not refresh past 2026-09-04 and the
   collector reports `ValueError`;
2. KR sector provider transport succeeds 5/5 but parsing/normalization ends in
   `ValueError`;
3. all eight KR stock final messages are rejected because producer
   `adjusted_intraday` is not in the renderer's price-basis vocabulary;
4. lagged macro rows such as WTI need an explicit latest-published/delayed freshness
   presentation state.

R6-R1 closes these source/contract boundaries and repeats a full fresh proof.

Do not change investment judgment semantics.

Do not merge main in R6-R1.

---

## 1. Baseline

Use `m12ds-r6-r1-baseline.json`.

Operating main:

`2097645892e30d84aba435416f98e7f9545a87fa`

Run 1 report:

`54fa9395432278b9e1acf6c14f5950f80398a8d44c8727ea50bea04ecf57829d`

Run 2 report:

`d1806ef34ff3de9a3fd5549a1f50aee654d4cff4a41a535223b6716d66f748c7`

Run 1/2 are preserved historical evidence.

Do not rewrite them as successful 24-message runs.

---

## 2. Preserve successful R6 functionality

Do not regress:

### US macro factual block
- Treasury 3Y
- Treasury 5Y
- Treasury 10Y
- Treasury 30Y
- breakeven
- real yield
- high-yield spread
- WTI
- VIX

### Night futures
For KOSPI200 and KOSDAQ150:
- daily;
- weekly current-week OHLC;
- included/expected elapsed sessions;
- month-to-date official KRX backfill;
- monthly OHLC;
- unresolved monthly return when no previous same-contract baseline;
- exact final-message E2E.

Observed successful coverage in both runs:
- weekly 2/2 elapsed sessions;
- monthly 16/16 elapsed sessions.

### Stock technical rendering
- technical support;
- technical resistance;
- tactical watch zone separately;
- fundamental entry range separately.

Any touched owner requires its existing regression.

---

# Workstream A — prove US OHLCV failure cause before repair

## 3. Reproduced facts

Completed US regular session:

`2026-09-22`

Yet both fresh generations retain:

- SPY: 2026-09-04
- QQQ: 2026-09-04
- IWM: 2026-09-04
- US sector/style proxy rows: 2026-09-04

and report fresh-collection warnings:

`ohlcv_analyst:<symbol>: ValueError`

Affected rows are correctly denied:
- `not_latest_completed_session`
- `row_temporal_or_source_denial`

Do NOT make 2026-09-04 eligible.

## 4. Diagnostic instrumentation

The existing frozen collector currently retains only `ValueError` and not enough evidence
to determine the source.

Before changing request/parser/cache behavior, add local diagnostic ownership.

For each failed symbol preserve in an isolated non-Git/private diagnostic artifact:

- provider id;
- endpoint/action;
- exact non-secret request parameters;
- request local/UTC/exchange-session cutoff;
- HTTP/provider status;
- raw response SHA-256;
- sanitized response shape and metadata;
- latest raw observation/bar date actually present;
- parser output row dates;
- selected current row;
- cache path/version;
- whether fallback/cache was used;
- exact exception type + message + stack owner.

Never include credentials.

Run a bounded no-model current-session reproduction.

Classify each symbol/family as exactly one:

- `UPSTREAM_CURRENT_BAR_UNAVAILABLE`
- `REQUEST_WINDOW_OR_SESSION_PARAMETER_DEFECT`
- `RAW_CURRENT_BAR_PRESENT_PARSER_DEFECT`
- `CURRENT_PARSE_FAILED_OLD_CACHE_RETAINED`
- `UNRESOLVED_PROVIDER_FAILURE`

Do not repair before this classification.

---

## 5. Bounded US repair

If the proven root cause is within the existing approved provider path:

### Request/session defect
Fix exchange-local request/session parameters generically.

### Parser defect
Repair the current provider response parser with versioned generic tests.

### Old-cache retention
A failed current fetch must not masquerade as a current source.

Keep old history for history/technical purposes, but current market rows become unavailable
unless the exact current session is owned.

After repair require current-session bars for the existing canonical US index/sector universe
when upstream actually supplies them.

### Upstream unavailable
If the existing approved provider truly lacks the completed session:
- do not add a new provider automatically;
- return exact evidence to Chat with
  `M12DS_R6_R1_US_UPSTREAM_SOURCE_UNAVAILABLE`.

A new market provider requires separate authorization.

---

## 6. US breadth remains separate

Run 2 proved the NASDAQ-Trader exact-session breadth file for 2026-09-22 was not yet
published; latest available was 2026-09-18.

Preserve:

`PUBLICATION_PENDING`

Do not substitute 2026-09-18 breadth as 2026-09-22.

US index/sector repair does not imply breadth availability.

---

# Workstream B — prove and repair KR sector ValueError

## 7. Reproduced facts

Both runs report:

- provider requests: 5
- provider successes: 5
- network failures: 0
- resulting sector status: `UNAVAILABLE`
- error: `ValueError`

This is consistent with post-transport parser/schema/normalization failure, but the exact
cause is not yet proven because rejected raw responses were not retained.

## 8. KR sector diagnostic capture

For a fresh bounded no-model call preserve locally:

- exact approved KRX/provider action;
- non-secret parameters;
- raw response SHA;
- sanitized response schema/keys/row count;
- exchange/session date fields;
- sector taxonomy identifiers/names;
- return/price fields used for ranking;
- parser stage;
- exact ValueError message/stack.

Then classify:

- `UPSTREAM_SCHEMA_CHANGED`
- `EXPECTED_FIELD_MISSING`
- `TYPE_COERCION_DEFECT`
- `SESSION_DATE_PARSE_DEFECT`
- `TAXONOMY_MAPPING_DEFECT`
- `UNRESOLVED`

## 9. KR sector parser repair

Only after classification, repair the existing approved parser generically.

Do not:
- invent values;
- use model prose to create rankings;
- combine KOSPI/KOSDAQ taxonomies without the existing owner;
- add a new provider without Chat.

Require deterministic same-session sector +TOP3/-TOP3 output according to the R6 contract.

---

# Workstream C — canonical current-price basis contract

## 10. Reproduced KR message failure

All eight KR subjects have:

- quote `as_of_date = 2026-09-23`
- evidence assessment date = 2026-09-23
- availability = ready
- contract = `current-price-context-v1`
- producer price basis = `adjusted_intraday`

The renderer accepts:
- `adjusted_close`
- `close`
- `intraday`

Therefore the error label:

`accepted_quote_asof_invalid`

is misleading in this case; the actual cause is price-basis vocabulary mismatch.

## 11. Introduce one typed price basis owner

Use:

`m12ds-r6-r1-market-source-and-price-basis-closure-v1`

Preferred canonical form:

- `phase = INTRADAY | CLOSE`
- `adjustment = RAW | ADJUSTED`

Legacy deterministic mappings:

- `intraday` -> INTRADAY / RAW
- `adjusted_intraday` -> INTRADAY / ADJUSTED
- `close` -> CLOSE / RAW
- `adjusted_close` -> CLOSE / ADJUSTED

Producer, validator, renderer and capture must consume the same owner.

No silent coercion.

If `adjusted_intraday` has no real source-owned adjustment semantics, do not accept the
label merely to make capture pass. Correct the producer contract instead and prove it from
the underlying quote source.

## 12. Required price-basis tests

At minimum:

- current KR adjusted intraday source with owned semantics -> accepted;
- raw intraday -> accepted with correct display;
- adjusted close -> accepted;
- raw close -> accepted;
- unknown basis -> fail;
- same date but invalid basis -> typed basis error, not misleading as-of error;
- stale date -> as-of error independently;
- unavailable quote -> availability error independently.

No investment-decision changes.

---

# Workstream D — macro publication-freshness presentation

## 13. Current result

Treasury tenors are restored.

WTI is also restored but the displayed latest observation is:

`2026-09-15`

for a 2026-09-23 message.

The market model already correctly says it did not use the lagged oil observation for
current direction.

The user still wants WTI visible, so encode this honestly.

## 14. Typed freshness state

For macro daily series assign one of:

- `CURRENT_BY_PROVIDER_CALENDAR`
- `LATEST_PUBLISHED_WITH_LAG`
- `STALE_UNEXPECTED`

The provider's expected publication calendar/lag owns the classification.

Do not use an arbitrary N-day threshold.

User-facing behavior:

### CURRENT
Normal factual row.

### LATEST_PUBLISHED_WITH_LAG
May remain visible, but label it explicitly as latest published / delayed and show the
observation date.

### STALE_UNEXPECTED
Do not place it in the current factual block; show unavailable/stale only if useful.

Apply the same generic contract to Treasury/FRED daily series, WTI, real yield,
breakeven, spread and VIX as appropriate to their source owners.

Do not alter market direction from a lagged row.

---

# Workstream E — final transport policy

## 15. User-approved standing retry contract

The user explicitly updated the standing Thesis Monitor transport policy.

Use:

- model `gpt-5.6-sol`
- xhigh
- **600 seconds (10 minutes) per process attempt**
- maximum **3 attempts total per logical request**
  - first attempt
  - byte-identical transient retry #1
  - byte-identical transient retry #2
- retries are permitted only for typed transient transport/process failures
- request bytes, schema, source bindings, upstream dependency hashes and logical-request identity must remain identical across retries
- no semantic/schema/source-use/policy/security/identity retry
- no result-driven prompt edit
- no source refresh between attempts
- no offline response substitution

If all three attempts fail for transient transport/process reasons:
- preserve all attempt receipts;
- mark that logical request failed;
- do not run a fourth attempt.

This **600s + two retries** policy supersedes the earlier 1200s + one-retry instruction
and is the standing policy for this task and future Thesis Monitor work unless the user
changes it again.

---

# Validation before model calls

## 16. Offline/focused gates

Before fresh full inference require:

### US OHLCV
- raw current bar parser fixture;
- request-window/session fixture;
- stale-cache failure fixture;
- current-session selection;
- 2026-09-04 stale row remains denied.

### KR sectors
- exact observed response-shape fixture;
- malformed response;
- session mismatch;
- KOSPI/KOSDAQ taxonomy ownership;
- deterministic ranking.

### Price basis
all tests from Workstream C.

### Macro freshness
- expected delayed release;
- unexpected stale release;
- weekend/holiday;
- no direction leakage from delayed row.

### Regression
- night D/W/M unchanged;
- stock support/resistance unchanged;
- R3/R4/R5/R6 decision semantics unchanged.

Run full pytest, Ruff and diff check.

Freeze implementation after PASS.

---

# Fresh full reproof

## 17. NEW fresh source generation

After code freeze collect a new generation.

Do not reuse Run 1 or Run 2 source rows as current.

Require explicit source receipts for:
- SPY/QQQ/IWM;
- US sector/style canonical universe;
- KR sectors;
- macro freshness states;
- all active stock quotes and price basis;
- KRX night D/W/M.

---

## 18. Pre-model information coverage gate

Before model calls require either:

### FULL
- current-session canonical US indices available;
- sufficient same-session US sectors for TOP3/BOTTOM3;
- KR sector ranking source available;
- 22/22 financial/stock source ready;
- 8/8 KR stock quote contexts renderable under typed basis.

or a separately documented truly upstream publication-unavailable state explicitly accepted
by Chat.

Do not auto-continue under `PARTIAL_USER_AUTHORIZED` in R6-R1.

The purpose is to prove the full information contract.

---

## 19. Fresh Market/Core/A/B

After full gate:

- Market 2;
- Core 22;
- A 22;
- B 22;

with the standing two-retry transport contract.

No target fitting.
No source refresh after model output.
No result-driven hotfix.

---

## 20. Exact 24-message capture

Expected:
- MARKET_US
- MARKET_KR
- 22 stocks

`24/24`

Require:

### MARKET_US
When source-owned and current:
- major indices;
- WTI with freshness state;
- 3Y/5Y/10Y/30Y;
- US +TOP3/-TOP3 sectors;
- market interpretation;
- KRX night D/W/M.

### MARKET_KR
- current index/breadth/flows;
- KR +TOP3/-TOP3 sectors under owned taxonomy;
- no incorrect night duplication.

### Stocks
For US and KR:
- Overall/New Buyer/Holder;
- price as-of;
- fundamental range if valid;
- technical support if valid;
- technical resistance if valid;
- tactical watch zone if valid.

No internal enums/refs/hashes.

---

## 21. Night regression gate

The already-working night behavior is mandatory:

KOSPI200:
- daily
- weekly current period
- monthly 16+ elapsed official sessions according to new reference date
- exact current reference calendar

KOSDAQ150:
same.

Do not hardcode `16/16`; recalculate expected elapsed sessions for the new run date.

Monthly return may remain unresolved if prior same-contract baseline remains unavailable.

---

## 22. Human review bundle

Create:

`m12ds-r6-r1-rendered-message-review.zip`

Include:
- exact 24 messages;
- US provider diagnostic/repair receipt;
- KR sector diagnostic/repair receipt;
- macro freshness receipt;
- price-basis contract/audit;
- support/resistance audit;
- night D/W/M E2E;
- message-quality audit;
- production-isolation receipt;
- full validation receipt.

Do not include credentials or unredacted provider secrets.

---

## 23. Acceptance

Full success:

`M12DS_R6_R1_FULL_INFORMATION_24_MESSAGE_PASS_READY_FOR_HUMAN_REVIEW`

Requires:
- source information contract full;
- Market/Core/A/B complete;
- 24/24 final captures;
- US indices and sector ranking restored;
- KR sector ranking restored;
- KR 8/8 stock messages accepted;
- macro lag display correct;
- support/resistance present where valid;
- night D/W/M PASS;
- full tests/lint PASS;
- production writes/sends 0.

No main merge in R6-R1.

---

## 24. Stop states

- `M12DS_R6_R1_US_PROVIDER_DIAGNOSIS_UNRESOLVED`
- `M12DS_R6_R1_US_UPSTREAM_SOURCE_UNAVAILABLE`
- `M12DS_R6_R1_KR_SECTOR_DIAGNOSIS_UNRESOLVED`
- `M12DS_R6_R1_KR_SECTOR_SOURCE_UNAVAILABLE`
- `M12DS_R6_R1_PRICE_BASIS_CONTRACT_FAILED`
- `M12DS_R6_R1_MACRO_FRESHNESS_CONTRACT_FAILED`
- `M12DS_R6_R1_INFORMATION_COVERAGE_INCOMPLETE`
- `M12DS_R6_R1_CURRENT_INFERENCE_INCOMPLETE`
- `M12DS_R6_R1_MESSAGE_CAPTURE_INCOMPLETE`
- `M12DS_R6_R1_NIGHT_REGRESSION`
- `M12DS_R6_R1_LOCAL_VALIDATION_FAILED`
- `M12DS_R6_R1_JUDGMENT_POLICY_SCOPE_EXPANSION_REQUIRES_CHAT`

Return exact evidence. Do not relax source/currentness rules to pass.

---

## 25. After approval

If R6-R1 exact messages are accepted by the user:

1. bounded R6 main integration + CI/replay;
2. then proceed to:
   `M12DT_NEW_TICKER_ONBOARDING_GATE`.

