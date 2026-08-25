# thesis-monitor — Free Analyst Cross-Industry / Cross-Thesis Semantic Ownership Guard Bounded Repair

## Metadata

- Workstream: `FREE_ANALYST_CONTEXT_OWNERSHIP_BOUNDED_REPAIR`
- Instruction version: `1.0`
- Date: `2026-08-25 KST`
- Authoring time context: approximately `19:26 KST`
- Repository: `sskim-ai/thesis-monitor`
- Task type: `BOUNDED_PRODUCTION_SAFETY_REPAIR + IMMUTABLE_CROSS_MARKET_REPLAY`
- Open Research production integration: `0`
- Public Action: `0.4.5`
- operationId: `20/20 unique`
- schema: `4`

### Expected current production main / operating

Latest reported production main/operating:

`c7816ca`

Resolve and record the exact full SHA for `origin/main` and operating before implementation.

### Triggering replay

Instruction:
`20260825-1905-kr-us-same-day-cross-market-adapter-replay.md`

Known review result:

```text
KR/US Market Adapter replay = safe PARTIAL
Code correctness report = PASS
Open P0/P1 reported = 0/0
Production main mutation = 0
```

However, human review identified a material semantic-ownership leak in a KR Free Analyst replay message.

### Triggering material defect

Hanwha Aerospace replay message contained memory/HBM interpretation content, including concepts equivalent to:

```text
HBM execution
ASP
product mix
very-high expectation framing
```

while the same message/entity context was Hanwha Aerospace and its relevant stored investment logic was defense/backlog/delivery/margin/working-capital oriented.

The canary simulation also selected that message, meaning the leak could have become user-visible in a natural run.

This is not a Market Adapter defect.

This is a Free Analyst synthesis / context ownership validation defect.

### Severity override

Treat the triggering issue as:

```text
OPEN_P0 = 0
OPEN_MATERIAL_P1 = 1

P1 =
cross-industry / cross-thesis synthesis context leakage
```

until repaired and replay-proven.

---

# 0. Objective

Repair the Free Analyst semantic ownership boundary so that a synthesis may only use industry/thesis-specific concepts that are actually supported by the current message's entity, packet, industry reasoning context, thesis drivers, Facts, relations, expectations, or approved Unknowns.

The target is:

```text
Fact / relation
+ entity
+ industry context
+ thesis driver
+ expectation context
        ↓
Free Analyst synthesis
        ↓
Semantic Ownership Validator
        ↓
Adaptive Renderer
        ↓
existing hard validators
```

not:

```text
generic successful synthesis from another ticker
→ copied/reused across current ticker
```

The repair must remain common across KR and US.

Do not create ticker-specific patches.

---

# 1. Work-instruction repository protocol

Store this exact instruction at:

`docs/work-instructions/20260825-free-analyst-semantic-ownership-guard-bounded-repair.md`

Before implementation:

```bash
git fetch origin
git status
git rev-parse origin/main
git rev-parse origin/codex/20260825-kr-us-same-day-adapter-replay
git rev-parse origin/codex/adaptive-renderer-selector-shadow
```

Then:

1. verify actual latest safe production main/operating
2. locate the exact KR immutable replay artifact containing the Hanwha leakage
3. locate the exact US run-37 immutable replay artifacts
4. commit/push this exact instruction as a **docs-only instruction commit**
5. record instruction path / commit SHA / version / implementation base SHA
6. create a dedicated repair branch from latest safe production main
7. no force push / no history rewrite

Recommended branch:

`codex/free-analyst-semantic-ownership-guard-repair`

---

# 2. Canary safety during repair

Current bounded Free Analyst canary may still be armed.

Before runtime code changes, inspect the next eligible production schedule.

If any natural production run could occur before the repair is promoted:

```text
temporarily disable only
FREE_ANALYST_ADAPTIVE_CANARY
```

using the existing supported kill switch.

Do NOT:
- disable ordinary production
- disable Pilot
- change Production Assist governance
- change canary limits
- enable full mode

After repair promotion and all replay gates PASS:
restore the same bounded canary state:

```text
market <= 1
stocks <= 2
total <= 3
full mode = OFF
```

Record before/after control-plane state.

If no eligible natural run can occur during the bounded repair window:
leaving canary armed is acceptable only if there is no risk of executing the defective path before promotion.

---

# 3. Hard prohibitions

Do NOT:

- hard-code Hanwha Aerospace
- hard-code SK hynix
- add ticker blacklists
- solve this with a flat list of forbidden words only
- remove all industry-specific language
- make Free Analyst generic
- weaken existing numeric/semantic/temporal validators
- allow unsupported synthesis if prose is hedged
- enable Open Research
- change Market Adapter acquisition logic
- change Inventory selection
- enable Trade AR
- change Phase 9.0E
- change valuation or price/RR ownership rules
- mutate production DB during replay
- manually send Telegram
- manually run KR/US production

---

# 4. Root-cause trace — mandatory

Trace the leaking Hanwha analysis through:

```text
natural KR packet
→ Free Analyst natural-packet adapter
→ industry reasoning context
→ stored investment logic / thesis drivers
→ Inventory / FCF / valuation contexts
→ Free Analyst prompt/input
→ structured analysis object
→ synthesis support refs
→ semantic validator
→ Adaptive Renderer
```

Determine whether the leak arose from one or more of:

```text
A. stale prior-message analysis state reused
B. shared template/context object mutated across tickers
C. cache key too broad / missing ticker or packet identity
D. benchmark/replay loop state bleed
E. synthesis support refs valid syntactically but wrong owner
F. industry reasoning context mapped from previous ticker
G. thesis-driver refs resolved outside current entity
H. expectation state reused from previous ticker
I. renderer reused prior message block
J. other — document exactly
```

Do not implement a fix before identifying the actual branch(es).

---

# 5. Ownership dimensions

Define or reinforce a typed ownership contract for every analytical synthesis item.

At minimum capture:

```text
entity_owner
ticker_owner
market_owner
packet_owner

industry_context_owner
thesis_driver_refs[]
fact_refs[]
relation_refs[]
expectation_refs[]
valuation_refs[]
unknown_refs[]
```

Not every claim requires all fields.

But every claim-bearing item must resolve to the current message/entity packet.

---

# 6. Semantic concept provenance

Industry/thesis-specific concepts must be evidence-bound.

Examples:

```text
HBM
DRAM / NAND
ASP
memory product mix
combined ratio
CSM
backlog
delivery schedule
project margin
fleet / freight
cloud margin
ARR / NRR
```

A concept may appear only if its support graph includes a compatible current-entity source, such as:

```text
current entity Fact
current entity relation
current entity stored thesis driver
current entity validation metric
current entity approved industry reasoning context
current entity Unknown / next-check
```

The validator must not infer support merely because:
- the concept is common in the sector globally
- another ticker in the same packet used it
- another message used the same sentence successfully

---

# 7. Do not overfit to keywords

A flat keyword blacklist is insufficient.

Example:

`product mix` can be valid for many industries.

Therefore semantic ownership should use typed concept families or source-bound claim ownership.

Possible internal concept families:

```text
MEMORY_HBM
MEMORY_ASP
MEMORY_PRODUCT_MIX
DEFENSE_BACKLOG
DEFENSE_DELIVERY
DEFENSE_PROJECT_MARGIN
INSURANCE_UNDERWRITING
LOGISTICS_FREIGHT
CLOUD_AI_CAPEX
```

Exact enum design may follow repository style.

The important rule is:

```text
concept family
→ must be supported by current-entity context
```

Do not create an exhaustive ontology in this bounded repair.
Cover the proven industry reasoning concepts already used by current production/shadow prompts.

---

# 8. Thesis-driver ownership

A thesis linkage must resolve only to thesis drivers belonging to the current monitored stock / current packet entity.

Hard target:

```text
cross-ticker thesis_driver_ref = reject
```

Example:

```text
Hanwha analysis
→ SK hynix HBM thesis driver
= reject
```

---

# 9. Expectation ownership

The triggering Hanwha message also used a `very high` expectation framing despite its current stored expectation being different.

Require:

```text
expectation statement
→ current entity expectation ref
```

Hard negative control:

```text
current entity expectation = elevated
previous ticker = very_high
rendered "very high expectations"
→ reject
```

Do not allow a generic expectation phrase without current-entity provenance if it implies a specific level.

---

# 10. Industry reasoning ownership

The approved industry reasoning context must be instantiated per current entity.

Audit:
- factory/factory method
- cache keys
- message-loop lifecycle
- mutable shared objects

Hard invariant:

```text
industry_context.ticker/entity
= current message ticker/entity
```

If cached:
cache key must include all dimensions required to avoid cross-entity contamination.

---

# 11. Per-message state isolation

Every message-generation call must start from a clean per-message analysis state.

Audit and test:

```text
analysis object
prompt context
support-ref collector
concept registry
unknown collector
renderer plan
```

for accidental reuse.

If shared state is intended:
make it immutable.

Mutable cross-message state should not carry claim-bearing context.

---

# 12. Support-ref owner validation

Current support refs may be syntactically valid but semantically owned by another ticker.

Enhance validation:

```text
support ref exists
AND
support ref owner == current message owner
```

Where refs are global/shared by design:
explicitly classify them as such, e.g.:

```text
macro market context
market-wide index context
common policy Fact
```

Do not treat entity-specific refs as global.

---

# 13. Relation ownership

For any relation used in synthesis:

```text
relation.lhs owner
relation.rhs owner
relation entity scope
current message entity
```

must be compatible.

Cross-entity relations are allowed only if explicitly designed as peer/market relations and correctly typed.

No accidental current-ticker synthesis from another ticker’s Inventory relation.

---

# 14. Renderer ownership

Adaptive Renderer must consume only the validated current-message structured analysis object.

It must not:
- reuse a previous Direct block
- reuse previous Hybrid block
- retain previous selection reasons
- retain previous expectation/industry labels

Add a per-message renderer-state reset test if necessary.

---

# 15. Positive-control examples

Mandatory acceptance fixtures should include:

### Memory company

Current packet supports:
- HBM thesis driver
- memory Inventory relation
- ASP / mix Unknown

Then:

```text
HBM / ASP / product mix synthesis
→ ACCEPT
```

when properly bounded.

### Defense company

Current packet supports:
- backlog
- delivery
- margin
- working-capital/Inventory relation if present

Then:

```text
backlog / delivery / margin synthesis
→ ACCEPT
```

### Cross-industry common concept

If `product mix` is explicitly supported by the defense company’s own Fact/driver:
it may be allowed.

This prevents keyword-only overblocking.

---

# 16. Negative-control examples

Mandatory:

### Memory → defense leak

```text
Hanwha/current defense entity
+ no HBM support refs
→ HBM synthesis
REJECT
```

### Expectation leak

```text
current expectation != very_high
→ "very high expectations"
without current ref
REJECT
```

### Insurance → semiconductor leak

```text
combined ratio language
→ semiconductor entity
REJECT
```

### Defense → logistics leak

```text
backlog/delivery-specific thesis linkage
→ logistics entity without support
REJECT
```

### Cross-ticker thesis ref

Any analysis item with a thesis-driver ref owned by a different ticker:
REJECT.

### Prior-message renderer block reuse

Second message contains exact claim-bearing block from first message without second-message refs:
REJECT.

---

# 17. Generic synthesis repetition — P2 audit only

The prior US replay showed repeated generic synthesis language across several names.

This task is not a broad quality rewrite.

However, audit whether the same root cause causing semantic leakage also caused generic repetition.

If yes and the fix naturally reduces repetition:
record it.

If generic repetition remains but is factually safe:
keep it as P2.

Do not widen the repair unnecessarily.

---

# 18. Mandatory KR immutable replay

Use the same immutable 2026-08-25 KR afternoon packet from the same-day replay.

Do not recollect providers.

Target:

```text
all expected messages reach safe terminal output

Hanwha:
HBM leakage = 0
memory ASP leakage = 0
memory product-mix leakage = 0
wrong expectation-level leakage = 0

cross-ticker support refs = 0
cross-ticker thesis refs = 0
cross-ticker relation refs = 0
```

Also preserve:
- KR valuation repair PASS
- Inventory semantics
- investor-flow semantics
- macro temporal semantics
- Market Adapter safe PARTIAL behavior

---

# 19. Mandatory Hanwha exact before/after

Create an exact focused comparison:

```text
PRE_REPAIR_HANWHA_REPLAY
POST_REPAIR_HANWHA_REPLAY
DETERMINISTIC_FALLBACK
```

Annotate every removed/changed claim with:
- why it was unsupported
- what current-entity evidence replaced it
- whether information value improved or remained neutral

The post-repair message should not become generic merely to pass.

---

# 20. Mandatory US run-37 regression

Use:

`2026-08-25-us-run-37-7e04812311c2`

Target:

```text
14/14 safe terminal output
no new fact mismatch
no new support-ref failure
no cross-ticker context leakage
no expectation leakage
no renderer state bleed
```

Preserve:
- US Market Adapter safe PARTIAL
- session semantics
- macro temporal
- directional relation repair
- FCF period identity
- current-price RR ownership

---

# 21. Cross-market context-ownership audit

Across KR + US immutable messages, produce:

```text
message count
entity-specific claims
global/shared claims
entity-owner mismatches
ticker-owner mismatches
industry-context mismatches
thesis-driver mismatches
expectation mismatches
relation-owner mismatches
```

Hard target:
all mismatch counts `0`.

---

# 22. Canary selector replay

Run the existing bounded canary simulation on both immutable packets.

Limits remain:

```text
market <= 1
stocks <= 2
total <= 3
```

For every selected candidate verify:

```text
semantic ownership PASS
support-ref owner PASS
industry context owner PASS
thesis-driver owner PASS
expectation owner PASS
runtime quality PASS
```

Hard target:

```text
selected candidate with ownership mismatch = 0
```

---

# 23. Canary eligibility guard

Add semantic ownership validation as an explicit canary eligibility requirement.

Conceptually:

```text
Free Analyst generated
→ synthesis support PASS
→ semantic ownership PASS
→ Adaptive Renderer PASS
→ hard validators PASS
→ runtime quality PASS
→ canary eligible
```

If semantic ownership fails:
fallback/current production path.

This guard must also apply in future full mode, not only canary.

---

# 24. Per-message fallback

If one message fails ownership:

```text
that message
→ deterministic fallback
```

Other message candidates may continue.

Do not block the full packet.

---

# 25. Production promotion scope

This repair may promote the semantic-ownership guard and required state-isolation fixes to main after replay/full validation.

Do NOT promote:
- Open Research
- Event Attribution
- new Market Adapter features beyond current deployed behavior
- full Free Analyst mode
- larger canary limits

---

# 26. Canary state after promotion

After PASS and production promotion:

If canary was temporarily disabled:
restore exactly:

```text
FREE_ANALYST_ADAPTIVE_CANARY =
ENABLED_PENDING_NATURAL

market <= 1
stocks <= 2
total <= 3

FREE_ANALYST_ADAPTIVE_FULL =
OFF
```

Do not expand cohort.

Open Research remains:

`0 / BLOCKED_CONNECTOR`

---

# 27. Natural-proof implication

Do not claim natural canary PASS from replay.

After repair:

```text
CODE_CORRECTNESS =
PASS

KR_FREE_ANALYST_CANARY_NATURAL =
still NOT_OBSERVED / PENDING

US_FREE_ANALYST_CANARY_NATURAL =
still pending
```

The next eligible natural run remains the actual delivery proof.

---

# 28. Required focused tests

Add tests for:

- current-message entity ownership
- ticker ownership
- packet ownership
- industry-context ownership
- thesis-driver ownership
- expectation ownership
- Fact owner
- relation owner
- allowed global/shared macro ref
- explicit peer/cross-entity ref type
- mutable shared-state isolation
- cache key isolation
- renderer state reset
- memory concept valid on memory ticker
- memory concept rejected on defense ticker
- defense concept valid on defense ticker
- defense concept rejected on unrelated ticker
- same generic phrase allowed if independently supported
- canary eligibility blocked on ownership failure
- per-message fallback
- canary max 1/2/3 preserved

---

# 29. Full regression suite

Preserve:

- KR valuation numeric-ref repair
- US directional relation repair
- FCF period identity
- current-price RR ownership
- Inventory user-visible semantics
- Trade AR OFF
- KR investor-flow reconciliation
- Macro temporal rehydration
- KR/US Market Adapter safe PARTIAL
- exactly-once
- packet persistence
- per-message fallback
- Open Research production integration = 0

---

# 30. Full validation

Required:

```text
focused ownership tests PASS
KR immutable replay PASS
US run-37 replay PASS
canary simulation PASS
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
API /health PASS
worktrees clean
```

Report exact counts.

---

# 31. Architecture docs

Create/update:

1. `docs/architecture/FREE_ANALYST_SEMANTIC_OWNERSHIP.md`
   - entity / ticker / packet ownership
   - industry context ownership
   - thesis-driver ownership
   - expectation ownership
   - global/shared exception rules

2. `docs/architecture/FREE_ANALYST_PRODUCTION_INTEGRATION.md`
   - add ownership validator stage

3. `docs/architecture/FREE_ANALYST_CANARY_POLICY.md`
   - semantic ownership required for eligibility

Do not describe Open Research as production-enabled.

---

# 32. Required reports

Create:

1. `docs/reports/20260825-free-analyst-semantic-ownership-root-cause.md`
2. `docs/reports/20260825-free-analyst-semantic-ownership-contract.md`
3. `docs/reports/20260825-free-analyst-semantic-ownership-negative-controls.md`
4. `docs/reports/20260825-kr-hanwha-context-leak-before-after.md`
5. `docs/reports/20260825-kr-semantic-ownership-post-repair-replay.md`
6. `docs/reports/20260825-us-run37-semantic-ownership-regression.md`
7. `docs/reports/20260825-cross-market-semantic-ownership-audit.md`
8. `docs/reports/20260825-free-analyst-canary-ownership-simulation.md`
9. `docs/reports/20260825-free-analyst-semantic-ownership-readiness.md`
10. `docs/reports/20260825-free-analyst-semantic-ownership-artifact-index.md`

Recommended JSON:

`docs/reports/20260825-free-analyst-semantic-ownership-readiness.json`

---

# 33. Exact message benchmark

Create:

`docs/reports/20260825-free-analyst-semantic-ownership-message-benchmark.md`

Include for every affected / selected case:

```text
PRE_REPAIR
POST_REPAIR
DETERMINISTIC_FALLBACK
ENTITY_OWNER
INDUSTRY_CONTEXT_OWNER
THESIS_DRIVER_REFS
EXPECTATION_REF
OWNERSHIP_VALIDATION
CANARY_ELIGIBLE
```

Mandatory focused inclusion:
Hanwha Aerospace.

---

# 34. Machine-readable readiness summary

Create:

`docs/reports/20260825-free-analyst-semantic-ownership-readiness.json`

Include:

```text
repository
root_cause
ownership_contract
kr_replay
us_replay
cross_market_audit
canary_simulation
safety
runtime_quality
promotion
natural_proof
next_action
```

---

# 35. Mandatory ZIP

Create:

`20260825-free-analyst-semantic-ownership-bounded-repair-bundle.zip`

Include all sanitized reports, message benchmarks, readiness JSON, and artifact index.

Compute/report SHA-256.

---

# 36. Gates

Set exactly:

```text
FREE_ANALYST_SEMANTIC_OWNERSHIP_REPAIR =
PASS / FAIL

ENTITY_OWNERSHIP =
PASS / FAIL

INDUSTRY_CONTEXT_OWNERSHIP =
PASS / FAIL

THESIS_DRIVER_OWNERSHIP =
PASS / FAIL

EXPECTATION_OWNERSHIP =
PASS / FAIL

RELATION_OWNERSHIP =
PASS / FAIL

RENDERER_STATE_ISOLATION =
PASS / FAIL

KR_SEMANTIC_OWNERSHIP_REPLAY =
PASS / FAIL

US_SEMANTIC_OWNERSHIP_REPLAY =
PASS / FAIL

CROSS_MARKET_OWNERSHIP_AUDIT =
PASS / FAIL

CANARY_OWNERSHIP_ELIGIBILITY =
PASS / FAIL

CODE_CORRECTNESS =
PASS / FAIL
```

---

# 37. P1 closure rule

The material P1 closes only if:

```text
Hanwha memory/HBM leakage = 0
wrong expectation leakage = 0
all cross-ticker ownership mismatch counts = 0
KR replay PASS
US replay PASS
canary-selected ownership mismatches = 0
validators remain strict
full tests / CI PASS
```

Then:

```text
OPEN_MATERIAL_P1 = 0
```

---

# 38. Promotion procedure

If all gates PASS:

1. promote bounded repair cleanly to main
2. sync operating
3. restart only thesis-monitor API if required
4. `/health` PASS
5. final main Actions PASS
6. worktrees clean
7. restore bounded canary if it was temporarily paused
8. confirm:
   - full mode OFF
   - limits 1/2/3
   - Open Research 0
   - Trade AR OFF
   - Production Assist governance unchanged
   - Pilot unchanged

Set:

```text
FREE_ANALYST_SEMANTIC_OWNERSHIP_REPAIR =
DEPLOYED_PENDING_NATURAL
```

---

# 39. Completion response

Return:

```text
INSTRUCTION_COMMIT = ...
BRANCH = ...
BASE_SHA = ...
IMPLEMENTATION_SHA = ...
FINAL_MAIN = ...
OPERATING = ...
REPORT_COMMIT = ...

ROOT_CAUSE_BRANCH = ...

PRE_REPAIR_HANWHA_CONTEXT_LEAKS = ...
POST_REPAIR_HANWHA_CONTEXT_LEAKS = 0

CROSS_TICKER_FACT_REF_MISMATCH = 0
CROSS_TICKER_RELATION_REF_MISMATCH = 0
CROSS_TICKER_THESIS_REF_MISMATCH = 0
INDUSTRY_CONTEXT_MISMATCH = 0
EXPECTATION_OWNERSHIP_MISMATCH = 0

FREE_ANALYST_SEMANTIC_OWNERSHIP_REPAIR = ...
ENTITY_OWNERSHIP = ...
INDUSTRY_CONTEXT_OWNERSHIP = ...
THESIS_DRIVER_OWNERSHIP = ...
EXPECTATION_OWNERSHIP = ...
RELATION_OWNERSHIP = ...
RENDERER_STATE_ISOLATION = ...

KR_SEMANTIC_OWNERSHIP_REPLAY = ...
US_SEMANTIC_OWNERSHIP_REPLAY = ...
CROSS_MARKET_OWNERSHIP_AUDIT = ...

KR_CANARY_SIMULATED_SELECTED = ...
US_CANARY_SIMULATED_SELECTED = ...
CANARY_SELECTED_OWNERSHIP_ERRORS = 0
CANARY_OWNERSHIP_ELIGIBILITY = ...

FACT_MISMATCH = 0
UNSUPPORTED_NUMERIC = 0
UNSUPPORTED_CAUSALITY = 0
TEMPORAL_VIOLATIONS = 0
TRADE_AR_LEAK = 0
HIDDEN_ARITHMETIC = 0
EXTERNAL_UNSOURCED_FACTS = 0
MATERIAL_INFORMATION_LOSS = 0

CANARY_STATE = ...
FULL_MODE = OFF
CANARY_LIMIT = 1/2/3
OPEN_RESEARCH_PRODUCTION_INTEGRATION = 0

CODE_CORRECTNESS = ...
NATURAL_LIVE_PROOF = PENDING

OPEN_P0 = ...
OPEN_MATERIAL_P1 = ...
P2_BACKLOG = ...

NEXT_ACTION =
WAIT_FOR_NEXT_ELIGIBLE_NATURAL_CANARY /
BOUNDED_REPAIR

PRODUCTION_MUTATION_FROM_REPLAY = 0
MANUAL_TELEGRAM_SEND = 0
MANUAL_PRODUCTION_TASK = 0

ZIP = ...
ZIP_SHA256 = ...
```

---

# 40. Severity

## P0

- wrong Fact/number/period
- cross-ticker entity Fact delivered
- Trade AR leak
- temporal violation
- hidden external fact
- hidden arithmetic
- duplicate delivery / receipt failure
- Open Research accidentally enabled
- full mode accidentally enabled

## P1

- memory/HBM context reaches defense/logistics/etc without support
- thesis-driver ref owned by wrong ticker
- wrong expectation level reused across tickers
- industry context cache/state contamination
- relation ownership mismatch
- renderer previous-message state reuse
- canary-selected message fails ownership validation
- per-message fallback fails

## P2

- generic but factually safe synthesis repetition
- stylistic template similarity
- some messages show no material improvement
- adapter remains safe PARTIAL because structured breadth is unavailable
- canary not yet naturally observed

---

# 41. Final principle

The Free Analyst is allowed to reason freely.

It is not allowed to borrow another company’s analytical world.

The correct boundary is:

```text
current entity
+ current packet
+ current industry context
+ current investment logic
+ current expectation
+ current Facts / relations
        ↓
free synthesis
```

not:

```text
previous successful message
→ reusable analytical content
```

This repair should make industry-specific analysis more trustworthy without making the AI generic.

After the bounded repair passes, the next eligible natural KR/US canary can proceed under the same 1/2/3 limits.
