# Price Structure v3 AI Feedback Loop

## Contract

`price-structure-v3-ai-feedback-loop-v1` connects a variable-AI ID selection to the deterministic
shadow engine:

```text
canonical bars -> degree candidates -> AI selected ID -> strict validator
-> deterministic Fib -> SR maps -> cross-timeframe confluence -> shadow render
```

The selection must echo ticker, degree, cutoff, adjustment basis, and ordered endpoint refs. The
validator also verifies that the hypothesis exists and that no endpoint is after the replay
cutoff. AI never calculates a technical price.

## Failure Behavior

Invalid selection or valid abstention omits all wave-owned Fibonacci values. Deterministic pivot,
Bollinger, box, and prior-high/low SR survives, so the packet remains useful without guessing.
Every feedback archive records the input evidence hash, selected ID/degree, validator result, Fib
IDs, zone IDs, confluence IDs, and exact shadow render.

## Boundary

This loop is archive-only. It is not imported by the production packet, current renderer,
fallback, Telegram, Public Action, assessment persistence, or thesis mutation path.
