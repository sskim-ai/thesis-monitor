# Structured Publication and Freshness Contract

Contract: `structured-market-context-v1`.

Every envelope owns market, exact session date, timezone-aware retrieval time, provider,
publication state, source references, optional payload hash, optional cross-section, and data gaps.

Allowed states are `AVAILABLE_CURRENT`, `AVAILABLE_PRIOR_SESSION`, `PUBLICATION_PENDING`, `PARTIAL`,
and `UNAVAILABLE`. Only `AVAILABLE_CURRENT` with an exact-session cross-section, fresh quality, and
`retrieved_at/as_of <= packet cutoff` can enter current reasoning.

Rules:

1. A future retrieval is invisible to a historical packet.
2. A different session file is never substituted.
3. Pending/partial/unavailable envelopes carry no invented number.
4. Cache contents are hash-verified and atomically replaced.
5. Provider failure returns Unknown and cannot block packet creation.
6. Prior-session evidence may remain context but is never called current.

The 16:05/08:05 KRX observer now persists pending/partial state envelopes as well as complete
snapshots. A complete snapshot requires a second bounded four-endpoint collection after readiness,
for at most eight provider calls in that capture.

Result: wrong-session, future-cutoff, hash-tamper, and missing-as-zero controls all fail closed.
