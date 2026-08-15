# Deterministic Security Identity Resolution

## Problem

A missing depositary indicator was previously represented by `is_depositary_security=false`.
The provider-native multiple contract treated that value as proof of a non-depositary security.
This could expose a consensus multiple even when the company name, security type, issuer type,
or ADR metadata conflicted and the current-security denominator had not been verified.

## Decision

Security identity eligibility uses `security-identity-v1` and four deterministic states:

| State | Meaning | Security/share-basis valuation |
| --- | --- | --- |
| `verified_depositary` | Depositary identity has affirmative evidence | Only with a verified current-security denominator and compatible currency/share basis |
| `verified_non_depositary` | Issuer and security evidence consistently verify a non-depositary security | Provider-native multiple may be eligible if the remaining source/period/basis contract passes |
| `conflict` | Two or more identity signals are inconsistent | Denied |
| `unknown` | Evidence is incomplete | Unknown and prose-ineligible |

The resolver records evidence sources and values, conflict reasons, verification status,
as-of/source provenance, and the eligibility decision. The durable assessment stores this
metadata inside the existing `financial_quality_source_metadata.security_identity` JSON contract,
so no database or Public Action schema change is required. The AI packet exposes the same result
as `security_identity:current` and on the valuation payload.

## Evidence

The resolver considers Watchlist issuer type, ordinary-share identifier and ADR ratio;
SecurityMaster issuer/security types, ADR identifier and ratio, identity quality/provider/warnings;
country and exchange; and an explicit ADR/ADS marker in the verified profile name. A profile-name
marker is conflict evidence, not an ADR ratio or conversion input.

Absence of an ADR identifier, a default `domestic_us` value, or legacy boolean `false` does not
establish `verified_non_depositary`. Conflicting sources are not silently ranked or overwritten.

## Eligibility Propagation

`conflict` and `unknown` propagate through `financial-quality-taint-v2` to all values that require
a current-security/share basis: EPS, PER, BVPS, PBR, forward multiples, historical per-share
percentiles, and derived valuation position. Raw audit values remain stored, but their numeric
registry rows have `prose_allowed=false`, no canonical display value, and no approved variants.

Issuer-level monetary facts, price, OHLCV, chart structure, volume, and KR investor flow remain
independent when their own contracts pass. A verified depositary still requires a compatible
current-security denominator; no FX or ADR-ratio inference is performed.

## Validator And Fallback

The binder rejects placeholders for identity-ineligible rows. The validator also rejects existing
or raw numeric claims and number-free valuation interpretations that cite a denied valuation fact.
The separate `security_identity:current` fact may support a concrete Unknown explanation.

The deterministic fallback reads the same persisted identity metadata. It removes denied numeric
and qualitative multiple claims while retaining independent price, chart, volume, supply, and
issuer-financial facts. Persisted-payload retry and single-delivery behavior are unchanged.

## Why

Provider provenance validates where a multiple came from; it does not prove what security or share
basis the denominator represents. Making identity an affirmative, auditable contract prevents an
unknown or conflicting listing from becoming an apparently canonical valuation fact.

## Rejected Alternatives

- Trusting `is_depositary_security=false`: absence was the original unsafe shortcut.
- Guessing from a ticker or company name: names are only conflict signals and cannot establish a ratio.
- Provider priority overwrite: it would conceal evidence conflicts.
- Prompt-only avoidance or renderer deletion: both operate after canonical eligibility and can be bypassed.
- Adding FX or ADR conversion: the required ratios and denominator basis are not verified.

## Safety Constraints

- No ticker-specific production branch.
- No inferred ADR ratio, currency conversion, premium, or discount.
- `unknown` and `conflict` never become verified non-depositary states.
- Numeric and qualitative valuation use share the same field-level eligibility boundary.
- Renderer remains a layout component, not a semantic rewriter.
- Schema 4, Public Action 0.4.5, and the existing database schema remain unchanged.

## Phase 7.2.5 Evidence

The isolated 2026-08-15 US replay classified SKHY as `conflict` because the profile name identifies
an ADR while SecurityMaster identifies a domestic common stock. Its previously visible consensus
fPER was denied; price and 20-day volume remained usable. GOOGL exposed a separate SecurityMaster
issuer/security-type conflict and was also failed closed. The 2026-08-14 KR replay remained
message-identical after normalizing only the Pilot candidate label.

This contract is experimental on `codex/phase-7-2-relational-reasoning`. Production remains on
`daily-review-v3.9` until a separate merge and deployment approval.
