# thesis-monitor — 2026-09-04 KR Natural V2 Failure Read-Only Forensics

## 목적
오늘 KR 자연 메시지가 `KR Pilot 5/5`로 전송된 이유를 읽기 전용으로 추적한다.
AI 추론 실패와 V2 validation/selector/renderer/delivery 실패를 분리한다.

## 1. 절대 금지
MODEL_RERUN=0
REPLAY=0
DATA_REFETCH=0
TELEGRAM_RESEND=0
PRODUCTION_MUTATION=0
SCHEDULER_CHANGE=0
DB_MUTATION=0
MAIN_MERGE=0

## 2. 첫 확인 — 오늘 실제 operating SHA
반드시 추출:
- MAIN_SHA
- OPERATING_SHA
- entrypoint revision
- selector version
- renderer version
- delivery orchestration version
- analysis policy version

비교 대상:
- KR repair final: `90cc52231c7343056c853c355ea90dfea10de25b`
- US repair final: `deb4dc511aafa6e435b0af00436d690e2e498c0b`
- KR+US integration SHA: 이미 존재하면 exact SHA 확인

분류:
OPERATING_REPAIR_STATE =
OLD_PRE_REPAIR /
KR_REPAIR_ONLY /
US_REPAIR_ONLY /
KR_US_INTEGRATED /
UNKNOWN

## 3. Authoritative KR run lineage
오늘 KR 자연 실행의:
- scheduler/job
- primary AI worker
- Codex/app-server
- claim/lease owner
- backup/retry/fallback
- selector/V2 gate
- renderer
- delivery worker

각각:
run_id, parent_run_id, packet_id, analysis/candidate/accepted/delivery generation,
scheduled/start/finish, heartbeat, fencing token, exit code, operating SHA.

## 4. 단일 타임라인
KR scheduler start부터 Telegram terminal까지:
source ready
→ packet
→ AI-consumability
→ claim
→ TLS/app-server/model
→ candidate
→ validation
→ correction
→ accepted
→ V2 eligibility
→ renderer selection
→ delivery pending/claim/send
→ backup/fallback
을 초 단위로 재구성한다.

## 5. AI 추론 자체 성공 여부
시장/종목 각각:
model reached?
TLS?
model result count?
candidate count?
candidate SHA?
elapsed?
retry?

KR_AI_MODEL_STATE =
NOT_REACHED /
COMPLETED /
FAILED_TLS /
FAILED_TIMEOUT /
FAILED_APP_SERVER /
FAILED_OTHER /
UNKNOWN

candidate가 존재하면 explicit V2가 안 갔다는 이유만으로 AI 실패라고 쓰지 않는다.

## 6. TLS 회귀 확인
오늘 KR 로그에서:
UnknownIssuer
TLS_CERTIFICATE_UNKNOWN_ISSUER
certificate verify
SSL/x509/issuer
DNS/timeout
검색.

KR_TLS_STATUS =
NO_TLS_ERROR_OBSERVED /
UNKNOWN_ISSUER_OBSERVED /
OTHER_TLS_ERROR /
INSUFFICIENT_LOGS

승인된 root-owned system CA 전달이 실제 KR natural runtime에 적용됐는지도 확인.
secret/cert contents는 노출 금지.

## 7. Claim / lease / backup
추출:
claim acquired
lease duration
heartbeat renewal count
last heartbeat
backup schedule
backup reclaim count
fencing token transitions
stale write rejection

KR_PRIMARY_OWNERSHIP =
HEALTHY_RETAINED /
RECLAIMED_WHILE_HEALTHY /
RECLAIMED_AFTER_STALE /
NO_CLAIM /
UNKNOWN

## 8. Candidate inventory
시장 + 모든 KR 종목:
candidate 존재?
structured V2 candidate?
legacy/pilot candidate?
candidate generation/SHA/persisted_at?

authoritative monitored universe 기준으로 총수를 계산한다.

## 9. Validation inventory
generation별:
validation PASS/FAIL
error count
error classes
correction attempt
corrected candidate SHA
corrected error count

분리:
market
stock
message quality
numeric/provenance
valuation
accounting
renderer/template

## 10. Accepted-plan
추출:
accepted market
accepted stocks
accepted total
accepted generation/SHA
accepted persisted_at
claim-bound final artifact
completion receipt

KR_ACCEPTED_STATE =
NONE /
PARTIAL /
COMPLETE /
COMPLETE_BUT_NOT_V2_ELIGIBLE /
UNKNOWN

## 11. Explicit V2 eligibility
정확한 selector/canary predicate를 찾는다.

필수:
required artifact
accepted count
claim owner requirement
completion receipt
message-quality requirement
renderer readiness

오늘:
V2_ELIGIBLE=true/false
reason codes
failed requirement

## 12. `KR Pilot 5/5`의 정확한 의미
이 문자열을 출력하는 함수/파일을 찾고 다음 중 무엇인지 확정:
legacy renderer
AI-assisted compatibility renderer
partial V2 canary
deterministic fallback
selector suppression
other

반드시:
- trigger predicate
- input artifact
- accepted AI text 사용 여부
- fallback인지 supported compatibility mode인지

`5/5`가 무엇을 의미하는지도 소스에서 확인. 추측 금지.

## 13. Explicit V2 vs Pilot divergence
표:
Stage | Explicit V2 | KR Pilot 5/5 | Today's owner
candidate
validation
accepted
selector
renderer
delivery

V2_FIRST_DIVERGENCE =
OPERATING_SHA_MISSING_REPAIR /
AI_MODEL_FAILURE /
CANDIDATE_INCOMPLETE /
VALIDATION_FAILURE /
CORRECTION_FAILURE /
ACCEPTED_INCOMPLETE /
CLAIM_BOUND_FINAL_ARTIFACT_MISSING /
COMPLETION_RECEIPT_MISSING /
SELECTOR_SUPPRESSION /
RENDERER_NOT_READY /
DELIVERY_OWNER_MISMATCH /
BACKUP_REUSE_METADATA_LOSS /
FALLBACK_POLICY /
OTHER /
UNKNOWN

## 14. Backup/reuse metadata 회귀
이전 KR 장애 클래스 재검사:
analysis_action=reuse?
backup packet reuse?
accepted-plan reuse?
delivery-state reuse?
selector metadata copied?
claim-bound completion metadata copied?

primary vs backup/reuse:
packet_id
candidate gen
accepted gen
V2 metadata
delivery gen
claim owner
completion receipt

REUSE_METADATA_INTEGRITY =
PASS / FAIL / NOT_APPLICABLE / UNKNOWN

## 15. Late validation overwrite
terminal send 뒤:
late validator write
late backup write
canonical result overwrite
delivery state regression
여부 확인.

TERMINAL_STATE_IMMUTABILITY =
PASS / FAIL / UNKNOWN

## 16. 실제 delivered mode map
각 Telegram 메시지를:
EXPLICIT_V2_AI /
KR_PILOT_AI_ASSISTED /
LEGACY_AI_ASSISTED /
DETERMINISTIC_FALLBACK /
BACKUP_AI /
UNKNOWN

으로 매핑.
sent_at, source generation, renderer, delivery receipt 기록.

## 17. exact message capture
시장 + 모든 KR 종목 raw UTF-8 저장.
각각 SHA-256, sent_at, source generation, renderer mode 기록.

## 18. 시장 메시지 semantic audit
관찰 메시지의:
`업종 상대 약세`에 +0.28%, +0.34%가 포함됨.

이것이:
- 절대 하락
- 지수/벤치마크 대비 상대 부진
중 무엇을 의미하는지 field semantics 확인.

양수 절대수익률이라도 상대 약세일 수 있으므로 contract가 그렇게 정의하면 contradiction으로 처리하지 않는다.

또:
외국인/기관 양시장 순매수
개인 양시장 순매도
의 exact fact_id/field/session_date/aggregation basis 추적.

MARKET_FLOW_PROVENANCE = PASS / FAIL / UNKNOWN

## 19. 000660 provenance audit
사용자 메시지의:
- HBM4 / AI 서버 수요
- 재고 vs 원가 규모
- ASP/제품 믹스 caveat
- 정규장 종가
- 지지구간
- 월봉 진행중 볼린저 저항
- 외국인/기관 1d/5d/20d
를 각각 fact_id / source field / numeric binding / renderer owner로 추적.

목적은 종목 재분석이 아니라 V2 validation/renderer ownership 실패 확인.

## 20. KR accounting/valuation safety
다음 위반 여부:
official provisional attribution
parent/common basis
EPS/BVPS denominator safety
PER/PBR/fPER/fPBR basis
KRW/security basis

blocked subject/error가 있으면 정확히 기록.
없는 숫자 생성 금지.

## 21. Price / supply provenance
000660의 current close, support, monthly Bollinger가 실제 packet/registry에 존재했는지 확인.
월봉 진행중 값이면 provisional wording contract 확인.

수급:
foreign/institution 1d/5d/20d
as_of_date
qty/value semantics
renderer labels
확인.

## 22. Message-quality failures
있다면 전부 추출:
template quality
semantic contradiction
unsupported wording
repetition
mandatory trade language
numeric provenance
unknown coverage
typed valuation coverage
price-token boundary

false positive 여부도 분류하되 수리하지 않는다.

## 23. Count reconciliation
monitored KR
candidate
validated
accepted
V2 eligible
Pilot rendered
fallback
Telegram sent
총수를 단계별로 맞춘다.

## 24. Exactly-once
duplicate
dedupe suppressed
fallback
backup send
late AI send
확인.

EXACTLY_ONCE = PASS / FAIL / UNKNOWN

## 25. 단계별 자연 proof
한 줄 PASS/FAIL로 끝내지 말고:
transport
claim/lease
candidate
validation
accepted
V2 selector
renderer
delivery
각각 상태를 기록.

## 26. 최초 material failure
FIRST_MATERIAL_FAILURE_CLASS =
OPERATING_SHA_MISSING_REPAIR /
TLS_TRANSPORT_FAILURE /
CLAIM_LEASE_OWNERSHIP_FAILURE /
CANDIDATE_GENERATION_FAILURE /
VALIDATOR_TRUE_REJECTION /
VALIDATOR_FALSE_POSITIVE /
CORRECTION_CONTEXT_FAILURE /
ACCEPTED_PLAN_INCOMPLETE /
CLAIM_BOUND_FINAL_ARTIFACT_MISSING /
COMPLETION_RECEIPT_MISSING /
SELECTOR_SUPPRESSION /
RENDERER_OWNERSHIP_FAILURE /
DELIVERY_METADATA_LOSS /
BACKUP_REUSE_METADATA_LOSS /
TERMINAL_STATE_OVERWRITE /
FALLBACK_POLICY /
OTHER /
UNKNOWN

그리고:
PRIMARY_ROOT_CAUSE
SECONDARY_EFFECTS
NOT_CAUSAL_OBSERVATIONS
분리.

## 27. 이번 작업에서는 수리 금지
root cause를 찾더라도:
code patch
selector relaxation
validator relaxation
renderer change
model rerun
resend
main merge
금지.

다음 repair task를 위한 exact file/function/state-key만 기록.

## 28. Required reports
1. docs/reports/20260904-kr-natural-operating-lineage.md
2. docs/reports/20260904-kr-natural-run-lineage.md
3. docs/reports/20260904-kr-natural-event-timeline.md
4. docs/reports/20260904-kr-natural-ai-model-runtime.md
5. docs/reports/20260904-kr-natural-tls-claim-lease-state.md
6. docs/reports/20260904-kr-natural-candidate-inventory.md
7. docs/reports/20260904-kr-natural-validation-errors.md
8. docs/reports/20260904-kr-natural-accepted-plan-state.md
9. docs/reports/20260904-kr-natural-v2-selector-state.md
10. docs/reports/20260904-kr-pilot-5of5-renderer-path.md
11. docs/reports/20260904-kr-primary-backup-reuse-integrity.md
12. docs/reports/20260904-kr-terminal-state-immutability.md
13. docs/reports/20260904-kr-market-message-semantic-audit.md
14. docs/reports/20260904-kr-000660-message-provenance.md
15. docs/reports/20260904-kr-exact-delivery-results.md
16. docs/reports/20260904-kr-v2-first-divergence.md
17. docs/reports/20260904-kr-natural-root-cause.md
18. docs/reports/20260904-kr-natural-artifact-index.md
19. docs/reports/20260904-kr-natural-forensic-executive-summary.md

Machine-readable:
20260904-kr-run-lineage.json
20260904-kr-event-timeline.json
20260904-kr-pipeline-stages.json
20260904-kr-validation-errors.json
20260904-kr-v2-selector.json
20260904-kr-delivery-results.json
20260904-kr-forensic-proof.json

Exact messages:
docs/reports/messages/20260904-kr-natural/

## 29. Required gates
TARGET_DATE = 2026-09-04
TARGET_MARKET = KR

AUTHORITATIVE_KR_RUN_IDENTIFIED = PASS / FAIL
MAIN_SHA = ...
OPERATING_SHA = ...

OPERATING_REPAIR_STATE =
OLD_PRE_REPAIR /
KR_REPAIR_ONLY /
US_REPAIR_ONLY /
KR_US_INTEGRATED /
UNKNOWN

KR_AI_MODEL_STATE =
NOT_REACHED /
COMPLETED /
FAILED_TLS /
FAILED_TIMEOUT /
FAILED_APP_SERVER /
FAILED_OTHER /
UNKNOWN

KR_TLS_STATUS =
NO_TLS_ERROR_OBSERVED /
UNKNOWN_ISSUER_OBSERVED /
OTHER_TLS_ERROR /
INSUFFICIENT_LOGS

KR_PRIMARY_OWNERSHIP =
HEALTHY_RETAINED /
RECLAIMED_WHILE_HEALTHY /
RECLAIMED_AFTER_STALE /
NO_CLAIM /
UNKNOWN

KR_CANDIDATE_TOTAL = ...
KR_VALIDATED_TOTAL = ...
KR_VALIDATION_ERROR_COUNT = ...
KR_ACCEPTED_TOTAL = ...

KR_ACCEPTED_STATE =
NONE /
PARTIAL /
COMPLETE /
COMPLETE_BUT_NOT_V2_ELIGIBLE /
UNKNOWN

V2_ELIGIBLE = YES / NO / UNKNOWN
V2_INELIGIBILITY_REASON = ...

KR_PILOT_5OF5_PATH_FOUND = YES / NO
KR_PILOT_5OF5_SEMANTICS = ...

V2_FIRST_DIVERGENCE =
OPERATING_SHA_MISSING_REPAIR /
AI_MODEL_FAILURE /
CANDIDATE_INCOMPLETE /
VALIDATION_FAILURE /
CORRECTION_FAILURE /
ACCEPTED_INCOMPLETE /
CLAIM_BOUND_FINAL_ARTIFACT_MISSING /
COMPLETION_RECEIPT_MISSING /
SELECTOR_SUPPRESSION /
RENDERER_NOT_READY /
DELIVERY_OWNER_MISMATCH /
BACKUP_REUSE_METADATA_LOSS /
FALLBACK_POLICY /
OTHER /
UNKNOWN

REUSE_METADATA_INTEGRITY = PASS / FAIL / NOT_APPLICABLE / UNKNOWN
TERMINAL_STATE_IMMUTABILITY = PASS / FAIL / UNKNOWN
MARKET_FLOW_PROVENANCE = PASS / FAIL / UNKNOWN
KR_ACCOUNTING_SAFETY = PASS / FAIL / UNKNOWN
KR_ACCOUNTING_VALUATION_SAFETY = PASS / FAIL / UNKNOWN

EXPLICIT_V2_AI_SENT = ...
KR_PILOT_AI_ASSISTED_SENT = ...
DETERMINISTIC_FALLBACK_SENT = ...
DUPLICATE_SENT = ...
EXACTLY_ONCE = PASS / FAIL / UNKNOWN

FIRST_MATERIAL_FAILURE_CLASS =
OPERATING_SHA_MISSING_REPAIR /
TLS_TRANSPORT_FAILURE /
CLAIM_LEASE_OWNERSHIP_FAILURE /
CANDIDATE_GENERATION_FAILURE /
VALIDATOR_TRUE_REJECTION /
VALIDATOR_FALSE_POSITIVE /
CORRECTION_CONTEXT_FAILURE /
ACCEPTED_PLAN_INCOMPLETE /
CLAIM_BOUND_FINAL_ARTIFACT_MISSING /
COMPLETION_RECEIPT_MISSING /
SELECTOR_SUPPRESSION /
RENDERER_OWNERSHIP_FAILURE /
DELIVERY_METADATA_LOSS /
BACKUP_REUSE_METADATA_LOSS /
TERMINAL_STATE_OVERWRITE /
FALLBACK_POLICY /
OTHER /
UNKNOWN

MODEL_RERUN = 0 / NONZERO
REPLAY = 0 / NONZERO
DATA_REFETCH = 0 / NONZERO
TELEGRAM_RESEND = 0 / NONZERO
PRODUCTION_MUTATION = 0 / NONZERO
SCHEDULER_CHANGE = 0 / NONZERO
DB_MUTATION = 0 / NONZERO
MAIN_MERGE = 0 / NONZERO

## 30. Completion response
AUTHORITATIVE KR RUN =
...

OPERATING CODE =
...

TIMELINE =
...

AI MODEL =
...

TLS =
...

CLAIM / BACKUP =
...

CANDIDATE =
...

VALIDATION =
...

ACCEPTED =
...

V2 SELECTOR =
...

KR PILOT 5/5 =
...

DELIVERY =
...

MARKET MESSAGE AUDIT =
...

000660 AUDIT =
...

FIRST MATERIAL FAILURE =
...

ROOT CAUSE =
...

SECONDARY EFFECTS =
...

NEXT REPAIR TARGETS =
exact file/function/state-key only

NO RERUN / NO MUTATION = PASS

ZIP =
...
ZIP_SHA256 =
...

## 31. Final principle
`KR Pilot 5/5`라는 표시만으로 AI 실패인지 V2 실패인지 알 수 없다.

반드시 아래를 구분한다:

AI inference failed
vs
AI candidate existed but validation failed
vs
accepted AI existed but V2 selector suppressed it
vs
V2 eligible but renderer/delivery chose Pilot
vs
old operating code never contained the intended V2 path

가장 먼저 갈라진 지점을 persisted facts로 확정한 뒤 그 층만 수리한다.
