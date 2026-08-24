# KR Fresh Fallback Bundle

Generation and integrity results:

- Market digest: 1/1
- Stock messages: 7/7
- Missing messages: 0
- Duplicate messages: 0
- Packet linkage: 8/8
- Telegram sends: 0

The stock messages preserve current 2026-08-24 price, RR, major-three supply tuples, valuation
fail-closed behavior, and three selected Inventory relations. Trade AR/AP enrichment is absent.

The bundle is not content-safe as a whole. Its market digest consumed a pre-contract morning macro
briefing and rendered lagging observations as current changes. Therefore completeness is PASS but
the required factual/temporal safety gate is FAIL.

`FALLBACK_BUNDLE = FAIL (MACRO_TEMPORAL_P0)`

The exact no-send output is in `20260824-kr-fresh-live-rehearsal-message-bundle.md`.
