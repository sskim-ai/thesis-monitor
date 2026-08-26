# OHLCV Bar Completion Contract

## Contract

`ohlcv-bar-completion-v1` binds every canonical price bar to a timeframe, exchange calendar,
period start/end, observation time, and `COMPLETE` or `PARTIAL` state. Presence in a provider
response is not completion evidence.

Daily bars become complete only after that exchange's regular-session close. Weekly and monthly
bars become complete only after the final exchange session in the respective calendar period.
The exchange calendar determines holiday and shortened-session boundaries.

## Pivot Safety

A confirmed pivot requires a complete pivot bar and the configured number of complete right-side
bars. The pivot preserves `pivot_bar_date`, `required_right_bar_count`,
`pivot_confirmation_date`, and the exact `confirmation_bar_ids`. Partial bars may contribute to
current candle context or a provisional endpoint, but never to confirmation.

For the 2026-08-26 SK hynix replay, the August monthly bar is partial. It therefore cannot be the
second right-side bar for the June monthly high; the June high and July low remain provisional.

## Safety

Unknown calendar coverage fails closed as partial. The contract does not alter the production
packet, current renderer, Telegram, assessment state, or thesis logic.
