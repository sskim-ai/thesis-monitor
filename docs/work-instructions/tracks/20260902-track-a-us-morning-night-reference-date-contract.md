# Track A — US Morning Night Reference-Date Contract

Normative rule:

`expected_reference_date = latest valid XKRX session strictly before observation_date_kst`

Run-51:
`2026-09-02 08:xx KST -> 2026-09-01`.

Do not use:
- observation date
- calendar-day minus one
- US regular-session date

as generic substitutes.

Keep:
- raw provider BAS_DD unchanged
- finality separate
- instrument/contract/value provenance separate

Add calendar tests for weekdays, Monday/weekend, KRX holidays, consecutive holidays, month/year boundaries, and US/KR holiday mismatch.
