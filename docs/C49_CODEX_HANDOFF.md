# C49 — 부분 문안 · 진입 후보 · SKHY 본주 재무 연결 검증

## 이번 작업의 목적

ChatGPT가 수정한 C49 지정 커밋을 Mac의 기존 환경에서 한 번 검증하고, **C48 보존 입력에서 진입 후보 탈락 사유와 SKHY 재무 사용 범위**를 확인한다. 결과를 한 묶음으로 제출한다. 이번 작업은 오프라인 검증과 기존 입력의 읽기 전용 진단이다.

C48의 실제 결과는 금융 HTTP 417회, 모델 30/42회·28개 수락, 최종 문안 0/15였다. SKHY는 `UNKNOWN_LIMIT`, 일반 종목 12개의 B2는 수락, TSM은 최초 호출과 재시도가 각각 타임아웃됐다. C48 `VALIDATE`는 제한 종목과 타임아웃 누락이 공존하는 결과를 거절했다. **그 원래 실행 결과를 C49 성공으로 바꾸거나 과거 B/B2 수락을 재발급하지 않는다.**

이번 코드의 변경은 다음 세 가지다.

| 변경 | 확인할 동작 |
|---|---|
| 혼합 부분 결과 | SKHY 제한 + TSM 확정 타임아웃 2회가 공존해도 시장 1개·정상 종목 12개·SKHY 제한 문안 1개를 보존한다. 14/15 부분 완료이며 TSM 판단은 미생성이다. |
| 진입 후보 기준 통일 | B 선택 목록, B2 가격 위치, 렌더러가 동일한 완료봉·가격 기준 함수를 사용한다. 제외 후보의 이유를 보존하고, 참고 가격을 매수 구간으로 승격하지 않는다. |
| 본주 회사 재무 활용 | 기존 동일 발행사 연결과 원재무 품질 검사를 통과한 현재 비교자료를 회사 실적·Core·종합 방향·A 판단에 연결한다. 주식별 가격·EPS·PER·적정가로 이전하지 않는다. |

SKHY가 일반 B2 대상으로 편입되면 기본 모델 계획은 29회에서 **30회**가 된다. C49는 미국의 기존 `B2_PER_TICKER_ONE_RETRY_V1`, `timeout_retry_cap=0` 경로에서 승인 상한 **42회**를 유지하고, 기본 30회를 예약한 뒤 남은 **12회를 MARKET·종목 B2 재시도가 공유**하도록 했다. 시장과 각 B2의 재시도는 각각 최대 1회다. 모든 대상의 재시도를 동시에 보장하는 예산은 아니다. 한국·진단 전용·명시적 combined 정책의 기존 예산 조건은 유지한다.

## 1. 지정 커밋과 기존 Python 사용

- 저장소: `sskim-ai/thesis-monitor`
- 브랜치: `codex/c49-partial-entry-issuer-20261124`
- `C49_COMMIT`: 이 문서와 함께 전달한 최종 **40자 SHA**. 문서가 들어 있는 자기 커밋 SHA를 문서 안에 중복 고정하지 않는다.
- Python: 기존 `/Users/sskim/Codex/thesis-monitor/.venv/bin/python`. 환경·패키지 재설치 없이 사용한다.
- 기존 개발 저장소에서 별도 worktree를 사용한다. `C49_REPO`, `C49_WORKTREE`, `C49_RESULT_DIR`는 실제 Mac 경로로 정한다. 결과는 새 유지보수 디렉터리에 둔다.

```bash
git -C "$C49_REPO" fetch origin codex/c49-partial-entry-issuer-20261124
git -C "$C49_REPO" merge-base --is-ancestor "$C49_COMMIT" origin/codex/c49-partial-entry-issuer-20261124
git -C "$C49_REPO" worktree add --detach "$C49_WORKTREE" "$C49_COMMIT"
git -C "$C49_WORKTREE" rev-parse HEAD
git -C "$C49_WORKTREE" status --short
```

이후 명령의 작업 디렉터리는 `C49_WORKTREE`다. 시험 시작·종료 HEAD와 worktree 상태, exit code를 기록한다. 변경분의 whitespace 확인은 `git diff --check "$C49_COMMIT^" "$C49_COMMIT"` 한 번으로 충분하다. 별도 파일별 코드 SHA 승인 목록을 만들지 않는다.

## 2. 집중 시험 한 번

개발 환경 Python 3.12.14에서는 진입 81개, 본주 재무 57개, 부분 결과·예산 10개의 **고유 148개 사례에 대해 최종 PASS 근거**를 확인했다. 처음 실패한 진단 우선순위·합성 fixture·Worker 예산 경계를 보완한 뒤 해당 사례만 재검증했고, 본주 재무 시험의 기대도 기존 매출·영업이익 비교 범위로 바로잡았다. 최종 코드에서 148개 전체를 다시 실행한 결과라고 표현하지 않는다. 이는 합성 자료를 실제 코드 경로에 넣은 검증이며 C48 실물 재수락·새 문안 생성이 아니다.

`C49_PY`를 위 기존 Python 경로로, `C49_XML`을 새 결과 디렉터리의 `C49_FOCUSED.xml` 절대 경로로 설정한다. 아래 목록은 **진입 48개 + 부분 결과·예산 10개 + 본주 재무 23개 = 81개**다. C44/C45 전체 시험, 전체 pytest, 보존 실물 전체 재생은 추가하지 않는다.

```bash
"$C49_PY" -m pytest -q \
  tests/test_c49_entry_candidate_basis.py \
  tests/test_c45_entry_basis.py \
  tests/test_c45_entry_presentation.py \
  tests/test_newbuyer_b2_shadow.py::test_frozen_adapter_request_no_mutation_and_real_controller_entry \
  tests/test_newbuyer_b2_shadow.py::test_timing_adapter_uses_exact_owned_price_zone_chain \
  tests/test_v8_mixed_retry.py::test_mixed_retry_exhaustion_preserves_verified_partial_messages \
  tests/test_v8_mixed_retry.py::test_nonmixed_partial_partition_and_old_STOP_remain_closed \
  tests/test_per_ticker_b2_kis_session.py::test_second_timeout_preserves_mixed_contract_and_no_third_attempt \
  tests/test_per_ticker_b2_kis_session.py::test_nonconfirmed_or_auth_failure_stops_without_retry \
  tests/test_c49_us_retry_budget.py \
  tests/test_c41_combined_retry.py::test_insufficient_kr18_19_26_and_us42_fail_before_worker \
  tests/test_c41_combined_retry.py::test_caller_rejects_insufficient_caps_before_source_db_or_runtime \
  tests/test_post_r22_ng09_business_bridge.py \
  tests/test_post_r22_ng16_skhy_history.py::test_current_consumer_synthetic_comparison_scope_and_valuation_denial \
  tests/test_post_r22_ng17_skhy_owner.py::test_synthetic_original_selected_fresh_projection_authority_chain_retains_scope \
  --junitxml="$C49_XML"
```

시험은 합성 자료·mock으로 실제 후보 구성·재시도·검증·렌더러 경로를 확인한다. 금융 HTTP·실제 모델 CLI·운영 DB는 호출하지 않는다. pytest 임시 디렉터리는 기본값을 사용하고, 모델 실행용 디렉터리를 Git 작업트리 안에 지정하지 않는다.

재시도 합성 fixture의 가용 디스크 메타데이터는 시험용 값이다. **운영 디스크 12GiB 검사를 완화한 변경이나 실환경 용량 PASS가 아니다.** 합성 모델의 타임아웃도 실제 모델을 600초씩 기다려 발생시키지 않는다.

다음 결과를 구분해 적는다.

- 혼합 제한·타임아웃: `RENDER_VERIFIED_PARTIAL_NO_SEND`, 실제 문안 14개, 예상 15개, TSM `unissued`의 원래 요청·시도 2회 보존.
- 일반 미국 14종목: 기본 30개 수락, MARKET 재시도 1회·B2 재시도 11회, 총 42회 합성 호출, 문안 15개.
- 공유 재시도 12회 소진 후 다음 종목의 첫 타임아웃: 원래 오류 유지. 가짜 두 번째 타임아웃이나 `unissued`를 만들지 않음.
- 완료 D/W/M 지지 후보: B 선택부터 B2·문안까지 동일 기준. 적격 후보가 없으면 구체적 부족 사유를 표시.
- 본주 재무: 현재 적격 비교가 `EVIDENCE_BASED`와 Core·A·B 준비 입력에 도달. 과거 연결·품질 거절·주식별 밸류에이션 제한은 그대로 유지.

실패하면 첫 실패와 해당 입력 경계를 남긴다. Mac 현장에서 지정 커밋을 고치거나 같은 전체 목록을 반복 실행하지 않는다. 아래의 읽기 전용 C48 진단은 가능한 범위까지 계속 수행해 함께 제출한다.

## 3. C48 원본 입력 한 번 진단

C48 결과 ZIP에는 요약과 비교표가 있지만 전체 B context와 SKHY 원재무 사용 기록은 들어 있지 않았다. Mac에 보존된 원래 consumer 실행 디렉터리를 읽는다. C48 `SCHEDULE.json`·`EXECUTION.json`과 실제 파일 위치를 사용하며, 아래 경로는 C48 결과에 기록된 출발점이다.

```text
/Users/sskim/Documents/Codex/2026-07-04/the/work/thesis-monitor-pr52-local-launchd-20261119/data/local-launchd/runs/c48-us-20261124-full/one-shot/2026-11-24/us-20261124-c48a1b2c/results/unified-snapshot-runs/local-us-2026-11-23-once-us-20261124-c48a1b2c-consumer
```

`C48_CYCLE`에 실제 원래 디렉터리를 설정한다. **C49 코드로 다음 읽기 전용 스크립트만 실행**한다.

```bash
"$C49_PY" -m scripts.c49_inspect_saved_inputs \
  --cycle "$C48_CYCLE" \
  --output "$C49_RESULT_DIR/C48_ENTRY_ISSUER_INPUTS.json"
```

스크립트는 기존 B2 snapshot 참조와 B context를 읽고, 원래 B2 요청의 context 연결을 확인한다. 동일 입력에 C49의 순수 후보 판정 함수를 적용해 진단 목록을 만든다. **Source 수락·모델 수락·문안 재생·Owner 발급·금융 수집을 수행하지 않는다.** 출력은 원래 cycle 밖의 새 파일에만 저장한다.

원래 B context, B2 요청, 필요한 snapshot이 정리되어 없으면 실제 누락 경로를 기록한다. 새 자료로 과거 입력을 보충하거나 현재 날짜를 붙여 재수락하지 않는다. `original_accepted_file_present`는 파일 존재 사실이며 수락 검증 PASS를 뜻하지 않는다. 입력 연결이 다르면 그 상태를 그대로 보고한다.

### 진입 후보 비교

`C48_DIAGNOSIS.md`에 아래 열을 정리한다. C48 원래 B2 판단은 기존 수락 결과 또는 원래 `B2_QA.json`에서 인용하고, 현재 코드로 계산한 후보 자격과 구분한다.

| 종목 | C48 B2 판단·타이밍 | 원래 선택 후보·출처 | 후보 탈락 사유 | 같은 입력의 다른 적격 후보 | 아직 부족한 원자료 |
|---|---|---|---|---|---|

확인할 핵심은 다음과 같다.

- C48의 `UNRESOLVED` 11개가 저장된 가격 규칙, 봉 기간 부재, 완료 거래일, 가격 조정 기준, 통화, 일봉 종가 연결, 기존 ENTRY 범위 중 무엇 때문에 발생했는지 실제 입력으로 분류한다.
- 적격 대안 후보가 있으면 ID를 적는다. 그것을 C48에서 새로 선택된 후보나 새 B2 결과라고 표시하지 않는다.
- `chart_price_rules`와 완료봉 연결이 없는 `chart_price_structure_v3_zone`은 참고자료로 남는다. V3 지지의 기간·조정 기준을 추정해서 채우지 않는다.
- SNDK의 기준가격 87.17과 기존 선택 구간 1100–1125의 차이는 원자료가 설명하는 범위만 적는다. 분할·다른 종목·환산 문제라고 추측해서 확정하지 않는다.
- CPNG의 원래 가격 위치가 계산됐어도 기업 위험에 따른 `AVOID` 판단이 매수로 바뀌는 것은 아니다. TSM은 B2 미생성으로 유지한다.

### SKHY 본주 연결

같은 문서에 `issuer_subjects.SKHY`를 근거로 다음을 적는다.

1. C48에서 실제 선택된 재무 출처와 `000660` 동일 발행사 연결, 현재/비교 기간, selected fact 목록.
2. 원래 comparison fact의 allowed/prohibited use와 품질 상태. 당시 `CONTEXT`에만 머문 근거가 무엇인지 확인.
3. C49가 바꾼 회사 실적 사용 범위와 실제 보존 입력의 부족 사항을 구분. 과거 판단을 복사하거나 `SKHY`라는 티커만으로 정상 모드를 강제하지 않음.
4. 본주 회사 재무와 SKHY의 가격·EPS·PER·적정가 제한을 분리. 회사 분석 가능과 지금 매수 가능은 다른 결과다.

이 진단은 **C48 당시 미해결 원인의 확인**이다. SKHY가 새 실물 캠페인에서 일반 B2로 성공했다거나, 기존 11종목의 실제 문안이 해결됐다는 보고로 바꾸지 않는다.

## 4. 이번 작업에서 유지할 운영 상태

C48 종료 보고 기준 **C38 12:45 사후 확인 OFF, 한국 평일 16:00 ON, 미국 정기 OFF, 구 한국 15:35 OFF**다. C48 이전 지시서의 C38 ON 보존 안내를 이번 작업에 다시 적용하지 않는다. 이번 작업에는 예약 등록·변경, 운영 핀·설치 변경, 신규 실물 캠페인이 없다.

오프라인 시험과 파일 진단에는 인증 파일·토큰·로그인이 필요하지 않다. 인증 내용 검사, 시험 로그인, 새 보안 점검·독립 승인·GC를 추가하지 않는다. 향후 실물 작업에서 인증 파일 사전 확인이 필요하면 기존 요구대로 존재·읽기 가능 두 가지뿐이다.

기존 실행 한도는 개별 CLI 600초, 부모 Worker 630초, 전체 캠페인 16200초, 실제 모델 최대 42회다. 모델 단계·VALIDATE·RENDER의 누적 로컬 600초 제한을 다시 만들지 않는다. 최초 오류 기록과 NO-SEND를 유지한다.

## 5. 한 묶음으로 제출

다음만 새 결과 디렉터리에 모으면 된다.

- `RESULT.md`: 지정 SHA, Python, 시험 시작·종료 HEAD, PASS/FAIL/ERROR/SKIP, 소요 시간, 원본 진단의 완료/미완료 범위.
- `C49_FOCUSED.xml`.
- `C48_ENTRY_ISSUER_INPUTS.json`, `C48_DIAGNOSIS.md`.
- 위 파일의 결과 ZIP과 SHA-256 사이드카. 기존 Codex Results 방식으로 전달한다.

시험 PASS와 보존 입력 진단 완료는 별도로 보고한다. 둘 다 끝났으면 `C49_MAC_OFFLINE_PASS / C48_INPUT_DIAGNOSIS_COMPLETE`, 원본 부족이 있으면 `C49_MAC_OFFLINE_PASS / C48_INPUT_DIAGNOSIS_INCOMPLETE`처럼 구분한다. 새 실물 문안 수는 0이며 합성 렌더링 수와 섞지 않는다.

금융 HTTP·실제 모델 CLI·운영 DB 접근·발송·주문·운영 설치·핀·예약 변경의 이번 실제 횟수를 함께 기록한다. 목적지 ZIP·사이드카 바이트 비교는 한 번, iCloud 업로드는 실제 완료를 관찰한 경우에만 완료로 보고한다. 별도 중복 감사 패키지는 필요 없다.
