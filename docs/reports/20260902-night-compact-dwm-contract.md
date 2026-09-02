# Night Compact D/W/M Contract

Track C projects existing official KRX same-contract history into a compact user block.

| Frame | User fields | Completion label | Baseline |
| --- | --- | --- | --- |
| Daily | open, close, gap %, return % | final source bar | validated preceding regular DAY close |
| Weekly | open, close, weekly % | `진행중` until complete | previous completed same-contract week close |
| Monthly | open, close, monthly % | `진행중` until complete | previous completed same-contract month close |

Contract maturity remains identity metadata. High and low remain internal and have zero user-visible occurrences in the frozen replay.

`CONTRACT_MONTH_PRESENTED_AS_MONTHLY_TIMEFRAME = 0`

`NIGHT_DAILY_OPEN_CLOSE_GAP_RETURN = PASS`

`NIGHT_WEEKLY_OPEN_CLOSE_RETURN = PASS`

`NIGHT_MONTHLY_OPEN_CLOSE_RETURN = PASS`
