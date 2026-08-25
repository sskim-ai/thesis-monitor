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
