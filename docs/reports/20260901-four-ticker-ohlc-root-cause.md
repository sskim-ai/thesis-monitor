# Four-Ticker OHLC Root Cause

| Ticker | Class | First bad stage | Repair | Final |
| --- | --- | --- | --- | --- |
| CPNG | STABLE_BAD_SOURCE | KIWOOM_RAW_RESPONSE | RAW_PROVIDER_INVALID_RETAIN_INVALID | INVALID |
| HUT | INTERMITTENT_BAD_SOURCE | KIWOOM_RAW_RESPONSE | RAW_PROVIDER_INVALID_RETAIN_INVALID | INVALID |
| MU | TRANSIENT_PROVIDER_DEFECT | PROVIDER_RESPONSE_INFERRED | PROVIDER_REFETCH_RECOVERED | FULL |
| SKHY | TRANSIENT_PROVIDER_DEFECT | PROVIDER_RESPONSE_INFERRED | PROVIDER_REFETCH_RECOVERED | FULL |

The common adapter maps provider-native fields without OHLC synthesis. CPNG and HUT remain fail-closed; MU and SKHY recover only because fresh provider responses are valid. Legacy run-49 retained a coarse error but not the malformed MU/SKHY row values, so those values are deliberately not reconstructed.
