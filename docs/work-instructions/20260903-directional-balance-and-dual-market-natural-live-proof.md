# thesis-monitor — Directional Balance + 2026-09-03 Dual Natural-Live Proof
## BUY:SELL directional balance
## HOLD is current neutrality, not automatic prior-decision carry-forward
## Same-evidence repeated-run variance detection
## Temporarily suppress unresolved night-futures user-facing section
## Observe both US morning and KR close natural cycles

---

# 0. Metadata

- Repository: `sskim-ai/thesis-monitor`
- Work date: `2026-09-03 KST`
- Task class: `DECISION_CONTRACT_REPAIR + TEMPORARY_MARKET_UI_GUARD + DUAL_NATURAL_LIVE_OBSERVATION`
- Production Assist: preserve `OFF`
- Automated trading/order sizing: `0`
- Decision policy retuning outside this explicit balance contract: `0`
- Production historical resend: `0`
- Manual natural-job trigger: `0`
- Scheduler timing/ownership change: `0`
- Night-futures date/session architecture repair: `0` in this task
- Night-futures user-facing display: temporarily suppressed until the separate session-date module is completed
- Track commits: required
- Final natural-live observation: required

Reference current safe line from the prior four-track program:

```text
main/operating reference =
f20ff4217a5897bdf30286216c6b425287235a21

runtime code reference =
deab50a122075b5fc710e97b74d9fbb63f2ac1e4
```

These are references only.

At task start:

```text
git fetch origin
resolve actual latest origin/main
resolve operating HEAD
resolve runtime/deployed SHA
verify clean worktrees
verify ancestry
```

---

# 1. Preserve already-working repairs

Do not regress:

```text
Codex natural runtime-state repair
Codex DNS/network preflight/retry repair
V2 natural path repair
daily-review semantic/provenance convergence
canonical product/model identifier provenance
CPNG/HUT technical recovery
US nominal Treasury 3Y/5Y/10Y/30Y primary rate block
common V2 stock disclaimer removal
accepted_decision_plan ownership
exactly-once delivery
```

Required:

```text
PREVIOUS_SAFE_REPAIRS_REGRESSION = 0
```

---

# 2. Night futures are explicitly out of scope

The KRX/Kiwoom date/session mapping remains unresolved.

The latest read-only verdict was:

```text
INSUFFICIENT_EVIDENCE
```

The production date/session contract must NOT be modified in this task.

For 2026-09-03 US morning message:

```text
temporarily suppress the user-facing night-futures section
```

rather than rendering a potentially misdated section.

Do not delete:
- KRX collector
- history store
- raw evidence
- D/W/M architecture

Only the user-facing inclusion gate is temporarily disabled.

Required:

```text
NIGHT_FUTURES_SESSION_ARCHITECTURE_CHANGED = 0
NIGHT_FUTURES_USER_FACING_TEMP_SUPPRESSED = PASS
```

Night futures must not affect US natural-live PASS/FAIL in this task.

---

# 3. New decision concept: directional balance

Each fresh V2 decision must include a structured:

```text
BUY : SELL directional balance
```

Example:

```text
BUY 6 : SELL 4
```

This is NOT:
- probability
- expected return
- target-price odds
- fixed-factor weighted score

It is:

```text
the relative directional force of the current evidence toward owning/buying
versus avoiding/selling, after considering business, earnings, expectations,
valuation, risk, and price/timing evidence.
```

Required user-facing warning in architecture docs:

```text
directional balance is not probability
```

Do not add that explanatory disclaimer to every Telegram stock message unless needed.

---

# 4. Balance scale

Use a normalized 10-point pair:

```text
buy_balance + sell_balance = 10
```

Allow:

```text
integer or 0.5 increments
```

Prefer the coarsest precision that is stable and interpretable.

Examples:

```text
6 : 4
5.5 : 4.5
5 : 5
4 : 6
```

Hard:

```text
BALANCE_SUM_NOT_10 = 0
FALSE_BALANCE_PRECISION = 0
```

---

# 5. Label derivation

Normative anchors:

```text
BUY 6 : SELL 4
→ BUY

BUY 5 : SELL 5
→ HOLD

BUY 4 : SELL 6
→ SELL
```

Preferred deterministic neutral band:

```text
BUY if buy_balance >= 6
SELL if sell_balance >= 6
HOLD otherwise
```

Therefore:

```text
5.5 : 4.5
→ HOLD

4.5 : 5.5
→ HOLD
```

Do not use prior accepted label to convert a neutral balance back into BUY or SELL.

Required:

```text
HOLD_MEANS_PRIOR_DECISION_CARRY_FORWARD = 0
```

If the repository chooses a slightly different neutral band:
it must be explicitly documented and regression-tested against the user anchors above.
The user anchors themselves are non-negotiable.

---

# 6. HOLD semantics

HOLD means:

```text
current evidence does not show a sufficiently clear directional advantage
toward BUY or SELL
```

It does NOT mean:

```text
keep whatever the prior accepted decision was
```

Example:

```text
prior:
BUY 6 : SELL 4
→ BUY

current:
BUY 5 : SELL 5
→ HOLD
```

This transition is allowed when current evidence supports neutrality.

Required:

```text
PRIOR_BUY_FORCES_CURRENT_HOLD_TO_BUY = 0
PRIOR_SELL_FORCES_CURRENT_HOLD_TO_SELL = 0
```

---

# 7. Candidate schema

Extend V2 candidate contract with repository-native equivalents of:

```json
{
  "decision": "BUY|HOLD|SELL",
  "directional_balance": {
    "buy": 6.0,
    "sell": 4.0
  },
  "buy_drivers": [],
  "sell_drivers": [],
  "balance_summary": ""
}
```

`buy_drivers` and `sell_drivers` must bind to evidence.

Do not create a new unstructured free-text scoring subsystem.

---

# 8. Accepted plan schema

Persist in `accepted_decision_plan`:

```text
accepted decision
accepted buy balance
accepted sell balance
accepted buy drivers
accepted sell drivers
evidence fingerprint
adjudication source/status
```

Raw candidate balance is not downstream authority.

Required:

```text
RAW_CANDIDATE_BALANCE_USED_AS_FINAL = 0
```

---

# 9. Message rendering

For every V2 accepted stock message:

```text
🧠 AI 분석 판단: BUY/HOLD/SELL
판단 균형: BUY 6 : SELL 4
판단 확신도: ...
```

For HOLD:

```text
🧠 AI 분석 판단: HOLD
판단 균형: BUY 5 : SELL 5
```

Do not imply the ratio is a probability.

Common order/auto-trading disclaimer remains removed.

Required:

```text
DIRECTIONAL_BALANCE_VISIBLE_COUNT =
all accepted-ready stock messages
```

---

# 10. Decision logic remains evidence-first

Do NOT implement:

```text
business 30%
valuation 20%
technical 10%
...
```

or any fixed universal factor weighting.

The model reasons over the evidence holistically and emits the directional balance.

Validators must ensure:
- drivers have evidence
- no unsupported number drives the balance
- technical/supply evidence does not dominate business/earnings/valuation without justification

Hard:

```text
FIXED_FACTOR_WEIGHTED_SCORE_INTRODUCED = 0
```

---

# 11. Adjudication trigger

Adjudication should consider:

```text
prior accepted label/balance
fresh candidate label/balance
evidence fingerprint delta
material evidence delta
balance delta
```

Adjudication is required when:
- label changes materially
- balance crosses BUY/HOLD/SELL band
- balance moves materially with unchanged or nonmaterial evidence
- current decision conflicts with a major configured thesis condition

Do not adjudicate merely because the exact ratio changes by a trivial amount.

---

# 12. Same-evidence repeated-run variance

This is mandatory.

For frozen control packets with identical:

```text
packet identity
evidence fingerprint
candidate input fingerprint
```

run at least:

```text
3 independent fresh model executions
```

in a non-production namespace.

For each ticker record:

```text
run 1 balance/label
run 2 balance/label
run 3 balance/label
```

No production sends.

---

# 13. Balance-variance metric

Because balances sum to 10, use:

```text
balance_distance =
abs(buy_balance_run_A - buy_balance_run_B)
```

Equivalent sell-side distance is redundant.

Classify:

```text
<= 0.5
MINOR_VARIANCE

1.0
MODERATE_VARIANCE

>= 1.5
MATERIAL_VARIANCE
```

Also classify:

```text
LABEL_STABLE
LABEL_BOUNDARY_CROSS
```

A label boundary cross under identical evidence is always review-worthy.

Required:

```text
SAME_EVIDENCE_LABEL_BOUNDARY_CROSS_COUNT = ...
```

---

# 14. Same-evidence accepted stability

Do not require the raw model candidate to be perfectly deterministic.

Instead require:

```text
accepted outcome
```

to be explainable and stable under the adjudication contract.

If repeated identical-evidence runs produce:

```text
6:4 BUY
5.5:4.5 HOLD
6:4 BUY
```

this is a boundary variance case.

The accepted contract must:
- expose the variance
- use adjudication
- not silently call all three identical

If repeated runs produce:

```text
8:2 BUY
5:5 HOLD
```

this is material variance and must block readiness until explained.

Required:

```text
UNEXPLAINED_SAME_EVIDENCE_ACCEPTED_DRIFT = 0
```

---

# 15. No majority-vote hack

Do NOT simply:

```text
run 3 times
pick majority label
```

as production decision logic.

Repeated runs are a diagnostic/calibration test.

Natural production remains:
- one candidate path
- adjudication as required
- one accepted plan

Hard:

```text
PRODUCTION_MODEL_MAJORITY_VOTING = 0
```

---

# 16. Prior balance vs current balance

For natural daily monitoring record:

```text
prior accepted balance
current candidate balance
current accepted balance
evidence delta
```

This makes transitions interpretable.

Example:

```text
prior:
BUY 6.0 : SELL 4.0

current:
BUY 5.0 : SELL 5.0

evidence delta:
expectation elevated
price confirmation lost

accepted:
HOLD 5.0 : 5.0
```

Do not automatically label this as investment-logic weakening.

---

# 17. Business thesis vs decision balance

Separate:

```text
business thesis change
earnings estimate impact
market expectations
valuation
price/timing
directional balance
```

A balance can move toward SELL because valuation/price worsens while business thesis remains unchanged.

Required:

```text
BALANCE_CHANGE_AUTOMATICALLY_CHANGES_BUSINESS_THESIS = 0
```

---

# 18. Track A — implementation target

Track A implements:
- candidate balance schema
- accepted plan balance schema
- label derivation
- HOLD semantics
- renderer balance line
- validators

Track A focused tests:
- 6:4 BUY
- 5:5 HOLD
- 4:6 SELL
- 5.5:4.5 HOLD
- prior BUY + current 5:5 → HOLD
- prior SELL + current 5:5 → HOLD
- sum=10
- no probability language
- no fixed weighted factor score

Required:

```text
TRACK_A_DIRECTIONAL_BALANCE = PASS
```

---

# 19. Track B — variance/adjudication target

Track B implements:
- balance delta fields
- same-evidence diagnostic harness
- label-boundary detection
- accepted drift reporting
- adjudication input updates

Use frozen controls:
- US run-51
- KR latest natural packet with complete V2-compatible evidence

Minimum:
```text
3 fresh executions per frozen control
```

Required:
- exact same evidence fingerprints
- per-run balances
- per-run labels
- candidate/accepted comparison
- no production send/state mutation

Set:

```text
TRACK_B_VARIANCE_ADJUDICATION = PASS
```

---

# 20. GOOGL mandatory control

Use the frozen GOOGL evidence that previously produced both:

```text
HOLD
BUY
```

under the same evidence fingerprint.

Require a specific report:

```text
GOOGL repeated fresh execution balances
GOOGL label boundary behavior
GOOGL adjudication result
GOOGL accepted stability
```

Set:

```text
GOOGL_SAME_EVIDENCE_DRIFT_EXPLAINED = PASS / FAIL
```

---

# 21. KR controls

Use at least:
- 000660
- 003690
- 005930
- 047810

to cover:
- valuation quality
- insurance holder logic
- risk/reward guard
- product identifier provenance

Directional balance must not weaken those validators.

---

# 22. Track C — temporary night-futures suppression

Until a separate session-date module resolves KRX vs Kiwoom date convention:

for US user-facing market messages:

```text
do not render the night-futures section
```

Do not delete or change:
- KRX raw collection
- history store
- D/W/M aggregation
- reconciliation artifacts

Implement as a temporary user-facing feature gate with explicit reason:

```text
SESSION_DATE_CONVENTION_PENDING
```

No user-facing warning line is required; omission is sufficient.

Required:

```text
US_NIGHT_FUTURES_USER_FACING_COUNT = 0
```

---

# 23. Track C — Treasury block stays

Preserve the user-approved primary US rates block:

```text
3Y / 5Y / 10Y / 30Y nominal Treasury
latest safe yield
+
previous valid observation delta in bp
```

Required:

```text
UST_3Y_5Y_10Y_30Y_BLOCK = PASS
REAL_YIELD_PRIMARY_USER_BLOCK_REINTRODUCED = 0
```

---

# 24. Track C — market message regression

US market message must still include:
- SPY/QQQ/IWM/SOXX/RSP
- market internals/relative strength
- sector strength/weakness
- 3Y/5Y/10Y/30Y Treasury block
- next checks

Night futures omitted temporarily.

KR market message unchanged except any ordinary fresh-data content.

Required:

```text
TRACK_C_MARKET_REGRESSION = PASS
```

---

# 25. Track D — pre-live integration

Before 2026-09-03 natural runs:

run:

```text
US production-equivalent
KR production-equivalent
```

Reference cohorts if unchanged:

```text
US = 14
KR = 8
```

Require:

```text
US context/candidate/accepted/explicit = 14/14/14/14
KR context/candidate/accepted/explicit = 8/8/8/8
fallback = 0
```

Each stock message must include:

```text
판단 균형: BUY x : SELL y
```

---

# 26. Test recipient integration

Use the existing dedicated TEST recipient.

No production recipient.

Use real Telegram transport.

Require:
- US test set exact
- KR test set exact
- duplicate 0
- no production-state mutation
- no night-futures user-facing section in US test market message

Hard:

```text
PRODUCTION_RECIPIENT_SEND = 0
PRODUCTION_DELIVERY_STATE_MUTATION = 0
```

---

# 27. 2026-09-03 US natural-live observation

Target:

```text
KST morning = 2026-09-03
US completed regular session = 2026-09-02
```

Read-only.

Do not manually trigger.

Capture:
- source-monitor run
- primary/backup/dispatcher
- packet/claim/cutoff
- network preflight
- Codex app-server
- model
- candidates
- accepted plans
- balances
- renderer
- validator
- delivery

Reference cohort if unchanged:

```text
14
```

---

# 28. US natural-live market checks

Require:
- canonical US session 2026-09-02
- market indices safe
- sector/relative facts safe
- Treasury 3Y/5Y/10Y/30Y block present
- night-futures block absent
- market final validation PASS

Set:

```text
US_NIGHT_FUTURES_SECTION_ABSENT = PASS
US_TREASURY_CURVE_PRESENT = PASS
```

---

# 29. US stock natural-live checks

For each ticker:
- decision
- accepted balance
- evidence fingerprint
- prior accepted balance
- evidence delta
- adjudication if required

Reference:
CORZ, CPNG, CRCL, GOOGL, HUT, IBM, MU, RXRX, SKHY, SNDK, TSLA, TSM, WRD, WULF.

Set:
```text
US_ACCEPTED_READY_COUNT
US_EXPLICIT_V2_COUNT
US_BALANCE_VISIBLE_COUNT
US_FALLBACK_COUNT
```

---

# 30. 2026-09-03 KR natural-live observation

Target:

```text
KRX regular session = 2026-09-03
KST close delivery = 2026-09-03
```

Read-only.

Reference cohort if unchanged:
- 000660
- 003690
- 005490
- 005930
- 010120
- 012450
- 047810
- 086280

Capture the same end-to-end path.

---

# 31. KR stock natural-live checks

For each:
- candidate
- accepted
- balance
- evidence delta
- adjudication
- explicit V2
- final validator
- delivery

Mandatory:
- 047810 identifier
- 000660 valuation-quality
- 005930 risk/reward
- 010120/012450 numerics

Set:
```text
KR_ACCEPTED_READY_COUNT
KR_EXPLICIT_V2_COUNT
KR_BALANCE_VISIBLE_COUNT
KR_FALLBACK_COUNT
```

---

# 32. Natural-live decision-change report

For US and KR, any accepted label change must report:

```text
ticker
prior label/balance
current label/balance
evidence fingerprint delta
material evidence delta
adjudication
business thesis changed? yes/no
valuation/expectation/price timing cause
```

Required:

```text
NATURAL_ACCEPTED_CHANGE_WITHOUT_EXPLANATION = 0
```

---

# 33. Natural-live balance interpretation

Do not overreact to:

```text
6.0:4.0 → 5.5:4.5
```

if label/logic remain explainable.

Do flag:

```text
8:2 → 5:5
```

with no material evidence delta.

Set:

```text
NATURAL_UNEXPLAINED_BALANCE_JUMP = 0 / NONZERO
```

---

# 34. Delivery

Preferred healthy counts if cohorts unchanged:

US:
```text
1 market + 14 stock = 15
```

KR:
```text
1 market + 8 stock = 9
```

Require:
- exactly once
- exact payload
- duplicate 0
- orphan 0
- unowned retry 0

---

# 35. Natural-live pass definitions

US:

```text
US_V2_NATURAL_LIVE = PASS
```

only if:
- source ready
- network preflight PASS
- model reached
- candidate 14
- accepted 14
- balance visible 14
- explicit V2 14
- fallback 0
- Treasury block present
- night-futures block absent
- exact payload/exactly once PASS
- material P1 0

KR:

```text
KR_V2_NATURAL_LIVE = PASS
```

only if:
- source ready
- network preflight PASS
- model reached
- candidate 8
- accepted 8
- balance visible 8
- explicit V2 8
- fallback 0
- exact payload/exactly once PASS
- material P1 0

---

# 36. Do not auto-repair after live failure

If either natural run fails:

```text
archive evidence
identify earliest failure
classify next repair
```

Do not patch during observation.

---

# 37. Required architecture docs

Create/update:

```text
docs/architecture/V2_DIRECTIONAL_BALANCE_CONTRACT.md
docs/architecture/V2_HOLD_NEUTRALITY_CONTRACT.md
docs/architecture/V2_SAME_EVIDENCE_VARIANCE_CONTRACT.md
docs/architecture/V2_ADJUDICATION_BALANCE_CONTRACT.md
docs/architecture/US_MARKET_TEMPORARY_NIGHT_FUTURES_SUPPRESSION.md
docs/architecture/DECISION_ACCEPTED_OWNERSHIP.md
```

---

# 38. Required reports — implementation

1. `docs/reports/20260903-directional-balance-schema.md`
2. `docs/reports/20260903-directional-balance-label-derivation.md`
3. `docs/reports/20260903-hold-neutrality-controls.md`
4. `docs/reports/20260903-balance-renderer-controls.md`
5. `docs/reports/20260903-same-evidence-variance-harness.md`
6. `docs/reports/20260903-googl-same-evidence-balance-control.md`
7. `docs/reports/20260903-kr-same-evidence-balance-controls.md`
8. `docs/reports/20260903-adjudication-balance-controls.md`
9. `docs/reports/20260903-night-futures-temp-suppression.md`
10. `docs/reports/20260903-market-message-regression.md`
11. `docs/reports/20260903-us-production-equivalent-balance.md`
12. `docs/reports/20260903-kr-production-equivalent-balance.md`
13. `docs/reports/20260903-test-recipient-balance-integration.md`

---

# 39. Required reports — natural live

US:
14. `docs/reports/20260903-us-natural-run-identity.md`
15. `docs/reports/20260903-us-natural-v2-balance-proof.md`
16. `docs/reports/20260903-us-natural-market-message-proof.md`
17. `docs/reports/20260903-us-natural-delivery-proof.md`

KR:
18. `docs/reports/20260903-kr-natural-run-identity.md`
19. `docs/reports/20260903-kr-natural-v2-balance-proof.md`
20. `docs/reports/20260903-kr-natural-market-message-proof.md`
21. `docs/reports/20260903-kr-natural-delivery-proof.md`

Combined:
22. `docs/reports/20260903-dual-market-decision-change-audit.md`
23. `docs/reports/20260903-dual-natural-live-proof.md`
24. `docs/reports/20260903-dual-natural-live-artifact-index.md`

Machine-readable:

```text
docs/reports/20260903-directional-balance-controls.json
docs/reports/20260903-same-evidence-variance.json
docs/reports/20260903-us-natural-live.json
docs/reports/20260903-kr-natural-live.json
docs/reports/20260903-dual-natural-live.json
```

---

# 40. Required gates

Set exactly:

```text
BASE_SHA =
...

PREVIOUS_SAFE_REPAIRS_REGRESSION =
0 / NONZERO

TRACK_A_COMMIT =
...

BALANCE_SUM_NOT_10 =
0 / NONZERO

FALSE_BALANCE_PRECISION =
0 / NONZERO

HOLD_MEANS_PRIOR_DECISION_CARRY_FORWARD =
0 / NONZERO

PRIOR_BUY_FORCES_CURRENT_HOLD_TO_BUY =
0 / NONZERO

PRIOR_SELL_FORCES_CURRENT_HOLD_TO_SELL =
0 / NONZERO

RAW_CANDIDATE_BALANCE_USED_AS_FINAL =
0 / NONZERO

FIXED_FACTOR_WEIGHTED_SCORE_INTRODUCED =
0 / NONZERO

TRACK_A_DIRECTIONAL_BALANCE =
PASS / FAIL

TRACK_B_COMMIT =
...

SAME_EVIDENCE_LABEL_BOUNDARY_CROSS_COUNT =
...

UNEXPLAINED_SAME_EVIDENCE_ACCEPTED_DRIFT =
0 / NONZERO

PRODUCTION_MODEL_MAJORITY_VOTING =
0 / NONZERO

GOOGL_SAME_EVIDENCE_DRIFT_EXPLAINED =
PASS / FAIL

BALANCE_CHANGE_AUTOMATICALLY_CHANGES_BUSINESS_THESIS =
0 / NONZERO

TRACK_B_VARIANCE_ADJUDICATION =
PASS / FAIL

TRACK_C_COMMIT =
...

NIGHT_FUTURES_SESSION_ARCHITECTURE_CHANGED =
0 / NONZERO

NIGHT_FUTURES_USER_FACING_TEMP_SUPPRESSED =
PASS / FAIL

US_NIGHT_FUTURES_USER_FACING_COUNT =
0 / NONZERO

UST_3Y_5Y_10Y_30Y_BLOCK =
PASS / FAIL

REAL_YIELD_PRIMARY_USER_BLOCK_REINTRODUCED =
0 / NONZERO

TRACK_C_MARKET_REGRESSION =
PASS / FAIL

TRACK_D_COMMIT =
...

US_PRODUCTION_EQUIVALENT =
PASS / FAIL

KR_PRODUCTION_EQUIVALENT =
PASS / FAIL

PRODUCTION_RECIPIENT_SEND =
0 / NONZERO

PRODUCTION_DELIVERY_STATE_MUTATION =
0 / NONZERO

TEST_RECIPIENT_INTEGRATION =
PASS / FAIL

US_CANONICAL_SESSION_DATE =
2026-09-02 / OTHER

US_ACCEPTED_READY_COUNT =
...

US_EXPLICIT_V2_COUNT =
...

US_BALANCE_VISIBLE_COUNT =
...

US_FALLBACK_COUNT =
...

US_NIGHT_FUTURES_SECTION_ABSENT =
PASS / FAIL

US_TREASURY_CURVE_PRESENT =
PASS / FAIL

US_EXACT_PAYLOAD =
PASS / FAIL

US_EXACTLY_ONCE =
PASS / FAIL

US_V2_NATURAL_LIVE =
PASS / PARTIAL_SAFE / FAIL

KR_CANONICAL_SESSION_DATE =
2026-09-03 / OTHER

KR_ACCEPTED_READY_COUNT =
...

KR_EXPLICIT_V2_COUNT =
...

KR_BALANCE_VISIBLE_COUNT =
...

KR_FALLBACK_COUNT =
...

KR_EXACT_PAYLOAD =
PASS / FAIL

KR_EXACTLY_ONCE =
PASS / FAIL

KR_V2_NATURAL_LIVE =
PASS / PARTIAL_SAFE / FAIL

NATURAL_ACCEPTED_CHANGE_WITHOUT_EXPLANATION =
0 / NONZERO

NATURAL_UNEXPLAINED_BALANCE_JUMP =
0 / NONZERO

OPEN_P0 =
...

OPEN_MATERIAL_P1 =
...

OPEN_P2 =
...

DUAL_MARKET_READY =
PASS / FAIL
```

---

# 41. Completion response

Return:

```text
WORK_INSTRUCTION_COMMIT = ...
BASE_SHA = ...

TRACK_A_COMMIT = ...
TRACK_A_DIRECTIONAL_BALANCE = ...

BALANCE_CONTRACT =
BUY >= ...
HOLD band ...
SELL >= ...

TRACK_B_COMMIT = ...
TRACK_B_VARIANCE_ADJUDICATION = ...
GOOGL_SAME_EVIDENCE_DRIFT_EXPLAINED = ...
SAME_EVIDENCE_LABEL_BOUNDARY_CROSS_COUNT = ...

TRACK_C_COMMIT = ...
NIGHT_FUTURES_USER_FACING_TEMP_SUPPRESSED = ...
UST_3Y_5Y_10Y_30Y_BLOCK = ...

TRACK_D_COMMIT = ...

FINAL_MAIN = ...
ORIGIN_MAIN = ...
OPERATING = ...
RUNTIME_CODE_SHA = ...

US_NATURAL =
run ...
packet ...
source ...
network ...
model ...
candidate ...
accepted ...
balances ...
fallback ...
market ...
delivery ...
US_V2_NATURAL_LIVE ...

US_DECISIONS =
CORZ ...
CPNG ...
CRCL ...
GOOGL ...
HUT ...
IBM ...
MU ...
RXRX ...
SKHY ...
SNDK ...
TSLA ...
TSM ...
WRD ...
WULF ...

KR_NATURAL =
run ...
packet ...
source ...
network ...
model ...
candidate ...
accepted ...
balances ...
fallback ...
market ...
delivery ...
KR_V2_NATURAL_LIVE ...

KR_DECISIONS =
000660 ...
003690 ...
005490 ...
005930 ...
010120 ...
012450 ...
047810 ...
086280 ...

DECISION_CHANGES =
ticker / prior label+balance / current label+balance / evidence delta / adjudication ...

NATURAL_UNEXPLAINED_BALANCE_JUMP = ...

OPEN_P0 = ...
OPEN_MATERIAL_P1 = ...
OPEN_P2 = ...

DUAL_MARKET_READY =
PASS / FAIL

NEXT_ACTION =
WAIT_FOR_NIGHT_FUTURES_SESSION_MODULE /
BOUNDED_REPAIR /
NO_ACTION

ZIP = ...
ZIP_SHA256 = ...
```

---

# 42. Mandatory completion ZIP

Create:

`20260903-directional-balance-and-dual-market-natural-live-proof-bundle.zip`

Include:
- exact master instruction
- all track instructions
- track commits/diffs
- balance schema/renderer tests
- HOLD neutrality tests
- same-evidence 3-run controls
- GOOGL drift analysis
- KR drift controls
- temporary night-futures suppression proof
- Treasury regression
- US/KR production-equivalent results
- TEST recipient receipts
- US natural run evidence
- KR natural run evidence
- exact sanitized messages
- decision-change audit
- delivery proof
- CI/main/runtime evidence
- machine-readable JSON
- artifact index

Exclude:
- recipient IDs
- tokens/auth headers
- Codex credentials/state DB contents
- account identifiers
- secrets
- hidden chain-of-thought

Compute SHA-256.

---

# 43. Final principle

For the next live cycle:

```text
HOLD = current neutrality
```

not:

```text
keep the previous label
```

The user should see:

```text
BUY/HOLD/SELL
+
BUY:SELL directional balance
```

The balance is not probability.

Repeated fresh executions with identical evidence are a diagnostic for model variance,
not a majority-vote production strategy.

Until the KRX/Kiwoom night-session date convention is resolved:

```text
do not show night futures to the user
```

Tomorrow's objective is to prove the repaired V2 decision path naturally on both:

```text
US morning
KR close
```

with no fallback and with transparent directional balance.
