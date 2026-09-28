# Thesis Monitor — R2B-R9-REV10
## Final event/quality + valuation + aggregate whole-source offline closure
### Then full fresh all-source recollection, post-R7 live adapter requalification, fresh Market/Core/A/B and exact detailed 24-message proof

**REV10 supersedes every prior unexecuted R2B-R9 instruction. Execute only REV10.**

REV9 correctly stopped before network.

REV9 closed and must preserve:

- current-only valid financial context → no fake quality → `UNKNOWN_LIMIT / OBSERVE`;
- bounded SEC absence-of-prior ownership;
- insurance-revenue semantics;
- field-isolated quality caution;
- issuer bridge descriptor with zero security-valuation transfer;
- conditional native PER/PBR parsing;
- negative-EPS `N/M`;
- detailed section owner/omission contract;
- synthetic UNKNOWN_LIMIT final sender-boundary capture;
- direct-comparison Core/A/B input readiness 22/22.

Exactly three root gates remain:

1. heterogeneous fresh/persisted event + fully-denied-quality + all NORMAL archetype final paths;
2. complete valuation typed matrix across deterministic/native/forward/historical cases;
3. one common-generation all22 + Market2 + macro/night + authority + replay twice + exact24 offline aggregate proof.

The final provider plan and live execution are dependent consequences of these three gates.
Do not list them as separate root P1s.

REV10 must close all three offline first.
If they PASS, REV10 must automatically issue the exact finite provider plan and continue into the full fresh live/ad-hoc proof in the same task.

No old mutable source may fill a current role.
No old model output may be reused.
No new provider may be introduced.
Alpha Vantage remains 0.

---

# 0. Newest SoT

Adopt REV9 as the newest implementation SoT.

REV9 result ZIP SHA-256:

`6790ff1c132034f4714580a388aee04adfef81e450774b62d4fadeda1c948ea8`

Uploaded sidecar:
exact match.

Independent bundle-manifest recheck:

- declared payloads: `915`
- actual manifest-scope payloads: `915`
- missing: `0`
- hash/size mismatch: `0`
- extra: `0`

Terminal:

`R2B_R9_REV9_PREFLIGHT_CONTRACT_GAP`

Repository:

- branch:
  `codex/r2b-r9-rev9-contract-closure`
- base:
  `62d5c74a97b2d1d1b377be9593c34671ebe345ef`
- work-instruction:
  `78150bcd39e8db743f470a6608f43242d6dc8942`
- exact tested implementation/final:
  `4a976b7d4f0d10c403c0225c6173f00c2c3bd9fb`
- operating main:
  `b610e6de0a8c33d199961e821ff1b130e1fa9ad4`

REV9 validation:

- focused:
  `537 PASS`
- full:
  `6404 PASS / 63 unchanged skips / 0 failures`
- Ruff / diff / Investment Knowledge / Chart Knowledge:
  PASS
- provider calls:
  `0`
- model calls:
  `0`
- production side effects:
  `0`

Do not revert accepted REV9 code.

---

# 1. Preserve accepted REV9 semantics

Do not reopen:

## 1.1 Current-only → UNKNOWN_LIMIT

Accepted positive path:

- current source acquired and owned;
- prior occurrence explicitly absent within bounded owner;
- comparison applicability =
  `QUALITY_NOT_APPLICABLE_NO_DIRECTIONAL_COMPARISON`;
- no fake financial-quality fact;
- no directional ref;
- Core/A/B → OBSERVE;
- actual detailed sender-boundary capture PASS.

Keep the distinction between:
- valid no-comparison;
- missing lineage/owner/source failure.

UNKNOWN_LIMIT must never hide an owner bug.

## 1.2 Issuer bridge

Preserve:
- same-legal-issuer business bridge when currently qualified;
- no price transfer;
- no technical transfer;
- no per-share denominator transfer;
- no security valuation transfer.

## 1.3 Valuation guard

Preserve:
- provider-native multiple is not automatically a current-price recomputation;
- valuation does not own Overall direction;
- missing basis/horizon/currentness → unavailable;
- negative EPS → N/M;
- no cross-security transfer.

## 1.4 Detailed renderer

Preserve user-facing stock format:

1. optional actual pilot label;
2. company/ticker;
3. AI judgment / balance or UNKNOWN_LIMIT / confidence / maturity / New Buyer / Holder;
4. reevaluation;
5. thesis / structural risk / market expectations;
6. core judgment;
7. business/earnings;
8. existing warnings;
9. key monitoring;
10. current price structure;
11. flow/positioning;
12. Valuation.

Do not render standalone:
- existing registered price rules;
- data caution;
- next checks;
- unresolved/unknown.

---

# 2. Remove hardcoded preflight blockers

Current `scripts/r2b_r9_full_fresh_requalification.py::candidate_plan()` contains literal gap strings such as:

- `FRESH_WHOLE_SOURCE_ALL22_MARKET_CONTEXT_REPLAY_NOT_QUALIFIED`
- `HETEROGENEOUS_EVENT_AND_DETAILED_ARCHETYPE_PROOF_NOT_CLOSED`
- `DETERMINISTIC_FORWARD_HISTORICAL_VALUATION_OWNER_PROOF_NOT_CLOSED`
- `COMPLETE_DETAILED_SECTION_OWNERS_AND_END_TO_END_24_CAPTURE_NOT_CLOSED`

This was appropriate while those implementations were absent, but REV10 must not leave dispatch permanently blocked by static strings after proof exists.

Replace the static blocker list with a receipt-derived Phase-A gate.

The controller must consume exact immutable proof receipts for:

- event/archetype gate;
- valuation matrix gate;
- aggregate whole-source gate;
- Market2 gate;
- Core/A/B all22 gate;
- exact24 sender-boundary gate;
- final finite provider plan.

`dispatch_allowed=true` only when every required receipt is PASS and hashes bind to the exact current code/policy/schema.

No count-only or caller-asserted PASS.

---

# 3. Root Gate A — fresh/persisted event ownership

REV9 root cause:

> Fresh descriptor has no event acquisition carrier; legacy event owner bounds availability by `business_cutoff`, while financial packet `generated_at` is collection start.

Implement event ownership in the fresh controller rather than importing old event output.

---

# 4. Separate event times explicitly

A fresh event path must distinguish:

- `collection_started_at`;
- `request_started_at`;
- `received_at`;
- `event_published_at`;
- `business_availability_cutoff`;
- `source_query_cutoff`;
- current proof/generation ID.

Do not use one timestamp for all meanings.

Rules:

- an event may be acquired after collection start;
- its source publication timestamp remains whatever the source owns;
- receipt time cannot be backdated;
- publication time cannot be replaced with collection start;
- a response received after the allowed business-availability cutoff cannot enter the packet;
- a publication later than the allowed source cutoff cannot enter the packet.

Do not claim a freshly retrieved response was present in the packet before it was received.

---

# 5. Fresh event descriptor/carrier

Extend the R9 fresh stock descriptor with an optional typed event carrier.

At minimum:

- ticker/security/issuer identity;
- event provider/source family;
- frozen acquisition plan;
- request/response/raw artifact bindings;
- request timestamp;
- response timestamp;
- publication timestamp;
- source URL/document identity;
- normalization receipt;
- event fingerprint;
- classification;
- relevance;
- `requires_review`;
- allowed/prohibited uses;
- current eligibility receipt;
- acquisition class:
  - `FRESH_CURRENT_RUN`;
  - `PERSISTED_SOURCE_RECHECK`.

The controller must read/verify the event carrier exactly like financial/valuation carriers:
relative paths, SHA checks, no symlink/parent escape, exact run ownership.

---

# 6. Fresh event path

Build a generic offline fixture for a newly acquired qualified event.

Require:

- finite pre-frozen plan;
- response received within business cutoff;
- publication timestamp source-owned;
- exact normalized event;
- event authority registered;
- allowed/prohibited uses preserved;
- business union integration;
- quality applicability explicit;
- stock packet assembly;
- Core/A/B input readiness;
- detailed final sender-boundary path.

Do not require a fresh event to be directional.
A context-only fresh event may lead to UNKNOWN_LIMIT.

---

# 7. Persisted event path

Build a distinct persisted-event carrier.

It must preserve:

- original acquisition/run ID;
- original provider;
- original raw body/response;
- original publication timestamp;
- original event fingerprint;
- original normalization;
- original authority;
- original `requires_review`.

REV10 produces a new **current eligibility receipt**, not a new acquisition identity.

Required acquisition class:

`PERSISTED_SOURCE_RECHECK`

Never:
- relabel persisted bytes as fresh;
- overwrite original acquisition time;
- claim the event was reacquired if no new provider call occurred.

Then prove:
persisted event
→ current eligibility
→ stock business union
→ source-use
→ Core/A/B
→ detailed final sender path.

---

# 8. Event-only UNKNOWN_LIMIT

Build an explicit positive fixture:

- packet otherwise complete;
- event exists;
- event is context-only;
- zero direction-eligible business facts;
- event authority remains context-only;
- quality comparison not applicable;
- Core UNKNOWN_LIMIT;
- A OBSERVE;
- B OBSERVE;
- detailed sender capture PASS.

This must not require a fake financial-quality record.

---

# 9. Fully-denied-quality valid consumer path

REV9 proved field-isolated caution but not the complete fully-denied quality consumer.

Construct a valid archetype where:

- comparison facts/source lineage exist;
- canonical business-quality owner returns a fully denied/caution state according to existing policy;
- the packet/source graph remains structurally complete;
- denied quality does not get reclassified as missing source;
- source-use/decision contract handles it exactly as existing policy intends;
- no ref-less quality effect;
- quality by itself does not create Overall direction;
- quality by itself does not create Holder REDUCE/REVIEW unless another authorized reason exists;
- Core/A/B actual input materializers PASS;
- detailed sender path PASS.

If existing policy says the denial should block all directional use:
- preserve that exact behavior;
- it may produce UNKNOWN_LIMIT or another valid limited state.
Do not force evidence-based NORMAL.

---

# 10. All required NORMAL archetypes through actual materializer→sender

REV9 direct22 input readiness is not enough.

Run each required evidence-based archetype through the actual offline stage/materializer chain and final sender boundary.

Required NORMAL archetypes include:

- US domestic SEC comparison;
- FPI comparison;
- KR ordinary OpenDART comparison;
- KR insurance revenue;
- quality clean;
- quality caution/denied as policy permits;
- direct current-security valuation qualified;
- valuation unavailable;
- valuation N/M;
- issuer bridge business evidence;
- fresh event where directional/event policy permits.

Each must reach:
- Core structured accepted output fixture;
- A structured accepted output fixture;
- B structured accepted output fixture;
- detailed plan;
- final sender payload bytes.

No special simplified renderer.

---

# 11. Root Gate B — complete valuation typed matrix

REV9 valuation state:

- native PER/PBR:
  conditional synthetic PASS when currency + metricAsOf exist;
- negative EPS:
  N/M PASS;
- fPER missing horizon:
  unavailable PASS;
- unavailable:
  PASS;
- deterministic SEC:
  OPEN;
- deterministic DART:
  OPEN;
- qualified fPER:
  OPEN;
- historical compatible distribution:
  OPEN.

REV10 must close the **contract matrix**, not force every live subject to have every metric.

A metric may remain unavailable in live data.

The gate passes when each possible state has an owned path:
- QUALIFIED;
- NOT_MEANINGFUL;
- UNAVAILABLE.

---

# 12. Existing authorized valuation sources only

Do not add providers.

Audit/use only already authorized/configured repository sources, including where actually present:

- Finnhub stock metrics/estimates;
- SEC;
- OpenDART;
- existing versioned historical valuation distributions;
- existing current stock/quote owners.

Alpha Vantage:
`0`.

Massive:
`0`.

No new commercial valuation provider.

---

# 13. Finnhub native PER/PBR

For a fresh native metric to be `QUALIFIED`, require:

- fresh R9 provider read;
- exact symbol/current traded security mapping;
- explicit currency from source/owned security metadata under current contract;
- source metric as-of / exact currentness metadata;
- valid numeric field;
- provider-native method explicitly labeled;
- source receipt/hash;
- no evidence of underlying/wrong security.

Do not present it as `current price ÷ owned denominator` unless that exact denominator is separately owned.

Renderer wording may say:
- `현재 PER: x배`;
- `현재 PBR: y배`;

but internal receipt must mark:
`PROVIDER_NATIVE_CURRENT_MULTIPLE`.

If metric as-of/currency/current-security identity is missing:
UNAVAILABLE.

---

# 14. Deterministic SEC PER/PBR contract

Do not broaden SEC business-direction authority.

Add a **valuation-specific** denominator projection.

For PER:

Accept only a denominator that can be owned for the current traded security/share basis.

Possible approved constructions, only if exact source semantics support them:

- directly reported per-share diluted/basic EPS with current-security share-class compatibility;
- exact TTM EPS assembled from four compatible quarter occurrences under one accepted formula.

Require:
- exact issuer;
- exact security/share basis;
- exact concepts;
- periods;
- units;
- split/share basis;
- currency compatibility;
- source row lineage.

No missing-quarter synthesis.
No annual/interim mixing unless the existing valuation contract explicitly owns it.

For PBR:

Require exact book-value-per-share denominator, or deterministic:

`eligible equity numerator ÷ eligible shares denominator`

only when both own the same current-security/share basis.

Do not use consolidated total equity divided by an unrelated/ambiguous share denominator.

If share basis cannot be proven:
UNAVAILABLE.

---

# 15. Deterministic OpenDART PER/PBR contract

Create an exact standard-concept valuation registry.

No fuzzy Korean/English account-name match.

For each accepted EPS/BPS/equity/share concept require:

- exact standard concept ID or already accepted explicit canonical mapping;
- statement role;
- report/fiscal period;
- consolidated/separate basis;
- KRW/unit;
- current ordinary-share basis;
- share-count/basis compatibility;
- exact source occurrence.

For 005930/047810/other KR stocks:
do not assume the same denominator exists.

If no exact current-security denominator:
metric unavailable.

Do not block the stock/message solely because an optional valuation metric is unavailable.

---

# 16. Qualified fPER contract

A qualified fPER needs more than a `forwardPE` number with no horizon.

Use only an existing authorized estimate owner.

Before live use, prove offline:

- exact traded security;
- provider/source;
- forward EPS or native forward multiple;
- estimate horizon, e.g. FY1/NTM or exact fiscal period;
- estimate as-of/publication timestamp;
- latest-published/currentness at R9 query time;
- currency/share basis;
- source receipt/hash.

If the configured Finnhub metric endpoint does not expose sufficient horizon/currentness:
- it remains UNAVAILABLE through that endpoint.

If an already-configured Finnhub estimate/consensus route in the repository does expose an exact period/horizon:
- freeze its exact endpoint/request/budget;
- use it.

Do not add an unconfigured endpoint spec by assumption.
Audit repository capability first.

If no exact horizon owner exists:
the **qualified-fPER path may be proven unavailable by contract**, and live fPER remains `판단 자료 부족`.

The valuation matrix gate does not require forcing a value; it requires a deterministic owned state.

---

# 17. Historical valuation distribution contract

Audit existing versioned historical valuation assets.

A historical percentile/median may render only when:

- versioned artifact ID/hash;
- same traded security;
- same metric definition;
- same share/security basis;
- compatible provider/method semantics;
- explicit historical window;
- current metric is qualified and comparable.

Historical artifacts may be reused as versioned reference data.
They are not current mutable values.

If no compatible versioned distribution exists:
historical comparison is unavailable/omitted.

Do not synthesize a distribution from arbitrary stored ratios.

---

# 18. Complete valuation matrix PASS definition

Produce:

`complete-valuation-contract-matrix.json`

Must include proof for:

- native PER qualified;
- native PBR qualified;
- deterministic SEC PER qualified or explicit source-semantic impossibility;
- deterministic SEC PBR qualified or explicit source-semantic impossibility;
- deterministic DART PER qualified or explicit source-semantic impossibility;
- deterministic DART PBR qualified or explicit source-semantic impossibility;
- fPER qualified if an existing exact owner exists, otherwise exact UNAVAILABLE owner;
- fPER missing horizon → unavailable;
- negative EPS → N/M;
- invalid/non-positive book basis → N/M or unavailable under policy;
- security basis unresolved → unavailable;
- historical compatible → display if an existing versioned fixture exists;
- historical incompatible/unavailable → omit;
- current price binding;
- no Overall-direction authority;
- no cross-security transfer.

Gate passes if every row has an exact owned state.
It does not require all rows to be numerically QUALIFIED.

---

# 19. Root Gate C — one common-generation aggregate proof

Build a single offline proof generation.

It must use one:

- `generation_id`;
- `run_started_at`;
- `business_availability_cutoff`;
- `query_as_of`;
- static identity/config version set;
- policy/schema hash set.

Do not combine independently generated fixture outputs with unrelated clocks/hashes and call that aggregate proof.

---

# 20. Exact synthetic all22 archetype assignment

Create one deterministic 22-subject offline cohort using the real roster and fresh-controller schemas.

The fixture data is synthetic, but the owner/archetype path must cover the current product's heterogeneous cases.

At minimum the 22 rows collectively include:

- ordinary US domestic SEC comparison;
- FPI comparison;
- KR ordinary OpenDART;
- insurance revenue;
- clean quality;
- denied/caution quality;
- current-only UNKNOWN_LIMIT;
- issuer bridge;
- persisted context event;
- fresh event;
- valuation native qualified;
- valuation deterministic qualified if contract supports;
- valuation N/M;
- valuation unavailable.

The mapping of ticker→fixture archetype is test-only.
Do not encode it in production logic.

---

# 21. Aggregate macro/night/Market fixture

In the same generation build:

## US Market

- major proxy/index facts;
- sector universe;
- breadth if current contract expects it;
- macro facts with source-owned observation periods;
- selected display plan.

## KR Market

- KOSPI/KOSDAQ;
- venue sectors;
- breadth/flow where expected;
- USD/KRW with source period;
- selected display plan.

## Night

- KOSPI200 only;
- D/W/M availability states.

All share the common generation/source-time domain.

---

# 22. Aggregate full-source composition

Compose:

- 22 stock packets;
- US Market component;
- KR Market component;
- macro;
- night;
- quality;
- valuation;
- events/bridges;
- optional denials;
- authority graph.

Produce a new offline:

- FullSourceRunSeed;
- US whole-source packet;
- KR whole-source packet;
- combined packet;
- authority graph.

No old mutable packet.

---

# 23. Aggregate replay twice

Replay the entire common-generation graph twice.

Require exact semantic/hash equality for:

- 22 stock packets;
- US Market component;
- KR Market component;
- macro;
- KOSPI200 night;
- event/bridge states;
- quality views;
- valuation views;
- US whole-source packet;
- KR whole-source packet;
- combined packet;
- authority graph.

Any wall-clock field that legitimately differs must be excluded from semantic identity under an already-owned contract, not ignored ad hoc.

---

# 24. Actual Market2 input/display proof

Feed the same aggregate packets into the exact current Market adapters.

Require:

- US Market input `1/1`;
- KR Market input `1/1`;
- exact source/numeric validation;
- selected user display plan;
- actual Market renderer;
- actual payload builder;
- final isolated sender-boundary bytes.

US final blocks:
- major indices/proxies;
- macro;
- judgment/confidence;
- sector TOP3/BOTTOM3 or 자료 부족;
- KOSPI200 D/W/M.

KR final blocks:
- market judgment;
- KOSPI TOP3/BOTTOM3;
- KOSDAQ TOP3/BOTTOM3;
- USD/KRW.

No all-numeric dump.

---

# 25. Actual all22 Core/A/B materializer proof

From the same aggregate graph:

Require:

- Core input/materializer/validator `22/22`;
- A input/materializer/validator `22/22`;
- B input/materializer/validator `22/22`.

Include:
- evidence-based NORMAL;
- UNKNOWN_LIMIT;
- quality denied/caution;
- bridge;
- event;
- qualified valuation;
- N/M valuation;
- unavailable valuation.

Use structured synthetic model outputs only to exercise the exact deterministic post-model contract.
No external model calls in Phase A.

No subset-only probe.

---

# 26. Exact24 offline final-boundary proof

Using the same aggregate generation:

Render/capture:

- Market US 1;
- Market KR 1;
- US stocks 14;
- KR stocks 8.

Total:
`24/24`.

Use the actual:
- Market renderer;
- detailed stock plan/renderer;
- payload builder;
- message/chunk preparation;
- isolated final send sink.

Do not reconstruct text after the fact.

Require:

- evidence-based detailed messages;
- UNKNOWN_LIMIT detailed messages;
- valuation section on every stock;
- removed standalone stock sections absent;
- no ref/hash/debug leakage;
- exact payload SHA per message.

---

# 27. Phase-A root-gate receipt

Create one immutable:

`r9-rev10-phase-a-root-gate.json`

Required fields:

- event_archetype_gate;
- denied_quality_gate;
- valuation_matrix_gate;
- aggregate_whole_source_gate;
- replay_twice_gate;
- Market2_gate;
- Core22_gate;
- A22_gate;
- B22_gate;
- exact24_gate;
- code SHA;
- policy/schema hashes;
- proof artifact hashes.

`dispatch_allowed=true` only if every required gate is PASS.

No literal hardcoded blocker strings after PASS.

If any gate fails:
`R2B_R9_REV10_PREFLIGHT_CONTRACT_GAP`
and provider/model calls remain 0.

---

# 28. Final provider plan

Only after Phase-A PASS.

Generate and seal the exact live plan from current code.

Include fresh reads needed for:

- stock price/OHLCV/technical;
- US Market;
- KR Market;
- FRED;
- EIA;
- ECOS;
- KOSPI200 night;
- SEC;
- OpenDART;
- event/news where the current role inventory requires it;
- Finnhub valuation/estimate reads only if existing configured owner is qualified.

For every provider:

- exact logical request identities;
- subjects/universe;
- endpoint/source family;
- page/document cap;
- timeout;
- retries;
- theoretical max attempts;
- mandatory/optional role.

Alpha Vantage:
`0`.

Massive/mock/undeclared fallback:
`0`.

No live request outside the sealed plan.

---

# 29. Fresh live/ad-hoc generation

Only after `dispatch_allowed=true`.

Use current scheduled-window mode or ad-hoc live requalification mode exactly as the current product contract permits.

At actual execution time:

- recompute exchange calendars;
- determine latest eligible completed US session;
- determine latest eligible completed KR session;
- freeze actual query time;
- freeze business availability cutoff;
- freeze provider plans.

Do not pretend ad-hoc execution was scheduled.

---

# 30. Full fresh all22 acquisition

Freshly acquire all mutable roles for:

US14:
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

KR8:
- 000660
- 003690
- 005490
- 005930
- 010120
- 012450
- 047810
- 086280

No complete-control exemption.

Fresh current-generation:
- current price;
- D/W/M OHLCV;
- technical;
- financial/business;
- comparison applicability;
- event carrier where configured;
- quality;
- valuation;
- flow/positioning;
- bridge if required.

---

# 31. Fresh Market/macro/night acquisition

US:
- selected major/style/index proxy roles;
- sector universe;
- breadth/participation where owned;
- macro;
- KOSPI200 night context.

KR:
- KOSPI/KOSDAQ;
- venue-specific sectors;
- breadth;
- investor flow where owned;
- USD/KRW.

Macro:
fresh retrieval + source-owned observation period/currentness.

Night:
KOSPI200 only.

No stale-cache substitution.

---

# 32. Fresh event semantics

Fresh event:

- event request/response receives current R9 IDs/times;
- publication time remains source-owned;
- availability cutoff enforced.

Persisted event:

- no new acquisition claim;
- original immutable source;
- new current-eligibility receipt.

No event-query broadening to force PASS.

---

# 33. Fresh valuation live semantics

For all22 create CurrentValuationView.

Each metric independently:

- QUALIFIED;
- N/M;
- 판단 자료 부족.

Use only current qualified sources.

Do not stop whole live proof merely because optional PER/PBR/fPER is unavailable.

Stop only if the valuation **typed contract itself** cannot produce an owned state.

Valuation section always renders.

---

# 34. Fresh source closure

Require live:

- stock packets `22/22`;
- Market source `2/2`;
- mandatory macro currentness explicit;
- KOSPI200 night;
- quality views all22;
- valuation views all22;
- event/bridge states complete under current policy.

Generate new:

- FullSourceRunSeed;
- US packet;
- KR packet;
- combined packet;
- authority graph.

No prior current-source hash reused as current identity.

---

# 35. Live replay twice

Freeze live raw/source corpus.

Disable external access.

Replay entire graph twice.

Require exact equality for the same aggregate dimensions as Phase A.

Then:

`NETWORK_FREE_SOURCE_ADAPTER_PREQUALIFIED = true`.

Only if current live role coverage also passes:

`COMPLETE_SOURCE_ADAPTER_QUALIFIED = true`.

Do not inherit qualification.

---

# 36. Fresh AI

Run completely fresh:

- Market `2/2`;
- Core `22/22`;
- A `22/22`;
- B `22/22`.

No old model output reuse.
No independent-review target labels.
No result-driven source refresh.
No semantic/schema repair.
No fallback/judge/selective ticker rerun.

Use only current approved transient transport retry policy.

---

# 37. Final US Market message

`미국 시장 · YYYY-MM-DD`

Display:

1. SPY/QQQ/etc selected major roles with change + %;
2. compact fresh/current or latest-published-verified macro;
3. market judgment + confidence;
4. sector TOP3/BOTTOM3 or 자료 부족;
5. KOSPI200 day/week/month.

No KOSDAQ150.

No stale macro.

---

# 38. Final KR Market message

`한국 시장 · YYYY-MM-DD`

Display:

1. market judgment:
   - KOSPI/KOSDAQ;
   - breadth/flow when owned;
2. sector:
   - KOSPI TOP3/BOTTOM3;
   - KOSDAQ TOP3/BOTTOM3;
3. USD/KRW:
   - level;
   - change if owned;
   - observation date if needed.

---

# 39. Final detailed stock message

Stable order:

1. optional actual pilot label;
2. company/ticker;
3. AI judgment / balance or UNKNOWN_LIMIT / confidence / maturity / New Buyer / Holder;
4. reevaluation;
5. thesis/risk/expectation;
6. core judgment;
7. business/earnings;
8. existing warnings;
9. key monitoring;
10. current price structure;
11. flow/positioning;
12. Valuation.

Do not render standalone:
- registered price rules;
- data caution;
- next checks;
- unresolved/unknown.

Valuation section mandatory.

Every metric row:
- qualified value;
- N/M;
- 판단 자료 부족.

No unsupported number.

---

# 40. Exact final sender-boundary capture

Capture exact bytes passed to production sender interface with delivery disabled.

Required:

- MARKET_US
- MARKET_KR
- US14 stock messages
- KR8 stock messages
- ALL_MESSAGES.md

Total:
`24/24`.

No post-hoc reconstruction.

---

# 41. Human-review bundle

On full PASS create:

`r2b-r9-rev10-fresh-24-message-human-review.zip`

Include:

- exact 24 payloads;
- message hashes;
- Market display-plan audit;
- detailed stock-plan audit;
- final-boundary traces;
- final provider plan;
- planned/theoretical/actual call ledger;
- macro currentness;
- KOSPI200 D/W/M;
- all22 stock source summary;
- current/prior comparison matrix;
- event matrix;
- quality matrix;
- valuation matrix;
- valuation source/denominator receipts;
- 005930/047810/SKHY/SNDK traces;
- fresh AI ledger;
- validation.

---

# 42. Production side effects — hard zero

Throughout REV10:

- Telegram send = 0;
- recipient intent = 0;
- production DB decision/warning writes = 0;
- scheduler mutation = 0;
- notification mutation = 0;
- broker = 0;
- deploy = 0;
- main merge = 0;
- remote push = 0;
- restart = 0.

---

# 43. Success terminal

Use only:

`R2B_R9_REV10_FULL_FRESH_ALL_SOURCE_24_MESSAGE_PASS_READY_FOR_HUMAN_REVIEW`

Require:

1. event/persisted-event gate PASS;
2. fully-denied-quality gate PASS;
3. all required NORMAL archetype sender paths PASS;
4. valuation typed matrix PASS;
5. aggregate common-generation all22 whole-source PASS;
6. aggregate replay twice PASS;
7. Market2 PASS;
8. Core/A/B offline 22/22 PASS;
9. exact24 offline final-boundary PASS;
10. phase-a gate receipt PASS;
11. `dispatch_allowed=true`;
12. exact finite live provider plan issued;
13. all mandatory mutable live roles freshly acquired;
14. live stock 22/22;
15. live Market 2/2;
16. macro/USDKRW currentness PASS;
17. KOSPI200-only PASS;
18. fresh quality views all22;
19. fresh valuation views all22;
20. event/bridge live states complete;
21. R7 direction guard PASS;
22. live replay twice PASS;
23. `COMPLETE_SOURCE_ADAPTER_QUALIFIED=true`;
24. fresh Market/Core/A/B complete;
25. exact final payloads 24/24;
26. message contracts PASS;
27. Alpha/fallback 0;
28. production side effects 0;
29. human-review ZIP created.

---

# 44. Honest stop terminals

## Offline root gate remains open

`R2B_R9_REV10_PREFLIGHT_CONTRACT_GAP`

No provider/model calls.

## Provider plan incomplete

`R2B_R9_REV10_PROVIDER_BUDGET_GAP`

No affected provider call.

## Fresh source partial

`R2B_R9_REV10_FULL_FRESH_SOURCE_PARTIAL`

No AI.

## Financial source/lineage failure

If a current-only source is valid with explicit no-comparison:
UNKNOWN_LIMIT may proceed.

If source acquisition/lineage itself fails:
`R2B_R9_REV10_FRESH_FINANCIAL_SOURCE_PARTIAL`.

## Event source gap

If event is optional and another valid business path exists:
preserve optional unavailable.

If event is mandatory for the subject's only business completeness path and acquisition/current-eligibility fails:
return exact event-source blocker.

No old event relabel.

## Valuation

Optional metric unavailable does not fail the run.

Fail only if CurrentValuationView cannot produce an owned QUALIFIED/N-M/UNAVAILABLE state.

Terminal:
`R2B_R9_REV10_VALUATION_CONTRACT_GAP`.

## Market/macro/FX partial

Use exact source-role terminal.
No stale fallback.

## Adapter qualification gap

`R2B_R9_REV10_LIVE_ADAPTER_REQUALIFICATION_GAP`.

No scheduler authorization.

## Model/render failure

Use exact stage terminal.
Preserve fresh source corpus.
Do not recollect because downstream failed.

---

# 45. Required validation

## Event
- fresh timing;
- availability cutoff;
- publication timestamp;
- persisted identity;
- event-only UNKNOWN_LIMIT;
- direction-eligible event where policy permits;
- no relabel.

## Quality
- current-only not-applicable;
- clean;
- caution;
- fully denied;
- no ref-less effect;
- quality not sole direction/Holder action.

## Valuation
- native PER/PBR;
- deterministic SEC/DART denominator path or explicit owned unavailable;
- fPER exact horizon path or explicit unavailable;
- N/M;
- security basis;
- current price binding;
- historical distribution compatible/incompatible;
- no cross-security transfer;
- no Overall direction.

## Aggregate
- one generation/clock;
- all22 heterogeneous;
- Market2;
- macro/night;
- authority;
- replay twice;
- Core/A/B;
- exact24 final boundary.

## Renderer
- evidence-based;
- UNKNOWN_LIMIT;
- valuation section every stock;
- removed sections absent;
- no debug/ref/hash leakage.

## Repository
- focused;
- full pytest;
- Ruff;
- diff;
- Investment Knowledge;
- Chart Knowledge;
- secret scan;
- unchanged skip/xfail identity.

---

# 46. Required result bundle

Return immutable ZIP + `.sha256`.

At minimum:

- REPORT.md
- summary.json
- REV9 result identity/SHA
- repository identities
- changed-file inventory

## Phase A
- static-blocker removal proof
- event carrier/availability-time contract
- fresh event fixture
- persisted event fixture
- event-only UNKNOWN_LIMIT
- fully-denied-quality fixture
- NORMAL archetype final-boundary matrix
- valuation capability audit update
- complete valuation contract matrix
- deterministic denominator receipts
- fPER owner/horizon audit
- historical distribution compatibility audit
- common-generation all22 fixture
- aggregate whole-source packets
- replay twice
- Market2 proof
- Core/A/B 22/22 proof
- exact24 offline payloads
- root gate receipt
- final provider plan

## Live fresh
- request receipts;
- raw/normalized hashes;
- stock 22;
- Market/macro/night;
- financial/business/events;
- quality;
- valuation;
- bridges;
- full-source graph;
- replay;
- adapter qualification.

## AI/render
- fresh Market/Core/A/B;
- accepted detailed plans;
- exact payloads/hashes.

## Human review
- `r2b-r9-rev10-fresh-24-message-human-review.zip`
- SHA.

## Safety
- provider planned/theoretical/actual;
- Alpha 0;
- fallback 0;
- production side effects 0;
- validation;
- secret scan;
- manifest.

---

# 47. After full PASS — generate only

Generate but do not execute:

`Post-R9-REV10 Unified Scheduler Cutover`

Require explicit human approval of the exact fresh 24 messages.

No scheduler activation inside REV10.

---

# 48. Final principle

REV9 proved that a valid current-only source can honestly become UNKNOWN_LIMIT without a fake
quality record.

REV10 finishes the remaining product surface:

- events must own time and fresh/persisted identity;
- denied quality must remain owned, not disappear;
- valuation must always resolve to qualified, N/M or unavailable without fabricating a denominator;
- all22 and both markets must survive one common-generation whole-source graph;
- the exact final 24 payloads must be proven before any provider/model money is spent.

Only after those offline gates pass may the full fresh live proof begin.
