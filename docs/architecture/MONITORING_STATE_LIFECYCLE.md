# Monitoring State Lifecycle

## Problem

An investment thesis changes slowly, while price structure, supply, valuation, and expectations can
change every session. Repeating registered price rules as if they were current support or resistance
hides those changes and can make a daily review stale even when the official thesis is unchanged.

## Decision

Persist a backward-compatible `monitoring_state` object inside each final
`ThesisAssessment.price_context`. No raw OHLCV bars are duplicated and no database migration is
required.

```text
Thesis state (slow)
  + registered price-rule history
  + current deterministic structure, supply, and valuation
  + previous final assessment
  -> monitoring-state-v1 current / previous / delta
  -> AI packet and assessment history
```

`current` contains price structure, registered-rule lifecycle, 1/5/20-day supply, valuation,
peer-valuation availability, market expectations, and selected macro effects. `previous` is the
previous final assessment only. `delta` records confirmation, support, resistance, RR, chart-state,
supply, and valuation-percentile changes even when `business_thesis_change` is
`no_material_change`.

## Why

The daily review can explain what changed without rewriting the original investment thesis. The
stored state is queryable through assessment history, while the immutable thesis still preserves the
original drivers, risks, and price rules.

## Rejected Alternative

- Rewriting registered price rules after every chart move.
- Promoting a crossed confirmation price to support without a verified zone or retest.
- Reusing registered support to manufacture current RR when dynamic support is unavailable.
- Comparing against pending or failed assessments.
- Storing hundreds of raw OHLCV bars in every assessment.

## Safety Constraint

- Thesis state is not monitoring state.
- Registered price rules are not dynamic price structure.
- A chart transition never changes business-thesis status automatically.
- Confirmation lifecycle is reset for a new thesis version; market-price continuity remains visible.
- Missing support, resistance, invalidation, or RR stays unavailable.
- Public Action 0.4.5 remains unchanged.

## Stored Contract

`monitoring-state-v1` is stored under `price_context.monitoring_state`:

```json
{
  "version": "monitoring-state-v1",
  "current": {
    "price_structure": {},
    "supply": {},
    "valuation": {},
    "peer_valuation": {},
    "market_expectation": {},
    "macro": {}
  },
  "previous": {},
  "delta": {}
}
```

Dynamic zones use a stable fingerprint of timeframe, role, pivot type, and constituent pivot dates.
Small daily boundary movement therefore does not create a false new zone.

## Registered Rule Lifecycle

Confirmation states are `not_reached`, `crossed`, `holding_above`, `retest_in_progress`,
`retest_held`, `failed_breakout`, or `not_configured`. Relevance is tracked separately as `active`,
`transition_reference`, `background`, or unavailable. Registered support can be
`superseded_for_current_structure`, but it is never deleted.

## Renderer Priority

The review uses this order:

1. today's price transition;
2. nearest Strong/Medium dynamic support and resistance;
3. current-price RR and chart invalidation;
4. a currently relevant registered rule;
5. legacy/background rules only when they still matter.

If no valid dynamic support exists, the review says so and withholds RR. It does not substitute the
registered support.

