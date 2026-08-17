# Semantic Scope And Decision Hierarchy

## Decision

`semantic-scope-and-decision-hierarchy-v1` hardens the Phase 8.4 full-message path without changing
schema 4. Draft-only references carry economic scope and supporting Fact IDs through binding, then
the binder removes them before public schema validation.

```text
canonical Facts
  -> economic scope
  -> denied-family boundary
  -> deterministic materiality candidates
  -> historical-context selection
  -> schema-4 draft and typed occurrences
  -> numeric/semantic validation
  -> existing renderer and runtime receipt
```

The contract is archive-only until a separate main-merge and deployment approval.

## Economic Scope

Supported scopes are `company`, `listed_security`, `segment`, `sum_of_parts_component`, and
`unknown`. Ordinary PER, PBR, fPER, fPBR, and their own-history distributions are
`listed_security`. Financial statements describe the issuer or company. Price describes the listed
security. Segment wording requires a segment-specific numerator, denominator, method, and canonical
Fact; industry concentration or pure-play status does not change a company multiple into a segment
multiple.

Typed valuation references bind one exact occurrence to its metric, Fact, numeric references, and
economic scope. A listed-security multiple presented as a business-segment multiple is rejected.

## Denied-Fact Echo

A denied financial family cannot support a number, comparison, causal statement, valuation
interpretation, thesis change, or qualitative premise. The boundary is semantic rather than a
global word ban: safe revenue can support revenue interpretation, while denied revenue cannot
support phrases such as strong external growth. A denial explanation may identify why a Fact is
excluded, but all subsequent reasoning must use independent safe Facts.

Draft-only semantic claim references bind the exact normalized span to supporting Fact IDs, claim
type, economic scope, and semantic family. Denied support is accepted only for the explicit
`denial_explanation` claim type.

## Decision-Material Delta

`decision-material-delta-v1` evaluates verified candidates before section ordering:

| Tier | Candidate |
|---|---|
| 1 | business thesis, earnings, financial-quality, or material corporate evidence |
| 2 | valuation regime or price/confirmation transition |
| 3 | RR or supply/positioning transition |
| 4 | static warning, unchanged Unknown, or registered level |

A mild supply divergence remains supporting context when verified earnings and valuation are the
more important current decision context. If earnings are denied, price, supply, safe PBR, and
execution evidence may correctly lead. Deterministic lifecycle transitions can override the base
tier. The audit stores candidates, tier, selected primary and secondary items, override, and reason.
The renderer neither calculates materiality nor mutates the business thesis.

Retrospective source recovery is not a historical-date event. If no verified material transition
exists, the message says there is no material delta and proceeds to current decision relevance.

## Historical Valuation Retention

Own-history context is eligible only when interpretation lineage is usable, comparability is
normal, sample count is at least 30, coverage is at least 80%, and the history end is no more than 14
days before the Fact as-of date. A decision-band candidate is at or below the 25th percentile or at
or above the 75th percentile. When several candidates qualify, the one farther from the 50th
percentile is selected; every other candidate receives a suppression reason.

Denied earnings suppress historical PE but do not suppress an independently safe historical PBR.
Percentiles describe rank among comparable observations and never become a percentage overvaluation
claim. Cyclical PER percentiles do not independently establish cheap or expensive valuation.

## Valuation Context Availability

`valuation-context-wording-v1` separates availability from use for current, own-history, peer, and
forward contexts. The renderer chooses wording from the structured class, while the binder checks
the exact sentence against the numeric semantics actually present in `valuation_analysis.text`.

| Current | History used | Peer used | Class |
|---|---:|---:|---|
| used | no | no | `CURRENT_ONLY` |
| used | yes | no | `CURRENT_PLUS_HISTORY` |
| used | no | yes | `CURRENT_PLUS_PEER` |
| used | yes | yes | `CURRENT_PLUS_HISTORY_PLUS_PEER` |
| unavailable | any | any | `LIMITED_VALUATION` |

A safe history candidate may be available but not selected because it is not decision-relevant. That
case is not described as unsafe or missing. When history is visible, current-only wording is always
invalid. Draft-only availability metadata is removed before public schema validation.

## Next-Check Baselines

An existing canonical current value may be the reference point for a next check. The binder owns the
value and its period/basis label. The AI may not invent a rounded threshold such as 6% when only a
current 5.7% margin is available.

## Observer And Holder

Role labels alone do not make two decisions distinct. New-observer text must contain an entry,
price, RR, resistance, or support-approach variable. Holder text must contain a thesis, support,
invalidation, earnings, warning, execution, or capital variable. The semantic validator removes role
labels before detecting identical bodies.

## Suppression And Length

Adaptive suppression records the safe historical candidate, whether it was selected, why it was
suppressed, and whether safe context was lost. There is no section quota. Correctness takes
precedence, while the portfolio target is no more than about 5% average character growth over Phase
8.4.

## Activation Boundary

Phase 8.4.1 received direct Work scores of 17/16/18/16/17. Phase 8.4.1.1 completes the wording
follow-up without changing decision hierarchy, denied-family rules, or historical selection.
Production Assist remains off; Scheduled Tasks, Pilot state, Telegram, the operating DB, and
immutable archives are unchanged by this retrospective.
