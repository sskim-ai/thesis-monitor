# Primary / Backup Network Retry Proof

US and KR primary/backup tasks share the same `app.jobs.stock_decision` entry point and
`accepted_decision_v2_runtime.generate` implementation. No scheduler, task time, producer
ownership, packet claim, or fallback routing configuration changed.

The shared contract enforces:

- DNS/TCP/TLS preflight before a model subprocess;
- three readiness attempts at most;
- one Codex transport retry at most;
- one original timeout deadline across retries;
- no retry for deterministic runtime/path/schema/provider/rate-limit failures;
- safe suppression with an exact terminal reason.

Focused tests prove a transient app-server transport failure recovers on attempt two, while a
three-attempt DNS failure starts zero model subprocesses.

`PRIMARY_BACKUP_NETWORK_CONTRACT_IDENTICAL = PASS`

`MULTIPLE_PRODUCERS_OWN_PACKET = 0`

`UNBOUNDED_NETWORK_RETRY = 0`

`RETRY_STORM = 0`

