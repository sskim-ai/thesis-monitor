# thesis-monitor — KR Market Digest Evidence Prioritization
# + US Entity-Specific Synthesis Bounded Repair
## Final bounded quality cleanup before Open Research connector work

## Metadata

- Workstream: `KR_DIGEST_PRIORITIZATION_US_ENTITY_SPECIFIC_SYNTHESIS`
- Instruction version: `1.0`
- Date: `2026-08-26 KST`
- Repository: `sskim-ai/thesis-monitor`
- Task type: `BOUNDED_MESSAGE_QUALITY_REPAIR`
- Source policy: `FREE_ONLY`
- Architecture redesign: `NO`
- Data acquisition redesign: `NO`
- Open Research production integration: `0`
- Free Analyst full mode: `OFF`
- Existing bounded canary: preserve `market 1 / stocks 2 / total 3`
- Trade AR: preserve `OFF`
- Public Action: preserve `0.4.5`
- operationId: preserve `20/20 unique`
- schema: preserve `4`

### Expected current safe baseline

Most recently reported production main / operating from the completed KR live-rehearsal + US exchange-breadth v1 work:

`760dbe1bfd58d8a2d03f85186f003a381e1e05a8`

Resolve the actual latest safe `origin/main` and operating SHA before implementation.  
If the repo has safely advanced, use the actual latest safe main.

### Current proven state

Do not reopen already-closed architecture work.

```text
KR Kiwoom market context
- index/breadth = PASS
- size/sector context = PASS
- market-wide investor flow = PASS
- stock monetary flow = PASS
- KOSDAQ concentration = allowed when reconciled
- KOSPI concentration = still fail-closed when basis/taxonomy is unresolved

US structured context
- SPY / QQQ / IWM / SOXX = available
- RSP equal-weight context = available
- sector context = available
- Nasdaq official breadth adapter = integrated safe PARTIAL
- exact-session breadth may be publication-pending
- NYSE breadth = unavailable unless a later safe source is added

Common AI
- Free Analyst = integrated
- Adaptive Renderer = integrated
- semantic ownership = PASS
- hard fact/numeric/temporal validators = PASS
```

### Remaining quality defects observed

#### KR

The market digest now correctly starts from domestic data, but later sections can fall back to generic macro / US semiconductor language even when rich KR evidence exists.

Typical undesirable shape:

```text
판단:
KOSDAQ > KOSPI, breadth positive, KR flows differentiated

왜 중요한가:
generic "경기 확장 하나로 모든 위험자산이 오르는 시장은 아니다"

다음 확인:
US semiconductor vs S&P500 relative return
```

The issue is not missing data anymore.  
It is **evidence prioritization inside the market digest**.

#### US

Several stock messages remain too similar in analytical wording even when their stored investment logic differs.

Observed issue class:

```text
CORZ / HUT / WULF / TSM
→ similar "HPC execution and cash conversion are not closed" style synthesis
```

The problem is not factual safety.  
The problem is that the synthesis does not always surface the **entity-specific thesis driver** strongly enough.

TSM must not read like an HPC transition company when its actual packet/framework points to semiconductor-specific drivers such as utilization/ASP/product mix/capex/FCF or packet equivalents.

---

# 0. Objective

Perform **one final bounded quality repair** with two independent tracks:

```text
TRACK A — KR market digest
Use domestic structured evidence consistently from judgment
through interpretation and next-check selection.

TRACK B — US stock synthesis
Require entity-specific thesis-driver linkage and reject generic-only
cross-company synthesis when a specific supported linkage exists.
```

Do not redesign:
- Common AI Core
- Market Adapter
- acquisition layer
- Free Analyst schema
- Adaptive Renderer
- validator architecture

This task should be small, testable, and replay-driven.

---

# 1. Repository protocol

Store this exact instruction at:

`docs/work-instructions/20260826-kr-market-digest-prioritization-us-entity-specific-synthesis-bounded-repair.md`

Before implementation:

```bash
git fetch origin
git status
git rev-parse HEAD
git rev-parse origin/main
```

Then:

1. verify actual latest safe main and operating
2. commit/push this exact instruction as a docs-only instruction commit
3. record instruction commit SHA
4. create a dedicated branch from latest safe main
5. no force push / history rewrite

Recommended branch:

`codex/kr-digest-us-entity-synthesis-bounded-repair`

---

# 2. Hard prohibitions

Do NOT:

- modify Kiwoom acquisition contracts
- modify Nasdaq breadth acquisition contracts
- add NYSE breadth in this task
- change US participant-flow policy
- loosen any hard validator
- weaken semantic ownership
- hard-code ticker-specific final sentences
- hard-code target benchmark output text
- force lexical uniqueness merely for style
- invent company-specific thesis drivers from model knowledge
- use external knowledge not present in the current evidence object
- enable Open Research
- enable Free Analyst full mode
- increase canary limits
- enable Trade AR
- change monitoring registration/watchlist
- manually send Telegram
- mutate production DB from replay
- manually execute production schedule

---

# TRACK A — KR Market Digest Evidence Prioritization

# 3. Core rule

When current KR domestic structured context is rich enough, the digest must remain anchored to that evidence throughout:

```text
판단
→ 왜 중요한가 / 해석
→ 다음 확인
```

Do not use domestic data only in the opening sentence and then revert to generic global/macro wording.

---

# 4. KR evidence priority classes

Introduce or reuse typed priority metadata for market-digest reasoning.

Suggested order:

```text
P1 KR_LOCAL_MARKET_STRUCTURE
  - KOSPI / KOSDAQ
  - breadth
  - size/style
  - local sector context

P2 KR_LOCAL_MARKET_FLOW
  - market-wide foreign/institution/individual
  - validated stock-vs-market monetary relation
  - validated concentration

P3 KR_LOCAL_STOCK_CROSS_SECTION
  - monitored-stock aggregate implications
  - only when safe and meaningful

P4 GLOBAL_CURRENT_CONTEXT
  - overnight US indices
  - semiconductor relative performance
  - rates / real yields
  - FX / macro

P5 REFERENCE_LAGGING_MACRO
```

This is a reasoning-priority contract, not a display requirement to include every level.

---

# 5. Domestic-richness gate

Add a deterministic / typed indicator:

```text
KR_DOMESTIC_CONTEXT_RICH = true / false
```

It may be true when a completed session has enough of:

```text
KOSPI/KOSDAQ
+ breadth for both markets
+ at least one of:
    market-wide participant flow
    size/style context
    sector context
```

Do not define richness by raw field count alone.

Document the exact predicate.

---

# 6. KR core-judgment rule

If:

`KR_DOMESTIC_CONTEXT_RICH = true`

then the market digest core judgment must be grounded primarily in P1/P2 evidence.

Global context may:
- corroborate
- contradict
- qualify

but should not replace the local interpretation.

---

# 7. KR interpretation / "왜 중요한가" rule

The interpretation block should explain what the local market structure means.

Preferred analytical transformations include:

```text
KOSDAQ > KOSPI
+ positive breadth in both
→ move was not simply one-index headline noise

mid/small > large
+ KOSDAQ stronger
→ participation tilted away from only large-cap leadership

foreign sells KOSPI
+ breadth remains positive
→ distinguish large-cap/foreign selling pressure from broad market risk-off

foreign sells KOSPI
+ buys KOSDAQ
→ participant flow differs by market
```

Only use transformations supported by current facts.

Do not automatically call:
- rotation
- risk-on
- risk-off
unless evidence strength supports it.

---

# 8. KR "contradiction value" rule

Global context may deserve prominence when it materially contradicts local evidence.

Example shape:

```text
KR local breadth positive
but overnight global semiconductor context weak
→ local participation was broader despite external sector pressure
```

This is allowed because the global evidence adds contrast.

Do not include global context merely because it exists.

---

# 9. KR next-check selection

The next check should be selected from the **decision-changing unresolved local question**.

When domestic context is rich, next-check candidates should normally come from:

```text
whether breadth persists
whether KOSDAQ / small-mid relative strength persists
whether foreign KOSPI selling continues/reverses
whether institution support continues
whether sector leadership broadens/narrows
whether concentration becomes safely measurable
```

A global next check such as:

```text
SOXX vs S&P500
```

may be selected only when:
- the KR conclusion materially depends on semiconductor/global context
- and the current local evidence cannot resolve the question alone

---

# 10. KR market-digest compression

Do not dump all data.

A good digest should usually retain only:

```text
1 market-structure conclusion
1 supporting local-flow/breadth interpretation
1 uncertainty boundary
1 next check
```

Exact numbers are optional unless they materially change interpretation.

---

# 11. KR concentration boundary

Preserve current safety state.

If KOSPI concentration remains blocked due `ka10051 ↔ ka10066` basis/taxonomy difference:

- do not quote a concentration percentage
- do not imply exact concentration
- may say large-stock flow direction is consistent with market flow only if supported

KOSDAQ concentration may be used only when current reconciliation remains valid.

---

# 12. KR benchmark

Use the fresh 2026-08-25 production-equivalent KR rehearsal context already created by the latest work.

No provider recollection is required for the first benchmark.

Benchmark exact:

```text
KR MARKET DIGEST
```

Also regression-check:

```text
SK hynix
Hanwha Aerospace
Samsung Electronics if present
all other KR target messages
```

Goal:
market-digest improvement without changing good stock messages unnecessarily.

---

# TRACK B — US Entity-Specific Synthesis

# 13. Core rule

A stock message must not be considered high-quality merely because every sentence is fact-safe.

When the packet contains a specific stored investment-logic driver, the synthesis should make that driver visible.

Required analytical shape:

```text
current entity
→ specific stored driver / validation metric
→ current evidence
→ unresolved proof
```

---

# 14. Entity-specific support contract

For each synthesis-eligible stock message, construct an allowed support set from the current packet / stored monitoring state:

```text
PRIMARY_THESIS_DRIVERS
VALIDATION_METRICS
EXPECTATION_BURDEN
VALUATION_FRAMEWORK
WARNING / KILL CONDITIONS
CURRENT_FACT_RELATIONS
NEXT_CHECKS
INDUSTRY_FRAMEWORK
```

The generated conclusion must bind to this set.

No external model knowledge may supply missing drivers.

---

# 15. Entity-specific discriminator

Add a quality concept:

```text
ENTITY_SPECIFIC_DISCRIMINATOR
```

A discriminator is a supported concept that helps distinguish this company's investment logic from unrelated monitored companies.

Examples of semantic categories only:

```text
semiconductor:
utilization / ASP / product mix / capex / FCF

datacenter transition:
energized/billing capacity / colocation margin / cash conversion

stablecoin platform:
reserve-income dependence / non-interest revenue

defense:
backlog / delivery / margin
```

These examples do not authorize ticker hard-coding.

Use only the actual entity's supported current fields.

---

# 16. Minimum synthesis-specificity rule

For a non-Minimal stock message:

require at least one of:

```text
specific thesis driver
specific validation metric
specific expectation burden linked to current driver
specific unresolved proof / next check
```

If none is supportable:

```text
renderer = Minimal
```

is better than generic filler.

---

# 17. Cross-message semantic repetition detector

Strengthen the quality audit across the US batch.

Normalize claim-bearing synthesis lines and classify:

```text
GENERIC_SHARED
ENTITY_SPECIFIC_SHARED_STRUCTURE
ENTITY_SPECIFIC_UNIQUE
```

Do not fail messages merely for similar sentence structure.

Fail canary eligibility when:

```text
same/near-same analytical claim
+
different entity/industry thesis
+
no entity-specific discriminator
+
specific supported driver was available
```

---

# 18. Same-industry overlap is allowed

CORZ / HUT / WULF may legitimately share some analytical vocabulary if their actual stored logic overlaps.

Do not force fake differentiation.

But each message should surface its own supported distinguishing driver where available.

Quality criterion:

```text
same architecture
≠ same analytical conclusion
```

---

# 19. Cross-industry generic leakage

Treat as material quality failure if a sentence appropriate to one business model is reused for an unrelated company.

Mandatory negative control:

```text
TSM must not be summarized as a generic HPC-transition / billing-MW company
unless such driver actually exists in its current packet.
```

Current semiconductor framework / packet equivalents should drive TSM-specific synthesis.

---

# 20. TSM benchmark

Using the current US immutable replay packet, require TSM synthesis to bind to actual packet-supported semiconductor logic.

Use current supported equivalents of:

```text
utilization
ASP
product mix
gross/operating margin
capex
FCF
advanced-node execution
```

Only fields actually present in current evidence may be used.

Do not add any absent metric from general knowledge.

---

# 21. CORZ benchmark

Require explicit current-entity thesis linkage using current packet-supported equivalents of:

```text
HPC / datacenter transition
energized/billing capacity
colocation economics
cash conversion
capex / financing / dilution
```

No requirement to mention all of them.

---

# 22. HUT / WULF benchmarks

Do not assume the same thesis as CORZ.

For each:
- inspect stored drivers
- select the current primary driver
- link the synthesis to that driver
- preserve any crypto/mining/power/HPC distinction only if packet-supported

The benchmark should prove that "same broad theme" does not collapse all names into one template.

---

# 23. CRCL positive control

CRCL already showed improved entity-specific synthesis in prior quality-v2 work.

Use it as a positive control.

Do not regress:
- reserve-income dependence
- non-interest/platform revenue
- current expectation burden
or packet equivalents.

---

# 24. US market digest and breadth

Do not alter the US market-digest architecture in this bounded repair unless the new stock-quality logic accidentally affects it.

Preserve:

```text
SPY / QQQ / IWM / SOXX
RSP
sector context
rates / real yields
Nasdaq breadth if exact-session available
```

If exact-session breadth is publication-pending:
keep it Unknown.

Do not use stale breadth.

---

# 25. US participant flow remains out of scope

Keep:

```text
US foreign/institution/retail daily market flow = Unknown
```

Do not attempt to solve it here.

---

# Common Quality Rules

# 26. Generic synthesis must not become a hard-coded blacklist

Do not solve the problem only by removing exact phrases.

The detector should work on semantic/typed features such as:

```text
driver coverage
entity-specific discriminator coverage
claim relation type
section duplication
cross-message normalized claim
```

Exact string matching may be a supplemental test only.

---

# 27. No fake novelty

Do not optimize for wording diversity.

This is not a style-generation task.

The goal is:

```text
analytical specificity
```

not:

```text
different adjectives for each ticker
```

---

# 28. Section role contract

For stock messages:

```text
🎯 판단
= what the current evidence means for the investment logic

🔎 왜 중요한가 / 핵심 근거
= why that evidence maps to the specific driver

⚖️ 해석의 균형
= what remains unresolved / competing interpretation

💰 기대·Valuation
= only if expectation/valuation materially changes interpretation

📌 다음 확인
= decision-changing next proof

📊 수급
= positioning only, not business-thesis proof
```

Do not duplicate the same claim across sections.

---

# 29. Minimal renderer rule

Prefer `Minimal` if:

- no new material company-specific synthesis is safely supportable
- all candidate synthesis lines are generic
- evidence adds little beyond current stored logic

This is a quality success, not a failure.

---

# 30. Canary eligibility

For a stock candidate:

```text
hard validators PASS
semantic ownership PASS
entity-specific support PASS or legitimate Minimal
generic cross-message repetition PASS
duplicate-section PASS
```

If quality fails:
- per-message fallback
- do not block entire packet

---

# 31. Benchmark data sources

Use existing immutable / archived replay artifacts only.

## KR

Use the latest successful `2026-08-25` post-deploy production-equivalent rehearsal context and packet.

## US

Use the current immutable US benchmark packet:

`2026-08-25-us-run-37-7e04812311c2`

Resolve its actual completed-session date from metadata.

Do not recollect providers to change the packet.

Breadth sidecar may only be used if its exact session matches.

---

# 32. Mandatory exact before/after report

Create:

`docs/reports/20260826-kr-us-bounded-quality-exact-before-after.md`

Include:

## KR
- KR MARKET DIGEST
- SK hynix
- Hanwha Aerospace
- Samsung Electronics if present

## US
- US MARKET DIGEST
- CORZ
- HUT
- WULF
- TSM
- CRCL

For each show:

```text
PRE_REPAIR
POST_REPAIR
DETERMINISTIC_REFERENCE
RENDERER
CANARY_ELIGIBLE
QUALITY_CLASSIFICATION
```

---

# 33. Mandatory KR market-digest annotation

For PRE and POST, annotate each sentence with:

```text
EVIDENCE_PRIORITY_CLASS:
P1 / P2 / P3 / P4 / P5

ROLE:
judgment / interpretation / uncertainty / next_check
```

The post-repair digest should demonstrate that rich local context stays dominant.

---

# 34. Mandatory US synthesis annotation

For each US benchmark stock show:

```text
PRIMARY_THESIS_DRIVER_SELECTED
ENTITY_SPECIFIC_DISCRIMINATOR
CURRENT_FACT_REFS
UNRESOLVED_PROOF
EXPECTATION_REF if used
```

Also show whether the previous generic line would now be:

```text
ACCEPTED
REWRITTEN
MINIMAL_FALLBACK
```

---

# 35. Cross-message repetition audit

Create:

`docs/reports/20260826-us-cross-message-synthesis-specificity-audit.md`

Report:

```text
claim-bearing synthesis lines
generic shared lines
entity-specific shared-structure lines
entity-specific unique lines

cross-industry generic repetition count
same-industry acceptable overlap count
messages with no discriminator despite available support
```

Hard target:

```text
cross-industry generic repetition = 0
messages missing discriminator when one is available = 0
```

---

# 36. KR local-evidence utilization audit

Create:

`docs/reports/20260826-kr-market-digest-evidence-utilization-audit.md`

Report:

```text
domestic-richness predicate result
P1/P2 facts available
P1/P2 facts used in judgment
P1/P2 facts used in interpretation
next-check source class
global-context sentences retained
reason global context was retained
```

Hard target when domestic richness = true:

```text
judgment local-first = yes
interpretation local-first = yes
next check local-first = yes
```

unless a documented material global contradiction exists.

---

# 37. Human quality classification

For each benchmark message:

```text
MATERIAL_IMPROVEMENT
MINOR_IMPROVEMENT
GOOD_CURRENT_STATE
NO_MEANINGFUL_CHANGE
REGRESSION
```

Do not require every message to improve.

Hard requirement:

`REGRESSION = 0`

for production promotion.

---

# 38. Hard safety targets

Across all KR/US replay outputs:

```text
FACT_MISMATCH = 0
UNSUPPORTED_NUMERIC = 0
UNSUPPORTED_CAUSALITY = 0
TEMPORAL_VIOLATIONS = 0
SESSION_DATE_CONFLICT = 0
SEMANTIC_OWNERSHIP_ERRORS = 0
HIDDEN_ARITHMETIC = 0
EXTERNAL_UNSOURCED_FACTS = 0
MATERIAL_INFORMATION_LOSS = 0
TRADE_AR_LEAK = 0
DEFAULT_ZERO = 0
```

No safety regression is acceptable for a quality improvement.

---

# 39. Focused tests — KR

Add tests for:

- domestic-richness predicate
- local evidence priority over global when rich
- global contradiction can still be retained
- next-check selects local unresolved question
- KOSPI concentration remains blocked when unresolved
- KOSDAQ concentration only when reconciled
- no raw data dump
- no return to generic US semiconductor next-check without material linkage

---

# 40. Focused tests — US

Add tests for:

- entity-specific discriminator extraction from stored state
- TSM does not inherit HPC-transition synthesis
- CORZ/HUT/WULF can share structure but require supported distinguishing driver where available
- CRCL positive-control preserved
- generic-only synthesis becomes Minimal/fallback when no specific linkage
- cross-industry generic repetition canary rejection
- same-industry legitimate overlap not falsely rejected
- no external-knowledge driver injection
- expectation wording matches current stored level
- semantic ownership preserved

---

# 41. Existing US breadth regression

Run regression tests proving:

```text
Nasdaq breadth publication-pending remains fail-closed
stale breadth is not injected
NYSE remains unavailable when no source exists
RSP/sector/index/rate context remains unchanged
```

Do not turn this bounded repair into breadth v2.

---

# 42. Full replay

Required:

```text
KR latest post-deploy replay
→ all expected messages safe

US run-37 replay
→ all expected messages safe
```

Expected prior counts:

```text
KR = 8
US = 14
```

Report actual counts.

---

# 43. Canary simulation

Preserve:

```text
market <= 1
stocks <= 2
total <= 3
```

Run KR and US separately.

For every selected candidate require:

```text
hard safety PASS
runtime quality PASS
semantic ownership PASS
specificity PASS or legitimate Minimal
```

No canary expansion.

---

# 44. Production promotion rule

This repair may promote if:

```text
KR market-digest prioritization PASS
US entity-specific synthesis PASS
cross-industry generic repetition = 0
REGRESSION = 0
all hard safety errors = 0
KR replay PASS
US replay PASS
canary simulation PASS
focused tests PASS
full tests PASS
CI PASS
OPEN_P0 = 0
OPEN_MATERIAL_P1 = 0
```

Keep:
- Free Analyst full OFF
- canary 1/2/3
- Open Research production 0
- Trade AR OFF

---

# 45. No natural-run wait required for code correctness

Do not wait for the next natural run to determine whether this bounded quality logic is correct.

Use replay for:
- code correctness
- message quality
- safety parity

The next natural run is only:
- scheduler proof
- current-provider freshness proof
- delivery/receipt proof

---

# 46. Report consistency repair

The previous completion bundle reportedly left a placeholder such as:

```text
FINAL_MAIN = HEAD
```

while the artifact manifest contained the actual final SHA.

In this task:
- do not leave `HEAD`, `<sha>`, or unresolved placeholders in the final completion report
- report exact commit SHAs
- verify report/manifest/main/operating consistency

Set:

```text
REPORT_SHA_CONSISTENCY = PASS / FAIL
```

This is a reporting-integrity cleanup, not a code-architecture change.

---

# 47. Required reports

Create:

1. `docs/reports/20260826-kr-market-digest-prioritization-root-cause.md`
2. `docs/reports/20260826-kr-market-digest-evidence-utilization-audit.md`
3. `docs/reports/20260826-us-entity-specific-synthesis-root-cause.md`
4. `docs/reports/20260826-us-cross-message-synthesis-specificity-audit.md`
5. `docs/reports/20260826-kr-us-bounded-quality-exact-before-after.md`
6. `docs/reports/20260826-kr-us-bounded-quality-safety-parity.md`
7. `docs/reports/20260826-kr-us-bounded-quality-canary-simulation.md`
8. `docs/reports/20260826-kr-us-bounded-quality-readiness.md`
9. `docs/reports/20260826-kr-us-bounded-quality-artifact-index.md`

Recommended JSON:

`docs/reports/20260826-kr-us-bounded-quality-readiness.json`

---

# 48. Architecture documentation

Update only the minimum relevant docs.

Recommended:

1. `docs/architecture/FREE_ANALYST_MESSAGE_QUALITY.md`
   - entity-specific discriminator
   - generic vs shared-structure distinction

2. `docs/architecture/KR_MARKET_DIGEST_QUALITY.md`
   - domestic-richness predicate
   - local evidence priority
   - next-check priority

3. `docs/architecture/FREE_ANALYST_CANARY_POLICY.md`
   - specificity eligibility

Do not rewrite unrelated architecture docs.

---

# 49. Full validation

Before final promotion:

```text
focused KR tests PASS
focused US tests PASS
KR replay PASS
US replay PASS
US breadth regression PASS
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
REPORT_SHA_CONSISTENCY PASS
```

---

# 50. Gates

Set exactly:

```text
KR_DOMESTIC_CONTEXT_RICH =
YES / NO

KR_MARKET_DIGEST_LOCAL_FIRST =
PASS / FAIL

KR_MARKET_DIGEST_NEXT_CHECK =
PASS / FAIL

KR_MARKET_DIGEST_QUALITY =
PASS / FAIL

US_ENTITY_SPECIFIC_SYNTHESIS =
PASS / FAIL

US_CROSS_INDUSTRY_GENERIC_REPETITION =
PASS / FAIL

US_SAME_INDUSTRY_OVERLAP_HANDLING =
PASS / FAIL

TSM_THESIS_SPECIFICITY =
PASS / FAIL

CORZ_THESIS_SPECIFICITY =
PASS / FAIL

HUT_THESIS_SPECIFICITY =
PASS / FAIL

WULF_THESIS_SPECIFICITY =
PASS / FAIL

CRCL_POSITIVE_CONTROL =
PASS / FAIL

KR_REPLAY =
PASS / FAIL

US_REPLAY =
PASS / FAIL

KR_CANARY_SIMULATION =
PASS / FAIL

US_CANARY_SIMULATION =
PASS / FAIL

SAFETY_PARITY =
PASS / FAIL

REPORT_SHA_CONSISTENCY =
PASS / FAIL

CODE_CORRECTNESS =
PASS / FAIL

PRODUCTION_READY =
YES / NO
```

---

# 51. Completion response

Return:

```text
INSTRUCTION_COMMIT = ...
BRANCH = ...
BASE_SHA = ...
IMPLEMENTATION_SHA = ...
REPORT_COMMIT = ...
FINAL_MAIN = ...
OPERATING = ...

KR_DOMESTIC_CONTEXT_RICH = ...
KR_MARKET_DIGEST_LOCAL_FIRST = ...
KR_MARKET_DIGEST_NEXT_CHECK = ...
KR_MARKET_DIGEST_QUALITY = ...

KR_PRE_MESSAGE = ...
KR_POST_MESSAGE = ...

US_ENTITY_SPECIFIC_SYNTHESIS = ...
US_CROSS_INDUSTRY_GENERIC_REPETITION = ...
US_SAME_INDUSTRY_OVERLAP_HANDLING = ...

TSM_THESIS_SPECIFICITY = ...
CORZ_THESIS_SPECIFICITY = ...
HUT_THESIS_SPECIFICITY = ...
WULF_THESIS_SPECIFICITY = ...
CRCL_POSITIVE_CONTROL = ...

GENERIC_SHARED_LINES_BEFORE = ...
GENERIC_SHARED_LINES_AFTER = ...
CROSS_INDUSTRY_GENERIC_REPETITION_BEFORE = ...
CROSS_INDUSTRY_GENERIC_REPETITION_AFTER = ...
MISSING_ENTITY_DISCRIMINATOR_BEFORE = ...
MISSING_ENTITY_DISCRIMINATOR_AFTER = ...

KR_REPLAY = .../...
US_REPLAY = .../...

KR_CANARY_SIMULATION = ...
US_CANARY_SIMULATION = ...

FACT_MISMATCH = 0
UNSUPPORTED_NUMERIC = 0
UNSUPPORTED_CAUSALITY = 0
TEMPORAL_VIOLATIONS = 0
SESSION_DATE_CONFLICT = 0
SEMANTIC_OWNERSHIP_ERRORS = 0
HIDDEN_ARITHMETIC = 0
EXTERNAL_UNSOURCED_FACTS = 0
MATERIAL_INFORMATION_LOSS = 0
TRADE_AR_LEAK = 0
DEFAULT_ZERO = 0

NASDAQ_BREADTH_REGRESSION = ...
NYSE_BREADTH_STATE = ...

FREE_ANALYST_CANARY = ...
FULL_MODE = OFF
CANARY_LIMIT = 1/2/3
OPEN_RESEARCH_PRODUCTION_INTEGRATION = 0
TRADE_AR = OFF

REPORT_SHA_CONSISTENCY = ...
CODE_CORRECTNESS = ...
PRODUCTION_READY = ...

OPEN_P0 = ...
OPEN_MATERIAL_P1 = ...
P2_BACKLOG = ...

NEXT_ACTION =
WAIT_FOR_NATURAL_PROOF /
CONTINUE_TO_OPEN_RESEARCH_CONNECTOR /
BOUNDED_REPAIR

PRODUCTION_MUTATION_FROM_REPLAY = 0
MANUAL_TELEGRAM_SEND = 0
MANUAL_SCHEDULED_TASK = 0

ZIP = ...
ZIP_SHA256 = ...
```

---

# 52. Mandatory ZIP

Create:

`20260826-kr-market-digest-us-entity-synthesis-bounded-repair-bundle.zip`

Include:
- this instruction
- exact before/after report
- KR evidence utilization audit
- US synthesis specificity audit
- safety parity
- canary simulation
- readiness report
- artifact index

Never include:
- auth tokens
- secrets
- authorization headers

Compute/report SHA-256.

---

# 53. Severity

## P0

- wrong fact/number/unit
- wrong session/date
- semantic ownership regression
- unsupported causal claim
- hidden arithmetic
- Trade AR leak
- stale breadth promoted as current
- secret/token exposure
- replay mutates production state

## P1

- KR rich domestic evidence exists but interpretation still defaults to unrelated global context
- KR next check remains global despite a more material local unresolved question
- TSM or another unrelated company receives HPC-transition synthesis without supporting evidence
- canary selects generic-only synthesis when specific support exists
- quality repair drops material current evidence
- report SHA/main/operating inconsistency obscures actual deployed state

## P2

- some same-industry wording remains similar but correctly thesis-linked
- Minimal chosen because no specific new synthesis exists
- NYSE breadth still unavailable
- Nasdaq exact-session breadth still publication-pending
- harmless stylistic preferences
- Open Research connector still unavailable

---

# 54. Final principle

Do not do another architecture iteration.

The data plumbing is now sufficiently strong.

The remaining job is:

```text
KR:
rich domestic evidence
→ keep it dominant through the full market-digest reasoning chain

US:
safe stock evidence
→ surface the actual entity-specific investment logic
→ do not collapse unrelated companies into one generic synthesis
```

After this bounded repair passes, stop message-polishing loops.

The next major engineering step should be:

```text
Open Research production connector
→ selective event attribution integration
```

unless a new P0/P1 appears.
