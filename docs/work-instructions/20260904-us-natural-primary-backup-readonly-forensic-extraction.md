# thesis-monitor — 2026-09-04 US Natural Primary/Backup Read-Only Forensic Extraction

## 목적

오늘 US 자연 모니터링에서 실제로 무슨 일이 있었는지 읽기 전용으로 재구성한다.

핵심 가설은 다음이다.

```text
08:00 primary는 실제로 실행/추론 중이었음
→ 08:20 상태체크가 primary artifact/state를 찾지 못함
→ "primary 없음" 또는 equivalent flag
→ backup 경로 진입
```

이 가설이 맞는지 로그·상태·artifact로 검증한다.

수리/재실행/재전송은 하지 않는다.

---

# 0. 범위

- Target: `US / 2026-09-04 KST`
- Expected user-visible messages: `market 1 + US14 stocks 14 = 15`
- US14:
  `CORZ, CPNG, CRCL, GOOGL, HUT, IBM, MU, RXRX, SKHY, SNDK, TSLA, TSM, WRD, WULF`
- Expected primary start: around `08:00 KST`
- Suspected checker/backup decision: around `08:20 KST`
- Prior shadow context:
  - shadow model call hit `TLS UnknownIssuer`
  - shadow call was stopped before US live to avoid interference
- This task:
  - `REPLAY=0`
  - `MODEL_RERUN=0`
  - `PRODUCTION_MUTATION=0`
  - `TELEGRAM_RESEND=0`
  - `SCHEDULER_CHANGE=0`
  - `DB_CHANGE=0`
  - `MAIN_MERGE=0`

---

# 1. 반드시 답할 질문

1. primary US 자연 실행은 실제로 시작됐는가?
2. primary는 model/Codex까지 도달했는가?
3. 08:20 전후 primary process는 살아 있었는가?
4. 08:20 checker가 정확히 무엇을 "primary 없음"으로 판단했는가?
5. checker가 본 identity/key/path와 실제 primary identity가 일치했는가?
6. backup은 정확히 어떤 reason code로 시작됐는가?
7. primary가 backup 시작 뒤에도 계속 진행됐는가?
8. primary/backup 중 누가 candidate/accepted/delivery owner였는가?
9. accepted AI review가 실제로 생성됐는가?
10. 생성됐다면 왜 사용자가 그 AI review를 받지 못했는가?
11. 자연 US도 shadow와 같은 `TLS UnknownIssuer`를 겪었는가?
12. 최종적으로 사용자가 받은 15개 메시지는 primary AI / backup AI / fallback 중 무엇이었는가?

---

# 2. Authoritative run lineage

07:45 KST부터 최종 delivery terminal까지 US 관련 모든 component를 찾는다.

최소:

```text
primary scheduler
primary job
primary model/app-server
08:20 checker/watchdog
backup scheduler/job
retry worker
fallback worker
delivery worker
```

각 component별:

```text
component
run_id
parent_run_id
market
business_date
analysis_generation
packet_id
candidate_generation
accepted_generation
delivery_generation
scheduled_at
started_at
last_heartbeat_at
finished_at
exit_code
process_id if logged
operating revision
runtime namespace
```

서로 다른 run을 business_date가 같다는 이유로 합치지 않는다.

---

# 3. 단일 chronological timeline

07:45 KST부터 terminal까지 초 단위로 가능한 한 정확하게 만든다.

필수 event:

```text
primary launch
job start
source ready
technical ready
packet persisted
AI-consumability ready
network/TLS preflight
app-server/CLI connect
model request start
model retry
model response complete
candidate persisted
validation
correction if any
accepted persisted
V2 eligibility
delivery pending
08:20 checker
primary-missing flag
backup trigger
backup start
backup reuse/fresh decision
backup model request/result
delivery claim
Telegram send
fallback eligibility/send
primary late completion
terminal state
```

---

# 4. 08:20 primary 실제 상태

08:15~08:25의 직접 증거를 수집한다.

확인:

```text
PID alive
heartbeat fresh/stale
app-server activity
stdout/stderr writes
model retry/stream
candidate/temp artifact updates
packet updates
lock ownership
run-state transition
```

분류:

```text
PRIMARY_STATE_AT_0820 =
NOT_STARTED
RUNNING_ACTIVE
RUNNING_STALLED
MODEL_INFERENCE_ACTIVE
MODEL_RETRY_ACTIVE
FINISHED_SUCCESS
FINISHED_FAILURE
PROCESS_MISSING
UNKNOWN
```

"artifact 없음"을 "process 없음"으로 해석하지 않는다.

---

# 5. 08:20 primary-missing flag

다음과 동등한 실제 로그/코드 경로를 찾는다.

```text
primary missing
primary absent
primary not found
no primary
backup required
```

반드시 추출:

```text
timestamp
component
reason code
lookup function
query/filter predicate
expected state/artifact
actual found/missing
deadline/age threshold
run_id
packet_id
analysis_generation
delivery_generation
market/date filters
artifact path / state key
heartbeat key
```

사람 친화 로그 문구만 보지 말고 실제 predicate를 확인한다.

---

# 6. Primary actual vs checker expected identity

표로 비교:

| Field | Primary actual | 08:20 checker expected | Match |
|---|---|---|---|
| market | | | |
| business_date | | | |
| run_id | | | |
| analysis_generation | | | |
| packet_id | | | |
| candidate_generation | | | |
| accepted_generation | | | |
| delivery_generation | | | |
| runtime namespace | | | |
| artifact path | | | |
| heartbeat key | | | |

Mismatch 분류:

```text
NONE
RUN_ID_MISMATCH
GENERATION_MISMATCH
PACKET_ID_MISMATCH
PATH_NAMESPACE_MISMATCH
HEARTBEAT_KEY_MISMATCH
DELIVERY_KEY_MISMATCH
OTHER
UNKNOWN
```

---

# 7. Checker 의미 구분

08:20 checker가 "primary 존재"를 무엇으로 정의했는지 정확히 판정한다.

가능성:

```text
process exists
heartbeat fresh
packet exists
candidate exists
accepted exists
delivery receipt exists
terminal success exists
```

만약:

```text
candidate/accepted artifact not yet persisted
```

를:

```text
primary process missing
```

으로 취급했다면 명확히 보고한다.

---

# 8. Deadline / watchdog

추출 가능한 모든 relevant timeout:

```text
primary liveness grace
model timeout
candidate deadline
accepted deadline
backup activation time
retry delay
fallback deadline
Telegram timeout
```

각각:
- configured value
- timer start basis
- actual elapsed time
- whether expired at 08:20

값이 없으면 `MISSING_FROM_NATURAL_ARTIFACTS`.

---

# 9. Primary/backup model stage

각각 다음을 뽑는다.

```text
network preflight reached/result
TLS handshake result
Codex app-server reached
CLI invocation reached
model request start
model result count
model completion
elapsed time
retry count
timeout/error class
```

분류:

```text
PRIMARY_MODEL_STATE =
NOT_REACHED
RUNNING
COMPLETED
FAILED_TLS
FAILED_TIMEOUT
FAILED_APP_SERVER
FAILED_OTHER
UNKNOWN
```

backup도 동일.

---

# 10. TLS UnknownIssuer forensic

오늘 자연 US 로그에서 다음 검색:

```text
UnknownIssuer
certificate verify
TLS
SSL
x509
issuer
CA
handshake
```

분류:

```text
NATURAL_US_TLS_STATUS =
NO_TLS_ERROR_OBSERVED
UNKNOWN_ISSUER_OBSERVED
OTHER_TLS_ERROR
INSUFFICIENT_LOGS
```

shadow runtime과 natural runtime 비교:
- CODEX_HOME
- CLI path/version
- app-server namespace
- sandbox/outside-sandbox
- trust/cert env if logged
- shared state/lock

Secrets는 노출하지 않는다.

---

# 11. Shadow interference audit

추출:

```text
shadow start
shadow UnknownIssuer retry window
shadow stop
US primary start
shared runtime?
shared app-server?
shared state DB?
shared model concurrency?
shared locks?
```

분류:

```text
SHADOW_US_INTERFERENCE =
NONE_CONFIRMED
POSSIBLE
CONFIRMED
UNKNOWN
```

시간이 겹쳤다는 이유만으로 interference라고 하지 않는다.

---

# 12. Candidate / validation / accepted

primary와 backup 각각:

```text
market candidate count
stock candidate count
candidate SHA
candidate persisted_at

validation status
failure reasons
correction count
corrected candidate count

accepted count
accepted SHA
accepted persisted_at
```

US 정상 목표:
`1 + 14 = 15`.

---

# 13. Backup trigger vs primary completion timing

비교:

```text
backup_trigger_at
candidate_persisted_at
validation_passed_at
accepted_persisted_at
```

분류:

```text
PRIMARY_COMPLETED_BEFORE_BACKUP
PRIMARY_COMPLETED_AFTER_BACKUP_TRIGGER
PRIMARY_NEVER_COMPLETED
BACKUP_COMPLETED_FIRST
BOTH_COMPLETED
UNKNOWN
```

primary가 backup 뒤 완료했다면 정확한 지연 시간을 기록한다.

---

# 14. Primary/backup overlap

각 process active interval을 구한다.

```text
primary active from/to
backup active from/to
overlap duration
```

그리고:

```text
both model calls concurrent?
same packet/generation write?
analysis reuse?
delivery ownership changed?
```

분류:

```text
NO_OVERLAP
OVERLAP_SAFE_DIFFERENT_GENERATION
OVERLAP_SHARED_STATE
OVERLAP_UNKNOWN
```

---

# 15. Backup action

backup의 실제 행동:

```text
analysis_action =
reuse
fresh
skip
fallback_only
delivery_retry_only
other
```

reuse라면 무엇을 reuse했는지:
- evidence
- packet
- candidate
- accepted
- delivery

"reuse"를 "AI review 완료"로 해석하지 않는다.

---

# 16. V2 eligibility / selector

primary와 backup별:

```text
V2 eligibility
selector/canary state
explicit AI market count
explicit stock V2 count
explicit AI total
suppression reason
```

US operating revision이 KR 수리 revision과 같은지/다른지도 명시한다.

---

# 17. Delivery lineage

각 accepted generation별:

```text
delivery status
pending
claimed
sent
failed
terminal
delivery owner
delivery generation
```

상태 전이를 재구성:

```text
accepted → pending → claimed → sent
```

또는:

```text
accepted → suppressed
accepted → fallback
```

pending이 사라졌다면 정확한 identity/key를 찾는다.

---

# 18. Backup trigger criterion

backup activation이 무엇을 기준으로 했는지 명시:

```text
process liveness
heartbeat
analysis completion
candidate completion
accepted completion
delivery completion
Telegram receipt
```

이게 이번 사건의 핵심 중 하나다.

---

# 19. Exactly-once delivery

실제 최종 전송 수:

```text
AI market
AI stocks
backup AI
fallback market
fallback stocks
duplicates
dedupe suppressions
```

정상 AI 목표:

```text
AI market 1
AI stocks 14
fallback 0
duplicate 0
```

---

# 20. Exact delivered messages

실제 전송된 US message raw UTF-8를 저장:

```text
market.txt
CORZ.txt
...
WULF.txt
```

각 메시지 metadata:

```text
sent_at
mode
owner run/generation
PRIMARY_AI / BACKUP_AI / FALLBACK / UNKNOWN
delivery receipt
```

재전송 금지.

---

# 21. 사용자에게 실제로 간 메시지 source map

최종 표:

| Message | Source |
|---|---|
| market | PRIMARY_AI / BACKUP_AI / FALLBACK / UNKNOWN |
| CORZ | ... |
| ... | ... |

---

# 22. Primary late result

primary가 backup/fallback 뒤에 완료됐다면:

```text
artifact exists?
candidate exists?
accepted exists?
delivery eligible?
why not sent?
```

상태:

```text
DISCARDED
SUPERSEDED
DEDUPED
ACCEPTED_NOT_SENT
DELIVERY_SUPPRESSED
ORPHANED
UNKNOWN
```

---

# 23. State ownership after backup

backup activation이:
- primary cancel
- supersede
- delivery owner transfer
- new generation
- same generation reuse
- primary status mutation

중 무엇을 했는지 persisted state 기준으로 그린다.

---

# 24. Exit codes

다음 exit code와 final classification 추출:

```text
primary
08:20 checker
backup
retry
fallback
delivery worker
```

exit 0만으로 AI 성공이라고 하지 않는다.

---

# 25. First material failure

최초의 materially wrong transition 분류:

```text
PRIMARY_PROCESS_FAILURE
MODEL_TRANSPORT_FAILURE
MODEL_TIMEOUT
LIVENESS_FALSE_NEGATIVE
ARTIFACT_READINESS_FALSE_NEGATIVE
RUN_IDENTITY_MISMATCH
GENERATION_IDENTITY_MISMATCH
PATH_NAMESPACE_MISMATCH
HEARTBEAT_STALE
BACKUP_TRIGGER_TOO_EARLY
DELIVERY_OWNERSHIP_FAILURE
SELECTOR_SUPPRESSION
OTHER
UNKNOWN
```

그 다음:
- `PRIMARY_ROOT_CAUSE`
- `SECONDARY_EFFECTS`
- `NOT_CAUSAL_OBSERVATIONS`

로 구분한다.

---

# 26. No repair

이번 작업에서는 root cause가 보여도 수정하지 않는다.

금지:
- code patch
- timeout 변경
- backup 시간 변경
- model rerun
- replay
- resend
- scheduler 변경
- DB mutation

다음 repair task에서 사용할 함수/파일/state key만 기록한다.

---

# 27. Required reports

Create:

1. `docs/reports/20260904-us-natural-run-lineage.md`
2. `docs/reports/20260904-us-natural-event-timeline.md`
3. `docs/reports/20260904-us-primary-state-at-0820.md`
4. `docs/reports/20260904-us-primary-missing-flag-source.md`
5. `docs/reports/20260904-us-primary-vs-checker-identity.md`
6. `docs/reports/20260904-us-watchdog-deadline-semantics.md`
7. `docs/reports/20260904-us-primary-model-runtime.md`
8. `docs/reports/20260904-us-backup-model-runtime.md`
9. `docs/reports/20260904-us-shadow-vs-natural-tls-runtime.md`
10. `docs/reports/20260904-us-candidate-validation-accepted-lineage.md`
11. `docs/reports/20260904-us-primary-backup-concurrency.md`
12. `docs/reports/20260904-us-v2-selector-delivery-lineage.md`
13. `docs/reports/20260904-us-exact-delivery-results.md`
14. `docs/reports/20260904-us-primary-late-result-handling.md`
15. `docs/reports/20260904-us-first-failure-and-root-cause.md`
16. `docs/reports/20260904-us-natural-run-anomalies.md`
17. `docs/reports/20260904-us-natural-artifact-index.md`
18. `docs/reports/20260904-us-natural-forensic-executive-summary.md`

Machine-readable:
- `20260904-us-run-lineage.json`
- `20260904-us-event-timeline.json`
- `20260904-us-primary-checker-identity.json`
- `20260904-us-pipeline-stages.json`
- `20260904-us-delivery-results.json`
- `20260904-us-forensic-proof.json`

Exact message directory:
`docs/reports/messages/20260904-us-natural/`

---

# 28. Required gates

```text
TARGET_DATE = 2026-09-04
TARGET_MARKET = US
EXPECTED_STOCK_COHORT = 14
EXPECTED_TOTAL_USER_MESSAGES = 15

AUTHORITATIVE_PRIMARY_RUN_IDENTIFIED = PASS / FAIL
AUTHORITATIVE_BACKUP_RUN_IDENTIFIED = PASS / FAIL / NOT_PRESENT

PRIMARY_STARTED = YES / NO / UNKNOWN

PRIMARY_STATE_AT_0820 =
NOT_STARTED /
RUNNING_ACTIVE /
RUNNING_STALLED /
MODEL_INFERENCE_ACTIVE /
MODEL_RETRY_ACTIVE /
FINISHED_SUCCESS /
FINISHED_FAILURE /
PROCESS_MISSING /
UNKNOWN

PRIMARY_MISSING_FLAG_FOUND = YES / NO
PRIMARY_MISSING_FLAG_TIMESTAMP = ... / NOT_FOUND
PRIMARY_MISSING_FLAG_PREDICATE = ...

PRIMARY_CHECKER_LOOKUP_IDENTITY_MATCH = PASS / FAIL / UNKNOWN

PRIMARY_CHECKER_MISMATCH_CLASS =
NONE /
RUN_ID_MISMATCH /
GENERATION_MISMATCH /
PACKET_ID_MISMATCH /
PATH_NAMESPACE_MISMATCH /
HEARTBEAT_KEY_MISMATCH /
DELIVERY_KEY_MISMATCH /
OTHER /
UNKNOWN

BACKUP_TRIGGER_TIMESTAMP = ... / NOT_FOUND
BACKUP_TRIGGER_REASON = ...

PRIMARY_MODEL_STATE =
NOT_REACHED /
RUNNING /
COMPLETED /
FAILED_TLS /
FAILED_TIMEOUT /
FAILED_APP_SERVER /
FAILED_OTHER /
UNKNOWN

BACKUP_MODEL_STATE =
NOT_REACHED /
RUNNING /
COMPLETED /
FAILED_TLS /
FAILED_TIMEOUT /
FAILED_APP_SERVER /
FAILED_OTHER /
UNKNOWN /
NOT_PRESENT

NATURAL_US_TLS_STATUS =
NO_TLS_ERROR_OBSERVED /
UNKNOWN_ISSUER_OBSERVED /
OTHER_TLS_ERROR /
INSUFFICIENT_LOGS

SHADOW_US_INTERFERENCE =
NONE_CONFIRMED /
POSSIBLE /
CONFIRMED /
UNKNOWN

PRIMARY_CANDIDATE_TOTAL = ...
PRIMARY_ACCEPTED_TOTAL = ...
BACKUP_CANDIDATE_TOTAL = ... / NOT_PRESENT
BACKUP_ACCEPTED_TOTAL = ... / NOT_PRESENT

PRIMARY_COMPLETION_RELATIVE_TO_BACKUP =
PRIMARY_COMPLETED_BEFORE_BACKUP /
PRIMARY_COMPLETED_AFTER_BACKUP_TRIGGER /
PRIMARY_NEVER_COMPLETED /
BACKUP_COMPLETED_FIRST /
BOTH_COMPLETED /
UNKNOWN

PRIMARY_BACKUP_OVERLAP =
NO_OVERLAP /
OVERLAP_SAFE_DIFFERENT_GENERATION /
OVERLAP_SHARED_STATE /
OVERLAP_UNKNOWN

AI_MARKET_SENT = ...
AI_STOCK_SENT = ...
FALLBACK_MARKET_SENT = ...
FALLBACK_STOCK_SENT = ...
BACKUP_SENT = ...
DUPLICATE_SENT = ...

PRIMARY_LATE_RESULT_STATE =
NOT_APPLICABLE /
DISCARDED /
SUPERSEDED /
DEDUPED /
ACCEPTED_NOT_SENT /
DELIVERY_SUPPRESSED /
ORPHANED /
UNKNOWN

FIRST_MATERIAL_FAILURE_CLASS =
PRIMARY_PROCESS_FAILURE /
MODEL_TRANSPORT_FAILURE /
MODEL_TIMEOUT /
LIVENESS_FALSE_NEGATIVE /
ARTIFACT_READINESS_FALSE_NEGATIVE /
RUN_IDENTITY_MISMATCH /
GENERATION_IDENTITY_MISMATCH /
PATH_NAMESPACE_MISMATCH /
HEARTBEAT_STALE /
BACKUP_TRIGGER_TOO_EARLY /
DELIVERY_OWNERSHIP_FAILURE /
SELECTOR_SUPPRESSION /
OTHER /
UNKNOWN

REPLAY = 0 / NONZERO
MODEL_RERUN = 0 / NONZERO
PRODUCTION_MUTATION = 0 / NONZERO
TELEGRAM_RESEND = 0 / NONZERO
SCHEDULER_MODIFICATION = 0 / NONZERO
DB_MUTATION = 0 / NONZERO
MAIN_MERGE = 0 / NONZERO
```

---

# 29. Completion response

Return:

```text
AUTHORITATIVE US RUN =
...

PRIMARY AT 08:20 =
...

PRIMARY-MISSING FLAG =
...

BACKUP =
...

TIMELINE =
08:00 ...
08:20 ...
backup ...
primary completion ...
delivery ...

MODEL =
primary ...
backup ...

TLS =
natural US ...
shadow comparison ...

CANDIDATE / ACCEPTED =
...

DELIVERY =
...

WHAT USER RECEIVED =
...

PRIMARY LATE RESULT =
...

FIRST MATERIAL FAILURE =
...

ROOT CAUSE =
...

SECONDARY EFFECTS =
...

NO REPLAY / NO RERUN / NO MUTATION =
PASS

ZIP =
...
ZIP_SHA256 =
...
```

수리 제안은 별도 요청 전까지 하지 않는다.

---

# 30. Final principle

이번에 가장 중요한 구분은 다음 셋이다.

```text
primary process가 실제로 없었음
vs
primary가 살아 있었지만 아직 result artifact가 없었음
vs
checker가 잘못된 identity/key로 primary를 찾았음
```

먼저 이 셋을 확정하고 나서 다음 repair를 설계한다.
