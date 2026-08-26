# Price Structure Wave Fibonacci v3

## Problem

The previous shadow model could choose a low/high pair per timeframe and calculate Fibonacci
levels without proving that the pair belonged to a coherent structural wave. It also used shorter
history budgets than the canonical `1200D / 600W / 300M` requirement.

## Decision

`price-structure-wave-fibonacci-v3` is an archive/test-only common KR/US core. It processes
completed adjusted bars in this order:

```text
monthly structure and primary-wave candidates
-> weekly endpoint confirmation
-> independent daily/weekly/monthly SR maps
-> wave-owned Fibonacci families
-> cross-timeframe synthesis
```

The implemented wave scope is bullish standard impulse only. Candidate endpoints come from
confirmed or explicitly provisional pivots. Elliott hard rules filter candidates before
Fibonacci fit contributes soft ranking. `NONE` and `AMBIGUOUS` are valid fail-closed outcomes.

Full-count ambiguity no longer requires deleting every Fib family. The deterministic dependency
registry tests each formula against the complete supplied ambiguity set. Exact-invariant and
existing-tolerance price-equivalent families survive; materially variant families are omitted.
Confluence is rebuilt only after this filtering step.

The bounded repair adds `ohlcv-bar-completion-v1`, provider-native 1200-day backfill, explicit
grand/current/intermediate degree separation, and a strict AI-selection feedback path. Partial
bars remain available for current context but cannot confirm pivots. A validated AI ID now owns
the subsequent deterministic Fib/confluence/render computation.

The core returns deterministic IDs, source provenance, hypothesis status, per-timeframe zones,
cross-timeframe confluence, and a monthly-to-daily shadow rendering order. AI may select only from
listed hypothesis IDs and cannot calculate a price.

## Why

Structural ownership keeps Fibonacci from manufacturing its own anchors and preserves the
difference between primary-cycle context, recovery barriers, and tactical price structure.

## Rejected Alternative

Generic low-to-high Fibonacci per timeframe, ticker-specific wave hard-coding, broad tolerance
widening, and forced Elliott labels were rejected.

## Safety Constraint

The module has no production import, route, packet, fallback, Telegram, task, assessment, or DB
integration. `PRICE_STRUCTURE_WAVE_FIB_V3 = INTEGRATED_READY_NOT_ARMED` only after the complete
shadow evidence and CI pass; any later user-visible enablement remains a separate decision.
