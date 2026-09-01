# Track D — Preserve Technical Recovery + Test Sink + Merge + Live Guard

Base from current safe main containing CPNG/HUT technical recovery.

Preserve:
- HUT quote/completed-candle finality
- CPNG feature-scoped validity
- recursive dependency safety
- approved-secondary-source boundary
- packet-owned technical context

Run:
- KR8 production-equivalent natural-path test
- US14 production-equivalent natural-path test
- dedicated 22-message test sink if cohort unchanged
- full regression / CI

No scheduler changes.
No production replay.

Merge only with P0/P1 = 0/0, then wait for natural live proof.
