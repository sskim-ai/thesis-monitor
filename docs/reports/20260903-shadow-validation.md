# Shadow Validation

## Result

- Candidate count: `14`
- PASS: `14`
- FAIL: `0`
- Balance-sum errors: `0`
- Unsupported entry zones: `0`
- Unsupported trim zones: `0`
- Invented stop losses: `0`
- Mandatory-sell trim wording: `0`

## Bounded Pre-Freeze Repair

Three model-copied evidence refs were invalid by one suffix or referred to a sibling ref. Signed-in Codex performed a bounded `EVIDENCE_REFS_ONLY` correction before the Phase-1 freeze. Decision labels, balances, stances, zones, and prose were unchanged.

| Ticker | Rejected ref | Replacement ref | Scope |
| --- | --- | --- | --- |
| CORZ | decision-evidence:8906a34193399a6c5d0 | decision-evidence:8906a34193399a6c5d0a | reference-only |
| GOOGL | decision-evidence:47e26c6f53ec96785224 | decision-evidence:47e26c6f53f6504d798d | reference-only |
| SKHY | decision-evidence:d2f6c30d68288191bbd428a394a78407 | decision-evidence:d2f6c30fdb85a421401f | reference-only |

The accepted candidate and all rendered messages were frozen only after the repaired validation reached `14/14 PASS`.
