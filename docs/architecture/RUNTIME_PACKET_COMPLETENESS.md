# Runtime Packet Completeness

## Purpose

Runtime packet completeness distinguishes a deterministic value that is unavailable by contract
from one that was calculated but lost before validation. It does not make unavailable data
optional, relax validation, or let the renderer calculate a replacement.

```text
calculated
  -> monitoring state
  -> canonicalized
  -> packeted
  -> semantically registered
  -> bound to exact prose
  -> render-selected
  -> validated
```

## Current-Price RR Contract

`current_price_risk_reward_ratio` is distinct from
`support_entry_risk_reward_ratio`. The current-price value is calculated from the current adjusted
chart close, the nearest valid Strong/Medium resistance lower bound, and the current chart
invalidation:

```text
upside = nearest resistance lower bound - current price
downside = current price - chart invalidation
current-price RR = upside / downside
```

The calculation is unavailable when resistance or invalidation is unavailable, or when upside or
downside is non-positive. It never uses `abs`, a farther resistance for a better result, a previous
session's RR, a registered thesis level, or the support-entry scenario as a substitute.

## Availability States

| State | Meaning | Validator behavior |
|---|---|---|
| `READY` | Monitoring value, canonical Fact, and exact semantic registry row agree | RR claim may be selected and must bind exactly |
| `UNAVAILABLE_BY_CONTRACT` | Current-price RR cannot be calculated from valid structure | RR claim is excluded; a specific Unknown may be used |
| `BUG_MISSING_FACT` | Monitoring state has a calculated current RR but no canonical Fact | Fail closed |
| `BUG_INVALID_FACT` | Canonical RR differs from monitoring state | Fail closed |
| `BUG_MISSING_NUMERIC_PATH` | Fact exists but `fields.ratio` is not registered | Fail closed |
| `BUG_INVALID_NUMERIC_PATH` | Value, unit, semantic, display, or prose eligibility differs | Fail closed |

The exact path is:

```text
chart:structure:risk_reward:current_price
  -> fields.ratio
  -> unit x
  -> semantic current_price_risk_reward_ratio
  -> deterministic canonical display
  -> exact text_ref and usage
```

## Session Integrity

Chart freshness is based on the latest completed exchange session, not weekdays. XKRX and XNYS
calendars determine holidays and the preceding session. A chart dated to the latest completed
session is fresh even when the assessment date is a weekday exchange holiday. A genuinely older
chart remains stale and cannot create chart structure Facts.

Calendar data is bounded. Dates outside the packaged exchange-calendar range retain the previous
conservative weekday fallback rather than raising or fabricating a session.

## Ownership

- `market_session.py` owns exchange-session eligibility.
- `ohlcv_client.py` owns chart freshness and price-date compatibility.
- `ohlcv_structure_service.py` owns resistance, invalidation, and RR calculation.
- `monitoring_state_service.py` owns current/previous/delta separation.
- `ai_review_service.py` owns canonical chart Facts and required grounding.
- `numeric_semantic_registry.py` owns semantic and unit registration.
- `numeric_provenance_service.py` owns exact prose binding.
- the full validator owns fail-closed claim and grounding enforcement.
- the renderer assembles validated text and never calculates RR.

`runtime_packet_completeness_service.py` provides a reusable read-only preflight. It reports the
missing layer but does not silently remove a required Fact from the render plan.

## Natural-Live Boundary

A retrospective replay can prove the repaired code reconstructs an immutable packet correctly. It
cannot close Natural Live Validation. The next natural KR session must independently show packet
completeness, full-validator PASS, runtime receipt PASS, correct fallback/delivery behavior,
complete archive, exactly-once accounting, and acceptable message quality.
