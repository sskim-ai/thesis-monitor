# Night Futures Session-Basis Audit

Accessed: `2026-08-19`

KRX states that the night session runs from 18:00 to 06:00 and assigns the trading
day by the 06:00 end time. A session beginning on T is therefore recorded as T+1,
together with the later T+1 regular session. See the [official KRX Night Session
rules](https://global.krx.co.kr/contents/GLB/02/0201/0201041004/GLB0201041004.jsp).

The archived implementation paired DAY and NIGHT rows carrying the same `BAS_DD`.
That DAY close occurs after the NIGHT close, so the comparison is reverse
chronological. The visible changes were backend calculations, not AI calculations.

| Fact | Night price | Same-date DAY price | Before change | After |
|---|---:|---:|---:|---|
| market:night_futures:1 | 1094.95 | 1078.25 | 16.7 | UNAVAILABLE_BY_CONTRACT |
| market:night_futures:2 | 1477.3 | 1429.4 | 47.9 | UNAVAILABLE_BY_CONTRACT |

For the 2026-08-19 morning packet, the required pair was 2026-08-19 NIGHT versus
2026-08-18 DAY. The 2026-08-19 provider query returned zero rows and the exact raw
provider response was not archived, so the user's approximately -4.29pt observation
cannot be reconstructed as a canonical value. The repaired result is
`UNAVAILABLE_BY_CONTRACT`; no value is hard-coded.

The new `night-futures-session-basis-v1` requires contract identity, NIGHT/DAY session identity,
reference/current prices, dates, source record IDs, raw payload SHA256 values, and a
deterministic change calculation. Missing or ambiguous evidence is suppressed.
