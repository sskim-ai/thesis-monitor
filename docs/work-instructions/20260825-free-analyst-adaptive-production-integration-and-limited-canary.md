# thesis-monitor — Free Analyst + Adaptive Renderer Production Integration & Limited Canary

## Metadata

- Workstream: `COMMON_AI_CORE_V1_PRODUCTION_INTEGRATION`
- Instruction version: `1.0`
- Date: `2026-08-25 KST`
- Authoring context: approximately `11:25 KST`
- Repository: `sskim-ai/thesis-monitor`
- Task type: `PRODUCTION_INTEGRATION_WITH_FAIL_CLOSED_LIMITED_CANARY`
- Open Research production integration: `OUT_OF_SCOPE`
- Production Assist: preserve current semantics; do not bypass
- Public Action: `0.4.5`
- operationId: `20/20 unique`
- schema: `4`

### Current expected production main / operating

`f7d2552185ff2ff6d932337e7555ce02f87fa613`

This SHA contains the deployed US directional-relation provenance repair.

Before implementation, resolve and use the actual latest safe `origin/main` and operating SHA.
Do not force the SHA above if main legitimately advanced for an independent safety repair.

### Proven shadow components

Evidence-Locked Free Analyst:
- shadow benchmark: PASS
- Fact boundary: PASS
- novel supported synthesis: PASS
- value-add: PASS

Adaptive Renderer:
- selector: PASS
- human benchmark alignment: 12/12
- material information loss: 0
- end-to-end shadow: PASS

US natural-packet adapter:
- `FREE_ANALYST_US_NATURAL_ADAPTER = PASS_SHADOW`
- `FREE_ANALYST_US_14_MESSAGE_REPLAY = PASS`
- `FREE_ANALYST_VALIDATED = 14`
- `FREE_ANALYST_FALLBACK = 0`

Open Research:
- sidecar preservation: PASS
- production integration is intentionally excluded from this task

### Latest triggering production repair

Known Track A implementation / current main:

`f7d2552185ff2ff6d932337e7555ce02f87fa613`

Known Track B shadow implementation:

`2123cd026467a80b8bee6ab52dba2ef640f5861e`

Known Track B report:

`d70313991c3cd2e4b4e54200aedb612ec772bcb6`

Triggering natural US packet:

`2026-08-25-us-run-37-7e04812311c2`

Known combined replay:

```text
production AI hard errors = 0
Free Analyst = 14/14
Open Research sidecar preserved = PASS
Adaptive Renderer = 14/14
Fact mismatch = 0
Unsupported causality = 0
Temporal violation = 0
Trade AR leak = 0
Material information loss = 0
```

### Known P2 backlog

Separate runtime-quality observations from the prior current-AI path:

- Korean current-price particle/grammar errors: `12`
- substantive repeated price wording: `5`

These are not P0/P1 but may cause fail-closed fallback.

This task must observe whether the Free Analyst + Adaptive path naturally removes or reproduces these issues.
Do not weaken runtime-quality validation merely to make the new path pass.

---

# 0. Objective

Integrate the already-proven common AI reasoning stack into the production codebase:

```text
Verified Production Packet
        ↓
Free Analyst
        ↓
Synthesis Support Validator
        ↓
Adaptive Renderer Selector
        ↓
Selected Renderer
        ↓
Existing Numeric / Semantic / Temporal /
Fact-Ownership / Final-Language / Runtime-Quality Validators
        ↓
AI-assisted Final Candidate
        ↓
Packet-bound Delivery Selection
```

with strict fallback:

```text
any AI-stage failure
→ existing deterministic fallback
```

The production integration must remain **research-independent**.

Do NOT integrate:
- Open Research Agent
- Event Attribution
- research triggers
- research sidecar retrieval

The target is to complete the **Common AI Reasoning Core v1**, not the Common Open Research stack.

---

# 1. Work-instruction repository protocol

Store this exact instruction at:

`docs/work-instructions/20260825-free-analyst-adaptive-production-integration-and-limited-canary.md`

Before implementation:

```bash
git fetch origin
git status
git rev-parse origin/main
git rev-parse origin/codex/us-natural-packet-free-analyst-adapter-repair
git rev-parse origin/codex/adaptive-renderer-selector-shadow
git rev-parse origin/codex/evidence-locked-free-analyst-shadow
```

Then:

1. verify actual latest safe production main
2. verify actual latest relevant shadow branch tips
3. commit/push this exact instruction as a **docs-only instruction commit**
4. record instruction path / commit SHA / version / implementation base SHA
5. create a dedicated integration branch from latest safe production main
6. port only the minimal proven Free Analyst / adapter / Adaptive Renderer implementation needed for production
7. do not merge Open Research code
8. no force push / history rewrite

Recommended branch:

`codex/free-analyst-adaptive-production-integration`

---

# 2. Integration principle — port, do not drag the entire shadow history

Do not merge whole shadow branches blindly.

The shadow branches contain:
- benchmark harnesses
- Open Research experiments
- report-only code
- shadow-only artifacts

Identify and port the minimum production-relevant units:

```text
Free Analyst structured analysis contract
Free Analyst natural packet adapter
synthesis support validator
Adaptive Renderer selector
Direct/Hybrid/Minimal renderers
claim provenance mapping
production-safe orchestration adapter
focused tests
```

Keep benchmark/report tooling separate unless needed for regression tests.

Document exact source commits/files used.

---

# 3. Hard prohibitions

Do NOT:

- integrate Open Research
- integrate Event Attribution
- create web/news searches in production
- enable Trade AR
- change Inventory selection logic
- change Phase 9.0E
- change Macro temporal logic
- change price/RR ownership rules
- change valuation basis rules
- loosen numeric validator
- loosen semantic validator
- loosen temporal validator
- loosen causal validator
- loosen final-language validator
- loosen runtime-quality validator
- change notification/receipt semantics
- add duplicate delivery paths
- send test Telegram messages manually
- rerun production jobs manually
- mutate production DB during replay
- change KRX/night-futures schedules
- change current meaning of Production Assist without an explicit control-plane audit

---

# 4. First step — control-plane audit

Before wiring user-visible behavior, identify the exact current meaning of:

```text
Production Assist = OFF
```

Trace:

```text
config
→ candidate generation
→ validation
→ final selection
→ delivery
```

Classify one:

## Branch A
Production Assist OFF means:
AI may be generated/validated internally but user-visible AI selection is disabled.

## Branch B
Production Assist OFF means something else and does not prohibit the intended canary.

## Branch C
Semantics are ambiguous / multiple gates conflict.

Required behavior:

- never bypass the authoritative gate
- document the actual semantics
- if Branch A:
  - production integration may still merge
  - limited canary must remain `READY_NOT_ARMED`
  - do not flip Production Assist in this task
- if Branch B:
  - limited canary may be armed using the supported production selector
- if Branch C:
  - stop user-visible canary activation
  - repair/control-plane clarification becomes P1
  - integration code may continue shadow/replay-only if safe

Set:

`PRODUCTION_ASSIST_CONTROL_PLANE = A / B / C`

---

# 5. Common production mode contract

Introduce or normalize a typed internal mode, repository-equivalent to:

```text
CURRENT
FREE_ANALYST_ADAPTIVE_CANARY
FREE_ANALYST_ADAPTIVE
```

Requirements:

- default remains compatible with current production behavior until explicit promotion step
- `FREE_ANALYST_ADAPTIVE_CANARY` is bounded
- `FREE_ANALYST_ADAPTIVE` is not enabled by this task
- mode must be independently kill-switchable
- mode must not be exposed in public Action schema
- no internal enum names in user-visible messages

If the repository already has a suitable mode/flag:
reuse it rather than creating duplicates.

---

# 6. Independent kill switch

Provide a fast production kill switch, repository-equivalent:

```text
FREE_ANALYST_ADAPTIVE_ENABLED = false
```

or equivalent mode reset.

Kill switch requirements:

- no schema migration
- no restart if existing config architecture supports hot/next-run config
- deterministic fallback remains available
- does not disable ordinary production delivery
- does not alter stored investment logic
- does not alter Inventory/FCF modes

Document rollback steps.

---

# 7. Production orchestration path

Integrate:

```text
production packet
        ↓
packet eligibility
        ↓
Free Analyst adapter
        ↓
Free Analyst structured analysis
        ↓
synthesis support validator
        ↓
Adaptive Renderer
        ↓
existing hard validators
        ↓
candidate eligibility
        ↓
final selector
```

No final message may bypass existing hard validators.

---

# 8. Per-message isolation

AI integration must operate per message, not all-or-nothing packet-wide.

Desired behavior:

```text
market digest AI candidate fails
→ market digest deterministic fallback
→ stock AI candidates may still pass

stock A AI candidate fails
→ stock A deterministic fallback
→ stock B may still use validated AI
```

Packet persistence / delivery must remain complete.

A single AI message failure must not block the full packet.

---

# 9. Fallback hierarchy

For the new mode, recommended hierarchy:

```text
Free Analyst + Adaptive candidate
        ↓
hard validation PASS
        → eligible AI-assisted final message

hard validation FAIL
        → existing deterministic fallback
```

Do not route failed Free Analyst output through an unvalidated prose fixer.

Bounded correction may be used only if it already exists and remains fully revalidated.

Do not make the legacy current-AI path a hidden second AI fallback unless there is an explicit reason and audit trail.

---

# 10. Structured analysis production contract

Port the proven structured object.

Must preserve semantic classes for:

- top findings
- thesis implications
- alternative interpretations
- expectation/valuation interaction
- positioning synthesis
- Unknowns
- next checks
- message plan

This is an internal conclusion/provenance object, not chain-of-thought.

No private reasoning storage.

---

# 11. Synthesis support types

Preserve typed support categories or repository equivalents:

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

Every claim-bearing analysis item must have a valid type and support refs.

No generic:

`AI_SUPPORTED`

---

# 12. Fact boundary

Production Free Analyst may use only:

- production packet canonical Facts
- canonical relations
- stored investment logic
- thesis drivers
- validation metrics
- warnings
- invalidation conditions
- expectation state
- valuation context
- price/RR facts
- supply/positioning facts
- macro temporal facts
- approved industry reasoning context
- explicit Unknowns

It may NOT use:
- web knowledge
- model memory about the company
- unsupplied consensus
- unsupplied customers/orders
- hidden calculations
- Open Research evidence in this task

---

# 13. No hidden arithmetic

Hard rule:

AI may not calculate a new number from raw packet values.

If Free Analyst needs:
- percentage-point gap
- ratio
- concentration
- comparison spread

it must already exist as a canonical relation.

Existing directional relation repair from current main must remain intact.

---

# 14. Thesis linkage

Free Analyst may synthesize:

```text
Fact / relation
→ stored investment logic
→ what the evidence supports/challenges
→ what remains unresolved
```

It must not automatically mutate:
- assessment state
- warning lifecycle
- valuation context
- monitoring version

Message interpretation and persisted monitoring state remain separate.

---

# 15. Alternative interpretation safety

When evidence is ambiguous, Free Analyst may preserve:

```text
positive interpretation
negative interpretation
current balance
unresolved reason
```

The Adaptive Renderer must not remove a material competing interpretation or uncertainty boundary.

---

# 16. Adaptive Renderer production contract

Use exactly the proven renderer families:

```text
DIRECT_ANALYST
CONCISE_HYBRID
MINIMAL_VNEXT
```

Selector remains deterministic.

No LLM call for renderer selection.

---

# 17. Direct-required production rule

DIRECT must remain required when compression would drop:

- a material alternative interpretation
- a causal boundary
- an uncertainty boundary
- a material expectation/execution threshold
- an Inventory/FCF interpretation boundary
- a temporal qualification

Hard target:

`material_information_loss = 0`

---

# 18. Minimal no-value rule

If Free Analyst adds no material analytical value:

- MINIMAL may be selected
- or deterministic/current concise output may remain preferred if existing architecture dictates

Do not force novelty.

No invented "insight" for quiet packets.

---

# 19. Existing hard validators remain authoritative

Every rendered candidate must pass the current production validators, including:

- numeric
- semantic
- relation ownership
- period
- currency/security basis
- price/RR ownership
- valuation basis
- temporal
- final-language
- runtime-quality
- forbidden causality
- Trade AR user-visible guard

Do not create a separate permissive validator set for Free Analyst.

---

# 20. Runtime-quality P2 audit

Specifically check the previously observed P2s:

```text
Korean current-price particle/grammar errors
substantive repeated price sentences
```

For each immutable replay and canary candidate record:

```text
price_particle_error_count
repeated_price_sentence_count
runtime_quality_result
fallback_reason
```

Do not hard-code fixes unless the new path reproduces the issue.

If Free Analyst + Adaptive naturally eliminates them:
record `NOT_REPRODUCED_IN_NEW_PATH`.

If reproduced:
bounded cleanup may be included only if trivial, isolated, and fully tested.
Otherwise keep as P2 follow-up.

---

# 21. Production packet / receipt invariants

Preserve:

```text
one immutable packet per run
one logical final message per expected slot
packet-bound delivery intent
no packetless intent
no duplicate final selection
receipt tied to final selected message
exactly-once unchanged
```

AI candidate generation must occur before final message selection without creating a second delivery path.

---

# 22. Candidate provenance

Persist audit metadata for each final message:

```text
analysis_mode
free_analyst_generated
free_analyst_validation
selected_renderer
renderer_selection_reasons
hard_validation
fallback_reason
final_delivery_mode
```

No secret prompts or chain-of-thought.

User-visible output must not expose internal flags.

---

# 23. Cross-market common-core requirement

Before promotion, prove the same production code works for both:

- KR immutable benchmark packet
- US immutable natural packet

No ticker-specific branches.

No market-specific Free Analyst fork.

Allowed market differences:
- packet acquisition
- session metadata
- supply semantics
- market-specific canonical facts

Reasoning schema remains common.

---

# 24. Mandatory immutable US replay

Use:

`2026-08-25-us-run-37-7e04812311c2`

Do not recollect providers.

Run all expected messages through production-integrated Free Analyst + Adaptive path.

Target:

```text
messages = 14
Free Analyst inputs = 14
validated = 14
hard validator errors = 0
material information loss = 0
fallback due Free Analyst/Adaptive hard error = 0
```

A runtime-quality-only fallback must be separately reported.

---

# 25. Mandatory immutable KR replay

Use the existing validated KR immutable benchmark/run used for prior Free Analyst / Adaptive comparison, preferably the 2026-08-24 19:34 rehearsal packet or the repository’s canonical equivalent.

No recollection.

Target:
- common adapter works
- no KR-specific regression
- Inventory semantics preserved
- investor-flow semantics preserved
- macro temporal semantics preserved
- Trade AR leak = 0

---

# 26. Exact replay comparison

For US and KR create exact comparison:

```text
EXISTING_PRODUCTION_OR_REHEARSAL_MESSAGE
FREE_ANALYST_DIRECT
FREE_ANALYST_HYBRID
ADAPTIVE_SELECTED
DETERMINISTIC_FALLBACK
```

No Open Research variants in this task.

---

# 27. Quality acceptance

For the combined immutable replay classify each message:

```text
MATERIAL_IMPROVEMENT
NO_MEANINGFUL_CHANGE
WORSE
```

Hard rule:

- `WORSE` due style only = P2
- `WORSE` due lost fact/boundary = P1
- wrong fact/number/time = P0

Do not require every message to improve.

---

# 28. Limited canary design

If control-plane permits a user-visible canary without bypassing `Production Assist` semantics, implement a deterministic per-packet canary.

Maximum user-visible AI-assisted selections per natural run:

```text
market digest: <= 1
stock messages: <= 2
total: <= 3
```

All remaining messages use current production output/fallback.

Do not hard-code tickers.

---

# 29. Canary candidate eligibility

A message may enter canary only if:

```text
Free Analyst generated
synthesis validation PASS
Adaptive Renderer PASS
all hard validators PASS
runtime-quality PASS
material information loss = 0
no research dependency
no Trade AR user-visible dependency
packet/receipt ownership valid
```

If any condition fails:
use existing deterministic production output.

---

# 30. Canary selection policy

Selector must be deterministic and auditable.

Preferred priority:

1. analytically material validated messages
2. exercise more than one renderer mode if safe
3. prefer lower ambiguity only if renderer boundary is preserved
4. avoid selecting multiple near-identical message shapes if a diverse safe sample exists

No ticker hard-coding.

No market-cap hard-coding.

No selection based on model preference.

Persist:

```text
canary_candidate
canary_selected
selection_reason
```

---

# 31. Canary safety boundaries

Do not use canary for a message if:

- hard validator needed correction more than supported bound
- claim provenance incomplete
- research sidecar is required
- Trade AR/broad AR/AP would appear
- unresolved temporal conflict exists
- runtime-quality fails
- receipt mapping is ambiguous

---

# 32. Canary behavior if Production Assist blocks AI delivery

If `PRODUCTION_ASSIST_CONTROL_PLANE = A`:

Do not bypass.

Set:

```text
FREE_ANALYST_ADAPTIVE_CANARY =
READY_NOT_ARMED
```

Still complete:
- code integration
- immutable replay
- non-delivery production-context canary simulation
- selector audit

Then report:
`NEXT_ACTION = EXPLICIT_CANARY_ENABLEMENT_DECISION`

No hidden flag flip.

---

# 33. Canary behavior if supported

If `PRODUCTION_ASSIST_CONTROL_PLANE = B` and all gates pass:

arm:

```text
FREE_ANALYST_ADAPTIVE_CANARY =
ENABLED_PENDING_NATURAL
```

No manual production run.

Wait for the next naturally scheduled eligible market run.

Do not send test messages outside natural production.

---

# 34. First natural canary acceptance

When natural canary occurs, require:

```text
packet terminal
expected delivery count complete
AI-assisted canary count <= 3
duplicates = 0
orphans = 0
receipt integrity = PASS
exactly_once = PASS

canary messages:
Fact mismatch = 0
Unsupported causality = 0
Temporal error = 0
Runtime-quality PASS
```

Do not automatically expand cohort after one PASS.

A separate expansion decision is required.

---

# 35. Canary rollback

If any canary message has:

- wrong fact/number
- causal overclaim
- temporal violation
- Trade AR leak
- receipt/exactly-once issue

immediately:

```text
FREE_ANALYST_ADAPTIVE_CANARY = DISABLED
```

and restore existing production selector.

Do not disable deterministic production.

Record incident.

---

# 36. Common AI Core v1 completion state

Set one:

```text
COMMON_AI_CORE_V1 =
INTEGRATION_FAIL /
INTEGRATED_READY_NOT_ARMED /
INTEGRATED_CANARY_PENDING_NATURAL /
CANARY_LIVE_PASS
```

This task can reach:
- `INTEGRATED_READY_NOT_ARMED`
- or `INTEGRATED_CANARY_PENDING_NATURAL`

Do not claim `CANARY_LIVE_PASS` without natural evidence.

---

# 37. Open Research status

This task must leave:

```text
OPEN_RESEARCH_PRODUCTION_INTEGRATION = 0
```

Keep the existing Open Research branch/evidence unchanged.

The next major common-stack work after Free Analyst + Adaptive natural canary is:

`OPEN_RESEARCH_SELECTIVE_PRODUCTION_INTEGRATION`

---

# 38. Full focused tests — common core

Add tests for:

- production natural packet adapter
- KR packet adapter
- structured analysis schema
- support-ref resolution
- bounded inference
- alternative interpretation
- expectation linkage
- positioning synthesis
- no hidden arithmetic
- external knowledge rejection
- Adaptive selector
- Direct-required
- Minimal no-value
- material-information-loss detection
- existing hard validator interoperability
- fallback per message
- packet completion despite AI failure
- canary eligibility
- canary selection
- canary max count
- no ticker hard-code
- kill switch
- Production Assist gate
- receipt/exactly-once selection invariants
- Trade AR user-visible zero

---

# 39. Negative controls

Mandatory:

### Unsupported fact
Free Analyst mentions company knowledge absent from packet
→ reject

### Hidden arithmetic
raw numbers supplied, relation absent, AI calculates difference
→ reject

### Temporal
reference macro item called today move
→ reject

### Directional relation
absolute gap used for `lower/higher`
→ reject

### Trade AR
shadow canary context leaks exact Trade AR user-visible
→ reject

### Selector
Adaptive compression drops material uncertainty boundary
→ reject

### Canary
4th AI message selected in same run
→ reject

### Production Assist
authoritative OFF gate bypass attempted
→ reject

### Receipt
AI and fallback both create final delivery rows
→ reject

---

# 40. Full regression suite

Preserve:

- US directional relation repair
- FCF period identity
- current-price RR ownership
- Macro temporal rehydration
- Inventory user-visible
- Trade AR OFF
- investor-flow semantics
- Phase 9.0E
- KR packet persistence
- non-trading-day guard
- KRX role-target
- night-futures session basis
- exactly-once
- deterministic fallback
- Open Research code not imported into production path

---

# 41. Full validation

Required:

```text
focused integration tests PASS
full pytest PASS
Ruff PASS
git diff --check PASS
Investment Knowledge parity PASS
Chart Knowledge parity PASS
Public Action 0.4.5 unchanged
operationId 20/20 unique
schema 4 unchanged
implementation SHA Actions Test/Lint PASS
final main SHA Actions Test/Lint PASS
```

Report exact counts.

---

# 42. Production dependency audit

Before promotion, produce import/dependency graph confirming:

```text
production Free Analyst path
does NOT import:
Open Research Agent
Event Attribution web/search connector
research scheduler
shadow-only benchmark runner
```

Research may share generic typed contracts only if there is no runtime search side effect.

---

# 43. Promotion gate

Set:

```text
FREE_ANALYST_ADAPTIVE_PRODUCTION_INTEGRATION =
PASS / FAIL

FREE_ANALYST_PRODUCTION_FACT_BOUNDARY =
PASS / FAIL

ADAPTIVE_RENDERER_PRODUCTION =
PASS / FAIL

PRODUCTION_FALLBACK_PARITY =
PASS / FAIL

PRODUCTION_DELIVERY_INTEGRITY =
PASS / FAIL
```

Promotion allowed only if all PASS and:

```text
OPEN_P0 = 0
OPEN_MATERIAL_P1 = 0
```

---

# 44. Promotion procedure

If gates PASS:

1. merge/fast-forward cleanly to main
2. sync operating
3. restart only the correct thesis-monitor API if imported runtime code requires it
4. do not restart unrelated OHLCV API
5. `/health` PASS
6. final main Actions Test/Lint PASS
7. worktrees clean
8. confirm Production Assist unchanged
9. confirm Inventory/Trade AR/Phase 9.0E unchanged
10. confirm production schedules unchanged

If an unrelated service is accidentally touched:
record incident and verify no config/data/schedule mutation before continuing.

---

# 45. No immediate full rollout

Even after production code promotion:

Do NOT set full mode:

`FREE_ANALYST_ADAPTIVE`

This task only permits:
- readiness
- or limited canary

A later natural-proof review must decide expansion.

---

# 46. Required architecture docs

Create/update:

1. `docs/architecture/COMMON_AI_CORE_V1.md`
   - production flow
   - ownership boundaries
   - fallback
   - kill switch

2. `docs/architecture/FREE_ANALYST_PRODUCTION_INTEGRATION.md`
   - packet adapter
   - support refs
   - validators

3. `docs/architecture/ADAPTIVE_RENDERER_PRODUCTION.md`
   - deterministic selector
   - Direct/Hybrid/Minimal
   - information-loss rule

4. `docs/architecture/FREE_ANALYST_CANARY_POLICY.md`
   - eligibility
   - max count
   - rollback

5. update relation semantics doc if needed
   - preserve signed directional binding

---

# 47. Required reports

Create:

1. `docs/reports/20260825-free-analyst-production-control-plane-audit.md`
2. `docs/reports/20260825-free-analyst-production-port-manifest.md`
3. `docs/reports/20260825-free-analyst-production-dependency-audit.md`
4. `docs/reports/20260825-free-analyst-production-us-run37-replay.md`
5. `docs/reports/20260825-free-analyst-production-kr-replay.md`
6. `docs/reports/20260825-adaptive-renderer-production-replay.md`
7. `docs/reports/20260825-free-analyst-runtime-quality-p2-audit.md`
8. `docs/reports/20260825-free-analyst-production-fallback-parity.md`
9. `docs/reports/20260825-free-analyst-production-delivery-integrity.md`
10. `docs/reports/20260825-free-analyst-canary-selection-simulation.md`
11. `docs/reports/20260825-free-analyst-production-message-benchmark.md`
12. `docs/reports/20260825-common-ai-core-v1-readiness.md`
13. `docs/reports/20260825-common-ai-core-v1-artifact-index.md`

Recommended JSON:

`docs/reports/20260825-common-ai-core-v1-readiness.json`

---

# 48. Exact message benchmark

Create:

`docs/reports/20260825-free-analyst-production-message-benchmark.md`

For each immutable replay message include:

```text
EXISTING MESSAGE
FREE_ANALYST DIRECT
FREE_ANALYST HYBRID
ADAPTIVE SELECTED
DETERMINISTIC FALLBACK
CANARY_ELIGIBLE
CANARY_SELECTION_REASON
```

No Open Research version.

---

# 49. Canary simulation report

Create a simulated natural-run selection without delivery.

Show:

```text
message slot
candidate eligible?
renderer
runtime quality
selected for canary?
reason
final simulated delivery mode
```

Hard target:
at most 3 selected.

---

# 50. Machine-readable readiness summary

Create:

`docs/reports/20260825-common-ai-core-v1-readiness.json`

Include:

```text
repository
control_plane
integration
us_replay
kr_replay
free_analyst
adaptive_renderer
hard_validation
runtime_quality
fallback
delivery_integrity
canary
production_isolation
open_research_excluded
gates
next_action
```

---

# 51. Mandatory ZIP

Create:

`20260825-free-analyst-adaptive-production-integration-bundle.zip`

Include all sanitized reports, message benchmark, readiness JSON, and artifact index.

Compute/report SHA-256.

---

# 52. Final status values

Successful implementation should report one of these.

## If Production Assist prevents user-visible canary

```text
FREE_ANALYST_ADAPTIVE_PRODUCTION_INTEGRATION = PASS
COMMON_AI_CORE_V1 = INTEGRATED_READY_NOT_ARMED
FREE_ANALYST_ADAPTIVE_CANARY = READY_NOT_ARMED
```

## If supported canary may be armed

```text
FREE_ANALYST_ADAPTIVE_PRODUCTION_INTEGRATION = PASS
COMMON_AI_CORE_V1 = INTEGRATED_CANARY_PENDING_NATURAL
FREE_ANALYST_ADAPTIVE_CANARY = ENABLED_PENDING_NATURAL
```

Do not claim natural canary PASS.

---

# 53. Completion response

Return:

```text
INSTRUCTION_COMMIT = ...
BRANCH = ...
BASE_SHA = ...
IMPLEMENTATION_SHA = ...
FINAL_MAIN = ...
OPERATING = ...
REPORT_COMMIT = ...

PRODUCTION_ASSIST_CONTROL_PLANE = A / B / C
PRODUCTION_ASSIST_FINAL = ...

FREE_ANALYST_ADAPTIVE_PRODUCTION_INTEGRATION = ...
FREE_ANALYST_PRODUCTION_FACT_BOUNDARY = ...
ADAPTIVE_RENDERER_PRODUCTION = ...
PRODUCTION_FALLBACK_PARITY = ...
PRODUCTION_DELIVERY_INTEGRITY = ...

US_RUN37_FREE_ANALYST = .../14
US_RUN37_ADAPTIVE = .../14
KR_REPLAY = PASS / FAIL

FACT_MISMATCH = ...
UNSUPPORTED_NUMERIC = ...
UNSUPPORTED_CAUSALITY = ...
TEMPORAL_VIOLATIONS = ...
TRADE_AR_LEAK = ...
HIDDEN_ARITHMETIC = ...
EXTERNAL_UNSOURCED_FACTS = ...
MATERIAL_INFORMATION_LOSS = ...

PRICE_PARTICLE_ERRORS_NEW_PATH = ...
REPEATED_PRICE_SENTENCES_NEW_PATH = ...
RUNTIME_QUALITY_NEW_PATH = ...

CANARY_MAX_PER_RUN = 3
CANARY_SIMULATED_SELECTED = ...
FREE_ANALYST_ADAPTIVE_CANARY =
READY_NOT_ARMED /
ENABLED_PENDING_NATURAL /
DISABLED

COMMON_AI_CORE_V1 =
INTEGRATED_READY_NOT_ARMED /
INTEGRATED_CANARY_PENDING_NATURAL /
INTEGRATION_FAIL

OPEN_RESEARCH_PRODUCTION_INTEGRATION = 0

PRODUCTION_MUTATION_FROM_REPLAY = 0
MANUAL_TELEGRAM_SEND = 0
SCHEDULE_CHANGE = 0

OPEN_P0 = ...
OPEN_MATERIAL_P1 = ...
P2_BACKLOG = ...

NEXT_ACTION =
WAIT_FOR_FREE_ANALYST_NATURAL_CANARY /
EXPLICIT_CANARY_ENABLEMENT_DECISION /
BOUNDED_REPAIR

ZIP = ...
ZIP_SHA256 = ...
```

---

# 54. Severity

## P0

- wrong user-visible fact/number/period
- Trade AR leak
- temporal violation
- hidden external fact
- hidden arithmetic accepted
- receipt/exactly-once regression
- duplicate delivery
- Production Assist bypass
- Open Research accidentally activated in production
- deterministic fallback unavailable

## P1

- Free Analyst adapter cannot consume production packet
- Adaptive renderer drops material boundary
- common KR/US schema diverges
- per-message fallback breaks packet completion
- hard validator bypass
- canary selection exceeds limit
- runtime dependency imports research/web path
- control plane ambiguous enough to risk unintended AI delivery

## P2

- harmless renderer preference
- runtime grammar/particle issue with fail-closed fallback
- repeated price wording with fail-closed fallback
- some messages show no analytical improvement
- canary not armed because Production Assist remains OFF
- report/observability polish

---

# 55. Final principle

The purpose of this task is to finish the **common AI reasoning engine**, not the research engine.

The intended production ownership is:

```text
Backend
= what is true

Free Analyst
= what matters and what the verified evidence means

Synthesis Validator
= whether the interpretation is supported

Adaptive Renderer
= how much analysis should be shown

Hard Validators
= whether the final message is factually, semantically,
  temporally, numerically, and linguistically safe

Deterministic Fallback
= guaranteed safe completion

Open Research
= still separate and OFF in production
```

Do not chase a full AI rollout.

Integrate safely, prove KR/US common behavior, preserve fallback, and arm at most a small natural canary if the existing control plane explicitly permits it.
