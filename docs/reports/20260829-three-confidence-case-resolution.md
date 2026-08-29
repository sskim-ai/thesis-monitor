# Three Confidence Case Resolution

- Date: `2026-08-29 KST`
- Contract: `decision-calibration-p1-repair-v1`
- Implementation SHA: `930952132077e8403bcec1a7e2c52d5732d8521a`
- Production canary: `OFF`
- Production recipient sends/intents: `0 / 0`

| Ticker | Final | Reason | Decision-critical limits | Stable decision |
|---|---:|---:|---|---:|
| CORZ | LOW | DATA_QUALITY_LIMIT | The latest full-statement financial-quality evidence is denied for decision use, directly limiting confidence in earnings and cash-flow interpretation. (`canonical:financial_quality:2026-06-30`)<br>Book-based valuation fails coherence and historical comparison is withheld, so valuation cannot reliably distinguish HOLD from either directional alternative. (`canonical:valuation:book_quality`, `canonical:valuation:current`)<br>Future cash generation, leverage stabilization, and fully diluted per-share economics remain insufficiently proven and weaken confidence in the decision boundary. (`decision-evidence:8906a34193399a6c5d0a`, `decision-evidence:d9ef83e7a574c9185b09`, `decision-evidence:cc2821e2af21b4635a68`) | HOLD |
| SKHY | LOW | SECURITY_BASIS_LIMIT | The packet does not establish a usable current financial period or supported financial-quality basis. (`canonical:earnings:latest`, `canonical:financial_quality:latest`)<br>Unverified per-security denominators and failed valuation-basis checks materially limit both valuation precision and confidence in the decision direction. (`canonical:security_basis:current`, `canonical:valuation:book_quality`, `canonical:valuation:multiple_relation`) | HOLD |
| SNDK | MEDIUM | ECONOMIC_PROOF_LIMIT | Expectations are speculative, while margin impact, revenue impact, and the conversion of contracts into revenue and cash flow remain unresolved; this limits economic proof and prevents HIGH confidence. (`decision-evidence:687af24c7385d2caf4a4`, `decision-evidence:78a04aa8286aa67990ec`, `decision-evidence:f66f3863507f91085d1a`, `decision-evidence:86645d2f1e1d8c65d8d6`)<br>The valuation inputs are usable but mixed, and withheld historical comparability limits precision without making the HOLD direction unreliable. (`canonical:valuation:current`, `canonical:valuation:book_quality`, `canonical:valuation:consensus_forward_earnings`) | HOLD |

- `CONFIDENCE_UNRESOLVED_COUNT_AFTER = 0`
