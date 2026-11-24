# C51 — 호출별 임시 상태 정리 · 환율 복원 · 지지 회복 판단

## 1. 목표와 이번 승인 범위

사용자는 C50R1 미국 15/15 및 11월 24일 한국 9/9 실제 문안 검토 뒤, 저장 누적을 줄이고 지지 무효화·회복 문안을 고치는 방향에 동의했다. 이번에는 **원/100엔·원/유로 수집 복원까지 코드에 반영하고, Mac 저장 정책 적용과 검증을 코덱스에서 진행**하도록 요청했다.

저장소는 `sskim-ai/thesis-monitor`, 브랜치는 `codex/c51-runtime-retention-fx-20261124`다. 함께 전달된 **40자 C51 커밋**을 사용한다. 기준 부모는 C50 `e7482fad6edc7e2c698359aa5fd17595bf625b48`이다. Mac 로컬 C50R1 `7343a871734d9eb094b2a1f087351e7140df6d9f`의 특정 tag용 4 GiB 예외를 병합하는 작업은 아니다.

이번 Mac 작업은 다음 순서로 수행한다.

1. 지정 커밋의 변경 집중 시험을 한 번 실행한다.
2. C50R1의 원래 기술 판단 자료와 C50·C50R1·최근 한국 실행의 용량을 좁게 확인한다.
3. 종료된 실행의 전용 CLI 임시 상태를 정리하고 실제 회수량을 기록한다.
4. 한국 평일 16:00 작업을 검증된 공통 커밋에 연결하고, 같은 커밋을 미국의 다음 실행 기준으로 준비한다. 미국 정기는 OFF로 둔다.
5. 아래 보관 정책을 기존 Mac 결과 관리에 적용하고, 자동화된 부분과 아직 수동인 부분을 구분해 보고한다.

추가 미국 단발이나 한국 즉시 재실행은 이번 검증에 필요하지 않다. 다음 기존 한국 정기 실행에서 실제 환율과 캐시 정리 결과를 확인한다. 발송·주문·운영 DB 쓰기는 하지 않는다.

## 2. 코드에서 바뀐 것

### 모델 임시 상태

각 호출이 끝나고 worker와 그 전용 process group이 사라진 뒤, 해당 invocation의 `runtime-state/<namespace>/`만 정리한다. prompt·schema·raw output·events·stderr·dispatch/exit/transport 기록·호출 원장은 유지한다. 원래 인증 파일은 그대로이며 임시 state 안의 참조만 제거된다.

정리 실패는 원래 모델 결과나 최초 오류를 덮어쓰지 않는다. 실행 중 살아 있는 프로세스가 있으면 정리하지 않고 상태를 남긴다. `runtime-cleanup.json`은 정리한 논리 바이트·파일 할당 바이트·파일 수를 기록한다.

이는 **실행 중 캐시 누적을 줄이는 자동 기능**이다. 이전 모든 Source를 자동 삭제하는 기능은 아니다. 작업 상한 2 GiB, 결과 상한 96,000,000바이트, 여유 공간 12 GiB는 유지한다. 10–30 MiB/일은 보관량 설계 목표일 뿐, 실측 결과나 새 차단 조건이 아니다.

### 한국 환율

원/달러의 기존 `KeyStatisticList` 조회와 함께 ECOS `StatisticSearch` 두 건을 실행한다.

| 표시 | 통계표 / 항목 | 원본 단위 |
|---|---|---|
| 원/100엔 | `731Y001 / 0000002` | 100엔당 원 |
| 원/유로 | `731Y001 / 0000003` | 1유로당 원 |

조회일 포함 최대 32일, 1페이지·각 1회다. 최신 관측일과 직전 관측일을 원본 응답에서 선택한다. 동일 응답·통화·단위·산술 관계가 맞을 때만 변동액과 변동률을 표시한다. 엔 환율에 100을 다시 곱하지 않는다. 자료가 없으면 미확보를 표시하며 다른 통화로 환산해 채우지 않는다.

한국 ECOS 공급자 한도는 1→3회, 한국 전체 금융 상한은 332→334회다. 미국 ECOS 1회·전체 710회 및 모델 상한은 그대로다. 두 통화를 서로 다른 요청으로 기록하되, 같은 요청의 중복 실행을 허용하지 않는다.

공식 metadata endpoint를 개발 환경에서 열지 못했으므로, 이번 코드는 실물 API의 실제 응답까지 검증한 상태가 아니다. 실제 응답의 통계표·항목 코드·명칭·단위·날짜가 일치해야 표시한다. 다음 기존 한국 실행의 두 응답으로 확인하며 별도 metadata 호출이나 시험 금융 호출을 추가하지 않는다.

HTTP 200의 누락·잘못된 항목·단위는 해당 환율 미확보로 처리한다. 네트워크 실패와 HTTP 오류에 대한 기존 캠페인 중단 정책은 유지한다. provider 단위의 합성 HTTP 실패 시험을 실물 캠페인 전체의 계속 실행 증명으로 표현하지 않는다.

### 판단·문안

- 일봉 선택 지지의 무효화는 기존 일봉 조건으로 판정한다. 이전 주봉 이탈은 별도의 확인 사항이다.
- 주봉 선택 지지는 완료 주봉 기준을 사용한다. 이후 주의 완료 일봉이 무효화선/지지 하단을 회복하면 회복 재확인으로 표시하고 다음 완료 주봉을 기다린다.
- 일봉 회복만으로 BUY 또는 신규매수 가능으로 승격하지 않는다. 원래 사업·가치평가 WAIT 사유와 구조 재검토 사유를 함께 보존한다.
- 신호 주기·기준봉 날짜·평가 일봉 날짜·회복 상태를 입력부터 문안까지 전달한다. 월봉 무효화는 기존 미정의 제한을 유지한다.
- 동일 발행사로 이미 수락된 본주의 실적 비교는 한국어로 표시한다. SKHY만의 예외가 아니며 다른 증권의 EPS·PER·적정가로 확대하지 않는다.

## 3. 작업트리와 최소 오프라인 검증

기존 Mac Python 3.11 환경을 사용한다. 패키지 재설치, 인증 토큰 검사, 시험 로그인, 파일별 코드 SHA 승인 목록을 추가하지 않는다. 인증 파일 사전 확인은 설정 경로의 존재·읽기 가능 여부뿐이다.

`C51_REPO`, `C51_WORKTREE`, `C51_RESULT_DIR`, `C51_COMMIT`, `C51_PY`를 실제 환경에서 정한다. `C51_PY`는 기존 `/Users/sskim/Codex/thesis-monitor/.venv/bin/python`이다. 한국·미국용으로 같은 코드 복사본 두 개를 새로 만들지 않고 공통 C51 worktree 하나를 사용한다. 기존 운영 작업트리를 checkout하거나 수정하지 않는다.

```bash
git -C "$C51_REPO" fetch origin codex/c51-runtime-retention-fx-20261124
git -C "$C51_REPO" merge-base --is-ancestor "$C51_COMMIT" origin/codex/c51-runtime-retention-fx-20261124
git -C "$C51_REPO" worktree add --detach "$C51_WORKTREE" "$C51_COMMIT"
git -C "$C51_WORKTREE" rev-parse HEAD
git -C "$C51_WORKTREE" status --short
git -C "$C51_WORKTREE" diff --check "$C51_COMMIT^" "$C51_COMMIT"
```

다음 명령의 작업 디렉터리는 C51 worktree다. 네 파일의 **47개 사례만 한 번** 실행한다(무효화 20, 발행사 문안 2, 환율 12, 임시 상태 13).

```bash
"$C51_PY" -m pytest -q \
  tests/test_c51_invalidation.py \
  tests/test_c51_issuer_presentation.py \
  tests/test_c51_kr_fx.py \
  tests/test_c51_runtime_retention.py \
  --junitxml="$C51_RESULT_DIR/C51_FOCUSED.xml"
```

금융·실제 모델·운영 DB를 사용하지 않는다. 프로세스 종료 시험은 작은 임시 Python subprocess를 사용하며 실제 Codex CLI를 호출하지 않는다. 시작·종료 HEAD, Python 버전, 시험 집계와 exit code만 기록한다. 전체 pytest, C49 81개, C50 19개, 실물 재생은 반복하지 않는다. 실패하면 그 오류와 관련 변경 경계만 제출하고 해당 운영 반영을 보류한다.

개발 단계의 결과는 부분별 실행과 실패 경계 재확인을 합친 것이다. 최종 전체 묶음을 한 번 실행한 기록으로 바꾸어 보고하지 않는다. 개발 호스트의 12 GiB 미만 여유 공간 때문에 일부 기존 저장 시험이 실패했으며, 시험용 파일시스템 여유를 지정해 해당 사례만 재확인했다. 운영 여유 공간 기준은 낮추지 않았다.

## 4. C50R1 원래 무효화 근거를 한 번 읽기

현재 제출 ZIP에는 원래 무효화 임계값·주기별 이탈 플래그가 빠져 있다. C50R1 `SCHEDULE.json`의 `run_root`와 실제 consumer terminal에서 원래 consumer 경로를 확인한다. 최신 코드로 보존 입력의 값을 읽되 새 Source 수락·모델 재수락·전체 문안 재생은 하지 않는다.

```bash
"$C51_PY" -m scripts.c49_inspect_saved_inputs \
  --cycle "$C50R1_CONSUMER" \
  --output "$C51_RESULT_DIR/C50R1_ORIGINAL_TECHNICAL_INPUTS.json"
```

이 도구는 기존 진단에 `original_chart_structure`와 무효화·상태·위험보상 fact를 추가했다. **GOOGL, MU, TSM, CPNG, TSLA**에 대해 원래 선택 지지 주기·구간, 무효화선, 일봉/주봉 이탈 플래그, 원래 상태, 평가 일봉/완료 주봉의 기준일·종가를 작은 표로 정리한다. 새 계산이 필요하면 원래 값과 분리한 순수 계산 비교만 허용한다. 당시 문안과 판단은 그대로 남긴다. 이 진단 때문에 C50R1 실물 성공을 실패로 재명명하지 않는다.

## 5. 실제 저장량 확인과 종료된 임시 상태 정리

대상은 **C50 최초 실패, C50R1 성공, 11월 24일 한국 정기**의 정확한 세 generation이다. 미국 경로는 각각 기존 유지보수 `SCHEDULE.json`의 `run_root`에서, 한국은 현재 등록 config와 `kr-2026-11-24/terminal.json`에서 찾는다. 모델 runtime은 각 generation의 `model-runtime-preflight.json`에서 읽는다. 홈 전체·디스크 전체·iCloud 전체를 다시 조사하지 않는다.

각 generation에 대해 다음을 한 번 실행한다. 결과 파일명은 서로 다르게 지정한다.

```bash
"$C51_PY" -m scripts.c51_storage_inventory \
  --generation "$EXACT_GENERATION" \
  --output "$C51_RESULT_DIR/STORAGE_BEFORE_<RUN>.json"
```

논리 바이트와 `st_blocks` 파일 할당 바이트를 구분한다. APFS의 공유 extent나 삭제 후 실제 가용 공간은 이 값만으로 단정하지 않는다. 이 도구는 원래 프로세스의 모든 동적 예산 분류를 복원하지 않으며 보고서의 `accounting_kind`와 실제 폴더별 집계를 따른다. 용량의 주원인이 어떤 디렉터리인지 확인하는 용도다.

세 실행의 terminal·관련 프로세스 종료·공유 lease 해제를 한 번 확인한다. C50R1 기술 근거 읽기가 끝난 뒤, inventory의 **안전한 `runtime_state_candidates[].disposable_state` 경로만** 정리한다. 과거 C50 기록에는 worker PID가 없으므로 새 cleanup 함수에 임의 PID를 넣어 통과시키지 않는다. Mac에서 실제 종료를 확인한 운영자가 정확한 경로 목록으로 정리한다. 중간 경로가 symlink인 제외 후보는 건드리지 않는다.

정리 범위는 `runtime-state/<namespace>`다. 같은 invocation의 prompt/output/events/receipt, 원래 Source·결과, 인증 원본, 사용자 Codex 홈, 운영 DB, Git worktree는 이 정리에 포함하지 않는다. 내부 auth symlink는 링크만 제거하고 대상을 따라가지 않는다. 각 실행별 제거 경로·파일 수·논리/할당 바이트·디스크 가용 공간 전후를 기록한다. 측정과 실제 삭제 결과가 없으면 회수 완료라고 쓰지 않는다.

정리 후 같은 도구를 한 번 실행하여 `STORAGE_AFTER_<RUN>.json`으로 저장한다. 이는 삭제 전후 확인이며 전체 분석 검증을 다시 하는 작업이 아니다. C50의 최초 오류·C50R1 15개·한국 9개 원문은 보존한다.

## 6. 장기 보관 정책의 Mac 적용

| 자료 | 보관 원칙 |
|---|---|
| 실제 최종 문안·판단/가격/행동 비교·실행 및 호출 요약 | 실행별 축약 기록으로 장기 보관 |
| 시장별 최신 정상 Source·수락 결과·호출 근거 | 각 시장 최신 정상 실행 1개 유지. 다음 정상 실행과 축약 기록이 완성된 뒤 교체 |
| 실패 실행 | 최초 오류, 실제 시도·타임아웃 기록, 관련 입력·원문 및 열린 진단에 필요한 최소 자료 보관 |
| 전용 CLI cache·세션 DB·tmp | 실행 종료 뒤 정리. C51 이후 호출별 자동 기능 적용 |
| 코드 | Git 커밋으로 보관. 공통 실행 worktree와 필요한 rollback만 유지 |

기존 결과 관리 경로에 최신 정상 참조와 일별 축약 기록을 저장한다. 축약 기록은 시장·거래일·실행 ID·커밋·원래 terminal 상태·실제 문안·B/B2 및 최종 행동·핵심 가격/지지·최초 오류·호출 수를 연결해야 한다. 미생성을 WAIT로 바꾸지 않는다.

**작은 결과 ZIP은 전체 Source의 백업이 아니다.** 오래된 전체 원본을 정리할 때는 최신 정상 원본, 현재 예약/실행 참조, 열린 진단에 필요한 원본을 먼저 제외한다. 최신 실패가 기존 최신 정상 원본을 교체해서도 안 된다. 같은 거래일의 재실행 방지용 intent·terminal·호출 원장을 삭제해 소비된 실행을 다시 가능하게 만들지 않는다.

`scripts/verified_report_gc.py`는 자체 manifest와 완전히 일치하는 펼친 보고서만 정리하는 기존 도구다. 원본 입력 전체 삭제에 억지로 적용하지 않는다. 이번 C51 코드에는 **자동 Source 회전 기능이 없다**. 기존 Mac postrun 관리에 이 보관 정책을 적용할 수 있으면 정확한 대상과 적용 범위를 기록하여 수행한다. 자동화에 저장소 코드 변경이 필요하면 운영 worktree에 임시 별도 로직을 만들지 말고, 필요한 연결 지점·현재 경로·남은 용량만 제출한다. 호출별 캐시 자동 정리와 확인된 기존 임시 상태 정리는 이와 별개로 완료한다.

## 7. 한국 공통 코드 적용 및 다음 정기 결과 확인

집중 시험 통과와 현재 실행 없음/공유 lease 해제를 확인한 뒤, 기존 한국 평일 16:00 config와 plist의 코드 경로·`code_commit`을 공통 C51 worktree/커밋으로 맞춘다. 기존 운영 config·plist의 작은 rollback 사본을 남긴다. 소스 설정·모델 binding·재시도 플래그는 기존 실제 값을 유지한다.

현재 `endpoint_rules`가 아래 경로를 이미 허용하면 그대로 사용한다. 그렇지 않으면 기존 규칙을 보존한 C51용 복사본의 `ecos` 배열에 다음 항목 하나를 추가한다.

```json
{
  "methods": ["GET"],
  "host": "ecos.bok.or.kr",
  "prefix": "/api/StatisticSearch/",
  "endpoint": "ECOS_STATISTICSEARCH",
  "path_contains_credentials": true
}
```

새 한국 config의 `endpoint_rules.path`와 기존 `sha256` 필드를 복사본의 실제 바이트에 맞춘다. 이 설정 참조 갱신은 파일별 코드 SHA 승인 목록을 새로 만드는 일이 아니다. 공유 미국 설정 파일이나 기존 `KeyStatisticList` 규칙은 수정하지 않는다. 자격증명이나 토큰 내용은 출력하지 않는다.

검증은 기존 `read_local_configuration()`, `config.endpoint_rules.read()` 후 JSON 파싱과 ECOS 새 경로 확인, `plutil -lint`로 충분하다. 변경 중 예정 시각이 겹치면 실행이 끝난 뒤 적용한다. plist를 수정한 뒤 **같은 기존 한국 label을 bootout/bootstrap**하여 로드된 작업을 갱신하고 `WorkingDirectory`·`ProgramArguments`·calendar를 한 번 readback한다. `RunAtLoad=False`, `KeepAlive=False`, 기존 평일 **16:00 KST**를 보존한다. `kickstart`나 즉시 분석을 하지 않는다. 미국 정기·구 한국 15:35·C38 12:45는 OFF를 유지한다. 미국은 다음 승인된 실행이 같은 공통 커밋을 사용하도록 준비만 한다.

다음 기존 한국 정기에서는 원래 consumer terminal의 시장 1개+종목 8개와 아래 항목만 확인한다.

- 원/달러·원/100엔·원/유로 실제 응답, 관측일, 단위, 비교 관측일과 최종 표시. 미확보가 있으면 실제 사유.
- 각 실제 모델 호출의 `runtime-cleanup.json` 상태와 회수량. 살아 있는 프로세스/정리 오류로 남은 항목은 사실대로 기록.
- 최종 retained bytes와 실행 중 peak를 분리. 원래 첫 오류·수락본·문안 보존.
- WAIT 사유, 가격 위치, 주기별 무효화/회복 표시. 자동 BUY가 생기지 않는지 실제 사례만 확인.

당장 다음 16:00까지 기다릴 수 없는 세션이라면 검증·설치 결과를 먼저 제출하고, 실제 실행 결과는 기존 postrun 경로에서 후속 제출한다. 실물 확인을 했다고 미리 쓰지 않는다.

## 8. 최소 결과 제출

`RESULT.md`, `C51_FOCUSED.xml`, 원래 기술 판단 요약, 저장량 전후·정리 결과, config/등록 readback을 한 결과 ZIP과 SHA-256 사이드카로 제출한다. 실제 Source·캐시·세션 DB를 결과 ZIP에 다시 넣지 않는다. 실제 한국 후속 문안은 생성된 경우에만 포함한다.

상태를 분리해서 적는다: `C51_MAC_OFFLINE_PASS`, `C51_CACHE_CLEANUP_COMPLETE/PARTIAL`, `C51_KR1600_COMMON_COMMIT_INSTALLED`, `C51_NEXT_REGULAR_ACTUAL_PENDING/COMPLETE`. 장기 Source 보존이 수동/자동 중 어느 수준인지도 적는다. 금융·실제 모델 호출 수는 오프라인 검증·기존 정기 실행을 구분한다. 반복 전수 검증·추가 인증 절차·추가 단발은 넣지 않는다.

결과 ZIP 목적지 바이트는 한 번 비교하고 iCloud 업로드 완료는 실제 완료를 관찰한 경우에만 보고한다.
