# thesis-monitor — Adaptive Renderer Selector v1 + End-to-End Free Analyst Shadow Integration

## Metadata

- Workstream: `AI Analyst Quality — Adaptive Renderer Selection`
- Instruction version: `1.0`
- Date: `2026-08-24 KST`
- Intended start: immediately after instruction commit, approximately `23:28 KST`
- Execution mode: `SHADOW_OFFLINE_ONLY`
- Production promotion: `BLOCKED_UNTIL_2026-08-25_US_NATURAL_REVIEW`
- Repository: `sskim-ai/thesis-monitor`

### Production main / operating

Current expected production main/operating:

`2e3e37cc75867d56a69211bbe93a3675cd87acd1`

IMPORTANT:
before implementation, resolve the actual latest safe `origin/main` and operating SHA.  
Do not force the SHA above if main legitimately advanced for an independent safety repair.

### Existing AI branches / evidence

Current extractive/compressive vNext branch:

`codex/ai-analyst-quality-vnext-shadow`

Known report commit:

`a8873b01474ca31c591a68069502aace48f37a0e`

Evidence-Locked Free Analyst branch:

`codex/evidence-locked-free-analyst-shadow`

Known SHAs:

```text
INSTRUCTION_COMMIT = 235b1914f965c2a194f939981aac24774e2f0969
BASE_SHA = a8873b01474ca31c591a68069502aace48f37a0e
IMPLEMENTATION_SHA = cccfb26e36b468eb0043aabf07eb9315f41b075d
REPORT_COMMIT = aad3041affd2036bc265e35d3ec1fe55ef97262b
```

Known shadow gates:

```text
FREE_ANALYST_SHADOW = PASS
FREE_ANALYST_FACT_BOUNDARY = PASS
FREE_ANALYST_NOVEL_SYNTHESIS = PASS
FREE_ANALYST_VALUE_ADD = PASS
FREE_ANALYST_VS_VNEXT = BETTER
FREE_ANALYST_RENDERER_CHOICE = VNEXT_HYBRID
FREE_ANALYST_PROMOTION_READY =
YES_PENDING_NATURAL_AND_SEPARATE_PROMOTION
```

Known benchmark:

```text
BENCHMARK_MESSAGES = 12
SYNTHESIS_ELIGIBLE_MESSAGES = 11

CURRENT_AI_AVG_CHARS = 863.50
VNEXT_AI_AVG_CHARS = 574.50
FREE_ANALYST_DIRECT_AVG_CHARS = 383.00
FREE_ANALYST_HYBRID_AVG_CHARS = 270.92

NOVEL_SUPPORTED_SYNTHESIS = 42
UNSUPPORTED_SYNTHESIS = 0

Human preference:
DIRECT = 3
HYBRID = 8
VNEXT/MINIMAL = 1
```

### Production feature state

- Production Assist: `OFF`
- Inventory user-visible mode: `SELECTIVE_INVENTORY`
- Exact Trade AR user-visible: `OFF_PENDING_NATURAL_PROOF`
- Phase 9.0E: `SELECTIVE_CURRENT_FORMAL_FULL_FCF`
- Public Action: `0.4.5`
- operationId: `20/20 unique`
- output schema: `4`

### Scheduled natural review

A separate one-shot review is already planned for:

`2026-08-25 09:20 KST`

This task must not interfere with that natural production proof.

---

# 0. Objective

The Free Analyst benchmark established that:

- free analytical synthesis adds real value
- direct rendering is best when interpretation boundaries matter
- hybrid rendering is usually best when analysis can be safely compressed
- minimal/vNext rendering remains useful for low-information or no-new-value cases

The unresolved production-design question is:

> Given a validated Free Analyst structured analysis object, which renderer should be selected automatically for this message?

Implement and test:

```text
Verified packet
        ↓
Free Analyst structured analysis
        ↓
Synthesis support validator
        ↓
Adaptive Renderer Selector v1
        ├─ DIRECT_ANALYST
        ├─ CONCISE_HYBRID
        └─ MINIMAL_VNEXT
        ↓
Selected renderer
        ↓
existing safety validators
        ↓
shadow would-send message
```

This task must remain shadow-only.

---

# 1. Work-instruction repository protocol

Store this exact instruction at:

`docs/work-instructions/20260824-2328-adaptive-renderer-selector-and-end-to-end-shadow-integration.md`

Before implementation:

```bash
git fetch origin
git status
git rev-parse HEAD
git rev-parse origin/main
git rev-parse origin/codex/evidence-locked-free-analyst-shadow
```

Then:

1. verify actual latest safe production main
2. verify actual latest Free Analyst branch tip
3. commit/push this exact instruction as a docs-only instruction commit
4. implementation must be based on the instruction commit SHA
5. create a dedicated branch from the latest safe Free Analyst shadow branch tip
6. no force push / no history rewrite
7. do not merge to production main

Recommended branch:

`codex/adaptive-renderer-selector-shadow`

If the Free Analyst branch legitimately advanced after `aad3041...`, use the actual latest safe branch tip and report the deviation.

---

# 2. Hard promotion freeze

This task MUST NOT:

- merge to main
- update operating
- restart production API for this feature
- change production AI selector
- change production prompt
- change production packet schema
- change production Telegram formatting
- change Production Assist
- change schedules
- run actual US/KR production tasks
- mutate production DB
- mutate Pilot
- mutate warnings
- mutate monitoring state
- mutate delivery rows
- mutate receipts
- enable Trade AR
- disable Inventory
- change Phase 9.0E
- change macro temporal logic
- change price/RR logic
- change valuation logic

Hard target:

```text
PRODUCTION_MUTATION = 0
TELEGRAM_SEND = 0
SCHEDULE_CHANGE = 0
MAIN_PROMOTION = 0
```

---

# 3. Design principle

Do not choose renderer based on ticker identity.

Do not choose renderer based on hard-coded industry names alone.

Choose based on the **validated analysis shape**.

The selector should answer:

```text
Does this analysis require interpretation balance or an explicit evidence boundary?
→ DIRECT

Is the conclusion clear and safely compressible without losing important boundaries?
→ HYBRID

Is there little or no new analytical value beyond a simple safe summary?
→ MINIMAL
```

---

# 4. Renderer enum

Use a typed enum or repository-equivalent:

```text
DIRECT_ANALYST
CONCISE_HYBRID
MINIMAL_VNEXT
```

Do not add more modes in v1 unless strictly necessary.

Do not expose the internal enum to end users.

---

# 5. Selector input

The selector should operate on the already validated Free Analyst structured analysis object, not raw provider payloads.

Allowed selector features may include:

```text
top_findings count
thesis_implications count
alternative_interpretations count
expectation_valuation_interaction count
positioning_synthesis count
unknowns count
next_checks count

support types used
claim strength
materiality
boundary presence
ambiguity / unresolved state
novel synthesis count
message plan
omitted blocks
renderer-specific safety requirements
```

The selector must not perform new financial interpretation itself.

---

# 6. Selector must remain deterministic

The renderer selector itself should be deterministic.

Preferred:

```text
typed rules / decision policy
```

Not preferred:

```text
another LLM call deciding which renderer it likes
```

The Free Analyst can reason freely.

Renderer selection should be auditable and reproducible.

---

# 7. DIRECT_ANALYST selection conditions

DIRECT should be favored when one or more materially important conditions are present.

Examples of valid triggers:

### A. Alternative interpretations matter

```text
alternative_interpretations count >= 1
and
dropping the alternative would materially bias the conclusion
```

Examples:
- Inventory relation with ASP/mix uncertainty
- operating improvement with a material counter-explanation
- conflicting business evidence

### B. Explicit uncertainty boundary matters

Example:

```text
the message must preserve:
"this suggests X,
but does not prove Y"
```

If Hybrid compression would remove the second clause or make the claim stronger, choose DIRECT.

### C. High expectation + unresolved execution

When:

```text
market expectation = elevated / very_high / speculative
```

and
the Free Analyst explicitly connects unresolved execution evidence to the required verification threshold.

If that connection is central, DIRECT may be preferable.

### D. Multiple material thesis implications

If the analysis needs two distinct material implications that cannot be safely collapsed.

### E. FCF / Inventory ambiguity

If safe user interpretation requires preserving:
- accounting relationship
- alternative explanation
- what remains Unknown

DIRECT should usually win.

---

# 8. CONCISE_HYBRID selection conditions

HYBRID should be favored when:

- Free Analyst generated useful analysis
- a clear primary conclusion exists
- safety boundary can be preserved in compressed form
- alternative interpretation is absent or non-material
- evidence is not heavily ambiguous
- next check is clear
- no important nuance is lost

Common shape:

```text
one main thesis implication
+ one evidence boundary
+ one next check
```

HYBRID should usually be the default for synthesis-eligible but straightforward messages.

---

# 9. MINIMAL_VNEXT selection conditions

MINIMAL should be favored when:

- no meaningful new analytical synthesis exists
- packet is low-information
- Free Analyst current balance = unresolved with no useful synthesis
- market digest has no new current observations
- material finding count is low
- most blocks would only repeat safe source facts
- current message should be short by design

MINIMAL must not be used merely to reduce token length when useful synthesis exists.

---

# 10. Hard "Direct-required" preservation rules

Even if HYBRID is shorter, it must not be selected if it would drop a material safety or analytical boundary.

Examples:

```text
alternative explanation required
causal boundary required
temporal qualification required
valuation basis caveat required
uncertainty necessary to prevent overclaim
```

Create an explicit:

`DIRECT_REQUIRED_REASON`

or repository-equivalent audit field.

---

# 11. Hard "Minimal-forbidden" rules

MINIMAL must not be selected when:

- a meaningful Free Analyst synthesis exists and materially changes understanding
- a high-expectation threshold connection exists
- a conflict/ambiguity requires explanation
- the main finding would otherwise be misleading
- Inventory/FCF requires a causal boundary
- a positioning synthesis meaningfully differs across horizons

Create an explicit:

`MINIMAL_FORBIDDEN_REASON`

if useful.

---

# 12. Selector decision record

Persist a shadow-only selector decision object:

```text
benchmark_id
selected_renderer
eligible_renderers[]
disallowed_renderers[]
selection_reasons[]
direct_required_reasons[]
minimal_forbidden_reasons[]
expected_information_loss[]
```

This must be auditable.

---

# 13. Information-loss audit

For every renderer candidate compare which analytical elements are retained/dropped.

Required element classes:

```text
primary conclusion
thesis linkage
alternative interpretation
uncertainty boundary
expectation/valuation connection
positioning synthesis
next check
material warning
```

Create:

```text
retained_elements[]
dropped_elements[]
material_dropped_elements[]
```

Hard gate:

`material_dropped_elements = 0`

for the selected renderer.

---

# 14. Human-preference benchmark

Use the prior human preference labels as an external benchmark target:

```text
DIRECT = 3
HYBRID = 8
MINIMAL/VNEXT = 1
```

Do NOT hard-code these labels into rules.

Run the selector blind to the preference label, then compare.

Report:

```text
exact_match
acceptable_alternative
material_mismatch
```

A selection can differ from human preference and still be acceptable if:
- no material information is lost
- reasoning is documented
- human review agrees it is a P2 preference difference

---

# 15. Selector performance gate

Set:

`ADAPTIVE_RENDERER_SELECTOR = PASS / FAIL`

PASS requires:

- 12/12 valid decisions
- material information loss = 0
- safety regressions = 0
- at least `10/12` exact human-preference matches

OR:

if exact matches are below 10/12:
- all nonmatches are documented as acceptable P2 alternatives
- no material mismatch
- human review agrees selector is usable

Report both exact match rate and semantic acceptable match rate.

---

# 16. Avoid overfitting to 12 messages

The benchmark is small.

Therefore add synthetic/fixture cases covering renderer boundaries.

Required fixture families:

### Direct-required
- material positive/negative alternative interpretation
- causal boundary
- high expectation + execution uncertainty
- ambiguous Inventory relationship
- FCF period-safe but interpretation-sensitive case

### Hybrid
- one clear thesis implication
- one clear next check
- no material opposing interpretation

### Minimal
- no new current evidence
- no material synthesis
- market digest reference-only state
- low-information packet

---

# 17. Selector negative controls

Required tests:

### Wrong compression
Alternative interpretation exists and is material.
Selector chooses HYBRID that drops it.
→ FAIL

### Overlong default
Clear single implication.
Selector always chooses DIRECT.
→ FAIL quality gate

### Minimal overuse
Novel thesis linkage exists.
Selector chooses MINIMAL.
→ FAIL

### Ticker hard-code
Specific ticker always maps to same renderer.
→ FAIL architecture review

### Industry hard-code
Renderer chosen only from industry label without analysis shape.
→ FAIL

---

# 18. Selector positive controls

Required:

### Ambiguous Inventory
→ DIRECT

### Clear FCF thesis linkage
→ HYBRID

### No new macro observation
→ MINIMAL

### Clear positioning synthesis with one caveat
→ HYBRID unless boundary loss occurs

### High expectation + two-sided execution interpretation
→ DIRECT

---

# 19. End-to-end shadow integration

After selector tests pass, wire the complete shadow path:

```text
immutable packet
→ Free Analyst
→ structured analysis
→ synthesis validator
→ Adaptive Renderer Selector
→ selected renderer
→ existing numeric validator
→ semantic validator
→ temporal validator
→ final-language validator
→ runtime-quality validator
→ shadow would-send bundle
```

This must be a real end-to-end shadow flow.

Do not assemble final messages manually in reports.

---

# 20. Fallback behavior in shadow architecture

Preserve the real production safety hierarchy conceptually.

Shadow evaluation should demonstrate:

```text
Free Analyst failure
→ no Free Analyst message

Free Analyst success + selector failure
→ selector-safe fallback candidate

selected renderer failure
→ safe existing vNext/current deterministic path

hard validation failure
→ deterministic fallback
```

No production selector changes in this task.

Define the future proposed hierarchy in documentation, but do not activate it.

---

# 21. Proposed future production hierarchy

Document only:

```text
production packet
→ Free Analyst
→ synthesis validator
→ Adaptive Renderer
→ hard validators
→ if PASS: AI-assisted message
→ if FAIL: deterministic fallback
```

Optional intermediate renderer fallback may be proposed only if it remains auditable.

Do not deploy.

---

# 22. Benchmark set

Use exactly the same immutable benchmark universe:

```text
KR = 8 messages
US = 4 messages
TOTAL = 12
```

No provider recollection.

No new live data needed.

Use the same benchmark manifest from the Free Analyst branch.

---

# 23. Required candidate generation

For every benchmark produce:

```text
CURRENT_AI
VNEXT_AI
FREE_ANALYST_DIRECT
FREE_ANALYST_HYBRID
MINIMAL_VNEXT
ADAPTIVE_SELECTED
DETERMINISTIC_REFERENCE
```

Where `MINIMAL_VNEXT` may reuse the existing safe concise renderer if semantically equivalent.

Do not fabricate a second minimal variant solely for the benchmark.

---

# 24. Exact selected message bundle

Create one exact bundle containing the selected Adaptive message for all 12 benchmark cases.

This is mandatory for human review.

The report must show:

```text
selected renderer
exact message
selection reasons
information retained
information omitted
```

---

# 25. Safety parity

Hard targets:

```text
FACT_MISMATCH = 0
UNSUPPORTED_NUMERIC_CLAIMS = 0
UNSUPPORTED_CAUSALITY = 0
TEMPORAL_VIOLATIONS = 0
TRADE_AR_LEAK = 0
HIDDEN_ARITHMETIC_ACCEPTED = 0
EXTERNAL_KNOWLEDGE_ACCEPTED = 0
MATERIAL_INFORMATION_LOSS = 0
```

---

# 26. Inventory checks

For Inventory-selected benchmark cases:

Selector must preserve:

- canonical total Inventory semantic
- relation meaning
- uncertainty boundary
- no demand-collapse claim
- no oversupply claim
- no hidden FCF inference
- no Trade AR leakage

Audit whether Direct or Hybrid was selected and why.

---

# 27. FCF checks

For selected FCF benchmark cases:

Preserve:

- correct fiscal/YTD/FY period semantics
- PPE-only scope where required
- no repeated exact number
- cash-conversion interpretation
- no unsupplied trend claim
- no valuation auto-change

---

# 28. Supply / positioning checks

If positioning synthesis is present:

Preserve:

- correct 1D/5D/20D window semantics
- participant taxonomy
- no residual-derived participant
- no institution double count
- no business-thesis change from supply alone

Audit whether MINIMAL would have lost useful cross-horizon context.

---

# 29. Macro temporal checks

For market digest and stock macro blocks:

- CURRENT remains current
- PRIOR_SESSION remains prior-session
- REFERENCE remains reference
- no false-current claim
- no reference-only today signal

Renderer choice must not alter temporal semantics.

---

# 30. Valuation / expectation checks

If Free Analyst made an expectation/valuation connection:

The selected renderer must preserve it if material.

Do not let HYBRID reduce:

```text
very high expectations
+ unresolved execution
→ higher confirmation threshold
```

to merely:

```text
valuation remains high
```

unless the exact evidence supports and preserves the same meaning.

No consensus invention.

---

# 31. Price/RR checks

Selected rendering must preserve:

- current-price ownership
- supported support/resistance language
- confirmation/invalidation semantics
- no fabricated targets/stops
- no thesis change from price alone

---

# 32. Message length

Report:

```text
CURRENT_AI_AVG_CHARS
VNEXT_AI_AVG_CHARS
FREE_ANALYST_DIRECT_AVG_CHARS
FREE_ANALYST_HYBRID_AVG_CHARS
ADAPTIVE_SELECTED_AVG_CHARS
```

Adaptive should normally remain far below current AI average.

Do not impose a rigid maximum.

Priority is:
no material information loss.

---

# 33. Analytical density

Create a useful non-score audit:

```text
analytical_points_per_message
novel_supported_synthesis_count
repeated_fact_lines
duplicate_caveats
numeric_recitation_lines
```

Target:
Adaptive should preserve Free Analyst value with fewer redundant lines.

---

# 34. Adaptive renderer value gate

Set:

`ADAPTIVE_RENDERER_VALUE_ADD = PASS / FAIL`

PASS requires:

- selected messages materially preserve Free Analyst reasoning
- selected messages are usually more concise than Direct
- no material boundary loss
- not merely choosing HYBRID for all messages
- at least two renderer modes are naturally selected
- preferably all three are exercised by benchmark or fixtures

---

# 35. End-to-end gate

Set:

`FREE_ANALYST_END_TO_END_SHADOW = PASS / FAIL`

PASS requires:

```text
packet
→ Free Analyst
→ structured analysis
→ support validator
→ selector
→ renderer
→ hard validators
→ final shadow message
```

for all 12 benchmark messages without manual intervention.

---

# 36. Proposed production integration manifest

Create a future-only integration manifest describing:

- new modules/files
- call order
- kill switches
- feature flags
- observability
- AI failure behavior
- renderer selection audit
- deterministic fallback behavior
- delivery isolation

Do not implement production wiring.

---

# 37. Feature flag proposal

Document a future safe feature flag, repository-equivalent:

```text
AI_ANALYST_MODE =
CURRENT
VNEXT
FREE_ANALYST_SHADOW
FREE_ANALYST_ADAPTIVE
```

Do not activate in production.

Do not change current public schema.

---

# 38. Observability proposal

For future production integration, define audit fields:

```text
analysis_mode
free_analyst_generated
synthesis_validation
selected_renderer
selection_reasons
hard_validation
fallback_reason
final_delivery_mode
```

Do not expose internal enum names to users.

---

# 39. Required focused tests

Add tests for:

- selector enum
- direct-required logic
- hybrid eligibility
- minimal eligibility
- material-information-loss detection
- deterministic reproducibility
- no ticker hard-code
- no industry-only hard-code
- ambiguity trigger
- expectation trigger
- Inventory trigger
- FCF trigger
- no-new-data minimal trigger
- end-to-end shadow path
- selected renderer validator parity
- production isolation

---

# 40. Full validation

Run:

- selector focused tests
- Free Analyst regression tests
- full pytest
- Ruff
- `git diff --check`
- Knowledge parity
- Chart Knowledge parity
- Action 0.4.5 unchanged
- operationId 20/20 unique
- schema unchanged
- implementation SHA GitHub Actions Test/Lint PASS
- final shadow branch tip Actions Test/Lint PASS

Production main does not need to move.

---

# 41. Required reports

Create:

1. `docs/reports/20260824-adaptive-renderer-selector-contract.md`
2. `docs/reports/20260824-adaptive-renderer-selector-decision-table.md`
3. `docs/reports/20260824-adaptive-renderer-human-preference-comparison.md`
4. `docs/reports/20260824-adaptive-renderer-information-loss-audit.md`
5. `docs/reports/20260824-adaptive-renderer-kr-benchmark.md`
6. `docs/reports/20260824-adaptive-renderer-us-benchmark.md`
7. `docs/reports/20260824-adaptive-renderer-end-to-end-shadow.md`
8. `docs/reports/20260824-adaptive-renderer-safety-parity.md`
9. `docs/reports/20260824-adaptive-renderer-production-integration-manifest.md`
10. `docs/reports/20260824-adaptive-renderer-readiness.md`
11. `docs/reports/20260824-adaptive-renderer-artifact-index.md`

Recommended JSON:

`docs/reports/20260824-adaptive-renderer-readiness.json`

---

# 42. Exact benchmark message report

Create:

`docs/reports/20260824-adaptive-renderer-message-benchmark.md`

For every benchmark case include exact:

```text
CURRENT_AI
VNEXT_AI
FREE_ANALYST_DIRECT
FREE_ANALYST_HYBRID
MINIMAL_VNEXT
ADAPTIVE_SELECTED
DETERMINISTIC_REFERENCE
```

Then:

```text
SELECTED_RENDERER
SELECTION_REASONS
HUMAN_PREFERENCE
MATCH_STATUS
MATERIAL_INFORMATION_LOSS
```

Mandatory.

---

# 43. Selector matrix report

Create a compact matrix:

| Benchmark | Selected | Human Pref | Exact Match | Acceptable Alt | Direct Required | Minimal Forbidden | Material Loss |
|---|---|---|---|---|---|---|---|

No hidden or unsupported scores.

---

# 44. Machine-readable summary

Create:

`docs/reports/20260824-adaptive-renderer-benchmark-summary.json`

Include:

```text
benchmark_count
renderer_counts
human_preference_counts
exact_match_count
acceptable_alternative_count
material_mismatch_count
avg_chars
safety
information_loss
end_to_end
gates
```

---

# 45. Mandatory ZIP

Create:

`20260824-adaptive-renderer-selector-shadow-bundle.zip`

Include all sanitized reports above.

Compute and report SHA-256.

---

# 46. Readiness gates

Set exactly:

```text
ADAPTIVE_RENDERER_SELECTOR =
PASS / FAIL

ADAPTIVE_RENDERER_HUMAN_ALIGNMENT =
PASS / FAIL

ADAPTIVE_RENDERER_INFORMATION_PRESERVATION =
PASS / FAIL

ADAPTIVE_RENDERER_SAFETY_PARITY =
PASS / FAIL

ADAPTIVE_RENDERER_VALUE_ADD =
PASS / FAIL

FREE_ANALYST_END_TO_END_SHADOW =
PASS / FAIL

ADAPTIVE_RENDERER_PROMOTION_READY =
YES_PENDING_20260825_NATURAL_AND_SEPARATE_PROMOTION /
NO
```

---

# 47. Human alignment gate

Set:

`ADAPTIVE_RENDERER_HUMAN_ALIGNMENT = PASS`

if either:

### Path A
```text
exact human-preference match >= 10/12
material mismatch = 0
```

or:

### Path B
```text
exact match < 10/12
but
every mismatch = acceptable P2 alternative
material mismatch = 0
documented human review agrees
```

Do not manufacture agreement.

---

# 48. Information preservation gate

Set:

`ADAPTIVE_RENDERER_INFORMATION_PRESERVATION = PASS`

only if:

```text
material_dropped_elements = 0
```

across all 12 selected messages.

---

# 49. Safety parity gate

Set:

`ADAPTIVE_RENDERER_SAFETY_PARITY = PASS`

only if:

```text
FACT_MISMATCH = 0
UNSUPPORTED_NUMERIC_CLAIMS = 0
UNSUPPORTED_CAUSALITY = 0
TEMPORAL_VIOLATIONS = 0
TRADE_AR_LEAK = 0
HIDDEN_ARITHMETIC_ACCEPTED = 0
EXTERNAL_KNOWLEDGE_ACCEPTED = 0
```

---

# 50. Promotion readiness rule

Even if every gate passes:

```text
PRODUCTION_PROMOTION = BLOCKED
```

until the separate 2026-08-25 US natural review is complete.

After the natural review, a separate promotion work instruction must choose and integrate the final production architecture.

Do not auto-promote.

---

# 51. Tomorrow decision matrix

Document the future decision, not execute it.

After the 09:20 natural review:

### If natural review has P0
Fix P0 first.

### If material P1
Bounded repair first.

### If P0/P1 = 0 and this task PASS
Next work:
`Free Analyst Adaptive Production Integration & Canary Promotion`

### If selector FAIL but Free Analyst reasoning PASS
Use:
`Free Analyst + fixed Hybrid`
or
perform bounded selector repair.

### If Free Analyst safety regresses
Do not promote any Free Analyst path.

---

# 52. Completion response

Return:

```text
INSTRUCTION_COMMIT = ...
BRANCH = ...
BASE_SHA = ...
IMPLEMENTATION_SHA = ...
REPORT_COMMIT = ...

BENCHMARK_MESSAGES = 12

SELECTED_DIRECT = ...
SELECTED_HYBRID = ...
SELECTED_MINIMAL = ...

HUMAN_PREF_DIRECT = 3
HUMAN_PREF_HYBRID = 8
HUMAN_PREF_MINIMAL = 1

EXACT_HUMAN_MATCH = .../12
ACCEPTABLE_ALTERNATIVES = ...
MATERIAL_MISMATCH = 0

FACT_MISMATCH = 0
UNSUPPORTED_NUMERIC_CLAIMS = 0
UNSUPPORTED_CAUSALITY = 0
TEMPORAL_VIOLATIONS = 0
TRADE_AR_LEAK = 0
HIDDEN_ARITHMETIC_ACCEPTED = 0
EXTERNAL_KNOWLEDGE_ACCEPTED = 0

MATERIAL_INFORMATION_LOSS = 0

CURRENT_AI_AVG_CHARS = ...
VNEXT_AI_AVG_CHARS = ...
FREE_ANALYST_DIRECT_AVG_CHARS = ...
FREE_ANALYST_HYBRID_AVG_CHARS = ...
ADAPTIVE_SELECTED_AVG_CHARS = ...

ADAPTIVE_RENDERER_SELECTOR = ...
ADAPTIVE_RENDERER_HUMAN_ALIGNMENT = ...
ADAPTIVE_RENDERER_INFORMATION_PRESERVATION = ...
ADAPTIVE_RENDERER_SAFETY_PARITY = ...
ADAPTIVE_RENDERER_VALUE_ADD = ...
FREE_ANALYST_END_TO_END_SHADOW = ...

ADAPTIVE_RENDERER_PROMOTION_READY =
YES_PENDING_20260825_NATURAL_AND_SEPARATE_PROMOTION / NO

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

# 53. Severity

## P0

- production mutation
- production main promotion
- wrong Fact/number/period
- unsupported causality
- temporal violation
- Trade AR/broad AR/AP leak
- hidden external knowledge accepted
- hidden arithmetic accepted
- material safety boundary dropped

## P1

- selector systematically drops useful synthesis
- material information loss
- selector overfits tickers
- direct/hybrid/minimal rule causes factual parity regression
- end-to-end shadow path cannot reproduce validated outputs

## P2

- human preference mismatch with no material information loss
- slightly overlong Direct selection
- slightly overcompressed but still complete Hybrid
- stylistic preference difference
- selector threshold tuning opportunity

P2 does not block tomorrow's natural production review.

---

# 54. Final principle

The Free Analyst should own the reasoning.

The Adaptive Renderer should own the compression level.

The selector should be deterministic and auditable.

The final architecture under test is:

```text
Backend:
What is true

Free Analyst:
What matters and what the evidence means

Synthesis Validator:
Whether the interpretation is supported

Adaptive Renderer:
How much of that analysis must be shown

Hard Validators:
Whether the final message stayed inside fact/semantic/temporal boundaries

Deterministic Fallback:
Safe delivery if AI path fails
```

This task should finish the shadow architecture tonight without changing tomorrow morning's production proof baseline.
