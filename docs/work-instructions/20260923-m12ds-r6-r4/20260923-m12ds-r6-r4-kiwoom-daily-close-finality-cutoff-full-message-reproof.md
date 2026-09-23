# Thesis Monitor — M12DS-R6-R4 Kiwoom Daily-Close Finality + Real Cutoff Proof + Full 24-Message Reproof

**Suggested work-instruction filename:**
`20260923-m12ds-r6-r4-kiwoom-daily-close-finality-cutoff-full-message-reproof.md`

**Suggested result bundle:**
`thesis-monitor-20260923-m12ds-r6-r4-kiwoom-daily-close-finality-cutoff-full-message-reproof-report.zip`

**Required review bundle on full success:**
`m12ds-r6-r4-rendered-message-review.zip` + `.sha256`

**Task ID:** `M12DS-R6-R4-20260923`

---

## 0. Objective

R6-R3-REV1 established:

1. Kiwoom official `usa06012` is explicitly **미국주식 일 차트**.
2. Its dated daily row contains O/H/L plus:
   `cur_prc = 현재가(종가)`.
3. Therefore row-local `cur_prc` is approved as the **daily-row close semantic** in the
   `usa06012` daily context.
4. Generic quote `cur_prc` remains `CURRENT_QUOTE`.
5. KR post-close completed-session sector ownership is fully proven for KOSPI/KOSDAQ.
6. Alpha Vantage existing account is not sustainable under the current production
   collection design and is removed from the active route for this task.

Remaining US questions only:

- does `usa06012` daily-row close represent the regular-session close rather than a value
  that can be changed by extended-hours activity?
- is the target completed-session row available by the actual configured source cutoff:
  08:05 / 08:10 / 08:15 / 08:20 KST?
- what is the correct exchange-routing owner for the canonical ETF universe?

R6-R4 closes those points using the existing Kiwoom route only.

When they pass, continue immediately through the fresh full-information
Market/Core/A/B + exact 24-message capture.

No Alpha Vantage calls.
No new provider.
No investment-policy change.
No main merge in R6-R4.

---

## 1. Baseline

Use `m12ds-r6-r4-baseline.json`.

Operating main:

`2097645892e30d84aba435416f98e7f9545a87fa`

Continue from:

`e25e41baf231318b873adf62cab8433eeded5b0e`

R6-R3-REV1 report SHA-256:

`e62452cc3d736b0e5af30daa8c58ac495d88d22320e25c41816058591456c88f`

Preserve:
- official usa06012 schema extraction;
- KR post-close receipts;
- all prior R6 source/message contracts;
- zero production mutation.

---

# Workstream A — canonical Kiwoom ETF exchange routing

## 2. Do not repeat SPY/NA

The R6-R3-REV1 direct `SPY/NA` call returned provider code 7.

This was explicitly classified as an unresolved/wrong exchange-routing probe, not as
proof that SPY is unsupported.

Do not hardcode `NA`.

---

## 3. Resolve exchange ownership from existing approved routes

Inspect the exact successful production/gateway route that previously returned SPY and the
other market ETFs.

Preferred ownership sources:

1. existing symbol/security metadata already used by the OHLCV analyst;
2. existing provider security-master/list response if already approved read-only;
3. existing deterministic symbol-to-exchange registry.

A bounded existing Kiwoom identity/list route may be used if necessary, but it must only
resolve exchange identity; it cannot become price authority.

For every required symbol record:

- symbol;
- security identity;
- Kiwoom exchange code required by usa06012;
- identity source;
- evidence hash.

Required universe includes at least:

- SPY
- QQQ
- IWM
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

plus any other canonical R6 US market rows required by the current market contract.

Create:

`kiwoom-us-etf-exchange-routing.json`

No ticker-specific guesses.

---

# Workstream B — daily-row close semantic is now frozen

## 4. Preserve context-specific mapping

Official schema:

- API: `미국주식 일 차트 (usa06012)`
- row date: `dt`
- O/H/L: `open_pric / high_pric / low_pric`
- row close: `cur_prc`, official label `현재가(종가)`

This semantic mapping is accepted **only within the dated usa06012 daily-row context**.

Add/retain negative controls:
- generic quote `cur_prc` is not daily close;
- sector/current quote `cur_prc` is not daily close;
- missing `dt` cannot create a daily-bar owner.

Do not reopen this question unless contradictory provider evidence is found.

---

# Workstream C — regular-session finality / extended-hours isolation

## 5. Exact question

The remaining finality question is not whether the field is a close.

It is:

> Does the usa06012 dated daily-row close remain the regular-session close after 16:00 ET,
> or can pre-/after-market trading mutate that same dated row?

Do not answer from wall-clock assumption alone.

---

## 6. Search existing exact-time evidence first

Before creating new calls, inspect already-existing local raw receipts/logs/caches for a
usa06012 response captured during an actual production source window:

- 08:05
- 08:10
- 08:15
- 08:20 KST

Use only evidence that owns:
- actual acquisition timestamp;
- provider/action;
- request identity;
- symbol/exchange route;
- raw response or trustworthy payload hash;
- target completed-session row.

Do not infer acquisition time solely from a copied file timestamp if ownership is
ambiguous.

Historical evidence from the prior R6 run may qualify if the original raw receipt is still
available and unambiguous.

If exact cutoff evidence exists, use it rather than waiting for a future day.

---

## 7. Extended-hours cross-context proof

Use a bounded read-only comparison where timing permits.

At a time when the US regular market is closed but extended-hours/pre-market is active:

1. fetch usa06012 daily row through the correct exchange route;
2. fetch an already-approved current-quote context separately;
3. preserve both raw hashes and timestamps;
4. repeat the daily-row fetch at least once after a short interval if the current quote
   changes or market activity is observable.

Strong supporting evidence is:

- current quote changes in extended hours;
- usa06012 latest completed-session row date/O/H/L/C remains unchanged.

If the quote does not change, absence of a change is not by itself conclusive.

Do not require current-quote movement if official provider documentation independently
establishes regular-session-only daily bars.

---

## 8. Previous-close consistency proof

Where an existing approved Kiwoom context exposes a previous regular-session close or an
equivalent deterministic relationship:

compare it against the usa06012 prior completed-session daily close.

Requirements:
- same security;
- same raw/adjusted basis;
- exact session date ownership.

This is qualification evidence only; no next-day lookahead dependency may be introduced
into the production algorithm.

---

## 9. Finality acceptance

Accept:

`SETTLED_REGULAR_SESSION_CLOSE`

for the target dated usa06012 row only if the evidence jointly supports:

- daily-row close semantic from official schema;
- exchange calendar says target regular session is CLOSED;
- extended-hours activity does not mutate the completed daily row, or official source
  semantics explicitly exclude extended-hours from that row;
- row date equals the latest completed US regular session.

Create:

`us-regular-session-close-kiwoom-daily-v1`

No global `cur_prc` reinterpretation.

---

# Workstream D — real production cutoff

## 10. Required cutoff

Production source attempts are:

- 08:05 KST
- 08:10 KST
- 08:15 KST
- 08:20 KST

The selected daily-close route must expose the immediately preceding completed US session
by an existing configured attempt.

---

## 11. Existing historical cutoff receipt path

If Workstream C finds a real historical cutoff receipt:

validate for the entire required universe, not only SPY.

Require:
- each canonical symbol route;
- target completed-session date;
- current daily close;
- previous same-basis daily close;
- no stale fallback;
- acquisition timestamp within an existing configured window.

If the historical evidence covers only a subset, it cannot establish full production
cutoff readiness.

---

## 12. If historical cutoff evidence is incomplete

Do not infer availability from an afternoon request.

Create a bounded **manual read-only cutoff observer** for the next real configured window.

The observer:
- does not enable launchd;
- does not enable production schedules;
- does not send messages;
- does not run model inference;
- uses the exact frozen Kiwoom request/route contract;
- records each configured cutoff attempt;
- stops once the full target completed session universe is available.

At each attempt preserve:
- actual KST/UTC/ET timestamp;
- exchange-calendar completed-session target;
- symbol;
- route/exchange code;
- latest usa06012 row date;
- current and previous daily close;
- raw hash;
- provider status.

Standing provider/model retry semantics remain separate from the scheduled cutoff gates.

If current execution is outside the cutoff window and no historical receipt exists:

finish all semantic/finality/offline work and stop:

`M12DS_R6_R4_KIWOOM_FINALITY_PASS_CUTOFF_OBSERVATION_PENDING`

Do not call Market/Core/A/B.

---

# Workstream E — full universe and sector ranking

## 13. Full US current-session universe

After finality + cutoff proof require:

- SPY / QQQ / IWM
- complete canonical sector universe
- any additional canonical style/market rows required by current R6 contract

all own the same completed regular session.

Current and previous close:
- same provider;
- same endpoint semantic;
- same price basis.

No stale 09/04 substitution.

---

## 14. US deterministic sector TOP3/BOTTOM3

From the qualified same-session canonical sector rows:

- TOP3
- BOTTOM3

Deterministic numeric return.
Stable tie-break.
No model ranking.

XLC must not be silently omitted.

---

# Workstream F — carry forward KR post-close PASS

## 15. Frozen KR authority

R6-R3-REV1 already proved:

`kr-post-close-sector-session-v1`

for both KOSPI and KOSDAQ with:
- CLOSED state;
- after-close collection;
- ka20001/ka20009 exact level + return parity;
- complete ka20003 sector snapshot;
- no tolerance;
- deterministic TOP3/BOTTOM3.

Preserve the qualification receipt.

In the final fresh generation, collect/bind the current run's KR data under the same
contract; do not simply copy the old numeric values forward.

---

## 16. KR final rankings

Final message factual blocks must show separately:

### KOSPI
- TOP3
- BOTTOM3

### KOSDAQ
- TOP3
- BOTTOM3

same-session only.
No cross-venue ranking mix.

---

# Workstream G — preserve all other R6 closures

## 17. KR stock quote basis

Preserve:

`adjusted_intraday = INTRADAY + ADJUSTED`

Fresh final proof must accept all 8 KR stock messages.

---

## 18. Night futures

Preserve official KRX:
- daily;
- weekly in-progress;
- month-to-date history;
- elapsed/expected coverage;
- D/W/M final-message E2E.

Recalculate for final source date.

---

## 19. Stock price structure

Preserve distinct:
- fundamental range;
- technical support;
- technical resistance;
- tactical watch zone.

---

## 20. Macro display

Preserve current-direction strictness.

Implement the already-authorized informational block for valid lagged observations:

`최신 확인값 (기준 YYYY-MM-DD)`

with no direction refs.

WTI may be shown there when source/value/date are valid but not current-direction
eligible.

---

# Workstream H — validation

## 21. Required tests

### Kiwoom
- official daily-row semantic fixture;
- quote-context negative control;
- correct exchange routing;
- wrong exchange denied;
- after-hours isolation/finality;
- same-basis previous close;
- full ETF universe;
- stale row denied;
- cutoff receipt validation;
- no lookahead requirement.

### KR
- frozen post-close owner regression;
- venue separation;
- deterministic rankings.

### R6 regression
- KR8 quote basis;
- macro informational/current separation;
- night D/W/M;
- support/resistance;
- investment policy unchanged.

Run:
- focused pytest;
- full pytest in clean environment;
- Ruff;
- diff check;
- Knowledge/Public Action checks.

Do not treat shell environment contamination as a product failure; preserve any first-run
environment failure separately and require a clean-environment same-code PASS.

No new skip/xfail.

---

# Workstream I — pre-model information gate

## 22. Required before inference

### US
- Kiwoom daily-row finality PASS;
- actual cutoff availability PASS;
- full canonical universe;
- current-session deterministic sector ranking.

### KR
- same-day post-close owner under fresh source generation;
- KOSPI/KOSDAQ rankings;
- 8/8 quote/basis context.

### Macro/night
- Treasury and WTI display classification;
- KRX night D/W/M.

No model calls if any mandatory block is missing.

---

# Workstream J — fresh full reproof

## 23. NEW fresh generation

Only after the complete source gate passes:

start a new fresh generation.

Freeze:
- code SHA;
- source generation;
- exact cutoff receipt;
- Kiwoom routing map;
- source authority receipts;
- requests.

No Alpha Vantage.

---

## 24. Market/Core/A/B

Run:

- Market 2/2
- Core 22/22
- A 22/22
- B 22/22

Standing transport policy:

- 600 seconds per attempt;
- first attempt + up to 2 byte-identical transient retries;
- max 3 attempts total;
- no fourth attempt;
- no retry for schema/semantic/source-use/policy/security/identity;
- no source refresh between retries;
- no offline substitution.

---

## 25. Exact 24-message capture

At the real final outbound boundary, sends disabled:

- MARKET_US
- MARKET_KR
- 22 stock messages

Require:

`24/24`

### MARKET_US
- major indices;
- US sector TOP3/BOTTOM3;
- Treasury 3Y/5Y/10Y/30Y;
- WTI current/latest-available label + date;
- market interpretation;
- KRX night D/W/M.

### MARKET_KR
- completed-session indices/breadth/flows;
- KOSPI TOP3/BOTTOM3;
- KOSDAQ TOP3/BOTTOM3.

### Every stock
- Overall;
- New Buyer;
- Holder;
- price as-of;
- fundamental range if valid;
- technical support if valid;
- technical resistance if valid;
- tactical watch zone if valid.

No internal refs/enums/hashes.

---

## 26. Review bundle

Create:

`m12ds-r6-r4-rendered-message-review.zip`

Include:
- exact 24 messages;
- Kiwoom official semantic receipt;
- exchange-routing receipt;
- finality/extended-hours proof;
- actual cutoff proof;
- full US universe audit;
- US/KR sector rankings;
- KR8 final capture proof;
- macro display/direction audit;
- night D/W/M E2E;
- production isolation;
- full validation.

---

## 27. Production isolation

Must remain zero:
- actual send;
- recipient intent;
- DB decision/warning write;
- scheduler mutation;
- notification mutation;
- broker action;
- deploy.

Do not enable the currently disabled production schedulers.

---

## 28. Full-success terminal

`M12DS_R6_R4_KIWOOM_DAILY_CLOSE_24_MESSAGE_PASS_READY_FOR_HUMAN_REVIEW`

Requires:
- Kiwoom daily close semantic + finality PASS;
- cutoff PASS;
- full US universe;
- US sector rankings;
- KR post-close owner + rankings;
- fresh Market/Core/A/B;
- 24/24 capture;
- night D/W/M PASS;
- full validation;
- production mutations 0.

---

## 29. Stop states

- `M12DS_R6_R4_KIWOOM_EXCHANGE_ROUTING_UNRESOLVED`
- `M12DS_R6_R4_KIWOOM_FINALITY_UNRESOLVED`
- `M12DS_R6_R4_KIWOOM_FINALITY_PASS_CUTOFF_OBSERVATION_PENDING`
- `M12DS_R6_R4_KIWOOM_CUTOFF_UNAVAILABLE`
- `M12DS_R6_R4_US_UNIVERSE_INCOMPLETE`
- `M12DS_R6_R4_KR_POST_CLOSE_REGRESSION`
- `M12DS_R6_R4_INFORMATION_COVERAGE_INCOMPLETE`
- `M12DS_R6_R4_CURRENT_INFERENCE_INCOMPLETE`
- `M12DS_R6_R4_MESSAGE_CAPTURE_INCOMPLETE`
- `M12DS_R6_R4_LOCAL_VALIDATION_FAILED`
- `M12DS_R6_R4_JUDGMENT_POLICY_SCOPE_EXPANSION_REQUIRES_CHAT`

Do not reintroduce Alpha or another provider in this task.

---

## 30. After human approval

After the exact 24 messages are reviewed and approved:

1. bounded R6 main integration + remote CI/replay;
2. then:
   `M12DT_NEW_TICKER_ONBOARDING_GATE`.
