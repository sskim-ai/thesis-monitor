# Variable AI Swing Anchor Selection

## Status

`variable-ai-swing-anchor-selection-v1` is an archive-shadow contract. It closes the distinction
between the old deterministic reference harness and an actual variable AI selector without arming
any production route.

## Ownership

```text
completed adjusted OHLCV
  -> deterministic pivots and SR candidates
  -> price-only rich evidence packet
  -> variable AI chooses canonical IDs and bounded reason categories
  -> backend validates ticker, timeframe, cutoff, identity, role, and chronology
  -> existing Decimal Fibonacci and confluence engine
  -> archive shadow
```

The AI never provides a price, ratio, Fibonacci level, target, stop, valuation, or thesis. Stage 1
selects IDs only. Stage 2 interpretation remains outside this repair.

## Output

Each monthly, weekly, and daily slot returns `SELECTED`, `INSUFFICIENT_STRUCTURE`, or `AMBIGUOUS`;
optional canonical support/resistance IDs; a bounded Fibonacci mode and pivot IDs; at most one
alternative; one to three reason categories; evidence refs; confidence; and a rationale of at most
240 characters. Extra fields are rejected.

## Validation

- Output ticker must match the packet ticker.
- IDs must exist in the same ticker and timeframe.
- Support and resistance roles must match their canonical zone roles.
- Low must precede high and have a lower canonical price.
- Extension correction must be a later low above the primary low.
- Every selected ID must also appear in `evidence_refs`.
- Alternative anchors receive the same identity and chronology checks.
- Future or unconfirmed pivots never enter the packet.

Wrong-ticker output rejects all slots. A bad single slot rejects only that timeframe. Malformed,
timed-out, refused, or unavailable runtime output fails closed. In every fallback, existing
deterministic SR survives, Fibonacci for that timeframe is omitted, and the packet continues.

## Runtime Trial

The approved archive route is the signed-in local Codex runtime with public-field restrictions. The
trial uses `gpt-5.6-sol`, high reasoning, an ephemeral session, a read-only sandbox, a strict JSON
schema, and no tools or external data. It adds no provider or paid API key. Frozen packets are reused
across repetitions; the prompt contains no previous/reference anchor or Fibonacci result.

## Isolation

The service is not imported by production packet assembly, scheduled AI tasks, fallback, Telegram,
Public Action, or assessment mutation. A separate instruction is required to arm any visible route.
