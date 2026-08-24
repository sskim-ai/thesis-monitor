# thesis-monitor — KR Shadow-Cohort Activation Gate / Packet Persistence Repair

## Metadata

- Workstream: `Bounded P1 production-availability repair`
- Instruction version: `1.0`
- Date: `2026-08-24 KST`
- Repository: `sskim-ai/thesis-monitor`
- Intended current main/operating:
  `a2d217f5b041a0409ed165b8bd66b98f36c5ed05`
- IMPORTANT:
  resolve and use the actual latest safe `origin/main` before implementation; do not force the SHA above if main legitimately advanced.
- Triggering natural review:
  `2026-08-24 17:10 KR Natural Multi-Proof Review`
- Triggering production result:
  normal KR trading-day analysis completed `7/7`, but packet persistence was blocked by:
  `shadow_cohort_activation_gate_failed`
- Observed production delivery:
  `0 / 8`
- Wrong delivery:
  `0`
- Duplicate:
  `0`
- New orphan delivery rows:
  `0`
- Open P0:
  `0`
- Open material P1:
  `1`
- Current working-capital user-visible mode:
  `SELECTIVE_INVENTORY`
- Inventory user-visible:
  `ENABLED_PENDING_NATURAL`
- Exact Trade AR:
  `OFF_PENDING_NATURAL_PROOF`
- Macro temporal repair:
  `DEPLOYED_PENDING_NATURAL`
- KR investor-flow repair:
  deployed, natural proof pending
- KR non-trading-day producer repair:
  deployed
- Production Assist:
  `OFF`
- Public Action:
  `0.4.5`
- Output schema:
  `4`

The goal is to determine why a **normal eligible KR trading-day packet** was prevented from persistence by a shadow/cohort activation gate, and repair only the incorrect coupling while preserving all genuine safety gates.

---

# 0. Work-instruction repository protocol

Store this exact instruction at:

`docs/work-instructions/20260824-kr-shadow-cohort-activation-gate-packet-persistence-repair.md`

Before implementation:

```bash
git fetch origin
git status
git rev-parse HEAD
git rev-parse origin/main
```

Then:

1. verify actual latest safe main/operating SHA
2. verify the triggering natural review artifacts are available
3. commit/push this instruction as a **docs-only instruction commit**
4. record:
   - instruction path
   - instruction commit SHA
   - instruction version
   - implementation base SHA
5. create the implementation branch from the latest safe main descendant containing the instruction commit
6. no force push / history rewrite
7. do not silently edit the instruction after implementation begins

Recommended branch:

`codex/kr-shadow-cohort-activation-gate-packet-persistence-repair`

---

# 1. Do not assume the gate is wrong

The first task is a root-cause trace.

Determine which branch is true:

## Branch A — shadow gate is incorrectly blocking production packet persistence

Example:

```text
normal trading-day production target = valid
analysis = complete
production safety checks = pass
shadow cohort not activated / not eligible
        ↓
shared gate returns false
        ↓
packet persistence denied
```

If this is confirmed:
decouple the shadow gate from production packet persistence.

## Branch B — gate is a legitimate production safety gate but its inputs are wrong

Example:

```text
gate should protect production
but one required input was miscomputed / stale / missing
```

If confirmed:
repair the input/derivation, not the gate.

## Branch C — gate bundles both production-safety and shadow-readiness conditions

If confirmed:
split the contract into explicit:
- production-blocking safety conditions
- shadow/canary-only readiness conditions

The completion report must state exactly:

`ROOT_CAUSE_BRANCH = A / B / C`

Do not bypass the gate before this classification is proven.

---

# 2. Hard prohibitions

Do NOT:

- simply `return true` from the gate
- delete the gate
- disable all shadow/cohort checks
- weaken packet validation
- weaken numeric/semantic validation
- create a packet when the market/session target is invalid
- create delivery intents without a persisted packet
- change KR producer schedule
- manually rerun the natural KR task
- manually send Telegram
- query providers to recreate run evidence
- rewrite the original failed natural archive
- mutate historical receipts
- change Inventory mode
- enable Trade AR
- change Phase 9.0E
- change macro temporal logic
- change investor-flow logic
- change KRX/night-futures logic
- change Public Action/schema
- mutate Pilot
- perform ad hoc DB changes

Use immutable run/review artifacts for replay.

---

# 3. Triggering immutable run

Identify the exact canonical failed KR natural run associated with the 2026-08-24 review.

Record:

- producer run ID
- intended packet ID
- assessment date
- XKRX target date/session
- analysis start/end
- 7/7 analysis result
- shadow cohort state
- activation gate input
- activation gate result
- packet persistence attempt/result
- notification/delivery-intent state
- primary/backup behavior
- error/traceback
- exactly-once state

Do not assume a run number if repository evidence uses a different identifier.

---

# 4. Full activation-gate trace

Trace the gate from caller to every condition.

Produce a table:

```text
condition
source
value
production-safety relevance
shadow-only relevance
expected behavior
actual behavior
```

At minimum inspect conditions related to:

- market/session eligibility
- analysis completeness
- packet schema validity
- numeric/semantic validation readiness
- deterministic fallback availability
- shadow cohort membership
- shadow cohort activation
- canary readiness
- feature mode
- user-visible working-capital mode
- Production Assist mode
- previous natural proof state
- packet persistence policy
- delivery hold policy

Do not infer semantics from variable names alone.

---

# 5. Shadow cohort purpose

Document what `shadow_cohort` actually controls.

Answer:

1. Does it select subjects for:
   - shadow AI?
   - runtime canary?
   - experimental comparison?
   - production delivery?
2. Is cohort activation intended to be:
   - production-blocking
   - shadow-only
   - comparison-only
3. What historical phase introduced the gate?
4. What tests/docstrings/contracts define its intended semantics?
5. Is the gate still needed after later Phase 9.x feature transitions?

This must be evidence-driven.

---

# 6. Production packet persistence contract

Define/reuse an explicit contract:

`kr-production-packet-persistence-v1`

Conceptual production-blocking conditions should include only genuine production requirements, such as:

```text
valid market/session target
analysis complete enough for safe packet
packet schema valid
required canonical evidence valid
fallback path available
no P0 safety conflict
packet persistence succeeds
```

Do not include shadow/canary readiness unless architecture explicitly proves it is a production safety requirement.

---

# 7. Shadow/canary readiness contract

If shadow readiness is separate, model it separately.

Suggested conceptual contract:

`shadow-cohort-readiness-v1`

It may determine:

- whether shadow comparison runs
- whether canary runs
- which subjects enter shadow cohort
- whether shadow output is archived

It must not block safe production delivery unless explicitly documented as a hard safety dependency.

---

# 8. Production independence principle

Preferred architecture:

```text
production analysis
→ production packet
→ safe delivery path
        ↓
post-terminal / detached shadow or canary
```

If current repository intentionally runs shadow before terminal:
it still must distinguish:

```text
shadow unavailable
≠
production unsafe
```

unless a true production safety contract says otherwise.

---

# 9. Packet persistence ordering

Preserve the recent repair invariant:

```text
analysis
→ valid immutable packet persisted
→ packet-bound delivery intent
→ review/delivery
```

Do not reintroduce:
- intent before packet
- orphan pending
- packetless deliverable state

The current failure created no new orphan rows; that safety must remain.

---

# 10. Safe degradation when shadow gate fails

If the confirmed gate is shadow-only and shadow readiness fails:

Expected safe behavior:

```text
production packet persists
production delivery proceeds
shadow/canary = suppressed / failed / not eligible
shadow failure recorded separately
```

Do not hide the shadow failure.

It should remain auditable but non-blocking.

---

# 11. Legitimate production-blocking fixture

Create at least one fixture where production packet persistence **must still fail**.

Examples:

- invalid XKRX target
- packet schema invalid
- required deterministic fallback unavailable
- unsafe numeric provenance
- explicit production P0 gate

The repair is not complete unless such fixtures still fail closed.

---

# 12. Immutable run replay — before/after

Primary acceptance replay:

```text
same 2026-08-24 KR natural input
```

Before:

```text
analysis = 7/7
shadow_cohort_activation_gate = fail
packet persisted = no
delivery eligibility = none
sent = 0/8
```

After repaired replay:

```text
normal trading-day target = valid
analysis = 7/7
production safety gate = pass
packet persisted = yes
packet-bound delivery intents = valid
AI/fallback pipeline becomes reachable
8-message delivery eligibility exists
shadow/cohort state remains honestly represented
```

Do not actually send Telegram in replay.

---

# 13. Exact delivery-eligibility acceptance

Repaired replay should prove:

- market digest + 7 stock messages can enter the normal delivery pipeline
- no duplicate intents
- exactly one packet
- exactly one logical delivery intent per expected message
- packet linkage exists
- fallback path remains available

Do not require AI candidate success for packet persistence if deterministic fallback is a supported safe path.

---

# 14. AI / fallback relationship

Audit whether the activation gate accidentally depends on AI/shadow success.

Production contract should preserve:

```text
AI success
→ AI-assisted delivery

AI fail
→ deterministic fallback
```

A shadow AI/cohort failure must not eliminate the deterministic production packet if fallback is safe.

Do not weaken AI validators.

---

# 15. Inventory user-visible interaction

Current mode:

`SELECTIVE_INVENTORY`

The production packet must be able to carry Inventory context if it is naturally selected.

Do not change Inventory selection or enablement.

Repaired replay should verify:

- Inventory context does not cause the gate failure
- Inventory-off negative fixture also works
- Trade AR remains OFF

Do not claim Inventory user-visible natural LIVE PASS from replay.

---

# 16. Macro temporal interaction

Macro temporal repair remains independent.

The packet must include the current macro context according to existing temporal rules.

Do not alter macro temporal classification.

Repaired replay should ensure macro context can reach the packet.

---

# 17. Investor-flow interaction

The current investor-flow reconciliation repair remains independent.

Do not change supply wording/logic.

Repaired replay may verify the data survives packet persistence.

No natural proof from replay.

---

# 18. Normal-day producer natural path

The repaired architecture must support:

```text
valid trading-day target
→ 7/7 analysis
→ packet persisted
→ packet-bound intents
→ primary
→ backup only if needed
```

No shadow feature should silently suppress the whole packet unless explicitly production-critical.

---

# 19. Non-trading-day regression

Preserve the recently fixed behavior:

```text
no valid KR production target
→ analysis 0
→ provider calls 0
→ packet 0
→ notification 0
→ Telegram 0
→ safe no-op
```

The packet persistence repair must not bypass the producer role-target guard.

---

# 20. Gate naming / semantics

If the current `shadow_cohort_activation_gate` name is misleading because it contains production checks:

prefer to split/rename internal contracts for clarity.

Do not rename large APIs gratuitously.

The final code should make it obvious which condition can block production.

---

# 21. Structured denial reasons

Production packet denial should use explicit reasons, e.g. repository-equivalent:

- `INVALID_PRODUCTION_TARGET`
- `PACKET_SCHEMA_INVALID`
- `PRODUCTION_SAFETY_GATE_FAILED`
- `PACKET_PERSISTENCE_FAILED`

Shadow-only issues should use separate reasons:

- `SHADOW_COHORT_NOT_ACTIVE`
- `SHADOW_CANARY_NOT_ELIGIBLE`
- `SHADOW_VALIDATION_FAILED`

Do not reuse one generic `activation_gate_failed` for unrelated states if it obscures severity.

---

# 22. Runtime receipt / audit

If production proceeds while shadow is suppressed:

persist enough audit metadata to answer:

```text
production packet persisted = yes
shadow cohort eligible = no
shadow reason = ...
production influence = 0
```

Do not expose internal shadow metadata to user messages.

---

# 23. Backward compatibility

Historical packets/receipts must remain readable.

Do not rewrite old gate outcomes.

If contract versioning is required:
add a new internal version without breaking old archives.

---

# 24. Idempotency

Repeated replay/producer processing must not create:

- duplicate packet
- duplicate intents
- duplicate receipt
- duplicate shadow attempt

Same run/session must resolve deterministically.

---

# 25. Tests — root cause

Create targeted tests reproducing the exact natural failure condition.

At least:

- normal trading day
- analysis 7/7
- production-safe
- shadow cohort inactive/not eligible
- old code blocks packet
- new code preserves production packet while shadow is separately suppressed, **if Branch A/C**

If Branch B:
reproduce incorrect input and prove corrected input makes legitimate gate pass.

---

# 26. Tests — production-blocking safety

Required fixtures where packet must remain blocked:

- invalid target
- invalid packet schema
- hard numeric/provenance failure
- explicit production P0 condition
- packet write failure

Do not allow the fix to turn all gates non-blocking.

---

# 27. Tests — shadow failure isolation

Required:

- shadow cohort inactive
- shadow validation fail
- canary unavailable
- shadow timeout
- shadow exception

For shadow-only failures:

```text
production packet/delivery eligibility unaffected
shadow state records failure/suppression
```

where architecture says production is safe.

---

# 28. Tests — fallback availability

Required:

- AI unavailable/rejected
- deterministic fallback available
- packet persists
- delivery remains eligible

No coupling between AI/shadow success and safe packet persistence.

---

# 29. Tests — packet/delivery invariant

Required:

- packet persistence success → delivery intents may be created
- packet persistence fail → no deliverable intents
- no packet → fallback cannot send orphan rows
- retry idempotent
- no new orphan rows

---

# 30. Tests — Inventory/Trade AR

Required:

- Inventory mode ON, selected context → packet persists
- Inventory mode ON, no selected context → packet persists
- Trade AR remains OFF
- Trade AR user-visible enrichment = 0

No feature-mode changes.

---

# 31. Tests — non-trading-day guard

Required regression:

- Saturday
- Sunday
- XKRX holiday
- normal trading day

The new fix must not undo no-target producer guard.

---

# 32. Run-36 / triggering run replay

Create:

`docs/reports/20260824-kr-shadow-gate-run-replay.md`

Use the exact immutable triggering run.

Include:

- before gate input/result
- root cause
- after production gate result
- after shadow gate result
- packet persistence
- delivery-intent eligibility
- no-send replay
- exact differences

Do not mutate original run artifacts.

---

# 33. Full validation

Required:

- focused gate tests PASS
- triggering immutable replay PASS
- legitimate production-block tests PASS
- shadow-isolation tests PASS
- packet/delivery integrity PASS
- fallback path PASS
- Inventory regression PASS
- Trade AR OFF regression PASS
- macro temporal regression PASS
- investor-flow regression PASS
- non-trading-day producer regression PASS
- exactly-once/receipt regression PASS
- full pytest PASS
- Ruff PASS
- `git diff --check` PASS
- Investment Knowledge parity PASS
- Chart Knowledge parity PASS
- Public Action/schema unchanged unless explicitly justified
- exact implementation SHA Actions PASS
- exact final main SHA Actions PASS after promotion

---

# 34. Promotion gate

Set:

`KR_SHADOW_GATE_PACKET_REPAIR_READY = YES/NO`

YES requires:

- root cause branch proven
- open P0 = 0
- material implementation P1 = 0
- triggering replay packet persists
- legitimate unsafe fixtures still block
- no orphan intents
- fallback remains safe
- Inventory mode unchanged
- Trade AR OFF
- full regression PASS
- CI PASS
- main ancestry clean

---

# 35. Promotion

After readiness YES:

- clean promotion to main
- operating sync
- restart API only if imported runtime code requires it
- health PASS
- schedules unchanged
- Inventory mode unchanged
- Trade AR unchanged
- Production Assist OFF

Do not manually rerun KR production.

The next natural eligible KR packet becomes live proof.

---

# 36. Natural proof state

After implementation/promotion:

```text
KR_SHADOW_GATE_PACKET_REPAIR =
DEPLOYED_PENDING_NATURAL

KR_PRODUCTION_NATURAL =
PENDING
```

Do not claim LIVE PASS from replay.

A future natural trading-day packet can mark LIVE PASS when:

- analysis completes
- packet persists
- packet-bound intents exist
- AI or fallback delivers expected bundle
- duplicate = 0
- exactly-once PASS
- no orphan rows

---

# 37. Required architecture doc

Create:

`docs/architecture/KR_PRODUCTION_PACKET_AND_SHADOW_GATE_SEPARATION.md`

Document:

- root-cause branch
- production packet persistence contract
- shadow/cohort readiness contract
- blocking vs non-blocking conditions
- fallback independence
- packet/delivery ordering
- denial reason taxonomy
- natural proof lifecycle

---

# 38. Required reports

Create:

1. `docs/reports/20260824-kr-shadow-gate-root-cause.md`
2. `docs/reports/20260824-kr-shadow-gate-condition-inventory.md`
3. `docs/reports/20260824-kr-production-packet-persistence-contract.md`
4. `docs/reports/20260824-kr-shadow-production-decoupling.md`
5. `docs/reports/20260824-kr-shadow-gate-run-replay.md`
6. `docs/reports/20260824-kr-shadow-gate-negative-controls.md`
7. `docs/reports/20260824-kr-packet-delivery-integrity-regression.md`
8. `docs/reports/20260824-kr-shadow-gate-validation.md`
9. `docs/reports/20260824-kr-shadow-gate-readiness.md`

Recommended JSON:

`docs/reports/20260824-kr-shadow-gate-readiness.json`

---

# 39. Complete report bundle

Create:

`20260824-kr-shadow-cohort-packet-persistence-repair-bundle.zip`

Include sanitized:

- root cause
- condition inventory
- packet persistence contract
- decoupling report
- immutable replay
- negative controls
- packet/delivery regression
- validation
- readiness JSON

Report ZIP SHA-256.

---

# 40. Completion report — repository

Report:

- instruction path
- instruction commit SHA
- branch
- base
- implementation SHA
- final SHA
- previous main
- final main
- operating
- promotion method
- API restart
- health
- worktrees
- deviations

---

# 41. Completion report — root cause

Must state exactly:

```text
ROOT_CAUSE_BRANCH = A / B / C
```

and explain:

- what `shadow_cohort_activation_gate` was intended to protect
- which condition actually failed
- whether that condition should block production
- why the normal trading-day packet was denied
- exact files/functions changed

---

# 42. Completion report — triggering replay

Report:

```text
analysis_complete
production_target_valid
shadow_gate_before
production_gate_after
shadow_state_after
packet_persisted_before
packet_persisted_after
delivery_intents_before
delivery_intents_after
AI/fallback_reachable
Telegram_sent_in_replay = 0
```

---

# 43. Completion report — safety

Report:

- manual Telegram = 0
- manual production task = 0
- provider recreation = 0
- DB/Pilot mutation = 0
- archive rewrite = 0
- packet/delivery orphan created = 0
- Inventory mode changed = NO
- Trade AR changed = NO
- macro temporal changed = NO
- investor-flow changed = NO
- Production Assist = OFF

---

# 44. Final status

Successful completion should report:

```text
KR_PRODUCTION_PACKET_PERSISTENCE = PASS
KR_SHADOW_PRODUCTION_DECOUPLING = PASS
KR_PACKET_DELIVERY_INTEGRITY = PASS

OPEN_P0 = 0
OPEN_MATERIAL_P1 = 0

KR_SHADOW_GATE_PACKET_REPAIR =
DEPLOYED_PENDING_NATURAL

KR_PRODUCTION_NATURAL =
PENDING

INVENTORY_USER_VISIBLE =
ENABLED_PENDING_NATURAL

TRADE_AR_USER_VISIBLE =
OFF_PENDING_NATURAL_PROOF

NEXT_ACTION =
WAIT_FOR_FIRST_SUCCESSFUL_KR_NATURAL_PACKET
```

If a genuine production-blocking condition remains unresolved:
report the exact bounded blocker and do not claim PASS.

---

# 45. Final philosophy

The natural failure is not evidence that shadow safety should be removed.

It is evidence that production and shadow readiness must have explicit boundaries.

The correct question is:

```text
Is production unsafe?
```

not:

```text
Is every shadow cohort/canary feature ready?
```

A safe production packet should not disappear merely because an optional shadow cohort is inactive.

At the same time, a genuinely unsafe packet must remain blocked.

Success is:

> normal trading-day production reaches immutable packet persistence and the safe AI/fallback delivery path, while shadow/cohort failures are recorded independently and every real production safety gate remains fail-closed.
