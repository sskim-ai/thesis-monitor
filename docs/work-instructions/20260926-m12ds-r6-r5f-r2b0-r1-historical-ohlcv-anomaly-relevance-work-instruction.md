# Thesis Monitor — M12DS-R6-R5F-R2B0-R1
## Historical OHLCV Anomaly Relevance / Scoped Fail-Closed Repair
### Reuse the sealed 88/88 acquisition; do not recollect or repair provider values

**Purpose:** resolve the R2B0 CPNG historical OHLC anomaly without changing provider values and without recollecting the 88 stock roles. Preserve the malformed source row exactly, determine whether each anomalous row is actually consumed by the current production-equivalent analysis graph, and fail only the affected analysis component when the anomaly is relevant.

---

# 0. Newest accepted SoT

Adopt R2B0 as the newest SoT for this scope.

R2B0 result ZIP SHA-256:

`addb050b835f79cf89a5eac05e9bf7fc63fcf32991e1d467be0f61875ea8fa96`

Terminal:

`M12DS_R6_R5F_R2B0_ONE_SHOT_SOURCE_ACQUISITION_PARTIAL`

Repository identities:

- base:
  `fdc1a1e69f3941676927b38c4d81ba4b4d6d369c`
- instruction:
  `80debb5f5ae8b24491b46b52cea863efd483ef99`
- implementation:
  `5d089f8bae0b1ab4eed93cd076e04cb3cc359d9b`
- final:
  `90ccfeed21c4fd1b2ced4fa1c4e312a9cd7c4eaa`
- operating main:
  `b610e6de0a8c33d199961e821ff1b130e1fa9ad4`

Accepted acquisition facts:

- logical stock-role acquisitions: `88/88 attempted`
- provider chart pages: `290`
- auth: `1`
- total transports: `291`
- original HTTP/data responses: all HTTP 200 / provider `return_code=0`
- native raw-owner replay: `88/88`
- usable role receipts under the old whole-payload integrity rule:
  - US `53/56`
  - KR `32/32`
  - total `85/88`
- retries: `0`
- fallback: `0`
- Alpha Vantage: `0`
- Massive: `0`
- mock/symbol-discovery/investor-flow calls: `0`

Do not recollect these 88 logical roles.

---

# 1. Exact source anomaly to preserve

The provider supplied the following malformed historical rows.

## CPNG adjusted_daily

Date:
`2023-06-05`

Provider/raw values:

- open = `16.35`
- high = `15.80`
- low = `15.43`
- close = `15.66`

Violation:

`HIGH_LT_OPEN`

Raw source SHA-256:

`3ea9c72c51fbad3770618bbafc989a54baff97628cc668789e410c0ca6550013`

Normalized row fingerprint:

`c1675848f004836f9e5d79a81164c2dcc5267364d1c877d155eedd42cbfc5b6b`

## CPNG adjusted_weekly

Date:
`2023-06-05`

Provider/raw values:

- open = `16.35`
- high = `16.20`
- low = `15.43`
- close = `16.01`

Violation:

`HIGH_LT_OPEN`

Raw source SHA-256:

`0f47cef592777cf6d5e8fe27c5ed709677109ab5ff0d66bf863eeef95183f34f`

Normalized row fingerprint:

`14e9ced1fbdd4d797c3e6b0fea4e156a2144db8c1876cf7de36b52bc66eb8fae`

## CPNG unadjusted_weekly_valuation

Same provider row/date/values and same source SHA as the weekly adjusted role, but owned by the unadjusted valuation role.

R2B0 already proved:

- the anomaly exists in original provider bytes;
- unchanged normalizer reproduces it;
- it is not a transport error;
- it is not a date relabel;
- it is not normalization drift;
- no row was repaired/clipped/swapped/backfilled/retried.

These facts are immutable.

---

# 2. Non-negotiable rule: never repair provider OHLC

Do **not**:

- change high to open;
- change open to high;
- clip high/low;
- swap fields;
- interpolate;
- replace with another provider;
- replace with later/earlier row;
- recalculate provider OHLC from intraday data;
- silently drop the anomaly before provenance capture;
- backfill from prior archives.

Raw and normalized source evidence must retain the exact provider values.

This task changes only **eligibility/scoping semantics**, not market data.

---

# 3. Separate three concepts

The existing whole-payload rule currently conflates:

1. `SOURCE_ROW_INTEGRITY`
2. `ANALYSIS_WINDOW_RELEVANCE`
3. `ROLE / ANALYSIS ELIGIBILITY`

Separate them explicitly.

## 3.1 SOURCE_ROW_INTEGRITY

Every bar still receives row-level integrity evaluation.

Possible state:

- `VALID`
- `SOURCE_ANOMALY_PRESERVED`

An anomalous row is never relabeled valid.

## 3.2 ANALYSIS_WINDOW_RELEVANCE

For every downstream consumer, determine whether the anomalous row is actually read/used by that consumer.

Possible state:

- `NOT_CONSUMED`
- `CONSUMED`
- `UNKNOWN`

`UNKNOWN` must fail closed for that consumer until traced.

## 3.3 CONSUMER ELIGIBILITY

A consumer may proceed only if every row it actually requires is valid under its existing semantic requirements.

An anomaly outside the consumer's actual consumed row set must not automatically invalidate unrelated analysis.

---

# 4. Derive the actual consumed row sets from code

Do not guess a lookback such as 200/500/900 bars.

Audit the real production-equivalent consumers for each stock-role input.

At minimum trace:

- chart/technical context builder;
- moving averages;
- RSI;
- ATR / volatility;
- support/resistance;
- pivot/wave/long-cycle logic;
- trend regime;
- price-position calculations;
- volume/value calculations;
- valuation current-price extraction;
- Core fact catalog;
- A/B chart context;
- renderer-visible technical fields.

For every consumer record:

- function/module;
- input role;
- timeframe;
- exact row selection rule;
- exact lookback/window;
- whether full history is consumed;
- whether malformed OHLC fields are actually referenced;
- whether only latest row/close is referenced;
- mandatory/optional output;
- failure behavior.

Produce a deterministic `consumer-row-relevance-matrix`.

---

# 5. Row-level anomaly policy

Use the following policy.

## Case A — anomaly is outside the consumer's consumed row set

Result:

`SOURCE_ANOMALY_PRESERVED_OUTSIDE_CONSUMED_WINDOW`

The consumer may proceed.

Requirements:

- anomaly remains in raw/source audit;
- anomaly date/fingerprint remains attached to role metadata;
- consumer input slice excludes it only because the existing consumer's row-selection rule does not select it;
- do not add a special hidden filter solely to make it disappear.

This means the existing consumer naturally does not use that row.

## Case B — anomaly is inside the consumer's consumed row set

Result:

`SOURCE_ANOMALY_RELEVANT_TO_CONSUMER`

That consumer must fail closed unless the **existing consumer semantics already have a documented missing/anomalous-row tolerance**.

Do not invent a new smoothing/repair rule.

Failure is scoped to the affected analysis output, not automatically the entire 22-subject pipeline.

## Case C — current/latest required row is anomalous

Result:

`CURRENT_SNAPSHOT_SOURCE_ANOMALY`

Fail the role immediately.

Do not use the role for production.

For a mandatory Class-A role, the snapshot attempt is incomplete and follows the normal retry state machine in a future operational run.

## Case D — relevance cannot be proven

Fail closed for that consumer:

`SOURCE_ANOMALY_RELEVANCE_UNKNOWN`

Do not assume irrelevant.

---

# 6. No special CPNG hardcoding

Do not write:

- `if symbol == CPNG`
- `if date == 2023-06-05`
- fixed ignored-date lists
- provider-specific anomaly waiver tables

The rule must be generic:

`row anomaly`
+
`consumer actual row-set relevance`
→ scoped eligibility.

Use the sealed CPNG case as a regression fixture only.

---

# 7. Role-level usability must become consumer-scoped

Do not retain the old all-or-nothing rule:

> any invalid row anywhere in the provider payload => entire role unusable for every purpose.

Instead expose at least:

- source role identity;
- total row count;
- anomalous rows;
- latest/current row validity;
- per-consumer relevant anomaly set;
- per-consumer eligibility.

Example only:

`adjusted_weekly`
may be eligible for a latest-close consumer but ineligible for a long-cycle consumer if the latter actually consumes the anomalous row.

Do not collapse the two back into one Boolean until the final downstream requirement is known.

---

# 8. Unadjusted weekly valuation special audit

Trace what `unadjusted_weekly_valuation` actually contributes.

If the valuation path consumes only:

- the latest eligible price/close;
- a bounded recent row set not containing 2023-06-05;

then the historical CPNG anomaly must not invalidate valuation.

If it actually consumes the anomalous row, preserve fail-closed behavior for that exact valuation component.

Do not infer either result in advance.

---

# 9. Stock materializer behavior

Re-run the pure stock materializer from the **sealed R2B0 acquisition** only.

No provider call.

For each US14/KR8 subject:

1. load exact sealed role receipts/source artifacts;
2. retain row-level anomaly metadata;
3. evaluate actual consumer relevance;
4. produce only analysis fields whose required source rows are eligible;
5. explicitly mark unavailable/failed analysis components;
6. preserve mandatory/optional semantics;
7. require non-empty observed-business union under existing Core rules;
8. never inject previous AI output;
9. never substitute an external provider.

The materializer must not require every historical bar in every payload to be globally valid when the downstream consumer does not use it.

---

# 10. Partial analysis vs whole-stock failure

Do not automatically fail an entire stock because one optional technical component cannot consume an anomalous historical row.

Use existing typed mandatory/optional semantics.

### If affected component is optional

- mark it unavailable with explicit reason;
- continue the stock packet if all mandatory fields remain valid.

### If affected component is mandatory for Core/A/B

- stock packet fails;
- preserve exact component/reason;
- do not fabricate.

### If current price/latest snapshot is affected

- stock packet fails.

Do not change mandatory fields to optional solely to make CPNG pass.

---

# 11. Reuse sealed 88 acquisition only

Network/provider calls in this task:

`0`

Specifically:

- Kiwoom/chart calls = 0
- Alpha Vantage = 0
- Massive = 0
- fallback providers = 0
- auth = 0

Use exact R2B0 acquisition artifacts.

Before analysis verify:

- R2B0 ZIP SHA exact;
- request plan SHA:
  `e7d63a5278937b5ff6949ff55e93acf984875d57c5eb09de765eaec1327167b4`
- all 88 role intents/receipts present;
- raw/source artifacts unchanged;
- source-integrity root-cause file unchanged.

---

# 12. Required regression tests

## Row integrity

- valid OHLC row remains valid;
- `HIGH_LT_OPEN` remains anomalous;
- `LOW_GT_OPEN`, `HIGH_LT_CLOSE`, `LOW_GT_CLOSE`, high<low equivalents remain anomalous under existing integrity contract;
- raw values never mutated.

## Relevance

- anomalous row outside a bounded consumer window -> consumer eligible;
- same row inside window -> consumer fails;
- unknown window -> fail;
- current/latest anomalous row -> role fails;
- consumer reading close-only is not failed by unrelated unused high/open anomaly only if its existing semantics truly do not require those fields.

## Scope

- one optional component failure does not fail unrelated consumers;
- one mandatory component failure fails the stock packet;
- one stock failure does not automatically fail all other stocks before normal source-packet completeness rules are evaluated.

## CPNG sealed fixture

Using exact R2B0 bytes:

- daily anomaly preserved;
- weekly anomaly preserved;
- valuation anomaly preserved;
- relevance decision derives from actual consumer row sets;
- no CPNG/date hardcode;
- no provider call.

---

# 13. Re-run 22-subject materializer

After repair/tests:

re-run the materializer against the sealed R2B0 88-role corpus.

Required report:

For each subject:

- role receipt coverage;
- anomaly count;
- current/latest row validity;
- consumer relevance;
- mandatory analysis availability;
- optional analysis availability;
- final materializer status;
- deterministic packet hash.

Explicitly report CPNG component-by-component.

Do not summarize it only as PASS/FAIL.

---

# 14. PASS outcomes

## Outcome A — all 22 materialize

Use:

`M12DS_R6_R5F_R2B0_R1_ANOMALY_SCOPING_MATERIALIZER_PASS`

Require:

- no provider requery;
- anomaly rows unchanged;
- 22/22 stock packets materialize;
- mandatory consumers all valid;
- optional failures explicit;
- no hidden repair;
- full validation PASS.

Then:

- rebuild network-free source prequalification;
- if it passes, generate the bounded R2B current-source + 24-message work instruction.

## Outcome B — CPNG/another subject still has mandatory anomaly-relevant analysis

Use:

`M12DS_R6_R5F_R2B0_R1_MANDATORY_ANALYSIS_ANOMALY_REMAINS`

This is not a reason to modify source values.

Return:

- exact consumer;
- exact row;
- exact consumed window/rule;
- why mandatory;
- smallest next product-policy decision required.

Do not recollect automatically.

## Outcome C — another implementation blocker appears

Return a narrowly named blocker with direct evidence.

Do not reopen historical-envelope recovery.

---

# 15. Do not weaken the production snapshot rule

This repair does not mean “bad OHLC is okay”.

For future operational runs:

- current/latest invalid row => collection attempt incomplete;
- retry at the normal next attempt time;
- historical anomaly relevant to mandatory analysis => affected packet fails;
- historical anomaly outside actual consumed windows => preserved for audit but does not poison unrelated analysis.

This applies equally to US and KR.

---

# 16. Model/message/scheduler scope

This task is materializer-only.

Required actual counts:

- provider calls = 0
- model calls = 0
- Market/Core/A/B calls = 0
- rendered messages = 0
- Telegram sends = 0
- production delivery intents = 0
- production DB writes = 0
- scheduler mutations = 0
- notification mutations = 0
- deploy/restart = 0.

Do not run the 24-message proof inside this task.

---

# 17. Validation

Required:

- anomaly integrity tests;
- consumer relevance tests;
- actual consumer-window audit tests;
- CPNG sealed-source regression;
- stock materializer positive/negative tests;
- 22-subject sealed-corpus materialization proof;
- prior R2A/R2A-R2/R2A-R3/R2A-R4/R2A-R5/R2B0 regressions;
- disabled unified entrypoint smoke;
- full pytest;
- Ruff;
- `git diff --check`;
- Investment Knowledge;
- Chart Knowledge;
- secret scan;
- no new unexplained skip/xfail.

Do not lower investment/source/schema thresholds.

---

# 18. Required result bundle

Return immutable ZIP + `.sha256` containing at minimum:

- `REPORT.md`
- `summary.json`
- R2B0 result identity/SHA receipt
- repository SHAs
- changed-file inventory
- sealed acquisition identity receipt
- source-integrity root-cause receipt
- consumer-row-relevance matrix
- role/consumer eligibility matrix
- CPNG detailed relevance report
- anomaly policy before/after
- 22-subject materializer matrix
- stock packet hashes
- optional/mandatory unavailable matrix
- provider/model/scheduler counters
- focused/full validation
- secret scan
- network-free prequalification result if reached
- R2B next instruction + SHA if Outcome A and prequalification PASS
- bundle manifest.

---

# 19. Final operating principle

The intended rule is:

> Preserve provider data exactly. Detect malformed rows. Use only rows that the real downstream analysis actually consumes. A malformed historical row must not invalidate unrelated analysis that never reads it, but any mandatory consumer that does read it must fail closed. Current/latest malformed source data always fails the snapshot.

No source-value repair is permitted.
