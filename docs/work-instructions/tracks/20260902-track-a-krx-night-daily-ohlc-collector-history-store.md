# Track A — KRX NIGHT Daily OHLC Collector + History Store

Verify the actual KRX endpoint/schema used by the repository.

Prove and map:
- date
- product/instrument
- contract/maturity
- NIGHT session
- open/high/low/close
- volume/change fields if available

Preserve raw response SHA and normalized row fingerprint.

Store daily bars keyed by:
instrument + contract + reference_date + NIGHT.

Validate OHLC relations.
Never clip/swap/interpolate malformed rows.

Implement incremental production history storage plus bounded historical backfill for missing dates.

For run-51 replay:
prefer archived rows.
If missing history must be backfilled, use TEST/HISTORICAL namespace and dates <= 2026-09-01 only.
Do not mutate the original run-51 packet.
