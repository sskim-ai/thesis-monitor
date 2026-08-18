# Phase 8.5.3 Natural Live Message Root Cause

## Evidence

- US packet: `2026-08-18-us-run-24-487c07bde4e1`
- KR packet: `2026-08-18-kr-run-25-23b5e31dc20e`
- Source: committed code plus immutable operating archive and read-only operating assessment DB
- Telegram replay sends: 0

## US Trace

`packet -> ready_for_ai -> AI output -> binder -> hard validator -> runtime quality -> fallback -> delivery`

- Natural runtime occurred and deterministic fallback delivered 14/14 at 08:40 KST.
- The final AI candidate passed numeric-label, identity, comparative, supply, financial-period, and valuation-evidence hard checks.
- Runtime quality rejected it for 3 literal duplicate groups and 7 semantic skeleton groups.
- The largest literal repeat was the stored-price-rule methodology sentence across 13 stocks.
- Three rejected claim artifacts exist before the final preserved candidate; bounded correction still left portfolio-level templates.

Classification: `AI_GENERATION / REPETITION / RUNTIME_QUALITY`.

## KR Trace

`packet -> ready_for_ai -> AI output -> binder -> hard validator -> runtime quality -> fallback -> delivery`

- Natural packet hard numeric and semantic validation had 0 errors.
- Runtime quality rejected the candidate for 5 literal duplicate groups and 7 semantic skeleton groups.
- Repeats concentrated in confirmation lifecycle methodology, supply-separation methodology, generic cash-conversion wording, and common observer phrasing.
- Two rejected claim artifacts exist before the final preserved candidate.
- Deterministic fallback delivered 8/8 at 17:10 KST; rejected AI sent was false.

Classification: `AI_GENERATION / REPETITION / RUNTIME_QUALITY`.

## Fallback Root Cause

The deterministic renderer in `notification_service._assessment_report` read `decision.new_observer_checks`, `decision.holder_checks`, and stored thesis price rules. The assessment already contained `monitoring_state.current.price_structure`, but fallback selection did not consume it. As a result, crossed confirmations remained labeled as future `상향 확인 가격`, while dynamic support, resistance, current-price RR, and chart invalidation were omitted.

Classification: `FALLBACK_RENDERER / LEGACY_PRICE_SELECTION`.

## Repair

- Added `current-price-context-v1`, a deterministic selector shared by runtime AI packets and fallback rendering.
- Added `runtime-message-specificity-v1` and exposed the existing `industry-specific-reasoning-v1` plan in natural packets.
- Kept the existing hard repetition threshold; added semantic-family telemetry for synonym-only methodology repeats.
- Updated the scheduled review skill to plan primary point, evidence, Unknown, and next confirmation before prose.
- Fallback now renders dynamic support/resistance, canonical current-price RR, chart invalidation, chart state, and registered confirmation lifecycle in that order.
- No renderer calculation, stale RR reuse, registered-rule support promotion, or ticker-specific production logic was added.
