# Thesis Monitor — 마스터 워크플로우

**버전:** 2026-09-08 / m3-nonproduction-monitoring-lifecycle-integration-v1
**문서 성격:** 최신 실행 결과와 사용자 결정에 맞춘 프로젝트 기준선·작업 순서 갱신본.
**현재 위치:** `M3 완료 — source-domain enrichment / Directional specificity 설계 검토가 다음 범위`
**운영 상태:** US/KR 예약 모니터링 중단 유지가 사용자 지시. 자동 재개 금지.
**M3는 격리 DB와 fixture repository에서 등록·baseline·readiness·Daily Delta를 검증했다. 모델 출력 개선·실종목 일반화·production readiness는 여전히 확인하지 않았다.**

---

## 1. 지금 프로젝트가 달성하려는 것

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

### S0 — 현재 권위 M2 결과

```text
thesis-monitor-20260908-nonproduction-integration-decision-message-quality-review-report.zip

실제 SHA-256:
3ca97b17511605c3ead9da46292d1bf151782189ccddf25cd83d3fbcc0939422
```

M3 시작 시 index payload 39개의 hash·size를 전부 재검산했고 mismatch 0, secret scan failure 0을 확인했다. M2의 최종 SHA는 `2257a05f9a599aafd0f3120fb8ab62655bee875a`이며 다음 범위는 M3 작업명과 정확히 일치했다.

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
M3.5 source-domain enrichment / Directional specificity 설계 검토
    [별도 승인 전 모델 호출 없음]
        ↓
M4  변경 사항·판정 기준 동결
    필요한 변경 경로 검증 + 별도 승인된 새 실종목 최종 proof
    [실험 결과 보고 운영 승격 여부 결정]
        ↓
M5  Production Integration Review
    배포·fallback·발송 소유권·rollback 검토
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

### M4 — 변경 동결과 최종 실모델 검증

앞선 의미 변경과 실제 출력 계약이 정리된 뒤에만 실행한다. 모델 호출은 해당 별도 지시서가 명시적으로 승인해야 한다.

기본 정책:
- 변경된 경로만큼의 모델 없는 검증과 필요한 제한적 fictional canary.
- 이전 prompt/model/source에 대한 PASS를 새 prompt의 검증으로 자동 승격하지 않음.
- 전체 일반화가 필요하면 기존 기준의 새 issuer-distinct US4/KR12, 새 source lock, FIRST→A→B→C.
- 단계·run별 gate, context별 즉시 보존, namespace 독립성 유지.
- 지금까지의 경계 안정성 기준을 사후 변경하거나 평균/다수결로 통과시키지 않음.
- 메시지 품질을 future hard gate로 사용할지는 실행 전 결정. 과거 advisory 결과는 그대로 유지.
- 완주와 합격을 구분하고, 반복 안정성과 입력 충분성·판단 유용성을 별개 보고.

현재 M4는 승인되지 않았다. 먼저 M3에서 남긴 source-domain backlog와 Directional specificity의 bounded 설계 결정을 동결해야 하며, M3 완료가 자동 32회 실행을 시작하지 않는다.

### M5 — 운영 통합 검토

점검 대상: 실제 production caller, 권한·설정, persistence, renderer version, exactly-once/lease, fallback·delivery retry, rollback, 기존 데이터 보존, 관측 가능성.

원래 roadmap의 production integration review를 유지한다. 실제 merge/deploy나 자연 실행은 별도 승인과 범위에 따른다. Offline 메시지가 좋아 보인다는 이유만으로 운영 통합을 건너뛰지 않는다.

### M6 — 명시적 재개와 일일 운영

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

이 문서의 M0~M6 상태는 프로젝트 계획용이다. 공개 Action enum이나 production schema를 새로 만들라는 뜻이 아니다.

---

## 11. 다음 한 작업과 그다음 결정

**완료한 작업:** M1 Unknown 계약 수리, M2 nonproduction 판단/메시지 통합 검토, M3 monitoring bootstrap·Daily Delta lifecycle 통합.

**권장 다음 한 작업, 아직 미승인:** `SOURCE_DOMAIN_ENRICHMENT_AND_DIRECTIONAL_SPECIFICITY_DESIGN_REVIEW`.
- 전년 비교, OCF/PPE-CAPEX, debt/liquidity, working capital, non-operating attribution backlog를 실제 판단 가치와 안전 계약 기준으로 좁힌다.
- M3 lifecycle 코드는 넓히지 않고 source→Core 입력 및 Directional specificity의 변경 필요 여부를 먼저 결정한다.
- 이 검토는 기본적으로 비운영·모델 호출 0이며, 변경할 semantic contract가 확정된 뒤에만 별도 승인된 새 model/real-holdout proof로 간다.

**새로운 주요 판단·입력 변경이 정해지기 전에 매번 FIRST/A/B/C를 반복하는 개발 흐름은 중단한다.** 기존 증거로 결정할 수 있는 부분은 먼저 결정하고, 변경을 묶어 동결한 뒤 필요한 실모델 검증을 수행한다.

---

## 12. 이번 마스터 변경 이력

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

이번 갱신은 M3 비운영 lifecycle 통합 결과를 반영한다. 완료 의미는 `M3_COMPLETE`이며 `model_emission_effectiveness=NOT_MEASURED`, `formal_current_cohort_stability=NOT_MEASURED`, `ownership_generalization=NOT_ESTABLISHED`, `production_readiness=NOT_READY`를 유지한다.

---

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
