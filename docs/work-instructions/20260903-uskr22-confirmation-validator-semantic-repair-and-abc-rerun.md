# thesis-monitor — US14 + KR8 Confirmation Validator Semantic Repair + Fresh ALL22 / A-B-C Re-run
## Repair only the lexical false positive in confirmation business-condition ownership
## Preserve the current Structured Autonomy judgment contract
## Start a completely new 22-subject blind generation
## Run A/B/C only after the new first run passes 22/22

---

# 0. Metadata

- Repository: `sskim-ai/thesis-monitor`
- Date: `2026-09-03 KST`
- Required starting base:
  `93d72816b5015c028b4a72475f4229fb120d3d10` or a descendant containing the completed provenance/renderer repairs
- Prior source packets:
  - US: `2026-09-03-us-run-53-055ae8ea01f6`
  - KR: `2026-09-03-kr-run-54-f19bb379daa7`
- Prior experiment:
  - fresh blind generation created correctly
  - evidence alias repair: PASS
  - 086280 nonexistent ref: `0`
  - WRD/WULF substantive confirmation repetition: `0`
  - unsupported price numeric: `0`
  - KR accounting safety: PASS
  - ADR/security-basis safety: PASS
  - first-run validation: `20/22`
  - A/B/C: `NOT_RUN_FIRST_GATE_FAILED`
- Current blockers:
  - CRCL: `generic_confirmation_structure_model_owned`
  - MU: `generic_confirmation_structure_model_owned`
- Production decision mutation: `0`
- Production renderer change: `0`
- Production send: `0`
- Scheduler change: `0`
- DB change: `0`
- Main merge: `0`

This is a bounded validator repair.

Do NOT redesign the investment-judgment architecture.

---

# 1. Source-derived blocker facts

The current validator uses a broad lexical guard equivalent to:

```text
종가
돌파
안착
확인선
저항
지지
가격
close
breakout
resistance
support
```

inside `confirmation_business_condition`.

This caused ordinary business-language false positives.

Observed CRCL business condition:

```text
USDC 점유율과 비이자성 수익 확대가 정상화 이익을 지지함.
```

The word:

```text
지지
```

means:

```text
supports earnings / business economics
```

not:

```text
technical support level
```

Observed MU business condition included:

```text
HBM 출하와 고객 채택이 확대되고 가격과 제품구성 강세 및 현금창출이 유지되는 것
```

The word:

```text
가격
```

means:

```text
product pricing
```

not:

```text
stock-price confirmation structure
```

Therefore:

```text
CRCL/MU failure class
= lexical semantic-ownership false positive
```

not:
- judgment error
- price provenance error
- evidence provenance error
- renderer repetition regression

---

# 2. Repair objective

Replace:

```text
broad single-keyword rejection
```

with:

```text
semantic-field ownership validation
```

The validator must still prevent the model from owning stock-price confirmation logic in the business-condition field.

It must NOT reject normal business language merely because it contains words such as:

```text
지지
가격
support
pricing
```

---

# 3. Preserve the field's role

`confirmation_business_condition` means:

```text
the non-price business / earnings / industry / economic condition
that should accompany a price confirmation before a new-buyer reassessment.
```

It is NOT the owner of:

```text
stock price
support zone
resistance zone
confirmation price
close-above condition
breakout semantics
retest semantics
```

Those remain owned by structured price fields and the deterministic renderer.

---

# 4. Preferred schema refinement

Do not leave `confirmation_business_condition` as an ungrounded free-text string if a narrow, non-judgment schema refinement can make ownership explicit.

Preferred native-equivalent shape:

```json
{
  "confirmation_business_condition": {
    "summary": "...",
    "evidence_refs": ["E03", "E07"]
  }
}
```

or a repository-native `EvidenceClaim`.

This is an evidence-grounding/schema safety change.

It is NOT a change to:
- BUY/HOLD/SELL logic
- directional balance
- threshold
- sector interpretation
- new-buyer stance logic
- holder stance logic

Required:

```text
CONFIRMATION_BUSINESS_CONDITION_GROUNDED = PASS
```

If changing the type would create disproportionate migration risk,
an equivalent separate structured `confirmation_business_condition_refs`
field is allowed.

Do not leave the field impossible to provenance-audit.

---

# 5. Evidence ownership for the business condition

The business condition must cite evidence aliases that resolve to same-subject, same-market, same-generation canonical facts.

The selected evidence should normally be:

```text
business
earnings
customer
industry
capital allocation
competitive
regulatory
cash-flow/economic
```

evidence.

The field must not rely solely on technical/price-structure evidence.

Required:

```text
BUSINESS_CONDITION_PRICE_ONLY_EVIDENCE = 0
```

A mixed evidence set is allowed only when:
- at least one cited non-price fact genuinely supports the business condition,
- the summary itself does not take ownership of the structured price rule.

---

# 6. Stop using broad words as ownership proxies

Remove or narrow the current logic that rejects any occurrence of generic tokens such as:

```text
지지
가격
support
```

by themselves.

These must be allowed in normal business meanings.

Examples that MUST PASS:

```text
USDC 성장과 비이자성 수익 확대가 정상화 이익을 지지함.

HBM 출하 확대와 제품 가격 강세가 현금창출을 지지함.

가격 결정력이 마진 방어를 지원함.

customer demand supports utilization.

pricing power supports margins.

supplier support improves execution.
```

Hard:

```text
GENERIC_BUSINESS_WORD_FALSE_POSITIVE = 0
```

---

# 7. What must still be blocked

The business-condition field must still reject actual stock-price / technical ownership.

Examples that MUST FAIL:

```text
종가가 확인선을 돌파해야 한다.

저항선 위로 안착해야 한다.

주가가 지지 구간을 회복해야 한다.

$950 돌파 후 재지지가 필요하다.

close above resistance.

breakout above the confirmation level.

retest the support zone.

price must recover the registered confirmation level.
```

The rejection reason should be specific, e.g.:

```text
confirmation_business_condition_contains_price_structure_semantics
```

not a generic lexical error.

---

# 8. Semantic detector design

Use a narrow semantic/phrase detector rather than a single-word blacklist.

Acceptable implementation strategies:

```text
A. structured evidence ownership + phrase patterns
B. repository-native typed semantic tags
C. AST/field ownership checks if price actions are already structured
D. equivalent deterministic semantic rule
```

Do not introduce a second AI/model call merely to decide whether the sentence is technical.

The validator must remain deterministic.

---

# 9. Technical phrase examples

A narrow deterministic detector may consider patterns such as:

Korean:

```text
종가 + 돌파/상회/회복/안착
주가 + 돌파/상회/회복/안착
저항선
지지선
저항 구간
지지 구간
확인선
확인 가격
등록 확인 가격
돌파 후 안착
돌파 후 재지지
```

English:

```text
close above/below
share price above/below
breakout above/through
resistance level/zone
support level/zone
confirmation level/price
retest support/resistance
registered confirmation price
```

Do not reject:

```text
revenue broke a record
pricing remained strong
business support
customer support
earnings support the thesis
```

unless actual stock-price semantics are present.

---

# 10. Numbers inside business conditions

Maintain existing numeric-prose safety.

The business-condition field must not become a backdoor for:

```text
$ price levels
percentage stock thresholds
unsupported valuation numerics
```

If the existing candidate contract already forbids free numeric prose, preserve it.

No weakening.

Required:

```text
CONFIRMATION_BUSINESS_CONDITION_PRICE_NUMERIC = 0
```

---

# 11. Renderer ownership remains unchanged

The deterministic renderer continues to own:

```text
pullback price zone
breakout confirmation level
registered confirmation semantics
holder resistance/rejection scenario
new-buyer breakout scenario
```

The model business condition contributes only the non-price condition.

Example:

```text
structured:
confirmation level = $X
semantics = REGISTERED_PRICE_CONFIRMATION

model business condition:
HBM 출하와 현금창출 강세가 유지되는 것

renderer:
• 상향 재검토: $X의 등록 확인 조건 충족 + HBM 출하와 현금창출 강세 유지
```

No duplicate technical sentence.

---

# 12. Structured Autonomy must remain frozen

Keep exactly:

```text
Fact
→ business / earnings
→ market expectations
→ valuation
→ price / timing
→ risks
→ BUY drivers
→ SELL drivers
→ qualitative synthesis
→ BUY:SELL balance
→ deterministic overall direction
→ new-buyer view
→ holder view
→ price scenarios
```

Do NOT change:

```text
BUY threshold
SELL threshold
0.5 increment
HOLD lean mapping
Unknown policy
sector-aware policy
entry/holder semantics
```

Required:

```text
JUDGMENT_LOGIC_CHANGED = 0
BALANCE_THRESHOLD_CHANGED = 0
```

---

# 13. Keep prior provenance repair intact

The evidence alias constrained-selection repair is already successful.

Preserve:

```text
FREE_FORM_EVIDENCE_REF_GENERATION = 0
ALIAS_ONE_TO_ONE_MAPPING = PASS
NONEXISTENT_EVIDENCE_REF = 0
CROSS_SUBJECT_EVIDENCE_REF = 0
CROSS_MARKET_EVIDENCE_REF = 0
CROSS_GENERATION_EVIDENCE_REF = 0
```

Do not revert to free-form canonical refs.

---

# 14. Keep prior renderer repetition repair intact

Preserve:

```text
WRD_WULF_SUBSTANTIVE_CONFIRMATION_REPETITION = 0
SUBSTANTIVE_REPETITION = 0
```

Do not solve the false positive by handing generic confirmation prose back to the model.

---

# 15. Mandatory validator regression matrix

Create explicit tests for both false positives and true positives.

## Must PASS

At least:

```text
CRCL exact prior sentence
MU exact prior sentence
Korean "지지" in earnings-support meaning
Korean "가격" in product-pricing meaning
English "support" in business-support meaning
English "pricing" in product-pricing meaning
```

## Must FAIL

At least:

```text
종가 돌파
저항선 안착
지지선 회복
확인선 회복
주가 돌파
close above resistance
breakout through confirmation
support-level retest
registered confirmation price recovery
```

Required:

```text
FALSE_POSITIVE_FIXTURE_PASS_COUNT >= 6
TRUE_POSITIVE_BLOCK_FIXTURE_PASS_COUNT >= 9
```

---

# 16. Property / fuzz-style coverage

Add bounded deterministic tests for ambiguous words.

Examples:

```text
지지
가격
support
pricing
close
```

Test them in both:
- business contexts
- technical contexts

The goal is to prevent another one-token semantic shortcut.

Do not use random external model output for this test.

---

# 17. Fresh experiment generation required

After validator repair:

```text
DO NOT resume the 20/22 run
DO NOT reuse its passing candidates
DO NOT rerun only CRCL/MU
```

Create a completely new experiment generation.

Required:

```text
NEW_EXPERIMENT_GENERATION = PASS
OLD_PASSING_CANDIDATE_REUSE = 0
SELECTIVE_TICKER_RERUN = 0
MANUAL_CANDIDATE_OVERRIDE = 0
```

---

# 18. Frozen source lock

US:

```text
2026-09-03-us-run-53-055ae8ea01f6
```

KR:

```text
2026-09-03-kr-run-54-f19bb379daa7
```

Universe:

```text
US14:
CORZ CPNG CRCL GOOGL HUT IBM MU RXRX SKHY SNDK TSLA TSM WRD WULF

KR8:
000660 003690 005490 005930 010120 012450 047810 086280

TOTAL = 22
```

Fresh fact collection:

```text
0
```

---

# 19. First fresh blind run

Run all 22 from scratch.

Prior labels/balances/messages must not be visible before the fresh candidate is frozen.

Required validation:

```text
schema
balance/label consistency
evidence alias validity
canonical ref resolution
business-condition evidence ownership
confirmation semantic ownership
numeric provenance
semantic provenance
valuation safety
price provenance
KR accounting safety
ADR/security-basis safety
Unknown policy
message contradiction
substantive repetition
identity/language
```

Success:

```text
FIRST_RUN_VALIDATED = 22
```

---

# 20. Hard first gate

If:

```text
FIRST_RUN_VALIDATED != 22
```

stop.

Set:

```text
A_B_C_GATE = NOT_RUN_FIRST_GATE_FAILED
```

Do not:
- selectively rerun
- candidate override
- manually patch text
- ignore one ticker
- weaken a validator

---

# 21. First-run comparison is diagnostic only

After the new first run is frozen,
compare against the previous 20/22 candidate generation.

Report:
- label changes
- balance changes
- lean changes
- new-buyer stance changes
- holder stance changes

Do not target any previous distribution.

The prior provisional distribution is not a desired answer.

---

# 22. A/B/C gate

Only when:

```text
FIRST_RUN_VALIDATED = 22
```

execute:

```text
RUN A
RUN B
RUN C
```

with:
- same frozen evidence
- same prompt
- same schema
- same validator
- same renderer contract
- same model/runtime class

No cross-run decision visibility.

No post-result tuning.

No majority-vote production decision.

---

# 23. A/B/C metrics

Per ticker record:

```text
label A/B/C
BUY balance A/B/C
SELL balance A/B/C
HOLD lean A/B/C
confidence A/B/C
new-buyer stance A/B/C
holder stance A/B/C
preferred entry mode A/B/C
pullback zone A/B/C
confirmation level A/B/C
trim zone A/B/C
downside review A/B/C
selected evidence alias sets A/B/C
```

---

# 24. Stability classification

Use:

```text
STABLE
BOUNDARY_UNCERTAINTY
UNSTABLE
```

Suggested:

```text
STABLE
- balance spread <= 0.5
- no label change
- no BUY_LEAN↔SELL_LEAN flip
- no material user-action stance change

BOUNDARY_UNCERTAINTY
- balance spread <= 1.0
- real label/lean boundary
- no extreme reversal

UNSTABLE
- balance spread >= 1.5
or BUY↔SELL reversal
or unexplained BUY_LEAN↔SELL_LEAN flip
or ATTRACTIVE↔AVOID reversal
or HOLDABLE↔REDUCE reversal
```

Do not hide variance with averages.

---

# 25. Special stability audit

Highlight:

```text
GOOGL
IBM
MU
SNDK
TSM
SKHY
WRD
005930
010120
```

because recent blind generations have shown boundary movement.

This is an audit list only.

Do NOT hardcode their desired label.

---

# 26. Evidence-selection variance

Since alias selection is constrained and valid,
A/B/C may select different evidence.

Classify:

```text
SAME_CORE_EVIDENCE
DIFFERENT_VALID_EVIDENCE_SAME_INTERPRETATION
DIFFERENT_VALID_EVIDENCE_DIFFERENT_INTERPRETATION
```

Do not require identical evidence aliases across runs.

Do require every selected alias to be valid.

---

# 27. Promotion-readiness rule

Do not declare ready unless:

```text
FIRST_RUN_VALIDATED = 22
RUN_A_VALIDATED = 22
RUN_B_VALIDATED = 22
RUN_C_VALIDATED = 22

SAME_EVIDENCE_BUY_SELL_REVERSAL_COUNT = 0

UNEXPLAINED_HOLD_LEAN_FLIP_COUNT = 0

UNSTABLE_TICKER_COUNT = 0

NONEXISTENT_EVIDENCE_REF = 0

UNSUPPORTED_PRICE_NUMERIC = 0

MESSAGE_INTERNAL_CONTRADICTION = 0

SUBSTANTIVE_REPETITION = 0

GENERIC_BUSINESS_WORD_FALSE_POSITIVE = 0

BUSINESS_CONDITION_TECHNICAL_OWNERSHIP_LEAK = 0

KR_ACCOUNTING_SAFETY = PASS

ADR_SECURITY_BASIS_SAFETY = PASS
```

Natural KR/US proof remains a separate later promotion gate.

---

# 28. Tests

Run:

```text
focused confirmation semantic validator tests
focused CRCL/MU regression tests
focused alias/provenance tests
focused renderer/repetition tests
focused all22 shadow contract tests
full pytest
Ruff
git diff --check
secret scan
```

If exact-SHA CI exists, run it for:
- implementation SHA
- final report SHA

Do not skip full pytest.

---

# 29. Production safety

Required:

```text
PRODUCTION_DECISION_MUTATION = 0
PRODUCTION_RENDERER_CHANGE = 0
PRODUCTION_SEND = 0
SCHEDULER_CHANGE = 0
DB_CHANGE = 0
MAIN_MERGE = 0
```

This remains shadow-only.

---

# 30. Required reports

Create:

1. `docs/reports/20260903-confirmation-business-condition-ownership-contract.md`
2. `docs/reports/20260903-confirmation-validator-semantic-repair.md`
3. `docs/reports/20260903-confirmation-validator-regression-matrix.md`
4. `docs/reports/20260903-crcl-mu-false-positive-proof.md`
5. `docs/reports/20260903-confirmation-business-condition-provenance.md`
6. `docs/reports/20260903-uskr22-fresh-rerun-source-lock.md`
7. `docs/reports/20260903-uskr22-fresh-rerun-first-run.md`
8. `docs/reports/20260903-uskr22-fresh-rerun-validation.md`
9. `docs/reports/20260903-uskr22-prior20-vs-new22.md`
10. `docs/reports/20260903-uskr22-run-a.md`
11. `docs/reports/20260903-uskr22-run-b.md`
12. `docs/reports/20260903-uskr22-run-c.md`
13. `docs/reports/20260903-uskr22-stability-comparison.md`
14. `docs/reports/20260903-uskr22-hold-lean-stability.md`
15. `docs/reports/20260903-uskr22-action-context-stability.md`
16. `docs/reports/20260903-uskr22-evidence-selection-variance.md`
17. `docs/reports/20260903-uskr22-message-quality.md`
18. `docs/reports/20260903-uskr22-promotion-readiness.md`
19. `docs/reports/20260903-uskr22-validator-repair-artifact-index.md`

Machine-readable:

```text
20260903-confirmation-validator-regression.json
20260903-uskr22-fresh-rerun-first-run.json
20260903-uskr22-run-a.json
20260903-uskr22-run-b.json
20260903-uskr22-run-c.json
20260903-uskr22-stability.json
20260903-uskr22-validator-repair-proof.json
```

Exact message previews:
- US14 combined
- KR8 combined
- one exact message per subject

---

# 31. Required gates

Set exactly:

```text
BASE =
93d72816b5015c028b4a72475f4229fb120d3d10 / DESCENDANT

JUDGMENT_LOGIC_CHANGED =
0 / NONZERO

BALANCE_THRESHOLD_CHANGED =
0 / NONZERO

CONFIRMATION_BUSINESS_CONDITION_GROUNDED =
PASS / FAIL

BUSINESS_CONDITION_PRICE_ONLY_EVIDENCE =
0 / NONZERO

GENERIC_BUSINESS_WORD_FALSE_POSITIVE =
0 / NONZERO

BUSINESS_CONDITION_TECHNICAL_OWNERSHIP_LEAK =
0 / NONZERO

CONFIRMATION_BUSINESS_CONDITION_PRICE_NUMERIC =
0 / NONZERO

FALSE_POSITIVE_FIXTURE_PASS_COUNT =
...

TRUE_POSITIVE_BLOCK_FIXTURE_PASS_COUNT =
...

FREE_FORM_EVIDENCE_REF_GENERATION =
0 / NONZERO

ALIAS_ONE_TO_ONE_MAPPING =
PASS / FAIL

NONEXISTENT_EVIDENCE_REF =
0 / NONZERO

CROSS_SUBJECT_EVIDENCE_REF =
0 / NONZERO

CROSS_MARKET_EVIDENCE_REF =
0 / NONZERO

CROSS_GENERATION_EVIDENCE_REF =
0 / NONZERO

WRD_WULF_SUBSTANTIVE_CONFIRMATION_REPETITION =
0 / NONZERO

NEW_EXPERIMENT_GENERATION =
PASS / FAIL

OLD_PASSING_CANDIDATE_REUSE =
0 / NONZERO

SELECTIVE_TICKER_RERUN =
0 / NONZERO

MANUAL_CANDIDATE_OVERRIDE =
0 / NONZERO

PRIOR_RESULT_VISIBLE_BEFORE_NEW_FRESH_BALANCE =
0 / NONZERO

FIRST_RUN_VALIDATED =
22 / OTHER

A_B_C_GATE =
RUN / NOT_RUN_FIRST_GATE_FAILED

RUN_A_VALIDATED =
22 / OTHER / NOT_RUN

RUN_B_VALIDATED =
22 / OTHER / NOT_RUN

RUN_C_VALIDATED =
22 / OTHER / NOT_RUN

SAME_EVIDENCE_BUY_SELL_REVERSAL_COUNT =
... / NOT_MEASURED

UNEXPLAINED_HOLD_LEAN_FLIP_COUNT =
... / NOT_MEASURED

BOUNDARY_UNCERTAINTY_COUNT =
... / NOT_MEASURED

UNSTABLE_TICKER_COUNT =
... / NOT_MEASURED

UNSUPPORTED_PRICE_NUMERIC =
0 / NONZERO

MESSAGE_INTERNAL_CONTRADICTION =
0 / NONZERO

SUBSTANTIVE_REPETITION =
0 / NONZERO

KR_ACCOUNTING_SAFETY =
PASS / FAIL

ADR_SECURITY_BASIS_SAFETY =
PASS / FAIL

PRODUCTION_DECISION_MUTATION =
0 / NONZERO

PRODUCTION_RENDERER_CHANGE =
0 / NONZERO

PRODUCTION_SEND =
0 / NONZERO

SCHEDULER_CHANGE =
0 / NONZERO

DB_CHANGE =
0 / NONZERO

MAIN_MERGE =
0 / NONZERO

PROMOTION_READINESS =
READY_FOR_PROMOTION_REVIEW /
NEEDS_MORE_SHADOW_WORK /
NOT_READY
```

---

# 32. Completion response

Return:

```text
BASE =
...

VALIDATOR ROOT CAUSE =
...

REPAIR =
...

CRCL FALSE-POSITIVE REGRESSION =
PASS / FAIL

MU FALSE-POSITIVE REGRESSION =
PASS / FAIL

TRUE TECHNICAL-OWNERSHIP BLOCK TESTS =
...

PROVENANCE =
...

FRESH ALL22 FIRST RUN =
validation ...
distribution ...

US14 =
ticker / label / balance / lean / new-buyer / holder

KR8 =
ticker / label / balance / lean / new-buyer / holder

A/B/C =
...

STABILITY =
stable ...
boundary ...
unstable ...

MATERIAL VARIANCE =
...

EVIDENCE-SELECTION VARIANCE =
...

MESSAGE QUALITY =
...

PROMOTION READINESS =
...

PRODUCTION MUTATION = 0
PRODUCTION SEND = 0
MAIN MERGE = 0

ZIP =
...
ZIP_SHA256 =
...
```

---

# 33. Stop conditions

Stop and do not run A/B/C if:
- first fresh ALL22 < 22/22
- CRCL/MU exact regression fixtures still fail
- a real technical confirmation sentence passes the business-condition validator
- evidence alias integrity regresses
- WRD/WULF substantive repetition regresses
- any validator is disabled merely to reach 22/22
- any ticker-specific exception is introduced

---

# 34. Final principle

The validator should determine:

```text
who owns the meaning
```

not:

```text
whether a generic word appears
```

Business language such as:

```text
earnings are supported
product pricing is strong
```

must remain valid.

Actual stock-price confirmation language must remain owned by structured price fields and the deterministic renderer.

After this narrow repair, restart all 22 from zero and measure stability only after a true 22/22 first-gate pass.
