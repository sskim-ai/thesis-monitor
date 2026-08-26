# Price Structure Shadow Policy

## Boundary

The multi-timeframe structure service is imported only by tests and the archive evidence generator.
It is not imported by production packet assembly, AI review delivery, fallback rendering, public
Action handlers, or monitoring-state mutation paths.

## Allowed

- Read-only canonical OHLCV acquisition.
- Completed-bar evidence construction.
- Structured ID selection and validation.
- Deterministic Fibonacci and bounded confluence.
- Sanitized shadow archive and before/after review.

## Prohibited

- Telegram or current message changes.
- Price-rule, warning, assessment, or business-thesis mutation.
- AI-provided Fibonacci prices or distance arithmetic.
- Target, stop, buy, or sell language.
- Cross-timeframe relabeling.
- Partial weekly/monthly anchor confirmation.
- Wide-tolerance confluence manufacturing.

## Promotion State

Passing archive gates sets `AI_FIBONACCI_MULTI_TIMEFRAME_STRUCTURE =
INTEGRATED_READY_NOT_ARMED`. A separate bounded enablement instruction is required before any
user-visible route may consume this shadow output.

## Variable AI Boundary

Variable anchor selection is permitted only through `price-only-ai-anchor-packet-v1`. The archive
runtime receives public completed OHLCV, deterministic candle features, canonical pivot/zone IDs,
and bounded segment refs. It receives no private/user/account/thesis fields and no prior anchor or
Fibonacci result. Typed output contains IDs only; backend validation and deterministic calculation
remain authoritative.

Runtime unavailability, timeout, malformed JSON, wrong IDs, or invalid chronology fail closed per
timeframe. Deterministic SR remains available, invalid Fibonacci is omitted, and independent valid
timeframes continue. Current production imports and user-visible output remain unchanged.
