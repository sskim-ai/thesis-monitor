# Price Structure v3 Legacy Token Boundary Policy

- Instruction commit: `97b65fc1d258339563b54961a83acd997867e11e`
- Implementation: `3685aa991589ca0e7cc560104d4ebf8289e3f91d`
- Test run: `v3-legacy-detector-run:9e082343e51115738580`
- Dataset: `v3-current-dataset:252d923f98173a1f2638`
- Render: `v3-legacy-detector-render:a1b39f8917bfcc17ee81`
- Source run: `v3-current-run:ff97be1d62a9810dc315`
- Target sessions: KR `2026-08-26`, US `2026-08-25`.

| Negative input | Matches | Result |
| --- | --- | --- |
| Recursion | 0 | PASS |
| recursion | 0 | PASS |
| conversion | 0 | PASS |
| version | 0 | PASS |
| diversion | 0 | PASS |
| precision | 0 | PASS |
| decision | 0 | PASS |
| macdonald | 0 | PASS |

| Positive input | Matches | Result |
| --- | --- | --- |
| RSI 72 | 1 | PASS |
| RSI가 70을 상회 | 1 | PASS |
| RSI는 과열 | 1 | PASS |
| MACD histogram 둔화 | 1 | PASS |
| MACD가 0선 아래 | 1 | PASS |
| 2026-08-12 OHLCV 기준 | 1 | PASS |
| OHLCV를 확인 | 1 | PASS |
| Bollinger 상단 | 1 | PASS |
| ATR 확대 | 1 | PASS |
