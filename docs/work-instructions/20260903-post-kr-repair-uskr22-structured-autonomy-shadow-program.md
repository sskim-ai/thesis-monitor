# thesis-monitor — Post-KR-Repair US14 + KR8 Structured Autonomy Shadow Program
## Continue the investment-judgment architecture across the complete monitored universe
## after the KR live-orchestration defect is engineering-closed
## Shadow only; no production decision/renderer/send mutation

---

# 0. Verified Phase-1 prerequisite

The KR live-orchestration repair bundle has been reviewed.

Verified repair lineage:

```text
incident operating revision:
5d5f3363d3a762b62698943b1feb4fa121d0d0f9

work-instruction commit:
20d052dee5f4ea0d6b2630a284434a98ca52596a

implementation:
d00741abbe227bd199c8383de0cad9bbd740ceeb

report set:
a3f604fc16c1c875856877f812b34388e77b1eee

final repair branch:
90cc52231c7343056c853c355ea90dfea10de25b

main merge:
0
```

Verified incident/root-cause facts:

```text
corrected accepted review             9/9

root cause A:
analysis reuse overwrote delivery ownership
→ primary pending 9 became retry-invisible

root cause B:
claim-bound final accepted V2 artifact missing
→ V2_DECISION_SUPPRESSED_SAFE

relationship:
INDEPENDENT
```

Verified repaired live-path E2E:

```text
real production entrypoint            PASS
signed-in Codex model reached         PASS
accepted total                        9
explicit AI market                    1
explicit stock V2                     8
pending after accept                  9
fresh-process retry discovered        9
TEST AI sends                         9
fallback sends                        0
duplicates                            0
```

Verified controlled failure path:

```text
AI sends                              0
fallback sends                        9
duplicates                            0
```

Verified tests:

```text
focused delivery/orchestration        60 passed
full pytest                           2161 passed
Ruff                                  PASS
git diff --check                      PASS
```

Repair verdict:

```text
READY_FOR_NATURAL_PROOF
```

Therefore this Phase-2 shadow program may proceed.

Natural KR proof is still pending and remains a production-promotion gate.

---

# 1. Branch/base requirement

Start this work from the repaired final branch:

```text
90cc52231c7343056c853c355ea90dfea10de25b
```

or a descendant containing the same implementation.

Do NOT start from the stale operating main revision
`5d5f336...` for this Phase-2 work.

Do not merge to main in this task.

Required:

```text
PHASE2_BASE_CONTAINS_KR_LIVE_REPAIR = PASS
MAIN_MERGE = 0
```

---

# 2. Goal

Apply the finalized Structured Autonomy judgment architecture to:

```text
US14 + KR8 = 22 monitored subjects
```

and answer:

```text
1. Does the same judgment structure work across both markets?
2. Does sector-aware autonomy remain intact?
3. Are BUY/HOLD/SELL and BUY:SELL balances stable on identical evidence?
4. Are new-buyer / holder views useful and semantically consistent?
5. Are entry/confirmation/trim/downside price scenarios fully supported?
6. Is the structure ready for later production promotion review?
```

This is not a live-delivery task.

---

# 3. Universe

US14:

```text
CORZ
CPNG
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

Required:

```text
US_COUNT = 14
KR_COUNT = 8
TOTAL_COUNT = 22
```

---

# 4. Evidence lock

## US

Use exact frozen source:

```text
2026-09-03-us-run-53-055ae8ea01f6
```

## KR

Use the authoritative natural run-54 primary packet:

```text
2026-09-03-kr-run-54-f19bb379daa7
```

The later reuse/fallback packet:

```text
2026-09-03-kr-run-54-78ed269de3df
```

must not replace the primary evidence owner.

It may be inspected only for lineage/ownership comparison where necessary.

No fresh market/news/financial fetch in the initial full-universe comparison.

Required:

```text
FRESH_FACT_COLLECTION = 0
CROSS_MARKET_FACT_LEAKAGE = 0
CROSS_GENERATION_FACT_LEAKAGE = 0
```

Create canonical evidence fingerprints for all 22.

---

# 5. Structured Autonomy principle

This system provides:

```text
structured reasoning
```

not:

```text
mechanical scoring
```

Forbidden:

```text
fixed factor weights
business 30 + valuation 20 + price 20 ...
universal factor arithmetic
sector-agnostic scorecard
balance interpreted as probability
```

Required reasoning order:

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
→ BUY:SELL directional balance
→ deterministic overall direction
→ new-buyer view
→ holder view
→ price scenarios
```

The model retains autonomy over:
- which facts dominate
- how sector context changes importance
- asymmetry
- confirmation cost
- evidence quality
- whether price/timing materially changes current actionability

---

# 6. Core judgment fields

Per subject produce:

```text
overall_direction
BUY / HOLD / SELL

directional_balance
BUY x : SELL y

hold_lean
BUY_LEAN / NEUTRAL / SELL_LEAN / NOT_HOLD

confidence
low / medium / high or repository-native equivalent

business_thesis_context
earnings_context
market_expectation_context
valuation_context
price_timing_context
risk_context

buy_drivers
sell_drivers
core_judgment
```

No hidden factor scores.

---

# 7. Directional balance contract

Required:

```text
BUY + SELL = 10
increment = 0.5
```

Label:

```text
BUY if BUY >= 6.0
SELL if SELL >= 6.0
HOLD otherwise
```

HOLD lean:

```text
5.5 : 4.5 → BUY_LEAN
5.0 : 5.0 → NEUTRAL
4.5 : 5.5 → SELL_LEAN
```

Balance is a coarse summary of judgment.

It is not:
- probability
- expected return
- confidence percentage
- formulaic score

---

# 8. Overall direction vs current entry

Lock semantics:

```text
overall_direction
= integrated current directional attractiveness of the stock

new_buyer_view
= whether a new position is attractive at the CURRENT price/setup

holder_view
= whether an existing holder's investment logic remains holdable/review/reduce
```

Therefore valid:

```text
overall_direction = BUY
new_buyer = WAIT
```

Renderer must make that distinction explicit.

Preferred:

```text
🧠 종합 방향: BUY
판단 균형: BUY 6.0 : SELL 4.0
현재 신규진입: WAIT
```

Hard:

```text
TOP_LABEL_ENTRY_STANCE_AMBIGUITY = 0
```

---

# 9. New-buyer view

Per subject:

```text
ATTRACTIVE
WAIT
AVOID
```

May contain:

```text
pullback_entry_zone
breakout_confirmation_level
preferred_entry_mode
```

Preferred entry mode:

```text
PULLBACK
CONFIRMATION
BOTH
NONE
```

Preserve both support/pullback and breakout/confirmation when both are valid.

Do not force the model to choose one numeric level.

---

# 10. AVOID semantics

For:

```text
new_buyer = AVOID
```

user-facing text must NOT say:

```text
진입 검토 구간
```

Instead:

```text
현재 신규진입은 피합니다.
재검토 가격 조건: ...
```

A supported price level may remain visible,
but must not sound like an immediate buy instruction.

Required:

```text
AVOID_RENDERED_AS_ACTIONABLE_ENTRY = 0
```

---

# 11. Same resistance, two scenarios

A verified resistance may legitimately be:

```text
holder trim/review zone
and
new-buyer breakout confirmation
```

Render scenario semantics:

```text
holder:
resistance rejection / failure
→ expectation and valuation reassessment

new buyer:
successful breakout / configured confirmation
→ trend-entry reassessment
```

Do not render the same number with contradictory unexplained instructions.

Required:

```text
SAME_LEVEL_SCENARIO_AMBIGUITY = 0
```

---

# 12. Holder view

Per subject:

```text
HOLDABLE
REVIEW
REDUCE
```

May include:

```text
upside_trim_review_zone
downside_price_review
business_invalidation_condition
```

These are distinct.

`upside_trim_review_zone` means:

```text
reassess valuation, expectations, and updated earnings here
```

not:

```text
automatic sell target
```

No invented stop-loss.

---

# 13. Price provenance

All rendered numeric price scenarios must come from verified:
- packet-owned technical structure
- stored price rules
- verified registered support/resistance
- verified confirmation/warning/invalidation

Forbidden:
- arbitrary discount
- round-number guess
- invented technical level
- unsafe extrapolation
- target-like hallucination

Required:

```text
UNSUPPORTED_PRICE_NUMERIC = 0
```

---

# 14. Sector-aware Unknown policy

General:

```text
Unknown != SELL evidence
```

Unknown normally affects:
- confidence
- actionability
- need for confirmation

Sector-normal characteristics do not automatically become directional penalties.

Examples:

```text
biotech cash burn
!= automatic SELL

memory low forward PER near cycle peak
!= automatic BUY

ADR/security-basis unknown
!= automatic SELL

AI/HPC capex
requires economic-conversion context
```

---

# 15. US-specific audits

Mandatory targeted review:

```text
MU
RXRX
SKHY
WRD
CPNG
SNDK
```

Purpose:
- MU: cycle/expectations vs strong HBM/FCF
- RXRX: sector-normal burn vs genuine deterioration
- SKHY: verified ADR/security risk vs valuation Unknown
- WRD: Unknown vs directional penalty
- CPNG/SNDK: HOLD lean stability

Do not hardcode outcomes.

---

# 16. KR-specific safety

For KR8 preserve:
- six-digit ticker identity
- official filing attribution
- preliminary vs formal financial-statement distinction
- total/common/parent income distinction
- financial currency
- safe EPS/BVPS basis
- safe PER/PBR/fPER/fPBR
- supply as Flow/Positioning only
- exact price/supply as_of_date

Do not:
- infer missing FCF/ROIC from preliminary results
- annualize one quarter EPS into PER
- reverse-engineer per-share values
- let foreign/institution flow alone strengthen/weaken business thesis

---

# 17. KR price/supply interpretation

Where packet has supply:

```text
today
5-day
20-day
foreign ownership
score / quality / primary signal where native
```

Use only as:
- current positioning
- timing/context

Never as standalone fundamental thesis change.

Price structure may influence:
- entry timing
- current directional balance

but must not automatically modify:
- business thesis state

---

# 18. Cross-market accounting/security basis

US/foreign:
- ADR/ADS/ordinary share basis safe
- no unsafe per-share recomputation

KR:
- common/parent attribution safe
- official preliminary-result limitations respected

If basis is uncertain:

```text
confidence ↓
unsafe valuation inference blocked
```

not:

```text
automatic SELL
```

---

# 19. Phase A — first blind 22-subject run

Run all 22 once.

Before fresh balance is frozen, the model must NOT see:
- prior accepted decision
- prior balance
- manual reference answer
- another subject's decision result

After fresh candidate freeze,
prior accepted may be used only for delta/adjudication diagnostics.

Required:

```text
PRIOR_ACCEPTED_VISIBLE_BEFORE_FRESH_BALANCE = 0
```

---

# 20. First-run output

For each subject capture:

```text
evidence fingerprint
overall direction
balance
lean
confidence

business context
earnings context
expectations context
valuation context
price/timing context
risk context

BUY drivers
SELL drivers

new-buyer stance
pullback zone
confirmation
preferred entry mode

holder stance
trim/review zone
downside review
business invalidation

re-evaluation up
re-evaluation down
```

Validate 22/22.

---

# 21. Phase B — three fresh same-evidence runs

After the first run is structurally valid,
execute three fresh independent runs:

```text
A
B
C
```

Exact same:
- evidence
- contract
- schema
- model/runtime class

No:
- cross-run visibility
- prompt change
- schema change
- selected reruns after observing result
- majority voting

Required:

```text
CROSS_EXECUTION_DECISION_VISIBILITY = 0
PROMPT_SCHEMA_CHANGED_BETWEEN_RUNS = 0
POST_RESULT_TUNING = 0
```

---

# 22. Stability measurements

Per subject compare A/B/C:

```text
label sequence
balance sequence
max balance distance
lean sequence
confidence sequence
new-buyer stance sequence
holder stance sequence
entry-mode sequence
pullback zone
confirmation
trim zone
downside review
```

Do not average away disagreement.

---

# 23. Stability classification

Classify:

```text
STABLE

BOUNDARY_UNCERTAINTY

UNSTABLE
```

Suggested:

```text
STABLE
balance spread <= 0.5
no label change
no BUY_LEAN↔SELL_LEAN flip
no material action-context change

BOUNDARY_UNCERTAINTY
balance spread <= 1.0
difference occurs at real threshold/boundary
no extreme reversal

UNSTABLE
balance spread >= 1.5
or BUY↔SELL reversal
or unexplained BUY_LEAN↔SELL_LEAN flip
or ATTRACTIVE↔AVOID reversal
or HOLDABLE↔REDUCE reversal on identical evidence without explainable boundary
```

---

# 24. HOLD lean diagnostics

A stable `HOLD` label is not sufficient.

Example:

```text
5.5:4.5 HOLD
→ 4.5:5.5 HOLD
```

is a meaningful directional flip.

Record:

```text
BUY_LEAN_TO_SELL_LEAN
SELL_LEAN_TO_BUY_LEAN
```

Required:

```text
UNEXPLAINED_HOLD_LEAN_FLIP = 0
```

for promotion candidacy.

---

# 25. User-action-context stability

Track independently:

```text
new-buyer:
ATTRACTIVE / WAIT / AVOID

holder:
HOLDABLE / REVIEW / REDUCE
```

A stable top label with unstable action context must be surfaced.

Example:

```text
HOLD / HOLD / HOLD
but
ATTRACTIVE / WAIT / AVOID
```

is not considered fully stable.

---

# 26. Price-scenario stability

Numeric price structures should be primarily deterministic.

Compare:
- exact equality
- overlap
- same verified basis, different selection
- unsupported divergence

Allow:

```text
VALID_SELECTION_VARIANCE
```

when multiple verified supports/resistances exist.

Do not allow:
- unsupported new number in one run
- different numeric source without evidence

---

# 27. Cross-market semantic consistency

Audit US vs KR for the same concept:

```text
high market expectations
valuation stretch
support proximity
resistance proximity
confirmation achieved
warning/invalidation breach
Unknown valuation
sector-normal cash burn/capex
positioning/supply
```

Consistency means:
- same definition
- same safety rules
- sector-appropriate interpretation

Not:
- same decision distribution

---

# 28. Full 22-message renderer

Render exact user-facing messages for all 22.

Required top structure:

```text
🧠 종합 방향
판단 균형
판단 방향 if HOLD
현재 신규진입

🎯 핵심 판단

🆕 신규진입 관점

💼 보유자 관점

🔄 재평가 조건
```

Then factual detail body.

Accepted plan is the sole judgment authority.

Detailed body owns facts, not independent judgment state.

Required:

```text
MESSAGE_INTERNAL_CONTRADICTION = 0
SUBSTANTIVE_REPETITION = 0
```

---

# 29. Separate US/KR message previews

Create:
- US14 combined exact preview
- KR8 combined exact preview
- ALL22 compact decision table

Do not send to production.

Optional TEST sink is not necessary for this task unless explicitly requested later.

---

# 30. Natural-proof relationship

The KR orchestration repair is currently:

```text
READY_FOR_NATURAL_PROOF
```

not yet:

```text
NATURAL_PRODUCTION_PROVEN
```

Therefore even if this 22-subject shadow task is excellent:

```text
DO NOT promote the new decision structure yet.
```

Later promotion review requires:
- repaired KR natural live success
- repaired US natural live success
- all22 stability acceptance

---

# 31. Natural live success targets later

KR:

```text
AI market             1
stock V2              8
fallback              0
duplicate             0
```

US:

```text
AI market             1
stock V2              14
fallback              0
duplicate             0
```

Markets must report independently.

Do not block a completed US report waiting for KR close.

---

# 32. Promotion candidate gates

Required before promotion review:

```text
ALL22_FIRST_RUN_VALIDATED = 22

RUN_A_VALIDATED = 22
RUN_B_VALIDATED = 22
RUN_C_VALIDATED = 22

SAME_EVIDENCE_BUY_SELL_REVERSAL_COUNT = 0

UNEXPLAINED_HOLD_LEAN_FLIP_COUNT = 0

UNSTABLE_TICKER_COUNT = 0

UNSUPPORTED_PRICE_NUMERIC = 0

MESSAGE_INTERNAL_CONTRADICTION = 0

UNKNOWN_AUTOMATIC_SELL_PENALTY = 0

SECTOR_NORMAL_ATTRIBUTE_AUTOMATIC_DIRECTIONAL_PENALTY = 0

KR_ACCOUNTING_VALUATION_SAFETY = PASS

ADR_SECURITY_BASIS_SAFETY = PASS
```

Boundary uncertainty may remain if explicit and adjudication-ready.

---

# 33. Required reports

Create:

1. `docs/reports/20260903-uskr22-phase2-source-lock.md`
2. `docs/reports/20260903-uskr22-structured-autonomy-contract.md`
3. `docs/reports/20260903-uskr22-first-shadow-decisions.md`
4. `docs/reports/20260903-uskr22-sector-aware-audit.md`
5. `docs/reports/20260903-uskr22-kr-accounting-valuation-audit.md`
6. `docs/reports/20260903-uskr22-adr-security-basis-audit.md`
7. `docs/reports/20260903-uskr22-price-scenario-audit.md`
8. `docs/reports/20260903-uskr22-run-a.md`
9. `docs/reports/20260903-uskr22-run-b.md`
10. `docs/reports/20260903-uskr22-run-c.md`
11. `docs/reports/20260903-uskr22-stability-comparison.md`
12. `docs/reports/20260903-uskr22-hold-lean-diagnostics.md`
13. `docs/reports/20260903-uskr22-action-context-stability.md`
14. `docs/reports/20260903-uskr22-cross-market-consistency.md`
15. `docs/reports/20260903-uskr22-message-quality.md`
16. `docs/reports/20260903-uskr22-promotion-readiness.md`
17. `docs/reports/20260903-uskr22-artifact-index.md`

Machine-readable:

```text
20260903-uskr22-first-run.json
20260903-uskr22-run-a.json
20260903-uskr22-run-b.json
20260903-uskr22-run-c.json
20260903-uskr22-stability.json
20260903-uskr22-price-scenarios.json
20260903-uskr22-proof.json
```

Exact message files:
- one per subject
- US14 combined preview
- KR8 combined preview

---

# 34. Required gates

Set exactly:

```text
PHASE2_BASE_CONTAINS_KR_LIVE_REPAIR =
PASS / FAIL

KR_REPAIR_BASE =
90cc52231c7343056c853c355ea90dfea10de25b / OTHER

US_SOURCE_PACKET =
2026-09-03-us-run-53-055ae8ea01f6

KR_SOURCE_PACKET =
2026-09-03-kr-run-54-f19bb379daa7

US_COUNT =
14 / OTHER

KR_COUNT =
8 / OTHER

TOTAL_COUNT =
22 / OTHER

FRESH_FACT_COLLECTION =
0 / NONZERO

CROSS_MARKET_FACT_LEAKAGE =
0 / NONZERO

CROSS_GENERATION_FACT_LEAKAGE =
0 / NONZERO

FIXED_FACTOR_WEIGHTING =
0 / NONZERO

SUBSCORE_ARITHMETIC =
0 / NONZERO

BALANCE_AS_PROBABILITY =
0 / NONZERO

UNKNOWN_AUTOMATIC_SELL_PENALTY =
0 / NONZERO

SECTOR_NORMAL_ATTRIBUTE_AUTOMATIC_DIRECTIONAL_PENALTY =
0 / NONZERO

TOP_LABEL_ENTRY_STANCE_AMBIGUITY =
0 / NONZERO

AVOID_RENDERED_AS_ACTIONABLE_ENTRY =
0 / NONZERO

SAME_LEVEL_SCENARIO_AMBIGUITY =
0 / NONZERO

PRIOR_ACCEPTED_VISIBLE_BEFORE_FRESH_BALANCE =
0 / NONZERO

ALL22_FIRST_RUN_VALIDATED =
22 / OTHER

RUN_A_VALIDATED =
22 / OTHER

RUN_B_VALIDATED =
22 / OTHER

RUN_C_VALIDATED =
22 / OTHER

CROSS_EXECUTION_DECISION_VISIBILITY =
0 / NONZERO

PROMPT_SCHEMA_CHANGED_BETWEEN_RUNS =
0 / NONZERO

POST_RESULT_TUNING =
0 / NONZERO

SAME_EVIDENCE_BUY_SELL_REVERSAL_COUNT =
...

UNEXPLAINED_HOLD_LEAN_FLIP_COUNT =
...

BOUNDARY_UNCERTAINTY_COUNT =
...

UNSTABLE_TICKER_COUNT =
...

UNSUPPORTED_PRICE_NUMERIC =
0 / NONZERO

MESSAGE_INTERNAL_CONTRADICTION =
0 / NONZERO

SUBSTANTIVE_REPETITION =
0 / NONZERO

KR_ACCOUNTING_VALUATION_SAFETY =
PASS / FAIL

ADR_SECURITY_BASIS_SAFETY =
PASS / FAIL

PRODUCTION_DECISION_MUTATION =
0 / NONZERO

PRODUCTION_RENDERER_CHANGE =
0 / NONZERO

PRODUCTION_SEND =
0 / NONZERO

MAIN_MERGE =
0 / NONZERO

PROMOTION_READINESS =
READY_FOR_PROMOTION_REVIEW /
NEEDS_MORE_SHADOW_WORK /
NOT_READY
```

---

# 35. Completion response

Return:

```text
BASE =
...

SOURCE LOCK =
US ...
KR ...

FIRST ALL22 RUN =
US14 distribution
KR8 distribution
ALL22 distribution

US14 DECISIONS =
ticker / label / balance / lean / new-buyer / holder

KR8 DECISIONS =
ticker / label / balance / lean / new-buyer / holder

STABILITY =
stable ...
boundary ...
unstable ...

MATERIAL LABEL/BALANCE VARIANCE =
...

HOLD LEAN VARIANCE =
...

ACTION-CONTEXT VARIANCE =
...

PRICE-SCENARIO QUALITY =
...

SECTOR / ACCOUNTING / ADR AUDITS =
...

MESSAGE QUALITY =
...

PROMOTION READINESS =
...

KR NATURAL PROOF STATUS =
PENDING

PRODUCTION MUTATION = 0
PRODUCTION SEND = 0
MAIN MERGE = 0

ZIP = ...
ZIP_SHA256 = ...
```

---

# 36. Completion ZIP

Create:

`20260903-post-kr-repair-uskr22-structured-autonomy-shadow-program-bundle.zip`

Include:
- exact instructions
- implementation/shadow schema diffs
- source locks/fingerprints
- 22 first-run decisions
- A/B/C stability artifacts
- 22 exact messages
- US/KR previews
- price provenance
- sector/accounting/security audits
- comparison reports
- machine-readable JSON
- artifact index
- tests
- secret scan

Exclude:
- credentials
- auth/session tokens
- recipient IDs
- state DB contents
- hidden chain-of-thought

Compute SHA-256.

---

# 37. Final principle

The KR live transport defect is engineering-closed enough to continue shadow judgment work,
but natural production proof is still required before promotion.

Now evaluate the judgment architecture on the whole monitored universe:

```text
same structure
same safety contract
sector-aware interpretation
US14 + KR8
22 subjects
three same-evidence executions
no production mutation
```

Do not tune the model toward a predetermined decision distribution.
