# KR Valuation Repair and KR/US Market Adapter Completion

## Repository

- Instruction commit: `c058839c5e63a08c096bd6a9a1b2139290d17eb0`
- Stage A branch: `codex/kr-valuation-numeric-ref-repair`
- Stage A implementation/final: `b39c2ea38a8d5d3466889a9da394df05ad95701a` /
  `5e0a480b6bec2797c958574349984401dda85939`
- Adapter branch: `codex/kr-us-market-adapters`
- Adapter base/implementation: `5e0a480b6bec2797c958574349984401dda85939` /
  `7a210efe101547c1981b934fbf3dc867bc3e6426`

## Stage A

- `KR_VALUATION_NUMERIC_REF_REPAIR = PASS`
- `KR_VALUATION_REPLAY = PASS`
- Run-38 typed PBR refs rejected before/after: `2 / 0`
- Full candidate errors after repair: `0`
- Fallback/numeric/security-basis rules weakened: `0`

## Adapters

- `MARKET_ADAPTER_COMMON_CONTRACT = PASS`
- `KR_MARKET_ADAPTER = PARTIAL`
- `US_MARKET_ADAPTER = PARTIAL`
- `KR_US_REASONING_SCHEMA_COMMON = PASS`
- `MARKET_CONTEXT_FACT_BOUNDARY = PASS`
- Hidden arithmetic / unit conflict / temporal errors: `0 / 0 / 0`
- KR/US value add: `NO_MATERIAL_VALUE / NO_MATERIAL_VALUE`

KR run-38 correctly retains local index, breadth, sector/size, and market flow as Unknown. US
run-37 normalizes SPY/QQQ/IWM, SOXX, and two exact relative relations while breadth and participant
flow remain Unknown. No provider recollection occurred.

## Research Boundary

- Research seed adapters: `PASS`
- `PRODUCTION_RESEARCH_CONNECTOR = NOT_AVAILABLE`
- `OPEN_RESEARCH_LIVE_CANARY = BLOCKED_CONNECTOR`
- `OPEN_RESEARCH_PRODUCTION_INTEGRATION = 0`

## Validation And Safety

- Focused adapter/packet/docs: PASS
- Full pytest: `1537 passed`, one upstream warning
- Ruff / diff / JSON: PASS
- Implementation Actions: run `32832505782`, Test/Lint PASS
- Public Action / operationId / schema: `0.4.5 / 20/20 unique / 4`
- Telegram / manual task / Pilot / DB / archive mutations: `0 / 0 / 0 / 0 / 0`
- Production Assist: `OFF`
- Open P0 / material P1: `0 / 0`

## Decision

- `STRUCTURED_MARKET_ADAPTER_PRODUCTION = DEPLOYED_PENDING_NATURAL`
- `COMMON_MARKET_ADAPTER_V1 = PRODUCTION_PENDING_NATURAL`
- `COMMON_OPEN_RESEARCH_V1 = BLOCKED_CONNECTOR`
- `NEXT_ACTION = WAIT_FOR_US_STRUCTURED_ADAPTER_NATURAL_CANARY`

The three 2026-08-26 natural reports remain intentionally absent until the scheduled US run exists.
