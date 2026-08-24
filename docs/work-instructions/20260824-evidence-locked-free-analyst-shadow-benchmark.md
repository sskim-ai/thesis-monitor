# thesis-monitor — Evidence-Locked Free Analyst Shadow Benchmark

## Metadata

- Workstream: `AI Analyst Quality — Evidence-Locked Free Analyst`
- Instruction version: `1.0`
- Date: `2026-08-24 KST`
- Execution mode: `SHADOW_OFFLINE_ONLY`
- Production promotion: `BLOCKED`
- Repository: `sskim-ai/thesis-monitor`
- Current production main/operating at instruction authoring:
  `2e3e37cc75867d56a69211bbe93a3675cd87acd1`
- Existing AI Analyst vNext shadow branch:
  `codex/ai-analyst-quality-vnext-shadow`
- Existing vNext implementation:
  `7d488b4d959fcbe325ea901f4ac030fc0ba87908`
- Existing vNext report commit:
  `a8873b01474ca31c591a68069502aace48f37a0e`
- Existing vNext gates:
  - `AI_ANALYST_VNEXT_SHADOW = PASS`
  - `AI_ANALYST_VALUE_ADD = PASS`
  - `AI_ANALYST_SAFETY_PARITY = PASS`
  - `AI_ANALYST_PROMOTION_READY = YES_PENDING_NATURAL`
- Scheduled production-proof review already planned:
  `2026-08-25 09:20 KST US Morning Natural Multi-Proof Review`
- Production Assist:
  `OFF`
- Inventory mode:
  `SELECTIVE_INVENTORY`
- Exact Trade AR user-visible:
  `OFF_PENDING_NATURAL_PROOF`
- Phase 9.0E:
  `SELECTIVE_CURRENT_FORMAL_FULL_FCF`
- Public Action:
  `0.4.5`
- Output schema:
  `4`

This task tests a materially freer AI analyst architecture while preserving a hard evidence boundary.

Target philosophy:

```text
Free reasoning / Hard fact boundary
```

The AI may freely:
- prioritize
- connect
- compare interpretations
- synthesize across facts
- connect facts to the stored investment logic
- connect evidence to market expectations and valuation context
- decide message structure
- omit low-value details

The AI may NOT:
- invent facts
- invent numbers
- perform hidden new arithmetic
- use outside knowledge
- create unsupported causal claims
- override temporal/security/period semantics
- change production state

This is a shadow benchmark only.

---

# 0. Work-instruction repository protocol

Store this exact instruction at:

`docs/work-instructions/20260824-evidence-locked-free-analyst-shadow-benchmark.md`

Before implementation:

```bash
git fetch origin
git status
git rev-parse HEAD
git rev-parse origin/main
git rev-parse origin/codex/ai-analyst-quality-vnext-shadow
```

Then:

1. verify actual current production main/operating SHA
2. verify actual latest remote vNext shadow branch SHA
3. use the latest clean vNext shadow branch tip as the feature base so the Free Analyst can be compared against and reuse vNext infrastructure
4. commit/push this exact work instruction as a docs-only instruction commit
5. implementation must be based on that instruction commit SHA
6. create a new dedicated branch
7. no force push / history rewrite

Recommended branch:

`codex/evidence-locked-free-analyst-shadow`

If the vNext branch legitimately advanced after the SHAs above, use the actual latest safe branch tip and report the deviation.

---

# 1. Hard promotion freeze

This task must NOT:

- merge to main
- update operating
- restart production API for production behavior
- change production AI selection
- change Production Assist
- change Telegram delivery
- change production schedules
- change packet schema used by production
- change feature modes
- enable Trade AR
- disable Inventory
- change Phase 9.0E
- change macro temporal behavior
- mutate production DB
- mutate Pilot
- mutate warnings
- mutate monitoring state
- mutate production receipts
- run actual US/KR production tasks

All Free Analyst outputs are shadow/offline only.

The 2026-08-25 natural US review must run against the unchanged production main unless a separate safety repair becomes necessary.

---

# 2. Why this task exists

The current vNext improved:

- compression
- dynamic section selection
- duplicate removal
- priority selection
- structural readability
- factual safety

But much of the claim-bearing prose remained extractive from the already validated current AI output.

The next experiment must answer:

> Can the AI create genuinely new, useful analytical synthesis from the same verified evidence without increasing factual risk?

Do not optimize for prettier wording.

Optimize for:

```text
evidence → interpretation → investment relevance → uncertainty boundary
```

---

# 3. Architecture under test

Implement a separate shadow architecture:

```text
Verified analysis packet
        ↓
Evidence-Locked Free Analyst
        ↓
Structured analysis object
        ↓
Synthesis support validator
        ↓
Existing numeric / semantic / temporal / language validators
        ↓
Telegram renderer
        ↓
Shadow benchmark only
```

Do not make the model directly produce the final Telegram message as its only output.

The structured analysis object is mandatory.

---

# 4. Evidence universe

The Free Analyst may use only information explicitly supplied in the immutable packet and allowed stored monitoring context.

Allowed evidence classes include repository-equivalent:

- canonical Facts
- canonical derived relations
- current earnings context
- cash-flow contexts
- working-capital contexts
- price/RR facts
- valuation context
- investor-flow facts
- macro temporal facts
- stored core investment logic
- thesis drivers
- validation metrics
- warnings
- invalidation conditions
- market expectation level
- explicitly supplied Unknowns
- industry reasoning contract

Forbidden:

- model memory about the company
- web/general knowledge not in the packet
- unstated consensus
- unstated customer/order facts
- unstated industry numbers
- invented targets/stops
- hidden external retrieval

No provider calls.

---

# 5. Structured analysis object

Create a typed shadow-only analysis contract, repository-equivalent to:

```text
analysis_version

top_findings[]
  - finding
  - evidence_refs[]
  - materiality_reason
  - confidence_label

thesis_implications[]
  - implication
  - thesis_driver_refs[]
  - evidence_refs[]
  - direction
      supports
      challenges
      mixed
      neutral
  - boundary

alternative_interpretations[]
  - positive_interpretation
  - negative_interpretation
  - evidence_refs[]
  - current_balance
  - unresolved_reason

expectation_valuation_interaction[]
  - analysis
  - expectation_ref
  - valuation_refs[]
  - evidence_refs[]
  - boundary

positioning_synthesis[]
  - analysis
  - window_refs[]
  - fundamental_boundary

unknowns[]
  - unresolved_question
  - why_it_matters
  - evidence_needed

next_checks[]
  - check
  - linked_thesis_driver
  - linked_unknown

message_plan
  - primary_conclusion
  - selected_blocks[]
  - omitted_blocks[]
  - omission_reasons[]
```

Exact field names may follow repository style, but preserve the semantic separation.

Do not expose private chain-of-thought.

This object is a concise analytical conclusion record, not hidden reasoning.

---

# 6. The model is free to synthesize

Unlike extractive vNext, the Free Analyst may create claim-bearing sentences that do not exactly appear in any source span.

However, every new analytical claim must be evidence-bound.

Examples of permitted synthesis:

```text
Fact:
Inventory growth trails COGS growth.

Stored logic:
Inventory pressure is an early-warning area.

Interpretation:
This does not currently look like inventory building faster than operating scale.

Boundary:
It does not prove end-demand strength because price/mix effects remain unresolved.
```

The interpretation does not need to be a pre-existing sentence.

It does need valid evidence support.

---

# 7. Synthesis support types

Every analytical statement must be classified into one of these support types or repository-equivalent:

```text
DIRECT_FACT
DIRECT_RELATION
THESIS_LINKAGE
BOUNDED_INFERENCE
ALTERNATIVE_INTERPRETATION
UNCERTAINTY_BOUNDARY
EXPECTATION_VALUATION_LINK
POSITIONING_SYNTHESIS
```

No unclassified claim-bearing sentence is allowed.

---

# 8. Evidence references

Every support-bearing analysis item must reference the smallest sufficient evidence set.

Examples:

```text
THESIS_LINKAGE
→ one canonical Fact/relation
+ one stored thesis driver

EXPECTATION_VALUATION_LINK
→ market expectation evidence
+ valuation context
+ relevant operating evidence

POSITIONING_SYNTHESIS
→ exact 1D/5D/20D canonical flow windows

BOUNDED_INFERENCE
→ one or more canonical Facts/relations
+ explicit boundary
```

A claim cannot cite an entire packet generically.

---

# 9. Bounded inference rule

Allow inference when all are true:

1. all factual premises are supplied
2. the conclusion is a reasonable interpretation of those premises
3. it does not introduce a hidden factual premise
4. uncertainty is preserved
5. a material alternative explanation is surfaced when relevant
6. the conclusion is not stronger than the evidence

Examples:

Allowed:
```text
Inventory is not obviously building faster than COGS.
```

Not allowed:
```text
Demand is healthy.
```

unless the packet independently supports demand health.

Allowed:
```text
High expectations raise the importance of execution confirmation.
```

Not allowed:
```text
The stock will derate if execution misses.
```

unless a supported conditional valuation framework exists and wording remains conditional.

---

# 10. Positive / negative interpretation pair

For materially ambiguous operating evidence, ask the Free Analyst to consider both:

```text
most plausible positive interpretation
most plausible negative interpretation
what current evidence can actually distinguish
what remains unresolved
```

Do not force this block when evidence is not ambiguous.

This is not a bull/bear entertainment section.

It is a guard against one-sided interpretation.

---

# 11. Current-balance conclusion

After alternative interpretations, the model may state:

```text
current_balance =
positive / negative / mixed / unresolved
```

Only as an interpretation.

This must not automatically change:

- stored investment logic state
- warning lifecycle
- valuation context
- market expectations
- assessment DB

Shadow analysis only.

---

# 12. Thesis linkage should become materially stronger

For every synthesis-eligible stock, attempt:

```text
important current evidence
→ stored investment logic / validation metric
→ what this changes or fails to change
→ next evidence needed
```

Do not merely append:
`투자 논리는 유지됩니다.`

Explain why.

---

# 13. Expectations must change the analytical threshold

Where market expectations are available:

### very_high / elevated
The AI may explain that execution evidence must be stronger to support the current valuation/expectation burden.

### low / depressed
The AI may explain what evidence would be necessary for rerating.

### balanced
Avoid forcing expectation analysis unless material.

Do not invent consensus or price targets.

---

# 14. Valuation reasoning

The AI may connect safe valuation context to operating evidence.

It may not:

- calculate a new multiple
- reverse-engineer EPS/BVPS
- invent fair value
- invent target prices
- equate low PER with cheap in cycle peaks
- change valuation status from working-capital or supply alone

Use existing industry valuation framework.

---

# 15. Supply / positioning reasoning

The Free Analyst may synthesize 1D/5D/20D flows freely inside the canonical participant taxonomy.

Example:

```text
short-term foreign selling is visible,
while 20-day institutional positioning is not aligned with the same direction;
this is tactical pressure rather than evidence of business deterioration.
```

Only if the underlying windows support it.

Still forbidden:

- residual-derived participants
- institution double counting
- timeless mixed-window statements
- fundamental logic change from supply alone

---

# 16. Working-capital reasoning

Inventory:

AI may discuss:
- relative growth vs Revenue/COGS
- whether inventory pressure appears to be accelerating or easing relative to operating scale
- why the relation matters to the stored logic

AI must preserve:
- total Inventory semantic
- correct PIT
- no Inventory Days / CCC
- no demand collapse/oversupply conclusion unless separately supported
- no hidden cash-flow inference

Trade AR:
user-visible remains OFF.

No AR/AP/DSO/DPO/CCC enrichment may leak.

---

# 17. Cash-flow reasoning

For selected current-formal FCF:

AI may connect:
- cash conversion
- capex burden
- operating execution
- investment logic verification

It may not:
- mix fiscal/YTD/FY periods
- use wrong PPE scope
- infer unsupplied FCF trends
- duplicate exact numbers unnecessarily

---

# 18. Price/RR reasoning

AI may interpret supplied RR/price structure.

It may not:
- invent new technical levels
- invent RSI/MACD
- invent target/stop
- claim business logic changed because price moved

Free analysis should focus on:
- current entry asymmetry
- confirmation/invalidation structure
- event risk

when the packet safely supplies those elements.

---

# 19. Macro reasoning

Macro temporal roles are immutable input semantics.

The Free Analyst may reason about real transmission channels only.

It may not:
- relabel prior-session/reference data as current
- create a new daily signal from ineligible reference facts
- generalize macro direction into a stock conclusion without a supplied channel

---

# 20. Unknown handling

Free analysis should use Unknowns actively.

Preferred structure:

```text
what is unknown
→ why it matters to the investment logic
→ what evidence would resolve it
```

Avoid:
- generic "추가 확인 필요"
- repeating next-check verbatim
- inventing unknowable data

---

# 21. Final Telegram rendering

After the structured analysis object passes support validation, render a concise Telegram message.

Renderer should be flexible.

Typical optional blocks:

```text
🎯 판단
🔎 핵심 근거
⚖️ 해석의 균형
💰 기대·Valuation / 가격
📊 포지셔닝
⚠️ 리스크
📌 다음 확인
```

Do not force every block.

The renderer should consume the validated analysis object, not reanalyze the raw packet.

---

# 22. Message goal

The final message should feel like:

```text
an analyst read the evidence,
decided what matters,
considered the opposing interpretation,
and told the user what would resolve the uncertainty
```

not:

```text
a template was filled with safe numbers
```

---

# 23. Benchmark set

Use the exact same immutable benchmark set from AI Analyst vNext.

Mandatory:

- KR: 8 messages from the 2026-08-24 19:34 immutable rehearsal
- US: the same 4 messages from the same 3 immutable packets used by vNext

No provider recollection.

Create a manifest tying each benchmark to:
- packet
- packet SHA/ref
- current AI output
- vNext output
- Free Analyst output

---

# 24. Primary 3-way quality comparison

For each benchmark item compare:

```text
A. Current validated AI
B. AI Analyst vNext
C. Evidence-Locked Free Analyst
```

Use the same facts.

Do not compare different market snapshots.

---

# 25. Deterministic reference

Also include deterministic fallback as a factual reference where available.

It is not part of the primary quality ranking.

Its role is:

```text
factual safety reference
```

---

# 26. Novel synthesis measurement

Measure whether the Free Analyst actually creates supported analysis beyond extractive span selection.

For each message record:

```text
claim_bearing_sentences
exact_source_span_sentences
novel_supported_synthesis_sentences
unsupported_synthesis_sentences
```

A novel supported synthesis is a sentence that:

- is not an exact source span from current AI/vNext
- has explicit evidence refs
- passes synthesis support validation
- adds analytical meaning rather than stylistic paraphrase

---

# 27. Free Analyst value-add gate

Set:

`FREE_ANALYST_VALUE_ADD = PASS / FAIL`

PASS requires:

- factual safety PASS
- unsupported synthesis = 0
- at least one meaningful new supported synthesis in a material/synthesis-eligible message
- majority of synthesis-eligible benchmark messages demonstrate material analytical value beyond vNext
- user-facing messages are not merely longer versions of vNext

Do not force novel synthesis into low-information packets.

Report the denominator:
`synthesis_eligible_messages`.

---

# 28. Analytical usefulness rubric

For each benchmark compare:

- priority judgment
- thesis linkage
- alternative interpretation quality
- uncertainty boundary
- expectations/valuation integration
- cross-horizon synthesis
- next-check quality
- concision
- industry specificity
- factual safety

Prefer explicit comparative notes over a fabricated aggregate score.

---

# 29. Human comparison report

The most important report must present exact text side-by-side:

```text
CURRENT_AI
VNEXT_AI
FREE_ANALYST
```

Then explain:

```text
What genuinely new analysis did Free Analyst add?
Was it supported?
Was it useful?
Did it become verbose?
Did vNext remain better?
```

This is mandatory.

---

# 30. Target style example — not a hard-coded output

A valid Free Analyst output may look conceptually like:

```text
🎯 판단
재고가 영업 규모보다 더 빠르게 쌓이는 모습은 현재 자료에서 뚜렷하지 않아
재고 자체가 투자 논리를 약화시키는 신호는 아니다.

🔎 핵심 근거
다만 메모리 재고 금액은 ASP와 제품 믹스의 영향을 받기 때문에
이 관계만으로 최종 수요 개선까지 확인할 수는 없다.
현재 기대가 높은 만큼 다음 판단은 재고보다 HBM 출하와 마진 지속성에 더 민감하다.

📌 다음 확인
HBM 출하/고객 채택과 마진이 현재 재고 관계를 실제 수익성 개선으로 연결하는지 확인.
```

Do not hard-code this wording or ticker logic.

---

# 31. Safety validator architecture

Add a separate shadow-only synthesis support validator.

It should validate:

- every analytical item has support type
- required evidence refs exist
- refs are eligible for that use
- numeric claims are canonical
- inference does not add unsupported premise
- alternative interpretation is labeled as interpretation
- temporal role preserved
- claim strength does not exceed evidence category
- user-visible forbidden fields remain blocked

Existing validators remain unchanged/strict.

---

# 32. No generic wildcard approval

Forbidden:

```text
if analysis_from_free_analyst:
    allow
```

or:

```text
if evidence_refs:
    allow
```

Support semantics must be typed.

A Fact ref alone does not automatically justify any inference.

---

# 33. Claim-strength rules

Implement bounded claim-strength rules, repository-equivalent.

Examples:

### Direct fact
Can use factual declarative language.

### Bounded inference
Must use interpretation language:
- 시사한다
- 현재 자료에서는
- 가능성이 있다
- 뚜렷하지 않다
- 단정하기 어렵다

### Alternative interpretation
Must be conditional.

### Unknown
Must not be resolved by inference.

Avoid over-mechanical phrase enforcement if semantic validator can support it, but preserve the strength hierarchy.

---

# 34. No hidden arithmetic

Free Analyst may not compute new values from packet numbers.

If it needs:
- spread
- percentage-point difference
- ratio
- trend relation

that derived relation must already exist in the packet.

Hard test required.

---

# 35. No external knowledge leakage

Create tests where the model plausibly "knows" something about the company that is absent from the packet.

Any such claim must be rejected.

Examples may include:
- customer names
- future products
- known industry events
- historical reputation

unless explicitly supplied.

---

# 36. No production coupling

The Free Analyst structured object, validators, and renderer must be shadow-only.

Hard targets:

```text
production packet changes = 0
production selector changes = 0
production AI prompt changes = 0
Telegram sends = 0
production DB mutation = 0
Pilot mutation = 0
schedule changes = 0
```

---

# 37. Current/vNext code isolation

Do not regress or rewrite the existing vNext branch unnecessarily.

Prefer an additive architecture:

```text
current AI
vNext
free analyst
```

available to the benchmark harness independently.

This is required for exact comparison.

---

# 38. Benchmark output length

Do not target a fixed reduction versus vNext.

The Free Analyst may be slightly longer if genuine synthesis adds value.

However:

- avoid returning to current AI verbosity
- avoid repeated numbers
- avoid duplicated caveats
- prefer 1–3 substantive analytical points

Report:
- current AI average chars
- vNext average chars
- Free Analyst average chars

---

# 39. Novel synthesis negative controls

Required tests:

### Unsupported causal leap
Fact:
inventory higher
Conclusion:
demand collapsed
→ REJECT

### Unsupported external fact
Packet lacks customer adoption.
Conclusion:
specific customer adoption accelerated
→ REJECT

### Hidden arithmetic
Two raw numbers supplied, relation absent.
AI computes percentage difference.
→ REJECT

### Stronger-than-evidence language
Ambiguous relation rendered as confirmed cause.
→ REJECT

### Temporal leakage
reference-lagging macro item rendered as today move.
→ REJECT

### Supply → fundamental state
foreign selling alone weakens business logic.
→ REJECT

---

# 40. Novel synthesis positive controls

Required tests:

### Thesis linkage
Fact + thesis driver → bounded investment implication
→ ACCEPT

### Expectation connection
very-high expectation + unresolved execution proof
→ higher verification threshold framing
→ ACCEPT

### Alternative interpretation
Inventory relation + ASP/mix uncertainty
→ two plausible interpretations with unresolved boundary
→ ACCEPT

### Cross-horizon positioning
1D/5D/20D facts → concise tactical-vs-medium-horizon synthesis
→ ACCEPT

---

# 41. KR mandatory benchmark cases

Use the immutable 19:34 packet and review at least:

- SK hynix
- Samsung Electronics
- POSCO Holdings
- Korean Re
- LS ELECTRIC
- Hanwha Aerospace
- Hyundai Glovis
- KR market digest

Focus on:

- Inventory synthesis
- industry-specific interpretation
- expectation threshold
- supply compression
- unknown framing
- alternative explanations

Do not hard-code output by ticker.

---

# 42. US mandatory benchmark cases

Use the same four vNext benchmark messages.

Focus on:

- FCF synthesis
- Inventory suppression/priority
- current-price RR ownership
- macro temporal context
- pre-profit/high-expectation analysis if present
- no hidden external knowledge

---

# 43. Free Analyst structured artifact

For every benchmark message, persist a sanitized structured analysis JSON.

Suggested path:

`artifacts/shadow/free-analyst/<benchmark-id>/analysis.json`

or repository-equivalent test artifact path.

Must include evidence refs but no secret provider payloads.

---

# 44. Explainability artifact

Create a compact per-message support map:

```text
final sentence
→ analysis item
→ support type
→ evidence refs
```

This is not private chain-of-thought.

It is a claim provenance map.

Mandatory for benchmark review.

---

# 45. Gates

Set:

```text
FREE_ANALYST_SHADOW = PASS / FAIL

FREE_ANALYST_FACT_BOUNDARY = PASS / FAIL

FREE_ANALYST_NOVEL_SYNTHESIS = PASS / FAIL

FREE_ANALYST_VALUE_ADD = PASS / FAIL

FREE_ANALYST_VS_VNEXT =
BETTER / MIXED / WORSE

FREE_ANALYST_PROMOTION_READY =
YES_PENDING_NATURAL_AND_SEPARATE_PROMOTION /
NO
```

No production promotion is allowed by this task.

---

# 46. Promotion decision rule

Do not promote automatically after benchmark PASS.

Wait for the 2026-08-25 09:20 natural review.

After that, a separate decision must choose among:

```text
A. current AI
B. vNext extractive/compressive
C. Evidence-Locked Free Analyst
D. hybrid:
   Free Analyst structured analysis
   + vNext concise renderer
```

The hybrid option must remain available.

A separate promotion instruction is required.

---

# 47. Hybrid architecture benchmark

Because the Free Analyst may reason well but write too much, also test:

```text
Free Analyst structured analysis
        ↓
vNext-style concise renderer
```

Compare this hybrid against the direct Free Analyst renderer.

Set:

`FREE_ANALYST_RENDERER_CHOICE = DIRECT / VNEXT_HYBRID / UNDECIDED`

Do not force a winner.

---

# 48. Human preference shortlist

For each benchmark message identify:

```text
best analytical reasoning
best final Telegram message
```

They may come from different variants.

This distinction is important.

---

# 49. Required tests

Add focused tests for:

- structured analysis schema
- evidence ref integrity
- support type classification
- bounded inference
- alternative interpretation
- expectation linkage
- thesis linkage
- cross-horizon supply synthesis
- unknown framing
- hidden arithmetic rejection
- external knowledge rejection
- unsupported causality rejection
- temporal leakage rejection
- Trade AR leak rejection
- exact Fact parity
- renderer isolation
- production isolation
- current/vNext regression

Run:

- focused tests
- full pytest
- Ruff
- `git diff --check`
- Knowledge parity
- Chart Knowledge parity
- Action/schema unchanged
- GitHub Actions on implementation/final branch tip

---

# 50. Required reports

Create:

1. `docs/reports/20260824-free-analyst-benchmark-manifest.md`
2. `docs/reports/20260824-free-analyst-structured-contract.md`
3. `docs/reports/20260824-free-analyst-synthesis-validator.md`
4. `docs/reports/20260824-free-analyst-kr-comparison.md`
5. `docs/reports/20260824-free-analyst-us-comparison.md`
6. `docs/reports/20260824-free-analyst-novel-synthesis-audit.md`
7. `docs/reports/20260824-free-analyst-claim-provenance.md`
8. `docs/reports/20260824-free-analyst-vnext-hybrid-comparison.md`
9. `docs/reports/20260824-free-analyst-safety-parity.md`
10. `docs/reports/20260824-free-analyst-value-add.md`
11. `docs/reports/20260824-free-analyst-readiness.md`
12. `docs/reports/20260824-free-analyst-artifact-index.md`

Recommended JSON:

`docs/reports/20260824-free-analyst-readiness.json`

---

# 51. Exact message comparison bundle

Create:

`docs/reports/20260824-free-analyst-message-benchmark.md`

For every benchmark include exact:

```text
CURRENT_AI
VNEXT_AI
FREE_ANALYST_DIRECT
FREE_ANALYST_VNEXT_HYBRID
DETERMINISTIC_REFERENCE
```

Then a concise comparison note.

Mandatory.

---

# 52. Machine-readable benchmark summary

Create:

`docs/reports/20260824-free-analyst-benchmark-summary.json`

Include:

```text
benchmark_count
synthesis_eligible_messages
current_ai_chars
vnext_chars
free_analyst_chars
hybrid_chars
novel_supported_synthesis_count
unsupported_synthesis_count
fact_mismatch
numeric_error
causal_error
temporal_error
trade_ar_leak
per_variant_preference
gates
```

---

# 53. Mandatory ZIP

Create:

`20260824-evidence-locked-free-analyst-shadow-bundle.zip`

Include all sanitized reports, exact message comparisons, readiness JSON, and claim-provenance artifacts.

Compute/report SHA-256.

---

# 54. Completion response

Return:

```text
INSTRUCTION_COMMIT = ...
BRANCH = ...
BASE_SHA = ...
IMPLEMENTATION_SHA = ...
REPORT_COMMIT = ...

BENCHMARK_MESSAGES = ...
SYNTHESIS_ELIGIBLE_MESSAGES = ...

FACT_MISMATCH = 0
UNSUPPORTED_NUMERIC_CLAIMS = 0
UNSUPPORTED_CAUSALITY = 0
TEMPORAL_VIOLATIONS = 0
TRADE_AR_LEAK = 0
HIDDEN_ARITHMETIC_REJECTIONS = ...
EXTERNAL_KNOWLEDGE_REJECTIONS = ...

NOVEL_SUPPORTED_SYNTHESIS = ...
UNSUPPORTED_SYNTHESIS = 0

CURRENT_AI_AVG_CHARS = ...
VNEXT_AI_AVG_CHARS = ...
FREE_ANALYST_DIRECT_AVG_CHARS = ...
FREE_ANALYST_HYBRID_AVG_CHARS = ...

FREE_ANALYST_SHADOW = ...
FREE_ANALYST_FACT_BOUNDARY = ...
FREE_ANALYST_NOVEL_SYNTHESIS = ...
FREE_ANALYST_VALUE_ADD = ...
FREE_ANALYST_VS_VNEXT = ...
FREE_ANALYST_RENDERER_CHOICE = ...

FREE_ANALYST_PROMOTION_READY =
YES_PENDING_NATURAL_AND_SEPARATE_PROMOTION / NO

PRODUCTION_PROMOTION = BLOCKED
PRODUCTION_MUTATION = 0
TELEGRAM_SEND = 0

OPEN_P0 = ...
OPEN_MATERIAL_P1 = ...
P2_BACKLOG = ...

ZIP = ...
ZIP_SHA256 = ...
```

---

# 55. Severity

## P0

- production behavior changes
- wrong Fact/number/period
- unsupported causal conclusion presented as fact
- temporal violation
- price/RR ownership regression
- valuation basis regression
- Trade AR/broad AR/AP leak
- external knowledge claim reaching accepted output

## P1

- fact-boundary validator allows unsupported synthesis
- hidden arithmetic reaches accepted output
- Free Analyst materially degrades factual parity
- systematic one-sided analysis without uncertainty handling
- hybrid/direct renderer drops material safety boundaries

## P2

- Free Analyst is too verbose
- some low-information messages show no synthesis
- stylistic repetition
- hybrid renderer usually wins
- vNext remains better on some message types

P2 does not block tomorrow's natural review.

---

# 56. Final philosophy

The purpose of this experiment is not to relax safety.

It is to move the freedom boundary.

Old boundary:

```text
Backend mostly decides the conclusion
AI rewrites it
```

New boundary:

```text
Backend decides what is true
AI decides what is important and what the evidence means
Validator decides whether the AI stayed inside the evidence
```

The model should be able to say something genuinely analytical that was not already written in a source sentence.

But every such statement must be traceable to evidence and appropriately bounded.

Success looks like:

```text
same verified facts
+ genuinely new supported synthesis
+ opposing interpretation considered where material
+ clearer investment relevance
+ explicit unresolved boundary
+ concise Telegram output
+ zero safety regression
```

Keep all of this shadow-only until the scheduled 2026-08-25 natural review is complete and a separate promotion decision is made.
