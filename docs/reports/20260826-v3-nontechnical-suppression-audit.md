# Price Structure v3 Nontechnical Suppression Audit

- Instruction commit: `97b65fc1d258339563b54961a83acd997867e11e`
- Implementation: `3685aa991589ca0e7cc560104d4ebf8289e3f91d`
- Test run: `v3-legacy-detector-run:9e082343e51115738580`
- Dataset: `v3-current-dataset:252d923f98173a1f2638`
- Render: `v3-legacy-detector-render:a1b39f8917bfcc17ee81`
- Source run: `v3-current-run:ff97be1d62a9810dc315`
- Target sessions: KR `2026-08-26`, US `2026-08-25`.

| Ticker | Suppressed fragment | Field | Tokens | Reason | Explained |
| --- | --- | --- | --- | --- | --- |
| MU | 2026-08-12 OHLCV 기준 MU는 월봉·주봉의 장기 상승 레짐이 유지되는 가운데 주봉 MACD와 주요 OSC가 플러스이고, 일봉 MACD histogram도 빠르게 개선되어 SKHY보다 중기 추세 구조가 안정적이다. | TECHNICAL_PROSE_CANDIDATE | OHLCV, 월봉, 주봉, 상승 레짐, 주봉, MACD, 일봉, MACD | stale_or_redundant_legacy_technical_sentence | PASS |

Only the stale MU technical sentence remains suppressed. Nontechnical suppression: `0`.
