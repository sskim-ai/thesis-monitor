# US Exchange Breadth Production Readiness

`US_EXCHANGE_BREADTH_PRODUCTION_READY = YES`

| Gate | Result |
| --- | --- |
| NASDAQ_OFFICIAL_BREADTH_CONTRACT | PASS |
| NASDAQ_BREADTH | PARTIAL |
| NYSE_BREADTH_SOURCE | UNAVAILABLE |
| NYSE_BREADTH | UNAVAILABLE |
| US_EXCHANGE_BREADTH | PARTIAL |
| US_EXCHANGE_BREADTH_VALUE_ADD | PASS |
| US_BREADTH_RUN37_REPLAY | PASS |
| US_BREADTH_MESSAGE_VALIDATION | PASS |
| US_BREADTH_CANARY_SIMULATION | PASS |
| US_EXCHANGE_BREADTH_PRODUCTION_READY | YES |

The safe v1 state is Nasdaq-only partial breadth. Exact run-37 breadth is suppressed because the
official row is not published; this is a P2 publication-lag observation, not a reason to inject an
older session. NYSE stays unavailable. Open P0: 0. Open material P1: 0.

Production readiness covers the official source adapter and fail-open sidecar. User-facing value
still requires a natural exact-session canary; no manual run or message is used as a substitute.
