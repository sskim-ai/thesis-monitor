# Track D — KR-only Bounded Enablement + Natural Proof

## Preconditions

Track C PASS.
Open P0/P1 = 0/0.

## Enable only

```text
KR market TOP3 sector policy
KR monitored-universe Price Structure v3
```

Keep:

```text
US Price Structure OFF
Production Assist OFF
```

If only a global Price Structure gate exists, do NOT enable global. Add the smallest KR-market scope guard.

## Post-enable smoke

Verify:

```text
KR Price Structure visible per eligibility
KR market TOP3 visible
US Price Structure absent
business/valuation unchanged
```

## Natural proof

Do not manually trigger.

Wait for next natural:

```text
KR afternoon market digest
KR monitored-stock messages
```

Only then set:

```text
KR_ROLLOUT = LIVE_PASS
```
