# Historical BUY Fixture Polarity Control

Two historical canonical BUY archives were adapted through the common polarity-claim validator;
the old candidate schema was not silently promoted to the current calibration schema.

- 003690 BUY: verified book discount under BUY; structural underwriting-loss risk under SELL.
- GOOGL BUY: favorable historical trailing-earnings valuation under BUY; AI-capex cash-return risk
  under SELL.
- Both messages are explicitly labeled historical and test-only.
- Dedicated test sink: `2/2 exact` as part of the six-message batch.
- Production send/state mutation: `0/0`.

`BUY_FIXTURE_POLARITY_VALIDATION = PASS`

`BUY_FIXTURE_PRODUCTION_SEND = 0`
