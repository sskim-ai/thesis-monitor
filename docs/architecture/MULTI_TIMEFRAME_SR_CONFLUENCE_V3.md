# Multi-Timeframe SR Confluence v3

## Problem

Pooling all price evidence before building timeframe maps obscures whether a zone is monthly
structural context, weekly confirmation, or daily execution context. It can also manufacture
confluence by using broad merge tolerances.

## Decision

`multi-timeframe-sr-confluence-v3` builds monthly, weekly, and daily maps independently, then runs
a final cross-timeframe merge. Pivot grouping starts at `3.00% / 2.25% / 1.75%` for monthly,
weekly, and daily and uses `max(price * grouping_pct, ATR14 * 0.50)`. Pivot-zone padding is bounded
by `min(ATR14 * 0.10, center * 0.01)`.

Cross-timeframe tolerances are `3.0% / 2.5% / 2.0%` by source map and are not widened to improve
agreement. Contributors retain timeframe, evidence type, family, method, degree, and target.
Support, resistance, and current-zone roles are recomputed against current price. Structural
importance and proximity are separate fields.

## Why

Independent maps preserve semantic roles while the final merge identifies genuine overlapping
evidence without erasing provenance.

## Rejected Alternative

One pooled map, one universal tolerance, nearest-level-only ranking, and dumping all historical
zones were rejected.

## Safety Constraint

Zone counts are capped, wide-tolerance confluence is prohibited, and the engine remains a shadow
sidecar. Existing production SR ownership and output are unchanged.
