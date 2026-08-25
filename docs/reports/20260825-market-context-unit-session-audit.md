# Market Context Unit and Session Audit

| Fact family | Unit/basis | Session rule | Result |
| --- | --- | --- | --- |
| KRX index | index points, official | exact `BAS_DD` | PASS |
| KRX breadth | security counts/ratios | exact KOSPI or KOSDAQ rows | PASS |
| KRX activity | reported shares/KRW value | exact `BAS_DD` | PASS |
| KR market flow | KRW net amount | absent in verified source | UNKNOWN |
| US RSP/sector | adjusted USD close return | completed common US session | PASS |
| US relative return | percentage points | same-session inputs | PASS |
| US participant flow | unsupported | never synthesized | PASS |

Incompatible units are not combined. Stock-share counts are not divided into market monetary flow,
and market concentration is not computed from mixed stock/market units. Relative returns are pure
percentage-point differences with source fact IDs.

8/25 partial/current US rows were excluded from the 8/24 replay. KRX 8/24 capability data was not
substituted into the 8/25 target replay.

`MARKET_CONTEXT_UNIT_CONFLICT = 0`

`MARKET_CONTEXT_DEFAULT_ZERO = 0`
