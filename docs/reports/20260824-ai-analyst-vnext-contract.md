# AI Analyst vNext Shadow Contract

- Contract: `ai-analyst-vnext-shadow-v1`
- Execution: `SHADOW_OFFLINE_ONLY`
- Objectives: `select`, `connect`, `synthesize`, `omit`, `explain_boundary`
- Production import/wiring: `0`

## Boundary

The vNext layer consumes an already validated rendered candidate and never recalculates a Fact. It
may rank sections, select exact source spans, synthesize by retaining an already validated relation
sentence, omit low-value numeric recitation, and deduplicate identical next-check/Unknown items.

It may not create arithmetic, numbers, causal predicates, price levels, valuation denominators,
participant identities, temporal roles, Inventory relations, FCF relations, or Trade AR output.
Every non-heading vNext line must be an exact substring of the current validated AI message.

## Dynamic Blocks

`오늘 판단` normally remains. `왜 중요한가`, `가격/Valuation`, `수급/포지셔닝`,
`리스크/경고`, and `다음 확인` are emitted only when their selected source span is useful. A supply
tuple may be omitted while its already validated cross-horizon conclusion is retained. Identical
next-check and Unknown content is rendered once.

## Advisory Gate

`AI_ANALYST_VALUE_ADD = PASS` requires factual parity, no unsupported numeric or causal claim, at
least one supported value-add type, material structural difference from deterministic/current text,
shorter output, and zero duplicate next-check/Unknown items. This gate is advisory and has no
production effect in this phase.
