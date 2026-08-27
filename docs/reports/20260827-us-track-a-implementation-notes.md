# US Track A Implementation Notes

- Run: `41`
- Packet: `2026-08-27-us-run-41-ae4f42c23abc`
- Target session: `2026-08-26`
- Implementation SHA: `069f002437163bff1df7aa6e258918c1777d5dfa`
- Replay mode: immutable archive read-only

- Branch: `codex/us-shared-market-digest-plan-repair`
- Commit: `c4b02a10c2b7da0184c7dba26c7c1db39344f258`
- Contract: `us-market-digest-plan-v1`
- AI and deterministic fallback consume the same ordered plan.
- Current core ETFs, RSP participation/style, sector dispersion, breadth state, and macro context have distinct typed slots.
- RSP is not exchange breadth; level-only facts do not acquire direction; pending breadth is not zero-filled.
- No ticker exception, threshold relaxation, numeric dump, or Price Structure v3 change was introduced.
