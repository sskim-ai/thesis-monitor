# C47 — 미국 야간선물 사전 제외 연결 · 새 단발 실물 문안 확인

## 목표와 이미 승인된 범위

사용자는 야간선물을 향후 포함할 데이터로 유지하면서, 이번 미국 실행은 수집 시작 전에 제외하고 **시장 1개 + 종목 14개의 실제 NO-SEND 문안**을 확인하도록 승인했다. C38 사후 확인의 모델 미도달 처리 수정도 승인했다. 이 지시서를 수행하기 위해 같은 승인을 다시 요청하지 않는다.

이번 변경은 사전 제외를 수집 계획 → Source 구성 → 시장 입력 → 모델·문안에 연결한다. 기본 `ORIGINAL_CURRENT_PROBE_ONLY` 경로는 유지한다. 제외 모드에서는 야간 조회·숫자·등락률·방향·참조를 만들지 않고 시장 문안에 제외 안내 한 줄을 표시한다. 야간 내부 `ValueError` 원인 조사와 정상 포함 경로의 실물 복구는 후속 작업이며, 야간선물을 영구 제거한 것으로 보고하지 않는다.

C46은 C45에서 Source 수락 전에 종료된 별도 실행이다. 그 실패 상태·422회 원장·원래 코드 핀을 그대로 두고, 새 실행은 새 config·tag·run_root·label을 사용한다. 현재 요청은 새 단발 1회이며, 반복 캠페인·미국 정기 활성화·발송·주문·DB 쓰기를 포함하지 않는다.

## 1. 정확한 커밋과 별도 작업트리 준비

- 저장소: `sskim-ai/thesis-monitor`
- 브랜치: `codex/c47-us-optional-night-20261124`
- 지정 커밋: **이 지시서와 함께 전달된 ChatGPT 최종 응답의 전체 SHA**를 사용한다. fetch 후 그 SHA가 브랜치에 있고 파일 내용이 일치하는지 확인한다. 나중에 브랜치가 이동했더라도 임의의 최신 HEAD로 바꾸지 않는다.
- 기존 Python: `/Users/sskim/Codex/thesis-monitor/.venv/bin/python`을 재사용한다. 새 환경·패키지 설치는 하지 않는다.

기존 C45 작업트리 `/Users/sskim/Documents/Codex/2026-07-04/the/work/thesis-monitor-c43-unified-20261123`는 12:45 C38 사후 확인이 `374145c4337d50673db672c73a49e071b1801b5b`로 읽는다. **그 작업트리를 C47로 checkout하지 않는다.** 동일 저장소에서 다음과 같은 별도 worktree를 지정 커밋으로 만든다.

`/Users/sskim/Documents/Codex/2026-07-04/the/work/thesis-monitor-c47-us-night-20261124`

실제 경로가 이미 있으면 용도·HEAD를 먼저 확인하고 사용자 작업을 덮지 않는다. 현재 KR 운영 핀·한국 평일 16:00 예약·미국 정기 OFF는 실제 파일과 launchd에서 한 번 읽어 기준으로 삼는다. 이 문서가 Mac의 현재 상태를 확인한 결과는 아니다.

## 2. 변경 경계만 한 번 오프라인 검증

다음 집중 시험 **42개만** C47 worktree에서 기존 Python으로 한 번 실행한다. `C47_PY`에는 위 기존 Python 절대 경로, `C47_XML`에는 새 C47 유지보수 디렉터리의 XML 절대 경로를 지정한다. JUnit XML과 exit code를 남긴다. C45의 53개·전체 pytest·보존 수락본 전체 재생·실제 인증 요청을 반복하지 않는다.

```bash
"$C47_PY" -m pytest -q \
  tests/test_c47_optional_night_source.py \
  tests/test_c47_optional_night_market.py \
  tests/test_c47_one_shot.py \
  tests/test_c47_postrun_source_stop.py \
  tests/test_c44_postrun.py \
  tests/test_c46_postrun_binding.py \
  tests/test_c38_future_one_shot.py \
  tests/test_c22ac_selected_whole.py::test_selected_required_budget_omits_only_unconsumed_optional_roles \
  tests/test_c22ac_selected_whole.py::test_selected_composition_raw_time_and_registration_guards \
  --junitxml="$C47_XML"
```

개발 환경 Python 3.12.14에서는 이 묶음이 **42 PASS, 12.60초**였다. 새 Source 시험은 임시 합성 DB·모의 native 결과로 실제 등록 실행 함수의 수집 계획 생성까지 확인하고, 외부 금융 전송 직전에 멈춘다. 시장·종목 문안 시험은 합성 입력을 실제 projection·렌더러에 연결한다. 실물 Source 수락·신규 모델 분석·운영 예약 적용까지 완료했다는 뜻은 아니다.

시험 도우미에는 새 정책 인자 전달을 반영했다. C43에서 이미 사라진 동작을 전제로 `client=None`의 private 한국 수급 조회를 직접 호출하던 오래된 단언은 제거했으며, 실제 컴파일된 조회 목록·예산·기본 야간 정책 비교는 유지했다. 이번 변경으로 운영 한국 수급 코드를 바꾸지 않았다.

`git diff --check`와 시작·종료 HEAD/작업트리 상태를 함께 확인한다. 시험에는 합성·mock 입력만 사용한다. 실물 금융·모델·운영 DB 접근으로 오프라인 시험을 보완하지 않는다. 실패한 경우에는 해당 실패를 먼저 보고하며 실물 실행을 시작하지 않는다.

## 3. 기존 C38 12:45 사후 확인의 제한된 유지보수

대상 디렉터리:

`/Users/sskim/Documents/Codex/2026-07-04/the/maintenance/20261122-pr52-c38-postrun`

아직 실행되지 않았고 해당 postrun 프로세스가 없을 때, C47의 `ops/c44/postrun.py`를 설치하고 기존 `FINAL_COMMAND_PIN.json`의 `script_sha256`만 새 파일 바이트의 SHA-256으로 갱신한다. `ops/c44/PIN_UPDATE.json`의 이전 해시·변경 범위를 따른다. 교체 전 두 파일은 작은 C47 작업 디렉터리에 보관하고 각각 원자교체한다.

다음은 그대로 보존한다.

- C38 원본 SCHEDULE·CODE_PINS·INSTALL_INTENT와 기존 08:10 실행 결과
- `CURRENT_EXECUTION_BINDING.json`의 C45 root/SHA/코드 핀 및 그 바이트 해시
- 기존 FINAL_COMMAND_PIN의 등록 명령·초기 설치 해시·현재 실행 연결 해시
- 12:45 plist·label·시각

새 postrun은 Source에서 끝난 실행을 `MARKET/CORE/A/B/B2/VALIDATE/RENDER = NOT_REACHED`, 모델·문안 0으로 기록하고 최초 Source 오류를 보존한다. 새 모델 사용권·문안·Source 수락을 만들지 않는다.

12:45에 새 C47 분석이 공유 lease를 사용 중이면, C38의 종료된 결과 읽기는 수행하고 **리소스 확인·이전 단발 정리만 유예**한다. 이를 새로운 분석 실패나 리소스 해제 완료로 보고하지 않는다. C47 종료 후 실제 lease가 비었을 때 원래 C38 label·해시가 일치하는 plist만 정리한다. 새 C47 작업이나 한국 예약에는 영향을 주지 않는다.

이미 C38 postrun이 실행 중이면 파일을 덮지 않는다. 이미 완료됐으면 기존 실제 결과를 읽어 상태를 보고하고, 같은 C38 사후 처리를 재실행하지 않는다. `postrun.py main()`을 설치 확인용으로 실행하지 않는다.

## 4. 새 미국 단발 시각과 설정

새 실행은 준비 완료 후 **가장 가까운 안전한 미래 시각**으로 한 번 등록한다. 기본 후보는 KST 현재 시각에 2분을 더한 뒤 다음 분 경계로 올림한 시각이다. **초·마이크로초는 0**으로 하고 config와 plist가 같은 시각을 가리키게 한다. 기존 분석 프로세스·공유 lease 사용 여부를 실제 확인한다.

- 후보 시작 시각 + 4시간 30분이 **한국 16:00보다 최소 10분 일찍** 끝나는 경우 그 후보를 사용한다.
- 그 구간을 확보하지 못하면 한국 16:00 실행의 실제 종료와 lease 해제를 확인한 뒤 최소 2분 후로 정한다. 한국 예약을 끄거나 캠페인 제한을 줄여 끼워 넣지 않는다.
- C38 12:45 작업은 종료된 별도 실행에 대한 읽기 전용 사후 확인이므로 새 금융·모델 캠페인으로 취급하지 않는다. 위의 정리 유예 동작을 사용한다.
- 날짜가 바뀌면 과거 예약 시각을 재사용하지 않는다. 등록 직전 기존 `us_market_session()`과 XNYS 달력으로 최신 **완료** 미국 거래일을 구하고 새 설정에 기록한다. 미래·미완료 거래일이나 단순 평일 계산을 사용하지 않는다.

2026-11-24 KST에 미국 11/23 거래가 최신 완료 거래인 시점에는 `target_session="2026-11-23"`이다. 실제 준비 시각이 달라지면 코드 달력의 결과를 확인하여 기록한다.

기존 C46 미국 단발 config를 읽어 필요한 실행환경·protocol 경로를 재사용하고, 별도 파일에 다음 값만 설정한다.

```json
{
  "enabled": true,
  "mode": "LIVE_NO_SEND",
  "market": "us",
  "code_commit": "<지정된 C47 전체 SHA>",
  "run_root": "<새 C47 run base 절대 경로>",
  "market_b2_timeout_retry": false,
  "kr_market_timeout_retry": false,
  "us_night_policy": "EXCLUDED_BEFORE_COLLECTION",
  "one_shot": {
    "tag": "us-<KST YYYYMMDD>-c47a6e2d",
    "scheduled_at": "<실제 등록할 ISO 시각, +09:00 포함>",
    "target_session": "<기존 달력에서 확인한 완료 거래일>"
  }
}
```

이는 전체 config가 아니라 변경할 필드 예시다. `basis`, `settings_env_file`, `shared_lease_path`, `source_configuration`, `model_binding`, `endpoint_rules`, `auxiliary_issuer` 등 나머지는 기존 유효 설정을 사용한다. 인증값 자체를 결과물에 출력하지 않는다. 새 config는 기존과 같이 현재 사용자 소유·0600으로 저장한다. 별도 인증 절차를 추가하지 않으며 인증 파일 확인은 존재·읽기 가능 범위로 유지한다.

새 `one_shot`는 코드가 tag·시각·완료 거래일을 함께 읽는 설정이다. 시작 허용 구간은 등록 시각부터 10분, 종료 한계는 등록 시각부터 4시간 30분으로 계산된다. C38의 오래된 tag나 하드코딩된 시각을 재사용하거나 운영 코드를 현장에서 다시 수정하지 않는다.

권장 경로는 기존 `.../data/local-launchd` 아래 `once-c47-us-<날짜>.json`, `runs/c47-us-<날짜>-full`, `logs/c47-<날짜>`이다. 실제 generation 디렉터리는 `<run_root>/one-shot/<KST 날짜>/<tag>`다. 이미 소비된 동일 tag·실행 디렉터리가 있으면 다른 tag를 만들어 자동 재실행하지 않는다.

## 5. 기존 실행기로 단발 등록

기존 미국 단발 plist를 템플릿으로 사용하되 별도 label을 만든다.

`local.thesis-monitor.us.full.once.c47.<YYYYMMDD>`

ProgramArguments는 다음 형태다.

```text
/Users/sskim/Codex/thesis-monitor/.venv/bin/python
-B
-m
app.jobs.unified_market_snapshot
--local-scheduled
--configuration
<새 C47 config 절대 경로>
--market
us
--one-shot-tag
<config.one_shot.tag와 같은 값>
```

`WorkingDirectory`는 C47 worktree로 지정한다. 환경에 코드 import 경로가 있다면 같은 worktree를 가리키도록 맞춘다. `StartCalendarInterval`은 실제 KST 시작 시각의 Month/Day/Hour/Minute, `RunAtLoad=False`, `KeepAlive=False`로 둔다. 새 로그 경로를 사용하고 추가 재발화 시각·StartInterval은 만들지 않는다. 연 단위 launchd 달력의 재발화는 코드의 정확한 날짜·소비된 intent 검사로 거절된다.

JSON 파싱·`read_local_configuration()`·정확한 완료 거래일·`plutil -lint`만 확인한 뒤 새 label을 `launchctl enable`하고 `bootstrap` 한 번 수행한다. 실제 runner 호출이나 `kickstart`는 하지 않는다. 등록 전 준비가 늦어져 후보 시각을 넘겼다면 아직 등록·소비되지 않은 후보만 새 미래 시각으로 다시 정한다.

등록 직후 `launchctl print gui/<uid>/<새 label>`을 한 번 읽어 다음을 확인한다: loaded/enabled, 지정 C47 root/SHA, config와 같은 tag·calendar, PID 없음·runs=0. 기존 12:45·한국 16:00·미국 정기 OFF 상태도 기록한다.

등록 완료는 `C47_US_SINGLE_REGISTERED_NOT_FIRED`로 먼저 보고한다. 실제 KST 시작·종료 한계·대상 완료 거래일·전체 SHA를 포함한다. 이 상태는 실물 PASS가 아니다.

## 6. 실물 호출 계약

| 항목 | 이번 단발 |
|---|---|
| 대상 | 시장 US + 기존 미국 14종목 |
| 금융 HTTP 상한 | 기존 710 유지. 새 계획의 야간 descriptor·실제 호출은 0 |
| 금융 자동 재시도 | 0 |
| Source | 1800초 |
| 실제 모델 | 기존 GPT-6.1 Sol / high 바인딩 |
| 개별 CLI / 부모 Worker | 600초 / 630초 |
| 전체 캠페인 | 최대 16200초, 등록 시각의 종료 한계를 넘지 않음 |
| 모델 호출 | 공유 최대 42회 |
| 타임아웃 재시도 | MARKET 확정 타임아웃 최대 1회, 각 B2 최대 1회, 모두 42회 안에서 |
| 의미 보정·캠페인 재시작 | 0 |
| 운영 DB | 기존 읽기 전용 캡처 1연결·5 SELECT·15초·64MiB |
| 발송·주문·운영 DB 쓰기 | 0 |

`market_b2_timeout_retry=false`에서도 기존 미국 B2 정책은 MARKET 재시도 1회와 종목별 B2 재시도를 공유 42회 안에서 지원한다. 이를 `true`로 바꾸면 43회 별도 예산 경로가 되므로 변경하지 않는다. 가능한 모든 타임아웃 재시도를 동시에 42회 안에서 보장한다고 보고하지 않는다.

전체 종목: CORZ, CPNG, CRCL, GOOGL, HUT, IBM, MU, RXRX, SKHY, SNDK, TSLA, TSM, WRD, WULF. SKHY의 기존 `UNKNOWN_LIMIT` 경로는 정상 B2 수락과 구분한다.

## 7. 원래 실행의 실제 문안과 판단 결과 수집

실행 중에는 기존 원장·상태 파일과 launchd만 읽는다. 기존 `maintenance/20261121-pr52-c36-readback-live/observe.py`의 읽기 전용 관찰 함수를 새 SCHEDULE/run_root에 연결하거나 동일 파일을 새 작업 디렉터리에 복사하여 사용한다. 복사본 옆 `SCHEDULE.json`에는 새 `label`, `tag`, 실제 generation `run_root`, `scheduled_kst`, `window_end`, `deadline`, `target_session`, `code_root`, `code_commit`, 새 config/plist 경로와 해시를 기록한다. 과거 SCHEDULE의 실행 시각·현재 상태·승인 영수증을 새 실행의 사실처럼 복사하지 않는다. 금융·모델·DB를 다시 호출하는 검증을 하지 않는다. C38 postrun을 C47 run_root로 바꾸지 않는다.

새 단발이 terminal을 쓰고 프로세스가 종료되면 즉시 결과를 읽는다. C47 완료 확인을 위해 C38 12:45 예약을 기다릴 필요는 없다.

- `<실제 generation 디렉터리>/terminal.json`의 `messages`가 최종 문안 원본이다.
- 같은 디렉터리의 `model-runtime-preflight.json`에서 `execution`, `journal_path`를 읽는다.
- 내부 결과는 `results/unified-snapshot-runs/<execution>`이다. 저장된 MARKET/CORE/A/B/B2/VALIDATE/RENDER 수락 결과와 최종 terminal이 같은 generation인지 기존 로더로 확인한다.
- 정상 전체 완료는 `RENDER_VERIFIED_NO_SEND`, 15개 ID가 `MARKET_US` + 위 14종목과 일치하고 원래 VALIDATE/RENDER/terminal의 문안이 일치한 경우다. 새 Owner·수락·문안 재생을 발급하지 않는다.
- 부분 결과·Source/모델 실패는 실제 상태와 최초 오류를 보고한다. `NOT_REACHED`를 WAIT/HOLD로 바꾸거나 15/15로 채우지 않는다. 새 tag·재수집·추가 모델 호출로 자동 복구하지 않는다.

`ACTUAL_MESSAGES.md`에는 **각 `messages[].text`를 그대로** ID별로 담는다. 요약으로 대체하지 않는다. 별도 비교표는 원래 B2 입력·결과와 렌더 결과에서 다음 열만 추출한다.

`종목 / 종합 판단 / 신규매수 판단과 사유 / 보유 판단 / 기준가격과 완료 거래일 / 선택 지지 및 봉 기간 / 가격 위치 / 진입 품질·무효화 / 최종 행동`

WAIT이면서 유리한 가격 위치, 기업 매력이 있으면서 구간 밖인 사례 등은 실제 사유가 연결됐는지 본다. 모두 BUY이거나 모든 지지 근거가 존재하는 것을 통과 기준으로 삼지 않는다. 실제로 관측되지 않은 주·월봉·돌파 사례는 미관측으로 기록한다.

최소 결과물은 `RESULT.md`, 실행/호출 집계, 실제 전체 문안, 종목 비교표, 최초 오류 또는 정상 terminal 요약, 집중 시험 XML이다. 원장·수락 원본은 원래 실행 경로에 보존하고 결과 ZIP에는 필요한 작은 자료만 넣는다. ZIP·SHA를 기존 Codex Results 방식으로 전달하며 저장 완료와 iCloud 업로드 완료는 각각 실제 관측한 상태만 보고한다.

종료 후 C47의 정확한 label만 비활성화·정리한다. C38 정리가 유예됐으면 원래 label/PID/plist 해시와 lease 해제를 확인해 그 대상만 마무리한다. 한국 정기·미국 정기 설정은 위 범위대로 유지한다.
