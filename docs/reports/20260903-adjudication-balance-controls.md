# 2026-09-03 Adjudication Balance Controls

## Runtime Controls

| Case | Expected | Result |
| --- | --- | --- |
| Same evidence, BUY `6:4` to BUY `6.5:3.5` | no adjudication | PASS |
| Same evidence, BUY `6:4` to BUY `7.5:2.5` | adjudication required | PASS |
| Label boundary crossing | adjudication required | PASS |
| Major configured thesis-condition conflict | adjudication required | PASS |
| Material move with missing adjudication | candidate suppressed | PASS |
| Material candidate move with `KEEP_V1` | prior balance retained | PASS |
| Material same-evidence move with `KEEP_V2` | accepted drift rejected | PASS |
| `KEEP_V2` balance/driver/summary mismatch | rejected | PASS |

The accepted consistency audit now records prior, candidate, and accepted balances, both balance distances, material accepted-balance drift, and final block ownership. A final block whose balance differs from the accepted plan fails the audit.

No balance transition automatically changes the business thesis or valuation context.
