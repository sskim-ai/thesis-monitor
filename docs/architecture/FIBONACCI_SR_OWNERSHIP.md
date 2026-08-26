# Fibonacci SR Ownership

## Contract

`fibonacci-sr-ownership-v1` assigns support and resistance exclusively to the deterministic
backend. Variable AI may select a canonical swing structure for Fibonacci analysis, but it cannot
select, replace, rank, or relabel support and resistance.

```text
completed adjusted OHLCV
  -> deterministic per-timeframe SR
  -> canonical swing-structure candidates
  -> variable AI structure IDs
  -> backend validation and consensus
  -> deterministic Fibonacci or safe omission
```

## Invariants

- Monthly, weekly, and daily SR are calculated once from the existing deterministic engine.
- The AI input may describe candle context and canonical structure IDs, but the output schema has
  no SR field.
- AI variation cannot alter SR values, owners, eligibility, or merge tolerance.
- Invalid, ambiguous, insufficient, or unstable Fibonacci selection affects only the corresponding
  timeframe's Fibonacci output. Deterministic SR remains available.
- No support/resistance algorithm, threshold, tolerance, price rule, or production route changes.

## Closure Evidence

The 2026-08-26 frozen 5/3 trial produced zero monthly, weekly, and daily SR runtime variation. The
legacy mixed classifier had treated SR-only movement as anchor instability in 11 cases: monthly 1,
weekly 7, and daily 3. The separated contract removes that false coupling while preserving true
anchor and mixed variation as Fibonacci-specific evidence.

