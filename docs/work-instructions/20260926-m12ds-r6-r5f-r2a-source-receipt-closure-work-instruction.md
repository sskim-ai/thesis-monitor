# R5F-R2a: Owner-Bound Acquisition Receipt Closure

## Purpose

Close R5F-R2's first failed gate, not rerun a broad AI experiment. Preserve
R5F-R1 orchestration and R5F-R2 source replay checks. No scheduler promotion,
production writes, Telegram, restart, deploy or remote push is authorized.

## Exact Boundaries

1. Add an opt-in request/response observer to existing OHLCV stock and market
   owners. Capture exact bytes or immutable source artifact, sanitized request
   identity, aware request/response times, response provider, symbol, adjustment
   and session basis, normalized hash and existing validator receipt.
   Instrument every retry/refetch, not only the successful terminal response.
   Default owner behavior must remain unchanged.
2. Make a per-market source owner plan that excludes Alpha, Massive and mock
   providers before dispatch. Audit nested calls and gateway upstream metadata.
   `provider_priority`, `ValuationSnapshotService.fetch` and
   `run_kr_close_market_briefing` are the known bypass points. Blocking new
   calls is insufficient while cached Alpha estimates/shares can still be read.
   Unavailable optional facts stay unavailable; do not invent a new provider.
3. Seed only canonical watchlist, security identity, stored thesis and required
   versioned business metadata into a new attempt-local store. Explicitly
   distinguish legitimate stored thesis/monitoring state from source caches.
   Do not wholesale copy operating assessments, source snapshots or macro
   observations and call them freshly collected. Freeze seed hashes separately.
4. Acquire declared night roles inside the attempt, or define and validate an
   explicit current-contract source-artifact acquisition role before use.
   Do not rewrite historical night receipt timestamps/attempt IDs.
5. Add equivalent receipts at financial, event, valuation and market archive
   boundaries for every consumed role. Optional missing roles need explicit
   owner denial; all retained values need source lineage.

## Offline First

Use saved raw fixtures where genuinely present. Exercise real owner parser,
normalizer and validator functions without network. Test A/B/C attempt
isolation, missing artifact, wrong symbol/date/basis, response tampering,
hidden prohibited provider, cached prohibited source, and no model on failure.
Do not manufacture HTTP payloads from existing normalized chart summaries.
Synthetic fixtures prove mechanics only, not real-source parity.

If a new bounded source acquisition is required because historical raw
responses are absent, freeze the exact market/role/request allowlist and budget
and obtain authorization under the active task. This document does not grant
new network authorization. Until a complete real cohort is available, keep
the adapter unqualified and no model calls.

## Resume R5F-R2

After real source parity passes, finish the per-market Market/Core/A/B bridge
using unchanged canonical owners, remove only research packaging dependencies,
prove deterministic request/schema/policy parity and dry-run delivery, and
then perform the original gated US15/KR9 message proof. Preserve failed source
attempts, hashes, reports and immutable iCloud-local receipts.

No scheduler R5F-R3 activation until the complete R5F-R2 gate is accepted.
