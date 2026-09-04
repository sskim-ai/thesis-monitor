# 2026-09-04 Explicit V2 Natural-Proof Gate

Contract: `explicit-v2-natural-proof-v1`

The gate counts these values independently:

- accepted AI total
- AI market sent
- explicit V2 stocks accepted
- explicit V2 stocks sent
- Pilot AI-assisted stocks sent
- deterministic fallback sent
- duplicate sent

For KR with eight stocks, PASS requires exactly `1` market, `8` explicit V2
accepted, `8` explicit V2 sent, and zero Pilot, fallback, and duplicates.

A `1+8` Pilot delivery is useful compatibility delivery but is not explicit-V2
natural proof. Tests verify that Pilot-only delivery fails this gate. The real
KR TEST E2E passed the strict counts, but remains TEST evidence. The next
ordinary KR scheduled run must satisfy the same gate before natural proof can
be marked complete.
