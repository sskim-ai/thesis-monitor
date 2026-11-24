# C50 — 차트 근거 JSON 보존 · 미국 단발 실제 문안 확인

## 목표와 승인 범위

사용자는 C49 결과 검토 뒤 **C50 차트 직렬화 수정 → 변경 경계 검증 → 새 미국 단발 1회에서 시장 1개·종목 14개의 실제 NO-SEND 문안 확인**에 동의했다. 이 문서는 그 승인 범위의 Mac 실행 지시서다. C49의 오프라인 전용 지시를 C50 실물 실행의 추가 승인 조건으로 적용하지 않는다.

C49 Mac 집중 시험 81개와 C48 보존 입력 진단은 완료됐다. C48에서 타이밍이 미해결이었던 수락 종목 11개 및 TSM의 일봉 JSON이 표시용 900자 제한으로 잘렸고, CPNG만 873자로 온전히 남아 있었다. C50은 기존 `statement` 필드에 D/W/M 차트 JSON을 완전하게 보존하고, 원본 fact 비교에도 같은 직렬화 함수를 사용한다. 잘린 과거 입력은 JSON 손상으로 진단하며, 이를 실제 통화·조정 기준·종가 충돌로 표시하지 않는다.

기존 C49의 B/B2/문안 공통 후보 기준, SKHY 본주 비교재무 연결, 타임아웃 누락과 제한 문안의 혼합 부분 완료, 미국 공유 모델 상한 42회는 유지한다. 저장 가격 규칙·완료봉 연결 없는 참고 S/R을 진입 후보로 승격하지 않는다. 새 실행의 판단과 실제 문안으로 효과를 확인한다.

## 1. 지정 커밋과 기존 환경

- 저장소: `sskim-ai/thesis-monitor`
- 브랜치: `codex/c50-lossless-chart-evidence-20261124`
- `C50_COMMIT`: 함께 전달한 최종 40자 SHA. 이후 브랜치가 이동해도 임의의 최신 HEAD로 대체하지 않는다.
- `C50_PY`: 기존 `/Users/sskim/Codex/thesis-monitor/.venv/bin/python`.
- `C50_REPO`, `C50_WORKTREE`, `C50_RESULT_DIR`: 실제 기존 Mac 저장소와 유지보수 경로를 확인해 정한다. 기존 운영 worktree를 checkout하지 않고 새 C50 worktree를 사용한다.

```bash
git -C "$C50_REPO" fetch origin codex/c50-lossless-chart-evidence-20261124
git -C "$C50_REPO" merge-base --is-ancestor "$C50_COMMIT" origin/codex/c50-lossless-chart-evidence-20261124
git -C "$C50_REPO" worktree add --detach "$C50_WORKTREE" "$C50_COMMIT"
git -C "$C50_WORKTREE" rev-parse HEAD
git -C "$C50_WORKTREE" status --short
git -C "$C50_WORKTREE" diff --check "$C50_COMMIT^" "$C50_COMMIT"
```

패키지 재설치·새 인증·파일별 코드 SHA 승인 목록은 추가하지 않는다. 아래 시험의 작업 디렉터리는 C50 worktree다. 시작·종료 HEAD, Python 버전, exit code를 기록한다.

## 2. C50 변경 경계만 한 번 오프라인 검증

`C50_XML`을 새 결과 디렉터리 안의 `C50_FOCUSED.xml` 절대 경로로 정한다.

```bash
"$C50_PY" -m pytest -q \
  tests/test_c50_chart_statement.py \
  tests/test_c50_entry_diagnostics.py \
  --junitxml="$C50_XML"
```

이 목록은 **19개 시험**이다. 실제 차트 fact 생성·근거 생성기를 거쳐 긴 D/W/M 자료가 B 입력·B2·렌더로 전달되는 6개 사례, 원본 비교와 비차트 축약 유지 3개, JSON 파손 진단과 기존 참고자료 제한 10개를 확인한다. 합성 입력과 기존 fixture를 사용하며 금융 HTTP·실제 모델·운영 DB는 호출하지 않는다. 기존 C49 81개·개발 148개·전체 pytest·C48 전체 재생은 반복하지 않는다.

개발 환경에서는 19개 고유 시험의 최종 결과가 모두 PASS다. 차트 통합 fixture의 source catalog 필터와 무효화 가격을 보완하는 동안 실패한 6개만 재검증했으며, 최종 19개 전체를 한 번에 재실행한 기록으로 보고하지 않는다. Mac은 위 두 파일을 지정 커밋에서 한 번 실행해 환경 결과를 제출한다.

실패하면 첫 오류와 해당 경계를 제출하고 실물은 시작하지 않는다. Mac에서 별도 코드 수정으로 지정 커밋을 바꾸거나 전체 시험을 반복하지 않는다. 통과하면 아래 이미 승인된 단발 준비를 계속한다.

## 3. 한국 16:00 작업과 겹치지 않는 미래 시각 선택

C49 보고 기준 상태는 **한국 평일 16:00 ON, C38 12:45 사후 확인 OFF, 미국 정기 OFF, 구 한국 15:35 OFF**다. 현재 등록 config·launchd·실행 프로세스·공유 lease를 한 번 확인해 실제 상태를 기록한다. 이전 문서의 C38 ON 전제를 되살리지 않는다.

이번 지시서 작성 시점은 2026-11-24 KST 15시대다. 한국 16:00 전에 최대 4시간 30분의 미국 실행을 끼워 넣지 않는다. 해당 한국 실행의 **terminal·프로세스 종료·공유 lease 해제**를 확인한 뒤 C50 단발 시각을 정한다. 이미 종료됐으면 그 현재 상태를 사용한다. 한국 작업이 실패한 경우에도 그 실행 결과를 보존하고, 종료·잠금 해제를 확인한 뒤 C50 준비를 계속할 수 있다.

후보는 준비 완료 후 **현재 시각 + 최소 2분을 다음 분 경계로 올린 미래 KST 시각**이다. 후보부터 4시간 30분과 10분 여유가 다음 기존 실행과 겹치지 않는지 확인한다. 충돌하면 기존 예약을 옮기지 않고 충돌이 해소된 다음 가능한 시간창을 사용한다. 과거 시각이나 임의로 예상한 한국 종료 시각으로 등록하지 않는다.

대상일은 기존 `latest_one_shot_us_session()` 및 XNYS 달력으로 최신 완료 정규장을 확인한다. 11월 24일 KST의 현재 완료장은 11월 23일이지만, 실제 등록 시각의 달력 결과를 우선한다. 시작 허용 창은 등록 시각부터 10분이며, 캠페인 종료 한계는 **등록 시작 시각 + 4시간 30분**이다. 늦게 발화해도 종료 한계가 연장되지 않는다.

실행 완료를 기다리는 동안에는 기존 상태·terminal·프로세스만 필요한 간격으로 읽는다. 상세 분석을 반복하거나 상태 관찰을 위해 모델·금융 호출을 추가하지 않는다.

## 4. 새 C50 config와 단발 하나 등록

실제로 읽은 기존 미국 config에서 환경·source/model protocol·공유 lease·전역 Kiwoom lane 경로를 가져온다. 새 C50 config·run root·tag·label만 생성한다. 과거 C48 수집팩·snapshot·Owner·수락본을 새 Source로 복사하는 절차는 없다. 새 실물 Source는 기존 실행기가 구성한다.

인증 파일 사전 확인이 필요하면 **설정 경로의 존재 여부와 현재 실행 환경의 읽기 가능 여부**만 확인한다. 내용 출력·토큰 파싱·해시 수집·시험 로그인·자동 갱신을 추가하지 않는다. 기존 실행기의 실제 인증 동작은 그대로 사용한다.

새 config의 주요 값은 다음과 같다. 아래는 전체 파일이 아니라 변경 필드다.

```json
{
  "enabled": true,
  "mode": "LIVE_NO_SEND",
  "market": "us",
  "code_commit": "C50_COMMIT의 실제 40자 값",
  "run_root": "확인한 기존 run base 아래의 새 C50 전용 절대 경로",
  "market_b2_timeout_retry": false,
  "kr_market_timeout_retry": false,
  "us_night_policy": "EXCLUDED_BEFORE_COLLECTION",
  "one_shot": {
    "tag": "us-실제KSTYYYYMMDD-c50a1b2c",
    "scheduled_at": "확정한 미래 ISO 시각(+09:00), 초·마이크로초 0",
    "target_session": "기존 달력으로 확인한 최신 완료 미국 거래일"
  }
}
```

tag 형식은 `^us-[0-9]{8}-[a-z0-9]{8}$`다. 실제 generation은 `<run_root>/one-shot/<KST 날짜>/<tag>`다. 기존 실행과 다른 새 base·소비되지 않은 tag를 사용한다.

label은 `local.thesis-monitor.us.full.once.c50.<YYYYMMDD>`처럼 구분하고, 기존 미국 plist의 실행환경으로 다음 인자를 사용한다.

```text
/Users/sskim/Codex/thesis-monitor/.venv/bin/python
-B
-m
app.jobs.unified_market_snapshot
--local-scheduled
--configuration
<새 C50 config 절대 경로>
--market
us
--one-shot-tag
<config와 같은 새 tag>
```

`WorkingDirectory`와 import 기준은 C50 지정 worktree다. `StartCalendarInterval`에는 실제 KST 시작 시각 하나만 넣고 `RunAtLoad=False`, `KeepAlive=False`로 둔다. 새 로그 경로를 사용한다.

등록 전 확인은 JSON 파싱·`read_local_configuration()`·완료장/시각 일치·`plutil -lint`로 충분하다. 새 label을 enable하고 bootstrap 한 번 수행한다. kickstart를 하지 않는다. 등록 전에 후보 시각을 놓쳤고 intent가 소비되지 않았다면 새 미래 시각으로 조정할 수 있다.

등록 직후 readback 한 번으로 C50 worktree·config·tag·calendar, loaded/enabled, 미발화 상태를 확인한다. `SCHEDULE.json`에 실제 코드 root·SHA·config·plist·label·generation·대상일·시작 허용 끝·캠페인 종료 한계를 기록한다. 이후 경로는 이 파일에서 읽는다.

등록 상태는 `C50_US_SINGLE_REGISTERED_NOT_FIRED`로 보고하고, 승인된 발화 한 번과 종료까지 관찰한다. intent가 소비된 이후에는 새 tag·추가 단발·캠페인 재시작으로 결과를 메우지 않는다. 예상 밖의 잠금 충돌·시간창 종료는 실제 미실행 사유와 intent 소비 여부를 보고한다.

## 5. 실행 한도

| 항목 | C50 미국 단발 |
|---|---|
| 대상 | MARKET_US + 기존 미국 14종목, 본주 000660은 기존 회사 재무 보조 의존성 |
| 금융 HTTP / 자동 재시도 | 최대 710회 / 0회 |
| Source | 최대 1800초 |
| 야간선물 | 이번 단발은 계획·실제 0회. 제외 안내 외 가격·등락률·방향 근거 생성 없음 |
| 모델 | 기존 유효 GPT-6.1 Sol / high 바인딩 |
| 실제 모델 호출 | 공유 최대 42회 |
| 확정 타임아웃 재시도 | MARKET 최대 1회, 각 종목 B2 최대 1회. 공유 예산 안에서 |
| 개별 CLI / 부모 Worker | 600초 / 630초 |
| 전체 캠페인 | 16200초 및 등록 시각에서 계산한 종료 한계 |
| 모델 단계·VALIDATE·RENDER 누적 로컬 600초 | 제거 상태 유지 |
| 운영 DB | 기존 읽기 전용 1연결·5 SELECT, 15초·64MiB 한도 |
| 발송·주문·운영 DB 쓰기 | 0회 |

`market_b2_timeout_retry=false`와 raw retry cap 0은 미국 재시도 OFF를 뜻하지 않는다. 기존 미국 `B2_PER_TICKER_ONE_RETRY_V1` 경로가 시장·B2 확정 타임아웃 재시도를 처리한다. SKHY까지 일반 대상이면 기본 30회와 공유 재시도 여유 12회이며, 나머지 종목의 최초 호출분을 먼저 확보한다. `market_b2_timeout_retry`를 `true`로 바꿔 기존 43회 확장 경로에 진입하지 않는다. 일반 14종목의 MARKET·B2 재시도를 모두 보장하려면 최대 45회가 필요하지만, 이번 실행은 승인된 공유 상한 42회를 유지한다.

대상 종목은 **CORZ, CPNG, CRCL, GOOGL, HUT, IBM, MU, RXRX, SKHY, SNDK, TSLA, TSM, WRD, WULF**다. 전 종목 BUY, 전 종목 적격 지지 확보, SKHY 일반 모드 강제를 통과 조건으로 삼지 않는다. 실제 수락된 근거와 실제 판단을 확인한다.

## 6. 실제 문안과 근거 연결 확인

실제 generation 아래에서 다음 원래 기록을 읽는다.

```text
<generation>/terminal.json
<generation>/model-runtime-preflight.json
<generation>/results/unified-snapshot-runs/<master>-consumer/terminal.json
```

`<master>`는 `local-us-<대상 거래일>-once-<tag>`다. 바깥 terminal이 실행 요약만 담는 경우가 있으므로 **원래 consumer terminal의 messages 및 VALIDATE/RENDER 결과**를 기준으로 확보한다. 실행 코드 동일성은 기존 자동 `initial_code_identity` 기록을 사용한다.

각 `messages[].text`를 수정 없이 UTF-8 `messages/<message_id>.txt`에 저장한다. `MESSAGE_HASHES.json`에 실제 TXT 바이트의 SHA-256을 남긴다. 원래 `content_sha256`과 raw TXT SHA가 같은 계산이라고 가정하지 않는다. `ACTUAL_MESSAGES.md`에는 읽기 편하게 원문을 ID별로 모으되 TXT를 대체하지 않는다.

기존 `scripts.c49_inspect_saved_inputs`는 세대에 종속되지 않은 읽기 전용 도구다. **새 C50 consumer에 B2 request가 실제 생성돼 있을 때만**, 다음처럼 새 결과를 읽는다. C48을 다시 진단할 필요는 없다.

```bash
"$C50_PY" -m scripts.c49_inspect_saved_inputs \
  --cycle "$C50_CONSUMER" \
  --output "$C50_RESULT_DIR/C50_ENTRY_INPUTS.json"
```

이는 새 실행의 원래 입력을 확인하는 단계이며 Source/모델 수락 재발급이나 문안 재생을 하지 않는다. B2 이전에 실패했다면 진단 미도달과 첫 실패를 적는다.

`STOCK_COMPARISON.md`에는 실제 결과에서 다음을 정리한다.

| 종목 | 종합 | 신규·사유 | 보유 | 기준가격·완료장 | 선택 지지·D/W/M | 가격 위치·진입 조건 | 최종 행동 |
|---|---|---|---|---|---|---|---|

핵심 확인은 다음과 같다.

- **직렬화:** 새 D/W/M statement가 완전한 JSON인지, 긴 일봉도 기존 원본 fact의 fields와 같은지 확인한다. 실제 필드값은 수정하지 않는다.
- **진입:** B 선택 후보와 B2 가격 위치·문안이 일치하는지 본다. 적격 지지가 없으면 그 이유를 표시하고 참고 가격으로 채우지 않는다.
- **판단:** WAIT인데 구간 안인 경우의 재무·가치평가 사유, ATTRACTIVE인데 구간 밖인 경우의 가격·확인 조건, 무효화가 최종 행동에 연결되는지 본다.
- **SKHY:** 본주 회사의 실제 비교재무가 Core·A·B 준비 및 모델 판단에 사용됐는지, 원래 품질 제한과 SKHY 자체 밸류에이션 제한이 구분되는지 기록한다. 자료상 제한이 남으면 실제 이유를 적는다.
- **시장:** SPY/QQQ·금리·WTI·달러·VIX·섹터 등 실제 시장 문안과 이번 야간 제외 표시를 확인한다.

완료 상태는 다음처럼 구분한다.

- `RENDER_VERIFIED_NO_SEND`와 정확한 시장+14종목 ID이면 **15/15 생성**. 제한 문안이 포함됐으면 일반 B2 수락 수와 제한 문안 수를 따로 적는다.
- `RENDER_VERIFIED_PARTIAL_NO_SEND`이면 실제 문안 수·누락 ID·사유를 보고한다. 한 종목 타임아웃으로 14/15이면 부분 완료다. 타임아웃 두 시도와 최초 오류 기록을 보존한다.
- 실패 시 실제 도달 단계·호출 수·최초 오류를 보고한다. 미생성을 WAIT/HOLD로 바꾸지 않는다.

## 7. 최소 결과 제출과 단발 종료 정리

다음 파일을 한 묶음으로 제출한다.

- `RESULT.md`: 전체 SHA, 오프라인 시험, 실제 등록/시작/종료 KST, 완료장, 단계 결과, HTTP·모델·재시도·문안 수 및 종류, NO-SEND.
- `C50_FOCUSED.xml`, 실제 `SCHEDULE.json`, 등록·종료 readback의 작은 기록.
- 실제 문안 TXT, `MESSAGE_HASHES.json`, `ACTUAL_MESSAGES.md`, `STOCK_COMPARISON.md`.
- 생성 가능했던 경우 `C50_ENTRY_INPUTS.json`, 첫 오류·타임아웃·모델 호출 집계의 필요한 원래 기록.
- 결과 ZIP과 SHA-256 사이드카. 기존 Codex Results 방식으로 전달한다.

종료 후 C50 프로세스 종료·공유 lease 해제를 확인하고 **C50의 정확한 단발 label/plist만 정리**한다. 한국 16:00·구 한국 15:35·C38·미국 정기와 기존 운영 핀은 유지한다. 실제 결과를 함께 검토하기 전 미국 정기를 켜지 않는다.

별도 전수 감사·인증 절차·GC·반복 독립 검증 패키지는 추가하지 않는다. ZIP·사이드카 목적지 바이트는 한 번 비교하고 iCloud 업로드는 실제 완료를 관찰한 경우에만 완료라고 보고한다. 합성 검증, 단발 등록, 실제 문안 생성, 업로드 상태를 구분해서 보고한다.
