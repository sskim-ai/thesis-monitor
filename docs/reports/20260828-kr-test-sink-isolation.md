# KR Test Sink Isolation

No test recipient was selected, so delivery remains fail-closed before namespace or sender use.

| Gate | Result |
| --- | --- |
| Namespace | `TEST_ONLY / KR_FINAL_PREENABLE / NON_PRODUCTION` |
| `TEST_PRODUCTION_SINK_COLLISION` | `0` |
| `TEST_PRODUCTION_INTENT_COLLISION` | `0` |
| `PRODUCTION_DELIVERY_INTENT_CREATED` | `0` |
| `TEST_MESSAGE_SENT_TO_PRODUCTION_RECIPIENT` | `0` |
| Raw test ID in log | `0` |
| Raw production ID in log | `0` |

Zero collision counters do not establish availability. `TEST_SINK_AVAILABLE` remains `NO`.
