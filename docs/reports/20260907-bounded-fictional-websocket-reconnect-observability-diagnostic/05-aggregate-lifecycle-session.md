# Aggregate Lifecycle, Retry, and Session Comparison

- Execution: `COMPLETED_BOUNDED_BUDGET`
- WebSocket disconnect signals: 0
- CLI retry signals: 0
- Disconnect then success: 0
- Disconnect then watchdog timeout: 0
- Distinct observed sessions: 3
- Distinct observed namespace hashes: 3
- Root cause confirmed: `false`
- Runtime reliability: `NOT_ESTABLISHED`

Observed CLI retry signals do not reveal upstream request-attempt or acceptance counts; both remain unknown/unavailable.
