# M12F 완료 보고서

작업일: 2026-09-09. 종료일: 2026-09-10 KST.
상태: **PARTIAL_STOPPED**. 새 실종목 proof와 production 모두 **NOT_READY**.

## 핵심 결과

- 금융업의 명시적 비적용 문장과 실제 산업재 금융지표 적용을 구분하는 validator를 수리했다.
- 기존 M12E FIC-FIN-08 원본은 오프라인 재검사 PASS다. 과거 원본 FAIL은 그대로 보존했다.
- 높은 부채와 얇은 현금이 한 재무완충력 축을 설명하는 FIC-FIN-05에서는, 안정적 영업이익과 차환·만기 심각성 미확인을 고려한 HOLD 4.5:5.5가 현재 계약에 부합한다.
- 과거 Sol의 SELL/WEAKENED를 Astra의 필수 정답으로 삼지 않았다. Directional prompt 변경은 0이다.
- 긍정 대조군 12개, 부정 대조군 20개와 혼합·모호성 대조군을 검증했다.

## 새 가상 실행

`generation_id = 20260909-m12f-fictional-20260909T150248Z-04f38944c4bf`

`source_lock_sha256 = 7e8f87c4ae0c931e6d893206097ad03e2d4ccb1e481a34194e343ac653c78c19`

| 항목 | 결과 |
|---|---|
| 모델 / effort | gpt-6-astra / xhigh |
| 계획 | 6 contexts, 24행 |
| 실제 시도 | 2 contexts |
| run-1/context-01 | 약 18분 53초, 4/4 PASS |
| run-1/context-02 | 30분 MODEL_TIMEOUT, raw output 없음 |
| 나머지 4회 | NOT_RUN |
| 생성된 4행 schema / semantic / grounding | PASS |
| CLI 내부 재연결 경고 | 첫 호출 1건 + 두 번째 1건 |
| wrapper 재시도 / batch split | 0 / 0 |
| timeout / 관측 capacity failure / orphan | 1 / 0 / 0 |
| 전체 반복 안정성 | NOT_MEASURED |
| 새 FIC-FIN-05 / 08 관측 | NOT_MEASURED |

첫 결과의 FIC-FIN-01/02/04는 각각 BUY 6:4, HOLD 4.5:5.5, HOLD 5:5로
동결된 계약과 일치했다. FIC-FIN-03은 QTD 흑자와 YTD 손실을 구분했다.
1회 관측을 반복 안정성 성공으로 확대하지 않는다.

두 번째 호출은 WebSocket 연결 리셋 경고 후 완성 출력 없이 watchdog에서 종료됐다.
이 관측만으로 서버 capacity, 금융 validator, schema 또는 source 문제를 원인으로
단정할 수 없다. 원본 receipt의 transport_attempt_count는 wrapper 호출 수이며,
CLI 내부 sampling 요청 총수를 의미하지 않는다. 실제 backend 요청 총수는 미측정이다.

## 검증과 안전

- 로컬 focused: 135/135 PASS.
- 로컬 full pytest: 3174/3174 PASS. Ruff / diff: PASS.
- GitHub CI: 3169 PASS / 5 FAIL, hosted lint SKIPPED.
- CI 실패는 과거 Git object 부재 3건과 로컬 ZIP 부재 2건이다. 신규 M12F 테스트의 로컬 ZIP 의존 1건도 포함된다.
- 첫 Phase A의 지시서 EOF 빈 줄 실패는 보존했다. 모델 호출 전에 공백만 정리하고 전체 검사를 재통과했다.
- generation 이후 코드·설정 변경, 재호출, fallback: 0.
- 실종목·judge·provider 호출, production DB/발송/merge/deploy: 0.
- 승인된 8개 예약은 시작·종료 모두 PAUSED다.

## 저장소와 다음 단계

- Branch: `codex/20260909-financial-exclusion-leverage-boundary-m12f`
- Base: `19b3dd7bc2353f418452e2db67c78e886a73cbc6`
- 지시서: `a7029856c189599c96f6c357bb2c949a47af10a3`
- 코드 구현: `dc80d2b67961d7e71983db91351657a4132f2e78`
- 최종 사전 동결: `13d21ae25b9a61b95ab433bb5070d4cf8fb21666`

P0 open: 0. P1 open: 2 (실행 timeout 원인 검토, hosted CI portability).
보고서의 final SHA와 index 검증 수치는 ZIP의 `reports/71-program-completion.json`에 있다.
원본 출력·실패·receipt는 수정하지 않았다.

**FRESH_REAL_PROOF_READINESS: NOT_READY**

다음 범위:
`BOUNDED_ASTRA_TRANSPORT_TIMEOUT_REVIEW_BEFORE_NEW_FULL_FICTIONAL_CANARY`

보존된 실행 증거를 먼저 검토하고, 별도 승인 후 새 generation으로 재검증해야 한다.
현재 실패를 근거로 금융 계약을 hotfix하거나 자동으로 모델 호출을 재개하지 않는다.
