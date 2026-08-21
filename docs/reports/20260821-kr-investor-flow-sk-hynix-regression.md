# 2026-08-21 SK hynix Investor-Flow Regression

- Ticker: `000660`
- Packet: `2026-08-21-kr-run-31-27d43ced72a0`
- Original packet/fallback: immutable
- Visible actor/window facts preserved: 9/9

| Window | Visible-three net | Other corporation | Domestic foreign | Omitted net | Full net |
|---|---:|---:|---:|---:|---:|
| 1d | -647,495 | +647,846 | -351 | +647,495 | 0 |
| 5d | -1,280,559 | +1,284,563 | -4,004 | +1,280,559 | 0 |
| 20d | -1,272,405 | +1,264,923 | +7,482 | +1,272,405 | 0 |

The omitted participant identity comes from explicit source fields. It is not inferred from the
residual. Institution subclasses sum exactly to institution total and are diagnostic only.

The 5d actor directions reverse the 20d institution/individual absorption frame. The repaired
primary signal is therefore `mixed_window_flow` with basis `mixed`; unqualified
`외국인 이탈·기관/개인 흡수` is suppressed. Investment logic and valuation deltas remain zero.
