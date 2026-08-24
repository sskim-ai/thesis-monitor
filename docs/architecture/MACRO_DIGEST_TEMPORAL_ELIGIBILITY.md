# Macro Digest Temporal Eligibility

## Contract

`macro-digest-temporal-eligibility-v1` separates provider/source validity from eligibility to
describe an observation as a new daily digest signal. It extends the existing `observed_at`,
`retrieved_at`, `frequency`, `market_session`, `quality_status`, and exchange-calendar metadata;
it is not a second macro truth store.

The architecture trace confirmed **Branch B**. Source dates and coarse freshness already existed,
but `MacroBriefing` dropped frequency and downstream consumers treated `fresh` as sufficient for
`today_signal`, important changes, macro-to-ticker impacts, and current-language rendering.

## Temporal Roles

| Role | Daily signal | Important changes | Regime/state | Rendering |
|---|---:|---:|---:|---|
| `CURRENT_OBSERVATION` | yes | yes | yes | current wording allowed |
| `PRIOR_MARKET_SESSION` | no | yes, with explicit prior-session label | yes | `직전 거래일(M/D)` |
| `REFERENCE_LAGGING` | no | no | yes when source quality permits | background/reference only |
| `STALE_FOR_DAILY_SIGNAL` | no | no | source policy only | suppressed from daily delta |
| `UNAVAILABLE` | no | no | no | unavailable |

`quality_status=fresh` never implies `CURRENT_OBSERVATION` by itself.

## Cadence And Session Logic

- `SPY`, `QQQ`, `IWM`, and `SOXX` are XNYS-session-bound. Their observation date is compared with
  the authoritative latest completed XNYS session and the previous briefing.
- FRED market/macro series are release-bound. A new observation date, or an explicit revised value
  for the same occurrence, may be current even when the cash-equity market is closed.
- ECOS `KeyStatisticList` currently assigns collection date to `USDKRW`; it does not expose a
  verified source occurrence date. It is therefore reference-only for daily deltas.
- Unknown cadence fails to reference-only. No universal 30/60/90-day rule is introduced.
- XNYS early closes use the exchange calendar's actual session close, not a fixed 16:00 close.
- Existing KRX night-futures session-pairing and stale gate remain authoritative and unchanged.

## State Versus Delta

The existing macro regime can retain valid older facts as background state. Daily axes are
separately recomputed from `CURRENT_OBSERVATION` facts only. Market-thesis `today_signal`, macro
shocks, and ticker impacts consume those daily-eligible facts. No current fact means a neutral
stored signal with explicit no-new-observation rationale; it does not change the longer-term thesis
state or confidence by itself.

## Consumption

`app/macro/temporal.py` builds one machine-readable context per briefing. `app/macro/service.py`
passes its current series and daily axes to shocks, theses, impacts, and the briefing builder.
The briefing preserves frequency plus the per-observation decision and the aggregate context.

Deterministic digest rendering:

- uses current facts as current changes;
- permits prior-session returns only with compact date labeling;
- suppresses reference/stale facts from important changes and current signals;
- changes `오늘 한 줄` / `중요한 변화` to `현재 한 줄` / `직전 거래일 맥락` when no current
  observation exists.

AI market context receives the same temporal contract, current/prior/reference Fact-ID partitions,
and current-only `key_change_fact_ids` and transmission candidates. Numeric facts remain available
for properly labeled background context; their temporal role is not erased.

## Legacy Compatibility

`macro-temporal-legacy-rehydration-v1` is a non-destructive compatibility view for persisted
briefings created before the temporal contract was stored. It derives roles from the existing
observation identity, cadence, market calendar, briefing cutoff, and the previous briefing when one
exists. The source briefing is deep-copied and never rewritten.

- A session-bound item matching the latest completed XNYS session is
  `PRIOR_MARKET_SESSION` when prior identity is unavailable; it is never defaulted current.
- A release-bound item becomes `CURRENT_OBSERVATION` only when both its observation and retrieval
  dates prove publication after the previous briefing cutoff.
- Reference-only and unknown-cadence items remain `REFERENCE_LAGGING`.
- Missing observation identity is `UNAVAILABLE`; older session data is
  `STALE_FOR_DAILY_SIGNAL`.

Daily digest, deterministic fallback, market intelligence, macro thesis sanitation, and AI semantic
validation consume this same derived view. Persisted legacy evidence and new-contract briefings keep
their original identities.

## Validation

The AI semantic gate rejects:

- reference, stale, or unavailable facts in `important_changes`;
- prior-session facts without explicit historical/session wording;
- `오늘`, `간밤`, or current-movement wording when all linked facts are non-current.

It allows explicit prior-session wording and genuinely new official macro releases during a closed
cash-equity session. Existing numeric provenance, runtime quality thresholds, schema 4, Public
Action 0.4.5, and all unrelated market/financial validators are unchanged.
