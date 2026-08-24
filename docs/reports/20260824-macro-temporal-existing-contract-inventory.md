# 2026-08-24 Macro Temporal Existing-Contract Inventory

## Decision

`ROOT_CAUSE_BRANCH = B`

The repository already knew observation identity, coarse source freshness, and market-session
state, but it had no canonical role separating current daily evidence from prior-session and
reference evidence.

| Existing component | Defined/populated | Consumed | Gap before repair |
|---|---|---|---|
| `observed_at` | `MacroObservation`, all providers | storage, briefing, Facts | renderer did not use it for current wording |
| `retrieved_at` / `vintage_at` | storage | audit/source lineage | not a digest eligibility gate |
| `frequency` | provider observation and DB | storage freshness | dropped by `market_observation_to_dict` |
| `market_session` | market/night providers | briefing/session display | closed session did not distinguish prior/reference facts |
| `quality_status` | provider/storage | regime, digest, impacts, AI Facts | `fresh` was treated as daily-current |
| latest completed session | `us_market_session` | regime/session state | not applied per macro series; early close used fixed time |
| `today_signal` | `MacroThesis` | briefing/digest | derived from all fresh regime-axis observations |
| market Fact `as_of_date` | market-intelligence builder | numeric binding | no temporal role or daily-use permission |
| night-futures freshness | dedicated session-basis gate | digest/AI | correct and retained unchanged |

## Loss/Ignore Points

1. `app/macro/storage.py::_freshness_status` established provider-cadence freshness only.
2. `app/macro/regime.py::assess_macro_regime` reused every latest `fresh/revised` change as an axis.
3. `app/macro/theses.py::update_macro_theses`, `app/macro/shocks.py`, and
   `app/macro/impact.py` had no per-series current-delta permission.
4. `app/macro/briefing.py::market_observation_to_dict` preserved dates but dropped frequency and no
   temporal role existed.
5. `app/services/daily_digest.py::_usable` equated provider freshness with daily usability.
6. `app/services/market_intelligence_service.py::_selected_change_fact_ids` ranked all fresh Facts.
7. AI instructions and validation had no current/prior/reference language boundary.

## Minimum Chosen Scope

The repair adds one derived sidecar contract on top of existing observations. It does not add a DB
column, migration, provider, parallel store, arbitrary recency threshold, or ticker exception.
State/regime evidence remains intact; only daily-delta eligibility is newly separated.
