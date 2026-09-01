# Run-49 ConnectError Replay

Packet: `2026-09-01-us-run-49-2d1bb6df1608`

The source packet remained immutable. A separate replay copy was enriched from the canonical
acquisition path and then prepared in `/tmp` with the repaired runtime. Preparation completed
without local HTTP and returned 14/14 decision contexts.

| Status | Count | Subjects |
|---|---:|---|
| FULL | 10 | CORZ, CRCL, GOOGL, IBM, RXRX, SNDK, TSLA, TSM, WRD, WULF |
| PARTIAL_SAFE | 0 | - |
| UNAVAILABLE | 0 | - |
| INVALID | 4 | CPNG, HUT, MU, SKHY |

The four invalid results are not transport regressions. Their provider rows independently violate
OHLC bounds, including current rows for HUT/MU/SKHY and historical CPNG rows. No ticker exception
was added. All 14 still reached decision-context preparation.

After explicit authorization, the isolated replay used signed-in Codex CLI
`gpt-5.6-sol / xhigh`. The repaired packet-owned path produced all 14 decision contexts without a
decision-stage HTTP request. Strict candidate validation used one batch-schema repair and six
subject-local repairs; no validator threshold changed and no candidate was manually edited.

| Candidate result | Count |
|---|---:|
| generated | 14 |
| accepted-ready | 14 |
| explicit BUY/HOLD/SELL | 14 |
| fallback | 0 |
| raw candidate visible | 0 |
| production send | 0 |

Accepted decision distribution is BUY/HOLD/SELL `0 / 11 / 3`. The final accepted-block message
quality receipt is `PASS`, with zero repeated substantive spans and zero manual or unresolved
numeric claims. The original source packet remained immutable and no production replay occurred.
