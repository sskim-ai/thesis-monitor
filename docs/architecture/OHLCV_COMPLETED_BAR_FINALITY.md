# OHLCV Completed-Bar Finality

Contract: `ohlcv-completed-bar-finality-v1`

## States

- `FINAL`: a completed close has explicit source ownership, valid OHLC enclosure, safe timestamp,
  and completed-session evidence.
- `PROVISIONAL`: the bar is open, live, partial, or after the completed-session cutoff.
- `UNCONFIRMED`: the row date is plausible but close ownership or provider finality is not proven.
- `INVALID`: the candidate completed candle has invalid identity, date, or OHLC enclosure.

A date alone never proves finality. For Kiwoom US chart rows, a later chart date can prove that an
older internally valid row is historical. The newest row still requires a provider-native settled
close or explicit final marker. A later valid acquisition therefore recovers automatically without
a ticker/date exception.

## Enforcement

Only `FINAL` rows enter feature calculation. Provisional and unconfirmed rows remain observable but
do not own candle facts. Invalid rows retain fingerprints and reasons. The contract never clips
high/low, copies a previous close, or expands an OHLC envelope.
