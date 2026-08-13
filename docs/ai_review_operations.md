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
| US primary | 08:50 | Process the packet finalized after the morning KRX gate. |
| US backup | 09:30 | Reclaim after the primary's 30-minute lease has expired. |
| KR primary | 16:15 | Process the successful Korean close packet. |
| KR backup | 16:55 | Reclaim after the primary's 30-minute lease has expired. |

Every invocation begins with a pending scan. Completed packet and policy combinations are no-ops.
Shadow tasks may catch up an eligible packet from the preceding 24 hours. The scheduling invariant is
`backup_delay > claim_lease + safety_margin`: the current 40-minute delay exceeds the 30-minute lease
by 10 minutes and the configured minimum safety margin is 5 minutes.

Every claim has a UUID and a claim-specific temporary output. Lease expiry permits reclaim but does
not invalidate the worker by itself. Once a backup creates a new claim, the prior worker is fenced and
cannot finalize, even if it later recovers.

## Desktop Requirements

For local-project Scheduled Tasks, verify all four conditions:

1. The Mac mini is powered on and connected to the network.
2. The ChatGPT desktop app is running and signed in to Codex.
3. The scheduled task points to the live local checkout of `sskim-ai/thesis-monitor`.
4. The task is active and has workspace-write access only.

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
the analysis policy, both Knowledge versions/checksums, frameworks used, fact references, and numeric
claims.

## Five-Day Single-Delivery Pilot

`AI_REVIEW_PILOT_ENABLED=true` enables a market-scoped delivery gate while
`AI_REVIEW_MODE=shadow` remains unchanged. The deterministic run queues and snapshots its exact
messages but marks only that market session as held. A validated Codex output releases one combined
AI-assisted market message and one combined message per stock. The official status, warnings,
valuation, price, supply, and data cautions remain deterministic.

KR holds after the 16:05 close run, uses the 16:15 primary and 16:55 backup, and releases the stored
deterministic set at 17:10 if no valid AI output exists. US holds after the morning KRX gate, uses the
08:50 primary and 09:30 backup, and falls back at 09:45. A validated AI delivery and deterministic
fallback are mutually exclusive for one packet. A late AI result after fallback is archived only.
Once AI-assisted delivery has started, Telegram failures resume that same rendered content and never
switch to a full deterministic report mid-message.

Install `ops/com.seungsoo.thesis-monitor.ai-review-fallback.plist` for the two local fallback checks.
Exact deterministic, AI, comparison, chart context, price transition, quantitative-grounding,
rendered Telegram, and delivery-result artifacts are stored in `data/ai_review/pilot/history`. Only
AI-assisted sessions whose validation, delivery, and archive all complete increment the market's
success counter. Pilot v1 history is preserved. Integrated Pilot v2 uses a separate state file and
starts each market at 0/5; each market returns to deterministic delivery after five successful v2
packets. This does not activate Production Assist.

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
Pilot v2 renders deterministic status and verified facts with validated AI interpretation once; it
does not append the full deterministic report below the AI narrative.

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
