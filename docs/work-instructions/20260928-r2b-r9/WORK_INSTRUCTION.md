# Thesis Monitor — R2B-R9
## Full Fresh All-Source Recollection + Post-R7 Live Adapter Requalification + Fresh 24-Message Proof

**Purpose:** discard the stale/sealed-data dependency of the prior R2B proof chain and perform one full fresh requalification using the current post-R7 runtime contract.

This task must freshly reacquire **all mutable data roles** for:

- US market
- KR market
- all US14 monitored stocks
- all KR8 monitored stocks
- current stock OHLCV / technical inputs
- current official financial/business evidence
- current market index / sector / breadth inputs
- all macro inputs actually consumed by the current Market owner
- current KRX night-futures/publication inputs configured by the product

Then, using **only the newly captured current-generation source graph**, it must:

1. qualify the full source adapter;
2. prove post-R7 source-use semantics;
3. run a completely fresh Market/Core/A/B dry run;
4. render 24 fresh messages;
5. return them for human review;
6. generate—but not execute—the final scheduler-cutover instruction only on full PASS.

This task supersedes the failed R2B-R8 comparison-resume path.

Do not resume R8.
Do not require the comparison ZIP.
Do not use R6/R7 model outputs or source packets as input to the new proof.

---

# 0. Superseded R8 state

Uploaded R8 result ZIP:

`thesis-monitor-20260928-r2b-r8-comparison-pending-report.zip`

Verified SHA-256:

`852a134c8b05ee74f2e4394e42fd4211bfa2ffe290dfe8a6887102815eb713d4`

R8 terminal:

`R2B_R8_COMPARISON_ARCHIVE_MISSING`

R8 confirmed:

- R7 objective direction guard remains PASS;
- corrected R7 corpus remains 24/24;
- executable runtime code was unchanged by R8;
- provider/model calls = 0;
- live requalification was NOT generated or executed;
- scheduler activation remains unauthorized.

R8 is now archival only.

The missing comparison archive is **not a prerequisite** for R9.

---

# 1. Runtime SoT

The runtime semantic SoT is the accepted post-R7 implementation.

R7 result ZIP SHA-256:

`aba5a144fb5b8bf8106684d2541352a8e72d12ed121bccbfabda036bebb62680`

Accepted R7 objective guard:

`R2B_R7_ABSOLUTE_CURRENT_DIRECTION_GUARD_PASS`

R7 runtime identities:

- branch:
  `codex/r2b-r7-absolute-financial-direction`
- base R6:
  `ad24ba92e8a7d8494a62c5e90a8321fba9c5230d`
- instruction:
  `7140f09f05f12e5b214f4511663a858a8b29d2ed`
- tested runtime implementation:
  `174af2b0a0cef373c85a9a27fe22604839c8acf9`
- report-only final:
  `d824014b7f9fad44a1619850d81a657925c6cf80`
- operating main:
  `b610e6de0a8c33d199961e821ff1b130e1fa9ad4`

If R9 starts from the R8 branch/repository state:
- first prove all executable runtime files are byte-identical to the accepted R7 runtime;
- R8 document/report-only differences are allowed;
- any executable drift blocks R9 before network.

Do not merge main.

---

# 2. What “fresh” means in R9

For every **mutable external data role** consumed by the proof:

`retrieved_in_R9_generation = true`

is mandatory.

A value is not fresh merely because:
- its economic observation date is recent;
- it appears in a previous packet;
- it was previously PASS;
- it matches today's provider value;
- it is copied from R6/R7;
- it is in a cache.

Required for every mutable role:

- new R9 request/read identity;
- retrieval timestamp;
- provider/source owner;
- response/source artifact identity;
- raw/source hash;
- normalization hash;
- observation/session date;
- publication/as-of date where applicable;
- role binding;
- freshness/publication state;
- validator receipt.

Historical R6/R7 values may be used **only after the new R9 packet is sealed**, for regression comparison.

They may never fill a missing R9 role.

---

# 3. Allowed static reuse

The following may be reused if their repository/config identities are unchanged:

- ticker/security master identity;
- issuer/corp/CIK mapping;
- exchange mapping;
- product configuration;
- thesis/configuration text;
- stored thesis version metadata;
- schemas;
- prompts;
- validators;
- source-owner code;
- policy code;
- canonical calendar logic.

Even these must be hash-bound to R9.

Do not treat static identity reuse as mutable source reuse.

---

# 4. Explicitly forbidden reuse

R9 must not source any current proof field from prior generations for:

- current price;
- daily/weekly/monthly OHLCV;
- technical indicators;
- support/resistance/watch-zone inputs;
- current market indices;
- sector/style values;
- breadth;
- flows;
- VIX;
- USD/dollar index;
- WTI;
- Treasury yields;
- real yield;
- breakeven;
- HY spread;
- other Market macro roles;
- night futures;
- current financial statements;
- current/prior financial comparison facts;
- current event/news acquisition;
- financial-quality result;
- observed_business_union;
- source-use PASS flags;
- complete packet flags;
- previous AI decisions.

No prior “already complete control” exemption.

---

# 5. Full current role inventory before network

Before the first external call, generate:

`r9-full-fresh-role-inventory.json`

Enumerate every role actually consumed by current:

- Market US
- Market KR
- Core
- A / New Buyer
- B / Holder
- renderer

For each role record:

- role ID
- market
- subjects/universe
- provider/source owner
- endpoint/source family
- mutable/static
- mandatory/optional
- expected session/period
- basis
- freshness/publication semantics
- validator
- fallback rule
- model-visible?
- user-visible?
- current configured display role?

Do not invent roles from old documentation.

The current runtime consumer graph owns the inventory.

---

# 6. Product-facing Market display policy

Separate:

1. data that the Market model needs internally;
2. data that the final user-facing message displays.

Preserve the current product policy rather than resurrecting old message formats.

Expected user-facing behavior:

- both markets include sector TOP3 / BOTTOM3 when qualified;
- stale macro rows must not dominate the message;
- US raw index/yield/WTI rows should not be dumped merely because the Market model consumes them internally, if current renderer/product policy has removed them;
- internal macro facts may still support Market reasoning when fresh/eligible.

If repository behavior conflicts with current configured product policy:
- freeze the exact conflict;
- do not silently choose an old format.

---

# 7. Full US14 fresh stock collection

US monitored subjects:

- CORZ
- CPNG
- CRCL
- GOOGL
- HUT
- IBM
- MU
- RXRX
- SKHY
- SNDK
- TSLA
- TSM
- WRD
- WULF

For **all 14**, with no complete-control exemption, freshly acquire all currently configured mutable stock roles.

At minimum where consumed:

- current/last completed-session price context;
- D/W/M OHLCV or the current canonical bar inventories;
- technical raw inputs;
- current technical state;
- current financial/business acquisition;
- current event/news role where configured;
- financial quality/source-use;
- current/prior comparative financial facts where available;
- exact source authority.

Do not reuse R6/R7 price or technical packets.

---

# 8. Full KR8 fresh stock collection

KR monitored subjects:

- 000660
- 003690
- 005490
- 005930
- 010120
- 012450
- 047810
- 086280

For **all 8**, freshly run the same current stock/financial/business owner contracts.

No exemptions for:
- 005930
- 047810
- 000660
- any previously complete stock.

At minimum where consumed:

- current/last completed-session price context;
- D/W/M OHLCV/current canonical bar roles;
- technical state;
- current OpenDART financial/business source;
- current/prior compatible comparison acquisition;
- financial-quality projection;
- source-use;
- current event/news role where configured.

No old PASS flags.

---

# 9. 005930 and 047810 are mandatory fresh-financial controls

The previous bug arose because current-only absolute facts survived without comparable directional evidence.

R9 must explicitly prove for both:

## Acquisition

Freshly query the current official KR financial/business source owner.

Do not say:
“already complete, do not reacquire.”

## Direction

For each financial field used directionally, require:

- exact issuer;
- exact filing/report;
- exact statement;
- exact period;
- current/prior compatible pair;
- statement basis;
- currency/unit;
- occurrence lineage;
- field quality;
- source-use PASS.

If only a current amount is available:
- context may survive;
- direction must remain unavailable.

If no other directional business fact survives:
- existing `UNKNOWN_LIMIT / OBSERVE` path applies.

Do not force BUY/HOLD continuity.

---

# 10. All 22 financial/business owners must be current-generation

For every subject, classify fresh business evidence into current-generation source-owned roles such as:

- `REPORTED_FINANCIAL`
- `BUSINESS_EVENT`
- other currently authorized role

Do not import old:
- comparative facts;
- event facts;
- issuer bridge outputs;
- business-union outputs

as current proof.

If persisted historical evidence is part of the **current product contract**, its continued eligibility must be re-established from its original immutable source plus a new R9 eligibility decision, and it must be labeled persisted—not newly acquired.

Prefer fresh official financial/business acquisition where the owner supports it.

---

# 11. Fresh US market collection

Freshly acquire all mutable US Market roles consumed by the current Market owner.

At minimum audit/collect as configured:

- current major-market/index proxies;
- current sector/style universe;
- sector relative performance/ranking;
- sector TOP3/BOTTOM3;
- breadth/participation;
- VIX;
- dollar/USD role;
- WTI;
- Treasury roles;
- real-yield role;
- breakeven role;
- HY spread;
- other current macro fields actually consumed by Market;
- KRX night/publication context if the US Market consumer uses it.

Do not accept prior R6 macro rows as R9 current values.

---

# 12. Fresh KR market collection

Freshly acquire all mutable KR Market roles consumed by the current Market owner.

At minimum where configured:

- KOSPI;
- KOSDAQ;
- breadth;
- KOSPI sector universe;
- KOSDAQ sector universe;
- sector TOP3/BOTTOM3;
- investor flows if qualified by the current source owner;
- current KR market publication/session context.

Do not mix pages/attempts across collection attempts.

Optional unavailable is not zero.

---

# 13. Macro freshness/publication contract

This section is mandatory because prior proof messages contained old macro observations.

Every macro role must be fetched/read again in R9.

For each role store:

- `retrieval_time`
- `observation_time/date`
- `publication_time/date` if source exposes it
- `expected_cadence`
- `latest_available_at_query_time`
- `freshness_state`
- `direction_eligible`
- `display_eligible`

Allowed freshness states should distinguish at least:

- `CURRENT_SESSION_OR_DATE`
- `LATEST_PUBLISHED_VERIFIED`
- `DELAYED_BY_SOURCE_CADENCE`
- `STALE_CACHE_NOT_ALLOWED`
- `PUBLICATION_CURRENTNESS_UNPROVEN`
- `OPTIONAL_UNAVAILABLE`

Do not use an arbitrary “N days old” rule if source cadence is not daily.

But:

> old cached data is never qualified merely because the series itself may publish slowly.

`LATEST_PUBLISHED_VERIFIED` requires a **current R9 provider/source query** proving that the returned observation is the latest available at the R9 query time.

If currentness cannot be proven:
- the role is unavailable/blocked according to its mandatory status;
- do not silently display the old value.

---

# 14. Market-session ownership

Use the current exchange calendars.

For each market freeze:

- actual execution timestamp;
- market calendar;
- latest eligible completed regular session;
- target session;
- collection mode;
- source session;
- query-time semantics.

No official-final-close wording unless current source contract supports it.

The product remains a query-time snapshot.

---

# 15. Scheduled-window mode versus ad-hoc live requalification

R9 supports two explicit modes.

## `SCHEDULED_WINDOW`

Use the current configured production collection windows from the repository.

Expected current unified design must be verified, not assumed.

The current known design is expected to be:

### US
- 08:10 KST first attempt
- if incomplete: 08:15 full Class-A recollection
- if still incomplete: 08:20 full Class-A recollection

### KR
Freeze the exact current repository-configured unified window before execution.
If it is the accepted 16:00/16:05/16:10 design, use it exactly.
If repository config differs, report the drift before network.

No primary/backup semantics.

## `AD_HOC_LIVE_REQUALIFICATION`

Allowed for this proof when outside a scheduled slot.

Use:
- actual current query time;
- latest eligible completed session per exchange;
- same production source owners;
- same mandatory role inventory;
- fresh retrieval of all mutable roles.

Do not pretend it was a scheduled run.

A later scheduler cutover still remains separate.

---

# 16. Attempt isolation and recollection

For mutable Class-A/market collection:

- attempt directory/state must be fresh;
- failed attempt remains diagnostic only;
- attempt N+1 may not patch attempt N;
- if the product policy requires retry, recollect the entire declared Class-A set for that market.

No cross-attempt symbol patching.

No previous generation import.

---

# 17. Full current financial acquisition budgets

Before any SEC/OpenDART/event acquisition, freeze a finite plan.

For every provider/source owner record:

- subjects;
- planned logical calls;
- theoretical max logical calls;
- planned pages;
- theoretical max pages;
- planned document reads;
- theoretical max document reads;
- timeout;
- retries;
- theoretical max transport attempts.

No request executes if the bound is unknown.

Transport policy unless current owner specifies stricter accepted behavior:

- first attempt = 1
- transient retries max = 2
- total attempts max = 3
- no semantic/schema/policy retry.

Alpha Vantage:

`planned = 0`
`actual = 0`

Account-wide user budget remains 25/day.

Massive/undeclared fallback:

`0`

---

# 18. Fresh financial comparison contract

For direction eligibility, absolute current values are not enough.

Require current-generation compatible comparative lineage for directional financial claims.

Examples:

- revenue current vs comparable prior;
- operating income current vs comparable prior;
- margin expansion/contraction when owned;
- another explicitly approved directional financial fact.

Each directional fact must bind all required occurrences.

No comparison lineage:
- context only;
- no direction.

This is the post-R7 guard and must be proven on fresh source.

---

# 19. Fresh quality owner

Run the deterministic typed quality owner from the fresh R9 financial/business inputs for all 22.

Do not copy R6/R7 quality states.

For each subject emit:

- financial-quality applicability;
- state;
- reason codes;
- source period;
- source refs;
- business-evidence quality effect;
- security valuation basis;
- source-use.

No fake quality refs.

No absent→clean shortcut.

---

# 20. Fresh SKHY issuer bridge, if still required

Do not reuse the old SKHY bridge result.

If current source topology still requires same-legal-issuer bridge:

- freshly prove security→issuer identity;
- freshly acquire/revalidate the issuer-level financial comparison in R9;
- preserve no per-share/valuation bridge;
- preserve no price/technical transfer.

If current SKHY official source now directly qualifies, use the current canonical owner instead.

Do not force the bridge.

---

# 21. Fresh SNDK evidence

Do not reuse the prior SNDK PASS flag.

Run current configured official financial/business/event owners.

Possible outcomes:

- fresh qualified financial comparison;
- fresh qualified event;
- persisted event remains independently eligible under current contract;
- no directional evidence -> `UNKNOWN_LIMIT`.

Do not upgrade a context-only headline.

---

# 22. Fresh stock packet closure

After all current-generation collection, build all 22 packets from R9 sources only.

Require matrix:

- ticker
- R9 attempt/generation
- current price status
- OHLCV status
- technical status
- financial source
- comparative financial status
- business event status
- quality status
- direction eligibility
- mandatory missing
- packet hash
- final status

No prior packet hash may qualify a subject.

Target:

`22/22 CURRENT R9 STOCK PACKETS PASS`

Honest partial is allowed; no model calls on partial.

---

# 23. Fresh Market packet closure

Build US and KR Market contexts using R9 source data only.

Require:

- source completeness;
- session alignment;
- macro currentness classification;
- sector/breadth coverage;
- fact catalog;
- numeric registry;
- source refs;
- optional denials;
- deterministic replay.

Target:

`MARKET 2/2 R9 SOURCE READY`

No stale-cache substitution.

---

# 24. Night futures / publication context

Freeze the current product-configured night-futures scope before network.

Expected product direction is **KOSPI200 only**; if repository still treats KOSDAQ150 as mandatory, report configuration drift rather than silently carrying the old scope.

For the configured product(s), freshly acquire/rebuild:

- daily;
- weekly;
- monthly;
- included/expected session metadata;
- current availability state.

If W/M are genuinely unavailable:
- return `자료 부족` / explicit unavailable state;
- do not reuse old W/M data.

Do not reuse 2026-09-23 night values as current R9 data.

---

# 25. Full fresh source authority graph

Only after:

- stock 22/22;
- Market 2/2;
- configured night/publication context complete according to policy;
- macro roles currentness classified;

create a new R9:

- FullSourceRunSeed
- US whole-source packet
- KR whole-source packet
- combined source packet
- authority graph

All must receive new R9 hashes.

No R6/REV10 whole-source hash may be reused as current identity.

---

# 26. Offline replay before AI

Freeze the R9 raw/source corpus.

Then disconnect/disable provider access and replay the full source composition twice.

Require identical semantic hashes for:

- stock packets 22/22;
- US Market;
- KR Market;
- full-source packets;
- authority graph.

Then set:

`NETWORK_FREE_SOURCE_ADAPTER_PREQUALIFIED = true`

only on PASS.

---

# 27. Live adapter qualification

`COMPLETE_SOURCE_ADAPTER_QUALIFIED = true`

only if all of the following hold on the current R9 live acquisition:

- all mandatory fresh roles obtained;
- no stale previous-generation source used;
- no fallback provider;
- attempt isolation PASS;
- full authority graph PASS;
- post-R7 direction guard PASS;
- replay PASS;
- current Market adapter 2/2 PASS;
- stock 22/22 PASS.

Do not inherit this flag from old results.

---

# 28. No old AI output reuse

After R9 source qualification, **do not reuse** R5/R6 Market/Core/A/B outputs.

Fresh data requires fresh inference.

Old AI outputs may be used only after R9 result sealing for descriptive regression.

---

# 29. Fresh Market/Core/A/B execution

Only after R9 full-source qualification.

Run completely fresh:

- Market `2/2`
- Core `22/22`
- A/New Buyer `22/22`
- B/Holder `22/22`

Use current accepted model/prompt/schema/policy.

No independent-review target labels.

No old model candidates.

Transport:

- exact current accepted model configuration;
- one initial attempt;
- existing accepted timeout;
- no semantic retry;
- no schema repair;
- no fallback;
- no judge;
- no selective per-ticker rerun.

If a model transport failure occurs, use only the project's already accepted transient transport retry policy; do not retry semantic/policy failures.

Record actual counts.

---

# 30. Fresh 24-message proof

Render exactly:

## US
- market = 1
- stocks = 14
- total = 15

## KR
- market = 1
- stocks = 8
- total = 9

Combined:

`24/24`

Each message must bind:

- R9 run seed
- R9 source packet
- R9 Market/Core/A/B output
- R9 source refs
- R9 current/session dates
- message hash.

No R6/R7 rendered message reuse.

---

# 31. Market-message semantic requirements

Review both fresh market messages.

Require:

- correct target session;
- no stale source presented as current;
- sector TOP3/BOTTOM3 when qualified;
- breadth/participation interpretation only when qualified;
- macro latest/current wording correct;
- no old date-heavy macro dump if current user-facing product policy does not require it;
- no official-final-close claim;
- no source/debug hashes in user-facing text;
- configured night-futures scope only.

If Market has insufficient same-session direction evidence:
- say so;
- do not replace it with stale macro.

---

# 32. Stock-message semantic requirements

For every stock require:

- Overall;
- New Buyer;
- Holder;
- current price/as-of context where allowed;
- fundamental/entry range only if basis valid;
- technical timing context if valid;
- exact current business evidence;
- no absolute-current financial fact used directionally;
- UNKNOWN_LIMIT when directional entitlement is zero.

Explicit fresh controls:

## 005930
Must not become positive merely because current revenue/profit is positive.

## 047810
Same.

## SNDK
Context-only evidence must remain non-directional.

## 000660 / SKHY
Fresh quality/issuer semantics only.

---

# 33. Human-review bundle

On full PASS create:

`r2b-r9-fresh-24-message-human-review.zip`

Include:

- exact 24 messages;
- 22 stock source summaries;
- US/KR Market source summaries;
- macro freshness ledger;
- current/prior financial comparison matrix;
- 005930 fresh evidence trace;
- 047810 fresh evidence trace;
- SNDK trace;
- SKHY trace;
- provider call ledger;
- source hashes;
- AI call ledger;
- validation.

This is the artifact to review before scheduler cutover.

---

# 34. Old-versus-fresh comparison is post-seal only

After the R9 24-message result is sealed, optionally compare descriptively against R7/R6.

Do not use the old outputs as model targets.

Useful post-seal checks:

- which previously UNKNOWN_LIMIT subjects now have comparative direction;
- whether 005930 gained valid current/prior evidence;
- whether US Market still reports insufficient data;
- whether macro timestamps are now current/latest-published verified;
- message stability.

No retuning inside R9.

---

# 35. Production side effects

Hard zero throughout R9:

- Telegram sends
- recipient intent
- production DB decision/warning writes
- scheduler mutation
- notification mutation
- broker actions
- deploy
- main merge
- remote push
- service restart

This remains a live-source + AI dry-run qualification.

---

# 36. Scheduler remains inactive

Do not activate schedules in R9.

Do not:
- unpause old primary/backup automations;
- install new launchd jobs;
- enable new unified jobs.

Scheduler cutover is a separate final task after human approval of the fresh 24-message proof.

---

# 37. R9 success terminal

Use:

`R2B_R9_FULL_FRESH_ALL_SOURCE_24_MESSAGE_PASS_READY_FOR_HUMAN_REVIEW`

only if:

1. all mutable roles are newly retrieved in R9;
2. stock packets = 22/22;
3. Market source contexts = 2/2;
4. macro currentness/publication state complete;
5. configured night/publication context qualified;
6. R9 full-source authority graph PASS;
7. post-R7 absolute-current direction guard PASS;
8. network-free replay PASS;
9. `COMPLETE_SOURCE_ADAPTER_QUALIFIED = true`;
10. fresh Market/Core/A/B all pass;
11. rendered messages = 24/24;
12. provider fallback = 0;
13. Alpha = 0;
14. production side effects = 0;
15. human-review ZIP generated.

---

# 38. Honest partial terminals

Use exact bounded failure states.

## Source role missing

`R2B_R9_FULL_FRESH_SOURCE_COVERAGE_PARTIAL`

Return every missing role/subject.

No AI.

## Macro currentness unresolved

`R2B_R9_MACRO_CURRENTNESS_GAP`

No stale cached substitute.

## Financial comparison partial

`R2B_R9_FRESH_FINANCIAL_COMPARISON_PARTIAL`

Return exact subject/field/period/source blocker.

No forced direction.

## Market source partial

`R2B_R9_MARKET_SOURCE_PARTIAL`

No Market AI.

## Adapter qualification gap

`R2B_R9_LIVE_ADAPTER_REQUALIFICATION_GAP`

No scheduler authorization.

## Model stage failure

Use exact Market/Core/A/B/render terminal and preserve the successfully sealed R9 source corpus.

Do not recollect data because AI failed.

---

# 39. Required validation

At minimum:

## Freshness
- prior packet reuse negative
- prior raw artifact reuse negative
- stale cache negative
- new retrieval receipt requirement
- latest-published macro positive/negative
- publication/currentness proof

## Stock
- all 22 fresh role coverage
- price/OHLCV
- technical
- current/prior financial
- quality
- source-use
- 005930
- 047810
- SNDK
- 000660
- SKHY
- CPNG anomaly

## Market
- US indices/proxies
- US sectors
- US breadth
- KR indices
- KR sectors
- KR breadth
- optional flows
- macro roles
- night/publication
- session ownership

## R7 guard
- absolute current positive amount -> not directional
- absolute current negative amount -> not automatically directional
- compatible comparison -> existing direction semantics
- zero direction -> UNKNOWN_LIMIT

## Adapter
- attempt isolation
- no fallback
- offline replay twice
- source authority
- current Market adapter
- COMPLETE_SOURCE_ADAPTER qualification

## AI
- fresh prompt/input binding
- Market 2/2
- Core 22/22
- A 22/22
- B 22/22
- 24/24 render

## Repository
- focused tests
- full pytest
- Ruff
- git diff --check
- Investment Knowledge
- Chart Knowledge
- secret scan
- no unexplained skip/xfail.

---

# 40. Required result bundle

Return immutable ZIP + `.sha256` containing at minimum:

- `REPORT.md`
- `summary.json`
- R7 runtime identity receipt
- R8 supersession receipt
- repository identities
- changed-file inventory

## Plan
- full fresh role inventory
- provider request plans/budgets
- market-session gate
- execution mode
- no-fallback proof

## Raw/source
- request/read receipts
- raw/source hashes
- normalization hashes
- session/publication times
- macro freshness ledger
- night-futures receipts
- all 22 stock source receipts

## Financial/business
- 22 current financial-source matrix
- current/prior comparison matrix
- quality matrix
- event matrix
- source-use/direction matrix
- 005930 trace
- 047810 trace
- SKHY trace
- SNDK trace

## Source closure
- 22 R9 packet matrix/hashes
- Market 2/2 packet hashes
- R9 FullSourceRunSeed
- US/KR/combined source hashes
- authority graph
- replay twice
- source-adapter qualification receipt

## AI
- fresh model-input binding
- Market/Core/A/B call ledgers
- raw/accepted outputs
- validators
- 24 message inventory/hashes

## Human review
- `r2b-r9-fresh-24-message-human-review.zip`
- SHA

## Safety
- Alpha 0
- fallback 0
- Telegram 0
- production DB 0
- scheduler 0
- broker/deploy/merge/push/restart 0
- secret scan
- bundle manifest

---

# 41. After PASS — generate only

On full R9 PASS, generate—but do not execute—the final:

`Post-R9 Unified Scheduler Cutover`

instruction.

It must:

- verify human approval is recorded;
- preserve one US unified schedule;
- preserve one KR unified schedule;
- retire/keep-disabled legacy primary/backup paths;
- duplicate active scheduling path count = 0;
- preserve trading-day/holiday skip;
- preserve first-complete-attempt semantics;
- preserve failure notice/debug bundle behavior;
- no automatic AI rerun after downstream failure.

Do not activate scheduler inside R9.

---

# 42. Final principle

R9 is not a replay of the old proof.

It is a new end-to-end source generation.

Every mutable market, macro, price, technical and business input must be freshly retrieved or freshly proven latest-published in the R9 generation.

No previous “PASS” may stand in for current data.

Only after that fresh source graph closes may the AI be run again and the system be considered ready for final human review.
