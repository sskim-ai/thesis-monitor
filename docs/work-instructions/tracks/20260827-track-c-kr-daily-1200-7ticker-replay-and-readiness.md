# Track C — KR Daily 1200 7-Ticker Replay + Readiness

## Replay controls

```text
000660
003690
005490
005930
010120
012450
086280
```

Frozen session:

`2026-08-27`

Report exact daily coverage and recomputed Price Structure.

Preserve:

```text
LONG_HORIZON != 가까운
remote-fill prohibited
Fib family safety
stored-rule separation
US OFF
TOP3 unchanged
```

## PASS

Either:

```text
PASS_1200
```

or:

```text
VERIFIED_PARTIAL_SAFE_1000
```

is acceptable if fully proven and all safety gates pass.

Then:

```text
KR_DAILY_1200_REPAIR = REPLAY_PASS_READY_FOR_PREENABLE
NEXT_ACTION = RERUN_KR_TOP3_PRICE_STRUCTURE_TEST_SINK_PREENABLEMENT
```
