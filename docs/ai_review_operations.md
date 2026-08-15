# Codex Scheduled Daily Review Operations

The daily AI review keeps the official assessment in `shadow` mode. It reads backend-verified local
packets and never changes the official assessment. During the separately gated five-success-day
delivery pilot, the backend may combine a validated narrative with deterministic status and numbers;
the Codex task itself never writes notification state. It does not use `OPENAI_API_KEY`, Responses
API, Chat Completions API, or external web research.

## Schedule

All times are Asia/Seoul.

| Task | Time | Purpose |
| --- | --- | --- |
| US primary | 08:15 | Poll packet readiness through 08:20, then process it with a 10-minute lease. |
| US backup | 08:30 | Reclaim an interrupted primary after its short lease. |
| KR primary | 16:15 | Process the successful Korean close packet. |
| KR backup | 16:55 | Reclaim after the primary's 30-minute lease has expired. |

Every invocation begins with a pending scan. Completed packet and policy combinations are no-ops.
Shadow tasks may catch up an eligible packet from the preceding 24 hours. KR retains the 30-minute
lease and 40-minute backup delay. The US primary explicitly uses a 10-minute lease; its 15-minute
backup delay preserves reclaim safety while supporting the fast morning path.

Every claim has a UUID and a claim-specific temporary output. Lease expiry permits reclaim but does
not invalidate the worker by itself. Once a backup creates a new claim, the prior worker is fenced and
cannot finalize, even if it later recovers.

## Desktop Requirements

For local-project Scheduled Tasks, verify all four conditions:

1. The Mac mini is powered on and connected to the network.
2. The ChatGPT desktop app is running and signed in to Codex.
3. The scheduled task points to the live local checkout of `sskim-ai/thesis-monitor`.
4. The task is active and has workspace-write access only.

The exact names, prompts, schedules, and verification checklist are maintained in
[SCHEDULED_TASK_CONTRACTS.md](operations/SCHEDULED_TASK_CONTRACTS.md). Do not create standalone web
duplicates when the local-project tasks are absent from the accessible task list.

Closing the desktop app is an AI shadow failure, not a deterministic-monitoring failure. Existing
monitoring and Telegram continue independently.

## Manual Checks

```bash
.venv/bin/python -m app.jobs.ai_review health --market us
.venv/bin/python -m app.jobs.ai_review health --market kr
```

A task claims work with:

```bash
.venv/bin/python -m app.jobs.ai_review claim --market us --owner manual-check
```

The claim result contains `claim_id`, packet path, and a claim-specific temporary output path. The
scheduled model reads `knowledge-index.md`, the routed sections of the full Knowledge mirror, and only
canonical packet facts. It writes only the temporary JSON and finalizes it with:

```bash
.venv/bin/python -m app.jobs.ai_review validate --packet-id PACKET_ID --claim-id CLAIM_ID
```

Claim, reclaim, final promotion, and claim cleanup are serialized by a stable per-packet POSIX
`flock` under `data/ai_review/locks`. The lock is held only for short filesystem mutations; Codex
analysis and schema validation run outside it. Lease expiry permits another worker to reclaim the
packet, but an expired worker may still finish while its claim remains current. Once a backup writes
a new claim ID, the older worker cannot promote its claim-specific temporary output or remove the
new claim. This guarantee assumes the configured Mac mini local POSIX filesystem, not a network
filesystem with unknown lock semantics.

Files ending in `.json.tmp` are incomplete and are never considered completed. Every output records
the analysis policy, both Knowledge versions/checksums, frameworks used, fact references, and final
numeric claims. For policy v3.9 drafts, Codex places numeric placeholders and `numeric_fact_refs`;
the backend renders those occurrences and generates the final schema-4 claims before validation.

## Five-Day Single-Delivery Pilot

`AI_REVIEW_PILOT_ENABLED=true` enables a market-scoped delivery gate while
`AI_REVIEW_MODE=shadow` remains unchanged. The deterministic run queues and snapshots its exact
messages but marks only that market session as held. A validated Codex output releases one combined
AI-assisted market message and one combined message per stock. The official status, warnings,
valuation, price, supply, and data cautions remain deterministic.

KR holds after the 16:05 close run, uses the 16:15 primary and 16:55 backup, and releases the stored
deterministic set at 17:10 if no valid AI output exists. US starts deterministic work and KRX fetch at
08:05, uses the 08:15 primary and 08:30 backup, and falls back at 08:40. A validated AI delivery and deterministic
fallback are mutually exclusive for one packet. A late AI result after fallback is archived only.
Once AI-assisted delivery has started, Telegram failures resume that same rendered content and never
switch to a full deterministic report mid-message.

Install `ops/com.seungsoo.thesis-monitor.ai-review-fallback.plist` for the two local fallback checks.
Install `ops/com.seungsoo.thesis-monitor.ai-review-delivery-retry.plist` for bounded retries of the
same finalized text at 08:22, 08:25, and 08:30. These retries never rerun analysis or rendering.
Exact deterministic, AI, comparison, chart context, price transition, quantitative-grounding,
rendered Telegram, and delivery-result artifacts are stored in `data/ai_review/pilot/history`. Only
AI-assisted sessions whose validation, delivery, and archive all complete increment the market's
success counter. Pilot v1 and v2 history is preserved. Market-intelligence Pilot v3 uses
`data/ai_review/pilot/state-v3.json` and starts each market at 0/5. Each market returns to
deterministic delivery after five successful v3 packets. This does not activate Production Assist.

## Phase 3 Review Contract

Output schema `2` and analysis policy `daily-review-v3.2` separate company identity from thematic
exposure. The primary industry framework comes from verified structured company industry, sector,
business model, or revenue-source fields in that order. Every active company has a profile provenance
record with quality and a source or documented limitation. Thesis wording can add a routed secondary
framework, such as Hyperscaler CAPEX transmission, but cannot replace a high-confidence primary
framework. Ambiguous identity stays on the general framework instead of being guessed from a ticker
or theme.

Every investment-related prose number is occurrence-bound. Its claim records the exact `fact_id`,
`field_path`, backend value, unit, semantic type, prose `text_ref`, and displayed usage. A claim cannot
cover the same token in another prose field or reuse a price as a growth rate. Only deterministic
registry variants, including the existing KRW compact formatter and approved percentage rounding,
may differ from the raw backend value.

Numeric prose also fails closed by semantic registry. Only entries marked `registered=true` and
`prose_allowed=true` may be cited. Revenue, margin, price, flows, valuation multiples, FX, and night
futures each have separate labels and units; unknown or audit-only semantics cannot use a generic
label fallback.

The `daily-review-v3.2` Shadow cohort started only after active-company profile coverage, routing smoke,
numeric-semantic coverage, Scheduled Task activation, and exact operational-checkout revision are
verified. Earlier results remain history but do not count toward the new 5-10 trading-day quality
window.

Verified company profiles can be refreshed without a schema migration:

```bash
.venv/bin/python -m app.jobs.populate_company_profiles --dry-run
.venv/bin/python -m app.jobs.populate_company_profiles
```

The first command checks the dynamically discovered active universe; the second persists official
identity fields and atomic provenance sidecars. Rerun after a confirmed merger, spin-off, or segment
reorganization, or when a profile's `verified_at` warrants review. A thesis-version change or news
theme is not a profile-refresh trigger.

## Phase 4/5 Dual-Knowledge Review Contract

Output schema `3` and analysis policy `daily-review-v3.5` keep Investment Knowledge v3 as the
fundamental, valuation, and data-safety authority and add Stock Chart & Value Analysis Knowledge v1 as
a separate OHLCV interpretation reference. The two source files are never merged. Backend validated
facts and Investment Knowledge safety rules take precedence over OHLCV outputs and chart examples.
Codex does not calculate indicators, fair value, target prices, support, resistance, Elliott waves,
Fibonacci levels, ATR, or risk/reward.

The OHLCV Analyst supplies adjusted daily, weekly, and monthly bars plus available Bollinger bands,
volume ratio, RSI, MACD, and Korean investor-flow horizons. AI packets contain compact chart summaries,
not raw bar history. The structure engine consumes those bars outside the AI Review service; any
structure that lacks sufficient history or confirmation remains an explicit unknown. Stale chart
timeframes are not routed into analysis or registered as prose-eligible numeric facts. Adjusted chart
prices remain separate from unadjusted historical-valuation prices.

`ohlcv-structure-v2` deterministically supplies Wilder ATR14, Local-Pivot zones and boxes, an
independent ATR-ZigZag Major Swing stream, Major-Swing-only Elliott/Fibonacci anchors, structural
invalidation, nearest-resistance risk/reward, and an internal chart state. Full pivot/swing audit stays
in the assessment price context; AI packets receive compact nearest zones, selected anchors, state,
and blocking unknowns. Local Pivots never feed the Major Swing detector. Chart invalidation never
mutates thesis invalidation, and chart states are not trading commands.

Price-rule transitions are deterministic and thesis-version isolated. A crossed confirmation price
advances the review to hold/retest/volume/supply questions without changing the business thesis.
Persistent thesis rules are not rewritten by Codex. Korean positioning remains split into 1-day,
5-day, and 20-day semantics; flow changes never alter the fundamental status by themselves.

Schema 3 requires integrated sections for core judgment, business and earnings, price and positioning,
supply, valuation, priority watches, next checks, and material unknowns. Safe numbers stay bound to
their exact fact, semantic, text location, and approved display. Quantitative-grounding telemetry flags
sections that avoid available evidence, but missing data never causes invented numbers. Integrated
Pilot v2 historically rendered deterministic status and verified facts with validated AI interpretation once; it
does not append the full deterministic report below the AI narrative.

## Phase 6 Market Intelligence Contract

Output schema `4` and analysis policy `daily-review-v3.8` retain deterministic market-fact
selection and verified portfolio transmission. The market packet now inventories indices,
sector proxies, rates, real rates, inflation expectations, credit, FX, oil, volatility,
liquidity, breadth, and market-wide flows. Only fresh or revised backend observations become
facts. Missing and stale categories remain explicit unknowns; Codex never fills them from
the web or general knowledge.

The service deterministically calculates approved relative-performance facts and selects
two to four material changes. It groups the session universe from verified company profiles
and allows market-to-portfolio links only when backed by existing macro-impact evidence or
the explicit semiconductor relative-performance contract. Every link is context, never
fundamental confirmation, and never changes an official thesis state.

Market numbers use the same exact prose-location and fail-closed semantic registry as stock
numbers. Schema 4 requires portfolio transmission and next checks to cite allowed market
facts. Grounding telemetry flags generic summaries, ungrounded market facts, and unsupported
portfolio transmission.

Pilot validation now rejects zero numeric claims when a market or stock has at least four safe,
prose-eligible anchors. Fresh backend-selected KRX night-futures facts are mandatory market evidence;
partial or unavailable contracts add a compact caution without blocking analysis after 08:20.

`ai-assisted-pilot-renderer-v3` shows one-line judgment, important changes, market structure,
portfolio transmission, next confirmation, and material data limits. It omits analysis-method
narration, raw provider metadata, market-assumption audit prose, and the duplicated full
deterministic market report. The exact packet, deterministic report, AI review, grounding
report, rendered message, and delivery result remain archived.

Pilot v3 resets the KR and US counters because market and stock messages now form one materially
different user experience. The state file is not backfilled from earlier cohorts. A session increments
only after validation, full AI-assisted delivery, and archive completion.

## Phase 7.1 Numeric Binding Contract

Analysis policy `daily-review-v3.9` keeps output schema 4 and introduces a draft-only
`numeric-fact-ref-v1` contract. Codex chooses a registered `fact_id`, `field_path`, exact `text_ref`,
and placeholder. The backend resolves the canonical value, unit, semantic, security/financial basis,
source-aware label, and display formatter, then creates the occurrence-bound `numeric_claims` entry.
Codex does not transcribe or round the raw number.

The independent schema, fact, semantic, and occurrence validator still runs after binding. Missing,
ambiguous, unregistered, prose-disallowed, wrong-scope, or improperly formatted references reject.
Manual legacy claims remain supported but do not bypass validation. TWD financial statements are
separate from USD ADR price and per-security valuation basis.

Final validation rejection archives machine correction context and preserves the held deterministic
fallback. Fallback network retries use the same persisted deterministic payload with bounded retry
state. Neither rejection nor retry recollects data, regenerates a packet, reruns analysis, reformats,
or increments the Pilot counter. See `docs/architecture/NUMERIC_PROVENANCE.md`.

The durable cross-session continuation reference is `docs/PROJECT_HANDOFF.md`.

## Security Boundary

Scheduled review may write only under `data/ai_review`. It must not edit `app`, `tests`, `ops`, project
configuration, or the database. External browsing is disabled. Packet facts are allowlisted and user
facts exclude raw parser/provider metadata. Credentials and account identifiers are never packet
fields.

## Promotion Policy

Keep `AI_REVIEW_MODE=shadow`. Review factual
accuracy, omission of material events, modeled-versus-consensus wording, historical-comparability
guardrails, usefulness of next checks, and primary/backup recovery. Assist mode requires an explicit
user decision; it is never enabled automatically.
