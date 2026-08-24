# Adaptive Renderer Safety Parity

| Hard target | Accepted count |
|---|---:|
| FACT_MISMATCH | `0` |
| UNSUPPORTED_NUMERIC_CLAIMS | `0` |
| UNSUPPORTED_CAUSALITY | `0` |
| TEMPORAL_VIOLATIONS | `0` |
| TRADE_AR_LEAK | `0` |
| HIDDEN_ARITHMETIC_ACCEPTED | `0` |
| EXTERNAL_KNOWLEDGE_ACCEPTED | `0` |
| MATERIAL_INFORMATION_LOSS | `0` |

Negative controls rejected hidden arithmetic `1`, external knowledge `1`, unsupported causality `1`, stronger language `1`, temporal leakage `1`, and Trade AR leakage `1`.

Inventory alternatives select Direct; clear FCF links select Hybrid without scope or valuation expansion; the macro reference-only case selects Minimal without changing temporal semantics. Price/RR and positioning remain source-bounded. Production safety validators and delivery are unchanged.
