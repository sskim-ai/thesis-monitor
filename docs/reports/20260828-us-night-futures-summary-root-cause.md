# US Night-Futures Summary Root Cause

Packet `2026-08-28-us-run-43-c086d78415ac` stored two legacy compact-summary strings: KOSPI200 `+1.2%` and KOSDAQ150
`+0.8%`. The same briefing's validated occurrences were session `2026-08-27`, values
`+0.63809967%` and `-0.51224475%`, while `night_futures_gate` expected `2026-08-28`, had no ready
products, and was `ai_review_hold`.

The compact `market_summary.items` producer therefore bypassed canonical gate ownership. The
renderer omitted stale canonical rows correctly, but legacy strings could still disagree in value,
sign, and session. Original archive and DB rows were not rewritten.

`NIGHT_FUTURES_RAW_SUMMARY_BYPASS = 0` after canonical projection.
