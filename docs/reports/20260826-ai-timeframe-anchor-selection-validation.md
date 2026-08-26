# AI Timeframe Anchor Selection Validation

The typed selection boundary accepts canonical IDs only; price fields are absent. The backend
validator checks ticker/timeframe ownership, zone role, evidence refs, chronology, confirmation
cutoff, and adjustment basis before any calculation.

This run used Codex-reviewed archive selections through the deterministic reference harness for all
20 subjects. All 20 validated and three repeated harness executions were identical. A separate
external variable AI-runtime trial was not performed because exporting the evidence packet was not
authorized; therefore `ANCHOR_SELECTION_STABILITY = PARTIAL`, not a claimed live-runtime PASS.

`AI_SWING_ANCHOR_SELECTION = PASS` for the typed ID-selection and validator contract.


- Active universe: `20` (`KR 7`, `US 13`).
- Shadow validation: `20/20` PASS.
- Timeframe availability: monthly `17`, weekly `19`, daily `19`.
- Fibonacci calculation availability: monthly `16`, weekly `19`, daily `19`.
- Subjects with strict cross-timeframe confluence: `10`.
- Compact/full parity: `20/20`.
- Historical look-ahead leaks: `0`.
