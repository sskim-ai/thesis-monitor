# AI Anchor Stability Policy

## Evidence

Stability is measured from repeated independent selections of the same frozen packet, never from
final prose. The exact benchmark uses two KR and two US stocks with five runs per packet. Every other
eligible monitored packet receives at least three runs. Runtime failures are counted and cannot be
reclassified as stable AI output.

## Metrics

Each timeframe records frequencies for low, high, correction-low, Fibonacci mode, support zone, and
resistance zone. Exact signatures also include regime. Compact-rich versus full-debug comparison is
performed on the benchmark after the independent compact trial.

## Structural Equivalence

Different IDs are equivalent only when they preserve timeframe role, support/resistance relation,
regime, and visible deterministic Fibonacci zones under the existing canonical merge tolerance:
monthly `3%`, weekly `2.25%`, daily `1.75%`. No trial-specific or wider tolerance exists.

- `STABLE`: every signature is identical.
- `MINOR_VARIATION`: IDs differ but the visible structure remains equivalent.
- `MATERIAL_VARIATION`: support/resistance, Fibonacci zones, or structural interpretation differs.

## Eligibility

Monthly or weekly material variation makes the stock ineligible for the first visible candidate
pool. Daily-only material variation preserves monthly/weekly output, retains deterministic daily SR,
and omits daily Fibonacci. Any material pivot selected from full debug but absent from compact-rich
fails packet sufficiency.

Passing this policy means `INTEGRATED_READY_NOT_ARMED`, not production enablement. A separate bounded
instruction must define cohort, kill switch, delivery isolation, and rollback.
