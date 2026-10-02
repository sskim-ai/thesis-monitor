# Thesis Monitor — R2B-R9-REV37
## Current Completed-Session Close ÷ KIS FY1 EPS
### Direct Current FY1 fPER Owner for Korean Securities
### KIS Unadjusted Close + Share-Unit Corporate-Action Guard
### Provider FY1 PER Preserved as Secondary Research-Snapshot Reference
### KR8 Bounded Proof Only — No Broad Full-Fresh / No Models / No 24-Message Run

**REV37 supersedes every prior unexecuted post-REV36 Korean forward-valuation instruction. Execute only REV37.**

The user explicitly chooses the following forward-valuation product policy:

> For Korean securities, the primary actionable forward multiple should be calculated from the values Thesis Monitor
> actually acquires:
>
> `current FY1 fPER = latest completed-session close / qualified KIS FY1 EPS`.
>
> KIS provider FY1 PER remains useful as a secondary research-snapshot reference but is not the primary current
> forward multiple.

This is especially important for cyclical semiconductor / AI-capex names where trailing PER may be much less useful
than current-price forward earnings valuation.

REV36 already qualified:

- KIS FY1 EPS:
  `7/8`
- KIS provider FY1 PER:
  `6/8`
- FY1 typed state:
  `8/8`.

Current derived FY1 fPER remained:

`0/8`

only because the existing generic valuation basis demanded:
- an independently owned unadjusted current-price source;
- a configured corporate-action/share-unit owner.

REV37 closes exactly those two prerequisites using official KIS sources.

---

# 0. Newest SoT

Adopt REV36 as newest Korean forward-valuation SoT.

REV36 result ZIP:

`thesis-monitor-20261001-r2b-r9-rev36-kis-protocol-scale-report.zip`

SHA-256:

`a5e9fa932056fbd797bc834a01b8ee5688d1d4942bb233c0d9e501cb7133dbf4`

Independent verification:

- uploaded sidecar:
  exact match;
- ZIP CRC:
  PASS;
- ZIP members:
  `246`;
- internal bundle manifest:
  `245/245`;
- missing:
  `0`;
- hash mismatch:
  `0`;
- size mismatch:
  `0`;
- extra:
  `0`.

Terminal:

`R2B_R9_REV36_KIS_FY1_FORWARD_OWNER_PASS_READY_FOR_PRODUCTION_INTEGRATION`

Repository:

- base:
  `60c79de5a56fe83145afc6d96ee7d69f30d5aca9`
- branch:
  `codex/r2b-r9-rev36-kis-protocol-scale`
- instruction:
  `983cd111b5f469b3bd9304b408f23d2f5d2a2f7f`
- implementation:
  `ac0846ab4c6472c20303df4a295b8498ef90a481`
- final:
  `e974621759e6ab76296485a8e2b47d707be4c5a7`
- operating:
  `b610e6de0a8c33d199961e821ff1b130e1fa9ad4`
- clean:
  true.

Validation:

- focused:
  `318 passed`
- full:
  `7364 passed / 63 skipped / 0 failed / 0 errors`
- Ruff:
  PASS
- git diff --check:
  PASS
- Investment Knowledge:
  PASS
- Chart Knowledge:
  PASS
- secret scan:
  PASS.

REV36 final free bytes:

`9,626,914,816`

REV37 is bounded and does not run a broad generation.

---

# 1. Preserve REV36 KIS FY1 protocol owner exactly

Do not reopen the output3 protocol-scale work.

Generic KIS estimate-perform output3 scale:

## EPS
`display = wire / 10`

## PER
`display = wire / 10`

Preserve:
- exact security identity;
- fiscal owner;
- FY1 selection;
- forecast-marker contract;
- 005930 full-layout mapping;
- 000660 partial EPS/growth mapping;
- KIS-house-research-not-consensus semantics.

No new EPS/PER calibration in REV37.

---

# 2. REV36 qualified FY1 EPS coverage

Preserve exact REV36 values as bounded fixtures only.

These are not automatically current after REV37; the goal of REV37 is arithmetic-owner closure.

## Qualified
000660:
- FY1 EPS:
  `378,298.2 KRW/share`
- estimate date:
  `2026-07-29`
- provider FY1 PER:
  unavailable, no PER row.

005930:
- FY1 EPS:
  `46,209`
- estimate date:
  `2026-07-30`
- provider FY1 PER:
  `4.5x`.

005490:
- FY1 EPS:
  `29,217.6`
- provider FY1 PER:
  `15.1x`.

010120:
- FY1 EPS:
  `3,680.2`
- provider FY1 PER:
  `67.0x`.

012450:
- FY1 EPS:
  `49,839.8`
- provider FY1 PER:
  `19.1x`.

047810:
- FY1 EPS:
  `2,325.2`
- provider FY1 PER:
  `64.7x`.

086280:
- FY1 EPS:
  `22,537.7`
- provider FY1 PER:
  `10.5x`.

## No KIS estimate
003690:
- FY1 EPS:
  unavailable
- provider FY1 PER:
  unavailable.

These values are regression fixtures.
Do not hardcode them into production logic.

---

# 3. Primary metric policy

Create/formalize:

`CurrentFY1Fper`

Formula:

`completed_session_unadjusted_close_KRW / KIS_FY1_EPS_KRW_PER_SHARE`

This is the primary user-facing forward valuation when qualified.

Required label:

`현재가 기준 fPER(FY1)`

or equivalent concise Korean wording.

Do not label it:
- KIS provider PER;
- KIS report-date PER;
- NTM PER;
- 12M forward PER;
- consensus PER.

It is a Thesis Monitor arithmetic metric using:
- current completed-session market price;
- KIS house-research FY1 EPS.

---

# 4. Provider FY1 PER becomes a secondary reference

Preserve:

`KIS_PROVIDER_FY1_PER_SNAPSHOT`

when available.

User-facing semantic:

`KIS fPER(FY1) · research snapshot YYYY-MM-DD`

This metric reflects the KIS research snapshot and may use a different price basis/time than the current market price.

It must not replace the primary current-price-derived metric.

When both exist, preserve both.

Example shape only:

- `현재가 기준 fPER(FY1): 5.9배`
- `KIS 리서치 fPER(FY1): 4.5배 · 2026-07-30`

Do not treat their difference as a data error by default.

---

# 5. Exact numerator source — KIS unadjusted daily close

Use the official KIS route:

`/uapi/domestic-stock/v1/quotations/inquire-daily-price`

API:
`주식현재가 일자별 [v1_국내주식-010]`

Required parameters:

- market:
  `J`
- exact six-digit security code;
- period:
  `D`
- original/adjusted price flag:
  `FID_ORG_ADJ_PRC=0`

Official KIS semantics:

`0 = 수정주가 미반영`

`1 = 수정주가 반영`

Therefore REV37 numerator must come from the exact `0` path.

Do not use the existing REV36 `adjusted_close` for the qualifying arithmetic.

The old adjusted-close projection may remain for regression/technical purposes.

---

# 6. Completed-session selection

Do not use intraday/current quote.

From the fresh KIS daily-price response select the exact latest completed Korean trading session under the existing
calendar owner.

At execution time:
- recompute the latest completed KR session;
- do not hardcode 2026-09-29 or 2026-09-30.

Required:
- exact session date;
- exact close field;
- exact six-digit security;
- KRX market;
- KRW;
- `FID_ORG_ADJ_PRC=0`;
- raw response SHA;
- retrieval timestamp.

If the latest returned row is today's incomplete session:
do not use it.

Select the frozen completed session.

---

# 7. CurrentFY1PriceReceipt

Create, repository naming permitting:

`CurrentFY1PriceReceipt`

Fields:

- security code;
- canonical security ID;
- KIS product identity;
- session date;
- close;
- currency:
  KRW;
- price basis:
  `KIS_UNADJUSTED_COMPLETED_SESSION_CLOSE`;
- `fid_org_adj_prc=0`;
- raw response SHA;
- retrieval timestamp;
- calendar-owner receipt;
- current-session-complete:
  true;
- overall_direction_use:
  false.

No arithmetic without this receipt.

---

# 8. Price-call scope

Only securities with qualified REV36 FY1 EPS need a price call:

- 000660
- 005930
- 005490
- 010120
- 012450
- 047810
- 086280.

003690:
- no FY1 EPS;
- no price call required for fPER proof.

Maximum fresh KIS daily-price calls:

`7`

One per qualified FY1 EPS security.

No repeated call for a more favorable close.

---

# 9. Share-unit compatibility — simplified but explicit policy

REV37 intentionally replaces the old overly broad generic basis requirement for this metric.

For `CurrentFY1Fper`, do **not** require:
- provider-owned EPS denominator construction;
- BPS/share-count reconstruction;
- generic unadjusted-price equivalence to old adjusted technical data;
- every corporate event type.

The only required compatibility question is:

> Has the per-share unit materially changed between the KIS FY1 estimate snapshot date and the completed-session close?

This is the relevant risk for dividing current price by a frozen per-share EPS estimate.

---

# 10. Share-unit-changing corporate-action guard

Use official KIS/KSD read-only event routes already present in the provider library.

Minimum required event families:

1. `ksdinfo_merger_split`
   - merger / split schedule;

2. `ksdinfo_rev_split`
   - face-value replacement / split-related schedule;

3. `ksdinfo_bonus_issue`
   - bonus issue / free-share issuance;

4. `ksdinfo_paidin_capin`
   - paid-in capital increase / rights issuance;

5. `ksdinfo_cap_dcrs`
   - capital reduction.

These are the share-unit/share-count-changing families relevant to stale per-share estimate compatibility.

Cash dividend is not a blocker.

Ordinary earnings/news/events are not blockers.

---

# 11. Efficient corporate-action acquisition

Do not make five calls per stock unless the endpoint contract requires it.

Preferred plan:

- define global action window:
  earliest qualified FY1 estimate date among current KR subjects
  through
  current completed-session date;

- query each required action family once with:
  `sht_cd=""`
  when the official endpoint supports all-security retrieval;

- filter exact monitored seven securities locally by official security code.

Preferred initial action calls:

`5`

Continuation may be followed only under the official route contract.

If an endpoint requires per-security querying:
re-plan deterministically before execution and record why.

No silent call explosion.

---

# 12. CorporateActionCompatibilityReceipt

For each FY1-qualified security create:

`CorporateActionCompatibilityReceipt`

Fields:

- security code;
- KIS FY1 estimate date;
- completed-session price date;
- queried event families;
- exact event records in window;
- effective/action dates;
- share-unit-changing boolean;
- compatibility state;
- source hashes.

States:

- `NO_SHARE_UNIT_CHANGE_IN_WINDOW`
- `SHARE_UNIT_CHANGE_REQUIRES_ADJUSTMENT`
- `CORPORATE_ACTION_SOURCE_INCOMPLETE`
- `UNAVAILABLE_OTHER_TYPED_REASON`.

Absence may qualify only if all required action-family queries completed successfully for the exact window.

No absent=>clean shortcut from a failed route.

---

# 13. Event effective-date policy

Use the event's effective/security-unit-changing date, not merely announcement date.

If a share-unit-changing action's effective date is:

- before or on KIS estimate date:
  it does not invalidate that estimate snapshot;

- after estimate date and on/before price date:
  current fPER is blocked unless an exact adjustment contract exists;

- after price date:
  it does not affect that completed-session fPER.

Do not block on future announced events whose share-unit effect has not yet occurred by the price date.

Record the event-date semantics used.

---

# 14. No adjustment arithmetic in REV37

If a post-estimate share-unit-changing action exists:

do not attempt to adjust FY1 EPS in REV37.

State:

`UNAVAILABLE_POST_ESTIMATE_SHARE_UNIT_CHANGE`

A later bounded task may define a split-adjustment owner if such a real case exists.

Do not invent adjustment ratios.

---

# 15. Current FY1 fPER qualification

For each security require:

1. qualified KIS FY1 EPS;
2. EPS > 0;
3. exact same six-digit security identity;
4. KIS unadjusted completed-session close;
5. KRW / KRW-per-share compatibility;
6. corporate-action compatibility:
   `NO_SHARE_UNIT_CHANGE_IN_WINDOW`.

Then compute exactly:

`fper = close / FY1_EPS`.

Use decimal arithmetic.

No floating binary instability in receipts.

Store:
- exact numerator;
- exact denominator;
- exact unrounded quotient;
- displayed rounded value;
- rounding policy.

Recommended display rounding:

`2 decimal places`

for user-facing messages.

Receipt retains higher precision.

---

# 16. N/M

If a qualified FY1 EPS is:

`<= 0`

state:

`NOT_MEANINGFUL`

User-facing:

`N/M`

No negative fPER.

No N/M if EPS itself is unavailable.

---

# 17. CurrentFY1FperReceipt

Create:

`CurrentFY1FperReceipt`

Fields:

- security code;
- canonical security ID;
- FY1 period;
- FY1 EPS;
- EPS estimate date;
- EPS source/receipt SHA;
- completed-session date;
- unadjusted close;
- price receipt SHA;
- corporate-action compatibility receipt SHA;
- exact quotient;
- display value;
- currency/basis;
- source age_days;
- metric:
  `CURRENT_PRICE_FY1_FPER`;
- source kind:
  `THESIS_MONITOR_DERIVED_FROM_KIS_CLOSE_AND_KIS_RESEARCH_EPS`;
- allowed roles:
  - VALUATION
  - NEW_BUYER_VALUATION
  - HOLDER_VALUATION
- prohibited:
  - OVERALL_DIRECTION
  - FUNDAMENTAL_CORE
  - PASS_A_DIRECTIONAL
  - supporting/contradicting business refs;
- overall_direction_use:
  false.

---

# 18. Do not conflate three PER concepts

REV37 must keep separate:

## A. Current trailing/current PER
Existing Kiwoom current provider snapshot.

## B. KIS provider FY1 PER
Research-snapshot forward PER at the KIS estimate snapshot.

## C. Current-price FY1 fPER
Latest completed-session unadjusted close / frozen KIS FY1 EPS.

Never overwrite one with another.

Future renderer target:

- `PER`
- `PBR`
- `현재가 기준 fPER(FY1)`
- `KIS 리서치 fPER(FY1)` secondary
- `FY1 EPS · KIS Research YYYY-MM-DD`.

---

# 19. Diagnostic provider-PER comparison

When both B and C exist:

compute a diagnostic difference only.

Allowed:
- ratio/difference;
- implied price movement interpretation.

Not allowed:
- reject current fPER because it differs;
- force equality;
- use provider PER to repair current close;
- use current fPER to rewrite KIS provider PER.

Expected differences are normal because price dates differ.

---

# 20. Bounded live proof target

REV37 should attempt current fPER for the seven FY1-EPS-qualified securities.

003690 remains:

`UNAVAILABLE_EPS`

unless no-estimate state changes in a future fresh KIS estimate acquisition.

No estimate-perform calls are needed in REV37.

Use sealed REV36 FY1 EPS fixtures for owner proof.

Production integration will reacquire FY1 EPS fresh in REV38.

---

# 21. No estimate refresh in REV37

KIS estimate-perform calls:

`0`

Reason:
REV37 is arithmetic/basis-owner closure.

Do not change:
- FY1 EPS values;
- estimate dates;
- provider PER values;
- FY1 coverage.

If the owner cannot qualify using sealed REV36 EPS:
stop honestly.

---

# 22. KIS calls and pacing

Expected fresh calls:

- daily-price:
  up to `7`;
- corporate-action families:
  preferred `5` plus bounded continuation;
- auth:
  one normal session as needed.

Hard KIS data-call maximum:

`20`

excluding auth.

Sequential only.

Use:
- official smart_sleep()
or
- >=1.1-second pacing.

No parallel calls.

No immediate retry on `EGW00201`.

---

# 23. Exact official price semantics

Pin official KIS documentation proving:

`FID_ORG_ADJ_PRC=0 = 수정주가 미반영`

and:

`1 = 수정주가 반영`.

Archive the exact documentation/source hash used by the owner.

Do not rely only on code comments copied into this instruction.

---

# 24. Exact official corporate-action route inventory

Before calls, verify from the official KIS repository/API configuration that the five action routes in Section 10 remain
current and read-only.

Record:
- API name;
- route;
- TR ID;
- date parameters;
- security filter semantics;
- continuation behavior.

No invented endpoint.

If one route is unavailable/deprecated:
do not silently omit it.

State the compatibility source incomplete unless an equivalent official route is explicitly proven.

---

# 25. Existing credential policy

The user explicitly accepts continued use of the current KIS key pair.

Use only secure local configuration.

Never print/log/archive:
- App Key;
- Secret;
- token;
- auth header.

If exposed:

`R2B_R9_REV37_KIS_SECRET_EXPOSURE_GAP`

Stop further KIS calls and do not archive the exposed output.

---

# 26. External transmission approval

REV37 explicitly authorizes bounded read-only access to:

- KIS domestic daily price;
- KIS/KSD corporate-action routes in Section 10;
- official KIS API/GitHub documentation;
- normal KIS auth.

No:
- estimate-perform refresh;
- FnGuide;
- Alpha Vantage;
- model runner;
- Telegram;
- order/trading APIs;
- production DB writes;
- scheduler mutation;
- deploy;
- main merge;
- remote push;
- restart.

No additional approval is needed for this exact scope.

---

# 27. No broad full-fresh / no models

REV37 must not run:

- all22 source collection;
- broad KR source collection;
- US collection;
- Market collection;
- Market/Core/A/B;
- exact24.

Models:

`0`

Messages:

`0/24`

Telegram:

`0`.

REV38 is the production integration proof if REV37 passes.

---

# 28. Disk guard

REV36 final free bytes:

`9,626,914,816`

REV37 is bounded.

Require before external calls:

`>= 8 GiB`

No full-generation GC solely for this task.

Safe temporary pytest/report cleanup is allowed under the existing protection rules.

Preserve all accepted immutable archives and blind-review artifacts.

---

# 29. Required tests

## Price
- FID_ORG_ADJ_PRC=0 positive;
- adjusted=1 cannot qualify numerator;
- exact completed-session selection;
- incomplete current-day row negative;
- wrong security/date/currency negative.

## Corporate actions
- all five required route families complete + no event → PASS;
- one route failed → cannot claim absence;
- split in window → block;
- reverse/face replacement in window → block;
- bonus issue in window → block;
- paid-in issuance in window → block;
- capital reduction in window → block;
- cash dividend only → does not block;
- action before estimate date → does not block;
- action after price date → does not block.

## Arithmetic
- positive EPS;
- zero EPS N/M;
- negative EPS N/M;
- unavailable EPS;
- exact Decimal quotient;
- stable rounding.

## Metric isolation
- current trailing PER separate;
- KIS provider FY1 PER separate;
- current-price FY1 fPER separate.

## Authority
- valuation/NewBuyer/Holder allowed;
- Overall/Core/A prohibited.

No tests may hardcode a ticker-specific formula.

---

# 30. Validation

Require:

- focused REV37 tests;
- REV32-36 KIS regression tests;
- current PER/PBR regression;
- valuation visibility/isolation;
- whole-source registry tests if owner registration changes;
- full pytest;
- Ruff;
- git diff --check;
- Investment Knowledge;
- Chart Knowledge;
- secret scan.

No PASS if full suite is red.

---

# 31. Success terminal

If:

- exact KIS unadjusted completed-session price owner closes;
- corporate-action compatibility owner closes;
- current FY1 fPER qualifies for every eligible security that has no share-unit-changing event;
- KR8 typed matrix is complete;
- full validation is green;

use:

`R2B_R9_REV37_CURRENT_FY1_FPER_OWNER_PASS_READY_FOR_PRODUCTION_INTEGRATION`

Success does not require:
- 003690 fPER;
- provider FY1 PER for 000660;
- all seven subjects to qualify if a real share-unit-changing event correctly blocks one.

No numeric target fitting.

---

# 32. Honest stop terminals

- `R2B_R9_REV37_KIS_UNADJUSTED_CLOSE_GAP`
- `R2B_R9_REV37_COMPLETED_SESSION_SELECTION_GAP`
- `R2B_R9_REV37_CORPORATE_ACTION_ROUTE_GAP`
- `R2B_R9_REV37_POST_ESTIMATE_SHARE_UNIT_CHANGE`
- `R2B_R9_REV37_FY1_FPER_ARITHMETIC_GAP`
- `R2B_R9_REV37_KIS_RATE_LIMIT_GAP`
- `R2B_R9_REV37_KIS_SECRET_EXPOSURE_GAP`
- `R2B_R9_REV37_VALIDATION_GAP`.

A real corporate action is a metric-level typed denial, not necessarily whole-task failure.

---

# 33. Required result bundle

Return immutable ZIP + `.sha256`.

At minimum:

## Integrity
- REPORT.md
- summary.json
- REV36 result SHA/integrity
- repository identities
- changed files
- bundle manifest.

## Price owner
- official price-route documentation
- exact requests/receipts
- unadjusted close rows
- completed-session selection receipts.

## Corporate actions
- official route inventory
- query plan
- raw/receipts
- per-security compatibility matrix
- event date/effective date logic.

## fPER
- KR8 current FY1 fPER matrix
- numerator/denominator
- exact quotient
- display value
- provider FY1 PER comparison diagnostic
- typed denials.

## Validation
- focused
- full
- Ruff
- diff
- knowledge
- secret scan.

## Safety
- KIS call counters
- estimate refresh 0
- FnGuide 0
- Alpha 0
- models 0
- messages 0
- Telegram 0
- production mutations 0.

---

# 34. Next-stage handoff

If PASS, prepare REV38 recommendation only.

REV38 should integrate into the normal Korean fresh pipeline:

1. fresh KIS estimate-perform;
2. KIS protocol owner → FY1 EPS;
3. fresh unadjusted completed-session close;
4. corporate-action compatibility;
5. current-price FY1 fPER;
6. existing current PER/PBR;
7. secondary KIS provider FY1 PER where available.

Then:
- archive-backed GC if required;
- one normal full-fresh all-source run;
- replay twice;
- expose forward valuation only to B/NewBuyer/Holder;
- final renderer shows the metrics distinctly;
- Market/Core/A direction remains untouched by valuation.

Do not execute REV38 inside REV37.

---

# 35. Final principle

For this use case, forward valuation should be useful, not merely provenance-perfect but unavailable.

The primary metric is simple:

`latest completed-session unadjusted close / qualified KIS FY1 EPS`.

The source contract therefore needs only the things that materially affect that arithmetic:

- exact security;
- exact completed-session close;
- exact FY1 EPS per share;
- same currency;
- no intervening share-unit-changing corporate action.

Do not require unrelated denominator reconstruction or generic PBR-style share ownership machinery.

KIS provider FY1 PER remains valuable as a dated research-snapshot reference.

The two metrics answer different questions:

- KIS provider FY1 PER:
  what KIS Research's snapshot implied at its research date;

- current FY1 fPER:
  what the same FY1 EPS implies at the latest completed-session market price.

For semiconductor/AI-cycle monitoring, the second is the primary actionable forward valuation.
