# V3 vs V5 Temporal-Grammar Root Cause

## Result

The latest fresh-first generation completed all six signed-in Codex CLI batches without transport
failure, then validated `20/22`. No retry, selective ticker rerun, candidate override, post-result
tuning, or A/B/C execution followed.

| Candidate set | Recorded validation | Current-validator recheck | Meaning |
| --- | --- | --- | --- |
| fresh-first v3 | 22/22 PASS | GOOGL PASS, MU PASS | Earlier wording used recognized future constructions |
| fresh-first v5 | 20/22 FAIL | GOOGL FAIL, MU FAIL | Fresh wording exposed two grammar gaps |

The source lock, universe, evidence fingerprints, price-map fingerprints, and alias ownership are
unchanged. The difference is generated prose selection, not a newer fact or a changed price input.

## GOOGL

The sector interpretation says that AI investment should be recovered through Cloud growth, cash
flow, and ROIC. Its selected evidence explicitly owns ROIC, so this is a qualitative future
checkpoint. The validator recognizes several future forms but not `회수돼야`; it therefore assigns
`unsupported_future_checkpoint_metric` even though semantic ownership is complete.

Classification: `VALIDATOR_FALSE_POSITIVE_FUTURE_GRAMMAR`.

## MU

The sector interpretation contrasts present-cycle profitability with future FCF and ROIC
durability. Its selected evidence explicitly owns ROIC. The validator checks the whole sentence for
`현재`, so the word attached to profitability is incorrectly applied to the later ROIC clause and
produces `unsupported_current_metric_value`.

Classification: `VALIDATOR_FALSE_POSITIVE_TEMPORAL_CLAUSE_SCOPE`.

## Why The Earlier Run Passed

Fresh model output is not text-deterministic even with the same frozen evidence. The v3 GOOGL and
MU candidates used future forms already covered by the validator, and both still pass when checked
with the current code. V5 used equally evidence-owned constructions outside the regex grammar.
Therefore the result is not a regression in source evidence or metric ownership; it is insufficient
grammar coverage revealed by natural wording variance.

## Bounded Repair

1. Add evidence-owned `회수돼야` and equivalent future recovery forms to the future-checkpoint
   grammar.
2. Scope current/historical markers to the metric-bearing clause so `현재 X ... 향후 ROIC` remains
   future, while `현재 ROIC` remains blocked.
3. Add positive and negative regression fixtures for both patterns without changing thresholds or
   allowing current/historical ROIC values.
4. After the deterministic repair, run one new ALL22 fresh-first gate. Run A/B/C once only if that
   gate reaches `22/22 PASS`.

Open P0: `0`. Open material P1: `1`. Promotion readiness:
`NEEDS_MORE_SHADOW_WORK`.
