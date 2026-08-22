# KR Run-33 Repaired Counterfactual Replay

Original immutable evidence remains unchanged:

```text
2026-08-22 16:05 KST
daily_kr run 33 -> 7/7 analysis -> 8 raw notification rows
packet artifact 0 -> hold FileNotFoundError -> repeated three times
Telegram 0
```

The repaired code was replayed at the same Saturday timestamp against an empty isolated database:

```text
role = kr_daily_production
target = none
skip_reason = no_valid_role_target
analysis_action = safe_noop
provider calls = 0
MonitorRun = 0
notification rows = 0
packet = 0
Telegram = 0
exit = normal
```

All three producer times produce the same result. The replay is retrospective and made no provider
request, production task run, Telegram send, database mutation, or archive rewrite.
