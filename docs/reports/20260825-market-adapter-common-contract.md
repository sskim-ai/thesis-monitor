# Market Adapter Common Contract

- Contract: `market-context-adapter-v1`
- Implementation: `7a210efe101547c1981b934fbf3dc867bc3e6426`
- Input: existing canonical market Fact catalog and optional `market-cross-section-v1`
- Output model: one `NormalizedMarketContext` for KR and US

## Gate Results

- `MARKET_ADAPTER_COMMON_CONTRACT = PASS`
- `KR_US_REASONING_SCHEMA_COMMON = PASS`
- `MARKET_CONTEXT_FACT_BOUNDARY = PASS`
- `MARKET_CONTEXT_HIDDEN_ARITHMETIC = 0`
- `MARKET_CONTEXT_UNIT_CONFLICT = 0`
- `MARKET_CONTEXT_TEMPORAL_ERRORS = 0`

The contract carries indices, breadth, size context, sectors, market-wide flow, concentration,
deterministic relations, session/publication state, and explicit gaps. Missing is Unknown, not zero.
Fact identity/date, cross-section market/cutoff, relation inputs/arithmetic, and market-specific unit
semantics are validated before exposure.

The adapter is a view over the existing truth store. It creates no parallel provider cache and does
not recalculate macro Facts. Public Action, output schema, fallback, and Telegram payload shape are
unchanged.

