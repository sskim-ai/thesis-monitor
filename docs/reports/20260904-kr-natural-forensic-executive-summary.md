# 2026-09-04 KR Natural V2 Failure Forensic Executive Summary

## 결론

KR 자연 검토 전체가 실패한 것은 아니다. 일반 AI 모델은 시장 1개와 종목 8개를 모두 생성했고, 한 번의 수정으로 초기 validation 오류 17개를 모두 닫았다. 백엔드는 지원되는 `KR Pilot 5/5` AI-assisted compatibility 경로로 9/9 메시지를 정확히 한 번 전송했다.

Explicit V2는 그보다 앞에서 갈라졌다. `stock_decision` 명령 자체의 제한시간은 1,800초였지만, 바깥 primary 자동화가 실행 168초 만에 signed-in Codex CLI xhigh 프로세스를 중단했다. 그 결과 primary에 persisted V2 candidate와 claim-bound accepted V2 artifact가 하나도 남지 않았고, selector는 올바르게 `V2_DECISION_SUPPRESSED_SAFE`를 선택했다.

뒤이은 backup은 같은 operating code와 V2 model path를 약 28분간 기다려 8/8을 완료했다. 다만 authoritative 9-message delivery가 이미 승리했으므로 dedupe가 이를 archive-only로 유지했다. 이는 TLS나 모델 불능이 아니라 primary 호출자의 조기 중단이 원인이었음을 뒷받침한다.

## Gates

| Gate | Result |
|---|---|
| `TARGET_DATE` | `2026-09-04` |
| `TARGET_MARKET` | `KR` |
| `AUTHORITATIVE_KR_RUN_IDENTIFIED` | `PASS` |
| `MAIN_SHA` | `906b092749511dc42d5799ed335165819efee2ea` |
| `OPERATING_SHA` | `906b092749511dc42d5799ed335165819efee2ea` |
| `OPERATING_REPAIR_STATE` | `KR_US_INTEGRATED` |
| `KR_AI_MODEL_STATE` | `COMPLETED` |
| `KR_TLS_STATUS` | `NO_TLS_ERROR_OBSERVED` |
| `KR_PRIMARY_OWNERSHIP` | `HEALTHY_RETAINED` |
| `KR_CANDIDATE_TOTAL` | `9` |
| `KR_VALIDATED_TOTAL` | `9` |
| `KR_VALIDATION_ERROR_COUNT` | `17` |
| `KR_ACCEPTED_TOTAL` | `9` |
| `KR_ACCEPTED_STATE` | `COMPLETE_BUT_NOT_V2_ELIGIBLE` |
| `V2_ELIGIBLE` | `NO` |
| `V2_INELIGIBILITY_REASON` | `claim-bound decision-v2-accepted artifact unavailable after caller-interrupted generation` |
| `KR_PILOT_5OF5_PATH_FOUND` | `YES` |
| `KR_PILOT_5OF5_SEMANTICS` | `AI_ASSISTED_COMPATIBILITY_RENDERER_FIFTH_SUCCESS_OF_FIVE` |
| `V2_FIRST_DIVERGENCE` | `CANDIDATE_INCOMPLETE` |
| `REUSE_METADATA_INTEGRITY` | `NOT_APPLICABLE` |
| `TERMINAL_STATE_IMMUTABILITY` | `PASS` |
| `MARKET_FLOW_PROVENANCE` | `PASS` |
| `KR_ACCOUNTING_SAFETY` | `PASS` |
| `KR_ACCOUNTING_VALUATION_SAFETY` | `PASS` |
| `EXPLICIT_V2_AI_SENT` | `0` |
| `KR_PILOT_AI_ASSISTED_SENT` | `9` |
| `DETERMINISTIC_FALLBACK_SENT` | `0` |
| `DUPLICATE_SENT` | `0` |
| `EXACTLY_ONCE` | `PASS` |
| `FIRST_MATERIAL_FAILURE_CLASS` | `CANDIDATE_GENERATION_FAILURE` |
| `MODEL_RERUN` | `0` |
| `REPLAY` | `0` |
| `DATA_REFETCH` | `0` |
| `TELEGRAM_RESEND` | `0` |
| `PRODUCTION_MUTATION` | `0` |
| `SCHEDULER_CHANGE` | `0` |
| `DB_MUTATION` | `0` |
| `MAIN_MERGE` | `0` |

## Repair Handoff

이번 작업에서는 수리하지 않았다. 다음 bounded task는 [root cause](20260904-kr-natural-root-cause.md)에 적은 orchestration wait contract와 interruption terminal-receipt 처리만 대상으로 삼아야 한다.
