# KR Valuation Semantic Validation

| ticker | safe PER | safe PBR | result |
| --- | --- | --- | --- |
| 000660 | suppressed | 4.4x | PASS_FALLBACK; AI_SCOPE_GUARD_TRIGGERED |
| 003690 | 6.2x | 0.7x | PASS |
| 005490 | 18.5x | 0.4x | PASS |
| 005930 | 11.2x | 2.6x | PASS |
| 010120 | suppressed | suppressed | PASS_FALLBACK; AI_SCOPE_GUARD_TRIGGERED |
| 012450 | suppressed | suppressed | PASS_FALLBACK; AI_SCOPE_GUARD_TRIGGERED |
| 047810 | suppressed | suppressed | PASS |
| 086280 | 9.5x | 1.3x | PASS |

The sent fallback used only eligible PER/PBR/fPER/fPBR fields and suppressed 010120, 012450, and 047810 where security/share basis was unresolved. It did not reconstruct denominators. The rejected AI candidate scope errors were contained. `KR_VALUATION_SEMANTIC_VALIDATION = PASS` for the live payload.
