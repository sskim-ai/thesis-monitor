# SR Proximity Relevance Gate

Contract: `sr-proximity-relevance-gate-v1`.

The gate has timeframe-aware base bands and expands them only with the median width of eligible
zones, subject to timeframe caps. It classifies `NEAR`, `RELEVANT`, `LONG_HORIZON`, and
`OUT_OF_ACTIVE_RANGE`. A cross-timeframe candidate must also remain close to the nearest valid
local zone on the same side. Long-history zones remain auditable but cannot become the current
nearest or active-major summary merely through historical source count.
