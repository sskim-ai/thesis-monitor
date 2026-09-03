# Shadow vs Reference: Reason Differences

These are observable summary attributions, not hidden chain-of-thought. The comparison found no new or missing run-53 evidence surface in the blind prompt; differences arose from weighting or zone selection over the same frozen facts.

| Ticker | Codex | Reference | Fact surface | Difference types | Observed summary |
| --- | --- | --- | --- | --- | --- |
| CORZ | HOLD 5.0:5.0 | HOLD 4.5:5.5 | SAME_FACT_DIFFERENT_INTERPRETATION | TECHNICAL_CONTEXT_WEIGHT, PRICE_ZONE_DERIVATION | Both views kept HOLD. Codex chose a lower support-defense entry, while the reference required recovery through the 17.45-18.38 resistance area. |
| CPNG | HOLD 4.5:5.5 | HOLD 5.5:4.5 | SAME_FACT_DIFFERENT_INTERPRETATION | EARNINGS_FCF_WEIGHT, RISK_WEIGHT, PRICE_ZONE_DERIVATION | Codex was one balance point more cautious and selected the lower dynamic support instead of the registered 15.45-15.70 support. |
| HUT | SELL 3.5:6.5 | SELL 3.0:7.0 | SAME_FACT_DIFFERENT_INTERPRETATION | RISK_WEIGHT, TECHNICAL_CONTEXT_WEIGHT, PRICE_ZONE_DERIVATION | Both views were SELL. Codex still allowed a wait-for-confirmation path at 97, while the reference left the entry numeric zone unstated and emphasized avoidance/recovery. |
| IBM | HOLD 5.5:4.5 | HOLD 5.5:4.5 | SAME_FACT_DIFFERENT_INTERPRETATION | TECHNICAL_CONTEXT_WEIGHT, PRICE_ZONE_DERIVATION | The decision and balance matched. Codex required breakout confirmation at 250 rather than using the lower 228-235 support area. |
| MU | HOLD 5.5:4.5 | BUY 6.5:3.5 | SAME_FACT_DIFFERENT_INTERPRETATION | MARKET_EXPECTATION_WEIGHT, VALUATION_WEIGHT, RISK_WEIGHT | Codex stopped at HOLD despite the same support entry area; the reference reached BUY by assigning more weight to the upside case than to cycle, expectation, and timing risk. |
| RXRX | SELL 4.0:6.0 | HOLD 5.0:5.0 | SAME_FACT_DIFFERENT_INTERPRETATION | BUSINESS_EVIDENCE_WEIGHT, EARNINGS_FCF_WEIGHT, RISK_WEIGHT | Codex reached SELL/AVOID and withheld an entry, while the reference retained HOLD with a 3.37-3.47 review zone. The split is chiefly the weight placed on pre-profit cash burn and clinical uncertainty. |
| SKHY | HOLD 5.0:5.0 | HOLD 5.0:5.0 | SAME_FACT_DIFFERENT_INTERPRETATION | VALUATION_WEIGHT, TECHNICAL_CONTEXT_WEIGHT, PRICE_ZONE_DERIVATION | Decision and balance matched, but Codex required confirmation at 163 instead of the reference's 147-151 support entry. |
| SNDK | HOLD 5.5:4.5 | HOLD 4.5:5.5 | SAME_FACT_DIFFERENT_INTERPRETATION | BUSINESS_EVIDENCE_WEIGHT, MARKET_EXPECTATION_WEIGHT | Both views were HOLD and used the same registered support, while Codex's balance was one point more constructive. |
| TSLA | SELL 3.0:7.0 | SELL 2.5:7.5 | SAME_FACT_DIFFERENT_INTERPRETATION | BUSINESS_EVIDENCE_WEIGHT, RISK_WEIGHT, PRICE_ZONE_DERIVATION | Both views were SELL. Codex withheld a numeric entry under AVOID, while the reference retained only a business-confirmation-conditioned 335-341 price review. |
| TSM | HOLD 5.5:4.5 | HOLD 5.5:4.5 | SAME_FACT_DIFFERENT_INTERPRETATION | TECHNICAL_CONTEXT_WEIGHT, PRICE_ZONE_DERIVATION | Decision and balance matched. Codex selected 432 breakout confirmation rather than the 407-414 support area. |
| WRD | HOLD 4.5:5.5 | SELL 3.5:6.5 | SAME_FACT_DIFFERENT_INTERPRETATION | BUSINESS_EVIDENCE_WEIGHT, RISK_WEIGHT, PRICE_TIMING_WEIGHT | Codex separated business progress from weak price timing and stopped at HOLD; the reference assigned enough execution and financing risk to reach SELL. |
| WULF | SELL 3.5:6.5 | SELL 2.5:7.5 | SAME_FACT_DIFFERENT_INTERPRETATION | RISK_WEIGHT, TECHNICAL_CONTEXT_WEIGHT, PRICE_ZONE_DERIVATION | Both views were SELL. Codex required a stricter 18.40 confirmation, versus the reference's 16.2-16.8 recovery area. |

## Material Label Differences

- `MU`: Codex `HOLD 5.5:4.5`; reference `BUY 6.5:3.5`.
- `RXRX`: Codex `SELL 4.0:6.0`; reference `HOLD 5.0:5.0`.
- `WRD`: Codex `HOLD 4.5:5.5`; reference `SELL 3.5:6.5`.

All three are `SAME_FACT_DIFFERENT_INTERPRETATION`; none is attributed to post-run-53 fact leakage.
