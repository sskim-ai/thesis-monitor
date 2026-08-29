# Cross-Market AI Decision Engine v1 Validation

## Lineage

- Source ZIP SHA-256: `8ee27fa924954fa24e40221abb6e9e7310e44c69643bac02c90680c6fb34a7fd`
- Exact instruction commit: `ec6ea8fa4449fd34961ecbbcf995064c46ff94a2`
- Base / previous main / operating: `7269120fb4d97abb61c5d5d5f91863f4c998e84b`
- Implementation: `f28d4bb3b8eacebe7fb48a3ca7800094711793eb`
- Implementation Actions run: `33231226457`, Test/Lint `PASS`
- Branch: `codex/20260829-cross-market-ai-decision-engine-v1`

## Engine

- Contract: `cross-market-ai-decision-engine-v1`
- AI route: signed-in local Codex CLI, archive-only, ephemeral/read-only
- Model / reasoning: `gpt-5.6-sol` / `xhigh`
- Current CLI batches: `10/10 PASS`; temporal CLI batches: `10/10 PASS`
- OHLCV feature families: `9`; full-history timeframe catalog: `78` facts
- D/W/M MACD contract: `PASS`; current availability `20/19/16`, with insufficient-history
  subjects explicitly unavailable rather than inferred
- OHLCV provider calls: `20` request, `20` success, `0` failure, `0` cache hit

## Decision Evidence

- Active universe: KR `7`, US/foreign `13`, total `20`
- Current shadow: `20/20 PASS`
- Distribution: BUY `2`, HOLD `18`, SELL `0`
- KR: `7/7 PASS`; US/foreign: `13/13 PASS`
- Exact numeric binding: automatic `54`, manual `0`, unresolved `0`
- Freeform numeric authority / AI-calculated features / AI-calculated multiples: `0 / 0 / 0`
- One-sided decision without opposing evidence: `0`
- Substantive cross-ticker repetition: `0`
- Average/max message characters: `1735.15 / 3013`

## Temporal Replay

- Subjects/checkpoints: `20 / 200`
- Accepted: `200/200`
- Status: `PARTIAL_SAFE`
- Look-ahead leak: `0`
- Decision changes / three-point flips / unexplained churn: `13 / 2 / 0`
- Full raw historical D/W/M and forward 20/60/120 diagnostics were not archived, so those
  diagnostics are suppressed and are not reconstructed from current data.

## Test Sink

- Dedicated non-production sink isolation: `PASS`
- Exact payloads: `20/20 PASS`
- Rate-limit recovery: exact remaining subset `18 + 2`
- Duplicate / orphan: `0 / 0`
- Production recipient sends / production intents: `0 / 0`
- Raw recipient IDs, secrets, tokens, and auth headers in repository reports: `0`

## Validation

- Focused tests: `7 passed`
- Full pytest: `1883 passed`, one upstream Starlette deprecation warning
- Full Ruff: `PASS`
- `git diff --check`: `PASS`
- Project-state JSON: `PASS`
- Investment Knowledge v3.1 checksum/mirror: `PASS`
- Chart Knowledge v1 checksum/mirror: `PASS`
- Public Action: `0.4.5`, unchanged
- Output schema: `4`, unchanged
- operationId: `20/20` unique
- Runtime production imports of new services: `0`
- Production user-visible behavior diff: `0`
- Local API/OHLCV health: `NOT_RUNNING`; no runtime import changed, so no restart was performed

## Safety And Gate

- Automated trade execution / order sizing: `0 / 0`
- Production packet / fallback / Scheduled Task changes: `0 / 0 / 0`
- Manual Scheduled Task / DB / assessment / Pilot mutation: `0 / 0 / 0 / 0`
- Production Assist: `OFF`, unchanged
- Open P0 / material P1: `0 / 0`
- P2: raw historical D/W/M archival, forward diagnostics, and operator wording review
- `DECISION_ENGINE_STATE = TEST_SINK_READY`
- `DECISION_CANARY_READINESS = PASS`
- `PRODUCTION_CANARY_ENABLED = false`
- `NEXT_ACTION = REVIEW_SHADOW_DECISIONS`

This PASS does not authorize a production canary. A bounded canary requires separate operator
review and explicit authorization.
