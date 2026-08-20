# thesis-monitor — Phase 9.0D Work Instruction

## Metadata

- Phase: `9.0D`
- Title: `Selective Cash-Flow Runtime Shadow Canary`
- Instruction version: `1.0`
- Date: `2026-08-20 KST`
- Repository: `sskim-ai/thesis-monitor`
- Intended base/main/operating at instruction creation: `32504d4604fd5e5d4a2bd65b42f973a45ce19445`
- Previous phase: `9.0C Cash Flow Shadow Consumption & Earnings-Quality Reasoning Integration`
- Previous phase result: `PHASE_9_0D_READY = YES`
- Target scope: `SELECTIVE_CASH_FLOW_RUNTIME_SHADOW_CANARY`
- Production Assist: `OFF`
- User-visible cash-flow exposure in this phase: `NO`

---

# 0. Instruction-repository protocol

Store this instruction at:

`docs/work-instructions/20260820-phase-9-0d-selective-cash-flow-runtime-shadow-canary.md`

If `docs/work-instructions/README.md` does not exist, create it using the repository work-instruction policy.

Before implementation:

1. Fetch latest origin.
2. Verify the active instruction file.
3. Commit/push the instruction as a docs-only commit if not already present on the implementation base.
4. Record `instruction_path`, `instruction_commit_sha`, and `instruction_version`.
5. Base the implementation branch on the latest safe main descendant containing the instruction commit, or explicitly reconcile any main drift.
6. Do not silently modify this instruction during implementation. Material amendments require a new committed instruction version.

Recommended implementation branch:

`codex/phase-9-0d-selective-cash-flow-runtime-shadow-canary`

---

# 1. Phase purpose

Phase 9.0A established the evidence architecture.

Phase 9.0B implemented canonical OCF, PPE CAPEX, and PPE-only derived FCF with deterministic lineage.

Phase 9.0C proved archive-only shadow consumption with:

- universe: 20
- consumption eligible: 12
- actual shadow use: 10
- full FCF reasoning: 9
- OCF-only reasoning: 1
- current formal: 10
- formal-lagging-provisional: 2
- blocked: 7
- insurance N/A: 1
- cash-flow Unknowns: 17 → 8 resolved / 8 still valid / 1 N/A suppressed
- numeric binding: automatic only
- PIT errors: 0
- stale-as-current errors: 0
- KR leakage errors: 0
- human quality: material improvement 8 / minor 4 / no change 8 / degraded 0

Phase 9.0D has one purpose:

**Run the already-validated cash-flow sidecar against real natural runtime packets without allowing it to influence production delivery.**

Desired topology:

```text
Natural Scheduled Task
        ↓
Production packet / normal production path
        ↓
Production validation / delivery / fallback / receipt
        ↓
Delivery outcome finalized independently
        ↓
Immutable live packet reference
        ↓
Cash-flow runtime shadow sidecar
        ↓
Shadow AI interpretation
        ↓
Shadow numeric binding
        ↓
Shadow semantic / PIT / freshness / quality validation
        ↓
Canary receipt + immutable archive
```

The shadow canary must never become a prerequisite for production delivery.

---

# 2. Core success definition

9.0D does not ask whether more FCF numbers were shown.

It asks whether, on a real naturally generated packet, the 9.0C consumption contract behaved as designed while production behavior remained unchanged.

Success requires:

- production delivery independence
- exact live-packet lineage
- no look-ahead
- no stale-as-current
- no KR blocked-data leakage
- no FCF fabrication
- no management/backend FCF confusion
- no cash-flow-based valuation fabrication
- no Telegram delivery count/content change caused by canary
- no exactly-once / receipt regression
- canary failures isolated from production exit status

---

# 3. Hard prohibitions

Do not:

- inject cash-flow sidecar into the actual production AI candidate
- change actual Telegram text because of cash flow
- change fallback text because of cash flow
- change Public Action `0.4.5`
- change output schema `4`
- change `daily-review-v3.10`
- change the four AI Scheduled Task IDs or schedules
- manually execute US/KR Scheduled Tasks
- manually send Telegram
- mutate Pilot
- manually mutate DB
- enable Production Assist
- create FCF Yield, FCF/share, EV/FCF, P/FCF
- create CCC, DSO, DPO, Inventory Days
- create standard ROIC or ROIC proxy
- repair KR OpenDART period context in this phase
- infer KR cash-flow period
- convert currencies for prettier shadow prose
- use future filings relative to packet cutoff
- substitute stale old FCF when latest formal period is blocked
- count a manual replay as natural canary proof
- treat canary failure as production delivery failure
- let canary exit status trigger backup/double delivery
- alter production receipt because canary failed
- rewrite prior run archives or receipts

---

# 4. Current runtime baseline verification

At task start:

```bash
git fetch origin
git status
git rev-parse HEAD
git rev-parse origin/main
```

Known prior operating SHA:

`32504d4604fd5e5d4a2bd65b42f973a45ce19445`

Actual latest `origin/main` is authoritative.

Verify:

- working tree clean
- API health
- policy `daily-review-v3.10`
- schema `4`
- AI mode `shadow`
- Production Assist `OFF`
- US primary `08:15 KST` ACTIVE
- US backup `08:30 KST` ACTIVE
- KR primary `16:15 KST` ACTIVE
- KR backup `16:55 KST` ACTIVE
- KRX telemetry `08:05 / 16:05` unchanged

---

# 5. Read before coding

Read the latest repository artifacts for:

## Phase 9.0A
- Cash Flow / Capital Efficiency architecture
- provider coverage
- active-universe coverage
- FCF eligibility
- industry applicability
- readiness

## Phase 9.0B
- canonical-core implementation
- active-universe results
- lineage verification
- FCF reproduction
- period derivation
- eligibility results
- canonical facts

## Phase 9.0C
- `CASH_FLOW_SHADOW_CONSUMPTION.md`
- PIT audit
- freshness audit
- comparable-period audit
- industry-reasoning audit
- Unknown-resolution audit
- before/after report
- shadow AI preview
- validation
- readiness
- shadow-context JSON if present

Also read:

- runtime reasoning ownership
- runtime message specificity
- numeric-fact references
- final language gate
- runtime message quality
- receipt/exactly-once contracts
- task orchestration / backup logic
- immutable archive conventions

Repository evidence is source of truth.

---

# 6. Integration architecture decision

First trace the exact production lifecycle.

Document the real order of:

1. deterministic packet creation
2. production AI generation
3. production validator
4. fallback eligibility
5. Telegram delivery
6. receipt creation
7. archive completion / delivery result
8. process exit code
9. primary/backup interaction

Do not guess.

Default preference:

**Run the shadow canary after production delivery outcome is finalized and immutable packet/delivery artifacts exist.**

This is preferred because:

- canary cannot delay Telegram
- canary cannot influence fallback
- canary cannot influence exactly-once
- canary cannot alter primary/backup decision
- the same natural packet can still be used

If repository architecture supports a safer equivalent isolation mechanism, use it and explain why.

---

# 7. Canary failure isolation

Required invariant:

```text
Production result = independent
Canary result = observational
```

If canary:

- times out
- AI generation fails
- validator fails
- archive write fails

then:

- production sent result remains unchanged
- production exit status remains unchanged
- backup task must not be triggered because of canary failure
- existing receipt remains valid
- canary gets its own failure receipt/state

No canary exception may escape into the delivery decision path.

---

# 8. Runtime sidecar source

The live canary must use the exact naturally generated packet.

Required references:

- packet ID
- assessment date
- market
- packet SHA if available
- policy
- schema
- monitored thesis version context
- source cutoff time
- exact production run identity

Cash-flow sidecar must be built from:

- Phase 9.0B canonical cash-flow facts
- Phase 9.0C PIT gate
- Phase 9.0C freshness gate
- Phase 9.0C comparable-period selector
- industry applicability
- materiality selector

No separate runtime cash-flow truth path.

---

# 9. Point-in-time runtime gate

For every natural packet:

```text
source filing/publication availability <= packet cutoff
```

must hold.

The fact may have been canonicalized later in software time, but its source availability must have existed by the natural packet cutoff.

If source availability date is missing, fail closed according to the existing PIT contract.

Future-filing leakage target:

`0`

---

# 10. Freshness runtime gate

Preserve Phase 9.0C behavior.

Possible internal usage states should map to existing equivalent concepts for:

- current formal
- formal-lagging-provisional
- stale context only
- blocked
- not applicable

Do not invent arbitrary day thresholds.

Important controls:

- TSM/WRD formal-lagging-provisional behavior remains suppressed/context-only where appropriate.
- old safe FCF never replaces a blocked newer formal period and is never called current.
- KR blocked OpenDART data must not leak.

---

# 11. Natural US canary behavior

US/foreign is the primary positive canary because Phase 9.0C found usable cash-flow context there.

The first naturally generated US packet should exercise, if present:

- at least one full FCF context
- HUT-style OCF-only context
- at least one CAPEX-heavy company
- at least one memory/semiconductor case
- at least one pre-profit/negative-FCF case where available
- formal-lagging-provisional suppression if applicable

Do not hard-code tickers into eligibility logic.

Ticker names may be used only in tests/audits.

---

# 12. Natural KR canary behavior

KR is primarily a negative control.

Expected:

- KR OpenDART cash-flow period context remains fail-closed
- cash-flow numeric injection into KR shadow reasoning = 0 unless a subject legitimately becomes eligible through pre-existing canonical logic
- Korean Re generic enterprise FCF remains N/A
- no hidden period inference
- no stale/ambiguous cash-flow substitution

KR lack of cash-flow coverage is not 9.0D failure by itself.

---

# 13. OCF-only control

If OCF is eligible but PPE CAPEX / FCF are blocked:

Allowed:

- operating cash generation/consumption context
- specific statement that FCF cannot be derived safely, when decision-relevant

Forbidden:

- infer FCF sign
- infer FCF amount
- phrase OCF as FCF
- treat missing CAPEX as zero

HUT-style OCF-only behavior must remain safe.

---

# 14. Full FCF control

When full FCF is consumption-eligible:

AI may use:

- OCF
- PPE CAPEX
- PPE-only FCF
- safe deterministic relation to compatible business/earnings evidence

But:

- exact numbers bind to canonical fact refs
- FCF binds to the derived FCF fact, not AI arithmetic
- CAPEX scope remains PPE-only
- company/management-defined FCF is not implied

---

# 15. Earnings-quality live reasoning

Allowed relationships include only evidence-supported interpretations.

- Revenue/earnings up + OCF/FCF up: may support stronger cash-conversion context; no automatic investment-logic strengthening.
- Earnings up + OCF down: may flag accounting-profit/cash-conversion divergence; do not claim working-capital cause without evidence.
- OCF positive + FCF negative: may indicate reinvestment absorption; do not call it operating cash burn.
- FCF improves because CAPEX falls: do not automatically label earnings quality improved.
- Negative biotech FCF: cash-burn context allowed; do not infer runway months without facts.
- Memory-cycle strong FCF: do not infer permanent structural FCF.

---

# 16. Cash-flow reasoning ownership

Preserve existing reasoning ownership.

Primary exact numeric owner:

`business_earnings` / earnings-quality context

Do not duplicate exact OCF/CAPEX/FCF numbers across:

- core judgment
- valuation
- price
- observer
- holder
- next-check

unless an existing typed ownership/transition contract explicitly permits it.

Core judgment may summarize meaning without repeating all exact numbers.

---

# 17. Resolved Unknown live behavior

If the live canary has fresh, consumption-eligible canonical FCF:

Forbidden:

> FCF is unavailable / cannot be checked

for the same semantic scope.

If OCF is available but FCF is blocked, the Unknown must be specific to missing/blocked PPE CAPEX or FCF derivation.

For stale context, do not say "there is no FCF" when historical canonical facts exist.

Contradictory Unknown target:

`0`

---

# 18. Numeric binding

Every exact number in shadow canary output must use the existing numeric provenance system.

Targets:

- automatic binding: 100%
- manual: 0
- rejected: 0
- unresolved: 0

Semantic types must distinguish:

- operating cash flow
- PPE CAPEX
- PPE-only FCF

No AI-side arithmetic.

---

# 19. Shadow semantic validator

The canary validator must reject at least:

- future_fact_used
- stale_as_current
- wrong period relation
- YTD described as quarter/QTD
- FCF claim without canonical FCF
- OCF described as FCF
- management_fcf_mislabel
- capex_scope_overclaim
- FCF/share
- FCF yield
- EV/FCF
- P/FCF
- CCC
- ROIC
- resolved_unknown_claimed_missing
- industry_not_applicable_cashflow
- unsupported runway inference
- cash-flow-only valuation-context change
- cash-flow-only thesis state change without required supporting evidence

Reuse existing validator architecture where possible.

---

# 20. Shadow runtime-quality gate

Apply the same relevant runtime-quality checks used by the production AI path.

Do not relax thresholds.

Check for new cash-flow boilerplate such as:

```text
OCF X, CAPEX Y, FCF Z
```

repeated across many tickers.

Structured sidecar tuples may repeat structurally.

Analytical prose must remain ticker/industry specific.

---

# 21. Canary candidate isolation

Required separate identities:

- production candidate ID
- shadow canary candidate ID
- shadow canary receipt ID
- packet ID

No overwriting.

The canary candidate must never be passed into:

- Telegram delivery
- fallback selection
- assessment persistence
- warning lifecycle
- Pilot success accounting

---

# 22. Canary persistence policy

Use immutable audit storage only.

Recommended canary artifact set:

- canary manifest
- cash-flow sidecar
- shadow input
- raw shadow AI output
- bound shadow output
- semantic validation
- runtime-quality receipt
- canary completion receipt

Do not use production `archive-complete` semantics if that marker has a specific delivery meaning.

Use a distinct canary completion marker/receipt.

---

# 23. Canary idempotency

Unique canary identity should include at minimum:

- packet ID
- cash-flow consumption contract version
- canary policy/version

Same natural packet processed twice:

- one logical canary
- retries attached to same identity
- no duplicate natural-proof count inflation

Backup task processing must not produce duplicate proof for the same canonical packet.

---

# 24. Primary / backup safety

Trace actual backup behavior.

The canary must not:

- change primary task success state
- make backup believe primary failed
- make backup resend Telegram
- create two independent natural-canary proofs for the same delivered packet without deduplication

If primary production succeeds but canary fails, production primary remains successful.

---

# 25. Canary performance isolation

Do not create an arbitrary millisecond budget.

Instead enforce:

- production delivery must not wait for canary result
- canary runs only after delivery finalization or equivalent non-blocking isolation
- record canary latency
- record AI latency
- record validator latency
- record archive latency

If resource contention affects production, classify severity and disable/isolate canary safely.

---

# 26. Canary failure states

Use existing vocabulary or equivalent precise states for:

- COMPLETE_PASS
- AI_GENERATION_FAILED
- NUMERIC_BINDING_FAILED
- SEMANTIC_VALIDATION_FAILED
- QUALITY_FAILED
- PIT_BLOCKED
- NO_CONSUMPTION_ELIGIBLE_CONTEXT
- ARCHIVE_FAILED
- DUPLICATE_SKIPPED

Do not collapse all failures into one generic error when more precise states are available.

---

# 27. No eligible context is valid

A natural packet may legitimately yield:

`NO_CONSUMPTION_ELIGIBLE_CONTEXT`

This is not failure if:

- eligibility was correctly evaluated
- no unsafe facts leaked
- production remained unaffected

---

# 28. Live value-add audit

For each naturally canaried ticker classify:

- MATERIAL_IMPROVEMENT
- MINOR_IMPROVEMENT
- NO_MEANINGFUL_CHANGE
- DEGRADED

Record:

- facts used
- Unknowns resolved
- remaining Unknown
- interpretation change
- message-length delta
- status-delta candidate if any

No status persistence.

---

# 29. Status-delta candidates

If shadow cash-flow reasoning proposes a different business-thesis assessment from production baseline, record:

- ticker
- production assessment
- shadow proposed assessment
- exact cash-flow facts
- other supporting facts
- interpretation
- whether required evidence contract is satisfied

Do not persist.

Cash-flow alone must not automatically change:

- business investment logic
- valuation context
- warning lifecycle

---

# 30. Natural proof is behavior-based

Do not invent a 3-run, 5-run, or arbitrary clean-session requirement.

Track:

- full FCF live consumption
- OCF-only live consumption
- stale/formal-lagging suppression
- blocked fact suppression
- KR fail-closed negative control
- Unknown resolution
- no user-visible influence
- no duplicate-delivery influence
- numeric provenance
- runtime quality

Each behavior is:

- OBSERVED_PASS
- OBSERVED_FAIL
- NOT_OBSERVED

Do not fabricate proof.

---

# 31. First natural US acceptance

The first natural US canary is sufficient for a readiness decision for the observed selective subset if:

- no open P0
- no open material P1
- production delivery isolation PASS
- at least one full-FCF path observed safely
- numeric binding PASS
- PIT/freshness PASS
- runtime quality PASS

Do not require every theoretical ticker class before moving forward.

Unobserved classes can remain excluded from later user-visible rollout.

---

# 32. KR negative-control acceptance

KR canary is successful if:

- blocked OpenDART cash flow does not leak
- Korean Re N/A remains correct
- production delivery remains unaffected

KR FCF coverage is not required.

---

# 33. P0 / P1 / P2

Continue Phase Advancement Rule v1.

## P0
Examples:

- future filing used
- stale FCF represented as current
- wrong OCF/CAPEX/FCF number
- wrong period/currency/entity
- KR blocked leakage
- canary changes production delivery
- canary causes duplicate delivery
- canary damages receipt/exactly-once
- canary candidate sent to Telegram

P0 blocks 9.0E.

## P1
Examples:

- live cash-flow reasoning materially distorts business interpretation
- CAPEX-heavy business treated as generic cash burn
- valid live FCF systematically omitted
- structural shadow quality failure

Bounded repair if material.

## P2
Examples:

- wording polish
- label placement
- minor verbosity
- optional management-FCF comparison
- unobserved ticker class
- optional formatting

P2 does not block 9.0E.

---

# 34. Next phase definition

If 9.0D passes:

`Phase 9.0E — Selective Cash-Flow User-Visible Integration`

Do not implement 9.0E in this task.

Potential selective rollout remains dynamically contract-driven, not ticker-hard-coded.

---

# 35. PHASE_9_0E_READY decision

After at least the first naturally generated US canary artifact is available, explicitly set:

`PHASE_9_0E_READY = YES` or `NO`

Overall `Natural AI-Assisted Delivery = PARTIAL` alone is not a blocker.

## YES minimum

- P0 open = 0
- material P1 open = 0
- natural US production isolation PASS
- observed full-FCF live path PASS
- numeric binding PASS
- PIT/freshness PASS
- semantic validator PASS
- runtime quality PASS
- actual production delivery unaffected
- cash-flow candidate never sent
- selective subset identifiable

KR negative control may remain `NOT_OBSERVED` for the initial YES only if 9.0E explicitly excludes KR until observed.

## NO

Must identify:

- exact P0/P1
- affected ticker/path
- root cause
- bounded repair

P2-only reasons cannot produce NO.

---

# 36. Runtime deployment sequence

Before promotion:

1. focused tests
2. production-isolation tests
3. full regression
4. full pytest
5. exact-SHA CI
6. verify zero user-visible diff
7. verify canary cannot affect production exit status
8. verify idempotency
9. verify artifact isolation
10. verify task configs unchanged

Then:

- clean main promotion
- operating sync
- API restart only if required
- health check
- AI tasks unchanged
- KRX telemetry unchanged
- Production Assist OFF

---

# 37. Morning freeze

Natural morning window:

- KRX telemetry `08:05 KST`
- US primary `08:15 KST`
- US backup `08:30 KST`

Recommended deployment freeze:

`07:55–08:40 KST`

If safe promotion is not completed before freeze:

- do not rush
- natural cycle runs on previous version
- promote after window
- use following natural session for canary proof

No manual compensation.

---

# 38. Tests — production isolation

Required tests:

1. production success + canary success → production unchanged
2. production success + canary AI failure → production unchanged
3. production success + canary validator failure → production unchanged
4. production success + canary archive failure → production unchanged
5. production fallback + canary success → fallback still exactly once
6. canary exception → no backup trigger
7. duplicate canary invocation → one logical canary proof
8. canary candidate → never enters Telegram sender

---

# 39. Tests — cash-flow semantics

Required:

- full FCF
- OCF-only
- blocked FCF
- formal-lagging-provisional
- stale context
- future filing
- negative OCF
- negative FCF
- OCF positive / FCF negative
- CAPEX increase/decrease
- management/backend FCF label separation
- foreign issuer-level FCF
- no per-share/yield
- insurance N/A
- KR OpenDART blocked
- resolved Unknown
- still-valid Unknown

---

# 40. Tests — runtime quality

Required:

- no portfolio-wide OCF/CAPEX/FCF boilerplate
- exact numbers have one primary owner
- core does not duplicate full cash-flow tuple
- industry-specific cash-flow reasoning
- no unsupported causality
- no automatic investment-logic status change
- no valuation-context change from FCF alone

Thresholds unchanged.

---

# 41. Regression suite

Must preserve:

- Phase 8.5.5 / 8.5.5.1 / 8.5.5.2
- run-27 / run-28 / run-29 repairs
- current PBR ownership
- CORZ typed valuation
- dynamic price context
- RR overlap guard
- confirmation lifecycle
- night-futures session/calendar
- fallback parity
- exactly-once
- receipt integrity
- KRX telemetry scheduler
- Phase 9.0B canonical core
- Phase 9.0C archive shadow consumption

---

# 42. Full validation

Required:

- focused 9.0D suite PASS
- full pytest PASS
- Ruff PASS
- `git diff --check` PASS
- Investment Knowledge parity PASS
- Chart Knowledge parity PASS
- Public Action `0.4.5`
- operationId `20/20 unique`
- schema `4`
- exact implementation SHA Actions Test/Lint PASS
- exact final SHA Actions Test/Lint PASS

---

# 43. Runtime mutation safety

During implementation/promotion:

- Manual Telegram: 0
- Manual Scheduled Task: 0
- Pilot mutation: 0
- DB manual mutation: 0
- archive rewrite: 0
- receipt rewrite: 0
- force push: 0
- Production Assist: OFF

Normal future natural scheduled execution is allowed.

---

# 44. Required architecture document

Create/update:

`docs/architecture/CASH_FLOW_RUNTIME_SHADOW_CANARY.md`

Document:

- runtime insertion point
- production isolation
- packet identity
- sidecar identity
- canary identity
- idempotency
- failure handling
- receipt/archive semantics
- natural-proof semantics
- user-visible boundary

---

# 45. Required implementation report

Create:

`docs/reports/20260820-phase9-0d-runtime-shadow-canary-implementation.md`

Include:

- exact integration path
- why insertion point is safe
- production failure isolation
- modules changed
- scheduler impact
- runtime-visible diff

---

# 46. Required validation report

Create:

`docs/reports/20260820-phase9-0d-validation.md`

Include:

- focused
- isolation
- regression
- full pytest
- semantic tests
- quality
- lint/diff/Knowledge/Action
- CI SHAs

---

# 47. Required pre-natural readiness report

Create before natural proof:

`docs/reports/20260820-phase9-0d-canary-readiness.md`

State:

- `RUNTIME_CANARY_DEPLOYED = YES/NO`
- `READY_FOR_NEXT_NATURAL_US_CANARY = YES/NO`
- production isolation verified
- task configuration unchanged
- expected artifact locations
- exact next natural slot
- Production Assist OFF

Do not claim natural PASS before it occurs.

---

# 48. Natural canary artifacts

Use runtime archive conventions, not tracked Git working tree.

Each completed canary should make it possible to locate by IDs/SHA:

- packet
- production delivery result
- sidecar
- raw shadow result
- bound result
- validation
- quality receipt
- canary receipt

---

# 49. Natural canary review report

After a natural canary actually occurs, generate read-only:

`docs/reports/<date>-phase9-0d-natural-canary-review.md`

Do not rewrite raw artifacts.

Include:

- packet ID
- market
- natural scheduled source
- production delivery mode/count
- production receipt status
- canary status
- cash-flow-consumed tickers
- full FCF count
- OCF-only count
- stale/blocked suppression count
- binding errors
- semantic errors
- quality errors
- production influence count
- duplicate influence count
- value-add classification
- P0/P1/P2

---

# 50. Natural proof states

Track separately:

## Runtime plumbing
- IMPLEMENTED_PENDING_NATURAL
- LIVE_PASS
- LIVE_FAIL

## Full FCF
- OBSERVED_PASS
- OBSERVED_FAIL
- NOT_OBSERVED

## OCF-only
- OBSERVED_PASS
- OBSERVED_FAIL
- NOT_OBSERVED

## Freshness suppression
- OBSERVED_PASS
- OBSERVED_FAIL
- NOT_OBSERVED

## KR blocked control
- OBSERVED_PASS
- OBSERVED_FAIL
- NOT_OBSERVED

Do not collapse these into one status.

---

# 51. Parallel KRX track

KRX telemetry remains independent.

Do not modify its code/config.

Completion report may read-only state:

- latest 08:05
- latest 16:05
- readiness

No additional provider calls for this task.

KRX completeness does not block 9.0D/9.0E.

---

# 52. KR OpenDART track

Keep:

`KR_OPENDART_PERIOD_RECOVERY_PRIORITY = MEDIUM`

Do not repair in 9.0D.

A natural KR canary with zero leakage proves fail-closed consumption, not KR coverage.

---

# 53. CCC / ROIC

Remain:

- CCC: DEFERRED
- Standard ROIC: DEFERRED

Any canary claim using either is a validator failure.

---

# 54. Work-instruction compliance

Completion report must include:

- instruction path
- instruction commit SHA
- instruction version
- implementation branch base
- deviation from instruction: YES/NO
- if YES: exact reason and safety impact

This policy becomes mandatory for subsequent phases.

---

# 55. Persistent state after implementation, before natural proof

If implementation/CI/promotion PASS:

```text
Phase 9.0D:
RUNTIME_CANARY_DEPLOYED_PENDING_NATURAL

Cash Flow Canonical Core:
IMPLEMENTED_SHADOW

Cash Flow Archive Shadow Consumption:
CLOSED_RETROSPECTIVE

Cash Flow Runtime Shadow:
DEPLOYED_PENDING_NATURAL

Cash Flow User Visible:
NOT_ENABLED

KR OpenDART Period Recovery:
MEDIUM_FOLLOWUP

CCC:
DEFERRED

ROIC:
DEFERRED
```

Do not set `PHASE_9_0E_READY = YES` before natural evidence.

---

# 56. Persistent state after natural proof

If the natural US canary passes minimum selective-subset gate:

```text
Cash Flow Runtime Shadow:
LIVE_PASS_SELECTIVE_SUBSET
```

Then explicitly decide:

`PHASE_9_0E_READY = YES/NO`

List NOT_OBSERVED behaviors separately.

Unobserved classes need not block selective rollout if excluded.

---

# 57. 9.0E selective rollout principle

If READY, do not recommend broad all-universe rollout.

Use an evidence-based scope such as:

- `SELECTIVE_MATERIAL_IMPROVEMENT_SUBSET`
- `SELECTIVE_FULL_FCF_CURRENT_FORMAL`

Actual eligibility remains dynamically contract-driven.

Never hard-code the Phase 9.0C tickers as permanent rollout tickers.

---

# 58. Independence from overall Natural AI-Assisted Delivery

Overall:

`Natural AI-Assisted Delivery = PARTIAL`

remains independent.

Production may send deterministic fallback while cash-flow shadow canary passes.

Do not fail 9.0D solely for unrelated production fallback.

Production AI-assisted success also does not automatically prove the cash-flow canary.

---

# 59. P0 interruption rule

If a natural runtime produces unrelated production P0:

- follow Phase Advancement Rule
- pause user-visible 9.0E decision if relevant
- repair P0
- preserve valid 9.0D evidence

If cash-flow canary causes P0:

- isolate/disable canary if needed
- targeted repair before user-visible integration

---

# 60. Completion-report format

## Repository
- instruction path
- instruction commit SHA
- instruction version
- branch
- base
- implementation
- final
- main
- operating
- push
- working trees

## Runtime architecture
- exact insertion point
- production isolation
- canary identity
- idempotency

## Production isolation
- Telegram diff
- fallback diff
- exit-code diff
- backup behavior
- receipt diff
- exactly-once diff

## Cash-flow runtime
- sidecar contract
- PIT
- freshness
- comparison
- materiality
- numeric ownership

## Tests
- focused
- isolation
- regression
- full
- Ruff
- diff
- Knowledge
- Action
- CI

## Operating
- API
- health
- policy
- schema
- AI mode
- Production Assist
- four AI tasks
- KRX telemetry

## Safety
- manual Telegram
- manual task
- Pilot
- DB
- archive rewrite
- receipt rewrite

## Pre-natural readiness
- runtime canary deployed
- next US natural slot
- expected artifacts
- natural proof not yet claimed

## Natural result, if available
- packet
- production delivery
- canary status
- consumed count
- full FCF
- OCF-only
- freshness suppression
- KR negative control
- errors
- value-add
- P0/P1/P2

## Final gate
- `PHASE_9_0E_READY = YES/NO/PENDING_FIRST_NATURAL_CANARY`
- exact reason
- if YES: selective scope
- if NO: bounded repair
- if pending: no manual run

---

# 61. Final philosophy

Phase 9.0D is not another financial-data research phase.

The canonical numbers already exist.
The archive-only reasoning already passed.

The remaining question is operational:

> Can the same cash-flow reasoning run on a real natural packet without touching the production decision path?

Invariant:

```text
Production delivery
        must remain independent
        of cash-flow shadow canary.
```

Therefore:

- canary success cannot improve production delivery
- canary failure cannot break production delivery
- canary output cannot be sent
- canary cannot change assessment persistence
- canary cannot change fallback eligibility
- canary cannot trigger backup delivery

The canary observes the real packet, interprets only validated canonical facts, and produces immutable shadow evidence.

A single natural US canary can be sufficient for a selective 9.0E readiness decision if the required behavior is actually exercised and no P0/material P1 appears.

Do not wait for an arbitrary number of runs.

Do not expand the phase because some ticker class was not observed.

Exclude unobserved classes from the selective rollout and continue.

The goal is not perfection before progress.

The goal is:

**safe selective progress with explicit boundaries.**
