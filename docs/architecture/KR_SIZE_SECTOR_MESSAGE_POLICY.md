# KR Size / Sector Message Policy

Contract owners: `kr-market-digest-quality-v1`, `kr-sector-relative-ranking-v1`

## Selection

The shared `KrMarketDigestPlan` deterministically selects two bounded slots after index, scoped
breadth, and aggregate participant flow:

1. `SIZE_STYLE`: complete same-session KOSPI large/mid/small and complete KOSDAQ100/MID300/SMALL
   groups.
2. `SECTOR_EXTREMES`: one relative-strong and one relative-weak non-empty sector for each available
   KOSPI/KOSDAQ market while the rollout guard is OFF. The guarded TOP3 form selects up to three
   relative-strong and three relative-weak sectors per market.

When at least one market has a complete safe group, the slot state is `SELECTED_REQUIRED`. Allowed
fail-closed states are `SOURCE_UNAVAILABLE`, `WRONG_SESSION`, `INVALID_SEMANTIC`, and
`NO_VALID_ROWS`. `OMITTED_SAFE_LENGTH_BUDGET` is not valid for these slots.

## Rendering

The backend owns ordering, extrema selection, sign, formatting, and source refs. AI and
deterministic fallback consume the same plan claims. The user-facing form uses compact registered
returns and the Korean labels `규모별`, `업종 상대 강세`, and `업종 상대 약세`.

Sector return ranks are not component breadth. The plan excludes KOSDAQ size/style indexes from
sector extrema and excludes rows with empty listed universes. Relative terminology remains valid
when all sectors are positive or all are negative.

The TOP3 form accepts only same-session `CURRENT_DIRECTIONAL` rows. It canonical-name deduplicates
before ranking and uses the stable order `(return, canonical sector name, source ref)`, descending
for strong and ascending for weak. Fewer than three safe rows remain fewer than three; the renderer
does not duplicate or carry forward sectors to fill a slot. Ranking is backend-owned and AI cannot
reorder it.

## Length Ownership

Current-session KR structure remains ahead of FX and global context. Under length pressure the
renderer reduces repetitive macro, prior-US context, redundant explanation, and verbose next-check
wording before dropping selected size/style or sector-extrema claims.

## Validation

`validate_kr_market_evidence_utilization` fails a candidate when a `SELECTED_REQUIRED` claim is not
present. It also rejects user-facing `leader` or `laggard`. Historical run-42 is the frozen negative
fixture: its delivered message is unchanged and must fail the new required-consumption policy,
while repaired AI and fallback previews must pass with identical selected source refs.

No provider acquisition, numeric-registry policy, flow reconciliation, concentration eligibility,
Price Structure v3, US market digest, business-thesis persistence, or delivery behavior is owned by
this policy. `KR_MARKET_SECTOR_TOP3_ENABLED` defaults OFF; changing it requires the separate
dedicated-test-sink rollout gate.
