# KR Valuation Numeric-Ref Root Cause

- Instruction: `docs/work-instructions/20260825-kr-valuation-ref-repair-and-kr-us-market-adapter-integration.md`
- Instruction commit: `c058839c5e63a08c096bd6a9a1b2139290d17eb0`
- Implementation: `b39c2ea38a8d5d3466889a9da394df05ad95701a`
- Packet: `2026-08-25-kr-run-38-6cd8c5d5091b`
- Classification: `C. historical/current ownership mapping mismatch`

## Immutable evidence

| Artifact | SHA-256 |
| --- | --- |
| inbox packet | `ef456b24b036fcc1b6926489c5e8058eed8a70f570f5df1d49e9c93fe35f487d` |
| rejected candidate | `43a6ef4a7ce8fca137d8c0483e08a6557d0ea23b512d03cfc4dab3ee4f563330` |
| runtime validation result | `f108a66d0d0194979e018ffa4d0933d14978cc72131a28751bc16a719c2cf8de` |

The packet safely registered `valuation:current/fields.price_to_book` and
`valuation:current/fields.historical_pb_statistics.current_percentile`. Both
were prose eligible and retained verified OpenDART book-value lineage.

The candidate correctly declared the typed interpretation facts
`valuation:book` and `valuation:historical_pb`, but its two numeric refs pointed
to the parent source `valuation:current`. Both numeric validation layers only
accepted an exact parent fact ID in `facts_used`, so they rejected the safe
typed declaration even though the typed facts contained the exact same field
and value.

Pre-repair errors:

```text
000660:numeric_fact_ref_fact_not_declared:s000660_val_pbr:valuation:current
000660:numeric_fact_ref_fact_not_declared:s000660_val_hist_pb:valuation:current
```

This was not a price, BVPS, security-basis, historical-period, or valuation
calculation defect. No valuation fact was removed and no validator was relaxed.

