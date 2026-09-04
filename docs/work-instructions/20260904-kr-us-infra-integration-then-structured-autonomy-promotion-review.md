# thesis-monitor — KR + US Infrastructure Integration
## KR frozen replay + real KR TEST E2E
## Combine KR delivery repair + US TLS/lease/validator repair
## Cross-market regression on the combined branch
## Merge infrastructure to main only after KR and US both PASS
## Then resume Structured Autonomy production-promotion review as a separate phase

---

# 0. Mission

Complete the production monitoring infrastructure repair before promoting the new decision structure.

There are TWO separate programs:

```text
PHASE 1
Production monitoring infrastructure integration

PHASE 2
Structured Autonomy decision-structure production promotion review
```

Do not mix them into one merge.

---

# 1. Known repair lineages

Common historical base:

```text
5d5f3363d3a762b62698943b1feb4fa121d0d0f9
```

KR live delivery/orchestration repair lineage:

```text
final repair branch SHA =
90cc52231c7343056c853c355ea90dfea10de25b
```

US natural TLS / lease / validator repair:

```text
final SHA =
deb4dc511aafa6e435b0af00436d690e2e498c0b
```

US repair state:

```text
TLS signed-in CLI preflight = PASS
UnknownIssuer = 0

independent heartbeat = implemented
real E2E lease renewals = 444

healthy primary backup reclaim = 0
stale primary reclaim/fencing = PASS

validator incident errors classified = 22/22
frozen replay remaining errors = 0

US TEST E2E:
AI market = 1
AI stocks = 14
total = 15/15
fallback = 0
duplicate = 0

READINESS =
READY_FOR_NATURAL_PROOF
```

KR repair state previously proved:

```text
real production entrypoint TEST E2E
accepted = 9
AI market = 1
stock AI/V2 = 8
fallback = 0
duplicate = 0

process-boundary recovery = PASS
delivery retry/recovery = PASS
late backup mutation blocked = PASS

main merge remained 0
```

The exact integration must preserve BOTH repair families.

---

# 2. Phase boundary

PHASE 1 may modify production infrastructure code.

PHASE 1 MUST NOT promote the unfinished Structured Autonomy decision contract.

Required:

```text
STRUCTURED_AUTONOMY_PRODUCTION_MUTATION = 0
```

PHASE 2 starts only after Phase 1 integration is merged and the infrastructure base is known.

Actual Structured Autonomy production send/persistence remains separately gated.

---

# 3. PHASE 1A — KR frozen replay

Before integration merge, replay the latest authoritative KR production packet through the repaired production validator and renderer WITHOUT model regeneration.

Use:

```text
KR source packet =
2026-09-03-kr-run-54-f19bb379daa7
```

Expected scope:

```text
market = 1
stocks = 8
total = 9
```

KR8:

```text
000660
003690
005490
005930
010120
012450
047810
086280
```

Frozen replay means:

```text
MODEL_RERUN = 0
FRESH_FACT_COLLECTION = 0
TELEGRAM_SEND = 0
```

Use persisted:
- packet
- candidate/accepted artifact if available
- numeric registry
- validation registry
- renderer inputs

Do not edit text to obtain PASS.

---

# 4. KR frozen replay required checks

Validate all of:

```text
schema
numeric provenance
market semantic provenance
earnings attribution
KR accounting basis
parent/common-share basis
official provisional earnings safety
PER/PBR/fPER/fPBR safety
Unknown semantics
price provenance
supply/positioning semantics
message contradiction
renderer ownership
delivery eligibility
```

Required:

```text
KR_FROZEN_REPLAY_VALIDATED = 9
KR_ACCOUNTING_SAFETY = PASS
KR_ACCOUNTING_VALUATION_SAFETY = PASS
KR_UNSUPPORTED_NUMERIC = 0
KR_MESSAGE_CONTRADICTION = 0
```

If frozen replay fails:
stop before real KR model E2E and classify the failure.

Do not weaken safety rules to force 9/9.

---

# 5. PHASE 1B — real KR TEST E2E

After KR frozen replay PASS, execute ONE real KR production-entrypoint TEST E2E.

Use:
- real KR production entrypoint
- real packet builder
- real signed-in CLI path
- US-repaired TLS trust path
- real claim / heartbeat / lease / fencing state machine
- real backup/retry/fallback orchestration
- real accepted-plan finalizer
- real Telegram adapter
- dedicated NON-PRODUCTION TEST recipient

Do NOT use production recipient.

Do NOT modify production scheduler.

---

# 6. KR TEST E2E expected success

Required:

```text
KR source ready = 9/9 scopes
primary claim acquired = PASS
signed-in CLI model result > 0
UnknownIssuer = 0

lease renewal observed > 0
healthy primary backup reclaim = 0

candidate = 9
validation = 9/9 PASS
accepted = 9

AI market TEST sent = 1
AI stocks TEST sent = 8

fallback = 0
duplicate = 0
```

The exact wording or directional decisions are NOT the infrastructure readiness target.

---

# 7. KR-specific safety in real E2E

Explicitly assert:

```text
KR_ACCOUNTING_SAFETY = PASS
KR_ACCOUNTING_VALUATION_SAFETY = PASS

OFFICIAL_PROVISIONAL_EARNINGS_SAFETY = PASS

COMMON_PARENT_ATTRIBUTION_UNSAFE_INFERENCE = 0

UNVERIFIED_EPS_BVPS_RECONSTRUCTION = 0

SUPPLY_FUNDAMENTAL_THESIS_MUTATION = 0
```

Supply/positioning may affect short-term positioning language only.

It must not independently mutate business investment logic.

---

# 8. KR lease / backup smoke proof

The full long-running 444-renewal proof does not need to be repeated.

But on the KR real E2E confirm:

```text
lease heartbeat observed
same fencing token retained
backup does not reclaim fresh primary
```

Controlled unit/integration matrix must still confirm:

```text
dead/stale primary → backup reclaim PASS
stale primary write → fenced
late AI after fallback → no duplicate
```

---

# 9. PHASE 1C — create integration branch

After standalone KR replay + KR TEST E2E PASS:

create a new integration branch.

Suggested:

```text
codex/20260904-kr-us-monitoring-infra-integration
```

Base selection:
use the clean common production ancestry,
then combine BOTH:

```text
KR repair:
90cc52231c7343056c853c355ea90dfea10de25b

US repair:
deb4dc511aafa6e435b0af00436d690e2e498c0b
```

Use merge/cherry-pick/rebase according to repository policy.

Do not silently drop either repair.

---

# 10. Integration conflict audit

The two repair families may overlap in:

```text
delivery orchestration
packet/generation ownership
retry/recovery
backup handling
accepted-plan finalization
claim state
fallback state
```

For every conflict:
record:
- file
- function
- KR behavior
- US behavior
- chosen integrated behavior
- why both guarantees remain preserved

Do not resolve conflicts by taking one side wholesale.

Required:

```text
KR_REPAIR_FEATURE_LOSS = 0
US_REPAIR_FEATURE_LOSS = 0
```

---

# 11. Required preserved KR guarantees

Integration branch must preserve:

```text
packet-bound AI metadata survives backup/reuse

pending AI delivery can be recovered across process boundary

delivery retry does not report no_pending while valid pending exists

late archival validation cannot overwrite terminal canonical delivery result

late backup cannot mutate already-sent terminal state

fallback exactly once

duplicate = 0
```

---

# 12. Required preserved US guarantees

Integration branch must preserve:

```text
approved TLS trust path

UnknownIssuer explicit classification

UnknownIssuer fail-fast / no retry storm

independent claim heartbeat during blocking model call

lease renewal

fencing token

fresh healthy primary blocks backup reclaim

dead primary allows backup reclaim

stale primary cannot finalize

fallback terminal blocks late AI delivery

validator 22-contract repair
```

---

# 13. Integration branch migration / schema audit

If KR and US repairs changed persisted claim/delivery state:

verify:
- schema compatibility
- migration requirement
- old rows/state readability
- idempotency
- restart behavior

Do NOT perform production DB mutation during test.

If migration is required:
produce a separate reviewed migration plan before main deployment.

Required:

```text
UNREVIEWED_PRODUCTION_DB_MIGRATION = 0
```

---

# 14. PHASE 1D — cross-market regression on integrated branch

Standalone branch PASS is not enough.

After KR + US code is combined, rerun BOTH real production-entrypoint TEST paths on the integration branch.

Order:

```text
KR TEST E2E
then
US TEST E2E
```

or vice versa if runtime isolation requires.

Do not run concurrently unless model/runtime isolation is proven.

---

# 15. Integrated KR TEST success gate

Required:

```text
KR_ACCEPTED = 9

KR_AI_MARKET_SENT = 1
KR_AI_STOCK_SENT = 8

KR_FALLBACK_SENT = 0
KR_DUPLICATE_SENT = 0

KR_HEALTHY_PRIMARY_BACKUP_RECLAIM = 0

KR_ACCOUNTING_SAFETY = PASS
KR_ACCOUNTING_VALUATION_SAFETY = PASS
```

---

# 16. Integrated US TEST success gate

Use the production-equivalent US test path proven by the US repair.

Required:

```text
US_ACCEPTED = 15

US_AI_MARKET_SENT = 1
US_AI_STOCK_SENT = 14

US_FALLBACK_SENT = 0
US_DUPLICATE_SENT = 0

US_HEALTHY_PRIMARY_BACKUP_RECLAIM = 0

US_TLS_UNKNOWN_ISSUER = 0

US_VALIDATOR = PASS
```

---

# 17. Cross-market shared-state regression matrix

Run controlled integration tests for:

```text
KR healthy primary + backup schedule
US healthy primary + backup schedule

KR stale primary reclaim
US stale primary reclaim

KR fallback before late AI
US fallback before late AI

KR process-boundary retry
US process-boundary retry

KR sent terminal + late backup
US sent terminal + late backup
```

For every scenario:

```text
duplicate = 0
terminal state immutable = PASS
```

---

# 18. Scheduler coexistence

Do not alter production schedules during integration testing.

Review whether KR/US schedules can overlap in:
- signed-in CLI
- app-server
- CODEX_HOME
- model concurrency
- state locks

If future overlap is possible:
ensure the production claim/runtime policy prevents cross-market interference.

Do not assume market separation means runtime separation.

---

# 19. Full regression suite

On the integrated branch run:

```text
focused KR orchestration tests
focused US TLS tests
focused claim/lease/fencing tests
focused backup/fallback tests
focused KR accounting/valuation tests
focused US validator tests
cross-market delivery tests
real KR TEST E2E
real US TEST E2E

full pytest
Ruff
git diff --check
Knowledge validation
Public Action schema validation
secret scan
```

No deleting tests.

---

# 20. Integration readiness

Only if BOTH markets pass on the combined branch:

```text
INFRA_INTEGRATION_READINESS =
READY_FOR_MAIN
```

Otherwise:

```text
NEEDS_MORE_REPAIR
```

Do not merge main based on standalone branch results.

---

# 21. PHASE 1E — main merge / operating deployment

When integrated KR and US PASS:

merge ONLY the infrastructure integration branch to main according to repository policy.

Required before merge:

```text
KR integrated PASS
US integrated PASS
full CI PASS
artifact index PASS
secret scan PASS
main diff reviewed
```

Structured Autonomy decision promotion must still be absent.

Required:

```text
STRUCTURED_AUTONOMY_PRODUCTION_MUTATION = 0
```

---

# 22. Operating SHA verification

After merge/deploy:

record:

```text
MAIN_SHA
OPERATING_SHA
```

Verify operating contains:

```text
KR repair lineage
US repair lineage
```

Do not infer deployment merely from a GitHub merge.

---

# 23. Natural proof after infrastructure merge

Natural proof is market-specific.

Next KR natural run should show:

```text
AI market = 1
AI stocks = 8
fallback = 0
duplicate = 0

healthy primary backup reclaim = 0
```

Next US natural run should show:

```text
AI market = 1
AI stocks = 14
fallback = 0
duplicate = 0

UnknownIssuer = 0

healthy primary backup reclaim = 0
```

If actual primary dies:
valid backup recovery is allowed.

Record KR and US natural verdict separately.

---

# 24. Phase 2 may begin after infrastructure main merge

After Phase 1 is merged to main, resume the Structured Autonomy program from the latest shadow state.

This includes the user-facing judgment structure:

```text
overall direction:
BUY / HOLD / SELL

directional balance:
BUY x : SELL y

HOLD lean:
BUY_LEAN / NEUTRAL / SELL_LEAN

new-buyer view:
ATTRACTIVE / WAIT / AVOID

holder view:
HOLDABLE / REVIEW / REDUCE

preferred entry:
PULLBACK / CONFIRMATION / BOTH / NONE

pullback entry zone
breakout / confirmation level

holder upside trim/review zone
holder downside review level
business invalidation condition
```

---

# 25. Decision structure semantics to preserve

Keep the established distinction:

```text
overall direction
!=
immediate entry stance
```

Example:

```text
종합 방향 = BUY
현재 신규진입 = WAIT
```

is valid.

BUY:SELL balance:
- sums to 10
- 0.5 increments
- not probability
- not expected return
- no fixed factor weighting

Deterministic label rule:

```text
BUY if buy >= 6
SELL if sell >= 6
otherwise HOLD
```

---

# 26. New-buyer semantics

Preserve:

```text
ATTRACTIVE
WAIT
AVOID
```

and:

```text
PULLBACK
CONFIRMATION
BOTH
NONE
```

For AVOID:
numeric levels must be described as:

```text
재검토 가격 조건
```

not actionable entry instructions.

---

# 27. Holder semantics

Preserve:

```text
HOLDABLE
REVIEW
REDUCE
```

Holder upside zone is:

```text
trim/review/reassessment zone
```

not an automatic sell target.

Holder downside price is:

```text
price review
```

not automatic stop-loss.

Business invalidation remains separate.

---

# 28. Same resistance / dual scenario semantics

The same verified resistance may legitimately mean:

```text
holder:
rejection/reassessment area

new buyer:
successful breakout confirmation
```

Renderer must explain both scenarios without contradiction.

---

# 29. Unknown / sector policy

Preserve:

```text
Unknown != SELL evidence
```

and:

```text
sector-normal characteristic
!= automatic negative
```

Examples:
- biotech development cash burn
- memory low forward PER near peak
- ADR/security-basis uncertainty

These affect confidence / valuation eligibility unless separate directional evidence exists.

---

# 30. Latest Structured Autonomy blocker to resume from

The most recent fresh-first experiment reached:

```text
21/22
```

with a bounded validator failure in KR `005490`.

The problematic pattern was a future-modal checkpoint such as:

```text
대규모 CAPEX가 FCF 감소, 순부채 증가와
향후 ROIC 악화로 이어질 수 있다.
```

The underlying metric ownership existed,
but the future-modal semantic validator did not recognize the construction.

Therefore the next Structured Autonomy repair should begin with:

```text
future-modal metric/checkpoint semantic ownership
```

not with label tuning.

Do not reuse 21 passing candidates.

After that repair:

```text
NEW ALL22 generation
→ fresh first 22/22
→ clean A/B/C
```

---

# 31. Structured Autonomy production-promotion review gate

The promotion review should evaluate:

```text
decision stability
balance stability
HOLD lean stability

new-buyer stance stability
holder stance stability

entry-mode stability

price-scenario provenance

evidence-selection variance

message quality
```

No manual ground-truth distribution.

Do not target a desired BUY/HOLD/SELL count.

---

# 32. Actual Structured Autonomy production mutation remains gated

After infrastructure main merge,
the review work may proceed.

But actual production decision mutation / renderer/send should require BOTH:

```text
A. Structured Autonomy promotion readiness PASS
B. integrated infrastructure natural proof sufficiently clean
```

Recommended minimum before actual decision-structure production switch:

```text
latest KR natural infrastructure proof = PASS
latest US natural infrastructure proof = PASS
```

If one market natural proof is still pending:
continue shadow/promotion review,
but do not activate production decision mutation for that market.

---

# 33. Separate commits / branches

Use separate histories.

Phase 1:

```text
codex/20260904-kr-us-monitoring-infra-integration
```

Phase 2 later:

```text
codex/...-structured-autonomy-production-promotion
```

Do not put decision-structure changes into the infrastructure merge commit.

This makes rollback independent.

---

# 34. Required Phase 1 reports

Create:

1. `docs/reports/20260904-kr-frozen-replay.md`
2. `docs/reports/20260904-kr-frozen-replay-validation.md`
3. `docs/reports/20260904-kr-real-test-e2e.md`
4. `docs/reports/20260904-kr-us-integration-lineage.md`
5. `docs/reports/20260904-kr-us-integration-conflict-audit.md`
6. `docs/reports/20260904-cross-market-claim-delivery-matrix.md`
7. `docs/reports/20260904-integrated-kr-test-e2e.md`
8. `docs/reports/20260904-integrated-us-test-e2e.md`
9. `docs/reports/20260904-infrastructure-main-readiness.md`
10. `docs/reports/20260904-main-operating-lineage.md`
11. `docs/reports/20260904-natural-proof-plan.md`
12. `docs/reports/20260904-infrastructure-artifact-index.md`

Machine-readable:

```text
20260904-kr-frozen-replay.json
20260904-kr-test-e2e.json
20260904-integration-lineage.json
20260904-cross-market-regression.json
20260904-infra-readiness.json
```

---

# 35. Required Phase 1 gates

```text
KR_REPAIR_SHA =
90cc52231c7343056c853c355ea90dfea10de25b

US_REPAIR_SHA =
deb4dc511aafa6e435b0af00436d690e2e498c0b

KR_FROZEN_REPLAY_VALIDATED =
9 / OTHER

KR_ACCOUNTING_SAFETY =
PASS / FAIL

KR_ACCOUNTING_VALUATION_SAFETY =
PASS / FAIL

KR_REAL_TEST_ACCEPTED =
9 / OTHER

KR_REAL_TEST_AI_MARKET_SENT =
1 / OTHER

KR_REAL_TEST_AI_STOCK_SENT =
8 / OTHER

KR_REAL_TEST_FALLBACK =
0 / NONZERO

KR_REAL_TEST_DUPLICATE =
0 / NONZERO

INTEGRATION_BRANCH =
...

KR_REPAIR_FEATURE_LOSS =
0 / NONZERO

US_REPAIR_FEATURE_LOSS =
0 / NONZERO

INTEGRATED_KR_ACCEPTED =
9 / OTHER

INTEGRATED_KR_AI_MARKET_SENT =
1 / OTHER

INTEGRATED_KR_AI_STOCK_SENT =
8 / OTHER

INTEGRATED_KR_FALLBACK =
0 / NONZERO

INTEGRATED_KR_DUPLICATE =
0 / NONZERO

INTEGRATED_US_ACCEPTED =
15 / OTHER

INTEGRATED_US_AI_MARKET_SENT =
1 / OTHER

INTEGRATED_US_AI_STOCK_SENT =
14 / OTHER

INTEGRATED_US_FALLBACK =
0 / NONZERO

INTEGRATED_US_DUPLICATE =
0 / NONZERO

INTEGRATED_US_TLS_UNKNOWN_ISSUER =
0 / NONZERO

CROSS_MARKET_HEALTHY_PRIMARY_BACKUP_RECLAIM =
0 / NONZERO

CROSS_MARKET_LATE_AI_DUPLICATE =
0 / NONZERO

FULL_TESTS =
PASS / FAIL

INFRA_INTEGRATION_READINESS =
READY_FOR_MAIN /
NEEDS_MORE_REPAIR

STRUCTURED_AUTONOMY_PRODUCTION_MUTATION =
0 / NONZERO

MAIN_MERGE =
0 / 1

MAIN_SHA =
... / NOT_MERGED

OPERATING_SHA =
... / NOT_DEPLOYED
```

---

# 36. Phase 2 handoff gates

When Phase 2 starts, record:

```text
INFRA_MAIN_SHA =
...

INFRA_OPERATING_SHA =
...

KR_NATURAL_INFRA_PROOF =
PASS / FAIL / PENDING

US_NATURAL_INFRA_PROOF =
PASS / FAIL / PENDING

STRUCTURED_AUTONOMY_LATEST_BLOCKER =
005490_FUTURE_MODAL_METRIC_SEMANTIC_OWNERSHIP

STRUCTURED_AUTONOMY_NEW_EXPERIMENT_GENERATION =
PASS / FAIL / NOT_STARTED

ALL22_FIRST_RUN =
22 / OTHER / NOT_STARTED

RUN_A =
22 / OTHER / NOT_STARTED

RUN_B =
22 / OTHER / NOT_STARTED

RUN_C =
22 / OTHER / NOT_STARTED

STRUCTURED_AUTONOMY_PROMOTION_READINESS =
READY_FOR_PRODUCTION_REVIEW /
NEEDS_MORE_SHADOW_WORK /
NOT_STARTED
```

---

# 37. Main merge rule

The user-requested sequence is:

```text
KR frozen replay
→ real KR TEST E2E
→ combine KR repair + US repair
→ integrated KR PASS
→ integrated US PASS
→ main merge
→ resume BUY/HOLD/SELL production-promotion review
```

Implement exactly this order.

Natural production observation continues after main merge.

Do not enable Structured Autonomy production decisions in the infrastructure merge.

---

# 38. Completion response for Phase 1

Return:

```text
KR FROZEN REPLAY =
...

KR REAL TEST =
...

INTEGRATION =
branch
base
KR repair included
US repair included
conflicts

INTEGRATED KR =
accepted
AI sent
fallback
duplicate

INTEGRATED US =
accepted
AI sent
fallback
duplicate
TLS

CROSS-MARKET =
claim
backup
late AI
terminal immutability

FULL TESTS =
...

MAIN READINESS =
...

MAIN MERGE =
...

OPERATING SHA =
...

NATURAL PROOF =
KR ...
US ...

STRUCTURED AUTONOMY =
not modified
next blocker ...
next phase ...
```

---

# 39. Stop conditions

Stop before integration if:

```text
KR frozen replay != 9/9
```

Stop before integration if:

```text
KR real TEST E2E != 9/9
```

Stop main merge if either integrated market fails.

Stop main merge if:
- duplicate > 0
- fallback unexpectedly > 0 in success scenario
- healthy primary backup reclaim > 0
- KR accounting safety fails
- US TLS UnknownIssuer returns
- either repair family loses a guarantee

Do not merge unfinished Structured Autonomy behavior.

---

# 40. Final principle

First make the monitoring substrate reliable for BOTH markets.

Then promote the new judgment structure.

The intended order is:

```text
reliable transport
→ reliable ownership / backup / delivery
→ KR + US integrated production base
→ natural proof
→ BUY/HOLD/SELL decision-structure promotion review
```

This keeps infrastructure risk separate from investment-judgment risk
and makes rollback and diagnosis much safer.
