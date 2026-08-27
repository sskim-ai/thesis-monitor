# KR Local-First Market Digest

Contract: `kr-market-digest-quality-v1`

## Ownership

The completed Korean session owns the primary KR afternoon digest. Evidence order is:

1. KOSPI and KOSDAQ direction.
2. KOSPI and KOSDAQ scoped breadth.
3. Same-session aggregate foreign, institution, and retail flow.
4. Same-session KOSPI and KOSDAQ size/style context.
5. Bounded non-empty sector-index relative-strong/relative-weak context.
6. KR close FX.
7. Prior/global macro context as a qualified secondary section.

Completed KOSPI/KOSDAQ indices plus reconciled scoped breadth are the minimum local-first contract.
Flow is consumed when present. Safe same-session size/style and sector-extrema layers use
`SELECTED_REQUIRED`; brevity alone cannot omit them. Their absence does not hand ownership back to
a prior US body.

## Shared Path

```text
structured market cross-section
-> market-context-adapter-v1
-> KrMarketDigestPlan
-> deterministic daily digest
-> AI market evidence catalog
```

The deterministic renderer and the AI evidence-lock adapter consume the same plan. The AI may
interpret supplied claims but does not calculate breadth, flow, size returns, or sector ranking.

## Boundaries

- Index direction and breadth are separate claims.
- Aggregate flow remains market participation evidence and cannot change a company thesis.
- Sector-index return is not sector-component breadth.
- KOSPI size rendering requires the complete large/mid/small trio; KOSDAQ size rendering requires
  the complete KOSDAQ100/MID300/SMALL trio. An incomplete market is omitted without fabrication,
  while a complete peer market may still render.
- Sector rendering excludes size/style rows and empty listed universes, then selects at most one
  relative-strong and one relative-weak sector per KOSPI/KOSDAQ scope.
- User-facing terminology is `상대 강세` and `상대 약세`; internal leader/laggard labels never
  reach prose.
- Length pressure removes repetitive global or prior-US context before required current-session KR
  size/sector structure.
- Unresolved `ka10051`/`ka10066` basis reconciliation cannot produce concentration prose.
- If typed current local context is unavailable, the existing deterministic path remains fail-safe.
