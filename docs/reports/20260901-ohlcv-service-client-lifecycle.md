# OHLCV Service And Client Lifecycle

The service LaunchAgent is host-managed and healthy. The repaired client creates a bounded request
per timeframe and classifies retryable connection, timeout, remote protocol, and 5xx failures.
Non-retryable HTTP and payload failures stop immediately for the affected request.

The service health probe separately records process, transport, data endpoint, and expected daily
bar. The observed production-like probe was `READY` on attempt 1 with daily `2026-08-31`.

Decision generation is no longer coupled to service lifecycle. A restart during source acquisition
can recover within bounds; a restart after packet freeze has no effect on V2 preparation.

`UNBOUNDED_SERVICE_STARTUP_WAIT = 0`
