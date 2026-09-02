# Night Reference XKRX Calendar Tests

The deterministic calendar matrix passes `8/8`.

| Case | Observation KST | Expected reference | Result |
|---|---|---|---|
| Ordinary weekday 08:00 | 2026-09-02 | 2026-09-01 | PASS |
| Ordinary weekday 08:20 | 2026-09-02 | 2026-09-01 | PASS |
| Monday | 2026-08-10 | 2026-08-07 | PASS |
| XKRX holiday | 2026-08-18 | 2026-08-14 | PASS |
| Consecutive holidays | 2026-09-28 | 2026-09-23 | PASS |
| Month boundary | 2026-09-01 | 2026-08-31 | PASS |
| Year boundary | 2027-01-04 | 2026-12-30 | PASS |
| US holiday, XKRX open | 2026-09-08 | 2026-09-07 | PASS |

The matrix proves that US holidays do not move the XKRX-owned target and that weekends, XKRX
holidays, month boundaries, and year boundaries do not rely on naive day subtraction. Machine
evidence is in `20260902-night-reference-contract.json`.
