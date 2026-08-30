# Pricing Requirement And Asymmetry

Contracts: `evidence-maturity-pricing-v2` and `scenario-asymmetry-confirmation-cost-v2`.

The existing market-expectation enum remains canonical. Pricing requirement is a separate AI
interpretation: conservative outcome sufficient, base case required, optimistic case required,
bull case required, or unknown. A non-unknown result needs both valuation and expectation refs.

Bear/Base/Bull are evidence-bound business scenarios, not target-price forecasts. Asymmetry,
confirmation cost, and pre-confirmation error cost are independent interpretations. Technical and
market features may inform timing but cannot alone own long-horizon asymmetry.
