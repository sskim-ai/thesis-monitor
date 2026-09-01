# OHLCV Adjustment Basis

The current Kiwoom route requests one provider-native adjusted response for every O/H/L/C field.
The `meta.adjusted` flag must match the request. The exact split-versus-dividend methodology is
provider-specific and is not expanded beyond that evidence.

Adjusted and unadjusted rows are never combined into one candle. The diagnostic uniform-adjustment
audit requires the same multiplicative factor across open, high, low, and close; a partial-field
factor fails closed. Volume is recorded separately because its treatment depends on the source
contract. The repository performs no system-side split arithmetic in this phase.

The legacy internal label `adjusted_close` is retained for Price Structure compatibility; it does
not authorize mixing an adjusted close with raw open/high/low. Provider response metadata and the
integrity audit are the authoritative basis controls.

