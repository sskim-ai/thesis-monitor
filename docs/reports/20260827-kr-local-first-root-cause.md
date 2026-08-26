# KR Local-First Root Cause

Packet `2026-08-26-kr-run-40-706bc3003536` contained same-session KOSPI/KOSDAQ indices, scoped
breadth, aggregate participant flow, size indices, sector rows, and KR close FX. The natural
deterministic digest consumed only FX because `build_daily_digest()` had no typed market-context
input. The AI quality layer already knew how to build a KR-local plan, but that plan was not shared
with the deterministic renderer.

The repair adds a shared `KrMarketDigestPlan` to `DailyDigest`, loads the same cached cross-section
used by the market adapter, persists the plan in the AI packet, and gives both deterministic and AI
rendering the same evidence hierarchy. Root cause status: `PASS`.

