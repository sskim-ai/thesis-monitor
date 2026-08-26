# Price Structure v3 Legacy Technical Prose Audit

- Instruction commit: `2ac7eaaede9cb8d9047173bbec5f2bd99c665573`
- Implementation: `4246efb4f8afa3516402d1df7864967c177ac6e7`
- Test run: `v3-renderer-run:2a7a4203cf52ba05d8f8`
- Dataset: `v3-current-dataset:252d923f98173a1f2638`
- Render: `v3-renderer-render:4fe27a16d89fa24af40e`
- Source current-data run: `v3-current-run:ff97be1d62a9810dc315`
- Target sessions: KR `2026-08-26`, US `2026-08-25`.

| Ticker | Before hits | Suppressed | After hits | Stale after |
| --- | --- | --- | --- | --- |
| 000660 | 0 | 0 | 0 | 0 |
| 003690 | 0 | 0 | 0 | 0 |
| 005490 | 0 | 0 | 0 | 0 |
| 005930 | 0 | 0 | 0 | 0 |
| 010120 | 0 | 0 | 0 | 0 |
| 012450 | 0 | 0 | 0 | 0 |
| 086280 | 0 | 0 | 0 | 0 |
| CORZ | 0 | 0 | 0 | 0 |
| CRCL | 0 | 0 | 0 | 0 |
| GOOGL | 0 | 0 | 0 | 0 |
| HUT | 0 | 0 | 0 | 0 |
| IBM | 0 | 0 | 0 | 0 |
| MU | 1 | 1 | 0 | 0 |
| RXRX | 1 | 1 | 0 | 0 |
| SKHY | 0 | 0 | 0 | 0 |
| SNDK | 0 | 0 | 0 | 0 |
| TSLA | 0 | 0 | 0 | 0 |
| TSM | 0 | 0 | 0 | 0 |
| WRD | 0 | 0 | 0 | 0 |
| WULF | 0 | 0 | 0 | 0 |

MU stale occurrence before:

```text
2026-08-12 OHLCV 기준 MU는 월봉·주봉의 장기 상승 레짐이 유지되는 가운데 주봉 MACD와 주요 OSC가 플러스이고, 일봉 MACD histogram도 빠르게 개선되어 SKHY보다 중기 추세 구조가 안정적이다.
```

MU stale occurrence after: `0`.
