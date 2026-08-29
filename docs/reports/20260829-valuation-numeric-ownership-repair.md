# Valuation Numeric Ownership Repair

| Ticker | Numeric ref | Typed owner fact | Reason |
| --- | --- | --- | --- |
| CRCL | pbr | valuation:current_pbr | typed_valuation_numeric_owner_handoff |
| CRCL | fpe | valuation:consensus_forward_earnings | typed_valuation_numeric_owner_handoff |
| GOOGL | pe | valuation:trailing_earnings | typed_valuation_numeric_owner_handoff |
| GOOGL | fpe | valuation:consensus_forward_earnings | typed_valuation_numeric_owner_handoff |
| HUT | pbr | valuation:current_pbr | typed_valuation_numeric_owner_handoff |
| HUT | fpe | valuation:consensus_forward_earnings | typed_valuation_numeric_owner_handoff |
| IBM | pe | valuation:trailing_earnings | typed_valuation_numeric_owner_handoff |
| IBM | fpe | valuation:consensus_forward_earnings | typed_valuation_numeric_owner_handoff |
| MU | pe | valuation:trailing_earnings | typed_valuation_numeric_owner_handoff |
| MU | pbr | valuation:current_pbr | typed_valuation_numeric_owner_handoff |
| RXRX | pbr | valuation:current_pbr | typed_valuation_numeric_owner_handoff |
| RXRX | pbpct | valuation:historical_pb | typed_valuation_numeric_owner_handoff |
| SNDK | pbr | valuation:current_pbr | typed_valuation_numeric_owner_handoff |
| SNDK | fpe | valuation:consensus_forward_earnings | typed_valuation_numeric_owner_handoff |
| TSLA | pe | valuation:trailing_earnings | typed_valuation_numeric_owner_handoff |
| TSLA | pbr | valuation:current_pbr | typed_valuation_numeric_owner_handoff |
| TSM | quality_unknown | security_basis:current | typed_valuation_quality_unknown_handoff |
| WRD | quality_unknown | security_basis:current | typed_valuation_quality_unknown_handoff |
| WULF | pbr | valuation:current_pbr | typed_valuation_numeric_owner_handoff |
| WULF | pbpct | valuation:historical_pb | typed_valuation_numeric_owner_handoff |

Numeric values still bind from their field-level canonical registry rows. Interpretation ownership is moved to eligible narrow facts, so denied mixed `valuation:current` no longer owns prose. TSM/WRD security-basis cautions are bound as typed `quality_unknown` occurrences. No denominator, currency conversion, or per-share value was inferred.
