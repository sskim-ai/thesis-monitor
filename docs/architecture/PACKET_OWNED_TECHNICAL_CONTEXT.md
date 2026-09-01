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
set, including rejected rows; the canonical computed feature packet is frozen for consumption.
Malformed specimens and refetch outcomes live in bounded acquisition telemetry. This avoids an
oversized raw payload while preserving enough evidence to distinguish stable, intermittent, and
recovered provider content.

## States

- `FULL`: configured D/W/M features are valid and current for their timeframe semantics.
- `PARTIAL_SAFE`: at least one safe usable timeframe exists, while another is missing or stale.
- `UNAVAILABLE`: no safe technical facts were acquired after bounded recovery.
- `INVALID`: supplied bars violate integrity or comparability requirements.

Only facts whose timeframe quality has `usable_for_current_reasoning=true` enter V2 evidence. The
decision packet always carries the context status and data-quality caution; missing evidence is not
silently neutral and does not hard-map to `HOLD`.

The source client applies `ohlcv-provider-integrity-v1` before this contract. One malformed-content
refetch may recover a transient response. A repeated malformed response is stored unchanged and
this context remains `INVALID`; invalid bars never produce the frozen feature packet.

## Compatibility

The internal serializer includes `technical_context`; ordinary `PriceContext.model_dump()` remains
unchanged. Legacy packets without the artifact become subject-local `UNAVAILABLE` contexts. No
ticker/date/value override exists.
