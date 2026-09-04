# thesis-monitor — Validator Ownership Repair + US Live Coexistence Guard
## Fix the two remaining false-positive ownership rules
## Preserve Structured Autonomy judgment logic
## Protect the 2026-09-04 08:00 KST US natural monitoring run from shadow-model interference
## Then run a completely fresh ALL22 + clean A/B/C stability proof

---

# 0. Metadata

- Repository: `sskim-ai/thesis-monitor`
- Date: `2026-09-04 KST`
- Required base:
  `7a71494c9ca67d6fce4495c278311bc50a1ae82c`
  or a descendant containing the same completed Korean-token-boundary repair
- Previous implementation:
  `fe09654f5badad56fd23f8313b11fc7ba826590d`
- Previous final:
  `7a71494c9ca67d6fce4495c278311bc50a1ae82c`
- Previous fresh first ALL22:
  `22/22 PASS`
- Previous A/B/C:
  - A `18/22`
  - B `22/22`
  - C `21/22`
- Previous stability:
  - STABLE `7`
  - BOUNDARY_UNCERTAINTY `14`
  - UNSTABLE `1`
  - only UNSTABLE: `CRCL`
- Previous BUY↔SELL direct reversal:
  `0`
- Previous unexplained HOLD lean flip:
  `0`
- Production mutation/send/scheduler/DB/main merge:
  all `0`

This task is a narrow validator-ownership repair plus clean stability rerun.

Do NOT redesign the investment-judgment model.

---

# 1. Verified remaining blocker class A
## Non-mandatory "automatic sell" phrasing false positive

Previous failed phrases included meanings such as:

```text
저항권에서는 자동 매도보다 사업 성과를 재점검...
상단 구간은 자동 매도보다 회복의 질을 평가...
상단 구간은 자동 매도보다 실적 정당화 여부를 재평가...
```

These do NOT instruct:

```text
자동 매도
```

They explicitly mean:

```text
do not mechanically sell;
reassess business/valuation instead.
```

The current validator is too lexical.

This is a semantic ownership false positive.

---

# 2. Desired handling for trade-language semantics

User-facing AI judgment must not emit mandatory trading instructions.

Still forbidden:

```text
반드시 매도
자동 매도
즉시 매도
무조건 매도
손절해야 한다
목표가 도달 시 매도
자동으로 비중 축소
```

when used affirmatively as a directive.

But do not reject non-directive/negated comparisons such as:

```text
자동 매도보다 실적 재평가가 우선
기계적 매도 대신 Valuation 재점검
무조건 매도할 구간은 아님
자동 축소가 아니라 사업 성과 확인이 우선
```

The detector must judge directive semantics, not raw substring presence.

---

# 3. Preferred fix for trade-language ownership

Do not endlessly expand a negation-word regex.

Preferred architecture:

```text
structured holder semantics
+
deterministic renderer wording
```

The model should output:

```text
holder stance
upside review zone
business/valuation reassessment condition
```

The renderer should own language equivalent to:

```text
이 구간은 자동 매도 목표가가 아니라
실적·Valuation 재평가 구간입니다.
```

or preferably avoid mentioning "자동 매도" entirely.

Recommended user-facing rendering:

```text
• 상방 재점검: $X~Y
• 이 구간에서는 실적·Valuation 정당화 여부를 다시 확인합니다.
```

Hard:

```text
MODEL_OWNED_MANDATORY_TRADE_DIRECTIVE = 0
```

---

# 4. Mandatory-trade semantic validator

Validator should reject when BOTH are present:

```text
trade action
+
imperative/mandatory/execution semantics
```

Examples that MUST FAIL:

```text
반드시 매도해야 한다.
즉시 매도한다.
무조건 비중을 줄인다.
자동으로 매도한다.
이 가격에서는 손절해야 한다.
sell immediately.
must sell.
automatically reduce the position.
```

Examples that MUST PASS:

```text
자동 매도보다 실적 재평가가 우선이다.
기계적 매도 대신 기대와 Valuation을 재점검한다.
무조건 매도할 가격대로 보지는 않는다.
자동 축소가 아니라 사업 성과를 확인한다.
```

Do not introduce an AI classifier.
The validator remains deterministic.

---

# 5. Verified remaining blocker class B
## Evidence-grounded future ROIC/checkpoint false positive

Previous failed A/C examples included language such as:

```text
수주 증가가 영업현금흐름과 FCF, ROIC 개선으로 이어지면...
ROIC가 상승하면...
```

The frozen evidence actually contained configured validation/strengthening conditions using ROIC.

Therefore:

```text
ROIC token itself
!= unsupported metric claim
```

The current global metric ban is too broad.

---

# 6. Distinguish metric claim types

The validator must distinguish at least:

```text
CURRENT_VALUE_CLAIM
CURRENT_CALCULATED_CLAIM
HISTORICAL_VALUE_CLAIM
FUTURE_VALIDATION_CONDITION
QUALITATIVE_DIRECTIONAL_CONDITION
```

Examples:

```text
"현재 ROIC는 14.2%"
→ CURRENT_VALUE_CLAIM
→ needs actual current ROIC evidence

"ROIC가 8%에서 12%로 상승"
→ HISTORICAL_VALUE_CLAIM
→ needs sourced period-comparable values

"ROIC가 개선되면 성장의 질이 확인"
→ FUTURE_VALIDATION_CONDITION
→ allowed if packet/investment-logic evidence explicitly owns ROIC as a validation metric

"ROIC 개선 여부를 확인"
→ QUALITATIVE_DIRECTIONAL_CONDITION
→ allowed if configured evidence supports ROIC as a future checkpoint
```

---

# 7. Metric grounding rule

For metrics such as:

```text
ROIC
CCC
DSO
DPO
FCF
ROE
```

do NOT use:

```text
metric name present → reject
```

Instead require a provenance-aware rule.

For current numeric claims:
- actual evidence value required
- period/currency/basis safe where applicable

For future qualitative checkpoints:
- metric must be explicitly present in:
  - stored investment logic
  - validation metrics
  - strengthen/weaken signals
  - earnings checkpoint
  - canonical evidence
- no current numeric value may be invented

Hard:

```text
UNSUPPORTED_CURRENT_METRIC_VALUE = 0
UNSUPPORTED_FUTURE_CHECKPOINT_METRIC = 0
```

---

# 8. Do not broaden unsafe financial inference

This repair must NOT authorize:

```text
calculating missing ROIC
calculating missing FCF
inventing CCC/DSO/DPO
deriving ROIC from partial financials
reverse-engineering missing metrics
```

If the packet says only:

```text
ROIC improvement is a future validation condition
```

the AI may say:

```text
ROIC 개선 여부를 확인
```

It may NOT say:

```text
현재 ROIC가 개선됐다
```

unless current evidence supports it.

---

# 9. Preferred metric evidence schema

Use structured ownership when possible.

Example native-equivalent:

```json
{
  "future_validation_metric": "ROIC",
  "direction": "IMPROVE",
  "evidence_refs": ["E05"],
  "claim_type": "FUTURE_VALIDATION_CONDITION"
}
```

The model may choose supported metrics.

The model may not mint:
- unsupported metric identities
- current values
- unsupported periods

This preserves autonomy while constraining factual claims.

---

# 10. Regression tests — trade language

Must PASS:

```text
자동 매도보다 사업 성과 재점검이 우선이다.
상단에서는 자동 매도보다 회복의 질을 평가한다.
무조건 매도할 가격대로 보지는 않는다.
기계적 매도 대신 Valuation 정당화를 확인한다.
```

Must FAIL:

```text
반드시 매도해야 한다.
즉시 매도한다.
자동으로 매도한다.
무조건 비중을 줄인다.
이 가격에서는 손절해야 한다.
must sell immediately.
automatically reduce the position.
```

---

# 11. Regression tests — metric claim type

Must PASS when evidence supports future metric ownership:

```text
ROIC가 개선되는지 확인한다.
ROIC 개선이 성장의 질을 확인해준다.
FCF와 ROIC 개선 여부를 함께 본다.
CCC 정상화가 운전자본 개선으로 이어지는지 확인한다.
```

Must FAIL without current-value evidence:

```text
현재 ROIC는 12.4%다.
ROIC가 전년 8%에서 14%로 상승했다.
현재 CCC는 31일이다.
DSO는 42일로 개선됐다.
```

Must FAIL if a future metric is not present anywhere in allowed evidence:

```text
ROIC 개선을 확인한다.
```

for a subject whose allowed evidence has no ROIC ownership.

---

# 12. Preserve all prior fixes

Do not regress:

```text
Korean price-token boundary detector
086280 evidence alias integrity
CRCL/MU generic business-word handling
WRD/WULF deterministic confirmation renderer
confirmation_business_condition grounding
same-subject/market/generation evidence ownership
KR accounting safety
ADR/security-basis safety
```

Required:

```text
047810_FALSE_POSITIVE = 0
GENERIC_BUSINESS_WORD_FALSE_POSITIVE = 0
NONEXISTENT_EVIDENCE_REF = 0
SUBSTANTIVE_REPETITION = 0
```

---

# 13. Structured Autonomy remains frozen

Do NOT change:

```text
Fact → business/earnings → expectations → valuation → price/timing → risk
→ BUY/SELL drivers → qualitative synthesis
→ BUY:SELL balance
→ deterministic overall direction
→ new-buyer view
→ holder view
```

Do NOT change:

```text
BUY threshold = 6.0
SELL threshold = 6.0
balance increment = 0.5
HOLD lean mapping
Unknown policy
sector-aware policy
```

Required:

```text
JUDGMENT_LOGIC_CHANGED = 0
BALANCE_THRESHOLD_CHANGED = 0
```

---

# 14. US LIVE MONITORING COEXISTENCE GUARD
## Protect the 2026-09-04 08:00 KST natural US monitoring run

The US natural monitoring window begins around:

```text
2026-09-04 08:00 KST
```

This task must not degrade:
- production model inference
- Codex app-server/runtime state
- scheduler latency
- delivery timing
- accepted-plan persistence
- Telegram delivery

---

# 15. Before 08:00 KST — classify task resource impact

Before any shadow/model-consuming step, determine whether this work shares any of the following with the US natural run:

```text
signed-in Codex CLI runtime
CODEX_HOME
Codex app-server process/state
SQLite/runtime state DB
model concurrency slot
CPU/memory budget that can materially delay inference
shared working directory lock
shared packet/output namespace
shared delivery/test adapter
```

Create:

```text
US_LIVE_RESOURCE_INTERFERENCE =
NONE
POSSIBLE
CONFIRMED
UNKNOWN
```

Do not guess based only on "different branch".

---

# 16. Safe work that may continue during US live

Unless it creates measured resource pressure, the following may continue:

```text
static code editing
markdown/report drafting
git diff inspection
unit tests that do NOT invoke Codex/model/app-server
small deterministic validator tests
Ruff
git diff --check
secret scan
```

Only if they do not:
- saturate CPU/memory
- lock shared state
- use the same Codex runtime
- mutate production scheduler state

---

# 17. Work that must pause if interference is POSSIBLE/CONFIRMED/UNKNOWN

Pause before 08:00 or immediately when entering the US live window if any step invokes:

```text
signed-in Codex CLI
Codex app-server
actual model inference
shared model runtime/state
shared delivery-state process
shared production-like scheduler
heavy parallel test workload likely to delay US inference
```

Required:

```text
SHADOW_MODEL_CALL_DURING_PROTECTED_US_LIVE_WINDOW = 0
```

when resource interference is not confidently `NONE`.

---

# 18. Pause timing

If interference status is:

```text
POSSIBLE
CONFIRMED
UNKNOWN
```

then by:

```text
07:55 KST
```

or at the next safe checkpoint before model invocation:

```text
finish current atomic non-model step
persist clean work
stop shadow model/app-server processes
release locks
do not start ALL22/A/B/C model run
```

Do not kill the production US process.

Do not change the US scheduler.

---

# 19. Do not use a guessed fixed resume time

Resume must be event-driven.

Do NOT simply resume at:

```text
08:30
09:00
```

unless the authoritative natural run has completed.

Required resume condition:

```text
US natural run authoritative status identified
AND
model/inference phase complete
AND
accepted/delivery phase complete
AND
expected US live messages reached terminal delivery state
AND
no production retry/backup process still owns shared Codex/model state
```

If the US run falls back safely:
resume after the final terminal delivery mode is known and the shared runtime is released.

---

# 20. What counts as "US live message sending finished"

Use authoritative run artifacts/receipts.

Preferred evidence:

```text
run_id
model_reached / model_completed
accepted count
delivery pending count = 0
delivery sent/terminal count complete
fallback terminal state if applicable
duplicate/dedupe terminal state
process exit / runtime released
```

Do not infer completion merely because the first Telegram message appeared.

---

# 21. If resource interference is NONE

If a preflight proves the shadow work is isolated:

```text
separate CODEX_HOME/runtime
separate app-server
no shared model concurrency limit
no production-state lock
no meaningful CPU/memory pressure
```

then concurrent work may continue.

Still:

```text
PRODUCTION_STATE_MUTATION = 0
PRODUCTION_SEND = 0
```

Document why interference was classified `NONE`.

---

# 22. Runtime health sampling

Around the protected US window, record without perturbing production:

```text
timestamp
US scheduler/run detected?
shared Codex process?
shadow Codex process?
CPU/memory pressure if native lightweight observation exists
shared runtime lock/state?
```

Do not introduce heavy polling.

No more than a low-frequency lightweight status check.

---

# 23. If US natural run itself fails

Do not use the shadow task to repair the US live failure mid-run.

Policy:

```text
observe
preserve artifacts
let production fallback/retry policy reach terminal state
resume shadow only after shared runtime is released
```

Create a short incident note for later review.

This task remains focused on validator/stability work.

---

# 24. Fresh ALL22 generation after validator repairs

After:
- validator focused tests PASS
- US live coexistence policy allows model execution

create a completely new experiment generation.

Do not reuse:
- prior first-run candidates
- prior A/B/C candidates
- prior passing messages

Required:

```text
NEW_EXPERIMENT_GENERATION = PASS
OLD_CANDIDATE_REUSE = 0
SELECTIVE_TICKER_RERUN = 0
MANUAL_CANDIDATE_OVERRIDE = 0
```

---

# 25. Frozen source lock

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
US14 + KR8 = 22
```

Fresh fact collection:

```text
0
```

---

# 26. Fresh first ALL22 blind run

All prior decision results hidden until fresh balance is frozen.

Validate:

```text
schema
balance/label
HOLD lean
evidence alias
canonical provenance
confirmation business grounding
Korean price-token semantics
mandatory-trade semantic ownership
metric claim-type ownership
numeric provenance
price provenance
valuation safety
KR accounting safety
ADR/security-basis safety
Unknown policy
message contradiction
substantive repetition
```

Required:

```text
FIRST_RUN_VALIDATED = 22
```

---

# 27. Hard first gate

If:

```text
FIRST_RUN_VALIDATED != 22
```

then:

```text
A_B_C_GATE = NOT_RUN_FIRST_GATE_FAILED
```

Stop.

No selective rerun.
No threshold weakening.
No candidate patch.
No phrase edit.

---

# 28. A/B/C after clean first gate

Only after:

```text
FIRST_RUN_VALIDATED = 22
```

run fresh A/B/C.

Exact same:
- evidence
- contract
- schema
- validators
- renderer
- model/runtime class

No:
- cross-run visibility
- prompt change
- schema change
- post-result tuning
- majority voting

---

# 29. Stability metrics

Per ticker:

```text
label A/B/C
balance A/B/C
HOLD lean A/B/C
confidence A/B/C

new-buyer stance A/B/C
holder stance A/B/C
entry mode A/B/C

pullback A/B/C
confirmation A/B/C
trim zone A/B/C
downside review A/B/C

selected evidence aliases A/B/C
```

---

# 30. Stability classification

Use existing:

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
- no material action-context reversal

BOUNDARY_UNCERTAINTY
- spread <= 1.0
- real threshold/boundary
- no extreme reversal

UNSTABLE
- spread >= 1.5
or BUY↔SELL reversal
or unexplained BUY_LEAN↔SELL_LEAN flip
or ATTRACTIVE↔AVOID reversal
or HOLDABLE↔REDUCE reversal
```

---

# 31. CRCL dedicated stability audit

Because previous cleanest evidence showed:

```text
A: HOLD 4.5:5.5 / WAIT / REVIEW
B: SELL 4.0:6.0 / AVOID / REDUCE
C: HOLD 4.5:5.5 / WAIT / HOLDABLE
```

create a dedicated audit after the new clean A/B/C.

Do not hardcode a desired CRCL answer.

Compare:
- exact evidence selected
- expectation interpretation
- valuation interpretation
- price/timing interpretation
- balance
- new-buyer stance
- holder stance

Classify whether variance is:

```text
REAL_BOUNDARY_UNCERTAINTY
ACTION_CONTEXT_OVERREACTION
EVIDENCE_SELECTION_VARIANCE
OTHER
```

Only do this after all three runs are validator-clean.

---

# 32. Promotion-readiness criteria

Do not declare ready unless:

```text
FIRST_RUN_VALIDATED = 22

RUN_A_VALIDATED = 22
RUN_B_VALIDATED = 22
RUN_C_VALIDATED = 22

SAME_EVIDENCE_BUY_SELL_REVERSAL_COUNT = 0

UNEXPLAINED_HOLD_LEAN_FLIP_COUNT = 0

UNSTABLE_TICKER_COUNT = 0

MODEL_OWNED_MANDATORY_TRADE_DIRECTIVE = 0

UNSUPPORTED_CURRENT_METRIC_VALUE = 0

UNSUPPORTED_FUTURE_CHECKPOINT_METRIC = 0

NONEXISTENT_EVIDENCE_REF = 0

UNSUPPORTED_PRICE_NUMERIC = 0

MESSAGE_INTERNAL_CONTRADICTION = 0

SUBSTANTIVE_REPETITION = 0

KR_ACCOUNTING_SAFETY = PASS

ADR_SECURITY_BASIS_SAFETY = PASS
```

Natural KR/US production proof remains a separate later gate.

---

# 33. Tests

Before model runs:

```text
focused mandatory-trade semantic tests
focused metric claim-type tests
focused Korean-token boundary regressions
focused alias/provenance tests
focused renderer repetition tests
```

After implementation:

```text
focused ALL22 contract tests
full pytest
Ruff
git diff --check
secret scan
```

If exact-SHA CI exists:
- implementation SHA
- final/report SHA

Do not skip full pytest.

---

# 34. Production safety

Required:

```text
PRODUCTION_DECISION_MUTATION = 0
PRODUCTION_RENDERER_CHANGE = 0
PRODUCTION_SEND = 0
SCHEDULER_CHANGE = 0
DB_CHANGE = 0
MAIN_MERGE = 0
```

The coexistence guard must never modify the US scheduler.

---

# 35. Required reports

Create:

1. `docs/reports/20260904-nonmandatory-trade-language-root-cause.md`
2. `docs/reports/20260904-mandatory-trade-semantic-validator-contract.md`
3. `docs/reports/20260904-future-metric-claim-type-contract.md`
4. `docs/reports/20260904-roic-fcf-metric-grounding-regression.md`
5. `docs/reports/20260904-us-live-coexistence-preflight.md`
6. `docs/reports/20260904-us-live-pause-resume-log.md`
7. `docs/reports/20260904-us-live-runtime-isolation-verdict.md`
8. `docs/reports/20260904-uskr22-validator-repair-source-lock.md`
9. `docs/reports/20260904-uskr22-fresh-first-run.md`
10. `docs/reports/20260904-uskr22-fresh-first-run-validation.md`
11. `docs/reports/20260904-uskr22-run-a.md`
12. `docs/reports/20260904-uskr22-run-b.md`
13. `docs/reports/20260904-uskr22-run-c.md`
14. `docs/reports/20260904-uskr22-stability-comparison.md`
15. `docs/reports/20260904-crcl-clean-stability-audit.md`
16. `docs/reports/20260904-uskr22-message-quality.md`
17. `docs/reports/20260904-uskr22-promotion-readiness.md`
18. `docs/reports/20260904-uskr22-validator-coexistence-artifact-index.md`

Machine-readable:

```text
20260904-trade-language-regression.json
20260904-metric-claim-type-regression.json
20260904-us-live-coexistence.json
20260904-uskr22-fresh-first-run.json
20260904-uskr22-run-a.json
20260904-uskr22-run-b.json
20260904-uskr22-run-c.json
20260904-uskr22-stability.json
20260904-uskr22-proof.json
```

---

# 36. Required gates

Set exactly:

```text
BASE =
7a71494c9ca67d6fce4495c278311bc50a1ae82c / DESCENDANT

JUDGMENT_LOGIC_CHANGED =
0 / NONZERO

BALANCE_THRESHOLD_CHANGED =
0 / NONZERO

MODEL_OWNED_MANDATORY_TRADE_DIRECTIVE =
0 / NONZERO

NONMANDATORY_TRADE_FALSE_POSITIVE =
0 / NONZERO

MANDATORY_TRADE_TRUE_POSITIVE_BLOCK =
PASS / FAIL

UNSUPPORTED_CURRENT_METRIC_VALUE =
0 / NONZERO

UNSUPPORTED_FUTURE_CHECKPOINT_METRIC =
0 / NONZERO

FUTURE_METRIC_GROUNDING =
PASS / FAIL

CURRENT_METRIC_VALUE_GROUNDING =
PASS / FAIL

047810_FALSE_POSITIVE =
0 / NONZERO

GENERIC_BUSINESS_WORD_FALSE_POSITIVE =
0 / NONZERO

NONEXISTENT_EVIDENCE_REF =
0 / NONZERO

SUBSTANTIVE_REPETITION =
0 / NONZERO

US_LIVE_RESOURCE_INTERFERENCE =
NONE /
POSSIBLE /
CONFIRMED /
UNKNOWN

US_LIVE_PROTECTED_WINDOW_START =
2026-09-04T08:00:00+09:00

SHADOW_MODEL_CALL_DURING_PROTECTED_US_LIVE_WINDOW =
0 / NONZERO / NOT_APPLICABLE_ISOLATED

US_LIVE_PAUSE_REQUIRED =
YES / NO

US_LIVE_PAUSE_STARTED_AT =
... / NOT_APPLICABLE

US_LIVE_AUTHORITATIVE_RUN_ID =
... / NOT_FOUND

US_LIVE_MODEL_PHASE_TERMINAL =
PASS / FAIL / NOT_APPLICABLE

US_LIVE_DELIVERY_TERMINAL =
PASS / FAIL / NOT_APPLICABLE

US_LIVE_SHARED_RUNTIME_RELEASED =
PASS / FAIL / NOT_APPLICABLE

SHADOW_RESUMED_AT =
... / NOT_APPLICABLE

NEW_EXPERIMENT_GENERATION =
PASS / FAIL

OLD_CANDIDATE_REUSE =
0 / NONZERO

SELECTIVE_TICKER_RERUN =
0 / NONZERO

MANUAL_CANDIDATE_OVERRIDE =
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

CRCL_STABILITY_CLASS =
STABLE /
BOUNDARY_UNCERTAINTY /
UNSTABLE /
NOT_MEASURED

UNSUPPORTED_PRICE_NUMERIC =
0 / NONZERO

MESSAGE_INTERNAL_CONTRADICTION =
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

# 37. Completion response

Return:

```text
BASE =
...

TRADE-LANGUAGE ROOT CAUSE =
...

TRADE-LANGUAGE REPAIR =
...

METRIC-CLAIM ROOT CAUSE =
...

METRIC-CLAIM REPAIR =
...

US LIVE COEXISTENCE =
interference ...
pause required ...
pause start ...
authoritative run ...
delivery terminal ...
resume ...

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

CRCL =
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

# 38. Stop conditions

Stop before model rerun if:
- mandatory-trade semantic tests do not fully pass
- evidence-grounded future metric tests do not fully pass
- prior alias/token-boundary/renderer fixes regress

Pause shadow model work if:
- US live interference is POSSIBLE/CONFIRMED/UNKNOWN
- protected window has started
- authoritative US live run has not reached terminal delivery/runtime release

Stop before A/B/C if:
- fresh first run <22/22

Do not:
- lower thresholds
- edit candidates
- selectively rerun
- retune after seeing CRCL
- interfere with the US natural scheduler

---

# 39. Final principle

This task has two independent responsibilities:

```text
A. Make validators understand semantic ownership accurately.
B. Never let shadow experimentation interfere with the real US natural monitoring run.
```

If US live and shadow model execution are truly isolated, continue concurrently.

If not proven isolated, production monitoring wins:
pause model-consuming shadow work,
wait for authoritative US terminal delivery,
then resume from the next clean checkpoint.
