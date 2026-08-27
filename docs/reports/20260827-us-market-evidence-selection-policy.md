# US Market Evidence Selection Policy

- Run: `41`
- Packet: `2026-08-27-us-run-41-ae4f42c23abc`
- Target session: `2026-08-26`
- Implementation SHA: `069f002437163bff1df7aa6e258918c1777d5dfa`
- Replay mode: immutable archive read-only

The selection order is current market, participation/style, sector dispersion, official breadth, then macro. Near-flat current ETF returns remain selected. RSP is a style proxy, not breadth. The sector relation is calculated once in the plan from current directional facts. Level-only XLC is excluded from the ranking. Breadth stays unavailable and is not zero-filled. Macro remains optional and subordinate.
