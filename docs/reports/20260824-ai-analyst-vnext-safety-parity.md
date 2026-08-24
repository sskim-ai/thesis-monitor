# AI Analyst vNext Safety Parity

| Gate | Result |
|---|---:|
| Factual parity | `PASS` |
| Fact mismatch | `0` |
| Unsupported numeric claims | `0` |
| Unsupported causality | `0` |
| Temporal violations | `0` |
| Price ownership violations | `0` |
| Valuation basis violations | `0` |
| Trade AR user-visible leak | `0` |

All vNext claim-bearing lines are exact source spans from the corresponding validated current AI
message. The benchmark adds no arithmetic and consumes no provider response beyond the immutable
artifacts named in the manifest. Current-AI/fallback parity is inherited from each immutable
validated replay receipt; vNext adds only source-span selection. Existing numeric, semantic,
temporal, causal, price, valuation, Inventory, FCF, and investor-flow validators are unchanged.
