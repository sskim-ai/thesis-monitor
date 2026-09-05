# KRX Night Futures Session Contract

- Contract: `krx-night-futures-session-quote-v1`
- Instrument: `XKRX:KOSPI200:FUTURES`
- Contract month: `202609`
- Session business date: `2026-09-04`
- Window: `2026-09-04T18:00:00+09:00` to `2026-09-05T06:00:00+09:00`
- Weekend state: `CLOSED`

세션 business date와 실제 timestamp를 별도로 보존한다. 가격은 positive finite OHLC 관계를, volume은 nonnegative를 검증한다.
