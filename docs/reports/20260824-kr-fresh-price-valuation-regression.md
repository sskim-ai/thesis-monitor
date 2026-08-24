# KR Fresh Price And Valuation Regression

## Price / RR

- Current 2026-08-24 close basis: 7/7
- Dynamic support/resistance: 7/7
- Chart invalidation: 7/7
- RR available and rendered: 6/7
- RR safely unavailable: 086280, because nearest support and resistance overlap
- Fabricated level or formula change: 0

All exact fallback price/RR values reproduce the canonical `current-price-context-v1` fields. No
registered confirmation was promoted into support without the existing lifecycle state.

## Valuation

Verified current multiples were selectively rendered for 000660, 003690, 005490, 005930, and
086280. 010120 and 012450 remained fail-closed because security/share-basis verification was not
complete. No denominator reconstruction, working-capital-driven valuation change, FCF yield, or
per-share FCF was created.

Generic enterprise cash-flow remained NOT_APPLICABLE for 003690 and suppressed for all other KR
subjects because the OpenDART period context remains excluded from current user-visible selection.

`PRICE_RR_REGRESSION = PASS`

`VALUATION_REGRESSION = PASS`
