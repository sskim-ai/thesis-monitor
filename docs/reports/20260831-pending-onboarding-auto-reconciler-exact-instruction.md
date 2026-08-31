# thesis-monitor — Pending Onboarding Auto-Reconciler + Market Preflight Resume
## Do NOT manually resume CPNG before this feature is deployed
## Use CPNG as a real positive control for generic pending-onboarding recovery
## Never force-enable; only READY after canonical prerequisites pass

---

# 0. Metadata

- Repository: `sskim-ai/thesis-monitor`
- Date: `2026-08-31 KST`
- Workstream: `PENDING_ONBOARDING_AUTO_RECONCILER`
- Task class: `ONBOARDING_AUTOMATION + PRELIVE_SAFETY_NET + LIVE_POSITIVE_CONTROL`
- Production Assist: preserve `OFF`
- Scheduler market delivery times: no change
- Automated trading/order sizing: `0`
- Manual CPNG-specific resume before implementation: `0`
- Ticker-specific onboarding bypass: `0`

Latest reported deployed lineage from the atomic onboarding repair:

```text
FINAL_MAIN / ORIGIN_MAIN / OPERATING =
9c0e290...

ACTIVE / READY-ACTIVE / INCOMPLETE =
21 / 21 / 0

047810 =
ACTIVE_READY

CPNG =
PENDING_ONBOARDING
active = false
production_eligible = false
```

Current CPNG blocker after its initial baseline assessment was added:

```text
INITIAL_EVIDENCE
```

Current CPNG completed prerequisites:

```text
IDENTITY
SECURITY_MASTER
COMPANY_PROFILE
INVESTMENT_LOGIC
INITIAL_BASELINE_ASSESSMENT
```

Resolve actual current SHAs and runtime state before implementation.

---

# 1. Core objective

After this work, a user should only need to say:

```text
"이 종목 모니터링 등록해줘"
```

The system should then:

```text
registration intent
→ PENDING_ONBOARDING
→ immediate onboarding attempt
→ if incomplete, persist exact blocker
→ background/scheduled reconciler retries eligible missing steps
→ market preflight performs one bounded last-chance resume
→ readiness validator
→ ACTIVE_READY only after PASS
```

The user should not need to manually ask for:

```text
INITIAL_EVIDENCE
INITIAL_BASELINE_ASSESSMENT
DECISION_READINESS
```

---

# 2. CPNG control policy

Do NOT perform a CPNG-specific manual resume before deploying this feature.

CPNG must remain the real legacy pending positive control.

Forbidden:

```text
resume_onboarding("CPNG") as a one-off admin/manual repair
direct active=true patch
direct blocker deletion
fake INITIAL_EVIDENCE row
ticker-specific CPNG exception
manual US production run just to activate it
```

Hard:

```text
CPNG_MANUAL_ONE_OFF_RESUME_BEFORE_RECONCILER = 0
CPNG_TICKER_SPECIFIC_BYPASS = 0
```

---

# 3. Three-layer automatic recovery

Implement all three layers.

## Layer A — immediate registration continuation

After explicit monitoring registration:

```text
monitoring_requested = true
→ PENDING_ONBOARDING
→ onboarding coordinator immediately attempts all remaining prerequisites
```

If complete:

```text
ACTIVE_READY
```

If incomplete:

```text
PENDING_ONBOARDING / ONBOARDING_FAILED
+
exact blockers
+
retry classification
```

Do not return "모니터링 등록 완료" unless ACTIVE_READY.

---

# 4. Layer B — scheduled onboarding reconciler

Add a generic pending-onboarding reconciler.

It scans only:

```text
monitoring_requested = true
AND onboarding_state in pending/retryable states
AND active = false
```

For each pending subject:

```text
load canonical onboarding state
skip completed stages idempotently
attempt only missing/retryable stages
run readiness validator
activate only after PASS
```

Never scan arbitrary unrequested tickers.

Hard:

```text
RECONCILER_AUTO_MONITORS_UNREQUESTED_SECURITY = 0
```

---

# 5. Reconciler scope

The reconciler must be cross-market capable but subject-isolated.

For each subject:

```text
ticker
market
current blockers
last attempt
retry class
next eligible retry time
```

One subject failure must not stop the remaining pending subjects.

Hard:

```text
ONE_PENDING_RECONCILE_FAILURE_BLOCKS_OTHERS = 0
```

---

# 6. Retry classification

Classify blockers.

## RETRYABLE

Examples:

```text
temporary provider failure
temporary price/OHLCV unavailable
earnings/event fetch timeout
transient model/provider failure
temporary DB/queue contention
```

Eligible for scheduled automatic retry.

## REVIEW_REQUIRED

Examples:

```text
ticker/company identity conflict
security basis conflict
ADR/ADS ratio ambiguity
currency/security mapping conflict
irreconcilable official data conflict
unsupported valuation denominator
```

Do not retry endlessly.

Persist exact reason and require review.

## WAIT_FOR_DATA

Examples:

```text
new listing with insufficient OHLCV
official earnings/financial basis not yet available
required session data not yet published
```

Retry only after the relevant time/data condition.

---

# 7. Backoff / retry safety

Use repository-native bounded backoff.

Do not retry every few seconds.

Persist:

```text
attempt_count
last_attempt_at
next_retry_at
last_failure_stage
retry_class
```

Hard:

```text
UNBOUNDED_ONBOARDING_RETRY_LOOP = 0
```

---

# 8. Layer C — market preflight last-chance resume

Before each KR/US production packet cutoff:

```text
select pending subjects for that market only
```

Perform one bounded last-chance onboarding resume for eligible RETRYABLE/WAIT_FOR_DATA subjects.

Then freeze the packet universe.

Order:

```text
market preflight
→ pending resume attempt
→ readiness validator
→ ACTIVE_READY subjects included if completed before cutoff
→ cutoff
→ immutable packet universe snapshot
```

Hard:

```text
PREFLIGHT_ACTIVATION_AFTER_PACKET_CUTOFF_INCLUDED = 0
```

---

# 9. Preflight must stay bounded

Do NOT run an expensive full initial research pipeline for every pending subject inside the production deadline.

The preflight layer should:

```text
resume already-persisted missing stages
use cached/canonical evidence where safe
perform bounded acquisition only
```

Heavy initial research belongs to immediate onboarding / background reconciler.

Hard:

```text
PRELIVE_ONBOARDING_CAUSES_PACKET_DEADLINE_OVERRUN = 0
```

---

# 10. Market isolation preserved

KR preflight:

```text
KR pending only
```

US preflight:

```text
US/foreign pending only
```

Hard:

```text
US_PENDING_RECONCILER_BLOCKS_KR = 0
KR_PENDING_RECONCILER_BLOCKS_US = 0
```

---

# 11. Ready peers never wait

Example:

```text
US:
13 ACTIVE_READY
1 CPNG PENDING
```

If CPNG resume fails:

```text
13 ready subjects proceed
CPNG remains pending/excluded
```

Hard:

```text
PENDING_SUBJECT_BLOCKS_READY_PEERS = 0
```

---

# 12. Activation authority

Only the canonical onboarding coordinator/readiness validator may transition:

```text
PENDING → READY → ACTIVE
```

The reconciler does not directly set active.

It asks the coordinator to resume.

Hard:

```text
RECONCILER_DIRECTLY_FORCE_SETS_ACTIVE = 0
```

---

# 13. INITIAL_EVIDENCE generation contract

Because CPNG currently lacks only INITIAL_EVIDENCE, this stage is a mandatory positive control.

INITIAL_EVIDENCE must bind:

```text
current thesis version
latest safe earnings checkpoint
relevant company/thesis events
valuation context
current price
D/W/M OHLCV feature availability
Price Structure
material market context
material Unknowns
as_of
evidence fingerprint
```

Do not create a placeholder row.

Hard:

```text
INITIAL_EVIDENCE_PLACEHOLDER_COUNTS_AS_PASS = 0
```

---

# 14. Existing baseline ordering

If a legacy pending stock already has a valid final INITIAL_BASELINE_ASSESSMENT but lacks INITIAL_EVIDENCE:

do not delete/recreate the baseline unnecessarily.

Instead:

```text
validate that the baseline can be reconciled to the newly frozen initial evidence
```

If the baseline references materially inconsistent evidence:

mark REVIEW_REQUIRED.

If compatible:

retain historical assessment identity and complete onboarding.

---

# 15. Decision readiness after evidence completion

After required evidence prerequisites pass:

```text
generate v2 candidate
→ material disagreement adjudication if required
→ accepted decision
→ DECISION_READINESS PASS
```

No raw candidate may grant activation.

Hard:

```text
RAW_CANDIDATE_GRANTS_ONBOARDING_READY = 0
```

---

# 16. Same-day eligibility

Persist:

```text
onboarding_ready_at
activated_at
market_packet_cutoff
first_eligible_session
```

If completed before cutoff:

current cycle eligible.

If completed after cutoff:

next eligible cycle.

No retroactive packet mutation.

---

# 17. Generic new-registration regression

Use test namespace/database.

Create at least:

```text
one temporary KR subject
one temporary US subject
```

Do NOT add test-only securities to the real production monitoring list.

Validate:

```text
registration
→ PENDING
→ automatic immediate continuation
→ ACTIVE_READY
```

No user second command.

---

# 18. Failure-path regression

Test temporary subjects with injected failures.

Required:

## profile temporary failure

```text
PENDING
→ reconciler retry
→ complete
→ ACTIVE_READY
```

## evidence temporary failure

```text
PENDING blocker INITIAL_EVIDENCE
→ reconciler retry
→ complete
```

## assessment failure

```text
PENDING blocker INITIAL_BASELINE_ASSESSMENT
→ retry
```

## REVIEW_REQUIRED security conflict

```text
must remain non-active
must not retry forever
```

---

# 19. Cross-market negative controls

Test:

```text
US pending subject fails resume
→ KR packet still PASS
```

and:

```text
KR pending subject fails resume
→ US packet still PASS
```

Required:

```text
CROSS_MARKET_PENDING_ISOLATION = PASS
```

---

# 20. Same-market negative control

Example:

```text
7 KR ready
1 KR pending
```

The 7 ready subjects must still reach:

```text
candidate
accepted
renderer
test sink
```

Pending one remains excluded/NOT_READY.

Required:

```text
SAME_MARKET_PENDING_ISOLATION = PASS
```

---

# 21. CPNG production positive control

After implementation and merge, allow the GENERIC reconciler to encounter CPNG naturally.

Do not invoke a ticker-specific action.

Observe:

```text
before:
CPNG = PENDING_ONBOARDING
blocker = INITIAL_EVIDENCE

generic reconciler attempt
        ↓
INITIAL_EVIDENCE result
        ↓
readiness validation
        ↓
v2 candidate/adjudication/accepted
        ↓
ACTIVE_READY or exact safe blocker
```

Allowed final outcomes:

```text
ACTIVE_READY
PENDING_SAFE_RETRYABLE
PENDING_REVIEW_REQUIRED
```

Not allowed:

```text
forced ACTIVE
silent blocker deletion
cross-market blockage
```

---

# 22. CPNG activation success criteria

If CPNG becomes ACTIVE_READY:

require:

```text
INITIAL_EVIDENCE = PASS
INITIAL_BASELINE_ASSESSMENT = PASS
DECISION_READINESS = PASS
accepted decision exists
active = true
production_eligible = true
onboarding blockers = []
first_eligible_session computed
```

If not:

report exact canonical blocker.

---

# 23. User-facing registration response contract

Change the registration completion response semantics.

## ACTIVE_READY

Only then:

```text
✅ 모니터링 등록 완료
현재 상태: ACTIVE_READY
다음 eligible cycle부터 자동 점검
```

## PENDING

Say:

```text
🟡 모니터링 등록 준비 중
현재 상태: PENDING_ONBOARDING
남은 단계: ...
자동 온보딩이 계속 진행됩니다.
```

Do not require the user to know internal enum names unless useful.

---

# 24. No false "registration complete"

Hard:

```text
USER_TOLD_ACTIVE_WHILE_PENDING = 0
```

The detailed saved investment logic may still be displayed in either state.

---

# 25. Reconciler observability

Create safe operational status fields:

```text
pending subject count
retryable count
review-required count
oldest pending age
attempted this run
completed this run
remaining pending
```

No secrets/account IDs.

---

# 26. Alerting / warning

Do not alert simply because pending count > 0.

Raise operational warning when:

```text
pending age exceeds configured SLA
repeated retryable failure exceeds threshold
review-required exists before an expected market cutoff
systemic reconciler failure occurs
```

No Telegram user alert unless current product contract supports it.

---

# 27. Scheduler strategy

Preferred:

```text
background reconciler runs independently of market delivery jobs
+
bounded market-preflight resume
```

Use repository-native scheduler infrastructure.

Do not alter existing KR/US delivery times.

Hard:

```text
MARKET_DELIVERY_SCHEDULE_DIFF = 0
```

---

# 28. No production message replay

Do not resend prior KR/US production messages.

This feature affects future eligible packets.

Hard:

```text
HISTORICAL_PRODUCTION_MESSAGE_REPLAY = 0
```

---

# 29. Accepted-v2 ownership preserved

Do not alter:

```text
candidate
→ adjudication
→ accepted decision
```

Hard:

```text
ACCEPTED_DECISION_OWNERSHIP_REGRESSION = 0
```

---

# 30. Price Structure / valuation isolation

No algorithm changes.

Hard:

```text
PRICE_STRUCTURE_NUMERIC_DIFF = 0
VALUATION_NUMERIC_DIFF = 0
```

---

# 31. Test sink

Before main merge:

run the actual reconciler/cohort path against test namespace.

Then render all eligible test subjects to test sink.

For current real production subjects, use read-only/preflight-equivalent checks where safe.

No production recipient.

Hard:

```text
TEST_PRODUCTION_RECIPIENT_SEND = 0
PRODUCTION_DELIVERY_INTENT_CREATED_DURING_TEST = 0
```

---

# 32. Main merge gate

Require:

```text
OPEN_P0 = 0
OPEN_MATERIAL_P1 = 0

generic registration auto-completion PASS
reconciler idempotency PASS
retry classification PASS
cross-market isolation PASS
same-market isolation PASS
pre/post cutoff PASS
CPNG generic control safe
accepted-v2 ownership unchanged
Price Structure/valuation unchanged
test-sink PASS
scheduler unchanged
```

Then merge to main.

---

# 33. Required reports

Create:

1. `docs/reports/20260831-pending-onboarding-reconciler-scope.md`
2. `docs/reports/20260831-onboarding-retry-classification.md`
3. `docs/reports/20260831-background-onboarding-reconciler.md`
4. `docs/reports/20260831-market-preflight-onboarding-resume.md`
5. `docs/reports/20260831-onboarding-cutoff-eligibility.md`
6. `docs/reports/20260831-generic-new-registration-e2e.md`
7. `docs/reports/20260831-pending-isolation-negative-controls.md`
8. `docs/reports/20260831-cpng-generic-reconciler-control.md`
9. `docs/reports/20260831-registration-user-facing-status.md`
10. `docs/reports/20260831-reconciler-test-sink.md`
11. `docs/reports/20260831-reconciler-main-merge.md`
12. `docs/reports/20260831-reconciler-readiness.md`
13. `docs/reports/20260831-reconciler-artifact-index.md`

Machine-readable:

```text
docs/reports/20260831-pending-onboarding-reconciler.json
docs/reports/20260831-cpng-reconciler-control.json
docs/reports/20260831-reconciler-readiness.json
```

---

# 34. Required gates

Set exactly:

```text
CPNG_MANUAL_ONE_OFF_RESUME_BEFORE_RECONCILER =
0 / NONZERO

CPNG_TICKER_SPECIFIC_BYPASS =
0 / NONZERO

RECONCILER_AUTO_MONITORS_UNREQUESTED_SECURITY =
0 / NONZERO

ONE_PENDING_RECONCILE_FAILURE_BLOCKS_OTHERS =
0 / NONZERO

UNBOUNDED_ONBOARDING_RETRY_LOOP =
0 / NONZERO

PREFLIGHT_ACTIVATION_AFTER_PACKET_CUTOFF_INCLUDED =
0 / NONZERO

PRELIVE_ONBOARDING_CAUSES_PACKET_DEADLINE_OVERRUN =
0 / NONZERO

US_PENDING_RECONCILER_BLOCKS_KR =
0 / NONZERO

KR_PENDING_RECONCILER_BLOCKS_US =
0 / NONZERO

PENDING_SUBJECT_BLOCKS_READY_PEERS =
0 / NONZERO

RECONCILER_DIRECTLY_FORCE_SETS_ACTIVE =
0 / NONZERO

INITIAL_EVIDENCE_PLACEHOLDER_COUNTS_AS_PASS =
0 / NONZERO

RAW_CANDIDATE_GRANTS_ONBOARDING_READY =
0 / NONZERO

GENERIC_NEW_KR_REGISTRATION =
PASS / FAIL

GENERIC_NEW_US_REGISTRATION =
PASS / FAIL

CROSS_MARKET_PENDING_ISOLATION =
PASS / FAIL

SAME_MARKET_PENDING_ISOLATION =
PASS / FAIL

CPNG_RECONCILER_RESULT =
ACTIVE_READY /
PENDING_SAFE_RETRYABLE /
PENDING_REVIEW_REQUIRED /
FAIL

CPNG_INITIAL_EVIDENCE =
PASS /
PENDING /
FAIL

CPNG_DECISION_READINESS =
PASS /
PENDING /
FAIL

CPNG_ACCEPTED_DECISION =
BUY /
HOLD /
SELL /
NOT_READY

CPNG_FIRST_ELIGIBLE_SESSION =
...

USER_TOLD_ACTIVE_WHILE_PENDING =
0 / NONZERO

MARKET_DELIVERY_SCHEDULE_DIFF =
0 / NONZERO

HISTORICAL_PRODUCTION_MESSAGE_REPLAY =
0 / NONZERO

ACCEPTED_DECISION_OWNERSHIP_REGRESSION =
0 / NONZERO

PRICE_STRUCTURE_NUMERIC_DIFF =
0 / NONZERO

VALUATION_NUMERIC_DIFF =
0 / NONZERO

TEST_EXACT_PAYLOAD =
PASS / FAIL

TEST_PRODUCTION_RECIPIENT_SEND =
0 / NONZERO

PRODUCTION_DELIVERY_INTENT_CREATED_DURING_TEST =
0 / NONZERO

OPEN_P0 =
...

OPEN_MATERIAL_P1 =
...

PENDING_ONBOARDING_AUTOMATION =
READY_FOR_MAIN /
FAIL
```

---

# 35. Completion response

Return:

```text
MASTER_INSTRUCTION_COMMIT = ...
BASE_SHA = ...
IMPLEMENTATION_SHA = ...
REPORT_COMMIT = ...
FINAL_MAIN = ...
ORIGIN_MAIN = ...
OPERATING = ...

BACKGROUND_RECONCILER =
enabled / disabled

MARKET_PREFLIGHT_RESUME =
enabled / disabled

GENERIC_NEW_KR_REGISTRATION = ...
GENERIC_NEW_US_REGISTRATION = ...

CROSS_MARKET_PENDING_ISOLATION = ...
SAME_MARKET_PENDING_ISOLATION = ...

CPNG_BEFORE =
state ...
blockers ...

CPNG_RECONCILER_ATTEMPT =
timestamp ...
stages attempted ...
result ...

CPNG_INITIAL_EVIDENCE = ...
CPNG_DECISION_READINESS = ...
CPNG_ACCEPTED_DECISION = ...
CPNG_RECONCILER_RESULT = ...
CPNG_FIRST_ELIGIBLE_SESSION = ...

CPNG_MANUAL_ONE_OFF_RESUME_BEFORE_RECONCILER = 0
CPNG_TICKER_SPECIFIC_BYPASS = 0
PENDING_SUBJECT_BLOCKS_READY_PEERS = 0

CURRENT_PENDING_COUNT = ...
CURRENT_RETRYABLE_COUNT = ...
CURRENT_REVIEW_REQUIRED_COUNT = ...
CURRENT_ACTIVE_READY_COUNT = ...

USER_TOLD_ACTIVE_WHILE_PENDING = 0
MARKET_DELIVERY_SCHEDULE_DIFF = 0
HISTORICAL_PRODUCTION_MESSAGE_REPLAY = 0

ACCEPTED_DECISION_OWNERSHIP_REGRESSION = 0
PRICE_STRUCTURE_NUMERIC_DIFF = 0
VALUATION_NUMERIC_DIFF = 0

TEST_MESSAGE_COUNT = ...
TEST_EXACT_PAYLOAD = ...
TEST_PRODUCTION_RECIPIENT_SEND = 0
PRODUCTION_DELIVERY_INTENT_CREATED_DURING_TEST = 0

OPEN_P0 = ...
OPEN_MATERIAL_P1 = ...

PENDING_ONBOARDING_AUTOMATION =
READY_FOR_MAIN /
FAIL

NEXT_ACTION =
WAIT_FOR_NATURAL_US_PACKET /
WAIT_FOR_NATURAL_KR_PACKET /
BOUNDED_REPAIR /
NO_ACTION

ZIP = ...
ZIP_SHA256 = ...
```

---

# 36. Mandatory completion ZIP

Create:

`20260831-pending-onboarding-auto-reconciler-and-preflight-resume-bundle.zip`

Include:

```text
exact instruction
reconciler design
retry classification
preflight-resume design
generic KR/US registration E2E
failure-path tests
cross-market/same-market isolation tests
CPNG before/after generic reconciler evidence
first-eligible-session evidence
test-sink messages
user-facing status contract
main-merge evidence
readiness JSON
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

# 37. Final principle

Do not manually rescue CPNG.

Make the generic onboarding system rescue any safe pending subject.

The correct behavior is:

```text
PENDING
→ automatically resume missing canonical stages
→ validate
→ ACTIVE_READY only on PASS
```

and if it still cannot complete:

```text
remain PENDING safely
while all ready peers and the other market continue normally.
```
