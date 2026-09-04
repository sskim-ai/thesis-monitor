# 2026-09-04 KR Natural Root Cause

## First Material Failure

`FIRST_MATERIAL_FAILURE_CLASS=CANDIDATE_GENERATION_FAILURE`

Primary 자동화는 16:25:31.825 KST에 기본 제한시간 1,800초로 `stock_decision generate`를 시작했다. 30초 poll을 네 번 수행한 뒤, 실행 168.326초 만인 16:28:20.151에 직접 `Ctrl-C`를 보냈다. Child process는 exit 1로 끝났고 wrapper에는 `OTHER_TRANSPORT_FAILURE:attempts=1`이 남았다.

## Primary Root Cause

Orchestration layer의 임의 대기 결정이 command-owned bounded wait보다 먼저 프로세스를 끊었다. V2 xhigh 생성이 batch 1 도중 중단되어 authoritative packet에는 claim-bound V2 candidate batch, accepted artifact, completion receipt가 생성되지 않았다.

## Secondary Effects

1. Explicit V2 selector는 stock V2 block을 올바르게 fail-closed 억제했다.
2. 일반 accepted AI content는 지원되는 Pilot 5/5 compatibility 경로로 계속 처리됐다.
3. 직접 `generate()`를 호출한 wrapper는 interruption을 traceback으로 종료하고 terminal receipt를 남기지 않아 primary heartbeat completion metadata의 정확한 수치를 확인할 수 없게 했다.

## Not Causal

- Operating SHA에는 KR/US repair가 이미 통합돼 있었다.
- TLS unknown-issuer 또는 app-server outage는 관찰되지 않았다.
- 일반 candidate의 validation 오류 17개는 한 번 수정 후 통과했다.
- Sandbox warning은 성공한 backup V2에도 동일하게 존재했다.
- Backup/reuse metadata는 authoritative terminal state를 덮어쓰지 않았다.

## Next Repair Targets

이번 작업에서는 수리하지 않았다. 다음 대상만 기록한다.

- `.agents/skills/thesis-monitor-daily-review/SKILL.md`: workflow step 6 bounded canary wait contract
- `app/jobs/stock_decision.py::_run`
- `app/jobs/accepted_decision_v2_runtime.py::generate`
- `app/jobs/accepted_decision_v2_runtime.py::_safe_suppression_receipt`
- State key `accepted-v2-generation-stage-v1`
- State key `v2-accepted-production-receipt-v1`
