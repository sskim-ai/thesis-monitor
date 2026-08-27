# KR Nearest Semantic Root Cause

The engine's `summary.nearest_support/resistance` means the mathematically nearest valid structural
candidate across available timeframes. The renderer treated that internal ownership as synonymous
with user-facing `가까운`, even though each zone already carried `proximity_tier` and
`active_relevance`. This allowed `RELEVANT` and `LONG_HORIZON` zones to inherit a false near label.

The internal fields remain intact. Rendering now applies a separate user-visible classification.
