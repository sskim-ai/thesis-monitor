# 2026-09-03 KR8 Earnings, Valuation, And Expectations

The native financial freshness state was `current` for all eight, based on the latest formal 2026-06-30 period. Valuation quality was `partial` for all eight. This report exposes only fields marked prose-eligible by the packet.

| Ticker | Safe earnings checkpoint | Safe valuation | Expectation | Expectation as-of | Main caution |
|---|---|---|---|---|---|
| 000660 | none; revenue/profit/margin tainted | PBR 4.3253x; historical PBR percentile 85.2 | very_high | 2026-08-12 | profitability outlier; earnings-based multiples withheld |
| 003690 | operating income KRW 175,045,476,922 | PER 6.4191x; PBR 0.6801x; fPER 6.4348x; fPBR 0.6294x | balanced | 2026-08-12 | insurance economics require underwriting/ROE context |
| 005490 | no prose-eligible revenue/profit/margin | PER 19.1941x; PBR 0.45x | balanced | 2026-08-10 | operating facts retained as non-prose fields |
| 005930 | revenue KRW 171,499,470,000,000; operating income KRW 89,492,412,000,000; margin 52.1823% | PER 11.1294x; PBR 2.5502x | very_high | 2026-08-12 | expectations require HBM/DS execution evidence |
| 010120 | no prose-eligible earnings amount | none | elevated | 2026-08-12 | current packet has insufficient multiple metadata |
| 012450 | no prose-eligible earnings amount | none | elevated | 2026-08-12 | safe EPS/BVPS basis unavailable |
| 047810 | operating income KRW 48,441,878,616 | none | elevated | 2026-08-31 | other earnings and valuation fields unavailable |
| 086280 | no prose-eligible revenue/profit/margin | PER 9.8306x; PBR 1.391x; fPER 9.0258x; fPBR 1.3882x | elevated | 2026-08-10 | earnings fields retained as non-prose fields |

The safe-valuation count is 5: `000660`, `003690`, `005490`, `005930`, and `086280`. This means at least one current or forward multiple was explicitly prose-eligible; it does not mean every multiple for that ticker was safe.

No FCF, ROIC, balance-sheet, attributable-income, guidance, or per-share fact was created in this extraction. The complete stored expectation objects, including priced-in items and upside/downside surprises, are copied in `20260903-kr8-facts.json`.

