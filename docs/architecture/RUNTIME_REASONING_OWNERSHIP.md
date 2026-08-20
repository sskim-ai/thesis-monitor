# Runtime Reasoning Ownership

Contract: `runtime-reasoning-ownership-v1`  
Specificity contract: `runtime-message-specificity-v2`  
Status: retrospective PASS, natural proof pending  
Date: 2026-08-20

## Purpose

Runtime reasoning must retain the owner of each claim before prose is authored. A fact may inform
more than one section, but one primary owner keeps the detailed claim. Other sections may state the
decision implication without repeating the same evidence or number.

| Owner | Scope | Examples |
|---|---|---|
| `business_earnings` | company economics and thesis causality | revenue, margin, order conversion |
| `valuation` | current/history/forward valuation context | PE, PB, denominator quality |
| `price_context` | entry and chart decision context | support, resistance, RR, confirmation |
| `positioning` | market-participant flow | foreign/institution daily and rolling flow |
| `security_identity` | issuer/security/share basis | ADR/ADS ratio and ordinary-share relation |
| `industry_driver` | industry-specific causal variables | spread, freight, combined ratio, memory ASP |
| `unknown` | unresolved company-specific evidence | missing basis or unverified metric |
| `next_check` | future evidence that can change the decision | named metric, driver, or event |

## Framework Boundary

Investment and industry frameworks explain business economics and valuation causality. Price
contexts describe entry location and chart state. `chart_risk_reward` is always `price_context`; it
is never an investment-thesis or industry-valuation framework. A price-context statement may say
the current RR is unfavorable, but it cannot stand in for steel, transport, insurance, memory, or
another industry explanation.

The packet publishes framework roles separately:

```text
investment_industry
price_context
security_identity
general_reasoning
```

The validator rejects `chart_risk_reward` when a candidate uses it without a packet-authorized
price-context role. It is not added to an industry allowlist to make a draft pass.

## Depositary Boundary

Depositary reasoning is eligible only when `security-identity-v2` resolves the security as
`verified_depositary`, or when a real unresolved depositary basis exists. A verified ratio statement
also requires ratio value, direction, and source. `domestic_common` and
`verified_non_depositary` suppress ADR/ADS/depositary-ratio candidates with
`security_identity_not_depositary`. Unknown or conflicting identity never permits prose saying a
ratio was verified.

The text validator requires an explicit ADR, ADS, or depositary qualifier before treating a ratio
statement as depositary reasoning. A company metric such as an insurance combined ratio must not
match that rule.

## Specificity And Repetition

Each candidate carries `owner`, `evidence_type`, `decision_role`, `section`, `specificity_key`,
`materiality`, and supporting `fact_ids`. Candidate selection follows these rules:

1. Keep one detailed owner for the same evidence and decision role.
2. Prefer a subject Fact plus industry driver plus decision consequence.
3. Suppress generic cash-flow, methodology, Unknown, and next-check candidates that recur across
   three or more subjects without distinct evidence or consequences.
4. Do not receive credit for synonym-only rewrites.
5. Preserve genuinely shared material risk when each subject has specific supporting evidence.

Observer prose owns entry attractiveness, expectation, price context, and confirmation. Holder
prose owns business thesis, earnings driver, kill condition, and fundamental deterioration. Exact
RR numbers remain in price context; observer prose may state only the resulting entry meaning.

## Business Numeric Ownership

`numeric-summary-ownership-v1` removes the former earnings numeric quota. `business_earnings`
prefers prose-eligible `earnings:*` revenue, gross/operating profit, margin, volume, ASP,
utilization, or another verified operating metric. A `valuation:*` TTM EPS is a valuation
denominator unless a separate earnings-period Fact establishes it as material earnings evidence.
BVPS remains valuation or balance-sheet context. Neither metric may fill a sparse business section.

The packet publishes `business_earnings_policy` with actual business Fact candidates, zero minimum
numeric anchors, valuation-owned semantics, and a company-specific Unknown fallback. The quality
gate independently rejects valuation-owned claims bound into `business_earnings`; prompt compliance
is not the only safety boundary.

## RR Delta Ownership

An RR number changing is not itself a material message event. `risk_reward_delta_policy` promotes a
candidate only when a canonical chart-state, confirmation-lifecycle, support/resistance, or RR-
availability transition makes it decision-relevant. The default standalone previous/current tuple
is prohibited. A permitted comparison is integrated with the primary price transition and remains
owned by `price_context`; US `supply_analysis` is not a daily RR-dump section. No new RR threshold,
formula, or chart-selection rule is introduced.

## Typed Skeletons

`typed-template-skeleton-v1` keys a repeated template by text structure plus section, owner,
numeric semantic types, and comparison relation. It therefore separates a price-context
`previous_risk_reward_ratio -> current_risk_reward_ratio` from a valuation
`price_to_book -> historical_pb_percentile` even when both render as two semicolon-separated
numbers. The same typed relation with the same prose structure across the existing threshold still
fails.

The detector also audits the portfolio-wide `현재 확인된 핵심 숫자는` family independently of
numeric arity, so one-, two-, and three-number variants do not evade the repetition boundary.
Canonical zone endpoint tuples retain their existing structural exception. There is no generic
numeric-pair or semicolon allowlist.

## Validation Boundary

Thresholds in `runtime-message-quality-v1` are unchanged. This contract reduces invalid candidates
before prose and keeps the existing validator as the final fail-closed boundary. It does not rewrite
validated prose in the renderer, infer missing Facts, create thresholds, alter RR calculations, or
weaken fallback and exactly-once behavior.
