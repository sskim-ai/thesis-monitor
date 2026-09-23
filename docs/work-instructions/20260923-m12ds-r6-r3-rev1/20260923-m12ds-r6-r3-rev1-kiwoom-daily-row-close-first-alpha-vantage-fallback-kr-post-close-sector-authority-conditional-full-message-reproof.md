# Thesis Monitor — M12DS-R6-R3-REV1 Kiwoom Daily-Row Close Qualification First + Alpha Vantage Fallback + KR Post-Close Sector Authority + Conditional Full 24-Message Reproof

**Suggested work-instruction filename:**  
`20260923-m12ds-r6-r3-rev1-kiwoom-daily-row-close-first-alpha-vantage-fallback-kr-post-close-sector-authority-conditional-full-message-reproof.md`

**Suggested result bundle:**  
`thesis-monitor-20260923-m12ds-r6-r3-rev1-kiwoom-daily-row-close-first-alpha-vantage-fallback-kr-post-close-sector-authority-conditional-full-message-reproof-report.zip`

**Required review bundle on full success:**  
`m12ds-r6-r3-rev1-rendered-message-review.zip` + `.sha256`

**Task ID:** `M12DS-R6-R3-REV1-20260923`

---

## 0. Authorization and objective

R6-R2 correctly stopped because the latest US row was carried only as
`CURRENT_QUOTE`, not as an owned `SETTLED_REGULAR_SESSION_CLOSE`.

The user has now clarified the preferred interpretation:

> If the existing Kiwoom `usa06012` OHLCV/daily-chart response is truly a dated daily
> candle and its row-local `cur_prc` is the close field of that daily candle, use the
> OHLCV daily-row close rather than introducing another provider.

Therefore the US route priority is now:

1. **FIRST: qualify the existing Kiwoom `usa06012` dated daily-row close semantics.**
2. **ONLY IF that cannot be proven:** qualify the already-configured Alpha Vantage
   account as a bounded fallback candidate.
3. Do not add any new API key, paid subscription, or new external provider.

This task must distinguish:

- generic/current quote semantics; from
- a `cur_prc` field located **inside a dated daily OHLCV row**.

The same field name does not imply the same semantic role in different response
structures.

In parallel, close KR same-day post-close sector ownership using the already-configured
Kiwoom routes.

If US completed-session close authority and KR post-close authority both pass, continue
through the fresh full-information Market/Core/A/B + exact 24-message capture.

Do not change investment judgment policy.

Do not merge main in R6-R3-REV1.

---

## 1. Baseline

Operating main:

`2097645892e30d84aba435416f98e7f9545a87fa`

Continue from R6-R2 final local branch state:

`d70b18f4619ffb0988236c3620a2841c59cb424d`

R6-R2 report SHA-256:

`fa9c63acb5f1a3dd5db25b403802afcfbd4c5eebfd43188a95fc10850259665e`

R6-R2 model calls:
`0`

R6-R2 new messages:
`0`

Preserve all previous status honestly.

Use `m12ds-r6-r3-rev1-baseline.json`.

---

# Phase A — Kiwoom `usa06012` daily-row semantic qualification

## 2. Prove the endpoint/response context before changing ownership

Inspect the exact existing Kiwoom route used by the OHLCV analyst:

`usa06012`

Record from the official Kiwoom documentation and the actual response/parser:

- API title/endpoint identity;
- whether the endpoint is explicitly daily chart / daily OHLCV / daily price history;
- request parameters that select the daily interval;
- row date field;
- row-local:
  - open;
  - high;
  - low;
  - `cur_prc`;
  - volume;
- ordering of rows;
- exchange/session date semantics;
- whether extended-hours trades are included in the daily row;
- whether the latest row remains mutable after the regular close.

Create:

`kiwoom-usa06012-daily-row-semantic-audit.json`

Do not change code before this audit exists.

---

## 3. Context-specific `cur_prc` interpretation

Do NOT globally relabel Kiwoom `cur_prc` as close.

A mapping is allowed only inside the proven dated daily-row schema.

Target typed interpretation:

`usa06012 dated DAILY_BAR row`
→ `open`
→ `high`
→ `low`
→ `close = row-local cur_prc`
→ `volume`

only if the official endpoint semantics and live behavior prove that the row-local
`cur_prc` is the daily candle close.

Generic/current quote endpoints must remain:

`CURRENT_QUOTE`

and must never inherit this mapping.

Add negative tests proving the same key name in a quote response is not treated as close.

---

## 4. Regular-session-only finality

A daily row must not become `SETTLED_REGULAR_SESSION_CLOSE` merely because:
- it has a date;
- the wall clock is after 16:00 ET;
- it is the latest row.

Prove whether the `usa06012` daily candle is a regular-session bar and whether after-hours
trades can mutate the row.

Use all available non-destructive evidence:

### A. Official documentation/schema
Prefer explicit provider documentation that the endpoint is regular-session daily OHLCV
and that row-local close represents that session's daily close.

### B. Existing parser/source behavior
Confirm the production parser already treats the row as an OHLCV candle for historical
daily analytics.

### C. Cross-context live check
When possible during the US after-hours window:
- capture `usa06012` latest dated daily row;
- capture a separate current-quote owner;
- if current quote changes while the daily row remains fixed, preserve the receipt.

This is supporting evidence, not a substitute for source semantics.

### D. Next-session previous-close check
If an already approved route exposes the next session's previous regular close,
compare it to the prior `usa06012` daily-row close under the same raw/adjusted basis.

Do not introduce lookahead into production. This comparison is qualification evidence
only.

---

## 5. Kiwoom acceptance criteria

Kiwoom may become the US completed-close owner only if all are proven:

- row is a dated daily candle;
- row-local `cur_prc` is the daily close field in that context;
- daily row excludes/does not mutate from after-hours trades, or the provider explicitly
  defines it as regular-session daily close;
- exact target exchange session date is owned;
- current and previous daily closes use the same basis;
- SPY / QQQ / IWM and the full canonical sector ETF universe are supported;
- data is available at the actual configured 08:05/08:10/08:15/08:20 KST collection
  window without needing the next trading day's row.

If all pass, create:

`us-regular-session-close-kiwoom-daily-v1`

binding:
- symbol;
- provider/action = Kiwoom `usa06012`;
- row date;
- daily OHLCV;
- close field provenance;
- previous session date/close;
- basis;
- finality;
- raw response SHA;
- parser contract/version.

Then **skip Alpha Vantage entirely**.

---

## 6. If Kiwoom semantics cannot be proven

Classify the reason exactly:

- `DAILY_ROW_CLOSE_SEMANTIC_UNPROVEN`
- `AFTER_HOURS_CONTAMINATION_POSSIBLE`
- `CUTOFF_PUBLICATION_UNAVAILABLE`
- `UNIVERSE_COVERAGE_INCOMPLETE`
- `BASIS_INCOMPATIBLE`
- `OTHER_TYPED_REASON`

Do not weaken the contract.

Only then proceed to Phase B.

---

# Phase B — Alpha Vantage fallback qualification, only if Phase A fails

## 7. Authorization boundary

The user authorizes only the repository's already-configured Alpha Vantage
credential/account as a fallback qualification candidate.

Allowed:
- documentation/schema review;
- bounded read-only live qualification;
- narrow typed EOD adapter only after qualification passes.

Not authorized:
- new API key;
- paid upgrade;
- credential replacement;
- another external provider.

---

## 8. Preferred Alpha Vantage endpoint

Prefer:

`TIME_SERIES_DAILY`

because the semantic target is a completed regular-session daily close.

`TIME_SERIES_DAILY_ADJUSTED` may be inspected only if:
- current account entitlement exists;
- adjustment semantics are necessary.

`GLOBAL_QUOTE` may be inspected as supporting metadata only.

Do not treat GLOBAL_QUOTE as settled close unless its semantics independently prove that.

---

## 9. Required fallback universe

At minimum:

### Major/style
- SPY
- QQQ
- IWM

### Sectors
- XLB
- XLC
- XLE
- XLF
- XLI
- XLK
- XLP
- XLRE
- XLU
- XLV
- XLY

Include any additional canonical R6 US sector symbols.

Do not shrink the universe to fit a rate limit.

---

## 10. Alpha Vantage semantic and account qualification

For each required symbol prove:

- endpoint;
- latest daily date;
- O/H/L/C semantics;
- regular-session-only close semantics;
- provider timezone;
- current/previous session dates;
- raw/adjusted basis;
- ETF support;
- response completeness;
- source row hash;
- account entitlement;
- calls needed for full production universe;
- sustainable rate limit.

Current and previous close must share one basis.

If account/limit is insufficient:

`M12DS_R6_R3_REV1_ALPHA_VANTAGE_ACCOUNT_INSUFFICIENT`

No upgrade.

---

## 11. Real 08:05 KST cutoff proof

A later successful response does not prove availability at the production cutoff.

For the selected US route (Kiwoom if Phase A passes, otherwise Alpha Vantage), prove
availability at an existing configured source attempt:

- 08:05 KST
- 08:10 KST
- 08:15 KST
- 08:20 KST

Record:
- actual timestamp KST/UTC/ET;
- target completed US session;
- newest daily row date;
- current and previous daily close;
- full-universe availability;
- raw response hashes;
- transient/rate-limit state.

If the task is not running during this window:
- finish semantic/offline qualification;
- do not infer cutoff timing from a later call;
- stop with:

`M12DS_R6_R3_REV1_US_SEMANTICS_PASS_CUTOFF_OBSERVATION_PENDING`

No model calls.

---

# Phase C — KR same-day post-close sector authority

## 12. Timing

Configured KR source attempts:

- 16:05
- 16:20
- 16:50 KST

KR regular close:
- 15:30 KST

A live proof is valid only after official exchange session state is CLOSED.

If run before close, defer the parity proof; do not fabricate it.

---

## 13. Existing KR route

Use only:

- `ka20001` current composite index
- `ka20003` venue-sector snapshot
- `ka20009` date-owned composite index history

for KOSPI/KOSDAQ separately.

No new KR provider.

---

## 14. Same-day parity

After close prove:

1. exchange state = CLOSED;
2. collection timestamp > 15:30;
3. `ka20001` owns same-day completed composite;
4. `ka20009` owns the same exact date;
5. exact index level parity under current representation;
6. exact return parity;
7. venue identity;
8. `ka20003` sector snapshot binds to the same completed session.

No new tolerance.

If parity fails:

`M12DS_R6_R3_REV1_KR_POST_CLOSE_PARITY_FAILED`

---

## 15. KR deterministic sector rankings

After parity passes:

- KOSPI TOP3 / BOTTOM3
- KOSDAQ TOP3 / BOTTOM3

same-session only.

Stable tie-break.
No model ranking.
No cross-venue taxonomy mixing.

Create:

`kr-post-close-sector-session-v1`

---

# Phase D — preserve already-closed R6 contracts

## 16. KR stock price basis

Preserve:

`adjusted_intraday = INTRADAY + ADJUSTED`

Require fresh final-message capture for all 8 KR stocks.

---

## 17. Night futures D/W/M

Preserve official KRX authority and current behavior:

- daily;
- weekly in-progress OHLC;
- elapsed/expected sessions;
- month-to-date official history;
- monthly OHLC;
- unresolved monthly return if no same-contract prior-month baseline.

Recompute for the fresh run date.

---

## 18. Stock technical levels

Preserve separately:

- fundamental range;
- technical support;
- technical resistance;
- tactical watch zone.

No technical/tactical range may be called fair value.

---

# Phase E — macro current versus latest-available display

## 19. Direction evidence remains strict

Only source-owned current facts may influence market direction.

Lagged WTI or another delayed macro row cannot become current-direction evidence.

---

## 20. Latest-available informational display

A valid but non-current macro observation may be shown in a separate factual block:

`최신 확인값 (기준 YYYY-MM-DD)`

with:
- exact value;
- owned observation date;
- source provenance;
- explicit separation from current-direction inference.

Do not display malformed/untrusted values.

---

# Phase F — offline validation

## 21. Kiwoom-specific tests

Before final live run add:

- dated daily-row fixture maps row-local `cur_prc` to close only inside `usa06012`
  daily context;
- generic quote `cur_prc` remains CURRENT_QUOTE;
- latest daily row same-basis current/previous close;
- after-hours contamination negative control;
- missing date;
- wrong interval;
- stale latest row;
- ETF universe coverage;
- no lookahead dependency.

---

## 22. Alpha Vantage fallback tests

Only if fallback path is needed:

- TIME_SERIES_DAILY semantics;
- same-basis pair;
- ETF universe;
- malformed response;
- entitlement/rate limit;
- adjusted/raw mismatch;
- no accidental GLOBAL_QUOTE promotion.

---

## 23. KR / regression tests

Require:
- CLOSED/post-close parity;
- before-close denial;
- index identity/date mismatch;
- KOSPI/KOSDAQ separation;
- deterministic ranking;
- KR8 adjusted_intraday basis;
- macro display/direction separation;
- night D/W/M;
- support/resistance;
- investment policy unchanged.

Run:
- focused pytest;
- full pytest;
- Ruff;
- diff check.

No new skip/xfail.

---

# Phase G — pre-model full-information gate

## 24. US gate

Require one qualified US source route:

### Preferred
`Kiwoom usa06012 daily-row close`

### Fallback
`Alpha Vantage TIME_SERIES_DAILY`

and require:
- current completed session at actual configured cutoff;
- SPY/QQQ/IWM;
- full canonical sector universe;
- same-basis previous close;
- deterministic sector TOP3/BOTTOM3.

Do not combine two providers for current/previous close unless an explicit reconciliation
owner exists.

---

## 25. KR gate

Require:
- post-close parity PASS;
- KOSPI/KOSDAQ completed-session sector rankings;
- 8/8 quote/basis contexts;
- all existing financial/source gates.

---

## 26. Macro / night gate

Require:
- Treasury 3Y/5Y/10Y/30Y display;
- WTI current/latest-available classification;
- strict direction-evidence separation;
- current KRX night D/W/M typed facts.

No model calls until the whole information gate passes.

---

# Phase H — fresh full production-equivalent reproof

## 27. NEW source generation

After code/source-contract freeze:

start a new fresh generation.

Do not silently reuse qualification probes unless they are explicitly incorporated into
the frozen final generation under the same typed owner.

Freeze:
- code SHA;
- source generation;
- cutoff receipt;
- selected US provider/route;
- source authority receipts;
- request hashes.

---

## 28. Market/Core/A/B

Run:

- Market 2/2
- Core 22/22
- A 22/22
- B 22/22

Standing transport policy:

- 600 seconds per process attempt;
- first attempt + up to 2 byte-identical transient retries;
- maximum 3 attempts total;
- no fourth attempt;
- no retry for schema/semantic/source-use/policy/security/identity;
- no source refresh between retries;
- no offline substitution.

---

## 29. Exact 24-message capture

At the actual final outbound boundary with sending disabled:

- MARKET_US
- MARKET_KR
- 22 stock messages

Require:

`24/24`

### MARKET_US
when owned:
- major indices;
- sector TOP3/BOTTOM3;
- Treasury 3Y/5Y/10Y/30Y;
- WTI current/latest-available label + date;
- market interpretation;
- KRX night D/W/M.

### MARKET_KR
- completed-session index/breadth/flows;
- KOSPI TOP3/BOTTOM3;
- KOSDAQ TOP3/BOTTOM3;
- no intraday/completed mixing.

### Every stock
- Overall;
- New Buyer;
- Holder;
- price as-of;
- fundamental range if valid;
- technical support if valid;
- technical resistance if valid;
- tactical watch zone if valid.

---

## 30. Review bundle

On success create:

`m12ds-r6-r3-rev1-rendered-message-review.zip`

Include:
- exact 24 texts;
- Kiwoom daily-row semantic audit;
- selected US source/cutoff receipt;
- Alpha Vantage qualification only if used;
- KR post-close parity;
- sector-ranking audit;
- macro display/direction separation;
- KR8 final capture proof;
- night D/W/M E2E;
- production isolation;
- full validation.

No credentials.

---

## 31. Production isolation

Must remain zero:

- actual send;
- recipient intent;
- DB decision/warning write;
- scheduler mutation;
- notification mutation;
- broker action;
- deploy.

Do not enable the currently disabled production launchd jobs.

Cutoff/qualification probes are manual bounded read-only calls only.

---

## 32. Full-success terminal

`M12DS_R6_R3_REV1_KIWOOM_FIRST_US_KR_AUTHORITY_24_MESSAGE_PASS_READY_FOR_HUMAN_REVIEW`

Requires:
- selected US route semantic PASS;
- actual cutoff availability PASS;
- full US universe;
- KR post-close parity PASS;
- US/KR sector rankings;
- fresh Market/Core/A/B;
- 24/24 final messages;
- night D/W/M PASS;
- tests/lint PASS;
- production mutation 0.

---

## 33. Other terminals

- `M12DS_R6_R3_REV1_KIWOOM_DAILY_CLOSE_QUALIFICATION_FAILED`
- `M12DS_R6_R3_REV1_ALPHA_VANTAGE_QUALIFICATION_FAILED`
- `M12DS_R6_R3_REV1_ALPHA_VANTAGE_ACCOUNT_INSUFFICIENT`
- `M12DS_R6_R3_REV1_US_SEMANTICS_PASS_CUTOFF_OBSERVATION_PENDING`
- `M12DS_R6_R3_REV1_US_CUTOFF_UNAVAILABLE`
- `M12DS_R6_R3_REV1_KR_POST_CLOSE_PARITY_PENDING`
- `M12DS_R6_R3_REV1_KR_POST_CLOSE_PARITY_FAILED`
- `M12DS_R6_R3_REV1_INFORMATION_COVERAGE_INCOMPLETE`
- `M12DS_R6_R3_REV1_CURRENT_INFERENCE_INCOMPLETE`
- `M12DS_R6_R3_REV1_MESSAGE_CAPTURE_INCOMPLETE`
- `M12DS_R6_R3_REV1_LOCAL_VALIDATION_FAILED`
- `M12DS_R6_R3_REV1_JUDGMENT_POLICY_SCOPE_EXPANSION_REQUIRES_CHAT`

No new provider/subscription.
No source-currentness weakening.

---

## 34. After human approval

After exact 24 messages are reviewed and approved:

1. bounded R6 integration to main + CI/replay;
2. then:
   `M12DT_NEW_TICKER_ONBOARDING_GATE`.
