# Mixed Risk-Context Financial Claim Clause Scope

## Status

- Phase: M12AV
- Contract: `financial-framework-claim-span-v1`
- Decision: `CLAUSE_LOCAL_FINANCIAL_FRAMEWORK_TEMPORAL_SCOPE`
- Scope: post-model financial-claim extraction and temporal validation only
- User-visible behavior: unchanged

## Problem

A `risk_context` field may legitimately combine a current structural-risk clause
with a future configured financial-risk clause. The field has one shared
`evidence_refs` array, so field-level temporal classification incorrectly made
the future financial clause current or ambiguous whenever a current structural
reference was also present.

The frozen M12AU examples followed this shape:

```text
current structural or operating risk,
future deterioration in cash generation and net debt
```

The resulting current net-debt evidence requirement was a false reject.

## Claim Span

`FrameworkClaim` preserves both scopes:

- `full_field_text`: normalized source field text
- `local_clause_text`: bounded clause containing the framework occurrence
- `local_clause_start` and `local_clause_end`: offsets into `full_field_text`
- `span_contract`: `financial-framework-claim-span-v1`

The splitter recognizes sentence boundaries, punctuation, bounded conjunctions,
and contrastive markers. It is deterministic and intentionally narrower than a
general Korean or English parser.

## Temporal Decision

Temporal role is evaluated against `local_clause_text`. A mixed-ref
`risk_context` financial claim is prospective only when both conditions hold:

1. The local clause contains an explicit future or conditional construction.
2. At least one configured strengthen, weaken, or invalidation reference names
   the same canonical financial framework.

Configured-source identity continues to come from the frozen configured-signal
contract. Framework relevance is detected with the existing canonical
financial-framework detector. A configured reference about another framework
cannot exempt the claim.

## Safety Precedence

Current magnitude and fulfilled-state language has precedence within the local
claim. Examples such as `현재 순부채가 높다`, `순부채가 이미 증가했다`, and
`향후에도 현재 순부채가 높다` remain current and require complete current
evidence.

When one field contains separate current and future occurrences of the same
framework, each occurrence receives its own clause span. The current claim
continues to fail closed when evidence is incomplete, while the supported future
claim remains prospective.

## Preserved Contracts

This change does not alter:

- model prompts or schemas
- configured-signal model views or current-driver fencing
- BusinessDeltaEvidenceView or MarketExpectationEvidenceView
- typed financial evidence projection
- PPE-only cash-conversion and FCF claim semantics
- QTD/YTD, working-capital, debt, ADR, or financial-sector safety
- renderer, delivery, monitoring, or production state

## Verification

The exact stopped M12AU Stage-1 candidates for FIC-FIN-01/02/04 now validate
without `net_debt_claim_without_complete_net_debt_evidence`. FIC-FIN-03 remains
valid. Negative fixtures retain current-claim failures, same-framework mixed
current/future detection, and unrelated configured-reference rejection.
