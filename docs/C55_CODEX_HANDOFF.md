# C55 — 주봉 최근성 보정, 저장봉 영향 비교, 미국 실물 문안 확인

## 승인된 목표

사용자는 C54 결과 검토 뒤 제시한 **최근성 계산 최소 수정 → C52 저장봉 영향 비교 → 새 미국 실물 NO-SEND 문안 15개 확인**에 동의했다. 아래 오프라인 확인과 새 단발 1회 등록·실행·결과 수집을 이어서 완료한다. 별도 반복 승인·새 인증 체계를 추가하지 않는다.

- 저장소: `sskim-ai/thesis-monitor`
- 브랜치: `codex/c55-weekly-recency-20261125`
- 기준: C54 `0dcbf90f264de35d7eaa2a6aa01afed9556e67f2`
- 검증·실행 코드: 채팅으로 전달한 최종 **C55 40자 커밋 SHA**
- 미국 단발: **2026-11-26 08:10 KST**, 미국 **2026-11-25 완료장**
- 사후 확인: **2026-11-26 12:45 KST**, 원래 C55 실행 읽기만 수행

한국 평일 16:00의 코드·예약과 미국 정기 OFF 상태는 유지한다. 기존 C52/C38 단발이나 사후 확인 label을 재활성화하지 않는다. 새 C55 전용 label·config·generation만 만든다. 실제 등록은 Mac의 readback으로 확인하고, 이 문서 자체를 예약 완료로 보고하지 않는다.

## 변경 내용과 해석

주봉 피벗은 최근 120개의 정규화된 유효 봉에서 위치를 매기는데, 구간 최근성은 주요 스윙용 최대 156개 봉 수를 사용하고 있었다. 이제 `build_price_zones()`에 **피벗 탐색과 같은 local lookback으로 정규화한 실제 봉 수**를 넘긴다. 주요 스윙의 156봉 이력과 기존 피벗·최근성 배점·지지 강도·손익비 기준은 그대로다.

C54의 PBR 입력 연결, 지표 기준일/조회 시각 구분, 선택 일봉과 과거 주봉의 위치 비교, 구체적인 대기 조건을 포함한다. C52 원문과 수락 결과는 수정하지 않는다. 최근성 수정으로 특정 7종목의 지지가 반드시 생기거나 매수 의견이 늘어야 한다는 합격 기준은 없다.

`c49_inspect_saved_inputs`는 원래 구조의 `chart_state`를 읽도록 고쳤다. 원래 선택 ID를 현재 코드로 평가한 필드는 `current_assessment_for_original_selected_candidate`로 명확히 이름 붙였다. 예전 JSON의 `original_selected_candidate_assessment`는 그 당시 새 진단값이었으므로 과거 수락본으로 해석하지 않는다.

## 1. 기존 환경에서 변경 경계만 한 번 확인

개발 환경의 기존 Python 3.12.14에서 아래 새 시험 **16개를 한 번 실행해 16 PASS / 실패·오류·skip 0, 1.60초, 종료 코드 0**을 확인했다. 주봉/일봉/월봉 경계 12개와 저장 자료 비교 4개다. 실제 C52 봉의 종목별 영향과 새 실물 문안은 Mac에서 확인할 항목이다.

기존 Python `/Users/sskim/Codex/thesis-monitor/.venv/bin/python`과 C55 전용 작업트리를 사용한다. 운영 중이거나 예약이 참조하는 작업트리를 checkout하지 않는다. 실제 경로를 `C55_REPO`, `C55_WORKTREE`, `C55_RESULT_DIR`, `C55_PY`, `C55_COMMIT`에 지정한다.

```bash
git -C "$C55_REPO" fetch origin codex/c55-weekly-recency-20261125
git -C "$C55_REPO" merge-base --is-ancestor "$C55_COMMIT" FETCH_HEAD
git -C "$C55_REPO" worktree add --detach "$C55_WORKTREE" "$C55_COMMIT"
git -C "$C55_WORKTREE" rev-parse HEAD
git -C "$C55_WORKTREE" status --short
git -C "$C55_WORKTREE" diff --check 0dcbf90f264de35d7eaa2a6aa01afed9556e67f2 "$C55_COMMIT"
```

기존 C55 작업트리가 있으면 올바른 커밋인지 확인하고 재사용한다. C55 작업트리에서 다음 두 파일만 한 번 실행한다.

```bash
"$C55_PY" -m pytest -q \
  tests/test_c55_pivot_recency.py \
  tests/test_c55_saved_structure.py \
  --junitxml="$C55_RESULT_DIR/C55_FOCUSED.xml"
```

시작·종료 HEAD, Python 버전, 집계, exit code, clean 여부만 기록한다. C54 35개, 기존 회귀 36개, 야간선물·인증·전체 시험을 다시 돌리지 않는다. 이번 변경의 실제 결함이 나오면 해당 경계를 수정하고 새 실물 등록을 보류한다.

## 2. C52의 저장봉으로 최근성 영향만 비교

기존 C54 결과가 확인한 C52 generation:

```text
/Users/sskim/Documents/Codex/2026-07-04/the/work/thesis-monitor-pr52-local-launchd-20261119/data/local-launchd/runs/c52-us-20261125-full/one-shot/2026-11-25/us-20261125-c52a1b2c
```

`C52_SOURCE_ROOT`는 위 경로의 `source`다. `C52_CONSUMER`는 원래 `model-runtime-preflight.json`의 `execution`이 가리키는 `results/unified-snapshot-runs/<execution>`이다. 기존 C54 보고서에 실제 소비자 경로가 있다. 홈·iCloud 전체를 탐색하지 않는다.

```bash
"$C55_PY" -m scripts.c55_compare_saved_structure \
  --source-root "$C52_SOURCE_ROOT" \
  --cycle "$C52_CONSUMER" \
  --tickers CORZ,CRCL,MU,RXRX,SKHY,SNDK,WRD \
  --output "$C55_RESULT_DIR/C52_RECENCY_IMPACT.json"
```

도구는 원래 normalized 일·주·월봉과 저장된 timeframe context를 읽고 기존 완료봉 투영 함수를 이용한다. 두 계산은 **같은 입력과 같은 C54 이후 규칙**을 사용하고, 비교 기준 쪽만 과거의 잘못된 `bar_count`를 재현한다. C52 당시의 무효화 정책까지 되돌린 전체 재생이 아니다.

확인할 것은 실제 유효 주봉 수, local/major 창 길이, 주봉 최근성 점수·강도 변화, 현재가 포함/아래 구간과 의미 있는 지지 후보의 변화다. 후보가 계속 없으면 확정 피벗 부재·강도 미달·현재가 위 구간 등 확인 가능한 이유를 적는다. 참고 V3 지지나 등록 가격을 자동으로 진입 구간으로 바꾸지 않는다.

기존 C54 입력 진단을 반복 생성하지 않는다. 비교 도구의 원래 C52 요약과 전후 계산을 구분해 작은 표로 정리한다. 원본 봉이 없거나 대상 분기와 맞지 않으면 해당 종목만 미확인으로 남기고 재수집하지 않는다. **저장 자료 부족 자체를 새 실물 실행의 추가 승인 조건으로 만들지 않는다.** 현재 코드의 실제 오류와 과거 자료 부족은 구분한다.

이 단계의 금융 HTTP·실모델·운영 DB·Source 재수락·전체 문안 재생은 0회다. 원래 generation 밖 결과 폴더에만 출력하며 원본을 수정하지 않는다.

## 3. 새 미국 단발 등록

C52의 성공한 미국 `SCHEDULE.json`이 가리키는 config에서 `basis`, `settings_env_file`, `shared_lease_path`, `source_configuration`, `model_binding`, `endpoint_rules`, `auxiliary_issuer`를 이어받는다. 한국 config를 출발점으로 쓰거나 상대 DB 경로를 새 worktree 기준으로 바꾸지 않는다.

다음은 변경 필드다. 새 config는 기존 local-launchd 설정 디렉터리에 현재 사용자 소유의 일반 파일로 0600에 저장한다. 기존 설정 로더가 요구하는 파일 형식을 그대로 맞추는 작업이다.

```json
{
  "enabled": true,
  "mode": "LIVE_NO_SEND",
  "market": "us",
  "code_commit": "<C55_COMMIT>",
  "run_root": "<새 C55 전용 run root>",
  "market_b2_timeout_retry": false,
  "kr_market_timeout_retry": false,
  "us_night_policy": "OPTIONAL_CURRENT_PROBE",
  "one_shot": {
    "tag": "us-20261126-c55a1b2c",
    "scheduled_at": "2026-11-26T08:10:00+09:00",
    "target_session": "2026-11-25"
  }
}
```

원래 실행기의 거래일 확인 경로로 새 config를 읽는다. 수집 실행 진입점은 호출하지 않는다.

```bash
"$C55_PY" - "$C55_CONFIG" <<'PY'
import sys
from app.jobs.unified_market_snapshot import read_local_configuration, latest_one_shot_us_session
config = read_local_configuration(sys.argv[1], "us")
session = latest_one_shot_us_session(
    config.one_shot.scheduled_at, one_shot_tag=config.one_shot.tag, config=config)
if session is None:
    raise SystemExit("C55_PLANNED_COMPLETED_SESSION_MISMATCH")
print({"scheduled_at": config.one_shot.scheduled_at.isoformat(),
       "target_session": session.isoformat(), "tag": config.one_shot.tag,
       "night_policy": config.us_night_policy})
PY
```

작업을 받았을 때 지정 시각이 이미 지났다면 지난 창을 강제로 실행하지 않는다. 다음 미래 08:10 KST로 잡고, `us_market_session(scheduled_at).latest_completed_regular_session_date`로 대상 완료장을 다시 계산해 날짜·tag·사후 시각을 함께 기록한다. 기존 소비 tag는 재사용하지 않는다. 새 단발의 실제 실행은 총 한 번이다.

| 항목 | 이어받을 값 |
|---|---|
| 대상 | 미국 시장 1 + 등록 미국 종목 14 |
| 시작 창 / 종료 한계 | 08:10 이상 08:20 미만 / 예약 시각부터 4시간 30분, 기본 계획 12:40 |
| 금융 HTTP / 모델 | 공유 최대 710회 / 공유 최대 42회 |
| 확정 모델 타임아웃 재시도 | MARKET 1회·각 종목 B2 1회 이내, 공유 상한 내 |
| Source / 모델 CLI / 부모 Worker | 1,800초 / 600초 / 630초 |
| 야간선물 | OPTIONAL_CURRENT_PROBE, 기존 최대 7날짜·요청당 20초·HTTP 재시도 0 |
| 작업 / 결과 / 최소 가용 공간 | 2 GiB / 96,000,000바이트 / 12 GiB |
| 임시 상태 | 기존 호출별 자동 정리 |
| DB / 발송 / 주문 | 기존 등록용 읽기만 사용, DB 쓰기·발송·주문 0 |

미국 `market_b2_timeout_retry=false`는 기존 `B2_PER_TICKER_ONE_RETRY_V1`의 MARKET/종목 B2 타임아웃 재시도를 유지하는 설정이다. true로 바꿔 43회 경로에 들어가지 않는다. 기본 30호출에서 모든 15대상이 동시에 재시도할 여유까지 보장하는 것은 아니다. 누적 모델/VALIDATE/RENDER 600초 제한을 복원하지 않는다.

인증 파일 사전 확인은 설정 경로의 존재·읽기 가능 여부 두 가지뿐이다. 토큰 파싱, 재로그인, 사전 금융 시험 조회, 별도 DB preflight를 추가하지 않는다. LIVE는 기존 등록용 읽기 연결·SELECT가 필요하므로 실제 건수를 기록한다. C52의 1연결·5 SELECT는 과거 관측값이며 이번 결과를 미리 같은 수로 쓰지 않는다.

실제 Mac의 현재 실행·공유 lease와 시간대를 한 번 확인한다. 공유 lease를 그대로 사용해 다른 실행과 병행하지 않는다. 발화 때 lease가 사용 중이면 기존 `NO_RUN_LOCK_BUSY`를 미실행으로 보고하고, 강제 kickstart나 새 tag로 반복 실행하지 않는다.

권장 label은 `local.thesis-monitor.us.full.once.c55.20261126`이다. plist는 `WorkingDirectory=<C55 worktree>`, `RunAtLoad=false`, `KeepAlive=false`, `StartCalendarInterval={Month:11, Day:26, Hour:8, Minute:10}`으로 둔다. `ProgramArguments`는 다음 순서다.

```text
/Users/sskim/Codex/thesis-monitor/.venv/bin/python
-B
-m
app.jobs.unified_market_snapshot
--local-scheduled
--configuration
<C55 config 절대 경로>
--market
us
--one-shot-tag
us-20261126-c55a1b2c
```

같은 C55 label이 이미 있으면 내용을 먼저 읽어 중복 등록하지 않는다. `plutil -lint`, 새 label의 enable/bootstrap, `launchctl print`로 실제 경로·인자·시각을 확인한다. `SCHEDULE.json`에 실제 generation, commit/worktree, config/plist, tag, 대상 거래일, 시작 창·deadline과 상한을 기록한다.

## 4. 사후 확인과 실제 문안 품질

11월 26일 **12:45 KST**에 C55 전용 사후 확인을 등록한다. C52에서 실제 사용한 읽기 전용 helper가 있으면 그 코드의 읽기 부분을 새 C55 generation/SCHEDULE에 연결한다. C38 고정 `ops/c44/postrun.py`, 이전 날짜·label·핀을 복사하지 않는다. 분석 실행 진입점이나 재수집 기능은 사후 helper에 넣지 않는다.

실제로 등록한 경로·calendar/readback을 `POSTRUN_SCHEDULE.json`에 기록한다. 사후 helper 등록에 실패해도 미국 분석 단발을 다시 등록하거나 실행하지 않는다. 자동 확인이 등록되지 않은 사실과 필요한 수동 readback을 명확히 보고한다.

종료 뒤 `<generation>/terminal.json`, 원래 preflight의 `execution`, 해당 consumer `terminal.json.messages[].text`를 읽는다. 메시지는 그대로 UTF-8 TXT와 `ACTUAL_MESSAGES.md`로 저장하고 실제 TXT 바이트의 해시를 남긴다. 추가 모델·재렌더로 빠진 문안을 채우지 않는다.

```bash
"$C55_PY" -m scripts.c49_inspect_saved_inputs \
  --cycle "$C55_CONSUMER" \
  --output "$C55_RESULT_DIR/C55_ACTUAL_INPUTS.json"

"$C55_PY" -m scripts.c51_storage_inventory \
  --generation "$C55_GENERATION" \
  --output "$C55_RESULT_DIR/C55_STORAGE_INVENTORY.json"
```

`STOCK_COMPARISON.md`에는 다음을 나란히 기록한다.

- 실제 종합·신규·보유 판단, 기준가격, 선택 지지 기간/구간, 무효화선, 현재가 손익비.
- 대기 사유·다음 확인 조건·최종 행동과 원래 B2 판단의 관계.
- PBR의 실제 전달 여부와 실제 수락 응답의 인용 여부를 **별도 열**로 표시. PER/fPER와 지표 기준일·조회 시각도 구분.
- 지지 후보가 없으면 확인 가능한 원인과 참고 S/R을 구분. 새 지지가 생겨도 바로 매수 조건으로 간주하지 않음.

C52와 C55는 거래일·가격·입력·모델 판단이 달라질 수 있다. 이번 동일 저장봉 비교는 최근성 수정의 영향을 확인하며, 새 실물 결과의 변화 전체를 최근성 또는 PBR 수정의 단독 효과라고 설명하지 않는다.

시장 문안에서는 야간선물의 실제 조회·확보 상태와 일별/주월 표시를 확인한다. KRX 최신 봉 미반환은 미국 전체 실패와 구분한다. 금융·모델·재시도·DB 읽기 건수, VALIDATE/RENDER, 최초 오류, 호출별 cleanup 결과와 최종 보관량을 기록한다. peak는 원래 실행에 기록된 수치만 사용한다.

원래 terminal과 프로세스 종료·lease 해제를 확인한 뒤 C55 전용 분석/사후 label·plist만 정리한다. 원래 Source·문안·최초 오류는 보존한다. 실패나 일부 미생성은 원래 상태로 보고하고 추가 캠페인을 자동 시작하지 않는다.

## 5. 결과 제출

등록 시: `RESULT.md`, `C55_FOCUSED.xml`, `C52_RECENCY_IMPACT.json`, 짧은 영향표, `SCHEDULE.json`, 실제 사후 확인 등록 결과. 실행 전 문안은 `PENDING`으로 둔다.

종료 시: 실제 15문안/미생성 목록, `STOCK_COMPARISON.md`, 필요한 원래 영수증·입력 진단·정리량을 작은 결과 ZIP과 SHA-256으로 제출한다. 전체 Source·원 OHLCV·모델 임시 폴더를 ZIP에 중복 복사하지 않는다. iCloud 업로드 완료는 실제 확인 후 보고한다.
