# thesis-monitor — US14 + KR8 Provenance / Renderer Repair + Full Blind Re-run
## Repair only the two first-gate failures
## Preserve Structured Autonomy judgment logic
## Re-run all 22 from a clean generation
## Run A/B/C stability only after 22/22 first-gate PASS

---

# 0. Metadata

- Repository: `sskim-ai/thesis-monitor`
- Date: `2026-09-03 KST`
- Base branch for prior all22 experiment:
  `90cc52231c7343056c853c355ea90dfea10de25b`
- Prior all22 implementation/result branch:
  `93d72816b5015c028b4a72475f4229fb120d3d10`
- Prior work-instruction commit:
  `0969e70`
- Prior first blind run:
  `21/22 PASS`
- Prior distribution:
  `BUY 7 / HOLD 10 / SELL 5`
- Prior A/B/C:
  `NOT_RUN_FIRST_GATE_FAILED`
- Prior promotion readiness:
  `NOT_READY`
- Production mutation: `0`
- Telegram send: `0`
- Scheduler change: `0`
- DB change: `0`
- Main merge: `0`

This task is a narrow repair.

Do NOT redesign the investment-judgment model.

---

# 1. Prior failure facts

The prior all22 first blind run failed for exactly two known quality classes.

## Failure A — evidence-reference integrity

Ticker:

```text
086280
```

Observed:

```text
one evidence ref was emitted that did not exist in the allowed evidence surface
```

Impact:

```text
candidate invalid
ALL22 validation = 21/22
```

This is a provenance/identity problem.

It is not a business-judgment problem.

---

## Failure B — substantive confirmation repetition

Tickers:

```text
WRD
WULF
```

Observed:

```text
one substantive confirmation sentence was repeated
```

The repeated semantics were generic confirmation language similar to:

```text
registered confirmation level must be recovered/held before reconsidering a new position
```

while ticker-specific confirmation levels were already separately present.

Impact:

```text
message repetition gate failed
```

This is a renderer/semantic-ownership problem.

It is not a directional-balance problem.

---

# 2. Preserve prior good gates

The prior run already proved:

```text
focused tests                    16 passed
full pytest                      2177 passed
Ruff                             PASS
git diff check                   PASS
GitHub Actions exact SHA         PASS

unsupported price numeric        0
KR accounting safety             PASS
ADR basis safety                 PASS
secret scan                      0

production mutation              0
Telegram send                    0
scheduler change                 0
DB change                        0
main merge                       0
```

Do not weaken or bypass these gates.

---

# 3. Core repair principle

Repair:

```text
identity selection
renderer ownership
```

Do not repair by:

```text
changing BUY/HOLD/SELL thresholds
changing balance rules
adding ticker-specific prompt instructions
editing 086280 candidate manually
editing WRD/WULF final text manually
reusing the old 21 passing candidates
selectively rerunning only failed tickers
```

Hard:

```text
JUDGMENT_LOGIC_CHANGED = 0
MANUAL_CANDIDATE_OVERRIDE = 0
SELECTIVE_TICKER_RERUN = 0
OLD_PASSING_CANDIDATE_REUSE = 0
```

---

# 4. Evidence-reference design goal

The model should retain autonomy over:

```text
which evidence matters
which evidence supports BUY drivers
which evidence supports SELL drivers
which evidence supports the final judgment
```

The model should NOT retain autonomy over:

```text
inventing evidence identifier strings
```

This is structured autonomy.

The model chooses from valid evidence identities;
it does not mint new identities.

---

# 5. Canonical evidence alias layer

For each subject packet, build a deterministic alias map before model invocation.

Example:

```text
E01 → canonical evidence ref A
E02 → canonical evidence ref B
E03 → canonical evidence ref C
...
```

Requirements:

```text
aliases unique within subject
ordering deterministic
same evidence fingerprint → same alias map
alias map persisted in shadow artifact
canonical ref preserved for audit
```

Do not use random aliases.

Do not use mutable list ordering if provider iteration is unstable.

---

# 6. Alias content

The model may see a compact evidence catalogue such as:

```text
E01 | date | category | concise fact
E02 | date | category | concise fact
...
```

The exact prompt format may follow repository-native conventions.

Each alias must map to exactly one canonical evidence object/ref.

No alias may map to:
- multiple unrelated facts
- nonexistent facts
- facts from another ticker
- facts from another market
- facts from another generation

Required:

```text
ALIAS_ONE_TO_ONE_MAPPING = PASS
```

---

# 7. Constrained selection

The candidate schema must constrain evidence selection to the subject's allowed alias set.

Preferred options:

```text
JSON schema enum
or repository-native constrained choice type
```

For example:

```json
"evidence_refs": {
  "type": "array",
  "items": {
    "enum": ["E01", "E02", "E03", "E04"]
  }
}
```

If dynamic enum generation is not supported by the current schema path,
use an equally strict native mechanism.

A free-form `string[]` is insufficient.

Hard:

```text
FREE_FORM_EVIDENCE_REF_GENERATION = 0
```

---

# 8. Alias resolution

After model output passes schema validation:

```text
E03
→ resolve deterministically
→ canonical evidence ref
```

Persist both where useful:

```text
selected_alias
canonical_ref
```

User-facing output should not expose internal aliases unless native message design requires it.

Downstream provenance validators should operate on canonical refs.

---

# 9. Evidence provenance safety

Required validations:

```text
selected alias exists
alias belongs to same subject
alias belongs to same evidence generation
alias belongs to same market
alias resolves one-to-one
canonical ref exists
canonical ref content fingerprint matches source
```

Hard:

```text
NONEXISTENT_EVIDENCE_REF = 0
CROSS_SUBJECT_EVIDENCE_REF = 0
CROSS_MARKET_EVIDENCE_REF = 0
CROSS_GENERATION_EVIDENCE_REF = 0
```

---

# 10. No ticker-specific 086280 workaround

Do NOT solve by:

```text
if ticker == 086280:
  drop unknown ref
```

or:

```text
086280 allowed refs = hardcoded list
```

The repair must work for:
- all US14
- all KR8
- future monitored tickers

Use generic packet-owned evidence catalogues.

---

# 11. Renderer repetition root cause

The prior messages contained:

```text
ticker-specific confirmation number
plus
generic substantive confirmation sentence
```

which repeated the same meaning across multiple tickers.

Do not ask the model to solve this with stylistic synonym generation.

That would create:
- unstable wording
- hidden semantic duplication
- unnecessary model variance

The renderer should own the repeated structural sentence.

---

# 12. Confirmation scenario ownership

Move confirmation scenario wording to structured fields.

Candidate should provide structured data such as:

```json
{
  "breakout_confirmation_level": 6.68,
  "confirmation_semantics": "registered_price_confirmation",
  "confirmation_business_condition": "...ticker-specific business condition..."
}
```

Repository-native equivalents are allowed.

The model should NOT generate a generic free-form sentence equivalent to:

```text
recover and hold the registered confirmation level before reconsidering entry
```

if the renderer can produce that deterministically.

Hard:

```text
GENERIC_CONFIRMATION_FREE_TEXT_OWNERSHIP = 0
```

---

# 13. Deterministic confirmation renderer

Renderer owns structural language.

Example:

```text
WRD
• 추세 확인 가격: $6.68
• 상향 재검토: $6.68 종가 회복·안착 + 상용화 경제성 확인

WULF
• 추세 확인 가격: $18.40
• 상향 재검토: $18.40 종가 회복·안착 + HPC 전환 경제성 확인
```

The structural clause may be templated.

The ticker-specific business condition may remain model-generated if supported.

The final sentence must combine:
- structured price condition
- ticker-specific substantive condition

without duplicating another user-facing line.

---

# 14. Existing confirmation semantics

Do not invent new multi-day confirmation rules.

Use:
- stored confirmation semantics
- registered price rule
- verified native technical semantics

If the stored rule says only:

```text
close above X
```

do not add:
- three-day hold
- weekly confirmation
- volume threshold

unless already owned by source rules.

---

# 15. Same resistance dual scenario remains

Keep prior semantic rule:

```text
holder:
resistance rejection/failure → reassess

new buyer:
successful breakout/confirmation → reconsider entry
```

Do not collapse them into one generic sentence.

Do not create substantive repetition between:
- current price structure
- new-buyer view
- re-evaluation conditions

---

# 16. AVOID semantics remain

If:

```text
new_buyer = AVOID
```

use:

```text
재검토 가격 조건
```

not:

```text
진입 검토 구간
```

No actionable-entry wording.

---

# 17. Judgment architecture remains frozen

Keep exactly the current Structured Autonomy contract:

```text
Fact
→ business / earnings
→ expectations
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

Do not add fixed weights.

Do not add factor arithmetic.

Do not retune thresholds.

Required:

```text
FIXED_FACTOR_WEIGHTING = 0
SUBSCORE_ARITHMETIC = 0
BALANCE_THRESHOLD_CHANGED = 0
```

---

# 18. Fresh experiment generation

After implementing the two generic repairs:

```text
start a NEW experiment generation
```

Do not patch the prior 21/22 generation.

Required:

```text
NEW_EXPERIMENT_GENERATION = PASS
```

The new run must have:
- new candidate generation IDs
- new candidate SHAs
- new accepted-shadow SHAs
- new rendered-message SHAs

Evidence packets remain frozen.

---

# 19. Source lock

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
US14
CORZ CPNG CRCL GOOGL HUT IBM MU RXRX SKHY SNDK TSLA TSM WRD WULF

KR8
000660 003690 005490 005930 010120 012450 047810 086280
```

Total:

```text
22
```

No fresh facts.

---

# 20. No reuse of prior decisions

The new first run must NOT reuse:

```text
prior labels
prior balances
prior new-buyer stances
prior holder stances
prior price-mode choices
prior candidate prose
```

Prior results may be loaded only AFTER the new first run is frozen,
for comparison reports.

Hard:

```text
PRIOR_RESULT_VISIBLE_BEFORE_NEW_FRESH_BALANCE = 0
```

---

# 21. Full first blind run

Run all 22 again from scratch.

Validation must include:

```text
schema
balance
label consistency
evidence alias validity
canonical ref resolution
numeric provenance
semantic provenance
valuation safety
price provenance
KR accounting safety
ADR/security-basis safety
message repetition
message contradiction
identity/language
```

Required:

```text
FIRST_RUN_VALIDATED = 22
```

Anything less stops the experiment.

---

# 22. First-run stop rule

If:

```text
FIRST_RUN_VALIDATED != 22
```

then:

```text
A/B/C = NOT_RUN_FIRST_GATE_FAILED
```

again.

Do not selectively rerun failures.

Do not manually override candidates.

Do not continue just because 21/22 or 20/22 passed.

---

# 23. First-run expected comparison

After new 22/22 is frozen,
compare to the prior failed first run.

Per ticker:

```text
old label
new label
old balance
new balance
old new-buyer stance
new new-buyer stance
old holder stance
new holder stance
```

This comparison is diagnostic only.

Do not attempt to recover the old distribution.

---

# 24. Do not target prior distribution

Prior distribution:

```text
BUY 7
HOLD 10
SELL 5
```

is NOT a target.

The repaired fresh run may differ.

Do not tune to reproduce:
- GOOGL BUY
- IBM BUY
- MU BUY
- SNDK BUY
- TSM BUY
- any KR label

Judge only stability and evidence quality.

---

# 25. A/B/C gate

Only if:

```text
FIRST_RUN_VALIDATED = 22
```

run:

```text
A
B
C
```

on identical frozen evidence and identical contract.

No cross-run visibility.

No prompt/schema changes.

No post-result tuning.

---

# 26. A/B/C stability metrics

Per ticker measure:

```text
label sequence
balance sequence
max balance spread
HOLD lean sequence
new-buyer stance sequence
holder stance sequence
preferred entry mode sequence
pullback zone
confirmation level
trim zone
downside review
```

Also measure:

```text
evidence alias selection variance
```

Important:
different valid evidence alias selections are allowed
if final interpretation remains supported.

---

# 27. Stability classification

Keep current classification:

```text
STABLE

BOUNDARY_UNCERTAINTY

UNSTABLE
```

Suggested:

```text
STABLE:
balance spread <= 0.5
no label change
no BUY_LEAN↔SELL_LEAN flip
no material action-context change

BOUNDARY_UNCERTAINTY:
spread <= 1.0
difference near real threshold
no extreme reversal

UNSTABLE:
spread >= 1.5
or BUY↔SELL reversal
or unexplained BUY_LEAN↔SELL_LEAN flip
or ATTRACTIVE↔AVOID reversal
or HOLDABLE↔REDUCE reversal
```

---

# 28. Evidence-selection variance audit

Because evidence IDs are now constrained aliases,
measure whether the model selects different valid evidence across A/B/C.

Classify:

```text
SAME_CORE_EVIDENCE
DIFFERENT_VALID_EVIDENCE_SAME_INTERPRETATION
DIFFERENT_VALID_EVIDENCE_DIFFERENT_INTERPRETATION
```

This is useful for understanding model variance.

Do not require identical aliases across runs.

---

# 29. Renderer repetition audit

Run repetition scan at:
- within-message level
- cross-section level
- cross-ticker structural-template level

Structural template similarity is allowed.

Substantive duplicated meaning inside one message is not.

Do not fail merely because the same template words appear across tickers.

The validator must distinguish:

```text
STRUCTURAL_TEMPLATE_REUSE
vs
SUBSTANTIVE_REPETITION
```

---

# 30. Repetition validator calibration

Do NOT weaken the substantive repetition validator.

Instead:
- normalize known renderer-owned structural template text
- exclude deterministic headings/template scaffolding from substantive comparison
- continue to detect duplicated investment meaning

Required:

```text
SUBSTANTIVE_REPETITION = 0
```

---

# 31. 086280 proof

Create a dedicated audit showing:

```text
allowed alias set
selected aliases
resolved canonical refs
all canonical refs exist
same-subject ownership
same-market ownership
same-generation ownership
```

Required:

```text
086280_NONEXISTENT_REF = 0
```

No ticker-specific code path.

---

# 32. WRD/WULF proof

Create a dedicated renderer audit showing:

```text
WRD confirmation fields
WRD final confirmation wording

WULF confirmation fields
WULF final confirmation wording
```

Prove:
- no duplicated substantive confirmation sentence
- both retain ticker-specific business conditions
- structured confirmation semantics remain correct
- no unsupported price numbers

---

# 33. Full quality gates

Required:

```text
ALL22_VALIDATED = 22

NONEXISTENT_EVIDENCE_REF = 0

CROSS_SUBJECT_EVIDENCE_REF = 0

CROSS_MARKET_EVIDENCE_REF = 0

CROSS_GENERATION_EVIDENCE_REF = 0

UNSUPPORTED_PRICE_NUMERIC = 0

MESSAGE_INTERNAL_CONTRADICTION = 0

SUBSTANTIVE_REPETITION = 0

KR_ACCOUNTING_SAFETY = PASS

ADR_SECURITY_BASIS_SAFETY = PASS

UNKNOWN_AUTOMATIC_SELL_PENALTY = 0
```

---

# 34. Tests

Run at minimum:

```text
focused alias/provenance tests
focused renderer/repetition tests
focused all22 shadow contract tests
full pytest
Ruff
git diff --check
secret scan
```

If CI exact-SHA workflow exists, run it for:
- implementation SHA
- final report SHA

Do not skip full pytest solely because changes appear small.

---

# 35. Production safety

This task remains shadow-only.

Required:

```text
PRODUCTION_DECISION_MUTATION = 0
PRODUCTION_RENDERER_CHANGE = 0
PRODUCTION_SEND = 0
SCHEDULER_CHANGE = 0
DB_CHANGE = 0
MAIN_MERGE = 0
```

Do not use the repaired KR natural scheduler for this experiment.

---

# 36. Required reports

Create:

1. `docs/reports/20260903-evidence-alias-contract.md`
2. `docs/reports/20260903-evidence-alias-resolution-proof.md`
3. `docs/reports/20260903-confirmation-renderer-ownership.md`
4. `docs/reports/20260903-repetition-validator-calibration.md`
5. `docs/reports/20260903-086280-evidence-ref-audit.md`
6. `docs/reports/20260903-wrd-wulf-confirmation-renderer-audit.md`
7. `docs/reports/20260903-uskr22-fresh-first-run.md`
8. `docs/reports/20260903-uskr22-fresh-first-run-validation.md`
9. `docs/reports/20260903-uskr22-prior-vs-fresh-first-run.md`
10. `docs/reports/20260903-uskr22-run-a.md`
11. `docs/reports/20260903-uskr22-run-b.md`
12. `docs/reports/20260903-uskr22-run-c.md`
13. `docs/reports/20260903-uskr22-stability-comparison.md`
14. `docs/reports/20260903-uskr22-evidence-selection-variance.md`
15. `docs/reports/20260903-uskr22-message-quality.md`
16. `docs/reports/20260903-uskr22-promotion-readiness.md`
17. `docs/reports/20260903-uskr22-artifact-index.md`

Machine-readable:

```text
20260903-evidence-alias-map.json
20260903-uskr22-fresh-first-run.json
20260903-uskr22-run-a.json
20260903-uskr22-run-b.json
20260903-uskr22-run-c.json
20260903-uskr22-stability.json
20260903-uskr22-proof.json
```

Exact message previews:
- US14 combined
- KR8 combined
- one exact file per subject

---

# 37. Required gates

Set exactly:

```text
BASE_BRANCH =
93d72816b5015c028b4a72475f4229fb120d3d10 / DESCENDANT

JUDGMENT_LOGIC_CHANGED =
0 / NONZERO

MANUAL_CANDIDATE_OVERRIDE =
0 / NONZERO

SELECTIVE_TICKER_RERUN =
0 / NONZERO

OLD_PASSING_CANDIDATE_REUSE =
0 / NONZERO

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

GENERIC_CONFIRMATION_FREE_TEXT_OWNERSHIP =
0 / NONZERO

NEW_EXPERIMENT_GENERATION =
PASS / FAIL

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

086280_NONEXISTENT_REF =
0 / NONZERO

WRD_WULF_SUBSTANTIVE_CONFIRMATION_REPETITION =
0 / NONZERO

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

# 38. Completion response

Return:

```text
BASE =
...

REPAIR =
evidence alias ...
renderer ownership ...

086280 =
...

WRD/WULF =
...

FRESH FIRST RUN =
validation ...
distribution ...

US14 =
ticker / label / balance / lean / new-buyer / holder

KR8 =
ticker / label / balance / lean / new-buyer / holder

A/B/C =
run status ...

STABILITY =
stable ...
boundary ...
unstable ...

EVIDENCE SELECTION VARIANCE =
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

# 39. Stop conditions

Stop immediately if:
- alias resolution is not one-to-one
- any nonexistent canonical ref appears
- first run is <22/22
- renderer still duplicates substantive confirmation meaning
- validator is weakened to pass
- ticker-specific workaround is introduced

Do not proceed to A/B/C after a failed first gate.

---

# 40. Final principle

The model should be free to decide:

```text
which valid evidence matters
and what that evidence means
```

The model should not be free to invent:

```text
evidence identities
or redundant structural confirmation prose
```

Fix identity and rendering deterministically.

Then restart the full 22-subject experiment from zero.
