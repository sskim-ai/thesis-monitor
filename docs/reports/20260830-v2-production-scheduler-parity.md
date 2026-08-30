# V2 Production Scheduler Parity

No Scheduled Task or LaunchAgent configuration was changed or manually triggered. The four normal
AI windows remain `08:15 / 08:30 / 16:15 / 16:55 KST`; KRX telemetry and night-futures observers
remain independent.

The seven thesis-monitor LaunchAgent plist SHA-256 values match before and after promotion:

```text
ai-review-delivery-retry       2ee920d697da1732efc79916d50a84e9f8b674284f741e909f3ca322e6319f6c
ai-review-fallback             079d4a7ca01707bee818a3598a445e10155ddc9025e463197e44e52c0ec4207a
daily                          020df8c4d3c2a9bfe5e49dea3cff506552c1798fcd4916f07155a68a600505ee
kr-close                       9eb77b8c019452154dc820086da01b0a721a7ab408aa9543426744b269247e3a
krx-publication-telemetry      d80181cb5f54d5e2d9758047fe2dea8f2aaf1fae6f9c1f120b97a5b7400813b9
night-futures observer         e5dbf6a870765e08e48ca2b772cdbd10bf108c51d137e119c036781a96b458fd
API                            35d9bc22301a896f470ae15e8949dcfe63ee79051b625c564badaa28e38ddad9
```

`SCHEDULER_DIFF_UNRELATED_TO_CUTOVER = 0`; `MANUAL_SCHEDULED_JOB_TRIGGER_20260830 = 0`.
