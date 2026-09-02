# 2026-09-03 Same-Evidence Variance Harness

## Implementation

The non-production harness freezes packet identity, evidence fingerprint, candidate-input fingerprint, and prior accepted baseline. It runs at least three independent signed-in Codex CLI executions in separate ephemeral state namespaces.

For each ticker it records candidate balance and label, whether adjudication was required, adjudication validity, and final accepted balance and label. Candidate and accepted pairwise maximum distances are classified independently. Label boundary crossings are counted pairwise.

## Safety

- Production majority voting: 0
- Production recipient sends: 0
- Production delivery-state mutation: 0
- Business-thesis auto mutation: 0
- Fixed universal factor weights: 0

The harness script is `scripts/directional_balance_variance_evidence.py`. Frozen execution results are written beneath an explicit output directory and are not imported by scheduled runtime.

## Focused Controls

Synthetic controls cover minor, moderate, and material distance; candidate BUY/HOLD boundary variance with stable accepted BUY; material accepted drift rejection; frozen identity mismatch; three-run minimum; minor-movement non-adjudication; and major thesis-condition conflict adjudication.

## Fresh Execution Result

GOOGL and four KR controls each completed three fresh `xhigh` executions. All
candidate and accepted balances were label-stable with maximum distance `0.0`.
Combined label boundary crossings, unexplained accepted drift, production sends,
production state mutations, and production majority voting were all `0`.

Machine-readable result:
`docs/reports/20260903-same-evidence-variance.json`.
