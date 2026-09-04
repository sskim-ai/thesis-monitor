# 2026-09-04 US Natural TLS / Lease / Validator Repair Readiness

## Required gates

| Gate | Result |
|---|---|
| `CURRENT_ABC_TERMINAL` | `PASS` |
| `CURRENT_ABC_MODEL_PROCESSES` | `0` |
| `CURRENT_ABC_APP_SERVER_RELEASED` | `PASS` |
| `BASE_SHA` | `5d5f3363d3a762b62698943b1feb4fa121d0d0f9` |
| `BASE_CONTAINS_NATURAL_OPERATING_REVISION` | `PASS` |
| `SHADOW_ONLY_DECISION_CONTRACT_IMPORTED` | `0` |
| `TLS_ROOT_CAUSE_IDENTIFIED` | `PASS` |
| `TLS_VERIFICATION_BYPASS` | `0` |
| `TLS_PREFLIGHT_MODEL_RESULT_COUNT` | `1` |
| `TLS_UNKNOWN_ISSUER` | `0` |
| `UNKNOWN_ISSUER_CLASSIFICATION` | `TLS_CERTIFICATE_UNKNOWN_ISSUER` |
| `UNKNOWN_ISSUER_RETRY_STORM` | `0` |
| `CLAIM_RENEWAL_IMPLEMENTED` | `PASS` |
| `CLAIM_FENCING_TOKEN` | `PASS` |
| `HEARTBEAT_SURVIVES_BLOCKING_MODEL_CALL` | `PASS` |
| `FRESH_PRIMARY_BLOCKS_BACKUP_RECLAIM` | `PASS` |
| `STALE_PRIMARY_ALLOWS_BACKUP_RECLAIM` | `PASS` |
| `STALE_PRIMARY_FINALIZATION_REJECTED` | `PASS` |
| `FALLBACK_LATE_AI_DUPLICATE` | `0` |
| `VALIDATOR_INCIDENT_ERRORS_FOUND` | `22` |
| `VALIDATOR_INCIDENT_ERRORS_CLASSIFIED` | `22` |
| `TICKER_SPECIFIC_VALIDATOR_EXCEPTION` | `0` |
| `VALIDATOR_GLOBAL_WEAKENING` | `0` |
| `UNSUPPORTED_NUMERIC_ACCEPTED` | `0` |
| `ADR_SECURITY_BASIS_SAFETY` | `PASS` |
| `US_TEST_E2E_PRIMARY_ACCEPTED` | `15` |
| `US_TEST_E2E_AI_MARKET_SENT` | `1` |
| `US_TEST_E2E_AI_STOCK_SENT` | `14` |
| `US_TEST_E2E_FALLBACK_SENT` | `0` |
| `US_TEST_E2E_DUPLICATE_SENT` | `0` |
| `US_TEST_E2E_BACKUP_WHILE_PRIMARY_HEALTHY` | `SAFE_NOOP_PRIMARY_ACTIVE` |
| `US_TEST_E2E_BACKUP_AFTER_PRIMARY_DEATH` | `PASS` |
| `STRUCTURED_AUTONOMY_PRODUCTION_PROMOTION` | `0` |
| `PRODUCTION_TELEGRAM_SEND` | `0` |
| `PRODUCTION_SCHEDULER_CHANGE` | `0` |
| `PRODUCTION_DB_MUTATION` | `0` |
| `MAIN_MERGE` | `0` |

## Validation

- Frozen 22-error replay: `PASS`, repaired errors `0`.
- Controlled TLS/lease/validator matrix: `28 passed`.
- Fallback/late-AI/duplicate matrix: `3 passed`.
- Full pytest: `2180 passed`, one upstream deprecation warning.
- Ruff: `PASS`.
- `git diff --check`: `PASS`.
- Knowledge checksum/runtime parity tests: `PASS`.
- Public Action OpenAPI: version `0.4.5`; operation IDs `20/20` unique.
- Implementation SHA Actions: `1a50853` `PASS`.
- Bounded quality repair SHA Actions: `21296c0` `PASS`.
- Secret scan: no chat ID value, API token, private key, or certificate body added.

Open P0: `0`. Open P1: `0`.

`READINESS = READY_FOR_NATURAL_PROOF`

This is the strongest allowed verdict. Natural production proof remains separate and requires primary transport success, accepted `15/15`, TEST-independent production delivery ownership, fallback `0`, duplicate `0`, and no fresh-primary reclaim.
