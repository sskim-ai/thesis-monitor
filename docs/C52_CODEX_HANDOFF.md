# C52 — 야간선물 복구 후 11월 25일 미국 08:10 단발

## 1. 목표와 승인된 작업

사용자는 야간선물의 세 경계를 먼저 수정한 뒤 다음 아침 미국 단발을 예약하도록 요청했다. 이번 작업은 **C52 지정 커밋의 Mac 오프라인 확인 → 2026-11-25 08:10 KST 미국 실물 NO-SEND 단발 등록 → 원래 실행 결과 수집**이다. 별도 재승인 없이 이 범위를 완료한다.

저장소는 `sskim-ai/thesis-monitor`, 브랜치는 `codex/c52-optional-night-us0810-20261125`다. 채팅에서 전달한 **40자 C52 커밋**을 사용한다. 부모는 C51 `48e288a9cb82e8e034360ac7ecd858f4aa438151`이다. C51의 저장 정리·환율·지지 회복 변경을 포함한다. C50R1의 특정 실행에만 적용했던 4 GiB 예외는 포함하지 않는다.

코드 반영과 Mac 환경 적용을 구분한다. 이 문서 자체는 launchd 등록 완료 영수증이 아니다. 실제 등록 readback과 실제 문안은 Mac에서 관측한 결과만 보고한다.

## 2. 세 경계에서 바뀐 동작

### A. 원래 응답으로 오류를 진단하고 위치를 남긴다

`scripts/c52_inspect_saved_night.py`가 C46의 원래 동결 계획·응답·요청 영수증을 읽고 현재 parser와 materializer를 오프라인으로 실행한다. 추가 요청이 필요하지만 저장 응답이 없으면 `INCOMPLETE_SAVED_CAPTURE / RECORDED_PREFIX_EXHAUSTED`로 끝낸다. 빈 응답을 만들어 채우거나 재수집하지 않는다. 임시 계산 이력은 임시 디렉터리에만 쓰고 제거한다.

현재 acquisition의 실패 기록에는 오류 종류와 코드 파일·함수·행이 남는다. 원래 예외 문자열이나 인증값은 결과에 넣지 않는다. **현재 코드 재생 결과와 C46의 당시 원인 확정은 별개다.** C46 당시 내부 예외가 충분히 기록되지 않았으므로, 현재 재생 성공을 과거 원인 확인으로 보고하지 않는다.

### B. 일별 종가·등락과 주·월봉 이력을 분리한다

완료 야간 종가와 같은 계약의 직전 정규장 종가가 검증되면 일별 가격·차이·등락률을 표시한다. OHLC 이력이 없으면 OHLC를 만들지 않고 종가 비교만 표시한다. 주·월봉 구성 자료가 없으면 각각 `자료 부족 (동일 만기 이력 미확보)`로 표시한다. 주·월봉 부족 때문에 유효한 일별 비교를 폐기하지 않는다.

완료 시각·거래일·계약·원본·산술 검증은 유지한다. 오래된 값, 미완료 값, 잘못된 프레임을 일별 신호로 승격하지 않는다. 이번 상품 범위는 기존 **KOSPI200**이다.

### C. 선택 야간선물 오류가 미국 전체 분석을 막지 않게 한다

새 실행 설정은 `us_night_policy="OPTIONAL_CURRENT_PROBE"`다. 실제 조회를 시도하므로 C47–C51의 사전 제외 설정과 다르다. 기존 `ORIGINAL_CURRENT_PROBE_ONLY`도 이번 설정으로 사용하지 않는다.

- 최대 7개 날짜의 원래 조회 계획을 사용한다. 요청당 20초, HTTP 재시도 0회다.
- HTTP 오류 중 401·403을 제외한 오류, 전송 오류, 해당 요청 자체의 타임아웃은 원래 실패 기록을 남기고 야간 조회를 종료한다.
- HTTP 200의 잘못된 JSON·빈 본문 및 야간 자료 처리 오류도 값 없는 미확보 결과로 연결한다.
- 다른 미국 필수 자료가 충족되면 Source와 모델 단계가 진행할 수 있다. 야간선물 미확보일 때 가격·등락·방향 사실은 생성하지 않고 최종 문안에 수집 오류/자료 처리 오류를 표시한다.
- 인증 오류, 전역 STOP, 외부 취소, 호출 상한, 로컬 저장 오류는 기존 중단을 유지한다. 야간선물 선택 처리로 저장 한도를 우회하지 않는다.

원래 요청 원장·실제 응답·실패 영수증을 사용한다. 별도 증거 사용권이나 파일별 코드 SHA 승인 목록을 추가하지 않는다.

## 3. 작업트리와 최소 오프라인 확인

기존 Mac Python `/Users/sskim/Codex/thesis-monitor/.venv/bin/python`을 사용한다. C51에서 확인한 Python 3.11.15 환경을 다시 설치하지 않는다. `C52_REPO`, `C52_WORKTREE`, `C52_RESULT_DIR`, `C52_COMMIT`, `C52_PY`를 실제 경로로 설정한다. 새 C52 worktree 하나를 사용하고 실행 중이거나 예약이 참조하는 기존 작업트리를 checkout하지 않는다.

```bash
git -C "$C52_REPO" fetch origin codex/c52-optional-night-us0810-20261125
git -C "$C52_REPO" merge-base --is-ancestor "$C52_COMMIT" origin/codex/c52-optional-night-us0810-20261125
git -C "$C52_REPO" worktree add --detach "$C52_WORKTREE" "$C52_COMMIT"
git -C "$C52_WORKTREE" rev-parse HEAD
git -C "$C52_WORKTREE" status --short
git -C "$C52_WORKTREE" diff --check "$C52_COMMIT^" "$C52_COMMIT"
```

C52 worktree에서 아래 **48개 사례를 한 번** 실행한다. 일별/주월 분리 15개, 실제 요청·원장 경계 15개, Source·최종 표시·등록 연결 13개, 저장 응답 진단 5개다.

```bash
"$C52_PY" -m pytest -q \
  tests/test_c52_night_daily.py \
  tests/test_c52_night_runtime.py \
  tests/test_c52_optional_night_source.py \
  tests/test_c52_saved_night.py \
  --junitxml="$C52_RESULT_DIR/C52_FOCUSED.xml"
```

이 시험은 합성 등록/입력, mock HTTP와 실제 dispatcher·원장·Source 재생·renderer를 사용한다. 금융·실제 모델·운영 DB를 호출하지 않는다. 실제 1초 요청 타이머와 외부 취소를 구분하는 시험도 포함한다. 모델 진입 시험의 Source/ModelPlan 수락 포트는 합성이므로 실물 문안 생성으로 보고하지 않는다.

개발 환경에서는 부분별 실행 및 실패 경계 재확인을 통해 신규 48개 고유 사례의 최신 결과가 통과했다. 전체 48개를 최종 커밋에서 한 번 실행한 기록은 아직 아니다. 기존 정상/제외 경계 6개도 별도로 통과했다. Mac 결과를 개발 기록과 합쳐 한 번의 실물 검증처럼 표현하지 않는다.

시작·종료 HEAD, Python 버전, 시험 집계, exit code와 clean 상태만 기록한다. C51 47개, C49 전수 시험, 전체 pytest를 반복하지 않는다. 실패하면 해당 오류를 기록하고 예약 적용을 보류한다. 실패한 경계 외에 검증 범위를 계속 넓히지 않는다.

## 4. C46 저장 야간 응답을 한 번 진단

C46의 기존 `SCHEDULE.json`/실행 보고서에 적힌 정확한 generation에서 `source/production-frozen-source-plan.json`과 원래 `night/probe`, `dispatch`를 확인한다. 홈·iCloud 전체를 탐색하지 않는다. C46 generation 자체를 `--source-root`로 넘기지 말고 실제 Source 디렉터리를 넘긴다.

```bash
"$C52_PY" -m scripts.c52_inspect_saved_night \
  --source-root "$C46_SOURCE_ROOT" \
  --output "$C52_RESULT_DIR/C46_NIGHT_DIAGNOSIS.json"
```

저장 5응답의 날짜·원본 일치 여부, parse 결과, 현재 일별/주월 materialize 결과를 요약한다. 후속 2응답이 원래 실행되지 않았다면 새로 만들지 않는다. 반환 코드 2의 상세 상태를 읽어 저장 입력 부족과 실제 현재 코드 오류를 구분한다.

보존 응답 부족 자체는 새 실행의 차단 사유로 추가하지 않는다. 신규 48개 경계가 통과했고 현재 코드의 결함이 새로 발견되지 않았다면 다음 등록을 계속한다. 현재 코드의 실제 결함이 드러나면 그 오류만 보고하고 등록을 보류한다. 과거 Source 재수락·B2 재수락·전체 문안 재생은 하지 않는다.

## 5. 내일 미국 단발 설정

성공한 C50R1 `SCHEDULE.json`이 가리키는 **미국 config**에서 `basis`, `settings_env_file`, `shared_lease_path`, `source_configuration`, `model_binding`, `endpoint_rules`, `auxiliary_issuer`를 읽어 새 C52 config에 이어받는다. 이전 실행 시각·tag·run_root·코드 핀은 복사하지 않는다. 한국 config를 미국의 출발 설정으로 쓰지 않는다.

새 label은 `local.thesis-monitor.us.full.once.c52.20261125`, 새 config는 기존 local-launchd 설정 디렉터리의 `once-c52-us-20261125.json`을 권장한다. 아래는 전체 config가 아니라 변경 필드다. tag는 형식상 유효한 제안값이며 기존 소비 기록과 겹치지 않는지 한 번 확인한다.

```json
{
  "enabled": true,
  "mode": "LIVE_NO_SEND",
  "market": "us",
  "code_commit": "<C52_COMMIT 40자>",
  "run_root": "<기존 run base 아래 새 C52 전용 절대 경로>",
  "market_b2_timeout_retry": false,
  "kr_market_timeout_retry": false,
  "us_night_policy": "OPTIONAL_CURRENT_PROBE",
  "one_shot": {
    "tag": "us-20261125-c52a1b2c",
    "scheduled_at": "2026-11-25T08:10:00+09:00",
    "target_session": "2026-11-24"
  }
}
```

실제 generation은 `<run_root>/one-shot/2026-11-25/<tag>`다. `SCHEDULE.json`의 `run_root`에는 이 실제 generation 경로를 기록한다. 예약 시각 기준 완료장은 미국 11월 24일이다. 등록하는 현재 시각의 11월 23일 완료장을 복사하지 않는다.

| 경계 | 이번 단발 값 |
|---|---|
| 시작 시각 / 허용 창 | 11월 25일 08:10 KST / 08:10 이상 08:20 미만 |
| 캠페인 종료 한계 | 같은 날 12:40 KST, 예약 시각부터 4시간 30분 |
| 대상 | 시장 1개 + 등록된 미국 14종목 |
| 금융 HTTP / 모델 | 기존 최대 710회 / 공유 최대 42회 |
| 모델 확정 타임아웃 재시도 | MARKET 최대 1회, 각 종목 B2 최대 1회, 공유 상한 내 |
| Source / 개별 CLI / 부모 Worker | 1800초 / 600초 / 630초 |
| 야간선물 | 최대 7날짜·요청당 20초·HTTP 재시도 0회 |
| 작업 / 결과 / 가용 공간 | 2 GiB / 96,000,000바이트 / 최소 12 GiB |
| 발송·주문·운영 DB 쓰기 | 0회 |

미국 `market_b2_timeout_retry=false`는 기존 미국 `B2_PER_TICKER_ONE_RETRY_V1` 경로를 유지하는 값이다. 이를 true로 바꿔 별도 확장 상한으로 들어가지 않는다. 기본 모델 30회에서 남는 예산은 12회이므로 시장과 모든 14종목이 동시에 재시도해도 모두 실행된다고 보장하지 않는다. 누적 모델/VALIDATE/RENDER 600초 제한은 복원하지 않는다.

## 6. launchd 등록과 readback

현재 실행과 공유 lease 상태를 한 번 확인한다. 인증 파일은 설정 경로의 존재와 읽기 가능 여부만 확인한다. 토큰 파싱·사전 로그인·금융 시험 조회를 추가하지 않는다. KRX의 기존 설정은 정상 설정 로더로 읽고 값은 출력하지 않는다.

새 config는 현재 사용자 소유의 일반 파일로 0600에 저장한다. 기존 `read_local_configuration(path, "us")`, 예약 시각의 `latest_one_shot_us_session()` 확인, `plutil -lint`로 설정을 확인한다. 이는 config 읽기이며 실행 진입점은 호출하지 않는다.

새 plist의 `WorkingDirectory`는 C52 worktree, `ProgramArguments`는 다음 순서다.

```text
/Users/sskim/Codex/thesis-monitor/.venv/bin/python
-B
-m
app.jobs.unified_market_snapshot
--local-scheduled
--configuration
<새 C52 config 절대 경로>
--market
us
--one-shot-tag
us-20261125-c52a1b2c
```

`StartCalendarInterval={Month:11, Day:25, Hour:8, Minute:10}`, `RunAtLoad=false`, `KeepAlive=false`로 둔다. Mac의 실제 시간대가 Asia/Seoul인지 읽어서 확인한다. 다음은 실제 uid·plist 경로를 채워 실행한다.

```bash
launchctl enable "gui/<uid>/local.thesis-monitor.us.full.once.c52.20261125"
launchctl bootstrap "gui/<uid>" "<새 C52 plist 절대 경로>"
launchctl print "gui/<uid>/local.thesis-monitor.us.full.once.c52.20261125"
```

같은 C52 label이 이미 있으면 실제 내용을 먼저 읽어 중복 등록하지 않는다. `kickstart`, 즉시 분석 실행, 예약 창을 놓친 뒤의 지연 재발화는 하지 않는다. 실행기가 같은 generation의 중복 소비를 막는 기존 동작을 유지한다.

`SCHEDULE.json`에는 tag, label, 실제 generation 경로, 대상 거래일, 예약 시각, 시작 창 종료, deadline, code_root/commit, config/plist 경로와 실제 바이트 해시, 위 한도와 정책을 기록한다. `launchctl print`의 작업 경로·인자·calendar를 한 번 대조한 뒤에만 `C52_US0810_REGISTERED`로 보고한다.

한국 평일 **16:00은 현재 C51 연결 그대로**, 미국 정기·구 한국 15:35·C38 12:45는 **OFF 그대로** 둔다. C52는 같은 Git 계보에서 검증하는 다음 릴리스이며 별도의 미국 영구 포크를 만들지 않는다. 한국 운영 핀의 후속 전환은 이번 미국 단발과 별개다.

## 7. 사후 확인과 실제 문안 확보

내일 **11월 25일 12:45 KST**에 새 C52 실행을 읽는 사후 확인을 준비한다. 기존 C38의 `ops/c44/postrun.py`는 날짜·C38 경로·핀에 고정돼 있으므로 재사용하거나 C38을 켜지 않는다.

Mac의 기존 `/Users/sskim/Documents/Codex/2026-07-04/the/maintenance/20261121-pr52-c36-readback-live/observe.py`를 한 번 읽어, 읽기 전용 `snapshot()` 기능과 원래 terminal 추출을 새 `SCHEDULE.json`에 연결할 수 있으면 **C52 maintenance 전용 작은 helper와 별도 `local.thesis-monitor.us.postrun.once.c52.20261125` label**로 등록한다. 분석 재시작·금융·모델·DB 호출은 넣지 않는다. 기존 C38 main/핀 체인을 가져오지 않는다. 이는 Mac 예약·결과 수집용 환경 연결이며 분석 코드의 로컬 분기를 만들지 않는다.

새 helper/등록이 실제 완료되면 그 경로·시각·readback을 `POSTRUN_SCHEDULE.json`으로 남긴다. 기능이 없거나 준비하지 못한 경우 `C52_POSTRUN_AUTOMATION_NOT_REGISTERED`로 명시하고 원래 단발 등록은 유지한다. 존재하지 않는 자동 알림을 약속하거나 ChatGPT 알림을 Mac 실행으로 대체하지 않는다.

종료 뒤 아래 원래 기록을 사용한다.

- `<generation>/terminal.json`
- `<generation>/model-runtime-preflight.json`의 `execution`
- `<generation>/results/unified-snapshot-runs/<execution>/terminal.json`의 원래 `messages`와 VALIDATE/RENDER 결과

`messages[].text`는 변경 없이 UTF-8 `messages/<message_id>.txt`로 저장하고 실제 TXT 바이트의 `MESSAGE_HASHES.json`, 원문 모음 `ACTUAL_MESSAGES.md`, 14종목 `STOCK_COMPARISON.md`를 만든다. 새 모델 호출이나 재렌더로 채우지 않는다. 원래 B2 입력이 생겼으면 다음 기존 도구로 판단·가격·지지 근거를 읽을 수 있다.

```bash
"$C52_PY" -m scripts.c49_inspect_saved_inputs \
  --cycle "$C52_CONSUMER" \
  --output "$C52_RESULT_DIR/C52_ENTRY_INPUTS.json"
```

확인 항목은 실제 시장 1+종목 14 문안, B/B2·최종 행동, 기준가격/선택 지지/진입 조건/WAIT 이유, 야간선물 상태·실제 조회 수·일별 비교일·주월 미확보 사유다. 일부 단계가 미도달이면 `NOT_REACHED`, 문안이 없으면 미생성으로 보고한다. 야간 미확보와 캠페인 자체 실패를 구분한다.

C51의 호출별 `runtime-cleanup.json`과 최종 남은 저장량도 이번 실제 실행에서 확인한다. `scripts.c51_storage_inventory --generation <정확한 generation> --output <결과>`를 사용할 수 있다. 실제 기록된 peak와 종료 후 retained bytes를 구분하고, peak가 없으면 추정하지 않는다. Source·원문·최초 오류를 보존하고 보관량 축소를 위해 같은 내용을 결과 ZIP에 중복하지 않는다.

terminal, 전용 프로세스 종료, 공유 lease 해제를 확인한 뒤 **C52의 정확한 분석 단발과 사후 확인 label/plist만** 정리한다. 날짜와 소비 기록을 보존해 내년 같은 날짜나 다음 wake에서 재실행되지 않게 한다. 추가 캠페인이나 재수집을 자동 시작하지 않는다.

## 8. 결과 제출

등록 단계는 `RESULT.md`, `C52_FOCUSED.xml`, `C46_NIGHT_DIAGNOSIS.json`, `SCHEDULE.json`, 실제 사후 확인 등록 여부를 작은 결과 ZIP과 SHA-256 사이드카로 제출한다. 상태를 `C52_MAC_OFFLINE_PASS`, `C52_C46_DIAGNOSIS_COMPLETE/PARTIAL`, `C52_US0810_REGISTERED`, `C52_POSTRUN_REGISTERED/NOT_REGISTERED`, `C52_ACTUAL_PENDING`으로 구분한다.

실행 뒤 실제 문안·비교표·야간선물·호출 수·자동 정리량을 별도 후속 결과로 제출한다. 파일별 수락 해시 목록이나 새로운 인증 절차를 추가하지 않는다. iCloud 목적지 바이트를 한 번 대조하고 업로드 완료는 실제 완료를 확인한 경우에만 보고한다. 아직 실행되지 않은 15/15나 야간선물 정상 표시를 미리 PASS로 쓰지 않는다.
