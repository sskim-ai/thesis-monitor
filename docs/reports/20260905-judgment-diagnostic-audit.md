# Judgment Diagnostic Audit

The figures below are observations, not target labels or calibration quotas.

| Run | BUY | HOLD | SELL | New buyer WAIT | Holder REVIEW |
| --- | ---: | ---: | ---: | ---: | ---: |
| FIRST | 5 | 13 | 4 | 16 | 7 |
| A | 4 | 13 | 5 | 14 | 7 |
| B | 6 | 12 | 4 | 18 | 9 |

CPNG and IBM were observed as ordinary regressions. No desired label, sentence, balance, entry mode, or holder stance was supplied. Prior blind-review labels were not used as targets. Majority voting and result-driven calibration were `0`.

B produced five validation failures. Four were audited false rejects: IBM's split evidence-union ownership, MU's `상승률` substring, and the same negated `즉시 매수가 아닌` construction for SNDK and TSLA. GOOGL was an intended ownership/severity fail-closed. The run was not repaired or repeated.
