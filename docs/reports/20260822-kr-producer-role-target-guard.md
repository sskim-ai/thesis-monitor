# KR Producer Role-Target Guard

- Contract: `xkrx-role-target-v1`
- New role: `kr_daily_production`
- Entry: `app.jobs.monitor_daily._run_market_job`
- Guard position: before analysis decision, KR-close briefing, providers, run creation, packet, and
  notifications

Eligibility requires an authoritative XKRX session on the observed KST date, completion after
15:30 KST, and exact equality between the target business date and requested run date. Calendar
errors and target mismatches fail closed.

At 2026-08-22 16:05, 16:20, and 16:50, the deterministic result is:

```text
target = none
production_eligible = false
skip_reason = no_valid_role_target
analysis/provider/packet/notification = 0
exit = safe_noop
```

Normal 2026-08-21/24 sessions proceed. Sunday, 2026-08-17 holiday, consecutive 2026-09-24/25
holidays, and 2026-12-31 closure all skip without calendar-day arithmetic. Existing KRX and night
roles retain their behavior.
