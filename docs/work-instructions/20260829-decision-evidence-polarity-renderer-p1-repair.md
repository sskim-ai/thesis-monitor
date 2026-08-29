# thesis-monitor — Decision Evidence Polarity Renderer P1 Repair
## Fix BUY-side / SELL-side evidence ownership before first natural canary cycle
## Freeze current canary classifications
## Repair labels/ownership, not decision outcomes
## Re-test exact 4 canary subjects + historical BUY fixture, then re-arm canary

---

# 0. Metadata

- Repository: `sskim-ai/thesis-monitor`
- Date: `2026-08-29 KST`
- Workstream: `DECISION_EVIDENCE_POLARITY_RENDERER_P1_REPAIR`
- Task class: `BOUNDED_SEMANTIC_RENDERER_VALIDATOR_P1_REPAIR`
- Production canary entering state: `ENABLED_AWAITING_NATURAL_PROOF`
- Natural canary cycles observed so far:
  - KR `0/2`
  - US `0/2`
- Automated trade execution: `0`
- Order sizing: `0`
- Thesis/monitoring mutation from decision output: `0`
- Production recipient send during repair/test: `0`
- Scheduler mutation: `0`

Source bundle:

`20260829-cross-market-decision-engine-bounded-canary-bundle.zip`

Source bundle SHA-256:

`3ad8f42025cfa57c4c9c20532b57d0d058d3494c025434aa08a950df3f5ed630`

Latest source-supported operating state:

```text
FINAL_MAIN / OPERATING =
483888edcd4afb64d108c667b47d7e9f6b5ba423

CANARY_KR =
003690
000660

CANARY_US =
GOOGL
RXRX

CURRENT ACCEPTED DECISIONS =
003690 HOLD
000660 HOLD
GOOGL HOLD
RXRX SELL

BUY fixture =
003690 / GOOGL historical canonical BUY packets
test-only PASS

KR natural cycles =
0

US natural cycles =
0
```

Before implementation:

```text
git fetch origin
verify clean worktrees
resolve actual latest safe origin/main
resolve actual operating checkout
use 483888... or safe linear descendant
record exact lineage
```

---

# 1. P1 defect

The current decision candidate has concepts like:

```text
supporting_evidence
opposing_evidence
```

These are relative to the **final decision**.

They are NOT guaranteed to mean:

```text
supporting_evidence = BUY side
opposing_evidence = SELL side
```

The renderer currently maps them too mechanically into:

```text
✅ BUY 쪽 근거
⚠️ SELL 쪽 근거
```

This produces semantically inverted or neutral content under the wrong polarity label.

---

# 2. Exact negative control — GOOGL

Source test message contained a SELL-side section whose content was actually bullish, conceptually:

```text
⚠️ SELL 쪽 근거:
favorable trailing valuation
attractive chart risk-reward
intact major structure
...
```

Those statements are not SELL-side evidence.

Hard requirement:

```text
GOOGL_BULLISH_EVIDENCE_UNDER_SELL_LABEL = 0
```

---

# 3. Exact negative control — RXRX

Source test message contained a SELL-side section with a neutral/data-quality statement, conceptually:

```text
⚠️ SELL 쪽 근거:
financial statement / security identity /
book-valuation basis are verified usable
```

That is not bearish evidence.

Hard requirement:

```text
RXRX_NEUTRAL_EVIDENCE_UNDER_SELL_LABEL = 0
```

---

# 4. Current decision freeze

This repair must NOT change the currently accepted 4-subject classifications merely because the renderer polarity is being fixed.

Freeze current accepted canary outcomes for regression:

```text
003690 = HOLD
000660 = HOLD
GOOGL = HOLD
RXRX = SELL
```

If the same canonical evidence packet is reused:

these decisions must remain unchanged.

Hard:

```text
POLARITY_REPAIR_CHANGED_DECISION = 0
```

If fresh evidence genuinely changes a decision later:

that belongs to the natural-cycle decision-delta contract, not this repair.

---

# 5. Immediate canary safety before repair

Because natural cycles are still `0/2` for both markets:

before changing code, temporarily suppress only the decision block for canary subjects if the next natural cycle could occur before repair completion.

Preferred safe state:

```text
DECISION_ENGINE_STATE = TEST_SINK_READY
PRODUCTION_CANARY_ENABLED = false
```

while preserving normal non-decision stock messages.

If the repository deployment workflow can guarantee repair completion before any next natural message without runtime exposure:

document that and keep the canary armed.

Do not allow a known polarity-defective decision block to reach production.

Set:

```text
CANARY_SAFETY_DURING_REPAIR =
TEMPORARILY_SUPPRESSED /
NO_EXPOSURE_WINDOW_CONFIRMED
```

---

# 6. Correct semantic ownership

Separate two concepts:

## 6.1 Decision-relative evidence

```text
decision_supporting_evidence
decision_opposing_evidence
```

Meaning:

```text
supports or challenges the final BUY/HOLD/SELL classification
```

Useful for internal reasoning / adjudication.

## 6.2 Directional polarity evidence

```text
buy_case_evidence
sell_case_evidence
neutral_context_evidence
```

or equivalent canonical enum:

```text
BULLISH
BEARISH
NEUTRAL
```

Meaning:

```text
BUY-side economic evidence
SELL-side economic evidence
directionally neutral/contextual evidence
```

The user-facing `BUY 쪽 / SELL 쪽` renderer must use directional polarity ownership only.

---

# 7. Canonical polarity enum

Prefer a backend structured field:

```text
evidence_polarity =
BULLISH
BEARISH
NEUTRAL
```

Optional additional semantic roles:

```text
DATA_QUALITY
TIMING_ONLY
VALUATION
FUNDAMENTAL
MARKET
TECHNICAL
```

Do not infer polarity from free-form sentence sentiment at render time.

Hard:

```text
RENDERER_FREEFORM_SENTIMENT_POLARITY_INFERENCE = 0
```

---

# 8. Polarity fact ownership

Every evidence item selected for a BUY/SELL section must have:

```text
evidence_ref
polarity
reason_role
source/basis
as_of
```

If numeric:

also require existing numeric provenance.

Hard:

```text
UNOWNED_POLARITY_EVIDENCE_VISIBLE = 0
```

---

# 9. Polarity is independent of final decision

Examples:

## HOLD

May contain:

```text
BULLISH:
strong business
cheap valuation
constructive momentum

BEARISH:
high expectations
margin risk
dilution
```

## BUY

Still must contain bearish/opposing evidence if material.

## SELL

Still must contain bullish/upside/optionality evidence if material.

Do not make:

```text
BUY decision → all evidence bullish
SELL decision → all evidence bearish
```

---

# 10. HOLD requirement

For HOLD:

```text
BUY 쪽 근거
→ strongest BULLISH evidence

SELL 쪽 근거
→ strongest BEARISH evidence
```

This naturally explains:

```text
why not SELL
why not BUY
```

Do not use decision-support/opposition order to choose the sections.

Hard:

```text
HOLD_BUY_SECTION_WITHOUT_BULLISH_EVIDENCE = 0
HOLD_SELL_SECTION_WITHOUT_BEARISH_EVIDENCE = 0
```

---

# 11. BUY requirement

For BUY:

```text
BUY 쪽 근거
→ strongest BULLISH evidence

SELL 쪽 근거
→ strongest BEARISH / risk evidence
```

The SELL section is opposing evidence to BUY in this case,
but still must be directionally bearish.

---

# 12. SELL requirement

For SELL:

```text
BUY 쪽 근거
→ strongest credible upside / optionality / bullish evidence

SELL 쪽 근거
→ strongest BEARISH evidence
```

This prevents one-sided liquidation language.

RXRX is the primary SELL control.

Hard:

```text
SELL_BUY_SECTION_WITHOUT_BULLISH_EVIDENCE = 0
SELL_SELL_SECTION_WITHOUT_BEARISH_EVIDENCE = 0
```

---

# 13. Neutral evidence handling

Examples:

```text
security identity verified
financial statement basis verified
numeric provenance complete
data source current
```

These are important but not inherently BUY or SELL evidence.

Do not place them under:

```text
✅ BUY 쪽 근거
⚠️ SELL 쪽 근거
```

unless a separate economic interpretation makes them directional and that interpretation is explicitly owned.

Neutral facts may appear under:

```text
데이터/판단 전제
```

only if user-facing material.

Otherwise omit from the decision summary.

Hard:

```text
NEUTRAL_FACT_FORCED_INTO_BUY_SELL_SECTION = 0
```

---

# 14. Data-quality evidence

Data-quality limitations can affect:

```text
confidence
unknowns
decision limitations
```

They are not automatically bearish.

Example:

```text
valuation basis unverified
```

should usually reduce confidence.

It becomes SELL-side only if the economic evidence itself is negative,
not merely because data is missing.

Hard:

```text
DATA_QUALITY_LIMIT_AUTOMATICALLY_BEARISH = 0
```

---

# 15. Timing evidence polarity

Timing evidence may be:

```text
BULLISH
BEARISH
NEUTRAL
```

but must remain tagged:

```text
TIMING_ONLY
```

when it should not own the long-horizon decision.

Example:

```text
weekly MACD weak
→ bearish timing evidence
→ not automatically long-horizon SELL evidence
```

Hard:

```text
TIMING_EVIDENCE_ESCALATED_TO_FUNDAMENTAL_POLARITY = 0
```

---

# 16. Validator ownership

Validator must consume the same structured polarity selection used by the renderer.

Required selected slots:

```text
selected_buy_case_refs
selected_sell_case_refs
selected_neutral_context_refs
```

Do not independently infer polarity from:

```text
supporting_evidence
opposing_evidence
sentence order
label text
```

Hard:

```text
VALIDATOR_RECOMPUTES_EVIDENCE_POLARITY = 0
```

---

# 17. Validator strictness

Negative controls:

```text
BULLISH evidence rendered under SELL label
→ FAIL

BEARISH evidence rendered under BUY label
→ FAIL

NEUTRAL evidence rendered as sole SELL evidence
→ FAIL

selected polarity evidence omitted
→ FAIL
```

Intentional evidence omission due message-density budget remains allowed when not selected.

Do not weaken validation.

---

# 18. Message-density budget

Do not solve polarity by printing every evidence item.

Target:

```text
BUY-side = 1–3 material items
SELL-side = 1–3 material items
```

Prefer the most decision-relevant evidence.

No duplicated statement across both sides.

Hard:

```text
SAME_EVIDENCE_IN_BUY_AND_SELL_SECTIONS = 0
```

---

# 19. GOOGL required post-repair control

Current accepted decision:

```text
GOOGL = HOLD
```

Required semantics:

```text
BUY side:
must contain genuinely bullish evidence
such as business quality / trailing valuation / credible earnings support
only where canonical evidence supports it

SELL side:
must contain genuinely bearish evidence
such as elevated expectations / AI CAPEX monetization risk /
forward valuation constraint
only where canonical evidence supports it
```

Do not hard-code prose.

Hard:

```text
GOOGL_POLARITY_VALIDATION = PASS
```

---

# 20. RXRX required post-repair control

Current accepted decision:

```text
RXRX = SELL
```

Required semantics:

```text
BUY side:
credible partner/clinical optionality or other genuine bullish evidence

SELL side:
unproven economic/clinical repeatability
losses/cash burn/dilution
or other genuine bearish evidence
```

Neutral data-quality statements cannot own SELL-side.

Hard:

```text
RXRX_POLARITY_VALIDATION = PASS
```

---

# 21. 003690 control

Current accepted:

```text
003690 = HOLD
```

Verify existing BUY/SELL sections remain semantically correct after shared repair.

Hard:

```text
DB_INSURANCE_POLARITY_VALIDATION = PASS
```

---

# 22. 000660 control

Current accepted:

```text
000660 = HOLD
```

Verify:

```text
HBM/AI-memory upside
```

stays on BUY side,

while:

```text
high expectations / valuation / normalization risk
```

stays on SELL side,

subject to actual canonical evidence.

Hard:

```text
SKHYNIX_POLARITY_VALIDATION = PASS
```

---

# 23. Historical BUY fixture regression

Re-run test-only historical canonical BUY fixtures:

```text
003690 prior BUY
GOOGL prior BUY
```

Verify:

```text
BUY side = bullish
SELL side = bearish
```

The fixture remains clearly historical/test-only.

Hard:

```text
BUY_FIXTURE_POLARITY_VALIDATION = PASS
BUY_FIXTURE_PRODUCTION_SEND = 0
```

---

# 24. Same-evidence decision continuity regression

Preserve the already-added continuity safety:

```text
same canonical evidence SHA
→ unexplained decision churn prohibited
```

This task does not redesign continuity.

Re-run controls:

```text
003690
000660
GOOGL
RXRX
```

Hard:

```text
POLARITY_REPAIR_DECISION_CONTINUITY = PASS
```

No polarity metadata change may accidentally become a reason to flip the decision.

---

# 25. Fresh-evidence behavior

When evidence SHA changes in a later natural cycle:

decision may change.

Require the existing delta explanation contract.

Do not lock classifications forever.

Hard:

```text
CONTINUITY_GATE_BLOCKS_REAL_EVIDENCE_CHANGE = 0
```

---

# 26. Track A — polarity contract implementation

Implement or formalize:

```text
BULLISH / BEARISH / NEUTRAL
```

at the structured evidence-item level.

Map existing canonical facts/interpretations to polarity through owned semantic selection.

Do not classify arbitrary source text via sentiment heuristics.

---

# 27. Track B — renderer/validator repair

Renderer:

```text
BUY label → selected BULLISH
SELL label → selected BEARISH
```

Validator:

enforces the exact structured polarity plan.

Preserve:

```text
decision
confidence
timing
hold reason
change conditions
Price Structure
valuation
```

unchanged.

---

# 28. Track C — 4-subject current test sink

Generate fresh current decision messages for:

```text
003690
000660
GOOGL
RXRX
```

Use current canonical evidence.

If evidence changed since the previous canary packet:

generate the legitimate new decision through the current engine,
then review the evidence delta.

Do not force the old decision if evidence genuinely changed.

---

# 29. Test-sink requirements

Use existing dedicated non-production sink.

Send:

```text
4 current canary subject messages
+ historical BUY fixture message(s)
```

No production recipients.

Hard:

```text
TEST_EXACT_PAYLOAD_MATCH = PASS
TEST_PRODUCTION_RECIPIENT_SEND = 0
PRODUCTION_DELIVERY_INTENT_CREATED = 0
TEST_DUPLICATE = 0
TEST_ORPHAN = 0
```

---

# 30. Semantic message-quality validator

Add explicit quality checks:

```text
BUY-section evidence polarity == BULLISH
SELL-section evidence polarity == BEARISH
neutral-only section invalid
same evidence not on both sides
```

Hard:

```text
BUY_SELL_POLARITY_MESSAGE_QUALITY = PASS
```

---

# 31. Canary re-arm

After all tests pass:

restore the exact bounded canary scope:

```text
KR:
003690
000660

US:
GOOGL
RXRX
```

Set:

```text
DECISION_ENGINE_STATE = CANARY
PRODUCTION_CANARY_ENABLED = true
```

Do not expand subjects.

---

# 32. Natural-cycle counters

Because no natural canary cycle has occurred yet:

keep counters at:

```text
KR = 0/2
US = 0/2
```

Do not count pre-repair test-sink sends.

Do not count BUY historical fixtures.

---

# 33. Natural proof after re-arm

On the next natural cycles verify:

```text
BUY-side polarity correct
SELL-side polarity correct
decision continuity/delta correct
confidence/timing unchanged unless evidence changes
Price Structure intact
exactly once
```

If polarity fails in production:

disable canary decision blocks and return to `TEST_SINK_READY`.

---

# 34. Non-canary isolation

Hard:

```text
NON_CANARY_DECISION_BLOCK_VISIBLE = 0
GLOBAL_DECISION_BLOCK_ENABLED = 0
```

No other monitored stocks receive decision blocks.

---

# 35. No decision recalibration in this repair

Do not reopen:

```text
BUY/HOLD/SELL taxonomy
SELL suppression calibration
HOLD-default calibration
timing taxonomy
confidence taxonomy
```

unless a direct polarity-related semantic conflict proves one is broken.

Current calibration bundle already passed P0/P1 = 0/0.

Hard:

```text
DECISION_CALIBRATION_POLICY_DIFF = 0
```

---

# 36. No Price Structure changes

Hard:

```text
PRICE_STRUCTURE_CODE_DIFF = 0
PRICE_STRUCTURE_NUMERIC_DIFF = 0
BOLLINGER_ONLY_MAJOR_SR_VISIBLE = 0
PROVISIONAL_BOLLINGER_AUTHORITY_LEAK = 0
```

---

# 37. No valuation changes

This is not a valuation repair.

Hard:

```text
VALUATION_NUMERIC_DIFF = 0
VALUATION_POLICY_DIFF = 0
```

---

# 38. No market-message changes

Hard:

```text
KR_MARKET_MESSAGE_DIFF = 0
US_MARKET_MESSAGE_DIFF = 0
```

---

# 39. Required reports

Create:

1. `docs/reports/20260829-decision-evidence-polarity-root-cause.md`
2. `docs/reports/20260829-decision-evidence-polarity-contract.md`
3. `docs/reports/20260829-googl-polarity-negative-control.md`
4. `docs/reports/20260829-rxrx-polarity-negative-control.md`
5. `docs/reports/20260829-003690-polarity-control.md`
6. `docs/reports/20260829-000660-polarity-control.md`
7. `docs/reports/20260829-buy-fixture-polarity-control.md`
8. `docs/reports/20260829-decision-continuity-regression.md`
9. `docs/reports/20260829-decision-polarity-renderer-validator.md`
10. `docs/reports/20260829-decision-polarity-test-sink.md`
11. `docs/reports/20260829-decision-polarity-message-quality.md`
12. `docs/reports/20260829-decision-canary-rearm.md`
13. `docs/reports/20260829-decision-polarity-readiness.md`
14. `docs/reports/20260829-decision-polarity-artifact-index.md`

Machine-readable:

```text
docs/reports/20260829-decision-polarity-readiness.json
```

---

# 40. Required gates

Set exactly:

```text
CANARY_SAFETY_DURING_REPAIR =
TEMPORARILY_SUPPRESSED /
NO_EXPOSURE_WINDOW_CONFIRMED

POLARITY_REPAIR_CHANGED_DECISION =
0 / NONZERO

RENDERER_FREEFORM_SENTIMENT_POLARITY_INFERENCE =
0 / NONZERO

UNOWNED_POLARITY_EVIDENCE_VISIBLE =
0 / NONZERO

NEUTRAL_FACT_FORCED_INTO_BUY_SELL_SECTION =
0 / NONZERO

DATA_QUALITY_LIMIT_AUTOMATICALLY_BEARISH =
0 / NONZERO

TIMING_EVIDENCE_ESCALATED_TO_FUNDAMENTAL_POLARITY =
0 / NONZERO

VALIDATOR_RECOMPUTES_EVIDENCE_POLARITY =
0 / NONZERO

SAME_EVIDENCE_IN_BUY_AND_SELL_SECTIONS =
0 / NONZERO

GOOGL_BULLISH_EVIDENCE_UNDER_SELL_LABEL =
0 / NONZERO

RXRX_NEUTRAL_EVIDENCE_UNDER_SELL_LABEL =
0 / NONZERO

GOOGL_POLARITY_VALIDATION =
PASS / FAIL

RXRX_POLARITY_VALIDATION =
PASS / FAIL

DB_INSURANCE_POLARITY_VALIDATION =
PASS / FAIL

SKHYNIX_POLARITY_VALIDATION =
PASS / FAIL

BUY_FIXTURE_POLARITY_VALIDATION =
PASS / NOT_AVAILABLE / FAIL

BUY_FIXTURE_PRODUCTION_SEND =
0 / NONZERO

POLARITY_REPAIR_DECISION_CONTINUITY =
PASS / FAIL

CONTINUITY_GATE_BLOCKS_REAL_EVIDENCE_CHANGE =
0 / NONZERO

BUY_SELL_POLARITY_MESSAGE_QUALITY =
PASS / FAIL

TEST_MESSAGE_COUNT =
...

TEST_EXACT_PAYLOAD_MATCH =
PASS / FAIL

TEST_PRODUCTION_RECIPIENT_SEND =
0 / NONZERO

PRODUCTION_DELIVERY_INTENT_CREATED =
0 / NONZERO

TEST_DUPLICATE =
0 / NONZERO

TEST_ORPHAN =
0 / NONZERO

DECISION_CALIBRATION_POLICY_DIFF =
0 / NONZERO

PRICE_STRUCTURE_CODE_DIFF =
0 / NONZERO

PRICE_STRUCTURE_NUMERIC_DIFF =
0 / NONZERO

VALUATION_NUMERIC_DIFF =
0 / NONZERO

VALUATION_POLICY_DIFF =
0 / NONZERO

KR_MARKET_MESSAGE_DIFF =
0 / NONZERO

US_MARKET_MESSAGE_DIFF =
0 / NONZERO

NON_CANARY_DECISION_BLOCK_VISIBLE =
0 / NONZERO

GLOBAL_DECISION_BLOCK_ENABLED =
0 / NONZERO

DECISION_ENGINE_STATE =
TEST_SINK_READY /
CANARY /
OTHER

PRODUCTION_CANARY_ENABLED =
true / false

KR_NATURAL_CANARY_CYCLES =
0 / 1 / 2 / MORE

US_NATURAL_CANARY_CYCLES =
0 / 1 / 2 / MORE

OPEN_P0 =
...

OPEN_MATERIAL_P1 =
...

DECISION_POLARITY_REPAIR =
REPAIRED_REARMED_AWAITING_NATURAL_PROOF /
FAIL
```

---

# 41. PASS rule

Require:

```text
GOOGL / RXRX defects fixed
003690 / 000660 controls PASS
BUY historical fixture polarity PASS
no decision change from polarity-only repair
continuity gate preserved
no free-form polarity inference
neutral evidence not mislabeled
validator strictness preserved
exact test-sink payload PASS
non-canary isolation PASS
Price Structure / valuation / market messages unchanged
P0 = 0
material P1 = 0
```

Then:

```text
DECISION_POLARITY_REPAIR =
REPAIRED_REARMED_AWAITING_NATURAL_PROOF
```

---

# 42. Completion response

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

CANARY_SAFETY_DURING_REPAIR = ...

CURRENT_DECISIONS =
003690 ...
000660 ...
GOOGL ...
RXRX ...

POLARITY_REPAIR_CHANGED_DECISION = 0

GOOGL_BEFORE_BUY_SIDE = ...
GOOGL_BEFORE_SELL_SIDE = ...
GOOGL_AFTER_BUY_SIDE = ...
GOOGL_AFTER_SELL_SIDE = ...

RXRX_BEFORE_BUY_SIDE = ...
RXRX_BEFORE_SELL_SIDE = ...
RXRX_AFTER_BUY_SIDE = ...
RXRX_AFTER_SELL_SIDE = ...

GOOGL_POLARITY_VALIDATION = ...
RXRX_POLARITY_VALIDATION = ...
DB_INSURANCE_POLARITY_VALIDATION = ...
SKHYNIX_POLARITY_VALIDATION = ...

BUY_FIXTURE_POLARITY_VALIDATION = ...
BUY_FIXTURE_PRODUCTION_SEND = 0

RENDERER_FREEFORM_SENTIMENT_POLARITY_INFERENCE = 0
UNOWNED_POLARITY_EVIDENCE_VISIBLE = 0
NEUTRAL_FACT_FORCED_INTO_BUY_SELL_SECTION = 0
VALIDATOR_RECOMPUTES_EVIDENCE_POLARITY = 0

POLARITY_REPAIR_DECISION_CONTINUITY = ...
CONTINUITY_GATE_BLOCKS_REAL_EVIDENCE_CHANGE = 0

BUY_SELL_POLARITY_MESSAGE_QUALITY = ...

TEST_MESSAGE_COUNT = ...
TEST_EXACT_PAYLOAD_MATCH = ...
TEST_PRODUCTION_RECIPIENT_SEND = 0
PRODUCTION_DELIVERY_INTENT_CREATED = 0
TEST_DUPLICATE = 0
TEST_ORPHAN = 0

DECISION_CALIBRATION_POLICY_DIFF = 0
PRICE_STRUCTURE_CODE_DIFF = 0
PRICE_STRUCTURE_NUMERIC_DIFF = 0
VALUATION_NUMERIC_DIFF = 0
VALUATION_POLICY_DIFF = 0
KR_MARKET_MESSAGE_DIFF = 0
US_MARKET_MESSAGE_DIFF = 0

NON_CANARY_DECISION_BLOCK_VISIBLE = 0
GLOBAL_DECISION_BLOCK_ENABLED = 0

DECISION_ENGINE_STATE = CANARY
PRODUCTION_CANARY_ENABLED = true

KR_NATURAL_CANARY_CYCLES = 0
US_NATURAL_CANARY_CYCLES = 0

OPEN_P0 = ...
OPEN_MATERIAL_P1 = ...

DECISION_POLARITY_REPAIR =
REPAIRED_REARMED_AWAITING_NATURAL_PROOF /
FAIL

NEXT_ACTION =
WAIT_FOR_NATURAL_CANARY_CYCLES /
BOUNDED_REPAIR

ZIP = ...
ZIP_SHA256 = ...
```

---

# 43. Mandatory completion ZIP

Create:

`20260829-decision-evidence-polarity-renderer-p1-repair-bundle.zip`

Include:

```text
exact instruction
all track instructions
root cause
polarity contract
GOOGL before/after
RXRX before/after
003690 / 000660 controls
BUY fixture control
continuity regression
renderer/validator evidence
test-sink exact messages
message-quality report
canary re-arm state
readiness JSON
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

# 44. Final principle

`supporting_evidence` and `opposing_evidence` answer:

```text
"What supports or challenges the final decision?"
```

They do NOT answer:

```text
"What is bullish?"
"What is bearish?"
```

The user-facing `BUY 쪽 근거 / SELL 쪽 근거` sections must be driven by explicit evidence polarity.

Fix that ownership before the first natural canary message is allowed to prove the feature.
