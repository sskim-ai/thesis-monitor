# Daily Thesis Monitoring

## Custom GPT behavior

When the user says a phrase such as "종목 앞으로 모니터링해줘":

1. Resolve the company to a canonical ticker.
2. Read company profile, earnings checkpoints, and recent thesis events.
3. Draft a concrete thesis with strengthening, weakening, and invalidation signals.
4. Call `monitorStock` with the ticker, company, and structured thesis.
5. Confirm the stored thesis version to the user.

When drafting or revising the thesis, include conditional `macro_exposures`
such as real yields, USD/KRW, oil, credit spreads, or hyperscaler CAPEX. An
automatically inferred exposure remains marked `review_required=true` until a
user-approved thesis version replaces it.

When the user asks to stop monitoring, call `stopMonitoringStock`. Deactivation preserves all thesis
versions and assessment history.

## Daily decision rules

- `strengthened`: provide separate new-buyer and holder-management views.
- `weakened`: distinguish thesis damage from price support and assign a risk level.
- `mixed`: preserve both positive and negative evidence for review.
- `invalidation_candidate`: alert but keep monitoring until the evidence is strong enough.
- `invalidated`: only confirmed when an explicit invalidation signal matches a high-relevance filing
  from OpenDART, SEC EDGAR, or company IR. The watchlist item is then deactivated, not deleted.
- `no_material_change`: store history and include the stock in the daily per-stock analysis without
  creating a separate material-event alert.

All assessments preserve confirmed evidence URLs and keep technical price position separate from
fundamental fair-value conclusions.

Each dated assessment also stores a cumulative `thesis_snapshot`: the approved base thesis, current
status, and deduplicated supporting, weakening, and invalidation evidence known on that date. The base
thesis changes only when the user or Custom GPT submits a revised version.

## Runtime and recovery

- Primary schedule: every day at 07:50 Asia/Seoul.
- Morning delivery gate: KRX night futures are queried at 08:00 and every five minutes through
  08:45. Analysis remains fixed at its 07:50 result; only night-futures context and pending U.S.
  morning notifications are refreshed.
- Macro collection and assessment run first; provider failure is isolated so stock monitoring still runs.
- Each macro provider fails independently and missing sources are shown as data-quality warnings.
- Every active stock receives a dated assessment, including no-material-change days.
- After all assessments are saved, one market digest and one analysis per active stock are queued for Telegram.
  U.S. morning deliveries remain queued until both expected-session KRX contracts are verified or
  the 08:45 deadline applies the existing partial/unavailable rendering policy.
- Strengthening, weakening, review, and invalidation events remain separate material-event alerts.
- Provider calls retry with exponential backoff.
- OHLCV and event-provider partial results are retained.
- Notification delivery uses a channel-specific persistent outbox and remains `dry_run` until Telegram is configured.
- Successful date-level runs are idempotent.

## Macro decision flow

1. Collect observations and dated events with source URLs and freshness status.
2. Classify material moves as rate, inflation, liquidity, credit, risk, energy,
   or technology CAPEX shocks.
3. Score growth, inflation, liquidity, financial conditions, risk appetite, and
   earnings momentum internally. The user message explains these axes in natural language.
4. Update competing macro theses without invalidating them from a single daily move.
5. Apply each stock thesis's signed exposure, weight, and transmission channel.
6. Save all stock assessments, build the complete daily digest, then send the digest and material alerts.

The default morning path does not call OpenAI or another LLM. Significance thresholds, macro
interpretation, stock selection, and Korean message rendering are deterministic. Stale, partial, and
provisional observations do not create a directional market signal; they lower confidence and appear
in the final data-quality section.

The three optional source keys are `FRED_API_KEY`, `EIA_API_KEY`, and
`ECOS_API_KEY`. Without them the run remains operational but the briefing is
marked `partial` and explicitly lists the unavailable sources.
