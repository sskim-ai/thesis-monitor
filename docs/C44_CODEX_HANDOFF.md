# C44: 원격 수정 후 Mac Codex 검증·유지보수 인계

## 1. 목표와 현재 상태

사용자가 허용한 GitHub 직접 수정·push 방식으로 C43 다음 변경을 준비했다. 이 문서는 종전 C44 작업지시서의 **코드 구현·push 금지 부분을 대체**한다. Mac에서는 구현을 처음부터 반복하지 않고 아래 원격 후보를 받아 보존 수락본을 재생하고 사후 처리 파일을 반영한다.

| 항목 | 값 |
|---|---|
| 저장소 | `sskim-ai/thesis-monitor` |
| 기준 브랜치 | `integration/pr52-unified-b2-entry-20261123` |
| 기준 C43 | `2efbe34028116b1ca883c04742aa3c6541ac0db6` |
| C44 검토 브랜치 | `codex/c44-session-entry-postrun-20261123` |
| 사용할 C44 commit | push 결과에서 전달된 최종 SHA. fetch 후 해당 SHA를 기록한다. |
| 분석 코드 운영 반영 | 하지 않음. KR C42 / US C38 기존 pin 유지 |
| Mac 실제 보존 수락본 replay | 아직 하지 않음. 아래 KR1·US1이 인계 범위 |
| Mac 사후 처리 설치 | 아직 하지 않음. 아래 유지보수 2개 파일이 인계 범위 |

코드는 C43 계보 위의 후보다. 원격 `main`이나 두 시장의 운영 작업트리를 이 후보로 바꾸는 작업은 포함하지 않는다. 같은 코드베이스에서 개발·검증하되 운영 전환 전까지 기존 시장별 실행 pin은 유지한다.

## 2. 이미 구현한 내용

### 완료 거래일과 평가일 구분

`app/services/detailed_stock_message_v2.py`에서 이미 수락된 `base.source_stock.completed_session_current_price.target_session`을 사용한다. 이 값은 가격 생산자가 보존한 완료 거래일이며, 세대·시장·종목·증권 식별자를 현재 수락 문맥과 대조한다. 원래 source는 상세 계획의 기존 digest에 묶여 있다.

이 날짜를 진입 품질 판단과 한국 선택 지지 구간 표시에 사용하고, 최종 renderer의 재구성도 같은 source에서 같은 날짜를 읽는다. `assessment_date`는 메시지·사업 평가일로 남는다. quote 날짜를 정답으로 대신 쓰거나 원본 B2 context에 새 필드를 넣지 않는다. projection이 없는 구형 자료는 완료 거래일 근거 부족으로 표시한다.

### 사용자 문안

일반 문안에는 해석 없는 `FAVORABLE_NOW`, `UNRESOLVED`, 긴 reason code를 출력하지 않는다. 원래 B2 request/result/authorization와 내부 timing/reason은 그대로 보존한다.

| 실제 근거 | 사용자 문안 |
|---|---|
| INSIDE | 가격 위치: 선택된 관찰 지지 구간 안 |
| ABOVE | 가격 위치: 선택된 관찰 지지 구간 위 |
| BELOW | 가격 위치: 선택된 관찰 지지 구간 아래 — 구조 재확인 |
| 일봉 없음·사용 불가 | 진입 판단: 일봉 데이터 부족 |
| ENTRY 권한의 지지 Fact 없음 | 진입 판단: 현재 적격 지지 구간 없음 |
| 완료일·통화·조정 기준이 실제로 다름 | 진입 판단: 가격 기준 확인 필요 + 확인된 불일치 |
| 지지는 있으나 선택 연결 부족 | 진입 판단: 선택된 진입 구간 확인 필요 |

경제적 대기 이유는 원래 reason_class로 표시한다. 기업 매력 있음·조건 확인 대기·매수 회피와 가격 위치를 구분한다. 참고 V3 S/R을 진입 구간으로 승격하지 않는다. 가격, PER/PBR/fPER, 사업 설명, Overall, Holder와 confidence 정책은 유지한다.

### 확인된 돌파와 남은 조건

기존 품질 경로가 허용한 동일 세션·ENTRY 권한의 `CONFIRM_ENTRY`와 종가 돌파·거래량 확인이 있으면 ABOVE의 최종 행동을 다음처럼 표시한다.

> 돌파·거래량 확인 완료, 선택된 지지 구간 기준의 진입은 가격 조정 대기

이미 확인된 신호를 다시 기다리라고 하지 않는다. ABOVE를 새 매수 허용 경로로 바꾸거나 거래량·R/R 임계치를 새로 만들지는 않는다.

### C38 사후 처리 후보

`ops/c44/postrun.py`는 기존 Mac 사후 스크립트의 수정본이다. 미국 정기 활성화 함수·호출을 제거했고, 완전 성공은 `C38_US_LIVE_15_15_PASS_US_REGULAR_DEFERRED`로 기록한다. 부분 성공·실패, 최초 분석 오류, 결과 수집과 종료된 단발 정리를 유지한다. `KR_unchanged`는 과거 등록 시점이 아닌 이번 사후 처리 시작·종료 해시를 비교한다.

이 파일은 기존 Mac 경로에 설치할 후보다. **저장소의 `ops/c44` 위치에서 main을 실행하지 않는다.** 상대 경로는 원래 유지보수 위치를 기준으로 동작한다.

## 3. 이미 수행한 집중 검증

다음 5개 파일의 총 **26개 사례가 통과**했다. 신규 C44 16개, 관련 기존 C43/C38 10개다. 개별 확인으로 끝났으며 저장소 전체 pytest를 로컬에서 반복하지 않았다.

```bash
python -m pytest -q \
  tests/test_c44_entry_presentation.py \
  tests/test_c44_renderer_replay.py \
  tests/test_c44_postrun.py \
  tests/test_c43_offline.py \
  tests/test_c38_future_one_shot.py
```

- 합성 KR/US 각각에서 실제 `stock_message → build_detailed_plan_v2 → render_detailed_v2` 경로를 실행했다. 종전 수락 계획 조회만 fixture로 대체했다.
- 평가일 11/24·완료 가격일 11/23이면 평가일 차이만으로 품질이 내려가지 않았다. 대상 완료일과 실제 가격 세션이 다르면 근거 부족을 유지했다.
- 확인된 ABOVE, 실제 결손 설명, DISPLAY 전용 지지 배제, 미지의 reason에 경제적 사유를 만들어 붙이지 않는 경우를 확인했다.
- 원본 context/source/B2 request/result/authorization 불변을 확인했다.
- 사후 처리 성공·부분·실패 및 KR 변경 여부를 임시 파일과 mock으로 확인했다. 실제 observer·영수증 재검증·정리·launchctl·업로드는 실행하지 않았다.

이 결과는 **합성 입력의 집중 시험**이다. C42/C36 실물 수락본 재생이나 새 실물 9/9·15/15 성공을 뜻하지 않는다. `tests/test_production_actual_entrypoint.py`의 바뀐 표시 assertion은 새 문안에 맞췄으며, 그 전체 캠페인 시험은 이 집중 검증에 포함하지 않았다. 기존 GitHub push CI는 저장소 설정대로 별도로 실행될 수 있고, 이 26개 PASS와 CI 전체 상태를 혼동하지 않는다.

## 4. Mac Codex 실행 순서

### A. C44 후보 받기

기존 통합 개발 작업트리를 재사용한다.

`/Users/sskim/Documents/Codex/2026-07-04/the/work/thesis-monitor-c43-unified-20261123`

1. 이 개발 작업트리의 HEAD/status를 한 번 확인한다. 사용자 변경이 있으면 보존하고 적절한 별도 검증 작업트리를 쓴다. 운영 작업트리에서 checkout하지 않는다.
2. `origin`에서 `codex/c44-session-entry-postrun-20261123`을 fetch하고, 전달된 최종 C44 SHA에서 로컬 검증 브랜치를 연다. C43을 다시 병합하거나 커밋을 cherry-pick하여 다른 후보를 만들지 않는다. 기존 로컬 branch가 있으면 현재 상태를 확인해 재사용한다. 강제 reset·force push는 하지 않는다.
3. 해당 SHA가 위 C43의 후손인지, 실제 import가 이 후보를 가리키는지 확인한다. 이전 C44 지시서의 코드 작성 단계를 다시 수행하지 않는다.

### B. 사후 처리 2개 파일 반영

미국 정기 OFF 보류를 확실히 반영하는 유지보수 설치까지 진행한다. 이 단계에 새 승인 대기를 만들지 않는다.

| 대상 | 작업 |
|---|---|
| `/Users/sskim/Documents/Codex/2026-07-04/the/maintenance/20261122-pr52-c38-postrun/postrun.py` | 준비된 `ops/c44/postrun.py`를 기존 경로에 설치 |
| 같은 디렉터리의 `FINAL_COMMAND_PIN.json` | 현재 실행 필드 `script_sha256`만 설치된 정확한 바이트 해시로 갱신 |

검토한 원본 postrun SHA-256:

`96018c3aa724e79eef49042d8d5fe81c83377a037a342af6a59669f1e2d7aa9f`

C44 후보 SHA-256:

`a496520648115a5c1004412eb9baab1c23a23c5ea6b1475ea4aeac00dcbdad74`

`ops/c44/PIN_UPDATE.json`은 갱신할 필드를 적은 안내다. **이를 기존 FINAL_COMMAND_PIN.json 전체와 교체하지 않는다.** 원래 `script`, `registered_command`, `initial_install_script_sha256`과 다른 과거 기록을 보존한다.

설치 직전에 기존 postrun의 PID·잠금·`actual-20261124` 존재를 한 번 확인한다. 아직 실행 전이고 충돌이 없으면 기존 잠금을 짧게 확보하고 준비한 스크립트와 실행 해시 기록을 맞춰 반영한다. 임시 파일 교체 등 기존 원자적 쓰기 방법을 쓰고 최종 설치 바이트와 현재 실행 pin이 일치하는지 확인한다. 원본 해시가 다르면 덮어쓰지 말고 실제 차이를 읽어 이미 반영됐거나 추가 사용자 변경이 있는지 판단한다. 같은 최소 변경만 보존하며 합친 경우 실제 최종 해시를 사용한다.

반영은 **2026-11-24 12:45 KST 발화 전에 끝내며, 발화 시각에 걸쳐 `postrun.lock`을 유지하지 않는다.** 이미 발화 시각이 됐다면 현재 실행·결과를 읽고 설치 여부를 별도로 보고한다. 기존 main의 비차단 잠금과 설치가 경합해 예정 실행이 빠지는 상황을 만들지 않는다.

실행 중이면 파일을 중간 교체하지 않는다. 이미 발화했거나 결과가 있으면 원래 결과를 읽고 설치 상태를 따로 보고한다. 소비 표시·결과 디렉터리를 지워 재실행하지 않는다. 다른 검증은 계속 완료한다.

이 설치는 같은 실행 경로의 2개 파일을 고치는 작업이다. 예약 label·시각·plist·인수나 분석 code pin을 바꾸지 않는다. launchctl reload/bootstrap/kickstart, 실제 postrun main, 단발 정리의 조기 실행은 하지 않는다. 기존 사후 처리에 들어 있는 종료 후 단발 정리는 예정된 실행의 기존 동작으로 남는다.

### C. 저장 수락본 KR1·US1 재생

1. KR은 C42의 보존 수락본 대표 1종목을 선택한다. US는 C43 검토에서 언급한 C36의 정상 가격–구간 관계 사례 중 1종목을 우선한다. V9의 일봉 부족 사례만으로 정상 US 관계를 확인했다고 하지 않는다.
2. 보존 source snapshot, B context, 수락 B/B2, authorization를 그대로 읽어 기존 오프라인 로더로 session을 구성한다. 운영 DB·새 금융 수집·모델을 호출하지 않는다.
3. C44의 실제 `production_message_renderer.stock_message → build_detailed_plan_v2 → render_detailed_v2`를 호출한다. 결과 문자열 일부를 치환해서 만든 문안을 replay라고 보고하지 않는다.
4. 원본 수락 자료와 원래 문안은 그대로 둔다. 새 문안에는 `보존 수락본 기반 오프라인 렌더`임을 표시한다. 기존 request/result/authorization의 hash를 고쳐 맞추거나 새 authorization를 발급하지 않는다. 실제 원래 완료 거래일과 평가일을 각각 기록한다.
5. 적격 지지 표시·대기 사유·참고 S/R 분리, 가격/PER/PBR/fPER/사업/Holder 보존을 확인한다. 기존 읽기 전용 재생의 원래 기록 시각을 사용하고 실시간 freshness를 완화하는 코드를 추가하지 않는다.
6. 필요한 원본이 없으면 알려진 보존 경로만 제한적으로 확인하고 `NOT_RUN: ORIGINAL_ACCEPTED_ARTIFACT_UNAVAILABLE`로 보고한다. 새 실물 수집으로 빈 자료를 채우지 않는다.

집중 시험을 Mac에서 확인할 때는 위 5개 파일을 한 번만 실행한다. 추가 시험은 실제 실패 원인 또는 수정한 경계에만 한정한다. C31/C37/C38/C41/C42 전체 검증과 21종목 감사를 반복하지 않는다.

### D. 예약·운영 pin 보존 확인

아래는 C43 최종 기록인 **2026-11-23 19:42:13 KST** 기준이다. Mac 작업 시작·종료 때 필요한 상태만 한 번씩 읽어 비교한다. 이 문서가 현재 Mac 상태를 새로 조회했다는 뜻은 아니다.

| 대상 | 유지할 상태 |
|---|---|
| US C38 단발 | 2026-11-24 08:10 KST, 기존 `db896306bc4a104241a51aa14caf64c9cf60c85f` pin |
| US C38 사후 확인 | 2026-11-24 12:45 KST, 기존 경로·시각 유지, 위 2개 파일만 보정 |
| KR 정기 | 평일 16:00 KST, 11/24부터, 기존 `2c0bc967280e1c0923fc491363e450e8cd9b332b` pin |
| 구 KR 15:35 | OFF |
| US 정기 | OFF, 활성화 보류 |

새 `KR_unchanged`는 원래 postrun이 보호하던 `kr_config`·`kr_plist` 두 파일의 실행 전후 비교다. 이를 KR16:00 예약 전체 readback을 대신한 것으로 확대하지 않는다.

## 5. 실행 계약 유지

- MARKET 및 적격 B2 종목별 확정 타임아웃 재시도 최대 1회. 기존 같은 입력·새 attempt ID 계약 유지.
- 개별 모델 CLI 600초, 부모 Worker 630초, 전체 캠페인 16,200초 유지. 모델 5단계·VALIDATE·RENDER의 누적 로컬 600초 제한을 되살리지 않는다.
- KR18/US29 기본 슬롯과 결합 후보 KR27/US43의 기존 계획을 유지한다. C38의 운영 cap42를 늘리지 않으며, 새 US43 실물 실행을 하지 않는다.
- 인증 파일 검사는 설정 경로에 존재하는지, 실행 환경에서 읽을 수 있는지 두 가지. 새 token·UID·mode·inode 검사나 재로그인을 추가하지 않는다.
- 최초 오류 영수증, NO-SEND, 기존 lease/Lane 유지. 새 금융·뉴스 HTTP, 모델/CLI, 운영 DB 연결·쓰기, 발송·주문·신규 캠페인 0회.

## 6. 결과 보고

코드 구현은 원격 C44 후보로 완료돼 있다. Mac은 실제 수행한 검증·설치 상태를 다음처럼 보고한다.

1. 받은 C44 SHA와 작업트리 상태.
2. 집중 시험 결과, KR1·US1 원래 세션/평가일과 새 문안, 원본 수락 자료 불변 확인.
3. postrun 설치 여부, 변경한 2개 파일, 스크립트 전후 SHA와 현재 실행 pin 일치.
4. 예약 정의·시각·label·plist 변경 0, 분석 운영 배포·pin 변경 0, 금융·모델·운영 DB·발송·주문 0.
5. KR16:00·구15:35OFF·US08:10/12:45·US정기OFF의 실제 종료 readback.

유지보수 2개 파일을 설치했다면 `운영 변경 0`으로 뭉뚱그리지 말고 **사후 처리 유지보수 2개 파일 반영 / 분석 배포·예약 변경 0**으로 구분한다.

전부 완료하면 `C44_READY_OFFLINE_AND_POSTRUN_MAINTENANCE_APPLIED`, 일부 자료나 설치가 남으면 `C44_PARTIAL_EXACT_REMAINING_ITEM`과 정확한 미완료 항목을 기록한다. 어느 상태도 통합 분석 코드의 운영 배포 또는 새 실물 성공을 뜻하지 않는다.

원래 결과 형식대로 짧은 RESULT, 필요한 diff·시험 결과, KR/US 새 문안, 유지보수 적용 영수증과 마지막 상태 조회를 한 벌로 모은다. 기존 전달 경로는 다음과 같다.

`/Users/sskim/Library/Mobile Documents/com~apple~CloudDocs/Codex Results/TM-PR52-C44-SESSION-ENTRY-POSTRUN-20261123/`

ZIP·SHA-256을 한 번 확인하고 기존 방식으로 iCloud 업로드 상태를 확인한다. 원격 업로드 상태를 확인하지 못하면 복사 완료와 업로드 미확인을 구분한다. 작업이 끝난 뒤 다음 날 실행까지 대기하지 않는다.
