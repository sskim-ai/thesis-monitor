# Price Structure v3 Current-Data Session Audit

- Instruction commit: `688c17280a10e91214d4bd9888522fdc6f9bc0c5`
- Implementation: `ef586c3816ff76417d2620636975d054935533d4`
- Test run: `v3-current-run:ff97be1d62a9810dc315`
- Dataset: `v3-current-dataset:252d923f98173a1f2638`
- Render: `v3-current-render:f6152bc2c61ced3eeffa`
- Observed at: `2026-08-26T19:49:57+09:00`
- Target sessions: KR `2026-08-26`, US `2026-08-25`.

The current provider returned an incomplete US `2026-08-26` stub for every US/foreign subject. The temporal gate excluded it, retained `2026-08-25`, and rebuilt only the current weekly/monthly contextual bar from completed daily data. KR uses the completed `2026-08-26` close.

| Ticker | Market | Live last | Safe last | Excluded | Safe close |
| --- | --- | --- | --- | --- | --- |
| 000660 | KR | 2026-08-26 | 2026-08-26 | 0 | 1688000.0 |
| 003690 | KR | 2026-08-26 | 2026-08-26 | 0 | 14510.0 |
| 005490 | KR | 2026-08-26 | 2026-08-26 | 0 | 328000.0 |
| 005930 | KR | 2026-08-26 | 2026-08-26 | 0 | 261500.0 |
| 010120 | KR | 2026-08-26 | 2026-08-26 | 0 | 201500.0 |
| 012450 | KR | 2026-08-26 | 2026-08-26 | 0 | 1087000.0 |
| 086280 | KR | 2026-08-26 | 2026-08-26 | 0 | 204500.0 |
| CORZ | US | 2026-08-26 | 2026-08-25 | 1 | 18.03 |
| CRCL | US | 2026-08-26 | 2026-08-25 | 1 | 92.02 |
| GOOGL | US | 2026-08-26 | 2026-08-25 | 1 | 346.96 |
| HUT | US | 2026-08-26 | 2026-08-25 | 1 | 85.5 |
| IBM | US | 2026-08-26 | 2026-08-25 | 1 | 234.19 |
| MU | US | 2026-08-26 | 2026-08-25 | 1 | 932.97 |
| RXRX | US | 2026-08-26 | 2026-08-25 | 1 | 3.56 |
| SKHY | US | 2026-08-26 | 2026-08-25 | 1 | 159.53 |
| SNDK | US | 2026-08-26 | 2026-08-25 | 1 | 1480.77 |
| TSLA | US | 2026-08-26 | 2026-08-25 | 1 | 350.25 |
| TSM | US | 2026-08-26 | 2026-08-25 | 1 | 417.41 |
| WRD | US | 2026-08-26 | 2026-08-25 | 1 | 6.08 |
| WULF | US | 2026-08-26 | 2026-08-25 | 1 | 16.32 |
