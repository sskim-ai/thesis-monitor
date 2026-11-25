# C57 — 실행 중 저장량 순회 경합 처리

## 기준과 실물 근거

- 저장소: `sskim-ai/thesis-monitor`
- 부모: C56R1 `ba7cd0c51f129f4dd250559d318445c3d54504ce`
- 구현 브랜치: `codex/c57-artifact-scan-race-20261125`
- 설치 대상: 최종 전달된 C57 40자 SHA. 브랜치를 가져온 뒤 해당 SHA와 HEAD를 대조하고 새 clean worktree를 사용한다.
- 코드 검증, Mac 설치, 실제 E2E 성공은 별도 상태다. C56R1 실물은 **FAILED_NO_SEND, 최종 문안 0/9**이며 C57의 실제 문안은 아직 생성되지 않았다.

확인한 `TM_PR52_C56R1_KR_20261125_LIVE_RESULT.zip`의 SHA-256:

```text
f58aca597e1f044bd78610442f31f9570492531506c2a9afb2662baf20b433f0
```

첨부 SHA와 ZIP CRC, 내부 terminal·최초 오류·Source 시간·시험 XML 해시가 일치했다. Mac Python 3.11.15의 C56R1 예약 집중 시험은 15/15 PASS였다. 2026-11-25 18:46 KST에 캠페인 한 번이 시작됐고 Source·ModelPlan·MARKET 및 8종목 CORE까지 수락됐다. 18:58:08 KST, A 첫 묶음 `000660/003690/005490`에서 `FileNotFoundError`로 종료됐다. B·B2·VALIDATE·RENDER는 미도달했다.

실제 스택은 `production_model_transport.communicate_and_measure` → `ResearchArtifactBudget.check` → `measure.visit` → `path.iterdir()`다. 기존 코드는 `lstat()` 시점의 파일 소멸만 처리하고, 디렉터리 열거 시점의 소멸을 처리하지 않는다. 같은 저장량 측정 경로를 한국·미국이 사용하므로 미국에도 같은 취약 지점이 있다. A의 worker 시간은 10.275초였고 이번 최초 오류는 600초 타임아웃이나 저장 상한 초과 오류가 아니다.

사라진 경로와 제거 주체는 원본 영수증에 없다. 따라서 호출별 정리 또는 특정 CLI 내부 작업이 해당 경로를 제거했다고 단정하지 않는다. 정리 5/5 완료와 잔여 runtime namespace 0은 종료 후 결과이며 원인 주체의 증명이 아니다. 실제 피크 저장량도 미기록이다.

## 수정 경계

C57은 등록된 호출별 `runtime-state`의 scratch 안에서 실제 소멸이 확인된 `ENOENT`만 디렉터리 열거·허용된 링크 메타데이터 순회 경합으로 처리한다. 그 외 실패는 중단·재전파하고 저장 분류와 제한된 상대경로 등 필요한 진단을 남긴다. 선언되지 않은 경로, 남아 있는 경로의 접근 오류, 비정상 링크 및 실제 용량 한도를 정상으로 바꾸지 않는다. 최초 `lstat()`에서 존재하지 않는 경로를 건너뛰는 기존 동작은 유지하며, 이미 관측된 선언 root나 보관할 Source/result를 가진 디렉터리가 열거 중 사라지는 경우는 중단한다.

디렉터리 목록을 좁은 예외 처리 안에서 먼저 읽고 자식 순회는 그 밖에서 수행한다. `lstat`·`iterdir`·`readlink`의 중단 오류에는 `RESEARCH_ARTIFACT_SCAN_FAILED`와 연산명·분류·errno·오류 종류·선언 root 기준 상대경로를 기록한다. 상대경로는 최대 256자로 제한해 최악의 Unicode JSON 이스케이프에서도 기존 4096바이트 최초 오류 영수증에 들어가게 한다. 삭제한 프로세스는 추정하거나 새로 기록하지 않는다.

Source·분석·판단·렌더링, 금융·모델 호출 상한, 타임아웃·재시도, NO-SEND, 기존 symlink 검사와 호출별 정리 정책은 유지한다. 절대 경로·인증 내용·원본 금융 응답을 오류 문맥에 추가하지 않는다. 구체적인 변경 내용과 검증 결과는 최종 C57 diff 및 아래 집중 시험 결과를 기준으로 확인한다.

## 집중 검증

기존 C56R1 코드를 그대로 불러온 합성 재현에서, 성공한 `lstat` 직후 실제 임시 디렉터리를 제거하자 `iterdir`의 `FileNotFoundError`를 재현했다. 실제 실패 경로와 제거 주체를 복원했다는 뜻은 아니다.

개발 환경 Python 3.12.14 검증:

- 새 `tests/test_c57_artifact_scan_race.py`: **28/28 PASS**. 소멸 경합, 보호 경로, 권한/I/O 오류, 허용·비정상 링크, hardlink 중복 제거·분류 우선순위·용량 상한, 최초 오류 진단과 Unicode 크기 경계를 확인했다.
- 아래 지정 시험의 최초 실행: **41 PASS / 4 FAIL**, errors/skipped 0. 4건은 `/tmp` 여유 공간 약 4.87 GiB가 기존 12 GiB 가드보다 작은 시험 환경 조건 때문에 검사 목표에 도달하기 전에 중단했다.
- 해당 기존 단위 시험의 가용 공간만 명시적인 합성 값으로 고정하고 **실패한 4건만 재실행해 4/4 PASS**했다. 운영 코드의 free-space 가드는 수정하지 않았고, 0바이트 여유 공간의 가드 거부 시험도 유지했다. 이미 통과한 41건은 반복하지 않았다.
- 고유 지정 시험 **45건 모두 PASS 확인**. Ruff 변경 Python 파일과 `git diff --check` PASS. 이 결과는 Mac 검증 또는 실제 E2E PASS를 뜻하지 않는다.

Mac의 지정 selector는 아래와 같다. 결과 디렉터리는 새로 준비한다.

```bash
/Users/sskim/Codex/thesis-monitor/.venv/bin/python -m pytest -q \
  tests/test_c57_artifact_scan_race.py \
  tests/test_c22av_cli_scratch_links.py \
  tests/test_c22ar_storage_continuation.py::test_capacity_prewrite_peak_and_unknown_symlink \
  tests/test_c51_runtime_retention.py::test_repeated_calls_do_not_accumulate_cache_in_work_budget \
  tests/test_c35_first_failure.py::test_terminal_write_failure_never_masks_primary \
  --junitxml=/Users/sskim/Documents/Codex/2026-07-04/the/maintenance/20261125-pr52-c57/verification/C57_FOCUSED.xml
```

Mac에서는 기존 `/Users/sskim/Codex/thesis-monitor/.venv/bin/python`의 Python 3.11.15를 사용해 위 **45건만 한 번** 실행하고 `C57_FOCUSED.xml`을 보관한다. 기존 C56 16개, C56R1 예약 15개 및 전체 suite를 반복하지 않는다. 시작·종료 HEAD, clean 상태, 실제 Python 버전·exit code·tests/failures/errors/skipped를 기록한다. 시험 실패 시 설치하지 않고 최초 실패 근거를 보존한다. 합성 시험과 별도로 실제 실행 볼륨의 가용 공간을 읽어서 기존 12 GiB 조건을 확인한다.

이번 검증·설치 작업의 실제 금융 HTTP·Source 수집·모델 호출·운영 DB 접근·발송·주문은 **모두 0회**다. 추가 KR 캠페인은 승인되지 않았으며 새 tag, 수동 재실행, kickstart, 재수집·재렌더를 추가하지 않는다.

## 기존 예약에 설치

기존 절차와 경로 확인은 `docs/C56_CODEX_HANDOFF.md`, `docs/C56R1_KR_ONESHOT_HANDOFF.md` 및 Mac의 실제 C56 설치 영수증을 사용한다. 활성 worktree를 checkout하지 않고 검증한 새 C57 worktree로 참조를 바꾼다.

1. 실제 KST 현재 시각, 공유 lease와 lane, 실행 중 worker, 기존 세 작업의 launchd 상태를 읽는다. 잠금이 비고 worker가 없는 시점에서만 설치한다. 미국 예약이 이미 발화·소비됐다면 해당 실행을 중간에 교체하거나 과거 예약을 다시 만들지 말고 관찰된 상태를 보고한다.
2. 기존 한국 정기와 미국 단발 config의 `code_commit`, plist의 실행·config 참조 경로와 `WorkingDirectory`를 새 C57 경로에 맞춘다. Python 실행 파일은 기존 것을 유지한다. config의 private 권한을 유지하고 변경 필드를 비교한다.
3. 미국 사후 확인 helper의 코드 검증 핀과 필요한 참조 경로도 동일 C57로 맞춘다. 기존 미국 실행 tag·대상 세대·run_root를 그대로 읽도록 연결한다. 사후 확인은 `readback_only`이며 새로운 분석 실행을 만들지 않는다.
4. config 로더, plist 문법, launchd의 실제 인수·경로·예약 시각, helper 핀과 대상 세대를 readback한다. `RunAtLoad=false`, `KeepAlive=false`를 유지하고 kickstart하지 않는다. 핀과 경로가 모두 일치한 뒤에만 설치 완료로 보고한다.

| 작업 | 유지할 예약·상태 |
|---|---|
| 한국 정기 `local.thesis-monitor.canonical.kr1600.no-send` | 평일 16:00 KST, 다음 정상 예약부터 C57 |
| 미국 단발 `local.thesis-monitor.us.full.once.c55.20261126` | 2026-11-26 08:10 KST, 미국 2026-11-25 완료장 |
| 미국 사후 확인 `local.thesis-monitor.us.postrun.once.c55.20261126` | 2026-11-26 12:45 KST, 같은 미국 실행 결과 읽기 |
| 미국 정기 `local.thesis-monitor.canonical.us.no-send` | OFF·미등록 유지 |

미국 기존 tag `us-20261126-c55a1b2c`, 시작 창 08:10 이상·08:20 미만, deadline 12:40, 대상 세대와 run_root는 변경하지 않는다. label과 tag의 `c55` 문자는 기존 식별자이며 코드 핀은 C57로 대조한다. C56R1 한국 단발은 이미 제거된 상태를 유지한다.

| 정책 | 한국 | 미국 |
|---|---|---|
| 금융 HTTP 상한 | 334 | 710 |
| 모델 공유 상한 | 27 | 42 |
| Source 제한 | 600초 | 1800초 |
| CLI / 부모 / campaign | 600 / 630 / 16200초 | 600 / 630 / 16200초 |
| 저장 상한·여유공간 | 작업 2 GiB, 결과 96,000,000 B, 여유 12 GiB | 동일 |
| 타임아웃 재시도 | 기존 MARKET/B2 정책 그대로 | 기존 MARKET/B2 정책 그대로 |
| 야간선물 | 기존 KR 설정 그대로 | `OPTIONAL_CURRENT_PROBE`, 최대 7일·요청 20초·HTTP 재시도 0 |
| 발송 | NO-SEND | NO-SEND |

provider별 상한과 나머지 설정은 원본 config의 값 그대로 보존한다. 설치를 이유로 한도·deadline을 늘리거나 새로운 probe를 하지 않는다.

## 보존과 결과 제출

기존 실패를 성공으로 덮어쓰지 않는다. 다음 terminal과 소비 기록·실패 세대를 보존하고 전후 SHA를 대조한다.

- C55 한국 실패 terminal: `49f146c61241d53fe86838dff0b7b76218bf3b1163dcc6e6a9a979338aa91043`
- C56R1 한국 실패 terminal: `bfc60350ac77c022a84f462a282af954e745a3e2fba7fc3f4ce27ff7ded6fee8`
- C56R1 최초 오류: `6fbcd947f989ea2110b326d478d70a44ab4814c3387cc26386f35a07d0f8b82f`

설치 결과에는 집중 시험 XML·실제 결과, 최종 SHA와 worktree 상태, config 변경 필드 비교, 세 예약의 핀·경로·시각 readback, OFF 유지와 실패 기록 보존, 추가 호출 0회를 담는다. 이 단계의 상태는 **C57 검증·설치 완료 / 실제 문안 PENDING**이며 E2E PASS로 보고하지 않는다.

Mac에서 결과 ZIP과 SHA-256을 만들 때는 위 검증 영수증만 담고 원본 금융 전체·DB·환경·인증·모델 임시 상태는 복사하지 않는다. iCloud를 사용할 수 있으면 실제 복사본 SHA와 업로드 완료를 확인한 뒤 보고한다. 아직 확인하지 않은 업로드를 완료로 기입하지 않는다. 다음 실제 결과는 이미 존재하는 정상 예약으로 확인하며 추가 캠페인을 시작하지 않는다.
