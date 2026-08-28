# thesis-monitor — Run-44 V3 Validator Convergence + Cross-Market Final Readiness
## One integrated task after Provisional Bollinger / Price Label rollout
## Verify first; repair only if still necessary
## Freeze the KR close incident as a permanent regression control
## Cross-market full-message test → final operating readiness → natural observation

---

# 0. Status / source bundle

Repository:

`sskim-ai/thesis-monitor`

Date:

`2026-08-28 KST`

Task:

`RUN44_V3_VALIDATOR_CONVERGENCE_CROSS_MARKET_FINAL_READINESS`

This instruction supersedes the previously prepared standalone hotfix:

`20260828-v3-renderer-validator-ownership-alignment-kr-close-p1-hotfix.md`

Do NOT execute that old instruction separately.

The user intentionally cancelled the 2026-08-28 16:50 KR close production run.
Do not recreate or manually rerun that production job today.

---

# 1. Latest completed rollout evidence

The supplied completed bundle reports:

```text
Base:
5500f539fc93a9162f762cef4f7069f24d0350db

Work-instruction:
73286dd44135bbc30ef3a145e02f5db81aedbdea

Implementation:
8c3bb493dc45a12c837053e08361f949ff771f00

Evidence commit:
d3a58c953c2dd6d100031421770be3a54d0328b5

Completion-summary final main / operating:
026df711fa151cc7816b2a57d9ed7d224c1b33cf
```

The completion summary also states:

```text
"The validated V3 price surface now owns dynamic S/R rendering,
removing the legacy fallback false rejection
fallback_dynamic_resistance_not_rendered
without weakening a threshold."
```

Current provisional-layer evidence:

```text
US replay: 13/13 PASS
KR replay: 7/7 PASS
test sink full messages: 20/20 exact PASS
focused tests: 150 passed
full pytest: 1865 passed, 1 warning
P0 / material P1: 0 / 0
rollout: DEPLOYED_AWAITING_NATURAL_PROOF
```

Important current controls include:

```text
MU:
current regular close $935.39
near resistance ~$938.01~942.72
provisional monthly Bollinger resistance ~$1,024.78~1,029.92

000660:
current regular close 1,653,000 KRW
near support ~1.592m~1.606m with daily Bollinger confluence
provisional monthly Bollinger resistance ~2.270m~2.282m

SNDK:
ELIGIBLE_SR_ONLY on the current official capture
near support ~$1,441.91~1,449.15
near resistance ~$1,497.48~1,504.99 with weekly Bollinger confluence
```

Do not hard-code these values into production behavior.
They are regression evidence only.

---

# 2. Report metadata discrepancy that must be reconciled

The readiness JSON / operating-promotion report inside the bundle still names:

```text
final_main / operating =
d3a58c953c2dd6d100031421770be3a54d0328b5
```

while the completion summary names:

```text
final main / operating =
026df711fa151cc7816b2a57d9ed7d224c1b33cf
```

Do not guess which is current.

At task start:

```text
git fetch origin
resolve actual origin/main
resolve actual operating checkout
verify ancestry
record deployment/runtime identity
```

Then classify:

```text
REPORT_METADATA_STALE_ONLY
or
OPERATING_LINEAGE_CONFLICT
```

Hard:

```text
FINAL_OPERATING_SHA_RECONCILED = PASS
```

If this is only stale report metadata:
repair/regenerate the reports.

If runtime lineage is genuinely inconsistent:
STOP before any promotion.

---

# 3. Incident to freeze permanently

Known failed KR close packet:

`2026-08-28-kr-run-44-4606feed1396`

Observed incident behavior:

```text
000660

V3 renderer selected:
- 가까운 지지
- 일봉 볼린저 중첩

V3 policy:
- user-facing dynamic Bollinger references are materiality/display-budget selected
- monthly dynamic resistance was intentionally not rendered

legacy validator:
active_resistance = true
→ required a standalone dynamic resistance phrase

failure:
fallback_dynamic_resistance_not_rendered

propagation:
current_price_context_service.py
→ validation failure
→ notification_service.py abort
→ KR close exits 1
```

Known failed production attempts:

```text
16:05 KST
16:20 KST auto retry
```

16:50 was cancelled.

---

# 4. Critical strategy — VERIFY BEFORE REPAIR

Because the just-completed provisional-Bollinger rollout claims the V3 price surface already removed the false rejection:

DO NOT immediately modify runtime code.

First run the exact frozen run-44 regression against the ACTUAL latest operating code.

Branching rule:

```text
IF run-44 now PASS:
    classify = ALREADY_FIXED_BY_LATEST_ROLLOUT
    do not rewrite validator runtime logic
    add/fix permanent regression tests + ownership documentation only

IF run-44 still FAILS with the same false rejection:
    classify = RUNTIME_HOTFIX_REQUIRED
    apply the smallest validator-ownership repair
```

Hard:

```text
UNNECESSARY_RUNTIME_REWRITE = 0
```

---

# 5. Correct V3 ownership contract

When V3 Price Structure rendering is enabled:

```text
candidate generation
→ safety
→ relevance/materiality
→ overlap/dedup
→ display budget
→ V3 selected render plan
→ renderer
→ validator
```

The final V3 selected render plan is the validator's source of truth.

Candidate existence alone is NOT a render obligation.

---

# 6. Required render-plan states

Use repository-native equivalents of:

```text
SELECTED_REQUIRED
SELECTED_AS_CONFLUENCE

OMITTED_BY_MATERIALITY
OMITTED_BY_DISPLAY_BUDGET
OMITTED_BY_OVERLAP_DEDUP
OMITTED_BY_SAFETY

NOT_AVAILABLE
```

Validation:

```text
SELECTED_REQUIRED
→ renderer must contain the selected fact

SELECTED_AS_CONFLUENCE
→ renderer must contain the selected confluence ownership

all intentional OMITTED states
→ must NOT produce a missing-render failure

NOT_AVAILABLE
→ must NOT produce a missing-render failure
```

---

# 7. Strictness must remain

This is not a validator disablement.

Negative control:

```text
V3 explicitly selects a dynamic resistance
renderer drops that selected fact
→ validator MUST fail
```

Hard:

```text
SELECTED_V3_FACT_MISSING_NOT_DETECTED = 0
```

---

# 8. No duplicated selection logic

The validator should consume the same structured plan used by the renderer.

Do not independently reconstruct:

```text
active_support
active_resistance
all available dynamic faces
```

and convert those back into mandatory output.

Hard:

```text
VALIDATOR_RECOMPUTES_V3_SELECTION = 0
```

---

# 9. Legacy compatibility

If V3 is disabled:

preserve legacy behavior.

Hard:

```text
LEGACY_VALIDATOR_POLICY_DIFF_WHEN_V3_OFF = 0
```

Do not broaden this incident fix into a legacy renderer redesign.

---

# 10. Provisional Bollinger compatibility

Current deployed hierarchy must remain:

```text
historical / authoritative structure
> completed-bar dynamic Bollinger
> provisional in-progress Bollinger
```

Validator requirements:

```text
selected completed Bollinger
→ require selected text/confluence

selected provisional Bollinger
→ require selected provisional text/confluence

omitted completed/provisional candidate
→ no missing-render failure
```

Hard:

```text
PROVISIONAL_CANDIDATE_EXISTENCE_AS_RENDER_REQUIREMENT = 0
```

---

# 11. Major S/R Reality Gate compatibility

Preserve:

```text
BOLLINGER_ONLY_MAJOR_SR_VISIBLE = 0
MAJOR_SR_WITHOUT_PRICE_ANCHOR = 0
GOOGL_424_AS_MAJOR_STRUCTURAL = 0
```

No validator change may resurrect dynamic-derived ranges as historical structural S/R.

---

# 12. Current quote / structure-close clarity compatibility

Preserve the new price ownership contract:

```text
현재가
vs
가격 구조 기준 종가(정규장)
```

If equal:
one concise regular-close line is allowed.

If different:
both labels must be explicit.

Hard:

```text
AMBIGUOUS_CURRENT_VS_STRUCTURE_PRICE_LABEL = 0
```

---

# 13. Phase A — exact run-44 frozen replay

Use:

`2026-08-28-kr-run-44-4606feed1396`

Read-only.

Do not mutate:

```text
task state
delivery state
notification state
assessment state
DB
```

Do not send to production.

Replay the full KR close message-generation path through:

```text
packet load
market message assembly
stock message assembly
Price Structure render plan
renderer
validator
notification pre-delivery validation
```

Stop before production delivery intent.

---

# 14. Run-44 000660 expected contract

Report the exact structured plan:

```text
selected fact refs
selected confluence refs
omitted candidate refs
omission reason per ref
renderer text
validator required refs
validator result
```

Historical incident expectation:

```text
selected:
- near support
- daily Bollinger confluence

omitted:
- monthly dynamic resistance
  due V3 materiality/display-budget ownership
```

Do not assume that current replay selection must be byte-identical if code/evidence semantics legitimately evolved.

The invariant is:

```text
intentionally omitted V3 candidate
must not become a validator-required output
```

Hard:

```text
RUN44_000660_FROZEN_REPLAY = PASS
RUN44_FALLBACK_DYNAMIC_RESISTANCE_NOT_RENDERED = 0
```

---

# 15. Phase B — permanent regression tests

Regardless of whether a runtime fix is needed:

add permanent tests for this incident class.

Required tests:

### Test 1 — historical false positive

```text
multiple active dynamic candidates
V3 chooses one/confluence
another is OMITTED_BY_DISPLAY_BUDGET or MATERIALITY
→ PASS
```

### Test 2 — selected fact really missing

```text
V3 selects dynamic resistance
renderer omits it
→ FAIL_AS_EXPECTED
```

### Test 3 — overlap/confluence

```text
near S/R overlaps Bollinger
V3 selects confluence annotation
standalone dynamic face omitted
→ PASS
```

### Test 4 — provisional layer

```text
valid provisional candidate exists but not selected
→ no validator failure

selected provisional candidate missing
→ FAIL
```

### Test 5 — V3 OFF

```text
legacy route unchanged
```

---

# 16. Phase C — KR7 cross-sectional replay

Replay:

```text
000660
003690
005490
005930
010120
012450
086280
```

Latest completed safe KR session.

Verify for each:

```text
eligibility
current quote / structure basis
near S/R
major structural S/R
completed Bollinger
provisional Bollinger
selected/omitted refs
validator obligations
final renderer result
```

Hard:

```text
KR7_V3_VALIDATOR_REPLAY = PASS
```

---

# 17. Phase D — US current monitored replay

Use the ACTUAL current monitored US/foreign universe.

Previous control list contained 13:

```text
CORZ
CRCL
GOOGL
HUT
IBM
MU
RXRX
SKHY
SNDK
TSLA
TSM
WRD
WULF
```

Do not assume the list is unchanged.

Verify the same V3 ownership contract.

Hard:

```text
US_CURRENT_MONITORED_V3_VALIDATOR_REPLAY = PASS
```

---

# 18. SNDK / WULF regression

The latest completed bundle states:

```text
SNDK = ELIGIBLE_SR_ONLY
WULF = ELIGIBLE_SR_ONLY
```

on the current official capture, with zero provisional bypass.

Preserve evidence-derived eligibility.

Do not introduce ticker exceptions.

Hard:

```text
SNDK_PROVISIONAL_LAYER_BYPASS = 0
WULF_PROVISIONAL_LAYER_BYPASS = 0
```

---

# 19. MU regression

Ensure current code preserves the intended semantics:

```text
near S/R
completed Bollinger/confluence
one provisional expansion reference when selected/material
```

Historical regression evidence:

```text
provisional monthly resistance:
~$1,024.78~$1,029.92
```

No hard coding.

Validator must require it only if the current V3 plan selects it.

---

# 20. 000660 regression

Preserve:

```text
near S/R
completed Bollinger confluence
provisional monthly expansion when currently selected/material
```

Historical completed-bundle evidence included:

```text
near support ~1.592m~1.606m with daily Bollinger confluence
provisional monthly resistance ~2.270m~2.282m
```

No hard coding.

The critical invariant is render-plan ownership.

---

# 21. Phase E — full test-sink convergence

After frozen replay + cross-market replay PASS:

use the existing dedicated NON-PRODUCTION test sink.

Generate production-equivalent user-visible messages from the latest safe data.

Required test products:

```text
KR market message: 1
KR monitored/control stock messages: actual KR count
US market message: 1
US monitored stock messages: actual US count
```

With the previous 7 KR / 13 US universe this would be:

```text
1 + 7 + 1 + 13 = 22 messages
```

but use actual current counts.

No production recipient.

---

# 22. Test-sink delivery requirements

For every test message:

```text
rendered payload
outbound payload
received payload
```

must match.

Hard:

```text
TEST_EXACT_PAYLOAD_MATCH = PASS
TEST_DUPLICATE = 0
TEST_ORPHAN = 0
TEST_PRODUCTION_RECIPIENT_SEND = 0
PRODUCTION_DELIVERY_INTENT_CREATED = 0
```

---

# 23. KR close full-batch test

The KR test batch must prove that the old failure no longer aborts the batch.

Verify:

```text
market message rendered
000660 rendered
remaining KR stocks rendered
validator PASS for all
test delivery completes
```

Hard:

```text
KR_CLOSE_TEST_BATCH_COMPLETES = PASS
KR_CLOSE_TEST_BATCH_MESSAGE_COUNT = expected count
```

---

# 24. User-facing Price Structure review

Human-review exact received stock messages.

Check:

```text
current price ownership readable
near support/resistance
major structural semantic correctness
completed Bollinger
provisional Bollinger
no duplicate dynamic clutter
no target/stop
no missing Price Structure due false validator rejection
```

Hard:

```text
CROSS_MARKET_MESSAGE_QUALITY = PASS
```

---

# 25. US market-message regression

No functional US market-message redesign in this task.

Verify only:

```text
major index numeric block
market internals
night-futures canonical gate
macro temporal safety
```

Hard:

```text
US_MARKET_MESSAGE_REGRESSION = PASS
```

Do not modify unless a material regression is directly observed.

---

# 26. KR market-message regression

Verify:

```text
KR index / breadth / flow
size/style
sector TOP3
```

No Price Structure content leakage into the market digest.

Hard:

```text
KR_MARKET_MESSAGE_REGRESSION = PASS
```

---

# 27. Runtime code-change decision

After Phase A:

## Case 1 — latest operating already fixes run-44

Set:

```text
RUNTIME_HOTFIX_REQUIRED = NO
```

Allowed code changes:

```text
permanent regression tests
structured validator-plan assertions
docs/reporting metadata
```

Do NOT rewrite working runtime behavior.

## Case 2 — latest operating still fails

Set:

```text
RUNTIME_HOTFIX_REQUIRED = YES
```

Apply only the smallest ownership repair:

```text
V3 selected plan
→ validator source of truth
```

Do not suppress real validator errors.

---

# 28. Notification service boundary

Keep:

```text
real validation failure
→ notification pipeline abort
```

Do NOT fix this incident by swallowing exceptions in `notification_service.py`.

Hard:

```text
NOTIFICATION_VALIDATION_FAILURE_SUPPRESSED = 0
```

---

# 29. Today's production scheduler policy

The user cancelled today's 16:50 KR production run.

Do not recreate it.

Do not manually trigger KR production close proof today.

Inspect scheduler state read-only.

Preserve future normal schedules unless a separate operational defect is found.

Hard:

```text
TODAY_1650_KR_RERUN_CREATED = 0
MANUAL_KR_CLOSE_PRODUCTION_RERUN = 0
```

---

# 30. Operating promotion

If runtime logic changes:

```text
full focused/replay/test gates PASS
→ normal operating promotion
```

If only tests/docs/report metadata change and runtime behavior is already correct:

do not perform a gratuitous runtime restart solely for a no-op.

Record:

```text
OPERATING_PROMOTION =
PASS
or
NO_RUNTIME_CHANGE_REQUIRED
```

In both cases resolve final main and actual operating identity.

---

# 31. Post-change smoke

Required:

```text
API health
OHLCV health
run-44 frozen replay
KR7 replay
US current universe replay
Major S/R Reality Gate
completed Bollinger layer
provisional Bollinger layer
price-label clarity
```

---

# 32. Full regression

Required:

```text
run-44 incident tests
V3 validator ownership tests
Price Structure renderer integration tests
Major S/R Reality Gate tests
completed dynamic Bollinger tests
provisional Bollinger tests
current-vs-structure-price tests
AI/fallback parity
KR7
US current monitored universe
test-sink exact payload

full pytest
Ruff
git diff --check
Knowledge parity
Public Action/schema parity
operationId uniqueness
CI
API health
OHLCV health
```

---

# 33. AI / fallback parity

Hard:

```text
AI_FALLBACK_V3_VALIDATION_OWNERSHIP_PARITY = PASS
AI_FALLBACK_PROVISIONAL_BOLLINGER_PARITY = PASS
AI_FALLBACK_PRICE_LABEL_PARITY = PASS
```

The validator obligations must be semantically identical even if explanatory prose differs.

---

# 34. Required reports

Create:

1. `docs/reports/20260828-final-operating-sha-reconciliation.md`
2. `docs/reports/20260828-run44-v3-validator-convergence-root-cause.md`
3. `docs/reports/20260828-run44-000660-exact-frozen-replay.md`
4. `docs/reports/20260828-v3-render-plan-validator-contract.md`
5. `docs/reports/20260828-v3-validator-regression-controls.md`
6. `docs/reports/20260828-kr7-v3-validator-convergence-replay.md`
7. `docs/reports/20260828-us-v3-validator-convergence-replay.md`
8. `docs/reports/20260828-cross-market-full-message-test-delivery.md`
9. `docs/reports/20260828-cross-market-exact-test-messages.md`
10. `docs/reports/20260828-cross-market-message-quality.md`
11. `docs/reports/20260828-market-message-regression.md`
12. `docs/reports/20260828-final-operating-readiness.md`
13. `docs/reports/20260828-natural-proof-status.md`
14. `docs/reports/20260828-final-convergence-artifact-index.md`

Machine-readable:

```text
docs/reports/20260828-final-operating-readiness.json
docs/reports/20260828-run44-v3-validator-convergence.json
```

---

# 35. Required architecture update

Create/update:

```text
docs/architecture/PRICE_STRUCTURE_V3_VALIDATOR_OWNERSHIP.md
docs/architecture/PRICE_STRUCTURE_V3_RENDERER_INTEGRATION.md
```

Canonical statement:

```text
candidate availability
≠ render obligation

V3 selected render plan
= validator source of truth
```

---

# 36. Required gates

Set exactly:

```text
FINAL_OPERATING_SHA_RECONCILED =
PASS / FAIL

OPERATING_BEFORE =
...

LATEST_MAIN_BEFORE =
...

REPORT_METADATA_STATUS =
CURRENT /
STALE_REPORT_METADATA_ONLY /
OPERATING_LINEAGE_CONFLICT

RUN44_PACKET =
2026-08-28-kr-run-44-4606feed1396

RUN44_000660_FROZEN_REPLAY =
PASS / FAIL

RUN44_FALLBACK_DYNAMIC_RESISTANCE_NOT_RENDERED =
0 / NONZERO

ROOT_CAUSE_RENDERER_VALIDATOR_OWNERSHIP_MISMATCH =
PASS / FAIL

LATEST_RUNTIME_ALREADY_FIXED =
YES / NO

RUNTIME_HOTFIX_REQUIRED =
YES / NO

UNNECESSARY_RUNTIME_REWRITE =
0 / NONZERO

VALIDATOR_RECOMPUTES_V3_SELECTION =
0 / NONZERO

V3_OMITTED_CANDIDATE_REQUIRED_BY_VALIDATOR =
0 / NONZERO

SELECTED_V3_FACT_MISSING_NOT_DETECTED =
0 / NONZERO

V3_SELECTED_FACT_MISSING_NEGATIVE_CONTROL =
FAIL_AS_EXPECTED / UNEXPECTED_PASS

V3_DISPLAY_BUDGET_OMISSION =
PASS / FAIL

V3_MATERIALITY_OMISSION =
PASS / FAIL

V3_OVERLAP_CONFLUENCE_OMISSION =
PASS / FAIL

PROVISIONAL_CANDIDATE_EXISTENCE_AS_RENDER_REQUIREMENT =
0 / NONZERO

LEGACY_VALIDATOR_POLICY_DIFF_WHEN_V3_OFF =
0 / NONZERO

NOTIFICATION_VALIDATION_FAILURE_SUPPRESSED =
0 / NONZERO

KR7_V3_VALIDATOR_REPLAY =
PASS / FAIL

US_CURRENT_MONITORED_V3_VALIDATOR_REPLAY =
PASS / FAIL

SNDK_PROVISIONAL_LAYER_BYPASS =
0 / NONZERO

WULF_PROVISIONAL_LAYER_BYPASS =
0 / NONZERO

BOLLINGER_ONLY_MAJOR_SR_VISIBLE =
0 / NONZERO

MAJOR_SR_WITHOUT_PRICE_ANCHOR =
0 / NONZERO

AMBIGUOUS_CURRENT_VS_STRUCTURE_PRICE_LABEL =
0 / NONZERO

AI_FALLBACK_V3_VALIDATION_OWNERSHIP_PARITY =
PASS / FAIL

AI_FALLBACK_PROVISIONAL_BOLLINGER_PARITY =
PASS / FAIL

AI_FALLBACK_PRICE_LABEL_PARITY =
PASS / FAIL

TEST_KR_MARKET_MESSAGE_COUNT =
...

TEST_KR_STOCK_MESSAGE_COUNT =
...

TEST_US_MARKET_MESSAGE_COUNT =
...

TEST_US_STOCK_MESSAGE_COUNT =
...

TEST_TOTAL_MESSAGE_COUNT =
...

TEST_EXACT_PAYLOAD_MATCH =
PASS / FAIL

TEST_DUPLICATE =
0 / NONZERO

TEST_ORPHAN =
0 / NONZERO

TEST_PRODUCTION_RECIPIENT_SEND =
0 / NONZERO

PRODUCTION_DELIVERY_INTENT_CREATED =
0 / NONZERO

KR_CLOSE_TEST_BATCH_COMPLETES =
PASS / FAIL

CROSS_MARKET_MESSAGE_QUALITY =
PASS / FAIL

KR_MARKET_MESSAGE_REGRESSION =
PASS / FAIL

US_MARKET_MESSAGE_REGRESSION =
PASS / FAIL

TODAY_1650_KR_RERUN_CREATED =
0 / NONZERO

MANUAL_KR_CLOSE_PRODUCTION_RERUN =
0 / NONZERO

OPERATING_PROMOTION =
PASS /
NO_RUNTIME_CHANGE_REQUIRED /
FAIL

FINAL_MAIN =
...

OPERATING =
...

OPEN_P0 =
...

OPEN_MATERIAL_P1 =
...

FINAL_V3_VALIDATOR_CONVERGENCE =
DEPLOYED_AWAITING_NATURAL_PROOF /
READY_NO_RUNTIME_CHANGE /
LIVE_PASS /
FAIL

NATURAL_KR_CLOSE_V3_VALIDATOR =
PENDING / PASS / FAIL

NATURAL_US_PRICE_STRUCTURE =
PENDING / PASS / FAIL

NATURAL_US_MARKET =
PENDING / PASS / FAIL
```

---

# 37. PASS rule

Require:

```text
actual operating SHA reconciled
run-44 exact replay PASS
fallback_dynamic_resistance_not_rendered = 0
selected V3 missing fact still fails
intentional omission passes
validator does not recompute selection
legacy V3-off unchanged
KR7 PASS
US current universe PASS
full test-sink messages PASS
market-message regressions PASS
Major S/R reality gate preserved
provisional layer preserved
price label clarity preserved
P0 = 0
material P1 = 0
```

---

# 38. Natural observation timing

Do not create background/manual proof jobs.

Current date is Friday 2026-08-28 KST.

Expected natural observation windows, subject to normal exchange/scheduler calendars:

```text
US morning / US stock messages:
next natural cycle after the Friday 2026-08-28 US session
→ likely Saturday 2026-08-29 KST morning

KR close:
Saturday is not a normal KRX trading day
→ next normal KR close proof is expected Monday 2026-08-31 KST
```

Do not fabricate natural proof before those jobs actually run.

---

# 39. Completion response

Return:

```text
INSTRUCTION_COMMIT = ...
BASE_SHA = ...

OPERATING_BEFORE = ...
LATEST_MAIN_BEFORE = ...
FINAL_OPERATING_SHA_RECONCILED = ...
REPORT_METADATA_STATUS = ...

BRANCH = ...
IMPLEMENTATION_SHA = ...
REPORT_COMMIT = ...
FINAL_MAIN = ...
OPERATING = ...

RUN44_PACKET =
2026-08-28-kr-run-44-4606feed1396

LATEST_RUNTIME_ALREADY_FIXED = ...
RUNTIME_HOTFIX_REQUIRED = ...

RUN44_000660_SELECTED_FACTS = ...
RUN44_000660_SELECTED_CONFLUENCE = ...
RUN44_000660_OMITTED_FACTS = ...
RUN44_000660_OMISSION_REASONS = ...

RUN44_000660_FROZEN_REPLAY = ...
RUN44_FALLBACK_DYNAMIC_RESISTANCE_NOT_RENDERED = 0

VALIDATOR_RECOMPUTES_V3_SELECTION = 0
V3_OMITTED_CANDIDATE_REQUIRED_BY_VALIDATOR = 0
SELECTED_V3_FACT_MISSING_NOT_DETECTED = 0
V3_SELECTED_FACT_MISSING_NEGATIVE_CONTROL = FAIL_AS_EXPECTED

V3_DISPLAY_BUDGET_OMISSION = PASS
V3_MATERIALITY_OMISSION = PASS
V3_OVERLAP_CONFLUENCE_OMISSION = PASS

LEGACY_VALIDATOR_POLICY_DIFF_WHEN_V3_OFF = 0
NOTIFICATION_VALIDATION_FAILURE_SUPPRESSED = 0

KR7_V3_VALIDATOR_REPLAY = ...
US_CURRENT_MONITORED_V3_VALIDATOR_REPLAY = ...

BOLLINGER_ONLY_MAJOR_SR_VISIBLE = 0
MAJOR_SR_WITHOUT_PRICE_ANCHOR = 0
SNDK_PROVISIONAL_LAYER_BYPASS = 0
WULF_PROVISIONAL_LAYER_BYPASS = 0
AMBIGUOUS_CURRENT_VS_STRUCTURE_PRICE_LABEL = 0

AI_FALLBACK_V3_VALIDATION_OWNERSHIP_PARITY = ...
AI_FALLBACK_PROVISIONAL_BOLLINGER_PARITY = ...
AI_FALLBACK_PRICE_LABEL_PARITY = ...

TEST_KR_MARKET_MESSAGE_COUNT = ...
TEST_KR_STOCK_MESSAGE_COUNT = ...
TEST_US_MARKET_MESSAGE_COUNT = ...
TEST_US_STOCK_MESSAGE_COUNT = ...
TEST_TOTAL_MESSAGE_COUNT = ...

TEST_EXACT_PAYLOAD_MATCH = ...
TEST_DUPLICATE = 0
TEST_ORPHAN = 0
TEST_PRODUCTION_RECIPIENT_SEND = 0
PRODUCTION_DELIVERY_INTENT_CREATED = 0

KR_CLOSE_TEST_BATCH_COMPLETES = ...
CROSS_MARKET_MESSAGE_QUALITY = ...
KR_MARKET_MESSAGE_REGRESSION = ...
US_MARKET_MESSAGE_REGRESSION = ...

TODAY_1650_KR_RERUN_CREATED = 0
MANUAL_KR_CLOSE_PRODUCTION_RERUN = 0

OPERATING_PROMOTION = ...

FOCUSED_TESTS = ...
FULL_PYTEST = ...
RUFF = ...
DIFF_CHECK = ...
KNOWLEDGE_PARITY = ...
PUBLIC_ACTION = ...
OPERATION_ID = ...
CI = ...
API_HEALTH = ...
OHLCV_HEALTH = ...

OPEN_P0 = ...
OPEN_MATERIAL_P1 = ...

FINAL_V3_VALIDATOR_CONVERGENCE =
DEPLOYED_AWAITING_NATURAL_PROOF /
READY_NO_RUNTIME_CHANGE /
LIVE_PASS /
FAIL

NATURAL_KR_CLOSE_V3_VALIDATOR =
PENDING /
PASS /
FAIL

NATURAL_US_PRICE_STRUCTURE =
PENDING /
PASS /
FAIL

NATURAL_US_MARKET =
PENDING /
PASS /
FAIL

NEXT_ACTION =
WAIT_FOR_NATURAL_US_MESSAGES /
WAIT_FOR_NEXT_NATURAL_KR_CLOSE /
BOUNDED_REPAIR /
NO_ACTION

ZIP = ...
ZIP_SHA256 = ...
```

---

# 40. Mandatory completion ZIP

Create:

`20260828-run44-v3-validator-convergence-cross-market-final-readiness-bundle.zip`

Include:

```text
exact instruction
operating-SHA reconciliation
run-44 root cause
run-44 exact frozen replay
structured render-plan evidence
permanent regression controls
KR7 replay
US current-universe replay
cross-market test delivery
exact test messages
market-message regression
message-quality report
operating promotion / no-op decision
natural-proof status
readiness JSON
test/CI summary
artifact index
```

Exclude:

```text
secrets
raw Telegram IDs
tokens
auth headers
account identifiers
hidden chain-of-thought
```

Compute SHA-256.

---

# 41. Final principle

The latest provisional-Bollinger rollout may already contain the behavioral fix.

Prove that first.

If it is already fixed:
do not rewrite working runtime logic merely because an older incident existed.

But permanently freeze run-44 as a regression test so that future changes to:

```text
materiality
display budget
completed Bollinger
provisional Bollinger
confluence
```

can never again cause a legacy validator to abort the entire KR close batch for intentionally omitted V3 output.
