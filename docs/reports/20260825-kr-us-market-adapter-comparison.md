# KR/US Market Adapter Comparison

| Dimension | KR | US |
| --- | --- | --- |
| Common schema | `market-context-adapter-v1` | `market-context-adapter-v1` |
| Local indices in replay | unavailable | SPY/QQQ/IWM |
| Sector context | unavailable | SOXX price proxy |
| Breadth | Unknown | Unknown |
| Size/concentration | Unknown | Unknown |
| Market-wide flow | KRW-only when verified; unavailable | KR participant semantics prohibited |
| Session vocabulary | pre/regular/after/closed | pre/regular/after/closed |
| Replay state | PARTIAL | PARTIAL |

The schema is common while acquisition and semantics remain market-specific. Neither market fills
missing data. KR overnight US context is not relabeled local, and US does not imitate KR investor
categories. The Common AI Core receives one typed input rather than two reasoning engines.

