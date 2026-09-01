# OHLCV Connection Retry And Recovery

Contract: `ohlcv-connection-recovery-v2`

## Health Contract

Health distinguishes four questions: process alive, loopback transport reachable, data endpoint
functional, and expected completed daily bar available. The resulting service state is `READY`,
`DEGRADED`, or `UNAVAILABLE`.

## Retry Policy

`OhlcvClient` retries only `ConnectError`, connect/read timeout, remote protocol errors, and server
5xx responses. Attempts use existing configured bounds, exponential backoff, deterministic jitter,
and a total deadline. Authentication, validation, and other non-retryable failures fail closed.

Telemetry records request, success, retry, connection-error, timeout, server-error, non-retryable,
cache-use, and failure classes. There is no unbounded startup wait or reconnect loop.

## Recovery Boundary

The source monitor may recover from a short restart and then freeze a full packet-owned context.
If recovery is exhausted, it freezes an unavailable subject context. The V2 decision stage never
reconnects because it performs no OHLCV HTTP call.

Run-49 reproduction proved the service itself and host/port configuration were healthy while the
restricted decision process could not access loopback. Packet ownership removes that namespace
boundary from decision generation; retry remains an acquisition-time resilience control.
