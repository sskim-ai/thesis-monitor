# Track A — US Night-Futures Summary Canonicalization Repair

Fix one ownership defect:

```text
market_summary night-futures numerics
must be generated only from canonical night_futures_gate facts.
```

Hard:

```text
raw summary bypass = 0
value/session conflict = 0
stale summary item = 0
prior-night-as-current = 0
```

Use a real historical current-directional fixture to verify display if available.
No synthetic fixture.
