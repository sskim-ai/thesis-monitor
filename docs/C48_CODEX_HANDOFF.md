# C48 — Source 계약 검사 간소화 · 미국 실제 문안 15개 확인

## 목표와 이미 승인된 실행

사용자는 C48 간소화와 **새 미국 단발 1회에서 시장 1개 + 종목 14개의 실제 NO-SEND 문안을 확보**하는 작업을 승인했다. 같은 범위의 승인을 다시 요청하지 않는다. ChatGPT가 수정·push한 정확한 커밋을 Mac Codex가 최소 검증한 뒤, 기존 예약과 겹치지 않는 미래 시각에 한 번 실행한다.

C47은 미국 11/23 완료장을 대상으로 금융 HTTP 417회, 야간선물 0회를 수행한 뒤 분석 Source 수락 전에 종료됐다. 수동 코드 SHA 목록에 C45 변경 한 항목이 남아 있어 모델·문안은 0이었다. C48은 **14파일 수동 SHA 승인 목록을 폐지하고, 데이터 계약·근거 관계 검사와 지정 Git 커밋·자동 실행 코드 식별로 역할을 나눈다.** 수집 자료의 종목·거래일·generation·근거 연결과 실제 모델 수락 검사를 제거하는 변경이 아니다.

한국 데이터 경로의 AST 고정 검사는 이번 변경 범위 밖이다. 이를 포함해 모든 해시·코드 검사가 제거됐다고 보고하지 않는다. C45의 B2 판단·가격 위치·진입 조건 연결과 C47의 야간선물 사전 제외를 유지한다. 야간선물은 이번 단발에서만 `EXCLUDED_BEFORE_COLLECTION`로 처리하며 향후 정상 포함 경로를 남긴다.

C47의 STOP·terminal·수집 자료·원장은 원래 경로에 보존한다. 그 실행을 수정·재개하거나 기존 자료를 새 Source 수락본으로 바꾸지 않는다. C48에는 새 config·tag·run root·label을 사용한다. 미국 정기 활성화, 발송, 주문, 운영 DB 쓰기는 이번 작업에 포함되지 않는다.

## 1. 정확한 코드와 현재 예약 상태 읽기

- 저장소: `sskim-ai/thesis-monitor`
- 브랜치: `codex/c48-source-contract-simplification-20261124`
- **`C48_COMMIT`은 이 문서와 함께 전달된 C48 최종 40자 커밋 SHA**로 설정한다. 문서가 포함된 자신의 커밋 SHA를 문서 안에 하드코딩하지 않는다. fetch 후 해당 SHA가 원격 브랜치에 있는지 확인하고, 이후 브랜치가 이동해도 임의의 최신 HEAD로 바꾸지 않는다.
- Python은 기존 `/Users/sskim/Codex/thesis-monitor/.venv/bin/python`을 `C48_PY`로 사용한다. 환경·패키지를 재설치하지 않는다.
- 기존 저장소에서 지정 커밋의 별도 worktree를 만든다. `C48_REPO`, `C48_WORKTREE`, `C48_RESULT_DIR`는 Mac의 실제 저장소·기존 유지보수 경로를 확인한 뒤 정한다. 이미 사용 중인 디렉터리를 덮지 않는다.

```bash
git -C "$C48_REPO" fetch origin codex/c48-source-contract-simplification-20261124
git -C "$C48_REPO" merge-base --is-ancestor "$C48_COMMIT" origin/codex/c48-source-contract-simplification-20261124
git -C "$C48_REPO" worktree add --detach "$C48_WORKTREE" "$C48_COMMIT"
git -C "$C48_WORKTREE" rev-parse HEAD
git -C "$C48_WORKTREE" status --short
```

기존 C45·C47·한국 운영 worktree를 checkout하지 않는다. C47 보고 시 한국 운영 핀은 `2c0bc967280e1c0923fc491363e450e8cd9b332b`였지만, 이는 현재 상태 확인을 대신하지 않는다. **현재 등록된 config와 launchd를 한 번 읽어** 아래의 실제 코드 경로·핀·시각·활성 상태와 공유 lease 사용 여부를 기록한다.

| 기존 작업 | 보존할 상태 |
|---|---|
| C38 미국 12:45 사후 확인 | 기존 예약·실행 연결 유지. 이미 완료됐다면 완료 결과 보존 |
| 한국 평일 16:00 | 기존 코드 핀과 예약 활성 유지 |
| 구 한국 15:35 | OFF 유지 |
| 미국 정기 | OFF 유지 |
| 종료된 C47 단발 | 제거 완료 상태 유지 |

새 설정의 환경·protocol 경로는 **실제로 읽은 기존 미국 config**에서 가져온다. 결과물에 적힌 오래된 경로를 현재 경로라고 가정하거나 누락 경로를 추측해 만들지 않는다. 인증 파일의 별도 확인은 **설정 경로에 존재하는가, 현재 실행 환경에서 읽을 수 있는가** 두 가지뿐이다. 인증 내용 출력·토큰 파싱·해시 수집·시험 로그인·자동 갱신을 추가하지 않는다.

## 2. C48 변경 경계만 한 번 오프라인 검증

개발 환경(Python 3.12.14)의 최종 검증은 **고유 33개 PASS**다: Source 계약 27개, 실행 코드 동일성 5개, 기존 C47 야간 제외 연결 1개. 최초 실행은 32 PASS·시험 구성 오류 1개였고, 합성 입력의 공유 참조를 분리하고 구체적인 거절 사유를 확인하도록 관련 시험만 수정했다. 생산 코드 추가 변경 없이 해당 7개만 다시 실행해 모두 통과했다. 전체 33개를 반복 실행하지 않았다. 이는 Mac 검증이나 실물 모델·문안 생성 완료를 뜻하지 않는다.

이 절의 C48 집중 시험을 기존 Python으로 **한 번만** 실행한다. `C48_XML`에는 새 결과 디렉터리 안의 XML 절대 경로를 사용한다. 시험은 합성·mock 자료로 계약과 실행 진입 경계를 확인하며 금융 HTTP·실제 모델 CLI·운영 DB를 호출하지 않는다.

```bash
"$C48_PY" -m pytest -q \
  tests/test_newbuyer_b2_v2_coverage.py \
  tests/test_c48_code_identity.py \
  tests/test_c47_optional_night_source.py::test_actual_registered_cycle_freezes_exclusion_before_any_financial_dispatch \
  --junitxml="$C48_XML"
```

확정 목록의 검증 목적은 다음과 같다.

- 수동 14파일 SHA 목록에 의존하지 않으며, 실제 Source 계약·근거 불일치는 거절한다.
- 지정 Git 핀과 자동 실행 코드 식별이 현재 실행에 연결되고, 실행 중 코드 변경은 기존 오류·NO-SEND를 보존하며 중단된다.
- 실행 초기의 코드 변경은 수집 전, 수집 중 변경은 모델 전, 모델 중 변경은 성공 결과 기록 전에 확인된다. 수집 자료에 대한 데이터 계약 검사는 자료를 확보한 뒤 수행하며 모든 계약 문제를 수집 전에 알 수 있다고 가정하지 않는다.
- 기존 미국 단발의 예산·야간 제외·한 번 실행 조건을 유지한다.

시작·종료 HEAD와 worktree 상태, `git diff --check`, JUnit XML과 exit code를 함께 남긴다. **C45의 53개, C47의 42개, 전체 pytest, 보존 실물 전체 재생을 반복하지 않는다.** 실제 실행기로 미리 들어가거나 인증·금융·모델 호출을 시험용으로 추가하지 않는다. 실패하면 첫 실패와 해당 경계를 보고하고 실물 실행은 시작하지 않는다. 현장에서 별도 코드 수정으로 지정 커밋을 바꾸지 않는다.

수동 SHA 목록을 다시 만들거나, 삭제된 목록의 해시를 자동 갱신하는 스크립트를 추가하지 않는다. 자동 실행 코드 식별은 기존 `runtime_code_identity()`가 계산하며 최초 값은 `<실제 generation>/model-runtime-preflight.json`의 `initial_code_identity`에 남는다. 실행기는 이 값과 수집 전·모델 전·성공 결과 기록 전의 값을 비교한다. 변경되면 `registered_runtime_code_changed`로 중단한다. 이 오류 코드만으로 수집 후 실패·모델 0회라고 단정하지 않고 원래 trace와 실제 원장으로 도달 단계·호출 수를 확인한다. 별도 기록 파일·사람 승인·사용권 발급 절차를 만들지 않는다.

## 3. 기존 예약을 보존하고 실제 실행 시각 결정

시각은 검증 완료 후 실제 KST 시계와 현재 예약을 보고 결정한다. 이 문서에 과거 시각을 고정해 등록하지 않는다. 우선 후보는 **현재 시각 + 최소 2분을 다음 분 경계로 올린 미래 시각**이며 초·마이크로초를 0으로 한다. 등록 직전에도 실행 프로세스·공유 lease와 충돌을 확인한다.

1. **후보 시작 + 4시간 30분 + 10분 여유가 한국 16:00 이전**이면 그 후보를 사용한다. 예상 소요 시간이 짧다는 이유로 최대 실행 시간의 충돌을 무시하지 않는다.
2. 오전 시간창을 확보하지 못하면 한국 16:00 실행의 실제 terminal·프로세스 종료·공유 lease 해제를 확인한 뒤, 같은 날 남아 있는 안전한 미래 시각으로 잡는다. 한국 예약 이동·비활성화·캠페인 제한 축소로 끼워 넣지 않는다.
3. C38 12:45는 기존 실행의 사후 확인이다. C47에서 이미 설치한 공유 lease 사용 중 정리 유예 동작을 그대로 사용한다. **이번 작업을 위해 `postrun.py`, `FINAL_COMMAND_PIN.json`, 현재 실행 연결을 다시 설치·갱신하거나 C38 postrun을 미리 실행하지 않는다.** 실제 설치 상태가 다르면 그 작업과 겹치지 않는 후보를 선택한다.
4. 오늘 안전한 미래 시각이 없으면 과거 시각·겹치는 시각으로 등록하지 않고, 현재 완료한 준비와 대기 이유·다음 가능한 후보를 보고한다. 이는 새 승인 절차가 아니라 기존 예약과 시간 상한을 지키기 위한 대기다.

미국 대상일은 기존 `app.services.market_session.us_market_session()`의 최신 완료 정규장과 XNYS 달력으로 확인한다. **2026-11-24 KST 현재 최신 완료장은 `2026-11-23`**이다. 새 시각에 `latest_one_shot_us_session()`이 같은 대상일을 반환하는지 확인한다. 날짜가 바뀌어 최신 완료장이 달라지면 과거 값을 강제로 통과시키지 말고 그 변화와 새 후보를 보고한다.

## 4. 새 미국 config와 단발 등록

기존 유효 미국 config의 환경·source/model protocol·공유 lease 경로를 유지하고 다음 필드만 새 파일에서 설정한다. `code_commit`에는 실제 `C48_COMMIT` 값을 넣는다. 아래는 전체 config가 아니라 변경 필드다.

```json
{
  "enabled": true,
  "mode": "LIVE_NO_SEND",
  "market": "us",
  "code_commit": "C48_COMMIT의 실제 40자 값",
  "run_root": "확인한 기존 run base 아래 새 C48 전용 절대 경로",
  "market_b2_timeout_retry": false,
  "kr_market_timeout_retry": false,
  "us_night_policy": "EXCLUDED_BEFORE_COLLECTION",
  "one_shot": {
    "tag": "us-실제KSTYYYYMMDD-c48a1b2c",
    "scheduled_at": "실제로 결정한 미래 ISO 시각(+09:00)",
    "target_session": "달력으로 확인한 최신 완료 미국 거래일"
  }
}
```

`one_shot.tag` 형식은 `us-YYYYMMDD-`와 소문자·숫자 8자리다. 같은 tag가 이미 소비됐으면 자동으로 다른 tag를 발급해 다시 실행하지 않는다. `run_root`는 기존 실행과 다른 새 base이고, 실제 generation은 `<run_root>/one-shot/<KST 날짜>/<tag>`다. 새 config는 기존 실행기의 저장 규칙대로 생성한다. 기존 config·운영 핀을 덮지 않는다.

새 label은 `local.thesis-monitor.us.full.once.c48.<YYYYMMDD>` 형태로 만들고, 실제 기존 미국 단발 plist의 실행환경을 사용한다. ProgramArguments는 기존 실행기를 그대로 사용한다.

```text
/Users/sskim/Codex/thesis-monitor/.venv/bin/python
-B
-m
app.jobs.unified_market_snapshot
--local-scheduled
--configuration
<새 C48 config 절대 경로>
--market
us
--one-shot-tag
<config.one_shot.tag와 같은 값>
```

`WorkingDirectory`와 import 경로는 정확한 C48 worktree로 맞춘다. `StartCalendarInterval`은 실제 KST 시작 시각의 Month/Day/Hour/Minute이며 `RunAtLoad=False`, `KeepAlive=False`로 둔다. 별도 새 로그 경로를 쓰고 추가 시각·StartInterval을 넣지 않는다.

등록 전에는 JSON 파싱, `read_local_configuration()`, 완료 거래일·시각 일치, `plutil -lint`만 확인한다. 원래 실행기의 Git 핀·자동 코드 식별 검사를 우회하거나 이를 위해 새 실물 실행을 미리 시작하지 않는다. 새 label을 enable한 뒤 bootstrap **한 번** 수행하며 `kickstart`를 하지 않는다. 등록 전에 후보 시각을 놓쳤고 intent도 소비되지 않았다면 새 미래 후보로 조정할 수 있다.

등록 직후 launchd readback 한 번으로 loaded/enabled, C48 worktree·config·tag·calendar, PID 없음·runs=0을 확인한다. 실제 설정과 Git HEAD로 전체 커밋을 확인한다. `SCHEDULE.json`에는 실제 generation 경로, 새 config/plist 경로, tag·label, 시작·10분 시작 허용 끝·종료 한계, 대상 완료장, 코드 root·SHA를 기록한다. 필요 경로는 이 파일에서 읽으며 과거 SCHEDULE의 시각·상태를 새 사실처럼 복사하지 않는다.

등록 완료는 **`C48_US_SINGLE_REGISTERED_NOT_FIRED`**로 보고한다. 실제 KST 시각·대상일·전체 SHA를 포함하고, 실물 PASS로 표현하지 않는다. 등록 후에는 승인된 한 번의 발화와 종료까지 관찰한다.

## 5. 유지할 실행 한도

| 항목 | 이번 미국 단발 |
|---|---|
| 대상 | MARKET_US + 기존 미국 14종목 |
| 야간선물 | 계획·실제 조회 0. 제외 안내 외 가격·등락률·방향·근거 참조 생성 없음 |
| 금융 HTTP / 자동 재시도 | 최대 710회 / 0회 |
| Source | 1800초 |
| 모델 바인딩 | 기존 유효 GPT-6.1 Sol / high 바인딩 |
| 개별 모델 CLI / 부모 Worker | 600초 / 630초 |
| 전체 캠페인 | 최대 16200초. 등록 시각에서 계산한 종료 한계 준수 |
| 실제 모델 호출 | 공유 상한 42회 |
| 확정 타임아웃 재시도 | MARKET 최대 1회, 각 종목 B2 최대 1회. 모두 공유 42회 안에서 |
| 모델 단계·VALIDATE·RENDER 누적 로컬 600초 | 제거 상태 유지 |
| 운영 DB | 기존 읽기 전용 1연결·5 SELECT, 15초·64MiB 한도 유지 |
| 발송·주문·운영 DB 쓰기 | 0회 |
| 의미 보정·캠페인 재시작·추가 단발 | 0회 |

`market_b2_timeout_retry=false`를 유지한다. 기존 미국 `B2_PER_TICKER_ONE_RETRY_V1` 정책은 MARKET·종목 B2 확정 타임아웃 재시도를 공유 42회 안에서 지원한다. `true`로 바꾸어 43회 예산 경로를 열지 않는다. 모든 종목과 MARKET에 재시도가 동시에 발생해도 전부 실행된다는 보장은 아니며 공유 상한이 우선한다. 실제 재시도가 0이면 재시도 분기가 실물에서 검증됐다고 보고하지 않는다.

종목은 **CORZ, CPNG, CRCL, GOOGL, HUT, IBM, MU, RXRX, SKHY, SNDK, TSLA, TSM, WRD, WULF**다. SKHY의 기존 `UNKNOWN_LIMIT` 경로는 정상 B2 수락과 구분한다. 전 종목 BUY·전 종목 지지 구간 확보를 통과 조건으로 삼지 않는다.

## 6. 실제 원문 확보와 판단 비교

실행 중에는 기존 원장·상태·프로세스만 읽는다. 기존 읽기 전용 관찰 함수가 필요하면 새 SCHEDULE을 사용해 호출하며, 원래 C38 postrun의 run root나 기존 결과를 바꾸지 않는다. 새로운 분석·수집·문안 재생으로 결과를 보완하지 않는다.

terminal이 쓰이고 프로세스가 종료되면 다음 기존 경로에서 원래 결과를 읽는다.

- `<실제 generation>/terminal.json`: 최종 실제 `messages`.
- `<실제 generation>/model-runtime-preflight.json`: 실행 ID·모델 journal 경로·`initial_code_identity`.
- `<실제 generation>/results/unified-snapshot-runs/<execution>`: 원래 단계 수락 결과와 최초 오류.
- 같은 generation의 원장·intent와 위 `initial_code_identity`: 실제 코드·설정·실행 연결 확인.

정상 전체 완료는 `RENDER_VERIFIED_NO_SEND`, **15개 ID = MARKET_US + 위 14종목**, 원래 VALIDATE·RENDER·terminal 문안 일치, NO-SEND로 판단한다. 기존 저장 결과 로더로 같은 generation과 문안 해시를 확인한다. 새 Owner·사용권·모델 수락을 발급하거나 원래 프로세스를 재현해 결과를 채우지 않는다.

**각 `messages[].text`를 UTF-8 원문 그대로 `messages/<message_id>.txt`로 저장**한다. 공백·개행·문장 수정 없이 저장하고 `MESSAGE_HASHES.json`에 실제 파일 바이트의 SHA-256을 남긴다. 원래 결과의 `content_sha256`은 기존 digest 규칙의 값이므로 raw UTF-8 파일 SHA와 같은 값이라고 가정하지 않는다. 필요하면 원래 content hash를 별도 필드로 함께 기록한다. `ACTUAL_MESSAGES.md`는 이 원문을 ID별로 모은 읽기용 문서이며 원문 TXT를 대체하지 않는다.

`STOCK_COMPARISON.md`는 원래 B2 입력·수락 결과·렌더 결과에서 다음 열을 채운다.

| 종목 | 종합 판단 | 신규매수 판단·사유 | 보유 판단 | 기준가격·완료 거래일 | 선택 지지·봉 기간 | 가격 위치 | 진입 조건·무효화 | 최종 행동 |
|---|---|---|---|---|---|---|---|---|

이번에 우리가 실제로 확인하려는 것은 다음 연결이다.

- 가격 위치가 유리해도 신규매수 WAIT이면 가치평가·재무·위험 등 실제 대기 사유가 연결되는가.
- 기업 매력이 있어도 구간 밖이면 가격 조정·신규 확인 신호 등 진입 조건이 명시되는가.
- 참고 S/R과 진입 판단에 선택된 지지가 구분되고, 현재 일봉가격을 완료 주·월봉 지지와 비교할 때 거래일·봉 기간이 맞는가.
- 선택 지지 무효화·근거 부족이 최종 행동에 반영되며 설명 없는 `UNRESOLVED`가 남지 않는가.

관측하지 않은 사례는 미관측, 미생성 결과는 미생성으로 적는다. 미도달을 WAIT/HOLD로 치환하지 않는다. 실패·부분 완료 시에는 실제 단계와 최초 오류를 그대로 기록하고 자동 재수집·재시작하지 않는다. 문안이 생겼어도 판단 연결에 문제가 있으면 해당 원문과 입력 근거를 남겨 다음 코드 검토 대상으로 보고한다.

## 7. 최소 제출과 종료 정리

제출은 다음 정도면 충분하다. 큰 원시 공급자 자료·인증 파일·환경 복제·중복 검증 패키지를 새로 만들지 않는다.

- `RESULT.md`: 전체 SHA, 오프라인 시험, 실제 시작·종료·대상일, 단계 결과, HTTP·모델·재시도·문안 수, NO-SEND, 보호 예약 상태.
- 집중 시험 JUnit XML, 실제 SCHEDULE·등록·종료 readback의 작은 기록.
- 실제 문안 TXT, `MESSAGE_HASHES.json`, `ACTUAL_MESSAGES.md`, `STOCK_COMPARISON.md`.
- 기존 원장에서 추출한 금융·모델 호출 집계와 원래 terminal/최초 오류의 필요한 작은 영수증. 자동 코드 식별은 원래 `model-runtime-preflight.json`의 `initial_code_identity`를 포함한다.
- 위 결과 ZIP과 SHA-256 사이드카. 기존 Codex Results 전달 방식으로 저장한다.

새로운 전수 감사·보안 점검·디스크 GC·독립 승인 패키지를 추가하지 않는다. ZIP·사이드카와 목적지 저장 파일 바이트를 한 번 비교하고, iCloud 업로드는 실제 완료가 관찰됐을 때만 완료라고 보고한다. 관찰하지 못한 단계는 구분한다.

종료 후 새 C48의 정확한 label만 비활성화하고 원래 기록과 일치하는 해당 plist를 정리한다. 프로세스 종료·공유 lease 해제를 확인하며 기존 C38·한국 예약을 건드리지 않는다. 기존 C38 정리가 실제로 유예된 경우에만 원래 정리 범위대로 마무리한다. **실물 결과를 함께 검토하기 전 미국 정기를 켜지 않는다.**
