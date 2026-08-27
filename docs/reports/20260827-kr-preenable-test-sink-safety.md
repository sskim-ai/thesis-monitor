# KR Pre-Enable Test-Sink Safety

| Check | Result |
| --- | --- |
| Dedicated test sink configured | False |
| Test alias | `NOT_CONFIGURED` |
| Production alias | `production:7937bea5b823` |
| Production collision | 0 |
| Namespace | `TEST_ONLY_NON_PRODUCTION` |
| Production delivery intent created | 0 |

Only `TELEGRAM_BOT_TOKEN` and `TELEGRAM_CHAT_ID` exist in the operating environment. No dedicated
test/staging/developer chat key exists in `.env` or the thesis-monitor LaunchAgents. Private IDs and
tokens are not included in this report.

`TEST_SINK_AVAILABLE = NO`

`TEST_SEND = BLOCKED_NO_SAFE_SINK`
