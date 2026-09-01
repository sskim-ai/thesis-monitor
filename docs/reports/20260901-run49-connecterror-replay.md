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

Candidate generation through the external signed-in CLI is recorded separately because it requires
explicit external-data authorization. No production replay occurred.
