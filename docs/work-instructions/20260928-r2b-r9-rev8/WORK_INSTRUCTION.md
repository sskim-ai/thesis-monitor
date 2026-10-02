# Thesis Monitor — R2B-R9-REV8
## Final offline integration closure → full fresh all-source recollection → post-R7 live requalification → fresh 24-message proof
### Wire macro/night + all22 fresh stock/quality/valuation + issuer bridge + Market/Core/A/B + detailed sender-boundary rendering

**REV8 supersedes all prior unexecuted R2B-R9 instructions. Execute only REV8.**

REV7 correctly stopped before network. It implemented and tested the component owners, but did not
yet close the end-to-end integration required to authorize a live full-fresh proof.

The remaining work is no longer source-policy discovery. It is integration closure.

REV8 must close exactly these remaining P1s offline first:

1. fresh macro/night raw outputs → current Market/full-source composition/replay;
2. fresh issuer bridge descriptor + current-security valuation view;
3. exact all22 integration across fresh technical → financial/business → quality → valuation → stock packet → whole source;
4. fresh source packet → existing Market/Core/A/B input adapters;
5. detailed stock renderer for both NORMAL and UNKNOWN_LIMIT decisions with complete owned section coverage;
6. accepted detailed plan → actual final sender-boundary capture route.

Only after all six are proven offline and the final finite provider plan is sealed may REV8 call providers.

Then REV8 must perform the full fresh acquisition and fresh 24-message proof in the same task.

---

# 0. Newest SoT

Adopt the REV7 partial-offline result as the newest implementation SoT.

Result ZIP SHA-256:

`fcec11f5cbeb93d0b3c35e19cbddaee7fec593c9c782480ea04fecadd4c42c9c`

Sidecar:
exact match.

Bundle:

- ZIP members: `68`
- bundle manifest internally verified by the result
- result terminal:
  `R2B_R9_REV7_PREFLIGHT_CONTRACT_GAP`

Repository:

- branch:
  `codex/r2b-r9-rev7-fresh-detailed-closure`
- base:
  `30efc244288d42c13a9b80aa5c4e70c386be26a3`
- instruction:
  `bf82dc5fba0362b43bc35a9261e2b01e414b8505`
- implementation:
  `c75222d2b75252e6ab44bd34a71c4f83dc6e59bf`
- final local:
  `3b8ebcfbe07b91e510013cd07236404fc04e71f0`
- accepted R7 runtime:
  `174af2b0a0cef373c85a9a27fe22604839c8acf9`
- operating/main:
  `b610e6de0a8c33d199961e821ff1b130e1fa9ad4`

REV7 validation:

- focused:
  `1103 PASS`
- full:
  `6298 PASS / 63 unchanged skips / 0 failures`
- Ruff / diff / Investment Knowledge / Chart Knowledge:
  PASS
- provider calls:
  `0`
- model calls:
  `0`
- production side effects:
  `0`

Do not discard the REV7 implementation.

Continue from its implementation/final checkpoint.

---

# 1. Preserve all already-closed contracts

Do not reopen:

- KOSPI200-only night product scope;
- Market internal fact view versus selected user display view;
- source-owned macro observation period handling;
- R7 absolute-current financial direction guard;
- existing bounded SEC owner;
- existing bounded OpenDART owner;
- current source-use rules;
- current quality semantics;
- current valuation security-basis restrictions;
- current message content requirements.

No threshold/validator relaxation.

---

# 2. REV7 open ledger — exact scope

REV7 owner map:

## Fresh stock

Implemented:

`mock/raw financial → selected comparison → quality → explicit-unavailable valuation → stock`

Open:

- all22 integration;
- issuer bridge.

## Whole source

Implemented:

- new fresh seed type;
- rejection of legacy publication carry-in.

Open:

- fresh macro/night → whole-source composition/replay.

## Detailed renderer

Implemented:

- normal decision fixture;
- canonical numeric registry;
- acceptance hashes;
- post-hoc mutation rejection.

Open:

- UNKNOWN_LIMIT;
- complete section owners;
- actual 24 sender-boundary capture;
- connection to fresh Market/Core/A/B.

These exact gaps own REV8.

---

# 3. No provider calls until final offline closure

REV8 Phase A remains network-free.

Required:

- provider calls = 0;
- model calls = 0.

Do not “test the controller” using live calls before the full integration is closed.

Candidate finite provider envelope from REV7/REV6 remains diagnostic only.

Final provider plan authority must be reissued after Phase A PASS.

---

# 4. Fresh macro/night → whole-source composition

REV6 already fixed source-time semantics and KOSPI200-only scope.

REV8 must now wire those fresh outputs into:

`unified_full_source_cohort.compose_full_source`

or the exact current equivalent.

## 4.1 Fresh macro component

Define an explicit typed R9 fresh macro component containing:

- run/generation ID;
- retrieved-at;
- query-as-of;
- source-owned observation period/date;
- publication date where available;
- freshness/currentness state;
- canonical macro fact IDs;
- numeric-registry entries;
- internal-use eligibility;
- display eligibility;
- source receipts/hashes.

No parent macro rows.

## 4.2 Fresh night component

Typed component must include only configured:

`KOSPI200`

and current run:

- daily;
- weekly;
- monthly;
- included/expected session metadata;
- source receipts/hashes;
- availability states;
- numeric registry.

No KOSDAQ150.

No old D/W/M summary.

## 4.3 Full-source binding

US/KR full-source composition must bind exact fresh macro/night components.

The whole-source packet must not accept:
- persisted old macro component;
- old night summary;
- old publication packet.

## 4.4 Replay

Create deterministic fixture tests proving:

fresh raw macro/night
→ normalized component
→ full source
→ Market input
→ display plan

replays byte/semantic-hash identical.

Tamper/wrong-run/wrong-observation-period negatives required.

---

# 5. Current issuer bridge descriptor

REV7 blocked bridge closure rather than transferring valuation rights. Preserve that safety.

Implement a typed fresh bridge descriptor only when needed.

Required fields:

- current target security ID/ticker;
- target traded-security class;
- current issuer identity;
- source ticker/security/issuer;
- same-legal-issuer proof;
- source acquisition run ID;
- source financial projection hash;
- exact business facts allowed to bridge;
- exact denied uses;
- current eligibility;
- descriptor hash.

Allowed:

- issuer-level business evidence if current generic policy permits it.

Forbidden by default:

- security per-share denominator transfer;
- price transfer;
- technical transfer;
- PER/PBR/fPER transfer;
- current-security valuation authority.

For SKHY or any future case, the bridge is generic and current-generation.

No ticker branch.

---

# 6. Bridge + current-security valuation view

For a bridged stock, always create a current-security valuation view.

If no qualified security-specific denominator exists:

- CurrentValuationView exists;
- PER/PBR/fPER status may be UNAVAILABLE;
- exact reason:
  security-specific denominator/basis unavailable;
- current traded-security price remains bound;
- valuation section still renders with unavailable metrics.

Do not use issuer bridge facts as security per-share denominators.

This closes the previously open:
`FRESH_ISSUER_BRIDGE_DESCRIPTOR_AND_SECURITY_VALUATION_VIEW_NOT_CLOSED`.

---

# 7. Valuation-capable owner audit before accepting universal unavailability

REV7's `current_fresh_valuation.py` deliberately denies PER/PBR/fPER because the bounded
revenue/operating-income/net-income financial collector owns no EPS/book/forward denominator.

Before keeping every metric unavailable, audit the current repository for **already authorized**
valuation-capable source owners/roles.

At minimum inspect current paths for:

- provider-native PER;
- provider-native PBR;
- BVPS/book-value-per-share;
- EPS / TTM EPS;
- forward EPS / consensus estimates;
- existing `ValuationSnapshotService`;
- existing quote/stock information roles;
- existing valuation snapshot/cache roles;
- any current stock wire role explicitly intended for valuation.

Produce:

`existing-valuation-capability-audit.json`

For each candidate:

- current configured/authorized?
- provider/source family;
- fresh R9 retrieval/read possible?
- current-security identity?
- share basis?
- currency?
- denominator period/horizon?
- source-time/currentness?
- bounded request plan?
- allowed metric(s)?
- directional-use false?
- usable in REV8 fresh proof?

Rules:

- do not add a new provider;
- do not use old cached multiple as current proof without a new latest/currentness read;
- do not cross security classes;
- do not weaken basis rules.

If an existing authorized owner can provide a fresh qualified metric:
wire it into CurrentValuationView.

If not:
metric remains `판단 자료 부족`.

Valuation section remains mandatory, but individual metrics are optional/unavailable.

---

# 8. All22 fresh stock integration

Build one offline integration path covering all22 from plan to final stock packet.

Required path:

`fresh technical input`
→ `fresh financial/business acquisition result`
→ `fresh comparison/event facts`
→ `fresh quality`
→ `fresh valuation`
→ `fresh issuer bridge if any`
→ `fresh evidence packet`
→ `fresh stock packet`
→ `source graph`

Run it for all 22 using deterministic offline fixtures that exercise each owner archetype.

No real provider data required in Phase A; fixtures must preserve the real schemas/contracts.

Required archetype coverage:

- ordinary US domestic SEC;
- FPI/ADR;
- KR OpenDART;
- insurance revenue semantic;
- quality denied/caution;
- quality clean;
- direct current-security valuation available;
- valuation unavailable;
- issuer bridge;
- persisted event eligible;
- no direction / UNKNOWN_LIMIT.

Then produce:

`offline-all22-integration-matrix.json`

with 22 rows and no subset execution.

All rows must reach a valid final state:
- evidence-based stock packet; or
- explicit policy-valid UNKNOWN_LIMIT source state;
not implementation missing.

---

# 9. Full-source all22 integration

Using the 22 offline integrated stock fixtures plus fresh macro/night/Market fixtures:

create a full R9 full-source packet end to end.

Require:

- US14 exact;
- KR8 exact;
- Market US component;
- Market KR component;
- macro;
- KOSPI200 night;
- authority graph;
- source-time domains;
- optional denials;
- no old source carry-in.

Replay twice.

This is an offline integration proof, not a live-data claim.

---

# 10. Fresh source → Market/Core/A/B adapters

REV7 says fresh Market/Core/A/B adapter is not wired.

Close it now.

## 10.1 Market

Fresh full-source Market component
→ existing accepted Market input contract
→ selected display plan.

No DB/cache/live read during replay.

## 10.2 Core

Fresh stock packet/evidence
→ current Core input.

Preserve:
- R7 direction guard;
- quality;
- UNKNOWN_LIMIT;
- source-use;
- no technical price leak where prohibited.

## 10.3 A / New Buyer

Fresh Core output + fresh valuation/security-basis/current-price/technical inputs
→ existing A input.

No ref-less quality effects.

No old valuation.

## 10.4 B / Holder

Fresh Core + A + source/evidence
→ existing B input.

No valuation-only holder action.

## 10.5 Offline stage proof

Use synthetic accepted model outputs solely to prove deterministic input/materializer/validator wiring.

Do not call models in Phase A.

Require 22/22 schema/input readiness for:
- Core;
- A;
- B;
plus Market 2/2.

---

# 11. Detailed renderer — support NORMAL and UNKNOWN_LIMIT as typed union

REV7 detailed plan accepts only normal calibration decision shape.

Implement a typed decision union.

Recommended conceptual forms:

- `DetailedEvidenceBasedDecisionPlan`
- `DetailedUnknownLimitDecisionPlan`

or repository-equivalent discriminated union.

Do not coerce UNKNOWN_LIMIT into BUY:SELL.

## 11.1 Evidence-based

Preserve:
- Overall;
- balance;
- confidence;
- maturity;
- New Buyer;
- Holder.

## 11.2 UNKNOWN_LIMIT

Render:

```text
🧠 AI 분석 판단: OBSERVE
판단 균형: 판단 자료 부족
판단 확신도: 판단 자료 부족
신규 매수자: OBSERVE
보유자: OBSERVE
```

Core judgment explains that directional business evidence is insufficient.

No ratio.

No direction confidence.

Valuation/price/technical context may still render if source-qualified, but cannot turn into a directional investment recommendation.

---

# 12. Complete detailed section-owner coverage

REV7 currently guarantees judgment/core/current-price/flow unavailable/valuation unavailable, while other sections depend on caller selections.

Close explicit owners for every allowed final section.

## 12.1 Reevaluation

Owner:
accepted structured reevaluation claims/checkpoints.

If absent:
section omitted.

## 12.2 Thesis state

Owner:
current accepted thesis-state materializer/versioned thesis config + accepted decision state.

Rows:
- investment thesis state;
- structural risk;
- market expectation.

Do not infer in renderer.

If a state has no current owner:
omit that row rather than invent.

## 12.3 Business/earnings

Owner:
accepted directional/context business claims.

Model prose must bind exact claims.

## 12.4 Existing warnings

Owner:
current versioned warning config and/or typed current warnings explicitly approved for user display.

No old rendered prose.

## 12.5 Monitoring

Owner:
current versioned monitored checkpoints and accepted structured future-checkpoint claims.

Prefer 2–4.

## 12.6 Price

Owner:
fresh technical fact catalog/numeric registry.

Possible rows:
- current price;
- support;
- resistance;
- weekly Bollinger;
- monthly provisional Bollinger.

Only current generation.

## 12.7 Flow/positioning

Owner:
fresh stock flow/volume source.

If no qualified owner:
typed explicit unavailable row.

## 12.8 Valuation

Owner:
fresh CurrentValuationView.

Section mandatory.

Every metric row is typed:
- qualified;
- N/M;
- unavailable.

Historical valuation rows only when current compatible historical owner exists.

---

# 13. Detailed plan must own prose and numbers before render

No post-hoc append.

Every final row must exist in accepted plan.

For each row record:

- section;
- row ID;
- owner type;
- source fact IDs;
- source hashes;
- claim refs if model-authored;
- numeric registry keys;
- formatting contract;
- visibility;
- row acceptance hash.

The entire plan receives:
`acceptance_sha256`.

`detailed_render()` must be a pure rendering of the accepted plan.

Rebuilding the plan from bound inputs must reproduce exact equality.

---

# 14. Actual accepted detailed capture route

Wire:

fresh packet
→ accepted Market/Core/A/B
→ accepted detailed plan
→ existing payload/message object
→ real current production sender payload builder
→ final isolated capture sink.

Do not stop at `detailed_render().text`.

Prove exact final payload bytes.

For stock capture:

- no later compact renderer replaces detailed text;
- no Telegram chunk preparation drops sections;
- no downstream wrapper injects old compact content.

Add:

`detailed-final-boundary-trace.json`

with:

- ticker;
- detailed plan hash;
- render hash;
- payload builder hash;
- final sender bytes SHA;
- production send count 0.

---

# 15. Detailed renderer final format

Final stock order:

1. optional actual pilot label;
2. company/ticker;
3. AI judgment / BUY:SELL or UNKNOWN_LIMIT / confidence / maturity / New Buyer / Holder;
4. reevaluation conditions;
5. thesis state / structural risk / market expectations;
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

Those states remain internal.

---

# 16. Market final-boundary route

Likewise prove selected Market display plans survive the actual sender payload path.

US final blocks:

- major indices/proxies;
- macro;
- market judgment;
- sector top/bottom;
- KOSPI200 D/W/M.

KR final blocks:

- market judgment;
- KOSPI/KOSDAQ sectors;
- USDKRW.

No all-numeric dump after selected rendering.

---

# 17. Phase-A complete gate

Before any provider call require:

- KOSPI200-only PASS;
- Market selected display PASS;
- macro source-time PASS;
- fresh all22 controller complete;
- macro/night → whole-source PASS;
- current issuer bridge descriptor PASS;
- current valuation view PASS;
- valuation capability audit complete;
- offline all22 integration 22/22;
- full-source replay twice PASS;
- Market 2/2 offline input readiness;
- Core/A/B 22/22 offline input readiness;
- detailed NORMAL PASS;
- detailed UNKNOWN_LIMIT PASS;
- complete section-owner coverage PASS;
- actual sender-boundary detailed capture fixture PASS;
- final finite provider plan complete.

Then issue:

`R2B_R9_REV8_PREFLIGHT_CONTRACTS_PASS`

and:

`dispatch_allowed = true`.

If any item remains open:

`R2B_R9_REV8_PREFLIGHT_CONTRACT_GAP`

Provider/model calls remain 0.

---

# 18. Final provider plan

After Phase-A PASS regenerate/freeze exact current plan.

Preserve bounded candidate envelopes only where they remain correct.

For every provider/source role record:

- exact requests;
- subject/universe;
- pages/documents;
- timeout;
- retry;
- theoretical max;
- role mapping;
- mandatory/optional.

Include any existing authorized fresh valuation source reads discovered in Section 7.

Alpha Vantage:
`0`

Massive/mock/undeclared fallback:
`0`

No request outside plan.

---

# 19. Fresh live/ad-hoc execution

After dispatch_allowed=true.

Use scheduled or ad-hoc live mode exactly as current config/contract permits.

No fiction about scheduled execution.

Recalculate target sessions at actual run time.

No old packet.

---

# 20. Full fresh all22 acquisition

Freshly execute all mutable roles for:

US14:
CORZ, CPNG, CRCL, GOOGL, HUT, IBM, MU, RXRX, SKHY, SNDK, TSLA, TSM, WRD, WULF

KR8:
000660, 003690, 005490, 005930, 010120, 012450, 047810, 086280

No complete-control exemptions.

Current-generation only:

- price;
- chart/technical;
- financial/business;
- quality;
- valuation;
- event where configured;
- flow/positioning;
- issuer bridge if needed.

---

# 21. Full fresh market/macro/night acquisition

US:
- selected major/style/index proxy roles;
- sector universe;
- breadth when owned;
- fresh macro;
- KOSPI200 night.

KR:
- KOSPI/KOSDAQ;
- venue sectors;
- breadth;
- investor flows where owned;
- USDKRW source period.

Macro:
fresh retrieval + source-owned observation period/currentness.

Night:
KOSPI200 only.

---

# 22. Current financial direction guard

Preserve R7:

current absolute amount alone is context, not direction.

Fresh controls:

- 005930;
- 047810.

If current/prior comparison is qualified:
use it.

Otherwise:
no forced direction.

Zero direction:
UNKNOWN_LIMIT.

---

# 23. Fresh source closure and replay

Require live:

- stocks 22/22;
- Market 2/2;
- mandatory macro currentness;
- KOSPI200 night;
- current quality views;
- current valuation views.

Generate new:

- run seed;
- US/KR/combined packets;
- authority graph.

Freeze raw/source corpus.

Replay twice network-free.

Only then:

`COMPLETE_SOURCE_ADAPTER_QUALIFIED = true`.

---

# 24. Fresh AI

No old AI output reuse.

Run fresh:

- Market 2/2;
- Core 22/22;
- A 22/22;
- B 22/22.

No result-driven source refresh or policy changes.

No independent-review target fitting.

---

# 25. Exact 24 final payloads

Use actual final sender boundary with delivery disabled.

Required:

- US Market 1
- KR Market 1
- US stocks 14
- KR stocks 8
- total 24

No post-hoc reconstruction.

---

# 26. Human-facing Market contract

## US

`미국 시장 · YYYY-MM-DD`

- SPY/QQQ/etc selected major roles with change + %;
- compact macro values;
- market judgment + confidence;
- sector TOP3/BOTTOM3 or 자료 부족;
- KOSPI200 D/W/M.

## KR

`한국 시장 · YYYY-MM-DD`

- market judgment: KOSPI/KOSDAQ + breadth/flow if qualified;
- KOSPI TOP3/BOTTOM3;
- KOSDAQ TOP3/BOTTOM3;
- USD/KRW.

No stale values.

---

# 27. Human-facing stock contract

Established detailed format:

- company/ticker;
- AI decision / balance / confidence / maturity / New Buyer / Holder;
- reevaluation;
- thesis/risk/expectation;
- core judgment;
- business/earnings;
- existing warnings;
- key monitoring;
- current price structure;
- flow/positioning;
- Valuation.

Valuation section mandatory.

Do not render standalone:
- registered price rules;
- data caution;
- next checks;
- unresolved/unknown.

No internal refs/enums/hashes.

---

# 28. Human-review bundle

On full PASS create:

`r2b-r9-rev8-fresh-24-message-human-review.zip`

Include:

- exact 24 payloads;
- hashes;
- Market display-plan audit;
- detailed stock-plan audit;
- final-boundary traces;
- provider plan/actual ledger;
- macro currentness;
- night D/W/M;
- 22 stock source summary;
- comparison/quality/valuation matrices;
- special subject traces;
- AI ledger;
- validation.

---

# 29. Production side effects

Hard zero:

- Telegram sends;
- recipient intent;
- production DB decision/warning writes;
- scheduler mutation;
- notifications mutation;
- broker;
- deploy;
- main merge;
- push;
- restart.

---

# 30. Success terminal

Use only:

`R2B_R9_REV8_FULL_FRESH_ALL_SOURCE_24_MESSAGE_PASS_READY_FOR_HUMAN_REVIEW`

Require:

1. all REV8 Phase-A contracts PASS;
2. dispatch_allowed=true;
3. final provider plan finite;
4. all mandatory mutable roles fresh;
5. stock 22/22;
6. Market 2/2;
7. KOSPI200-only;
8. macro/USDKRW currentness;
9. fresh quality views;
10. fresh valuation views;
11. fresh full-source graph;
12. R7 direction guard;
13. replay twice;
14. adapter qualified;
15. fresh Market/Core/A/B;
16. detailed NORMAL + UNKNOWN_LIMIT final rendering;
17. exact 24 sender-boundary payloads;
18. message contracts PASS;
19. Alpha/fallback 0;
20. production side effects 0;
21. human-review ZIP generated.

---

# 31. Honest stop terminals

## Offline integration still open

`R2B_R9_REV8_PREFLIGHT_CONTRACT_GAP`

No provider/model calls.

## Provider plan incomplete

`R2B_R9_REV8_PROVIDER_BUDGET_GAP`

No affected provider call.

## Fresh source partial

`R2B_R9_REV8_FULL_FRESH_SOURCE_PARTIAL`

No AI.

## Financial comparison partial

`R2B_R9_REV8_FRESH_FINANCIAL_COMPARISON_PARTIAL`

No forced direction.

## Market/macro/FX partial

Use exact source-role terminal.

No stale fallback.

## Adapter qualification gap

`R2B_R9_REV8_LIVE_ADAPTER_REQUALIFICATION_GAP`

No scheduler authorization.

## Model/render failure

Use exact stage terminal.

Preserve fresh source corpus.

Do not recollect because downstream failed.

---

# 32. Validation

## Integration
- fresh controller all22;
- macro/night full-source;
- bridge descriptor;
- current-security valuation;
- valuation capability audit;
- all22 offline matrix;
- full-source replay.

## Detailed renderer
- evidence-based;
- UNKNOWN_LIMIT;
- all section owners;
- numeric/source binding;
- no post-hoc rows;
- actual sender boundary;
- forbidden standalone sections absent.

## Valuation
- provider-native/deterministic ownership;
- PER/PBR/fPER;
- basis/currency/period;
- forward currentness;
- historical compatibility;
- unavailable state;
- no cross-security transfer;
- no Overall direction from valuation.

## Market
- selected display;
- sector ranks;
- KOSPI200 only;
- macro dates;
- USDKRW.

## Source direction
- absolute current non-directional;
- comparative direction;
- UNKNOWN_LIMIT.

## Repository
- focused;
- full pytest;
- Ruff;
- diff;
- Knowledge;
- Chart;
- secret scan;
- skip/xfail parity.

---

# 33. Required result bundle

Return immutable ZIP + `.sha256`.

At minimum:

- REPORT.md
- summary.json
- REV7 identity/SHA
- repository identities
- changed-file inventory

## Phase A
- fresh controller integration map
- macro/night whole-source proof
- issuer bridge descriptor contract
- valuation capability audit
- valuation view binding proof
- offline all22 matrix
- full-source replay
- Market/Core/A/B readiness
- detailed NORMAL/UNKNOWN_LIMIT plan proofs
- section-owner matrix
- final-boundary fixture trace
- final provider plan

## Live fresh
- request receipts;
- raw/normalized source hashes;
- stock 22;
- Market/macro/night;
- financial/business;
- quality;
- valuation;
- bridges;
- full-source graph;
- replay;
- adapter qualification.

## AI/render
- fresh Market/Core/A/B;
- accepted detailed plans;
- exact payloads;
- hashes.

## Human review
- `r2b-r9-rev8-fresh-24-message-human-review.zip`
- SHA.

## Safety
- provider planned/theoretical/actual;
- Alpha/fallback 0;
- production side effects 0;
- validation;
- secret scan;
- manifest.

---

# 34. After full PASS — generate only

Generate, do not execute:

`Post-R9-REV8 Unified Scheduler Cutover`

Only after human approval of the exact 24 messages.

No scheduler activation inside REV8.

---

# 35. Final principle

REV7 has already implemented the pieces.

REV8's job is to connect them into one complete ownership chain before spending provider/model calls.

A source is not “fresh” until it survives:
acquisition → business/quality/valuation → stock/full-source → model input → detailed final payload
without falling back to a prior mutable artifact.

A detailed message is not “accepted” until every rendered row is in a typed, source-bound plan
that survives the actual sender boundary unchanged.
