# Transport Runtime Forensic

The FIRST run stopped before any model process was spawned.

| Field | Value |
| --- | --- |
| Surface stop reason | `transport_receipt_missing` |
| Confirmed root cause | `LIVE_WORKLOAD_GUARD_PS_PERMISSION_DENIED` |
| Root exception | `PermissionError: [Errno 1] Operation not permitted: 'ps'` |
| Prompt identity parse | PASS |
| Failure stage | PRE_SPAWN |
| Model invocations | 0 |
| Subject outputs | 0 |
| Transport receipts | 0 |
| Retries | 0 |
| Mid-run hotfixes | 0 |
| Holdout exposure | UNEXPOSED |

The guard calls `ps -axo command=` before writing its coexistence event and before
delegating to the transport adapter. The execution sandbox denied that process
inspection. Context preservation then raised `transport_receipt_missing`, masking
the original pre-spawn exception.

The instruction's stop-on-first-failure rule was honored. FIRST and A/B/C were not
retried. A subsequent run requires a separately frozen repair that preserves the
original exception and makes workload observation compatible with the execution
sandbox.
