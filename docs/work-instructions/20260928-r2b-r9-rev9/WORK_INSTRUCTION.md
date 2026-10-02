# Thesis Monitor — R2B-R9-REV9
## Final archetype + UNKNOWN_LIMIT + valuation + whole-source offline closure
### Then full fresh all-source recollection, post-R7 adapter requalification, fresh Market/Core/A/B and exact detailed 24-message proof

**REV9 supersedes every prior unexecuted R2B-R9 instruction. Execute only REV9.**

REV8 made substantial progress and correctly stopped before network.

Accepted REV8 offline facts:

- direct fresh financial comparison path works end to end for 22 synthetic subject rows;
- Core/A/B offline input readiness is `22/22` on that direct-comparison path;
- FRED/EIA/ECOS raw replay works;
- KOSPI200 raw D/W/M replay works;
- a NORMAL detailed sender-boundary path works;
- issuer-level business evidence does not automatically transfer security valuation;
- provider/model calls remain zero.

REV8 did **not** qualify the full product because four root contracts are still open:

1. fresh current-only business source cannot reach `UNKNOWN_LIMIT` because comparison-quality is required first;
2. heterogeneous business archetypes are not all proven through one controller;
3. fresh PER/PBR/fPER denominator ownership is not connected;
4. full all22 + Market2 + macro/night + authority + replay + detailed sender boundary is not closed.

The fifth REV8 issue, final provider plan / live execution, is dependent on those four root contracts and is not an independent design gap.

REV9 must close those four root contracts offline first.

Only then may it freeze the final provider plan and perform the full fresh live/ad-hoc proof.

No old mutable source may fill a current R9 role.
No old model output may be reused.
No new provider may be introduced.

---

# 0. Newest SoT

Adopt REV8 as the newest implementation SoT.

REV8 result ZIP SHA-256:

`bc7bc9ca8e5f297a52f0b0ffab3366e4e183686d266942c3de83ea56c70b22e8`

Sidecar:
exact match.

ZIP CRC:
PASS.

Terminal:

`R2B_R9_REV8_PREFLIGHT_CONTRACT_GAP`

Repository:

- branch:
  `codex/r2b-r9-rev8-final-integration`
- base:
  `3b8ebcfbe07b91e510013cd07236404fc04e71f0`
- work-instruction:
  `0ae7d84b441921989432437a52b29f4ef2d26d55`
- exact tested implementation:
  `af7f85eba085748265609b27cda42aefdc58faf6`
- operating:
  `b610e6de0a8c33d199961e821ff1b130e1fa9ad4`

REV8 validation:

- focused:
  `1163 PASS`
- full:
  `6358 PASS / 63 unchanged skips / 0 failures`
- Ruff:
  PASS
- git diff --check:
  PASS
- Investment Knowledge:
  PASS
- Chart Knowledge:
  PASS
- provider calls:
  `0`
- model calls:
  `0`
- production side effects:
  `0`

Do not revert accepted REV8 code.

---

# 1. Exact REV8 open ledger

REV8 reported:

## P1-1

`all22 whole-source + Market input/display`

Reason:
component replay exists, but aggregate all22 authority/replay and Market2 proof are not closed.

## P1-2

`issuer bridge and heterogeneous source archetypes`

Reason:
target valuation correctly denies security transfer, but descriptor roundtrip plus insurance,
quality-denied and persisted-event paths are not all qualified.

## P1-3

`current-only source -> UNKNOWN_LIMIT detailed sender capture`

Reason:
`canonical_business_quality_owner.derive_fresh` raises:

`EXPECTED_BUSINESS_QUALITY_OWNER_OUTPUT_MISSING`

because the wanted comparison-quality receipt set is empty before the valid zero-direction consumer can run.

## P1-4

`qualified/N-M valuation + all detailed section owners`

Reason:
no qualified fresh denominator owner is bound; complete thesis/warning/checkpoint/technical section-owner selection not yet proven.

## P1-5

`final provider plan and whole-chain execution`

Dependent on P1-1..4.

REV9 must not report P1-5 as open after P1-1..4 close; instead it must generate the exact finite plan and continue to live proof in the same task.

---

# 2. Preserve accepted contracts

Do not reopen:

- KOSPI200-only night scope;
- Market internal-fact versus selected-display separation;
- source-owned macro observation period;
- R7 absolute-current direction guard;
- bounded SEC/OpenDART owners;
- current source-use contract;
- business/security-quality separation;
- security valuation basis;
- detailed message information architecture;
- removed user-facing stock sections.

No validator/threshold weakening.

---

# 3. P1-3 first — current-only source must reach UNKNOWN_LIMIT honestly

This is the most important semantic gap.

Current failing path:

`fresh current-only reported source`
→ no compatible comparison facts
→ comparison quality receipt set empty
→ `derive_fresh`
→ `EXPECTED_BUSINESS_QUALITY_OWNER_OUTPUT_MISSING`
→ stock assembly stops
→ valid UNKNOWN_LIMIT consumer never gets a chance.

This is wrong when the source owner has honestly proven:

- current source fact exists;
- the current fact is factual/context eligible;
- no compatible prior comparison is available under the bounded current owner;
- no owner/lineage/transport failure occurred;
- no directional fact exists.

Do not solve this by fabricating a comparison or a clean quality record.

---

# 4. Add a typed quality-applicability state for context-only current financial evidence

Audit the existing canonical business-quality contract and implement the smallest generic distinction.

Recommended conceptual states:

- `QUALITY_RECORD_PRESENT`
- `QUALITY_NOT_APPLICABLE_NO_DIRECTIONAL_COMPARISON`
- `QUALITY_EXPECTED_OWNER_OUTPUT_MISSING`

Use repository-native naming if an equivalent type already exists.

## 4.1 `QUALITY_RECORD_PRESENT`

A real comparison/business-quality record exists.

Normal existing quality logic applies.

## 4.2 `QUALITY_NOT_APPLICABLE_NO_DIRECTIONAL_COMPARISON`

Use only when all are proven:

- source acquisition itself succeeded;
- issuer/security ownership succeeded;
- current field lineage succeeded;
- current field is context eligible;
- current/prior compatibility result explicitly says no compatible directional comparison exists;
- comparison absence is an observed owner outcome, not a missing implementation/input;
- no direction-eligible financial fact remains;
- no business-quality comparison effect can be computed because there is no directional comparison to grade.

Required semantics:

- do not create a fake `canonical:financial_quality:*` fact;
- do not map to `verified_usable`;
- do not map to `CONFIDENCE_ONLY`;
- do not imply clean financial quality;
- business-quality effect for directional comparison is **not applicable**;
- the stock may continue to source-use preflight;
- zero directional entitlement may then produce the already accepted `UNKNOWN_LIMIT / OBSERVE`.

The current-only fact remains factual/context evidence only.

## 4.3 `QUALITY_EXPECTED_OWNER_OUTPUT_MISSING`

Use when:

- a comparison/quality output should exist;
- but an input, lineage, source owner or implementation is missing.

This remains fail-closed.

Do not allow UNKNOWN_LIMIT to hide an owner bug.

---

# 5. Exact current-only comparison-absence ownership

Do not infer “no comparison” from an empty list alone.

The bounded financial projection/acquisition result must expose a typed reason for comparison absence.

Accepted examples may include repository-native equivalents of:

- no compatible prior period within bounded owner;
- prior occurrence absent;
- period role incompatible;
- current-only source by product design.

Distinguish these from:

- acquisition failure;
- document missing;
- lineage unresolved;
- statement basis unresolved;
- unit/currency mismatch;
- source-use owner missing.

Only a **successful context source with explicit no-direction comparison result** may take the no-quality-applicable path.

---

# 6. UNKNOWN_LIMIT end-to-end positive proof

Build generic offline fixtures.

At minimum:

1. current-only clean source + explicit no-compatible-prior result
   → quality applicability `NOT_APPLICABLE_NO_DIRECTIONAL_COMPARISON`
   → directional refs `0`
   → Core preflight UNKNOWN_LIMIT PASS
   → A OBSERVE
   → B OBSERVE
   → detailed UNKNOWN_LIMIT plan
   → actual final sender-boundary capture PASS.

2. current-only source + missing lineage
   → FAIL before UNKNOWN_LIMIT.

3. current-only source + transport failure
   → FAIL.

4. compatible comparison exists
   → normal evidence-based quality path, not UNKNOWN_LIMIT.

5. context-only event + no direction
   → UNKNOWN_LIMIT if packet otherwise complete.

6. technical/valuation availability cannot bootstrap direction.

No ticker-specific code.

This closes REV8 P1-3 only if the **actual detailed final-boundary bytes** are proven.

---

# 7. P1-2 — heterogeneous archetype qualification

REV8 direct22 proves only the synthetic direct-comparison owner path.

REV9 must build explicit offline fixtures through the same fresh controller for every product archetype required by the current cohort.

Required archetypes:

1. domestic US SEC direct comparison;
2. foreign-private-issuer direct comparison;
3. KR OpenDART ordinary financial comparison;
4. KR insurance revenue semantic;
5. quality clean;
6. quality caution/denied but source packet still usable according to policy;
7. current-only / UNKNOWN_LIMIT;
8. issuer-level business bridge with security valuation denied;
9. persisted event currently eligible;
10. fresh event currently eligible;
11. valuation qualified;
12. valuation N/M;
13. valuation unavailable;
14. no event/financial direction but complete context packet.

Each archetype must pass:

`raw/source fixture`
→ `fresh financial/business owner`
→ `quality applicability/state`
→ `valuation view`
→ `stock packet`
→ `evidence/source-use`
→ `Core/A/B input readiness`
→ `detailed plan`
→ `sender-boundary fixture`.

Do not require every archetype to have an evidence-based directional result.

UNKNOWN_LIMIT is a valid terminal decision mode.

---

# 8. Insurance archetype

Use exact standard IFRS insurance semantics already accepted.

Require:

- `ifrs-full_InsuranceRevenue` maps to canonical revenue only under the existing exact semantic rules;
- current/prior comparison;
- operating-income fact independence;
- financial quality;
- no fuzzy account-name authority;
- full fresh packet integration;
- detailed message business/valuation sections.

No ticker-specific branch.

---

# 9. Quality-denied archetype

Use an offline fixture where source comparison exists but business-quality state is caution/denied.

Required:

- exact quality fact/ref when applicable;
- `CONFIDENCE_ONLY` remains non-directional;
- quality alone cannot downgrade Overall;
- quality alone cannot create Holder REVIEW/REDUCE;
- A/B materializer receives an owned effect;
- detailed message may express lower confidence in user language through existing judgment fields;
- no standalone `데이터 주의` section.

No ref-less confidence effect.

---

# 10. Persisted-event archetype

Use the existing persisted-event contract.

Required:

- original immutable event source;
- new current eligibility decision;
- explicit persisted status;
- no relabel as fresh acquisition;
- exact allowed/prohibited uses;
- no valuation authority;
- no price/technical transfer;
- complete stock/source packet where policy permits;
- detailed plan/final sender path.

Context-only persisted event must not create direction.

---

# 11. Issuer bridge archetype

Build a complete descriptor roundtrip.

Required:

- target traded security;
- source security/issuer;
- same-legal-issuer proof;
- current run;
- source current financial acquisition hash;
- exact bridged business fact IDs;
- bridge receipt hash;
- allowed uses;
- prohibited uses.

Mandatory prohibitions:

- current price transfer;
- technical transfer;
- per-share denominator transfer;
- PER/PBR/fPER transfer;
- security valuation transfer.

Then create the target security's own CurrentValuationView.

If no security-specific denominator exists:
- valuation metrics are unavailable;
- Valuation section remains valid with `판단 자료 부족`.

No fake security metric from issuer bridge.

---

# 12. P1-4 — connect existing authorized valuation capabilities

REV8 audit found existing capabilities but no fresh R9 denominator entitlement.

Do not conclude PER/PBR/fPER are universally unavailable.

Do not add a new provider.

Use already authorized owners only.

---

# 13. Fresh valuation priority/order

For each subject, audit and use the highest-authority current-security-compatible source under existing policy.

Candidate families already present:

## 13.1 Finnhub native metrics / estimates

Existing configured capabilities include:

- `peTTM`
- `pbQuarterly` / `pbAnnual`
- `epsTTM`
- provider consensus / forwardPE paths

REV9 may use Finnhub **only because it is already configured/authorized in the repository**, not as a newly introduced provider.

Before live calls:
- verify exact ticker/security mapping;
- freeze exact endpoint(s);
- freeze one finite request plan;
- freeze timeout/retry;
- prove current-security identity;
- define source-time/currentness.

PER/PBR native metrics must have a current R9 read receipt.

fPER must additionally prove:
- estimate horizon;
- estimate publication/as-of;
- latest-published status.

If native forwardPE lacks a provable horizon/currentness:
- `fPER: 판단 자료 부족`.

No Alpha Vantage.

## 13.2 SEC official denominator derivation

The already-authorized SEC source may contain:

- EPS;
- equity/book;
- shares.

Extend **valuation-specific projection only** if exact current-security/share basis and period rules can be proven.

Do not broaden business-direction fields.

Required for deterministic PER/PBR:

- current R9 price;
- exact EPS or BVPS denominator;
- compatible periods;
- same traded-security/share basis;
- currency/unit;
- denominator lineage.

If four-quarter TTM construction is required:
- all four occurrences must be explicit and compatible.

No missing quarter synthesis.

## 13.3 OpenDART official denominator derivation

Similarly audit exact standard per-share/book concepts from the already authorized OpenDART documents.

Do not use fuzzy account names.

Require:
- exact concept/statement;
- current-security/share basis;
- currency/unit;
- period;
- shares/BVPS/EPS lineage as applicable.

If unavailable:
metric remains unavailable.

## 13.4 Historical distribution

Historical valuation distributions may be reused as **versioned historical reference**, not current data, when:

- same traded security;
- same metric definition;
- same currency/security basis;
- exact version/hash;
- current metric is fresh and compatible.

Historical cache may not supply the current multiple.

---

# 14. Fresh valuation typed states

For each metric:

- `QUALIFIED`
- `NOT_MEANINGFUL`
- `UNAVAILABLE`

`NOT_MEANINGFUL` covers non-positive denominator conditions where a normal positive multiple is not economically meaningful.

Every metric stores:

- current R9 numerator price;
- denominator/value source;
- denominator period/horizon;
- publication/as-of;
- currentness;
- method:
  - provider native;
  - deterministic;
- security/share basis;
- source hashes;
- display eligibility;
- New Buyer/entry-use eligibility;
- `overall_direction_use = false`.

No value without ownership.

---

# 15. Valuation offline qualification matrix

Build archetype fixtures proving:

1. qualified native PER/PBR;
2. qualified deterministic PER/PBR;
3. fPER with exact horizon/currentness;
4. fPER missing horizon → unavailable;
5. negative EPS → N/M;
6. zero/negative book denominator → N/M/unavailable per existing policy;
7. ADR/issuer bridge → security metric unavailable;
8. wrong currency → unavailable;
9. wrong share class → unavailable;
10. old cached current metric → denied;
11. historical percentile compatible → display;
12. historical percentile incompatible → omit/unavailable.

Then bind to detailed Valuation rendering.

---

# 16. Detailed stock section-owner closure

REV8 reports that complete state/warning/checkpoint/technical selection is not proven.

Close **owner or explicit omission** for every allowed section.

A detailed message does not require every optional section to be populated.

It requires every section to have a deterministic owner/visibility decision.

For each section produce:

- owner;
- input contract;
- visibility rule;
- exact omitted reason if hidden;
- row source bindings;
- acceptance hash.

---

# 17. Section owner matrix

Required sections:

## Judgment block — mandatory
Owner:
accepted Core/A/B.

## Reevaluation — optional
Owner:
accepted structured reevaluation conditions / future checkpoints.

If none:
omit.

## Thesis/risk/expectation — optional rows
Owner:
versioned thesis/config + accepted deterministic state.

If a row lacks an owner:
omit that row.

Do not infer in renderer.

## Core judgment — mandatory
Owner:
accepted decision + decisive claims.

## Business/earnings — optional
Owner:
fresh business facts/claims.

## Existing warnings — optional
Owner:
current versioned warning config / explicit current typed warning.

No old rendered prose.

## Key monitoring — optional
Owner:
versioned monitored checkpoints + accepted structured future checkpoints.

## Price structure — current price mandatory, other rows optional
Owner:
fresh technical context.

Support/resistance/Bollinger rows render only when qualified.

## Flow/positioning — optional but explicit
Owner:
fresh source role.

If product format requires a visible block and no source exists:
render `자료 부족`.
Do not invent.

## Valuation — section mandatory
Owner:
CurrentValuationView.

Each metric independently renders:
- value;
- N/M;
- 판단 자료 부족.

Do not render separate:
- registered price rules;
- data caution;
- next checks;
- unresolved/unknown.

Those remain internal.

---

# 18. Detailed NORMAL and UNKNOWN_LIMIT full-plan proof

Build two full plans with all section visibility decisions:

- Evidence-based NORMAL
- UNKNOWN_LIMIT

For each:
- accepted plan hash;
- all numeric registry bindings;
- all claim/source bindings;
- pure renderer;
- actual production sender payload builder;
- isolated final capture sink.

Require exact final bytes.

No post-hoc append.

No compact renderer replacement.

---

# 19. P1-1 — aggregate all22 whole-source + Market2 proof

After P1-2/3/4 close offline, build a complete synthetic full cohort using the heterogeneous archetype fixtures.

Required:

- exact US14 population;
- exact KR8 population;
- all stock final states valid;
- fresh Market US component;
- fresh Market KR component;
- fresh macro component;
- KOSPI200 night component;
- valuation views;
- quality states;
- optional denials;
- source-time domains;
- authority graph.

Create an offline FullSourceRunSeed and full packets.

No old mutable packet.

---

# 20. Whole-source replay twice

Replay full synthetic composition twice.

Require exact equality for:

- 22 stock packets;
- US Market component;
- KR Market component;
- macro;
- night;
- quality views;
- valuation views;
- US whole-source packet;
- KR whole-source packet;
- combined packet;
- authority graph.

Set offline:

`whole_source_replay_twice = PASS`

only then.

---

# 21. Market2 offline input/display proof

Feed the complete offline whole-source packets through the exact existing Market adapter.

Require:

- US Market input readiness `1/1`;
- KR Market input readiness `1/1`;
- selected display-plan generation;
- numeric/source binding;
- final Market sender-boundary fixture.

US display:
- major indices/proxies;
- macro;
- market judgment;
- sector TOP3/BOTTOM3;
- KOSPI200 D/W/M.

KR display:
- market judgment;
- KOSPI/KOSDAQ sector TOP3/BOTTOM3;
- USD/KRW.

No all-numeric dump.

---

# 22. Full all22 Core/A/B offline readiness

Using the same offline whole-source cohort:

Require:

- Core `22/22`;
- A `22/22`;
- B `22/22`.

Must include at least:
- evidence-based;
- UNKNOWN_LIMIT;
- quality denied;
- issuer bridge;
- persisted event;
- valuation available;
- valuation N/M;
- valuation unavailable.

No synthetic path may skip the actual input/materializer/validator contracts.

---

# 23. Exact24 offline sender-boundary proof

Before provider calls, build a synthetic-but-contract-real exact 24 payload set:

- Market US 1;
- Market KR 1;
- US14;
- KR8.

Use:
- exact current renderer;
- exact payload builder;
- exact chunk/preparation boundary;
- isolated send sink.

This is not a live content proof.

It is the final end-to-end contract proof.

Require:
- 24/24 payloads;
- detailed stock format;
- UNKNOWN_LIMIT stock format;
- Valuation section every stock;
- removed standalone stock sections absent;
- selected Market format;
- no refs/hashes/debug leakage.

---

# 24. Phase-A final gate

Before any provider call require all:

- current-only UNKNOWN_LIMIT positive path PASS;
- heterogeneous archetypes PASS;
- valuation capability connection PASS;
- valuation qualified/N-M/unavailable matrix PASS;
- detailed section owner matrix PASS;
- detailed NORMAL PASS;
- detailed UNKNOWN_LIMIT PASS;
- aggregate all22 full-source PASS;
- whole-source replay twice PASS;
- Market2 PASS;
- Core/A/B 22/22 PASS;
- exact24 offline sender-boundary PASS;
- all provider budgets finite.

Then issue:

`R2B_R9_REV9_PREFLIGHT_CONTRACTS_PASS`

and:

`dispatch_allowed = true`.

If any remain open:

`R2B_R9_REV9_PREFLIGHT_CONTRACT_GAP`

Provider/model calls = 0.

---

# 25. Final provider plan after Phase-A PASS

Regenerate the exact live plan from current code.

Include all fresh required external reads:

- stock chart/price;
- US Market;
- KR Market;
- FRED;
- EIA;
- ECOS;
- KOSPI200 night;
- SEC;
- OpenDART;
- event/news if current role inventory requires;
- Finnhub valuation/estimate reads if qualified by Section 13 and current product configuration.

For each:
- exact subject/universe;
- endpoint/source family;
- logical requests;
- page/document caps;
- timeout;
- retries;
- theoretical max attempts;
- mandatory/optional roles.

Alpha Vantage:
`planned = 0`
`actual = 0`

Massive/mock/undeclared fallback:
`0`

No request outside plan.

---

# 26. Fresh live/ad-hoc generation

Only after `dispatch_allowed=true`.

Use scheduled-window or ad-hoc requalification mode exactly as current contract permits.

Recompute actual target sessions at execution time.

No old current packet.

No old current metric.

No old AI output.

---

# 27. Full fresh all22 acquisition

Freshly acquire all mutable roles for:

US14:
CORZ, CPNG, CRCL, GOOGL, HUT, IBM, MU, RXRX, SKHY, SNDK, TSLA, TSM, WRD, WULF

KR8:
000660, 003690, 005490, 005930, 010120, 012450, 047810, 086280

No complete-control exemption.

Fresh:
- price/OHLCV;
- technical;
- financial/business;
- quality;
- valuation;
- event when configured;
- flow/positioning;
- issuer bridge if needed.

---

# 28. Fresh market/macro/night

Freshly acquire:

## US
- selected major/style/index proxy roles;
- sector universe;
- breadth/participation where owned;
- macro;
- KOSPI200 night.

## KR
- KOSPI/KOSDAQ;
- venue sectors;
- breadth;
- investor flows where owned;
- USD/KRW.

Macro:
fresh retrieval + source-owned observation period/currentness.

Night:
KOSPI200 only.

---

# 29. Fresh source closure

Require:

- stocks `22/22`;
- Market source `2/2`;
- KOSPI200 current contract PASS;
- mandatory macro currentness explicit;
- quality views all22;
- valuation views all22.

Individual optional valuation metrics may remain unavailable.

Create new:

- FullSourceRunSeed;
- US packet;
- KR packet;
- combined packet;
- authority graph.

---

# 30. Live network-free replay twice

Freeze live raw/source corpus.

Disable provider access.

Replay twice.

Require exact semantic equality.

Only then:

`NETWORK_FREE_SOURCE_ADAPTER_PREQUALIFIED = true`

and, if live role coverage also passed:

`COMPLETE_SOURCE_ADAPTER_QUALIFIED = true`.

Do not inherit qualification.

---

# 31. Fresh AI

Run no old outputs.

Fresh:

- Market 2/2;
- Core 22/22;
- A 22/22;
- B 22/22.

No target fitting.

No source refresh after inference begins.

No semantic/schema retry.

Only current accepted transient model transport retry policy, if any.

---

# 32. Final Market messages

## US

`미국 시장 · YYYY-MM-DD`

Display:
- SPY/QQQ/etc selected major rows with change + %;
- compact current/latest-published macro;
- market judgment + confidence;
- sector TOP3/BOTTOM3 or 자료 부족;
- KOSPI200 day/week/month.

No KOSDAQ150.

## KR

`한국 시장 · YYYY-MM-DD`

Display:
- KOSPI/KOSDAQ market judgment;
- breadth/flow where owned;
- KOSPI TOP3/BOTTOM3;
- KOSDAQ TOP3/BOTTOM3;
- USD/KRW.

---

# 33. Final detailed stock messages

Stable user-facing order:

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

Valuation section always appears.

Metric rows:
- qualified value;
- N/M;
- 판단 자료 부족.

No unsupported number.

---

# 34. Exact final-boundary capture

Capture exact sender payload bytes with delivery disabled.

Required:

- MARKET_US
- MARKET_KR
- 22 stock messages
- ALL_MESSAGES.md

Total:
`24/24`

No post-hoc reconstruction.

---

# 35. Human-review bundle

On full PASS create:

`r2b-r9-rev9-fresh-24-message-human-review.zip`

Include:

- exact 24 payloads;
- message hashes;
- Market display audit;
- detailed plan audit;
- final-boundary traces;
- provider planned/theoretical/actual ledger;
- macro currentness;
- KOSPI200 D/W/M;
- all22 source summary;
- financial comparison matrix;
- quality matrix;
- valuation matrix;
- valuation capability/source receipts;
- 005930/047810/SKHY/SNDK traces;
- AI ledger;
- validation.

---

# 36. Production side effects

Hard zero:

- Telegram;
- recipient intent;
- production DB decisions/warnings;
- scheduler mutation;
- notifications mutation;
- broker;
- deploy;
- main merge;
- push;
- restart.

---

# 37. Success terminal

Use only:

`R2B_R9_REV9_FULL_FRESH_ALL_SOURCE_24_MESSAGE_PASS_READY_FOR_HUMAN_REVIEW`

Require:

1. current-only UNKNOWN_LIMIT contract closed;
2. all heterogeneous archetypes closed;
3. qualified/N-M/unavailable valuation paths closed;
4. detailed section-owner contract closed;
5. all22 offline full-source replay twice PASS;
6. Market2 offline PASS;
7. Core/A/B offline 22/22;
8. exact24 offline sender proof PASS;
9. final finite provider plan issued;
10. all mandatory mutable live roles freshly acquired;
11. live stock 22/22;
12. live Market 2/2;
13. macro/USDKRW currentness PASS;
14. KOSPI200-only PASS;
15. fresh quality views all22;
16. fresh valuation views all22;
17. R7 direction guard PASS;
18. live replay twice PASS;
19. COMPLETE_SOURCE_ADAPTER_QUALIFIED=true;
20. fresh Market/Core/A/B complete;
21. exact final payloads 24/24;
22. message contracts PASS;
23. Alpha/fallback 0;
24. production side effects 0;
25. human-review ZIP created.

---

# 38. Honest stop terminals

## Offline contracts remain open

`R2B_R9_REV9_PREFLIGHT_CONTRACT_GAP`

No provider/model calls.

## Valuation source owner cannot qualify

If Valuation section can still render unavailable safely:
- do not stop the whole task solely because an optional metric is unavailable.

Stop only if the valuation **contract itself** cannot produce a typed qualified/N-M/unavailable result.

Terminal:
`R2B_R9_REV9_VALUATION_CONTRACT_GAP`

## Provider plan unbounded

`R2B_R9_REV9_PROVIDER_BUDGET_GAP`

No affected provider calls.

## Fresh source partial

`R2B_R9_REV9_FULL_FRESH_SOURCE_PARTIAL`

No AI.

## Financial comparison partial

If affected stock can validly become UNKNOWN_LIMIT and packet is otherwise complete:
- UNKNOWN_LIMIT is allowed.

Do not treat all missing comparison as whole-run failure.

If source acquisition/lineage itself is incomplete:
`R2B_R9_REV9_FRESH_FINANCIAL_SOURCE_PARTIAL`.

## Market/macro/FX partial

Use exact role terminal.
No stale fallback.

## Adapter qualification gap

`R2B_R9_REV9_LIVE_ADAPTER_REQUALIFICATION_GAP`

No scheduler authorization.

## Model/render failure

Use exact stage terminal.
Preserve live source corpus.
Do not recollect because downstream failed.

---

# 39. Validation

## Current-only / UNKNOWN_LIMIT
- explicit no-comparison owner state;
- owner-error negative;
- source failure negative;
- context-only current fact;
- zero direction;
- detailed UNKNOWN_LIMIT sender capture.

## Heterogeneous archetypes
- US domestic;
- FPI;
- KR ordinary;
- insurance;
- quality denied;
- bridge;
- persisted event;
- fresh event;
- UNKNOWN_LIMIT.

## Valuation
- Finnhub native current metrics where qualified;
- official deterministic denominator paths;
- fPER horizon/currentness;
- N/M;
- unavailable;
- security basis;
- historical distribution compatibility;
- no cross-security transfer;
- no Overall direction from valuation.

## Whole source
- all22 exact;
- Market2;
- macro;
- night;
- source time;
- replay twice.

## Detailed renderer
- section owner matrix;
- NORMAL;
- UNKNOWN_LIMIT;
- all numeric/source bindings;
- no post-hoc append;
- exact sender bytes;
- removed sections absent.

## Market
- selected display;
- sectors;
- KOSPI200 only;
- macro currentness;
- USDKRW.

## Repository
- focused;
- full pytest;
- Ruff;
- diff;
- Investment Knowledge;
- Chart Knowledge;
- secret scan;
- skip/xfail parity.

---

# 40. Required result bundle

Return immutable ZIP + `.sha256`.

At minimum:

- REPORT.md
- summary.json
- REV8 result identity/SHA
- repository identities
- changed-file inventory

## Offline closure
- quality applicability contract;
- current-only UNKNOWN_LIMIT proof;
- archetype qualification matrix;
- bridge descriptor proof;
- persisted/fresh event proofs;
- valuation capability audit update;
- valuation owner bindings;
- qualified/N-M/unavailable matrix;
- section owner matrix;
- detailed NORMAL/UNKNOWN_LIMIT plans;
- all22 full-source replay;
- Market2 proof;
- Core/A/B readiness;
- exact24 offline sender proof;
- final provider plan.

## Live fresh
- request receipts;
- raw/normalized hashes;
- stock 22;
- Market/macro/night;
- financial/business;
- quality;
- valuation;
- bridges/events;
- full-source graph;
- replay;
- adapter qualification.

## AI/render
- fresh Market/Core/A/B;
- accepted detailed plans;
- exact payloads/hashes.

## Human review
- `r2b-r9-rev9-fresh-24-message-human-review.zip`
- SHA.

## Safety
- planned/theoretical/actual provider counters;
- Alpha 0;
- fallback 0;
- production side effects 0;
- validation;
- secret scan;
- manifest.

---

# 41. After full PASS — generate only

Generate but do not execute:

`Post-R9-REV9 Unified Scheduler Cutover`

Require human approval of the exact fresh 24 messages.

No scheduler activation inside REV9.

---

# 42. Final principle

A lack of comparative financial evidence is not automatically a source failure.

If the current source is valid but directional comparison is genuinely unavailable, the system
must be able to complete the stock packet and say UNKNOWN_LIMIT without inventing quality,
direction or comparison.

Likewise, Valuation must distinguish:
- qualified;
- not meaningful;
- unavailable.

It does not need to fabricate a number to satisfy the UI.

Only after these semantics and all heterogeneous source archetypes survive the complete
all22 + Market2 + sender-boundary offline chain may the system spend provider/model calls on the
full fresh proof.
