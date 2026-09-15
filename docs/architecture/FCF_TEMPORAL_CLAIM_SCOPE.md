# FCF Temporal Claim Scope

## Status

- Contract: `fcf-temporal-claim-span-v1`
- Fulfillment polarity: `current-fulfillment-polarity-v1`
- Scope: post-model validation only
- User-visible schema change: none

## Boundary

The FCF validator consumes local clause spans produced by the existing
`financial-framework-claim-span-v1` boundary implementation. FCF remains a
specialized support concept and is not added to the general industrial
financial-framework registry.

Each FCF occurrence carries the source field path, normalized full field,
local clause text and offsets, FCF term offsets, bound evidence references,
and the shared span contract. Multiple FCF occurrences are evaluated
independently. OCF and an OCF-less-PPE proxy do not become FCF evidence.

## Currentness

Current-fulfillment classification distinguishes:

- affirmative current fulfillment;
- negated current fulfillment;
- a current-scope marker without fulfillment;
- no fulfillment signal; and
- ambiguous fulfillment language.

Negated predicates are masked only over their local matched span before a
separate affirmative predicate is sought. Therefore `현재 충족된 사실은
아니다` is not affirmative, while a later independent `FCF는 이미 감소했다`
still requires safe current FCF evidence.

The words `현재`, `지금`, `currently`, and `now` are scope markers, not proof
of fulfillment by themselves. Current numeric FCF, current positive/negative
state, and affirmative change or confirmation predicates remain fail-closed.

## Frozen Contracts

This repair does not change model prompts, model schemas, configured-signal
views, configured FCF support mapping, BusinessDeltaEvidenceView,
MarketExpectationEvidenceView, financial evidence projection, or two-stage
composition semantics. Current FCF still requires `free_cash_flow` or
`reported_free_cash_flow` evidence on a compatible basis; OCF and the
PPE-only cash-conversion proxy cannot satisfy it.
