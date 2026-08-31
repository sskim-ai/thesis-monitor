# thesis-monitor — 2026-09-01 KST US V2 Natural Live Read-Only Verification

## 목적
2026-08-31 America/New_York 정규장 마감분이 2026-09-01 KST 오전에 자연 실행된 결과를 **read-only**로 검증한다.

사용자가 받은 메시지상 US 시장 메시지는 최신 포맷으로 보이지만, CORZ 종목 메시지에는 명시적 `BUY/HOLD/SELL` v2 판단 블록이 보이지 않았다.

이번 작업은 수동 재실행/재전송/수정 없이 아래 파이프라인의 어느 단계에서 v2가 사라졌는지 확정한다.

`cohort → candidate → adjudication → accepted_decision → selector → renderer → validator → delivery`

---

## 0. 현재 US/foreign active universe

현재 runtime active 목록 기준 14종목:

- CORZ
- CPNG
- CRCL
- GOOGL
- HUT
- IBM
- MU
- RXRX
- SKHY
- SNDK
- TSLA
- TSM
- WRD
- WULF

따라서 CPNG가 packet cutoff 전에 ACTIVE_READY였다면 기대 메시지 수는:

```text
US market 1
US/foreign stocks 14
TOTAL 15
```

CPNG가 cutoff 이후 활성화됐다면 cutoff 당시 frozen cohort를 기준으로 actual expected count를 별도로 기록한다.

---

## 1. 절대 금지

이 작업은 proof 전용이다.

금지:
- US production job 수동 실행
- primary/backup scheduler 수동 trigger
- Telegram production 재전송
- retry 수동 생성
- accepted decision 수정
- onboarding 상태 수정
- feature flag 수정
- scheduler 수정
- proof 도중 merge/repair

필수:

```text
MANUAL_US_PRODUCTION_JOB_TRIGGER = 0
MANUAL_US_PRODUCTION_SEND = 0
US_PRODUCTION_STATE_MUTATION = 0
```

---

## 2. Target cycle

Target:

```text
US market session = 2026-08-31 America/New_York
KST delivery date = 2026-09-01
```

수집:
- run/job ID
- primary scheduled/actual
- backup scheduled/actual
- packet claim owner
- packet ID
- dispatcher/delivery timestamp
- evidence cutoff
- job exit
- natural retry relation

필수:

`US_CANONICAL_SESSION_DATE = 2026-08-31`

---

## 3. Runtime lineage / feature state

Read-only 수집:
- origin/main HEAD
- operating HEAD
- runtime/deployed SHA
- config/feature version

그리고 실제 production state:

```text
VISIBLE_STOCK_DECISION_ENGINE
V2_PRODUCTION_ENABLED
FULL_MONITORED_STOCK_COVERAGE_TARGET
V1_VISIBLE_DECISION_ENGINE
V1_ROLLBACK_AVAILABLE
PRODUCTION_ASSIST
background onboarding reconciler
market-preflight onboarding resume
```

기대 semantics:

```text
VISIBLE_STOCK_DECISION_ENGINE = V2_ACCEPTED
V2_PRODUCTION_ENABLED = true
FULL_MONITORED_STOCK_COVERAGE_TARGET = true
V1_VISIBLE_DECISION_ENGINE = false
V1_ROLLBACK_AVAILABLE = true
PRODUCTION_ASSIST = OFF
```

Gate:

`US_RUNTIME_LINEAGE = PASS / DOCUMENTED_DOC_ONLY_DESCENDANT / FAIL`

---

## 4. Frozen cohort

packet cutoff 시점의 immutable US cohort를 수집한다.

각 종목:
- active at cutoff?
- onboarding_ready?
- production_eligible?
- included?
- excluded?
- exclusion reason?
- first eligible session?

Hard:

```text
US_PACKET_UNIVERSE_MUTATED_AFTER_CUTOFF = 0
```

---

## 5. CPNG mandatory control

CPNG는 이번 US proof의 핵심 신규 종목이다.

cutoff 기준 확인:
- monitoring_requested
- active
- onboarding_ready
- production_eligible
- blockers
- first eligible session

그리고:
- frozen cohort 포함?
- v2 candidate 생성?
- adjudication 필요/완료?
- accepted decision?
- message render?
- delivery?

상태:

```text
CPNG_V2_LIVE_STATUS =
PASS /
NOT_READY_SAFE /
EXCLUDED_AFTER_CUTOFF_SAFE /
MISSING_UNEXPECTED /
FAIL
```

Hard:

`CPNG_BLOCKS_OTHER_US_SUBJECTS = 0`

---

## 6. US 시장 메시지 검증

사용자가 받은 메시지 예시는:

```text
🇺🇸 미국시장 마감

SPY -0.30%
QQQ +0.05%
IWM -0.62%
SOXX +0.48%
RSP -0.59%

SOXX 상대강세
에너지 +2.04%
커뮤니케이션 서비스 -1.35%
미국 10년물 실질금리 상승
```

실제 production payload에서 검증:
- SPY/QQQ/IWM/SOXX/RSP
- SOXX relative signal
- IWM relative signal if material
- RSP participation semantics
- sector strong/weak
- macro temporal role
- night-futures canonical state

Gates:

```text
US_MARKET_MESSAGE_QUALITY = PASS / PARTIAL_SAFE / FAIL
US_MACRO_TEMPORAL_SAFETY = PASS / PARTIAL_SAFE / FAIL
US_NIGHT_FUTURES = CURRENT_SAFE / SOURCE_LIMITATION_SAFE / OMITTED_OTHER_SAFE / FAIL
```

---

## 7. Per-stock v2 pipeline

cutoff-eligible 전 종목에 대해 수집:

```text
evidence fingerprint
candidate generated?
candidate decision
prior accepted decision
material disagreement?
adjudication required?
adjudication status
accepted decision
accepted source
accepted plan present?
confidence
timing
renderer route
explicit BUY/HOLD/SELL visible?
raw candidate visible?
```

Fresh evidence면 과거 frozen decision과 달라도 된다.

Hard:

```text
US_SAME_EVIDENCE_UNEXPLAINED_DECISION_CHURN = 0
US_UNADJUDICATED_MATERIAL_CHANGE_VISIBLE = 0
US_RAW_CANDIDATE_VISIBLE = 0
```

---

## 8. Renderer route audit

각 실제 stock message가 어떤 경로에서 생성됐는지 반드시 식별한다.

분류:

```text
V2_ACCEPTED_RENDERER
LEGACY_V1_RENDERER
AI_ASSIST_PILOT_RENDERER
DETERMINISTIC_FALLBACK
OTHER
```

수집:
- selector decision
- accepted_decision_plan present?
- renderer route
- decision block selected?
- suppression reason?

필수:

`US_RENDERER_ROUTE_IDENTIFIED_COUNT = cutoff eligible count`

---

## 9. Explicit decision-block requirement

accepted-ready 종목은 user-facing 메시지에 명시적으로:

```text
🧠 AI 분석 판단: BUY / HOLD / SELL
```

또는 동등한 top-level decision이 보여야 한다.

중요:

```text
투자 논리: 유지
```

는 HOLD가 아니다.

따라서 accepted decision이 존재하는데 message에 BUY/HOLD/SELL이 없으면:

```text
ACCEPTED_EXISTS_RENDERER_OMITTED = true
```

로 처리한다.

---

## 10. CORZ exact trace

사용자가 받은 CORZ 메시지에는 explicit BUY/HOLD/SELL이 없었다.

CORZ를 end-to-end 추적:

```text
evidence
→ candidate
→ prior accepted
→ adjudication
→ accepted decision
→ accepted plan
→ selector
→ renderer
→ validator
→ rendered payload
→ outbound
→ received
```

최종 상태:

```text
CORZ_V2_STATUS =
ACCEPTED_AND_VISIBLE /
ACCEPTED_BUT_RENDERER_OMITTED /
CANDIDATE_ONLY_NO_ACCEPTED /
NOT_READY_SAFE_SUPPRESSION /
OLD_RENDERER_ROUTE /
FALLBACK_RENDERER_ROUTE /
OTHER_FAIL
```

---

## 11. GOOGL control

GOOGL은 과거 accepted pre-confirmation BUY control이었다.

fresh data로 판단은 바뀔 수 있다.

검증:
- prior accepted
- fresh candidate
- adjudication
- new accepted
- visible top-level decision
- preconfirmation_buy if still applicable

Gate:

```text
GOOGL_V2_LIVE_CONTROL =
PASS /
CHANGED_WITH_EXPLAINED_EVIDENCE /
FAIL
```

---

## 12. SELL controls

과거 SELL controls:
- HUT
- TSLA
- WULF

fresh evidence로 바뀔 수 있음.

검증:
- accepted decision
- bearish polarity
- visible decision
- order-command language 없음

Gate:

```text
US_SELL_PATH_VISIBILITY =
PASS /
NOT_APPLICABLE_AFTER_VALID_CHANGE /
FAIL
```

---

## 13. CPNG decision control

CPNG가 cutoff cohort에 포함됐다면 반드시:

```text
candidate
→ adjudication if needed
→ accepted decision
→ explicit BUY/HOLD/SELL message
```

까지 확인한다.

`투자 논리: 유지`만 있는 것은 v2 proof가 아니다.

---

## 14. Price Structure / Valuation

전 종목:
- current regular close
- near support/resistance
- major price-anchored structural levels
- completed Bollinger
- provisional Bollinger
- stored monitoring price rule
- security/share/currency basis
- safe valuation multiples
- N/M semantics
- forward caveats

Gates:

```text
US_PRICE_STRUCTURE_CONTRACT = PASS / FAIL
US_VALUATION_CONTRACT = PASS / FAIL
```

알고리즘 수정 금지.

---

## 15. Exactly-once / exact payload

수집:
- expected production count
- packet count
- intents
- sent
- received
- duplicates
- orphans
- unowned retries

그리고 모든 메시지에서:
- rendered
- outbound
- received/recorded

Gates:

```text
US_LIVE_EXACT_PAYLOAD = PASS / FAIL
US_EXACTLY_ONCE_DELIVERY = PASS / FAIL
US_DUPLICATE = 0 / NONZERO
US_ORPHAN = 0 / NONZERO
US_UNOWNED_RETRY = 0 / NONZERO
```

---

## 16. Message quality

전 stock message:
- explicit accepted BUY/HOLD/SELL
- Korean core wording
- BUY side bullish only
- SELL side bearish only
- neutral/Unknown separate
- no raw candidate
- no self-transition
- no empty section header
- no contradictory decision
- no order command

기록:

`US_EMPTY_VISIBLE_SECTION_COUNT = ...`

Gate:

`US_V2_MESSAGE_QUALITY = PASS / PARTIAL_SAFE / FAIL`

---

## 17. Root-cause taxonomy

v2가 빠졌다면 종목별 earliest failure stage를 하나만 선택:

```text
ONBOARDING_NOT_READY
PACKET_COHORT_EXCLUDED
CANDIDATE_NOT_GENERATED
ADJUDICATION_INCOMPLETE
ACCEPTED_PLAN_NOT_CREATED
PRODUCTION_SELECTOR_WRONG_ENGINE
RENDERER_WRONG_ROUTE
RENDERER_OMITTED_ACCEPTED_BLOCK
VALIDATOR_SUPPRESSED_BLOCK
DETERMINISTIC_FALLBACK_PATH
OTHER
```

그리고 scope:

```text
SYSTEMIC
SUBJECT_SPECIFIC
```

proof 단계에서는 수정하지 않는다.

---

## 18. Expected counts

CPNG가 cutoff 전에 ready였다면:

```text
US_ACTIVE_US_FOREIGN_COUNT = 14
US_EXPECTED_STOCK_MESSAGE_COUNT = 14
US_EXPECTED_PRODUCTION_MESSAGE_COUNT = 15
```

CPNG가 cutoff 이후 active면 actual cutoff count를 사용하고 그 근거를 남긴다.

---

## 19. Severity

P0:
- wrong recipient / secret exposure
- duplicate prod send
- raw candidate as final
- wrong ticker identity

Material P1:
- v2 absent systematically after cutover
- accepted decisions exist but renderer systematically omits BUY/HOLD/SELL
- old/fallback renderer used unexpectedly for cohort
- unadjudicated decision visible
- CPNG blocks ready peers
- material Price Structure/valuation contamination

P2:
- isolated wording
- minor density
- empty optional section

---

## 20. Final classification

```text
US_V2_NATURAL_LIVE =
PASS /
PARTIAL_SAFE /
FAIL
```

PASS:
- correct session
- frozen cohort correct
- CPNG handled correctly
- all accepted-ready subjects show explicit v2 decision
- raw candidate 0
- unadjudicated visible 0
- market message PASS
- Price Structure PASS
- Valuation PASS
- exactly-once PASS
- P0/P1 = 0/0

FAIL examples:
- CORZ-like old/fallback template systematic
- accepted decision exists but decision block absent
- selector still routes old engine
- cohort-wide fallback unexpectedly used

---

## 21. User-simple-message rule

사용자는 내부 로그를 제공할 필요가 없다.

사용자가 간단하게 몇 개 Telegram 메시지만 보내도:
- backend/runtime
- packet
- accepted decision store
- renderer route
- delivery evidence

로 full proof를 구성해야 한다.

사용자 메시지는 visual control일 뿐이다.

가능하면 비교:
- US market
- CORZ
- CPNG
- GOOGL
- SELL control 1개

---

## 22. Required reports

Create:
1. `20260901-us-v2-natural-live-run-identity.md`
2. `20260901-us-v2-runtime-lineage.md`
3. `20260901-us-v2-feature-state.md`
4. `20260901-us-v2-frozen-cohort.md`
5. `20260901-us-v2-cpng-live-control.md`
6. `20260901-us-market-message-proof.md`
7. `20260901-us-macro-night-futures.md`
8. `20260901-us-v2-candidate-adjudication-accepted.md`
9. `20260901-us-v2-renderer-route-audit.md`
10. `20260901-us-v2-corz-root-cause.md`
11. `20260901-us-v2-googl-control.md`
12. `20260901-us-v2-sell-controls.md`
13. `20260901-us-v2-price-structure.md`
14. `20260901-us-v2-valuation.md`
15. `20260901-us-v2-live-exact-messages.md`
16. `20260901-us-v2-live-delivery.md`
17. `20260901-us-v2-message-quality.md`
18. `20260901-us-v2-natural-live-proof.md`
19. `20260901-us-v2-artifact-index.md`

Machine-readable:
- `20260901-us-v2-live-decisions.json`
- `20260901-us-v2-renderer-routes.json`
- `20260901-us-v2-live-delivery.json`
- `20260901-us-v2-natural-live-proof.json`

---

## 23. Required gates

```text
MANUAL_US_PRODUCTION_JOB_TRIGGER = 0 / NONZERO
MANUAL_US_PRODUCTION_SEND = 0 / NONZERO
US_PRODUCTION_STATE_MUTATION = 0 / NONZERO

US_CANONICAL_SESSION_DATE = 2026-08-31 / OTHER
US_RUNTIME_LINEAGE = PASS / DOCUMENTED_DOC_ONLY_DESCENDANT / FAIL

US_ACTIVE_US_FOREIGN_COUNT = 14 / OTHER
US_CUTOFF_ELIGIBLE_STOCK_COUNT = ...

CPNG_CUTOFF_STATUS =
ACTIVE_READY_BEFORE_CUTOFF /
ACTIVE_READY_AFTER_CUTOFF /
NOT_READY /
OTHER

CPNG_V2_LIVE_STATUS =
PASS /
NOT_READY_SAFE /
EXCLUDED_AFTER_CUTOFF_SAFE /
MISSING_UNEXPECTED /
FAIL

CPNG_BLOCKS_OTHER_US_SUBJECTS = 0 / NONZERO
US_PACKET_UNIVERSE_MUTATED_AFTER_CUTOFF = 0 / NONZERO

US_MARKET_MESSAGE_QUALITY = PASS / PARTIAL_SAFE / FAIL
US_MACRO_TEMPORAL_SAFETY = PASS / PARTIAL_SAFE / FAIL
US_NIGHT_FUTURES = CURRENT_SAFE / SOURCE_LIMITATION_SAFE / OMITTED_OTHER_SAFE / FAIL

US_SAME_EVIDENCE_UNEXPLAINED_DECISION_CHURN = 0 / NONZERO
US_UNADJUDICATED_MATERIAL_CHANGE_VISIBLE = 0 / NONZERO

US_ACCEPTED_READY_COUNT = ...
US_NOT_READY_COUNT = ...
US_ACCEPTED_BUY_COUNT = ...
US_ACCEPTED_HOLD_COUNT = ...
US_ACCEPTED_SELL_COUNT = ...

US_RENDERER_ROUTE_IDENTIFIED_COUNT = ...
US_EXPLICIT_DECISION_BLOCK_VISIBLE_COUNT = ...
US_OLD_OR_FALLBACK_STOCK_MESSAGE_COUNT = ...
US_RAW_CANDIDATE_VISIBLE = 0 / NONZERO

CORZ_V2_STATUS = ...
GOOGL_V2_LIVE_CONTROL = ...
US_SELL_PATH_VISIBILITY = ...

PRIMARY_V2_ABSENCE_ROOT_CAUSE =
NONE /
ONBOARDING_NOT_READY /
PACKET_COHORT_EXCLUDED /
CANDIDATE_NOT_GENERATED /
ADJUDICATION_INCOMPLETE /
ACCEPTED_PLAN_NOT_CREATED /
PRODUCTION_SELECTOR_WRONG_ENGINE /
RENDERER_WRONG_ROUTE /
RENDERER_OMITTED_ACCEPTED_BLOCK /
VALIDATOR_SUPPRESSED_BLOCK /
DETERMINISTIC_FALLBACK_PATH /
OTHER

V2_ABSENCE_SCOPE = NONE / SUBJECT_SPECIFIC / SYSTEMIC

US_PRICE_STRUCTURE_CONTRACT = PASS / FAIL
US_VALUATION_CONTRACT = PASS / FAIL

US_EXPECTED_STOCK_MESSAGE_COUNT = 14 / OTHER
US_EXPECTED_PRODUCTION_MESSAGE_COUNT = 15 / OTHER
US_SENT_PRODUCTION_MESSAGE_COUNT = ...
US_RECEIVED_PRODUCTION_MESSAGE_COUNT = ...
US_LIVE_EXACT_PAYLOAD = PASS / FAIL
US_EXACTLY_ONCE_DELIVERY = PASS / FAIL
US_DUPLICATE = 0 / NONZERO
US_ORPHAN = 0 / NONZERO
US_UNOWNED_RETRY = 0 / NONZERO

US_EMPTY_VISIBLE_SECTION_COUNT = ...
US_V2_MESSAGE_QUALITY = PASS / PARTIAL_SAFE / FAIL

OPEN_P0 = ...
OPEN_MATERIAL_P1 = ...
OPEN_P2 = ...

US_V2_NATURAL_LIVE = PASS / PARTIAL_SAFE / FAIL
```

---

## 24. Completion response

Return:

```text
RUN_ID = ...
PACKET_ID = ...
US_CANONICAL_SESSION_DATE = 2026-08-31

PRIMARY_SCHEDULED = ...
PRIMARY_ACTUAL = ...
BACKUP_SCHEDULED = ...
BACKUP_ACTUAL = ...
PACKET_CLAIM_OWNER = ...
DISPATCH_TIME = ...
JOB_EXIT = ...

ORIGIN_MAIN = ...
OPERATING = ...
RUNTIME_CODE_SHA = ...
US_RUNTIME_LINEAGE = ...

VISIBLE_STOCK_DECISION_ENGINE = ...
V2_PRODUCTION_ENABLED = ...
FULL_MONITORED_STOCK_COVERAGE_TARGET = ...

US_ACTIVE_US_FOREIGN_COUNT = 14
US_CUTOFF_ELIGIBLE_STOCK_COUNT = ...

CPNG_CUTOFF_STATUS = ...
CPNG_V2_LIVE_STATUS = ...
CPNG_BLOCKS_OTHER_US_SUBJECTS = 0

US_MARKET_MESSAGE_QUALITY = ...
US_MACRO_TEMPORAL_SAFETY = ...
US_NIGHT_FUTURES = ...

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

US_ACCEPTED_READY_COUNT = ...
US_NOT_READY_COUNT = ...
US_ACCEPTED_BUY_COUNT = ...
US_ACCEPTED_HOLD_COUNT = ...
US_ACCEPTED_SELL_COUNT = ...

US_RENDERER_ROUTE_IDENTIFIED_COUNT = ...
US_EXPLICIT_DECISION_BLOCK_VISIBLE_COUNT = ...
US_OLD_OR_FALLBACK_STOCK_MESSAGE_COUNT = ...
US_RAW_CANDIDATE_VISIBLE = 0

CORZ_V2_STATUS = ...
GOOGL_V2_LIVE_CONTROL = ...
US_SELL_PATH_VISIBILITY = ...

PRIMARY_V2_ABSENCE_ROOT_CAUSE = ...
V2_ABSENCE_SCOPE = ...

US_PRICE_STRUCTURE_CONTRACT = ...
US_VALUATION_CONTRACT = ...

US_EXPECTED_STOCK_MESSAGE_COUNT = 14
US_EXPECTED_PRODUCTION_MESSAGE_COUNT = 15
US_SENT_PRODUCTION_MESSAGE_COUNT = ...
US_RECEIVED_PRODUCTION_MESSAGE_COUNT = ...
US_LIVE_EXACT_PAYLOAD = ...
US_EXACTLY_ONCE_DELIVERY = ...
US_DUPLICATE = 0
US_ORPHAN = 0
US_UNOWNED_RETRY = 0

US_V2_MESSAGE_QUALITY = ...

OPEN_P0 = ...
OPEN_MATERIAL_P1 = ...
OPEN_P2 = ...

US_V2_NATURAL_LIVE = ...

NEXT_ACTION =
NO_ACTION /
BOUNDED_RENDERER_ROUTE_REPAIR /
BOUNDED_DECISION_PIPELINE_REPAIR /
ROLLBACK_REVIEW

ZIP = ...
ZIP_SHA256 = ...
```

---

## 25. Mandatory ZIP

Create:
`20260901-us-v2-natural-live-readonly-verification-bundle.zip`

Include:
- exact instruction
- run identity
- runtime lineage
- feature state
- frozen cohort
- CPNG control
- exact US market message
- macro/night-futures evidence
- candidate/adjudication/accepted table
- renderer-route audit
- CORZ root-cause trace
- GOOGL control
- SELL controls
- Price Structure
- valuation
- exact production messages
- delivery evidence
- message quality
- final natural-live proof
- machine-readable JSON
- artifact index

Exclude:
- secrets
- Telegram recipient IDs
- tokens
- auth headers
- account identifiers
- hidden chain-of-thought

Compute SHA-256.

---

## Final principle

현재 보이는 CORZ 메시지만 보면 v2 decision block이 빠진 정황은 강하다.

하지만 이번 proof에서는 추측으로 끝내지 않고:

`candidate → adjudication → accepted → selector → renderer → delivery`

중 **처음 끊긴 지점을 정확히 찾아야 한다.**

proof 중 repair는 하지 않는다.
