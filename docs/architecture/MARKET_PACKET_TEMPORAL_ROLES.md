# Market Packet Temporal Roles

Every market date has an explicit role:

- `observation_time`: when the packet or probe observed the source.
- `us_regular_session_date`: completed US regular session represented by the morning review.
- `krx_regular_business_date`: Korean regular session from which the night session starts.
- `night_session_business_date`: completed KRX night-session end date.
- `provider_night_bas_dd`: provider date that must match the completed night session.
- `ui_session_start_date`: user-facing start-session date when needed.

These roles are not interchangeable. An observation calendar date does not automatically become
the expected provider date, and a US session date does not override the KRX business calendar.
Missing or stale temporal evidence is suppressed or marked source-limited, never filled by date
guessing.
