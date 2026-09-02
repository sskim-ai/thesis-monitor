# Track C — Night-Futures Session-Date Mapping Repair

## Run-51 evidence

Observation: 2026-09-02 KST morning.
Current gate expected: 2026-09-02.
Provider/Kiwoom returned: 2026-09-01.
Both products HTTP 200.
Raw SHA:
39fff1232b66a8ff3fc464d35d21f300ba63595391df440cc2289d2f50fd6d28.

The user also observes Kiwoom UI labels the relevant overnight session 2026-09-01.

## Required

Prove `night_bas_dd` semantics from provider/repository evidence.

Model separately:
- observation_time_kst
- US_regular_session_date
- KRX_regular_business_date
- night_session_business_date
- provider_night_bas_dd
- finality

Use KRX business-calendar mapping.
Do not use simple calendar-day minus one.
Do not hardcode US session date.

Test:
- ordinary weekdays
- Monday
- weekends
- KRX holidays/consecutive holidays
- month/year boundary
- US/KR holiday mismatch

Verify contract/maturity/finality/change-percent provenance.

## Run-51 replay

Use immutable raw response.
If semantic/finality proof confirms 2026-09-01 is current:
- ready 2/2
- market packet includes both
- renderer displays both
- status PASS

If not, return exact independent blocker.

Do not classify mapping bugs as SOURCE_LIMITATION_SAFE.
