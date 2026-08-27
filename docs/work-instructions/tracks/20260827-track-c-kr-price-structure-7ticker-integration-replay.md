# Track C — KR Price Structure 7-Ticker Integration Replay

## Preconditions

Track A + Track B on the same latest safe main.

## Replay

Target frozen session:

`2026-08-27`

Tickers:

```text
000660
003690
005490
005930
010120
012450
086280
```

Report:

```text
D/W/M coverage
eligibility
internal nearest
user-visible near
major structural zones
proximity tier
distance
source timeframe/family
Fib state
stored-rule separation
exact rendered section
validator result
```

Do not send Telegram and do not enable runtime flags.

## PASS state

```text
KR_PRICE_STRUCTURE_REPAIR = REPLAY_PASS_READY_FOR_PREENABLE
NEXT_ACTION = RERUN_KR_TOP3_PRICE_STRUCTURE_TEST_SINK_PREENABLEMENT
```
