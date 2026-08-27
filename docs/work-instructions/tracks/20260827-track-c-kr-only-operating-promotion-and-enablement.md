# Track C — KR-Only Operating Promotion + Sequential Enablement

## Preconditions

Track B PASS.
Open P0/P1 = 0/0.

## Sequence

```text
1. promote latest validated main to operating
   with both KR flags OFF

2. health + FEATURE_OFF_PARITY

3. kr_market_sector_top3_enabled = true
   smoke market digest

4. kr_price_structure_v3_enabled = true
   smoke all monitored KR stock messages

5. prove US Price Structure remains OFF

6. wait for natural KR messages
```

If any smoke fails, rollback only the affected flag and STOP.

No manual production scheduler execution.

Final pre-natural state:

```text
KR_ROLLOUT = ENABLED_AWAITING_NATURAL_PROOF
```

Only natural market + stock proof may upgrade to `LIVE_PASS`.
