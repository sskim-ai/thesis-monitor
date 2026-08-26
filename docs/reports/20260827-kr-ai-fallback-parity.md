# KR AI / Fallback Parity

Both paths now consume `KrMarketDigestPlan` produced from `market-context-adapter-v1`.

- Deterministic `DailyDigest` renders all selected plan claims before FX/global context.
- AI evidence locking converts the same claims to evidence atoms and bounded analysis items.
- Exact breadth/flow numerics remain backend-owned; the plan uses deterministic direction/relation
  prose and does not ask the model to calculate.
- Concentration scopes used by the plan are empty.

`AI_FALLBACK_LOCAL_FIRST_PARITY=PASS` and
`AI_FALLBACK_NUMERIC_SAFETY_PARITY=PASS` in retrospective replay. Natural parity remains pending
until the next scheduled KR close.

