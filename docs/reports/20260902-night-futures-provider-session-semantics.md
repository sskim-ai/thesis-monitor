# Night Futures Provider Session Semantics

Historical official KRX rows prove that night-futures `BAS_DD` is the completed session end date.
For example, a row ending on 2026-08-28 uses the 2026-08-27 regular close as its preceding base,
which is inconsistent with treating `BAS_DD` as the UI start date.

Therefore the 2026-09-02 08:20 KST observation expected official `BAS_DD=2026-09-02` for the night
session that started on the 2026-09-01 KRX business day. The source repeatedly returned
`2026-09-01`, so both instruments were correctly stale and not ready.

- Provider semantics: `PROVEN`
- Run-51 provider date: `2026-09-01`
- Forced reclassification: `0`
