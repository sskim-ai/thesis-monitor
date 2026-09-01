# Track A — Local OHLCV Root Cause + Connection Lifecycle

Reproduce the exact `httpcore.ConnectError` from run-49.

Map:
- client module/function
- resolved host/port/path
- config/env source
- service/process owner
- Price Structure/source-monitor OHLCV paths
- startup order
- connection pool / timeout / retry behavior

Do not assume the lower-level cause.

Fix the actual cause.

Add:
- data-path health check
- bounded readiness wait
- bounded reconnect/backoff
- service-restart recovery test

Output one primary root-cause classification plus evidence.
