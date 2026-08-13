# Knowledge v3 Merge Decisions

## Sources

| Source | Role | Lines | Bytes | SHA-256 |
|---|---|---:|---:|---|
| `1-custom_gpt_knowledge_ko-2.md` (Current Custom GPT Knowledge) | Safety, data, and monitoring base | 648 | 28,988 | `2acc979bcfc06c7fa8c30ddbbb0a73e1f30017359d9668613970fd1bb0fd8518` |
| `1-thesis_monitor_analysis_knowledge_v2.md` | Analytical-depth donor | 942 | 16,599 | `9c769f6be1ea6d17b858a14b35a7b2cd63201c0dc8066f7b05368d9bab967176` |

The merge priority was data safety, share/accounting/currency comparability, current backend contract, monitoring lifecycle, analytical depth, then examples. The documents were not concatenated.

## KEEP_CURRENT

- Fact / Interpretation / Unknown and source hierarchy.
- Initial Research versus version-specific Daily Delta.
- Earnings attribution, quarter-versus-TTM EPS, no one-quarter annualization, and preliminary-earnings limits.
- ADR/ADS ratio direction, security, currency, FX, and denominator checks.
- Historical valuation comparability and fail-closed behavior.
- Modeled, consensus, and provider-only forward valuation provenance.
- Industry-specific valuation frameworks. Current already covered every compatible donor metric and had broader memory, cloud, biotech, and pre-profit safety.
- Conditional OHLCV, supply separation, warning provenance, and partial-provider handling.
- Current public Action reference. The v2 operation examples did not replace it.

## MERGE_FROM_V2

- FOMC interpretation through Decision, Statement, Dot Plot, SEP, Press Conference, and Market Reaction.
- Hyperscaler CAPEX transmission through GPU/ASIC, HBM, foundry, packaging, equipment, and power/cooling/data-center infrastructure.
- The distinction among budget, order, shipment, revenue recognition, margin, cash conversion, and ROIC.

## REWRITE_COMBINED

- Price and volume combinations were retained only as conditional interpretations. They cannot mutate the business thesis without supporting facts.

## DROP_V2

- The fixed 100-point score and score-to-candidate mapping.
- Mechanical Reward/Risk quality thresholds.
- Mandatory RSI, MACD, Bollinger, support, and resistance usage.
- The ADR shortcut that multiplies price, ratio, and FX without first proving ratio direction and basis.
- Outdated Action examples and external APIs presented as if they were available public Actions.

## OPERATIONAL_NOT_KNOWLEDGE

Market run times, KRX retry gates, provider endpoints, notification retries, Scheduled Task times, and claim leases remain in runtime policy, operations documentation, and backend configuration. They are not part of the investment-reasoning manual.

## Result

Knowledge v3 is a 704-line semantic merge. It preserves the Current document's safety level and adds only the donor's compatible analytical depth.
