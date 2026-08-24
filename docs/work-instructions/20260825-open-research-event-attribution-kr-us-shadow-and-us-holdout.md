# thesis-monitor — Open Research & Event Attribution Layer v1
## KR Historical Benchmark + US Fresh Morning Holdout, Shadow-Only

## Metadata

- Workstream: `Open Research & Event Attribution Layer v1`
- Instruction version: `1.0`
- Authoring time context: `2026-08-25 01:57 KST`
- Execution mode: `SHADOW_ONLY`
- Production promotion: `BLOCKED`
- Repository: `sskim-ai/thesis-monitor`

### Production baseline

Expected current production main/operating:

`2e3e37cc75867d56a69211bbe93a3675cd87acd1`

IMPORTANT:
resolve the actual latest safe `origin/main` and operating SHA before execution.
Do not force the SHA above if main legitimately advanced for an independent safety repair.

### Latest shadow architecture

Adaptive Renderer shadow branch:

`codex/adaptive-renderer-selector-shadow`

Known SHAs from the latest completed shadow work:

```text
BASE = aad3041affd2036bc265e35d3ec1fe55ef97262b
INSTRUCTION_COMMIT = 8c7fbf1822cd392a73d33634a65dafe4e605e2a3
IMPLEMENTATION_SHA = 14e93584d8256f425d66f4b88602224606e0ec99
REPORT_COMMIT = 5e30b17bf1fa10acb5483bfb6961b2a6d6fc8a86
```

Known gates:

```text
FREE_ANALYST_SHADOW = PASS
FREE_ANALYST_FACT_BOUNDARY = PASS
FREE_ANALYST_NOVEL_SYNTHESIS = PASS
FREE_ANALYST_VALUE_ADD = PASS

ADAPTIVE_RENDERER_SELECTOR = PASS
ADAPTIVE_RENDERER_HUMAN_ALIGNMENT = PASS
ADAPTIVE_RENDERER_INFORMATION_PRESERVATION = PASS
ADAPTIVE_RENDERER_SAFETY_PARITY = PASS
ADAPTIVE_RENDERER_VALUE_ADD = PASS
FREE_ANALYST_END_TO_END_SHADOW = PASS
```

Known renderer benchmark:

```text
12 messages
Direct 3
Hybrid 8
Minimal 1
Human preference exact match 12/12
Material information loss 0
```

### Current production state

- Production Assist: `OFF`
- Inventory mode: `SELECTIVE_INVENTORY`
- Exact Trade AR user-visible: `OFF_PENDING_NATURAL_PROOF`
- Phase 9.0E: `SELECTIVE_CURRENT_FORMAL_FULL_FCF`
- Public Action: `0.4.5`
- operationId: `20/20 unique`
- schema: `4`

### Existing natural-review task

A separate production-natural review is already planned for the next US morning slot.

At this instruction's authoring time, the next intended US morning evidence slot is later on `2026-08-25 KST`.

Do not modify or replace that natural-review task.

This work should register its own **shadow-only US holdout review after the natural packet exists**.

Recommended default:
`2026-08-25 09:50 KST`

If this instruction is registered after that wall-clock time, schedule the shadow holdout for the next valid US natural morning after the production packet is terminal.
Record any schedule deviation explicitly.

---

# 0. Objective

The current system is strong at:

- canonical financial facts
- valuation basis
- price/RR ownership
- investor-flow facts
- macro temporal correctness
- cash flow
- working capital
- deterministic safety
- bounded analytical synthesis

The missing layer is:

> "Why did this stock / sector / market move today?"

The goal is to add a shadow-only research layer that can freely search and follow leads across public sources while still converting all usable research into a typed, source-bound evidence model before it reaches the Free Analyst.

Target architecture:

```text
Existing Verified Evidence Packet
        +
Open Research Agent
        ↓
Research Evidence Normalizer
        ↓
Source / Entity / Time Validator
        ↓
Event Attribution Analyst
        ↓
Competing Hypotheses
        ↓
Attribution / Negative-Evidence Validator
        ↓
Research Sidecar
        +
Existing Packet
        ↓
Evidence-Locked Free Analyst
        ↓
Synthesis Validator
        ↓
Adaptive Renderer
        ↓
Existing Hard Validators
        ↓
Shadow Would-Send Message
```

This task must cover both:

1. Korean market / Korean stocks
2. US market / US stocks

No production integration is allowed.

---

# 1. Work-instruction repository protocol

Store this exact instruction at:

`docs/work-instructions/20260825-open-research-event-attribution-kr-us-shadow-and-us-holdout.md`

Before implementation:

```bash
git fetch origin
git status
git rev-parse HEAD
git rev-parse origin/main
git rev-parse origin/codex/adaptive-renderer-selector-shadow
```

Then:

1. verify actual production main/operating SHA
2. verify latest Adaptive Renderer shadow branch tip
3. commit/push this exact instruction as a docs-only instruction commit
4. implementation must be based on that instruction commit SHA
5. create a dedicated branch from the latest safe Adaptive Renderer shadow branch
6. no force push / history rewrite
7. do not merge to main

Recommended branch:

`codex/open-research-event-attribution-shadow`

If the Adaptive Renderer branch legitimately advanced, use the actual latest safe tip and report the deviation.

---

# 2. Hard production freeze

This task MUST NOT:

- merge to main
- update operating
- restart production API for this feature
- change production AI prompt
- change production AI selector
- change production packet schema
- change Telegram delivery
- change production message formatting
- change schedules for normal production
- modify existing US/KR natural tasks
- mutate DB
- mutate Pilot
- mutate warning lifecycle
- mutate investment-logic versions
- mutate receipts
- mutate notificationdelivery rows
- enable Trade AR
- disable Inventory
- change Phase 9.0E
- change macro temporal policy
- change KRX/night-futures policy

Hard targets:

```text
PRODUCTION_MUTATION = 0
TELEGRAM_SEND = 0
PRODUCTION_TASK_RUN = 0
MAIN_PROMOTION = 0
```

Only the separate shadow holdout Scheduled Task described below may be created.

---

# 3. No paid research APIs

Permanent policy for this workstream:

`FREE_ONLY`

Do not add a paid news/search API.

Prefer:

1. issuer official releases / IR
2. SEC / OpenDART / exchange / regulator
3. central bank / government / official statistics
4. public company/industry official sources
5. high-quality major news available through existing supported search/browser capability
6. other public web sources only as lead-generation or secondary corroboration

If the current runtime has no generic free web-research connector:

- implement the research contract and shadow harness
- use the existing supported Codex/web research capability for shadow validation
- do not invent a fake production provider
- document the future provider boundary separately

---

# 4. Research freedom principle

The Open Research Agent may generate follow-up queries dynamically.

Example pattern:

```text
Initial observation:
large stock decline

Search:
company name + decline reason + date
        ↓
Find capital-allocation event
        ↓
Search:
official shareholder-return announcement
peer shareholder-return comparison
        ↓
Find concentrated institutional/foreign selling
        ↓
Search:
market-wide flow
breadth
sector flows
        ↓
Find global semiconductor weakness
        ↓
Search:
US rates
sector index
peer moves
```

Do not hard-code these exact queries.

The Agent should be free to pivot as evidence emerges.

---

# 5. Query budget

Research must be bounded.

Recommended defaults per event cluster:

```text
initial queries: <= 6
follow-up rounds: <= 3
total query count per cluster: <= 18
```

For the full market holdout, use materiality-based clustering rather than running 18 searches for every monitored ticker.

If more queries are needed:
record why.

Do not optimize for exhaustive internet coverage.

Optimize for:
- source quality
- causal discrimination
- sufficient evidence to compare hypotheses

---

# 6. Search log

Persist a sanitized shadow search log:

```text
research_cluster_id
query
created_at
reason
parent_query
result_count
selected_sources[]
rejected_sources[]
```

Do not persist secrets or session credentials.

This log is audit evidence, not user output.

---

# 7. Source hierarchy

Use source tiers.

## Tier 1 — Primary

- company official release / IR
- SEC
- OpenDART
- KRX / exchange
- central bank
- government / official statistics
- regulator

## Tier 2 — High-quality independent reporting

Examples:
- Reuters
- AP
- major financial publications
- reputable business press

Exact source availability may vary.

## Tier 3 — Useful secondary reporting

May corroborate or surface leads.

## Tier 4 — Lead only

Blogs, aggregators, community, unsourced commentary.

Tier 4 must not independently support a confirmed event fact.

---

# 8. Source de-duplication

Detect:

- wire-service syndication
- verbatim republication
- same original company statement repeated by many outlets
- copied analyst note summaries

Do not count ten copies of one Reuters article as ten independent confirmations.

Persist:

```text
source_family
original_source
syndicated_from
independent_confirmation
```

when detectable.

---

# 9. Entity validation

Every research item must bind to:

```text
entity
ticker
market
issuer identity
related entity if different
relationship type
```

Examples of relationship type:

```text
DIRECT_ISSUER
CUSTOMER
SUPPLIER
PEER
SECTOR
MACRO
MARKET_STRUCTURE
```

Do not treat a related-company event as a direct issuer event.

---

# 10. Event-time validation

Persist separately:

```text
event_at
published_at
retrieved_at
research_cutoff
market_session
```

For causal attribution:

an event that occurred after the relevant price move cannot be treated as the cause of that move.

A post-close article may support interpretation of an earlier event, but the article publication itself is not the causal event.

Create:

`CAUSAL_TIME_ELIGIBLE = true/false`

---

# 11. Research evidence model

Create a typed shadow-only evidence contract.

Suggested semantic shape:

```text
research_evidence_id
cluster_id
entity
ticker
market

source
source_tier
source_type
source_ref

event_at
published_at
retrieved_at

evidence_type:
  CONFIRMED_EVENT_FACT
  CONFIRMED_MARKET_FACT
  CONFIRMED_FLOW_FACT
  CONFIRMED_BREADTH_FACT
  REPORTED_INTERPRETATION
  NEGATIVE_EVIDENCE
  UNKNOWN

statement
fact_semantic

causal_time_eligible
currentness_role

corroboration_refs[]
contradiction_refs[]
limitations[]
```

Exact field names may follow repository style.

---

# 12. Fact / Interpretation / Negative Evidence / Unknown

Keep these separate.

## Confirmed Fact

A source-supported fact.

## Interpretation

An explanation inferred from facts.

## Negative Evidence

Safe form:

```text
Within the searched official / high-quality source scope,
no verified evidence was found for X.
```

NOT:

```text
X does not exist.
```

## Unknown

The research did not resolve the issue.

This distinction is mandatory.

---

# 13. Negative-evidence scope object

Every negative-evidence claim must include:

```text
question
searched_source_tiers
query_count
searched_time_window
entities/sectors checked
last_search_at
what_was_not_found
coverage_limitations
```

Example:

```text
No verified new HBM-order reduction,
HBM price decline,
or customer CAPEX cut was found
within the searched official and major-news scope.
```

Do not turn this into:
`HBM fundamentals are fine`.

---

# 14. Research arithmetic remains deterministic

If research facts produce useful quantitative relations, compute them in deterministic code.

Examples:

```text
two-stock share of total foreign selling
sector contribution to index decline
breadth ratios
flow concentration
```

The AI must not perform hidden arithmetic.

Create canonical research-derived relations with:

```text
input refs
formula
period
unit
result
```

If required inputs are unavailable:
leave Unknown.

---

# 15. Market breadth evidence

Support both KR and US markets.

Potential evidence:

### KR
- KOSPI
- KOSDAQ
- advancers / decliners where available
- market-wide foreign/institutional flows where available
- sector returns
- large-cap vs mid/small-cap relative performance
- index contribution concentration

### US
- S&P 500 / Nasdaq / Russell / SOX
- advancers / decliners where available
- equal-weight vs cap-weight behavior where available
- sector ETF / sector index behavior
- mega-cap concentration
- rates / dollar / oil / credit context where relevant

Do not fabricate missing breadth data.

Use only actual free/public evidence.

---

# 16. Research event clusters

Research should work by event cluster.

Suggested cluster types:

```text
COMPANY_SPECIFIC_CATALYST
SECTOR_INDUSTRY_CATALYST
MARKET_BREADTH_ROTATION
POSITIONING_FLOW
MACRO_RATES_FX
TECHNICAL_MECHANICAL
UPCOMING_EVENT_RISK
UNKNOWN
```

These are internal categories.

Do not expose enum names verbatim to users.

---

# 17. Competing-hypothesis model

For each material move, the Event Attribution Analyst should generate multiple plausible causes before concluding.

Suggested typed structure:

```text
hypothesis_id
hypothesis_type
description

supporting_evidence_refs[]
contradicting_evidence_refs[]
unresolved_questions[]

causal_time_valid
scope:
  company
  sector
  market
  macro
  positioning

attribution_strength:
  STRONG
  MODERATE
  WEAK
  UNRESOLVED

what_would_change_the_view[]
```

Do not use probabilities unless there is a supported probabilistic model.

---

# 18. Mandatory hypothesis competition

For large or unusual price moves, test at least:

1. company-specific news/event
2. sector/industry development
3. market-wide/risk-off or rotation
4. positioning/flow
5. macro discount-rate / rates / FX / commodity channel

Add other hypotheses only if supported.

Do not force all five into final prose.

---

# 19. Cause vs correlation

A correlated move is not automatically causal.

Example:

```text
US long yields high
+ semiconductor stocks weak
```

may support a macro-risk hypothesis.

It does not prove:

```text
yield move caused this stock's decline
```

unless timing and cross-sectional evidence are consistent.

Use language strength accordingly.

---

# 20. Event Attribution Analyst output

Create a structured attribution object:

```text
event_attribution_version

observed_move
  security
  session
  close_return
  intraday_shape if available

primary_hypothesis
secondary_hypotheses[]
rejected_or_weak_hypotheses[]

company_specific_findings[]
sector_findings[]
market_breadth_findings[]
positioning_findings[]
macro_findings[]

negative_evidence[]
unknowns[]
next_confirmation_events[]
```

Do not include private chain-of-thought.

This is a concise conclusion record.

---

# 21. Attribution strength rules

## STRONG

- direct company event
- time-consistent
- primary/high-quality source
- price/flow behavior consistent
- no stronger contradiction

## MODERATE

- multiple consistent facts
- causal interpretation still inferred

## WEAK

- plausible but indirect

## UNRESOLVED

- evidence insufficient or competing explanations remain

Do not convert `STRONG` into factual certainty for an inferred cause.

---

# 22. Integration with existing packet

Research evidence must remain a sidecar.

Do NOT rewrite canonical production Facts.

Conceptually:

```text
production_analysis_packet
+
research_sidecar
=
shadow_augmented_analysis_packet
```

Existing packet remains immutable.

---

# 23. Integration with Free Analyst

Extend the shadow Free Analyst input to include:

```text
confirmed research facts
research-derived relations
competing hypotheses
negative evidence
research unknowns
next event checks
source-quality metadata
```

The Free Analyst may synthesize across:

- existing canonical facts
- research facts
- stored investment logic
- market expectations
- valuation
- price
- supply
- macro

But every research-based claim must carry source/evidence refs.

---

# 24. Research claim support types

Add shadow support types or repository-equivalent:

```text
RESEARCH_DIRECT_FACT
RESEARCH_REPORTED_INTERPRETATION
EVENT_ATTRIBUTION_INFERENCE
NEGATIVE_EVIDENCE_BOUNDARY
CROSS_SECTIONAL_SYNTHESIS
MARKET_BREADTH_SYNTHESIS
UPCOMING_EVENT_CHECK
```

No generic:
`RESEARCH_SUPPORTED`

Typed semantics are required.

---

# 25. Research claim provenance

For every final research-derived sentence create:

```text
final sentence
→ Free Analyst analysis item
→ support type
→ research evidence refs
→ canonical packet refs if used
→ source tier
```

This is mandatory.

No hidden reasoning disclosure is needed.

---

# 26. Causality validator

Implement a shadow-only Event Attribution / Causality Validator.

It must reject or downgrade:

- cause after price move
- one-source speculative claim as confirmed
- related-company event treated as direct issuer fact
- market move inferred from one stock only
- supply alone treated as business deterioration
- negative evidence rendered as existential certainty
- sector move rendered as company-specific cause without direct evidence
- macro correlation rendered as proven cause
- unsupported "profit taking", "deleveraging", "rotation" stated as fact

Interpretive wording may be allowed with evidence and boundaries.

---

# 27. Negative-evidence validator

Hard rules:

Allowed:

```text
"현재 확인한 공식자료와 주요 보도 범위에서는
신규 주문 감소 근거를 확인하지 못했습니다."
```

Reject:

```text
"신규 주문 감소는 없습니다."
```

Allowed:

```text
"검색 범위에서는 HBM 수요 훼손을 직접 가리키는 새 근거가 확인되지 않았습니다."
```

Reject:

```text
"HBM 수요는 문제없습니다."
```

---

# 28. Research source-language safety

If an article says:

```text
"investors were disappointed"
```

do not automatically convert to:

```text
market consensus was disappointed
```

Preserve attribution:

```text
Reuters reported that ...
```

or summarize as an interpretation with source refs.

Company guidance and journalist interpretation must remain separate.

---

# 29. Upcoming-event handling

Upcoming events may be included when verified.

Examples:

- earnings
- FOMC
- official investor day
- product launch
- regulatory deadline

The system may say:

```text
this is the next event that could confirm/refute the current attribution
```

It may not say:

```text
this event will reverse the stock
```

---

# 30. KR historical benchmark — mandatory

Use the `2026-08-24` Korean market move as the first historical benchmark.

Primary benchmark questions:

### Samsung Electronics
- Was there a verified company-specific catalyst?
- Was the catalyst related to capital allocation / shareholder return?
- What exact official facts were announced?
- Which parts of "expectation disappointment" are interpretation rather than official Fact?

### SK hynix
- Was there a separate verified same-day company-specific negative catalyst?
- Was its move consistent with broader semiconductor/large-cap positioning?
- What evidence supports or contradicts that attribution?

### Joint Samsung + SK hynix
- Was investor selling unusually concentrated?
- Can concentration be quantified safely from actual available data?
- Was market breadth consistent with broad risk-off or large-cap concentration?
- Did KOSDAQ / other sectors diverge?
- Was there verified new HBM order/price/customer-CAPEX deterioration in the searched scope?

### External environment
- US semiconductor risk appetite
- long rates
- relevant futures / peers
- upcoming major semiconductor event if verified and temporally relevant

Do not hard-code the expected conclusion.

The benchmark should independently reconstruct the most supported attribution.

---

# 31. KR benchmark source requirements

Aim for:

- official Samsung source
- official SK hynix source
- at least one high-quality independent report
- market/breadth source
- flow source where safely available
- global semiconductor/macro source where relevant

If any source class is unavailable:
report Unknown.

Do not fabricate the famous "92%" concentration figure unless the exact underlying values are captured and deterministically computed.

---

# 32. KR benchmark comparison target

Create:

```text
Human/reference narrative
vs
System research attribution
```

Do not require verbatim agreement.

Compare:

- identified cause classes
- Fact/Interpretation separation
- negative evidence safety
- market-breadth reasoning
- flow concentration
- thesis implication
- next confirmation event

Classify:

```text
MATERIAL_MATCH
PARTIAL_MATCH
MATERIAL_MISS
```

---

# 33. US fresh morning holdout — mandatory

After the next natural US production packet is terminal, run a separate shadow-only research holdout.

Recommended default scheduled execution:

`2026-08-25 09:50 KST`

This is intentionally after the existing `09:20` natural review window.

If the natural packet/review is still nonterminal:

- wait read-only until `10:05 KST`
- do not trigger production
- if still unavailable:
  set `US_FRESH_RESEARCH_HOLDOUT = DEFERRED_NONTERMINAL`
  and create the result bundle anyway

If this instruction is being registered after the scheduled wall time:
run at the next eligible US morning after a natural production packet is terminal.

---

# 34. Create one-shot shadow Scheduled Task

Create a one-shot Codex Scheduled Task.

Recommended name:

`open-research-us-fresh-holdout`

Task requirements:

- shadow only
- repository branch/worktree for this feature
- no production mutation
- no Telegram
- no provider re-run of production packet
- may perform fresh public web research at holdout cutoff
- consumes the already-created immutable US natural packet
- creates reports and ZIP
- disables/removes itself after one terminal run if recurring scheduling fallback is used

Record task ID and cleanup state.

---

# 35. US holdout research scope

Use the actual natural US packet.

Research:

### Market-level
- main US index/sector move drivers
- rates / dollar / oil / macro releases if relevant
- breadth / concentration if available
- sector rotation
- semiconductor/AI risk appetite if material

### Stock-level
Select the material/eventful monitored names based on:

- packet event relevance
- unusual move
- new official event
- material warning
- price/flow anomaly
- existing thesis sensitivity

Do not run deep research on every ticker if nothing material happened.

Record selection reason.

---

# 36. US holdout competing hypotheses

For each researched stock or event cluster, test:

- direct issuer event
- earnings/guidance
- sector/peer event
- macro discount-rate channel
- broad risk-on/risk-off
- positioning/flow if actual evidence exists
- mechanical/index effect if supported
- no clear attribution

Do not force a cause.

---

# 37. US market digest research output

Generate a shadow research-enhanced US market digest.

It should answer:

```text
What actually changed?
What appears to have driven the move?
Was it broad or concentrated?
What evidence argues against the obvious alternative explanation?
What next event would change the interpretation?
```

Do not make it longer merely because more sources were collected.

Feed it through the Adaptive Renderer.

---

# 38. Research-enhanced stock message

For each selected material stock, target a concise structure like:

```text
🎯 오늘 움직임의 성격
🔎 가장 강한 근거
⚖️ 대안 해석 / 무엇은 아직 미확인인가
📌 다음 확인
```

Optional:
- price/valuation
- positioning
- macro channel

Only when material.

---

# 39. Integration with Adaptive Renderer

The Adaptive Renderer should decide among:

```text
DIRECT_ANALYST
CONCISE_HYBRID
MINIMAL_VNEXT
```

using the existing validated analysis shape plus research attribution shape.

DIRECT should be favored when:
- competing hypotheses materially matter
- negative-evidence boundary must be preserved
- attribution remains uncertain
- multiple cause layers must be shown

HYBRID when:
- primary cause is well-supported
- one caveat is sufficient

MINIMAL when:
- there is no meaningful research value-add
- no material new attribution exists

Do not hard-code by market.

---

# 40. Research-specific Direct-required rule

Create a Direct-required trigger when compression would drop:

- a material competing hypothesis
- a negative-evidence boundary
- causal-time qualification
- a distinction between company event and market/sector effect

Material boundary loss is not allowed.

---

# 41. Research no-value behavior

If research adds no verified value:

```text
OPEN_RESEARCH_VALUE_ADD = NO_MATERIAL_VALUE
```

and the system should keep the existing non-research AI message.

Do not invent a "why" explanation to justify the research layer.

This is important.

---

# 42. Freshness / cutoff contract

For each research run record:

```text
research_cutoff
market_session
latest eligible event time
latest eligible publication time
post-close-only sources
```

For explaining a session move:
facts discovered after close may help attribution, but events occurring after close are not causes of the regular-session move.

---

# 43. Cross-market applicability

The architecture must not be KR-specific.

No logic like:

```text
if ticker == Samsung:
...
```

No logic like:

```text
if market == KR:
use hypothesis A
else:
use B
```

Market-specific adapters are allowed for:
- exchange calendars
- source normalization
- breadth fields
- participant taxonomies

Attribution semantics remain common.

---

# 44. KR/US source adapters

Create shared interface plus market adapters where needed.

Example:

```text
ResearchSourceAdapter
  search()
  fetch()
  normalize()

KRResearchAdapter
USResearchAdapter
```

But do not invent providers.

Adapters may wrap the actually available free research/search capability.

---

# 45. Search failure behavior

A failed search/provider must not kill the full shadow packet.

Per source/query:

```text
success
partial
failed
```

Research outcome may become:

```text
PARTIAL_RESEARCH
```

If key causal evidence is unavailable:
attribution remains unresolved.

No unsafe fallback.

---

# 46. Copyright / quote discipline

Do not reproduce long article passages.

Store:
- source title
- publication time
- short fact paraphrase
- source reference

Use minimal quotes only when necessary.

Reports should be paraphrase-heavy.

---

# 47. Research quality controls

Detect and flag:

- stale article
- article about another security
- pre-event background reused as today's catalyst
- duplicate wire story
- anonymous speculative commentary
- headline/body mismatch
- article publication after the claimed causal window
- "shares fell because..." article with no underlying evidence

Do not automatically trust causal language in headlines.

---

# 48. Benchmark harness

Create a reusable shadow harness:

```text
research_event_attribution_benchmark(
  packet_ref,
  market,
  cutoff,
  research_mode,
  expected_questions
)
```

Outputs:

```text
research log
normalized evidence
hypotheses
attribution object
Free Analyst analysis
Adaptive Renderer decision
final shadow message
validation
```

No production side effects.

---

# 49. KR benchmark gates

Set:

```text
KR_OPEN_RESEARCH_BENCHMARK =
PASS / PARTIAL / FAIL

KR_EVENT_ATTRIBUTION =
PASS / PARTIAL / FAIL

KR_MARKET_BREADTH_SYNTHESIS =
PASS / NOT_OBSERVED / FAIL

KR_NEGATIVE_EVIDENCE_SAFETY =
PASS / FAIL

KR_RESEARCH_FREE_ANALYST_VALUE_ADD =
PASS / NO_MATERIAL_VALUE / FAIL
```

---

# 50. US holdout gates

Set:

```text
US_FRESH_RESEARCH_HOLDOUT =
PASS / FAIL / DEFERRED_NONTERMINAL / NOT_OBSERVED

US_EVENT_ATTRIBUTION =
PASS / PARTIAL / FAIL / NOT_OBSERVED

US_MARKET_BREADTH_SYNTHESIS =
PASS / NOT_OBSERVED / FAIL

US_NEGATIVE_EVIDENCE_SAFETY =
PASS / FAIL / NOT_OBSERVED

US_RESEARCH_FREE_ANALYST_VALUE_ADD =
PASS / NO_MATERIAL_VALUE / FAIL / NOT_OBSERVED
```

---

# 51. Global safety gates

Set:

```text
OPEN_RESEARCH_SHADOW = PASS / FAIL

SOURCE_PROVENANCE = PASS / FAIL

ENTITY_TIME_VALIDATION = PASS / FAIL

EVENT_ATTRIBUTION_FACT_BOUNDARY = PASS / FAIL

CAUSAL_ATTRIBUTION_SAFETY = PASS / FAIL

NEGATIVE_EVIDENCE_SAFETY = PASS / FAIL

RESEARCH_HIDDEN_ARITHMETIC = 0

RESEARCH_EXTERNAL_UNSOURCED_FACTS = 0

RESEARCH_PRODUCTION_MUTATION = 0
```

---

# 52. Free Analyst / Adaptive integration gates

Set:

```text
RESEARCH_FREE_ANALYST_FACT_BOUNDARY = PASS / FAIL

RESEARCH_FREE_ANALYST_VALUE_ADD =
PASS / NO_MATERIAL_VALUE / FAIL

RESEARCH_ADAPTIVE_RENDERER =
PASS / FAIL

RESEARCH_MATERIAL_INFORMATION_LOSS = 0

RESEARCH_END_TO_END_SHADOW = PASS / FAIL
```

---

# 53. Research value-add definition

`RESEARCH_FREE_ANALYST_VALUE_ADD = PASS` requires at least one of:

- verified company-specific catalyst not present in the original packet
- market-breadth explanation
- cross-sectional positioning concentration
- meaningful competing-hypothesis discrimination
- safe negative evidence that materially narrows the explanation
- verified upcoming event that changes the next-check framing

Mere article summary is not value-add.

---

# 54. KR historical benchmark — no answer-key hard coding

The supplied human narrative may be used only as a qualitative comparison reference.

Do not:

- hard-code the shareholder-return conclusion
- hard-code the "92%" figure
- hard-code "positioning washout"
- hard-code HBM thesis result

The system must arrive at its own attribution from collected evidence.

---

# 55. US holdout — holdout integrity

Do not inspect a human-written answer key before generating the US research result.

The holdout must be genuinely fresh.

After generation, human review may compare it with:
- actual market reporting
- natural production message
- later commentary

This keeps the US test informative.

---

# 56. Proposed future production trigger policy — document only

Do not deploy, but propose when Open Research should run in production.

Possible triggers:

```text
material price move
new official event
thesis-sensitive event
large gap/reversal
market-wide unusual breadth
sector shock
new warning
user asks "why did it move?"
```

Do not propose "research every ticker deeply every day" as default unless cost and latency support it.

---

# 57. Latency / cost report

Even though paid APIs are forbidden, report:

```text
query count
pages fetched
research duration
model calls
estimated token usage if available
```

Separate:

- KR historical benchmark
- US fresh holdout

The goal is to understand whether this can become selective production research later.

---

# 58. Future production architecture proposal

Document only:

```text
Normal deterministic packet
        ↓
Research trigger
        ├─ no trigger → existing Free Analyst
        └─ trigger
             ↓
         Open Research Agent
             ↓
         Event Attribution
             ↓
         research sidecar
             ↓
         Free Analyst
             ↓
         Adaptive Renderer
             ↓
         hard validators
             ↓
         deterministic fallback if AI/research fails
```

No activation.

---

# 59. Kill switch proposal

Document a future independent kill switch:

```text
OPEN_RESEARCH_ENABLED = false
```

so production can fall back to the existing non-research packet without disabling Free Analyst.

Do not activate any feature flag now.

---

# 60. Required focused tests

Add tests for:

- source-tier normalization
- duplicate/syndicated source detection
- entity identity
- related-company vs direct issuer distinction
- causal time eligibility
- event-after-close rejection
- negative-evidence scope
- negative-evidence overclaim rejection
- competing-hypothesis structure
- cause-vs-correlation
- market-breadth synthesis
- deterministic research arithmetic
- hidden arithmetic rejection
- source-attribution preservation
- research claim provenance
- Free Analyst research integration
- Adaptive Renderer research Direct-required rule
- no-value research behavior
- KR/US market abstraction
- production isolation
- holdout scheduler isolation

---

# 61. Full validation

Run:

- focused tests
- full pytest
- Ruff
- `git diff --check`
- Investment Knowledge parity
- Chart Knowledge parity
- Public Action unchanged
- operationId 20/20 unique
- schema unchanged
- implementation SHA GitHub Actions Test/Lint
- final shadow branch tip GitHub Actions Test/Lint

Production main must remain unchanged.

---

# 62. Required KR reports

Create:

1. `docs/reports/20260825-open-research-architecture.md`
2. `docs/reports/20260825-open-research-source-policy.md`
3. `docs/reports/20260825-event-attribution-contract.md`
4. `docs/reports/20260825-negative-evidence-contract.md`
5. `docs/reports/20260825-kr-20260824-research-search-log.md`
6. `docs/reports/20260825-kr-20260824-research-evidence.md`
7. `docs/reports/20260825-kr-20260824-event-attribution.md`
8. `docs/reports/20260825-kr-20260824-research-message-benchmark.md`
9. `docs/reports/20260825-kr-20260824-research-value-add.md`

---

# 63. Required US holdout reports

Create after the fresh natural packet:

10. `docs/reports/20260825-us-fresh-research-holdout-registration.md`
11. `docs/reports/20260825-us-fresh-research-search-log.md`
12. `docs/reports/20260825-us-fresh-research-evidence.md`
13. `docs/reports/20260825-us-fresh-event-attribution.md`
14. `docs/reports/20260825-us-fresh-research-message-bundle.md`
15. `docs/reports/20260825-us-fresh-research-value-add.md`
16. `docs/reports/20260825-us-fresh-research-holdout-gates.md`

If the holdout runs on a later date because of registration timing:
use the actual date in filenames and cross-reference this instruction.

---

# 64. Required cross-market reports

17. `docs/reports/20260825-open-research-kr-us-comparison.md`
18. `docs/reports/20260825-open-research-causality-safety.md`
19. `docs/reports/20260825-open-research-free-analyst-adaptive-integration.md`
20. `docs/reports/20260825-open-research-latency-cost.md`
21. `docs/reports/20260825-open-research-production-integration-proposal.md`
22. `docs/reports/20260825-open-research-readiness.md`
23. `docs/reports/20260825-open-research-artifact-index.md`

Recommended JSON:

`docs/reports/20260825-open-research-readiness.json`

---

# 65. Exact message benchmark report

Create:

`docs/reports/20260825-open-research-message-benchmark.md`

For the KR historical benchmark include:

```text
EXISTING_PACKET_AI
FREE_ANALYST_NO_RESEARCH
FREE_ANALYST_WITH_RESEARCH_DIRECT
FREE_ANALYST_WITH_RESEARCH_HYBRID
ADAPTIVE_SELECTED_RESEARCH
```

For the US fresh holdout include:

```text
NATURAL_PRODUCTION_MESSAGE
FREE_ANALYST_NO_RESEARCH
FREE_ANALYST_WITH_RESEARCH
ADAPTIVE_SELECTED_RESEARCH
```

Mark all research variants:

`SHADOW — NOT SENT`

---

# 66. Machine-readable summary

Create:

`docs/reports/20260825-open-research-benchmark-summary.json`

Include:

```text
repository
research_architecture
source_policy
kr_benchmark
us_holdout
source_counts
query_counts
hypothesis_counts
attribution
negative_evidence
free_analyst
adaptive_renderer
safety
latency
production_isolation
gates
next_action
```

---

# 67. Mandatory result ZIP

Create:

`20260825-open-research-event-attribution-shadow-bundle.zip`

Include all sanitized KR, US, cross-market, provenance, benchmark, and readiness reports.

If the US holdout is deferred:
the ZIP must still include:
- completed KR benchmark
- implementation validation
- scheduled holdout registration
- defer state
- all available evidence

After the US holdout later completes:
produce a final replacement/final bundle with a new SHA.

Report SHA-256.

---

# 68. Scheduled-task cleanup

After US holdout terminal execution:

- if true one-shot: record terminal state
- if recurring fallback mechanism was used: disable/remove it
- verify no next run remains
- record cleanup time

Do not leave research task recurring.

---

# 69. Readiness states

Set:

```text
OPEN_RESEARCH_SHADOW =
PASS / FAIL

KR_OPEN_RESEARCH_BENCHMARK =
PASS / PARTIAL / FAIL

KR_EVENT_ATTRIBUTION =
PASS / PARTIAL / FAIL

US_FRESH_RESEARCH_HOLDOUT =
PASS / FAIL / DEFERRED_NONTERMINAL / NOT_OBSERVED

US_EVENT_ATTRIBUTION =
PASS / PARTIAL / FAIL / NOT_OBSERVED

SOURCE_PROVENANCE =
PASS / FAIL

ENTITY_TIME_VALIDATION =
PASS / FAIL

EVENT_ATTRIBUTION_FACT_BOUNDARY =
PASS / FAIL

CAUSAL_ATTRIBUTION_SAFETY =
PASS / FAIL

NEGATIVE_EVIDENCE_SAFETY =
PASS / FAIL

RESEARCH_FREE_ANALYST_FACT_BOUNDARY =
PASS / FAIL

RESEARCH_FREE_ANALYST_VALUE_ADD =
PASS / NO_MATERIAL_VALUE / FAIL

RESEARCH_ADAPTIVE_RENDERER =
PASS / FAIL

RESEARCH_END_TO_END_SHADOW =
PASS / FAIL

OPEN_RESEARCH_PROMOTION_READY =
YES_PENDING_NATURAL_AND_SEPARATE_INTEGRATION /
NO
```

---

# 70. Promotion rule

Even if every shadow gate passes:

```text
PRODUCTION_PROMOTION = BLOCKED
```

A separate production integration instruction is required.

Before promotion, require:

- existing US production natural review has no open P0/material P1
- US fresh research holdout passes or yields a clearly safe partial result
- source/causality/negative-evidence gates pass
- Free Analyst + Adaptive Renderer remain safe
- no production regression

---

# 71. Completion response — immediate implementation/KR phase

After implementation and KR benchmark, return:

```text
INSTRUCTION_COMMIT = ...
BRANCH = ...
BASE_SHA = ...
IMPLEMENTATION_SHA = ...
REPORT_COMMIT = ...

OPEN_RESEARCH_SHADOW = ...

KR_OPEN_RESEARCH_BENCHMARK = ...
KR_EVENT_ATTRIBUTION = ...
KR_MARKET_BREADTH_SYNTHESIS = ...
KR_NEGATIVE_EVIDENCE_SAFETY = ...
KR_RESEARCH_FREE_ANALYST_VALUE_ADD = ...

SOURCE_PROVENANCE = ...
ENTITY_TIME_VALIDATION = ...
EVENT_ATTRIBUTION_FACT_BOUNDARY = ...
CAUSAL_ATTRIBUTION_SAFETY = ...
NEGATIVE_EVIDENCE_SAFETY = ...

KR_QUERY_COUNT = ...
KR_SOURCE_COUNT = ...
KR_PRIMARY_SOURCE_COUNT = ...
KR_HIGH_QUALITY_NEWS_COUNT = ...

US_HOLDOUT_TASK_NAME = ...
US_HOLDOUT_TASK_ID = ...
US_HOLDOUT_SCHEDULE = ...
US_HOLDOUT_STATE = SCHEDULED

PRODUCTION_PROMOTION = BLOCKED
PRODUCTION_MUTATION = 0
TELEGRAM_SEND = 0

OPEN_P0 = ...
OPEN_MATERIAL_P1 = ...

ZIP = ...
ZIP_SHA256 = ...
```

---

# 72. Completion response — US holdout terminal phase

After the US holdout executes, append/report:

```text
US_FRESH_RESEARCH_HOLDOUT = ...
US_EVENT_ATTRIBUTION = ...
US_MARKET_BREADTH_SYNTHESIS = ...
US_NEGATIVE_EVIDENCE_SAFETY = ...
US_RESEARCH_FREE_ANALYST_VALUE_ADD = ...

US_QUERY_COUNT = ...
US_SOURCE_COUNT = ...
US_PRIMARY_SOURCE_COUNT = ...
US_HIGH_QUALITY_NEWS_COUNT = ...

RESEARCH_ADAPTIVE_RENDERER = ...
RESEARCH_END_TO_END_SHADOW = ...

OPEN_RESEARCH_PROMOTION_READY =
YES_PENDING_NATURAL_AND_SEPARATE_INTEGRATION / NO

US_HOLDOUT_TASK_CLEANUP = ...
PRODUCTION_MUTATION = 0
TELEGRAM_SEND = 0

OPEN_P0 = ...
OPEN_MATERIAL_P1 = ...

FINAL_ZIP = ...
FINAL_ZIP_SHA256 = ...
FINAL_REPORT_COMMIT = ...
```

---

# 73. Severity

## P0

- production/main behavior change
- Telegram send
- DB/Pilot mutation
- wrong entity
- wrong event time used causally
- unsupported factual claim
- negative evidence stated as certainty
- unsourced external fact accepted
- hidden arithmetic accepted
- research-generated user-visible Trade AR/broad AR/AP leak
- false-current macro attribution

## P1

- causal attribution systematically overclaims
- source provenance lost
- one-sided hypothesis analysis
- material competing explanation dropped
- research degrades Free Analyst factual boundary
- US fresh holdout cannot run because architecture is KR-specific
- research task interferes with natural production review

## P2

- incomplete breadth because free source unavailable
- no material research value on a quiet stock/day
- minor source duplication
- renderer preference issue
- query budget tuning
- research latency higher than desired

P2 does not require rollback of production because this feature is shadow-only.

---

# 74. Final principle

The goal is not:

```text
AI reads more news.
```

The goal is:

```text
AI searches freely,
but evidence enters the system through a strict source/time/entity boundary.

Then the AI compares competing explanations
instead of grabbing the first headline.

Finally it tells the user:
- what is confirmed
- what most likely explains the move
- what alternative explanation remains
- what was not found in the searched scope
- what event/data would change the interpretation
```

The final role split should be:

```text
Backend / deterministic core
= canonical market and financial truth

Open Research Agent
= discover relevant public evidence freely

Event Attribution Analyst
= compare plausible causes

Causality / Negative-Evidence Validator
= stop unsupported "why" stories

Free Analyst
= connect the explanation to the investment logic

Adaptive Renderer
= show only the amount of explanation that is actually useful

Deterministic Fallback
= keep production safe if research/AI fails
```

Build and benchmark this now in shadow.

Use the Korean 2026-08-24 move as the historical benchmark.

Use the next naturally generated US morning packet as the fresh holdout.

Do not change production until both the normal natural-proof track and this research track are reviewed separately.
