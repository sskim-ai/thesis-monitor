# thesis-monitor — Korean Price-Token Boundary Repair + Fresh ALL22 + Final A/B/C Gate
## Fix the 047810 substring false positive without weakening technical ownership validation
## Preserve all prior Structured Autonomy / provenance / renderer repairs
## Start a completely new US14 + KR8 blind generation
## Run A/B/C only after a true 22/22 first-gate PASS

---

# 0. Metadata

- Repository: `sskim-ai/thesis-monitor`
- Date: `2026-09-03 KST`
- Branch:
  `codex/20260903-uskr22-confirmation-validator-semantic-repair-abc`
- Required base:
  `25feb161ceed9c27d30399b5e1035352f3cc3018`
  or a descendant containing the same implementation/report state
- Previous implementation SHA:
  `a73beefc64135f1ec0ff77f79d5068678cf035b6`
- Previous final/report SHA:
  `25feb161ceed9c27d30399b5e1035352f3cc3018`
- Previous fresh ALL22:
  `21/22`
- Previous A/B/C:
  `NOT_RUN_FIRST_GATE_FAILED`
- Previous distribution:
  `BUY 6 / HOLD 13 / SELL 3`
- Production mutation/send/scheduler/DB/main merge:
  all `0`

This is a narrow lexical-boundary repair.

Do NOT change the investment-judgment contract.

---

# 1. Verified blocker

The previous semantic validator correctly fixed:

```text
CRCL:
"USDC 점유율과 비이자성 수익 확대가 정상화 이익을 지지함."
→ PASS

MU:
"HBM 출하와 고객 채택이 확대되고 가격과 제품구성 강세 및 현금창출이 유지되는 것"
→ PASS
```

But the next fresh generation exposed:

```text
047810:
"양산 인도와 경공격기 해외 수주가 확대되고
수익성과 현금흐름이 회복되는 것"
```

The current Korean price-structure detector matched the substring:

```text
수주가 ... 회복
  └주가 ... 회복
```

as if it meant:

```text
주가 ... 회복
```

This is a false positive.

Verified classification:

```text
GENERIC_BUSINESS_WORD_FALSE_POSITIVE = 1
BUSINESS_CONDITION_TECHNICAL_OWNERSHIP_LEAK = 0
```

Therefore the failure is:

```text
substring/token-boundary defect
```

not:
- business-judgment error
- technical ownership leak
- evidence provenance error
- price provenance error
- renderer repetition
- accounting/security-basis error

---

# 2. Current risky pattern

The current implementation contains a pattern conceptually equivalent to:

```regex
(?:종가|주가)(?:가|는|이|의)? ... (돌파|상회|하회|회복|안착|재지지)
```

without a safe left lexical boundary.

That permits:

```text
수주가
발주가
...
```

to contain an accidental `주가` match.

Do not patch only the exact 047810 phrase.

---

# 3. Repair objective

The detector must distinguish:

```text
actual stock-price subjects
```

from:

```text
Hangul compounds that merely contain the same character sequence
```

Required result:

```text
수주가 확대 ... 현금흐름 회복
→ business language → PASS

주가가 저항을 회복
→ technical ownership → FAIL
```

---

# 4. No ticker-specific exception

Forbidden:

```text
if ticker == "047810":
    allow
```

Forbidden:

```text
if "수주가" in text:
    skip validator
```

as the sole fix.

The solution must be a generic Korean token/subject boundary mechanism.

Required:

```text
TICKER_SPECIFIC_EXCEPTION = 0
```

---

# 5. Preferred detector architecture

Create a deterministic helper conceptually equivalent to:

```text
contains_korean_price_subject_action(text)
```

Do not rely on a raw substring regex over:

```text
주가
종가
```

alone.

Recommended logic:

```text
1. recognize a finite set of valid technical price-subject expressions
2. require the recognized subject to start at a valid lexical boundary
3. allow Korean grammatical particles after the subject
4. require a nearby technical price action / structure phrase
5. separately detect explicit support/resistance/confirmation nouns
```

No external NLP/model call is needed.

---

# 6. Valid left boundary

For a standalone Korean technical subject such as:

```text
주가
종가
```

its start must be one of:

```text
start of string
or
preceded by a non-Hangul lexical delimiter
```

Examples of acceptable delimiters:

```text
space
newline
punctuation
opening bracket/quote
bullet/separator
```

Thus:

```text
주가가 회복
→ match

현재 주가가 회복
→ recognized compound subject

수주가 회복
→ standalone "주가" must NOT match because preceding char is Hangul "수"

발주가 증가
→ must NOT match

최종가격 상승
→ standalone "종가" must NOT match because preceding char is Hangul "최"
```

---

# 7. Recognized technical subject expressions

Support repository-native equivalents of at least:

```text
주가
현재 주가
현재주가
당일 주가
당일주가

종가
정규장 종가
정규장종가
전일 종가
전일종가
당일 종가
당일종가
```

Additional clearly technical compounds may be added if already used in production messages.

Do not add broad compounds merely to improve recall.

Each recognized compound must itself start at a valid lexical boundary.

---

# 8. Korean particles after subject

The detector must tolerate common grammatical particles such as:

```text
가
는
이
의
를
에서
으로
보다
```

where appropriate.

Examples that must still be detected:

```text
주가가 저항을 돌파
주가는 확인선을 회복
종가가 저항 상단을 상회
전일종가보다 하회
현재주가가 지지선을 이탈
```

Do not require a whitespace after `주가/종가`.

---

# 9. Technical action/context requirement

A recognized price subject alone is not sufficient.

Require nearby technical price semantics such as:

```text
돌파
상회
하회
회복
안착
재지지
이탈
붕괴
```

or explicit technical structure nouns such as:

```text
저항선
지지선
확인선
저항 구간
지지 구간
확인 가격
등록 확인 가격
```

Preserve existing correct English technical patterns.

---

# 10. Business compounds that MUST PASS

Expand regression fixtures to include at least:

```text
양산 인도와 경공격기 해외 수주가 확대되고 수익성과 현금흐름이 회복되는 것

수주가 확대되고 영업현금흐름이 개선되는 것

해외 발주가 증가하고 생산 효율이 회복되는 것

최종가격 상승이 수익성 개선을 지지함.

제품 가격 회복이 마진 개선을 지원함.

평균판매가격 개선이 현금창출을 지지함.

원재료 가격이 안정되고 마진이 회복되는 것

판매가격 강세가 이익을 지지함.
```

Also preserve prior passing fixtures:

```text
CRCL exact prior sentence
MU exact prior sentence
가격 결정력이 마진 방어를 지원함
pricing power supports margins
customer demand supports utilization
supplier support improves execution
```

---

# 11. Important compound false-positive cases

Explicitly test character-sequence collisions:

```text
수주가
발주가
신규수주가
해외수주가

최종가격
제품가격
판매가격
평균판매가격
원재료가격
```

None may trigger merely because they contain:

```text
주가
종가
가격
```

in a business meaning.

---

# 12. Technical phrases that MUST FAIL

At least:

```text
주가가 확인선을 돌파해야 한다.
주가는 저항선을 회복해야 한다.
현재 주가가 저항 상단을 상회해야 한다.
현재주가가 지지선을 회복해야 한다.
당일주가가 확인 가격을 돌파해야 한다.

종가가 확인선을 돌파해야 한다.
정규장 종가가 저항 상단에 안착해야 한다.
정규장종가가 확인 가격을 상회해야 한다.
전일 종가를 하회했다.
전일종가보다 하회했다.

저항선 위로 안착해야 한다.
지지선 회복이 필요하다.
확인선 돌파가 필요하다.
등록 확인 가격을 회복해야 한다.
```

Preserve prior English true-positive blocks:

```text
close above resistance
breakout through confirmation
support-level retest
registered confirmation price recovery
```

---

# 13. Do not overfit to whitespace

Korean technical text may appear with or without whitespace:

```text
현재 주가
현재주가

정규장 종가
정규장종가

전일 종가
전일종가
```

Test both.

But do not achieve this by allowing arbitrary Hangul characters before `주가/종가`.

Use explicit recognized compounds.

---

# 14. Do not solve with negative-word blacklist alone

A list such as:

```text
수주가
발주가
```

may be used as additional defense,
but it must not be the primary architecture.

Reason:

```text
future compounds can create the same substring collision
```

Primary ownership must be:

```text
recognized technical subject + valid boundary + technical action/context
```

---

# 15. Preserve evidence grounding

The current grounded business-condition repair remains mandatory:

```text
confirmation_business_condition_refs
```

must resolve to allowed same-subject/same-market/same-generation evidence.

Required:

```text
CONFIRMATION_BUSINESS_CONDITION_GROUNDED = PASS
BUSINESS_CONDITION_PRICE_ONLY_EVIDENCE = 0
```

Do not remove evidence grounding to fix the lexical bug.

---

# 16. Preserve evidence alias repair

Keep:

```text
FREE_FORM_EVIDENCE_REF_GENERATION = 0
ALIAS_ONE_TO_ONE_MAPPING = PASS
NONEXISTENT_EVIDENCE_REF = 0
CROSS_SUBJECT_EVIDENCE_REF = 0
CROSS_MARKET_EVIDENCE_REF = 0
CROSS_GENERATION_EVIDENCE_REF = 0
```

No regression to free-form IDs.

---

# 17. Preserve renderer ownership

Keep deterministic renderer ownership of:

```text
confirmation level
price confirmation semantics
holder resistance/rejection scenario
new-buyer breakout scenario
```

Business condition remains non-price business prose.

Required:

```text
GENERIC_CONFIRMATION_FREE_TEXT_OWNERSHIP = 0
WRD_WULF_SUBSTANTIVE_CONFIRMATION_REPETITION = 0
```

---

# 18. Preserve Structured Autonomy

Do not change:

```text
reasoning order
BUY/SELL threshold
0.5 balance increments
HOLD lean mapping
sector-aware Unknown policy
new-buyer stance semantics
holder stance semantics
entry/confirmation/trim semantics
```

Required:

```text
JUDGMENT_LOGIC_CHANGED = 0
BALANCE_THRESHOLD_CHANGED = 0
```

---

# 19. Focused detector tests before any model run

Before starting a new ALL22 experiment, run the expanded boundary corpus.

Required minimum:

```text
BUSINESS_FALSE_POSITIVE_FIXTURES >= 15
TECHNICAL_TRUE_POSITIVE_FIXTURES >= 15
```

All must pass.

Also add direct unit tests for:

```text
"수주가" does not match standalone 주가
"발주가" does not match standalone 주가
"최종가격" does not match standalone 종가
"현재주가" is recognized
"전일종가" is recognized
"정규장종가" is recognized
```

---

# 20. Mutation / fuzz-style deterministic corpus

Create deterministic combinatorial tests for:

Business prefixes:

```text
수
발
신규수
해외수
```

with:

```text
주가
```

and business actions:

```text
확대
증가
유지
개선
회복
```

These must not trigger merely from substring collisions.

Technical recognized subjects:

```text
주가
현재주가
당일주가
종가
전일종가
정규장종가
```

combined with technical actions:

```text
돌파
상회
하회
회복
안착
재지지
이탈
```

must trigger where semantically applicable.

This is deterministic test generation, not random fuzzing.

---

# 21. Fresh experiment generation

Only after focused boundary tests PASS:

```text
start NEW experiment generation
```

Do not continue the previous 21/22 run.

Do not reuse its passing candidates.

Do not rerun only 047810.

Required:

```text
NEW_EXPERIMENT_GENERATION = PASS
OLD_PASSING_CANDIDATE_REUSE = 0
SELECTIVE_TICKER_RERUN = 0
MANUAL_CANDIDATE_OVERRIDE = 0
```

---

# 22. Source lock

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

KR8:
000660
003690
005490
005930
010120
012450
047810
086280
```

Total:

```text
22
```

Fresh fact collection:

```text
0
```

---

# 23. Fresh ALL22 blind first run

Hide all previous candidate decisions until the new fresh candidate is frozen.

Run all 22 from scratch.

Validate:

```text
schema
directional balance
deterministic label
HOLD lean
evidence alias
canonical evidence resolution
confirmation business grounding
Korean price-token semantic ownership
numeric provenance
semantic provenance
price provenance
valuation safety
KR accounting safety
ADR/security-basis safety
Unknown policy
message contradiction
substantive repetition
identity/language
```

Required:

```text
FIRST_RUN_VALIDATED = 22
```

---

# 24. Hard first gate

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
No candidate override.
No post-hoc sentence edit.
No validator disable.

---

# 25. 047810 dedicated proof

Create a dedicated report for the new fresh run showing:

```text
exact confirmation_business_condition
detector decision
matched technical subjects, if any
matched technical actions, if any
grounded evidence refs
validation result
```

Required:

```text
047810_FALSE_POSITIVE = 0
```

If the new model output is genuinely technical,
reject it normally.

Do not force 047810 to pass.

---

# 26. A/B/C only after 22/22

If and only if:

```text
FIRST_RUN_VALIDATED = 22
```

execute:

```text
RUN A
RUN B
RUN C
```

with identical:
- frozen evidence
- prompt
- schema
- validator
- renderer
- model/runtime class

No cross-run decision visibility.

No prompt/schema change between runs.

No post-result tuning.

No majority voting.

---

# 27. A/B/C measurements

Per ticker:

```text
label A/B/C
balance A/B/C
HOLD lean A/B/C
confidence A/B/C

new-buyer stance A/B/C
holder stance A/B/C
preferred entry mode A/B/C

pullback zone A/B/C
confirmation level A/B/C
trim/review zone A/B/C
downside review A/B/C

selected evidence aliases A/B/C
```

---

# 28. Stability classification

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
- no material new-buyer/holder reversal

BOUNDARY_UNCERTAINTY
- balance spread <= 1.0
- real threshold/boundary
- no extreme reversal

UNSTABLE
- spread >= 1.5
or BUY↔SELL reversal
or unexplained BUY_LEAN↔SELL_LEAN flip
or ATTRACTIVE↔AVOID reversal
or HOLDABLE↔REDUCE reversal
```

Do not hide variance with averages.

---

# 29. Special stability audit

Highlight, without hardcoding outcomes:

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
047810
```

These have either:
- recent boundary movement
- validator incident history
- meaningful stance variance potential

---

# 30. Promotion-readiness rule

Do not declare ready unless:

```text
FIRST_RUN_VALIDATED = 22

RUN_A_VALIDATED = 22
RUN_B_VALIDATED = 22
RUN_C_VALIDATED = 22

SAME_EVIDENCE_BUY_SELL_REVERSAL_COUNT = 0

UNEXPLAINED_HOLD_LEAN_FLIP_COUNT = 0

UNSTABLE_TICKER_COUNT = 0

047810_FALSE_POSITIVE = 0

GENERIC_BUSINESS_WORD_FALSE_POSITIVE = 0

BUSINESS_CONDITION_TECHNICAL_OWNERSHIP_LEAK = 0

NONEXISTENT_EVIDENCE_REF = 0

UNSUPPORTED_PRICE_NUMERIC = 0

MESSAGE_INTERNAL_CONTRADICTION = 0

SUBSTANTIVE_REPETITION = 0

KR_ACCOUNTING_SAFETY = PASS

ADR_SECURITY_BASIS_SAFETY = PASS
```

Natural KR/US production proof remains a separate later gate.

---

# 31. Tests

Run:

```text
focused Korean token-boundary tests
focused confirmation semantic tests
focused CRCL/MU/047810 regressions
focused alias/provenance tests
focused renderer/repetition tests
focused ALL22 shadow tests
full pytest
Ruff
git diff --check
secret scan
```

If exact-SHA CI exists:
- implementation SHA CI
- final/report SHA CI

Do not skip full pytest.

---

# 32. Production safety

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

# 33. Required reports

Create:

1. `docs/reports/20260903-korean-price-token-boundary-root-cause.md`
2. `docs/reports/20260903-korean-price-subject-detector-contract.md`
3. `docs/reports/20260903-korean-business-compound-regression-matrix.md`
4. `docs/reports/20260903-korean-technical-subject-regression-matrix.md`
5. `docs/reports/20260903-047810-false-positive-regression-proof.md`
6. `docs/reports/20260903-uskr22-boundary-repair-source-lock.md`
7. `docs/reports/20260903-uskr22-boundary-repair-first-run.md`
8. `docs/reports/20260903-uskr22-boundary-repair-validation.md`
9. `docs/reports/20260903-uskr22-prior21-vs-new-first-run.md`
10. `docs/reports/20260903-uskr22-run-a.md`
11. `docs/reports/20260903-uskr22-run-b.md`
12. `docs/reports/20260903-uskr22-run-c.md`
13. `docs/reports/20260903-uskr22-stability-comparison.md`
14. `docs/reports/20260903-uskr22-hold-lean-stability.md`
15. `docs/reports/20260903-uskr22-action-context-stability.md`
16. `docs/reports/20260903-uskr22-evidence-selection-variance.md`
17. `docs/reports/20260903-uskr22-message-quality.md`
18. `docs/reports/20260903-uskr22-promotion-readiness.md`
19. `docs/reports/20260903-uskr22-boundary-repair-artifact-index.md`

Machine-readable:

```text
20260903-korean-token-boundary-regression.json
20260903-uskr22-boundary-repair-first-run.json
20260903-uskr22-run-a.json
20260903-uskr22-run-b.json
20260903-uskr22-run-c.json
20260903-uskr22-stability.json
20260903-uskr22-boundary-repair-proof.json
```

Exact message previews:
- US14 combined
- KR8 combined
- one exact message per ticker

---

# 34. Required gates

Set exactly:

```text
BASE =
25feb161ceed9c27d30399b5e1035352f3cc3018 / DESCENDANT

JUDGMENT_LOGIC_CHANGED =
0 / NONZERO

BALANCE_THRESHOLD_CHANGED =
0 / NONZERO

TICKER_SPECIFIC_EXCEPTION =
0 / NONZERO

KOREAN_PRICE_SUBJECT_BOUNDARY_DETECTOR =
PASS / FAIL

BUSINESS_FALSE_POSITIVE_FIXTURE_COUNT =
...

BUSINESS_FALSE_POSITIVE_FIXTURE_PASS_COUNT =
...

TECHNICAL_TRUE_POSITIVE_FIXTURE_COUNT =
...

TECHNICAL_TRUE_POSITIVE_FIXTURE_PASS_COUNT =
...

CRCL_REGRESSION =
PASS / FAIL

MU_REGRESSION =
PASS / FAIL

047810_REGRESSION =
PASS / FAIL

GENERIC_BUSINESS_WORD_FALSE_POSITIVE =
0 / NONZERO

BUSINESS_CONDITION_TECHNICAL_OWNERSHIP_LEAK =
0 / NONZERO

CONFIRMATION_BUSINESS_CONDITION_GROUNDED =
PASS / FAIL

BUSINESS_CONDITION_PRICE_ONLY_EVIDENCE =
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

047810_FALSE_POSITIVE =
0 / NONZERO

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

# 35. Completion response

Return:

```text
BASE =
...

TOKEN-BOUNDARY ROOT CAUSE =
...

REPAIR =
...

REGRESSION MATRIX =
business pass ...
technical block ...

CRCL =
...

MU =
...

047810 =
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

# 36. Stop conditions

Stop before ALL22 if:
- the expanded Korean boundary fixture matrix does not fully pass
- CRCL/MU regressions break
- true technical phrases stop being detected
- alias/provenance repair regresses

Stop before A/B/C if:
- fresh first run is <22/22
- 047810 is still a false positive
- substantive repetition returns
- any unsupported price numeric appears
- any validator was disabled to achieve pass

---

# 37. Final principle

The validator must recognize:

```text
technical meaning
```

not:

```text
accidental character overlap
```

`수주가` is not `주가`.
`최종가격` is not `종가`.

But:

```text
현재주가
전일종가
정규장 종가
```

must remain valid technical subjects.

Fix the lexical boundary generically, then restart the entire 22-subject experiment and finally measure the decision stability itself.
