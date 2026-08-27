# KR Final Test Sink Configuration

## Audit

The existing repository-native configuration accepts exactly one of:

- `TELEGRAM_TEST_CHAT_ID`
- `TEST_TELEGRAM_CHAT_ID`
- `TELEGRAM_STAGING_CHAT_ID`
- `TELEGRAM_DEVELOPER_CHAT_ID`

The canonical `.env` contains the production recipient key only. The operating worktree and
current process environment contain no approved test recipient key. No value was invented,
discovered from Telegram, or copied from production.

| Gate | Result |
| --- | --- |
| `TEST_SINK_AVAILABLE` | `NO` |
| Test sink alias | `NOT_CONFIGURED` |
| Test sink redacted hash | `NOT_CONFIGURED` |
| Production sink redacted hash | `production:7937bea5b823` |
| Configuration reason | `dedicated_test_sink_not_configured` |
| `SECRET_IN_REPO` | `0` |
| Raw private sink ID in report | `0` |

`KR_FINAL_PREENABLE_DETAIL = BLOCKED_NO_TEST_SINK`

Track B and Track C must not start.
