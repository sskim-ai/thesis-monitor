# Run-27 Repetition Audit

Date: 2026-08-19  
Packet: `2026-08-19-kr-run-27-63a064e837ff`

## Before

| Pattern | Count | Subjects |
|---|---:|---|
| `<numeric> 기록했고, <numeric> 기록했습니다.` | 7 | all active KR subjects |
| `<numeric>는입니다.` | 4 | 000660, 005930, 010120, 012450 |
| financial amount-basis warning | 3 | 005490, 005930, 010120 |
| `재고·CAPEX 이후 FCF·ROIC` | 3 | 000660, 005490, 005930 |

Substantive repeat count was 2, maximum identical sentence coverage was 3, and template skeleton
repeat count was 4. Generic methodology count was already 0.

## Ownership Trace

| Origin | Failure | Repair |
|---|---|---|
| supply prose template | six values split into the same three sentences | lead with subject-specific relationship, retain all six bound values in one compact sentence |
| numeric postposition | `은/는` attached before authored `입니다` | remove only the duplicate postposition metadata before binding |
| generic financial caution | same methodology sentence in three business sections | suppress cross-ticker generic candidate; retain specific data caution and evidence |
| generic next check | same FCF/ROIC fragment in three watch lists | suppress candidate lacking a distinct subject metric/consequence |

No word-swapping or threshold increase is used. Subject-specific industry relationships remain:
HBM execution, reinsurance profitability, steel spread, memory/foundry execution, power-equipment
order conversion, defense-order conversion, and freight/volume/margin.

## After

| Measure | Before | After |
|---|---:|---:|
| substantive repetitions | 2 | 0 |
| maximum substantive repeat | 3 | 0 |
| template skeleton repetitions | 4 | 0 |
| generic methodology repetitions | 0 | 0 |
| runtime hard checks | FAIL | PASS |

Average stock-message length falls from 1,410.14 to 1,377.14 characters. Observer/holder sections,
dynamic support/resistance, confirmation lifecycle, numeric provenance, and all six KR supply facts
remain present. Full text is in `20260819-run27-repaired-ai-preview.md`; machine-readable ownership
and suppression details are in `20260819-run27-reasoning-ownership-audit.json`.

