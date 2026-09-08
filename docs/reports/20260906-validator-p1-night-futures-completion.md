# Validator P1 And Night Futures Completion

## Outcome

- Generation: `20260905-uskr22-validator-night-20260905T161259Z-1a32918a3962`
- Source lock: `f3b7d4c08c32312c2207acae2cb9353926940e41a2bcf254a7214a041d246be0`
- FIRST: `22/22`
- A: `22/22`
- B: `17/22`
- C: `NOT_RUN`
- Stop state: `STOPPED_B_GATE`
- Model / effort: `gpt-5.6-sol / xhigh`

The experiment stopped exactly at the first failed A/B/C gate. No selective rerun, candidate reuse, prompt edit, builder edit, validator edit, renderer edit, threshold relaxation, ticker exception, Korean grammar regex, or post-result hotfix occurred.

## B Failures

- Metric-kind ownership: `GOOGL`, `IBM`.
- Directional probability false positive: `MU` (`상승률` contained `승률`).
- Mandatory trade false positive: `SNDK`, `TSLA` (negated `즉시 매수가 아닌`).
- Cross-ticker repeated substantive span: `1`, the identical negated sentence for SNDK/TSLA.

Audited false rejects are `4`: IBM metric-union ownership, MU substring matching, and SNDK/TSLA negation handling. GOOGL is an intended fail-closed because the selected metric evidence did not own strengthening severity.

## Independent Gates

- Validator P1: `NEEDS_BOUNDED_REPAIR`
- Logical schema: `DISCRIMINATED_UNION`, LEAF failures `0`
- Night futures: `READY_FOR_PRODUCTION_REVIEW`, separate frozen shadow only
- Structured Autonomy: `NEEDS_MORE_SHADOW_WORK`
- Main/operating: unchanged at `d18e68b1e944d7749d093b08797fcd9498412680`
- Production send/mutation: `0`

## Validation

Focused tests `245 passed`; full pytest `2450 passed`; Ruff and git diff check passed. Knowledge checksums, Public Action `0.4.5`, output schema `4`, and operationId `20/20` remain unchanged.
