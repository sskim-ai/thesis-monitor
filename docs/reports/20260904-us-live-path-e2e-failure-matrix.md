# 2026-09-04 US Live-Path E2E Failure Matrix

| Scenario | Evidence | Result |
|---|---|---|
| Compact `UnknownIssuer` | classifier-level injected log; one subprocess attempt | specific TLS class, retry storm `0` |
| Transient app-server transport | first call fails, second succeeds | bounded retry preserved |
| Network preflight failure | readiness fails before subprocess | model subprocess starts `0` |
| Blocking model call | heartbeat thread runs while caller sleeps | renewals continue |
| Foreign owner/token renewal | mismatched owner and token | `ownership_lost` |
| Healthy primary at backup window | fresh renewed lease | backup no-op |
| Primary death/stall | heartbeat stops and lease expires | backup reclaims with generation 2 |
| Stale primary finalization | backup owns new fence | `stale_claim_output` |
| Validation rejected | fallback deadline remains eligible | deterministic fallback preserved |
| Fallback wins before late AI | late AI completes after fallback | `archive_only`, send `0` |
| Duplicate AI delivery entry | same packet entered again | additional send `0` |
| First real E2E quality failure | structural templates counted as substantive | fail-closed, TEST send `0` |
| Repaired exact E2E | typed owner/semantic/template match | TEST `15/15`, fallback `0`, duplicate `0` |

Focused controlled matrix: `28 passed`; explicit fallback/duplicate matrix: `3 passed`.
