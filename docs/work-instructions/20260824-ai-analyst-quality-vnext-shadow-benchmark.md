# thesis-monitor — AI Analyst Quality vNext Shadow Benchmark

## Metadata

- Workstream: `AI Analyst Quality vNext`
- Instruction version: `1.0`
- Date: `2026-08-24 KST`
- Execution mode: `SHADOW_OFFLINE_ONLY`
- Promotion mode: `NO_PRODUCTION_PROMOTION_BEFORE_2026-08-25_US_NATURAL_REVIEW`
- Repository: `sskim-ai/thesis-monitor`
- Intended current main/operating:
  `2e3e37cc75867d56a69211bbe93a3675cd87acd1`
- IMPORTANT:
  resolve actual latest safe `origin/main` before implementation.
- Current Production Assist:
  `OFF`
- Current Inventory mode:
  `SELECTIVE_INVENTORY`
- Exact Trade AR user-visible:
  `OFF_PENDING_NATURAL_PROOF`
- Phase 9.0E:
  `SELECTIVE_CURRENT_FORMAL_FULL_FCF`
- Scheduled natural review already planned:
  `2026-08-25 09:20 KST US Morning Natural Multi-Proof Review`

This task improves the **analytical value-add and compression quality** of AI-assisted messages without weakening factual, numeric, semantic, temporal, or causal safety.

The key problem is not correctness. Current AI output is factually safe but too close to deterministic rendering.

Target:

```text
deterministic facts
+ strict claim boundary
+ dynamic analytical prioritization
+ thesis linkage
+ cross-horizon synthesis
+ expectation/valuation connection
+ concise unknown framing
```

Do not turn the AI into a freer numeric generator.

---

# 0. Work-instruction repository protocol

Store this exact instruction at:

`docs/work-instructions/20260824-ai-analyst-quality-vnext-shadow-benchmark.md`

Before implementation:

```bash
git fetch origin
git status
git rev-parse HEAD
git rev-parse origin/main
```

Then:

1. verify actual latest safe main/operating SHA
2. commit/push this instruction as a docs-only instruction commit
3. record instruction path / commit SHA / version / base SHA
4. create a dedicated feature branch
5. no force push / history rewrite
6. do not merge/promote to runtime main before the 2026-08-25 US natural review completes

Recommended branch:

`codex/ai-analyst-quality-vnext-shadow`

---

# 1. Hard promotion freeze

This task may implement and test code on a feature branch.

It must NOT:

- merge to main
- update operating
- restart production API
- change production AI preference
- change Production Assist
- change schedules
- change Telegram delivery
- change feature modes
- mutate DB/Pilot
- enable Trade AR
- disable Inventory
- change macro temporal behavior
- change packet schemas
- change numeric/semantic validators
- loosen claim ownership
- loosen unsupported causality controls

Promotion is explicitly deferred until after the 2026-08-25 morning natural proof review.

---

# 2. Problem statement

Current AI-assisted messages are safe but too deterministic-like.

Observed issues include:

- same section order across very different industries
- excessive numeric recitation
- insufficient prioritization
- weak explicit connection from Fact → investment logic
- weak expectation/valuation synthesis
- duplicate `다음 확인` and `미확인`
- supply paragraphs that repeat 1D/5D/20D numbers instead of synthesizing time horizons
- identical rhythm across memory, insurance, defense, power equipment, logistics, etc.
- AI output often functions as a natural-language renderer rather than an analyst

The objective is not more flourish.

The objective is:

```text
more judgment structure
with the same factual boundary
```

---

# 3. Safety ownership remains unchanged

Backend remains authoritative for:

- numbers
- calculations
- Fact IDs
- relation IDs
- periods
- currencies
- security basis
- price/RR
- valuation ownership
- macro temporal role
- investor-flow participant taxonomy
- Inventory/FCF selection eligibility

Validators remain authoritative for:

- numeric claim validation
- semantic claim validation
- temporal validity
- unsupported causality
- final-language restrictions
- fact ownership

AI is allowed more freedom only in:

- priority selection
- ordering
- synthesis
- explanation
- omission of low-value sections
- concise thesis linkage
- concise unknown framing

---

# 4. Benchmark evidence set

Use immutable captured production/rehearsal packets only.

Mandatory KR benchmark:

`2026-08-24-kr-live-rehearsal-193419`

Mandatory KR names:
use actual packet universe, not hard-coded names.

Include at minimum the names where prior validated output demonstrated different analytical shapes, such as:
- memory
- insurance
- industrial/materials
- power equipment
- defense
- logistics

Mandatory US benchmark:

Select at least 3 immutable previously validated US packets, including where available:
- one FCF-heavy name
- one Inventory-eligible or Inventory-suppressed name
- one current-price/RR-sensitive name

Do not recollect providers.

Create a benchmark manifest.

---

# 5. Three-way comparison

For every benchmark message produce:

```text
A. deterministic fallback
B. current validated AI
C. AI Analyst Quality vNext
```

All three must consume the same immutable packet.

This is mandatory.

Do not compare different market snapshots.

---

# 6. Core output model — dynamic analytical structure

Replace the assumption that every message must contain every section.

The vNext AI should choose the smallest useful structure from the available evidence.

Recommended semantic blocks:

```text
🎯 오늘 판단
🔎 왜 중요한가
📈 사업/실적
💰 가격/Valuation
📊 수급/포지셔닝
⚠️ 리스크/경고
📌 다음 확인
```

These are optional blocks, not mandatory templates.

Rules:

- `오늘 판단` should normally exist
- other blocks appear only if materially useful
- `미확인` should not duplicate `다음 확인`
- empty or low-value sections should be omitted
- do not invent alternate headings merely for stylistic variety

---

# 7. Analytical value-add contract

For each stock, AI vNext should perform at least one of the following if evidence permits:

1. `priority_selection`
2. `thesis_linkage`
3. `cross_horizon_synthesis`
4. `expectation_valuation_connection`
5. `unknown_resolution_framing`

Record which ones were actually used.

If none can be supported:
AI should remain close to deterministic and report low value-add rather than fabricate insight.

---

# 8. Priority selection

The AI should identify the top 1–3 relevant facts.

Avoid treating every available field as equally important.

Example behavior:

Bad:
```text
all 1D/5D/20D supply numbers
+ all price bands
+ all valuation cautions
+ all unknowns
```

Better:
```text
one operating issue
+ one price/expectation issue
+ one next verification item
```

Backend still controls what facts are eligible.

---

# 9. Thesis linkage

For a material business/financial fact, connect:

```text
Fact
→ what it means for the existing investment logic
→ what it does NOT yet prove
```

Example pattern:

```text
Inventory growth < COGS growth
→ inventory pressure is not obviously worsening
→ but this does not prove end-demand strength because ASP/mix can affect inventory value
```

Do not turn this example into ticker-specific hard-coded logic.

---

# 10. Cross-horizon supply synthesis

Do not mechanically enumerate all 1D/5D/20D values when a shorter synthesis is sufficient.

Allowed synthesis:

```text
short-term selling
but medium-term institutional positioning still positive
→ tactical pressure, not fundamental evidence
```

Only if exact underlying windows support it.

When numeric detail matters, keep the minimal supporting numbers.

Hard restrictions remain:

- no residual-derived participant
- no institution double count
- no timeless mixed-window label
- supply alone cannot strengthen/weaken business logic

---

# 11. Expectation / valuation connection

When market expectations are `elevated`, `very_high`, or `speculative`, AI should explain why the next proof threshold is higher.

When expectations are low/depressed, explain what evidence would be needed for rerating.

Do not invent consensus.

Do not invent target price.

Do not reverse-engineer denominators.

Allowed analytical connection:

```text
high expectations
+ current execution uncertainty
→ operational confirmation has more valuation importance
```

---

# 12. Price/RR integration

Current price/RR should not be dumped as a raw paragraph if the analytical conclusion can be stated more clearly.

Keep exact levels only when they materially change the judgment.

Prefer:

```text
current price sits well above dynamic support and below resistance;
business logic may be intact but entry margin is narrower/wider
```

Only when exact supported price facts justify it.

Do not fabricate new levels or technical indicators.

---

# 13. Inventory / FCF synthesis

When Inventory is selected:

AI should explain what the relation indicates and what remains unknown.

Do not:
- claim demand collapse
- claim oversupply
- claim cash-flow deterioration unless separately supported

When FCF is selected:

connect to:
- cash conversion
- capex burden
- thesis verification

without repeating the same exact number multiple times.

If both Inventory and FCF exist:
honor existing redundancy/priority logic.

---

# 14. Unknown / next-check deduplication

Current issue:
`다음 확인` and `미확인` often repeat the same sentence.

vNext rule:

```text
next_check
= the concrete next observable item

unknown
= only a distinct unresolved uncertainty that cannot yet be converted into a next-check item
```

If identical:
render only one.

Target:

`duplicate_next_check_unknown = 0`

---

# 15. Market digest vNext

The market digest should prioritize:

1. new current observations
2. relevant prior-session context
3. reference-lagging data only when structurally useful

Do not expand old/reference data just to fill the digest.

Dynamic digest may be shorter.

Do not break macro temporal contracts.

---

# 16. Industry-specific analytical rhythm

The output should reflect actual evidence shape, not cosmetic synonym changes.

Examples:

### Memory
- cycle / ASP / mix / inventory / HBM execution

### Insurance
- underwriting / capital / reserve / ROE context
- no manufacturing FCF framing

### Defense / EPC
- backlog → revenue → working capital / cash conversion

### Logistics
- volume / freight / asset efficiency

### Power equipment
- order conversion / margin / cash collection

Do not hard-code these exact narratives per ticker.

Use industry reasoning contracts already present.

---

# 17. Concision target

Target message length reduction:

`20%–35%` versus current AI average

but only if meaning is preserved.

Do not compress by deleting the core conclusion or required safety caveat.

Report:

- current AI characters
- vNext characters
- reduction %
- facts retained
- analytical value-add blocks

---

# 18. Numeric-density target

Measure visible numeric token density.

The vNext should usually reduce unnecessary numeric repetition.

Do not set a rigid universal percentage gate.

Instead flag messages where:
- many numbers remain
- but the analytical conclusion does not depend on them

---

# 19. Deterministic differentiation gate

Create a machine-readable gate:

`AI_ANALYST_VALUE_ADD = PASS / FAIL`

PASS requires:

- factual parity PASS
- no unsupported claims
- at least one supported analytical value-add operation
- output is materially more useful than deterministic fallback
- not merely synonym/paraphrase substitution

Also create:

```text
VALUE_ADD_TYPES = [
  priority_selection,
  thesis_linkage,
  cross_horizon_synthesis,
  expectation_valuation_connection,
  unknown_resolution_framing
]
```

per message.

---

# 20. Safety gates

Hard targets:

```text
fact_mismatch = 0
unsupported_numeric_claim = 0
unsupported_causality = 0
temporal_violation = 0
price_ownership_violation = 0
valuation_basis_violation = 0
Trade_AR_user_visible_leak = 0
```

Any hard safety regression blocks readiness.

---

# 21. AI/fallback factual parity

Compare exact underlying claims for:

- business status
- warnings
- price
- valuation
- cash flow
- Inventory
- supply
- macro
- next checks

Target mismatch:

`0`

Prose may be structurally different.

---

# 22. Current AI vs vNext quality rubric

For each benchmark message score/label:

- prioritization
- thesis linkage
- compression
- non-duplication
- cross-horizon synthesis
- expectation linkage
- industry specificity
- readability
- analytical usefulness

Do not use a made-up composite score unless the repository already has a supported quality scoring contract.

Prefer explicit PASS/FAIL criteria and side-by-side notes.

---

# 23. Human-readable benchmark report

Create a report showing for each selected benchmark:

```text
Deterministic
Current AI
vNext AI
Why vNext is better/worse
Any safety changes
```

Include exact text.

---

# 24. KR 19:34 benchmark mandatory review points

Review specifically:

- market digest temporal compression
- SK hynix Inventory interpretation
- Samsung Inventory interpretation
- POSCO Inventory interpretation
- supply horizon compression
- duplicated next-check/unknown removal
- dynamic section omission

Do not alter the underlying facts.

---

# 25. US benchmark mandatory review points

Review:

- FCF period labeling
- current-price RR ownership
- Inventory suppression where FCF is stronger
- no duplicated FCF sentence
- macro temporal role
- AI vs fallback factual parity

---

# 26. Runtime-quality validator changes

Do NOT loosen existing safety validators.

If needed, add a separate vNext quality validator that checks:

- duplicate next-check/unknown
- redundant sections
- excessive numeric recitation
- missing thesis linkage where material facts exist
- deterministic-like paraphrase only

This validator should be advisory/shadow for this phase.

It must not affect production.

---

# 27. Prompt/contract design principle

Avoid asking the model to "be more insightful" in an unconstrained way.

Provide explicit structured objectives:

```text
select
connect
synthesize
omit
explain boundary
```

The prompt should tell AI:

- use only supplied facts
- do not restate every number
- rank material facts
- connect facts to investment logic
- state what the fact does not prove
- omit irrelevant sections
- avoid duplicate next-check/unknown
- compress supply horizons
- preserve uncertainty

---

# 28. No hidden new calculations

AI vNext may not create new arithmetic unless the value is already supplied as canonical/derived evidence.

If a comparative relation is needed:
backend must supply it.

No mental math added only for vNext.

---

# 29. No production influence

During this task:

```text
vNext production selection = 0
vNext Telegram sends = 0
vNext DB mutation = 0
vNext packet mutation = 0
```

Use shadow/offline output only.

---

# 30. Optional blind comparison

If practical, add a lightweight blind comparison harness:

- randomize labels A/B/C
- compare current AI vs vNext on analytical usefulness
- reveal identity after review

This may remain manual and report-only.

No need for external evaluators.

---

# 31. Readiness states

Set:

```text
AI_ANALYST_VNEXT_SHADOW =
PASS / FAIL

AI_ANALYST_VALUE_ADD =
PASS / FAIL

AI_ANALYST_SAFETY_PARITY =
PASS / FAIL

AI_ANALYST_PROMOTION_READY =
YES_PENDING_NATURAL / NO
```

`YES_PENDING_NATURAL` means:
the feature branch is technically ready but must not be merged until the scheduled 2026-08-25 US natural review has completed without a new material blocker.

---

# 32. Promotion gate after tomorrow's natural review

Do not perform this automatically.

After the 2026-08-25 natural review, promotion may be considered only if:

```text
OPEN_P0 = 0
OPEN_MATERIAL_P1 = 0

US_PRODUCTION_NATURAL = LIVE_PASS
US_AI_COMPATIBILITY_NATURAL = LIVE_PASS or safe supported state
MACRO_TEMPORAL_NATURAL = LIVE_PASS or no material blocker

AI_ANALYST_VNEXT_SHADOW = PASS
AI_ANALYST_VALUE_ADD = PASS
AI_ANALYST_SAFETY_PARITY = PASS
```

If tomorrow's natural review exposes a P0/P1:
fix that first.

---

# 33. Required tests

Add focused tests for:

- dynamic section omission
- duplicate next-check/unknown removal
- supply cross-horizon synthesis
- high-expectation thesis linkage
- Inventory boundary explanation
- FCF concise synthesis
- no new arithmetic
- no unsupported causality
- no Trade AR leak
- factual parity
- deterministic differentiation gate

Run:

- focused tests
- full pytest
- Ruff
- `git diff --check`
- Knowledge parity
- Action/schema unchanged

---

# 34. Required reports

Create:

1. `docs/reports/20260824-ai-analyst-vnext-benchmark-manifest.md`
2. `docs/reports/20260824-ai-analyst-vnext-contract.md`
3. `docs/reports/20260824-ai-analyst-vnext-kr-193419-comparison.md`
4. `docs/reports/20260824-ai-analyst-vnext-us-comparison.md`
5. `docs/reports/20260824-ai-analyst-vnext-safety-parity.md`
6. `docs/reports/20260824-ai-analyst-vnext-value-add.md`
7. `docs/reports/20260824-ai-analyst-vnext-quality-regression.md`
8. `docs/reports/20260824-ai-analyst-vnext-readiness.md`
9. `docs/reports/20260824-ai-analyst-vnext-artifact-index.md`

Recommended JSON:

`docs/reports/20260824-ai-analyst-vnext-readiness.json`

---

# 35. Exact benchmark message bundle

Create:

`docs/reports/20260824-ai-analyst-vnext-message-benchmark.md`

For each benchmark item include:

```text
DETERMINISTIC
CURRENT_AI
VNEXT_AI
```

with exact full text.

This report is mandatory.

---

# 36. Mandatory ZIP

Create:

`20260824-ai-analyst-quality-vnext-shadow-bundle.zip`

Include sanitized:

- benchmark manifest
- exact message benchmark
- KR comparison
- US comparison
- safety parity
- value-add report
- quality regression
- readiness
- readiness JSON
- artifact index

Report SHA-256.

---

# 37. Completion response

Return:

```text
INSTRUCTION_COMMIT = ...
BRANCH = ...
BASE_SHA = ...
IMPLEMENTATION_SHA = ...

BENCHMARK_KR_MESSAGES = ...
BENCHMARK_US_MESSAGES = ...

FACT_MISMATCH = 0
UNSUPPORTED_NUMERIC_CLAIMS = 0
UNSUPPORTED_CAUSALITY = 0
TEMPORAL_VIOLATIONS = 0
TRADE_AR_LEAK = 0

DUPLICATE_NEXT_CHECK_UNKNOWN_BEFORE = ...
DUPLICATE_NEXT_CHECK_UNKNOWN_AFTER = 0

CURRENT_AI_AVG_CHARS = ...
VNEXT_AI_AVG_CHARS = ...
COMPRESSION = ...%

VALUE_ADD_PRIORITY_SELECTION = ...
VALUE_ADD_THESIS_LINKAGE = ...
VALUE_ADD_CROSS_HORIZON_SYNTHESIS = ...
VALUE_ADD_EXPECTATION_VALUATION = ...
VALUE_ADD_UNKNOWN_FRAMING = ...

AI_ANALYST_VNEXT_SHADOW = ...
AI_ANALYST_VALUE_ADD = ...
AI_ANALYST_SAFETY_PARITY = ...
AI_ANALYST_PROMOTION_READY = ...

PRODUCTION_PROMOTION = BLOCKED_UNTIL_20260825_NATURAL_REVIEW
PRODUCTION_MUTATION = 0
TELEGRAM_SEND = 0

OPEN_P0 = ...
OPEN_MATERIAL_P1 = ...
P2_BACKLOG = ...

ZIP = ...
ZIP_SHA256 = ...
REPORT_COMMIT = ...
```

---

# 38. Severity

## P0

- wrong Fact/number/period
- unsupported causal conclusion
- temporal violation
- price/RR ownership regression
- valuation basis regression
- Trade AR user-visible leak
- production influence

## P1

- factual parity mismatch
- vNext removes a material safety caveat
- prompt causes repeated unsupported claims
- major quality regression vs current AI

## P2

- message still somewhat template-like
- compression below target
- benign section-order repetition
- stylistic awkwardness
- value-add weak in low-information packets

P2 does not require core rollback.

---

# 39. Final principle

Do not make the AI "more free."

Make it **more selective and more analytical** inside a strict fact boundary.

Target transformation:

```text
Current AI
= safe deterministic-like renderer

vNext
= safe analyst that selects, connects, synthesizes, and omits
```

The proof is not prettier prose.

The proof is:

```text
same facts
fewer unnecessary words
less numeric recitation
clearer investment-logic linkage
less duplication
more useful prioritization
zero safety regression
```

Keep this shadow-only until tomorrow's natural US proof is complete.
