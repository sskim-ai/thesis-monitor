# KR Orphan Delivery Evidence Lock

Evidence was captured read-only before reconciliation from production SQLite and the immutable
AI-review directories. Telegram destination identifiers and payload text are excluded.

- Run: ID 33, `daily_kr`, success 7/7, 2026-08-22
- Packet: `2026-08-22-kr-run-33-c2491c2e78ad`
- Packet/claim/outbox/history artifacts: 0
- Stock rows expected from run details: 7
- Companion KR digest rows: 1
- Total target rows: 8
- Sent/status sent/sent_at: 0/0/0
- Attempt count: 0 for all rows
- Packet reference: absent for all rows

| ID | Ticker | Type | Status before | Payload SHA-256 |
| --- | --- | --- | --- | --- |
| 250 | `__DAILY_DIGEST_KR__` | digest | pending | `a3c65ff6c5b11d4e651a5f0b87272061ea2b2b4a2d4af9e3e7d5d10b5f52dc56` |
| 251 | `000660` | stock | pending | `a0f0a8ed8103ea575785177a7b3bbfd8ac3c11ecdb549b06fe5da5da0e4e8e05` |
| 252 | `003690` | stock | pending | `ac4729bdea02efc78adf165f31d0f7c82e3410b0f612ccacfa5a4624a859206c` |
| 253 | `005490` | stock | pending | `37bfe1c9c2c4148c0729257ea5ec26f2d0b4ab4000097c81a4ddc9086bb2176e` |
| 254 | `005930` | stock | pending | `9144360739ef9d1c2186b8166f17cc99c016f7e6ae6d68b3cbba69935427cf8e` |
| 255 | `010120` | stock | pending | `fe6b4fec53134c0071e9367b0bfc0f05fdf920c33f8c9035797e3c1d85eff326` |
| 256 | `012450` | stock | pending | `6e22a50dbbe18f04f18ed2155bc915907dc7f414c92cf771145542aab68d370a` |
| 257 | `086280` | stock | pending | `80609e8abc8dce1f645921015622536e10d27817379a945a9992b025e3a9587f` |

The exact IDs were derived from run identity and run-details tickers, not timestamp alone.
