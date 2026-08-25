# KR Market Digest Quality

## Contract

`kr-market-digest-quality-v1` consumes `market-context-adapter-v1`. It does not infer richness from
the number of fields or from generated prose.

`KR_DOMESTIC_CONTEXT_RICH` is true only when all of the following hold:

1. The provider-complete session is final and equals the calendar-derived latest completed KR
   regular session.
2. Same-session KOSPI and KOSDAQ index facts are present.
3. Reconciled KOSPI and KOSDAQ breadth are both available.
4. At least one typed local context family is present: market-wide participant flow, size/style, or
   sector context.

## Priority

When richness is true, the renderer uses this order:

1. `P1_KR_LOCAL_MARKET_STRUCTURE`: KOSPI/KOSDAQ, breadth, size/style, sectors.
2. `P2_KR_LOCAL_MARKET_FLOW`: market-wide participant flow and safely reconciled concentration.
3. `P3_KR_LOCAL_STOCK_CROSS_SECTION`.
4. `P4_GLOBAL_CURRENT_CONTEXT`.
5. `P5_REFERENCE_LAGGING_MACRO`.

Judgment, interpretation, and next check must each remain in P1/P2 unless a documented global fact
materially contradicts the local conclusion. The compact default is one structure conclusion, one
local interpretation, one boundary, and one decision-changing local next check.

KOSPI concentration remains excluded while the `ka10051` and `ka10066` basis/taxonomy mismatch is
unresolved. KOSDAQ concentration may be consumed only from the existing reconciled canonical
relation; the bounded repair does not require displaying it and does not quote either market's raw
concentration tuple.
