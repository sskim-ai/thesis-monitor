# KR Local-First Market Digest

Contract: `kr-market-digest-quality-v1`

## Ownership

The completed Korean session owns the primary KR afternoon digest. Evidence order is:

1. KOSPI and KOSDAQ direction.
2. KOSPI and KOSDAQ scoped breadth.
3. Same-session aggregate foreign, institution, and retail flow.
4. Same-session size context.
5. Bounded non-empty sector-index leader/laggard context.
6. KR close FX.
7. Prior/global macro context as a qualified secondary section.

Completed KOSPI/KOSDAQ indices plus reconciled scoped breadth are the minimum local-first contract.
Flow, size, and sector layers are consumed when present; their absence does not hand ownership back
to a prior US body.

## Shared Path

```text
structured market cross-section
-> market-context-adapter-v1
-> KrMarketDigestPlan
-> deterministic daily digest
-> AI market evidence catalog
```

The deterministic renderer and the AI evidence-lock adapter consume the same plan. The AI may
interpret the supplied claims but does not calculate breadth or flow values.

## Boundaries

- Index direction and breadth are separate claims.
- Aggregate flow remains market participation evidence and cannot change a company thesis.
- Sector-index return is not sector-component breadth.
- Sector rendering excludes empty listed universes and selects at most one relative leader and one
  relative laggard per KOSPI/KOSDAQ scope.
- Unresolved `ka10051`/`ka10066` basis reconciliation cannot produce concentration prose.
- If typed current local context is unavailable, the existing deterministic path remains fail-safe.

