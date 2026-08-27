# KR Test Sink Configuration

Canonical secret key `TELEGRAM_TEST_CHAT_ID` is configured outside git. Raw IDs and the bot token
are absent from reports, git diff, and receipt artifacts.

| Field | Result |
| --- | --- |
| Test alias | `test:6d6e2ff463bf` |
| Production alias | `production:7937bea5b823` |
| Direct runtime equality | `DISTINCT` |
| Settings-model load | PASS |
| Secret in repo | `0` |

`TEST_SINK_AVAILABLE = YES`
