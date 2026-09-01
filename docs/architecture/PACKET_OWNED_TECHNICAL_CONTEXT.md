# Packet-Owned Technical Context

Contract: `packet-owned-technical-context-v1`

## Purpose

The artifact freezes validated D/W/M technical evidence at source-monitor time so every downstream
decision observes the same data. It is internal packet evidence, not a public Action field.

## Identity

`technical_context_id` is deterministic over ticker, market, cutoff, raw-bar fingerprint, and
feature fingerprint. The artifact records session, source, source version, adjustment basis,
currency, security identity, as-of time, last completed bars, bar/feature counts, quality,
acquisition telemetry, cautions, and failure reason.

The raw bars are not copied into the AI packet. The immutable raw-bar fingerprint proves the input
set; the canonical computed feature packet is frozen for consumption. This avoids an oversized raw
payload while preventing downstream recomputation.

## States

- `FULL`: configured D/W/M features are valid and current for their timeframe semantics.
- `PARTIAL_SAFE`: at least one safe usable timeframe exists, while another is missing or stale.
- `UNAVAILABLE`: no safe technical facts were acquired after bounded recovery.
- `INVALID`: supplied bars violate integrity or comparability requirements.

Only facts whose timeframe quality has `usable_for_current_reasoning=true` enter V2 evidence. The
decision packet always carries the context status and data-quality caution; missing evidence is not
silently neutral and does not hard-map to `HOLD`.

## Compatibility

The internal serializer includes `technical_context`; ordinary `PriceContext.model_dump()` remains
unchanged. Legacy packets without the artifact become subject-local `UNAVAILABLE` contexts. No
ticker/date/value override exists.
