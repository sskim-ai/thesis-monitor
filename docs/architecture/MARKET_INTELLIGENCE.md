# Market Intelligence and Portfolio Transmission

## Problem

Earlier market messages explained method and repeated deterministic text but did not consistently
identify what moved, what the structure meant, or why it mattered to monitored companies. Allowing
Codex to fill missing breadth, sector, rate, FX, flow, or commodity data would create unverifiable
market narratives.

## Decision

`daily-review-v3.7` and output schema 4 use a deterministic market-intelligence layer:

```text
Verified market observations
  -> fact catalog and coverage
  -> approved relative performance
  -> two to four important changes
  -> market structure
  -> verified portfolio exposure groups
  -> allowed company transmission
  -> one to three next confirmations
  -> validated market Telegram
```

`app/services/market_intelligence_service.py` creates the packet contract. Codex selects and explains
only those facts. `ai-assisted-pilot-renderer-v3` integrates each fact once near its interpretation.

## Why

Market intelligence becomes auditable and relevant without turning a market move into a company
fact. The message stays compact and focuses on current changes rather than repeating every macro axis
or persistent assumption.

## Rejected Alternatives

- Web or external API collection by Codex.
- Treating index direction as broad risk-on without breadth.
- Treating absolute sector return as relative leadership without a backend relative fact.
- Applying every market fact to every monitored group.
- Converting rates, FX, oil, or sector moves directly into company earnings or thesis changes.
- Appending the full deterministic market report below the AI interpretation.

## Safety Constraints

- Only `fresh` or `revised` backend observations enter the fact catalog.
- Missing and stale categories remain explicit unknowns.
- Market numeric claims use exact fact, field, value, unit, semantic, prose location, usage, and scope.
- Market facts and stock facts cannot substitute for one another.
- Portfolio groups come from verified company profile and existing thesis exposure, never ticker rules.
- Market context is a tailwind, headwind, or neutral context; it is not fundamental confirmation.
- Important changes and portfolio groups are capped at four; next checks and cautions at three.
- With at least four prose-eligible market anchors, zero numeric claims is a hard validation failure.
- Fresh KOSPI200/KOSDAQ150 night-futures facts selected by the backend are required market facts and
  must appear in the interpretation, an important change, and exact numeric claims.

## Packet Inventory

The market packet inventories indices, sector proxies, breadth, market flows, FX, nominal and real
rates, breakeven inflation, credit, oil, volatility, liquidity, night futures, six-axis macro regime,
assumptions, portfolio groups, data quality, and unknowns. Availability is explicit by category.

Current verified limitations are:

- KR local indices are unavailable in the AI market packet.
- Breadth and market-wide investor flows are unavailable.
- Sector coverage is partial and currently SOXX-only.
- A stale broad-dollar observation is excluded instead of being backfilled.

## Night Futures

The US packet records expected session, query timestamps, source session, contract verification,
freshness, packet/catalog selection, AI usage, and Telegram rendering for both KRX contracts. Both
fresh contracts are compared in the dedicated Korean-opening section. One fresh contract is used
with a compact caution for the other; zero fresh contracts do not block market analysis. Night
futures are opening-price and overnight-risk context only, never company fundamental confirmation.

## Fact Selection and Structure

The selector chooses material facts that explain market direction, concentration, relative sector
leadership, positioning, discount-rate/FX transmission, or monitored portfolio relevance. Relative
performance is calculated deterministically. Codex does not subtract benchmark returns itself.

A regime description needs at least two compatible verified signals. Index direction without breadth
cannot prove broad participation. Allowed natural-language outcomes include broad or selective risk
appetite, large-cap concentration, growth or defensive leadership, cyclical rotation, discount-rate
pressure, liquidity support, and mixed conditions.

## Numeric Semantics

Distinct contracts cover:

- index, sector, and relative returns;
- FX level, point change, and percentage change;
- nominal/real yield level and basis-point change;
- breakeven and credit-spread level/change;
- oil price and oil return;
- futures close, point change, and return;
- volatility and broad-dollar levels/returns.

Level wording cannot cover a change and vice versa. A futures close cannot be described as a return.
An index return cannot be relabeled as a sector return. Registry scope prevents stock-only semantics
from appearing in market prose; verified market facts use `both` only when compact stock transmission
is allowed.

## FX, Rates, and Commodities

Transmission is conditional:

- FX may affect translation, imported input costs, and foreign positioning.
- Rates may affect discount rates, financing costs, and sector multiples.
- Oil may affect inflation, transport costs, and energy margins.

No direction applies mechanically to every exporter, growth company, carrier, or energy business. If
verified company exposure is absent, the fact remains generic market context. Even with exposure, a
market move does not prove company revenue, margin, or thesis change.

## Portfolio Exposure and Transmission

Groups come from verified `industry`, `sector`, `business_units`, `revenue_sources`, and stored thesis
macro impacts. Specialized groups include semiconductor/memory, insurance, transport, automotive,
biotech, and other Knowledge taxonomy categories. General/low profiles do not receive invented
sector-specific links. Known taxonomy-coverage cases such as POSCO Holdings, Samsung Electronics,
LS ELECTRIC, and Hanwha Aerospace remain documented gaps rather than ticker overrides.

Each transmission records the market fact, economic channel, direction, condition, affected group,
and `not_fundamental_confirmation=true`. Irrelevant groups are omitted. Stock messages may briefly
reference a linked market fact, then move to company-specific earnings, valuation, price, and supply.

## Next Confirmation and Data Caution

Each next check cites an available backend market fact that could confirm or disprove the current
interpretation. Generic phrases such as “monitor future market conditions” fail validation. Cautions
are limited to one to three missing/stale inputs that materially weaken the judgment; raw provider
metadata is never shown.

## Renderer Acceptance

KR messages contain one-line judgment, actual changes, market structure, portfolio transmission,
next confirmation, and material cautions. US messages add the backend-verified Korean pre-open night
futures section. Night futures are opening context, never Korean company thesis confirmation.
