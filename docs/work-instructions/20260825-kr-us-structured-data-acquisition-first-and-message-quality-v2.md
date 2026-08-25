# thesis-monitor — KR/US Structured Market Data Acquisition First + Message Quality v2
## Supersedes the earlier KR/US Message Quality Bounded Repair

## Metadata

- Workstream: `KR_US_STRUCTURED_DATA_FIRST_QUALITY_V2`
- Instruction version: `2.0`
- Date: `2026-08-25 KST`
- Authoring time context: `2026-08-25 21:16 KST`
- Repository: `sskim-ai/thesis-monitor`
- Task type: `STRUCTURED_DATA_ACQUISITION → ENRICHED_REPLAY → ONE-SHOT_MESSAGE_QUALITY_V2`
- No paid APIs: `FREE_ONLY`
- Open Research production integration: `0`
- Free Analyst full mode: `OFF`
- Existing bounded canary: preserve `market 1 / stocks 2 / total 3`
- Public Action: `0.4.5`
- operationId: `20/20 unique`
- schema: `4`

### Supersedes

This instruction **supersedes**:

`docs/work-instructions/20260825-kr-us-message-quality-market-specific-bounded-repair.md`

Reason:

The prior instruction focused first on prose/priority quality.  
Subsequent review showed that the larger current bottleneck is **market-specific structured evidence density**, especially breadth, market-wide flow, sector/style context, and local index context.

Do not execute the superseded instruction as the primary next task.

If it was already committed:
- preserve it as immutable history
- do not rewrite/delete it
- create a short supersession note pointing to this v2 instruction

If implementation based on the superseded instruction already started:
- stop before production promotion
- preserve useful tests/report artifacts
- port only generally useful quality components after Stage C of this instruction proves the enriched-data baseline

### Expected current production main / operating

Latest reported main/operating:

`b7dc15117b9295ab272eafb71c2e280b468a9307`

Resolve the actual latest safe `origin/main` and operating SHA before implementation.

### Current architecture state

Already proven / deployed:

```text
Common AI Core v1
= integrated

Free Analyst
= KR 8/8 replay PASS
= US 14/14 replay PASS

Adaptive Renderer
= PASS

Semantic ownership
= PASS
Hanwha cross-industry leakage 4 → 0

KR valuation numeric-ref repair
= PASS

KR/US Market Adapter common contract
= PASS / safe PARTIAL

Open Research common shadow engine
= PASS

Production Research Connector
= NOT_AVAILABLE / BLOCKED_CONNECTOR

Open Research production integration
= 0
```

### Current evidence bottleneck

#### KR structured context currently incomplete

Known/observed gaps include:

```text
KOSPI local completed-session context
KOSDAQ local completed-session context
KOSPI/KOSDAQ advancers / decliners / unchanged
sector performance
large / mid / small relative performance
market-wide foreign / institution / retail flow
index contribution / large-cap concentration
```

Stock-level KR price/supply is stronger than market-level KR context.

#### US structured context currently incomplete

Known/observed gaps include:

```text
broad-market advancers / decliners / unchanged
equal-weight vs cap-weight context
sector breadth / fuller sector context
mega-cap / concentration context
```

Existing US context already includes useful equivalents of:

```text
SPY
QQQ
IWM
SOXX
rates / real yields / macro temporal context
```

US daily KR-style participant flow must remain unsupported unless a real compatible source exists.

---

# 0. Project decision

Do **not** spend another full iteration polishing sparse-input messages first.

The required sequence is now:

```text
Stage A
Structured source capability audit

Stage B
KR/US market-data acquisition implementation

Stage C
2026-08-25 same-day enriched replay
using:
  immutable natural packets
  +
  separately labeled supplemental structured evidence

Stage D
Message Quality v2
one bounded pass on the richer evidence shape

Stage E
KR/US immutable regression + canary simulation

Stage F
Production promotion of safe structured acquisition + quality v2

Stage G
Next natural US/KR canary
```

Open Research remains separate and OFF in production.

---

# 1. Work-instruction repository protocol

Store this exact instruction at:

`docs/work-instructions/20260825-kr-us-structured-data-acquisition-first-and-message-quality-v2.md`

Before implementation:

```bash
git fetch origin
git status
git rev-parse HEAD
git rev-parse origin/main
```

Then:

1. verify actual latest safe main/operating SHA
2. commit/push this exact instruction as a **docs-only instruction commit**
3. record:
   - instruction path
   - instruction commit SHA
   - instruction version
   - implementation base SHA
4. create a dedicated implementation branch from latest safe production main
5. no force push / history rewrite
6. do not merge Open Research shadow branches into this implementation

Recommended branch:

`codex/kr-us-structured-data-first-quality-v2`

---

# 2. Hard prohibitions

Do NOT:

- loosen numeric/semantic/temporal/fact-ownership validators
- weaken semantic ownership guard
- fabricate breadth
- fabricate market-wide flow
- fabricate sector/style data
- default unavailable market fields to zero
- mix incompatible units
- calculate stock quantity / market-wide monetary-flow concentration
- invent US foreign/institution/retail daily cash-equity flow
- add paid data/news APIs
- use generic web/news search as the primary source for structured numbers when a structured/official source exists
- enable Open Research in production
- enable Free Analyst full mode
- increase canary above 1/2/3
- enable Trade AR
- disable Inventory
- change Phase 9.0E
- change Macro temporal policy
- change price/RR ownership
- change valuation basis
- manually send Telegram
- manually run natural KR/US production
- mutate production DB during replay

---

# 3. Key design principle

The Common AI Core is not the current bottleneck.

The primary target is:

```text
better verified market evidence
→
better analysis
```

not:

```text
same sparse evidence
→
more prompt / prose tuning
```

Market-specific differences should live in:

```text
acquisition
normalization
session
market taxonomy
```

not in separate KR/US reasoning engines.

---

# Stage A — Structured Source Capability Audit

# 4. Audit current runtime/provider capabilities first

Before adding new code, inventory every existing free/official structured source already available in the repository/runtime.

Create a capability matrix:

```text
field
market
provider/source
official?
structured?
free?
same-day available?
next-morning available?
unit
session basis
historical access?
current runtime integration?
known publication delay?
```

Do not assume a missing packet field means the runtime has no source.

---

# 5. Source priority policy

For structured market data, prefer:

## Tier 1
Exchange / official market / regulator / government / central-bank source

## Tier 2
Existing production structured provider already used by thesis-monitor

## Tier 3
Existing free structured provider with stable provenance and session semantics

## Tier 4
Public structured endpoint already supported by the repo

Do not use:
- article text
- search snippets
- scraped headlines

as the primary source for breadth / flow / index closes if structured evidence is available.

---

# 6. Acquisition vs publication readiness

A market field may be:

```text
AVAILABLE_CURRENT
AVAILABLE_PRIOR_SESSION
PUBLICATION_PENDING
PARTIAL
UNAVAILABLE
```

Do not convert:

`PUBLICATION_PENDING → 0`

or:

`UNAVAILABLE → 0`

Publication timing is part of the evidence.

---

# Stage B — Common Structured Market Context Contract

# 7. Preserve the existing common adapter contract

Do not rewrite the adapter architecture unnecessarily.

Extend the existing common normalized context only where required.

Target semantic shape:

```text
market
session
as_of
cutoff

indices[]
breadth
sectors[]
style_size[]
market_flows[]
concentration[]
session_context
publication_state
data_gaps[]
```

Every quantitative field requires source/time/unit metadata.

---

# 8. Deterministic derived relations

Any derived market relation must be backend-computed.

Examples:

```text
breadth_ratio
QQQ_minus_SPY
SOXX_minus_SPY
equal_weight_minus_cap_weight
KOSDAQ_minus_KOSPI
top_N_market_flow_concentration
top_N_index_contribution
```

Only compute when:

```text
same date/session
compatible units
same scope
compatible definitions
```

Persist:
- formula
- input refs
- units
- session/date
- result

No AI arithmetic.

---

# Stage B-KR — KR Structured Data Acquisition

# 9. KR minimum viable structured acquisition

Priority P0/P1-equivalent acquisition targets for message usefulness:

## Required target set

```text
KOSPI close / return / as_of
KOSDAQ close / return / as_of

KOSPI:
  advancers
  decliners
  unchanged

KOSDAQ:
  advancers
  decliners
  unchanged

market-wide investor flow where officially/structurally available:
  foreign
  institution
  retail
  other official categories
  unit
  market scope
  as_of
```

These are the highest-value gaps for KR market interpretation.

---

# 10. KR second-priority target set

Implement when a safe free structured source exists:

```text
sector returns
large / mid / small relative performance
index contribution concentration
top market-cap contribution
```

Do not block v1 completion if these remain unavailable.

---

# 11. KR same-day vs next-morning publication contract

Preserve the proven KRX lifecycle.

For each field distinguish:

```text
session completed
same-day provider pending
same-day complete
next-morning complete
```

The KR digest should be able to say:

```text
same-day market breadth / flow not yet published
```

instead of pretending it is available.

---

# 12. KR market-wide flow unit contract

Market-wide flow must explicitly store:

```text
participant
net_flow
unit:
  KRW / shares / other
market scope
as_of
```

Stock-level participant flow may use shares.

Do not calculate concentration across incompatible units.

If compatible stock-level monetary flow cannot be obtained:

```text
stock-to-market flow concentration = Unknown
```

---

# 13. KR breadth validity

Breadth must bind to the correct market.

Never:

```text
overnight US breadth
→ KR local breadth
```

Never:

```text
KOSDAQ breadth
→ KOSPI breadth
```

Persist exchange/market identity.

---

# 14. KR acquisition acceptance

Set:

```text
KR_STRUCTURED_ACQUISITION =
PASS / PARTIAL / FAIL
```

PASS:
minimum required target set is safely available for the intended session.

PARTIAL:
some fields unavailable/pending but all failures are explicit and fail-closed.

FAIL:
wrong date/market/unit or unsafe defaulting.

Safe PARTIAL may still be production-eligible.

---

# Stage B-US — US Structured Data Acquisition

# 15. Preserve existing useful US inputs

Do not regress:

```text
SPY / broad-market context
QQQ / growth context
IWM / small-cap context
SOXX / semiconductor context
validated rates / real-yield / macro temporal context
```

These current facts must remain available to the Free Analyst.

---

# 16. US minimum new target set

Prioritize:

```text
broad-market advancers
broad-market decliners
unchanged if source supports it

equal-weight vs cap-weight context

sector returns / sector index or ETF context
```

The purpose is to distinguish:

```text
broad risk-off
vs
mega-cap/growth concentration
vs
sector-specific weakness
```

---

# 17. US second-priority target set

If safely available:

```text
Nasdaq breadth
small-cap breadth
SOX breadth / semiconductor constituent breadth
mega-cap contribution concentration
```

Do not block v1 if absent.

---

# 18. US participant-flow rule

Do not imitate KR.

Unless a real compatible structured source exists:

```text
US daily foreign flow = Unknown
US daily institution flow = Unknown
US daily retail flow = Unknown
```

Future:
- ETF flow
- options positioning
- short interest
- 13F

must remain separate evidence types with their own frequency semantics.

---

# 19. US session contract

Preserve:

```text
premarket
regular session
after-hours
```

A post-close event must not explain the regular-session move.

Any breadth/index/sector fact must bind to the same session being analyzed.

---

# 20. US acquisition acceptance

Set:

`US_STRUCTURED_ACQUISITION = PASS / PARTIAL / FAIL`

Safe PARTIAL is acceptable if missing fields remain Unknown and current useful SPY/QQQ/IWM/SOXX context is preserved.

---

# Stage C — Same-Day Enriched Evidence Replay

# 21. Mandatory immutable baseline evidence

Use:

## US

`2026-08-25-us-run-37-7e04812311c2`

## KR

the exact immutable `2026-08-25` KR afternoon natural packet used in the latest KR replay/canary reviews.

These packets remain untouched.

---

# 22. Supplemental structured evidence class

Because the newly implemented acquisition fields were not necessarily archived in the natural packet, allow one explicitly separate evidence class:

```text
SUPPLEMENTAL_STRUCTURED_EVIDENCE
```

For each supplemental field record:

```text
market
target session/date
retrieved_at
provider/source
source ref
field
unit
publication state
```

Never relabel it as:

`NATURAL_PACKET_EVIDENCE`.

---

# 23. Same-day target

Where the provider still supports the completed `2026-08-25` session, collect structured data for that exact completed session.

Do not query a later session and compare it as if it were 8/25.

If the source cannot reproduce the exact session:
leave Unknown.

---

# 24. Enriched KR replay

Construct:

```text
immutable KR packet
+
supplemental structured KR market context
```

Then run:

```text
Free Analyst
→ synthesis validator
→ Adaptive Renderer
→ hard validators
```

Compare against the sparse-input replay.

Required evaluation:

```text
Does the digest now distinguish:
- KOSPI vs KOSDAQ
- broad vs concentrated move
- market-wide flow
- sector/size structure where available?

Does stock analysis remain thesis-first?
```

---

# 25. Enriched US replay

Construct:

```text
immutable US run-37 packet
+
supplemental structured US market context
```

Evaluate:

```text
broad vs concentrated market move
growth vs broad-market behavior
semiconductor relative behavior
equal-weight signal
sector behavior
rate/real-yield context
breadth Unknown only when genuinely unavailable
```

---

# 26. Enriched-context value gate

Set:

```text
KR_STRUCTURED_CONTEXT_VALUE_ADD =
PASS / NO_MATERIAL_VALUE / FAIL

US_STRUCTURED_CONTEXT_VALUE_ADD =
PASS / NO_MATERIAL_VALUE / FAIL
```

PASS requires the new structured data to materially improve at least one of:

- market-move classification
- breadth interpretation
- concentration interpretation
- participant-flow interpretation
- sector/style differentiation

Do not define value-add as “message got longer.”

---

# 27. Before/after evidence-shape report

Create an explicit comparison:

```text
SPARSE_CONTEXT
vs
ENRICHED_CONTEXT
```

For KR and US list:
- fields added
- fields still Unknown
- analyses newly supportable
- analyses still not supportable

This is required before Stage D.

---

# Stage D — Message Quality v2
## Only after structured enrichment baseline is known

# 28. Do not port the old quality repair blindly

Use the superseded instruction only as a source of candidate ideas.

Re-evaluate each prior quality issue against the enriched packets.

Some problems may disappear naturally once the AI has better evidence.

Only repair issues that remain.

---

# 29. Common Message Quality v2 contract

Preferred stock-message order:

```text
1. primary investment logic
2. current evidence relevant to it
3. what current evidence does NOT prove
4. expectations / valuation if material
5. positioning if material
6. next check
```

Auxiliary accounting metrics do not automatically lead.

---

# 30. Thesis-first prioritization

Use the structured analysis object to distinguish:

```text
PRIMARY_THESIS_EVIDENCE
AUXILIARY_OPERATING_EVIDENCE
POSITIONING_EVIDENCE
PRICE_EVIDENCE
VALUATION_EVIDENCE
```

The opening conclusion should normally derive from:

`PRIMARY_THESIS_EVIDENCE`.

Exceptions:
a material event may promote another evidence type.

---

# 31. Generic synthesis rule

Generic lines that could apply unchanged to unrelated companies should not be used when a more specific current-entity thesis linkage is available.

Example of undesirable semantic shape:

```text
현재 근거는 핵심 사업 조건을 보여도
다음 확인까지 닫지는 못합니다.
```

If no specific synthesis is safely supportable:
prefer Minimal over generic filler.

---

# 32. Duplicate section rule

Within one message:

```text
판단
왜 중요한가
```

must not repeat the same substantive claim.

Target:

`duplicate_substantive_section_claims = 0`

---

# Stage D-KR — KR Quality v2

# 33. KR digest with enriched context

If structured local data is now available, priority is:

```text
1. KOSPI / KOSDAQ
2. local breadth
3. market-wide participant flow
4. sector / size structure
5. stock-level concentration if safely computable
6. overnight/global context
```

Global context remains secondary.

---

# 34. KR digest if acquisition remains partial

If domestic data still cannot be acquired:

do not endlessly polish the sparse digest.

Use a concise insufficiency message:

```text
known domestic facts
missing breadth/flow
what cannot be concluded
```

and keep the acquisition gap as a separate backlog.

---

# 35. KR stock messages

Use current entity thesis first.

Mandatory benchmark examples from immutable packet:

- SK hynix
- Hanwha Aerospace

Requirements:

SK hynix:
- current HBM/memory thesis driver
- expectation burden only from current expectation ref
- positioning remains tactical
- no generic duplicate synthesis

Hanwha:
- backlog/delivery/margin lead
- Inventory only supporting if selected
- no HBM/ASP leakage

Do not hard-code output.

---

# Stage D-US — US Quality v2

# 36. US market digest

Preserve material current facts.

With enriched context, preferred reasoning shape:

```text
broad index
+ growth/style
+ semiconductor
+ breadth/equal-weight
+ rates/real yields
→ classify whether move is broad, concentrated, sector-specific, or unresolved
```

Do not call broad risk-off when breadth contradicts or is Unknown.

---

# 37. US stock messages

Mandatory benchmark examples:

- CORZ
- CRCL

Use only their actual stored thesis drivers.

CORZ:
use packet-supported equivalents of:
- AI datacenter / colocation transition
- energized or billing capacity
- margin / cash conversion
- capex/debt/dilution

CRCL:
use packet-supported equivalents of:
- USDC/platform growth
- reserve-income dependence
- non-interest/platform revenue
- cash-flow resilience

If those drivers are not in the current packet:
do not invent them.

---

# 38. Generic synthesis repetition gate

For canary eligibility:

if a message contains generic repeated analysis despite an available company-specific thesis linkage:

```text
canary eligible = false
```

Per-message fallback.

Do not block the packet.

---

# 39. Quality v2 gates

Set:

```text
KR_MESSAGE_QUALITY_V2 =
PASS / FAIL

US_MESSAGE_QUALITY_V2 =
PASS / FAIL

COMMON_MESSAGE_QUALITY_V2 =
PASS / FAIL

GENERIC_SYNTHESIS_REPETITION =
PASS / FAIL

THESIS_FIRST_PRIORITIZATION =
PASS / FAIL

MARKET_DIGEST_EVIDENCE_UTILIZATION =
PASS / FAIL
```

---

# Stage E — Cross-Market Regression + Canary Simulation

# 40. Mandatory KR replay

Use enriched KR evidence object.

Target:
all expected messages reach safe terminal output.

Preserve:
- valuation ref repair
- semantic ownership
- Inventory
- investor-flow semantics
- Macro temporal
- Trade AR OFF

---

# 41. Mandatory US replay

Use enriched run-37 evidence object.

Target:
all 14 messages safe.

Preserve:
- directional relation repair
- FCF period identity
- RR ownership
- Macro temporal
- semantic ownership

---

# 42. Cross-market common reasoning audit

Hard target:

```text
same Free Analyst schema
same synthesis validator
same Adaptive Renderer
same hard validator path
```

Market differences only in:
- acquisition
- normalization
- market taxonomy
- session semantics

Set:

`KR_US_REASONING_SCHEMA_COMMON = PASS / FAIL`

---

# 43. Canary simulation

Preserve existing limits:

```text
market <= 1
stocks <= 2
total <= 3
```

For each selected message require:

```text
semantic ownership PASS
thesis-first quality PASS
generic repetition gate PASS
hard validators PASS
runtime-quality PASS
material information loss = 0
```

No ticker hard-coding.

---

# 44. Hard safety targets

Across KR + US:

```text
FACT_MISMATCH = 0
UNSUPPORTED_NUMERIC = 0
UNSUPPORTED_CAUSALITY = 0
TEMPORAL_VIOLATIONS = 0
TRADE_AR_LEAK = 0
HIDDEN_ARITHMETIC = 0
EXTERNAL_UNSOURCED_FACTS = 0
SEMANTIC_OWNERSHIP_ERRORS = 0
MATERIAL_INFORMATION_LOSS = 0
MARKET_CONTEXT_UNIT_CONFLICT = 0
MARKET_CONTEXT_DEFAULT_ZERO = 0
```

---

# Stage F — Production Promotion

# 45. Promotion separation

Promote only components that independently pass.

## Structured acquisition

May promote if:
- safe PASS/PARTIAL
- fail-closed
- no packet blocking
- provenance/time/unit correct
- full tests/CI PASS

## Message Quality v2

May promote if:
- enriched replay PASS
- quality gates PASS
- all hard safety errors 0
- canary simulation PASS

Do not wait for every optional breadth/sector field to be perfect.

---

# 46. Partial-source behavior

A structured source failure must not block normal production.

Expected:

```text
field unavailable
→ Unknown
→ AI sees absence
→ message may omit or qualify
→ packet continues
```

No adapter may become a new single point of production failure.

---

# 47. Current canary state

After safe promotion, preserve:

```text
FREE_ANALYST_ADAPTIVE_CANARY = armed / existing state
market <= 1
stocks <= 2
total <= 3
FREE_ANALYST_ADAPTIVE_FULL = OFF
```

No expansion.

---

# 48. Open Research remains out of production

Keep:

```text
OPEN_RESEARCH_PRODUCTION_INTEGRATION = 0
PRODUCTION_RESEARCH_CONNECTOR = NOT_AVAILABLE
```

This task improves the deterministic evidence base that Open Research will later use.

Do not solve the connector problem here.

---

# Stage G — Natural Proof

# 49. Next US natural run

After promotion, use the next naturally scheduled US run as:

```text
US_STRUCTURED_MARKET_CONTEXT_NATURAL
+
US_FREE_ANALYST_CANARY_NATURAL
```

No manual run.

---

# 50. Next KR natural run

Use the next eligible KR run as:

```text
KR_STRUCTURED_MARKET_CONTEXT_NATURAL
+
KR_FREE_ANALYST_CANARY_NATURAL
```

No manual run.

Natural proof is delivery/scheduler/receipt proof, not the first time we evaluate code correctness.

---

# 51. Required source-capability reports

Create:

1. `docs/reports/20260825-kr-us-structured-source-capability-matrix.md`
2. `docs/reports/20260825-kr-structured-acquisition-source-audit.md`
3. `docs/reports/20260825-us-structured-acquisition-source-audit.md`
4. `docs/reports/20260825-structured-publication-freshness-contract.md`

---

# 52. Required acquisition reports

5. `docs/reports/20260825-kr-structured-acquisition-implementation.md`
6. `docs/reports/20260825-us-structured-acquisition-implementation.md`
7. `docs/reports/20260825-market-context-unit-session-audit.md`
8. `docs/reports/20260825-kr-us-structured-acquisition-readiness.md`

---

# 53. Required enriched-replay reports

9. `docs/reports/20260825-kr-enriched-market-context-replay.md`
10. `docs/reports/20260825-us-run37-enriched-market-context-replay.md`
11. `docs/reports/20260825-kr-us-sparse-vs-enriched-context.md`
12. `docs/reports/20260825-kr-us-structured-context-value-add.md`

---

# 54. Required Message Quality v2 reports

13. `docs/reports/20260825-message-quality-v2-root-cause.md`
14. `docs/reports/20260825-kr-message-quality-v2.md`
15. `docs/reports/20260825-us-message-quality-v2.md`
16. `docs/reports/20260825-generic-synthesis-v2-audit.md`
17. `docs/reports/20260825-thesis-first-prioritization-audit.md`
18. `docs/reports/20260825-message-quality-v2-safety-parity.md`

---

# 55. Exact benchmark report

Create:

`docs/reports/20260825-kr-us-enriched-message-quality-v2-exact-benchmark.md`

Mandatory cases:

```text
KR MARKET DIGEST
SK HYNIX
HANWHA AEROSPACE

US MARKET DIGEST
CORZ
CRCL
```

For each show:

```text
SPARSE_PREVIOUS
ENRICHED_PRE_QUALITY
ENRICHED_POST_QUALITY_V2
DETERMINISTIC_REFERENCE
ADAPTIVE_SELECTED
```

This is the key human-review artifact.

---

# 56. Required canary/readiness reports

19. `docs/reports/20260825-kr-us-quality-v2-canary-simulation.md`
20. `docs/reports/20260825-kr-us-structured-data-quality-v2-readiness.md`
21. `docs/reports/20260825-kr-us-structured-data-quality-v2-artifact-index.md`

Recommended JSON:

`docs/reports/20260825-kr-us-structured-data-quality-v2-readiness.json`

---

# 57. Data-gap inventory

Create:

`docs/reports/20260825-kr-us-post-acquisition-data-gap-inventory.md`

For every target field:

```text
market
field
available?
source
same-day?
next-morning?
production integrated?
user-visible value?
remaining limitation?
priority
```

This determines later acquisition backlog.

---

# 58. Focused tests — structured acquisition

Required:

### Common
- missing remains Unknown
- no zero default
- source/time/unit provenance
- deterministic derived relation
- incompatible unit blocked
- wrong-session blocked

### KR
- KOSPI/KOSDAQ identity
- breadth identity
- same-day publication pending
- market-wide flow units
- stock/market mixed-unit concentration blocked

### US
- broad/growth/small-cap/semiconductor context
- breadth normalization
- equal-weight context if supplied
- sector context
- session semantics
- no KR participant-flow invention

---

# 59. Focused tests — Message Quality v2

Required:

- thesis-first prioritization
- auxiliary metric does not automatically lead
- generic synthesis rejection
- duplicate section suppression
- Minimal when no specific synthesis exists
- KR local data priority
- KR global context secondary
- US current market facts preserved
- US breadth Unknown boundary
- semantic ownership preserved
- canary quality eligibility

---

# 60. Full validation

Before any production promotion:

```text
focused structured tests PASS
focused quality-v2 tests PASS
KR enriched replay PASS
US enriched replay PASS
canary simulation PASS
full pytest PASS
Ruff PASS
git diff --check PASS
Investment Knowledge parity PASS
Chart Knowledge parity PASS
Public Action 0.4.5 unchanged
operationId 20/20 unique
schema 4 unchanged
implementation SHA Actions PASS
final main SHA Actions PASS
API /health PASS
worktrees clean
```

---

# 61. Readiness gates

Set:

```text
STRUCTURED_SOURCE_CAPABILITY_AUDIT =
PASS / FAIL

KR_STRUCTURED_ACQUISITION =
PASS / PARTIAL / FAIL

US_STRUCTURED_ACQUISITION =
PASS / PARTIAL / FAIL

KR_STRUCTURED_CONTEXT_VALUE_ADD =
PASS / NO_MATERIAL_VALUE / FAIL

US_STRUCTURED_CONTEXT_VALUE_ADD =
PASS / NO_MATERIAL_VALUE / FAIL

KR_MESSAGE_QUALITY_V2 =
PASS / FAIL

US_MESSAGE_QUALITY_V2 =
PASS / FAIL

COMMON_MESSAGE_QUALITY_V2 =
PASS / FAIL

GENERIC_SYNTHESIS_REPETITION =
PASS / FAIL

THESIS_FIRST_PRIORITIZATION =
PASS / FAIL

MARKET_DIGEST_EVIDENCE_UTILIZATION =
PASS / FAIL

KR_US_REASONING_SCHEMA_COMMON =
PASS / FAIL

STRUCTURED_DATA_QUALITY_V2_PRODUCTION_READY =
YES / NO
```

---

# 62. Completion response

Return:

```text
INSTRUCTION_COMMIT = ...
BRANCH = ...
BASE_SHA = ...
IMPLEMENTATION_SHA = ...
FINAL_MAIN = ...
OPERATING = ...
REPORT_COMMIT = ...

SUPERSEDED_INSTRUCTION =
20260825-kr-us-message-quality-market-specific-bounded-repair.md

STRUCTURED_SOURCE_CAPABILITY_AUDIT = ...

KR_STRUCTURED_ACQUISITION = ...
US_STRUCTURED_ACQUISITION = ...

KR_NEW_FIELDS =
[index / breadth / sector / flow list]

US_NEW_FIELDS =
[breadth / equal-weight / sector list]

KR_REMAINING_DATA_GAPS = ...
US_REMAINING_DATA_GAPS = ...

KR_STRUCTURED_CONTEXT_VALUE_ADD = ...
US_STRUCTURED_CONTEXT_VALUE_ADD = ...

KR_MESSAGE_QUALITY_V2 = ...
US_MESSAGE_QUALITY_V2 = ...
COMMON_MESSAGE_QUALITY_V2 = ...

GENERIC_SYNTHESIS_LINES_BEFORE = ...
GENERIC_SYNTHESIS_LINES_AFTER = ...

DUPLICATE_SECTION_CLAIMS_BEFORE = ...
DUPLICATE_SECTION_CLAIMS_AFTER = ...

KR_ENRICHED_REPLAY = .../...
US_ENRICHED_REPLAY = .../...

KR_CANARY_SIMULATED_SELECTED = ...
US_CANARY_SIMULATED_SELECTED = ...

FACT_MISMATCH = 0
UNSUPPORTED_NUMERIC = 0
UNSUPPORTED_CAUSALITY = 0
TEMPORAL_VIOLATIONS = 0
TRADE_AR_LEAK = 0
HIDDEN_ARITHMETIC = 0
EXTERNAL_UNSOURCED_FACTS = 0
SEMANTIC_OWNERSHIP_ERRORS = 0
MATERIAL_INFORMATION_LOSS = 0
MARKET_CONTEXT_UNIT_CONFLICT = 0
MARKET_CONTEXT_DEFAULT_ZERO = 0

FREE_ANALYST_ADAPTIVE_CANARY = ...
FREE_ANALYST_ADAPTIVE_FULL = OFF
CANARY_LIMIT = 1/2/3

OPEN_RESEARCH_PRODUCTION_INTEGRATION = 0
PRODUCTION_RESEARCH_CONNECTOR = NOT_AVAILABLE

STRUCTURED_DATA_QUALITY_V2_PRODUCTION_READY = ...

OPEN_P0 = ...
OPEN_MATERIAL_P1 = ...
P2_BACKLOG = ...

NEXT_ACTION =
WAIT_FOR_US_STRUCTURED_QUALITY_V2_NATURAL_CANARY /
WAIT_FOR_KR_STRUCTURED_QUALITY_V2_NATURAL_CANARY /
BOUNDED_REPAIR

PRODUCTION_MUTATION_FROM_REPLAY = 0
MANUAL_TELEGRAM_SEND = 0
MANUAL_PRODUCTION_TASK = 0

ZIP = ...
ZIP_SHA256 = ...
```

---

# 63. Severity

## P0

- wrong market/index/breadth/flow fact
- wrong session/date
- incompatible-unit relation displayed
- fabricated structured field
- temporal violation
- Trade AR leak
- hidden arithmetic
- external unsourced fact
- semantic ownership regression
- duplicate delivery / receipt regression
- Open Research accidentally enabled
- full mode accidentally enabled

## P1

- structured acquisition silently defaults missing to zero
- KR/US schema diverges materially
- adapter blocks whole packet on partial provider failure
- market digest materially misclassifies broad vs concentrated move
- generic synthesis remains canary-selected despite available specific thesis linkage
- new quality rules drop material packet evidence
- canary quality gate fails

## P2

- optional sector/size/breadth field still unavailable
- KRX same-day publication remains pending
- US participant flow unsupported
- safe PARTIAL adapter
- low-value context correctly omitted
- stylistic preference
- Open Research connector still unavailable

---

# 64. Final principle

The project should stop iterating on sparse-message prose as the main loop.

The new main loop is:

```text
acquire better structured market evidence
→ normalize safely
→ replay the same real packets
→ then tune message quality once
→ natural canary
```

For KR:

```text
domestic index
+ breadth
+ market-wide flow
+ sector/size
→ before global context
```

For US:

```text
broad/growth/small-cap/semiconductor
+ breadth
+ equal-weight
+ sector
+ rates
```

For both:

```text
same Common AI Core
same semantic ownership
same hard validators
different market evidence acquisition
```

Do not redesign Free Analyst again unless the richer evidence replay proves a real remaining reasoning defect.
