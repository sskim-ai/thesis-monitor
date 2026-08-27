# KR Final Test Sink Isolation

The configured production recipient is present only as a one-way alias. No test recipient exists,
so collision comparison is fail-closed before delivery rather than bypassed with production.

| Gate | Result |
| --- | --- |
| Namespace | `TEST_ONLY_NON_PRODUCTION` |
| `TEST_PRODUCTION_SINK_COLLISION` | `0` |
| `TEST_PRODUCTION_INTENT_COLLISION` | `0` |
| `TEST_MESSAGE_SENT_TO_PRODUCTION_RECIPIENT` | `0` |
| `PRODUCTION_DELIVERY_INTENT_CREATED` | `0` |
| Raw recipient IDs exposed | `0` |

The zero collision counters do not mean a test route is available. Availability remains `NO`, so
all sends are prohibited.
