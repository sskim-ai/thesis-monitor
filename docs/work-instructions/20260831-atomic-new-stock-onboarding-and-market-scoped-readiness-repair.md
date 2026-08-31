# thesis-monitor — Atomic New-Stock Onboarding + Market/Cohort-Scoped Readiness Repair
## Prevent active monitoring before production prerequisites are complete
## Prevent one incomplete stock from blocking an entire market or the other market
## Backfill current incomplete controls: 047810 and CPNG
## Preserve accepted-v2 decision ownership and exactly-once delivery

---

# 0. Metadata

- Repository: `sskim-ai/thesis-monitor`
- Date: `2026-08-31 KST`
- Workstream: `ATOMIC_ONBOARDING_AND_SCOPED_READINESS_REPAIR`
- Task class: `P1_ROOT_CAUSE_REPAIR + DATA_LIFECYCLE + READINESS_ISOLATION + BACKFILL`
- Production decision authority: preserve `V2_ACCEPTED`
- Automated trading: `0`
- Order sizing: `0`
- Production Assist: preserve `OFF`
- Price Structure calculation changes: `0`
- Valuation calculation changes: `0`
- Scheduler timing changes: `0`
- Manual production resend: `0`

Latest known safe production lineage before this repair:

```text
cutover final/main/operating lineage =
ecd01297f81d0b68aaf95ecfe866721b6aa2c104

earlier deployed runtime/code SHA in the cutover bundle =
2a30bb3dcaecb40f83ca53f59982de1e18dab0ee
```

Use actual repository/runtime truth at implementation start:

```text
git fetch origin
verify clean worktrees
resolve latest safe origin/main
resolve operating checkout
record runtime/deployed SHA if distinct
use ecd012... or a safe linear descendant
```

Do not assume documentation-only descendants are runtime defects.

---

# 1. Incident to fix

The first KR accepted-v2 natural live proof on 2026-08-31 showed:

```text
KR market data collection = PASS
KR investor-flow collection = PASS
new KR subject 047810 included = PASS
market 1 + KR stock 8 delivery = 9/9 exact
duplicate/orphan = 0/0
Price Structure = PASS
Valuation = PASS

BUT

V2 accepted-ready = 0 / 8
V2 decision block visible = 0 / 8
KR_V2_NATURAL_LIVE = FAIL
```

Observed readiness state:

```text
active monitored universe = 22

new subjects:
047810 한국항공우주산업
CPNG Coupang

active monitoring = present
investment logic / thesis = present
company row = present

BUT
security master = missing/incomplete
company profile = incomplete
latest/initial assessment = missing
```

The production readiness gate evaluated the whole active universe instead of the packet/market cohort.

Result:

```text
one or more incomplete subjects
        ↓
global readiness FAIL
        ↓
KR candidate generation blocked for all KR stocks
        ↓
no accepted v2 decision blocks
        ↓
deterministic fallback messages only
```

This task must fix BOTH lifecycle and readiness scope.

---

# 2. Root design principle

A monitored stock must not become production-active until its required production prerequisites are complete.

Canonical lifecycle:

```text
registration requested
        ↓
PENDING_ONBOARDING
        ↓
identity / security master
        ↓
company profile
        ↓
initial investment research / investment logic
        ↓
initial evidence snapshot
        ↓
initial baseline assessment
        ↓
readiness validator
        ↓
READY
        ↓
ACTIVE
```

Production selection:

```text
market = target market
AND monitoring state = ACTIVE
AND onboarding_ready = true
AND subject is eligible for the target packet cutoff
```

One incomplete subject must fail closed for itself, not block unrelated subjects.

---

# 3. Hard invariants

After this repair:

```text
ACTIVE_IMPLIES_ONBOARDING_READY = true

ACTIVE_SUBJECT_MISSING_REQUIRED_PREREQUISITE = 0

PENDING_SUBJECT_VISIBLE_IN_PRODUCTION_DECISION_BLOCK = 0

CROSS_MARKET_READINESS_CONTAMINATION = 0

ONE_INCOMPLETE_SUBJECT_BLOCKS_READY_PEERS = 0
```

Do not implement ticker-specific exceptions.

Hard:

```text
TICKER_SPECIFIC_ONBOARDING_BYPASS = 0
```

---

# 4. Work split

```text
Track A
Atomic onboarding state machine / lifecycle

Track B
Market/cohort-scoped readiness isolation

Track C
Backfill 047810 + CPNG and repair existing inconsistent active rows safely

Track D
Regression, test-sink, main merge, next-live guard
```

Recommended branches:

```text
codex/atomic-monitoring-onboarding
codex/market-scoped-readiness
codex/incomplete-subject-backfill
codex/onboarding-readiness-regression
```

---

# 5. Track A — onboarding state model

Implement repository-native equivalent of:

```text
PENDING_ONBOARDING
READY
ACTIVE
ONBOARDING_FAILED
INACTIVE
```

If the repository already has a compatible lifecycle, extend it instead of creating duplicate state systems.

Minimum semantics:

## PENDING_ONBOARDING

Registration request accepted but mandatory prerequisites are not yet complete.

Must NOT be eligible for production stock-decision rendering.

## READY

Mandatory prerequisites validated.

May be activated automatically or by the existing registration workflow.

## ACTIVE

Production eligible.

Invariant:

```text
ACTIVE => readiness validator PASS
```

## ONBOARDING_FAILED

Onboarding encountered a material failure requiring retry/review.

Must not appear as ACTIVE.

## INACTIVE

Existing stopped/disabled monitoring semantics.

Do not break historical stop-monitoring behavior.

---

# 6. Separate monitoring intent from production eligibility

Preserve that the user explicitly asked to monitor a stock even while onboarding is incomplete.

Store separately:

```text
monitoring_requested = true
onboarding_state = PENDING_ONBOARDING
production_eligible = false
```

Do not misrepresent this as active live monitoring until ready.

User-facing semantics should be able to say:

```text
모니터링 등록 요청은 접수됐지만,
필수 기업/증권 정보 검증이 완료되지 않아 아직 라이브 점검 대상에는 포함되지 않았습니다.
```

---

# 7. Atomic onboarding transaction

A new monitoring registration must orchestrate:

```text
1. normalize ticker / exchange / market
2. security master create-or-validate
3. company profile create-or-validate
4. initial investment logic create-or-validate
5. initial evidence snapshot
6. initial baseline assessment
7. onboarding readiness validation
8. activate only after PASS
```

Do not set `active=true` before step 7 passes.

Hard:

```text
ACTIVE_SET_BEFORE_READINESS_PASS = 0
```

---

# 8. Security Master mandatory fields

Use repository-native schema.

At minimum validate the fields required for safe production use:

```text
canonical ticker
exchange / venue
market / country
security type
trading currency
financial/reporting currency where relevant
ordinary/share/ADR/ADS basis where relevant
ADR/ADS ratio and direction if applicable
canonical company linkage
```

For KR:

```text
6-digit ticker normalization
KR market ownership
KRW security basis
```

For US/foreign:

ensure security basis is explicit enough for valuation/share calculations.

If a field is legitimately unavailable but non-blocking:
document the allowed-safe-unavailable contract.

Do not mark ready if a required share/security basis is unresolved.

---

# 9. Company Profile mandatory fields

Create/validate:

```text
canonical company identity
business structure
industry / sector
major business segments
material customer / geographic / industry exposure where available
competitive positioning summary
capital-allocation context where relevant
```

Use `getCompanyProfile`-equivalent backend acquisition/source of truth.

Do not create a shallow placeholder profile solely to satisfy the gate.

Hard:

```text
PLACEHOLDER_PROFILE_COUNTS_AS_READY = 0
```

---

# 10. Initial investment logic

Registration must contain a production-usable investment logic record:

```text
core investment logic
drivers
validation metrics
strengthen signals
weaken signals
invalidation signals
market expectations
valuation framework
important macro exposures
price rules only if evidence-supported
```

This can come from the initial investment research already performed before the explicit monitoring request.

Do not silently activate a ticker with only a name/ticker row.

---

# 11. Initial evidence snapshot

At onboarding capture the evidence actually needed to support the first production decision:

```text
latest earnings checkpoint
recent/longer-term company events
current valuation context
current price/OHLCV availability
Price Structure availability or explicit safe-unavailable state
market context
positioning/flow where applicable
material Unknowns
```

No requirement that every optional metric be available.

The validator must distinguish:

```text
REQUIRED
OPTIONAL_SAFE_UNAVAILABLE
BLOCKING_UNKNOWN
```

---

# 12. Initial baseline assessment

Create a baseline assessment during onboarding.

Recommended semantic type:

```text
INITIAL_BASELINE
```

or repository-native equivalent.

It should include:

```text
as_of
evidence fingerprint
business investment-logic status
market-expectation assessment
valuation context
earnings-estimate impact if known
confirmed facts
inferred implications
Unknowns
new-observer view
holder view if applicable
price view if safe
risk level
confidence
```

This is the baseline for the next daily delta.

Do not manufacture a daily change label relative to a nonexistent prior day.

---

# 13. BUY/HOLD/SELL at onboarding

The onboarding pipeline may also prepare the initial v2 candidate/accepted analytical classification if the decision engine supports it.

But:

```text
initial baseline assessment
```

and:

```text
BUY/HOLD/SELL accepted decision
```

remain separate records.

Do not force BUY/HOLD/SELL merely to activate monitoring if the decision engine safely returns `NOT_READY`.

Define whether `NOT_READY` blocks ACTIVE based on product policy:

Preferred for this system:

```text
required business/security/profile prerequisites PASS
+
decision prerequisites PASS
→ ACTIVE
```

If the repository intentionally allows ACTIVE with temporary decision suppression, document and test that exception explicitly.

Do not leave this ambiguous.

---

# 14. Onboarding readiness validator

Create one canonical validator.

Output at minimum:

```text
onboarding_ready
blocking_requirements[]
safe_unavailable_requirements[]
completed_requirements[]
failure_stage
as_of
```

Required categories:

```text
IDENTITY
SECURITY_MASTER
COMPANY_PROFILE
INVESTMENT_LOGIC
INITIAL_EVIDENCE
INITIAL_BASELINE_ASSESSMENT
DECISION_READINESS
```

Hard:

```text
ONBOARDING_VALIDATOR_SINGLE_AUTHORITY = PASS
```

---

# 15. Activation operation

Only the onboarding coordinator/transaction may transition:

```text
PENDING_ONBOARDING → READY → ACTIVE
```

Do not let independent downstream jobs infer ACTIVE from partial rows.

Hard:

```text
DOWNSTREAM_JOB_AUTO_ACTIVATES_PARTIAL_SUBJECT = 0
```

---

# 16. Idempotency

Re-running onboarding for the same normalized security must be idempotent.

It must:

```text
fill missing prerequisites
update safe mutable current fields
preserve monitoring/investment-logic history
avoid duplicate active rows
avoid duplicate security-master rows
avoid duplicate initial assessments
```

Hard:

```text
ONBOARDING_IDEMPOTENT = PASS
```

---

# 17. Failure and retry

If one step fails:

```text
state = PENDING_ONBOARDING or ONBOARDING_FAILED
production_eligible = false
failure_stage = exact stage
```

Retry resumes from canonical persisted state.

Do not erase earlier successful steps.

Do not create a second monitoring identity.

---

# 18. Existing `monitorStock` semantics

Preserve explicit-user-intent rule.

This engineering task must not cause arbitrary stocks to be auto-monitored.

`monitorStock` or its internal coordinator remains triggered only after explicit monitoring intent.

The repair changes what happens AFTER registration intent is received.

---

# 19. Track B — packet/cohort-scoped readiness

Production readiness must be evaluated against the actual packet cohort.

Canonical selection concept:

```text
target_session
target_market
packet_cutoff
monitoring_state = ACTIVE
onboarding_ready = true
subject eligible at cutoff
```

Then readiness validation occurs per subject within that cohort.

---

# 20. KR scoped readiness

KR production must evaluate:

```text
market = KR
eligible at KR packet cutoff
```

Only.

A US onboarding failure must not block KR production.

Hard:

```text
US_INCOMPLETE_BLOCKS_KR_PACKET = 0
```

---

# 21. US scoped readiness

US production must evaluate:

```text
market = US / configured foreign cohort
eligible at US packet cutoff
```

Only.

A KR onboarding failure must not block US production.

Hard:

```text
KR_INCOMPLETE_BLOCKS_US_PACKET = 0
```

---

# 22. Per-subject fail-closed

Within the target market:

if one subject unexpectedly becomes incomplete:

```text
that subject = NOT_READY / suppressed
ready peers continue
```

unless the missing requirement reveals a packet-wide integrity failure.

Hard:

```text
ONE_KR_SUBJECT_NOT_READY_BLOCKS_OTHER_KR_READY_SUBJECTS = 0
ONE_US_SUBJECT_NOT_READY_BLOCKS_OTHER_US_READY_SUBJECTS = 0
```

Document the narrow conditions that legitimately justify packet-wide abort.

Examples may include:

```text
market session identity failure
shared canonical market packet corruption
security-wide auth/source failure causing all subject evidence invalid
```

Do not use ordinary per-company profile incompleteness as a packet-wide abort.

---

# 23. Cutoff semantics

A same-day new subject belongs to the current live packet only if:

```text
onboarding READY/ACTIVE before packet cutoff
```

If activation occurs after cutoff:

```text
exclude from current packet
include starting next eligible cycle
```

Record:

```text
registration_requested_at
onboarding_ready_at
activated_at
packet_cutoff
first_eligible_session
```

This removes ambiguity like the 047810 case.

---

# 24. Production universe snapshot

Each packet must own an immutable subject-universe snapshot:

```text
market
session
cutoff
eligible subjects
excluded pending subjects
exclusion reasons
```

Downstream candidate/renderer/delivery must consume that snapshot.

Do not re-query a mutable global active list halfway through packet construction.

Hard:

```text
PACKET_UNIVERSE_MUTATES_AFTER_CUTOFF = 0
```

---

# 25. Decision-engine cohort

V2 candidate generation must iterate the packet universe snapshot.

It must not preflight the entire global monitored universe first.

Hard:

```text
V2_GLOBAL_UNIVERSE_GATE_BEFORE_COHORT = 0
```

---

# 26. Accepted decision ownership preserved

Keep the already-repaired pipeline:

```text
candidate
→ material disagreement
→ adjudication if required
→ accepted_decision
```

This task must not alter the accepted-decision ownership contract.

Hard:

```text
ACCEPTED_DECISION_OWNERSHIP_REGRESSION = 0
```

---

# 27. Track C — current incomplete subject repair

Mandatory live controls:

## 047810 한국항공우주산업

Current incident evidence showed it had been active with incomplete production prerequisites.

Backfill/validate:

```text
security master
company profile
investment logic linkage
initial evidence snapshot
initial baseline assessment
decision readiness
```

Expected post-repair:

```text
onboarding_ready = true
state = ACTIVE
```

only if all required gates pass.

If not:

move to/retain non-active pending state safely and report exact blocker.

Do not leave `ACTIVE + incomplete`.

---

# 28. CPNG Coupang

Backfill/validate:

```text
US security master
company profile
investment logic linkage
initial evidence
initial baseline assessment
decision readiness
```

Mandatory attention:

```text
security/share/currency basis
US/foreign routing
valuation method
latest earnings context
Price Structure/OHLCV availability
```

Expected post-repair:

```text
onboarding_ready = true
state = ACTIVE
next US packet eligible
```

only after PASS.

---

# 29. Do not create fake completeness

For either 047810 or CPNG:

do not mark fields complete with:

```text
UNKNOWN
N/A
placeholder
empty object
copied peer data
```

unless the schema explicitly allows that exact safe-unavailable state.

Hard:

```text
FAKE_COMPLETENESS_TO_PASS_ONBOARDING = 0
```

---

# 30. Cross-ticker contamination controls

Mandatory:

```text
047810 does not inherit 012450 facts merely because both are defense-related
CPNG does not inherit another US consumer/e-commerce profile
```

Verify:

```text
company identity
earnings
valuation
OHLCV
Price Structure
sector
macro exposures
```

all belong to the correct security.

Hard:

```text
CROSS_TICKER_ONBOARDING_FACT_CONTAMINATION = 0
```

---

# 31. Existing active universe audit

Audit ALL currently active monitored subjects.

For each determine:

```text
active?
onboarding validator PASS?
missing required prerequisite?
baseline assessment present?
security master safe?
company profile complete?
```

Expected after repair:

```text
ACTIVE_INCOMPLETE_SUBJECT_COUNT = 0
```

Do not only patch 047810/CPNG.

---

# 32. Existing historical rows

Do not delete monitoring history or old assessment history.

If old active rows are inconsistent:

repair current state while preserving historical facts.

If a historical record was incorrectly labeled active before readiness, document an errata if needed.

---

# 33. Database/schema migration safety

If schema changes are needed:

```text
backward-compatible migration
explicit defaults
no destructive column rewrite
migration tested on copy/test DB
rollback path documented
```

Do not expose DB credentials.

Hard:

```text
DESTRUCTIVE_ONBOARDING_SCHEMA_MIGRATION = 0
```

---

# 34. Track D — regression tests

Required unit/integration controls:

## A. happy-path new KR ticker

```text
request monitor
→ PENDING
→ all prerequisites
→ baseline assessment
→ READY
→ ACTIVE
```

## B. happy-path new US ticker

same.

## C. company profile failure

```text
security master PASS
profile FAIL
→ not ACTIVE
```

## D. initial assessment failure

```text
profile PASS
assessment FAIL
→ not ACTIVE
```

## E. idempotent re-run

same ticker twice → one monitoring identity / no duplicate baseline.

## F. KR incomplete vs US ready

KR incomplete subject must not block US ready cohort.

## G. US incomplete vs KR ready

US incomplete subject must not block KR ready cohort.

## H. one incomplete KR peer

7 ready KR + 1 incomplete KR:
7 ready subjects still reach candidate/accepted/render;
incomplete subject safely excluded/NOT_READY.

## I. post-cutoff activation

new subject READY after packet cutoff:
not in current packet;
eligible next cycle.

## J. pre-cutoff activation

READY before cutoff:
included in current packet.

---

# 35. Regression against the 2026-08-31 incident

Create a deterministic incident replay fixture:

```text
KR ready legacy subjects
+
047810 incomplete
+
CPNG incomplete
```

Old behavior:

```text
global profile gate FAIL
→ KR v2 0/8
```

Required repaired behavior:

```text
KR cohort readiness independent of CPNG
ready KR peers continue
047810 behavior depends only on its own cutoff/readiness state
```

Hard:

```text
INCIDENT_20260831_REPLAY = PASS
```

---

# 36. Positive control: all-ready 22

After backfill, if all current 22 subjects are truly ready:

run non-production all-universe preflight.

Expected:

```text
KR ready = current KR active eligible count
US ready = current US active eligible count
global active-incomplete = 0
```

Do not force a count if runtime universe changed.

---

# 37. Test-sink

Before main merge:

send non-production test messages for:

```text
all current KR eligible subjects
all current US eligible subjects
```

Use packet/cohort-scoped selection.

Mandatory exact controls:

```text
047810
CPNG
003690
GOOGL
HUT
RXRX
SNDK
```

No production recipient.

Hard:

```text
TEST_PRODUCTION_RECIPIENT_SEND = 0
PRODUCTION_DELIVERY_INTENT_CREATED_DURING_TEST = 0
```

---

# 38. New-subject message quality

For 047810 and CPNG verify:

```text
canonical name/ticker
explicit BUY/HOLD/SELL if accepted-ready
Korean user-facing decision prose
correct polarity
market expectations
valuation
Price Structure
Unknowns
decision-aware change conditions
no copied-peer facts
no order command
```

Hard:

```text
047810_TEST_MESSAGE_QUALITY = PASS
CPNG_TEST_MESSAGE_QUALITY = PASS
```

if both become ready.

If one remains safely pending:

report `NOT_READY_SAFE`, not PASS.

---

# 39. Production merge rule

Merge to main only if:

```text
OPEN_P0 = 0
OPEN_MATERIAL_P1 = 0

atomic onboarding tests PASS
market/cohort-scoped readiness PASS
incident replay PASS
active-incomplete audit PASS
047810/CPNG resolved to READY or safe non-active pending
test-sink exact PASS for eligible subjects
accepted decision ownership unchanged
Price Structure/valuation unchanged
```

---

# 40. US next-live protection

Because CPNG is expected for the next US natural cycle:

if CPNG onboarding is READY before the US packet cutoff:

```text
include CPNG
```

If not READY:

```text
exclude/suppress CPNG safely
all other ready US subjects must continue
```

Hard:

```text
CPNG_NOT_READY_BLOCKS_OTHER_US_SUBJECTS = 0
```

Do not manually send US production to prove the fix.

---

# 41. KR next-live protection

For the next KR natural cycle:

```text
ready KR subjects continue independently
```

If 047810 is ready, include it.

If not, safely exclude/suppress it without blocking peers.

Hard:

```text
047810_NOT_READY_BLOCKS_OTHER_KR_SUBJECTS = 0
```

---

# 42. Existing scheduler preservation

Do not change:

```text
KR primary/backup/dispatcher timing
US primary/backup timing
```

for this repair.

Hard:

```text
SCHEDULER_DIFF = 0
```

---

# 43. No manual production replay

The 2026-08-31 failed v2 live messages have already been delivered via deterministic fallback.

Do not resend corrected versions to production recipients in this task.

Preserve exactly-once history.

Hard:

```text
MANUAL_REPLAY_OF_20260831_KR_MESSAGES = 0
```

---

# 44. Price Structure / valuation isolation

No calculation changes.

Hard:

```text
PRICE_STRUCTURE_NUMERIC_DIFF = 0
VALUATION_NUMERIC_DIFF = 0
```

New-subject onboarding may populate their own correct data,
but must not change algorithms.

---

# 45. User-facing onboarding status

If repository/product surfaces registration status, use clear states.

Recommended Korean semantics:

```text
등록 준비 중
등록 완료
등록 실패/검토 필요
모니터링 중단
```

Do not tell the user "모니터링 중" while required production onboarding is incomplete.

---

# 46. Required architecture docs

Create/update:

```text
docs/architecture/MONITORING_ONBOARDING_LIFECYCLE.md
docs/architecture/ONBOARDING_READINESS_CONTRACT.md
docs/architecture/MARKET_COHORT_SCOPED_READINESS.md
docs/architecture/PRODUCTION_PACKET_UNIVERSE_SNAPSHOT.md
```

---

# 47. Required reports

Create at minimum:

1. `docs/reports/20260831-onboarding-readiness-root-cause.md`
2. `docs/reports/20260831-monitoring-onboarding-state-machine.md`
3. `docs/reports/20260831-onboarding-required-prerequisites.md`
4. `docs/reports/20260831-onboarding-validator-contract.md`
5. `docs/reports/20260831-market-cohort-readiness-contract.md`
6. `docs/reports/20260831-production-packet-universe-contract.md`
7. `docs/reports/20260831-active-incomplete-universe-audit.md`
8. `docs/reports/20260831-047810-onboarding-backfill.md`
9. `docs/reports/20260831-cpng-onboarding-backfill.md`
10. `docs/reports/20260831-cross-ticker-contamination-controls.md`
11. `docs/reports/20260831-incident-replay-kr-global-gate.md`
12. `docs/reports/20260831-onboarding-idempotency.md`
13. `docs/reports/20260831-scoped-readiness-test-sink.md`
14. `docs/reports/20260831-new-subject-message-quality.md`
15. `docs/reports/20260831-onboarding-readiness-main-merge.md`
16. `docs/reports/20260831-onboarding-readiness-live-guard.md`
17. `docs/reports/20260831-onboarding-readiness-artifact-index.md`

Machine-readable:

```text
docs/reports/20260831-active-onboarding-readiness-audit.json
docs/reports/20260831-new-subject-readiness.json
docs/reports/20260831-onboarding-readiness-deployment.json
```

---

# 48. Required gates

Set exactly:

```text
ACTIVE_IMPLIES_ONBOARDING_READY =
PASS / FAIL

ACTIVE_SUBJECT_MISSING_REQUIRED_PREREQUISITE =
0 / NONZERO

PENDING_SUBJECT_VISIBLE_IN_PRODUCTION_DECISION_BLOCK =
0 / NONZERO

CROSS_MARKET_READINESS_CONTAMINATION =
0 / NONZERO

ONE_INCOMPLETE_SUBJECT_BLOCKS_READY_PEERS =
0 / NONZERO

TICKER_SPECIFIC_ONBOARDING_BYPASS =
0 / NONZERO

ACTIVE_SET_BEFORE_READINESS_PASS =
0 / NONZERO

PLACEHOLDER_PROFILE_COUNTS_AS_READY =
0 / NONZERO

ONBOARDING_VALIDATOR_SINGLE_AUTHORITY =
PASS / FAIL

DOWNSTREAM_JOB_AUTO_ACTIVATES_PARTIAL_SUBJECT =
0 / NONZERO

ONBOARDING_IDEMPOTENT =
PASS / FAIL

US_INCOMPLETE_BLOCKS_KR_PACKET =
0 / NONZERO

KR_INCOMPLETE_BLOCKS_US_PACKET =
0 / NONZERO

ONE_KR_SUBJECT_NOT_READY_BLOCKS_OTHER_KR_READY_SUBJECTS =
0 / NONZERO

ONE_US_SUBJECT_NOT_READY_BLOCKS_OTHER_US_READY_SUBJECTS =
0 / NONZERO

PACKET_UNIVERSE_MUTATES_AFTER_CUTOFF =
0 / NONZERO

V2_GLOBAL_UNIVERSE_GATE_BEFORE_COHORT =
0 / NONZERO

ACCEPTED_DECISION_OWNERSHIP_REGRESSION =
0 / NONZERO

FAKE_COMPLETENESS_TO_PASS_ONBOARDING =
0 / NONZERO

CROSS_TICKER_ONBOARDING_FACT_CONTAMINATION =
0 / NONZERO

ACTIVE_INCOMPLETE_SUBJECT_COUNT =
0 / NONZERO

DESTRUCTIVE_ONBOARDING_SCHEMA_MIGRATION =
0 / NONZERO

INCIDENT_20260831_REPLAY =
PASS / FAIL

047810_ONBOARDING_STATE =
ACTIVE_READY /
PENDING_SAFE /
FAIL

CPNG_ONBOARDING_STATE =
ACTIVE_READY /
PENDING_SAFE /
FAIL

047810_TEST_MESSAGE_QUALITY =
PASS /
NOT_READY_SAFE /
FAIL

CPNG_TEST_MESSAGE_QUALITY =
PASS /
NOT_READY_SAFE /
FAIL

CPNG_NOT_READY_BLOCKS_OTHER_US_SUBJECTS =
0 / NONZERO

047810_NOT_READY_BLOCKS_OTHER_KR_SUBJECTS =
0 / NONZERO

TEST_EXACT_PAYLOAD =
PASS / FAIL

TEST_PRODUCTION_RECIPIENT_SEND =
0 / NONZERO

PRODUCTION_DELIVERY_INTENT_CREATED_DURING_TEST =
0 / NONZERO

SCHEDULER_DIFF =
0 / NONZERO

MANUAL_REPLAY_OF_20260831_KR_MESSAGES =
0 / NONZERO

PRICE_STRUCTURE_NUMERIC_DIFF =
0 / NONZERO

VALUATION_NUMERIC_DIFF =
0 / NONZERO

OPEN_P0 =
...

OPEN_MATERIAL_P1 =
...

ONBOARDING_READINESS_REPAIR =
READY_FOR_MAIN /
FAIL
```

---

# 49. Main merge + deployment state

After all gates PASS:

```text
merge to main
verify origin/main
verify operating checkout
verify runtime feature state
```

Required:

```text
FINAL_MAIN = ORIGIN_MAIN = OPERATING
```

or document only a known runtime/deployment SHA distinction.

Do not leave production on a feature branch.

---

# 50. Completion response

Return:

```text
MASTER_INSTRUCTION_COMMIT = ...
BASE_SHA = ...

TRACK_A_BRANCH = ...
TRACK_A_IMPLEMENTATION = ...

TRACK_B_BRANCH = ...
TRACK_B_IMPLEMENTATION = ...

TRACK_C_BRANCH = ...
TRACK_C_IMPLEMENTATION = ...

TRACK_D_BRANCH = ...
TRACK_D_RESULT = ...

REPORT_COMMIT = ...
FINAL_MAIN = ...
ORIGIN_MAIN = ...
OPERATING = ...

ONBOARDING_STATE_MODEL =
...

ACTIVE_IMPLIES_ONBOARDING_READY = ...
ACTIVE_SUBJECT_MISSING_REQUIRED_PREREQUISITE = ...

CURRENT_ACTIVE_SUBJECT_COUNT = ...
CURRENT_READY_ACTIVE_SUBJECT_COUNT = ...
ACTIVE_INCOMPLETE_SUBJECT_COUNT = ...

047810_ONBOARDING_STATE = ...
047810_BLOCKERS = ...
047810_FIRST_ELIGIBLE_SESSION = ...

CPNG_ONBOARDING_STATE = ...
CPNG_BLOCKERS = ...
CPNG_FIRST_ELIGIBLE_SESSION = ...

US_INCOMPLETE_BLOCKS_KR_PACKET = 0
KR_INCOMPLETE_BLOCKS_US_PACKET = 0
ONE_INCOMPLETE_SUBJECT_BLOCKS_READY_PEERS = 0

INCIDENT_20260831_REPLAY = ...
ONBOARDING_IDEMPOTENT = ...
PACKET_UNIVERSE_MUTATES_AFTER_CUTOFF = 0
V2_GLOBAL_UNIVERSE_GATE_BEFORE_COHORT = 0

047810_TEST_MESSAGE_QUALITY = ...
CPNG_TEST_MESSAGE_QUALITY = ...

TEST_MESSAGE_COUNT = ...
TEST_EXACT_PAYLOAD = ...
TEST_PRODUCTION_RECIPIENT_SEND = 0
PRODUCTION_DELIVERY_INTENT_CREATED_DURING_TEST = 0

ACCEPTED_DECISION_OWNERSHIP_REGRESSION = 0
PRICE_STRUCTURE_NUMERIC_DIFF = 0
VALUATION_NUMERIC_DIFF = 0
SCHEDULER_DIFF = 0
MANUAL_REPLAY_OF_20260831_KR_MESSAGES = 0

OPEN_P0 = ...
OPEN_MATERIAL_P1 = ...

ONBOARDING_READINESS_REPAIR =
READY_FOR_MAIN /
FAIL

NEXT_ACTION =
WAIT_FOR_US_NATURAL_LIVE /
WAIT_FOR_NEXT_KR_NATURAL_LIVE /
BOUNDED_REPAIR /
NO_ACTION

ZIP = ...
ZIP_SHA256 = ...
```

---

# 51. Mandatory completion ZIP

Create:

`20260831-atomic-new-stock-onboarding-and-market-scoped-readiness-repair-bundle.zip`

Include:

```text
exact master instruction
all track instructions
root-cause evidence
state-machine contract
required-prerequisite matrix
onboarding validator
market/cohort readiness design
packet universe snapshot contract
full active-universe audit
047810 backfill
CPNG backfill
incident replay
idempotency tests
cross-market negative controls
test-sink exact messages
new-subject message-quality review
main-merge evidence
deployment/readiness JSON
test/CI summary
artifact index
```

Exclude:

```text
secrets
Telegram recipient IDs
tokens
auth headers
account identifiers
hidden chain-of-thought
```

Compute SHA-256.

---

# 52. Final principle

A stock being "registered for monitoring" and a stock being "production-ready active monitoring" are not the same moment.

The system must guarantee:

```text
explicit user monitoring intent
        ↓
safe onboarding completion
        ↓
ACTIVE
```

and production must guarantee:

```text
one incomplete subject affects itself,
not every ready subject,
and never the other market.
```

The repair is complete only when both invariants are true.
