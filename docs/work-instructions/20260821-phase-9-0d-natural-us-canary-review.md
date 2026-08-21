# thesis-monitor — 2026-08-21 US Natural Run Review Work Instruction

## Metadata
- Task: `READ_ONLY_NATURAL_RUN_REVIEW`
- Date: `2026-08-21 KST`
- Repository: `sskim-ai/thesis-monitor`
- Related phase: `9.0D Selective Cash-Flow Runtime Shadow Canary`
- Instruction version: `1.0`
- Known 9.0D instruction commit: `a24e4f2210f944fa7c43d8dbf8be1d1a8e652164`
- Known 9.0D implementation commit: `578d33e13dbbefe375275c64cd04e631a7141b84`
- Known main/operating before review: `3d6cfab1d881c336ff64c66466d12068aa51d1e4`
- Morning schedule: KRX `08:05`, US primary `08:15`, US backup `08:30` KST
- Production Assist: `OFF`
- Cash-flow user-visible integration: `OFF`

## 0. Work-instruction protocol
Store this file at:
`docs/work-instructions/20260821-phase-9-0d-natural-us-canary-review.md`

Before review:
1. `git fetch origin`
2. Verify `origin/main`, operating HEAD, and clean working trees.
3. Commit/push this instruction as a docs-only commit if not already present on the review base.
4. Record `instruction_path`, `instruction_commit_sha`, `instruction_version`.
5. Do not modify runtime/implementation code in this review.
6. Findings become evidence for the next task; do not fix them here.

Recommended branch:
`codex/20260821-us-natural-canary-review`

## 1. Result delivery — Git OR one ZIP
Preferred Git mode:
- `docs/reports/20260821-phase9-0d-natural-us-canary-review.md`
- `docs/reports/20260821-phase9-0d-natural-us-canary-review.json`
- optional `docs/reports/20260821-phase9-0d-natural-us-canary-artifact-index.md`
- commit/push on the review branch only; do not change main/operating.

ZIP fallback:
`20260821-phase9-0d-natural-us-canary-review-bundle.zip`

ZIP should contain the Markdown, JSON, and optional artifact index. Report ZIP SHA-256.

Never commit/package secrets, tokens, auth headers, or sensitive environment values. Raw runtime artifacts should remain immutable in their archive and be referenced by path/ID/SHA.

## 2. Hard prohibitions
- manual US primary/backup run: 0
- manual Telegram: 0
- provider call solely to recreate missing natural evidence: 0
- manual KRX provider call: 0
- Pilot/DB/assessment/warning mutation: 0
- archive/receipt rewrite: 0
- production code/scheduler/prompt/Public Action changes: 0
- Production Assist change: 0
- 9.0E implementation: 0
- KR OpenDART period recovery: 0
- CCC/ROIC work: 0
- manual replay counted as natural proof: 0

## 3. Start-state verification
Read-only verify:
```bash
git fetch origin
git status
git rev-parse HEAD
git rev-parse origin/main
```
Confirm:
- working trees clean
- API health if available
- policy `daily-review-v3.10`
- schema `4`
- AI mode `shadow`
- Production Assist `OFF`
- AI tasks: US 08:15/08:30, KR 16:15/16:55 unchanged
- KRX telemetry 08:05/16:05 unchanged

## 4. Identify today’s exact natural US run
Find the real `2026-08-21` natural US production run. Record:
- packet ID
- assessment date / market / policy / schema
- scheduler source
- primary/backup identity
- packet creation time
- production terminal time
- delivery time
- packet/archive references and SHA if available

If multiple runs exist, identify the canonical run and explain backup/duplicate/abandoned runs.

## 5. Reconstruct production lifecycle
Reconstruct:
`natural task → packet → production AI → validation → quality → eligibility → AI-assisted/fallback → Telegram → receipt → terminal state → backup interaction`

Record exact status at each stage before examining the cash-flow canary.

## 6. Production delivery review
Record:
- AI candidate generated
- semantic/numeric validation
- runtime quality
- final language
- delivery mode
- sent/expected/pending/failed/duplicate counts
- receipt
- exactly-once
- archive/delivery-result state

If fallback occurred, extract exact rejection/delivery reason and classify it separately from the cash-flow canary.

## 7. Natural AI-Assisted track
Evaluate independently:
- actual AI-assisted delivery or fallback
- prior reasoning-ownership/repetition repairs
- overall `Natural AI-Assisted Delivery` state

An unrelated production fallback does not automatically fail 9.0D.

## 8. Prior repair regression matrix
For each, mark `OBSERVED_PASS`, `OBSERVED_FAIL`, or `NOT_OBSERVED`.

Phase 8.5.5:
- depositary/security false positive
- `chart_risk_reward` framework leakage
- observer/holder ownership
- specific Unknowns/next checks

Phase 8.5.5.1:
- generic `현재 확인된 핵심 숫자는...`
- valuation EPS/BVPS leaking into business filler
- coarse typed numeric skeleton collision
- non-material prior/current RR repetition

Phase 8.5.5.2:
- structured supply tuple vs prose
- current RR primary ownership
- cross-section RR duplication
- generic inventory/CAPEX/FCF/ROIC boilerplate

## 9. Night-futures safety
Inspect existing natural artifacts only:
- current completed NIGHT availability
- preceding eligible DAY selection
- same contract
- stale substitution 0
- same-date later-DAY misbinding 0
- if incomplete lineage, user-visible suppression

Report session safety and whether live numeric exposure was observed.

## 10. KRX 08:05 telemetry
Read today’s already-generated 08:05 artifact if present:
- observation exists
- role
- target XKRX business date
- provider business date
- HTTP status
- row count / eligible rows
- publication readiness
- role-proof eligibility
- raw payload reference/SHA
- scheduler exit

No new provider call. KRX completeness does not block 9.0E.

## 11. Locate the 9.0D natural canary
For today’s exact US packet, locate:
- canary ID
- sidecar ID
- canary policy/version
- cash-flow consumption contract version
- invocation source
- canary receipt/completion artifact
- artifact hashes

Natural evidence requires scheduler-derived runtime invocation. Manual replay is not natural proof.

## 12. Verify insertion point and isolation
Prove from artifacts/timestamps that production terminal result was finalized before, or architecturally independently from, the canary.

Record:
- production terminal timestamp
- canary start/end
- whether production waited
- whether canary affected exit status

Target production influence: `0`.

## 13. Production isolation audit
Explicitly verify:
- Telegram content influence: 0
- Telegram count influence: 0
- fallback eligibility influence: 0
- exit-code influence: 0
- backup-trigger influence: 0
- production receipt influence: 0
- exactly-once influence: 0
- Pilot influence: 0
- assessment/warning persistence influence: 0

Any non-zero production impact is normally P0.

## 14. Canary status
Record exact state, using repository vocabulary or equivalents:
- COMPLETE_PASS
- AI_GENERATION_FAILED
- NUMERIC_BINDING_FAILED
- SEMANTIC_VALIDATION_FAILED
- QUALITY_FAILED
- PIT_BLOCKED
- NO_CONSUMPTION_ELIGIBLE_CONTEXT
- ARCHIVE_FAILED
- DUPLICATE_SKIPPED

If canary artifact is missing, distinguish invocation failure, pre-artifact crash, idempotent skip, no eligible context, and archive failure.

## 15. Canary coverage
For today’s packet record:
- monitored subjects
- canonical eligible
- consumption eligible
- actually consumed
- full FCF
- OCF-only
- CAPEX-only if supported
- formal-lagging-provisional suppressed/context-only
- stale suppressed
- blocked
- N/A
- ticker lists for each category

Eligibility remains contract-driven.

## 16. Full-FCF live audit
For every consumed full-FCF subject verify:
- OCF Fact ID
- PPE-CAPEX Fact ID
- derived FCF Fact ID
- FCF input Fact IDs
- issuer/period/currency/unit/entity/basis compatibility
- source availability <= packet cutoff
- freshness eligibility
- no AI-side FCF arithmetic

Targets:
- lineage errors 0
- arithmetic errors 0
- future-fact errors 0

## 17. OCF-only behavior
If naturally exercised:
- OCF is described only as OCF
- no FCF amount/sign inference
- missing CAPEX is not zero
- Unknown/caution names the FCF derivation limitation

Mark `OBSERVED_PASS/FAIL/NOT_OBSERVED`.

## 18. Freshness / formal-lagging-provisional
Verify naturally exercised lagging-formal cases:
- older formal cash flow remains canonical
- not described as current-quarter FCF
- suppressed/context-only according to 9.0C
- no old-FCF substitution for blocked newer period

Mark `OBSERVED_PASS/FAIL/NOT_OBSERVED`.

## 19. PIT audit
For every consumed Fact:
`source filing/publication date <= packet cutoff`

Record consumed count, PIT-valid count, future-fact suppressions, violations.

Target PIT violations: `0`.

## 20. Numeric binding
Record:
- automatic
- manual
- rejected
- unresolved
- formatting failures

Targets:
`manual=0`, `rejected=0`, `unresolved=0`.

Every exact OCF/PPE-CAPEX/FCF number must bind to canonical facts.

## 21. Semantic validation
Record exact errors. Target: `0`.

Explicitly check:
- future_fact_used
- stale_as_current
- wrong period relation / YTD-as-quarter
- FCF without canonical Fact
- OCF-as-FCF
- management/backend FCF confusion
- CAPEX scope overclaim
- unsupported FCF/share, FCF yield, EV/FCF, P/FCF
- CCC / ROIC
- resolved Unknown claimed missing
- N/A/insurance leakage
- unsupported runway inference
- cash-flow-only valuation change
- cash-flow-only thesis-state change

## 22. Runtime message quality
Record:
- substantive repetition
- typed/template repetition
- generic methodology repetition
- cash-flow boilerplate
- duplicate exact cash-flow numbers across sections
- Unknown specificity
- next-check specificity
- final language

Target runtime quality: `PASS`.
Threshold changes: `0`.

## 23. Unknown-resolution live audit
Compare production baseline vs canary:
- cash-flow Unknowns before
- resolved
- still valid
- N/A suppressed
- contradictory retained
- wrongly suppressed

Target contradictory retained: `0`.

Fresh FCF present + same-scope "FCF unavailable" is an error.
OCF-only must not be described as total cash-flow unavailability.

## 24. Earnings-quality value add
Classify each consumed ticker:
- MATERIAL_IMPROVEMENT
- MINOR_IMPROVEMENT
- NO_MEANINGFUL_CHANGE
- DEGRADED

Give one concise evidence-based reason per ticker.

Do not force improvement.

## 25. Status-delta candidates
If canary proposes a different investment-logic state:
- ticker
- baseline state
- shadow state
- cash-flow facts
- other supporting facts
- whether evidence rule is met

Persistence: `0`.

## 26. Length / numeric density
Record:
- baseline vs shadow message length
- delta %
- cash-flow numeric count

Check:
- no default three-number dump
- no broad verbosity expansion
- no portfolio-wide `OCF X / CAPEX Y / FCF Z` scaffold

No arbitrary length threshold.

## 27. Natural behavior matrix
Produce:

| Behavior | State | Evidence |
|---|---|---|
| Runtime canary plumbing | OBSERVED_PASS/FAIL | ... |
| Production isolation | OBSERVED_PASS/FAIL | ... |
| Full FCF consumption | OBSERVED_PASS/FAIL/NOT_OBSERVED | ... |
| OCF-only consumption | OBSERVED_PASS/FAIL/NOT_OBSERVED | ... |
| Freshness suppression | OBSERVED_PASS/FAIL/NOT_OBSERVED | ... |
| Blocked/stale suppression | OBSERVED_PASS/FAIL/NOT_OBSERVED | ... |
| Numeric provenance | OBSERVED_PASS/FAIL | ... |
| Semantic validation | OBSERVED_PASS/FAIL | ... |
| Runtime quality | OBSERVED_PASS/FAIL | ... |
| Unknown resolution | OBSERVED_PASS/FAIL/NOT_OBSERVED | ... |
| KR negative control | NOT_OBSERVED unless natural KR evidence exists | ... |

Do not fabricate unobserved proof.

## 28. P0/P1/P2
Classify every finding.

P0 examples:
- production influence
- wrong cash-flow number
- wrong period/currency/entity
- future filing
- stale-as-current
- KR blocked leakage
- duplicate/receipt/exactly-once damage
- canary candidate sent

P1 examples:
- materially distorted cash-flow interpretation
- CAPEX-heavy company mislabeled as generic cash burn
- valid current FCF systematically omitted
- structural quality failure

P2 examples:
- minor wording/placement/verbosity
- optional management-FCF comparison
- unobserved class
- KRX completeness

Report open P0, open P1, P2 backlog.

## 29. PHASE_9_0E_READY gate
After reviewing today’s real natural US canary, set exactly:

`PHASE_9_0E_READY = YES` or `NO`

### YES minimum
- natural US canary exists
- production isolation PASS
- at least one full-FCF live path OBSERVED_PASS
- P0 open = 0
- material P1 open = 0
- PIT PASS
- freshness PASS for consumed facts
- numeric binding PASS
- semantic validation PASS
- runtime quality PASS
- canary Telegram exposure = 0
- selective rollout subset identifiable

Unobserved classes may be excluded from 9.0E.

Overall production `Natural AI-Assisted Delivery = PARTIAL` alone does not block 9.0E.

KR may remain excluded from initial 9.0E.

### NO
Use NO only for a concrete P0/material P1 or because no valid full-FCF natural live path was observed.

If NO, provide exact blocker, severity, path/ticker, and bounded repair.

P2-only reasons cannot produce NO.

## 30. If YES
Do not implement 9.0E.

Recommend:
`Phase 9.0E — Selective Cash-Flow User-Visible Integration`

Initial rollout should be dynamically contract-driven and narrow, e.g.:
- current-formal full-FCF
- material-improvement subset
- KR excluded until separately approved
- formal-lagging-provisional excluded from current numeric display
- OCF-only separately gated if insufficiently observed

Do not hard-code permanent ticker lists.

## 31. If NO
Do not start broad research.

Recommend exactly one bounded repair:
- canary invocation/isolation
- PIT/freshness
- numeric binding
- semantic ownership
- runtime quality

If production safety was affected, state whether canary should be disabled pending repair.

## 32. Artifact index
Index without rewriting:
- production packet
- production AI candidate
- production validation
- production quality receipt
- fallback artifact if any
- delivery result
- production receipt
- canary manifest
- cash-flow sidecar
- shadow raw output
- shadow bound output
- shadow semantic validation
- shadow quality receipt
- canary receipt
- KRX 08:05 telemetry

For each include path/ref, SHA-256 if available, and immutable/original status.

## 33. Completion report
Include:

### Work instruction
- path
- commit SHA
- version

### Repository
- review branch
- base
- origin/main
- operating SHA
- working trees
- main/operating changes: expected 0

### Natural US run
- packet ID
- scheduler source
- primary/backup
- timestamps
- policy/schema

### Production outcome
- AI candidate/validation/quality
- delivery mode
- sent/expected/pending/failed/duplicate
- receipt/exactly-once

### Production AI track
- Natural AI-Assisted state
- prior-repair regression

### Night futures
- safety
- numeric exposure/suppression

### KRX 08:05
- observation
- target date
- rows
- readiness

### 9.0D canary
- ID/linkage/source/status/timings

### Production isolation
- all influence counts

### Cash-flow canary
- eligible/consumed/full FCF/OCF-only/stale/blocked/N/A

### PIT/freshness
- violations/suppressions

### Numeric
- automatic/manual/rejected/unresolved

### Semantic/quality
- exact errors
- quality receipt

### Unknown resolution
- before/resolved/remaining/contradictory

### Value add
- material/minor/no-change/degraded

### Natural behavior matrix
- all states

### Severity
- P0/P1/P2

### Final gate
- `PHASE_9_0E_READY = YES/NO`
- reason
- next selective scope or bounded repair

### Result delivery
- Git branch/commit/URLs OR ZIP path/SHA-256

## 34. No code changes from findings
Even if a defect is found:
- do not fix it
- do not change scheduler/canary/validator
- do not merge to main

This review produces evidence for the next work instruction.

## 35. Final philosophy
Answer three independent questions:

1. Did production work?
2. Did the cash-flow shadow canary work?
3. Did the canary influence production by exactly zero?

A production fallback can coexist with a successful canary.
A production AI-assisted success does not automatically prove the canary.

The key 9.0D evidence is:

**a naturally generated full-FCF path that passes PIT, freshness, provenance, semantics and quality while production influence remains zero.**

If observed with no P0/material P1, selective 9.0E may proceed without waiting for arbitrary additional runs.

If a behavior was not exercised, mark it `NOT_OBSERVED` and exclude that class from the initial rollout rather than delaying the whole roadmap.

The review goal is not to find another reason to wait.

It is to decide from today’s real evidence whether the validated selective subset is ready for user-visible cash-flow integration.
