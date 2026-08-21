# Phase 9.0D.1 Cross-Artifact Consistency Audit

## Gate

The runtime canary now compares production baseline claims with the same point-in-time canonical
context used by the shadow candidate. The audit covers availability, sign/state, period, scope, and
currentness even when no exact cash-flow number appears in production prose.

Rendered headings restore ownership before evaluation. Core, business/earnings, warnings and data
cautions are current analytical surfaces. Persistent risks and next checks are conditional surfaces.
An unrelated `TTM EPS` valuation label cannot assign TTM period identity to an earlier FCF claim.

## Run-30 Before / After

| Surface | Before | After |
|---|---:|---:|
| Saved TSLA core unsupported claims | 2 | 0 at render/packet boundary |
| Packet TSLA core unsupported claims | 2 | 0 |
| Packet TSLA warning unsupported claims | 1 | 0 |
| Fallback TSLA core unsupported claims | 2 | 0 |
| Fallback TSLA warning unsupported claims | 1 | 0 |
| Repaired portfolio cross-artifact errors | - | 0 |

## Canary Behavior

The canary writes `baseline-consistency.json` beside its existing semantic receipt. A fixture with
the same positive canonical Fact and contradictory qualitative claim in both packet and delivered
message produces four `baseline_cash_flow_unsupported_claim` errors and
`SEMANTIC_VALIDATION_FAILED`. The normal fixture remains `COMPLETE_PASS` and idempotent.

Production isolation is unchanged: the audit runs after terminal delivery in the detached canary,
has no Telegram import, and cannot affect fallback eligibility, exit status, receipt, backup,
assessment, warning lifecycle, or Pilot state.

## Regression Controls

| Class | Result |
|---|---|
| Current positive vs current negative baseline | suppress/reject |
| Current negative vs negative baseline | keep with compatible scope or qualify |
| Explicit historical claim with provenance | keep as history |
| Prior negative without period | suppress |
| Management FCF vs PPE-only FCF | not directly comparable |
| Generic unknown-scope claim without provenance | suppress |
| Negative OCF with FCF unavailable | no FCF inference |
| Stale fact while newer formal is blocked | no current substitution |
| No canonical check | provenance required |
| Implied `FCF 흑자 전환 필요` | current-negative implication detected |
| Insurance | generic enterprise FCF suppressed/N/A |

Thresholds, canonical formulas, Phase 9.0B facts, Phase 9.0C selectors, and canary scheduling are
unchanged.

