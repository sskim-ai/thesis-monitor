# US Shared Market Digest Plan

- Run: `41`
- Packet: `2026-08-27-us-run-41-ae4f42c23abc`
- Target session: `2026-08-26`
- Implementation SHA: `069f002437163bff1df7aa6e258918c1777d5dfa`
- Replay mode: immutable archive read-only

| Priority | Slot | State | Required | Evidence refs |
|---:|---|---|---|---|
| 1 | `CURRENT_MARKET` | `SELECTED` | YES | `market:index:SPY`, `market:index:QQQ`, `market:index:IWM`, `market:sector:SOXX` |
| 2 | `PARTICIPATION_STYLE` | `SELECTED` | YES | `market:style:RSP`, `market:index:SPY` |
| 3 | `SECTOR_DISPERSION` | `SELECTED` | YES | `market:sector:XLI`, `market:sector:XLV` |
| 4 | `BREADTH_STATE` | `OMITTED_UNAVAILABLE` | NO | - |
| 5 | `MACRO_CONTEXT` | `SELECTED` | NO | `market:real_yield:DFII10` |

AI and fallback plan SHA-256: `8761a2f65a3ae6b429f1d7feb0a4ab67bd5120ca0d27526ed9fc6f9b570ce8ef`.
