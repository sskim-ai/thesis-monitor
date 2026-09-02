# Market Packet Temporal Roles

Every market date has an explicit role:

- `observation_time`: when the packet or probe observed the source.
- `us_regular_session_date`: completed US regular session represented by the morning review.
- `expected_reference_date`: latest valid XKRX business date strictly before
  the US morning KST observation date.
- `provider_raw_bas_dd`: unmodified provider date.
- `reference_date_match`: whether the raw provider date equals the product
  reference date.
- `comparison_day_date`: preceding eligible XKRX DAY row used for the
  same-contract change calculation.
- `finality_valid`: independent 06:00 KST completion gate.
- `ui_session_start_date`: user-facing start-session date when needed.

These roles are not interchangeable. An observation calendar date does not automatically become
the expected provider date, and a US session date does not override the KRX business calendar.
For `2026-09-02 08:00 KST`, the expected reference date is `2026-09-01`.
A provider raw date of `2026-09-01` is therefore current for this product path,
not stale. Missing, stale, future, or unfinalized evidence is suppressed and is
never filled by date guessing.
