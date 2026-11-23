# C46 — 11월 24일 미국 08:10 단발을 C45로 전환

## 이미 승인된 작업

사용자 지시: “8시10분에 미국장 예약 아직 남아있는데, 이거 최신코드로 예약 변경해서 미국시장이랑 미국종목들 실제메세지까지 어떻게 나오나 확인해보자.”

이 지시는 **기존 2026-11-24 08:10 KST 미국 단발의 분석 코드 전환과 필요한 12:45 사후 확인 연결**을 승인한다. 이전 C43/C44/C45 작업의 ‘이 예약을 변경하지 않는다’는 제한은 이번 변경 범위에 한해 대체된다. 같은 승인을 다시 요청하지 않는다.

분석 커밋은 Mac에서 53/53 PASS한 **`374145c4337d50673db672c73a49e071b1801b5b`**로 고정한다. 이 문서와 `ops/c44/postrun.py`를 제공하는 C46 지원 커밋은 전달 메시지의 전체 SHA를 사용한다. **분석 작업트리를 C46 지원 커밋으로 checkout하지 않는다.** 지원 파일은 fetch 후 `git show <지원 SHA>:<파일>`로 꺼낸다.

## 유지할 실행 범위

| 항목 | 값 |
|---|---|
| 실행 label | `local.thesis-monitor.us.full.once.c38.20261124` |
| 단발 tag | `us-20261124-c38f2a6d` |
| 시작 / 시작 허용 창 | 2026-11-24 08:10 KST / 기존 08:10~08:20 |
| 완료 거래일 / 종료 상한 | 2026-11-23 / 2026-11-24 12:40 KST |
| 사후 확인 | 기존 2026-11-24 12:45 KST, label·plist·시각 유지 |
| 모드 / 출력 | LIVE_NO_SEND / MARKET_US 1개 + 종목 14개 = 15개 |
| 모델 | 기존 gpt-6.1-sol / high / 물리 호출 최대 42회 |
| 재시도 | MARKET·일반 종목 B2 각각 확정 타임아웃 최대 1회, 총 42회 안에서 |
| HTTP / 금융 재시도 | 기존 공급자별 상한·총 710회 / 0회 |
| DB | 기존 실행 시 읽기 전용 캡처 1연결·SELECT 최대 5·15초·64MiB |
| 시간 제한 | CLI 600초·부모 630초·전체 16,200초 |
| 발송 / 주문 / 운영 DB 쓰기 | 모두 0 |

`market_b2_timeout_retry=False`를 유지한다. 기존 C38 tag에서 True로 바꾸면 시작 전에 충돌로 거절된다. False여도 기존 US per-ticker 정책은 MARKET의 첫 확정 타임아웃 재시도를 허용한다. 설정의 `market_timeout_retry_cap=0`은 MARKET 독립 예약분이 없다는 뜻이며, 재시도가 금지됐다는 뜻이 아니다. **29 기본 + MARKET 1 + B2 13의 최악 43회를 모두 보장하지는 않는다.** 이번에는 상한을 43으로 올리거나 실패 캠페인을 다시 시작하지 않는다.

한국 평일 16:00, 구 한국 15:35 OFF, 미국 정기 OFF를 유지한다. 성공해도 미국 정기를 활성화하지 않는다.

## 실제 경로

기준 디렉터리:
`/Users/sskim/Documents/Codex/2026-07-04/the`

- C45 개발 작업트리 후보: `work/thesis-monitor-c43-unified-20261123` — 실제 HEAD·clean을 확인하고, 실행 종료까지 그대로 고정한다.
- 기존 C38 등록 기록: `maintenance/20261122-pr52-c38-next-session`
- 사후 처리: `maintenance/20261122-pr52-c38-postrun`
- 단발 config: `work/thesis-monitor-pr52-local-launchd-20261119/data/local-launchd/once-c38-us-20261124.json`
- 단발 plist: `/Users/sskim/Library/LaunchAgents/local.thesis-monitor.us.full.once.c38.20261124.plist`
- 기존 Python: `/Users/sskim/Codex/thesis-monitor/.venv/bin/python`

단발의 `run_root`, tag, config 경로, Python, Source·모델 binding, endpoint 규칙, env 파일, shared lease, Native 경로, 로그 경로는 재사용한다. 새 tag나 새 실행 디렉터리를 만들어 이미 소비된 실행을 우회하지 않는다.

## 1. 변경 전 한 번 확인

현재 KST가 **08:10 이전**이고 대상 label에 PID가 없으며, 기존 run 디렉터리의 `intent.json`, `terminal.json`, `campaign.jsonl`, `STOP` 및 부모의 `<tag>.intent.json`이 없는지 확인한다. 실제 경로는 기존 `SCHEDULE.json`에서 읽는다. 기존 shared lease와 Lane에 실행이 없을 때만 교체한다.

이미 실행됐거나 시작 시간이 지났으면 교체·중단·kickstart·중복 실행하지 않고 실제 상태를 보고한다. 새 시각의 실행을 임의로 만들지 않는다.

기존 config·plist·설치된 postrun.py·FINAL_COMMAND_PIN.json의 변경 전 바이트를 작은 C46 작업 디렉터리에 보관한다. C38 원본 등록 ZIP, SCHEDULE.json, CODE_PINS.json, INSTALL_INTENT.json, LIVE_SCOPE_APPROVAL.json은 그대로 둔다. C38 원래 install.py/control.py를 재실행하지 않는다.

## 2. 교체할 5개 파일을 먼저 준비

### 08:10 분석: 2개

1. 기존 단발 config는 `code_commit`만 C45 전체 SHA로 바꾼다. `market_b2_timeout_retry`가 없으면 기존 기본 False를 유지하고, 기존 False이면 그대로 둔다. `enabled=True`, `mode='LIVE_NO_SEND'`, `market='us'`와 다른 설정은 보존한다.
2. 기존 단발 plist는 `WorkingDirectory`를 실제 C45 작업트리로 바꾼다. 원래 등록본에는 EnvironmentVariables가 없으며, 실제 파일에 코드 import 경로가 추가되어 있으면 그 경로도 C45와 일치시킨다. ProgramArguments·label·calendar·RunAtLoad=False·KeepAlive=False는 유지한다.

### 12:45 사후 확인: 3개

3. C46 지원 커밋의 `ops/c44/postrun.py`를 기존 사후 처리 경로의 `postrun.py`로 설치한다. 이 버전은 기존 C44의 미국 정기 OFF 동작을 보존하며, 아래 현재 실행 연결을 읽고 observer import 전에 C45 경로를 적용한다.
4. 같은 디렉터리에 `CURRENT_EXECUTION_BINDING.json`을 작성한다. 스키마는 아래와 같다. `<...>`는 실제 후보 파일·작업트리 바이트로 계산한다.

```json
{
  "prior_C38_schedule_sha256": "<변경하지 않은 C38/SCHEDULE.json SHA-256>",
  "schedule_overrides": {
    "code_root": "<실제 C45 작업트리 절대 경로>",
    "code_commit": "374145c4337d50673db672c73a49e071b1801b5b",
    "configuration_sha256": "<새 단발 config SHA-256>",
    "plist_sha256": "<새 08:10 plist SHA-256>",
    "C37_timer_sha256": "<C45 app/services/research_no_send_run.py SHA-256>",
    "after_terminal": "US_REGULAR_OFF"
  },
  "code_pins": {
    "files": {
      "app/jobs/unified_market_snapshot.py": {"bytes": 0, "sha256": "<실제 값>"},
      "app/services/research_no_send_run.py": {"bytes": 0, "sha256": "<실제 값>"},
      "app/services/unified_stock_owner.py": {"bytes": 0, "sha256": "<실제 값>"},
      "app/services/entry_price_basis.py": {"bytes": 0, "sha256": "<실제 값>"},
      "app/services/new_buyer_input_owner.py": {"bytes": 0, "sha256": "<실제 값>"},
      "app/services/detailed_stock_message_v2.py": {"bytes": 0, "sha256": "<실제 값>"}
    }
  }
}
```

`bytes: 0`은 예시 자리표시자이며 실제 크기로 기록한다. `prior_C38_schedule_sha256`는 기존 사후 처리 INSTALL_INTENT의 `original_C38_schedule_sha256`와 같아야 한다. C45 타이머 파일은 C38 당시와 바이트가 다르므로 과거 타이머 해시를 복사하지 않는다.

5. 기존 `FINAL_COMMAND_PIN.json`에서 `script_sha256`를 새 postrun 바이트 해시로 갱신하고, `current_execution_binding_sha256`에 위 JSON의 실제 바이트 해시를 추가한다. 기존 `script`, `registered_command`, `initial_install_script_sha256`와 다른 과거 정보는 보존한다. `PIN_UPDATE.json`을 파일 전체와 교체하지 않는다.

기존 12:45 plist·시각·label은 변경하거나 reload할 필요가 없다. 설치된 postrun이 C45 import 경로와 현재 핀을 적용한다. tag·run_root·42/710 상한 등은 원본 SCHEDULE에서 계속 읽는다.

## 3. 짧은 설치 확인 후 동일 예약으로 교체

후보 파일의 Python 구문, JSON 파싱, plist 문법, C45 HEAD·모듈 경로 및 현재 연결 값만 확인한다. 실제 분석 runner나 postrun main은 실행하지 않는다. C45의 53개 시험·전체 pytest·과거 수락본 재생·새 인증·보안 검사를 반복하지 않는다. 인증 파일은 기존 합의대로 존재·읽기 가능만 다루며 실물 로그인/모델 호출로 시험하지 않는다.

교체 직전 08:10 이전·대상 미실행 상태를 다시 확인한다. **해당 08:10 label만** bootout한 뒤 준비한 파일을 각각 원자교체하고, 5개 파일의 연결이 맞는지 확인한다. 기존 소유권·모드(특히 config의 0600)를 유지한다. 동일 label을 enable/bootstrap 한 번 수행하고, readback에서 다음을 한 번 확인한다.

- loaded/enabled, 새 C45 WorkingDirectory, 기존 config/tag/08:10 calendar
- PID 없음·runs=0, RunAtLoad=False, KeepAlive=False
- config의 C45 SHA, 변경한 파일과 current binding의 해시 일치
- 12:45 사후 확인과 한국·미국 정기 설정은 지정한 범위대로 보존

`kickstart` 또는 즉시 분석 실행은 하지 않는다. 설치 실패 시 아직 실행 전이면 이전 5개 파일·등록 상태로 되돌리고 실패를 보고한다. 실행이 시작됐으면 파일을 덮거나 프로세스를 중단하지 않는다.

bootstrap과 등록 확인도 08:10 전에 완료한다. 교체 도중 이 시각이 지나면 정상 대기 등록 완료로 보고하지 않고 실제 시작·미시작 상태를 확인한다.

등록 완료를 먼저 `C46_US0810_C45_REGISTERED_NOT_FIRED`로 보고한다. 보고에는 실제 적용한 C45 root/SHA, 두 label·시간, 미실행 상태, 보존한 42회 상한을 포함한다. 이 상태를 실물 PASS로 부르지 않는다.

## 4. 예정된 실제 실행과 문안 확인

08:10 기존 runner가 새 입력으로 정상 실행하게 한다. 예정된 실물 단계에서는 원래 승인된 금융 조회·모델 호출·읽기 전용 DB 캡처가 허용된다. 준비 단계의 호출 0과 실물 실행의 실제 호출 수를 구분한다.

12:45 기존 사후 확인이 같은 generation의 원래 terminal·B2 결과·최종 문안을 읽는다. 별도 캠페인·새 모델 호출·Owner 재발급·문안 재생은 하지 않는다. 원래 최초 오류를 보존하고, 부분 성공이나 SKHY 제한 메시지를 정상 B2 성공으로 바꾸지 않는다. 사후 확인은 종료된 해당 단발만 정리하며 미국 정기를 켜지 않는다.

최종 결과에는 기존 사후 확인 결과와 함께 **원래 메시지 전체 15개**를 읽기 쉬운 Markdown 또는 텍스트로 담는다. 원본 `text`를 그대로 내보내며 요약문으로 대체하지 않는다. 메시지가 15개 미만이면 실제 생성된 개수와 누락·실패 사유를 기록한다.

종목별 비교표는 기존 결과에서 다음만 추출한다: 종합 판단, 신규매수 판단·사유, 보유 판단, 기준가격·완료 거래일, 선택 지지·봉 기간, 가격 위치, 진입 품질/무효화, 최종 행동. SKHY UNKNOWN_LIMIT는 별도 제한 상태로 표시한다. 실제 관측되지 않은 주·월봉/돌파 사례는 미관측으로 둔다.

통과 기준은 실제 `intent.code_commit=C45`, 동일 generation의 수락·RENDER·terminal 일치, 실제 시장 1+종목14 문안 및 NO-SEND 보존이다. 데이터 부족으로 명확한 이유가 있는 WAIT은 정상일 수 있으며, 모두 BUY가 되거나 모든 진입 근거가 생기는 것을 성공 조건으로 삼지 않는다.

작은 결과 ZIP·SHA와 실제 문안 파일을 기존 Codex Results 방식으로 전달한다. 등록·실행·문안 검토·iCloud 완료는 각각 관측한 상태로 구분해 보고한다.

## 지원 코드 확인

C46 변경은 사후 처리의 현재 실행 연결과 결과의 코드 핀 표기에 한정된다. 개발 환경에서 새 연결 경계 4개와 기존 사후 처리 회귀 4개, **총 8개가 통과**했다. 실제 main·launchctl·금융·모델·운영 DB는 실행하지 않았다. Mac에서는 위 설치 대상의 짧은 구문·핀·등록 확인만 수행하며 C45 53개를 다시 실행하지 않는다.
