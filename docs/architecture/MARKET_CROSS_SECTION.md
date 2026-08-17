# Market Cross-Section Architecture

## Purpose

`market-cross-section-v1` supplies provider-neutral US and KR market breadth without asking the AI to
calculate, infer, or fill missing market data. It is a context layer only:

```text
provider raw response
  -> normalized listed-security rows
  -> explicit eligible-universe filter
  -> deterministic breadth and concentration calculations
  -> canonical market Facts and numeric semantics
  -> optional market interpretation
```

Breadth, sector participation, and market flow are tailwind, headwind, or positioning context. They
never confirm or change a company fundamental thesis by themselves.

## Common Contract

The `MarketCrossSection` model records:

- market, session date, timezone-aware provider timestamp;
- index observations;
- eligible, advance, decline, and unchanged counts;
- advance ratio, A/D ratio, median return, and equal-weight return;
- total trading volume and safely calculated close-times-volume value;
- concentration evidence whose proxy role is explicit;
- sector rows with provider taxonomy and either `actual_sector_breadth` or
  `sector_price_proxy` role;
- market flow only when an official/queryable aggregate source exists;
- provider, coverage, freshness, universe version, calculation version, exclusions, and source hash.

Missing is never zero. Stale data is not promoted as the current session. Partial data exposes only
the verified subset.

## US Universe

The initial Massive universe is security-level, not issuer-level. Separate listed share classes such
as GOOG and GOOGL remain separate securities. The filter accepts active USD US-listed operating
equity types `CS`, `ADRC`, `OS`, and `NYRS` on eligible primary exchanges. It excludes funds, ETF,
ETN, preferred, warrant, right, unit, OTC, inactive, test issue, missing reference identity, and rows
without the same ticker's previous adjusted close.

The grouped endpoint alone is not sufficient because it includes non-operating securities. Massive
reference metadata is therefore a required input to breadth. Provider row order never affects the
result.

## Concentration And Sectors

The first concentration metric is:

```text
SPY daily return - eligible-security equal-weight return
```

It is stored as `broad_cap_weight_proxy_gap`, not as a cap-weighted whole-market return. Sector ETF
returns, when used, are `sector_price_proxy`; they are not constituent sector breadth.

## KR Provider Priority

The target ordering is:

1. KRX official API as primary canonical KR market data after approval and validation;
2. Kiwoom as `bridge_shadow`, later reconciliation/secondary;
3. unavailable when neither source has comparable current-session evidence.

Kiwoom never becomes an authoritative replacement for KRX. Automatic metric-level fallback is
disabled until the same-date universe, units, session, and calculation semantics reconcile for at
least five trading sessions.

## Reconciliation

Every provider records raw count, eligible count, excluded count, and exclusion reasons. A comparison
is not valid when market, date, or universe version differs. KRX/Kiwoom reconciliation checks index
levels within official rounding tolerance, exact counts after universe normalization, return rounding,
and normalized trading-value units. ETF, preferred, REIT, SPAC, no-trade, suspended, and new-listing
rules are diagnosed before assigning provider error.

## Delivery Boundary

Phase 8 providers are shadow-only. They are not registered in Scheduled Tasks or Telegram delivery.
The existing numeric provenance registry owns every new market number. Provider absence preserves the
existing proxy context and explicit Unknown; SPY/QQQ/SOXX are never relabeled as breadth.
