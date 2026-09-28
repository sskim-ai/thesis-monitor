# Thesis Monitor — R2B-R7
## Absolute-Current Financial Direction Guard + Post-Comparison Policy Calibration Audit
### Fix objective source-policy violations only; do not retune Monitoring AI to match the independent reviewer

**Purpose:** repair the two objectively invalid directional claims found after the sealed R2B-R6 comparison, while preserving all other accepted R6 outputs and conducting a no-retune audit of systematic judgment differences.

R2B-R7 is **not** a target-fitting task.

It must not change policy merely because Monitoring AI disagreed with the independent reviewer.

The only authorized behavioral repair is the already-established source rule:

> An absolute current financial amount, by itself, is context. It is not observed directional business evidence. A positive or negative direction requires a compatible comparative observation or another existing policy-approved directional fact.

The current R6 violations are 005930 and 047810.

All calibration observations for CPNG/HUT/WULF, large-cap New Buyer WAIT behavior, Holder compression, and score-range compression are audit-only in R7.

---

# 0. Newest SoT

Adopt R2B-R6 as the newest sealed Monitoring-AI result.

R2B-R6 result ZIP SHA-256:

`c2578c352831f5240e83ca6c6d9ac81957adfc89bd0cabe0f38f960f003648a3`

Terminal:

`R2B_R6_MONITORING_AI_24_MESSAGE_PASS_READY_FOR_BLIND_COMPARISON`

Neutral comparison-ready receipt confirms:

- message count:
  `24`
- comparison performed in R6:
  `false`
- independent assessment content read in R6:
  `false`
- source packet SHA:
  `c4fbc25ec81abe61c3981bfaa44204cc7e15cc252f25cbe6aedc6b2a1de9b44f`
- Market inherited calls:
  `2`
- Core inherited calls:
  `8`
- A new calls:
  `8`
- B new calls:
  `8`
- cumulative calls:
  `26`

R6 accepted execution:

- Market `2/2`
- Core `22/22`
- A `22/22`
- B `22/22`
- rendered `24/24`
- retry/fallback/judge `0`
- provider refresh `0`
- production sends/intents/writes/scheduler/deploy `0`

Do not overwrite R6.

---

# 1. Blind comparison evidence

Independent V2 was frozen before Monitoring-AI reveal.

Independent V2 bundle SHA-256:

`b025e86ba211fafe89d56be8268652c6482d589ea12e8510dbf040442e40ed77`

Independent V2 JSON SHA-256:

`9a083de6bef2b5b0e617136e10a67eed00ff5cacffc79809825f2ea51d34557d`

Post-seal comparison report ZIP SHA-256:

`8002957138129ec4d31bb9880c5d038de0114a60206a5248c293efa45334504f`

R7 may read the comparison report because the blind comparison is now complete.

However:

- do not use independent labels as target labels;
- do not fit per-ticker outputs;
- do not alter thresholds to maximize agreement.

Use the comparison only to identify generic contract violations and audit policy behavior.

---

# 2. Exact objective policy violation

Scan all R6 Core atomic claims.

Found exactly three directional claims whose only financial source is a current-only absolute earnings fact:

## 005930

1. BULLISH:
   `Reported revenue is positive; source period 2026-06-30. Revenue presence alone does not establish growth, profitability or durability.`

   source:
   `canonical:earnings:2026-06-30`

2. BULLISH:
   `Reported operating_income is positive; source period 2026-06-30. Recurrence is not established by this observation.`

   source:
   `canonical:earnings:2026-06-30`

These claims were later used as supporting refs for:

- Overall BUY
- Holder HOLDABLE

## 047810

1. BULLISH:
   `Reported operating_income is positive; source period 2026-06-30. Recurrence is not established by this observation.`

   source:
   `canonical:earnings:2026-06-30`

This claim was later used as positive Overall/Holder support.

No other R6 Core directional claim was found with a current-only `canonical:earnings:*` source.

This must be proven again programmatically; do not hardcode the count as policy.

---

# 3. Existing product/source rule is authoritative

Preserve the already-adopted financial direction contract:

- exact issuer/security ownership
- exact provider/document identity
- exact financial period
- period role
- statement basis
- currency/unit
- canonical field semantic
- exact source row/occurrence lineage
- source-use eligibility

For **direction**, additionally require:

- compatible current/prior observation; or
- another existing explicitly approved observed directional fact.

Absolute current amount alone may be:

`ABSOLUTE_CONTEXT_ELIGIBLE`

but must not be:

`DIRECTION_ELIGIBLE`

merely because:

- revenue > 0
- operating income > 0
- net income > 0
- another amount is numerically positive/negative.

---

# 4. Fix the source-use eligibility before Core

Do not wait until renderer validation.

The source-use/claim builder feeding Core must classify current-only financial facts correctly.

For facts equivalent to:

`canonical:earnings:<period>`

with no compatible prior/comparison lineage:

allowed uses may include existing context/factual uses.

They must be prohibited from at least:

- `OVERALL_DIRECTION`
- `HOLDER_STANCE`
- `ENTRY`
- any other existing directional decision use

according to the existing source-use taxonomy.

Do not prohibit ordinary factual display if existing policy allows it.

Do not change comparison facts:

`canonical:earnings_comparison:*`

that already pass comparative lineage.

---

# 5. Core atomic-claim polarity guard

Add a generic deterministic/semantic rule:

A Core atomic claim with polarity:

- `BULLISH`
- `BEARISH`

must not be supported solely by a source fact whose directional eligibility is false.

For an absolute current financial amount:

- factual text may remain;
- polarity must be `NEUTRAL` / context-equivalent;
- or the claim must be excluded from directional Core claim set.

Do not change the underlying numeric fact.

Do not hide the fact.

Do not create a prior value.

---

# 6. Claim text/polarity contradiction guard

The current 005930 claim itself says:

`Revenue presence alone does not establish growth...`

while its polarity is `BULLISH`.

Add a generic semantic consistency rule:

If claim text/typed source semantics explicitly state that a fact does not establish direction, the claim cannot carry BULLISH/BEARISH polarity unless another direction-eligible ref is present.

Prefer typed source-use state over keyword text.

Do not implement a natural-language keyword heuristic as the owner.

---

# 7. Directional entitlement recomputation

After the source-use fix, recompute directional entitlement for all 22 from the sealed R6 source packet.

Expected by current forensic evidence—but not hardcoded:

- 005930 may fall to zero authorized Overall-direction refs
- 047810 may fall to zero authorized Overall-direction refs

If zero:
- use the already accepted generic `UNKNOWN_LIMIT / OBSERVE` whole-decision path.

Do not preserve their old BUY/HOLD merely for continuity.

If another valid direction-eligible ref exists:
- use it normally.

---

# 8. 005930 / 047810 corrected semantics

Do not hardcode final investment labels.

Generic expected path if no other directional source remains:

- Overall = `OBSERVE`
- New Buyer = `OBSERVE`
- Holder = `OBSERVE`
- ratio = null
- directional confidence = null / NOT_ASSESSED
- current technical/price information remains context only
- configured thesis conditions remain non-observed conditions
- no positive business direction inferred from current absolute profit/revenue

The renderer must clearly state directional evidence is insufficient.

---

# 9. Twenty-subject invariance

Subjects other than any genuinely affected by the generic direction guard must preserve exact R6 decisions and message hashes where possible.

At minimum audit all 22.

If a subject's R6 directional evidence is comparative and valid:
- its result should not change due this repair.

No ticker-specific exception.

Produce:

`absolute-current-direction-impact-matrix.json`

with:
- ticker
- directional refs before
- absolute-current refs
- comparative refs
- refs removed from direction
- decision mode before/after
- result changed?
- exact reason

---

# 10. No new model calls unless strictly necessary

First perform the entire repair and 22-subject decision-mode recomputation offline.

If 005930/047810 become UNKNOWN_LIMIT:

- use the existing deterministic UNKNOWN_LIMIT path;
- do not call Core/A/B for those subjects merely to obtain an OBSERVE result.

Preserve the existing sealed R6 model outputs for unaffected subjects.

No new provider calls.

If the existing pipeline technically requires a model-stage recomputation for an affected non-UNKNOWN_LIMIT subject:
- freeze the exact minimal plan;
- return to Chat before model execution unless it is already within an accepted deterministic continuation contract.

Default R7 model calls:
`0`

---

# 11. Produce a corrected 24-message review corpus if possible with zero model calls

If only deterministic limitation-state corrections are needed:

- reuse the 22 unaffected R6 messages exactly;
- regenerate affected message(s) from the corrected deterministic policy path;
- produce a new corrected review corpus of 24 messages;
- do not overwrite the original R6 Monitoring-AI result.

Clearly label:

`POST_COMPARISON_SOURCE_POLICY_CORRECTED`

This is not the original blind-comparison result.

Keep both artifacts.

---

# 12. Policy-calibration audit — no tuning

Separately inspect the comparison differences.

At minimum audit:

## A. Execution-dependent growth downside sensitivity

Subjects:
- CPNG
- HUT
- WULF

Question:

Why can materially worsening operating economics produce:
- New Buyer AVOID
- Holder REVIEW

while Overall remains close to neutral or even slightly buy-leaning?

Trace:

- archetype
- active-risk policy
- persistence requirement
- Overall reason class
- directional score bins
- Holder policy

Do not change thresholds.

Output:
`execution-growth-downside-calibration-audit.json`

## B. New Buyer systematic conservatism

R6 observed:
- active BUY/ATTRACTIVE count among evidence-based subjects:
  `0`
- WAIT/AVOID dominates

Trace exact causes:
- fundamental valuation unresolved
- security valuation basis unresolved
- entry-range unavailable
- tactical gate
- other exact structured reasons

Do not relax valuation requirements.

Output:
`new-buyer-actionability-audit.json`

## C. Holder action compression

R6 observed:
- no ADD
- no REDUCE
- HOLDABLE/REVIEW/OBSERVE only

Trace whether this is:
- schema vocabulary
- policy restriction
- source evidence insufficiency
- current sample only

Do not add actions.

Output:
`holder-actionability-audit.json`

## D. Directional-score compression

R6 evidence-based scores observed within approximately:
`4.5 .. 7.5`

Independent V2 used:
`2 .. 8`

Audit:
- schema min/max
- policy bins
- model prompt
- semantic validator
- observed sample

Do not retune.

Output:
`directional-score-compression-audit.json`

---

# 13. Large-cap policy descriptively compare, do not fit

Descriptively report how current policy treats:

- GOOGL
- MU
- TSM
- SKHY
- 000660
- 005930

especially:

- Overall direction
- New Buyer WAIT due valuation/security basis
- Holder result
- confidence

Do not change policy based on the independent review.

Return a product-policy decision matrix showing possible future options, not recommendations encoded into code.

---

# 14. Source-quality versus judgment-policy distinction

For 000660 and similar cases, distinguish:

- AI conservatism caused by `financial_quality` limitation
versus
- investment-policy conservatism.

Do not solve a source-quality denial by changing investment thresholds.

If source quality is the limiting factor:
- record it as source-coverage/quality work.

---

# 15. Validation

Required:

## Direction eligibility

- absolute current positive revenue -> not directional
- absolute current positive operating income -> not directional
- absolute current loss/negative amount -> not automatically bearish
- compatible current/prior higher -> directional where existing policy permits
- compatible current/prior lower -> directional where existing policy permits
- mismatched period -> not directional
- source-use denied -> not directional

## Claim polarity

- non-directional source-only + BULLISH -> fail
- non-directional source-only + BEARISH -> fail
- non-directional source-only + NEUTRAL -> pass
- mixed refs with valid directional ref -> policy applies normally

## Current cohort

- 22-subject directional-ref audit
- 005930 regression
- 047810 regression
- SNDK UNKNOWN_LIMIT unchanged
- all comparison-source claims unchanged

## R6 invariance

- source packet hashes unchanged
- Market outputs unchanged
- unaffected Core/A/B outputs unchanged
- quality supplement unchanged
- independent comparison artifacts unchanged

## Repository

- full pytest
- Ruff
- `git diff --check`
- Investment Knowledge
- Chart Knowledge
- secret scan
- no new unexplained skip/xfail

---

# 16. Production side effects

Hard zero:

- provider/source refresh
- Alpha Vantage
- model calls by default
- Telegram
- recipient intent
- production DB writes
- scheduler mutation
- broker
- deploy
- main merge
- remote push
- restart

R7 is policy-correction + audit.

---

# 17. Completion terminals

## Objective source-policy repair PASS

`R2B_R7_ABSOLUTE_CURRENT_DIRECTION_GUARD_PASS`

Require:

- no absolute-current-only financial fact can own directional polarity
- 22-subject audit PASS
- affected decisions corrected generically
- R6 source hashes unchanged
- validation PASS
- calibration audits produced
- no policy retuning

## Additional directional source unexpectedly exists

If 005930/047810 remain evidence-based via another valid source:
- document exact ref
- do not force UNKNOWN_LIMIT.

## Direction guard causes unrelated subject regression

`R2B_R7_DIRECTION_GUARD_SCOPE_REGRESSION`

Stop.

## Calibration audit finds a contract bug

Report the exact generic contract bug but do not repair it unless it is the authorized absolute-current rule.

---

# 18. Required artifacts

At minimum:

- REPORT.md
- summary.json
- R6 result identity/SHA
- comparison report identity/SHA
- repository identities
- changed-file inventory

## Objective fix

- current-only financial source-use contract before/after
- 22-subject directional-source matrix
- absolute-current directional claim inventory
- claim-polarity validation matrix
- `absolute-current-direction-impact-matrix.json`
- 005930 before/after
- 047810 before/after
- corrected message corpus if deterministic
- unaffected R6 invariance receipt

## Calibration audit

- `execution-growth-downside-calibration-audit.json`
- `new-buyer-actionability-audit.json`
- `holder-actionability-audit.json`
- `directional-score-compression-audit.json`
- large-cap descriptive policy matrix
- source-quality-vs-policy matrix

## Safety/validation

- model/provider counters
- production side-effect counters
- focused/full validation
- secret scan
- bundle manifest

---

# 19. Final principle

Do not tune Monitoring AI toward the independent reviewer.

Fix only what violates the source contract.

A current absolute financial amount can be displayed as context, but it cannot become observed business direction without compatible comparative evidence.

After that objective repair, use the independent comparison only to decide whether separate, explicit future policy-calibration work is desirable.
