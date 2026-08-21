# Night-Futures Observer Isolation

## Schedule

The current lifecycle is production collection through 08:20, delivery retries through 08:30, and
fallback at 08:40 KST. The observer therefore runs at 08:45 and, only if still unresolved, 09:15.
This is the smallest bounded window that distinguishes shortly-after-deadline readiness from a
meaningfully later or still-absent state without overlapping production.

## Isolation Proof

The observer imports the KRX provider and telemetry service only. It imports no database Session,
morning gate, market-summary writer, packet builder, notifier, fallback, or Telegram service.
Tests show a ready 08:45 result produces a telemetry receipt and suppresses the 09:15 provider call.
An empty 08:45 result permits exactly one 09:15 horizon call and records
`NOT_READY_WITHIN_OBSERVER_HORIZON`.

Output counters are fixed at zero for production market-summary writes, Telegram writes, and
production effect. The observer LaunchAgent has no `RunAtLoad`; deployment does not manually invoke
the provider.

The 08:30 backup path itself has no night-futures provider call. Attempt records state
`backup_path_provider_attempted=false`; no synthetic production query was added.
