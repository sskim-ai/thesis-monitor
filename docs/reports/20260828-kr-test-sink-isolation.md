# KR Test Sink Isolation

| Gate | Result |
| --- | --- |
| Namespace | `TEST_ONLY_NON_PRODUCTION` |
| Test alias | `test:6d6e2ff463bf` |
| Production alias | `production:7937bea5b823` |
| Recipient collision | `0` |
| Production intent collision | `0` |
| Production-recipient test send | `0` |
| Production delivery intent | `0` |

The isolated audit sender accepts only the canonical test key, refuses an existing receipt, uses
one network attempt per payload, and never calls the production notifier or delivery database.
