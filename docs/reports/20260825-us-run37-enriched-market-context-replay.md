# US Run-37 Enriched Market Context Replay

- Packet: `2026-08-25-us-run-37-7e04812311c2`
- Packet SHA256: `17e14c4c7fd04017574f60057176c8e0560b0351ec9f3c865ba5dd543ae7e6cc`
- Immutable packet rewrite: `0`
- Supplemental evidence: completed 8/24 RSP and 11 sector ETF bars

RSP rose about `0.12%` from 8/21 to 8/24 and exceeded the packet's cap-weighted SPY return. XLP
and XLF were the strongest two verified sector proxies; XLK and XLE were the weakest two. The
enriched digest can therefore distinguish equal-weight participation from cap-weighted index
movement and sector concentration without claiming exchange breadth.

Breadth remains `UNAVAILABLE`; participant flow remains `UNAVAILABLE_NOT_SUPPORTED`. No 8/25
partial bar entered the replay.

All 13 stocks and the digest are safe: `14/14` eligible. CORZ and CRCL use stored HPC/colocation and
USDC/reserve-income drivers rather than generic synthesis. Generic lines fall `26 -> 0`; duplicate
messages fall `13 -> 0`; hard safety errors remain `0`.

`US_STRUCTURED_CONTEXT_VALUE_ADD = PASS`.
