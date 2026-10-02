# R2B-R9-REV6 사전계약 구현·종료 보고서

## 최종 판정

**R2B_R9_REV6_PREFLIGHT_CONTRACT_GAP**

REV6 전체 완료가 아닙니다. Phase A에서 P1 두 건이 남아 지시서 35절에 따라
라이브 수집과 AI 실행을 시작하지 않고 종료했습니다. 공급자나 모델의 실패가
아니며, 22종목/24메시지는 모두 NOT_RUN입니다. 통과할 때까지 재실행한 AI는 없습니다.

## 저장소

- Branch: `codex/r2b-r9-rev6-contract-closure`
- Base: `e868b781f880dc639457739d0e6785cda3feca4b`
- Work-instruction commit: `cc490817400f22b857c507feb13676589a898da0`
- Implementation/exact tested SHA: `fd0f1bed69fe8f30a1dbe6c7a76e21ffc695c999`
- Accepted R7 diagnostic runtime: `174af2b0a0cef373c85a9a27fe22604839c8acf9`
- Operating: `b610e6de0a8c33d199961e821ff1b130e1fa9ad4`, clean, 변경 없음
- 원본 지시서 ZIP과 최초 지시서 커밋 보존. 사본의 끝 공백 한 곳만 정리.
- 원격 push/main merge/deploy/restart: 모두 0
- 보고서 커밋의 exact SHA와 변경 파일 hash는 `repository-identities.json`에 기록.

## 구현한 오프라인 계약

1. KOSPI200-only: 수집기·파서·히스토리·replay·eligibility·표시가 한 제품 범위를
   공유합니다. KOSDAQ150은 필수가 아니며 선택값에 섞이지 않습니다. 원본 전체
   response hash는 계속 보존하고 경제값의 동일성과 구분합니다.
2. Market 내부 사실/표시 분리: typed display plan, fact/registry hash binding,
   SPY/QQQ/IWM 종가·변화·등락률, 세션별 US/KOSPI/KOSDAQ TOP3/BOTTOM3,
   중복 업종 거절, source-dated USDKRW, KOSPI200 일·주·월 unavailable 표시.
   Accepted Market renderer의 명시적 plan 입력만 지원하며 production 자동 주입은 없습니다.
3. Macro source time: query/retrieval/observation/publication을 분리했습니다.
   ECOS TIME 누락을 조회 날짜로 대체하지 않습니다. FRED는 bounded response의
   최신 유효 row를 선택하고, EIA는 source period를 유지하되 최신성 미증명 상태입니다.
   실제 live ECOS 응답과 대체 timeseries route 검증은 NOT_RUN입니다.
4. All22 오프라인 후보 계획: 88개 가격 역할과 SEC/OpenDART 22종목 예산,
   같은 generation/time/bytes 확인 및 과거 mutable carry-in 거절을 구현했습니다.
   SNDK/005930/047810 제외는 없습니다. 이 계획은 **실행 자격이 아닙니다**.

## 남은 P1 두 건

### P1-C: 완전 신규 소스 controller 및 조합

`scripts/r2b_r9_full_fresh_requalification.py`는 아직 구현되지 않았습니다.
기존 `unified_live_cohort_proof.supplemental_class_c`는 parent 재무·품질·macro에
의존하고, `compose_full_source`는 class-C 금융 입력/기존 versioned business를
요구합니다. 새 bounded 재무 계획은 매출·영업이익·순이익 비교 범위이며,
fresh 품질·EPS/BVPS/forward·security valuation을 끝까지 소유하지 않습니다.
이를 새 값처럼 포장하지 않았습니다. 후보 예산 총 상한
2526회는 최악의 transport 상한일 뿐,
필수 source-role 전체의 실행 계획이 완성됐다는 뜻이 아닙니다. 실제 요청은 0회입니다.

다음 수정은 fresh financial binding을 native stock/full-source 조합기에 연결하고,
동일 수집 증거에서 품질·valuation·issuer bridge를 새로 생성한 뒤 전체 graph를
두 번 replay하는 범위입니다. 기존 parent-packet 경로의 우회 재사용은 금지합니다.

### 상세 종목 renderer

`AcceptedCalibrationPlan`/`calibration_render`는 아직 간략 카드입니다.
요청된 사업·실적, 경고, 2~4개 monitoring, 가격 구조, 수급/참여,
항상 존재하는 valuation 블록의 typed 입력과 acceptance hash 연결이 없습니다.
후처리 문단을 붙여 상세 22개를 만든 것처럼 보고하지 않았습니다.
상세 plan/검증을 먼저 만들고 실제 sender-boundary 캡처로 검증해야 합니다.

## 실행 계수

| 단계 | 실제/목표 | 상태 |
|---|---:|---|
| Provider requests | 0 | 사전계약으로 차단 |
| Stock chart roles | 0/88 | NOT_RUN |
| Fresh stock packets | 0/22 | NOT_RUN |
| Market contexts | 0/2 | NOT_RUN |
| Market/Core/A/B calls | 0/0/0/0 | NOT_RUN |
| Full-source replay twice | 0/2 | NOT_RUN |
| Exact final messages | 0/24 | NOT_RUN |

`COMPLETE_SOURCE_ADAPTER_QUALIFIED=false`. Human-review ZIP과 scheduler cutover
지시서는 만들지 않았습니다. Fixture display plan은 synthetic 단위 증명이며
실제 시황·종목 메시지가 아닙니다. P0 open=0, P1 open=2.

## 검증

- Focused: 948 PASS
- Full pytest: 6264 PASS / 63 unchanged skips / 0 failure
- Ruff, git diff --check, Investment Knowledge, Chart Knowledge: PASS
- exact-SHA clean-tree 및 skip/xfail identity 비교: PASS
- Socket/DNS 차단 아래 실제 외부 연결: 0
- 기존 역사적 scope audit는 FAIL 기대값을 유지하며 추가 변경 파일만 명시했습니다.
- 과거 2종목 필수 테스트를 KOSPI200-only 기대값으로 변경했으며 skip/threshold 완화는 없습니다.
- 이전 진단 검증의 실패와 최종 검증을 모두 분리 보존했습니다.
- GitHub Actions: NOT_RUN (push 금지); 로컬 전체 검증으로만 판정.

## 운영·전달

DB·설정·스케줄러·operating SHA는 직전 R9 safety snapshot과 동일합니다.
Telegram/recipient intent/DB writes/warning/scheduler/notification/broker actions는 0.
기존 원시 증거·평가 이력은 변경하지 않았습니다. 실제 재수집 corpus도 없습니다.

결과는 비밀값 검사 후 ZIP 1개와 SHA 1개로 봉인합니다. iCloud Drive 루트와
Thesis Monitor 폴더에 복사하고 destination hash 및 파일별 업로드 완료를 확인합니다.
클라우드 전달 결과는 로컬 `icloud-delivery.json`에 별도 기록합니다.
