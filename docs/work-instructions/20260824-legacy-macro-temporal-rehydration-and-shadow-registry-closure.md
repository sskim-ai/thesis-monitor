# thesis-monitor — Legacy Macro Temporal Rehydration + Shadow Numeric Registry Closure

## Metadata

- Workstream: `P0 repair + bounded shadow-registry completion + end-to-end rehearsal closure`
- Instruction version: `1.0`
- Date: `2026-08-24 KST`
- Repository: `sskim-ai/thesis-monitor`
- Intended current main/operating:
  `96825de767f8ff25b59ab4451df305df5dd873cc`
- IMPORTANT:
  resolve and use the actual latest safe `origin/main` before implementation; do not force the SHA above if main legitimately advanced.
- Triggering rehearsal:
  `2026-08-24-kr-live-rehearsal-193419`
- Rehearsal cutoff:
  `2026-08-24T19:34:19+09:00`
- Rehearsal packet:
  persisted successfully
- Dry-run intents:
  `8`
- Duplicate/orphan intents:
  `0 / 0`
- Production DB mutation:
  `0`
- Telegram sends:
  `0`
- Triggering P0:
  legacy morning macro briefing lacked the newly introduced temporal role metadata and was fail-opened as `CURRENT_OBSERVATION`
- Triggering AI/shadow issue:
  shadow numeric gate saw approximately `210` unregistered investor-flow audit numeric fields and suppressed AI candidate generation
- Current Inventory mode:
  `SELECTIVE_INVENTORY`
- Inventory user-visible:
  `ENABLED_PENDING_NATURAL`
- Exact Trade AR:
  `OFF_PENDING_NATURAL_PROOF`
- Phase 9.0E:
  `SELECTIVE_CURRENT_FORMAL_FULL_FCF`
- Macro temporal contract:
  `macro-digest-temporal-eligibility-v1`
- Production Assist:
  `OFF`
- Public Action:
  `0.4.5`
- Output schema:
  `4`

This instruction intentionally closes **both** remaining rehearsal gaps:

1. P0 legacy macro temporal compatibility
2. shadow numeric registry completeness for investor-flow audit fields

After both are repaired, rerun the same rehearsal evidence end-to-end and, if safe, optionally perform one fresh current no-delivery rehearsal.

Do not wait for the next natural production run to validate code correctness.

---

# 0. Work-instruction repository protocol

Store this exact instruction at:

`docs/work-instructions/20260824-legacy-macro-temporal-rehydration-and-shadow-registry-closure.md`

Before implementation:

```bash
git fetch origin
git status
git rev-parse HEAD
git rev-parse origin/main
```

Then:

1. verify actual latest safe main/operating SHA
2. verify the triggering rehearsal artifacts are available
3. commit/push this instruction as a **docs-only instruction commit**
4. record:
   - instruction path
   - instruction commit SHA
   - instruction version
   - implementation base SHA
5. create implementation branch from the latest safe main descendant containing the instruction commit
6. no force push / history rewrite
7. do not silently edit this instruction after implementation begins

Recommended branch:

`codex/legacy-macro-temporal-shadow-registry-closure`

---

# 1. Repair scope

This task has three ordered stages.

## Stage A — P0
`Legacy Macro Briefing Temporal Rehydration & Fail-Closed Compatibility`

## Stage B — bounded shadow completeness
`Investor-Flow Audit Numeric Registry Completion`

## Stage C — end-to-end closure
Replay the immutable 19:34 rehearsal and prove:
- packet persistence
- dry-run intents
- AI candidate reachability
- fallback completion
- Inventory parity
- investor-flow safety
- macro temporal safety
- zero production mutation

Do not start Stage C until Stage A and Stage B focused tests pass.

---

# 2. Hard prohibitions

Do NOT:

- delete or overwrite the failed 16:xx natural run
- overwrite the 19:34 rehearsal artifacts
- manually send Telegram
- run actual KR primary/backup Scheduled Tasks
- mutate production notification rows
- mutate assessment DB
- mutate warning lifecycle
- mutate thesis versions
- mutate Pilot
- enable Trade AR
- disable Inventory
- change Phase 9.0E mode
- change macro source dates
- change night-futures deadline
- change KRX schedules
- loosen the AI numeric/semantic claim gate
- register audit fields as prose-eligible without semantic proof
- use wildcard/blanket numeric-registry allow rules
- make missing temporal metadata default to current
- rewrite legacy persisted macro briefings in place
- fabricate historical temporal roles

---

# 3. Evidence lock

Before code changes create a read-only evidence index for:

## A. Legacy macro briefing
- morning briefing ID/path
- briefing creation time
- market session
- each market-summary item's:
  - metric
  - observed_at
  - retrieved_at
  - frequency
  - provider freshness
  - old/new temporal metadata presence
- thesis signals stored in the briefing
- market-summary fields consumed at 19:34

## B. Shadow numeric gate
- exact count of unregistered numeric paths
- exact distinct semantic field names/paths
- ticker/window distribution
- source contract
- whether each is:
  - canonical flow fact
  - derived reconciliation fact
  - diagnostic/audit-only value
  - display helper
  - unsupported/unknown

Do not rely on the approximate `210` count without verifying it.

---

# 4. Stage A root cause — legacy temporal compatibility

Confirm the exact fail-open path.

Expected class to verify:

```text
legacy persisted briefing
→ no temporal_role / temporal eligibility metadata
→ consumer helper sees missing field
→ defaults to CURRENT_OBSERVATION
→ old observations become current signal
```

Trace every consumer that can do this, including repository-equivalent:

- daily digest
- market intelligence service
- macro thesis/today-signal builder
- AI macro packet
- deterministic fallback renderer
- per-ticker macro impact if applicable

The repair must close **all** fail-open paths, not just the visible digest formatter.

---

# 5. Do not mutate legacy briefing

Legacy persisted briefings are immutable historical evidence.

Do not backfill them in place.

Instead create a runtime/derived compatibility layer, suggested:

`macro-temporal-legacy-rehydration-v1`

Conceptual flow:

```text
persisted legacy item
        ↓
existing observed_at / retrieved_at / frequency / market_session
        ↓
current briefing/rehearsal cutoff
        ↓
same macro-digest-temporal classifier used by new data
        ↓
derived temporal role
        ↓
consumer
```

The derived role may be cached in a new non-destructive sidecar if existing architecture supports it, but original persisted evidence remains unchanged.

---

# 6. Rehydration inputs

Use only existing evidence.

Potential inputs:

- observed_at
- retrieved_at
- as_of_date
- source frequency/cadence
- series type
- market-session binding
- briefing created_at
- previous briefing cutoff if available
- market calendar
- source/provider freshness

Do not infer currentness from:

- `quality_status=fresh` alone
- retrieval time alone
- wall-clock day alone

---

# 7. Fail-closed compatibility rule

If temporal metadata is missing and sufficient legacy evidence exists:
rehydrate deterministically.

If evidence is insufficient:

```text
missing temporal role
→ NEVER CURRENT_OBSERVATION by default
```

Use the safest repository-equivalent state, conceptually:

- `REFERENCE_LAGGING`
- `STALE_FOR_DAILY_SIGNAL`
- `UNAVAILABLE`
- explicit `current_signal_eligible=false`

Choose based on actual available evidence.

The compatibility fallback must be **current-signal ineligible**.

---

# 8. Legacy item classification requirements

For each legacy market item produce:

```text
metric
legacy fields present
legacy fields missing
derived temporal role
derivation reason
eligible_today_signal
eligible_important_changes
eligible_regime
confidence / caution
```

No user-facing confidence score is required.

---

# 9. Legacy market thesis signals

The rehearsal found legacy thesis signals created from old observations.

Do not blindly reuse stored:

- positive
- negative
- weak positive
- weak negative

as a **new today_signal** when the source facts are temporally ineligible.

The compatibility layer must either:

A. recompute the current daily signal from rehydrated eligible facts, or

B. mark the stored daily signal as legacy/non-current and exclude it from current delta.

Longer-term regime/thesis state may remain valid.

Do not rewrite historical thesis state.

---

# 10. Macro-to-ticker impact compatibility

Audit whether legacy briefing signals can create fresh ticker macro impact deltas.

Required invariant:

```text
legacy/reference-only macro fact
→ may support structural macro exposure
→ must not create a false new daily ticker impact delta
```

No long-term exposure mappings should be removed.

---

# 11. AI/fallback macro parity

Both AI and fallback must consume the same **rehydrated temporal view**.

The AI must not receive a legacy item as current if fallback sees it as reference.

Parity targets:

```text
temporal role mismatch = 0
today-signal eligibility mismatch = 0
important-change eligibility mismatch = 0
```

---

# 12. Stage A mandatory negative controls

Required tests:

### Missing new temporal fields + old observation
```text
briefing date 8/24
observed_at 8/20
temporal_role missing
→ CURRENT_OBSERVATION forbidden
```

### Missing temporal fields + prior US cash session
```text
8/21 equity close
8/24 briefing
→ PRIOR_MARKET_SESSION
```

### Missing temporal fields + genuinely new same-day macro release
If evidence proves it was newly published after prior cutoff:
may classify CURRENT_OBSERVATION even if cash equity market is closed.

### Insufficient metadata
Must be current-signal ineligible.

---

# 13. Stage A trigger rehearsal acceptance

Using the exact 19:34 rehearsal macro input:

Target:

```text
false-current macro claims = 0
legacy items defaulted current = 0
today_signal driven by ineligible legacy facts = 0
```

The resulting digest may be shorter.

That is acceptable.

---

# 14. Stage B root cause — shadow numeric registry

The prior rehearsal did not generate an AI candidate because the shadow numeric gate encountered approximately 210 unregistered investor-flow audit numeric paths.

This task must **inventory and type them**, not merely whitelist them.

---

# 15. Numeric registry principle

Every numeric field presented to the shadow/AI validation layer must be one of:

```text
REGISTERED_PROSE_ELIGIBLE
REGISTERED_AUDIT_ONLY
REGISTERED_INTERNAL_DERIVED
EXPLICITLY_EXCLUDED_NON_NUMERIC_CONTEXT
UNSUPPORTED_BLOCKING
```

The gate should not fail just because a valid audit-only numeric field is not allowed in prose.

But every numeric field must be accounted for.

---

# 16. Investor-flow audit categories

Classify actual paths into semantic families, likely including repository-equivalent:

- foreign flow
- institution flow
- retail flow
- other-corporation flow
- other-foreign flow
- full-participant reconciliation totals
- displayed-participant totals
- omitted-participant totals
- reconciliation difference
- window aggregates
- attribution materiality diagnostics
- coverage ratios
- signal-basis diagnostics
- ownership position
- audit counts

Do not assume these exact families; derive from actual paths.

---

# 17. Prose eligibility must remain narrow

Do not make all registered fields AI-claimable.

For each registry entry define:

```text
semantic_type
canonical_fact_or_relation_ref
unit
window
owner
prose_allowed
audit_only
allowed_sections
```

Examples:

### Canonical user-facing flow
May be prose-eligible if already supported by the supply contract.

### Reconciliation diagnostic
Usually:
`prose_allowed = false`

### Audit count / materiality helper
Usually:
`prose_allowed = false`

### Unknown/unverifiable numeric path
Remain blocking until understood.

---

# 18. No residual-derived participant leakage

The investor-flow repair explicitly prohibited inventing participant identity from residual arithmetic.

Numeric registry work must not reintroduce:

```text
reconciliation residual
→ prose participant flow
```

Audit-only residual/reconciliation numbers may be registered as non-prose diagnostics.

---

# 19. No institutional double counting

If institution total and institution subcomponents coexist:

- numeric registry may know both
- AI claim contract must not allow summing both as independent top-level participants

Preserve canonical reconciliation taxonomy.

---

# 20. Registry generation

Prefer deterministic generation from canonical investor-flow schema/contract rather than manually writing hundreds of path strings.

Allowed:

```text
canonical field schema
→ registry entries
```

Forbidden:

```text
if path startswith "investor_flow":
    allow
```

No broad wildcard bypass.

---

# 21. Unknown field behavior

After implementing registry coverage:

Any newly appearing unrecognized numeric investor-flow path must still fail closed.

Do not make the gate permissive to future unknown fields.

---

# 22. AI claim gate remains unchanged/strict

The recently separated shadow/production gate allowed fallback packet persistence.

This task must not weaken the AI claim gate.

Desired behavior:

```text
all numeric fields accounted for
        ↓
AI candidate generation allowed
        ↓
AI may only claim prose-eligible registered fields
        ↓
numeric/semantic validator remains strict
```

---

# 23. Registry coverage acceptance

Report:

```text
verified unregistered before = N
accounted after = N
prose eligible = X
audit only = Y
internal derived = Z
unsupported blocking = 0
```

Do not claim closure if any unexplained numeric path remains.

---

# 24. Registry negative controls

Required:

- known audit-only field used in AI prose → reject
- known prose-eligible canonical flow field → allowed with Fact ref
- unknown new numeric path → block
- wrong window → reject
- wrong participant semantic → reject
- reconciliation residual as participant → reject
- institution total + subclass double count → reject

---

# 25. Stage C — immutable 19:34 rehearsal replay

After Stage A/B implementation, replay the exact rehearsal:

`2026-08-24-kr-live-rehearsal-193419`

Use its immutable captured data and cutoff.

Do not recollect providers for this first acceptance replay.

Required target:

```text
packet_count = 1
dry_run_intent_count = 8
duplicate_intents = 0
orphan_intents = 0

macro_temporal = PASS
investor_flow = PASS

AI_candidate_generated = YES
fallback_bundle_complete = YES

Trade_AR_user_visible = 0
production_DB_mutation = 0
Telegram_send = 0
```

---

# 26. AI candidate acceptance

For the immutable rehearsal:

Generate the AI candidate now that numeric registry coverage is complete.

Record:

- generation status
- correction attempts
- numeric validation
- semantic validation
- final-language validation
- runtime-quality validation

Target factual hard errors:

`0`

If only a P2 runtime-quality issue remains and fallback is safe:
report separately.

Do not loosen validators.

---

# 27. AI/fallback Inventory parity

The prior rehearsal had safe Inventory facts but could not observe AI parity.

After repair compare AI vs fallback:

- selected tickers
- Inventory context IDs
- Fact IDs
- relation IDs
- balance dates
- relation direction
- numeric values
- suppression reasons
- FCF redundancy handling

Mismatch target:

`0`

Set:

```text
INVENTORY_USER_VISIBLE_REHEARSAL =
PASS / FAIL / NOT_OBSERVED
```

PASS requires at least one selected Inventory context and zero factual/semantic mismatch.

Still do not call it natural proof.

---

# 28. Trade AR negative control

Hard target:

```text
exact Trade AR user-visible enrichment = 0
broad AR enrichment = 0
AP enrichment = 0
```

The canary/shadow layer may use exact Trade AR if allowed by 9.1D, but user-visible mode remains OFF.

---

# 29. Investor-flow rehearsal acceptance

For all active KR names:

```text
reconciliation errors = 0
unsupported absorber attribution = 0
residual-derived participant claims = 0
mixed-window timeless signal = 0
```

AI and fallback must use the same attribution-safe contract.

---

# 30. Macro temporal rehearsal acceptance

For all macro facts in the replay:

```text
false-current claims = 0
missing temporal metadata defaulted current = 0
reference-only facts creating today_signal = 0
AI/fallback temporal mismatch = 0
```

---

# 31. Exact final message previews

Create exact non-delivery message bundles for:

A. validated AI candidate, if valid

B. deterministic fallback

Include:
- market digest
- all stock messages
- exact order

Mark:

`REHEARSAL REPLAY — NOT SENT`

Audit:
- Inventory wording
- investor-flow wording
- macro temporal wording
- price/RR
- valuation
- data cautions
- duplication

---

# 32. Optional fresh current rehearsal after immutable replay PASS

Only after immutable replay passes all P0/material-P1 gates:

perform **one** additional fresh current no-delivery rehearsal using current time/cutoff if operationally safe.

Purpose:
prove compatibility layer + registry also work on newly collected data.

Rules:

- new rehearsal ID
- no production DB mutation
- no Telegram
- no Scheduled Task
- one normal collection pass only
- distinguish from the 19:34 replay
- do not overwrite earlier rehearsal artifacts

If current market/provider conditions make a fresh rehearsal inappropriate:
skip it and report reason.

The immutable replay is the mandatory acceptance proof.

---

# 33. Production notification / DB isolation

Before and after all replay/rehearsal steps verify no changes to:

- production notificationdelivery rows
- sent_at
- production packet archive
- official assessment DB
- warnings
- thesis history
- Pilot
- feature modes
- schedules

Any unintended mutation = P0.

---

# 34. Natural states remain pending

Even after a complete PASS:

```text
KR_PRODUCTION_NATURAL = PENDING
INVENTORY_USER_VISIBLE_NATURAL = PENDING / existing state
KR_INVESTOR_FLOW_NATURAL = PENDING
MACRO_TEMPORAL_NATURAL = PENDING
US_AI_COMPATIBILITY_NATURAL = existing state
```

Do not manufacture natural proof.

What this task closes is:
- code compatibility
- end-to-end non-delivery readiness

---

# 35. Implementation promotion gate

Set:

`LEGACY_MACRO_AND_SHADOW_REGISTRY_REPAIR_READY = YES/NO`

YES requires:

- legacy macro fail-open path eliminated
- no missing temporal metadata defaults current
- all legacy compatibility negative controls PASS
- verified shadow numeric fields fully accounted
- no unexplained numeric path
- audit-only values not prose-eligible
- AI candidate generated
- AI numeric/semantic hard errors = 0
- fallback bundle complete
- Inventory AI/fallback parity PASS
- Trade AR leakage = 0
- investor-flow PASS
- macro temporal PASS
- production DB mutation = 0
- Telegram = 0
- full tests/CI PASS

---

# 36. Full regression suite

Preserve:

- macro-digest-temporal-eligibility-v1 for new briefings
- 2026-08-24 US normal temporal replay
- KR packet/shadow decoupling
- KR producer non-trading-day guard
- packet-before-intent invariant
- KR investor-flow reconciliation
- Inventory user-visible selector
- Trade AR OFF
- Phase 9.0E cash flow
- current-price RR
- valuation
- exactly-once/receipts
- KRX role-target
- night-futures telemetry/session basis

---

# 37. Full validation

Required:

- focused legacy temporal tests PASS
- focused shadow registry tests PASS
- numeric-registry negative controls PASS
- immutable 19:34 replay PASS
- AI candidate validation PASS
- AI/fallback factual parity PASS
- Inventory parity PASS
- investor-flow PASS
- macro temporal PASS
- production isolation PASS
- full pytest PASS
- Ruff PASS
- `git diff --check` PASS
- Investment Knowledge parity PASS
- Chart Knowledge parity PASS
- Public Action/schema unchanged unless explicitly justified
- exact implementation SHA Actions PASS
- exact final main SHA Actions PASS after promotion

---

# 38. Promotion

After readiness YES:

- promote cleanly to main
- sync operating
- restart API only if imported runtime code requires it
- `/health` PASS
- worktrees clean
- Inventory mode unchanged
- Trade AR unchanged
- Production Assist OFF
- schedules unchanged

Do not manually run actual production after promotion.

---

# 39. Required architecture docs

Create/update:

1. `docs/architecture/MACRO_DIGEST_TEMPORAL_ELIGIBILITY.md`
   - add legacy rehydration/fail-closed compatibility

2. `docs/architecture/SHADOW_NUMERIC_REGISTRY.md`
   - investor-flow registry semantics
   - prose-eligible vs audit-only
   - unknown-path fail-closed behavior

3. if appropriate update:
   `docs/architecture/KR_PRODUCTION_PACKET_AND_SHADOW_GATE_SEPARATION.md`
   - document that registry readiness affects AI/shadow claims but not safe packet persistence

---

# 40. Required reports

Create:

1. `docs/reports/20260824-legacy-macro-temporal-root-cause.md`
2. `docs/reports/20260824-legacy-macro-temporal-rehydration-audit.md`
3. `docs/reports/20260824-legacy-macro-temporal-negative-controls.md`
4. `docs/reports/20260824-shadow-investor-flow-numeric-field-inventory.md`
5. `docs/reports/20260824-shadow-investor-flow-registry-classification.md`
6. `docs/reports/20260824-shadow-investor-flow-registry-negative-controls.md`
7. `docs/reports/20260824-rehearsal-193419-post-repair-replay.md`
8. `docs/reports/20260824-rehearsal-193419-ai-fallback-parity.md`
9. `docs/reports/20260824-rehearsal-193419-inventory-parity.md`
10. `docs/reports/20260824-rehearsal-193419-macro-temporal-validation.md`
11. `docs/reports/20260824-rehearsal-193419-investor-flow-validation.md`
12. `docs/reports/20260824-legacy-macro-shadow-registry-validation.md`
13. `docs/reports/20260824-legacy-macro-shadow-registry-readiness.md`

If optional fresh current rehearsal is performed:
14. `docs/reports/20260824-post-repair-fresh-rehearsal.md`

Recommended JSON:

`docs/reports/20260824-legacy-macro-shadow-registry-readiness.json`

---

# 41. Exact message bundle

Create:

`docs/reports/20260824-rehearsal-193419-post-repair-message-bundle.md`

Include:

- validated AI market digest + stock messages if AI candidate passes
- deterministic fallback market digest + stock messages
- selected production-preference bundle
- no-send watermark

No Telegram destination identifiers.

---

# 42. Complete report bundle

Create:

`20260824-legacy-macro-shadow-registry-closure-bundle.zip`

Include sanitized:

- macro root cause/rehydration
- registry inventory/classification
- negative controls
- immutable replay
- AI/fallback parity
- Inventory parity
- investor-flow validation
- macro validation
- message bundle
- readiness JSON
- optional fresh rehearsal report if performed

Report SHA-256.

---

# 43. Completion report — repository

Report:

- instruction path
- instruction commit
- branch
- base
- implementation
- final
- previous main
- final main
- operating
- promotion method
- API restart
- health
- worktrees
- deviations

---

# 44. Completion report — legacy macro

Report:

```text
LEGACY_MACRO_TEMPORAL_REHYDRATION = PASS/FAIL

legacy items inspected = N
rehydrated = N
insufficient-metadata fail-closed = N
defaulted CURRENT_OBSERVATION from missing metadata = 0
false-current claims = 0
```

Also:
- exact consumers changed
- whether historical persisted briefings were mutated: target NO

---

# 45. Completion report — shadow registry

Report:

```text
verified unregistered numeric paths before = N
accounted after = N
prose eligible = X
audit only = Y
internal derived = Z
unsupported blocking = 0
unknown wildcard allow = 0
```

Also:
- AI claim gate changed? expected NO / stricter-neutral only
- residual-derived participant prose eligibility = 0

---

# 46. Completion report — immutable rehearsal

Report:

```text
REHEARSAL_ID = 2026-08-24-kr-live-rehearsal-193419

packet_count = 1
dry_run_intents = 8
duplicates = 0
orphans = 0

AI_candidate_generated = ...
AI_numeric = ...
AI_semantic = ...
AI_final_language = ...
AI_runtime_quality = ...

fallback_bundle = ...

INVENTORY_USER_VISIBLE_REHEARSAL = ...
TRADE_AR_USER_VISIBLE_ENRICHMENT = 0

KR_INVESTOR_FLOW_REHEARSAL = ...
MACRO_TEMPORAL_REHEARSAL = ...

production_db_mutation = 0
telegram_send = 0
```

---

# 47. Final status

Successful completion should report:

```text
LEGACY_MACRO_TEMPORAL_REHYDRATION = PASS
SHADOW_INVESTOR_FLOW_NUMERIC_REGISTRY = PASS

KR_PRODUCTION_REPAIRED_LIVE_REHEARSAL = PASS
KR_PACKET_DELIVERY_DRY_RUN = PASS

AI_CANDIDATE_REHEARSAL = PASS
INVENTORY_USER_VISIBLE_REHEARSAL = PASS
KR_INVESTOR_FLOW_REHEARSAL = PASS
MACRO_TEMPORAL_REHEARSAL = PASS

TRADE_AR_USER_VISIBLE = OFF_PENDING_NATURAL_PROOF

OPEN_P0 = 0
OPEN_MATERIAL_P1 = 0

LEGACY_MACRO_AND_SHADOW_REGISTRY_REPAIR =
DEPLOYED_PENDING_NATURAL

NEXT_ACTION =
WAIT_FOR_FIRST_SUCCESSFUL_KR_NATURAL_PACKET
```

If AI runtime-quality has only a P2 issue but factual/semantic validation passes and fallback is complete:
state that separately without converting it into P1 automatically.

---

# 48. Final philosophy

The 19:34 rehearsal found two different compatibility gaps.

The first was dangerous:

```text
missing legacy temporal metadata
→ treated as current
```

That must become:

```text
rehydrate from evidence
or
fail closed as non-current
```

The second prevented AI comparison:

```text
valid investor-flow audit numerics
→ unregistered
→ shadow candidate suppressed
```

That must become:

```text
every numeric field explicitly accounted for
→ only semantically safe fields prose-eligible
→ audit diagnostics remain non-prose
→ unknown fields still block
```

Do not solve either problem by weakening safety.

The target end state is:

```text
safe packet
+ complete deterministic fallback
+ valid AI candidate
+ Inventory parity
+ safe investor-flow interpretation
+ temporally honest macro digest
+ zero user/production mutation
```

Then the next scheduled KR packet only has to prove the natural scheduler/delivery lifecycle—not basic code correctness.
