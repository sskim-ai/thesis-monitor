# M12DS-R6-R3-REV1 Revision Note

This revision changes only the US settled-close route priority.

Previous R6-R3:
1. Alpha Vantage qualification first.

Revised R6-R3-REV1:
1. Qualify existing Kiwoom `usa06012` dated daily OHLCV rows first.
2. If the row context proves that row-local `cur_prc` is the regular-session daily
   candle close and final at the production cutoff, use Kiwoom.
3. Only if Kiwoom semantics/finality cannot be proven, qualify the already-configured
   Alpha Vantage account as fallback.

The revision explicitly forbids globally mapping every `cur_prc` field to close.
Generic quote contexts remain CURRENT_QUOTE.

KR post-close, macro latest-available display, KR price-basis, night D/W/M,
support/resistance, transport policy, no-send isolation and 24-message proof requirements
remain unchanged.
