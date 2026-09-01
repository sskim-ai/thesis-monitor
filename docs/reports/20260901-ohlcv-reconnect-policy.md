# OHLCV Reconnect Policy

- Attempts: existing `monitor_retry_attempts`, minimum 1.
- Delay: existing base delay, exponential backoff, deterministic request jitter.
- Deadline: bounded by the client request deadline.
- Retryable: connect error, connect/read timeout, remote protocol error, HTTP 5xx.
- Not retryable: authentication, semantic validation, malformed payload, non-5xx HTTP errors.
- Exhaustion: freeze `UNAVAILABLE` for that subject; continue peers.

Fault controls proved first-request ConnectError recovery and bounded connect/read timeout
exhaustion. Health-probe attempts are additionally capped at five.

`UNBOUNDED_OHLCV_RECONNECT = 0`

`OHLCV_SERVICE_RESTART_RECOVERY = PASS`
