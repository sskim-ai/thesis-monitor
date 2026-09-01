# Track A — KR Run / Packet / Data Lineage / Freshness

Target:
- KR session 2026-09-01
- 8 active KR reference subjects
- expected 1 market + 8 stock only if cutoff proves all eligible

Collect read-only:
- scheduler actual runs
- packet ID / claim owner / cutoff
- runtime SHA
- frozen cohort
- source-monitor receipts
- market session/freshness
- price/supply dates
- packet-owned D/W/M technical-context states
- evidence fingerprints

Build today-vs-last-pass field-level data delta.

No rerun, resend, cache patch, or DB mutation.
