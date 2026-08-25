# Market Context Adapter

## Status

`market-context-adapter-v1` is the common typed boundary between verified market Facts and the
Common AI Core. It is implemented for KR and US packets as a production sidecar pending natural
observation. It does not fetch data, alter public schemas, or replace `market-cross-section-v1`.

```text
verified market Fact catalog / optional MarketCrossSection
  -> point-in-time filter
  -> market-specific semantic adapter
  -> common NormalizedMarketContext
  -> packet sidecar
  -> existing AI validation and fallback
```

## Contract

The normalized object carries market, assessment/session dates, timezone-aware `as_of` and cutoff,
indices, breadth, size context, sectors, market-wide flows, concentration, deterministic relations,
session state, provider-publication state, source policy, and explicit gaps. KR and US return the
same model. Missing fields are empty/Unknown and are never zero-filled.

Every consumed Fact needs a canonical `fact_id` and valid `as_of_date`. Facts after the assessment
date are suppressed. A supplied cross-section must match market and be available no later than the
cutoff. Missing IDs and dates remain named gaps.

## Deterministic Relations

Breadth participation and concentration preserve formula, input refs, result, unit, date, scope,
and limitations. Existing relative-return Facts are exposed only when both input Facts exist on the
same date and their arithmetic reproduces exactly. The AI does no subtraction or ratio calculation.

## Packet Boundary

The sidecar is derived from Facts already owned by packet identity, so the sidecar itself is excluded
from immutable packet hashing. Its `as_of` follows packet generation time without creating a new
packet ID. Internal official-source hints are excluded from the AI packet to preserve the existing
provider-detail sanitization rule.

Public Action `0.4.5`, output schema `4`, fallback rendering, Telegram payload shape, canary limits,
and delivery identity remain unchanged.

## Failure Policy

- Partial fields do not block packet creation.
- Future or unidentified Facts are suppressed.
- Cross-market cross-sections fail closed.
- Mixed-unit KR market flow fails closed.
- Unsupported US participant-flow semantics fail closed.
- Stock-level flow and macro Facts are not recast as market-wide adapter data.

