# thesis-monitor — KR Size / Sector Message Selection Bounded Repair
## Current-session 규모별 + 업종별 내부구조를 KR 오후 메시지에 기본 노출
## No acquisition / numeric-registry / Price Structure changes

---

# 0. Metadata

- Repository: `sskim-ai/thesis-monitor`
- Date: `2026-08-27 KST`
- Workstream: `KR_SIZE_SECTOR_MESSAGE_SELECTION_BOUNDED_REPAIR`
- Task type: `BOUNDED_RENDERER_SELECTION_REPAIR`
- Source policy: preserve current production source policy
- Current natural KR proof: `LIVE_PASS`
- Current KR local-first digest: `PASS`
- Current KR numeric registry: `PASS`
- Current Price Structure v3: `INTEGRATED_READY_NOT_ARMED`
- Price Structure Track C: preserve current master gate / do not arm in this task
- Production Assist: preserve `OFF`
- Telegram manual send: `0`
- Manual scheduled task: `0`
- DB mutation: `0`
- Official assessment mutation: `0`

### Latest known safe code lineage

Latest reported main / operating before this task:

`a1fb1a7006109f8699e03997662bde27db5ad464`

There may be a later report-only KR natural-reproof commit.

Before implementation:

1. `git fetch origin`
2. verify clean worktree
3. resolve actual latest safe `origin/main`
4. record current operating SHA
5. use the latest safe linear descendant as base

Do not move backward to an older code SHA merely because the natural-proof report was generated from it.

---

# 1. Why this task exists

The 2026-08-27 natural KR close proved:

```text
ka20001 index/breadth          PASS
ka20003 size/sector            PASS
ka10051 aggregate flow         PASS
ka10066 pagination             PASS
numeric registry               PASS
ready_for_ai                   true
KR local-first digest          PASS
exactly once                   PASS
```

But the final AI digest classified:

```text
KR_SIZE_CONTEXT_USED   = OMITTED_SAFE
KR_SECTOR_CONTEXT_USED = OMITTED_SAFE
```

even though same-session structured data was present and safe.

The user-facing policy should now change:

```text
current-session 규모별 구조
+
current-session 업종 상대 강·약
```

should normally be shown in the KR afternoon message when safe `ka20003` data exists.

This is not a provider/acquisition defect.

---

# 2. Frozen natural control — run 42

Use the exact natural packet as a regression fixture:

```text
Run ID:
42

Target:
2026-08-27

Packet:
2026-08-27-kr-run-42-5d8d23e6fbd6
```

Frozen safe `ka20003` controls:

## KOSPI size

```text
대형주 +1.66%
중형주 +0.22%
소형주 -0.13%
```

## KOSDAQ size/style

```text
KOSDAQ 100  +1.94%
KOSDAQ MID 300 +0.76%
KOSDAQ SMALL +0.44%
```

## KOSPI sector extremes

```text
전기/전자 +2.62%
유통      -2.36%
```

## KOSDAQ sector extremes

```text
금융      +3.21%
오락/문화 -1.29%
```

These are regression controls only.

Do not hard-code these values into production logic.

---

# 3. Exact historical message defect

The natural run-42 AI message was safe but too sparse:

```text
🤖 AI 보조 한국시장 마감 · KR Pilot 4/5

🎯 판단
KOSPI와 KOSDAQ의 지수 방향과 시장 폭이 엇갈려 국내 장을 하나의 방향으로 묶기 어렵습니다.

🔎 핵심 근거
외국인은 양 시장에서 순매수했습니다. 기관은 양 시장에서 순매수했습니다. 개인은 양 시장에서 순매도했습니다.

📌 다음 확인
• 양 시장의 상승·하락 종목 분포와 외국인·기관의 시장별 수급 방향이 함께 유지되는지 확인합니다.
```

The repair must retain the good local-first structure while adding bounded market-internal detail.

---

# 4. New user-facing policy

When safe same-session `ka20003` data exists:

```text
규모별 구조
→ required message content

업종 상대 강세 / 상대 약세
→ required message content
```

They are no longer `OMITTED_SAFE` solely for brevity.

If the source is unavailable / stale / invalid:

```text
omit safely
```

Never fabricate or carry forward stale values.

---

# 5. Preferred Korean terminology

Do not render internal English labels:

```text
leader
laggard
```

to the user.

Use:

```text
상대 강세 업종
상대 약세 업종
```

or a similarly natural Korean equivalent.

Recommended canonical labels:

```text
규모별
업종 상대 강세
업종 상대 약세
```

Do not use emotionally loaded language such as:

```text
최악 업종
폭락 업종
패배 업종
```

---

# 6. Why "상대 강세 / 상대 약세" is preferred

The strongest and weakest sector can both be positive or both be negative.

Therefore avoid a semantic rule that assumes:

```text
leader = 상승
laggard = 하락
```

Use relative language.

Examples:

```text
all sectors positive
→ strongest = 상대 강세
→ weakest   = 상대 약세

all sectors negative
→ least negative may still be 상대 강세
→ most negative = 상대 약세
```

The numeric return remains authoritative.

---

# 7. Required KR message hierarchy

Preserve KR local-first ownership.

New priority:

```text
1. KOSPI / KOSDAQ direction
2. KOSPI / KOSDAQ breadth
3. foreign / institution / retail aggregate flow
4. 규모별 구조
5. 업종 상대 강세 / 상대 약세
6. KR FX when material
7. prior/global macro as secondary
8. next-check
```

The new size/sector detail must not displace index, breadth, or aggregate flow.

---

# 8. Message-length policy

Do not preserve the previous short message by dropping KR size/sector again.

When length pressure exists, reduce in this order:

```text
1. repetitive global macro
2. secondary prior-US context
3. redundant explanation
4. verbose next-check wording
```

before dropping:

```text
current-session KR 규모별
current-session KR 업종 상대 강·약
```

Hard:

```text
GLOBAL_CONTEXT_PRIORITIZED_OVER_KR_SIZE_SECTOR = 0
```

---

# 9. Size/style slot — required when safe

When same-session `ka20003` size/style data is valid:

the message must consume a bounded size/style summary.

For KOSPI, normally include:

```text
대형
중형
소형
```

For KOSDAQ, when all three current supported style indexes are valid, normally include:

```text
KOSDAQ 100
KOSDAQ MID 300
KOSDAQ SMALL
```

Use the repository's user-facing canonical names.

Do not expose internal codes.

---

# 10. Compact size rendering

Preferred compact structure:

```text
규모별
KOSPI 대형 +x.xx% · 중형 +x.xx% · 소형 -x.xx%
KOSDAQ100 +x.xx% · MID300 +x.xx% · SMALL +x.xx%
```

Exact punctuation/line breaks may adapt to the renderer.

Do not include component advance/decline counts in the default size line unless separately material.

Those counts remain evidence/provenance.

---

# 11. Size/style interpretation

The renderer may add a short deterministic/AI interpretation such as:

```text
대형주 중심
중소형 상대 약세
KOSDAQ 대형 성장군 우위
```

only if supported by the current-session values.

No unsupported causality.

No AI arithmetic.

Hard:

```text
AI_DERIVED_SIZE_RETURN = 0
UNSUPPORTED_SIZE_STYLE_INTERPRETATION = 0
```

---

# 12. Sector slot — required when safe

When same-session safe sector rows exist:

for each market select a bounded pair:

```text
relative strongest sector
relative weakest sector
```

Normally:

```text
KOSPI 1 strongest + 1 weakest
KOSDAQ 1 strongest + 1 weakest
```

Do not dump every sector.

---

# 13. Compact sector rendering

Preferred semantic format:

```text
업종 상대 강세
KOSPI 전기·전자 +x.xx% · KOSDAQ 금융 +x.xx%

업종 상대 약세
KOSPI 유통 -x.xx% · KOSDAQ 오락·문화 -x.xx%
```

or one compact two-line equivalent.

Do not expose:

```text
leader
laggard
```

in user-facing prose.

---

# 14. Sector return vs component breadth

Preserve the existing semantic distinction.

A sector row may contain:

```text
sector-index return
component advance/decline/unchanged counts
```

The default user-facing "상대 강세/약세" selection is based on the backend-owned sector return ranking
unless the existing canonical policy explicitly says otherwise.

Never call:

```text
sector return
```

`sector breadth`.

Hard:

```text
SECTOR_RETURN_AS_SECTOR_BREADTH = 0
```

---

# 15. No AI ranking arithmetic

Sector extrema must be selected in deterministic backend logic.

AI receives:

```text
selected strongest sector
selected weakest sector
return
evidence refs
```

AI must not sort raw sector tables.

Hard:

```text
AI_DERIVED_SECTOR_RETURN = 0
AI_DERIVED_SECTOR_RANKING = 0
```

---

# 16. Shared AI / fallback ownership

The existing KR local-first plan should remain the single ownership layer.

Extend it with required slots, using repository-native names:

```text
SIZE_STYLE
SECTOR_EXTREMES
```

or equivalent existing fields.

Both:

```text
AI
deterministic fallback
```

must consume the same selected size/sector evidence.

Hard:

```text
AI_FALLBACK_SIZE_STYLE_PARITY = PASS
AI_FALLBACK_SECTOR_PARITY = PASS
```

Do not build separate selection logic.

---

# 17. New selection state

For valid same-session size/sector data, use a state equivalent to:

```text
SELECTED_REQUIRED
```

Do not allow:

```text
OMITTED_SAFE_LENGTH_BUDGET
```

as the normal state when the data is safe.

Allowed safe omissions:

```text
SOURCE_UNAVAILABLE
WRONG_SESSION
INVALID_SEMANTIC
NO_VALID_ROWS
```

and only other explicitly documented safety reasons.

---

# 18. Runtime evidence-utilization validator

Extend the existing deterministic utilization checks.

When safe current-session size/style exists:

```text
SIZE_STYLE_SLOT_CONSUMED = PASS
```

When safe sector extrema exist:

```text
SECTOR_EXTREMES_SLOT_CONSUMED = PASS
```

Run-42 historical message should fail these new gates.

Hard:

```text
SIZE_STYLE_AVAILABLE_BUT_OMITTED = 0
SECTOR_EXTREMES_AVAILABLE_BUT_OMITTED = 0
```

---

# 19. Historical run-42 negative fixture

The exact old run-42 message must fail the new policy because:

```text
size/style available
sector extrema available
final message consumes neither
```

Expected:

```text
RUN42_OLD_MESSAGE_NEW_POLICY = FAIL_AS_EXPECTED
```

Do not mutate the historical delivery.

---

# 20. Run-42 repaired candidate

Generate both:

```text
AI candidate
deterministic fallback candidate
```

using the immutable run-42 packet.

A semantically valid repaired candidate should contain:

```text
existing KOSPI/KOSDAQ + breadth interpretation
existing aggregate participant flow
KOSPI/KOSDAQ size/style
KOSPI/KOSDAQ relative strong/weak sectors
next-check
```

Global macro is optional secondary context.

Do not hard-code exact prose.

---

# 21. Example only — not canonical wording

A compact user-facing structure may look like:

```text
🎯 판단
KOSPI와 KOSDAQ이 올랐지만 내부 확산 정도는 달랐습니다.

🔎 수급
외국인·기관은 양 시장 순매수, 개인은 순매도였습니다.

📊 시장 내부
규모별: KOSPI 대형 +1.66% · 중형 +0.22% · 소형 -0.13%
KOSDAQ100 +1.94% · MID300 +0.76% · SMALL +0.44%

업종 상대 강세: KOSPI 전기·전자 +2.62% · KOSDAQ 금융 +3.21%
업종 상대 약세: KOSPI 유통 -2.36% · KOSDAQ 오락·문화 -1.29%
```

This is a regression example only.

Do not hard-code these values or wording.

---

# 22. Numeric provenance

All user-visible size/sector returns must come from registered backend numerics.

Hard:

```text
UNREGISTERED_SIZE_SECTOR_NUMERIC = 0
AI_CALCULATED_SIZE_SECTOR_NUMERIC = 0
NUMBERS_WITHOUT_PROVENANCE = 0
```

Do not change the already-passing numeric registry unless a direct missing supported path is found.

---

# 23. Numeric registry isolation

Current natural KR proof showed:

```text
TOTAL_NUMERIC_PATHS = 1989
SUPPORTED_CANONICAL_PATHS = 252
REGISTERED_SUPPORTED_PATHS = 252
INTERNAL_ONLY_PATHS = 126
UNSUPPORTED_PATHS = 0
NUMERIC_GATE = PASS
READY_FOR_AI = true
```

This task should not redesign the registry.

Hard:

```text
NUMERIC_REGISTRY_POLICY_DIFF = 0
```

except a strictly necessary compatibility update backed by an explicit failing current path.

---

# 24. Reconciliation / concentration isolation

Current participant-flow reconciliation remains separate.

Do not change:

```text
ka10051 aggregate ownership
ka10066 pagination
reconciliation tolerance
concentration eligibility
```

Hard:

```text
RECONCILIATION_TOLERANCE_WIDENED = 0
UNRECONCILED_CONCENTRATION_PROSE = 0
```

Size/sector message inclusion must not be coupled to participant concentration.

---

# 25. KR breadth / flow regression

Preserve:

```text
KOSPI/KOSDAQ direction
breadth
foreign/institution/retail aggregate flow
```

Hard:

```text
KR_DIRECTION_REGRESSION = 0
KR_BREADTH_REGRESSION = 0
KR_AGGREGATE_FLOW_REGRESSION = 0
```

---

# 26. No global-context regression

Prior/global macro remains secondary.

If size/sector inclusion causes length pressure:

global context should be reduced first.

Hard:

```text
PRIOR_US_BODY_REUSED_AS_KR_PRIMARY = 0
GLOBAL_CONTEXT_DOMINATES_KR_LOCAL = 0
```

---

# 27. Price Structure v3 isolation

Price Structure v3 remains:

`INTEGRATED_READY_NOT_ARMED`

This task does not enable:

```text
deterministic current SR
nearest support/resistance
major structural SR
wave/Fib
Fib/SR confluence
```

Hard:

```text
PRICE_STRUCTURE_V3_CODE_DIFF = 0
PRICE_STRUCTURE_RUNTIME_ARMED = 0
V3_PRICE_STRUCTURE_LEAK = 0
```

---

# 28. US Track isolation

Do not change the US current-session evidence-consumption repair.

Hard:

```text
US_MARKET_DIGEST_CODE_DIFF = 0
```

If a shared generic renderer utility must change:

prove exact US parity.

---

# 29. Business investment-logic isolation

No market size/sector movement may directly change stored investment logic.

Hard:

```text
MARKET_CONTEXT_AS_BUSINESS_THESIS_CHANGE = 0
BUSINESS_THESIS_MUTATION = 0
```

---

# 30. Focused tests

Required:

### Size/style

```text
all KOSPI size rows valid
→ all 3 displayed compactly

all KOSDAQ style rows valid
→ all 3 displayed compactly

one row invalid
→ no fabricated value
→ safe policy documented

same-session unavailable
→ slot safely unavailable
```

### Sector

```text
positive strongest / negative weakest
→ 상대 강세 / 상대 약세

all sectors positive
→ relative labels remain semantically valid

all sectors negative
→ relative labels remain semantically valid

sector source stale
→ omit

one market unavailable
→ render only safe market
```

### Length

```text
size/sector + global context over budget
→ reduce global context first
→ size/sector remains
```

### AI/fallback

```text
same packet
→ same selected size rows
→ same selected sector extrema
```

---

# 31. Run-42 immutable replay

Replay exact packet:

`2026-08-27-kr-run-42-5d8d23e6fbd6`

No Telegram.
No manual task.
No DB mutation.
No assessment mutation.
No historical archive rewrite.

Produce:

```text
historical exact message
repaired AI candidate
repaired fallback candidate
exact diff
selected size/style refs
selected sector refs
utilization validator result
numeric provenance
message length comparison
```

---

# 32. Run-42 replay gates

Set:

```text
KR_SIZE_STYLE_MESSAGE = PASS
KR_SECTOR_MESSAGE = PASS

KOSPI_SIZE_STYLE_CONSUMED = PASS
KOSDAQ_SIZE_STYLE_CONSUMED = PASS

KOSPI_RELATIVE_STRONG_SECTOR_CONSUMED = PASS
KOSPI_RELATIVE_WEAK_SECTOR_CONSUMED = PASS
KOSDAQ_RELATIVE_STRONG_SECTOR_CONSUMED = PASS
KOSDAQ_RELATIVE_WEAK_SECTOR_CONSUMED = PASS

SIZE_STYLE_AVAILABLE_BUT_OMITTED = 0
SECTOR_EXTREMES_AVAILABLE_BUT_OMITTED = 0

RUN42_OLD_MESSAGE_NEW_POLICY = FAIL_AS_EXPECTED

AI_FALLBACK_SIZE_STYLE_PARITY = PASS
AI_FALLBACK_SECTOR_PARITY = PASS

GLOBAL_CONTEXT_PRIORITIZED_OVER_KR_SIZE_SECTOR = 0

UNREGISTERED_SIZE_SECTOR_NUMERIC = 0
AI_CALCULATED_SIZE_SECTOR_NUMERIC = 0
AI_DERIVED_SECTOR_RANKING = 0

KR_DIRECTION_REGRESSION = 0
KR_BREADTH_REGRESSION = 0
KR_AGGREGATE_FLOW_REGRESSION = 0
```

---

# 33. Message quality review

Human-review repaired run-42 candidate.

Check:

```text
Does the message remain compact enough for daily use?
Can the reader immediately see large/mid/small leadership?
Can the reader immediately see relative strong/weak sectors?
Are KOSPI and KOSDAQ kept distinct?
Are percentages attributable to current-session ka20003?
Is "leader/laggard" absent from user-facing Korean?
Is global macro secondary?
```

Hard:

```text
MESSAGE_QUALITY = PASS
USER_FACING_LEADER_LAGGARD_TERM = 0
```

---

# 34. Full regression

Required:

```text
focused size/style tests
focused sector tests
run-42 replay
KR local-first tests
numeric provenance tests
reconciliation/concentration tests
full pytest
Ruff
git diff --check
Knowledge parity
Public Action/schema parity
operationId uniqueness
```

No public Action change expected.

---

# 35. Architecture / policy docs

Create/update:

```text
docs/architecture/KR_LOCAL_FIRST_MARKET_DIGEST.md
docs/architecture/KR_SIZE_SECTOR_MESSAGE_POLICY.md
```

Document:

```text
size/style required-selection policy
sector extrema selection policy
relative strong/weak terminology
length-budget ownership
AI/fallback shared ownership
safe omission reasons
```

---

# 36. Required reports

Create:

1. `docs/reports/20260827-kr-size-sector-selection-root-cause.md`
2. `docs/reports/20260827-kr-size-sector-message-policy.md`
3. `docs/reports/20260827-kr-run42-size-sector-plan.md`
4. `docs/reports/20260827-kr-run42-before-after-message.md`
5. `docs/reports/20260827-kr-run42-ai-fallback-size-sector-parity.md`
6. `docs/reports/20260827-kr-run42-size-sector-provenance.md`
7. `docs/reports/20260827-kr-size-sector-message-quality.md`
8. `docs/reports/20260827-kr-size-sector-safety-parity.md`
9. `docs/reports/20260827-kr-size-sector-repair-readiness.md`
10. `docs/reports/20260827-kr-size-sector-artifact-index.md`

Machine-readable recommended:

```text
docs/reports/20260827-kr-run42-size-sector-utilization.json
docs/reports/20260827-kr-size-sector-repair-readiness.json
```

---

# 37. Required hard gates

Set exactly:

```text
KR_SIZE_SECTOR_SELECTION_POLICY =
PASS / FAIL

KR_SIZE_STYLE_MESSAGE =
PASS / FAIL

KR_SECTOR_MESSAGE =
PASS / FAIL

KOSPI_SIZE_STYLE_CONSUMED =
PASS / NOT_AVAILABLE / FAIL

KOSDAQ_SIZE_STYLE_CONSUMED =
PASS / NOT_AVAILABLE / FAIL

KOSPI_RELATIVE_STRONG_SECTOR_CONSUMED =
PASS / NOT_AVAILABLE / FAIL

KOSPI_RELATIVE_WEAK_SECTOR_CONSUMED =
PASS / NOT_AVAILABLE / FAIL

KOSDAQ_RELATIVE_STRONG_SECTOR_CONSUMED =
PASS / NOT_AVAILABLE / FAIL

KOSDAQ_RELATIVE_WEAK_SECTOR_CONSUMED =
PASS / NOT_AVAILABLE / FAIL

SIZE_STYLE_AVAILABLE_BUT_OMITTED =
0 / NONZERO

SECTOR_EXTREMES_AVAILABLE_BUT_OMITTED =
0 / NONZERO

GLOBAL_CONTEXT_PRIORITIZED_OVER_KR_SIZE_SECTOR =
0 / NONZERO

RUN42_OLD_MESSAGE_NEW_POLICY =
FAIL_AS_EXPECTED / UNEXPECTED_PASS

AI_FALLBACK_SIZE_STYLE_PARITY =
PASS / FAIL

AI_FALLBACK_SECTOR_PARITY =
PASS / FAIL

USER_FACING_LEADER_LAGGARD_TERM =
0 / NONZERO

SECTOR_RETURN_AS_SECTOR_BREADTH =
0 / NONZERO

UNREGISTERED_SIZE_SECTOR_NUMERIC =
0 / NONZERO

AI_CALCULATED_SIZE_SECTOR_NUMERIC =
0 / NONZERO

AI_DERIVED_SIZE_RETURN =
0 / NONZERO

AI_DERIVED_SECTOR_RETURN =
0 / NONZERO

AI_DERIVED_SECTOR_RANKING =
0 / NONZERO

UNSUPPORTED_SIZE_STYLE_INTERPRETATION =
0 / NONZERO

NUMERIC_REGISTRY_POLICY_DIFF =
0 / NONZERO

RECONCILIATION_TOLERANCE_WIDENED =
0 / NONZERO

UNRECONCILED_CONCENTRATION_PROSE =
0 / NONZERO

KR_DIRECTION_REGRESSION =
0 / NONZERO

KR_BREADTH_REGRESSION =
0 / NONZERO

KR_AGGREGATE_FLOW_REGRESSION =
0 / NONZERO

PRIOR_US_BODY_REUSED_AS_KR_PRIMARY =
0 / NONZERO

GLOBAL_CONTEXT_DOMINATES_KR_LOCAL =
0 / NONZERO

PRICE_STRUCTURE_V3_CODE_DIFF =
0 / NONZERO

PRICE_STRUCTURE_RUNTIME_ARMED =
0 / NONZERO

V3_PRICE_STRUCTURE_LEAK =
0 / NONZERO

US_MARKET_DIGEST_CODE_DIFF =
0 / NONZERO

BUSINESS_THESIS_MUTATION =
0 / NONZERO

TELEGRAM_SEND =
0 / NONZERO

MANUAL_TASK =
0 / NONZERO

DB_MUTATION =
0 / NONZERO

OFFICIAL_ASSESSMENT_MUTATION =
0 / NONZERO

ARCHIVE_REWRITE =
0 / NONZERO

MESSAGE_QUALITY =
PASS / FAIL

CODE_CORRECTNESS =
PASS / FAIL

KR_SIZE_SECTOR_MESSAGE_REPAIR =
REPLAY_PASS_NATURAL_REPROOF_PENDING /
FAIL
```

---

# 38. Replay completion state

If all gates pass:

```text
OPEN_P0 = 0
OPEN_MATERIAL_P1 = 0

KR_SIZE_SECTOR_MESSAGE_REPAIR =
REPLAY_PASS_NATURAL_REPROOF_PENDING
```

Do not manually trigger a natural message.

Do not claim `LIVE_PASS` from replay.

---

# 39. Next natural KR close proof

After repaired code reaches operating main:

wait for the next naturally scheduled KR afternoon/close message.

Read-only verify:

```text
current session
exact packet
route
exact message

size/style present if safe
relative strong/weak sectors present if safe

index/breadth/flow still present
global context still secondary
numeric provenance safe
exactly once
```

Hard natural gates:

```text
NATURAL_KR_SIZE_STYLE_VISIBLE = PASS
NATURAL_KR_SECTOR_EXTREMES_VISIBLE = PASS
NATURAL_KR_LOCAL_FIRST_REGRESSION = 0
NATURAL_KR_NUMERIC_SAFETY = PASS
NATURAL_KR_DUPLICATE = 0
NATURAL_KR_ORPHAN = 0
```

Only then:

```text
KR_SIZE_SECTOR_MESSAGE_REPAIR = LIVE_PASS
```

---

# 40. Price Structure relationship

This repair is independent from Price Structure v3.

Do not automatically change:

```text
PRICE_STRUCTURE_TRACK_C
PRICE_STRUCTURE_RUNTIME_ARMED
```

Any Price Structure selective enablement still requires its own explicit instruction / master gate.

---

# 41. Severity

## P0

- wrong-session size/sector numbers
- fabricated size/sector returns
- duplicate live message
- Price Structure unexpectedly armed
- historical production archive mutated

## P1

- safe current size/style still omitted
- safe sector extremes still omitted
- global context wins length budget over required KR internal structure
- AI/fallback select different size/sector facts
- sector ranking computed by AI
- leader/laggard internal labels leak to user-facing output
- sector return mislabeled as sector breadth
- index/breadth/flow regresses

## P2

- punctuation / line-break differences
- exact Korean label variants with same meaning
- natural reproof pending after replay PASS

---

# 42. Completion response

Return:

```text
INSTRUCTION_COMMIT = ...
BASE_SHA = ...
BRANCH = ...
IMPLEMENTATION_SHA = ...
REPORT_COMMIT = ...
FINAL_MAIN = ...
OPERATING = ...

RUN42_PACKET =
2026-08-27-kr-run-42-5d8d23e6fbd6

KR_SIZE_SECTOR_SELECTION_POLICY = ...
KR_SIZE_STYLE_MESSAGE = ...
KR_SECTOR_MESSAGE = ...

KOSPI_SIZE_STYLE_CONSUMED = ...
KOSDAQ_SIZE_STYLE_CONSUMED = ...

KOSPI_RELATIVE_STRONG_SECTOR_CONSUMED = ...
KOSPI_RELATIVE_WEAK_SECTOR_CONSUMED = ...
KOSDAQ_RELATIVE_STRONG_SECTOR_CONSUMED = ...
KOSDAQ_RELATIVE_WEAK_SECTOR_CONSUMED = ...

SIZE_STYLE_AVAILABLE_BUT_OMITTED = 0
SECTOR_EXTREMES_AVAILABLE_BUT_OMITTED = 0
GLOBAL_CONTEXT_PRIORITIZED_OVER_KR_SIZE_SECTOR = 0

RUN42_OLD_MESSAGE_NEW_POLICY = FAIL_AS_EXPECTED

RUN42_REPAIRED_AI_MESSAGE =
...

RUN42_REPAIRED_FALLBACK_MESSAGE =
...

AI_FALLBACK_SIZE_STYLE_PARITY = ...
AI_FALLBACK_SECTOR_PARITY = ...

USER_FACING_LEADER_LAGGARD_TERM = 0
SECTOR_RETURN_AS_SECTOR_BREADTH = 0

UNREGISTERED_SIZE_SECTOR_NUMERIC = 0
AI_CALCULATED_SIZE_SECTOR_NUMERIC = 0
AI_DERIVED_SIZE_RETURN = 0
AI_DERIVED_SECTOR_RETURN = 0
AI_DERIVED_SECTOR_RANKING = 0

NUMERIC_REGISTRY_POLICY_DIFF = 0
RECONCILIATION_TOLERANCE_WIDENED = 0
UNRECONCILED_CONCENTRATION_PROSE = 0

KR_DIRECTION_REGRESSION = 0
KR_BREADTH_REGRESSION = 0
KR_AGGREGATE_FLOW_REGRESSION = 0

PRIOR_US_BODY_REUSED_AS_KR_PRIMARY = 0
GLOBAL_CONTEXT_DOMINATES_KR_LOCAL = 0

PRICE_STRUCTURE_V3_CODE_DIFF = 0
PRICE_STRUCTURE_RUNTIME_ARMED = 0
V3_PRICE_STRUCTURE_LEAK = 0
US_MARKET_DIGEST_CODE_DIFF = 0
BUSINESS_THESIS_MUTATION = 0

FOCUSED_TESTS = ...
FULL_PYTEST = ...
RUFF = ...
DIFF_CHECK = ...
KNOWLEDGE_PARITY = ...
PUBLIC_ACTION = ...
OPERATION_ID = ...
CI = ...

TELEGRAM_SEND = 0
MANUAL_TASK = 0
DB_MUTATION = 0
OFFICIAL_ASSESSMENT_MUTATION = 0
ARCHIVE_REWRITE = 0

MESSAGE_QUALITY = ...

OPEN_P0 = ...
OPEN_MATERIAL_P1 = ...

KR_SIZE_SECTOR_MESSAGE_REPAIR =
REPLAY_PASS_NATURAL_REPROOF_PENDING /
LIVE_PASS /
FAIL

NATURAL_KR_REPROOF =
PENDING /
PASS /
FAIL

NEXT_ACTION =
WAIT_FOR_NEXT_NATURAL_KR_CLOSE /
NO_ACTION /
BOUNDED_REPAIR

ZIP = ...
ZIP_SHA256 = ...
```

---

# 43. Mandatory completion ZIP

Create:

`20260827-kr-size-sector-message-selection-bounded-repair-bundle.zip`

Include:

```text
exact instruction
root-cause report
message policy
run-42 plan
before/after message
AI/fallback parity
numeric provenance
message quality
safety parity
readiness
machine-readable utilization
test/CI summary
artifact index
```

Do not include:

```text
secrets
auth headers
account identifiers
private tokens
hidden chain-of-thought
```

Compute SHA-256.

---

# 44. Final principle

The KR close message should not stop at:

```text
지수
breadth
수급
```

when the same packet already knows:

```text
어떤 규모가 강했는지
어떤 규모가 약했는지
어떤 업종이 상대적으로 강했는지
어떤 업종이 상대적으로 약했는지
```

When safe current-session `ka20003` evidence exists, that internal market structure is part of the
daily Korean market answer, not optional decoration.

Keep it compact.
Keep it local-first.
Keep the numerics backend-owned.
