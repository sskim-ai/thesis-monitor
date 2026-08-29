# Current-Time Message Quality

- Execution time (KST): `2026-08-29T21:16:59.579875+09:00`
- Mode: read-only current-time E2E test

## Result

| Gate | Result |
|---|---|
| Exact six-message builder | `PASS` |
| Received payload validation | `6 / 6 PASS` |
| BUY/SELL polarity | `PASS` |
| Price Structure / technical safety | `PASS` |
| Order language | `0` |
| Order sizing | `0` |
| Production intent | `0` |

## Per Message

| Message | Characters | SHA-256 | Validator |
|---|---:|---|---|
| KR_MARKET | 706 | `77082b2ffa21df42005ae1d9256b55ff28a6d2fdb137c9a1f1585d98d3010c03` | PASS |
| US_MARKET | 239 | `04bd0c599428b1a6a3b1306f022961ed2324c223470b68561d7918052816ea97` | PASS |
| 003690 | 1937 | `d9cd741962f45e79b7c9780b3d4cd0bcdb84fcc4610201f42467cdf1d3f35212` | PASS |
| 000660 | 1808 | `c25c249a2e3a2d8613906bd246658fad8f9d15f87f7019f242bad6290c2dc557` | PASS |
| GOOGL | 2697 | `adb7503c68f4bf9fe8e4fe04851ab9efc4ea4920e20e1d745b2343c6ac44c10e` | PASS |
| RXRX | 2110 | `c3ea5bdc030bb10ded4a1d6d9f06a9db9a5cf57d14c6736f1c3b6cfe7df7bf46` | PASS |

The KR sector renderer excludes size/index taxonomy rows from sector TOP3. Nasdaq breadth and night futures were omitted when their exact sessions were not fresh.
