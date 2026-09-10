# Thesis Monitor — 마스터 워크플로우

**버전:** 2026-09-10 / m12w-sol-restoration-semantic-stop-closeout-v1
**문서 성격:** 최신 실행 결과와 사용자 결정에 맞춘 프로젝트 기준선·작업 순서 갱신본.
**현재 위치:** `M12W Sol/xhigh transport 회복 관측 / 첫 context target 불일치 / 추가 호출 중단 / fresh real NOT_READY`
**운영 상태:** US/KR 예약 모니터링 중단 유지가 사용자 지시. 자동 재개 금지.
**M12W는 M12U 의미 계약과 source/prompt/schema를 그대로 두고 proof-critical 모델만 GPT-5.6 Sol/xhigh로 복원했다. 새 첫 context는 407.7초에 transport/schema 4/4를 반환했지만 FIC-FIN-01 BUY가 frozen 6.0 대신 6.5여서 전체 generation을 중단했다. 나머지 5개 context는 NOT_RUN이며 반복 안정성은 미측정이다. 재호출·hotfix·main merge·운영 변경은 0이다.**

---

## 1. 지금 프로젝트가 달성하려는 것

### 최신 M12W 결과

지시서 `e8441e0`, 구현 `538cb76` 순서로 동결했다. GPT-6 Astra는 proof-critical
경로에서 중단하고 `gpt-5.6-sol / xhigh`, 1,800초, 4종목/context, wrapper retry 0을
적용했다. M12U 금융 의미, target, fictional source, prompt, schema, selector와 운영 코드는
변경하지 않았다. 로컬 focused/full은 260/3255 PASS, Ruff/diff PASS다. Hosted CI는
3250 PASS/기존 portability 5 FAIL이며 M12W 신규 실패는 0이다.

새 generation `20260910-m12w-fictional-20260910T020309Z-f8b8bd468c5a`의 첫 호출은
407.720583초에 Sol/xhigh identity, parsed output, schema 4/4를 반환했다. Timeout, capacity,
CLI 내부 retry, wrapper retry, orphan은 모두 0이다. 그러나 FIC-FIN-01 BUY가 frozen target
6.0 대신 6.5여서 `frozen_ordinal_contract_inconsistent`가 발생했고 whole-generation stop을
적용했다. FIC-FIN-02/03/04는 해당 호출에서 PASS, 나머지 5개 context는 NOT_RUN이다.

따라서 Sol transport 회복은 한 context에서 관측됐지만 full 8x3 stability는 입증되지 않았다.
Fresh real과 production은 NOT_READY다. 다음 범위는
`BOUNDED_SOL_DIRECTIONAL_CONTRACT_REPAIR`; threshold 자동 변경, 현 generation 재개,
selective rerun, 모델 fallback은 금지한다. 예약 8개는 PAUSED 상태를 유지한다.
결과 근거: `docs/reports/20260910-m12w-completion.md`와 M12W reports 53/59/63/69.

아래 M12V 및 이전 단계는 역사적 결과이며 M12W 재실행 또는 운영 재개 승인이 아니다.

### 이전 M12V 결과

지시서 `f1da357`, architecture 결정 `2e50558`, 구현 `46ec85c` 순서로 동결했다.
선택한 단일 실험 계약은 `INCREASED_FINITE_ABSOLUTE_WATCHDOG`: 1,800초에서 2,400초로
한도를 늘리고 기존 lifecycle 관측기를 archive-only adapter에서 재사용했다. Wrapper retry 0,
4종목/context를 유지했으며 기존 app/runtime 파일과 M12U 금융 의미·prompt·schema는 변경하지 않았다.

새 generation `20260910-m12v-fictional-20260910T002912Z-cb6d03277dc8`은 첫 context에서
2,400.062226초에 MODEL_TIMEOUT으로 종료됐다. 시작 09:29:20 KST, 종료 receipt 10:09:24 KST.
stdout/최종 출력 0, CLI에 기록된 내부 retry 0, wrapper retry 0, orphan 0이다.
나머지 5개 context는 NOT_RUN. 679개 동결 코드/계약 파일은 실행 후에도 동일하다.
금융 semantic/core/formal/stance/delta 안정성은 NOT_MEASURED이며 PASS로 승격하지 않는다.

40분 finite tail tolerance로 충분하다는 가설은 이번 호출에서 입증되지 않았다.
백엔드가 요청을 받았는지, 추론 중이었는지, 전송이 멈췄는지는 현재 관측으로 확정할 수 없다.
다음 범위는 `ASTRA_FINITE_2400_TAIL_TOLERANCE_ASSUMPTION_REVIEW`이며 새 실행 승인은 별도다.
현재 generation 재개, 자동 timeout 증가, 재시도, context 분할, 실종목 실험은 금지한다.

집중 243/full local 3238 PASS, Ruff/diff PASS. 구현 hosted CI는 3233 PASS/기존 portability
5 FAIL이며 M12V 신규 실패 0이다. P0 0/P1 2(runtime proof 실패, 기존 hosted CI backlog).
예약 8개 PAUSED 유지, main merge/deploy/운영 변경 0. Fresh real 및 production NOT_READY.
결과 근거: `docs/reports/20260910-m12v-completion.md`와 M12V reports 56/70/72/86.

아래 M12U 및 이전 단계는 역사적 결과이며 M12V 재실행 또는 운영 재개 승인이 아니다.

### 이전 M12U 결과

지시서 `459af10`, 오프라인 계약 검토 `f73ce3a`, 구현 `551f98f` 순서로 동결했다.
명시적 비적용의 명사 보어 표현을 generic classifier에서 허용하되 실제 적용/모순/산업재 anchor는 차단한다.
서로 다른 evidence category가 곧 경제적으로 독립된 근거는 아니다. 미확인 재융자 부담에 의존한
시장기대는 같은 위험의 중복 corroboration이므로 해당 패턴은 HOLD 4.5:5.5 SELL_LEAN이다.
확인된 별도 위험과 독립된 현재 기대 불일치는 추가 근거가 될 수 있다. 숫자 threshold/증분/tie-break는 그대로다.
한 문단 외 prompt, source, schema, selector, financial grounding, Daily Delta, Price-Timing, renderer 및 runtime은 동결했다.

새 generation `20260910-m12u-fictional-20260909T231913Z-1e045065810d`의 첫 context가
출력 없이 1,800.068784초 MODEL_TIMEOUT으로 종료됐다. 1회 시도/출력 0건, 이후 5개 context NOT_RUN.
내부 retry/wrapper retry/orphan은 0. 실제 semantic/core/formal/stance/delta 안정성은 NOT_MEASURED이다.
집중 186/full local 3225 PASS, Ruff/diff PASS. Hosted CI는 기존 portability 5건 실패, M12U 신규 실패 0.
P0 0/P1 2(timeout 재발, 기존 hosted CI). 8개 예약 중단 유지, main/운영 변경 0.
다음은 `ASTRA_TRANSPORT_RUNTIME_ARCHITECTURE_REVIEW`. 현재 generation 재개/재시도/timeout 증가는 금지한다.
결과 근거: `docs/reports/20260910-m12u-completion.md` 및 M12U reports 79/81/82.

아래 M12T 및 이전 단계는 역사적 결과이며, M12U 실행 안정성이나 운영 재개 승인을 뜻하지 않는다.

### 최신 M12T 결과

M12E/M12F prompt와 schema는 generation ID 외 동일하고 격리·watchdog 결함은 발견되지 않았다.
분류는 `TRANSIENT_WEBSOCKET_OR_SERVICE_DEGRADATION_LIKELY`이며 정확한 내부 원인은 미확정이다.
지시서 `09f434f`, 구현 `695464f`를 동결한 새 generation은 두 호출 모두 321.70초/331.91초에 반환했다.
timeout, CLI 내부 retry, wrapper retry는 모두 0이다. 그러나 FIC-FIN-05가 동결된 HOLD 4.5:5.5 대신
입력의 market-expectation을 별도 부정 근거로 해석해 SELL 4:6을 선택했고, FIC-FIN-08의
"일반 사업회사의 부채·운전자본 틀은 적용 대상이 아니다"가 false reject됐다.
schema 8/8, 최종 gate 6/8; 이후 4개 context는 시작하지 않았다. 3회 안정성은 미측정이다.
추가 모델 호출·수정·재시도·main merge·운영 변경은 0. 8개 예약 중단 유지.
집중 140/full local 3179 PASS, Ruff/diff PASS. Hosted CI는 기존 portability 5건 실패 유지,
M12T 신규 실패 0. P0 0/P1 3; fresh real 및 production NOT_READY.
다음은 generic 명시적 비적용 범위와 leverage/기대 근거 독립성의 bounded repair이다.
결과와 원본 구분은 `docs/reports/20260910-m12t-completion.md` 및 M12T report 62/63을 따른다.

```text
사용자가 원하는 종목
    ↓
기업·거래주식 식별 / 기존 무료 데이터 경로 확인
    ↓
검증된 자료 수집 / 필수 근거 충족 여부 판단
    ↓
초기 분석과 절대 투자 판단
    ↓
사용자가 명시적으로 모니터링 등록 요청
    ↓
버전형 투자 논리 기준선 저장
    ↓
초기 자료 보강 / source sufficiency / monitoring readiness
    ↓
기준선 이후 새로운 사건에 대한 Daily Delta
    ↓
기존 투자 논리의 변화 + 현재 절대 판단 + 가격·타이밍을 구분한 메시지
```

여기서 반드시 구분한다.

| 질문 | 담당 |
|---|---|
| 현재 사업·재무·가치평가 근거가 어떤 방향을 지지하는가? | Directional Core |
| 실제 확보된 가격·기술적 자료에서 진입·재점검 조건은 어떤가? | Price-Timing |
| 이전 기준선 이후 투자 논리를 바꿀 새 사실이 생겼는가? | Daily Delta |
| 최종 행동 표현을 어떻게 일관되게 표시하는가? | Structured state + Renderer |

좋은 기업, 유리한 주가, 오늘의 투자 논리 변화는 같은 판단이 아니다. `BUY/HOLD/SELL`은 매수·매도 주문을 실행하는 기능이 아니며, `BUY:SELL` 배점을 확률이나 수익률로 설명하지 않는다.

---

## 2. 문서의 근거와 우선순위

### S0 — 현재 권위 M4 결과

```text
thesis-monitor-20260908-source-domain-enrichment-directional-specificity-design-review-report.zip

실제 SHA-256:
4e575e3b2b6881025285865be4c996d335f587c880dabe27b4166c2322802dc7
```

M5 시작 시 M4 ZIP checksum과 unzip integrity를 재검산해 PASS를 확인했다. 실제 M4 final SHA는 `1f39271b6d7e161dc86bc11d71dd111b2b48937d`다. M4 `program-completion`의 `final_head_sha`/`report_commit=NOT_MEASURED`는 역사적 보고 누락으로 보존하며 의미 drift로 간주하지 않는다.

### S1 — 상위 실모델 실행 결과

```text
thesis-monitor-20260908-authoritative-result-identity-reconciliation-us-source-expansion-proof-resume-report.zip

실제 SHA-256:
2a58b8e8dbfcc6e3aa7cb4900bec2d16d29f149b69160e8fd0c5b0522f6a798e
```

첨부 체크섬과 일치한다. 전체 파일 2,008개, index 자체를 제외한 payload 2,007개의 hash·크기가 일치했다. 원본 출력 29개는 각각 동봉 schema 검증을 통과했다. 이는 문서 작성 시 로컬 산출물 검증이며 저장소 테스트나 현재 서버 조회가 아니다.

### S2 — 기존 engineering handoff

`thesis-monitor-new-session-system-prompt-handoff-bundle(1).zip`의 다음 문서를 기반으로 했다.

- `00_START_HERE.md`, `01_SYSTEM_PROMPT_FULL.md`
- `04_ARCHITECTURE_CONTRACTS.md`
- `05_EXPERIMENT_AND_PROMOTION_PROTOCOL.md`
- `06_MONITORING_BOOTSTRAP_AND_LIVE_ROADMAP.md`

기존 roadmap의 “지금은 synthetic canary fixture repair”와 과거 untouched cohort 선언은 **역사적 상태로 남기고 현재 작업에서는 대체**한다.

### S3 — 투자·자료 안전 기준

`Investment Thesis Analysis & Monitoring Knowledge Guide v3`.

### S4 — 이 대화의 최신 사용자 결정

무료 데이터 경로만 사용, 새로운 무료 API 관리 게이트 개발은 후순위, US 실패로 KR의 안전한 독립 진단을 생략하지 않음, 기존 예약 일시 중단, 자동 재개 금지, 일곱 종목의 재무정보 활용 범위 논의는 나중에 판단 구조 검토에서 다시 다룸.

관심사별 권위를 분리한다. 현재 단계 입력은 S0, 역사적 실모델 실행은 S1, 현재 코드는 실제 HEAD/worktree, 다음 변경 권한은 현재 작업지시서, 투자 안전은 S3, 운영 중단·비용 정책은 S4를 따른다. 보고서와 raw 실행이 충돌하면 원본은 수정하지 않고 별도 정정 기록을 남긴다.

검토한 첨부 안에는 독립적인 기존 `MASTER_WORKFLOW` 파일이 없었다. 이 문서는 기존 handoff roadmap을 최신 결과로 통합한 갱신본이다. 실행자는 저장소에 실제 canonical master가 있는지 확인해 그 문서에 반영하고, 없다면 하나의 경로를 정한다. 여러 master를 병행해 서로 다른 현재 상태를 만들지 않는다.

---

## 3. 최신 상태 장부: 구현·실증·운영을 분리

| 영역 | 근거가 있는 상태 | 아직 주장할 수 없는 것 |
|---|---|---|
| 무료 자료 기반 신규 기업 준비 | 최신 US 11개 검사 중 4개, KR 16개 중 12개 통과; 새 cohort/source lock 생성 | 모든 미국·한국 종목의 정상 등록·갱신 보장 |
| 환경설정·runner/adapter·ID·namespace | 이전 결함 수리 후 최신 실제 29회 출력 생성, namespace 충돌 0 | 향후 모든 실행의 무장애 보장 |
| Directional Core / Timing 역할 분리 | 최신 FIRST/A/B 전체 run의 hard gate PASS로 보고 | C 전체, 실종목 일반화 전체 PASS |
| Unknown 교차필드 일관성 | 공통 invariant와 Core 조기 검사를 구현; NEON 원본은 Core에서 즉시 거절 | 수정 prompt의 실제 모델 출력 개선 |
| Directional calibration | 수정된 계약과 과거 가상 반복 PASS 존재 | 실종목 경계 변동 해결 |
| 메시지 품질 | FIRST/A/B 48개 전체 trace 완료; 기존 반복 advisory 유지 | Renderer ownership PASS를 메시지 내용 PASS로 확대 |
| 기존 코드와 새 판단 경로 연결 | 기존 경계 10/10 재검증, lifecycle-qualified nonproduction adapter와 file-only renderer 검증 완료 | production 전체 연결이나 실등록 E2E 완성 |
| Monitoring Bootstrap / Daily Delta 연결 | 격리 SQLite에서 canonical 등록·evidence·baseline·resume·daily monitor 실행, fixture lifecycle 12/12 PASS | production DB·실등록·실발송 검증 |
| 재무 source-domain 설계 | 전년동기 비교, OCF, PPE-only cash conversion, debt/liquidity, working capital, non-operating effects 6/6 계약과 업종 적용성 동결 | source producer 활성화, packet extension 구현, prompt/모델 검증 |
| 예약 운영 | M3 시작 관측에서 승인된 8개 중단, 변경 0 | 예약 재개나 현재 운영 activation |
| 운영 반영 | 최신 작업의 live V2·등록·발송·production DB 변경 0 | 새 판단 구조의 live activation |

### 최신 실모델 실행 장부

| Run | Core 원본 | Timing 원본 | 완전한 run gate |
|---|---:|---:|---|
| FIRST | 16행 | 16행 | Ownership / renderer / hard-safety PASS |
| A | 16행 | 16행 | PASS |
| B | 16행 | 16행 | PASS |
| C | 16행 | 4행 | 부분 실행 후 중단; 전체 gate NOT_MEASURED |

```text
계획 context 32
실제 호출·raw 문서 29
Transport 출력 생성 성공 29
Context 부분 의미 검사 PASS 28 / FAIL 1
Core 원본 64행 / Timing 원본 52행
고유 기업 16개
완성된 조합 결과·메시지 각각 48개
공식 안정성 NOT_MEASURED
전체 일반화 NOT_ESTABLISHED
```

S1 최상단 `C = NOT_RUN`은 상세 실행과 맞지 않는다. 마스터의 현재 해석은 **C 5개 context 실행 후 부분 실패**다. 원본 최상단 값을 덮어쓰지 않고 다음 작업에서 정정 보고·생성 로직을 정리한다.

`failed_real_contexts=0`도 transport 기준이다. 의미 검증 실패까지 0이라는 뜻이 아니다. 미측정 안정성의 0-filled counter는 PASS가 아니다.

[S1: `completion.json`; `experiment/fresh-real-proof/model-contexts/`; `reports/fresh-real-internal/proofs/`; `reports/proofs/60-fresh-directional-core-stability.json`]

---

## 4. 현재 결함과 독립적인 후속 질문

### 4.1 지금 수리할 결함: Unknown 표현과 조기 검사

NEON C Core의 같은 항목에 다음이 함께 있다.

```text
treatment = CONFIRMATION_REQUIRED
directional_negative_basis = ["E02"]
```

현재 계약상 이 조합은 `unknown_nonnegative_has_directional_basis`를 발생시킨다. E02는 실제 과거 공식 손실을 가리킨다. 문제는 “손실 사실”과 “현재 상황의 추가 확인 필요”를 동일 Unknown 처리 안에서 충돌하게 작성한 것이다.

정상 구분:

```text
과거 손실이 확인됨 → 해당 사실·위험·매도 근거 필드에서 기간·한계를 보존
현재도 지속되는지는 미확인 → Unknown/확인 필요로 별도 표현
```

유효한 손실 사실을 무조건 삭제하거나, 결측을 부정 근거로 바꾸거나, 모델 판단을 HOLD로 강제하지 않는다.

이 충돌은 Core 원본에 존재했고 Core 직후에는 PASS, Timing 이후 조합 검사에서 FAIL이었다. 최신 증거는 **작성 계약과 검출 시점의 보완 필요**를 지지한다. Timing이 방향을 바꿨다는 증거는 아니다.

[S1: C/Core/batch-01 `output.raw.json`, C/Timing/batch-01 `prompt.txt`, `partial_semantic_audit.json`]

### 4.2 판단 안정성: 별도 분석 후 결정

FIRST/A/B는 방향이 같았지만, C에서는 RMD·AA·TDW·014820·318060·106240·263750이 0.5점 차이로 분류 경계를 넘었다. 이는 원본의 **사후 기술적 비교**이며 공식 안정성 결과가 아니다.

다음 분석은 canonical evidence identity, 현재성, Unknown, 근거 선택, 배점과 문장을 함께 비교한다. 같은 E02 alias를 다른 context의 같은 사실이라고 취급하지 않는다. 이전 cohort에서 확인했던 calibration 원인을 새 cohort에 자동 적용하지 않는다.

다수결·평균·합격 run 선택·임계값 변경으로 결과를 안정돼 보이게 만드는 것은 금지한다.

### 4.3 메시지 품질: 문장 다양화만의 문제가 아님

완주한 세 run의 반복 문구 수는 FIRST 13, A 16, B 21이다. 당시에는 advisory였으며 사후에 hard gate로 바꾸지 않는다.

다음에는 반복된 안전 헤더와 실질적인 종목 설명을 구분하고, 원인이 입력 압축인지 모델 설명인지 renderer인지 추적한다. 없는 정보를 넣거나 종목명만 바꿔 반복 탐지를 피하지 않는다.

### 4.4 수집 원자료 → 판단 입력의 충분성

일곱 종목 독립 검토에서 논의한 현금흐름·차입·전년 비교 등 원자료 활용 범위는 **사용자가 별도 판단 구조 논의로 미룬 항목**이다.

중요도가 낮다는 뜻은 아니다. 상태는 `DEFERRED_EXPLICIT_DECISION_REQUIRED`다. 이번 필드 수리에 묶어 조용히 입력을 넓히지 않는다. 이후 메시지를 문장만 다듬어 개선됐다고 결론 내리기 전에, 이 입력 범위 문제를 다시 논의한다.

---

## 5. 갱신된 전체 진행 순서

```text
M0  자료·실행 기반과 실험 무결성 확보
    [한정 범위의 완료 증거 유지]
        ↓
M1  Unknown 필드 일관성 / Core 조기 검사 수리
    + 기존 64 Core·52 Timing·48 메시지 오프라인 분석
    + 기존 코드 연결 경계 조사
    [CODE + OFFLINE EVIDENCE REVIEW COMPLETE]
        ↓
M2  기존 코드와 발송 없는 통합 / 판단·메시지 품질 개선
    [NONPRODUCTION INTEGRATION + OFFLINE DECISION COMPLETE]
        ↓
M3  명시적 신규 등록 → baseline → bootstrap → Daily Delta
    격리된 환경에서 lifecycle 연결 검증
    [COMPLETE: 운영 DB·실등록·발송 없음]
        ↓
M4  source-domain enrichment / Directional specificity 설계 검토
    [COMPLETE: 6개 금융 도메인 계약과 구현 순서 동결]
        ↓
M5  DecisionEvidencePacket financial_context 확장
    [COMPLETE: additive optional schema + hard validation]
        ↓
NEXT  Existing Canonical Financial Domain Adapter
    기존 전년동기·OCF·PPE canonical Fact만 packet으로 연결
        ↓
LATER  추가 source mapping → Directional specificity → model/holdout
    [각각 별도 승인과 검증]
        ↓
M6  사용자의 명시적 예약 재개 승인
    통제된 US/KR 자연 실행 확인 → 일상 모니터링
```

M2와 M3의 저장소 조사·테스트 설계는 일부 병행할 수 있다. 하지만 **불확실한 판단 입력·규칙을 그대로 둔 채 최종 proof와 production readiness를 먼저 선언하지 않는다.** 큰 의미 변경이 정해지면 그 변경을 동결한 뒤 최종 검증한다.

M1이 끝날 때마다 새 16종목·32호출을 자동 시작하지 않는다. 현재 단계의 실제 blocker를 보고 다음 한 작업을 결정한다.

---

## 6. 단계별 목적·산출물·종료 조건

### M0 — 기존 기반: 다시 만들지 않을 범위

범위: 기존 무료 source 경로, 기업/주식 identity, source sufficiency, 가격 선택자료 분리, protected env 연결, runner↔adapter, runtime identity, context namespace/workdir, 단일 watchdog, 즉시 출력 보존, issuer-level exclusion.

상태: 과거와 최신 결과에서 각 수리 및 한정 실행 증거 확보.

재개 조건: 새로운 직접 증거로 결함이 확인되거나 관련 코드가 변경됐을 때만 해당 경로를 재검증한다. “혹시 모르니” 모든 가상 probe·universe scan을 반복하지 않는다.

Source PASS는 분석을 시작할 근거이지, 투자 매력이 충분하거나 모든 지표가 완전하다는 보장이 아니다. 가격자료의 `UNAVAILABLE_SAFE` 허용은 필수 재무근거 기준 완화가 아니다.

### M1 — 완료: 좁은 수리 + 증거 분석

실행 문서: `20260908-unknown-field-consistency-early-core-validation-offline-evidence-review.md`.

허용:
- Unknown producer 규칙·공통 검증기·Core 조기 검사 연결의 제한적 수리.
- Exact NEON 실패 재현과 허용·거절 사례를 포함하는 offline 회귀.
- 64 Core·52 Timing의 적용 가능한 감사.
- 48 완성 메시지의 provenance·구체성·반복 원인 점검.
- 실제 저장소에서 기존/공유/실험 전용 코드 경계 조사.
- 마스터 현황과 다음 결정 갱신.

호출 예산: **실제 모델 0 / 가상 모델 0 / AI judge 0 / provider 수집 0**.

완료 근거:
- 구현 커밋 `df8ffb7`: Unknown treatment/basis invariant를 공통 helper로 만들고 Core partial audit와 최종 validator가 공유한다.
- exact NEON C Core는 `unknown_treatments[0].directional_negative_basis`에서 `unknown_nonnegative_has_directional_basis`로 조기 거절된다.
- offline fixture 10/10 PASS. 유효한 `DIRECTIONAL_NEGATIVE`와 별도 확인 필요 Unknown은 보존한다.
- 보존 자료 감사: Core 64/64, Timing 52/52, 완성 메시지 48/48. 예상된 NEON 계보 외 신규 의미 실패 0.
- B→C 절대 방향 경계 이동 7개, 직접 BUY↔SELL 반전 0. C는 완성 run이 아니므로 공식 안정성은 `NOT_MEASURED`.
- source registry 149개에 현재 16개 canonical issuer를 보고서 artifact에서 idempotent하게 합쳐 165개로 조정했고, 2차 적용 추가 0을 확인했다.
- prompt 문구와 hash가 바뀌었으므로 model emission effectiveness는 `NOT_MEASURED`; 기존 calibration 결과를 새 prompt에 이전하지 않는다.
- 모델/provider/DB/send/registration/main/deploy 변경은 모두 0이며 승인된 8개 예약 중단을 유지했다.

종료 조건:
- 원래 잘못된 raw는 조기 검사에서도 거절된다.
- 유효한 사실과 Unknown을 바르게 나눈 fixture는 통과한다.
- 기존 owner·accounting·security·source 안전 규칙을 약화하지 않는다.
- 수정 효과는 `코드·offline 회귀 통과`로 한정하고 model emission은 미측정으로 남긴다.
- 안정성·메시지 문제의 다음 변경 범위가 근거와 함께 정리된다.

Prompt가 바뀌면 신규 hash·revision을 기록한다. Calibration ladder가 그대로라고 whole prompt hash까지 그대로라고 보고하지 않는다.

### M2 — 완료: 공통 판단 경로와 메시지의 비운영 통합

실행 문서: `20260908-nonproduction-integration-and-decision-message-quality-review.md`.

M1의 module inventory를 바탕으로 기존 기능을 재사용했다. 새 판단 엔진을 legacy DB 상태 변경이나 발송 경로에 연결하지 않았다.

주요 확인:
- 기존 분석·모니터링 코드와 실험 runner 사이 실제 공유/중복 부분.
- Absolute judgment와 Daily Delta 필드의 일관된 구분.
- Unknown과 확인된 위험이 메시지에도 구분되는지.
- 종목 고유 근거·다음 확인 항목이 출력에 남는지.
- 메시지 반복이 입력 부족인지, 추론 일반화인지, renderer 중복인지.
- 일곱 종목에서 제기한 raw-to-Core 정보 활용 범위의 재논의 필요성.

완료 근거:
- 기존 production/shared 경계 10/10을 현재 HEAD에서 다시 확인했다.
- `INITIAL_ABSOLUTE`, `MONITORING_BASELINE`, `DAILY_DELTA`를 분리하는 pure nonproduction adapter를 추가했다.
- 명시적 monitoring intent가 없으면 registration intent를 만들지 않고, onboarding 미완료는 monitoring-ready가 아님을 fixture로 확인했다.
- bootstrap enrichment, missing refresh, price-only movement, Unknown을 각각 daily strengthened, no-material-change, fundamental delta, negative evidence로 바꾸는 경로를 차단했다.
- 기존 DecisionEvidencePacket, Directional Core, Price-Timing, composition, validator, renderer 계약을 그대로 재사용했다. 모든 새 메시지는 `OFFLINE_NONPRODUCTION_DERIVATIVE`다.
- 보존 16종목의 8개 domain을 source → normalized → packet → owned Core → rendered reasoning 순서로 감사했다. 보존 packet에서 Core로 떨어진 대상 domain은 0이다.
- 기간 구분과 valuation-unavailable 맥락은 이미 Core에 공급된다. 전년 비교, OCF/PPE-CAPEX, debt/liquidity, working capital은 이 보존 cold-start archive에 없으며 Core drop으로 분류하지 않는다.
- 명시적 non-operating/financial-income attribution은 operating income과 net income의 단순 차이로 만들 수 없어 별도 design decision으로 남겼다.
- 48/48 보존 메시지와 반복 cluster 50개를 다시 추적했다. 실질 반복은 주로 model-owned 문장과 stable renderer wrapper 안의 model content이며, 희소·동형 입력이 함께 제약한다.
- renderer가 종목별 재무 분석을 새로 쓰거나 synonym으로 반복을 숨기는 변경은 하지 않았다.
- 실제/가상/judge model, provider, production DB, 등록, assessment, warning, queue, send, main merge, deploy, live V2, Night Futures, scheduler resume는 모두 0이다.

일반 문장만 바꾸지 않는다. 입력/추론 변경이 필요하면 별도 bounded change로 결정한다. Stable output과 충분한 투자 근거는 별개의 합격 조건이다.

종료 조건은 충족했다. 단, lifecycle bootstrap의 실제 격리 연결과 새 model emission은 각각 `NOT_MEASURED`다. 새 지시서 없이 M3, 실모델 proof, production 작업을 자동 실행하지 않는다.

### M3 — 완료: 신규 편입과 기존 보유 종목의 lifecycle 연결

실행 문서: `20260908-nonproduction-monitoring-bootstrap-and-daily-delta-lifecycle-integration.md`.

격리된 SQLite와 fixture repository에서 다음 상태 전이를 검증했다.

```text
명시적 등록 → 저장된 투자 논리 버전
→ 자료 보강 필요 / 준비 상태
→ 유효 baseline 및 기준시점
→ 기준선 이후 첫 새 사건
→ Daily Delta
```

완료 근거:
- 실제 `register_monitoring_item_with_continuation`, `build_initial_evidence`, `ensure_initial_baseline`, `resume_onboarding_subject`, `run_daily_monitor`를 인메모리 SQLite에서 fixture dependency로 실행했다.
- 같은 명시적 등록의 thesis version 1개, baseline 1개, 다음 날짜 Daily Delta 1개, notification row 0개를 확인했다.
- 12개 필수 fixture가 모두 통과했다. bootstrap·늦게 도착한 pre-baseline 사실은 Daily Delta로 승격되지 않았다.
- refresh 누락은 `needs_review`이며 `no_material_change`로 바뀌지 않는다. price·supply·valuation만으로 business thesis delta를 만들지 않는다.
- positive, negative, invalidation-candidate의 post-cutoff business evidence와 warning open/resolve, assessment 멱등성을 검증했다.
- 신규·기존 종목이 같은 Directional Core / Price-Timing / validator / renderer 계약을 사용한다. 12개 메시지는 모두 file-only `OFFLINE_NONPRODUCTION_DERIVATIVE`다.
- 모델·provider·production DB·실등록·warning persistence·notification queue·send·main merge·deploy·V2·Night Futures·scheduler resume는 모두 0이다.

M3 완료는 lifecycle semantics의 비운영 증명이다. production readiness는 `NOT_READY`이며 예약 작업은 자동 재개하지 않는다.

### M4 — 완료: source-domain enrichment / Directional specificity 설계

무료·공식 source stack에서 전년동기 비교, OCF, PPE-only cash conversion, debt/liquidity, working capital, non-operating effects의 6개 도메인을 분류했다. `DecisionEvidenceRef`에 optional typed financial context가 먼저 필요하다는 결론과 `schema → existing canonical adapters → additional mappings → Directional specificity → sector gate review` 순서를 동결했다.

M4는 설계 단계였다. 실제 packet schema, source producer, prompt, 모델, 실종목 holdout, production을 바꾸지 않았다.

### M5 — 완료: DecisionEvidencePacket 금융 컨텍스트 확장

`DecisionEvidenceRef.financial_context`에 다음을 typed metadata로 추가했다.

```text
canonical metric / verified financial currency / explicit unit scale
QTD | YTD | FY | TTM | POINT_IN_TIME
entity scope / statement basis / total-parent-common attribution
DIRECT_REPORTED | DERIVED_SAFE
verified | partial quality
comparison lineage / derivation lineage / bounded limitations
```

기간 구조, inclusive duration, 통화 필요성, direct/derived 일관성, ordered input refs와 중복, 빈 식별자를 fail-closed한다. 회계 의미의 비교 가능성, debt component completeness, sector applicability, trade AR 범위와 attribution completeness는 다음 domain adapter validator 책임으로 남겼다.

기존 14개 archived `DecisionEvidencePacket`은 모두 parse됐고 `financial_context`가 없는 canonical serialization SHA가 M5 전 기준과 같았다. 새 내부 JSON schema는 optional field를 포함하지만, M5 항목을 제거한 legacy projection SHA는 과거 frozen schema SHA와 일치한다. Public Action 0.4.5와 20개 operationId에는 이 내부 타입이 노출되지 않는다.

생산 builder emission, compact AI context 소비, source sufficiency, Directional/Price-Timing prompt, provider, 모델, DB, queue, 발송, main/deploy, 예약 재개는 모두 0이다. production readiness는 `NOT_READY`다.

### M6 — 완료: 기존 canonical 금융 도메인 adapter

공유 `existing-canonical-financial-domain-adapter-v1`을 추가해 기존 `canonical_cash_flow_fact`만 M5의 optional `financial_context` envelope로 연결했다. 허용 범위는 전년동기 동일기간 비교 lineage, direct reported OCF, direct reported PPE-only 취득 현금유출, 그리고 동일 period/currency/unit/entity/statement/attribution의 기존 OCF·PPE Fact를 입력으로 갖는 `ocf_less_ppe_capex`다.

보존된 Phase 9 canonical 606개 행에서 330개 context를 안전하게 구성했다. 구성은 OCF 122, PPE 104, OCF-PPE 104이며 130개에는 compatible prior-year comparison lineage가 붙었다. 나머지 276개는 projection에 완전한 derived-period metadata가 없어서 OCF 102, PPE 87, OCF-PPE 87을 그대로 fail-closed했다. 이는 source fact 손실이나 0 대체가 아니라 다음 mapping/projection subpackage의 명시적 backlog다.

KR OpenDART OCF/PPE는 정확한 duration period가 없는 경우 계속 차단된다. 단위 scale 변환과 FX, maintenance capex 추론, management-defined FCF 명칭, debt/liquidity·working capital·non-operating 도메인은 추가하지 않았다. 새 SEC/OpenDART/provider mapping은 0개다.

내부 packet instance에는 eligible `financial_context`가 생기지만 compact AI context는 before/after byte-equivalent다. Directional/Price-Timing prompt, source sufficiency, Daily Delta, renderer, 모델 호출, provider fetch, DB·queue·발송·deploy·예약 상태는 변하지 않았다. focused 482개와 전체 2887개 테스트, Ruff, diff check가 통과했다. production readiness는 `NOT_READY`이며 모니터링은 중단 상태를 유지한다.

### M7 — 완료: 금융 lineage와 KR duration-period projection

`canonical-financial-lineage-projection-v1`을 추가해 선택된 canonical cash-flow Fact와 compatible prior-year Fact, 그리고 기존 derived Fact의 ordered input closure를 packet builder의 내부 adapter 입력으로 projection한다. support-only 행은 `ARCHIVE_ONLY`이고 prose·interpretation·numeric registry 및 compact AI context에는 노출되지 않는다. formula, derivation version, ordered input Fact/source ref, fiscal period, currency/unit, issuer/entity/statement basis와 source occurrence identity를 digest로 고정하며 누락·충돌·순서 불일치는 계속 fail-closed한다.

보존된 Phase 9 canonical 606개 행을 새 source 계산 없이 재검증한 결과 606개 모두 typed context로 재현됐다. OCF 224, PPE 191, OCF-PPE 191이며 compatible prior-year comparison은 164개다. M6에서 차단됐던 derived-period OCF/PPE 189개와 그 입력 lineage가 필요했던 OCF-PPE 87개가 기존 formula/version/input identity projection으로 해소됐다. 새 derivation, SEC/OpenDART taxonomy mapping, ticker-specific 예외는 0개다.

OpenDART duration mapper는 XBRL의 exact entity, taxonomy, amount, KRW unit, statement basis, duration start/end가 한 occurrence로 일치할 때만 기간을 채운다. 보고서 코드만으로 1월 1일이나 분기 시작일을 추정하던 경로는 제거했다. 비달력 결산을 포함한 synthetic contract fixture는 통과했지만 저장소에는 실제 KR canonical cash-flow Fact가 없으므로 issuer coverage는 여전히 `SOURCE_PRESENT_BUT_PERIOD_BLOCKED`다. KR OCF 7개와 보험 제외 PPE 6개의 실제 period block은 유지하며, 이는 mapper 기능과 시장 coverage를 분리한 결과다.

compact AI context, Directional/Price-Timing prompt, source sufficiency, Daily Delta, renderer, model/provider, production DB·queue·send·deploy는 변하지 않았다. focused 252개와 전체 2920개 테스트, Ruff, diff check가 통과했다. production readiness는 `NOT_READY`이며 승인된 8개 모니터링 경로는 중단 상태를 유지한다.

### M8 — 완료: source-class financial mapping

OpenDART CFS/OFS의 exact taxonomy·amount·KRW unit·entity·duration·statement-basis member·filing identity가 일치할 때만 canonical OCF/PPE fact를 승격한다. 실제 보존 KR 7종목에서 OCF 7개와 보험 제외 PPE 6개를 재현했다. HUT은 preserved PPE source occurrence 부족, SKHY는 issuer occurrence 부재로 ticker 예외 없이 defer했다.

### M9 — 완료: interest-bearing debt와 liquidity mapping

`interest-bearing-debt-liquidity-v1`은 direct `cash_and_cash_equivalents`, 명시적 current/non-current borrowings·bonds·notes·convertible debt, 별도 restricted cash와 lease-liability context를 POINT_IN_TIME fact로 만든다. `interest_bearing_debt_total`은 current와 non-current scope가 모두 있고 component가 non-overlapping이며 date/currency/unit/entity/statement/document가 호환되는 경우에만 생성한다. `net_debt`는 이 complete total에서 같은 기준의 cash and cash equivalents만 차감한다. restricted cash, marketable securities, price currency와 ADR ratio는 사용하지 않는다. 음수 net debt는 같은 공식의 유효한 결과다.

기존 `FinancialSnapshot.debt`는 OpenDART `부채총계`를 담는 legacy ambiguous field로 확인됐다. M9 canonical bridge는 이를 사용하지 않으며 total/current/non-current liabilities semantic을 debt 입력으로 명시적으로 거부한다. lease liability는 `SEPARATE_CONTEXT_ONLY`, restricted cash는 `EXCLUDE_FROM_NET_DEBT_CASH_BASIS`로 동결했다. 은행·보험·재보험은 industrial net-debt 경로 대신 `SECTOR_FRAMEWORK_REQUIRED`로 분리한다.

보존된 실제 KR archive에서는 비금융 6곳 중 5곳이 complete debt total과 net debt로 재현됐다. `010120`은 전환우선주부채 의미가 불명확해 PARTIAL로 차단됐고, `003690` 보험은 NOT_APPLICABLE이다. 보존된 US balance-sheet payload가 없어 US 실제 coverage는 0이며 synthetic SEC contract fixture만 별도로 통과했다. coverage를 늘리기 위한 fuzzy/ticker-specific mapping은 0이다.

새 debt/liquidity context는 internal packet metadata까지만 도달하고 compact AI context에는 노출되지 않는다. Directional/Price-Timing prompt, source sufficiency, Daily Delta, warning, working capital, non-operating effects, model/provider, production DB·queue·send·deploy·scheduler는 변하지 않았다. M9 focused 295개와 전체 2950개 테스트, Ruff, diff check가 통과했다. production readiness는 `NOT_READY`이며 모니터링은 중단 상태를 유지한다.

### M10 — 완료: inventory, receivables, working-capital component mapping

`inventory-receivables-working-capital-v1`은 exact official taxonomy와 POINT_IN_TIME context가 일치할 때만 inventory aggregate/component, trade/broad receivables, trade/broad payables, current assets/liabilities, contract assets/liabilities를 canonical fact와 internal `financial_context`로 승격한다. aggregate inventory가 있으면 child component를 함께 합산하거나 중복 노출하지 않고 aggregate가 우선한다. trade와 broad, gross와 net, contract와 trade balance는 서로 다른 semantic scope로 유지한다.

안전한 파생은 같은 metric·semantic·currency·unit·entity·statement·gross/net basis의 두 잔액에 대한 `balance_absolute_delta`뿐이다. `prior_year_comparable`과 `prior_year_end`를 별도 kind로 보존하며, 반기말 대 전기말은 YoY가 아니다. current assets minus current liabilities를 operating working capital로 부르는 공식과 DSO/DIO/DPO/CCC는 생성하지 않는다. 은행·보험·재보험은 `SECTOR_FRAMEWORK_REQUIRED`, SaaS/platform 등은 필요 시 `CONTEXT_ONLY`로 분리한다.

보존된 실제 KR archive에서 비금융 6곳 모두 inventory/current asset/current liability를 exact OpenDART/XBRL instant context로 재현했다. trade AR/AP는 각각 5곳, 나머지 1곳은 broad receivable/payable context만 안전했다. contract assets와 contract liabilities는 각각 3곳이다. 38개 balance delta는 모두 `prior_year_end` 비교이며 실제 prior-year comparable은 보존 자료에 없다. Receivable delta는 8개로, 6개 issuer scope에 더해 POSCO와 LS ELECTRIC의 current/noncurrent trade receivable을 각각 분리한 결과이며 합산 Fact가 아니다. Payable delta는 6개다. 보험 `003690`의 generic working-capital emission은 0이다. 보존된 US balance-sheet payload는 계속 0이므로 실제 US coverage는 주장하지 않고 exact SEC source-class capability만 synthetic fixture로 검증했다.

새 working-capital context는 internal packet metadata에만 존재하며 compact AI context, Directional/Price-Timing prompt, renderer, source sufficiency, Daily Delta, warning, debt/liquidity semantics를 바꾸지 않는다. M10 focused 339개와 전체 2970개 테스트, Ruff, diff check가 통과했다. production readiness는 `NOT_READY`, monitoring은 `PAUSED`를 유지한다.

### 후속 — 명시적 재개와 일일 운영

사용자가 재개를 요청할 때만 승인된 US/KR 예약을 다시 활성화한다.

- 마지막 정상 평가·자료 기준시점을 확인.
- 중단 기간을 “변화 없음”으로 처리하지 않음.
- backlog의 이미 발송/미발송 상태와 중복 방지 확인.
- 통제된 KR/US 자연 실행과 발송 결과 관찰.
- 모니터링 등록·investment logic·history는 유지.

새 판단 구조 검증 성공은 예약 재개의 자동 트리거가 아니다.

---

## 7. 변경하지 않는 판단·자료 계약

```text
BUY if buy >= 6.0
SELL if sell >= 6.0
otherwise HOLD
BUY:SELL sum = 10
increment = 0.5
```

HOLD의 5.5:4.5는 BUY_LEAN, 5.0:5.0은 NEUTRAL, 4.5:5.5는 SELL_LEAN이다. 별도 STRONG BUY output enum을 새로 가정하지 않는다.

Directional Core는 비가격 issuer 근거로 방향·배점·HOLD lean·fundamental 관점·business invalidation을 소유한다. Price-Timing은 실제 제공된 가격·technical·supply로 타이밍만 담당한다.

Price-Timing은 신규 관찰자의 판단을 더 보수적으로만 조정할 수 있고, 가격만으로 holder REDUCE나 사업 무효화를 만들 수 없다. Renderer는 주요 행동 표현을 소유하며 AI 추론은 실질 설명을 담당한다.

유지하는 자료 안전:
- 통화·기간·귀속·주식/ADR 기준이 맞을 때만 수치 비교.
- 단일분기 EPS 임의 연율화·provider 배수에서 EPS/BVPS 역산 금지.
- 잠정실적에 없는 현금흐름·BS 항목 생성 금지.
- 없는 기술적 지표·지지선·목표가·손절가 생성 금지.
- 가격·수급 변화를 fundamental delta로 복사하지 않음.
- Unknown은 실제 부정적 사실과 구분하며 없는 정보를 추정해 채우지 않음.

---

## 8. 실험 자산·holdout 상태 관리

세 상태를 별도로 관리한다.

| 축 | 질문 |
|---|---|
| Output exposure | 실제 결과가 나왔는가, 몇 기업·단계까지인가? |
| Semantic revelation | 판단·필드·안전 계약 결함이 실제로 드러났는가? |
| Retirement | 앞으로 unseen 시험에 다시 사용할 수 있는가? |

최신 cohort:

```text
RMD / NEON / AA / TDW
066900 / 079370 / 247540 / 183300
014820 / 318060 / 106240 / 263750
170900 / 039980 / 026960 / 251970
```

상태: `FULLY_EXPOSED / RETIRED_FOR_ARCHITECTURE_REPAIR`, future unseen reuse 0.

S1 source lock:

```text
3023b419f6c385abbe734c0e3b97667767a2c6cf2fd598522fe83215fcc3ebac
```

이 source lock은 offline 원본 대조용이다. 새 unseen proof용으로 재사용하지 않는다. 현재 task의 offline regression fixture는 새로운 실모델 증거가 아니다.

제외 registry는 보고된 149개를 현재 저장소 상태와 비교하고 최신 cohort 누락을 canonical issuer 단위로 추가한다. 단순 ticker 문자열만으로 share-class alias를 구분하지 않는다. 예상 합계 165를 검증 없이 강제하지 않는다.

원본 raw·prompt·schema·receipt는 그대로 보존하고 모든 재검증·수정 fixture·재렌더링은 별도 파생물로 표시한다. C를 채워서 완주한 것처럼 만드는 replay나 selective continuation은 금지한다.

---

## 9. 운영·비용·실행환경 정책

### 무료 외부 데이터

기존 무료·공식 경로에서 가져올 수 있는 자료 안에서 운영한다. 유료 추가·tier upgrade·유료 fallback은 승인하지 않았다. 무료 API 요금제 전수 감사나 새 관리 게이트도 현재 우선순위가 아니다.

실제 한도·자료 부재가 발생하면 기존 방식으로 명시하고, 중요한 값은 만들지 않는다. 지원 후보 universe와 실제 등록 완료, source PASS, investment attractiveness를 혼동하지 않는다.

### 예약 중단

마지막 기록에 있는 승인 객체는 다음 8개다.

```text
Thesis Monitor AI Review US Primary
Thesis Monitor AI Review US Backup
Thesis Monitor AI Review KR Primary
Thesis Monitor AI Review KR Backup
com.seungsoo.thesis-monitor.daily
com.seungsoo.thesis-monitor.kr-close
com.seungsoo.thesis-monitor.ai-review-fallback
com.seungsoo.thesis-monitor.ai-review-delivery-retry
```

현재 실행자가 existing safe observation으로 상태를 확인한다. 승인된 객체가 이미 중단이면 변경 0, 예상 밖 재활성화가 확인되면 기존 승인 범위 안에서 중단 유지 후 실제 변경 건수를 기록한다. 다른 scheduler/Night Futures를 중단하거나 실행 중인 자연 작업을 강제 종료하지 않는다.

### 모델/runtime

미래의 승인된 proof 기본 설정은 현행 프로젝트 계약을 유지한다.

```text
gpt-5.6-sol / xhigh
MODEL_CONTEXT_COUPLED / 4 subjects
1800-second single watchdog
per-context unique namespace / workdir / invocation
```

완료된 M1의 모델 호출은 0이다. Transport의 capacity·disconnect·내부 retry·watchdog를 서로 구분하고, 과거 회복 사례를 무장애 보증으로 표현하지 않는다. Wrapper 자동 retry·모델 변경·batch split·timeout 증가는 별도 근거와 승인 없이 하지 않는다.

---

## 10. 결과 보고의 공통 형식

모든 다음 결과는 최소한 다음을 분리한다.

```text
Code / offline regression
Source readiness
Transport completion
Schema / identity acceptance
Core / Timing / combined semantic checks
Run-level ownership / renderer / hard-safety
Descriptive comparison
Formal stability / generalization
Message quality
Bootstrap/integration readiness
Production activation / scheduler state
```

`NOT_MEASURED`는 실패도 성공도 아니다. `0`에는 반드시 검사한 모집단·분모를 붙인다. raw output 수, 기업 수, stage row 수, 성공 run 수를 섞지 않는다.

Master 갱신 때마다 기록:
1. 읽은 최신 결과 파일명·실제 SHA.
2. 완료·실패·미측정 변화와 해당 원본 artifact.
3. 실제 코드 변경과 현재 저장소 상태.
4. 사용자에게 승인받은 다음 범위와 금지 범위.
5. 최신 운영 관측 시각과 운영 변경 유무.
6. 후속 phase의 진입 조건.

이 문서의 M0~M12 상태는 프로젝트 계획용이다. 공개 Action enum이나 production schema를 새로 만들라는 뜻이 아니다.

---

## 11. M11 결론과 다음 한 작업

**완료한 작업:** M1 Unknown 계약 수리, M2 nonproduction 판단/메시지 통합 검토, M3 monitoring bootstrap·Daily Delta lifecycle 통합, M4 source-domain enrichment·Directional specificity 설계 검토, M5 `DecisionEvidencePacket` 금융 컨텍스트 확장, M6 기존 canonical 금융 adapter 구현, M7 compatible prior-year·derived-period lineage와 exact OpenDART duration projection 구현, M8 reusable source-class 분류와 exact-context canonical source promotion 구현, M9 interest-bearing debt/liquidity canonical mapping과 complete-scope derivation 구현, M10 inventory/receivables/payables와 명시적 balance-comparison mapping 구현, M11 non-operating/financial-income effects exact mapping과 bounded net-financial-effect derivation 구현.

M8 source-class 판정:

```text
HUT PPE = SOURCE_EVIDENCE_INSUFFICIENT / DEFER_NO_TICKER_EXCEPTION
SKHY OCF/PPE = GENERIC IFRS CLASS ALREADY SUPPORTED / ISSUER OCCURRENCE ABSENT
KR OpenDART = GENERIC_SOURCE_CLASS_WITH_BOUNDED_VARIANT / IMPLEMENTED
```

HUT은 보존된 추출 결과에 OCF만 있고 원본 CompanyFacts concept set이나 미등록 PPE extension이 남아 있지 않아 안전한 alias를 만들 수 없다. SKHY는 TSM·WRD가 증명하는 issuer-level IFRS 20-F/6-K class를 이미 지원하지만, 보존 SKHY source에는 정식 현금흐름 occurrence가 0개이므로 역사적 gap은 그대로 fail-closed다.

KR은 실제 7개 보존 OpenDART full-statement/XBRL cache에서 동일 원인을 확인했다. `ConsolidatedAndSeparateFinancialStatementsAxis`라는 축 이름 자체에 두 basis 단어가 함께 있어 이전 parser가 모호하다고 판단했지만, 실제 member는 각 context에서 `ConsolidatedMember` 또는 `SeparateMember`로 단일하다. M8은 basis member를 우선하고 exact taxonomy·amount·KRW unit·entity·duration·filing identity가 모두 일치할 때만 direct reported canonical fact로 승격한다. 7개 issuer의 OCF/PPE source fact는 exact YTD context로 재현됐고 ticker 분기는 0이다. 보험 1개는 source evidence 보존과 generic enterprise FCF applicability를 분리해 기존 N/A를 유지한다.

M11 contract는 `non-operating-financial-income-effects-v1`이다. Direct source 금액의 부호와 official presentation을 보존하고 financial income, financial cost, interest income/expense, FX gain/loss, disposal·fair-value effect, broad other context, equity-method context, tax, continuing/discontinued result를 서로 다른 semantic으로 유지한다. 유일한 파생은 exact official aggregate finance income minus compatible aggregate finance cost이며, official direct net가 있으면 이를 우선한다. Child component만으로 total을 합성하거나 aggregate와 child를 이중 합산하지 않는다.

보존된 실제 KR 자료에서는 비금융 6개 모두 finance income/cost와 tax direct fact가 있었고, safe net-financial-effect는 6개 issuer에서 확인됐다. 이 중 5개는 동일 document·period·currency·unit·entity·basis·attribution의 aggregate 두 입력에서 파생됐고 1개는 official direct net다. Interest income/expense는 각각 1개 issuer에서만 exact direct fact로 확인됐다. Aggregate/child overlap 8건은 parent precedence와 child descriptive preservation으로 처리했으며 합산 0, source conflict 0, sign-ambiguous derivation 0이다. 보험 1개는 `SECTOR_FRAMEWORK_REQUIRED`로 분리해 generic emission 0을 유지한다.

보존된 US/foreign income-statement 원본은 0개이므로 M11은 실 US issuer coverage를 주장하지 않는다. SEC CompanyFacts adapter의 exact taxonomy capability는 fixture로만 검증하며 issuer별 실제 coverage와 구분한다. Broad other income/expense는 context-only이고 equity-method와 tax는 operating performance나 finance aggregate로 재분류하지 않는다. Universal non-operating total, reconstructed operating profit, adjusted/normalized earnings·EPS, ETR, recurrence/materiality score 파생은 모두 0이다.

6개 financial domain의 model-free 검토 결과는 `READY_WITH_KNOWN_OPTIONAL_GAPS`다. 남은 공백은 US 실 archive와 sector-specific framework 같은 선택적 source/industry 범위이며, 다음 Directional specificity 구현을 막는 generic schema/semantic gap은 확인되지 않았다.

**권장 다음 한 작업, 아직 미승인:** `DIRECTIONAL_FINANCIAL_CONTEXT_CONSUMPTION_AND_SPECIFICITY_IMPLEMENTATION`.
- M5~M11 typed financial context 중 claim과 sector에 필요한 최소 evidence만 Directional Core에 공급한다.
- data activation과 최종 real-model proof를 분리한다.
- source-sufficiency gate, Daily Delta, warning, Price-Timing, renderer, production 활성화와 schedule resume는 계속 포함하지 않는다.
- financial-sector capital framework와 `010120`의 ambiguous convertible preferred liability는 별도 문제로 유지한다.

M4 source 지원 분류는 US `2 supported / 4 partial / 0 unsupported`, KR `1 supported / 5 partial / 0 unsupported`다. 이는 보편적 issuer coverage가 아니라 현재 parser·mapping·보존 fixture의 계약 수준 분류다. KR OCF/PPE period context, complete interest-bearing debt, trade AR/AP, generic non-operating bridge는 계속 fail-closed 또는 mapping-incomplete다.

6개 도메인 모두 missing을 negative로 바꾸지 않는다. 새 universal source gate는 0개다. debt/liquidity만 financing-dependent sector/framework의 조건부 gate 후보이며, 실제 gate 변경 전 별도 coverage 검토가 필요하다. CCC·ROIC, maintenance capex, generic net debt, partial capex를 company FCF로 부르는 경로는 허용하지 않는다. M11 fact도 Directional Core, compact AI context, source sufficiency, Daily Delta 또는 warning에 아직 소비되지 않는다.

**새로운 주요 판단·입력 변경이 정해지기 전에 매번 FIRST/A/B/C를 반복하는 개발 흐름은 중단한다.** 기존 증거로 결정할 수 있는 부분은 먼저 결정하고, 변경을 묶어 동결한 뒤 필요한 실모델 검증을 수행한다.

---

## 12. M12 결과와 다음 한 작업

M12 구현 커밋 `72c28172949939b268806f5cb347ae4761a0d7f0`은 `directional-financial-decision-context-v1` selector, Directional Core 전용 compact context, cited-alias financial semantic validator를 추가했다. 최대 8개 입력 중 실제 fixture 선택은 최대 3개였고, 8/8 compact context가 의도적으로 변했으나 기존 non-financial evidence drop은 0이었다. financial block의 price/technical/supply ref는 모두 0이며 Price-Timing prompt hash는 이전과 동일하다.

Phase A는 focused `561 passed`, full `3014 passed`, Ruff와 `git diff --check`를 포함해 전 항목 PASS했다. M11 bundle SHA와 53개 payload 무결성도 PASS했다. source lock은 `0da54da972b6cf6874486d9f47d461a72d11a3055152c6d9f35a0f19c2e7c40d`다.

Fictional canary는 첫 context 4개 결과를 schema 4/4, transport 1/1로 받았다. invalid reference, FCF 오표현, prior-year-end YoY 오표현, debt completeness, normalized earnings, fixed score, price/technical/supply 침범은 모두 0이었다. FIC-FIN-03은 QTD 흑자와 YTD 손실 두 fact를 모두 인용하고 “분기”와 “누적”을 명시했으나 frozen case validator가 YTD 한국어 표현으로 `누계`만 인식해 `qtd_ytd_conflict_not_explicit` false reject를 냈다. 결과·validator·prompt를 수정하거나 선택 재실행하지 않고 1/6에서 fail-closed 중단했다.

따라서 현재 상태는 `M12_DETERMINISTIC_COMPLETE_CANARY_BLOCKED`, fresh real proof와 production readiness는 `NOT_READY`다. 다음 한 작업은 `BOUNDED_DIRECTIONAL_FINANCIAL_CONTEXT_REPAIR`: ticker 예외나 threshold 변경 없이 generic QTD/YTD 의미 validator가 `누계`와 `누적` 같은 정상 누적 표현을 동등하게 처리하도록 수리하고, 새 generation에서 fictional 6-context canary 전체를 다시 검증한다. 실 issuer proof는 그 뒤에만 진행한다.

운영 변경은 0이다. 승인된 Codex 4개 automation은 PAUSED, launchd 4개 경로는 DISABLED이며 자동 재개하지 않았다. provider fetch, production DB/assessment/warning/notification/send, main merge, deploy도 모두 0이다.

---

## 12R. M12R validator repair와 fail-closed 결과

M12R instruction commit은 `d01c02f3338093bf5ee380f65b8b5907ff5bbf25`, validator repair commit은 `5c26778d708d5c25fae2b2a2e9fb5433f174045e`, read-only schedule observation compatibility commit은 `ffc3fd557f056feac693e596cb48214a5e41aea3`다. formal generation은 `20260909-m12r-fictional-20260909T043009Z-ffc3fd557f05`, source lock은 `326d00b2dd12077427cc13b721e9d6287cfc68401d9d1b1f484765a79864f47d`다.

Generic QTD/YTD validator는 같은 metric의 structured QTD/YTD evidence, 같은 claim의 양쪽 fact 인용, 제한된 분기·누계 표지와 명시적 대비 관계를 함께 요구한다. 정상 한국어 `누계`·`누적`·`연초 이후`, 영어 `YTD`·`year-to-date`·`cumulative`를 인식하되 무관한 `누적적으로`는 허용하지 않는다. 보존 M12 FIC-FIN-03 raw output은 이제 PASS했고 positive fixture `6/6`, negative fixture `10/10`이 각각 통과·거부됐다. historical root cause는 `QTD_YTD_VALIDATOR_KOREAN_CUMULATIVE_WORDING_FALSE_REJECT`로 닫혔다.

Phase A는 focused `570 passed`, full `3022 passed`(warning 2), Ruff와 `git diff --check`까지 PASS했다. 새 model call 전 prompt, selector, fictional cases, schema, threshold와 calibration 변경은 0이었고 source sufficiency, Daily Delta, renderer, warning 의미 변경도 0이었다.

새 fictional canary는 run-1/context-01이 PASS한 뒤 run-1/context-02의 FIC-FIN-06에서 `material_financial_anchor_not_used`와 `working_capital_checkpoint_not_used`가 발생해 규칙대로 즉시 중단했다. 해당 output은 재고·매출채권을 해석했지만 선택된 `canonical:fictional:FIC-FIN-06:inventory-current`와 `canonical:fictional:FIC-FIN-06:trade-receivables-current`를 인용하지 않았다. transport·schema는 정상이고 QTD/YTD false reject/accept 및 나머지 고위험 financial semantic 오류는 0이었다. 완료 호출은 `2/6`, 나머지 `4/6`은 NOT_RUN이며 retry, timeout, capacity failure, orphan은 모두 0이다. 후보·prompt·builder·validator·config는 model 시작 후 수정하지 않았다.

따라서 M12R 상태는 `BLOCKED`, stability는 `NOT_MEASURED`, `fresh_real_proof_readiness=NOT_READY`, `production_readiness=NOT_READY`다. 다음 scope는 `BOUNDED_DIRECTIONAL_FINANCIAL_CONTEXT_REPAIR`이며 FIC-FIN-06의 canonical working-capital anchor 누락만 별도 bounded repair로 다룬다. fresh real proof, provider fetch, production DB/assessment/warning/notification/send, main merge, deploy는 수행하지 않는다.

운영 중단은 그대로다. Codex automation 4개는 PAUSED, launchd 4개는 DISABLED로 관측됐고 scheduler mutation과 자동 재개는 0이다.

---

## 12G. M12G financial-anchor grounding repair와 fail-closed 결과

M12G instruction commit은 `7e3fac6385760e3356213eab81c67e957d1c55d6`, initial implementation commit은 `b89aec98b59d38b9b1cfb6dfa946a1c47a52f53e`, 최종 frozen implementation commit은 `63aaf9f72cc7ee021c0bf70a746ba5ae5472b218`다. formal generation은 `20260909-m12g-fictional-20260909T054736Z-63aaf9f72cc7`, source lock은 `2a46c2abd2740b52a21799c5b3ed91a77061c7c79520eaef5e2adae30b1544ff`다. 첫 Phase A 시도는 모델 호출 0 상태에서 legacy 20KB prompt-size gate 두 건 때문에 중단했고 그 증거를 별도 보존했다. prompt 의미나 legacy threshold를 완화하지 않고 grounding 문구를 압축해 diagnostic `19,957 bytes`, sequential probes `19,985 / 19,997 / 19,997 bytes`로 기존 경계를 복구했다.

Deterministic gate는 보존 FIC-FIN-03 PASS, 기존 FIC-FIN-06 FAIL 유지, typed inventory/AR refs를 relevant fields에 넣은 corrected FIC-FIN-06 PASS를 확인했다. positive grounding fixture `6/6`은 통과했고 narrative-only substitution, irrelevant typed ref, unrelated-field-only typed ref의 negative fixture `3/3`은 거부됐다. selected financial context가 없는 control에는 새 인용 의무를 만들지 않았다. selector, fictional case, schema, financial/QTD-YTD validator, calibration, Price-Timing, source sufficiency, Daily Delta, renderer와 warning semantic change는 모두 0이다. Phase A는 focused `578 passed`, full `3030 passed`(warning 2), Ruff와 `git diff --check`까지 PASS했다.

새 canary는 run-1/context-01의 4개 subject가 PASS했고 selected/used typed financial refs는 `11/11`이었다. run-1/context-02는 transport PASS(`gpt-5.6-sol`, xhigh, return code 0, retry/timeout/capacity/orphan 0), schema `4/4`였지만 FIC-FIN-06이 선택된 `inventory-current`와 `trade-receivables-current` refs를 사용하지 않았다. 이에 `material_financial_anchor_not_used`, `working_capital_checkpoint_not_used`, `material_financial_anchor_grounding_failure`, `working_capital_grounding_failure`, `narrative_substitution_failure`가 발생했다. 해당 context의 나머지 3개 subject는 PASS했고, 규칙대로 `2/6`에서 즉시 중단해 나머지 `4/6`은 NOT_RUN이다. 새 model call 이후 candidate, prompt, builder, selector, validator, schema와 config 수정은 0이다.

따라서 M12G deterministic repair는 완료됐지만 full fictional canary는 `PROMPT_GROUNDING_INSUFFICIENT`로 BLOCKED다. formal stability와 message-specificity는 `NOT_MEASURED`, `fresh_real_proof_readiness=NOT_READY`, `production_readiness=NOT_READY`다. 다음 scope는 `FINANCIAL_CONTEXT_OUTPUT_GROUNDING_ARCHITECTURE_REVIEW`다. 이는 validator 완화나 ticker 예외 추가가 아니라, 선택된 typed financial anchor가 material claim/checkpoint output에 구조적으로 귀속되도록 하는 계약 검토여야 한다.

실 issuer model call, provider fetch, production DB/assessment/warning/notification/send, main merge, deploy는 모두 0이다. 예약 중단은 유지하며 scheduler mutation과 자동 재개도 0이다.

---

## 12A. M12A financial-context output grounding architecture review

M12A work-instruction commit은 `938569446f309376c3519dd63fd33d505c790e57`, offline review/prototype 최종 implementation commit은 `20e5fec5bf0b243e6205c48aa4f875c37b203164`다. authoritative M12G bundle SHA `69fc255d836d3dd886882754c21a233d82541c86ff627a5a5c8342249012aa68`를 다시 계산했고 indexed payload `160`, missing/extra/hash/size/secret mismatch는 모두 0이었다.

현재 grounding 흐름을 끝까지 추적한 결과 alias 체계 자체는 이미 하나다. `stage_alias_catalogs`는 narrative ref와 selector가 고른 typed financial ref를 동일 `EvidenceAliasCatalog`에 넣고, 기존 alias resolver와 output `evidence_refs`도 양쪽을 동일하게 해석할 수 있다. 실제 split은 모델 입력 직전 `scripts/directional_core_price_timing_holdout.py::_owned_context`에서 생긴다. 선택된 typed financial alias `15/15`는 catalog에 있지만 ordinary `evidence[]`에는 `0/15`이고, 별도 `financial_decision_context.evidence_items[]`에만 들어간다. typed alias의 catalog statement `15/15`도 `{"value":"..."}` 형태라 narrative alias보다 사람에게 보이는 의미가 약하다.

보존된 완료 출력의 model-free replay 감사는 M12 `11 selected / 8 used`, M12R `15 / 12`, M12G `15 / 13`, 합계 `41 / 33`이었다. FIC-FIN-06은 M12R과 M12G 모두 working-capital 내용을 narrative로 올바르게 설명했지만 selected inventory/trade-AR typed ref를 전혀 쓰지 않아 narrative-substitution failure가 두 번 반복됐다. 현재 8개 fictional packet에서 selected typed item 15개 중 8개는 동일 사실을 요약하는 narrative row가 있었지만 producer-supplied backing lineage는 `0`이었다. text/topic 유사성은 분류 감사에만 썼고 lineage로 승격하지 않았다.

Option A/B/C를 FIC-FIN-05와 FIC-FIN-06에 오프라인 직렬화했다. Option A는 기존 alias 번호와 canonical/source/comparison/derivation lineage를 그대로 두고 selector가 고른 typed item만 ordinary `evidence[]`에 한 번 추가한다. statement는 metric, period, comparison에서 결정적으로 만든 neutral 문장이고, value와 상세 period/basis는 structured metadata에 남는다. output schema, resolver, validator 의미, renderer를 바꿀 필요가 없다. Option B는 provenance-based `backing_financial_refs`가 있으면 안전하지만 현재 narrative producer의 실제 lineage가 0이므로 text matching 없이 문제를 해결할 수 없다. 기존 `metric_refs`는 checkpoint metric ownership이지 source provenance가 아니어서 재사용하지 않는다. Option C는 새 output field로 검사할 수 있지만 schema migration, legacy artifact, model compliance surface를 늘리면서 이미 가능한 ordinary `evidence_refs` 기능을 중복한다. 별도 proven problem이 없어 hybrid도 선택하지 않았다.

따라서 preferred architecture는 `FIRST_CLASS_TYPED_EVIDENCE_UNIFICATION`, 다음 bounded scope는 `FIRST_CLASS_TYPED_FINANCIAL_EVIDENCE_INDEX_IMPLEMENTATION`으로 동결했다. double-counting identity는 canonical ref다. 같은 typed fact가 `evidence[]` claim과 `financial_decision_context` detail metadata에 함께 보여도 하나의 anchor로만 센다. lineage 없는 narrative summary는 typed anchor로 세지 않으며, financial detail block은 두 번째 증거가 아니다. narrative는 사실의 의미, Unknown, sector interpretation을 계속 소유한다. raw financial dump와 unselected fact projection은 모두 0이다.

과거 M12G FIC-FIN-06 output은 Option A와 B에서도 그대로 FAIL이고 Option C에서는 legacy/NOT_APPLICABLE이다. corrected FIC-FIN-06 fixture는 세 옵션 모두 표현 가능하지만 model result로 재분류하지 않았다. 이 review는 과거 실패를 소급 수정하지 않는다.

검증은 focused `51 passed`, full `3040 passed`(기존 warning 2), Ruff PASS, `git diff --check` PASS다. model/provider 호출, production DB/assessment/warning/notification/send, monitoring registration, main merge, deploy는 모두 0이다. 8개 승인 중단 경로는 PAUSED/DISABLED 상태로 관측했고 scheduler mutation과 automatic resume도 0이다.

M12A 상태는 `COMPLETE`지만 repaired architecture는 아직 실제 Directional runner에 구현하지 않았고 새 fictional canary도 실행하지 않았다. 따라서 `fresh_real_proof_readiness=NOT_READY`, `production_readiness=NOT_READY`다. 다음 작업은 동결한 Option A만 구현한 뒤 동일 8-subject x 3-repeat fictional canary를 새 generation으로 실행하는 것이다. 그 전체가 통과한 뒤에만 fresh-real financial-context generalization proof로 이동한다.

---

## 12B. M12B first-class typed financial evidence 구현과 fail-closed 결과

M12B work-instruction commit은 `c92194414db5200cf30df1f912f9ebedc6036a43`, frozen implementation commit은 `746ef9ba1586973d84b49fd233e460660f5b91fa`다. authoritative M12A bundle SHA `cef338a297c6a04908d0255f845b3526f78eabb9aa8d8f5d6c12fdcb97e9b227`를 다시 계산했고 indexed payload `46`, missing/extra/hash/size/secret mismatch는 모두 0이었다.

동결한 Option A `FIRST_CLASS_TYPED_EVIDENCE_UNIFICATION`을 구현했다. selector가 선택한 typed financial item만 ordinary `evidence[]`에 기존 canonical alias와 catalog 순서 그대로 한 번 투영하고, `evidence_kind=TYPED_FINANCIAL` 및 compact financial semantics를 붙였다. metric·기간·비교관계에서 결정적으로 만든 neutral statement를 사용하면서 상세 lineage와 basis는 기존 `financial_decision_context`에 유지한다. 선택 15개는 first-class projection 15개와 정확히 일치했고 suppressed projection, alias renumber, duplicate alias, detail removal은 모두 0이었다. financial context가 없는 FIC-FIN-07과 sector-framework-only FIC-FIN-08은 ordinary context가 byte-equivalent였고 price/technical/supply leakage도 0이었다.

기존 핵심 회귀는 그대로 보존했다. 과거 M12G FIC-FIN-06 raw output은 여전히 FAIL이고 corrected fixture는 PASS이며 FIC-FIN-03 QTD/YTD 회귀도 PASS다. selector, directional/Price-Timing prompt, financial/QTD-YTD validator semantics, output schema, renderer, calibration, source sufficiency, Daily Delta와 warning 의미 변경은 0이다. Phase A는 model call 전 전 항목 PASS했고 focused `594 passed`, full `3056 passed`(기존 warning 2), Ruff와 `git diff --check`도 PASS했다. source lock은 `5bfe8b8ed1f8878bc2d6787e81e34c3a35bc2c424aff80b137d6b44fc9300149`다.

새 generation `20260909-m12b-fictional-20260909T085320Z-746ef9ba1586`은 동일 8개 fictional subject, 2개 context, 3회 반복, `gpt-5.6-sol` xhigh, 1800초 single watchdog으로 동결했다. run-1/context-01과 run-1/context-02는 모두 PASS했고, 첫 반복의 FIC-FIN-06도 first-class inventory/trade-AR 근거를 직접 사용해 PASS했다. run-2/context-01은 transport와 schema가 정상이고 4개 중 3개 subject가 PASS했으나 FIC-FIN-02에서 `working_capital_grounding_failure` 1건이 발생해 규칙대로 즉시 중단했다. 완료 호출은 `3/6`, 출력은 `12/24`, 나머지 `3/6`은 NOT_RUN이며 formal stability는 `NOT_MEASURED`다. retry, timeout, capacity failure, orphan process는 모두 0이고 model 시작 후 candidate, prompt, builder, selector, validator, schema 또는 config 수정은 0이다.

FIC-FIN-02는 선택된 typed ref `3/3`을 출력 전체에서 모두 사용했고 material financial anchor와 narrative-substitution 검사도 통과했다. 그러나 `risk_context`의 “운전자본 흡수가 지속될 수 있다”는 claim은 narrative structural-risk와 remaining-unknown만 인용했고 typed inventory ref는 별도 Unknown treatment에서만 사용했다. 따라서 이는 source/transport/schema/QTD-YTD 문제가 아니라, 운전자본 claim과 checkpoint가 같은 typed 근거를 직접 소유해야 한다는 claim-level grounding 계약 실패다. 부분 표본 합계는 selected/first-class/used typed refs `26/26/26`, material-anchor failure `0`, working-capital grounding failure `1`, narrative-substitution failure `0`, irrelevant-ref failure `0`이다.

따라서 M12B projection 구현은 완료됐지만 full fictional canary는 `BLOCKED`다. `fresh_real_proof_readiness=NOT_READY`, `production_readiness=NOT_READY`이며 자동 gate의 다음 scope는 `DIRECTIONAL_OUTPUT_FINANCIAL_GROUNDING_SCHEMA_REVIEW_OR_IMPLEMENTATION`이다. 다음 작업은 validator 완화나 prompt-only 문구 추가가 아니라, typed working-capital evidence가 이를 주장하는 material claim/checkpoint에 구조적으로 귀속되는지 좁게 검토해야 한다. fresh real issuer proof와 production integration은 시작하지 않는다.

실 issuer model call, judge call, provider fetch, production DB/assessment/warning/notification/send, monitoring registration, main merge와 deploy는 모두 0이다. Codex automation 4개는 PAUSED, launchd 4개는 DISABLED 상태를 유지하며 scheduler mutation과 automatic resume도 0이다.

---

## 12C. M12C materiality-scoped working-capital grounding repair와 fail-closed 결과

M12C work-instruction commit은 `6a75e839fd05d7d8b095ae5d23180f621b7abb3a`,
forensic freeze commit은 `d7ce2b7e24b3fee8373aa2daee5313242b3e325f`, 최종
implementation commit은 `4f367e27588b030508ae4c9d4ad0181caf64d0de`다. M12B
authoritative bundle SHA
`66b53e4991ec46774f2000c871650d2a4390bd88505cc4ae802be0bbc17844cd`와
indexed payload 112개의 missing/extra/hash/size/secret mismatch 0을 다시 확인했다.

코드 변경 전 forensic은 M12B FIC-FIN-02 run-2 실패를
`SELECTION_TRIGGERED_OVERREACH`로 동결했다. 선택된 inventory fact가 별도
Unknown/context claim에서 직접 사용되고 cash-conversion typed anchor도 material claim에
귀속됐지만, generic `운전자본` narrative가 checkpoint path에 있다는 이유만으로 기존
validator가 inventory-specific checkpoint grounding을 요구했다. Branch A repair는 선택
자체가 아니라 material checkpoint claim의 explicit inventory/trade-AR/trade-AP metric
사용을 hard trigger로 만들고, 해당 metric과 일치하는 typed ref만 그 claim을 ground하도록
좁혔다. ticker/case branch는 0이다.

결정론적 회귀에서 M12B FIC-FIN-02 run-1/run-2와 M12B FIC-FIN-06 run-1은
PASS, old M12G FIC-FIN-06 narrative substitution은 FAIL 유지, corrected FIC-FIN-06은
PASS였다. positive fixture 4/4와 negative fixture 5/5가 기대대로 닫혔고 FIC-FIN-03
QTD/YTD 역사 회귀도 PASS했다. first-class projection, selector, Directional/Price-Timing
prompt, output schema, QTD/YTD 및 non-WC financial validator, calibration, source
sufficiency, Daily Delta/lifecycle/warning, renderer 변경은 0이다. focused/full pytest,
Ruff, `git diff --check`와 production side-effect firewall도 PASS했다. 최초 deterministic
preflight는 model call 전에 report-builder field-name mismatch로 중단됐고, 산출물을
분리 보존한 뒤 새 SHA와 새 generation으로 다시 동결했다. 이 preflight의 model call은
0이다.

formal generation은
`20260909-m12c-fictional-20260909T101525Z-4f367e27588b`, source lock은
`3b8ae0ec3b8b3fc9f8cfd82aab2919abc4c4a701f8e71022cba9fd10f7c44c9a`다.
동일 8개 fictional subject, 2개 context, 3회 반복, `gpt-5.6-sol` xhigh,
1800초 single watchdog, retry 0으로 실행했다. 첫 4개 context는 PASS했고
run-3/context-01 transport와 schema도 정상이라 총 `5/6` model contexts와 `20/24`
rows를 보존했다. material-anchor, true metric-specific WC grounding, narrative
substitution, irrelevant financial ref, invalid ref, FCF/debt/normalized-earnings 및
price/technical/supply 위반은 0이었다.

run-3/context-01의 FIC-FIN-03만 `qtd_ytd_conflict_not_explicit`로 FAIL했다. 출력은
QTD와 YTD operating-income typed ref를 모두 인용하고 `분기 영업흑자`와 `누적
영업손실`을 `상충`, `기간별로 구분해 함께 반영`, `섞지 않는다`고 명시했다. 그러나
frozen QTD/YTD validator의 relation matcher가 이 정상 관계 표현을 인식하지 않아
linked claim 7개에도 explicit claim을 0개로 계산했다. 이는 M12C working-capital
repair 실패가 아니라 별도의 generic QTD/YTD relation-language false reject다. 범위
규칙대로 validator/prompt/candidate를 수정하거나 선택 재실행하지 않았고, 6번째 호출은
NOT_RUN이다. formal stability와 message-specificity는 `NOT_MEASURED`다.

따라서 `M12C_CANARY_FAIL`, `fresh_real_proof_readiness=NOT_READY`,
`production_readiness=NOT_READY`다. 다음 한 작업은
`BOUNDED_DIRECTIONAL_FINANCIAL_CONTEXT_REPAIR`: ticker 예외나 threshold 완화 없이
structured QTD/YTD 양쪽 ref를 인용한 claim의 일반적인 한국어 대비·구분 관계를
bounded하게 인식하는지 검토하고 새 generation으로 전체 fictional canary를 다시
증명한다. real issuer model call/provider fetch와 production
DB/assessment/warning/notification/send, main merge, deploy는 모두 0이다. 승인된 8개
monitoring 경로는 PAUSED/DISABLED 상태를 유지하며 scheduler mutation과 automatic
resume도 0이다.

---

## 12D. M12D QTD/YTD plain-Korean validator repair와 stability fail-closed 결과

M12D work-instruction commit은 `dd28946351e9a1517d1c50992c93265113efdba0`,
forensic freeze commit은 `4b1b0417514b85b5c37a7ca61394ab98f522f099`,
implementation commit은 `3ad040f73f7f159519cb5d47058571c101f1a6c3`다. M12C
authoritative bundle SHA
`2ce3b4e501743fb9e640b62807a96658e54b1f682298a486ea0d0c3dc32dd92e`와
indexed payload 121개의 hash/size mismatch 0 및 secret-scan failure 0을 확인했다.

구현 전 forensic은 M12C run-3 FIC-FIN-03 실패를
`OTHER_BOUNDED_VALIDATOR_DEFECT:KOREAN_PERIOD_RELATION_MARKER_FALSE_REJECT`로
동결했다. 기존 validator는 plain `분기` QTD와 `누적` YTD marker, 같은 metric의 양쪽
typed evidence linkage를 이미 인식했지만, 두 기간 결과의 관계를 명시한 `상충`을
relation marker로 인식하지 못했다. Branch A 구현은 QTD/YTD relation matcher에 일반
한국어 marker `상충` 하나만 추가했다. fictional case, WC validator, first-class
projection/selection, Directional·Price-Timing prompt, output schema, 다른 financial
validator, threshold/increment/HOLD lean/calibration, source sufficiency, Daily
Delta/lifecycle/warning, renderer 변경은 0이다.

보존 M12C run-1/run-2/run-3 및 historical FIC-FIN-03 회귀, positive fixture와
false-accept negative fixture, claim-path와 same-metric evidence-linkage 검사는 모두
PASS했다. focused pytest는 625 passed, full pytest는 3087 passed, Ruff와
`git diff --check`도 PASS했다. model-call gate 전 호출은 0이었다.

formal generation은
`20260909-m12d-fictional-20260909T113907Z-3ad040f73f7f`, source lock은
`b8f7a16ab2570b2d738a4891ca1d7d3f793a4686581da4cf6b5955367231ba67`다.
동일 8개 fictional subject, 2개 context, 3회 반복, `gpt-5.6-sol` xhigh, single
watchdog, retry 0으로 전체 6/6 context와 24/24 output을 완료했다. schema 24/24,
hard financial semantic violation, QTD/YTD false reject/false accept/true semantic
violation, working-capital/material-anchor grounding failure, narrative substitution,
invalid financial ref와 opposite-direction reversal은 모두 0이다. model context는
6/6 PASS했고 retry/timeout/capacity/orphan도 모두 0이다. 특히 세 반복의
FIC-FIN-03은 QTD/YTD contract를 모두 PASS했다.

그러나 formal stability는 STABLE 4, BOUNDARY_UNCERTAINTY 3, UNSTABLE 1로
FAIL했다. FIC-FIN-02가 동일 동결 입력에서 `SELL -> HOLD(SELL_LEAN) -> SELL`로
변해 `DIRECTION_OR_OPPOSING_HOLD_LEAN_CHANGED`로 분류됐다. opposite-direction
reversal은 0이고 hard semantics와 grounding은 전부 PASS이므로, 이는 이번 QTD/YTD
repair의 재실패나 runtime failure가 아니라 별도의 material financial interpretation
stability 문제다. 지시대로 threshold/calibration/prompt/candidate를 수정하거나
선택 재실행하지 않았다.

따라서 `M12D_CANARY_FAIL`, `fresh_real_proof_readiness=NOT_READY`,
`production_readiness=NOT_READY`다. 다음 한 작업은
`BOUNDED_DIRECTIONAL_FINANCIAL_CONTEXT_STABILITY_REVIEW`이며 FIC-FIN-02의 경계
변동을 threshold-adjacent uncertainty와 material evidence interpretation variability로
분리해 조사한다. real issuer model call, judge call, provider fetch, production
DB/assessment/warning/notification/send, monitoring registration, main merge, deploy는
모두 0이다. 승인된 8개 monitoring 경로는 PAUSED/DISABLED 상태를 유지하고 scheduler
mutation과 automatic resume도 0이다.

---

## 12S. M12S financial-context stability root-cause review와 다음 수리 동결

M12S work-instruction commit은 `1c50d011d9bb12665fb0b5075eff1077c5557ea4`,
offline fingerprint tooling implementation commit은
`8dfe7dadb5f90375d547bd55217437c6420658a2`다. M12D authoritative bundle SHA
`b7eb58d997048799c499daa7b2be29a429791772781d1ab23c6540f03fa7a9a3`와 indexed
payload 127개의 hash/size mismatch 0을 다시 확인하고, generation
`20260909-m12d-fictional-20260909T113907Z-3ad040f73f7f`의 보존 output 24개만
결정론적으로 fingerprint했다. 새 model/judge/provider call은 0이다.

정규화한 fingerprint는 direction/balance/thesis/new-buyer/holder뿐 아니라 material 및
dominant anchor, driver·Unknown·reevaluation·invalidation domain, 실제 사용된 typed
financial metric과 operating/cash-conversion/debt-liquidity/working-capital/non-operating
semantic polarity를 분리한다. 단순 ref 추가, claim field 이동, 동일 경제 사실의 공동
인용 또는 0.5 balance 차이는 material interpretation delta로 승격하지 않는다. 24개
pairwise 비교에서 명시적 polarity 반전이나 causal-domain 교체는 0이었고, stable control의
anchor/thesis label 차이는 formal success를 고쳐 쓰지 않는 advisory로만 보존했다.

비안정 4종목의 primary root cause는 다음과 같다. FIC-FIN-01은 같은 positive
operating/cash-conversion/resilience 해석에서 6.0/6.5와 ATTRACTIVE/WAIT가 갈린
`ADJACENT_BALANCE_BUCKET_CALIBRATION_AMBIGUITY`이고, new-buyer 차이는 독립 secondary
ambiguity다. FIC-FIN-02는 같은 cash-conversion deterioration, healthy demand, 원인·가역성
Unknown 아래 SELL 6.0과 HOLD SELL_LEAN 5.5가 갈린 같은 primary root cause다.
FIC-FIN-04도 flat operations와 non-operating net-income support를 동일하게 해석하면서
5.0/5.5가 갈렸다. FIC-FIN-05는 direction 4.0:6.0, WEAKENED, debt/liquidity anchors가
동일한데 holder만 REVIEW/REDUCE로 갈린 `HOLDER_STANCE_CALIBRATION_AMBIGUITY`다.
`true_semantic_variance_subject_count=0`이며 M12D의 STABLE 4,
BOUNDARY_UNCERTAINTY 3, UNSTABLE 1과 전체 FAIL은 그대로 유지한다.

현재 Directional contract는 5.0/5.5/6.0/6.5와 6.0 threshold, 0.5 increment,
adjacent-fit 시 5.0 방향의 보수적 tie-break를 이미 명시한다. 그러나 shared-lineage cash
metrics와 independent corroboration의 차이, corroboration과 limiting Unknown의 ordinal
배치, flat operations와 non-operating support의 5.0/5.5 경계, valuation/persistence
Unknown이 남을 때 6.0/6.5 경계가 financial context에 충분히 구체적이지 않다. 실제
M12D 세 경계 case는 보수적 tie-break를 일관되게 적용하지 않았다. new-buyer와 holder
enum도 각각 valuation/confirmation 및 fundamental REVIEW/REDUCE 경계를 명확히 닫지
않지만 하나의 직접 결합 원인은 아니므로 primary repair에 함께 넣지 않는다. formal
stability classifier는 실제 output instability를 올바르게 검출했으므로 `KEEP`이고 과거
결과 재분류는 0이다.

따라서 한정된 다음 repair는
`BOUNDED_FINANCIAL_CONTEXT_BOUNDARY_CALIBRATION_REPAIR`로 동결한다. 다음 scope는
`BOUNDED_FINANCIAL_CONTEXT_BOUNDARY_CALIBRATION_REPAIR_AND_FULL_FICTIONAL_CANARY`다.
threshold/increment/HOLD lean은 바꾸지 않고 evidence sufficiency와 기존 tie-break의
적용만 일반 계약으로 명확히 한 뒤, 새 generation에서 동일 8개 subject x 3회 전체
fictional canary를 수행한다. new-buyer와 holder ambiguity는 독립 후속 검토로 남긴다.

M12S는 review-only이므로 Directional prompt/calibration/new-buyer/holder/classifier,
financial selector/source mapping, QTD/YTD·working-capital validator, schema,
Price-Timing, renderer, production runtime 변경은 0이다. production DB/assessment/warning/
notification/send, monitoring registration, main merge, deploy도 0이고 승인된 monitoring
8개는 PAUSED/DISABLED 상태를 유지한다. `M12S_COMPLETE`,
`fresh_real_proof_readiness=NOT_READY`, `production_readiness=NOT_READY`이며 repaired full
fictional canary 전에는 fresh real proof나 monitoring resume를 시작하지 않는다.

---

## 12E. M12E boundary calibration repair와 부분 canary 종료

작업지시서 commit은 `3dd15fdc9ef60ad14a120fa22bf03a7b79a6ac1a`, base는
`67bdc56bcd0dba05d154c727fa1f819816b1a1f4`, frozen implementation은
`44ce3a5894a4cf1086cb9b0c21c9f5d5b8dac630`이다. branch는
`codex/20260909-bounded-financial-context-boundary-calibration-m12e`이며
main `d18e68b1e944d7749d093b08797fcd9498412680`에 merge/deploy하지 않았다.
M12S 권위 ZIP SHA `d9533246a23d7fc6eab6da6637f1254a8748f7e37aa45252840566df5602f3de`와
payload 38개를 재검증했다. 기존 M12D source context는 내용 변경 없이 재사용했다.

변경 owner는 `directional_balance_service.ORDINAL_CALIBRATION_PROMPT`의 일반 문단
4개뿐이다. 같은 OCF/PPE residual lineage를 독립 근거로 중복 계산하지 않고,
원인·가역성·지속성 Unknown을 negative evidence가 아닌 강도 제한으로 취급하며,
flat operations와 non-operating support만으로 positive lean을 만들지 않고,
최소 방향 6.0과 더 강한 6.5의 근거를 분리한다. threshold 6.0, increment 0.5,
HOLD lean, 보수적 tie-break, buyer/holder, schema, selector, financial/QTD/WC validator,
classifier, Price-Timing, renderer, source sufficiency, Daily Delta는 그대로다.

모델 호출 전 focused 107/107, full pytest 3123/3123, Ruff 및 diff 검사가 PASS했다.
초기 deterministic 실패 3건은 원본을 보존하고, historical 전체 파일 freeze를
non-prompt AST freeze로 구분하며 역사적 transport 크기 fixture에 정확한 이전 prompt를
사용하도록 테스트만 수리했다. transport 크기 제한은 그대로이고 실제 M12E canary는
새 prompt를 사용했다. GitHub Actions implementation exact SHA는 **FAIL**이다:
shallow checkout의 historical git object 부재 4건, hosted Linux에 local-only ZIP 부재
1건이다. 이 중 2건은 신규 M12E history-dependent test이고 3건은 기존 테스트다.
이를 CI PASS로 표시하지 않으며 frozen generation 이후 CI hotfix도 하지 않는다.

초기 구현 authoring receipt는 Astra/ultra였음을 사용자에게 공개했다. 사용자의 모델
설정 변경 후 Astra/xhigh turn receipt를 확인하고 frozen diff를 재검토했다. 실제
investment canary 두 호출은 모두 `gpt-6-astra / xhigh`, CLI `0.153.4`로 확인됐다.
모든 구현이 처음부터 xhigh였다고 주장하지 않는다.

```text
generation_id = 20260909-m12e-fictional-20260909T135434Z-60be4412b6eb
source_lock_sha256 = f560bb1aa9ed648916d5a1b5c40ca2973c6cdd27a16297789195189b467666c6
planned contexts = 6 (2 contexts x 3 repetitions)
completed calls = 2; remaining 4 = NOT_RUN
transport = 2/2 PASS; canary contexts = 1 PASS / 1 FAIL
schema = 8/8 PASS; frozen semantic = 7/8 PASS
frozen validator errors = 2; separate false-reject findings = 2
selected / first-class / used typed refs = 15 / 15 / 15
grounding failures = 0; QTD/YTD violations = 0
full formal/core/stance repeated stability = NOT_MEASURED
retry / timeout / capacity failure / orphan receipt count = 0
```

FIC-FIN-08은 보험업에 일반 영업기업의 순부채·운전자본 틀을 **적용하지 않는다**고
명시했고 typed financial refs는 사용하지 않았다. 그러나 `순부채` 존재만 보는
financial validator와 case audit이 각각 `net_debt_claim_without_complete_net_debt_evidence`,
`financial_sector_generic_reasoning`을 발생시켰다. 소스 감사상 비적용 문장의 false
reject 2건이며 해당 오류가 가리킨 실질적 부채 계산·금융업 일반화 위반은 확인되지
않았다. 원본 후보와 frozen FAIL은 수정하지 않는다. 두 번째 호출 즉시 전체 generation을
중단했으며 나머지 4회 호출·selective rerun·중간 hotfix는 0이다.

목표 FIC-FIN-01/02/04의 첫 관측은 각각 BUY 6:4, HOLD 4.5:5.5 SELL_LEAN,
HOLD 5:5 NEUTRAL로 계약에 부합했다. 단 한 번의 관측이므로 안정성 성공은 아니다.
독립 회귀 관측 FIC-FIN-05는 기존 M12D의 SELL 4:6 / WEAKENED에서 이번에는
HOLD 4.5:5.5 SELL_LEAN / UNCHANGED로 나타났다. complete interest-bearing debt와
cash 근거를 인용했지만 재융자 조건·만기 집중 Unknown을 강도 제한으로 사용했다.
계약 clarification이 독립 leverage 근거까지 과도하게 제한하는지 bounded review가
필요하다. 모델도 Sol에서 Astra로 바뀌었으므로 prompt만의 인과 효과로 단정하지 않는다.
buyer/holder summary의 literal `[E..]` alias 8건은 별도 메시지 품질 advisory다.

`M12E=PARTIAL_STOPPED`, `P0 open=0`, `P1 open=2`이며 다음 scope는
`BOUNDED_FINANCIAL_EXCLUSION_VALIDATOR_REPAIR_AND_LEVERAGE_BOUNDARY_REVIEW`다.
이 scope는 다음 승인 작업의 제안이지 현재 frozen canary 수리 권한이 아니다.
new-buyer/holder 독립 안정성 후속은 미측정 상태로 유지한다.
`fresh_real_proof_readiness=NOT_READY`, `production_readiness=NOT_READY`다.
실종목·judge·provider 신규 호출, production DB/assessment/warning/notification/send,
monitoring registration, scheduler 변경·자동 재개는 모두 0이다. 종료 관측에서도 승인된
예약 8개는 PAUSED/DISABLED였다. 증거 및 세부 completion은
[M12E reports](reports/20260909-bounded-financial-context-boundary-calibration-full-fictional-canary/59-program-completion.json)에 보존한다.

---

## 12F. 금융업 비적용 수리, 레버리지 계약 검토와 실행 시간초과 종료

작업지시서 commit은 `a7029856c189599c96f6c357bb2c949a47af10a3`, base는
`19b3dd7bc2353f418452e2db67c78e886a73cbc6`이다. 코드 구현은
`dc80d2b67961d7e71983db91351657a4132f2e78`, 최종 사전 동결은
`13d21ae25b9a61b95ab433bb5070d4cf8fb21666`이다. 첫 Phase A는 첨부 지시서 끝의
빈 줄 하나로 diff 검사만 실패했다. 원본 FAIL과 모델 호출 0회를 보존한 뒤 공백만
정리하고 focused 135/135, full pytest 3174/3174, Ruff, base 대비 diff를 재통과했다.
M12E ZIP SHA와 payload 177개 무결성도 재확인했다.

일반 helper는 `ASSERTION_OR_APPLICATION`, `EXPLICIT_EXCLUSION`,
`UNCERTAIN_OR_AMBIGUOUS`를 구분한다. 명시적으로 지배되는 명사형 framework
비적용만 허용하고, 다른 절·필드의 실제 적용이나 산업재 typed ref를 면제하지 않는다.
기존 M12E FIC-FIN-08 원본의 별도 오프라인 replay는 PASS다. positive 12개와
negative 20개 대조군, 혼합·모호한 문장 대조군을 확인했다. 원래 M12E FAIL은 유지한다.

레버리지 root cause는 `ASTRA_OUTPUT_CONSISTENT_WITH_CURRENT_5_5_CONTRACT`다.
이 사례의 complete debt와 cash는 같은 재무완충력 축의 구성요소이며 참조 수로
독립 악재를 중복 계산하지 않는다. 영업이익이 안정적이고 차환·만기·상환 압력의
심각성이 미확인인 경우 5.5 negative lean이 타당하다. Unknown은 호재가 아니라
강도 제한이다. 실제 차환·상환 압력은 별도 최소 SELL 근거가 될 수 있지만 점수표나
기계적 checklist는 만들지 않는다. baseline 대비 악화가 입력에 없으므로 UNCHANGED는
타당하다. Sol의 과거 SELL/WEAKENED/AVOID를 Astra 필수 label로 삼지 않는다.
따라서 Branch A를 선택했고 prompt·threshold·increment·lean·tie-break·buyer/holder는
변경 0이다. selector·typed projection·WC/QTD·기타 financial validator·Price-Timing·
renderer·source sufficiency·Daily Delta도 그대로다.

```text
generation = 20260909-m12f-fictional-20260909T150248Z-04f38944c4bf
source_lock_sha256 = 7e8f87c4ae0c931e6d893206097ad03e2d4ccb1e481a34194e343ac653c78c19
authoring / attempted runner = gpt-6-astra / xhigh
planned = 6 contexts / 24 rows
attempted = 2 contexts; remaining 4 NOT_RUN
run-1/context-01 = PASS, 4/4 schema + semantic + grounding
run-1/context-02 = MODEL_TIMEOUT at 1800 seconds, raw output absent
completed selected / used typed refs = 11 / 11
completed-row financial violations / grounding failures = 0 / 0
wrapper retry = 0; CLI internal reconnect warnings = 2
timeout = 1; observed capacity failure = 0; orphan = 0
full formal/core/stance stability = NOT_MEASURED
new FIC-FIN-05/08 result = NOT_MEASURED
```

첫 context는 약 1133.48초에 완료됐다. FIC-FIN-01/02/04의 첫 bucket은 각각
BUY 6:4, HOLD 4.5:5.5, HOLD 5:5로 동결 계약과 부합했고 FIC-FIN-03의 QTD 흑자와
YTD 손실도 구분했다. 단 한 번의 관측은 안정성 PASS가 아니다. 두 번째 context는
WebSocket connection-reset 경고 뒤 완성 출력 없이 watchdog에서 SIGTERM 종료됐다.
첫 context에도 내부 재연결 경고가 1건 있었으므로 총 2건을 명시한다. 원본 receipt의
transport_attempt_count=1은 wrapper 호출 수이며 실제 내부 sampling 재시도 전체를
뜻하지 않는다. backend request 총수는 미측정이다. timeout을 금융 validator 또는
capacity 문제로 단정하지 않는다. 실패 receipt의 observed_runtime 후처리 누락은
로그 header로 보완해 검증했으며 원본 receipt는 변경하지 않는다.

GitHub hosted CI는 코드 구현 및 공백 정리 SHA에서 3169 PASS / 5 FAIL이다.
historical Git object 부재 3건, 로컬 전용 ZIP 부재 2건이며 새 M12F 테스트의 ZIP
의존 실패 1건도 포함된다. hosted lint는 test 실패로 SKIPPED다. 이를 CI PASS로
표시하지 않는다. 생성 이후 662개 코드 파일과 4개 설정 파일의 해시 변경은 0이다.

`P0 open=0`, `P1 open=2`는 실행 timeout의 원인 검토와 hosted CI portability다.
`fresh_real_proof_readiness=NOT_READY`, `production_readiness=NOT_READY`이며 다음은
`BOUNDED_ASTRA_TRANSPORT_TIMEOUT_REVIEW_BEFORE_NEW_FULL_FICTIONAL_CANARY`다.
현재 결과를 보고 금융 계약을 다시 바꾸거나 즉시 재호출하지 않는다. 보존된 실행
증거 검토 후 별도 승인과 새 generation이 필요하다. 전역 buyer/holder 수리 필요성은
현재 표본으로 판단하지 않는다. 실종목·judge·provider 호출과 모든 운영 mutation은 0,
종료 관측에서도 승인된 예약 8개는 PAUSED다. 원본과 세부 결과는
[M12F reports](reports/20260909-financial-exclusion-validator-repair-leverage-boundary-full-fictional-canary/71-program-completion.json)에 있다.

---

## 13. 이번 마스터 변경 이력

| 이전 표현/흐름 | 이번 정리 |
|---|---|
| Source/canary 준비와 새 holdout 반복이 사실상 현재 작업 | 공통 판단 필드·검사 수리와 보존 증거 분석을 현재 단계로 이동 |
| 다음 scope `GENERIC_OWNERSHIP_ARCHITECTURE_REPAIR`만 존재 | 원본 label은 보존하되, 승인 범위는 Unknown contract/early Core validation으로 좁힘 |
| C가 summary에서 NOT_RUN | raw 기준 부분 실행 후 실패로 명시; 정정 artifact 필요 |
| Calibration 가상 PASS | 해당 prompt의 역사적 PASS로 유지; 실종목 안정성은 아직 미확립 |
| Renderer ownership PASS | 메시지 구체성·입력 충분성과 별개로 기록 |
| Ownership proof 다음 바로 bootstrap | 비운영 통합·판단/메시지 품질·lifecycle 검토 후 필요한 최종 proof/승격 순서 명시 |
| Production scheduler 변경 무조건 0 | 사용자 승인 8개 중단 유지에 한정한 예외와 실제 건수 보고 |
| 자동 live 재개 가능성 | 명시적 사용자 재개 승인 전까지 0 |
| 새 기능 부족이면 universe부터 확대 | 새로운 직접 blocker가 확인되지 않으면 기존 기반 수리 반복 금지 |
| M2에서 source-to-Core 누락을 가정 | 보존 8-domain 감사에서 packet→Core drop 0; archive 부재와 Core drop을 분리 |
| 반복 문장을 renderer synonym으로 완화 | model-owned reasoning, wrapper, input equivalence를 분리하고 renderer ownership 유지 |
| Initial/Baseline/Daily를 같은 change 필드로 표현 가능 | lifecycle mode와 baseline/cutoff/refresh provenance를 명시하고 잘못된 delta 승격 차단 |
| M3 lifecycle이 계획 상태 | 격리 SQLite canonical 경계 실행과 12/12 fixture로 완료; production readiness는 유지 |
| M3 뒤 즉시 최종 holdout 가능 | source-domain / Directional specificity 설계 판단을 먼저 수행 |
| 6개 재무 도메인을 한 번에 production packet과 prompt에 추가 | typed packet 확장 → 기존 canonical adapter → 추가 source mapping → Directional specificity → model/holdout 순으로 분리 |
| 총부채를 debt로 사용 가능 | interest-bearing debt scope가 아니므로 debt/liquidity 계약에서 명시적으로 차단 |
| OCF-PPE 지출을 일반 FCF로 표시 | `OCF less PPE acquisition cash outflow` 또는 PPE-only 범위로 제한하고 management-defined FCF와 구분 |
| 새 재무정보를 universal source gate로 추가 | universal gate 0; claim/sector 조건부 의미만 동결 |
| M4가 제안한 optional financial context는 미구현 | M5에서 additive typed schema와 hard validator 구현; producer와 AI 소비는 계속 0 |
| M5 envelope는 비어 있는 optional field | M6에서 기존 canonical OCF/PPE/OCF-PPE에만 shared adapter를 연결; compact AI context 소비는 계속 0 |
| derived-period OCF/PPE도 input ID만 있으면 adapter가 신뢰 가능 | formula/version을 포함한 완전한 lineage projection이 없으므로 M6에서 fail-closed하고 다음 mapping backlog로 이동 |
| M6의 derived-period 차단은 source fact 부재 | M7에서 보존된 189개 derived-period lineage와 87개 FCF input chain을 projection해 해소; 새 derivation은 0 |
| KR period mapper 구현은 곧 KR 시장 지원 | exact-context mapper capability와 실제 issuer coverage를 분리; real cached canonical KR fact 부재로 실제 KR block 유지 |
| OpenDART axis 이름에 consolidated/separate가 모두 있으므로 basis 불명 | axis label이 아니라 exact dimension member로 basis를 판별; real cache 7개에서 고유 duration context 승격 |
| HUT/SKHY 역사적 gap이면 issuer 예외를 추가 가능 | HUT은 source evidence 부족으로 defer, SKHY는 generic IFRS class 지원과 issuer occurrence 부재를 분리; ticker branch 0 |
| M8에서 새 금융 source가 생기면 모델 입력과 Daily Delta도 확장 | canonical/financial_context까지만 확장하고 compact AI context·source sufficiency·Daily Delta는 그대로 유지 |
| legacy `FinancialSnapshot.debt`를 debt total로 재사용 가능 | 실제 source가 `부채총계`이므로 M9 canonical debt 입력에서 차단하고 legacy field를 재해석하지 않음 |
| 알려진 debt component 합계를 total debt로 표시 | current/non-current completeness와 overlap·basis 검사를 모두 통과할 때만 total 및 net debt 생성 |
| cash 또는 cash+restricted cash를 같은 liquidity basis로 차감 | net debt cash basis는 cash and cash equivalents only; restricted/combined cash는 별도 context 또는 차단 |
| 금융업에도 industrial net debt 적용 | bank/insurance/reinsurance는 sector framework required로 분리 |
| inventory·trade AR/AP와 broad/current/contract balance를 같은 working-capital 값으로 취급 | exact semantic class를 분리하고 aggregate·net precedence 및 overlap 차단 적용 |
| 반기말과 전기말 차이를 YoY로 표현 가능 | `prior_year_end`로 명시하고 `prior_year_comparable`과 별도 lineage 유지 |
| current assets minus current liabilities를 operating working capital로 사용 | M10에서 universal NWC/OWC 공식과 DSO/DIO/DPO/CCC 파생을 모두 금지 |
| 전체 내부 packet schema SHA가 과거 실험 SHA와 달라지면 무조건 실패 | M5 필드를 제거한 legacy projection SHA가 과거 값과 같아야 하며 새 schema SHA는 별도 동결 |

이번 갱신은 M11 non-operating/financial-income effects direct mapping, statement-presentation 보존, aggregate/child overlap 제어와 bounded net-financial-effect derivation을 반영한다. 완료 의미는 `M11_COMPLETE`이며 `financial_domain_coverage_readiness=READY_WITH_KNOWN_OPTIONAL_GAPS`, `model_emission_effectiveness=NOT_MEASURED`, `formal_current_cohort_stability=NOT_MEASURED`, `ownership_generalization=NOT_ESTABLISHED`, `production_readiness=NOT_READY`를 유지한다. compact AI context, Directional/Timing prompt, renderer, source sufficiency, Daily Delta·warning 의미 변경은 0이다. 모델 호출·provider fetch·production mutation·send·merge·deploy·scheduler resume도 모두 0이다.

---

## 2026-09-10 M12X Positive Stronger-Bucket Contract Review

M12W의 FIC-FIN-01 `BUY 6.0` exact target은 generic contract보다 좁은 fixture 제약이었다.
M12X는 production Directional prompt, threshold, increment, HOLD lean, tie-break, 금융 의미론,
source packet을 바꾸지 않고 목표만 `BUY 6.5`로 바로잡았다. 영업 개선, reported QTD OCF 및
현금전환 개선, 순현금 회복력은 서로 다른 지지 축이며 가치평가와 지속성 Unknown은 확신의
한계이지 보편적인 6.5 상한이 아니다. 점수표나 evidence-count 규칙은 도입하지 않았다.

새 generation `20260910-m12x-fictional-20260910T031958Z-a6c5d77c56d5`는 source lock
`9b66dd9ac8eca70fc7cb9e7912f575d9014b3430fb725917269837f17136c2a8`로 동결했다.
Sol/xhigh run-1 context-01은 4/4 PASS했고 FIC-FIN-01은 `BUY 6.5:3.5`로 새 계약과 일치했다.
context-02는 transport 자체는 PASS했지만 FIC-FIN-05가 frozen `BUY 4.5` 대신 `4.0`,
FIC-FIN-08이 보험 exclusion 문장에 대해 net-debt/financial-sector generic reasoning 오류를
받아 FAIL했다. 전체 중단 규칙에 따라 run-2/3 네 context는 NOT_RUN이며 안정성은
NOT_MEASURED다. 재호출, selective rerun, 중간 hotfix는 없었다.

따라서 `M12X_PARTIAL_STOPPED`, `fresh_real_proof_readiness=NOT_READY`,
`production_readiness=NOT_READY`, 다음 scope는 `SOL_RUNTIME_REGRESSION_REVIEW`다. 다음 검토는
보존 출력만으로 FIC-FIN-05 exact target의 정당성과 FIC-FIN-08의 명시적 exclusion 언어
오탐 가능성을 분리해야 한다. 새 model call은 별도 승인과 새 generation 전까지 금지한다.
실종목/model judge/provider/production send 및 모든 운영 mutation은 0이고, 시작과 종료 시
예약 8개는 모두 PAUSED였다. 상세 결과는
[M12X completion](reports/20260910-m12x-completion.md)과
[program completion](reports/20260910-positive-stronger-bucket-contract-review-full-sol-fictional-canary/75-program-completion.json)에 있다.

## 2026-09-10 M12AA Boundary-Band and Financial-Framework Application Scope

M12AA는 canary 중단 조건을 runtime/schema/objective-semantic hard failure와 calibration,
stance, confidence observation으로 분리했다. 같은 shared role classifier가 net-debt와
financial-sector validation을 소유하며, 산업회사식 틀의 실제 적용과 명시적 비적용 또는
대체 프레임 적용을 구분한다. M12Z의 FIC-FIN-08 보험 문장은 contrastive replacement로
통과했고 실제 mixed application과 unresolved material use는 계속 fail-closed한다.

새 generation `20260910-m12aa-fictional-20260910T065817Z-ba878001b3d4`는 source lock
`bc882f77f32f2fe9a2448d71cf7ad30147a49bcfb2588a81d4013d35d7a2e37a` 아래
`gpt-5.6-sol / xhigh` 6/6 context와 24/24 schema row를 완료했다. timeout, retry,
capacity, orphan, runtime/schema/objective-semantic hard failure, invalid reference, grounding,
financial-sector false reject/accept, business-delta failure는 모두 0이다. production prompt,
threshold, increment, lean, tie-break, source selection, Daily Delta, Price-Timing, renderer와
운영 동작은 변경하지 않았다.

FIC-FIN-05는 `SELL 4.0:6.0`, `HOLD 4.5:5.5 SELL_LEAN`, `SELL 4.0:6.0`으로
변동했다. frozen minimum-SELL tuple의 `lean=null`과 schema 출력의 `NOT_HOLD`가 달라 두
SELL row는 exact comparator에서 `OUT_OF_BAND_OTHER`로 남는다. output 후 band/target을
바꾸거나 PASS로 재해석하지 않았다. FIC-FIN-08은 balance가 5:5로 유지됐지만 holder
stance가 REVIEW/HOLDABLE로 변했다. 최종 분류는 stable 6, boundary uncertainty 1,
unstable 1이며 opposite-direction reversal은 0이다.

따라서 `M12AA_COMPLETE`지만 `fresh_real_proof_readiness=NOT_READY`와
`production_readiness=NOT_READY`다. P0는 0이고 P1은 frozen band shape mismatch와
material stance instability 두 건이다. 다음 scope는
`BOUNDED_NEW_BUYER_STANCE_CALIBRATION_REPAIR_GPT56_SOL`이며 새 모델 호출은 별도 승인이
필요하다. 실종목/provider/judge 호출, production mutation/send, merge/deploy, scheduler
변경과 자동 재개는 모두 0이고 예약 8개는 PAUSED 상태를 유지했다. 상세 결과는
[M12AA completion](reports/20260910-m12aa-completion.md)과
[program completion](reports/20260910-boundary-band-canary-policy-financial-framework-application-scope-full-sol-canary/81-program-completion.json)에 있다.

## 2026-09-10 M12AB Leverage HOLD/SELL Boundary Resolution Architecture

M12AB는 M12AA comparator의 non-HOLD `lean=null`, `NOT_HOLD`, not-applicable 표현을 같은
canonical 상태로 정규화했다. 이에 따라 FIC-FIN-05의 M12AA 관측은 minimum SELL 2회,
HOLD 4.5:5.5 SELL_LEAN 1회, out-of-band 0회이며 stable preference는
`MIXED_BOUNDARY`로 정정됐다. M12AA 원본 ZIP은 변경하지 않았다.

Options A-H 검토에서는 Option F를 유일하게 선택했다. AI가 raw core와 인접 경계 선언을
소유하고, 별도 versioned experimental resolver가 선언된 두 인접 bucket 중 5.0에 가까운
덜 방향적인 endpoint만 기계적으로 선택한다. raw와 resolved core를 모두 보존하며 majority
vote, 평균, 고정 점수, evidence-count bucket, ticker-specific 규칙은 도입하지 않았다.
production schema와 prompt, threshold, increment, tie-break, source semantics도 그대로다.

새 generation `20260910-m12ab-fictional-20260910T092640Z-741ca9a40148`는 source lock
`1018dd3213e9514f2ebe38f2b0223a3e3a88d096bbef31e2edf90d30edbe0adb` 아래
`gpt-5.6-sol / xhigh`로 시작했다. run-1 context-01은 4/4 PASS했다. context-02는 transport,
parse, schema 4/4는 PASS했지만 FIC-FIN-08 보험 문맥에서
`net_debt_claim_without_complete_net_debt_evidence`와 `financial_sector_generic_reasoning`
두 objective-semantic hard error가 발생했다. 규칙대로 2/6 calls, 8/24 rows에서 즉시
중단했고 selective rerun, 중간 hotfix, 새 generation은 없었다. 미실행 16 rows는
schema failure가 아니라 `NOT_RUN`이다.

FIC-FIN-05의 유일한 관측은 raw/resolved 모두 `HOLD 4.5:5.5 SELL_LEAN`이었지만 boundary
declaration은 없었다. 요구된 3회 boundary declaration 및 안정성은 측정 불가다. 따라서
`M12AB_PARTIAL`, `fresh_real_proof_readiness=NOT_READY`,
`production_readiness=NOT_READY`이며 다음 scope는
`LEVERAGE_HOLD_SELL_BOUNDARY_RESOLUTION_REPAIR_GPT56_SOL`이다. 실종목/provider/judge 호출,
production send/mutation, merge/deploy, scheduler 변경은 모두 0이고 시작과 종료 시 예약
8개는 모두 PAUSED였다. 상세 결과는
[M12AB completion](reports/20260910-m12ab-completion.md)과
[program completion](reports/20260910-leverage-hold-sell-boundary-resolution-architecture-full-sol-canary/88-program-completion.json)에 있다.

## 부록 A. 핵심 증거 위치

모두 S1 ZIP 내부 상대 경로다.

```text
completion.json
artifact-index.json

experiment/fresh-real-proof/model-contexts/{FIRST,A,B,C}/DIRECTIONAL_CORE/batch-*/output.raw.json
experiment/fresh-real-proof/model-contexts/{FIRST,A,B,C}/PRICE_TIMING/batch-*/output.raw.json
experiment/fresh-real-proof/model-contexts/C/DIRECTIONAL_CORE/batch-01/partial_semantic_audit.json
experiment/fresh-real-proof/model-contexts/C/PRICE_TIMING/batch-01/partial_semantic_audit.json

experiment/fresh-real-proof/issuer-results/{FIRST,A,B}/{ticker}/composed-state.json
experiment/fresh-real-proof/issuer-results/{FIRST,A,B}/{ticker}/rendered-message.txt
experiment/fresh-real-proof/issuer-results/{FIRST,A,B}/{ticker}/renderer-input-lineage.json

reports/proofs/60-fresh-directional-core-stability.json
reports/proofs/61-fresh-price-timing-stability.json
reports/proofs/65-fresh-message-quality-summary.json
reports/proofs/69-next-scope-handoff.json
experiment/fresh-real-proof/schedule-pause-observation.json
```

`{...}`와 `batch-*`는 path pattern이며 모든 조합이 존재한다는 뜻이 아니다. C Timing은 batch-01만 존재한다.

## 부록 B. 읽는 순서

새 세션에서는 이 master → M3 완료 보고서 → M3 작업지시서 → M2 완료 보고서 → 필요한 S1/S2/S3 순으로 프로젝트 상태를 확인한다. 다음 설계 검토와 모델 proof는 각각 별도 지시와 승인 후 시작하며, 옛 handoff의 현재 단계나 cohort를 복원해서 덮어쓰지 않는다.
