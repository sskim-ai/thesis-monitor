# thesis-monitor — V2 Adjudicated Decision Ownership Repair
## Make `accepted_decision` the single authoritative v2 decision after adjudication
## Fix raw-candidate leakage into summary / renderer / test-sink / migration readiness
## Preserve v2 reasoning logic; do not retune BUY/HOLD/SELL
## V1 production canary remains unchanged

---

# 0. Metadata

- Repository: `sskim-ai/thesis-monitor`
- Date: `2026-08-30 KST`
- Workstream: `V2_ADJUDICATED_DECISION_OWNERSHIP_REPAIR`
- Task class: `DECISION_OWNERSHIP + REPORTING + RENDERER + TEST_SINK_CONVERGENCE`
- V2 production exposure: `0`
- V2 remains shadow/test-only in this task
- V1 production canary: preserve current runtime state
- Automated trading: `0`
- Order sizing: `0`
- Thesis/monitoring mutation: `0`
- Scheduler mutation: `0`

Source bundle:

`20260830-preconfirmation-asymmetry-decision-engine-v2-bundle.zip`

Source-supported latest lineage:

```text
MASTER_INSTRUCTION_COMMIT =
46bdf4c

BASE_SHA =
1359a5769c36d64dd5e0acc9bbf03f90578fb062

TRACK_A =
5aed685d588f0cc6572ceb582f96be492cfb5e40

TRACK_B =
de2d7c9f153429500038416c60f02caa0fdc6b92

TRACK_C =
209e1ebdf3e77b8ea5806cb5c9bf6db59b08712e

TRACK_D =
c0c9139babb06ead11112aea072a67ef364a9b22

REPORT_COMMIT =
40a8e20

FINAL_MAIN / OPERATING =
29bdd4cf378438fedad7f602b4b8ede80c46dd44
```

Before implementation:

```text
git fetch origin
verify clean worktrees
resolve actual latest safe origin/main
resolve actual operating checkout
use 29bdd4... or a safe linear descendant
record current v1 canary state
```

Do not alter v1 canary membership or decisions.

---

# 1. Exact defect

The v2 pipeline currently has two different decision authorities:

```text
raw v2 candidate
→ summary
→ test sink
→ migration readiness

material disagreement
→ adjudication
→ accepted decision
```

The source bundle proves these paths diverge.

Raw v2 completion summary says:

```text
BUY 2 / HOLD 14 / SELL 4

003690 = BUY
GOOGL = BUY
HUT = SELL
RXRX = HOLD
SNDK = SELL
```

But the adjudication report says:

```text
003690:
V1 HOLD vs V2 BUY
KEEP_V1
accepted = HOLD

GOOGL:
V1 HOLD vs V2 BUY
KEEP_V2
accepted = BUY

HUT:
V1 HOLD vs V2 SELL
KEEP_V2
accepted = SELL

RXRX:
V1 SELL vs V2 HOLD
KEEP_V2
accepted = HOLD

SNDK:
V1 HOLD vs V2 SELL
KEEP_V1
accepted = HOLD
```

Therefore the authoritative frozen v2 distribution after adjudication is:

```text
BUY 1
HOLD 16
SELL 3
```

not:

```text
BUY 2
HOLD 14
SELL 4
```

---

# 2. Root principle

V2 decision ownership must be:

```text
candidate_decision
        ↓
material disagreement?
        │
        ├─ NO
        │   ↓
        │ accepted_decision = candidate_decision
        │
        └─ YES
            ↓
        adjudication
            ↓
        accepted_decision = adjudicated winner
```

Everything downstream must consume:

```text
accepted_decision
```

only.

---

# 3. Keep all three artifacts

Do NOT delete candidate/adjudication history.

Persist separately:

```text
candidate_decision
adjudication_result
accepted_decision
```

Each must have immutable identity/fingerprint.

Recommended metadata:

```text
candidate_decision_id
candidate_evidence_fingerprint

adjudication_id
adjudication_reason
adjudication_recommendation

accepted_decision_id
accepted_decision
accepted_source =
  CANDIDATE
  ADJUDICATION_KEEP_V1
  ADJUDICATION_KEEP_V2
accepted_evidence_fingerprint
accepted_as_of
```

Use repository-native names if equivalent fields exist.

---

# 4. Accepted decision is authoritative

The following consumers MUST use accepted v2 decision state:

```text
completion summary
current v2 decision table
distribution counts
renderer
test-sink messages
message-quality validator
migration readiness
canary-migration recommendation
decision agreement reports
machine-readable readiness JSON
```

Hard:

```text
RAW_V2_CANDIDATE_USED_AS_FINAL_AFTER_ADJUDICATION = 0
```

---

# 5. No second reasoning pass merely to fix ownership

This task is NOT a decision-calibration rerun.

For the frozen v2 evidence:

do not regenerate BUY/HOLD/SELL merely to obtain the expected distribution.

Use the existing:

```text
candidate
+
adjudication
```

to deterministically derive accepted decisions.

Hard:

```text
OWNERSHIP_REPAIR_REDECIDED_FROZEN_CASES = 0
```

---

# 6. Frozen accepted-decision control set

Under the exact frozen source evidence, require:

```text
000660 = HOLD
003690 = HOLD
005490 = HOLD
005930 = HOLD
010120 = HOLD
012450 = HOLD
086280 = HOLD

CORZ = HOLD
CRCL = HOLD
GOOGL = BUY
HUT = SELL
IBM = HOLD
MU = HOLD
RXRX = HOLD
SKHY = HOLD
SNDK = HOLD
TSLA = SELL
TSM = HOLD
WRD = HOLD
WULF = SELL
```

Frozen distribution:

```text
BUY = 1
HOLD = 16
SELL = 3
```

Hard:

```text
FROZEN_ACCEPTED_V2_DISTRIBUTION = PASS
```

These are frozen regression expectations only.
Fresh future evidence may legitimately change decisions.

---

# 7. Five adjudication controls

Exact accepted ownership:

```text
003690
candidate = BUY
adjudication = KEEP_V1
accepted = HOLD
accepted_source = ADJUDICATION_KEEP_V1

GOOGL
candidate = BUY
adjudication = KEEP_V2
accepted = BUY
accepted_source = ADJUDICATION_KEEP_V2

HUT
candidate = SELL
adjudication = KEEP_V2
accepted = SELL
accepted_source = ADJUDICATION_KEEP_V2

RXRX
candidate = HOLD
adjudication = KEEP_V2
accepted = HOLD
accepted_source = ADJUDICATION_KEEP_V2

SNDK
candidate = SELL
adjudication = KEEP_V1
accepted = HOLD
accepted_source = ADJUDICATION_KEEP_V1
```

Hard:

```text
FIVE_ADJUDICATION_ACCEPTED_OWNERSHIP = PASS
```

---

# 8. Why KEEP_V1 is still a v2 accepted decision

`ADJUDICATION_KEEP_V1` does NOT mean:

```text
v2 failed
or
v1 becomes the permanent engine
```

It means:

```text
within the v2 review process,
the adjudicator concluded the v1 classification
was better supported by the same canonical evidence.
```

The accepted v2 record must still contain:

```text
accepted_decision
accepted_source
adjudication reason
v2 evidence-maturity/asymmetry context where relevant
```

Do not drop v2 explanatory fields simply because KEEP_V1 won.

---

# 9. Accepted reasoning ownership

For adjudicated cases, user/test-facing decision explanation must align with the accepted classification.

Do not render:

```text
accepted = HOLD
but decisive reason from raw SELL/BUY candidate
```

Construct one accepted decision plan from:

```text
winning decision semantics
adjudication rationale
canonical evidence refs
v2 maturity/pricing/asymmetry fields that remain compatible
```

Hard:

```text
ACCEPTED_DECISION_REASON_CONFLICT = 0
```

---

# 10. Evidence refs remain canonical

Adjudication cannot invent new company/market numerics.

Every accepted explanation must use existing canonical refs from:

```text
v1 evidence packet
v2 evidence packet
adjudication-supported structured interpretations
```

Hard:

```text
ADJUDICATION_INTRODUCED_UNREGISTERED_NUMERIC = 0
```

---

# 11. Pre-confirmation BUY ownership

Under frozen accepted decisions:

```text
GOOGL = BUY
PRE_CONFIRMATION_BUY = true
```

003690 raw v2 had:

```text
BUY
PRE_CONFIRMATION_BUY = true
```

but accepted decision is HOLD.

Therefore the final accepted 003690 record must NOT still claim:

```text
PRE_CONFIRMATION_BUY = true
```

as a current accepted flag.

Preserve it only in candidate-history/audit.

Hard:

```text
REJECTED_PRECONFIRMATION_BUY_LEAKED_TO_ACCEPTED = 0
```

---

# 12. Accepted v2 maturity/asymmetry consistency

For each adjudicated case verify that accepted fields are semantically compatible.

Examples:

```text
accepted HOLD
may still have PARTIAL maturity
and FAVORABLE candidate asymmetry,
but the accepted rationale must explain why residual risk/data quality
prevents BUY.

accepted SELL
must not retain a final user-facing
FAVORABLE asymmetry flag without qualification.
```

Do not mechanically copy every raw-v2 interpretation into accepted state.

If an interpretation is candidate-specific:

keep it in candidate history,
not accepted output.

---

# 13. Track A — canonical ownership implementation

Implement one deterministic decision-resolution service or repository-native equivalent:

```text
resolve_accepted_v2_decision(
    candidate,
    disagreement,
    adjudication
)
```

Responsibilities:

```text
choose accepted decision
assign accepted source
bind accepted reasoning
bind accepted v2 interpretation fields
preserve immutable candidate/adjudication history
produce accepted fingerprint
```

No AI call required for this ownership resolution.

---

# 14. Idempotency

Given identical:

```text
candidate ID
adjudication ID
evidence fingerprint
```

accepted resolution must be deterministic/idempotent.

Hard:

```text
ACCEPTED_DECISION_RESOLUTION_IDEMPOTENT = PASS
```

---

# 15. Missing adjudication fail-closed

If:

```text
material disagreement = true
```

but adjudication is:

```text
missing
invalid
not final
```

then:

```text
accepted_decision = NOT_READY
```

Do NOT fall back silently to raw candidate.

Hard:

```text
MATERIAL_DISAGREEMENT_WITHOUT_ADJUDICATION_ACCEPTED = 0
```

---

# 16. Non-material disagreement policy

If the existing architecture distinguishes:

```text
material
non-material
```

disagreements:

only the configured adjudication-required class blocks accepted resolution.

Document the rule.

Do not introduce ad hoc per-ticker behavior.

---

# 17. Track B — summary ownership repair

Regenerate:

```text
COMPLETION_SUMMARY
current decisions
distribution
preconfirmation BUY count
postconfirmation HOLD count
migration readiness
```

from accepted decisions.

For the frozen evidence, expected:

```text
BUY = 1
HOLD = 16
SELL = 3

accepted preconfirmation BUY:
GOOGL = true

003690:
accepted HOLD
candidate preconfirmation BUY retained only in audit history
```

Do not report raw candidate counts as final distribution.

---

# 18. Machine-readable report ownership

Update all current v2 machine-readable artifacts so fields are explicit:

```text
candidate_decision
accepted_decision
accepted_source
adjudication_status
```

Avoid ambiguous field:

```text
decision
```

unless it explicitly means:

```text
accepted_decision
```

Document that contract.

Hard:

```text
AMBIGUOUS_V2_DECISION_FIELD = 0
```

---

# 19. Renderer ownership

The v2 renderer must consume:

```text
accepted_decision_plan
```

not:

```text
raw_candidate
```

Hard:

```text
V2_RENDERER_USES_RAW_CANDIDATE_AFTER_ADJUDICATION = 0
```

---

# 20. Validator ownership

Validator must validate:

```text
accepted decision
accepted polarity
accepted maturity/asymmetry fields
accepted change conditions
accepted evidence refs
```

against the same accepted plan used by renderer.

Do not independently choose between v1/v2.

Hard:

```text
V2_VALIDATOR_RECOMPUTES_ACCEPTED_DECISION = 0
```

---

# 21. Test-sink ownership

The prior v2 test sink used raw v2 decisions.

That evidence is not sufficient for migration readiness.

After repair, send all accepted v2 decisions to the dedicated non-production test sink.

User-facing label:

```text
🧪 SHADOW V2 · accepted decision 검증
```

or equivalent.

No production recipient.

---

# 22. Frozen test-sink exact controls

Under frozen same evidence, exact decision labels in the new accepted test messages must include:

```text
003690 HOLD
GOOGL BUY
HUT SELL
RXRX HOLD
SNDK HOLD
TSLA SELL
WULF SELL
```

and all remaining subjects HOLD.

Hard:

```text
ACCEPTED_TEST_SINK_DECISION_PARITY = PASS
```

---

# 23. Accepted reasoning controls

Mandatory exact semantic review:

## 003690

Accepted:

```text
HOLD
```

Must explain why partial proof + valuation discount do NOT yet justify BUY after adjudication.

Must not still speak as if current decision is pre-confirmation BUY.

## GOOGL

Accepted:

```text
BUY
```

Must preserve the v2 pre-confirmation asymmetry rationale.

## HUT

Accepted:

```text
SELL
```

Must preserve downside-dominant risk/reward reasoning.

## RXRX

Accepted:

```text
HOLD
```

Must not keep raw/v1 SELL rhetoric as the decisive conclusion.

## SNDK

Accepted:

```text
HOLD
```

Must not keep raw v2 SELL as current user-facing decision.

---

# 24. Polarity / localization controls

Preserve already-passing contracts:

```text
BULLISH / BEARISH / NEUTRAL polarity
US Korean decision rendering
003690 = 코리안리
```

Hard:

```text
POLARITY_REGRESSION = 0
US_DECISION_LOCALIZATION_REGRESSION = 0
TICKER_003690_IDENTITY = 코리안리
```

---

# 25. Price Structure / valuation isolation

No Price Structure or valuation computation changes.

Hard:

```text
PRICE_STRUCTURE_NUMERIC_DIFF = 0
VALUATION_NUMERIC_DIFF = 0
```

---

# 26. Current v1 production canary isolation

Current v1 production canary remains untouched.

Do not:

```text
change v1 decision block
change v1 canary subjects
replace v1 with v2
increment v1 natural counters
```

Hard:

```text
V1_CANARY_STATE_DIFF = 0
V2_PRODUCTION_DECISION_BLOCK_VISIBLE = 0
```

---

# 27. Track C — frozen 20-subject accepted replay

Use the frozen v2 source artifacts.

Do not call new external data.

Do not change evidence cutoff.

Resolve all 20 accepted decisions deterministically.

Required:

```text
20/20 accepted records
5/5 adjudication controls
distribution 1/16/3
```

---

# 28. Fresh current shadow after ownership repair

After frozen ownership PASS, optionally run one current 20-stock v2 shadow through the repaired pipeline using fresh canonical evidence.

This fresh run is diagnostic.

If evidence changed:

decisions may differ.

The important invariant is:

```text
candidate
→ adjudication if needed
→ accepted
→ renderer/test/readiness
```

If a fresh material disagreement occurs:

do not produce accepted decision until adjudication completes.

---

# 29. Migration readiness must use accepted decisions

Recompute:

```text
V2_MIGRATION_RECOMMENDATION
```

only after:

```text
accepted 20/20
accepted test-sink PASS
accepted message-quality PASS
ownership reports PASS
```

Do not use candidate-level test results as migration evidence.

---

# 30. Migration readiness status

Allowed:

```text
READY_FOR_BOUNDED_CANARY_MIGRATION
READY_WITH_OBSERVATION
NOT_READY
```

Do NOT migrate production in this task.

---

# 31. Current expected recommendation

Do not hard-code the recommendation.

Given the source evidence, `READY_WITH_OBSERVATION` may remain reasonable.

But recalculate from the corrected accepted-decision pipeline.

---

# 32. Accepted-distribution diagnostics

Report separately:

```text
candidate distribution
accepted distribution
```

This distinction must remain visible for audit.

For frozen source:

```text
candidate =
BUY 2 / HOLD 14 / SELL 4

accepted =
BUY 1 / HOLD 16 / SELL 3
```

---

# 33. Candidate-vs-accepted disagreement report

For all 20:

```text
ticker
v1
v2 candidate
material disagreement?
adjudication
accepted decision
accepted source
```

This becomes the primary audit artifact.

---

# 34. Historical candidate preservation

Do not rewrite prior raw v2 test-sink evidence.

Keep it as historical candidate-path evidence.

Create a correction/addendum stating:

```text
prior test sink validated raw v2 candidate rendering,
not accepted adjudicated migration output.
```

---

# 35. Completion summary correction

The previous completion summary is materially misleading if read as final accepted decisions.

Do one of:

```text
regenerate mutable completion summary
or
add explicit corrected completion summary / errata
```

Prefer preserving immutable artifacts with errata.

Hard:

```text
FINAL_SUMMARY_REPORTS_RAW_V2_AS_ACCEPTED = 0
```

---

# 36. Required tests

Focused tests must include:

### 36.1 No disagreement

```text
candidate HOLD
no material disagreement
→ accepted HOLD / source CANDIDATE
```

### 36.2 KEEP_V1

```text
candidate BUY
v1 HOLD
adjudication KEEP_V1
→ accepted HOLD
```

### 36.3 KEEP_V2

```text
candidate SELL
adjudication KEEP_V2
→ accepted SELL
```

### 36.4 Missing adjudication

```text
material disagreement
no adjudication
→ NOT_READY
```

### 36.5 Idempotency

same inputs → same accepted fingerprint.

### 36.6 Renderer

renderer uses accepted, not candidate.

### 36.7 Validator

validator fails if rendered decision != accepted decision.

### 36.8 Reports

counts come from accepted decisions.

---

# 37. Test-sink full-universe proof

Send accepted v2 messages for the actual current/frozen 20-subject set to dedicated test sink.

No production recipient.

Require:

```text
TEST_ACCEPTED_V2_MESSAGE_COUNT = 20
TEST_ACCEPTED_V2_EXACT_PAYLOAD = PASS
TEST_ACCEPTED_V2_MESSAGE_QUALITY = PASS
TEST_PRODUCTION_RECIPIENT_SEND = 0
PRODUCTION_DELIVERY_INTENT_CREATED = 0
```

---

# 38. BUY path control

GOOGL accepted BUY is now a real accepted-v2 BUY control.

Verify:

```text
accepted = BUY
preconfirmation_buy = true
BUY-side polarity correct
SELL-side risk evidence correct
no order command
```

This is stronger migration evidence than the previous raw candidate-only BUY test.

Hard:

```text
ACCEPTED_GOOGL_PRECONFIRMATION_BUY = PASS
```

---

# 39. HOLD controls

003690 and SNDK are critical controls because raw v2 wanted a directional classification but adjudication retained HOLD.

Hard:

```text
ACCEPTED_003690_HOLD = PASS
ACCEPTED_SNDK_HOLD = PASS
```

---

# 40. SELL controls

HUT / TSLA / WULF accepted SELL.

Hard:

```text
ACCEPTED_SELL_CONTROLS = PASS
```

SELL remains analytical, not mandatory liquidation.

---

# 41. No order-command language

Hard:

```text
ORDER_COMMAND_LANGUAGE = 0
ORDER_SIZING_OUTPUT = 0
```

---

# 42. No fixed-rule regression

Preserve v2 design:

```text
PRECONFIRMATION_DECISION_FROM_FIXED_RULE = 0
FINAL_DECISION_FROM_FIXED_WEIGHT_SUM = 0
MATURITY_HARD_MAPS_TO_DECISION = 0
```

---

# 43. Required architecture docs

Create/update:

```text
docs/architecture/V2_ACCEPTED_DECISION_OWNERSHIP.md
docs/architecture/DECISION_ENGINE_V2_SHADOW_MIGRATION.md
```

Canonical statement:

```text
candidate is not final
adjudication resolves material disagreement
accepted_decision is the only downstream authority
```

---

# 44. Required reports

Create at minimum:

1. `docs/reports/20260830-v2-accepted-decision-root-cause.md`
2. `docs/reports/20260830-v2-accepted-decision-contract.md`
3. `docs/reports/20260830-v2-candidate-vs-accepted-20.md`
4. `docs/reports/20260830-v2-five-adjudication-ownership-controls.md`
5. `docs/reports/20260830-v2-accepted-reasoning-controls.md`
6. `docs/reports/20260830-v2-accepted-distribution.md`
7. `docs/reports/20260830-v2-completion-summary-errata.md`
8. `docs/reports/20260830-v2-accepted-renderer-validator.md`
9. `docs/reports/20260830-v2-accepted-test-sink.md`
10. `docs/reports/20260830-v2-accepted-message-quality.md`
11. `docs/reports/20260830-v2-accepted-migration-readiness.md`
12. `docs/reports/20260830-v2-accepted-artifact-index.md`

Machine-readable:

```text
docs/reports/20260830-v2-accepted-decisions.json
docs/reports/20260830-v2-accepted-migration-readiness.json
```

---

# 45. Required gates

Set exactly:

```text
RAW_V2_CANDIDATE_USED_AS_FINAL_AFTER_ADJUDICATION =
0 / NONZERO

OWNERSHIP_REPAIR_REDECIDED_FROZEN_CASES =
0 / NONZERO

FROZEN_ACCEPTED_V2_DISTRIBUTION =
PASS / FAIL

FIVE_ADJUDICATION_ACCEPTED_OWNERSHIP =
PASS / FAIL

ACCEPTED_DECISION_REASON_CONFLICT =
0 / NONZERO

ADJUDICATION_INTRODUCED_UNREGISTERED_NUMERIC =
0 / NONZERO

REJECTED_PRECONFIRMATION_BUY_LEAKED_TO_ACCEPTED =
0 / NONZERO

ACCEPTED_DECISION_RESOLUTION_IDEMPOTENT =
PASS / FAIL

MATERIAL_DISAGREEMENT_WITHOUT_ADJUDICATION_ACCEPTED =
0 / NONZERO

AMBIGUOUS_V2_DECISION_FIELD =
0 / NONZERO

V2_RENDERER_USES_RAW_CANDIDATE_AFTER_ADJUDICATION =
0 / NONZERO

V2_VALIDATOR_RECOMPUTES_ACCEPTED_DECISION =
0 / NONZERO

ACCEPTED_TEST_SINK_DECISION_PARITY =
PASS / FAIL

FINAL_SUMMARY_REPORTS_RAW_V2_AS_ACCEPTED =
0 / NONZERO

CANDIDATE_BUY_COUNT =
2 / OTHER

CANDIDATE_HOLD_COUNT =
14 / OTHER

CANDIDATE_SELL_COUNT =
4 / OTHER

ACCEPTED_BUY_COUNT =
1 / OTHER

ACCEPTED_HOLD_COUNT =
16 / OTHER

ACCEPTED_SELL_COUNT =
3 / OTHER

ACCEPTED_GOOGL_PRECONFIRMATION_BUY =
PASS / FAIL

ACCEPTED_003690_HOLD =
PASS / FAIL

ACCEPTED_SNDK_HOLD =
PASS / FAIL

ACCEPTED_SELL_CONTROLS =
PASS / FAIL

POLARITY_REGRESSION =
0 / NONZERO

US_DECISION_LOCALIZATION_REGRESSION =
0 / NONZERO

TICKER_003690_IDENTITY =
코리안리 / OTHER

PRICE_STRUCTURE_NUMERIC_DIFF =
0 / NONZERO

VALUATION_NUMERIC_DIFF =
0 / NONZERO

V1_CANARY_STATE_DIFF =
0 / NONZERO

V2_PRODUCTION_DECISION_BLOCK_VISIBLE =
0 / NONZERO

PRECONFIRMATION_DECISION_FROM_FIXED_RULE =
0 / NONZERO

FINAL_DECISION_FROM_FIXED_WEIGHT_SUM =
0 / NONZERO

MATURITY_HARD_MAPS_TO_DECISION =
0 / NONZERO

ORDER_COMMAND_LANGUAGE =
0 / NONZERO

ORDER_SIZING_OUTPUT =
0 / NONZERO

TEST_ACCEPTED_V2_MESSAGE_COUNT =
20 / OTHER

TEST_ACCEPTED_V2_EXACT_PAYLOAD =
PASS / FAIL

TEST_ACCEPTED_V2_MESSAGE_QUALITY =
PASS / FAIL

TEST_PRODUCTION_RECIPIENT_SEND =
0 / NONZERO

PRODUCTION_DELIVERY_INTENT_CREATED =
0 / NONZERO

OPEN_P0 =
...

OPEN_MATERIAL_P1 =
...

V2_ACCEPTED_OWNERSHIP =
READY_FOR_MIGRATION_REVIEW /
FAIL

V2_MIGRATION_RECOMMENDATION =
READY_FOR_BOUNDED_CANARY_MIGRATION /
READY_WITH_OBSERVATION /
NOT_READY
```

---

# 46. PASS rule

Require:

```text
accepted_decision is single downstream authority
5/5 adjudication controls correct
frozen distribution = 1 BUY / 16 HOLD / 3 SELL
accepted reasoning matches accepted labels
no rejected preconfirmation BUY leakage
reports/counts use accepted decisions
renderer/validator use accepted plan
20/20 accepted test-sink exact PASS
v1 production canary unchanged
v2 production exposure = 0
P0 = 0
material P1 = 0
```

Then:

```text
V2_ACCEPTED_OWNERSHIP = READY_FOR_MIGRATION_REVIEW
```

Do not migrate production in this task.

---

# 47. Completion response

Return:

```text
MASTER_INSTRUCTION_COMMIT = ...
BASE_SHA = ...

TRACK_A_BRANCH = ...
TRACK_A_IMPLEMENTATION = ...

TRACK_B_BRANCH = ...
TRACK_B_IMPLEMENTATION = ...

TRACK_C_BRANCH = ...
TRACK_C_RESULT = ...

REPORT_COMMIT = ...
FINAL_MAIN = ...
OPERATING = ...

CANDIDATE_DISTRIBUTION =
BUY 2 / HOLD 14 / SELL 4

ACCEPTED_DISTRIBUTION =
BUY 1 / HOLD 16 / SELL 3

FIVE_ADJUDICATION_CONTROLS =
003690 candidate BUY → accepted HOLD / KEEP_V1
GOOGL candidate BUY → accepted BUY / KEEP_V2
HUT candidate SELL → accepted SELL / KEEP_V2
RXRX candidate HOLD → accepted HOLD / KEEP_V2
SNDK candidate SELL → accepted HOLD / KEEP_V1

RAW_V2_CANDIDATE_USED_AS_FINAL_AFTER_ADJUDICATION = 0
OWNERSHIP_REPAIR_REDECIDED_FROZEN_CASES = 0
FROZEN_ACCEPTED_V2_DISTRIBUTION = ...
FIVE_ADJUDICATION_ACCEPTED_OWNERSHIP = ...

ACCEPTED_DECISION_REASON_CONFLICT = 0
ADJUDICATION_INTRODUCED_UNREGISTERED_NUMERIC = 0
REJECTED_PRECONFIRMATION_BUY_LEAKED_TO_ACCEPTED = 0

ACCEPTED_DECISION_RESOLUTION_IDEMPOTENT = ...
MATERIAL_DISAGREEMENT_WITHOUT_ADJUDICATION_ACCEPTED = 0

AMBIGUOUS_V2_DECISION_FIELD = 0
V2_RENDERER_USES_RAW_CANDIDATE_AFTER_ADJUDICATION = 0
V2_VALIDATOR_RECOMPUTES_ACCEPTED_DECISION = 0

ACCEPTED_GOOGL_PRECONFIRMATION_BUY = ...
ACCEPTED_003690_HOLD = ...
ACCEPTED_SNDK_HOLD = ...
ACCEPTED_SELL_CONTROLS = ...

TEST_ACCEPTED_V2_MESSAGE_COUNT = 20
TEST_ACCEPTED_V2_EXACT_PAYLOAD = ...
TEST_ACCEPTED_V2_MESSAGE_QUALITY = ...
TEST_PRODUCTION_RECIPIENT_SEND = 0
PRODUCTION_DELIVERY_INTENT_CREATED = 0

POLARITY_REGRESSION = 0
US_DECISION_LOCALIZATION_REGRESSION = 0
TICKER_003690_IDENTITY = 코리안리

PRICE_STRUCTURE_NUMERIC_DIFF = 0
VALUATION_NUMERIC_DIFF = 0
V1_CANARY_STATE_DIFF = 0
V2_PRODUCTION_DECISION_BLOCK_VISIBLE = 0

OPEN_P0 = ...
OPEN_MATERIAL_P1 = ...

V2_ACCEPTED_OWNERSHIP =
READY_FOR_MIGRATION_REVIEW /
FAIL

V2_MIGRATION_RECOMMENDATION =
READY_FOR_BOUNDED_CANARY_MIGRATION /
READY_WITH_OBSERVATION /
NOT_READY

NEXT_ACTION =
REVIEW_ACCEPTED_V2_MESSAGES /
PREPARE_V2_BOUNDED_MIGRATION /
BOUNDED_REPAIR /
NO_ACTION

ZIP = ...
ZIP_SHA256 = ...
```

---

# 48. Mandatory completion ZIP

Create:

`20260830-v2-adjudicated-decision-ownership-repair-bundle.zip`

Include:

```text
exact master instruction
all track instructions
root-cause report
accepted-decision contract
20-stock candidate-vs-accepted table
five adjudication controls
accepted reasoning controls
corrected distribution
completion-summary errata
renderer/validator ownership evidence
20 accepted exact test messages
message-quality review
migration readiness
machine-readable accepted-decision JSON
test/CI summary
artifact index
```

Exclude:

```text
secrets
Telegram IDs
tokens
auth headers
account identifiers
hidden chain-of-thought
```

Compute SHA-256.

---

# 49. Final principle

A v2 candidate is a proposal.

Adjudication resolves material disagreement.

Only the resulting accepted decision may drive:

```text
summary
renderer
validator
test sink
migration readiness
```

Preserve every earlier stage for audit,
but never let a rejected candidate leak back into the final product path.
