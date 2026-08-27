# US Market Digest Plan

Version: `us-market-digest-plan-v1`

## Input

The plan consumes the existing market `fact_catalog`, `key_change_fact_ids`, and coverage state.
It does not fetch data or create a parallel market truth store.

Each slot records:

- slot and priority
- deterministic claim text
- canonical evidence refs and numeric field refs
- observation dates and temporal roles
- materiality explanation
- selection or safe omission reason
- whether consumption is mandatory

Allowed omission reasons are `SELECTED`, `OMITTED_SAFE_NOT_MATERIAL`,
`OMITTED_SAFE_LENGTH_BUDGET`, `OMITTED_UNAVAILABLE`, and `OMITTED_TEMPORAL`.

## Selection

`CURRENT_MARKET` selects available current directional SPY, QQQ, IWM, and SOXX observations. One
bounded direction statement may carry several refs; exact ETF returns do not have to be dumped.

`PARTICIPATION_STYLE` selects current directional RSP and, when available, SPY for a same-session
direction relation.

`SECTOR_DISPERSION` selects the strongest and weakest current directional sector proxies, excluding
SOXX because SOXX is already part of the core market slot. Level-only sector observations do not
enter directional ranking.

`BREADTH_STATE` uses only official issue-level breadth facts. Missing or publication-pending data
remain unavailable and are never replaced by RSP.

`MACRO_CONTEXT` retains at most the first non-price fact chosen by the existing key-change policy.
It is optional and subordinate to current market structure.

## Rendering

Fallback renders selected primary claims before the existing macro sections. AI packets store the
same serialized plan. The adaptive market renderer uses the plan's current claim and one bounded
supporting statement that can include style, sector, and available breadth.

The plan does not require an exact numeric claim for every selected ref. Numeric claims that are
made remain governed by the existing numeric registry and binding pipeline.
