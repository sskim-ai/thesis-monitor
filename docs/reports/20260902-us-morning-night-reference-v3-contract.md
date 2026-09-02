# US Morning Night Reference V3 Contract

Contract: `us-morning-night-reference-date-v3`

## Rule

For a US morning observation on KST date `D`, select the latest valid XKRX business date strictly
before `D`.

- Date owner: XKRX calendar
- US regular-session date: metadata only, not a mapping input
- Calendar-day subtraction: prohibited
- Provider raw `BAS_DD`: preserved without relabeling
- Finality: independent 06:00 KST gate

## Classification

- Raw date equals expected date: `DATE_MATCH`
- Raw date precedes expected date: `STALE_PRIOR_REFERENCE`
- Raw date follows expected date: `UNEXPECTED_FUTURE_REFERENCE`

Date match is necessary but not sufficient. Readiness still requires exact instrument/contract
identity, valid maturity, same-contract preceding DAY comparison, row integrity, change
cross-check, source provenance, and finality.

Run-51 example: observation `2026-09-02 08:20 KST`, expected `2026-09-01`, raw `BAS_DD`
`2026-09-01`, match `true`.
