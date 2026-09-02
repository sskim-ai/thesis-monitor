# Track C — US 10Y Real-Yield Level + Delta

Use the same packet-owned 10Y real-yield series already used in the market message.

For frozen run-51 extract:
- latest safe observation level/date
- immediately previous valid observation level/date

Calculate:
delta_pp = current - previous
delta_bp = delta_pp * 100

Render, for example:
`미 10년 실질금리 1.82% (08/31 관측) · 직전 관측 대비 +0.04%p (+4bp)`

Do not use percentage-return semantics.
Do not call stale data "today".
Preserve source precision and numeric provenance.

If the previous observation is unavailable from frozen lineage, fail this enriched actual-send proof instead of fetching new data or inventing a delta.
