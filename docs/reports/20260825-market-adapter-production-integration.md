# Market Adapter Production Integration

- Branch: `codex/kr-us-market-adapters`
- Base: `5e0a480b6bec2797c958574349984401dda85939`
- Implementation: `7a210efe101547c1981b934fbf3dc867bc3e6426`
- Contract: `market-context-adapter-v1`
- Focused adapter/packet tests: `202 passed`
- Full pytest: `1537 passed`, one upstream deprecation warning
- Ruff / `git diff --check`: `PASS / PASS`
- Implementation GitHub Actions: run `32832505782`, Test/Lint `PASS`

The packet builder attaches a sanitized `adapter_context` derived from its existing market Fact
catalog. Partial fields remain Unknown. The sidecar is excluded from immutable packet hashing because
its information is already owned by canonical source Facts; generated time cannot create duplicate
packet identities.

## Unchanged Boundaries

- Public Action: `0.4.5`
- output schema: `4`
- fallback renderer: unchanged
- Telegram schema/delivery count: unchanged
- canary limits: `1/2/3`
- Trade AR / Inventory / Phase 9.0E: unchanged
- Open Research production integration: `0`

Exact implementation-SHA CI passed. With clean linear promotion and operating health confirmation,
the final state is `STRUCTURED_MARKET_ADAPTER_PRODUCTION = DEPLOYED_PENDING_NATURAL`.
